import pytest
from ui.chart_panel import ChartPanel

@pytest.fixture
def panel_zoom(qapp, sample_bars):
    p = ChartPanel()
    p.resize(900,600)
    p.show()
    p.set_symbol("TEST")
    p.update_chart(sample_bars)
    qapp.processEvents()
    yield p
    p.hide()
    p.close()

def test_zoom_in_out_around_centre(panel_zoom, qapp):
    vb = panel_zoom.price_plot.getViewBox()
    x_range_before, y_range_before = vb.viewRange()
    x_center_before = (x_range_before[0]+x_range_before[1])/2
    y_center_before = (y_range_before[0]+y_range_before[1])/2
    x_width_before = x_range_before[1]-x_range_before[0]
    y_width_before = y_range_before[1]-y_range_before[0]
    # zoom in
    panel_zoom._zoom_by(0.8)
    qapp.processEvents()
    x_range, y_range = vb.viewRange()
    x_center = (x_range[0]+x_range[1])/2
    y_center = (y_range[0]+y_range[1])/2
    assert x_range[1]-x_range[0] == pytest.approx(x_width_before*0.8, rel=0.02)
    assert y_range[1]-y_range[0] == pytest.approx(y_width_before*0.8, rel=0.02)
    assert x_center == pytest.approx(x_center_before, rel=0.01)
    assert y_center == pytest.approx(y_center_before, rel=0.01)
    # zoom out
    panel_zoom._zoom_by(1.25)
    qapp.processEvents()
    x_range2, y_range2 = vb.viewRange()
    # should roughly return to original
    assert x_range2[1]-x_range2[0] == pytest.approx(x_width_before, rel=0.03)
    assert y_range2[1]-y_range2[0] == pytest.approx(y_width_before, rel=0.03)

def test_reset_restores_default_framing(panel_zoom, qapp):
    vb = panel_zoom.price_plot.getViewBox()
    vol_vb = panel_zoom.volume_plot.getViewBox()
    x_before, y_before = vb.viewRange()
    vol_before = vol_vb.viewRange()[1]
    # zoom in twice
    panel_zoom._zoom_by(0.5)
    panel_zoom._zoom_by(0.5)
    qapp.processEvents()
    x_zoomed = vb.viewRange()[0]
    assert x_zoomed != x_before
    # reset
    panel_zoom._reset_view()
    qapp.processEvents()
    x_after, y_after = vb.viewRange()
    vol_after = vol_vb.viewRange()[1]
    assert x_after == pytest.approx(x_before, rel=0.01)
    assert y_after == pytest.approx(y_before, rel=0.01)
    assert vol_after == pytest.approx(vol_before, rel=0.01)

def test_no_bars_no_op(qapp):
    p = ChartPanel()
    p.resize(900,600)
    p.show()
    qapp.processEvents()
    # no bars loaded
    try:
        p._zoom_by(0.8)
        p._zoom_by(1.25)
        p._reset_view()
    except Exception as e:
        pytest.fail(f"should not raise {e}")
    # also at limits — zoom many times
    from data.models import Bar
    bars = [Bar("TEST","5 mins", 1700000000+i*60, 100,101,99,100,1000) for i in range(5)]
    p.set_symbol("TEST")
    p.update_chart(bars)
    qapp.processEvents()
    for _ in range(20):
        p._zoom_by(0.5)
    qapp.processEvents()
    # should still be valid
    x_range, y_range = p.price_plot.getViewBox().viewRange()
    assert x_range[1] > x_range[0]
    assert y_range[1] > y_range[0]
    p.hide()
    p.close()
