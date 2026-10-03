"""T50 / D18 Phase 5 — offscreen end-to-end verification of D17/D18 dock geometry.

Boots a **real** ``ui.main_window.MainWindow`` on the offscreen Qt platform
(``IBApiClient.connect`` monkeypatched so the TWS-seeking managers never open a
socket, exactly as the D17/D18-region suites do) and verifies the *rendered*
D18 geometry end-to-end rather than the pure helpers:

* AC-D18.1 — the single right region is fully on-screen in a full-screen-sized
  window, with a positive width, without manual repositioning;
* AC-D18.2 / AC-D18.4 — the rendered region grows to the ``floor(0.40 ×
  chart_area)`` cap and shrinks to ``RIGHT_DOCK_MIN_WIDTH``, with the chart area
  moving inversely;
* AC-D18.3 — the Active Trader ladder section and the Portfolio section render at
  equal width and each equals the region content width;
* AC-D18.5 — with both docks near their maxima, enlarging one keeps the rendered
  chart area ``>= 400px`` and shrinks the other;
* AC-D18.6 — wide ladder/portfolio content cannot push the region off-screen or
  past the cap (content scrolls/clips internally);
* AC-D18.7 — the right region's width/visibility returns to its default on
  restart and no right-region QSettings key is written.

Everything is parameterized over at least two window sizes plus a small-display
case (see ``_WINDOW_SIZES``).

Geometry / tolerance notes
--------------------------
This module deliberately mirrors the deterministic ``_make_window`` harness used
by ``tests/test_dock_widths_d18_impl.py``: the offscreen toolbar's
``minimumSizeHint`` is very wide and pins the central widget (masking the
behaviour under test), so the toolbar is hidden to give the chart area a real,
adjustable width. The single right region is **kept visible** — D18 is about the
region, so hiding it would test the wrong path.

``MainWindow._apply_dock_widths`` only re-issues ``resizeDocks`` when a computed
width differs from the current width by more than 1px (an explicit acceptance
criterion), so a residual of at most 1px is expected throughout and asserted
with ``+1``.

The 40% cap is measured against the **post-resize** chart area (the width committed
by ``MainWindow._plan_dock_widths`` is a fixed point of
``right == floor(0.40 × (invariant − left − right))``). On a window wide enough
for the cap to be feasible the fixed point equals ``floor(0.40 × chart_area)`` to
within 1px; on the small-display case the window is *infeasible* (both dock
minimums already consume the chart-minimum budget) and the region simply holds at
``RIGHT_DOCK_MIN_WIDTH`` — those cases assert the demanding invariants
(on-screen, positive, chart ``>= 400``, never above the cap) instead of a cap
equality that the window cannot reach. This is the honest reading of AC-D18.2:
"stops at floor(0.40 × chart_area)" where that cap is reachable.
"""

import pytest
from PyQt6.QtCore import QEvent, QSettings, Qt
from PyQt6.QtWidgets import QDockWidget, QTableWidgetItem

from ui.dock_layout import (
    CHART_MIN_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    right_dock_max_width,
    watchlist_max_width,
)
from ui.watchlist_panel import WATCHLIST_WIDTH_KEY

_QSETTINGS_ORG = "NDThinkChart"
_QSETTINGS_APP = "NDThinkChart"

#: Keys a naive right-region persistence would introduce (AC-D18.7). None may be
#: written; the region is in-memory only, matching D10's volume-toggle precedent.
_RIGHT_PERSISTENCE_HINTS = ("right", "active_trader", "portfolio", "right_dock")

#: Rendered window sizes exercised end-to-end. The first two are large enough for
#: the 40% cap to be reachable (a "full-screen-sized" case and a 1600×900 case);
#: the last is a small-display case where the window is infeasible and the region
#: holds at its minimum. At least two sizes + a small display, per the task.
_WINDOW_SIZES = [(1920, 1080), (1600, 900), (1100, 700)]

#: Sizes on which the 40% cap is actually reachable, so it can be asserted as an
#: equality (within the 1px re-issue tolerance). The small case is excluded.
_CAP_REACHABLE_SIZES = [(1920, 1080), (1600, 900)]

