"""
chart_panel.py
Main chart widget: price plot (candlestick + indicator overlays)
+ volume subplot linked on the X-axis.
Supports 5 render modes and dynamic study overlays.
"""

import hashlib
from bisect import bisect_left, bisect_right
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSplitter, QPushButton
from PyQt6.QtCore import Qt, QEvent, pyqtSignal

from ui.candlestick_item import CandlestickItem, ChartMode, capped_body_half_width
from ui.drawing_overlay import DrawingViewBox, DrawingOverlay, TOOL_CURSOR
from ui.alarm_overlay import AlarmOverlay
from ui.event_marker_overlay import EventMarkerOverlay
from ui.chart_mouse_router import ChartMouseRouter, RouterMode
from ui.overlays.gap_overlay import RthGapOverlay
from ui.overlays.vix_overlay import VixOverlay
from ui.overlays.ict_overlay import ICTStudyOverlay
from ui.visual_conventions import DiagonalStrikeButton
from pyqtgraph.graphicsItems.DateAxisItem import TickSpec, ZoomLevel, makeSStepper, DAY_SPACING, HOUR_SPACING
from datetime import timezone, timedelta

from data.bar_aggregator import TIMEFRAME_SECONDS
from config import settings
from services.market_calendar import session_windows
from services.backfill_service import floor_bar_budget
from services.time_collapse_service import TimeCollapseMap, build_collapse_map


class CollapsedDateAxis(pg.DateAxisItem):
    """Date axis for a display-x (collapsed) x-model (D21.4).

    When the D21.4 collapse map is active the ViewBox x-coordinates are
    *display-x* (non-trading time removed), not timestamps. Ticks are still
    positioned at display-x, but each tick value is inverse-mapped through the
    collapse map to its original timestamp before formatting, so the labels
    show the real calendar time of the bar at that position.
    """

    def __init__(self, utc: bool = True, tz_offset: int = 0):
        super().__init__(utc=utc)
        # Adjust utcOffset for non-UTC display
        if tz_offset != 0:
            self.utcOffset = tz_offset
        custom_zoom = ZoomLevel([
            TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), '%m/%d'),
            TickSpec(HOUR_SPACING, makeSStepper(HOUR_SPACING), '%H:%M', autoSkip=[1, 6]),
        ], 'MM/DD HH:MM')
        self.zoomLevels[5 * 3600 * 24] = custom_zoom  # Replace DAY_HOUR_ZOOM_LEVEL
        self._collapse_map: TimeCollapseMap | None = None

    def set_collapse_map(self, collapse_map: TimeCollapseMap | None) -> None:
        """Set (or clear) the display-x -> ts map used for tick labels."""
        self._collapse_map = collapse_map
        self.picture = None
        self.update()

    def tickStrings(self, values, scale, spacing):
        cmap = self._collapse_map
        if cmap is not None and not cmap.is_identity:
            # Tick positions are display-x; inverse-map each back to the real
            # timestamp before formatting so labels show wall-clock time.
            values = [cmap.to_ts(v * scale) for v in values]
            scale = 1.0
        return super().tickStrings(values, scale, spacing)


def _custom_date_axis(utc: bool = True, tz_offset: int = 0) -> "pg.DateAxisItem":
    """Create a collapse-aware DateAxisItem with MM/DD HH:MM zoom levels.

    Args:
        utc: If True, use UTC. If False, use local timezone.
        tz_offset: Timezone offset in seconds (positive for timezones behind UTC like ET).
                   e.g., 18000 for EST, 14400 for EDT.
    """
    return CollapsedDateAxis(utc=utc, tz_offset=tz_offset)


# D8 / RG-002: the single pinned volume nice-number family. The old fixed list
# [10k .. 10M] is retained ONLY as a regression fixture in
# tests/test_volume_linear.py and is never a live code path.
VOLUME_NICE_MANTISSAS = (1.0, 1.5, 2.0, 2.5, 5.0, 7.5)
VOLUME_NICE_FLOOR = 100.0

# D21.6 / AC-D21.6.1: the volume pane can grow to a real, usable height. The
# former 120px cap was the same as the oscillator cap and left volume unusable;
# the new 480px ceiling lets the user drag the price/volume splitter until the
# volume pane reaches at least 360px (3x the old cap). The price pane keeps a
# ~200px floor so growing volume never collapses price into an unreadable
# sliver. The oscillator pane cap is intentionally left unchanged at 120px.
VOLUME_PANE_MAX_HEIGHT = 480
PRICE_PANE_MIN_HEIGHT = 200


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

    D21.2 / AC-D21.2.1 note: the *live* volume pane ceiling is no longer this
    whole-list nice-max; it is ``1.10 x max(visible volume)`` computed by
    ``ChartPanel._recompute_visible_volume_range``. This helper is retained for
    the all-zero ``100`` floor and as the pinned-family fixture the volume test
    modules exercise directly.
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
    sma_update, ema_update, vwap_update,
    bollinger_update, rsi_update, macd_update,
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

# D28.4: ICT concepts are computed over a trailing window, not the full
# series — the overlay renders window-relative bar indices, so the window
# itself is passed as the bar list (indices stay consistent by construction).
ICT_TRAILING_BARS = 500


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

# D21.10 / AC-D21.10.2: yellow dashed preview line shown while a chart-click
# alarm popup is open. Owned by ChartPanel (not the AlarmOverlay) so it can be
# created/updated/removed independently of the real alarm lines.
ALARM_PREVIEW_COLOR = "#ffff00"


