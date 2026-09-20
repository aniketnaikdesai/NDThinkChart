"""Integration tests driving the drawing overlay through real Qt mouse events.

These cover the pyqtgraph event plumbing (press / drag / click / grabber) that
direct method-call tests cannot: the overlay must not take the Qt mouse grabber,
or pyqtgraph stops delivering drag and click events.
"""

import pytest
import pyqtgraph as pg
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from data.models import Drawing


@pytest.fixture
def panel(chart_panel, sample_bars, qapp):
    chart_panel.set_symbol("TEST")
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel
    chart_panel.hide()


def move_with_button(panel, pos: QPoint):
    event = QMouseEvent(
        QEvent.Type.MouseMove, QPointF(pos),
        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(panel.price_plot.viewport(), event)
    QApplication.processEvents()


def viewport_point(panel, overlay, x: float, y: float) -> QPoint:
    # Map view (data) coordinates to viewport pixels through the ViewBox.
    # Manual viewport-width lerping is wrong: the ViewBox only occupies the
    # region inside the axis strips, so scene x/y are offset from widget px.
    vb = panel.price_plot.getViewBox()
    scene_pos = vb.mapViewToScene(pg.Point(x, y))
    return QPoint(int(scene_pos.x()), int(scene_pos.y()))


def test_click_click_creates_trendline(panel, sample_bars):
    ov = panel.drawing_overlay
    viewport = panel.price_plot.viewport()
    created = []
    ov.created.connect(created.append)
    ov.set_tool("trendline")

    p1 = viewport_point(panel, ov, sample_bars[10].ts, 112.0)
    p2 = viewport_point(panel, ov, sample_bars[30].ts, 115.0)
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, pos=p1)
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, pos=p2)
    QApplication.processEvents()

    assert len(created) == 1
    assert created[0].kind == "trendline"
    assert created[0].payload["p1"]["x"] < created[0].payload["p2"]["x"]


def test_drag_creates_horizontal(panel, sample_bars):
    ov = panel.drawing_overlay
    viewport = panel.price_plot.viewport()
    created = []
    ov.created.connect(created.append)
    ov.set_tool("horizontal")

    start = viewport_point(panel, ov, sample_bars[10].ts, 112.0)
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
    for dy in range(10, 61, 10):
        move_with_button(panel, QPoint(start.x(), start.y() + dy))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=QPoint(start.x(), start.y() + 60))
    QApplication.processEvents()

    assert len(created) == 1
    assert created[0].kind == "horizontal"
    assert ov._draft is None


def test_does_not_take_mouse_grabber(panel, sample_bars):
    ov = panel.drawing_overlay
    viewport = panel.price_plot.viewport()
    ov.set_tool("horizontal")
    start = viewport_point(panel, ov, sample_bars[10].ts, 112.0)
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
    QApplication.processEvents()
    assert panel.price_plot.scene().mouseGrabberItem() is None
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=start)


def test_select_and_delete_with_keyboard(panel, sample_bars):
    ov = panel.drawing_overlay
    viewport = panel.price_plot.viewport()
    drawing = Drawing(
        symbol="TEST", kind="horizontal", payload={"y": 112.0}, id=1,
    )
    ov.set_data("TEST", [drawing], [])
    ov.set_tool("cursor")

    point = viewport_point(panel, ov, sample_bars[10].ts, 112.0)
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, pos=point)
    QApplication.processEvents()
    assert ov._selected_id == 1

    deleted = []
    ov.deleted.connect(deleted.append)
    QTest.keyClick(panel, Qt.Key.Key_Delete)
    QApplication.processEvents()
    assert deleted == [1]
    assert ov._find_drawing(1) is None


def test_body_drag_moves_both_endpoints(panel, sample_bars):
    ov = panel.drawing_overlay
    viewport = panel.price_plot.viewport()
    drawing = Drawing(
        symbol="TEST", kind="trendline", id=1,
        payload={"p1": {"x": sample_bars[2].ts, "y": 110.0},
                 "p2": {"x": sample_bars[20].ts, "y": 116.0}},
    )
    ov.set_data("TEST", [drawing], [])
    ov.set_tool("cursor")

    start = viewport_point(panel, ov, sample_bars[11].ts, 113.0)
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
    for dx in (5, 10, 20):
        move_with_button(panel, QPoint(start.x() + dx, start.y() - dx))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton,
                       pos=QPoint(start.x() + 20, start.y() - 20))
    QApplication.processEvents()

    assert drawing.payload["p1"]["y"] > 110.0
    assert drawing.payload["p2"]["y"] > 116.0