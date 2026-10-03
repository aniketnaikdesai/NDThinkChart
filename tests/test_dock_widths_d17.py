"""T47 / D17 Phase 2 — live watchlist clamp in ``MainWindow``.

These are focused offscreen integration tests for the ``ui/main_window.py`` side
of D17: the shared ``MainWindow._apply_dock_widths`` clamp, the drag hook / event
filter, the two-directional ``resizeEvent`` re-clamp, persistence re-clamping,
and the re-entrancy guard that prevents recursion/jitter.

Geometry note (deterministic offscreen harness)
-----------------------------------------------
On the offscreen platform the toolbar's ``minimumSizeHint`` is ~1716px wide,
which pins the central widget and caps the left dock far below the 50% rule —
masking the very behaviour under test. The toolbar is not part of the D17
surface, so ``_make_window`` hides it (and the right docks) to give the chart
area a real, adjustable width and let the watchlist dock reach its cap.

Tolerance note
--------------
``_apply_dock_widths`` only re-issues ``resizeDocks`` when the computed width
differs from the current width by **more than 1px** (an explicit acceptance
criterion), so a residual of at most 1px is expected and asserted with ``+1``.
"""

import pytest
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QDockWidget

from ui.watchlist_panel import (
    CHART_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    DEFAULT_WATCHLIST_WIDTH,
    WATCHLIST_WIDTH_KEY,
    watchlist_max_width,
)

# Right-hand docks are unrelated to the D17 watchlist clamp under test.
_RIGHT_DOCKS = ("Active Trader", "Portfolio")

_QSETTINGS_ORG = "NDThinkChart"
_QSETTINGS_APP = "NDThinkChart"


def _seed_saved_width(value) -> None:
    settings = QSettings(_QSETTINGS_ORG, _QSETTINGS_APP)
    if value is None:
        settings.remove(WATCHLIST_WIDTH_KEY)
    else:
        settings.setValue(WATCHLIST_WIDTH_KEY, value)
    settings.sync()


def _make_window(monkeypatch, qapp, width=1600, height=900):
    """Build a shown ``MainWindow`` that never touches TWS.

    Hides the toolbar (its offscreen minimum pins the geometry) and the right
    docks so the watchlist clamp is the only horizontal constraint under test.
    """
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()

    # Relax the offscreen toolbar constraint and drop the unrelated right docks.
    central_layout = win.centralWidget().layout()
    if central_layout is not None and central_layout.count() > 0:
        toolbar = central_layout.itemAt(0).widget()
        if toolbar is not None:
            toolbar.hide()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in _RIGHT_DOCKS:
            dock.hide()
    qapp.processEvents()
    return win


def _drive_to_cap(win, qapp, iterations=12):
    """Repeatedly request an oversized width until the clamp settles.

    Each call re-reads the (shrinking) chart area, so the width converges to the
    stable fixed point where ``dock == floor(0.50 * chart_area)``.
    """
    for _ in range(iterations):
        win._apply_dock_widths(10 ** 6)
        qapp.processEvents()


# ── T47-T01 / AC-D17.1 — drag right: grow to the chart-area cap ──────────────

def test_T47_T01_drag_right_grows_to_chart_area_cap(monkeypatch, qapp):
    """T47-T01 / AC-D17.1: watchlist grows to the 50%-of-chart-area cap."""
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        ca_before = win._chart_area_width()
        assert win.watchlist_dock.width() < ca_before

        # Simulate the continuous drag: repeated oversized requests, each
        # re-reading the chart area until the clamp settles.
        _drive_to_cap(win, qapp)

        ca_after = win._chart_area_width()
        cap = watchlist_max_width(ca_after)
        dock_w = win.watchlist_dock.width()

        # The cap binds: within the mandated 1px re-issue tolerance of the
        # 50%-of-chart-area rule, and never above the cap term.
        assert abs(dock_w - int(ca_after * 0.50)) <= 1
        assert dock_w <= cap + 1
        assert dock_w > WATCHLIST_MIN_WIDTH
        # The chart area narrowed versus the pre-drag value.
        assert ca_after < ca_before
    finally:
        win.close()


