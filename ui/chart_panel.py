"""
chart_panel.py
Main chart widget: price plot (candlestick + indicator overlays)
+ volume subplot linked on the X-axis.
Supports 5 render modes and dynamic study overlays.
"""

import hashlib
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSplitter
from PyQt6.QtCore import Qt, QEvent, pyqtSignal

from ui.candlestick_item import CandlestickItem, ChartMode
from ui.drawing_overlay import DrawingViewBox, DrawingOverlay, TOOL_CURSOR
from ui.alarm_overlay import AlarmOverlay
from ui.chart_mouse_router import ChartMouseRouter, RouterMode
from ui.overlays.gap_overlay import RthGapOverlay
from ui.overlays.vix_overlay import VixOverlay
from ui.overlays.ict_overlay import ICTStudyOverlay
from pyqtgraph.graphicsItems.DateAxisItem import TickSpec, ZoomLevel, makeSStepper, DAY_SPACING, HOUR_SPACING
from datetime import timezone, timedelta


def _custom_date_axis(utc: bool = True, tz_offset: int = 0) -> "pg.DateAxisItem":
    """Create a DateAxisItem with custom MM/DD HH:MM format via zoom levels.
    
    Args:
        utc: If True, use UTC. If False, use local timezone.
        tz_offset: Timezone offset in seconds (positive for timezones behind UTC like ET).
                   e.g., 18000 for EST, 14400 for EDT.
    """
    import pyqtgraph as pg
    axis = pg.DateAxisItem(utc=utc)
    # Adjust utcOffset for non-UTC display
    if tz_offset != 0:
        axis.utcOffset = tz_offset
    custom_zoom = ZoomLevel([
        TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), '%m/%d'),
        TickSpec(HOUR_SPACING, makeSStepper(HOUR_SPACING), '%H:%M', autoSkip=[1, 6]),
    ], 'MM/DD HH:MM')
    axis.zoomLevels[5 * 3600 * 24] = custom_zoom  # Replace DAY_HOUR_ZOOM_LEVEL
    return axis


# D8 / RG-002: the single pinned volume nice-number family. The old fixed list
# [10k .. 10M] is retained ONLY as a regression fixture in
# tests/test_volume_linear.py and is never a live code path.
VOLUME_NICE_MANTISSAS = (1.0, 1.5, 2.0, 2.5, 5.0, 7.5)
VOLUME_NICE_FLOOR = 100.0


def _volume_nice_family(max_exponent: int = 12) -> tuple[float, ...]:
    """Return the pinned volume family ``1 / 1.5 / 2 / 2.5 / 5 / 7.5 x 10^k`` (RG-002).

    Values are generated from ``1 x 10^2`` — the required ``100`` floor
    (AC-D8.4) — upward, so the sequence scales with ``k`` and has no fixed
    ceiling. This is the only live volume nice-number family; the old fixed
    ``[10k .. 10M]`` list is a test fixture only.
    """
    values: list[float] = []
    for k in range(2, max_exponent + 1):
        base = 10.0 ** k
        for mantissa in VOLUME_NICE_MANTISSAS:
            values.append(mantissa * base)
    return tuple(values)


def _nice_volume_max(max_vol: float) -> float:
    """Return the smallest pinned-family value ``>= max_vol * 1.1``.

    Family (RG-002 / AC-D8.1): ``1 / 1.5 / 2 / 2.5 / 5 / 7.5 x 10^k``, floored at
    ``100`` with no fixed ceiling. ``max_vol == 0`` (or any target at or below the
    floor) returns ``100`` (AC-D8.4). This replaces the coarse fixed
    ``[10k .. 10M]`` list whose ``10k`` floor and 5M fallback are the
    ESC-003 / ESC-008 defects.
    """
    if max_vol <= 0:
        return VOLUME_NICE_FLOOR
    target = float(max_vol) * 1.1
    if target <= VOLUME_NICE_FLOOR:
        return VOLUME_NICE_FLOOR
    k = 2
    while True:
        base = 10.0 ** k
        for mantissa in VOLUME_NICE_MANTISSAS:
            value = mantissa * base
            if value >= target:
                return value
        k += 1


def _format_volume_tick(value: float) -> str:
    """Format a volume-axis tick as ``500.0K`` / ``1.0M`` (AC-D8.3)."""
    v = float(value)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}K"
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


class _VolumeAxisItem(pg.AxisItem):
    """Right axis for the volume subplot using the D8 tick formatter (AC-D8.3)."""

    def tickStrings(self, values, scale, spacing):
        return [_format_volume_tick(v * scale) for v in values]


from services.indicator_service import (
    calculate_sma, calculate_ema, calculate_vwap,
    calculate_bollinger_bands, calculate_rsi, calculate_macd,
)
from services.gap_vix_service import (
    calculate_rth_gaps,
    calculate_vix_standard_deviation,
    infer_ticker_context,
)
from services.ict_service import calculate_ict_concepts
from services.session_service import session_bands
from ui.overlays.session_overlay import SessionOverlay
from ui.zoom_overlay import ZoomOverlay

# Oscillator studies rendered in a third subplot
OSCILLATOR_TYPES = {"rsi", "macd"}


