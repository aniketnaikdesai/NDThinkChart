"""
alarm_overlay.py
Renders price alarms as horizontal lines on the price plot and handles their
interaction: click-to-create (in alarm mode), drag-to-adjust, and a right-click
context menu for rearm / mute / delete.

Alarm prices map directly onto the price axis, so no timestamp anchoring is
needed (unlike drawings).
"""

from typing import Optional

import pyqtgraph as pg
from PyQt6.QtCore import QObject, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QMenu

from data.models import Alarm

ALARM_HIT_TOLERANCE_PX = 7

TRIGGERED_COLOR = "#f87171"
ARMED_COLOR = "#fbbf24"
MUTED_COLOR = "#94a3b8"
INACTIVE_COLOR = "#64748b"

DIRECTION_GLYPH = {
    "cross_above": "▲",
    "cross_below": "▼",
    "cross_either": "◆",
}


class AlarmOverlay(QObject):
    create_requested = pyqtSignal(float)     # price for a new alarm
    moved = pyqtSignal(int, float)           # alarm_id, new price
    mute_toggled = pyqtSignal(int, bool)     # alarm_id, sound
    rearm_requested = pyqtSignal(int)        # alarm_id
    delete_requested = pyqtSignal(int)       # alarm_id

    def __init__(self, plot: pg.PlotWidget, editable: bool = True):
        super().__init__()
        self._plot = plot
        self._view = plot.getViewBox()
        # D24: pop-out charts are read-only — all mouse interactions that
        # could mutate shared alarms are inert when not editable.
        self._editable = editable
        self._alarms: list[Alarm] = []
        self._items: dict = {}
        self._bar_count: int = 0
        # D21.4: the alarm label sits at the display-x of the last bar. The
        # ViewBox x-model is display-x after collapse, so the last bar's
        # timestamp is mapped through the collapse map before positioning.
        self._last_bar_ts: Optional[int] = None
        self._collapse_map = None
        self._alarm_mode: bool = False
        self._drag: Optional[dict] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_bars(self, bars) -> None:
        self._bar_count = len(bars) if bars else 0
        self._last_bar_ts = int(bars[-1].ts) if bars else None
        self._reposition_labels()

    def set_collapse_map(self, collapse_map) -> None:
        """Set the D21.4 display-x map used to place the alarm label (x)."""
        self._collapse_map = collapse_map
        self._reposition_labels()

    def _reposition_labels(self) -> None:
        x = self._label_x()
        for alarm in self._alarms:
            items = self._items.get(alarm.id)
            if items:
                items[1].setPos(x, alarm.price)

    def set_alarm_mode(self, enabled: bool) -> None:
        self._alarm_mode = bool(enabled)
        self._drag = None

    def is_alarm_mode(self) -> bool:
        return self._alarm_mode

    def set_data(self, alarms: list[Alarm]) -> None:
        self._clear_items()
        self._drag = None
        # D39: only price alarms draw chart lines — volume_burst alarms have
        # no price level (price=0.0 would draw a bogus line at zero).
        self._alarms = [a for a in alarms if getattr(a, "kind", "price") == "price"]
        for alarm in self._alarms:
            self._build_items(alarm)

    def refresh(self) -> None:
        self.set_data(self._alarms)

    def alarm_count(self) -> int:
        return len(self._alarms)

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _color_for(self, alarm: Alarm) -> str:
        if alarm.triggered:
            return TRIGGERED_COLOR
        if not alarm.active:
            return INACTIVE_COLOR
        if not alarm.sound:
            return MUTED_COLOR
        return ARMED_COLOR

    def _clear_items(self) -> None:
        for items in self._items.values():
            for item in items:
                self._plot.removeItem(item)
        self._items.clear()

    def _build_items(self, alarm: Alarm) -> None:
        if alarm.id is None:
            return
        color = self._color_for(alarm)
        line = pg.InfiniteLine(pos=alarm.price, angle=0, pen=pg.mkPen(color, width=1.4))
        line.setZValue(6)
        line.setMovable(False)
        self._plot.addItem(line)

        label = pg.TextItem(self._label_text(alarm), color=color, anchor=(1, 0.5))
        label.setPos(self._label_x(), alarm.price)
        label.setZValue(7)
        self._plot.addItem(label)

        self._items[alarm.id] = [line, label]

    def _label_text(self, alarm: Alarm) -> str:
        glyph = DIRECTION_GLYPH.get(alarm.direction, "")
        text = f"{glyph} {alarm.price:.4f}"
        if alarm.triggered:
            text += " (hit)"
        elif not alarm.active:
            text += " (off)"
        elif not alarm.sound:
            text += " (muted)"
        if alarm.note:
            text += f" · {alarm.note}"
        return text

    def _label_x(self) -> float:
        """The display-x at which alarm labels are anchored (D21.4).

        After collapse the ViewBox x-model is display-x, so the label uses the
        display-x of the last bar rather than its raw timestamp.
        """
        if self._last_bar_ts is None:
            return 0.0
        cmap = self._collapse_map
        if cmap is None:
            return float(self._last_bar_ts)
        return float(cmap.to_display(self._last_bar_ts))

    def _restyle_alarm(self, alarm: Alarm) -> None:
        items = self._items.get(alarm.id)
        if not items:
            self._build_items(alarm)
            return
        color = self._color_for(alarm)
        line, label = items
        line.setPen(pg.mkPen(color, width=1.4))
        line.setValue(alarm.price)
        label.setColor(color)
        label.setText(self._label_text(alarm))
        label.setPos(self._label_x(), alarm.price)

    # ── Event routing ──────────────────────────────────────────────────────────

    def set_editable(self, editable: bool) -> None:
        """D24: toggle read-only mode (pop-outs stay non-editable)."""
        self._editable = editable
        self._drag = None

    def view_mouse_press(self, ev) -> bool:
        if not self._editable:
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False

        if self._alarm_mode:
            pos = self._view.mapSceneToView(ev.scenePos())
            self.create_requested.emit(float(pos.y()))
            return True

        alarm = self._hit(ev.scenePos())
        if alarm is not None and alarm.id is not None:
            self._drag = {"id": alarm.id}
            return True

        return False

    def view_mouse_drag(self, ev) -> bool:
        if not self._editable:
            return False
        if ev.button() != Qt.MouseButton.LeftButton or self._drag is None:
            return False
        alarm = self._find(self._drag["id"])
        if alarm is None:
            self._drag = None
            return False

        pos = self._view.mapSceneToView(ev.scenePos())
        alarm.price = float(pos.y())
        self._restyle_alarm(alarm)
        if ev.isFinish():
            if alarm.id is not None:
                self.moved.emit(alarm.id, alarm.price)
            self._drag = None
        return True

    def view_mouse_click(self, ev) -> bool:
        if not self._editable:
            return False
        if ev.button() == Qt.MouseButton.RightButton:
            alarm = self._hit(ev.scenePos())
            if alarm is not None:
                self._show_menu(alarm)
                return True
            return False
        self._drag = None
        return False

    def _show_menu(self, alarm: Alarm) -> None:
        if alarm.id is None:
            return
        menu = QMenu()
        rearm = menu.addAction("Rearm")
        mute = menu.addAction("Unmute" if not alarm.sound else "Mute")
        menu.addSeparator()
        delete = menu.addAction("Delete Alarm")
        chosen = menu.exec(QCursor.pos())
        if chosen is rearm:
            self.rearm_requested.emit(alarm.id)
        elif chosen is mute:
            self.mute_toggled.emit(alarm.id, not alarm.sound)
        elif chosen is delete:
            self.delete_requested.emit(alarm.id)

    # ── Hit testing ────────────────────────────────────────────────────────────

    def _hit(self, scene_pos: QPointF) -> Optional[Alarm]:
        if not self._alarms:
            return None
        best = None
        best_dist = ALARM_HIT_TOLERANCE_PX
        for alarm in self._alarms:
            scene_y = self._view.mapViewToScene(QPointF(0.0, alarm.price)).y()
            dist = abs(scene_y - scene_pos.y())
            if dist <= best_dist:
                best = alarm
                best_dist = dist
        return best

    def _find(self, alarm_id: int) -> Optional[Alarm]:
        for alarm in self._alarms:
            if alarm.id == alarm_id:
                return alarm
        return None
