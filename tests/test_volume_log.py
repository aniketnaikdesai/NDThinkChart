import pytest
from ui.chart_panel import ChartPanel, _nice_volume_max
from data.models import Bar

def _bar(ts, vol):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=100, high=101, low=99, close=100, volume=vol)

def test_volume_log_mode(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    # Linear mode expected after D8 revision (was log before)
    assert vb.state["logMode"] == [False, False]
    panel.hide()
    panel.close()

def test_volume_zero_mapped_to_one(qapp, sample_bars):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*60, 0) for i in range(5)]
    bars[2] = _bar(1_700_000_100, 1000)
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    assert vb.state["logMode"] == [False, False]
    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    # Upper bound must match the pinned nice-family value for the max volume:
    # _nice_volume_max(1000) == 1500 (10k floor removed under D8/ESC-015).
    max_vol = max(b.volume for b in bars)
    assert y_range[1] == pytest.approx(_nice_volume_max(max_vol), rel=0.02)
    # Pin the concrete family value too so a drift in max_vol/bars is visible.
    assert _nice_volume_max(max_vol) == pytest.approx(1_500, rel=0.02)
    panel.hide()
    panel.close()

def test_volume_autorange_upper(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*60, 1000 + i*100) for i in range(10)]
    max_vol = max(b.volume for b in bars)
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    assert vb.state["logMode"] == [False, False]
    y_range = vb.viewRange()[1]
    expected_nice = _nice_volume_max(max_vol)
    assert y_range[0] == pytest.approx(0, abs=1)
    assert y_range[1] == pytest.approx(expected_nice, rel=0.02)
    panel.hide()
    panel.close()
