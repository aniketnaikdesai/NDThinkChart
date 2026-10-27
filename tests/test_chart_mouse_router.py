"""Tests for ui/chart_mouse_router.py — overlay event precedence + RouterMode."""

from ui.chart_mouse_router import ChartMouseRouter, RouterMode


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


# ── RouterMode state machine (ESC-002 / T21) ───────────────────────────────────


class ProbeOverlay:
    """Configurable overlay double recording every interaction.

    Implements all three accessors (``tool_active`` / ``is_active`` /
    ``is_alarm_mode``) so the router's defensive probes are exercised, and
    records side-effect calls for assertions.
    """

    def __init__(self, tool_active=False, is_active=False, alarm_mode=False,
                 consume=False):
        self._tool_active = tool_active
        self._is_active = is_active
        self._alarm_mode = alarm_mode
        self.consume = consume
        self.calls = []
        self.pending = None

    def tool_active(self):
        return self._tool_active

    def is_active(self):
        return self._is_active

    def is_alarm_mode(self):
        return self._alarm_mode

    def set_tool(self, tool):
        self.calls.append(("set_tool", tool))

    def set_active(self, active):
        self.calls.append(("set_active", active))
        self._is_active = bool(active)

    def set_alarm_mode(self, enabled):
        self.calls.append(("set_alarm_mode", enabled))
        self._alarm_mode = bool(enabled)

    def cancel(self):
        self.calls.append("cancel")

    def view_mouse_press(self, ev):
        self.calls.append("press")
        return self.consume

    def view_mouse_drag(self, ev):
        self.calls.append("drag")
        return self.consume

    def view_mouse_click(self, ev):
        self.calls.append("click")
        return self.consume


def test_magnifier_refused_during_alarm_placement():
    """T21-T04 / AC-D3.9 (TR-9)."""
    alarm = ProbeOverlay(alarm_mode=False)
    zoom = ProbeOverlay(is_active=False)
    router = ChartMouseRouter()
    router.alarm = alarm
    router.zoom = zoom
    router.enter_alarm_placing()
    assert router.active_mode == RouterMode.ALARM_PLACING

    # A pending placement in the alarm overlay must survive the refusal.
    alarm.pending = {"price": 123.0}
    calls_before = list(alarm.calls)

    assert router.enter_zoom() is False
    assert router.active_mode == RouterMode.ALARM_PLACING
    assert alarm.pending == {"price": 123.0}
    assert alarm.calls == calls_before
    assert ("set_alarm_mode", False) not in alarm.calls
    assert zoom.is_active() is False
    assert ("set_active", True) not in zoom.calls


def test_magnifier_refused_shows_status_hint(qapp):
    """T21-T05 / AC-D3.9: TR-9 refusal reaches MainWindow's hint.

    The page runs the same frozen router, so a refusal there reports through
    ``LwBridge.pageZoomRefused`` → the view's ``zoom_refused`` — the signal
    MainWindow wires to "Finish or cancel alarm placement before zooming".
    The Python control shim takes the same decision through the router.
    """
    from ui.lwc_view import LwcChartView

    view = LwcChartView()
    try:
        assert view.set_alarm_mode(True) == "ALARM_PLACING"
        assert view.router.active_mode == RouterMode.ALARM_PLACING

        refused = []
        view.zoom_refused.connect(lambda: refused.append(True))

        view.bridge.pageZoomRefused.emit({"trigger": "enter_zoom"})
        qapp.processEvents()
        assert refused == [True]

        out = view.handle_control("magnifier", True)
        assert out["refused"] is True
        assert out["mode"] == "ALARM_PLACING"
        assert view.router.active_mode == RouterMode.ALARM_PLACING
    finally:
        view.close()


def test_reconcile_mode_from_wired_overlays():
    """T21-T06 / RC-3: precedence DRAWING > ZOOMING > ALARM_PLACING > IDLE."""
    drawing = ProbeOverlay(tool_active=False)
    alarm = ProbeOverlay(alarm_mode=True)
    zoom = ProbeOverlay(is_active=True)
    router = ChartMouseRouter()
    router.drawing = drawing
    router.alarm = alarm
    router.zoom = zoom

    assert router.active_mode == RouterMode.ZOOMING  # zoom beats alarm

    drawing._tool_active = True
    router.drawing = drawing
    assert router.active_mode == RouterMode.DRAWING  # drawing beats all

    drawing._tool_active = False
    router.drawing = drawing
    assert router.active_mode == RouterMode.ZOOMING

    zoom._is_active = False
    router.zoom = zoom
    assert router.active_mode == RouterMode.ALARM_PLACING

    alarm._alarm_mode = False
    router.alarm = alarm
    assert router.active_mode == RouterMode.IDLE


def test_click_in_drawing_reaches_only_drawing():
    """T21-T07 / RC-4b."""
    drawing = ProbeOverlay(tool_active=True)
    alarm = ProbeOverlay(alarm_mode=False)
    router = ChartMouseRouter()
    router.drawing = drawing
    router.alarm = alarm
    assert router.active_mode == RouterMode.DRAWING

    assert router.view_mouse_click(object()) is False
    assert drawing.calls == ["click"]
    assert alarm.calls == []
