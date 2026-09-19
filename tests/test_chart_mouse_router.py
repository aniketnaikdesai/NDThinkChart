"""Tests for ui/chart_mouse_router.py — overlay event precedence."""

from ui.chart_mouse_router import ChartMouseRouter


class FakeOverlay:
    def __init__(self, consume=False, tool_active=False):
        self.consume = consume
        self._tool_active = tool_active
        self.calls = []

    def tool_active(self):
        return self._tool_active

    def view_mouse_press(self, ev):
        self.calls.append("press")
        return self.consume

    def view_mouse_drag(self, ev):
        self.calls.append("drag")
        return self.consume

    def view_mouse_click(self, ev):
        self.calls.append("click")
        return self.consume


def build(drawing, alarm):
    router = ChartMouseRouter()
    router.drawing = drawing
    router.alarm = alarm
    return router


def test_alarm_press_wins_in_cursor_mode():
    drawing = FakeOverlay(consume=True)
    alarm = FakeOverlay(consume=True)
    router = build(drawing, alarm)
    assert router.view_mouse_press(object()) is True
    assert alarm.calls == ["press"]
    assert drawing.calls == []


def test_drawing_tool_blocks_alarm_press():
    drawing = FakeOverlay(consume=True, tool_active=True)
    alarm = FakeOverlay(consume=True)
    router = build(drawing, alarm)
    assert router.view_mouse_press(object()) is True
    assert alarm.calls == []
    assert drawing.calls == ["press"]


def test_alarm_miss_falls_through_to_drawing():
    drawing = FakeOverlay(consume=True)
    alarm = FakeOverlay(consume=False)
    router = build(drawing, alarm)
    assert router.view_mouse_press(object()) is True
    assert alarm.calls == ["press"]
    assert drawing.calls == ["press"]


def test_click_prefers_alarm_then_drawing():
    drawing = FakeOverlay(consume=False)
    alarm = FakeOverlay(consume=False)
    router = build(drawing, alarm)
    assert router.view_mouse_click(object()) is False
    assert alarm.calls == ["click"]
    assert drawing.calls == ["click"]


def test_missing_overlays_are_safe():
    router = ChartMouseRouter()
    assert router.view_mouse_press(object()) is False
    assert router.view_mouse_drag(object()) is False
    assert router.view_mouse_click(object()) is False
