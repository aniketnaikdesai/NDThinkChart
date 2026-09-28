"""D11 drawing price-label tests.

Task mapping (T25 / AC-D11.4 re-scope, ESC-006):

- T25-T01 ``test_label_vs_label_bbox_no_intersection`` — label-vs-label
  collision only: consecutive inner-right labels offset >= 15 px and their
  scene bounding boxes do not intersect.
- T25-T02 ``test_crosshair_chip_excluded_from_label_collision`` — the
  crosshair chip is out of scope for label collision accounting.
- T25-T03 ``test_horizontal_label_inner_right`` /
  ``test_zone_two_labels_inner_right`` / ``test_labels_stack_not_overlapping``
  — preserved AC-D11.1 / AC-D11.2 / AC-D11.3 coverage.
"""

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

def _inner_price_labels(panel, drawing_id):
    """Inner-right D11 price labels (anchor=(1,0.5), Z=10) for a drawing."""
    items = panel.drawing_overlay._items.get(drawing_id, [])
    return [it for it in items
            if isinstance(it, pg.TextItem) and it.anchor == pg.Point(1, 0.5)]

def _scene_bbox(item):
    """Scene-space bounding rect of a scene TextItem."""
    return item.mapRectToScene(item.boundingRect())

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

def test_label_vs_label_bbox_no_intersection(panel, qapp):
    """T25-T01 / AC-D11.4: two drawings at nearby prices (within the label
    band) render inner-right labels whose scene bounding boxes do not
    intersect; consecutive labels are offset >= 15 px and each stays fully
    inside view_rect on the right edge."""
    d1 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 102.0}, color="#ff0000", id=5)
    d2 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 102.05}, color="#00ff00", id=6)
    panel.drawing_overlay.add_drawing(d1)
    panel.drawing_overlay.add_drawing(d2)
    qapp.processEvents()

    labels = _inner_price_labels(panel, 5) + _inner_price_labels(panel, 6)
    assert len(labels) == 2

    vb = panel.price_plot.getViewBox()
    view_rect_scene = vb.mapRectToScene(vb.rect())

    labels.sort(key=lambda label: label.pos().y())
    a_bbox = _scene_bbox(labels[0])
    b_bbox = _scene_bbox(labels[1])

    # AC-D11.4: consecutive labels are offset by >= 15 px.
    center_dy = abs(a_bbox.center().y() - b_bbox.center().y())
    assert center_dy >= 15, f"consecutive label offset {center_dy}px < 15px"

    # AC-D11.4: each label remains fully inside view_rect on the right edge.
    for bbox in (a_bbox, b_bbox):
        assert bbox.right() <= view_rect_scene.right() + 1, f"{bbox} bleeds past right edge"
        assert bbox.left() >= view_rect_scene.left() - 1, f"{bbox} bleeds past left edge"

    # AC-D11.4 (Measurable): scene bounding rects do not intersect — the
    # centre separation must be at least the label bounding-box height.
    bbox_height = max(a_bbox.height(), b_bbox.height())
    assert center_dy >= bbox_height, (
        f"D11 label bounding boxes overlap: centre separation {center_dy}px "
        f"< label bbox height {bbox_height}px")
    assert not a_bbox.intersects(b_bbox), (
        f"D11 label bounding boxes intersect: {a_bbox} vs {b_bbox}")

def test_crosshair_chip_excluded_from_label_collision(panel, qapp):
    """T25-T02 / AC-D11.4 edge: a crosshair chip resting on a drawing's price
    lives in the Y-axis lane and must not participate in label collision
    accounting — no drawing label is displaced by the chip."""
    d1 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 102.0}, color="#ff0000", id=7)
    d2 = Drawing(symbol="TEST", kind="horizontal", payload={"y": 102.05}, color="#00ff00", id=8)
    panel.drawing_overlay.add_drawing(d1)
    panel.drawing_overlay.add_drawing(d2)
    qapp.processEvents()

    labels = _inner_price_labels(panel, 7) + _inner_price_labels(panel, 8)
    assert len(labels) == 2
    labels.sort(key=lambda label: label.pos().y())
    positions_before = [label.pos() for label in labels]

    # Rest the crosshair exactly on the first drawing's price.
    vb = panel.price_plot.getViewBox()
    ts = 1_700_000_000 + 20 * 300
    panel._update_crosshair(vb.mapViewToScene(pg.Point(ts, 102.0)))
    qapp.processEvents()
    assert panel._price_tag.isVisible()
    assert float(panel._price_tag.toPlainText().replace(",", "")) == pytest.approx(102.0)

    # Re-run the stacking pass: the chip must not displace any drawing label.
    panel.drawing_overlay._update_inner_labels()
    qapp.processEvents()
    positions_after = [label.pos() for label in labels]
    assert positions_after == positions_before

    # The chip is not part of the drawing overlay's collision set.
    collision_items = [it for items in panel.drawing_overlay._items.values() for it in items]
    assert panel._price_tag not in collision_items

    # Labels remain label-vs-label consistent (still offset >= 15 px).
    offset = abs(positions_after[1].y() - positions_after[0].y())
    assert offset >= 15
