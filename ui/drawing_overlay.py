"""
drawing_overlay.py
Renders user drawings on the price plot and handles the drawing workflow:
tool selection, click-click or click-drag creation, selection, draggable
endpoint/body editing, and deletion.

Drawings are anchored to timestamps in their payload; the overlay maps those
to candle bar indices internally so drawings stay aligned across chart reloads.
Event flows through a DrawingViewBox that routes left-button gestures here so
they do not trigger the default ViewBox pan behavior.
"""

import bisect
from typing import Optional

import pyqtgraph as pg
from PyQt6.QtCore import QObject, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen

from data.models import Drawing, DrawingGroup
from services.drawing_service import (
    DEFAULT_DRAWING_COLOR,
    fib_levels,
    normalize_payload,
)

TOOL_CURSOR = "cursor"
DRAWING_TOOLS = ("trendline", "horizontal", "zone", "fibonacci", "measure")

HANDLE_SIZE = 10
HIT_TOLERANCE_PX = 8
MIN_DRAG_PX = 3


class DrawingViewBox(pg.ViewBox):
    """ViewBox binding left-button gestures to the drawing overlay."""

    def __init__(self, overlay_getter, **kwargs):
        super().__init__(**kwargs)
        self._ov_getter = overlay_getter

    def mousePressEvent(self, ev):
        ov = self._ov_getter()
        if ov is not None and ov.view_mouse_press(ev):
            # Do not take the Qt mouse grabber: pyqtgraph only emits drag/click
            # events while no item has grabbed the mouse. The press is tracked
            # by the overlay itself, so explicitly ignore it here.
            ev.ignore()
            return
        super().mousePressEvent(ev)

    def mouseDragEvent(self, ev, axis=None):
        ov = self._ov_getter()
        if ov is not None and ov.view_mouse_drag(ev):
            ev.accept()
            return
        super().mouseDragEvent(ev, axis)

    def mouseClickEvent(self, ev):
        ov = self._ov_getter()
        if ov is not None and ov.view_mouse_click(ev):
            ev.accept()
            return
        super().mouseClickEvent(ev)