class _StudyCache:
    """Cache for computed study values keyed by (symbol, timeframe, studies_hash).

    Stores computed arrays so that on intra-bar ticks or new candles,
    only the latest values need recomputation for the new bar.
    """

    def __init__(self):
        self._cache: dict[str, dict] = {}

    def _studies_hash(self, studies: list) -> str:
        """Compute a hash of the enabled study configurations."""
        enabled = [(s["type"], s.get("params", {}))
                   for s in studies if s.get("enabled")]
        return hashlib.md5(str(enabled).encode()).hexdigest()[:16]

    def _key(self, symbol: str, timeframe: str, studies_hash: str) -> str:
        return f"{symbol}:{timeframe}:{studies_hash}"

    def get(self, symbol: str, timeframe: str, studies: list) -> dict | None:
        """Return cached study arrays if valid for current studies."""
        h = self._studies_hash(studies)
        k = self._key(symbol, timeframe, h)
        return self._cache.get(k)

    def set(self, symbol: str, timeframe: str, studies: list, data: dict):
        h = self._studies_hash(studies)
        k = self._key(symbol, timeframe, h)
        self._cache[k] = data

    def invalidate(self, symbol: str | None = None, timeframe: str | None = None):
        """Invalidate cache entries. If symbol/timeframe is None, clear all."""
        if symbol is None and timeframe is None:
            self._cache.clear()
        else:
            prefix = f"{symbol or '*'}:{timeframe or '*'}"
            to_del = [k for k in self._cache if k.startswith(prefix)]
            for k in to_del:
                self._cache.pop(k, None)


# D2 / Q33 crosshair price chip: the chip renders in the Y-axis lane (outside
# the plot, right of the vertical axis line) as a grey pill with white text.
# Axis tick-label overlap is by design (no deconfliction offset), so the lane
# is reserved wide enough for a long price to keep the pill unclipped and
# clear of a right-side dock.
PRICE_TAG_FILL = "#4b5563"
PRICE_TAG_TEXT_COLOR = "#ffffff"
PRICE_TAG_PAD = 3.0
PRICE_TAG_LANE_SAMPLE = "123,456.78"


