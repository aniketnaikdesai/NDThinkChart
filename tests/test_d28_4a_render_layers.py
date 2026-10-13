"""D28.4 (4b-1) — static-history + live-bar render layers.

A 5-second tick must NOT regenerate the full candle QPicture: the static
layer holds closed bars (regenerated only when the series changes) and a
dedicated live layer holds the forming bar. The candle half-width is
cached at full-rebuild time, not recomputed per tick.
"""
from data.models import Bar
from ui.chart_panel import ChartPanel

BASE = 1_760_000_000


def _bar(i, spacing=300, px=100.0):
    return Bar("TEST", "5 mins", BASE + i * spacing,
               px, px + 1.0, px - 1.0, px + 0.5, 1000.0)


def _make_panel(qapp, n=50):
    panel = ChartPanel()
    panel.set_timeframe("5 mins")
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    panel.update_chart([_bar(i) for i in range(n)])
    qapp.processEvents()
    # __init__ + update_chart each generate once; reset for the assertions.
    panel.candlestick.regen_count = 0
    panel.live_candle.regen_count = 0
    return panel


def test_static_layer_not_regenerated_on_forming_ticks(qapp):
    """20 forming-bar ticks: static QPicture regen count stays 0."""
    panel = _make_panel(qapp)
    try:
        for i in range(20):
            b = _bar(49, px=100.0 + i * 0.1)
            panel.update_last_bar(b, False)
        qapp.processEvents()
        assert panel.candlestick.regen_count == 0, \
            "forming-bar ticks must not regenerate the static history picture"
        assert panel.live_candle.regen_count == 20, \
            "each forming tick must refresh only the live layer"
    finally:
        panel.close()


def test_new_candle_commits_to_static_once(qapp):
    """A new candle regenerates the static layer exactly once."""
    panel = _make_panel(qapp)
    try:
        new = _bar(50, px=110.0)
        panel.update_last_bar(new, True)
        qapp.processEvents()
        assert panel.candlestick.regen_count == 1
        # The live layer now shows the new forming bar.
        assert panel.live_candle._raw_data[-1][0] == panel._to_display(new.ts)
        # And the committed bar is in the static layer.
        assert panel.candlestick._raw_data[-1][0] == panel._to_display(_bar(49).ts)
    finally:
        panel.close()


def test_width_cache_reused_across_ticks(qapp):
    """The candle half-width is computed at full rebuild, reused per tick."""
    panel = _make_panel(qapp)
    try:
        w0 = panel._candle_half_width
        assert w0 > 0
        for i in range(5):
            panel.update_last_bar(_bar(49, px=100.0 + i), False)
        assert panel._candle_half_width == w0, \
            "forming ticks must reuse the cached width"
        # A series change (new candle) recomputes the cache.
        panel.update_last_bar(_bar(50, px=110.0), True)
        assert panel._candle_half_width > 0
    finally:
        panel.close()


def test_live_layer_matches_static_render(qapp):
    """Live candle data == what the static layer would draw for the last bar."""
    panel = _make_panel(qapp, n=10)
    try:
        last = panel._plotted_bars[-1]
        dx = panel._to_display(last.ts)
        live = panel.live_candle._raw_data
        assert len(live) == 1
        assert live[0] == (dx, last.open, last.high, last.low, last.close)
        # Mode changes propagate to both layers.
        from ui.candlestick_item import ChartMode
        panel.set_chart_mode(ChartMode.LINE)
        assert panel.live_candle._mode == ChartMode.LINE
        assert panel.candlestick._mode == ChartMode.LINE
    finally:
        panel.close()


def test_empty_chart_live_bar_starts_series(qapp):
    """update_last_bar on an empty chart still works (pop-out, no history)."""
    panel = ChartPanel()
    panel.set_timeframe("5 mins")
    panel.resize(900, 600)
    panel.show()
    try:
        b = _bar(0)
        panel.update_last_bar(b, True)
        qapp.processEvents()
        assert panel.live_candle.regen_count >= 1
        assert len(panel.live_candle._raw_data) == 1
    finally:
        panel.close()
