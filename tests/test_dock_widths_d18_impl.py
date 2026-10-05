"""T49 / D18 Phase 4 — right-region 40% cap, cross-clamp, content bound, full-screen.

Focused offscreen integration tests for the ``ui/main_window.py`` side of D18:
the single right region wired into the shared ``MainWindow._apply_dock_widths``
(grows to ``floor(0.40 × chart_area)``, shrinks to ``RIGHT_DOCK_MIN_WIDTH``,
cross-clamps with the watchlist so ``chart_area >= 400px``), the
``changeEvent(WindowStateChange)`` / ``resizeEvent`` full-screen normalize, the
"not persisted" default, and the panel content bound that keeps the region
on-screen when the ladder/portfolio content is wider than the region.

Geometry note (deterministic offscreen harness)
----------------------------------------------
D19 Phase 2: the offscreen toolbar's ``minimumSizeHint`` (~1716px) no longer
pins the central widget — it is wrapped in a horizontal ``QScrollArea``
(``ToolbarScroll``) — so the harness runs with the toolbar **visible** and no
masking, and the dock geometry settles to the requested window size. Unlike the
D17 tests, the single right region is **kept visible** here — the D18 cap is
about the region, so hiding it would diverge.

Tolerance note
--------------
``_apply_dock_widths`` only re-issues ``resizeDocks`` when the computed width
differs from the current width by more than 1px (an explicit acceptance
criterion), so a residual of at most 1px is expected and asserted with ``+1``.
Qt also distributes slack among the docks listed to ``resizeDocks``; the
implementation passes both docks together so each stays at its plan value.
"""

from pathlib import Path

import pytest
from PyQt6.QtCore import QEvent, QSettings, Qt
from PyQt6.QtWidgets import QDockWidget, QTableWidgetItem, QWidget

from ui.dock_layout import (
    CHART_MIN_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    right_dock_max_width,
    watchlist_max_width,
)
from ui.watchlist_panel import WATCHLIST_WIDTH_KEY

_QSETTINGS_ORG = "NDThinkChart"
_QSETTINGS_APP = "NDThinkChart"

# Keys a naive right-region persistence would introduce (AC-D18.7). None may be
# written; the region is in-memory only, matching D10's volume-toggle precedent.
_RIGHT_PERSISTENCE_HINTS = ("right", "active_trader", "portfolio", "right_dock")


def _clean_settings() -> QSettings:
    settings = QSettings(_QSETTINGS_ORG, _QSETTINGS_APP)
    settings.remove(WATCHLIST_WIDTH_KEY)
    settings.sync()
    return settings


def _make_window(monkeypatch, qapp, width=1600, height=900):
    """Build a shown ``MainWindow`` that never touches TWS, right region visible."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()

    # D19 Phase 2: the toolbar is wrapped in a horizontal ``QScrollArea``
    # (``ToolbarScroll``), so its ~1716px natural width no longer pins the
    # central widget. The harness therefore exercises a **toolbar-visible**
    # window with no masking, and the dock geometry settles to the requested
    # window size.
    qapp.processEvents()
    win.resize(width, height)
    qapp.processEvents()
    return win


def _drive_right_to_cap(win, qapp, iterations=14):
    """Repeatedly request an oversized right region until the clamp settles."""
    for _ in range(iterations):
        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()


# ── T56-T01 / AC-D19.6 — toolbar visible, no masking ─────────────────────────

def test_T56_T01_toolbar_visible_and_no_masking(monkeypatch, qapp):
    """T56-T01 / AC-D19.6: harness shows the toolbar; no hide() masking remains."""
    win = _make_window(monkeypatch, qapp)
    try:
        toolbar = win.findChild(QWidget, "MainToolbar")
        assert toolbar is not None, "MainToolbar widget not found"
        assert toolbar.isVisible(), "toolbar is not visible in the harness window"
    finally:
        win.close()

    # The module source must contain no toolbar-hiding masking and no stale
    # central-layout itemAt(0) toolbar lookup (which now resolves to the scroll
    # wrapper). Needles are built at runtime so this assertion cannot match itself.
    source = Path(__file__).read_text(encoding="utf-8")
    assert ("toolbar" + ".hide()") not in source
    assert ("itemAt(0).widget" + "()") not in source


# ── T49-T01 / AC-D18.2 — grow right to the 40%-of-chart-area cap ─────────────

def test_T49_T01_grow_right_to_chart_area_cap(monkeypatch, qapp):
    """T49-T01 / AC-D18.2: the right region grows to the 40% cap; chart narrows."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        assert win.right_dock.isVisible()
        ca_before = win._chart_area_width()
        assert win.right_dock.width() < ca_before

        _drive_right_to_cap(win, qapp)

        ca_after = win._chart_area_width()
        cap = right_dock_max_width(ca_after)
        region_w = win.right_dock.width()

        # The 40% cap binds (within the mandated 1px re-issue tolerance) and is
        # never exceeded during/after the resize.
        assert region_w <= cap + 1, (region_w, cap, ca_after)
        assert abs(region_w - int(ca_after * 0.40)) <= 1, (region_w, ca_after)
        assert region_w > RIGHT_DOCK_MIN_WIDTH
        # The chart area narrowed correspondingly.
        assert ca_after < ca_before
    finally:
        win.close()