#: Sizes on which the window is infeasible: both dock minimums already exhaust the
#: ``chart_area − CHART_MIN_WIDTH`` budget, so the region cannot grow past its min.
_INFEASIBLE_SIZES = [(1100, 700)]


def _clean_settings() -> QSettings:
    """Remove our own watchlist key so each test starts from a clean slate."""
    settings = QSettings(_QSETTINGS_ORG, _QSETTINGS_APP)
    settings.remove(WATCHLIST_WIDTH_KEY)
    settings.sync()
    return settings


def _make_window(monkeypatch, qapp, width: int = 1600, height: int = 900):
    """Build a shown ``MainWindow`` that never touches TWS, right region visible.

    ``IBApiClient.connect`` is monkeypatched to a no-op, which is what keeps the
    market-data / realtime / depth managers (all built around the client) from
    opening a socket in the offscreen harness. The offscreen toolbar is hidden so
    the dock geometry can settle to the requested window size.
    """
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()

    # Relax the offscreen toolbar constraint so the dock geometry can settle.
    central_layout = win.centralWidget().layout()
    if central_layout is not None and central_layout.count() > 0:
        toolbar = central_layout.itemAt(0).widget()
        if toolbar is not None:
            toolbar.hide()
    qapp.processEvents()
    win.resize(width, height)
    qapp.processEvents()
    return win


def _drive_right_to_cap(win, qapp, iterations: int = 14) -> None:
    """Repeatedly request an oversized right region until the clamp settles."""
    for _ in range(iterations):
        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()


def _drive_right_below_min(win, qapp, iterations: int = 6) -> None:
    """Repeatedly request a below-minimum right region until it floors."""
    for _ in range(iterations):
        win._apply_dock_widths(None, 0)
        qapp.processEvents()


def _assert_on_screen(win, tol: int = 1):
    """Assert the rendered right region is inside the window rect, width > 0."""
    rect = win.rect()
    geo = win.right_dock.geometry()
    assert geo.width() > 0, geo.getRect()
    assert geo.left() >= 0, geo.getRect()
    assert geo.top() >= 0, geo.getRect()
    assert geo.right() <= rect.right() + tol, (geo.getRect(), rect.getRect())
    assert geo.bottom() <= rect.bottom() + tol, (geo.getRect(), rect.getRect())
    return geo, rect


# ── T50-T01 / AC-D18.1 — full-screen-sized region fully on-screen ────────────

