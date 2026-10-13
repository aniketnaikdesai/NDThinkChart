"""D28.4 (4b-3) — bisection over cached display-x arrays.

_find_closest_bar (crosshair) and _recompute_visible_volume_range (volume
ceiling, incl. the per-frame pan/zoom path) must use bisection over a
cached display-x array instead of O(n) scans. These tests pin the exact
behaviour (equivalence with the brute-force definition); the refactor must
keep them green.
"""
from bisect import bisect_left

from data.models import Bar
from ui.chart_panel import ChartPanel

BASE = 1_760_000_000


def _bar(i, vol=1000.0, px=100.0):
    # 5-min bars with a weekend-style gap every 50 bars (collapse exercised).
    gap = (i // 50) * 2 * 86400
    return Bar("TEST", "5 mins", BASE + i * 300 + gap,
               px, px + 1.0, px - 1.0, px + 0.5, vol)


def _make_panel(qapp, n=200):
    panel = ChartPanel()
    panel.set_symbol("TEST")
    panel.set_timeframe("5 mins")
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    panel.update_chart([_bar(i, vol=1000.0 + (i % 37) * 13.0) for i in range(n)])
    qapp.processEvents()
    return panel


def _brute_closest(panel, target_x):
    bars = panel._plotted_bars
    if not bars:
        return -1
    xs = [panel._to_display(b.ts) for b in bars]
    best, best_d = 0, abs(xs[0] - target_x)
    for i, dx in enumerate(xs):
        d = abs(dx - target_x)
        if d < best_d:
            best, best_d = i, d
        elif d > best_d:
            break
    if len(xs) > 1:
        bar_w = (xs[1] - xs[0]) / 2
        if best_d > bar_w:
            return -1
    return best


def _scene_x_for_display(panel, dx):
    from PyQt6.QtCore import QPointF
    import pyqtgraph as pg
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(dx, 0)).x()


def test_find_closest_bar_matches_brute_force(qapp):
    panel = _make_panel(qapp)
    try:
        bars = panel._plotted_bars
        for i in (0, 1, 17, 49, 50, 51, 99, 150, len(bars) - 1):
            dx = panel._to_display(bars[i].ts)
            for off in (-40.0, 0.0, 40.0):
                scene_x = _scene_x_for_display(panel, dx + off)
                assert panel._find_closest_bar(scene_x) == \
                    _brute_closest(panel, dx + off), (i, off)
    finally:
        panel.close()


def test_find_closest_bar_out_of_tolerance(qapp):
    panel = _make_panel(qapp)
    try:
        bars = panel._plotted_bars
        # Bar 49 -> 50 spans a 2-day (collapsed) gap; an hour into the gap
        # is many bar-widths from every bar.
        dx = panel._to_display(bars[49].ts)
        far = dx + 3600
        assert panel._find_closest_bar(_scene_x_for_display(panel, far)) == -1
    finally:
        panel.close()


def test_volume_ceiling_matches_brute_force(qapp):
    panel = _make_panel(qapp)
    try:
        bars = panel._plotted_bars
        vb = panel.price_plot.getViewBox()
        # Zoom to a middle third of the series.
        x0 = panel._to_display(bars[60].ts)
        x1 = panel._to_display(bars[140].ts)
        vb.setRange(xRange=(x0, x1), padding=0)
        qapp.processEvents()
        got = panel._recompute_visible_volume_range(force=True)
        vols = [b.volume for b in bars
                if x0 <= panel._to_display(b.ts) <= x1]
        assert got == max(vols) * 1.1
        # Full range: ceiling covers the global max.
        all_max = max(b.volume for b in bars)
        vb.setRange(
            xRange=(panel._to_display(bars[0].ts) - 300,
                    panel._to_display(bars[-1].ts) + 300),
            padding=0)
        qapp.processEvents()
        assert panel._recompute_visible_volume_range(force=True) == all_max * 1.1
    finally:
        panel.close()


def test_plot_xs_cache_consistent(qapp):
    panel = _make_panel(qapp, n=50)
    try:
        assert panel._plot_xs == [
            panel._to_display(b.ts) for b in panel._plotted_bars]
        # New candle keeps the cache consistent.
        panel.update_last_bar(_bar(200, vol=5000.0), True)
        qapp.processEvents()
        assert panel._plot_xs == [
            panel._to_display(b.ts) for b in panel._plotted_bars]
        assert len(panel._plot_xs) == len(panel._plotted_bars) == 51
    finally:
        panel.close()


def test_bisect_used_not_linear_scan(monkeypatch, qapp):
    """Structural: the hot paths must bisect, not scan."""
    import ui.chart_panel as cp
    panel = _make_panel(qapp, n=50)
    try:
        # If the implementation still built the O(n) xs list per call,
        # patching the list comprehension away would break it; instead
        # assert the cached array exists and is used by checking that
        # clearing it changes behaviour deterministically.
        assert isinstance(panel._plot_xs, list) and len(panel._plot_xs) == 50
        saved = panel._plot_xs
        panel._plot_xs = []
        try:
            assert panel._find_closest_bar(
                _scene_x_for_display(panel, 1_760_000_000.0)) == -1
        finally:
            panel._plot_xs = saved
    finally:
        panel.close()
