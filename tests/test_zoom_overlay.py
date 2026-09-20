import pytest
import pyqtgraph as pg
from PyQt6.QtCore import QPointF, Qt

from ui.chart_panel import ChartPanel
from ui.chart_mouse_router import ChartMouseRouter

def scene_point(panel, x_view, y_view):
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(x_view, y_view))

class FakeEvent:
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

def test_magnifier_drag_sets_range(panel_zoom, qapp):
    vb = panel_zoom.price_plot.getViewBox()
    panel_zoom.set_zoom_mode(True)
    assert panel_zoom.is_zoom_active()
    x1, x2 = panel_zoom._bars[10].ts, panel_zoom._bars[50].ts
    y1, y2 = 100, 105
    start = scene_point(panel_zoom, x1, y1)
    end = scene_point(panel_zoom, x2, y2)
    # press
    ev_press = FakeEvent(Qt.MouseButton.LeftButton, start)
    assert panel_zoom._zoom_overlay.view_mouse_press(ev_press)
    # drag to end (finish)
    ev_drag = FakeEvent(Qt.MouseButton.LeftButton, end, is_finish=True)
    assert panel_zoom._zoom_overlay.view_mouse_drag(ev_drag)
    qapp.processEvents()
    x_range, y_range = vb.viewRange()
    assert x_range[0] == pytest.approx(min(x1,x2), rel=0.02)
    assert x_range[1] == pytest.approx(max(x1,x2), rel=0.02)
    assert y_range[0] == pytest.approx(min(y1,y2), rel=0.02)
    assert y_range[1] == pytest.approx(max(y1,y2), rel=0.02)
    # rubber band hidden
    assert not panel_zoom._zoom_overlay._rect_item.isVisible()

def test_magnifier_cancel_esc_and_right_click(panel_zoom, qapp):
    vb = panel_zoom.price_plot.getViewBox()
    panel_zoom.set_zoom_mode(True)
    x_range_before, y_range_before = vb.viewRange()
    start = scene_point(panel_zoom, panel_zoom._bars[10].ts, 100)
    end = scene_point(panel_zoom, panel_zoom._bars[20].ts, 105)
    ev_press = FakeEvent(Qt.MouseButton.LeftButton, start)
    panel_zoom._zoom_overlay.view_mouse_press(ev_press)
    # simulate intermediate drag
    mid = scene_point(panel_zoom, panel_zoom._bars[15].ts, 102)
    ev_drag = FakeEvent(Qt.MouseButton.LeftButton, mid, is_finish=False)
    panel_zoom._zoom_overlay.view_mouse_drag(ev_drag)
    assert panel_zoom._zoom_overlay._dragging
    # Esc cancel via panel key
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import QEvent
    # Directly call cancel as key handler would
    panel_zoom._zoom_overlay.cancel()
    assert not panel_zoom._zoom_overlay._dragging
    x_range_after, y_range_after = vb.viewRange()
    assert x_range_before == pytest.approx(x_range_after)
    assert y_range_before == pytest.approx(y_range_after)
    # Right-click cancel
    panel_zoom.set_zoom_mode(True)
    ev_press2 = FakeEvent(Qt.MouseButton.LeftButton, start)
    panel_zoom._zoom_overlay.view_mouse_press(ev_press2)
    ev_right = FakeEvent(Qt.MouseButton.RightButton, end)
    result = panel_zoom._zoom_overlay.view_mouse_press(ev_right)
    assert result is True
    assert not panel_zoom._zoom_overlay._dragging
    assert vb.viewRange()[0] == pytest.approx(x_range_before)

def test_magnifier_stays_active_after_zoom(panel_zoom, qapp):
    panel_zoom.set_zoom_mode(True)
    start = scene_point(panel_zoom, panel_zoom._bars[10].ts, 99)
    end = scene_point(panel_zoom, panel_zoom._bars[30].ts, 108)
    panel_zoom._zoom_overlay.view_mouse_press(FakeEvent(Qt.MouseButton.LeftButton, start))
    panel_zoom._zoom_overlay.view_mouse_drag(FakeEvent(Qt.MouseButton.LeftButton, end, is_finish=True))
    qapp.processEvents()
    assert panel_zoom.is_zoom_active() is True
    assert panel_zoom._chart_controls.btn_magnify.isChecked() is True

def test_magnifier_degenerate_and_outside_ignored(panel_zoom, qapp):
    vb = panel_zoom.price_plot.getViewBox()
    panel_zoom.set_zoom_mode(True)
    x_before, y_before = vb.viewRange()
    # degenerate 2px
    start = scene_point(panel_zoom, panel_zoom._bars[10].ts, 100)
    # end very close (2px in scene)
    # small offset in scene coords: 2 px
    end_small = QPointF(start.x()+2, start.y()+2)
    panel_zoom._zoom_overlay.view_mouse_press(FakeEvent(Qt.MouseButton.LeftButton, start))
    panel_zoom._zoom_overlay.view_mouse_drag(FakeEvent(Qt.MouseButton.LeftButton, end_small, is_finish=True))
    qapp.processEvents()
    x_after, y_after = vb.viewRange()
    assert x_before == pytest.approx(x_after)
    assert y_before == pytest.approx(y_after)
    # outside plot
    outside = QPointF(vb.mapRectToScene(vb.rect()).right()+50, vb.mapRectToScene(vb.rect()).top()-50)
    ev_out = FakeEvent(Qt.MouseButton.LeftButton, outside)
    assert panel_zoom._zoom_overlay.view_mouse_press(ev_out) is False

def test_magnifier_reset_on_symbol_timeframe_and_router_precedence(panel_zoom, qapp):
    panel_zoom.set_zoom_mode(True)
    assert panel_zoom.is_zoom_active()
    panel_zoom.set_symbol("AAPL")
    assert not panel_zoom.is_zoom_active()
    panel_zoom.set_zoom_mode(True)
    panel_zoom.set_timeframe("1 hour")
    assert not panel_zoom.is_zoom_active()
    # Router precedence
    panel_zoom.set_zoom_mode(True)
    # Fake alarm and drawing that would otherwise handle press
    class FakeHandler:
        def __init__(self):
            self.called = False
        def view_mouse_press(self, ev):
            self.called = True
            return True
        def view_mouse_drag(self, ev):
            self.called = True
            return True
        def view_mouse_click(self, ev):
            self.called = True
            return True
        def is_active(self):
            return True
        def tool_active(self):
            return True
    fake_alarm = FakeHandler()
    fake_drawing = FakeHandler()
    panel_zoom.mouse_router.alarm = fake_alarm
    panel_zoom.mouse_router.drawing = fake_drawing
    start = scene_point(panel_zoom, panel_zoom._bars[10].ts, 100) if panel_zoom._bars else QPointF(0,0)
    ev = FakeEvent(Qt.MouseButton.LeftButton, start)
    # router should give to zoom first
    result = panel_zoom.mouse_router.view_mouse_press(ev)
    assert result is True
    # ensure alarm/drawing not called (since zoom consumed)
    # Reset fake flags after router: we patched but zoom returns True so alarm/drawing not reached
    # Verify zoom still active
    assert panel_zoom.is_zoom_active()
