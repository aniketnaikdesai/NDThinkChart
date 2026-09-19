"""
chart_panel.py
Main chart widget: price plot (candlestick + indicator overlays)
+ volume subplot linked on the X-axis.
Supports 5 render modes and dynamic study overlays.
"""

import hashlib
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSplitter
from PyQt6.QtCore import Qt

from ui.candlestick_item import CandlestickItem, ChartMode
from ui.drawing_overlay import DrawingViewBox, DrawingOverlay
from ui.alarm_overlay import AlarmOverlay
from ui.chart_mouse_router import ChartMouseRouter
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


class ChartPanel(QWidget):
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

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Price plot ────────────────────────────────────────────────────────
        self.drawing_overlay = None
        self.alarm_overlay = None
        self.mouse_router = ChartMouseRouter()

        # Create PlotWidget with default ViewBox so DateAxisItem links properly
        self.price_plot = pg.PlotWidget()
        self.price_plot.showGrid(x=True, y=True, alpha=0.08)
        self.price_plot.getAxis('left').setStyle(tickFont=None)
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
            ov = self.drawing_overlay
            if ov is not None and ov.view_mouse_press(ev):
                ev.ignore()
                return
            orig_mousePressEvent(ev)

        def mouseDragEvent(ev, axis=None):
            ov = self.drawing_overlay
            if ov is not None and ov.view_mouse_drag(ev):
                ev.accept()
                return
            orig_mouseDragEvent(ev, axis)

        def mouseClickEvent(ev):
            ov = self.drawing_overlay
            if ov is not None and ov.view_mouse_click(ev):
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

        # Set up hover event for crosshair
        vb = self.price_plot.getViewBox()
        vb.scene().sigMouseHover.connect(self._on_mouse_hover)

        # Advanced study renderers
        self._gap_overlay = RthGapOverlay(self.price_plot)
        self._vix_overlay = VixOverlay(self.price_plot)
        self._ict_overlay = ICTStudyOverlay(self.price_plot)

        # ── Volume plot ───────────────────────────────────────────────────────
        self.volume_plot = pg.PlotWidget()
        self.volume_plot.setMaximumHeight(120)
        self.volume_plot.showGrid(x=True, y=True, alpha=0.05)
        self.volume_plot.setXLink(self.price_plot)
        # Use DateAxisItem for volume too, with proper formatting
        vol_date_axis = _custom_date_axis(utc=(self._tz_offset == 0), tz_offset=self._tz_offset)
        self.volume_plot.setAxisItems({'bottom': vol_date_axis})
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.volume_plot.addItem(self.volume_bars)

        # ── Oscillator plot (RSI / MACD) ──────────────────────────────────────
        self.osc_plot = pg.PlotWidget()
        self.osc_plot.setMaximumHeight(120)
        self.osc_plot.showGrid(x=True, y=True, alpha=0.05)
        self.osc_plot.setXLink(self.price_plot)
        self.osc_plot.hide()            # hidden until an oscillator study is enabled

        splitter.addWidget(self.price_plot)
        splitter.addWidget(self.volume_plot)
        splitter.addWidget(self.osc_plot)
        splitter.setSizes([600, 120, 120])
        layout.addWidget(splitter)

    # ── Public API ─────────────────────────────────────────────────────────────

    def _router_ref(self):
        return self.mouse_router

    def _on_mouse_hover(self, event):
        """Handle mouse hover events to update crosshair."""
        if not isinstance(event, list):
            pos = event.scenePos()
            if self.price_plot.scene() and pos:
                self._update_crosshair(pos)
        else:
            for ev in event:
                pos = ev.scenePos()
                if self.price_plot.scene() and pos:
                    self._update_crosshair(pos)

    def _create_crosshair(self):
        """Create crosshair lines and tooltip for hover display."""
        self.crosshair_v = pg.InfiniteLine(pen=pg.mkPen('#94a3b8', width=1, style=Qt.PenStyle.DashLine))
        self.crosshair_h = pg.InfiniteLine(pen=pg.mkPen('#94a3b8', width=1, style=Qt.PenStyle.DashLine))
        self.price_plot.addItem(self.crosshair_v)
        self.price_plot.addItem(self.crosshair_h)

        # Tooltip label for time and price
        self.crosshair_label = pg.TextItem(anchor=(0.5, 1), fill=pg.mkColor('#0d0f14ff'))
        self.crosshair_label.setColor('#e2e8f0')
        self.price_plot.addItem(self.crosshair_label)
        self.crosshair_label.hide()

    def _update_crosshair(self, pos):
        """Update crosshair position and show tooltip with time/price."""
        if not self._bars or not pos:
            self.crosshair_label.hide()
            self.crosshair_v.hide()
            self.crosshair_h.hide()
            return

        x, y = pos.x(), pos.y()

        # Update crosshair lines
        self.crosshair_v.setPos(x)
        self.crosshair_h.setPos(y)
        self.crosshair_v.show()
        self.crosshair_h.show()

        # Find closest bar and get interpolated price
        closest_bar_idx = self._find_closest_bar(x)
        if closest_bar_idx >= 0:
            bar = self._bars[closest_bar_idx]
            time_str = self._format_time(bar.ts)
            price = y

            # Show crosshair label
            self.crosshair_label.setText(f"{time_str}\n{price:.2f}")
            self.crosshair_label.setPos(x, y - 20)
            self.crosshair_label.show()
        else:
            self.crosshair_label.hide()

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

    def _format_time(self, ts):
        """Format timestamp for display."""
        from datetime import datetime
        dt = datetime.fromtimestamp(ts)
        return dt.strftime('%m/%d %H:%M:%S')

    def set_chart_mode(self, mode: ChartMode):
        self.candlestick.set_mode(mode)

    def set_alarm_mode(self, enabled: bool):
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_alarm_mode(enabled)

    def set_alarms(self, alarms):
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_data(alarms)

    def set_symbol(self, symbol: str):
        self._symbol = symbol
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_symbol(symbol)

    def set_drawing_tool(self, tool: str):
        self.setFocus()
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_tool(tool)

    def set_studies(self, studies: list):
        self._studies = studies
        self._study_cache.invalidate(self._symbol, self._current_timeframe)
        if self._bars:
            self._apply_studies()

    def set_timeframe(self, timeframe: str):
        self._current_timeframe = timeframe

    def set_timezone(self, tz_offset: int):
        """Change the timezone offset for x-axis display (seconds from UTC)."""
        self._tz_offset = tz_offset
        # Recreate axes with new timezone
        date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.price_plot.setAxisItems({'bottom': date_axis})
        vol_date_axis = _custom_date_axis(utc=(tz_offset == 0), tz_offset=tz_offset)
        self.volume_plot.setAxisItems({'bottom': vol_date_axis})
        self._refresh_candles()  # Redraw to update axis labels

    def update_chart(self, bars):
        """Full refresh — called after historical data loads."""
        if not bars:
            # Clear chart explicitly for empty load (e.g., SPY first load
            # before IBKR delta returns). Avoid stale data from previous symbol.
            self._bars = []
            self._refresh_candles()
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
        if is_new_candle or self._bars[-1].ts != bar.ts:
            self._bars.append(bar)
        else:
            self._bars[-1] = bar
        self._refresh_candles()
        if self.drawing_overlay is not None:
            self.drawing_overlay.set_bars(self._bars)
        if self.alarm_overlay is not None:
            self.alarm_overlay.set_bars(self._bars)
        if is_new_candle:
            self._apply_studies()

    def keyPressEvent(self, event):
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

    def _refresh_candles(self, auto_range: bool = False):
        candle_data, vol_x, vol_h, vol_colors = [], [], [], []
        for bar in self._bars:
            candle_data.append((bar.ts, bar.open, bar.high, bar.low, bar.close))
            vol_x.append(bar.ts)
            vol_h.append(bar.volume)
            vol_colors.append('#34d399' if bar.close >= bar.open else '#f87171')

        self.candlestick.set_data(candle_data)
        self.volume_bars.setOpts(x=vol_x, height=vol_h, brushes=vol_colors)
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
            vb.setRange(xRange=(t0 - 2 * bar_w, t1 + 8 * bar_w),
                        yRange=(lows, highs), padding=0.03)
            max_vol = max((b.volume for b in self._bars), default=1.0)
            self.volume_plot.getViewBox().setRange(yRange=(0.0, max(max_vol, 1.0) * 1.1))

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
