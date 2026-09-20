"""Tests for D2: crosshair price chip stays inside plot right edge."""

import pyqtgraph as pg
import pytest
from PyQt6.QtCore import QEvent

from ui.chart_panel import ChartPanel

def scene_point(panel, x_view: float, y_view: float):
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(x_view, y_view))

@pytest.fixture
def panel2(chart_panel, sample_bars, qapp):
    chart_panel.set_symbol("TEST")
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel
    chart_panel.hide()

def test_chip_visible_inside_right_edge(panel2, sample_bars):
    bar = sample_bars[50]
    pos = scene_point(panel2, bar.ts, 105.5)
    panel2._update_crosshair(pos)
    assert panel2._price_tag.isVisible()
    vb = panel2.price_plot.getViewBox()
    view_right = vb.mapRectToScene(vb.rect()).right()
    # right-aligned: pos.x <= view_right
    assert panel2._price_tag.pos().x() <= view_right - 1
    # bounding rect inside
    br = panel2._price_tag.mapRectToScene(panel2._price_tag.boundingRect())
    assert br.right() <= view_right + 1
    assert panel2._price_tag.toPlainText() == "105.50"

def test_chip_stays_inside_after_zoom(panel2, sample_bars, qapp):
    bar = sample_bars[100]
    panel2._update_crosshair(scene_point(panel2, bar.ts, 110.0))
    vb = panel2.price_plot.getViewBox()
    # zoom in
    vb.scaleBy((0.5, 0.5))
    qapp.processEvents()
    panel2._update_crosshair(scene_point(panel2, bar.ts, 112.34))
    view_right = vb.mapRectToScene(vb.rect()).right()
    assert panel2._price_tag.isVisible()
    assert panel2._price_tag.pos().x() <= view_right - 1
    br = panel2._price_tag.mapRectToScene(panel2._price_tag.boundingRect())
    assert br.right() <= view_right + 1
    assert panel2._price_tag.toPlainText() == "112.34"

def test_leave_hides_chip(panel2, sample_bars):
    bar = sample_bars[30]
    panel2._update_crosshair(scene_point(panel2, bar.ts, 106.0))
    assert panel2._price_tag.isVisible()
    leave = QEvent(QEvent.Type.Leave)
    panel2.eventFilter(panel2.price_plot.viewport(), leave)
    assert not panel2._price_tag.isVisible()

def test_long_price_and_edge_positions(panel2, sample_bars, qapp):
    vb = panel2.price_plot.getViewBox()
    # long price — ensure view contains the price
    vb.setRange(yRange=(0, 200000), padding=0)
    qapp.processEvents()
    pos = scene_point(panel2, sample_bars[80].ts, 123456.78)
    panel2._update_crosshair(pos)
    view_right = vb.mapRectToScene(vb.rect()).right()
    br = panel2._price_tag.mapRectToScene(panel2._price_tag.boundingRect())
    assert panel2._price_tag.isVisible()
    assert br.right() <= view_right + 1
    # near top edge — reset view to sample range first
    panel2.update_chart(sample_bars)
    qapp.processEvents()
    vb = panel2.price_plot.getViewBox()
    pos_top = scene_point(panel2, sample_bars[20].ts, 200.0)
    panel2._update_crosshair(pos_top)
    # If still visible, top should be near view top; if outside view it hides — either is valid, but should not bleed excessively
    if panel2._price_tag.isVisible():
        br_top = panel2._price_tag.mapRectToScene(panel2._price_tag.boundingRect())
        assert br_top.top() >= vb.mapRectToScene(vb.rect()).top() - 20
    # narrow window
    panel2.resize(500, 400)
    qapp.processEvents()
    pos_narrow = scene_point(panel2, sample_bars[60].ts, 108.5)
    panel2._update_crosshair(pos_narrow)
    view_right_n = vb.mapRectToScene(vb.rect()).right()
    br_n = panel2._price_tag.mapRectToScene(panel2._price_tag.boundingRect())
    assert br_n.right() <= view_right_n + 1
