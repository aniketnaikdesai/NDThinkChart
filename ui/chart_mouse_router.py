"""
chart_mouse_router.py
Single routing point between the price plot's ViewBox and the chart overlays.

Alarms get first refusal on a press (so alarm lines can be dragged and
click-to-create works in alarm mode) unless a drawing tool is active, in which
case the drawing overlay owns the gesture.
"""


class ChartMouseRouter:
    def __init__(self):
        self.drawing = None
        self.alarm = None

    def _drawing_active(self) -> bool:
        return self.drawing is not None and self.drawing.tool_active()

    def view_mouse_press(self, ev) -> bool:
        if not self._drawing_active() and self.alarm is not None:
            if self.alarm.view_mouse_press(ev):
                return True
        if self.drawing is not None:
            return self.drawing.view_mouse_press(ev)
        return False

    def view_mouse_drag(self, ev) -> bool:
        if not self._drawing_active() and self.alarm is not None:
            if self.alarm.view_mouse_drag(ev):
                return True
        if self.drawing is not None:
            return self.drawing.view_mouse_drag(ev)
        return False

    def view_mouse_click(self, ev) -> bool:
        if self.alarm is not None:
            if self.alarm.view_mouse_click(ev):
                return True
        if self.drawing is not None:
            return self.drawing.view_mouse_click(ev)
        return False
