"""Real Qt event-path tests for alarm interaction, mirroring the drawing tests."""

import pytest
import pyqtgraph as pg
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from data.models import Alarm


@pytest.fixture
def panel(chart_panel, sample_bars, qapp):
    chart_panel.set_symbol("TEST")
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel
    chart_panel.hide()


def price_point(panel, overlay, price: float, ts: float | None = None) -> QPoint:
    vb = panel.price_plot.getViewBox()
    if ts is None:
        ts = panel._bars[len(panel._bars) // 2].ts if panel._bars else 0
    scene_pos = vb.mapViewToScene(pg.Point(ts, price))
    return QPoint(int(scene_pos.x()), int(scene_pos.y()))


def move_with_button(panel, pos: QPoint):
    event = QMouseEvent(
        QEvent.Type.MouseMove, QPointF(pos),
        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(panel.price_plot.viewport(), event)
    QApplication.processEvents()


def test_alarm_mode_click_requests_price(panel):
    ov = panel.alarm_overlay
    viewport = panel.price_plot.viewport()
    ov.set_alarm_mode(True)
    prices = []
    ov.create_requested.connect(prices.append)

    mid_ts = panel._bars[len(panel._bars) // 2].ts
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton,
                     pos=price_point(panel, ov, 118.0, mid_ts))
    QApplication.processEvents()

    assert len(prices) == 1
    assert prices[0] == pytest.approx(118.0, abs=0.5)


def test_drag_existing_alarm_emits_new_price(panel):
    ov = panel.alarm_overlay
    viewport = panel.price_plot.viewport()
    alarm = Alarm(id=1, symbol="TEST", price=110.0, direction="cross_either")
    ov.set_data([alarm])
    ov.set_alarm_mode(False)

    moved = []
    ov.moved.connect(lambda i, p: moved.append((i, p)))

    mid_ts = panel._bars[len(panel._bars) // 2].ts
    start = price_point(panel, ov, 110.0, mid_ts)
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
    for dy in (5, 10, 20):
        move_with_button(panel, QPoint(start.x(), start.y() - dy))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton,
                       pos=QPoint(start.x(), start.y() - 20))
    QApplication.processEvents()

    assert moved and moved[0][0] == 1
    assert alarm.price > 110.0
    assert ov._drag is None


def test_alarm_drag_does_not_take_grabber(panel):
    ov = panel.alarm_overlay
    viewport = panel.price_plot.viewport()
    ov.set_data([Alarm(id=1, symbol="TEST", price=110.0, direction="cross_either")])
    mid_ts = panel._bars[len(panel._bars) // 2].ts
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton,
                     pos=price_point(panel, ov, 110.0, mid_ts))
    QApplication.processEvents()
    assert panel.price_plot.scene().mouseGrabberItem() is None
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton,
                       pos=price_point(panel, ov, 110.0, mid_ts))