class DrawingOverlay(QObject):
    created = pyqtSignal(object)          # Drawing (no id yet)
    # D27.10: (drawing_id, new payload, color) — the settings path edits
    # colour in-memory, so it must travel with the update to persist.
    updated = pyqtSignal(int, dict, str)
    deleted = pyqtSignal(int)             # drawing_id
    selection_changed = pyqtSignal(int)   # drawing id or -1
    mode_changed = pyqtSignal(str)        # active tool name
    settings_requested = pyqtSignal(object)  # Drawing opened for editing

    def __init__(self, plot: pg.PlotWidget, editable: bool = True):
        super().__init__()
        self._plot = plot
        self._view = plot.getViewBox()
        # D24: pop-out charts are read-only — all mouse interactions that
        # could mutate shared drawings are inert when not editable.
        self._editable = editable

        self._bar_ts: list[int] = []
        # D21.4: the ViewBox x-model is display-x (non-trading time collapsed
        # away) whenever a collapse map is active. Render maps ``ts -> display-x``
        # and drag maps ``display-x -> ts`` through this map.
        self._collapse_map = None
        self._symbol: str = ""
        self._drawings: list[Drawing] = []
        self._groups: dict = {}
        self._items: dict = {}
        self._handles = pg.ScatterPlotItem()
        self._plot.addItem(self._handles)

        self._tool: str = TOOL_CURSOR
        self._active_group_id: Optional[int] = None
        self._active_color: str = DEFAULT_DRAWING_COLOR
        self._selected_id: Optional[int] = None

        self._draft: Optional[dict] = None
        self._drag: Optional[dict] = None

        self._move_proxy = pg.SignalProxy(
            plot.scene().sigMouseMoved, rateLimit=60, slot=self._on_mouse_moved
        )
        try:
            self._view.sigRangeChanged.connect(self._on_view_range_changed)
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_symbol(self, symbol: str):
        self._symbol = symbol

    def set_bars(self, bars) -> None:
        self._bar_ts = [b.ts for b in bars] if bars else []
        self._rerender()

    def set_collapse_map(self, collapse_map) -> None:
        """Set the D21.4 display-x map used for rendering and drag.

        ``None`` (or an identity map) keeps the historical raw-timestamp
        x-model; a non-identity map makes ``_ts_to_x`` render at display-x and
        ``_x_to_ts`` inverse-map a dragged display-x back to its timestamp.
        """
        self._collapse_map = collapse_map
        self._rerender()

    def _rerender(self) -> None:
        """Rebuild existing drawing items at the current display-x positions.

        Called when the bar set or the collapse map changes so time-anchored
        drawings stay on their bars after a timeframe / Ext-Hours collapse
        (AC-D21.4.1). No-op when there are no drawings yet.
        """
        if not self._drawings:
            return
        self._clear_all_items()
        for drawing in self._drawings:
            self._build_items(drawing)
        self._restyle_selected()
        self._refresh_handles()

    def set_data(self, symbol: str, drawings: list[Drawing],
                 groups: list[DrawingGroup]) -> None:
        self._symbol = symbol
        self._clear_draft()
        self._drag = None
        self.clear_selection()
        self._clear_all_items()
        self._drawings = list(drawings)
        self._groups = {g.id: g for g in groups if g.id is not None}
        for drawing in self._drawings:
            self._build_items(drawing)

    def set_groups(self, groups: list[DrawingGroup]) -> None:
        self._groups = {g.id: g for g in groups if g.id is not None}
        self._drag = None
        self._clear_all_items()
        for drawing in self._drawings:
            self._build_items(drawing)
        self._restyle_selected()

    def set_tool(self, tool: str) -> None:
        self._clear_draft()
        self._tool = tool if tool in DRAWING_TOOLS else TOOL_CURSOR
        self.mode_changed.emit(self._tool)
        if self._tool == TOOL_CURSOR and self._drag is not None:
            self._drag = None

    def set_active_group(self, group_id: Optional[int],
                         color: str = DEFAULT_DRAWING_COLOR) -> None:
        if group_id is None or group_id in self._groups:
            self._active_group_id = group_id
            self._active_color = color

    def add_drawing(self, drawing: Drawing) -> None:
        self._clear_draft()
        self._drawings.append(drawing)
        if drawing.id is not None:
            self._build_items(drawing)

    def remove_drawing(self, drawing_id: int) -> None:
        self._remove_items(drawing_id)
        self._drawings = [d for d in self._drawings if d.id != drawing_id]
        if self._selected_id == drawing_id:
            self._selected_id = None
            self._handles.setData([])
            self.selection_changed.emit(-1)

    def delete_selected(self) -> None:
        if self._selected_id is None:
            return
        drawing = self._find_drawing(self._selected_id)
        if drawing is None or drawing.id is None or self._is_locked_group(drawing):
            return
        drawing_id = drawing.id
        self.remove_drawing(drawing_id)
        self.deleted.emit(drawing_id)

    def has_selection(self) -> bool:
        return self._selected_id is not None

    def tool_active(self) -> bool:
        return self._tool != TOOL_CURSOR

    def clear_selection(self) -> None:
        if self._selected_id is not None:
            drawing = self._find_drawing(self._selected_id)
            if drawing is not None:
                self._restore_drawing_style(drawing)
            self._selected_id = None
        self._handles.setData([])
        self.selection_changed.emit(-1)

    # ── Group helpers ──────────────────────────────────────────────────────────

    def _is_locked_group(self, drawing: Drawing) -> bool:
        group = self._groups.get(drawing.group_id)
        return bool(group is not None and group.locked)

    def _is_visible_group(self, drawing: Drawing) -> bool:
        group = self._groups.get(drawing.group_id)
        return bool(group is None or group.visible)

    # ── Coordinate helpers ─────────────────────────────────────────────────────

    def _ts_to_x(self, ts: int) -> float:
        """Map a timestamp to the ViewBox x-coordinate.

        With a D21.4 collapse map active the x-model is display-x, so the
        timestamp is mapped through ``to_display``; otherwise it is the raw
        timestamp (identity).
        """
        cmap = self._collapse_map
        if cmap is None:
            return float(ts)
        return float(cmap.to_display(ts))

    def _x_to_ts(self, x: float) -> int:
        """Inverse-map a ViewBox x-coordinate back to a timestamp.

        With a collapse map active, a dragged display-x is inverse-mapped via
        ``to_ts``; otherwise x is already the timestamp.
        """
        cmap = self._collapse_map
        if cmap is None:
            return int(round(x))
        return int(round(cmap.to_ts(x)))

    def _view_pos(self, ev) -> QPointF:
        return self._view.mapSceneToView(ev.scenePos())

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _clear_all_items(self) -> None:
        for items in self._items.values():
            for item in items:
                self._detach_item(item)
        self._items.clear()
        self._handles.setData([])

    def _detach_item(self, item) -> None:
        """Remove an item from the scene or plot safely.

        Inner price labels are added directly to the scene (not the PlotItem),
        so removeItem must be called on the item's own scene to avoid leaking
        stale labels across rebuilds.
        """
        scene = self._plot.scene()
        if scene is not None and getattr(scene, "dragItem", None) is item:
            scene.dragItem = None
        try:
            it_scene = item.scene()
            if it_scene is not None:
                it_scene.removeItem(item)
        except Exception:
            pass
        try:
            self._plot.removeItem(item)
        except Exception:
            pass

    def _remove_items(self, drawing_id) -> None:
        items = self._items.pop(drawing_id, [])
        for item in items:
            self._detach_item(item)

    def _build_items(self, drawing: Drawing) -> None:
        key = drawing.id if drawing.id is not None else id(drawing)
        self._remove_items(key)
        if not self._is_visible_group(drawing):
            return
        kind = drawing.kind
        color = drawing.color or DEFAULT_DRAWING_COLOR
        try:
            payload = normalize_payload(kind, drawing.payload)
        except ValueError:
            return
        items = []

        if kind == "trendline":
            items.append(pg.PlotDataItem(
                [self._ts_to_x(payload["p1"]["x"]), self._ts_to_x(payload["p2"]["x"])],
                [payload["p1"]["y"], payload["p2"]["y"]],
                pen=pg.mkPen(color, width=1.4),
            ))
            # Inner-right price labels for both endpoints
            items.append(self._add_inner_price_label(payload["p1"]["y"], color))
            items.append(self._add_inner_price_label(payload["p2"]["y"], color))

        elif kind == "horizontal":
            items.append(pg.InfiniteLine(
                pos=payload["y"], angle=0, pen=pg.mkPen(color, width=1.2)
            ))
            items.append(self._add_inner_price_label(payload["y"], color))

        elif kind == "zone":
            brush = QColor(color)
            brush.setAlpha(36)
            region = pg.LinearRegionItem(
                values=(payload["y1"], payload["y2"]),
                orientation="horizontal",
                brush=brush,
                pen=pg.mkPen(color, width=1.0),
                movable=False,
            )
            region.setZValue(-4)
            items.append(region)
            items.append(self._add_inner_price_label(payload["y1"], color))
            items.append(self._add_inner_price_label(payload["y2"], color))

        elif kind == "fibonacci":
            for ratio, price in fib_levels(
                    payload["p1"]["y"], payload["p2"]["y"], payload["type"]):
                line = pg.InfiniteLine(pos=price, angle=0, pen=pg.mkPen(color, width=1.0))
                line.setZValue(-3)
                items.append(line)
                # Level label at inner right (price only, ratio in text)
                label = self._add_inner_price_label(price, color)
                # Keep ratio in text as before but use inner position
                label.setPlainText(f"{ratio * 100:.1f}%  {price:.2f}")
                items.append(label)

        elif kind == "measure":
            x1, y1 = self._ts_to_x(payload["p1"]["x"]), payload["p1"]["y"]
            x2, y2 = self._ts_to_x(payload["p2"]["x"]), payload["p2"]["y"]
            items.append(pg.PlotDataItem([x1, x2], [y1, y2], pen=pg.mkPen(color, width=1.4)))
            dy = y2 - y1
            pct = (dy / y1 * 100.0) if y1 else 0.0
            label = pg.TextItem(f"Δ {dy:+.2f}  ({pct:+.2f}%)", color=color, anchor=(0.5, 1.3))
            label.setPos((x1 + x2) / 2, (y1 + y2) / 2)
            items.append(label)

        for item in items:
            item.setZValue(10)
            # For scene TextItems (inner-right labels), add to scene instead of plot
            # to keep them inside the data area and not clipped by the axis.
            # Distinguish by checking if item is a TextItem with anchor (1,0.5) and high Z
            # — those are inner labels, add to scene.
            try:
                if isinstance(item, pg.TextItem) and item.anchor == pg.Point(1, 0.5) and item.zValue() == 10:
                    scene = self._plot.scene()
                    if scene is not None:
                        scene.addItem(item)
                    else:
                        self._plot.addItem(item)
                else:
                    self._plot.addItem(item)
            except Exception:
                self._plot.addItem(item)
        self._items[key] = items
        # Update inner label positions for stacking
        self._update_inner_labels()

    def _add_inner_price_label(self, price: float, color: str) -> pg.TextItem:
        """Create a price label anchored inside the plot at the right edge (not yet added).

        Positioning and stacking are finalized by _update_inner_labels(), which runs
        after every rebuild and on every view-range change.
        """
        label = pg.TextItem(f"{price:.2f}", color=color, anchor=(1, 0.5))
        label.setZValue(10)
        try:
            vb = self._view
            view_rect_scene = vb.mapRectToScene(vb.rect())
            scene_y = vb.mapViewToScene(pg.Point(0, price)).y()
            scene_y = max(view_rect_scene.top(), min(view_rect_scene.bottom(), scene_y))
            label.setPos(view_rect_scene.right() - 4, scene_y)
        except Exception:
            try:
                label.setPos(
                    self._ts_to_x(self._bar_ts[-1]) if self._bar_ts else 0, price
                )
            except Exception:
                label.setPos(0, price)
        return label

    def _is_inner_price_label(self, item) -> bool:
        try:
            return (isinstance(item, pg.TextItem)
                    and item.anchor == pg.Point(1, 0.5)
                    and item.zValue() == 10)
        except Exception:
            return False

    def _label_scene_height(self, item) -> float:
        """Measured height of a label's scene bounding box, in scene units.

        Uses the same graphical measurement the tests rely on
        (``mapRectToScene(item.boundingRect())``); falls back to
        ``sceneBoundingRect()`` and finally to 0.0 when the item is not yet
        laid out. A real 9 pt label is ~23 px tall, so a hard-coded 15 px
        centre offset lets consecutive boxes overlap.
        """
        try:
            height = item.mapRectToScene(item.boundingRect()).height()
        except Exception:
            height = 0.0
        if not height or height <= 0:
            try:
                height = item.sceneBoundingRect().height()
            except Exception:
                height = 0.0
        try:
            return float(height) if height and height > 0 else 0.0
        except Exception:
            return 0.0

    def _update_inner_labels(self):
        """Reposition all inner-right labels to the right edge with stacking.

        Labels are sorted by scene-y (top to bottom); any label closer than the
        measured label bounding-box height (never less than 15 px) to the
        previously placed one is pushed down so prices remain legible when
        drawings share similar levels. Because the offset comes from the
        emitted TextItem's scene bbox, consecutive label boxes never intersect.
        The whole label box is clamped inside view_rect.
        """
        try:
            vb = self._view
            if vb.scene() is None:
                return
            view_rect_scene = vb.mapRectToScene(vb.rect())
            entries = []
            for items in self._items.values():
                for item in items:
                    if not self._is_inner_price_label(item):
                        continue
                    try:
                        txt = item.toPlainText().strip()
                        price = float(txt.split()[-1]) if txt else None
                    except Exception:
                        price = None
                    if price is None:
                        continue
                    scene_y = vb.mapViewToScene(pg.Point(0, price)).y()
                    entries.append((item, scene_y))
            entries.sort(key=lambda t: t[1])
            last_y = None
            last_height = 0.0
            for item, y in entries:
                height = self._label_scene_height(item)
                half = height / 2.0
                top_limit = view_rect_scene.top() + half
                bottom_limit = view_rect_scene.bottom() - half
                if top_limit > bottom_limit:
                    mid = (view_rect_scene.top() + view_rect_scene.bottom()) / 2.0
                    top_limit = bottom_limit = mid
                y = max(top_limit, min(bottom_limit, y))
                # Stack by at least the measured bbox height (never below 15px)
                # so consecutive label boxes cannot intersect.
                offset = max(15.0, height, last_height)
                if last_y is not None and y - last_y < offset:
                    y = min(last_y + offset, bottom_limit)
                last_y = y
                last_height = height
                item.setPos(view_rect_scene.right() - 4, y)
        except Exception:
            pass

    def _on_view_range_changed(self):
        self._update_inner_labels()

    def _restore_drawing_style(self, drawing: Drawing) -> None:
        key = drawing.id if drawing.id is not None else id(drawing)
        self._remove_items(key)
        self._build_items(drawing)

    def _style_selected(self, drawing: Drawing) -> None:
        key = drawing.id if drawing.id is not None else id(drawing)
        for item in self._items.get(key, []):
            if isinstance(item, (pg.InfiniteLine, pg.PlotDataItem)):
                item.setPen(pg.mkPen("#ffffff", width=2.0))

    def _restyle_selected(self) -> None:
        if self._selected_id is None:
            return
        drawing = self._find_drawing(self._selected_id)
        if drawing is not None:
            self._style_selected(drawing)
        self._refresh_handles()

    def _refresh_handles(self) -> None:
        drawing = self._find_drawing(self._selected_id)
        if drawing is None or drawing.id is None or self._is_locked_group(drawing):
            self._handles.setData([])
            return
        try:
            payload = normalize_payload(drawing.kind, drawing.payload)
        except ValueError:
            self._handles.setData([])
            return
        spots = []
        for i, (ts, price) in enumerate(self._handle_points(drawing.kind, payload)):
            spots.append({
                "pos": (self._ts_to_x(ts), price),
                "size": HANDLE_SIZE,
                "symbol": "o",
                "pen": pg.mkPen("#ffffff", width=1.5),
                "brush": pg.mkBrush("#0ea5e9"),
                "data": (drawing.id, i),
            })
        self._handles.setData(spots)

    def _handle_points(self, kind: str, payload: dict) -> list[tuple[int, float]]:
        if kind in ("trendline", "fibonacci", "measure"):
            return [(payload["p1"]["x"], payload["p1"]["y"]),
                    (payload["p2"]["x"], payload["p2"]["y"])]
        if kind == "horizontal":
            return [(0, payload["y"])]
        if kind == "zone":
            return [(payload["x1"], payload["y1"]),
                    (payload["x2"], payload["y2"])]
        return []

    # ── Hit testing (pixel space) ──────────────────────────────────────────────

    def _scene(self, x: float, y: float) -> QPointF:
        return self._view.mapViewToScene(QPointF(x, y))

    def _dist_px(self, a: QPointF, b: QPointF) -> float:
        return ((a.x() - b.x()) ** 2 + (a.y() - b.y()) ** 2) ** 0.5

    def _dist_segment_px(self, p: QPointF, a: QPointF, b: QPointF) -> float:
        abx, aby = b.x() - a.x(), b.y() - a.y()
        apx, apy = p.x() - a.x(), p.y() - a.y()
        denom = abx * abx + aby * aby
        if denom <= 0:
            return self._dist_px(p, a)
        t = max(0.0, min(1.0, (apx * abx + apy * aby) / denom))
        return self._dist_px(p, QPointF(a.x() + t * abx, a.y() + t * aby))

    def _hit_drawing(self, scene_pos: QPointF) -> Optional[Drawing]:
        for drawing in reversed(self._drawings):
            if drawing.id is None or not self._is_visible_group(drawing):
                continue
            try:
                payload = normalize_payload(drawing.kind, drawing.payload)
            except ValueError:
                continue
            kind = drawing.kind

            if kind in ("trendline", "measure"):
                a = self._scene(self._ts_to_x(payload["p1"]["x"]), payload["p1"]["y"])
                b = self._scene(self._ts_to_x(payload["p2"]["x"]), payload["p2"]["y"])
                if self._dist_segment_px(scene_pos, a, b) <= HIT_TOLERANCE_PX:
                    return drawing

            elif kind == "fibonacci":
                for _ratio, price in fib_levels(
                        payload["p1"]["y"], payload["p2"]["y"], payload["type"]):
                    y_scene = self._scene(0, price).y()
                    if abs(scene_pos.y() - y_scene) <= HIT_TOLERANCE_PX:
                        return drawing

            elif kind == "horizontal":
                y_scene = self._scene(0, payload["y"]).y()
                if abs(scene_pos.y() - y_scene) <= HIT_TOLERANCE_PX:
                    return drawing

            elif kind == "zone":
                # Scene y grows downward: top edge = scene of max price (smaller y)
                top_y = self._scene(0, max(payload["y1"], payload["y2"])).y()
                bottom_y = self._scene(0, min(payload["y1"], payload["y2"])).y()
                if top_y <= scene_pos.y() <= bottom_y:
                    return drawing
        return None

    def _hit_handle(self, view_pos: QPointF):
        for spot in self._handles.pointsAt(view_pos):
            if spot.data() is not None:
                return spot.data()
        return None

    # ── ViewBox event routing ──────────────────────────────────────────────────

    def set_editable(self, editable: bool) -> None:
        """D24: toggle read-only mode (pop-outs stay non-editable)."""
        self._editable = editable
        self._drag = None

    def view_mouse_press(self, ev) -> bool:
        if not self._editable:
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False
        pos = self._view_pos(ev)
        if self._tool != TOOL_CURSOR:
            if self._draft is None:
                self._start_draft(ev.scenePos(), pos)
            else:
                self._commit_draft(pos)
            return True

        handle = self._hit_handle(pos)
        if handle is not None:
            drawing_id, point_index = handle
            drawing = self._find_drawing(drawing_id)
            if drawing is not None:
                self._select(drawing_id)
                self._drag = {
                    "id": drawing_id, "point_index": point_index, "body": False,
                    "locked": self._is_locked_group(drawing),
                    "grab": (pos.x(), pos.y()),
                }
            return True

        drawing = self._hit_drawing(ev.scenePos())
        if drawing is not None and drawing.id is not None:
            self._select(drawing.id)
            self._drag = {
                "id": drawing.id, "point_index": -1, "body": True,
                "locked": self._is_locked_group(drawing),
                "grab": (pos.x(), pos.y()),
            }
            return True

        if self._selected_id is not None:
            self.clear_selection()
        return False

    def view_mouse_drag(self, ev) -> bool:
        if not self._editable:
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False
        pos = self._view_pos(ev)

        if self._tool != TOOL_CURSOR:
            if self._draft is not None:
                self._update_draft(ev.scenePos(), pos)
                if ev.isFinish():
                    self._commit_draft(pos)
            return True

        if self._drag is not None and not self._drag["locked"]:
            self._apply_drag(pos)
            if ev.isFinish():
                self._drag = None
            return True

        return False

    def view_mouse_click(self, ev) -> bool:
        if not self._editable:
            return False
        # A click (no drag) ends any pending drag session.
        was_drag = self._drag is not None
        self._drag = None
        # Double-click on a zone / horizontal line opens its settings dialog.
        try:
            is_double = ev.double()
        except Exception:
            is_double = False
        if is_double and ev.button() == Qt.MouseButton.LeftButton:
            drawing = self._hit_drawing(ev.scenePos())
            if drawing is not None and drawing.id is not None and drawing.kind in ("zone", "horizontal"):
                if not self._is_locked_group(drawing):
                    self.settings_requested.emit(drawing)
                    return True
        return False

    # ── Draft (tool mode) ──────────────────────────────────────────────────────

    def _start_draft(self, scene_pos: QPointF, pos: QPointF) -> None:
        item = pg.PlotDataItem([], [], pen=self._preview_pen())
        item.setZValue(9)
        self._plot.addItem(item)
        self._draft = {
            "kind": self._tool,
            "anchor_ts": self._x_to_ts(pos.x()),
            "anchor_y": pos.y(),
            "press_scene": QPointF(scene_pos.x(), scene_pos.y()),
            "moved": False,
            "preview": [item],
        }

    def _on_mouse_moved(self, evs) -> None:
        if self._draft is None or self._tool == TOOL_CURSOR:
            return
        scene_pos = evs[0]
        self._update_draft(scene_pos, self._view.mapSceneToView(scene_pos))

    def _update_draft(self, scene_pos: QPointF, pos: QPointF) -> None:
        if self._draft is None:
            return
        if self._dist_px(scene_pos, self._draft["press_scene"]) > MIN_DRAG_PX:
            self._draft["moved"] = True
        view_pos = self._view.mapViewToScene(pos)
        self._update_preview(self._x_to_ts(pos.x()), view_pos.y())

    def _preview_pen(self) -> QPen:
        return pg.mkPen("#93c5fd", width=1.2, style=Qt.PenStyle.DashLine)

    def _update_preview(self, ts2: int, y2: float) -> None:
        if self._draft is None:
            return
        for item in self._draft["preview"]:
            self._plot.removeItem(item)
        kind = self._draft["kind"]
        x1 = self._ts_to_x(self._draft["anchor_ts"])
        x2 = self._ts_to_x(ts2)
        anchor_y = self._draft["anchor_y"]

        if kind in ("trendline", "measure"):
            new = pg.PlotDataItem([x1, x2], [anchor_y, y2], pen=self._preview_pen())
        elif kind == "horizontal":
            new = pg.InfiniteLine(pos=y2, angle=0, pen=self._preview_pen())
        elif kind == "zone":
            brush = QColor("#93c5fd")
            brush.setAlpha(28)
            new = pg.LinearRegionItem(
                values=(min(anchor_y, y2), max(anchor_y, y2)),
                orientation="horizontal",
                brush=brush,
                pen=self._preview_pen(),
            )
        elif kind == "fibonacci":
            new = pg.PlotDataItem([x1, x2], [anchor_y, y2], pen=self._preview_pen())
        else:
            new = pg.PlotDataItem()
        new.setZValue(9)
        self._plot.addItem(new)
        self._draft["preview"] = [new]

    def _commit_draft(self, pos: QPointF) -> None:
        if self._draft is None:
            return
        draft = self._draft
        kind = draft["kind"]
        ts2 = self._x_to_ts(pos.x())
        y2 = pos.y()
        group = self._groups.get(self._active_group_id)
        color = group.color if (group and group.color) else self._active_color

        if kind == "trendline":
            payload = {"p1": {"x": draft["anchor_ts"], "y": draft["anchor_y"]},
                       "p2": {"x": ts2, "y": y2}}
        elif kind == "measure":
            payload = {"p1": {"x": draft["anchor_ts"], "y": draft["anchor_y"]},
                       "p2": {"x": ts2, "y": y2}}
        elif kind == "horizontal":
            payload = {"y": y2}
        elif kind == "zone":
            payload = {"x1": draft["anchor_ts"], "x2": ts2,
                       "y1": draft["anchor_y"], "y2": y2}
        elif kind == "fibonacci":
            payload = {"p1": {"x": draft["anchor_ts"], "y": draft["anchor_y"]},
                       "p2": {"x": ts2, "y": y2}, "type": "retr"}
        else:
            payload = {}

        try:
            payload = normalize_payload(kind, payload)
        except ValueError:
            self._clear_draft()
            return
        self._clear_draft()
        self.created.emit(Drawing(
            symbol=self._symbol,
            kind=kind,
            payload=payload,
            color=color,
            group_id=self._active_group_id,
        ))

    def _clear_draft(self) -> None:
        if self._draft:
            for item in self._draft["preview"]:
                self._plot.removeItem(item)
        self._draft = None

    # ── Drag editing (cursor mode) ─────────────────────────────────────────────

    def _apply_drag(self, pos: QPointF) -> None:
        if self._drag is None:
            return
        drawing = self._find_drawing(self._drag["id"])
        if drawing is None:
            return
        try:
            payload = normalize_payload(drawing.kind, drawing.payload)
        except ValueError:
            return
        kind = drawing.kind
        drag = self._drag
        dx_ts = self._x_to_ts(pos.x()) - self._x_to_ts(drag["grab"][0])
        dy = pos.y() - drag["grab"][1]

        if not drag["body"]:
            if kind in ("trendline", "measure", "fibonacci"):
                target = "p1" if drag["point_index"] == 0 else "p2"
                payload[target] = {"x": self._x_to_ts(pos.x()), "y": pos.y()}
            elif kind == "horizontal":
                payload["y"] = pos.y()
            elif kind == "zone":
                payload["y1" if drag["point_index"] == 0 else "y2"] = pos.y()
        else:
            if kind in ("trendline", "measure", "fibonacci"):
                payload["p1"]["x"] += dx_ts
                payload["p1"]["y"] += dy
                payload["p2"]["x"] += dx_ts
                payload["p2"]["y"] += dy
            elif kind == "horizontal":
                payload["y"] = pos.y()
            elif kind == "zone":
                payload["y1"] += dy
                payload["y2"] += dy

        try:
            payload = normalize_payload(kind, payload)
        except ValueError:
            return
        drawing.payload = payload

        # Update items in place instead of removing/recreating to avoid
        # pyqtgraph scene dragItem reference to deleted C++ objects
        key = drawing.id if drawing.id is not None else id(drawing)
        items = self._items.get(key, [])

        if kind == "trendline":
            # items[0] is PlotDataItem
            if items:
                x1 = self._ts_to_x(payload["p1"]["x"])
                x2 = self._ts_to_x(payload["p2"]["x"])
                items[0].setData([x1, x2], [payload["p1"]["y"], payload["p2"]["y"]])

        elif kind == "horizontal":
            # items[0] is InfiniteLine
            if items:
                items[0].setPos(payload["y"])

        elif kind == "zone":
            # items[0] is LinearRegionItem
            if items:
                items[0].setRegion((payload["y1"], payload["y2"]))

        elif kind == "fibonacci":
            # items: [InfiniteLine, TextItem, InfiniteLine, TextItem, ...]
            # Update in place if number of levels matches, else rebuild
            new_levels = list(fib_levels(
                payload["p1"]["y"], payload["p2"]["y"], payload["type"]))
            num_new = len(new_levels)
            num_existing_lines = (len(items) + 1) // 2  # each level has line + label
            
            if num_new == num_existing_lines:
                # Update existing items in place
                for i, (ratio, price) in enumerate(new_levels):
                    line_idx = i * 2
                    label_idx = i * 2 + 1
                    if line_idx < len(items):
                        items[line_idx].setPos(price)
                    if label_idx < len(items):
                        items[label_idx].setText(f"{ratio * 100:.1f}%  {price:.2f}")
                        items[label_idx].setPos(
                            self._ts_to_x(self._bar_ts[-1]) if self._bar_ts else 0,
                            price,
                        )
            else:
                # Number of levels changed, need to rebuild
                self._restore_drawing_style(drawing)
                self._style_selected(drawing)
                self._refresh_handles()
                self.updated.emit(int(drawing.id), payload, drawing.color)
                return

        elif kind == "measure":
            # items[0] is PlotDataItem, items[1] is TextItem
            if items:
                x1, y1 = self._ts_to_x(payload["p1"]["x"]), payload["p1"]["y"]
                x2, y2 = self._ts_to_x(payload["p2"]["x"]), payload["p2"]["y"]
                items[0].setData([x1, x2], [y1, y2])
                dy_val = y2 - y1
                pct = (dy_val / y1 * 100.0) if y1 else 0.0
                if len(items) > 1:
                    items[1].setText(f"Δ {dy_val:+.2f}  ({pct:+.2f}%)")
                    items[1].setPos((x1 + x2) / 2, (y1 + y2) / 2)

        # For non-fibonacci, apply selection styling and refresh handles
        self._style_selected(drawing)
        self._refresh_handles()
        self.updated.emit(int(drawing.id), payload, drawing.color)

    def _select(self, drawing_id: int) -> None:
        prev_id = self._selected_id
        if prev_id is not None and prev_id != drawing_id:
            prev = self._find_drawing(prev_id)
            if prev is not None:
                self._restore_drawing_style(prev)
        self._selected_id = drawing_id
        drawing = self._find_drawing(drawing_id)
        if drawing is not None:
            self._style_selected(drawing)
        self._refresh_handles()
        self.selection_changed.emit(drawing_id)

    def _find_drawing(self, drawing_id) -> Optional[Drawing]:
        if drawing_id is None:
            return None
        for drawing in self._drawings:
            if drawing.id == drawing_id:
                return drawing
        return None