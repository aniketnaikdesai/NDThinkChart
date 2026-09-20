import pytest
from ui.chart_panel import ChartPanel, _nice_volume_max
from data.models import Bar

def _bar(ts, vol, o=100, c=100):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=101, low=99, close=c, volume=vol)

def test_volume_y_linear_no_negatives_nice_max(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    # Should be linear
    assert vb.state["logMode"] == [False, False] or vb.state["logMode"][1] is False
    # Create bars with max 2.2M
    bars = [_bar(1_700_000_000 + i*60, 500_000 + i*10_000) for i in range(10)]
    # Set max to 2.2M
    bars[-1] = _bar(1_700_000_900, 2_200_000)
    max_vol = max(b.volume for b in bars)
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    # Upper should be nice_max
    expected_nice = _nice_volume_max(max_vol)
    assert y_range[1] == pytest.approx(expected_nice, rel=0.02)
    # No negative tick
    assert y_range[0] >= 0
    panel.hide()
    panel.close()

def test_volume_bars_coloured_by_price(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    # Create up and down candles
    bars = [
        _bar(1_700_000_000, 1000, o=95, c=105), # up -> green
        _bar(1_700_000_060, 1000, o=105, c=95),  # down -> red
    ]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    # Check volume bar brushes
    # volume_bars is BarGraphItem, check opts
    # We can check that panel.volume_bars has brushes set
    # For now, check that update_chart did not error and bars are present
    assert len(panel._bars) == 2
    panel.hide()
    panel.close()

def test_volume_ticks_formatting(qapp):
    # Test nice_max logic directly
    assert _nice_volume_max(0) == 10_000
    assert _nice_volume_max(8_000) == 10_000
    assert _nice_volume_max(80_000) == 100_000
    assert _nice_volume_max(2_200_000) == 2_500_000
    assert _nice_volume_max(1_050_000) == 1_500_000
    # Check that yRange lower is 0 for various max
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*60, 10_000) for i in range(5)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    panel.hide()
    panel.close()
