"""Zoom overlay — rubber-band area zoom for ChartPanel."""

from PyQt6.QtCore import QObject, QRectF, Qt
from PyQt6.QtWidgets import QGraphicsRectItem
import pyqtgraph as pg

class ZoomOverlay(QObject):
    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self._plot = plot
        self._view = plot.getViewBox()
        self._active = False
        self._dragging = False
        self._start_scene = None
        self._rect_item = QGraphicsRectItem()
        pen = pg.mkPen('#60a5fa', width=1, style=Qt.PenStyle.DashLine)
        brush = pg.mkBrush(96, 165, 250, 40)
        self._rect_item.setPen(pen)
        self._rect_item.setBrush(brush)
        self._rect_item.setZValue(1000)
        self._rect_item.hide()
        # Add to scene
        scene = self._view.scene()
        if scene is not None:
            scene.addItem(self._rect_item)
        else:
            # If scene not yet available, defer via plot
            self._plot.scene().addItem(self._rect_item)

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        self._active = bool(active)
        if not self._active:
            self.cancel()

    def cancel(self):
        if self._dragging:
            self._dragging = False
            self._start_scene = None
            self._rect_item.hide()

    def view_mouse_press(self, ev) -> bool:
        if not self._active:
            return False
        # Right-click cancels selection if dragging
        if ev.button() == Qt.MouseButton.RightButton:
            if self._dragging:
                self.cancel()
                ev.accept()
                return True
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False
        # Check that press is inside view rect
        try:
            scene_pos = ev.scenePos()
        except Exception:
            return False
        view_rect_scene = self._view.mapRectToScene(self._view.rect())
        if not view_rect_scene.contains(scene_pos):
            return False
        # Start drag
        self._dragging = True
        self._start_scene = scene_pos
        rect = QRectF(scene_pos, scene_pos)
        self._rect_item.setRect(rect)
        self._rect_item.show()
        ev.accept()
        return True

    def view_mouse_drag(self, ev) -> bool:
        if not self._active or not self._dragging:
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False
        try:
            cur = ev.scenePos()
        except Exception:
            return False
        rect = QRectF(self._start_scene, cur).normalized()
        self._rect_item.setRect(rect)
        if ev.isFinish():
            self._dragging = False
            self._rect_item.hide()
            # degenerate check
            if rect.width() < 5 or rect.height() < 5:
                self._start_scene = None
                ev.accept()
                return True
            # Map to view
            p1 = self._view.mapSceneToView(rect.topLeft())
            p2 = self._view.mapSceneToView(rect.bottomRight())
            x1, x2 = min(p1.x(), p2.x()), max(p1.x(), p2.x())
            y1, y2 = min(p1.y(), p2.y()), max(p1.y(), p2.y())
            # Apply range to price view; volume linked on X will follow via XLink
            self._view.setRange(xRange=(x1, x2), yRange=(y1, y2), padding=0)
            self._start_scene = None
            ev.accept()
            return True
        ev.accept()
        return True

    def view_mouse_click(self, ev) -> bool:
        # No click handling; return False so other overlays can handle click
        return False
