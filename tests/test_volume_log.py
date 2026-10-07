import pytest
from ui.chart_panel import ChartPanel
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
    # D21.2 ceiling: 1.10 x the max volume of the bars in the visible x-range
    # (the D8 whole-list nice-max ceiling is superseded).
    max_vol = max(b.volume for b in bars)
    assert y_range[1] == pytest.approx(max_vol * 1.1, rel=0.02)
    # Pin the concrete value too so a drift in max_vol/bars is visible.
    assert max_vol * 1.1 == pytest.approx(1_100, rel=0.02)
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
    expected_ceiling = max_vol * 1.1
    assert y_range[0] == pytest.approx(0, abs=1)
    assert y_range[1] == pytest.approx(expected_ceiling, rel=0.02)
    panel.hide()
    panel.close()