class ChartPanel(QWidget):
    # AC-D3.9: emitted when the magnifier is refused because alarm placement is armed.
    zoom_refused = pyqtSignal()

    def __init__(self, tz_offset: int = 0):
        super().__init__()
        self._bars: list = []
        self._studies: list = []
        self._overlay_items: list = []
        self._osc_items: list = []
        self._symbol: str = ""
        self._current_timeframe: str | None = None
        self._study_cache = _StudyCache()
        self._tz_offset = tz_offset  # timezone offset in seconds (positive behind UTC, e.g., 18000 for EST, 14400 for EDT)

        # ESC-007 / AC-D8.6: cached running volume max and the ceiling last
        # applied to the volume ViewBox. Rebuilt O(N) on a load / new bar and
        # widened O(1) on intra-bar ticks (the forming last bar grows live).
        self._vol_max: float = 0.0
        self._volume_nice_max: float = VOLUME_NICE_FLOOR

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Price plot ────────────────────────────────────────────────────────
        self.drawing_overlay = None
        self.alarm_overlay = None
        self.mouse_router = ChartMouseRouter()

        # Create PlotWidget with default ViewBox so DateAxisItem links properly
        self.price_plot = pg.PlotWidget()
        self.price_plot.showGrid(x=True, y=True, alpha=0.08)
        self.price_plot.hideAxis('left')
        self.price_plot.showAxis('right')
        self.price_plot.getAxis('right').setStyle(tickFont=None)
        # X-axis: actual timestamps using DateAxisItem with timezone support
        date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.price_plot.setAxisItems({'bottom': date_axis})

        # Monkey-patch the default ViewBox for custom mouse-gesture handling
        vb = self.price_plot.getViewBox()
        router_ref = self._router_ref

        def _ov_getter():
            return self.drawing_overlay

        orig_mousePressEvent = vb.mousePressEvent
        orig_mouseDragEvent = vb.mouseDragEvent
        orig_mouseClickEvent = vb.mouseClickEvent

        def mousePressEvent(ev):
            if self.mouse_router.view_mouse_press(ev):
                ev.ignore()
                return
            orig_mousePressEvent(ev)

        def mouseDragEvent(ev, axis=None):
            if self.mouse_router.view_mouse_drag(ev):
                ev.accept()
                return
            orig_mouseDragEvent(ev, axis)

        def mouseClickEvent(ev):
            if self.mouse_router.view_mouse_click(ev):
                ev.accept()
                return
            orig_mouseClickEvent(ev)

        vb.mousePressEvent = mousePressEvent  # type: ignore[method-assign]
        vb.mouseDragEvent = mouseDragEvent  # type: ignore[method-assign]
        vb.mouseClickEvent = mouseClickEvent  # type: ignore[method-assign]

        self.candlestick = CandlestickItem([], mode=ChartMode.CANDLES)
        self.price_plot.addItem(self.candlestick)
        self.drawing_overlay = DrawingOverlay(self.price_plot)
        self.alarm_overlay = AlarmOverlay(self.price_plot)
        self.mouse_router.drawing = self.drawing_overlay
        self.mouse_router.alarm = self.alarm_overlay

        # Create crosshair for hover display
        self._create_crosshair()

        # Track mouse moves for the crosshair. NOTE: sigMouseHover emits the
        # list of hovered *items* (whose scenePos() is the item origin), not a
        # position; sigMouseMoved emits the cursor's scene position.
        vb = self.price_plot.getViewBox()
        vb.scene().sigMouseMoved.connect(self._on_mouse_moved)

        # Crosshair cursor over the chart; Qt restores the arrow automatically
        # once the mouse leaves the widget.
        viewport = self.price_plot.viewport()
        viewport.setCursor(Qt.CursorShape.CrossCursor)
        viewport.installEventFilter(self)

        # Advanced study renderers
        self._gap_overlay = RthGapOverlay(self.price_plot)
        self._vix_overlay = VixOverlay(self.price_plot)
        self._ict_overlay = ICTStudyOverlay(self.price_plot)
        self._session_overlay = SessionOverlay(self.price_plot)
        self._ext_hours = True

        # ── Volume plot ───────────────────────────────────────────────────────
        self.volume_plot = pg.PlotWidget()
        self.volume_plot.setMaximumHeight(120)
        self.volume_plot.showGrid(x=True, y=True, alpha=0.05)
        self.volume_plot.hideAxis('left')
        # Right axis uses the D8 volume tick formatter (AC-D8.3: 500.0K / 1.0M).
        self.volume_plot.setAxisItems({'right': _VolumeAxisItem(orientation='right')})
        self.volume_plot.showAxis('right')
        self.volume_plot.getAxis('right').setStyle(tickFont=None)
        self.volume_plot.setXLink(self.price_plot)
        # Use DateAxisItem for volume too, with proper formatting
        vol_date_axis = _custom_date_axis(utc=(self._tz_offset == 0), tz_offset=self._tz_offset)
        self.volume_plot.setAxisItems({'bottom': vol_date_axis})
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.volume_plot.addItem(self.volume_bars)
        # Linear Y for volume — dynamic nice ticks, no negatives (see D8)
        try:
            self.volume_plot.getViewBox().setLogMode('y', False)
        except Exception:
            pass

        # ── Oscillator plot (RSI / MACD) ──────────────────────────────────────
        self.osc_plot = pg.PlotWidget()
        self.osc_plot.setMaximumHeight(120)
        self.osc_plot.showGrid(x=True, y=True, alpha=0.05)
        self.osc_plot.hideAxis('left')
        self.osc_plot.showAxis('right')
        self.osc_plot.getAxis('right').setStyle(tickFont=None)
        self.osc_plot.setXLink(self.price_plot)
        self.osc_plot.hide()            # hidden until an oscillator study is enabled

        self._splitter.addWidget(self.price_plot)
        self._splitter.addWidget(self.volume_plot)
        self._splitter.addWidget(self.osc_plot)
        self._splitter.setSizes([600, 120, 120])
        layout.addWidget(self._splitter)

        # Volume show/hide toggle — top left of volume panel (bottom left of price chart).
        # RC-4a: the affordance is the checkable text label "Volume" (no eye
        # icon or bar glyph); the checkable behaviour is retained.
        from PyQt6.QtWidgets import QPushButton as _VolumeToggleButton
        self._volume_toggle = _VolumeToggleButton("Volume", self)
        self._volume_toggle.setCheckable(True)
        self._volume_toggle.setChecked(True)
        self._volume_toggle.setToolTip("Show/hide volume panel")
        self._volume_toggle.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 6px; background: rgba(30,30,30,0.9); border: 1px solid #4b5563; border-radius: 4px; color: #e5e7eb; } QPushButton:checked { background: rgba(52,211,153,0.15); }")
        self._volume_toggle.toggled.connect(self._on_volume_toggled)
        self._volume_toggle.show()
        self._volume_toggle.raise_()
        self._position_volume_toggle()

        # Zoom control cluster (top-right outlined) — floats over chart area
        from ui.chart_controls import ChartControls
        self._chart_controls = ChartControls(self)
        self._chart_controls.raise_()
        self._chart_controls.show()
        # Keep controls fully inside chart area, left of the price axis
        self._position_zoom_controls()
        # Wire zoom signals
        self._chart_controls.zoom_in.connect(lambda: self._zoom_by(0.8))
        self._chart_controls.zoom_out.connect(lambda: self._zoom_by(1.25))
        self._chart_controls.reset.connect(self._reset_view)
        # Zoom overlay (magnifier)
        self._zoom_overlay = ZoomOverlay(self.price_plot)
        self.mouse_router.zoom = self._zoom_overlay
        self._chart_controls.magnify_toggled.connect(self.set_zoom_mode)
        # Drawing settings dialogs (D12 / D15)
        self.drawing_overlay.settings_requested.connect(self._on_drawing_settings_requested)

    def _on_drawing_settings_requested(self, drawing):
        """Open the matching settings dialog for a zone / horizontal line."""
        from ui.zone_settings_dialog import ZoneSettingsDialog
        from ui.horizontal_line_settings_dialog import HorizontalLineSettingsDialog
        if drawing.kind == "zone":
            dlg = ZoneSettingsDialog(drawing, parent=self)
        elif drawing.kind == "horizontal":
            dlg = HorizontalLineSettingsDialog(drawing, parent=self)
        else:
            return
        if dlg.exec():
            payload, color = dlg.get_updated_drawing()
            drawing.payload = payload
            drawing.color = color
            self.drawing_overlay._restore_drawing_style(drawing)
            if drawing.id is not None:
                self.drawing_overlay.updated.emit(drawing.id, payload)

    # ── Public API ─────────────────────────────────────────────────────────────

    def _router_ref(self):
        return self.mouse_router

    def _on_mouse_moved(self, scene_pos):
        """Track mouse moves to position the crosshair."""
        self._update_crosshair(scene_pos)

    def _position_zoom_controls(self):
        if not hasattr(self, "_chart_controls") or self._chart_controls is None:
            return
        try:
            axis_w = self.price_plot.getAxis('right').width()
        except Exception:
            axis_w = 50
        # The price-chip lane may be reserved wider than the laid-out axis
        # (D2/Q33, AC-D2.1); keep the floating controls clear of it too.
        axis_w = max(axis_w, getattr(self, "_price_lane_width", 0))
        if axis_w < 20:
            axis_w = 50
        margin = 12
        x = self.width() - self._chart_controls.width() - axis_w - margin
        if x < 8:
            x = 8
        self._chart_controls.move(int(x), 10)
        self._chart_controls.raise_()

    def _position_volume_toggle(self):
        if not hasattr(self, "_volume_toggle") or self._volume_toggle is None:
            return
        # Top left of volume panel = bottom left of price chart; map volume_plot to ChartPanel
        try:
            # volume_plot geometry in ChartPanel coords
            vol_geo = self.volume_plot.geometry()
            # If volume is hidden, its geometry height is 0; place at bottom of price_plot
            if not self.volume_plot.isVisible() or vol_geo.height() <= 5:
                # place at bottom left of price_plot area
                price_geo = self.price_plot.geometry()
                x = price_geo.left() + 8
                y = price_geo.bottom() - self._volume_toggle.height() - 4
            else:
                x = vol_geo.left() + 8
                y = vol_geo.top() + 4
            self._volume_toggle.move(int(x), int(y))
            self._volume_toggle.raise_()
        except Exception:
            pass

    def _on_volume_toggled(self, checked: bool):
        self.volume_plot.setVisible(checked)
        try:
            self.volume_plot.getAxis('right').setVisible(checked)
        except Exception:
            pass
        # Rebalance splitter so price expands when volume hidden
        try:
            if hasattr(self, "_splitter"):
                self._splitter.refresh()
        except Exception:
            pass
        self._position_volume_toggle()
        self._position_zoom_controls()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_zoom_controls()
        self._position_volume_toggle()

    def eventFilter(self, obj, event):
        """Hide the crosshair when the mouse leaves the price plot."""
        if obj is self.price_plot.viewport() and event.type() == QEvent.Type.Leave:
            self._hide_crosshair()
        return super().eventFilter(obj, event)

    def _create_crosshair(self):
        """Create dotted crosshair lines plus price/time labels for the axes."""
        self.crosshair_v = pg.InfiniteLine(angle=90, pen=pg.mkPen('#94a3b8', width=1, style=Qt.PenStyle.DashLine))
        self.crosshair_h = pg.InfiniteLine(angle=0, pen=pg.mkPen('#94a3b8', width=1, style=Qt.PenStyle.DashLine))
        self.price_plot.addItem(self.crosshair_v)
        self.price_plot.addItem(self.crosshair_h)

        # Axis chips drawn over the right/bottom axes. Scene items so they
        # never affect the view's auto-range. D2/Q33: the price chip is a grey
        # pill with white text, left-anchored at the plot's vertical axis line
        # so it grows rightward into the Y-axis lane — overlapping the tick
        # label at the same price is by design (no deconfliction offset).
        scene = self.price_plot.getViewBox().scene()
        self._price_tag = pg.TextItem(anchor=(0, 0.5), fill=pg.mkColor(PRICE_TAG_FILL))
        self._time_tag = pg.TextItem(anchor=(0.5, 0), fill=pg.mkColor('#94a3b8'))
        self._price_tag.setColor(PRICE_TAG_TEXT_COLOR)
        self._time_tag.setColor('#0d0f14')
        for tag in (self._price_tag, self._time_tag):
            tag.setZValue(999)
            tag.hide()
            scene.addItem(tag)
        self._reserve_price_tag_lane()

    def _reserve_price_tag_lane(self) -> None:
        """Reserve Y-axis lane width for the price chip (D2/Q33, AC-D2.1).

        The pill grows rightward from the plot's vertical axis line, so the
        Y-axis lane must be wide enough for a long price (e.g. ``123,456.78``)
        to stay unclipped and outside any right-side dock. Reserving the width
        once, up front, avoids growing the axis while the cursor moves — which
        would position the pill against a stale lane until the next layout.
        """
        probe = pg.TextItem(anchor=(0, 0.5))
        probe.setText(PRICE_TAG_LANE_SAMPLE)
        needed = int(probe.boundingRect().width() + 2 * PRICE_TAG_PAD) + 1
        self._price_lane_width = needed
        axis = self.price_plot.getAxis('right')
        fixed = getattr(axis, 'fixedWidth', None)
        if fixed is None or fixed < needed:
            axis.setWidth(needed)

    def _position_price_tag(self, view_rect_scene, price_y: float) -> None:
        """Place the price pill in the Y-axis lane at the cursor's price (D2/Q33).

        Left-anchored at the plot's vertical axis line — scene
        ``x = view_rect_scene.right() + PRICE_TAG_PAD`` — extending right into
        the lane. A right-edge guard shifts the pill left when the label is
        wider than the lane, so it is never clipped at the widget's right edge
        (and therefore never bleeds under a right-side dock); the vertical
        clamp keeps the pill inside the plot near the top/bottom edges.
        """
        chip = self._price_tag.boundingRect()
        chip_w, chip_h = chip.width(), chip.height()
        lane_left = view_rect_scene.right()
        lane_right = lane_left + float(self.price_plot.getAxis('right').width())
        x = lane_left + PRICE_TAG_PAD
        if x + chip_w > lane_right:
            x = lane_right - chip_w
        half = chip_h / 2.0
        if price_y - half < view_rect_scene.top():
            price_y = view_rect_scene.top() + half
        elif price_y + half > view_rect_scene.bottom():
            price_y = view_rect_scene.bottom() - half
        self._price_tag.setPos(x, price_y)

    def _hide_crosshair(self):
        """Hide crosshair lines and both axis chips."""
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        self._price_tag.hide()
        self._time_tag.hide()

    def _update_crosshair(self, scene_pos):
        """Update crosshair lines and axis chips for a scene position."""
        vb = self.price_plot.getViewBox()
        if vb.scene() is None:
            return
        view_rect_scene = vb.mapRectToScene(vb.rect())
        if not self._bars or not view_rect_scene.contains(scene_pos):
            self._hide_crosshair()
            return

        view_pos = vb.mapSceneToView(scene_pos)
        x, y = view_pos.x(), view_pos.y()

        # Update crosshair lines
        self.crosshair_v.setPos(x)
        self.crosshair_h.setPos(y)
        self.crosshair_v.show()
        self.crosshair_h.show()

        # D2/Q33: price pill in the Y-axis lane at the cursor's price level.
        self._price_tag.setText(f"{y:,.2f}")
        price_y = vb.mapViewToScene(pg.Point(0, y)).y()
        self._position_price_tag(view_rect_scene, price_y)
        self._price_tag.show()

        # Time chip on the bottom axis, snapped to the nearest candle
        closest_bar_idx = self._find_closest_bar(scene_pos.x())
        if closest_bar_idx >= 0:
            bar = self._bars[closest_bar_idx]
            self._time_tag.setText(self._format_axis_time(bar.ts))
            chip_x = vb.mapViewToScene(pg.Point(bar.ts, 0)).x()
            chip_x = min(max(chip_x, view_rect_scene.left()), view_rect_scene.right())
            self._time_tag.setPos(chip_x, view_rect_scene.bottom())
            self._time_tag.show()
        else:
            self._time_tag.hide()

    def _find_closest_bar(self, x):
        """Find the bar closest to the given x position."""
        if not self._bars:
            return -1

        # Convert x position to timestamp
        vb = self.price_plot.getViewBox()
        map_to_data = vb.mapSceneToView(pg.Point(x, 0))
        target_ts = map_to_data.x()

        # Find closest bar
        closest_idx = 0
        min_diff = abs(self._bars[0].ts - target_ts)

        for i, bar in enumerate(self._bars):
            diff = abs(bar.ts - target_ts)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
            elif diff > min_diff:
                break

        # Check if within tolerance (e.g., 1/2 bar width)
        if self._bars and len(self._bars) > 1:
            bar_width = (self._bars[1].ts - self._bars[0].ts) / 2
            if min_diff > bar_width:
                return -1

        return closest_idx

    def _format_axis_time(self, ts):
        """Format a timestamp in the chart's display timezone.

        Mirrors pyqtgraph DateAxisItem: utcfromtimestamp(ts - utcOffset),
        where a positive offset means a zone behind UTC (e.g. 18000 for EST).
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(ts - self._tz_offset, tz=timezone.utc)
        return dt.strftime('%m/%d %H:%M')

    def set_chart_mode(self, mode: ChartMode):
        self.candlestick.set_mode(mode)

    def set_alarm_mode(self, enabled: bool):
        """Thin adapter (signature unchanged): route alarm intent through the router.

        Enabling exits any active zoom (TR-6); disabling returns to IDLE (TR-13).
        """
        enabled = bool(enabled)
        if enabled:
            self.mouse_router.enter_alarm_placing()
        else:
            if self.alarm_overlay is not None:
                self.alarm_overlay.set_alarm_mode(False)
            if self.mouse_router.active_mode == RouterMode.ALARM_PLACING:
                self.mouse_router.exit_to_idle()
        self._sync_magnifier(self.mouse_router.active_mode == RouterMode.ZOOMING)

    def set_alarms(self, alarms):
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_data(alarms)

    def set_symbol(self, symbol: str):
        self._symbol = symbol
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_symbol(symbol)
        # TR-17 / AC-D14.4 (ESC-010): a symbol change — including the D14
        # mid-drag double-click path — must clear any in-progress drawing
        # draft/drag and return the router to IDLE *before* the overlay items
        # are detached, so no stale gesture state survives into the new symbol.
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_tool(TOOL_CURSOR)
        if self.mouse_router is not None:
            self.mouse_router.exit_to_idle()
        # Reset magnifier on symbol change (A6)
        if hasattr(self, "_zoom_overlay"):
            self.set_zoom_mode(False)

    def set_drawing_tool(self, tool: str):
        """Thin adapter (signature unchanged): route drawing intent through the router."""
        self.setFocus()
        self.mouse_router.enter_drawing(tool)
        self._sync_magnifier(self.mouse_router.active_mode == RouterMode.ZOOMING)

    def set_studies(self, studies: list):
        self._studies = studies
        self._study_cache.invalidate(self._symbol, self._current_timeframe)
        if self._bars:
            self._apply_studies()

    def set_timeframe(self, timeframe: str):
        self._current_timeframe = timeframe
        if hasattr(self, "_zoom_overlay"):
            self.set_zoom_mode(False)
        if self._bars:
            self._render_sessions()

    def set_timezone(self, tz_offset: int):
        """Change the timezone offset for x-axis display (seconds from UTC)."""
        self._tz_offset = tz_offset
        # Recreate axes with new timezone
        date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.price_plot.setAxisItems({'bottom': date_axis})
        vol_date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.volume_plot.setAxisItems({'bottom': vol_date_axis})
        self._refresh_candles()  # Redraw to update axis labels
        # AC-D8.7: re-apply the cached ceiling on this auto_range=False path so
        # the volume Y range is never left stale after the axis swap.
        self._ensure_volume_range(force=True)

    def set_extended_hours(self, enabled: bool):
        self._ext_hours = enabled
        if self._bars:
            self._render_sessions()

    def _zoom_by(self, factor: float):
        if not self._bars:
            return
        vb = self.price_plot.getViewBox()
        try:
            # factor <1 zoom in, >1 zoom out; both axes around centre
            vb.scaleBy((factor, factor))
        except Exception:
            pass

    def _reset_view(self):
        if not self._bars:
            return
        self._refresh_candles(auto_range=True)

    def _sync_magnifier(self, active: bool):
        """Check/uncheck the magnifier control without re-emitting ``toggled``."""
        if hasattr(self, "_chart_controls") and self._chart_controls is not None:
            btn = self._chart_controls.btn_magnify
            if btn.isChecked() != bool(active):
                btn.blockSignals(True)
                btn.setChecked(bool(active))
                btn.blockSignals(False)

    def set_zoom_mode(self, enabled: bool):
        """Thin adapter (signature unchanged): route magnifier intent through the router.

        ``enter_zoom()`` returns ``False`` while alarm placement is armed
        (TR-9 / AC-D3.9): the magnifier is re-unchecked via ``blockSignals`` and
        ``zoom_refused`` is emitted so MainWindow can show the status hint.
        """
        enabled = bool(enabled)
        if enabled:
            if not self.mouse_router.enter_zoom():
                self._sync_magnifier(False)
                self.zoom_refused.emit()
                return
            self._sync_magnifier(True)
            return
        if self.mouse_router.active_mode == RouterMode.ZOOMING:
            self.mouse_router.exit_to_idle()
        elif hasattr(self, "_zoom_overlay") and self._zoom_overlay is not None:
            # Keep the overlay in sync without disturbing DRAWING / ALARM_PLACING.
            self._zoom_overlay.set_active(False)
        self._sync_magnifier(False)

    def is_zoom_active(self) -> bool:
        return bool(getattr(self, "_zoom_overlay", None) and self._zoom_overlay.is_active())

    def _render_sessions(self):
        # Clear previous
        if hasattr(self, "_session_overlay"):
            self._session_overlay.clear()
        if not self._ext_hours:
            return
        if not self._bars:
            return
        if self._current_timeframe == "1 day":
            return
        bands = session_bands(self._bars, self._current_timeframe or "")
        if bands:
            self._session_overlay.render(bands)

    def update_chart(self, bars):
        """Full refresh — called after historical data loads."""
        if not bars:
            # Clear chart explicitly for empty load (e.g., SPY first load
            # before IBKR delta returns). Avoid stale data from previous symbol.
            self._bars = []
            self._vol_max = 0.0
            self._volume_nice_max = VOLUME_NICE_FLOOR
            self._hide_crosshair()
            self._refresh_candles()
            if hasattr(self, "_session_overlay"):
                self._session_overlay.clear()
            return
        self._bars = list(bars)
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_bars(self._bars)
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_bars(self._bars)
        self._rebuild(auto_range=True)

    def update_last_bar(self, bar, is_new_candle: bool):
        """Intra-bar live update. Repaints candle + volume; re-applies studies
        only when a new candle period closes so live ticks stay responsive."""
        if not self._bars:
            return
        new_period = is_new_candle or self._bars[-1].ts != bar.ts
        if new_period:
            self._bars.append(bar)
            # New bar / load: refresh the cached running max O(N) once.
            self._recompute_vol_max()
        else:
            self._bars[-1] = bar
            # Intra-bar tick: widen the ceiling O(1) against the cached max.
            self._widen_volume_for(bar)
        self._refresh_candles()
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_bars(self._bars)
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_bars(self._bars)
        if is_new_candle:
            self._apply_studies()
            self._render_sessions()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, "_zoom_overlay") and self._zoom_overlay.is_active():
                # Cancel pending selection if dragging, but keep mode active per AC-D3.3/3.4
                if getattr(self._zoom_overlay, "_dragging", False):
                    self._zoom_overlay.cancel()
                    event.accept()
                    return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.drawing_overlay is not None and self.drawing_overlay.has_selection():
                self.drawing_overlay.delete_selected()
                event.accept()
                return
        super().keyPressEvent(event)

    # ── Private ────────────────────────────────────────────────────────────────

    def _rebuild(self, auto_range: bool = False):
        self._refresh_candles(auto_range=auto_range)
        if self._studies:
            self._apply_studies()
        self._render_sessions()

    def _refresh_candles(self, auto_range: bool = False):
        candle_data, vol_x, vol_h, vol_colors = [], [], [], []
        for bar in self._bars:
            candle_data.append((bar.ts, bar.open, bar.high, bar.low, bar.close))
            vol_x.append(bar.ts)
            vol_h.append(float(bar.volume))
            vol_colors.append('#34d399' if bar.close >= bar.open else '#f87171')

        # Frame the view explicitly from the data: ViewBox.autoRange() mis-computes
        # childrenBounds for epoch-magnitude x-coordinates (anchors xMin at 0),
        # leaving candles as a sub-pixel sliver off-screen.
        if auto_range and self._bars:
            vb = self.price_plot.getViewBox()
            t0, t1 = self._bars[0].ts, self._bars[-1].ts
            bar_w = self._bars[1].ts - self._bars[0].ts if len(self._bars) > 1 else 300
            lows = min(b.low for b in self._bars)
            highs = max(b.high for b in self._bars)
            if highs - lows <= 0:
                highs = lows + max(abs(lows), 1.0)
            # AC-D6.4 / ESC-013: apply the real x-range BEFORE generating the
            # candle picture.  The D6 body clamp in
            # ui/candlestick_item.py::_draw_candles reads the ViewBox range at
            # generation time; if the picture is built first the clamp sees the
            # untouched default range, never binds, and the dense-view body
            # collapses to a sub-pixel sliver.
            vb.setRange(xRange=(t0 - 2 * bar_w, t1 + 8 * bar_w),
                        yRange=(lows, highs), padding=0.03)

        # AC-D9.1 / ESC-020: derive the volume half-width from the *final* view
        # range, after the auto-range branch above has applied it.  This is the
        # same generate-before-setRange ordering defect T32/ESC-013 fixed for the
        # candle picture: if w_vol is computed before `vb.setRange(...)`, the
        # min_w_vol clamp sees the untouched default range on a first load, never
        # binds, and the volume bars come out far narrower than the price bodies.
        # Sharing the price's `w` (65% of median_diff, 35% gap) keeps the two
        # panels vertically aligned, including the dense 4px minimum.
        if len(self._bars) > 1:
            time_diffs_vol = [self._bars[i].ts - self._bars[i-1].ts for i in range(1, len(self._bars))]
            time_diffs_vol.sort()
            median_diff_vol = time_diffs_vol[len(time_diffs_vol)//2]
            w_vol = median_diff_vol * 0.325
            try:
                vb_vol = self.price_plot.getViewBox()
                if vb_vol is not None and vb_vol.width() > 50:
                    x_range_vol = vb_vol.viewRange()[0]
                    x_span_vol = x_range_vol[1] - x_range_vol[0]
                    if x_span_vol > 0:
                        px_per_sec_vol = vb_vol.width() / x_span_vol
                        min_w_vol = 2.0 / px_per_sec_vol
                        if w_vol < min_w_vol:
                            w_vol = min_w_vol
            except Exception:
                pass
        else:
            w_vol = 0.25

        self.volume_bars.setOpts(x=vol_x, height=vol_h, width=w_vol*2, brushes=vol_colors)

        if auto_range and self._bars:
            # Generate the candle picture now that the real range is known.
            self.candlestick.set_data(candle_data)
            # Full load: rebuild the cached running max O(N) once, then apply.
            self._recompute_vol_max()
            self._ensure_volume_range(force=True)
        else:
            # Non-auto-range refresh (intra-bar redraw / set_timezone / empty
            # load): the ViewBox range is already the real one, so the clamp
            # computes against it.  Still regenerate to clear/refresh the picture.
            self.candlestick.set_data(candle_data)
            if self._bars:
                # auto_range=False refresh: re-apply the cached ceiling so the
                # range tracks the cached running max.
                self._ensure_volume_range()

    def _recompute_vol_max(self) -> float:
        """Refresh the cached running volume max O(N) over the current bars.

        Called once per data load (``_refresh_candles(auto_range=True)``) and
        once per new bar (``update_last_bar`` with a new period).
        """
        self._vol_max = max((float(b.volume) for b in self._bars), default=0.0)
        return self._vol_max

    def _ensure_volume_range(self, force: bool = False) -> float:
        """Apply the volume ceiling derived from the cached running max.

        O(1): recompute the nice ceiling from ``self._vol_max`` and write the
        volume Y range only when the ceiling changes (or when ``force`` is set).
        Returns the ceiling currently applied.
        """
        nice = _nice_volume_max(self._vol_max)
        if force or nice > self._volume_nice_max:
            self._volume_nice_max = nice
            self.volume_plot.getViewBox().setRange(yRange=(0, nice), padding=0)
        return self._volume_nice_max

    def _widen_volume_for(self, bar) -> float:
        """O(1) only-widen ceiling update for one live (intra-bar) tick.

        Computes ``live_max = max(_vol_max, bar.volume)`` against the cached
        running max and widens the ceiling only when that crosses the current
        nice_max; a non-crossing tick performs no range write.
        """
        self._vol_max = max(self._vol_max, float(bar.volume))
        return self._ensure_volume_range()

    def _clear_overlays(self):
        for item in self._overlay_items:
            self.price_plot.removeItem(item)
        for item in self._osc_items:
            self.osc_plot.removeItem(item)
        self._overlay_items.clear()
        self._osc_items.clear()
        self._gap_overlay.clear()
        self._vix_overlay.clear()
        self._ict_overlay.clear()
        if hasattr(self, "_session_overlay"):
            self._session_overlay.clear()

    def _apply_studies(self):
        self._clear_overlays()
        if not self._bars:
            return

        closes  = [b.close  for b in self._bars]
        highs   = [b.high   for b in self._bars]
        lows    = [b.low    for b in self._bars]
        volumes = [b.volume for b in self._bars]
        timestamps = [b.ts for b in self._bars]
        xs      = timestamps

        all_vals: dict[str, list] = {}
        for study in self._studies:
            if not study.get("enabled"):
                continue
            stype  = study["type"]
            params = study.get("params", {})
            color  = params.get("color", "#ffffff")

            if stype == "sma":
                vals = calculate_sma(closes, params.get("period", 20))
                self._add_line(xs, vals, color)
                all_vals[stype] = vals

            elif stype in ("ema", "ema2"):
                vals = calculate_ema(closes, params.get("period", 9))
                self._add_line(xs, vals, color)
                all_vals[stype] = vals

            elif stype == "vwap":
                vals = calculate_vwap(
                    highs, lows, closes, volumes,
                    timestamps=timestamps,
                )
                self._add_line(xs, vals, color, width=1.5)
                all_vals[stype] = vals

            elif stype == "bollinger":
                upper, mid, lower = calculate_bollinger_bands(
                    closes, params.get("period", 20), params.get("std_dev", 2.0)
                )
                self._add_line(xs, upper, color)
                self._add_line(xs, mid,   color, style=Qt.PenStyle.DotLine)
                self._add_line(xs, lower, color)
                all_vals[stype] = upper
                all_vals[f"{stype}_mid"] = mid
                all_vals[f"{stype}_lower"] = lower

            elif stype == "rsi":
                vals = calculate_rsi(closes, params.get("period", 14))
                ob = params.get("overbought", 70)
                os_ = params.get("oversold", 30)
                self._add_osc_line(xs, vals, "#818cf8")
                self._add_osc_hline(ob, "#f87171", style=Qt.PenStyle.DotLine)
                self._add_osc_hline(os_, "#34d399", style=Qt.PenStyle.DotLine)
                all_vals[stype] = vals

            elif stype == "macd":
                macd_line, signal_line, histogram = calculate_macd(
                    closes,
                    params.get("fast", 12),
                    params.get("slow", 26),
                    params.get("signal", 9),
                )
                self._add_osc_line(xs, macd_line,   "#60a5fa")
                self._add_osc_line(xs, signal_line, "#f59e0b")
                bar_x, bar_h, bar_c = [], [], []
                for i, v in enumerate(histogram):
                    if v is not None:
                        bar_x.append(i)
                        bar_h.append(v)
                        bar_c.append('#34d399' if v >= 0 else '#f87171')
                hist_bars = pg.BarGraphItem(x=bar_x, height=bar_h, width=0.6, brushes=bar_c)
                self.osc_plot.addItem(hist_bars)
                self._osc_items.append(hist_bars)
                all_vals[stype] = macd_line
                all_vals["macd_signal"] = signal_line

            elif stype == "rth_gaps":
                ticker = infer_ticker_context(self._symbol, self._bars)
                gaps = calculate_rth_gaps(self._bars, ticker, params)
                self._gap_overlay.render(gaps, len(self._bars))

            elif stype == "vix_sd":
                ticker = infer_ticker_context(self._symbol, self._bars)
                result = calculate_vix_standard_deviation(ticker, self._bars, params)
                self._vix_overlay.render(result, len(self._bars))

            elif stype == "ict":
                ticker = infer_ticker_context(self._symbol, self._bars)
                result = calculate_ict_concepts(self._bars, ticker, params)
                self._ict_overlay.render(result, len(self._bars))

        # Cache the computed values for incremental updates
        cacheable = {k: list(v) for k, v in all_vals.items()}
        if cacheable:
            self._study_cache.set(self._symbol, self._current_timeframe or "", self._studies, cacheable)

        has_oscillator = any(s.get("enabled") and s.get("type") in OSCILLATOR_TYPES for s in self._studies)
        if has_oscillator:
            self.osc_plot.show()
        else:
            self.osc_plot.hide()

    def _add_line(self, xs, vals, color: str, width: float = 1.0,
                  style=Qt.PenStyle.SolidLine):
        x_pts, y_pts = zip(*[(x, v) for x, v in zip(xs, vals) if v is not None]) if any(v is not None for v in vals) else ([], [])
        if not x_pts:
            return
        pen = pg.mkPen(color=color, width=width, style=style)
        curve = pg.PlotDataItem(list(x_pts), list(y_pts), pen=pen)
        self.price_plot.addItem(curve)
        self._overlay_items.append(curve)

    def _add_osc_line(self, xs, vals, color: str, width: float = 1.0,
                      style=Qt.PenStyle.SolidLine):
        x_pts, y_pts = zip(*[(x, v) for x, v in zip(xs, vals) if v is not None]) if any(v is not None for v in vals) else ([], [])
        if not x_pts:
            return
        pen = pg.mkPen(color=color, width=width, style=style)
        curve = pg.PlotDataItem(list(x_pts), list(y_pts), pen=pen)
        self.osc_plot.addItem(curve)
        self._osc_items.append(curve)

    def _add_osc_hline(self, y: float, color: str,
                       style=Qt.PenStyle.SolidLine):
        pen = pg.mkPen(color=color, width=0.8, style=style)
        line = pg.InfiniteLine(pos=y, angle=0, pen=pen)
        self.osc_plot.addItem(line)
        self._osc_items.append(line)