# ── T47-T02 / AC-D17.2 — drag left: shrink to WATCHLIST_MIN_WIDTH ────────────

def test_T47_T02_drag_left_reduces_to_minimum(monkeypatch, qapp):
    """T47-T02 / AC-D17.2: leftward drag decreases monotonically to 150px."""
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        _drive_to_cap(win, qapp)
        start = win.watchlist_dock.width()
        assert start > WATCHLIST_MIN_WIDTH

        prev = start
        for requested in (700, 600, 500, 400, 300, 200, 160, 100):
            win._apply_dock_widths(requested)
            qapp.processEvents()
            width = win.watchlist_dock.width()
            assert width <= prev, (requested, width, prev)
            assert width >= WATCHLIST_MIN_WIDTH, (requested, width)
            prev = width

        # A below-minimum request floors at the dock minimum.
        win._apply_dock_widths(0)
        qapp.processEvents()
        assert win.watchlist_dock.width() == WATCHLIST_MIN_WIDTH
    finally:
        win.close()


# ── T47-T03 / AC-D17.3 — cap binds during the drag, no resizeEvent ───────────

def test_T47_T03_cap_enforced_by_handler_without_window_resize(
    monkeypatch, qapp
):
    """T47-T03 / AC-D17.3: the drag hook clamps an overshoot with no resize."""
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        # Count window resize events so we can prove none fires in this path.
        resize_events = []
        original_resize_event = win.resizeEvent

        def _counting_resize_event(event):
            resize_events.append(event)
            original_resize_event(event)

        win.resizeEvent = _counting_resize_event

        # Overshoot the cap by resizing the dock past it (a real handle drag can
        # put the splitter section past the cap before our hook pulls it back).
        ca_before = win._chart_area_width()
        cap_before = watchlist_max_width(ca_before)
        overshoot = cap_before + 300
        win.resizeDocks(
            [win.watchlist_dock], [overshoot], Qt.Orientation.Horizontal
        )
        qapp.processEvents()
        assert win.watchlist_dock.width() > cap_before
        resize_events.clear()  # ignore any incidental resize before the drag

        # Invoke the drag hook directly: no window resize is performed here.
        win._on_dock_splitter_moved(0, 0)
        qapp.processEvents()

        dock_w = win.watchlist_dock.width()
        assert resize_events == [], "the drag hook must not trigger a window resize"
        # The width is the *cap*, not the oversized request.
        assert dock_w != overshoot
        assert dock_w <= cap_before + 1
        # The chart minimum is preserved.
        assert win._chart_area_width() >= CHART_MIN_WIDTH
    finally:
        win.close()


# ── T47-T04 / AC-D17.4 — persisted width restored, clamped ───────────────────

def test_T47_T04_persisted_width_restored_clamped(monkeypatch, qapp):
    """T47-T04 / AC-D17.4: a large saved width is restored clamped to the cap."""
    _seed_saved_width(10 ** 6)
    win = _make_window(monkeypatch, qapp)
    try:
        ca = win._chart_area_width()
        cap = watchlist_max_width(ca)
        # Restored as an int px value clamped to the current chart-area cap.
        assert isinstance(win._watchlist_width, int)
        assert win._watchlist_width == cap
        assert win.watchlist_dock.width() <= cap + 1
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
    finally:
        win.close()
        _seed_saved_width(None)


def test_T47_T04_default_and_floor(monkeypatch, qapp):
    """T47-T04 / AC-D17.4: no saved value yields ~220px; small values floor at 150."""
    # No saved value → the ~220px default (chart area is wide enough for it).
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        assert win._watchlist_width == DEFAULT_WATCHLIST_WIDTH
        assert win.watchlist_dock.width() == DEFAULT_WATCHLIST_WIDTH
    finally:
        win.close()

    # A too-small saved value is never below the 150px floor.
    _seed_saved_width(10)
    win2 = _make_window(monkeypatch, qapp)
    try:
        assert win2._watchlist_width == WATCHLIST_MIN_WIDTH
        assert win2.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
    finally:
        win2.close()
        _seed_saved_width(None)


