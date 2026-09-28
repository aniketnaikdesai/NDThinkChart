"""Tests for ui/chart_mouse_router.py — overlay event precedence + RouterMode."""

import pytest
import pyqtgraph as pg
from PyQt6.QtCore import Qt

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


class FakeEvent:
    """Minimal pyqtgraph mouse-event double (button / scenePos / isFinish)."""

    def __init__(self, button, scene_pos, is_finish=False):
        self._button = button
        self._scene_pos = scene_pos
        self._is_finish = is_finish
        self.accepted = False

    def button(self):
        return self._button

    def scenePos(self):
        return self._scene_pos

    def isFinish(self):
        return self._is_finish

    def accept(self):
        self.accepted = True

    def ignore(self):
        pass


@pytest.fixture
def panel(qapp, sample_bars):
    from ui.chart_panel import ChartPanel

    p = ChartPanel()
    p.resize(900, 600)
    p.show()
    p.set_symbol("TEST")
    p.update_chart(sample_bars)
    qapp.processEvents()
    yield p
    p.hide()
    p.close()


def _scene_pos(panel, x_view, y_view):
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(x_view, y_view))


def test_zoom_during_draw_cancels_draw(panel, qapp):
    """T21-T01 / AC-D3.7 forward (TR-4)."""
    from ui.drawing_overlay import TOOL_CURSOR

    panel.set_drawing_tool("zone")
    assert panel.mouse_router.active_mode == RouterMode.DRAWING

    mid_ts = panel._bars[len(panel._bars) // 2].ts
    press = FakeEvent(Qt.MouseButton.LeftButton, _scene_pos(panel, mid_ts, 110.0))
    assert panel.mouse_router.view_mouse_press(press) is True
    assert panel.drawing_overlay._draft is not None
    preview_items = list(panel.drawing_overlay._draft["preview"])
    assert preview_items

    assert panel.mouse_router.enter_zoom() is True
    qapp.processEvents()

    assert panel.drawing_overlay._tool == TOOL_CURSOR
    assert panel.drawing_overlay._draft is None
    assert all(item.scene() is None for item in preview_items)
    assert panel.mouse_router.active_mode == RouterMode.ZOOMING
    assert panel._zoom_overlay.is_active() is True


def test_draw_blocked_during_zoom(panel, monkeypatch):
    """T21-T02 / AC-D3.7 reverse (TR-5)."""
    panel.set_zoom_mode(True)
    assert panel.mouse_router.active_mode == RouterMode.ZOOMING
    assert panel._zoom_overlay.is_active() is True

    cancelled = []
    monkeypatch.setattr(panel._zoom_overlay, "cancel", lambda: cancelled.append(True))

    panel.mouse_router.enter_drawing("trendline")

    assert panel._zoom_overlay.is_active() is False
    assert cancelled  # zoom.cancel() ran
    assert panel.mouse_router.active_mode == RouterMode.DRAWING
    assert panel.drawing_overlay.tool_active() is True


def test_alarm_placement_blocks_zoom(panel, monkeypatch):
    """T21-T03 / AC-D3.8 (TR-6)."""
    panel.set_zoom_mode(True)
    assert panel.mouse_router.active_mode == RouterMode.ZOOMING

    cancelled = []
    monkeypatch.setattr(panel._zoom_overlay, "cancel", lambda: cancelled.append(True))

    panel.mouse_router.enter_alarm_placing()

    assert panel._zoom_overlay.is_active() is False
    assert cancelled
    assert panel.mouse_router.active_mode == RouterMode.ALARM_PLACING
    assert panel.alarm_overlay.is_alarm_mode() is True


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


def test_magnifier_refused_shows_status_hint(monkeypatch, qapp):
    """T21-T05 / AC-D3.9 integration: button re-unchecked + MainWindow hint."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    try:
        cp = win.chart_panel
        cp.set_alarm_mode(True)
        assert cp.mouse_router.active_mode == RouterMode.ALARM_PLACING

        refused = []
        cp.zoom_refused.connect(lambda: refused.append(True))

        cp._chart_controls.btn_magnify.setChecked(True)
        qapp.processEvents()

        assert len(refused) == 1
        assert cp._chart_controls.btn_magnify.isChecked() is False
        assert win.status_bar.currentMessage() == (
            "Finish or cancel alarm placement before zooming"
        )
        assert cp.mouse_router.active_mode == RouterMode.ALARM_PLACING
        assert cp.alarm_overlay.is_alarm_mode() is True
        assert cp.is_zoom_active() is False
    finally:
        win.close()


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


def test_router_mode_is_mutually_exclusive(panel):
    """T21-T08: DRAWING and ZOOMING can never both be active."""
    panel.set_drawing_tool("zone")
    assert panel.mouse_router.active_mode == RouterMode.DRAWING
    assert panel._zoom_overlay.is_active() is False

    panel.set_zoom_mode(True)
    assert panel.mouse_router.active_mode == RouterMode.ZOOMING
    assert panel.drawing_overlay.tool_active() is False
    assert not (panel.drawing_overlay.tool_active() and panel._zoom_overlay.is_active())

    panel.set_drawing_tool("trendline")
    assert panel.mouse_router.active_mode == RouterMode.DRAWING
    assert panel._zoom_overlay.is_active() is False
    assert not (panel.drawing_overlay.tool_active() and panel._zoom_overlay.is_active())

    assert panel.mouse_router.active_mode in tuple(RouterMode)


def test_zoom_stays_active_after_completed_zoom(panel, qapp):
    """T21-T09 / AC-D3.2 + AC-D3.4 preserved."""
    panel.set_zoom_mode(True)
    start = _scene_pos(panel, panel._bars[10].ts, 100.0)
    end = _scene_pos(panel, panel._bars[50].ts, 105.0)

    assert panel.mouse_router.view_mouse_press(
        FakeEvent(Qt.MouseButton.LeftButton, start)) is True
    assert panel.mouse_router.view_mouse_drag(
        FakeEvent(Qt.MouseButton.LeftButton, end, is_finish=True)) is True
    qapp.processEvents()

    assert panel.mouse_router.active_mode == RouterMode.ZOOMING
    assert panel._chart_controls.btn_magnify.isChecked() is True


def test_esc_cancels_selection_not_mode(panel, qapp):
    """T21-T10 / AC-D3.3 preserved (TR-14)."""
    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QKeyEvent

    panel.set_zoom_mode(True)
    start = _scene_pos(panel, panel._bars[10].ts, 100.0)
    assert panel.mouse_router.view_mouse_press(
        FakeEvent(Qt.MouseButton.LeftButton, start)) is True
    assert panel._zoom_overlay._dragging is True

    esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                    Qt.KeyboardModifier.NoModifier)
    panel.keyPressEvent(esc)
    qapp.processEvents()

    assert panel._zoom_overlay._dragging is False
    assert panel.mouse_router.active_mode == RouterMode.ZOOMING
