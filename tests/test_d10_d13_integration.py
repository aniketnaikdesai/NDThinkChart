"""T28 / ESC-005: combined D10 (volume hide) + D13 (watchlist max clamp).

Layout structure (documented per ESC-005):
  * ``ChartPanel`` owns a single vertical ``QSplitter`` holding
    ``[price_plot, volume_plot, osc_plot]`` (``ui/chart_panel.py``). D10's
    ``_on_volume_toggled`` only hides the volume plot and calls
    ``QSplitter.refresh()`` on that vertical splitter.
  * The watchlist is a separate ``QDockWidget`` on the ``MainWindow``
    (``ui/main_window.py``), i.e. **not** a nested splitter. Its width is
    governed by the D13 helpers in ``ui/watchlist_panel.py``
    (``watchlist_max_width`` / ``clamp_watchlist_width``).

ESC-005 is the cross-cutting gap: no test combined a volume hide with a
max-clamp watchlist drag and asserted the price panel keeps its 400px width
minimum. These tests cover that combination in one offscreen ``MainWindow``.

The right-hand docks (Active Trader / Portfolio) are hidden for the duration
of each test so that D10/D13 is the only horizontal constraint under test --
the D13/D17 clamp reserves ``CHART_MIN_WIDTH`` against the **chart area**
(``centralWidget().width()``), not the whole window width (D17/B1).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from ui.watchlist_panel import (
    CHART_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    watchlist_max_width,
    clamp_watchlist_width,
)

# The single right region (Active Trader ladder + Portfolio, D18 Phase 3) is
# unrelated to the D10/D13 interaction under test.
_RIGHT_DOCKS = ("Active Trader",)


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


def test_T28_T01_volume_hidden_and_watchlist_max_clamp_keeps_price_panel(
    monkeypatch, qapp
):
    """T28-T01 / ESC-005: chart stays >= 400px with volume hidden + max dock."""
    win = _make_main_window(monkeypatch, qapp)
    try:
        cp = win.chart_panel

        # D10: hide the volume panel.
        cp._volume_toggle.setChecked(False)
        qapp.processEvents()
        assert not cp.volume_plot.isVisible()
        assert not cp.volume_plot.getAxis('right').isVisible()

        # D17/B1: the denominator is the chart area (central widget width), not
        # the whole window width.
        chart_area_w = win.centralWidget().width()
        max_w = watchlist_max_width(chart_area_w)

        # D13/D17: drag the watchlist to its maximum clamp for this chart area.
        _drag_watchlist_to(win, max_w, qapp)

        # ESC-005: the price panel never drops below its 400px minimum, and
        # the dock stays inside the D13/D17 range.
        assert WATCHLIST_MIN_WIDTH <= win.watchlist_dock.width() <= max_w
        assert cp.width() >= CHART_MIN_WIDTH
        assert cp.price_plot.width() >= CHART_MIN_WIDTH
        assert win.centralWidget().width() >= CHART_MIN_WIDTH
        # The clamp reserves CHART_MIN_WIDTH against the chart area (D17/B1).
        assert win.centralWidget().width() >= CHART_MIN_WIDTH

        # Overshooting the clamp must still never shrink the price panel below
        # its minimum.
        _drag_watchlist_to(win, max_w + 1000, qapp)
        assert cp.width() >= CHART_MIN_WIDTH
        assert cp.price_plot.width() >= CHART_MIN_WIDTH
    finally:
        win.close()


def test_T28_T02_watchlist_clamp_with_volume_hidden_and_splitter_restored(
    monkeypatch, qapp
):
    """T28-T02 / AC-D13.1 + AC-D10.1: clamp while hidden, splitter restores."""
    win = _make_main_window(monkeypatch, qapp)
    try:
        cp = win.chart_panel
        # D17/B1: the watchlist cap is derived from the chart area.
        chart_area_w = win.centralWidget().width()
        max_w = watchlist_max_width(chart_area_w)

        # Baseline while the volume panel is visible.
        assert cp.volume_plot.isVisible()
        sizes_visible = cp._splitter.sizes()

        # D10: hide volume, then drag the watchlist to its max clamp.
        cp._volume_toggle.setChecked(False)
        qapp.processEvents()
        assert not cp.volume_plot.isVisible()

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
        assert cp.width() >= CHART_MIN_WIDTH

        # AC-D10.1: the hide/show cycle restores the splitter correctly.
        cp._volume_toggle.setChecked(True)
        qapp.processEvents()
        assert cp.volume_plot.isVisible()
        assert cp._splitter.sizes() == sizes_visible
    finally:
        win.close()