@pytest.mark.parametrize("size", _WINDOW_SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
def test_T50_T01_fullscreen_region_on_screen(monkeypatch, qapp, size):
    """T50-T01 / AC-D18.1: boot + show + render leaves the region on-screen."""
    _clean_settings()
    width, height = size
    win = _make_window(monkeypatch, qapp, width=width, height=height)
    try:
        # The single row region exists and rendered visible.
        assert win.right_dock.isVisible()
        assert win.right_dock.objectName() == "Active Trader"

        # Without any manual repositioning, the rendered region lies within the
        # window rect with a positive width.
        _assert_on_screen(win)

        # The WindowStateChange normalize (full-screen path) must keep it there.
        win.changeEvent(QEvent(QEvent.Type.WindowStateChange))
        qapp.processEvents()
        qapp.processEvents()
        _assert_on_screen(win)

        # And a subsequent resize back to the same size also re-clamps on-screen.
        win.resize(width, height)
        qapp.processEvents()
        _assert_on_screen(win)
    finally:
        win.close()
        _clean_settings()


# ── T50-T02 / AC-D18.2 + AC-D18.4 — cap and minimum on the rendered path ─────

@pytest.mark.parametrize("size", _WINDOW_SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
def test_T50_T02_rendered_cap_and_minimum(monkeypatch, qapp, size):
    """T50-T02 / AC-D18.2/04: overshoot stops at the cap; undershoot at the min."""
    _clean_settings()
    width, height = size
    win = _make_window(monkeypatch, qapp, width=width, height=height)
    try:
        # ── Overshoot: never exceeds the 40% chart-area cap ──────────────────
        _drive_right_to_cap(win, qapp)
        ca_after = win._chart_area_width()
        cap = right_dock_max_width(ca_after)
        region_w = win.right_dock.width()

        assert region_w <= cap + 1, (region_w, cap, ca_after)
        assert region_w >= RIGHT_DOCK_MIN_WIDTH, (region_w, ca_after)
        # The rendered fixed point is self-consistent with the chart area it
        # leaves behind (the implementation's stated contract).
        plan_left, plan_right = win._plan_dock_widths(
            ca_after, win.watchlist_dock.width(), win.right_dock.width()
        )
        assert region_w == plan_right, (region_w, plan_right)

        if size in _CAP_REACHABLE_SIZES:
            # The cap actually binds: within the 1px re-issue tolerance of the
            # floor(0.40 × chart_area) rule on the rendered (post-resize) area.
            assert abs(region_w - int(ca_after * 0.40)) <= 1, (region_w, ca_after)
            assert region_w > RIGHT_DOCK_MIN_WIDTH
            assert ca_after >= CHART_MIN_WIDTH

        if size in _INFEASIBLE_SIZES:
            # The window cannot support the cap (both dock minimums alone exceed
            # the chart-minimum budget): the region holds at its minimum and the
            # chart keeps its minimum — never below either dock's floor.
            assert region_w == RIGHT_DOCK_MIN_WIDTH, (region_w, ca_after)
            assert ca_after >= CHART_MIN_WIDTH

        # ── Shrink below the minimum: floors at exactly RIGHT_DOCK_MIN_WIDTH ──
        # Grow first so the decrease is observable, then undershoot.
        _drive_right_to_cap(win, qapp)
        grown = win.right_dock.width()
        chart_grown = win._chart_area_width()
        _drive_right_below_min(win, qapp)
        shrunk = win.right_dock.width()
        chart_shrunk = win._chart_area_width()

        assert shrunk == RIGHT_DOCK_MIN_WIDTH, (shrunk,)
        assert shrunk <= grown + 1, (shrunk, grown)
        # The chart area moves inversely: shrinking the dock grows the chart.
        assert chart_shrunk >= chart_grown, (chart_shrunk, chart_grown)

        # Below-minimum requests cannot go under the floor even after repeats.
        for _ in range(3):
            win._apply_dock_widths(None, 0)
            qapp.processEvents()
            assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win.close()
        _clean_settings()


# ── T50-T03 / AC-D18.3 — equal-width stacked sections ───────────────────────

@pytest.mark.parametrize("size", _WINDOW_SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
def test_T50_T03_sections_equal_width(monkeypatch, qapp, size):
    """T50-T03 / AC-D18.3: ladder and portfolio render equal, at the content width."""
    _clean_settings()
    width, height = size
    win = _make_window(monkeypatch, qapp, width=width, height=height)
    try:
        for label, drive in (
            ("default", lambda: None),
            ("at-cap", lambda: _drive_right_to_cap(win, qapp)),
            ("at-min", lambda: _drive_right_below_min(win, qapp)),
        ):
            drive()
            qapp.processEvents()

            trader_w = win.active_trader.width()
            portfolio_w = win.portfolio_panel.width()
            content_w = win.right_dock_container.width()

            assert abs(trader_w - portfolio_w) <= 1, (label, trader_w, portfolio_w)
            # Each equals the region content width (equal by construction).
            assert abs(trader_w - content_w) <= 1, (label, trader_w, content_w)
            assert abs(portfolio_w - content_w) <= 1, (label, portfolio_w, content_w)
            assert content_w > 0
    finally:
        win.close()
        _clean_settings()


# ── T50-T04 / AC-D18.5 — cross-clamp keeps chart >= 400, shrinks the other ──

@pytest.mark.parametrize("size", [(1920, 1080), (1600, 900)], ids=lambda s: f"{s[0]}x{s[1]}")
def test_T50_T04_cross_clamp_keeps_chart_minimum(monkeypatch, qapp, size):
    """T50-T04 / AC-D18.5: enlarging one rendered dock shrinks the other."""
    _clean_settings()
    width, height = size
    win = _make_window(monkeypatch, qapp, width=width, height=height)
    try:
        # ── Put both docks near their individual maxima ─────────────────────
        ca = win._chart_area_width()
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [watchlist_max_width(ca) - 10, right_dock_max_width(ca) - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        left_before = win.watchlist_dock.width()
        right_before = win.right_dock.width()
        assert left_before > 0 and right_before > 0

        # ── Enlarge the right region through the live apply path: the
        # watchlist must yield so the chart keeps its minimum. ──────────────
        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH, (
            win._chart_area_width(), size,
        )
        assert win.watchlist_dock.width() < left_before, (
            win.watchlist_dock.width(), left_before,
        )
        assert win.right_dock.width() >= RIGHT_DOCK_MIN_WIDTH
        _assert_on_screen(win)

        # ── Re-establish both-large and enlarge the watchlist: the right yields. ─
        ca = win._chart_area_width()
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [watchlist_max_width(ca) - 10, right_dock_max_width(ca) - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        right_before = win.right_dock.width()
        assert right_before > RIGHT_DOCK_MIN_WIDTH, right_before

        win._apply_dock_widths(10 ** 6, None)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH, (
            win._chart_area_width(), size,
        )
        assert win.right_dock.width() < right_before, (
            win.right_dock.width(), right_before,
        )
        assert win.watchlist_dock.width() >= 150
        _assert_on_screen(win)
    finally:
        win.close()
        _clean_settings()


# ── T50-T05 / AC-D18.6 — wide content cannot overflow the region ────────────

@pytest.mark.parametrize("size", _WINDOW_SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
def test_T50_T05_wide_content_stays_in_cap_and_window(monkeypatch, qapp, size):
    """T50-T05 / AC-D18.6: wide ladder/portfolio content stays on-screen under cap."""
    _clean_settings()
    width, height = size
    win = _make_window(monkeypatch, qapp, width=width, height=height)
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

        # Enlarge the region against wide content and assert the content did not
        # push it off-screen or past the cap (it scrolls/clips internally).
        _drive_right_to_cap(win, qapp)
        ca = win._chart_area_width()
        cap = right_dock_max_width(ca)
        geo, rect = _assert_on_screen(win)
        assert win.right_dock.width() <= cap + 1, (win.right_dock.width(), cap)
        assert geo.right() <= rect.right() + 1, (geo.getRect(), rect.getRect())

        # The content bound also keeps the region shrinkable to its minimum.
        _drive_right_below_min(win, qapp)
        assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
        _assert_on_screen(win)
    finally:
        win.close()
        _clean_settings()


# ── T50-T06 / AC-D18.7 — restart returns to default; nothing persisted ──────

def test_T50_T06_restart_returns_default_not_persisted(monkeypatch, qapp):
    """T50-T06 / AC-D18.7: no right-region QSettings key; default on restart."""
    settings = _clean_settings()
    win = _make_window(monkeypatch, qapp)
    try:
        # Enlarge the region, then close (which persists only the watchlist).
        _drive_right_to_cap(win, qapp)
        assert win.right_dock.width() > RIGHT_DOCK_MIN_WIDTH
        assert win._right_dock_width > RIGHT_DOCK_MIN_WIDTH
        win.close()
        qapp.processEvents()
    finally:
        if win.isVisible():
            win.close()
        qapp.processEvents()

    # No new persistence key was introduced for the right region. System/macOS
    # keys (``com/apple/...``, ``NS...``, ``AK...``) are not ours; inspect only
    # app-namespace keys.
    keys = [
        k for k in settings.allKeys()
        if not k.lower().startswith(("com/", "org/", "apple", "ns", "_ak", "ak"))
    ]
    for key in keys:
        lowered = key.lower()
        assert not any(hint in lowered for hint in _RIGHT_PERSISTENCE_HINTS), key

    # Reconstructing against the same QSettings returns the region to its default.
    win2 = _make_window(monkeypatch, qapp)
    try:
        assert win2._right_dock_width == RIGHT_DOCK_MIN_WIDTH
        assert win2.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
        _assert_on_screen(win2)
    finally:
        win2.close()
        _clean_settings()