class ChartPanel(QWidget):
    # AC-D3.9: emitted when the magnifier is refused because alarm placement is armed.
    zoom_refused = pyqtSignal()

    def __init__(self, tz_offset: int = 0, editable: bool = True):
        super().__init__()
        # D24: pop-out charts pass editable=False — drawing, alarm placement,
        # studies/timeframe/mode interaction are disabled; overlays render and
        # crosshair/zoom/pan keep working.
        self._editable = editable
        self._bars: list = []
        # D21.4: the display-x collapse map and the indices of the bars actually
        # plotted (with Ext Hours OFF only RTH bars are plotted). ``_bars`` is
        # never mutated or filtered — collapse is a display-only transform.
        self._collapse_map: TimeCollapseMap | None = None
        self._plotted_indices: list = []
        # D28.4: cached display-x / volume arrays aligned with
        # _plotted_bars — bisection targets for the crosshair and the
        # volume ceiling (no O(n) scans on per-frame paths).
        self._plot_xs: list[float] = []
        self._plot_vols: list[float] = []
        self._studies: list = []
        self._overlay_items: list = []
        self._osc_items: list = []
        self._symbol: str = ""
        self._current_timeframe: str | None = None
        self._study_cache = _StudyCache()
        self._tz_offset = tz_offset  # timezone offset in seconds (positive behind UTC, e.g., 18000 for EST, 14400 for EDT)

        # D21.2 / AC-D21.2.1: the volume Y ceiling last applied to the volume
        # ViewBox. It is derived from the bars in the visible x-range on every
        # x-range change and on every bar update
        # (``_recompute_visible_volume_range``). Supersedes the D8 whole-list
        # nice-max / ESC-007 only-widen ceiling.
        self._volume_nice_max: float = VOLUME_NICE_FLOOR

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Price plot ────────────────────────────────────────────────────────
        self.drawing_overlay = None
        self.alarm_overlay = None
        # D21.10 / AC-D21.10.2: the live chart-click alarm preview line, or None.
        self._alarm_preview_line = None
        self.mouse_router = ChartMouseRouter()

        # Create PlotWidget with default ViewBox so DateAxisItem links properly
        self.price_plot = pg.PlotWidget()
        self.price_plot.showGrid(x=True, y=True, alpha=0.08)
        self.price_plot.hideAxis('left')
        self.price_plot.showAxis('right')
        self.price_plot.getAxis('right').setStyle(tickFont=None)
        # X-axis: actual timestamps using DateAxisItem with timezone support
        self._price_date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.price_plot.setAxisItems({'bottom': self._price_date_axis})

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
        # D28.4: live-bar layer — holds only the forming bar so per-tick
        # updates never regenerate the static history QPicture.
        self.live_candle = CandlestickItem([], mode=ChartMode.CANDLES)
        self.price_plot.addItem(self.live_candle)
        # D28.4: cached candle half-width, recomputed only at full rebuild
        # (bar-count or spacing change), reused by forming-bar ticks.
        self._candle_half_width: float = 0.0
        # D42/S14: the display-x pitch (ViewBox logical px) cached alongside the
        # half-width, so the shared density cap recovers ``median_diff`` without
        # re-running the O(n log n) median-spacing sort D28.4 removed.
        self._candle_pitch: float | None = None
        self.drawing_overlay = DrawingOverlay(self.price_plot,
                                            editable=editable)
        self.alarm_overlay = AlarmOverlay(self.price_plot,
                                          editable=editable)
        # D38: corporate-event markers on the time axis.
        self.event_overlay = EventMarkerOverlay(self.price_plot)
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
        # D21.6 / AC-D21.6.1: raise the volume ceiling from the former 120px
        # (same as the oscillator cap) to 480px so the user can grow the volume
        # pane to at least 360px by dragging the price/volume splitter.
        self.volume_plot.setMaximumHeight(VOLUME_PANE_MAX_HEIGHT)
        self.volume_plot.showGrid(x=True, y=True, alpha=0.05)
        self.volume_plot.hideAxis('left')
        # Right axis uses the D8 volume tick formatter (AC-D8.3: 500.0K / 1.0M).
        self.volume_plot.setAxisItems({'right': _VolumeAxisItem(orientation='right')})
        self.volume_plot.showAxis('right')
        self.volume_plot.getAxis('right').setStyle(tickFont=None)
        self.volume_plot.setXLink(self.price_plot)
        # Use DateAxisItem for volume too, with proper formatting
        self._vol_date_axis = _custom_date_axis(utc=(self._tz_offset == 0), tz_offset=self._tz_offset)
        self.volume_plot.setAxisItems({'bottom': self._vol_date_axis})
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.volume_plot.addItem(self.volume_bars)
        # D28.4: live-volume layer — the forming bar's volume, updated per
        # tick without rebuilding the static volume picture.
        self.live_volume = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.volume_plot.addItem(self.live_volume)
        # Linear Y for volume — dynamic nice ticks, no negatives (see D8)
        try:
            self.volume_plot.getViewBox().setLogMode('y', False)
        except Exception:
            pass
        # D21.1 / AC-D21.1.1: hard-limit the volume Y minimum at 0 so no
        # interactive y-interaction can pull the view below zero. The ViewBox
        # limit clamps every range change routed through ``setRange`` — mouse
        # drag → ``translateBy``, wheel zoom → ``scaleBy`` — while the
        # programmatic ``setRange(yRange=(0, ceiling))`` writes in
        # ``_recompute_visible_volume_range`` stay inside the limit unchanged (the
        # all-zero ``[0, 100]`` floor is preserved). The limit persists on the
        # ViewBox across reloads, so a symbol/timeframe switch re-applies it.
        self.volume_plot.getViewBox().setLimits(yMin=0)

        # D21.2 / AC-D21.2.1: the volume Y ceiling tracks the bars in the visible
        # x-range. Recompute it on every visible-x change (zoom in/out, pan,
        # magnifier area-zoom) — this supersedes the D8 nice-max ceiling and
        # ESC-007's only-widen rule for zoom while preserving ESC-007's
        # forming-bar no-clip intent via the bar-update recompute.
        self.price_plot.getViewBox().sigXRangeChanged.connect(
            self._on_price_x_range_changed
        )

        # ── Oscillator plot (RSI / MACD) ──────────────────────────────────────
        self.osc_plot = pg.PlotWidget()
        self.osc_plot.setMaximumHeight(120)
        self.osc_plot.showGrid(x=True, y=True, alpha=0.05)
        self.osc_plot.hideAxis('left')
        self.osc_plot.showAxis('right')
        self.osc_plot.getAxis('right').setStyle(tickFont=None)
        self.osc_plot.setXLink(self.price_plot)
        self.osc_plot.hide()            # hidden until an oscillator study is enabled

        # D21.6 / AC-D21.6.1: the price pane keeps a ~200px floor so growing
        # the volume pane (up to VOLUME_PANE_MAX_HEIGHT) never collapses price
        # into an unreadable sliver. The oscillator pane keeps its 120px cap.
        self.price_plot.setMinimumHeight(PRICE_PANE_MIN_HEIGHT)

        self._splitter.addWidget(self.price_plot)
        self._splitter.addWidget(self.volume_plot)
        self._splitter.addWidget(self.osc_plot)
        self._splitter.setSizes([600, 120, 120])
        # Price takes the slack on resize (stretch 1); the volume pane keeps
        # its dragged size (stretch 0) instead of being squeezed by a window
        # resize, so a grown volume pane is not silently shrunk back.
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setStretchFactor(2, 0)
        layout.addWidget(self._splitter)

        # Volume show/hide toggle — top left of volume panel (bottom left of price chart).
        # RC-4a: the affordance is the checkable text label "Volume" (no eye
        # icon or bar glyph); the checkable behaviour is retained.
        # D21.8 / AC-D21.12.1: the toggle is a DiagonalStrikeButton so the label
        # is struck through (VIS-D21.1) while the pane is hidden (unchecked) and
        # unstruck while shown (checked). D10 placement/behaviour are unchanged.
        self._volume_toggle = DiagonalStrikeButton("Volume", self)
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
                # D27.10: the edited colour must persist, not just re-render.
                self.drawing_overlay.updated.emit(drawing.id, payload, color)

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

    def bind_d38_session(self, session, yf_source=None) -> None:
        """Attach the session driving the event-marker overlay (38b.2)."""
        self._d38_session = session
        self._d38_yf_source = yf_source
        session.events_updated.connect(self._on_events_updated)
        session.dividend_updated.connect(self._on_events_updated)
        self._on_events_updated()
        # Kick the (cache-first, non-blocking) yfinance refresh.
        try:
            session.refresh_events(yf_source)
        except Exception:
            pass

    def unbind_d38_session(self, session) -> None:
        for sig, slot in ((session.events_updated, self._on_events_updated),
                          (session.dividend_updated, self._on_events_updated)):
            try:
                sig.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        if getattr(self, "_d38_session", None) is session:
            self._d38_session = None
            self._d38_yf_source = None
        if getattr(self, "event_overlay", None) is not None:
            self.event_overlay.clear()

    def _on_events_updated(self) -> None:
        session = getattr(self, "_d38_session", None)
        overlay = getattr(self, "event_overlay", None)
        if session is None or overlay is None:
            return
        try:
            overlay.set_events(session.events(),
                               unavailable=session.events_unavailable())
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

        # Time chip on the bottom axis, snapped to the nearest candle. The x-axis
        # is display-x after collapse (D21.4), so the chip is positioned at the
        # bar's display-x and the label inverse-maps that back to its ts.
        closest_bar_idx = self._find_closest_bar(scene_pos.x())
        if closest_bar_idx >= 0:
            bar = self._plotted_bars[closest_bar_idx]
            dx = self._to_display(bar.ts)
            self._time_tag.setText(self._format_axis_time(self._to_ts(dx)))
            chip_x = vb.mapViewToScene(pg.Point(dx, 0)).x()
            chip_x = min(max(chip_x, view_rect_scene.left()), view_rect_scene.right())
            self._time_tag.setPos(chip_x, view_rect_scene.bottom())
            self._time_tag.show()
        else:
            self._time_tag.hide()

    def _find_closest_bar(self, x):
        """Find the plotted bar closest to the given scene x position.

        D28.4: bisection over the cached display-x array (the array is
        monotonic in ts order) instead of the O(n) per-mousemove scan.
        """
        xs = self._plot_xs
        if not xs:
            return -1

        # Convert scene x to a display-x coordinate (the ViewBox x-model).
        vb = self.price_plot.getViewBox()
        map_to_data = vb.mapSceneToView(pg.Point(x, 0))
        target_x = map_to_data.x()

        # The closest bar brackets the insertion point.
        i = bisect_left(xs, target_x)
        closest_idx, min_diff = -1, None
        for j in (i - 1, i):
            if 0 <= j < len(xs):
                diff = abs(xs[j] - target_x)
                if min_diff is None or diff < min_diff:
                    closest_idx, min_diff = j, diff

        # Check if within tolerance (e.g., 1/2 bar width in display-x)
        if len(xs) > 1:
            bar_width = (xs[1] - xs[0]) / 2
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

    # ── D21.4 display-x collapse ──────────────────────────────────────────────

    @property
    def _plotted_bars(self) -> list:
        """The bars actually plotted (RTH-only with Ext Hours OFF)."""
        return [self._bars[i] for i in self._plotted_indices]

    def _compute_plotted_indices(self) -> list:
        """Return indices into ``self._bars`` for the bars to plot.

        With Ext Hours ON every bar is plotted. With Ext Hours OFF (RTH) only
        RTH bars are plotted (``AC-D21.4.3``) — this is a *display* filter; the
        underlying ``self._bars`` list (and every ``Bar.ts``) is untouched.
        Indices (not objects) are stored so an in-place intra-bar update of the
        forming bar is reflected in the plotted set.
        """
        if self._ext_hours or not self._bars:
            return list(range(len(self._bars)))
        tf = self._current_timeframe
        if tf is None or tf not in TIMEFRAME_SECONDS:
            return list(range(len(self._bars)))
        period = TIMEFRAME_SECONDS[tf]
        return [
            i for i, b in enumerate(self._bars)
            if session_windows(int(b.ts), int(b.ts) + period, False)
        ]

    def _rebuild_collapse_map(self) -> None:
        """Rebuild the display-x collapse map and push it to the date axes."""
        self._plotted_indices = self._compute_plotted_indices()
        tf = self._current_timeframe
        if tf is None or tf not in TIMEFRAME_SECONDS:
            self._collapse_map = None
        else:
            self._collapse_map = build_collapse_map(
                self._plotted_bars, tf, self._ext_hours
            )
        self._sync_plot_arrays()
        self._sync_collapsed_axes()
        self._sync_collapsed_consumers()

    def _sync_plot_arrays(self) -> None:
        """D28.4: refresh the cached display-x / volume arrays (bisection)."""
        to_display = self._to_display
        self._plot_xs = [to_display(b.ts) for b in self._plotted_bars]
        self._plot_vols = [float(b.volume) for b in self._plotted_bars]

    def _new_bar_is_plotted(self, bar) -> bool:
        """D28.4: the _compute_plotted_indices predicate for a single bar."""
        if self._ext_hours:
            return True
        tf = self._current_timeframe
        if tf is None or tf not in TIMEFRAME_SECONDS:
            return True
        period = TIMEFRAME_SECONDS[tf]
        return bool(session_windows(int(bar.ts), int(bar.ts) + period, False))

    def _extend_collapse_map(self) -> None:
        """D28.4: tail-extend the collapse map for an appended bar.

        Falls back to a full rebuild when the new bar is not a forward
        plotted extension (RTH-filtered out, unknown timeframe, missing
        map, or non-forward timestamp).
        """
        bars = self._bars
        if not bars:
            return
        bar = bars[-1]
        cmap = self._collapse_map
        if cmap is None or not self._new_bar_is_plotted(bar):
            self._rebuild_collapse_map()
            return
        if not cmap.extend(bar.ts):
            self._rebuild_collapse_map()
            return
        self._plotted_indices.append(len(bars) - 1)
        self._plot_xs.append(cmap.to_display(bar.ts))
        self._plot_vols.append(float(bar.volume))
        self._sync_collapsed_axes()
        self._sync_collapsed_consumers()

    def _sync_collapsed_consumers(self) -> None:
        """Push the collapse map + plotted bars to the drawing/alarm overlays.

        D21.4 consumers: drawings render at display-x and drag inverse-maps it;
        the alarm label uses the display-x of the last bar. Both must see the
        same map as the candles/volume and the date axes.
        """
        bars = self._plotted_bars
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_collapse_map(self._collapse_map)
            self.drawing_overlay.set_bars(bars)
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_collapse_map(self._collapse_map)
            self.alarm_overlay.set_bars(bars)
        # D38: event markers position at display-x too.
        if getattr(self, "event_overlay", None) is not None:
            self.event_overlay.set_collapse_map(self._collapse_map)
            self.event_overlay.set_bars(bars)
        # D27.2: the study overlays render at display-x too; they map bar
        # indices through the same collapse map as the candles.
        for overlay in (self._gap_overlay, self._vix_overlay,
                        self._ict_overlay):
            if overlay is not None:
                overlay.set_collapse_map(self._collapse_map)

    def _sync_collapsed_axes(self) -> None:
        for name in ("_price_date_axis", "_vol_date_axis"):
            axis = getattr(self, name, None)
            if axis is not None and hasattr(axis, "set_collapse_map"):
                axis.set_collapse_map(self._collapse_map)

    def _to_display(self, ts):
        """Map an original timestamp to display-x (identity when no map)."""
        cmap = self._collapse_map
        if cmap is None:
            return ts
        return cmap.to_display(ts)

    def _to_ts(self, x):
        """Inverse-map a display-x back to the original timestamp."""
        cmap = self._collapse_map
        if cmap is None:
            return x
        return cmap.to_ts(x)

    def set_chart_mode(self, mode: ChartMode):
        self.candlestick.set_mode(mode)
        # D28.4: the live layer renders the same mode as the static layer.
        self.live_candle.set_mode(mode)

    def set_alarm_mode(self, enabled: bool):
        """Thin adapter (signature unchanged): route alarm intent through the router.

        Enabling exits any active zoom (TR-6); disabling returns to IDLE (TR-13).
        D24: no-op when the panel is not editable (pop-out).
        """
        if not self._editable:
            return
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

    # ── D21.10 alarm preview line ─────────────────────────────────────────────

    @property
    def alarm_preview_line(self):
        """The live yellow dashed preview line, or ``None`` when hidden."""
        return self._alarm_preview_line

    def show_alarm_preview(self, price: float) -> None:
        """Show the yellow dashed preview line at ``price`` (AC-D21.10.2).

        Owned by the panel, non-movable, and shown only while a chart-click
        alarm popup is open. Idempotent: a second call just moves the line.
        """
        if self._alarm_preview_line is None:
            line = pg.InfiniteLine(
                pos=float(price),
                angle=0,
                pen=pg.mkPen(
                    ALARM_PREVIEW_COLOR,
                    width=1.4,
                    style=Qt.PenStyle.DashLine,
                ),
            )
            line.setMovable(False)
            line.setZValue(5)
            self.price_plot.addItem(line)
            self._alarm_preview_line = line
        else:
            self._alarm_preview_line.setValue(float(price))
        self._alarm_preview_line.show()

    def update_alarm_preview(self, price: float) -> None:
        """Move the preview line to ``price`` live (AC-D21.10.3)."""
        if self._alarm_preview_line is not None:
            self._alarm_preview_line.setValue(float(price))
            self._alarm_preview_line.show()

    def hide_alarm_preview(self) -> None:
        """Remove the preview line (AC-D21.10.4)."""
        if self._alarm_preview_line is not None:
            self.price_plot.removeItem(self._alarm_preview_line)
            self._alarm_preview_line = None

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
        """Thin adapter (signature unchanged): route drawing intent through the router.

        D24: no-op when the panel is not editable (pop-out).
        """
        if not self._editable:
            return
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
            # D21.4: the collapse map is timeframe-dependent — rebuild it and
            # re-render at the new display-x positions.
            self._rebuild_collapse_map()
            self._refresh_candles()
            self._render_sessions()

    def set_timezone(self, tz_offset: int):
        """Change the timezone offset for x-axis display (seconds from UTC)."""
        self._tz_offset = tz_offset
        # Recreate axes with new timezone
        self._price_date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.price_plot.setAxisItems({'bottom': self._price_date_axis})
        self._vol_date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.volume_plot.setAxisItems({'bottom': self._vol_date_axis})
        self._sync_collapsed_axes()
        self._refresh_candles()  # Redraw to update axis labels
        # D21.2 / AC-D8.7: re-apply the visible ceiling on this auto_range=False
        # path so the volume Y range is never left stale after the axis swap.
        self._recompute_visible_volume_range(force=True)

    def set_extended_hours(self, enabled: bool):
        self._ext_hours = enabled
        if self._bars:
            # D21.4: Ext Hours changes both the plotted bar set (RTH filter) and
            # the collapse map's session windows — rebuild and re-render.
            self._rebuild_collapse_map()
            self._refresh_candles()
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
            # D21.4: the price/volume x-axis is display-x after collapse, so the
            # D1 pre/post bands must be mapped through the same collapse map to
            # land on the sessions actually shown (AC-D21.4.3).
            mapped = [
                {
                    "kind": band["kind"],
                    "start_ts": self._to_display(band["start_ts"]),
                    "end_ts": self._to_display(band["end_ts"]),
                }
                for band in bands
            ]
            self._session_overlay.render(mapped)

    def update_chart(self, bars):
        """Full refresh — called after historical data loads."""
        if not bars:
            # Clear chart explicitly for empty load (e.g., SPY first load
            # before IBKR delta returns). Avoid stale data from previous symbol.
            self._bars = []
            self._plotted_indices = []
            self._collapse_map = None
            self._plot_xs = []
            self._plot_vols = []
            self._sync_collapsed_axes()
            self._sync_collapsed_consumers()
            self._volume_nice_max = VOLUME_NICE_FLOOR
            self._hide_crosshair()
            self._refresh_candles()
            if hasattr(self, "_session_overlay"):
                self._session_overlay.clear()
            return
        self._bars = list(bars)
        # D28.4: a wholesale bar replacement invalidates the study cache — the
        # incremental fingerprint is (n_bars, last_ts), which a
        # value-correcting backfill can match by coincidence. The valuable
        # per-new-candle incremental path goes through update_last_bar, not
        # here, so nothing important is lost.
        self._study_cache.invalidate(self._symbol, self._current_timeframe)
        # D21.4: build the display-x collapse map from the freshly loaded bars
        # before the candles/volume are (re)generated at display-x. This also
        # syncs the drawing/alarm overlays (their bars + collapse map).
        self._rebuild_collapse_map()
        self._rebuild(auto_range=True)

    def update_last_bar(self, bar, is_new_candle: bool):
        """Intra-bar live update. Repaints candle + volume; re-applies studies
        only when a new candle period closes so live ticks stay responsive.
        D24: a new candle on an empty chart starts the series (pop-out with
        no history yet)."""
        if not self._bars:
            if is_new_candle:
                self.update_chart([bar])
            return
        new_period = is_new_candle or self._bars[-1].ts != bar.ts
        if new_period:
            self._bars.append(bar)
            # D42/S18 (RC-D42-1): the panel's series cap is floor-aware — the
            # third SESSION_BAR_CAP site. It uses the same derived budget the
            # session caps and BarCache.prune's `keep` use, so the AC-D16.8
            # depth floor is not re-trimmed out of the DISPLAYED series on the
            # next new-candle tick (update_chart seeds this series from the
            # session's now-up-to-33,120-bar series). The flat
            # settings.SESSION_BAR_CAP stays the default/minimum (a daily
            # timeframe returns it).
            budget = floor_bar_budget(
                self._current_timeframe or "", self._ext_hours)
            if len(self._bars) > budget:
                # D28.4: mirror the session's series cap so panels don't grow
                # unbounded in steady-state live (sessions prune their heads;
                # panels never re-sync via update_chart). Head-pruning changes
                # the span, so rebuild the collapse map (NOT extend) and
                # invalidate the study cache — the incremental paths assume a
                # pure tail extension of a batch-computed series.
                del self._bars[: len(self._bars) - budget]
                self._rebuild_collapse_map()
                self._study_cache.invalidate(
                    self._symbol, self._current_timeframe)
            else:
                # D21.4: a new bar changes the collapse map's span — D28.4
                # tail-extends it instead of rebuilding.
                self._extend_collapse_map()
            # D21.2 / AC-D21.2.1: recompute the visible ceiling for a new bar.
            self._recompute_visible_volume_range()
        else:
            self._bars[-1] = bar
            # D28.4: forming-bar tick — live layers only, no static regen.
            # (Refreshes _plot_vols[-1] first so the ceiling check below
            # sees the tick's volume.)
            self._refresh_live_bar()
            # D24 perf: the forming bar's volume only grows; skip the
            # ceiling recompute unless it could raise the ceiling.
            if bar.volume * 1.1 > self._volume_nice_max:
                self._recompute_visible_volume_range()
            return
        self._refresh_candles()
        # D24 perf: overlay x-positions depend on bar timestamps; a forming-bar
        # tick doesn't move them, so skip the set_bars (which repositions labels).
        if new_period:
            if self.drawing_overlay is not None:
                self.drawing_overlay.set_bars(self._plotted_bars)
            if self.alarm_overlay is not None:
                self.alarm_overlay.set_bars(self._plotted_bars)
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
            # D24: read-only pop-outs never delete drawings.
            if (self._editable and self.drawing_overlay is not None
                    and self.drawing_overlay.has_selection()):
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

    def _view_px_per_sec(self):
        """D42: ViewBox logical pixels per display-x unit for the current range.

        The unit ``capped_body_half_width``'s ``px_per_sec`` argument expects
        (``vb.width() / x_span``) — the same scale ``_draw_candles`` reads.
        Returns ``None`` when the view is too small or the span is degenerate.
        """
        try:
            vb = self.price_plot.getViewBox()
            if vb is not None and vb.width() > 50:
                x_range = vb.viewRange()[0]
                x_span = x_range[1] - x_range[0]
                if x_span > 0:
                    return vb.width() / x_span
        except Exception:
            pass
        return None

    def _compute_candle_half_width(self, bars) -> float:
        """D28.4/D42: candle half-width and display-x pitch from median spacing.

        Computed once per full rebuild and cached (``_candle_half_width``);
        forming-bar ticks reuse the cache instead of the O(n log n) sort.  The
        display-x pitch is cached alongside it (``_candle_pitch``, in ViewBox
        logical pixels) so the D42/S14 density cap recovers
        ``median_diff = pitch / px_per_sec`` without re-running that sort.
        """
        if len(bars) > 1:
            diffs = sorted(
                self._to_display(bars[i].ts) - self._to_display(bars[i - 1].ts)
                for i in range(1, len(bars))
            )
            median_diff = diffs[len(diffs) // 2]
            px_per_sec = self._view_px_per_sec()
            self._candle_pitch = (
                median_diff * px_per_sec if px_per_sec else None
            )
            return median_diff * 0.325
        self._candle_pitch = None
        return 0.25  # fallback for a single bar (matches CandlestickItem)

    def _clamp_half_width(self, w: float) -> float:
        """D42/S13: apply the shared density-aware cap to a cached half-width.

        Delegates to ``capped_body_half_width`` — the one implementation the
        candle layers also use — so the volume width cannot drift from the
        candle body (R63).  ``median_diff`` is recovered from the cached
        display-x pitch and the final view scale, matching ``_draw_candles``.
        """
        px_per_sec = self._view_px_per_sec()
        if px_per_sec:
            pitch = self._candle_pitch
            median_diff = (
                pitch / px_per_sec if pitch is not None else w / 0.325
            )
            return capped_body_half_width(median_diff, w, px_per_sec)
        return w

    def _refresh_candles(self, auto_range: bool = False):
        # D21.4: candles/volume are plotted at *display-x* (non-trading time
        # collapsed away), and with Ext Hours OFF only the RTH bars are plotted.
        # ``self._bars`` (and every Bar.ts) stays untouched — display-only.
        # D28.4: the static layer holds closed bars; the live layer holds only
        # the forming bar, so per-tick updates never regenerate the history
        # QPicture.
        bars = self._plotted_bars
        history, live = bars[:-1], bars[-1:]
        candle_data, vol_x, vol_h, vol_colors = [], [], [], []
        for bar in history:
            dx = self._to_display(bar.ts)
            candle_data.append((dx, bar.open, bar.high, bar.low, bar.close))
            vol_x.append(dx)
            vol_h.append(float(bar.volume))
            vol_colors.append('#34d399' if bar.close >= bar.open else '#f87171')
        live_data = []
        for bar in live:
            dx = self._to_display(bar.ts)
            live_data.append((dx, bar.open, bar.high, bar.low, bar.close))

        # Frame the view explicitly from the data: ViewBox.autoRange() mis-computes
        # childrenBounds for epoch-magnitude x-coordinates (anchors xMin at 0),
        # leaving candles as a sub-pixel sliver off-screen.
        if auto_range and bars:
            vb = self.price_plot.getViewBox()
            t0, t1 = self._to_display(bars[0].ts), self._to_display(bars[-1].ts)
            bar_w = (
                self._to_display(bars[1].ts) - self._to_display(bars[0].ts)
                if len(bars) > 1 else 300
            )
            lows = min(b.low for b in bars)
            highs = max(b.high for b in bars)
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

        # AC-D9.1 / ESC-020 / D42: derive the candle half-width AND the display-x
        # pitch from the *final* view range, after the auto-range branch above
        # has applied it.  This is the same generate-before-setRange ordering
        # defect T32/ESC-013 fixed for the candle picture: if the width/pitch are
        # computed before `vb.setRange(...)`, the cap sees the untouched default
        # range on a first load and the dense-view bodies/bars never bind.
        # D28.4: reuse the cached candle half-width for volume (same 65% of
        # median_diff, 35% gap formula); the D42/S13 density cap is applied
        # through the one shared helper (the candle layers get it at generation
        # time from the same pitch instead).
        self._candle_half_width = self._compute_candle_half_width(bars)
        w_vol = self._clamp_half_width(self._candle_half_width) if bars else 0.25

        self.volume_bars.setOpts(x=vol_x, height=vol_h, width=w_vol*2, brushes=vol_colors)
        if live:
            lbar = live[0]
            ldx = self._to_display(lbar.ts)
            self.live_volume.setOpts(
                x=[ldx], height=[float(lbar.volume)], width=w_vol * 2,
                brushes=['#34d399' if lbar.close >= lbar.open else '#f87171'],
            )
        else:
            self.live_volume.setOpts(x=[], height=[], width=w_vol * 2)

        if auto_range and bars:
            # Generate the candle pictures now that the real range is known.
            self.candlestick.set_data(candle_data, width=self._candle_half_width,
                                      pitch=self._candle_pitch)
            self.live_candle.set_data(live_data, width=self._candle_half_width,
                                      pitch=self._candle_pitch)
            # Full load: derive the ceiling from the bars now visible.
            self._recompute_visible_volume_range(force=True)
        else:
            # Non-auto-range refresh (intra-bar redraw / set_timezone / empty
            # load): the ViewBox range is already the real one, so the ceiling
            # computes against it.  Still regenerate to clear/refresh the picture.
            self.candlestick.set_data(candle_data, width=self._candle_half_width,
                                      pitch=self._candle_pitch)
            self.live_candle.set_data(live_data, width=self._candle_half_width,
                                      pitch=self._candle_pitch)
            if bars:
                # auto_range=False refresh: re-apply the visible ceiling so the
                # range tracks the bars currently in view.
                self._recompute_visible_volume_range()

    def _refresh_live_bar(self):
        """D28.4: forming-bar tick — update ONLY the live layers.

        The static history QPicture is untouched (no regen, no width
        recompute, no collapse rebuild); only the 1-bar live candle and the
        1-bar live volume are redrawn.
        """
        bars = self._plotted_bars
        if not bars:
            return
        bar = bars[-1]
        dx = self._to_display(bar.ts)
        self.live_candle.set_data(
            [(dx, bar.open, bar.high, bar.low, bar.close)],
            width=self._candle_half_width,
            pitch=self._candle_pitch,
        )
        color = '#34d399' if bar.close >= bar.open else '#f87171'
        self.live_volume.setOpts(
            x=[dx], height=[float(bar.volume)],
            width=self._clamp_half_width(self._candle_half_width) * 2,
            brushes=[color],
        )
        # D28.4: keep the cached volume array fresh for the ceiling bisect.
        if self._plotted_indices and self._plotted_indices[-1] == len(self._bars) - 1:
            self._plot_vols[-1] = float(bar.volume)

    def _recompute_visible_volume_range(self, force: bool = False) -> float:
        """Recompute the volume Y ceiling from the visible x-range (D21.2).

        AC-D21.2.1: the ceiling is ``1.10 x max(volume of bars whose x lies in
        the currently visible x-range)``; when no bar is visible, or every
        visible bar has zero volume, the ceiling falls back to
        ``VOLUME_NICE_FLOOR`` (100). The Y minimum is always 0 (D21.1 limit).

        This supersedes D8's whole-list nice-max ceiling and ESC-007's
        only-widen rule for zoom/pan, while preserving ESC-007's forming-bar
        no-clip intent: the range is recomputed on every bar update so a growing
        last bar widens the ceiling.

        Writes the volume Y range only when the ceiling actually changes (or
        ``force``), so a non-crossing bar update performs no range write.
        Returns the ceiling currently applied.
        """
        x_range = self.price_plot.getViewBox().viewRange()[0]
        x0, x1 = float(x_range[0]), float(x_range[1])
        # D28.4: bisect the cached display-x array to the visible slice —
        # no O(n) scan on the per-frame pan/zoom path. (D21.2 reconciliation
        # (D21.4): the visible x-range is display-x after collapse, so each
        # bar's *display-x* is compared against it — not the raw timestamp.)
        xs, vols = self._plot_xs, self._plot_vols
        lo = bisect_left(xs, x0)
        hi = bisect_right(xs, x1, lo=lo)
        visible_max = max(vols[lo:hi], default=0.0)
        # ESC-028 / AC-D21.2.1: the ``VOLUME_NICE_FLOOR`` (100) fallback applies
        # ONLY when there is no visible non-zero volume (no visible bar, or every
        # visible bar is zero). For any positive visible max the literal
        # ``1.10 x visible_max`` holds — including the small band
        # ``0 < visible_max <= 90.9`` (e.g. 10 -> 11, 50 -> 55), which a second
        # unconditional ``< VOLUME_NICE_FLOOR`` clamp would incorrectly inflate
        # to 100. Do not reintroduce that clamp.
        if visible_max > 0.0:
            ceiling = visible_max * 1.1
        else:
            ceiling = VOLUME_NICE_FLOOR
        if force or abs(ceiling - self._volume_nice_max) > 1e-9 * max(1.0, abs(ceiling)):
            self._volume_nice_max = ceiling
            self.volume_plot.getViewBox().setRange(yRange=(0, ceiling), padding=0)
        return self._volume_nice_max

    def _on_price_x_range_changed(self, *_args) -> None:
        """Recompute the visible volume ceiling on every visible-x change."""
        self._recompute_visible_volume_range()

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

    # ── D28.4 study computation ──────────────────────────────────────────
    # Numeric studies are computed through the incremental *_update
    # functions (services/indicator_service.py), which exactly match the
    # batch calculate_* tails. The full path feeds every bar once (building
    # fresh states); the new-candle path shifts the cached arrays and
    # computes only the new bar.

    @staticmethod
    def _study_key(stype: str, idx: int) -> str:
        """Per-study-instance cache key (two SMAs with different periods
        must not collide)."""
        return f"{stype}:{idx}"

    def _study_update_one(self, stype: str, params: dict, state: dict,
                          bar) -> dict[str, object]:
        """Advance one study's incremental state with one bar.

        Returns {suffix: value}; the empty suffix is the study's primary
        series (e.g. "bollinger:0" -> upper, "bollinger:0_mid" -> middle).
        """
        if stype == "sma":
            return {"": sma_update(state, bar.close, params.get("period", 20))}
        if stype in ("ema", "ema2"):
            return {"": ema_update(state, bar.close, params.get("period", 9))}
        if stype == "vwap":
            return {"": vwap_update(state, bar.high, bar.low, bar.close,
                                    bar.volume, bar.ts)}
        if stype == "bollinger":
            upper, mid, lower = bollinger_update(
                state, bar.close,
                params.get("period", 20), params.get("std_dev", 2.0))
            return {"": upper, "_mid": mid, "_lower": lower}
        if stype == "rsi":
            return {"": rsi_update(state, bar.close, params.get("period", 14))}
        if stype == "macd":
            m, s = macd_update(
                state, bar.close,
                params.get("fast", 12), params.get("slow", 26),
                params.get("signal", 9))
            return {"": m, "_signal": s}
        return {}

    # Study types with incremental numeric computation (overlay studies —
    # rth_gaps/vix_sd/ict — render directly and are never cached).
    _INCREMENTAL_STUDIES = frozenset(
        {"sma", "ema", "ema2", "vwap", "bollinger", "rsi", "macd"})

    def _study_values_full(self, bars) -> tuple[dict, dict]:
        """Compute every numeric study over all bars, building fresh states."""
        all_vals: dict[str, list] = {}
        states: dict[str, dict] = {}
        for idx, study in enumerate(self._studies):
            if not study.get("enabled"):
                continue
            stype = study["type"]
            if stype not in self._INCREMENTAL_STUDIES:
                continue  # overlay study — rendered, not cached
            params = study.get("params", {})
            key = self._study_key(stype, idx)
            state: dict = {}
            series: dict[str, list] = {}
            for bar in bars:
                for suffix, value in self._study_update_one(
                        stype, params, state, bar).items():
                    series.setdefault(suffix, []).append(value)
            for suffix, vals in series.items():
                all_vals[f"{key}{suffix}"] = vals
            states[key] = state
        return all_vals, states

    def _study_values_incremental(self, cached: dict, new_bar) -> tuple[dict, dict]:
        """Shift cached arrays and compute only the new bar (D28.4)."""
        all_vals = {k: list(v) for k, v in cached["values"].items()}
        states = cached["states"]
        for idx, study in enumerate(self._studies):
            if not study.get("enabled"):
                continue
            stype = study["type"]
            key = self._study_key(stype, idx)
            state = states.get(key)
            if state is None:
                continue  # overlay study — rendered, not cached
            for suffix, value in self._study_update_one(
                    stype, study.get("params", {}), state, new_bar).items():
                all_vals[f"{key}{suffix}"].append(value)
        return all_vals, states

    def _compute_study_values(self, bars) -> tuple[dict, dict]:
        """Full or incremental study computation (D28.4).

        The incremental path applies when the cache holds this exact study
        set for the series ending at the previous bar (n_bars == len-1 and
        the second-to-last timestamp matches) — i.e. exactly one new candle
        arrived. Anything else (fresh load, timeframe/study change, history
        rewrite) takes the full path.
        """
        n = len(bars)
        cached = self._study_cache.get(
            self._symbol, self._current_timeframe or "", self._studies)
        if (cached is not None and n >= 2
                and cached.get("n_bars") == n - 1
                and cached.get("last_ts") == bars[-2].ts):
            return self._study_values_incremental(cached, bars[-1])
        return self._study_values_full(bars)

    def _render_study_values(self, all_vals: dict[str, list], xs: list) -> None:
        """Render precomputed study values (shared by both compute paths)."""
        for idx, study in enumerate(self._studies):
            if not study.get("enabled"):
                continue
            stype = study["type"]
            params = study.get("params", {})
            color = params.get("color", "#ffffff")
            key = self._study_key(stype, idx)

            if stype == "sma":
                self._add_line(xs, all_vals[key], color)
            elif stype in ("ema", "ema2"):
                self._add_line(xs, all_vals[key], color)
            elif stype == "vwap":
                self._add_line(xs, all_vals[key], color, width=1.5)
            elif stype == "bollinger":
                self._add_line(xs, all_vals[key], color)
                self._add_line(xs, all_vals[f"{key}_mid"], color,
                               style=Qt.PenStyle.DotLine)
                self._add_line(xs, all_vals[f"{key}_lower"], color)
            elif stype == "rsi":
                ob = params.get("overbought", 70)
                os_ = params.get("oversold", 30)
                self._add_osc_line(xs, all_vals[key], "#818cf8")
                self._add_osc_hline(ob, "#f87171", style=Qt.PenStyle.DotLine)
                self._add_osc_hline(os_, "#34d399", style=Qt.PenStyle.DotLine)
            elif stype == "macd":
                macd_line = all_vals[key]
                signal_line = all_vals[f"{key}_signal"]
                self._add_osc_line(xs, macd_line,   "#60a5fa")
                self._add_osc_line(xs, signal_line, "#f59e0b")
                bar_x, bar_h, bar_c = [], [], []
                for i, (m, s) in enumerate(zip(macd_line, signal_line)):
                    if m is not None and s is not None:
                        # D27.2: histogram bars share the lines' display-x
                        # axis; raw indices would render off-screen.
                        bar_x.append(xs[i])
                        bar_h.append(m - s)
                        bar_c.append('#34d399' if m - s >= 0 else '#f87171')
                hist_bars = pg.BarGraphItem(x=bar_x, height=bar_h, width=0.6, brushes=bar_c)
                self.osc_plot.addItem(hist_bars)
                self._osc_items.append(hist_bars)
            elif stype == "rth_gaps":
                ticker = infer_ticker_context(self._symbol, self._bars)
                gaps = calculate_rth_gaps(self._bars, ticker, params)
                self._gap_overlay.render(gaps, self._bars)
            elif stype == "vix_sd":
                ticker = infer_ticker_context(self._symbol, self._bars)
                result = calculate_vix_standard_deviation(ticker, self._bars, params)
                self._vix_overlay.render(result, self._bars)
            elif stype == "ict":
                # D28.4: ICT concepts are capped to a trailing window — the
                # overlay takes window-relative indices with the window's own
                # bars, so indices stay consistent by construction.
                ticker = infer_ticker_context(self._symbol, self._bars)
                window = self._bars[-ICT_TRAILING_BARS:]
                result = calculate_ict_concepts(window, ticker, params)
                self._ict_overlay.render(result, window)

    def _apply_studies(self):
        self._clear_overlays()
        if not self._bars:
            return

        bars = self._bars
        # D21.4: indicator lines share the price/volume x-axis, so plot them at
        # display-x too (aligned with the collapsed candles).
        xs = [self._to_display(b.ts) for b in bars]

        # D28.4: full or incremental computation — the cache is actually read.
        all_vals, states = self._compute_study_values(bars)
        self._render_study_values(all_vals, xs)

        # Cache values + incremental states for the new-candle path.
        if all_vals:
            self._study_cache.set(
                self._symbol, self._current_timeframe or "", self._studies,
                {"n_bars": len(bars), "last_ts": bars[-1].ts,
                 "values": {k: list(v) for k, v in all_vals.items()},
                 "states": states},
            )

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
