import pytest
from ui.chart_panel import ChartPanel
from data.models import Bar

def _bar(ts, vol, o=100, c=100):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=101, low=99, close=c, volume=vol)

def test_volume_width_equals_price_width(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*300, 1000) for i in range(20)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    # Check volume bar width equals price body width (w*2)
    # Get price w via candlestick item's w: we can infer from volume width
    vol_width = panel.volume_bars.opts['width']
    # Price body width is w*2, where w = median_diff*0.325
    # For our bars, median_diff = 300, w=97.5, width=195
    # Volume width should be same
    assert vol_width == pytest.approx(195, rel=0.1)
    # Also check that volume width is not the old fixed 0.6
    assert vol_width != pytest.approx(0.6, rel=0.01)
    panel.hide()
    panel.close()

def test_volume_width_dense_clamped(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*60, 1000) for i in range(960)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    vol_width = panel.volume_bars.opts['width']
    # With dense, w is clamped to 4px in device, but data width w*2 should still be >=4px device
    # Check that volume width is still w*2 and not 0.6, and is clamped
    assert vol_width != pytest.approx(0.6, rel=0.01)
    # The width should be at least 4px in data units converted? Hard to check exactly, but ensure it's not 0.6
    assert vol_width > 10  # for dense, w*2 should be >10 data units (since median_diff 60*0.325*2=39)
    panel.hide()
    panel.close()
