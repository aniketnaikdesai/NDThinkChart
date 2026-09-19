"""Tests for ui/alarm_overlay.py — rendering, hit-testing and drag editing."""

import pytest
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication

from data.models import Alarm
from ui.alarm_overlay import AlarmOverlay, ARMED_COLOR, TRIGGERED_COLOR


@pytest.fixture
def overlay(chart_panel, sample_bars, qapp):
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel.alarm_overlay
    chart_panel.hide()


def make_alarm(price, direction="cross_either", alarm_id=1, **kwargs):
    return Alarm(id=alarm_id, symbol="TEST", price=price, direction=direction,
                 **kwargs)


def scene_point(overlay, price: float) -> QPointF:
    return overlay._view.mapViewToScene(QPointF(0.0, price))


class TestRendering:
    def test_set_data_creates_items_per_alarm(self, overlay):
        overlay.set_data([make_alarm(105.0, alarm_id=1),
                          make_alarm(95.0, alarm_id=2)])
        assert set(overlay._items.keys()) == {1, 2}

    def test_refresh_rebuilds_after_state_change(self, overlay):
        alarm = make_alarm(105.0)
        overlay.set_data([alarm])
        alarm.triggered = True
        overlay.refresh()
        line, _label = overlay._items[1]
        assert line.pen.color().name() == TRIGGERED_COLOR

    def test_armed_color(self, overlay):
        overlay.set_data([make_alarm(105.0)])
        line, _label = overlay._items[1]
        assert line.pen.color().name() == ARMED_COLOR

    def test_clear_on_empty(self, overlay):
        overlay.set_data([make_alarm(105.0)])
        overlay.set_data([])
        assert overlay._items == {}
        assert overlay.alarm_count() == 0


class TestHitTesting:
    def test_hit_within_tolerance(self, overlay):
        alarm = make_alarm(105.0)
        overlay.set_data([alarm])
        assert overlay._hit(scene_point(overlay, 105.0)) is alarm

    def test_miss_far_away(self, overlay):
        overlay.set_data([make_alarm(105.0)])
        assert overlay._hit(scene_point(overlay, 150.0)) is None


class TestAlarmModeCreation:
    def test_press_emits_price_in_alarm_mode(self, overlay):
        overlay.set_alarm_mode(True)
        prices = []
        overlay.create_requested.connect(prices.append)
        overlay.view_mouse_press(StubEvent(scene_point(overlay, 123.5)))
        assert prices and prices[0] == pytest.approx(123.5, abs=0.5)

    def test_press_without_mode_does_not_create(self, overlay):
        prices = []
        overlay.create_requested.connect(prices.append)
        assert overlay.view_mouse_press(StubEvent(scene_point(overlay, 123.5))) is False
        assert prices == []


class TestDragEditing:
    def test_drag_updates_price_and_emits_on_finish(self, overlay):
        alarm = make_alarm(105.0)
        overlay.set_data([alarm])
        overlay.view_mouse_press(StubEvent(scene_point(overlay, 105.0)))
        moved = []
        overlay.moved.connect(lambda i, p: moved.append((i, p)))

        overlay.view_mouse_drag(
            StubEvent(scene_point(overlay, 112.0), finish=False)
        )
        assert alarm.price == pytest.approx(112.0, abs=0.5)
        assert moved == []

        overlay.view_mouse_drag(
            StubEvent(scene_point(overlay, 112.0), finish=True)
        )
        assert moved and moved[0][0] == 1
        assert overlay._drag is None

    def test_press_off_alarm_does_not_start_drag(self, overlay):
        overlay.set_data([make_alarm(105.0)])
        assert overlay.view_mouse_press(StubEvent(scene_point(overlay, 150.0))) is False
        assert overlay._drag is None


class StubEvent:
    """Minimal stand-in exposing the fields the overlay reads off an event."""

    def __init__(self, scene_pos: QPointF, finish: bool = False,
                 button=Qt.MouseButton.LeftButton):
        self._scene = scene_pos
        self._finish = finish
        self._button = button

    def scenePos(self):
        return self._scene

    def button(self):
        return self._button

    def isFinish(self):
        return self._finish
