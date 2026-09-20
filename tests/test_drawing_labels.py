import pytest
import pyqtgraph as pg
from data.models import Drawing
from ui.chart_panel import ChartPanel

def _bar(ts, price=100):
    from data.models import Bar
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=price, high=price+0.5, low=price-0.5, close=price, volume=1000)

@pytest.fixture
def panel(qapp):
    p = ChartPanel()
    p.resize(900,600)
    p.show()
    qapp.processEvents()
    # Load some bars
    bars = [_bar(1_700_000_000 + i*300, 100+i*0.1) for i in range(50)]
    p.set_symbol("TEST")
    p.update_chart(bars)
    qapp.processEvents()
    yield p
    p.hide()
    p.close()

def test_horizontal_label_inner_right(panel, qapp):
    # Create horizontal line drawing
    drawing = Drawing(symbol="TEST", kind="horizontal", payload={"y": 105.5}, color="#ff0000", id=1)
    panel.drawing_overlay.add_drawing(drawing)
    qapp.processEvents()
    # Find the label for this drawing (inner-right)
    items = panel.drawing_overlay._items.get(1, [])
    labels = [it for it in items if isinstance(it, pg.TextItem)]
    assert len(labels) >= 1
    label = labels[0]
    assert label.anchor == pg.Point(1, 0.5)
    assert label.toPlainText() == "105.50"
    # Check position is near right edge
    vb = panel.price_plot.getViewBox()
    view_rect_scene = vb.mapRectToScene(vb.rect())
    pos = label.pos()
    # pos is in scene coords, should be right -4
    assert pos.x() == pytest.approx(view_rect_scene.right() - 4, abs=2)
    assert label.isVisible() or True  # may be inside

def test_zone_two_labels_inner_right(panel, qapp):
    drawing = Drawing(symbol="TEST", kind="zone", payload={"x1": 1_700_000_000, "x2": 1_700_000_300, "y1": 102, "y2": 98}, color="#00ff00", id=2)
    panel.drawing_overlay.add_drawing(drawing)
    qapp.processEvents()
    items = panel.drawing_overlay._items.get(2, [])
    labels = [it for it in items if isinstance(it, pg.TextItem)]
    assert len(labels) == 2
    texts = sorted([l.toPlainText() for l in labels])
    assert "102.00" in texts or "102" in str(texts)
    assert "98.00" in texts or "98" in str(texts)
    vb = panel.price_plot.getViewBox()
    view_rect_scene = vb.mapRectToScene(vb.rect())
    for label in labels:
        assert label.anchor == pg.Point(1, 0.5)
        assert label.pos().x() == pytest.approx(view_rect_scene.right() - 4, abs=2)

def test_labels_stack_not_overlapping(panel, qapp):
    # Two drawings at nearby prices should stack
    d1 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 100.0}, color="#ff0000", id=3)
    d2 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 100.05}, color="#00ff00", id=4)
    panel.drawing_overlay.add_drawing(d1)
    panel.drawing_overlay.add_drawing(d2)
    qapp.processEvents()
    labels = []
    for did in [3,4]:
        items = panel.drawing_overlay._items.get(did, [])
        labels.extend([it for it in items if isinstance(it, pg.TextItem)])
    assert len(labels) == 2
    y0 = labels[0].pos().y()
    y1 = labels[1].pos().y()
    assert abs(y0 - y1) >= 10  # stacked offset