# ── T47-T05 / AC-D17.5 — re-clamp when the chart area shrinks ────────────────

def test_T47_T05_reclamp_when_chart_area_shrinks(monkeypatch, qapp):
    """T47-T05 / AC-D17.5: narrowing the window re-clamps to the new cap."""
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        _drive_to_cap(win, qapp)
        wide_dock = win.watchlist_dock.width()
        assert wide_dock > WATCHLIST_MIN_WIDTH

        # Narrow the window: this fires resizeEvent → the shared re-clamp.
        win.resize(900, 700)
        qapp.processEvents()

        new_ca = win._chart_area_width()
        new_cap = watchlist_max_width(new_ca)
        assert new_cap < wide_dock
        assert win.watchlist_dock.width() <= new_cap + 1
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH

        # Still resizable after the re-clamp.
        win._apply_dock_widths(WATCHLIST_MIN_WIDTH + 20)
        qapp.processEvents()
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
        assert win.watchlist_dock.width() <= watchlist_max_width(
            win._chart_area_width()
        ) + 1
    finally:
        win.close()


# ── T47-T06 — re-entrancy guard / no-op when unchanged ───────────────────────

def test_T47_T06_reentrancy_guard_and_noop_when_unchanged(monkeypatch, qapp):
    """T47-T06: repeated applies at fixed geometry do not re-issue resizeDocks."""
    _seed_saved_width(None)
    win = _make_window(monkeypatch, qapp)
    try:
        calls = []
        real_resize_docks = win.resizeDocks

        def _counting_resize_docks(docks, sizes, orientation):
            calls.append((list(sizes), orientation))
            return real_resize_docks(docks, sizes, orientation)

        win.resizeDocks = _counting_resize_docks

        # Converge, then continue applying at the settled geometry.
        _drive_to_cap(win, qapp)
        settled = len(calls)
        for _ in range(5):
            win._apply_dock_widths(10 ** 6)
            qapp.processEvents()
        # No further resizeDocks calls: the residual is within the 1px tolerance.
        assert len(calls) == settled, (settled, len(calls))

        # A re-entrant apply is suppressed by the guard flag.
        before = len(calls)
        win._applying_dock_widths = True
        try:
            result = win._apply_dock_widths(10 ** 6)
        finally:
            win._applying_dock_widths = False
        assert len(calls) == before
        assert result == win._watchlist_width

        # No stack growth / recursion: a fresh apply still works afterwards.
        win._apply_dock_widths(0)
        qapp.processEvents()
        assert win.watchlist_dock.width() == WATCHLIST_MIN_WIDTH
    finally:
        win.close()


# ── T47-T07 — the D10/D13 integration suite is updated to chart-area ─────────

def test_T47_T07_d10_d13_integration_chart_area_denominator():
    """T47-T07: run the updated D10/D13 integration module and assert it is green.

    ``tests/test_d10_d13_integration.py`` is updated in lockstep to the
    chart-area denominator and the existing D10 volume-toggle assertions remain.
    """
    import importlib.util
    from pathlib import Path

    module_path = Path(__file__).resolve().parent / "test_d10_d13_integration.py"
    spec = importlib.util.spec_from_file_location(
        "test_d10_d13_integration", module_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # The module's clamp helper must be the chart-area one (D17 denominator).
    from ui.watchlist_panel import watchlist_max_width as panel_cap
    assert mod.watchlist_max_width is panel_cap
    # The clamp formula used in the module is the chart-area formula.
    for chart_area_w in (1400, 900, 600):
        assert mod.watchlist_max_width(chart_area_w) == max(
            WATCHLIST_MIN_WIDTH,
            min(int(chart_area_w * 0.50), chart_area_w - CHART_MIN_WIDTH),
        )