# ── T49-T02 / AC-D18.4 — stop at cap and minimum, no overshoot ───────────────

def test_T49_T02_right_stops_at_cap_and_minimum(monkeypatch, qapp):
    """T49-T02 / AC-D18.4: over-cap floors at the cap; below-min floors at 200."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        # Over-cap request, driven to a settled cap before the monotonic
        # sequence. With the toolbar visible a single apply under-converges (the
        # cap denominator is the post-resize chart area), so the request is
        # iterated to its fixed point first; the cap still binds and is never
        # exceeded.
        _drive_right_to_cap(win, qapp)
        ca = win._chart_area_width()
        cap = right_dock_max_width(ca)
        assert win.right_dock.width() <= cap + 1, (win.right_dock.width(), cap)

        # Shrinking sequence decreases monotonically and never below the min.
        prev = win.right_dock.width()
        for requested in (900, 600, 400, 300, 250, 210, 100):
            win._apply_dock_widths(None, requested)
            qapp.processEvents()
            width = win.right_dock.width()
            assert width >= RIGHT_DOCK_MIN_WIDTH, (requested, width)
            assert width <= prev, (requested, width, prev)
            prev = width

        # A below-minimum request floors at exactly the region minimum.
        for requested in (0, 50):
            win._apply_dock_widths(None, requested)
            qapp.processEvents()
            assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH, requested
    finally:
        win.close()


# ── T49-T03 / AC-D18.5 — combined cross-clamp keeps chart >= 400 ─────────────

def test_T49_T03_cross_clamp_keeps_chart_minimum(monkeypatch, qapp):
    """T49-T03 / AC-D18.5: enlarging one dock shrinks the other; chart >= 400."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        ca = win._chart_area_width()
        left_max = watchlist_max_width(ca)
        right_max = right_dock_max_width(ca)

        # Put both docks near their individual maxima against the current area.
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [left_max - 10, right_max - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        left_before = win.watchlist_dock.width()
        right_before = win.right_dock.width()
        assert left_before > 0 and right_before > 0

        # Enlarge the right region: the watchlist must yield so the chart keeps
        # its minimum.
        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH
        assert win.watchlist_dock.width() < left_before, (
            win.watchlist_dock.width(), left_before
        )
        assert win.right_dock.width() >= RIGHT_DOCK_MIN_WIDTH

        # Re-establish both-large and enlarge the watchlist: the right yields.
        ca = win._chart_area_width()
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [watchlist_max_width(ca) - 10, right_dock_max_width(ca) - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        right_before = win.right_dock.width()
        win._apply_dock_widths(10 ** 6, None)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH
        assert win.right_dock.width() < right_before, (
            win.right_dock.width(), right_before
        )
        assert win.watchlist_dock.width() >= 150
    finally:
        win.close()


# ── T49-T04 / AC-D18.1 — full-screen normalize keeps the region on-screen ────

def test_T49_T04_fullscreen_normalize_region_on_screen(monkeypatch, qapp):
    """T49-T04 / AC-D18.1: after a WindowStateChange/resize the region fits."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp, width=1920, height=1080)
    try:
        # Deliver the OS window-state change (no showFullScreen is required);
        # changeEvent defers the normalize via a coalesced single-shot.
        win.changeEvent(QEvent(QEvent.Type.WindowStateChange))
        qapp.processEvents()
        qapp.processEvents()

        rect = win.rect()
        geo = win.right_dock.geometry()
        assert geo.width() > 0
        assert geo.left() >= 0
        assert geo.top() >= 0
        assert geo.right() <= rect.right() + 1, (geo.getRect(), rect.getRect())
        assert geo.bottom() <= rect.bottom() + 1, (geo.getRect(), rect.getRect())

        # A subsequent window resize path also re-clamps without pushing the
        # region off-screen.
        win.resize(1920, 1080)
        qapp.processEvents()
        geo = win.right_dock.geometry()
        rect = win.rect()
        assert geo.width() > 0
        assert geo.right() <= rect.right() + 1
        assert geo.left() >= 0
    finally:
        win.close()


# ── T49-T05 / AC-D18.6 — wide content must not push the region off-screen ────

def test_T49_T05_wide_content_stays_within_cap_and_window(monkeypatch, qapp):
    """T49-T05 / AC-D18.6: wide ladder/portfolio content does not overflow."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp, width=1600, height=900)
    try:
        wide = "123456789012345678901234567890"
        for row in range(8):
            for col in range(win.active_trader.ladder.columnCount()):
                win.active_trader.ladder.setItem(row, col, QTableWidgetItem(wide))
        for row in range(8):
            for col in range(win.portfolio_panel.positions_table.columnCount()):
                win.portfolio_panel.positions_table.setItem(
                    row, col, QTableWidgetItem(wide)
                )
        qapp.processEvents()

        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()

        ca = win._chart_area_width()
        cap = right_dock_max_width(ca)
        geo = win.right_dock.geometry()
        rect = win.rect()

        assert geo.width() > 0
        assert win.right_dock.width() <= cap + 1, (win.right_dock.width(), cap)
        assert geo.right() <= rect.right() + 1, (geo.getRect(), rect.getRect())
        assert geo.left() >= 0 and geo.top() >= 0

        # The content bound keeps the region shrinkable to its minimum too.
        win._apply_dock_widths(None, 0)
        qapp.processEvents()
        assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win.close()


# ── T49-T06 / AC-D18.7 — the right region is not persisted ───────────────────

def test_T49_T06_right_region_not_persisted(monkeypatch, qapp):
    """T49-T06 / AC-D18.7: no right-region QSettings key; default on restart."""
    settings = _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        # Enlarge the region, then close (which persists only the watchlist).
        _drive_right_to_cap(win, qapp)
        assert win.right_dock.width() > RIGHT_DOCK_MIN_WIDTH
        win.close()
        qapp.processEvents()
    finally:
        if win.isVisible():
            win.close()
        qapp.processEvents()

    # No new persistence key was introduced for the right region. System/macOS
    # keys (``com/apple/...``) are not ours; inspect only app-namespace keys.
    keys = [
        k for k in settings.allKeys()
        if not k.lower().startswith(("com/", "org/", "apple"))
    ]
    for key in keys:
        lowered = key.lower()
        assert not any(hint in lowered for hint in _RIGHT_PERSISTENCE_HINTS), key

    # Reconstructing against the same QSettings returns the region to its default.
    win2 = _make_window(monkeypatch, qapp)
    try:
        assert win2._right_dock_width == RIGHT_DOCK_MIN_WIDTH
        assert win2.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win2.close()
        _clean_settings()


# ── T49-T07 — no recursion/jitter between the two regions' rescale ───────────

def test_T49_T07_no_recursion_or_jitter_when_stable(monkeypatch, qapp):
    """T49-T07: repeated applies at fixed geometry are a no-op; guard holds."""
    _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        calls = []
        real_resize_docks = win.resizeDocks

        def _counting_resize_docks(docks, sizes, orientation):
            calls.append((list(sizes), orientation))
            return real_resize_docks(docks, sizes, orientation)

        win.resizeDocks = _counting_resize_docks

        # Converge first.
        _drive_right_to_cap(win, qapp)
        settled = len(calls)
        # Once stable, further applies must not re-issue resizeDocks.
        for _ in range(5):
            win._apply_dock_widths(None, 10 ** 6)
            qapp.processEvents()
        assert len(calls) == settled, (settled, len(calls))

        # A re-entrant apply is suppressed by the guard flag.
        before = len(calls)
        win._applying_dock_widths = True
        try:
            result = win._apply_dock_widths(10 ** 6, 10 ** 6)
        finally:
            win._applying_dock_widths = False
        assert len(calls) == before
        assert result == win._watchlist_width

        # Still functional afterwards (no stack growth / recursion).
        win._apply_dock_widths(None, 0)
        qapp.processEvents()
        assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win.close()
        _clean_settings()
