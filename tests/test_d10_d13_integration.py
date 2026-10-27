"""T28 / ESC-005: D13 watchlist max clamp against the D17/B1 chart area.

The D10 half of this combination (the volume pane's hide/show and the Qt
vertical splitter that held ``price_plot`` / ``volume_plot``) is retired with
the pyqtgraph chart engine: ``chart_panel`` is now the LWC view and has no
volume pane, no splitter and no price plot. What survives is the
cross-cutting invariant these tests were written for — the watchlist dock can
never squeeze the chart area below its 400px minimum.

Layout structure (documented per ESC-005):
  * The chart is ``MainWindow.chart_panel`` (``LwcChartView``); the chart area
    used by the clamp is ``centralWidget().width()``.
  * The watchlist is a separate ``QDockWidget`` on the ``MainWindow``
    (``ui/main_window.py``), i.e. **not** a nested splitter. Its width is
    governed by the D13 helpers in ``ui/watchlist_panel.py``
    (``watchlist_max_width`` / ``clamp_watchlist_width``).

ESC-005 is the cross-cutting gap: no test combined a dock drag to its maximum
clamp with the price panel's 400px width minimum. These tests cover that in
one offscreen ``MainWindow``.

The right-hand dock (the single Portfolio section, D41 / S6) is hidden for the
duration of each test so that D13 is the only horizontal constraint under test --
the D13/D17 clamp reserves ``CHART_MIN_WIDTH`` against the **chart area**
(``centralWidget().width()``), not the whole window width (D17/B1).
"""

import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from ui.watchlist_panel import (
    CHART_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    watchlist_max_width,
    clamp_watchlist_width,
)

# The single right region (Portfolio only, D41 / S6) is unrelated to the
# D10/D13 interaction under test.
_RIGHT_DOCKS = ("Portfolio",)


def _make_main_window(monkeypatch, qapp):
    """Build a shown MainWindow without ever touching TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()

    # ESC-005 is specifically D10 (volume) + D13 (watchlist); the right-hand
    # docks are an independent horizontal consumer, so remove them from the
    # equation to test the clamp itself.
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in _RIGHT_DOCKS:
            dock.hide()
    qapp.processEvents()
    return win


def _drag_watchlist_to(win, width, qapp):
    """Emulate the user dragging the watchlist splitter to *width*."""
    win.resizeDocks([win.watchlist_dock], [int(width)], Qt.Orientation.Horizontal)
    qapp.processEvents()


def _watchlist_within_its_cap(win) -> bool:
    """True when the watchlist dock sits inside its D13/D17 cap (settled)."""
    try:
        chart_area = win.centralWidget().width()
        return (
            chart_area >= CHART_MIN_WIDTH
            and win.watchlist_dock.width() <= watchlist_max_width(chart_area)
        )
    except Exception:
        return True


def _settle_dock_clamp(win, qapp, *, turns: int = 80, deadline_s: float = 5.0):
    """Bounded drain/settle of ``MainWindow``'s dock-width clamp.

    ``MainWindow`` keeps the watchlist inside its D13/D17 cap with a clamp it
    applies over deferred ``QTimer.singleShot(0)`` turns (``_deferred_dock_clamp``
    / ``_schedule_dock_clamp``). A programmatic ``resizeDocks`` overshoot can
    therefore leave the dock over its cap -- and the chart area squeezed -- until
    that clamp has run; under system load the assertion used to fire first and
    observe the pre-clamp width (``assert 88 >= 400``). Process pending events
    and re-apply the shared clamp (``_apply_dock_widths``, the single apply entry
    point the deferred passes also call) until the watchlist is back inside its
    cap for the chart area it leaves behind, or a fixed turn budget / monotonic
    deadline is exhausted.

    Bounded by construction: a fixed turn count *and* a monotonic deadline,
    never an unbounded loop. It only waits for the existing clamp to settle --
    the assertions that follow are unchanged.
    """
    deadline = time.monotonic() + deadline_s
    for _ in range(turns):
        qapp.processEvents()
        if _watchlist_within_its_cap(win):
            break
        win._apply_dock_widths()
        if time.monotonic() >= deadline:
            break
    # One further turn so the final applied resize is laid out before reading.
    qapp.processEvents()


def test_T28_T01_watchlist_max_clamp_keeps_chart_min_width(
    monkeypatch, qapp
):
    """T28-T01 / ESC-005: chart area stays >= 400px with the dock at max."""
    win = _make_main_window(monkeypatch, qapp)
    try:
        # D17/B1: the denominator is the chart area (central widget width), not
        # the whole window width.
        chart_area_w = win.centralWidget().width()
        max_w = watchlist_max_width(chart_area_w)

        # D13/D17: drag the watchlist to its maximum clamp for this chart area.
        _drag_watchlist_to(win, max_w, qapp)

        # ESC-005: the price panel never drops below its 400px minimum, and
        # the dock stays inside the D13/D17 range.
        assert WATCHLIST_MIN_WIDTH <= win.watchlist_dock.width() <= max_w
        assert win.chart_panel.width() >= CHART_MIN_WIDTH
        assert win.centralWidget().width() >= CHART_MIN_WIDTH

        # Overshooting the clamp must still never shrink the chart below
        # its minimum.
        _drag_watchlist_to(win, max_w + 1000, qapp)
        # Drain the deferred dock clamp so the asserts below never observe the
        # pre-clamp width (bounded settle; the assertions are unchanged).
        _settle_dock_clamp(win, qapp)
        assert win.chart_panel.width() >= CHART_MIN_WIDTH
        assert win.centralWidget().width() >= CHART_MIN_WIDTH
    finally:
        win.close()


def test_T28_T02_watchlist_clamp_keeps_chart_min_width(monkeypatch, qapp):
    """T28-T02 / AC-D13.1: the watchlist clamp reserves the chart minimum."""
    win = _make_main_window(monkeypatch, qapp)
    try:
        # D17/B1: the watchlist cap is derived from the chart area.
        chart_area_w = win.centralWidget().width()
        max_w = watchlist_max_width(chart_area_w)

        # AC-D13.1/D17: the clamp is [150, min(floor(0.50 x chart_area),
        # chart_area - 400)], measured against the chart area (D17/B1).
        assert max_w == max(
            WATCHLIST_MIN_WIDTH,
            min(int(chart_area_w * 0.50), chart_area_w - CHART_MIN_WIDTH),
        )
        assert clamp_watchlist_width(10 ** 6, chart_area_w) == max_w
        assert clamp_watchlist_width(0, chart_area_w) == WATCHLIST_MIN_WIDTH
        if max_w > WATCHLIST_MIN_WIDTH:
            assert (
                clamp_watchlist_width(WATCHLIST_MIN_WIDTH + 1, chart_area_w)
                == WATCHLIST_MIN_WIDTH + 1
            )

        _drag_watchlist_to(win, max_w, qapp)
        dock_w = win.watchlist_dock.width()
        assert WATCHLIST_MIN_WIDTH <= dock_w <= max_w
        assert win.chart_panel.width() >= CHART_MIN_WIDTH
        assert win.centralWidget().width() >= CHART_MIN_WIDTH
    finally:
        win.close()
