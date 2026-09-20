import threading
from copy import deepcopy
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")


def _eastern_offset(now: datetime | None = None) -> int:
    """Return pyqtgraph utcOffset for Eastern Time (positive = behind UTC).

    EDT (UTC-4) -> 14400, EST (UTC-5) -> 18000. Uses live DST.
    """
    ts = now if now is not None else datetime.now(_EASTERN)
    return -int(ts.utcoffset().total_seconds())  # type: ignore[union-attr]
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QStatusBar, QDockWidget
)
from PyQt6.QtCore import Qt, QSettings

from config import settings
from ibkr.client import IBApiClient, ConnectionState
from ibkr.market_data import MarketDataManager, TIMEFRAME_CONFIG
from ibkr.market_depth import MarketDepthManager
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.contracts import get_contract_for_symbol
from ibkr.utils import parse_ibkr_date
from ibkr.orders import orders as order_registry
from ibkr.id_manager import id_manager
from ibkr.pacing import pacing_manager
from ibkr.subscription_manager import SubscriptionManager
from ui.chart_panel import ChartPanel
from ui.candlestick_item import ChartMode
from ui.watchlist_panel import (
    WatchlistPanel,
    WATCHLIST_MIN_WIDTH,
    load_watchlist_width,
    save_watchlist_width,
    clamp_watchlist_width,
    watchlist_max_width,
    should_load_on_double_click,
)
from ui.studies_dialog import StudiesDialog, DEFAULT_STUDIES
from ui.alarm_dialog import AlarmDialog
from ui.drawing_groups_dialog import DrawingGroupsDialog
from ui.active_trader_panel import ActiveTraderPanel, on_depth_callback
from ui.active_portfolio_panel import ActivePortfolioPanel
from ui.toast import Toast
from data.alarm_store import AlarmStore
from data.models import Bar, Position
from data.bar_cache import BarCache
from data.bar_aggregator import BarAggregator
from data.study_store import StudyStore
from data.drawing_store import DrawingStore
from data.db import db
from services.alarm_service import evaluate_alarms
from services.drawing_service import DEFAULT_DRAWING_COLOR
from services.sound_service import SoundService

# Default watchlist symbols — used only on first run before DB persistence
DEFAULT_WATCHLIST = ["AAPL", "TSLA", "SPY", "QQQ", "NVDA"]


def _ibkr_end_date(ts: int) -> str:
    """Format as IBKR endDateTime yyyyMMdd-HH:mm:ss in UTC.

    The hyphenated format explicitly signals UTC to TWS and avoids
    warning 2174. The space-separated format is deprecated and
    treated as instrument local time zone.
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d-%H:%M:%S")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IBKR Trading Terminal")
        self.resize(1400, 900)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet("background: #101218; border-bottom: 1px solid #232938;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 0, 8, 0)
        tb_layout.setSpacing(6)

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Symbol (e.g. AAPL)")
        self.symbol_input.setFixedWidth(120)
        self.symbol_input.returnPressed.connect(self.load_chart)

        self.tf_combo = QComboBox()
        self.tf_combo.addItems(list(TIMEFRAME_CONFIG.keys()))
        self.tf_combo.setCurrentText("5 mins")
        self.tf_combo.setFixedWidth(90)

        self.load_btn = QPushButton("Load Chart")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.load_chart)

        # Chart-mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Candles", "Hollow", "Heikin-Ashi", "Line", "Area"])
        self.mode_combo.setFixedWidth(110)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

        # Studies button
        self.studies_btn = QPushButton("Studies…")
        self.studies_btn.clicked.connect(self._open_studies_dialog)

        self.alarms_btn = QPushButton("Alarms (0)")
        self.alarms_btn.clicked.connect(self._open_alarm_dialog)

        self.alarm_mode_btn = QPushButton("Alarm Mode")
        self.alarm_mode_btn.setCheckable(True)
        self.alarm_mode_btn.toggled.connect(self._on_alarm_mode_toggled)

        self.sound_btn = QPushButton("Sound")
        self.sound_btn.setFixedWidth(56)
        self.sound_btn.setCheckable(True)
        self.sound_btn.setChecked(True)
        self.sound_btn.setToolTip("Alert sounds")
        self.sound_btn.toggled.connect(self._on_sound_toggled)

        # DOM / Active Trader toggle
        self.dom_btn = QPushButton("DOM")
        self.dom_btn.setCheckable(True)
        self.dom_btn.setChecked(False)
        self.dom_btn.setToolTip("Market Depth / Active Trader Panel")
        self.dom_btn.toggled.connect(self._on_dom_toggled)

        # Extended Hours toggle
        self.ext_hours_btn = QPushButton("Ext Hours")
        self.ext_hours_btn.setCheckable(True)
        self.ext_hours_btn.setChecked(True)  # Default to extended hours
        self.ext_hours_btn.setToolTip("Include pre/post-market data")
        self.ext_hours_btn.setFixedWidth(80)
        self.ext_hours_btn.toggled.connect(self._on_ext_hours_toggled)

        # Timezone selector
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(["UTC", "Eastern Time"])
        self.tz_combo.setCurrentText("Eastern Time")
        self.tz_combo.setFixedWidth(110)
        self.tz_combo.setToolTip("Chart x-axis timezone")
        self.tz_combo.currentTextChanged.connect(self._on_tz_changed)

        # Drawing tools
        self.draw_combo = QComboBox()
        self.draw_combo.addItems(["Cursor", "Trendline", "Horizontal", "Zone", "Fibonacci", "Measure"])
        self.draw_combo.setFixedWidth(110)
        self.draw_combo.currentTextChanged.connect(self._on_draw_tool_changed)

        self.draw_set_combo = QComboBox()
        self.draw_set_combo.setFixedWidth(140)
        self.draw_set_combo.currentIndexChanged.connect(self._on_active_draw_group_changed)

        self.draw_sets_btn = QPushButton("Sets…")
        self.draw_sets_btn.clicked.connect(self._open_drawing_groups_dialog)

        self.draw_delete_btn = QPushButton("Del")
        self.draw_delete_btn.setFixedWidth(38)
        self.draw_delete_btn.setEnabled(False)
        self.draw_delete_btn.clicked.connect(self._delete_selected_drawing)

        self.conn_badge = QLabel("● Connecting")
        self.conn_badge.setStyleSheet("color: #fbbf24;")

        tb_layout.addWidget(QLabel("Symbol:"))
        tb_layout.addWidget(self.symbol_input)
        tb_layout.addWidget(QLabel("TF:"))
        tb_layout.addWidget(self.tf_combo)
        tb_layout.addWidget(self.load_btn)
        tb_layout.addWidget(QLabel("|"))
        tb_layout.addWidget(QLabel("Mode:"))
        tb_layout.addWidget(self.mode_combo)
        tb_layout.addWidget(self.studies_btn)
        tb_layout.addWidget(self.alarms_btn)
        tb_layout.addWidget(self.alarm_mode_btn)
        tb_layout.addWidget(self.sound_btn)
        tb_layout.addWidget(self.dom_btn)
        tb_layout.addWidget(self.ext_hours_btn)
        tb_layout.addWidget(self.tz_combo)
        tb_layout.addWidget(QLabel("|"))
        tb_layout.addWidget(QLabel("Draw:"))
        tb_layout.addWidget(self.draw_combo)
        tb_layout.addWidget(self.draw_set_combo)
        tb_layout.addWidget(self.draw_sets_btn)
        tb_layout.addWidget(self.draw_delete_btn)
        tb_layout.addStretch()
        tb_layout.addWidget(self.conn_badge)

        # ── Central chart area ────────────────────────────────────────────────
        # Dynamic Eastern offset (DST-aware): EDT=14400, EST=18000
        self._tz_offset = _eastern_offset()
        self.chart_panel = ChartPanel(tz_offset=self._tz_offset)
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(toolbar)
        vbox.addWidget(self.chart_panel)
        self.setCentralWidget(central)

        # ── Watchlist dock ────────────────────────────────────────────────────
        self.watchlist_panel = WatchlistPanel()
        self.watchlist_dock = QDockWidget("Watchlist", self)
        self.watchlist_dock.setWidget(self.watchlist_panel)
        self.watchlist_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.watchlist_panel.setMinimumWidth(WATCHLIST_MIN_WIDTH)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.watchlist_dock)
        # D13: restore persisted width (clamped) and clamp on window resize
        self._settings = QSettings("NDThinkChart", "NDThinkChart")
        self._watchlist_width = load_watchlist_width(self._settings, self.width())
        self.resizeDocks([self.watchlist_dock], [self._watchlist_width], Qt.Orientation.Horizontal)
        # D14: double-click a row loads the chart
        self.watchlist_panel.row_double_clicked.connect(self._on_watchlist_row_double_clicked)

        # ── Active Trader dock (DOM) ──────────────────────────────────────
        self.active_trader = ActiveTraderPanel()
        trader_dock = QDockWidget("Active Trader", self)
        trader_dock.setWidget(self.active_trader)
        trader_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, trader_dock)

        # ── Portfolio dock ─────────────────────────────────────────────────────
        self.portfolio_panel = ActivePortfolioPanel()
        portfolio_dock = QDockWidget("Portfolio", self)
        portfolio_dock.setWidget(self.portfolio_panel)
        portfolio_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, portfolio_dock)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Connecting to IBKR…")

        # ── IBKR client ───────────────────────────────────────────────────────
        self.ib_client = IBApiClient()
        self.md_manager = MarketDataManager(self.ib_client)
        self.rt_manager = RealtimeBarsManager(self.ib_client)
        self.depth_manager = MarketDepthManager(self.ib_client)
        self.sub_manager = SubscriptionManager()

        # Inject md_manager into watchlist
        self.watchlist_panel.set_market_data_manager(self.md_manager)
        self.watchlist_panel.set_depth_manager(self.depth_manager)

        # Drawing overlay wiring
        self.chart_panel.drawing_overlay.created.connect(self._on_drawing_created)
        self.chart_panel.drawing_overlay.updated.connect(self._on_drawing_updated)
        self.chart_panel.drawing_overlay.deleted.connect(self._on_drawing_deleted)
        self.chart_panel.drawing_overlay.selection_changed.connect(self._on_drawing_selection_changed)

        # Alarm overlay wiring
        aov = self.chart_panel.alarm_overlay
        aov.create_requested.connect(self._on_alarm_create_requested)
        aov.moved.connect(self._on_alarm_moved)
        aov.mute_toggled.connect(self._on_alarm_mute_toggled)
        aov.rearm_requested.connect(self._on_alarm_rearm_requested)
        aov.delete_requested.connect(self._on_alarm_delete_requested)

        # Alert sounds + transient toast
        self.sound_service = SoundService(enabled=True)
        self.sound_service.warm()
        self.toast = Toast(self.chart_panel)

        # Bridge signal wiring
        b = self.ib_client.bridge
        b.connected.connect(self._on_connected)
        b.disconnected.connect(self._on_disconnected)
        b.error_msg.connect(self._on_error)
        b.historical_bar.connect(self._on_historical_bar)
        b.historical_data_end.connect(self._on_historical_data_end)
        b.tick_price.connect(self.watchlist_panel.on_tick_price)
        b.tick_size.connect(self.watchlist_panel.on_tick_size)
        b.realtime_bar.connect(self._on_realtime_bar)
        b.update_mkt_depth.connect(self._on_mkt_depth)
        b.open_order.connect(self._on_open_order)
        b.exec_details.connect(self._on_exec_details)
        b.order_status.connect(self._on_order_status)

        # Account & portfolio signals
        b.account_summary.connect(self._on_account_summary)
        b.account_summary_end.connect(self._on_account_summary_end)
        b.position_update.connect(self._on_position_update)
        b.position_end.connect(self._on_position_end)

        # Initialize empty portfolio display
        self.portfolio_panel.set_account_summary({})
        self.portfolio_panel.set_positions([])

        # Portfolio panel signal wiring
        self.portfolio_panel.position_close_requested.connect(self._on_portfolio_close_position)
        self.portfolio_panel.group_close_requested.connect(self._on_portfolio_close_group)
        self.portfolio_panel.flatten_all_requested.connect(self._on_portfolio_flatten_all)
        self.portfolio_panel.position_sltp_changed.connect(self._on_portfolio_sltp_changed)
        self.portfolio_panel.group_sltp_changed.connect(self._on_portfolio_group_sltp_changed)

        # Active trader order entry
        self.active_trader.order_place_requested.connect(self._on_order_place_requested)

        # State
        self._current_req_id: int | None = None
        self._depth_req_id: int | None = None
        self._pending_bars: list[Bar] = []
        self._current_symbol: str = ""
        self._current_tf: str = "5 mins"
        self._rt_req_id: int | None = None
        self._aggregator: BarAggregator | None = None
        self._current_studies: list[dict] = deepcopy(DEFAULT_STUDIES)
        self._current_alarms = []
        self._last_chart_price: float | None = None
        self._active_draw_group_id: int | None = None
        self._pending_brackets: dict[int, tuple[str, float]] = {}  # parent_id -> (action, qty)

        # Start connection
        self.ib_client.connect(settings.IBKR_HOST, settings.IBKR_PORT, settings.IBKR_CLIENT_ID)
        threading.Thread(target=self.ib_client.run, daemon=True, name="ibkr-reader").start()

    # ── Connection slots ──────────────────────────────────────────────────────

    def _on_connected(self):
        self.conn_badge.setText("● Live")
        self.conn_badge.setStyleSheet("color: #34d399;")
        self.load_btn.setEnabled(True)
        self.status_bar.showMessage(f"Connected — IBKR port {settings.IBKR_PORT}")
        self._restore_watchlist()
        self._replay_subscriptions()

    def _restore_watchlist(self):
        saved = db.get_watchlist()
        symbols = [sym for sym, _cat in saved] if saved else []
        if not symbols:
            symbols = list(DEFAULT_WATCHLIST)
            db.set_watchlist(symbols)
        for sym in symbols:
            self.watchlist_panel.add_symbol(sym, get_contract_for_symbol(sym))

    def _replay_subscriptions(self):
        """Replay all recorded subscriptions after reconnection."""
        for symbol in self.sub_manager._subscriptions:
            req_ids = self.sub_manager.get_req_ids(symbol)
            contract = get_contract_for_symbol(symbol)
            for req_id in req_ids:
                self.rt_manager.subscribe(symbol, contract)
            # Also replay market depth
            # self.depth_manager needs integration, skip for now

    def _on_disconnected(self):
        self.conn_badge.setText("● Disconnected")
        self.conn_badge.setStyleSheet("color: #f87171;")
        self.load_btn.setEnabled(False)
        self.status_bar.showMessage("Disconnected from IBKR")

    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        self.status_bar.showMessage(f"Error [{errorCode}]: {errorString}", 8000)

    # ── Chart loading ─────────────────────────────────────────────────────────

    def load_chart(self):
        symbol = self.symbol_input.text().strip().upper()
        timeframe = self.tf_combo.currentText()
        if not symbol:
            self.status_bar.showMessage("Enter a symbol first.", 3000)
            return

        # Cancel any previous RT subscription
        if self._rt_req_id is not None:
            self.rt_manager.unsubscribe(self._rt_req_id)
            self._rt_req_id = None

        self._current_symbol = symbol
        self._current_tf = timeframe
        self._pending_bars = []
        self.chart_panel.set_symbol(symbol)
        self.chart_panel.set_timeframe(timeframe)
        self.chart_panel.set_extended_hours(self.ext_hours_btn.isChecked())
        self._reload_drawings(symbol)
        self._refresh_drawing_groups(symbol)
        self._current_studies = self._load_studies_for_symbol(symbol)
        self.chart_panel.set_studies(self._current_studies)
        self._current_alarms = AlarmStore.load(symbol)
        self._refresh_alarm_badge()

        # Create a fresh aggregator for the new symbol/timeframe
        self._aggregator = BarAggregator(
            symbol=symbol,
            timeframe=timeframe,
            on_bar_update=self._on_aggregated_bar,
        )

        # Step 1: Show cached bars immediately
        cached = BarCache.get_bars(symbol, timeframe)
        self._last_chart_price = cached[-1].close if cached else None
        if cached:
            self.chart_panel.update_chart(cached)
            self.status_bar.showMessage(
                f"{symbol} — {len(cached)} cached bars. Fetching delta…"
            )

        # Step 2: Fetch delta from IBKR up to now (covers gap since cache).
        # Previously end_dt = last_ts+60 anchored the window to the stale cache
        # end, so bars after the cache (e.g., Fri 14:00-20:00) were never fetched.
        # end_dt="" means up-to-now; overlap is deduped by INSERT OR REPLACE.
        end_dt = ""
        contract = get_contract_for_symbol(symbol)
        ext_hours = self.ext_hours_btn.isChecked()
        self._current_req_id = self.md_manager.req_historical_data(
            contract=contract,
            timeframe=timeframe,
            endDateTime=end_dt,
            whatToShow="TRADES",
            useRTH=1,
            extended_hours=ext_hours,
        )

        # Step 3: Start real-time bar stream
        self._rt_req_id = self.rt_manager.subscribe(symbol, contract)

        # DOM subscription (only if DOM panel is visible)
        if self.dom_btn.isChecked():
            self._subscribe_dom()

        self.status_bar.showMessage(
            f"Requesting {symbol} [{timeframe}]… (hist reqId {self._current_req_id},"
            f" rt reqId {self._rt_req_id})"
        )

    # ── Drawing slots ─────────────────────────────────────────────────────────

    def _reload_drawings(self, symbol: str):
        groups = DrawingStore.groups_for_symbol(symbol)
        drawings = DrawingStore.drawings_for_symbol(symbol)
        if self._active_draw_group_id not in {g.id for g in groups}:
            self._active_draw_group_id = None
        self.chart_panel.drawing_overlay.set_data(symbol, drawings, groups)
        self._apply_active_draw_group()

    def _refresh_drawing_groups(self, symbol: str):
        self.draw_set_combo.blockSignals(True)
        self.draw_set_combo.clear()
        self.draw_set_combo.addItem("— Ungrouped —", None)
        for group in DrawingStore.groups_for_symbol(symbol):
            self.draw_set_combo.addItem(group.name, group.id)
        index = self.draw_set_combo.findData(self._active_draw_group_id)
        self.draw_set_combo.setCurrentIndex(index if index >= 0 else 0)
        self.draw_set_combo.blockSignals(False)
        self._apply_active_draw_group()

    def _apply_active_draw_group(self):
        color = DEFAULT_DRAWING_COLOR
        groups = DrawingStore.groups_for_symbol(self._current_symbol) if self._current_symbol else []
        for group in groups:
            if group.id == self._active_draw_group_id and group.color:
                color = group.color
        self.chart_panel.drawing_overlay.set_active_group(self._active_draw_group_id, color)

    def _on_active_draw_group_changed(self, _index: int):
        self._active_draw_group_id = self.draw_set_combo.currentData()
        self._apply_active_draw_group()

    def _on_draw_tool_changed(self, label: str):
        tool = {
            "Cursor": "cursor",
            "Trendline": "trendline",
            "Horizontal": "horizontal",
            "Zone": "zone",
            "Fibonacci": "fibonacci",
            "Measure": "measure",
        }.get(label, "cursor")
        if tool != "cursor" and self.alarm_mode_btn.isChecked():
            self.alarm_mode_btn.setChecked(False)
        self.chart_panel.set_drawing_tool(tool)

    def _on_drawing_created(self, drawing):
        drawing_id = DrawingStore.create_drawing(drawing)
        drawing.id = drawing_id
        self.chart_panel.drawing_overlay.add_drawing(drawing)
        self.status_bar.showMessage(
            f"Drawing added ({drawing.kind}) on {drawing.symbol}.", 3000
        )

    def _on_drawing_updated(self, drawing_id: int, payload: dict):
        DrawingStore.update_drawing(drawing_id, payload)

    def _on_drawing_deleted(self, drawing_id: int):
        DrawingStore.delete_drawing(drawing_id)
        self.status_bar.showMessage("Drawing deleted.", 2000)

    def _on_drawing_selection_changed(self, drawing_id: int):
        self.draw_delete_btn.setEnabled(drawing_id >= 0)

    def _delete_selected_drawing(self):
        self.chart_panel.drawing_overlay.delete_selected()

    def _open_drawing_groups_dialog(self):
        if not self._current_symbol:
            self.status_bar.showMessage("Load a symbol before managing drawing sets.", 3000)
            return
        dialog = DrawingGroupsDialog(self._current_symbol, self)
        dialog.changed.connect(self._on_drawing_groups_changed)
        dialog.exec()

    def _on_drawing_groups_changed(self):
        if not self._current_symbol:
            return
        groups = DrawingStore.groups_for_symbol(self._current_symbol)
        drawings = DrawingStore.drawings_for_symbol(self._current_symbol)
        self.chart_panel.drawing_overlay.set_data(self._current_symbol, drawings, groups)
        self._refresh_drawing_groups(self._current_symbol)

    # ── Historical data slots ─────────────────────────────────────────────────

    def _on_historical_bar(self, reqId: int, bar):
        if reqId != self._current_req_id:
            return
        ts = parse_ibkr_date(bar.date)
        self._pending_bars.append(Bar(
            symbol=self._current_symbol,
            timeframe=self._current_tf,
            ts=ts,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=float(bar.volume),
        ))

    def _on_historical_data_end(self, reqId: int):
        if reqId != self._current_req_id:
            return
        BarCache.save_bars(self._pending_bars)
        all_bars = BarCache.get_bars(self._current_symbol, self._current_tf)
        self.chart_panel.update_chart(all_bars)
        self._last_chart_price = all_bars[-1].close if all_bars else None
        self.status_bar.showMessage(
            f"{self._current_symbol} — {len(all_bars)} bars "
            f"({len(self._pending_bars)} new). Live stream active."
        )
        self._pending_bars = []

    # ── Real-time bar slot ────────────────────────────────────────────────────

    def _on_realtime_bar(self, reqId: int, time: int, o: float, h: float,
                         l: float, c: float, vol: float, wap: float, count: int):
        if reqId != self._rt_req_id or self._aggregator is None:
            return
        self._aggregator.push(time, o, h, l, c, vol)

    def _on_aggregated_bar(self, bar: Bar, is_new_candle: bool):
        """Called by BarAggregator on main thread (signal is already queued)."""
        self.chart_panel.update_last_bar(bar, is_new_candle)
        triggered = evaluate_alarms(
            self._last_chart_price,
            bar.close,
            self._current_alarms,
        )
        for alarm in triggered:
            if alarm.id is not None:
                AlarmStore.mark_triggered(alarm.id)
            alarm.triggered = True
            self.status_bar.showMessage(
                f"{bar.symbol} alarm triggered at {alarm.price:.4f}", 8000
            )
        if triggered:
            self._refresh_alarm_badge()
            self._notify_alarm_triggered(triggered)
        self._last_chart_price = bar.close

    def _notify_alarm_triggered(self, triggered: list):
        lines = [
            f"{a.price:.4f} ({a.note})" if a.note else f"{a.price:.4f}"
            for a in triggered
        ]
        self.toast.show_message(f"Alarm: {self._current_symbol} @ " + ", ".join(lines))
        if any(a.sound for a in triggered):
            self.sound_service.play_alarm()

    # ── Chart controls ────────────────────────────────────────────────────────

    def _on_mode_changed(self, label: str):
        mode_by_label = {
            "Candles": ChartMode.CANDLES,
            "Hollow": ChartMode.HOLLOW,
            "Heikin-Ashi": ChartMode.HEIKIN,
            "Line": ChartMode.LINE,
            "Area": ChartMode.AREA,
        }
        self.chart_panel.set_chart_mode(mode_by_label.get(label, ChartMode.CANDLES))

    def _open_studies_dialog(self):
        dialog = StudiesDialog(self._current_studies, self)
        dialog.studies_changed.connect(self._on_studies_changed)
        dialog.exec()

    def _open_alarm_dialog(self):
        if not self._current_symbol:
            self.status_bar.showMessage("Load a symbol before creating alarms.", 3000)
            return
        dialog = AlarmDialog(self._current_symbol, self._last_chart_price, self)
        dialog.alarms_changed.connect(self._reload_current_alarms)
        dialog.exec()
        self._reload_current_alarms()

    def _on_studies_changed(self, studies: list[dict]):
        self._current_studies = deepcopy(studies)
        self.chart_panel.set_studies(self._current_studies)
        if self._current_symbol:
            StudyStore.save(self._current_symbol, self._current_studies)
            self.status_bar.showMessage(
                f"{self._current_symbol} studies saved.", 3000
            )

    def _load_studies_for_symbol(self, symbol: str) -> list[dict]:
        saved_by_type = {study["type"]: study for study in StudyStore.load(symbol)}
        merged: list[dict] = []
        for default in DEFAULT_STUDIES:
            cfg = deepcopy(default)
            saved = saved_by_type.get(cfg["type"])
            if saved:
                cfg["enabled"] = saved.get("enabled", cfg["enabled"])
                cfg["params"].update(saved.get("params", {}))
            merged.append(cfg)
        return merged

    def _reload_current_alarms(self):
        if not self._current_symbol:
            return
        self._current_alarms = AlarmStore.load(self._current_symbol)
        self._refresh_alarm_badge()

    def _refresh_alarm_badge(self):
        active_count = sum(
            1 for alarm in self._current_alarms
            if alarm.active and not alarm.triggered
        )
        triggered_count = sum(1 for alarm in self._current_alarms if alarm.triggered)
        label = f"Alarms ({active_count})"
        if triggered_count:
            label += f" / {triggered_count}"
        self.alarms_btn.setText(label)
        self.chart_panel.set_alarms(self._current_alarms)

    # ── Alarm overlay slots ───────────────────────────────────────────────────

    def _on_alarm_mode_toggled(self, enabled: bool):
        self.chart_panel.set_alarm_mode(enabled)
        if enabled:
            self.draw_combo.setCurrentText("Cursor")
            self.status_bar.showMessage(
                "Alarm mode: click the chart to place a price alarm.", 4000
            )

    def _on_sound_toggled(self, enabled: bool):
        self.sound_service.set_enabled(enabled)

    # ── Watchlist width / double-click slots (D13 / D14) ─────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if getattr(self, "watchlist_dock", None) is not None and self.watchlist_dock.isVisible():
                max_w = watchlist_max_width(self.width())
                if self.watchlist_dock.width() > max_w:
                    self._watchlist_width = clamp_watchlist_width(max_w, self.width())
                    self.resizeDocks(
                        [self.watchlist_dock], [self._watchlist_width], Qt.Orientation.Horizontal
                    )
        except Exception:
            pass

    def _on_watchlist_row_double_clicked(self, symbol: str):
        """D14: load the double-clicked symbol exactly like Load Chart."""
        connected = False
        try:
            connected = bool(self.ib_client.connected)
        except Exception:
            connected = False
        decision = should_load_on_double_click(
            getattr(self, "_current_symbol", ""), symbol, connected
        )
        if decision == "noop_disconnected":
            self.status_bar.showMessage("Disconnected — cannot load chart.", 3000)
            return
        if decision != "load":
            return
        self.symbol_input.setText((symbol or "").strip().upper())
        self.load_chart()

    # ── Extended Hours / Timezone slots ────────────────────────────────────────

    def _on_ext_hours_toggled(self, enabled: bool):
        """Reload chart with/without extended hours when toggled."""
        if self._current_symbol:
            self.status_bar.showMessage(
                f"Extended hours: {'ON' if enabled else 'OFF'} — reloading chart…", 3000
            )
            self.load_chart()

    def _on_tz_changed(self, label: str):
        """Change chart x-axis timezone."""
        if label == "Eastern Time":
            self._tz_offset = _eastern_offset()
        else:  # UTC
            self._tz_offset = 0
        self.chart_panel.set_timezone(self._tz_offset)
        self.status_bar.showMessage(f"Timezone: {label}", 3000)

    # ── DOM / Active Trader slots ────────────────────────────────────────────

    def _on_dom_toggled(self, enabled: bool):
        """Show/hide the Active Trader dock."""
        trader_dock = self.findChild(QDockWidget, "Active Trader")
        if trader_dock:
            trader_dock.setVisible(enabled)
        if enabled:
            self._subscribe_dom()
            self.status_bar.showMessage(
                f"DOM active for {self._current_symbol or '—'}", 4000
            )

    def _subscribe_dom(self):
        """Subscribe to Level I/II market depth for the current symbol."""
        if not self._current_symbol or self.depth_manager is None:
            return
        # Cancel any previous subscription
        self.depth_manager.cancel_all()
        contract = get_contract_for_symbol(self._current_symbol)
        self._depth_req_id = self.depth_manager.subscribe(
            self._current_symbol, contract, num_levels=10
        )
        self.active_trader.set_symbol(self._current_symbol)
        self.status_bar.showMessage(
            f"Subscribing to DOM for {self._current_symbol}…", 3000
        )

    def _on_mkt_depth(self, req_id: int, position: int, operation: int,
                      side: int, price: float, size: int):
        """Handle incoming market-depth updates."""
        symbol = self.depth_manager.on_update(req_id, position, operation, side, price, size)
        if symbol is None:
            return
        # Update last price for the ladder mid-row display
        if price > 0:
            self.active_trader.set_last_price(price)
        snapshot = self.depth_manager.snapshot(req_id)
        on_depth_callback(self.active_trader, snapshot)

    # ── Alarm overlay slots ───────────────────────────────────────────────────

    def _on_alarm_create_requested(self, price: float):
        if not self._current_symbol:
            return
        self.alarm_mode_btn.setChecked(False)
        dialog = AlarmDialog(self._current_symbol, price, self)
        dialog.alarms_changed.connect(self._reload_current_alarms)
        dialog.exec()
        self._reload_current_alarms()

    def _on_alarm_moved(self, alarm_id: int, price: float):
        AlarmStore.set_price(alarm_id, price)
        self._reload_current_alarms()

    def _on_alarm_mute_toggled(self, alarm_id: int, sound: bool):
        AlarmStore.set_sound(alarm_id, sound)
        self._reload_current_alarms()

    def _on_alarm_rearm_requested(self, alarm_id: int):
        AlarmStore.rearm(alarm_id)
        self._reload_current_alarms()

    def _on_alarm_delete_requested(self, alarm_id: int):
        AlarmStore.delete(alarm_id)
        self._reload_current_alarms()
        self.status_bar.showMessage("Alarm deleted.", 2000)

    # ── Order Entry ─────────────────────────────────────────────────

    def _on_order_place_requested(self, symbol: str, action: str, qty: float,
                                    order_type: str, lmt_price: float,
                                    stop_price: float, target_price: float):
        """Handle order placement request from ActiveTraderPanel."""
        contract = get_contract_for_symbol(symbol)
        self._place_order(contract, symbol, action, qty, order_type,
                           lmt_price, stop_price, target_price)

    def _place_order(self, contract, symbol, action, qty, order_type,
                      lmt_price, stop_price, target_price):
        """Build order(s) and place via the client."""
        pacing_manager.throttle_realtime()

        if order_type == "MKT":
            order = order_registry.market_order(action, qty)
            parent_id = id_manager.get_id()
            self.ib_client.placeOrder(parent_id, contract, order)
            user_order = order_registry.UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="MKT", transmit=True,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(parent_id, action, qty, "Submitted")

        elif order_type == "LMT":
            order = order_registry.limit_order(action, qty, lmt_price)
            parent_id = id_manager.get_id()
            self.ib_client.placeOrder(parent_id, contract, order)
            user_order = order_registry.UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="LMT", lmt_price=lmt_price,
                transmit=True,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(parent_id, action, qty, "Submitted")

        elif order_type == "STP":
            order = order_registry.stop_order(action, qty, stop_price)
            parent_id = id_manager.get_id()
            self.ib_client.placeOrder(parent_id, contract, order)
            user_order = order_registry.UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="STP", aux_price=stop_price,
                transmit=True,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(parent_id, action, qty, "Submitted")

        elif order_type == "BRACKET":
            parent_id = id_manager.get_id()
            parent, stop, target = order_registry.bracket_order(
                parent_id, action, qty, lmt_price, stop_price, target_price,
            )
            self.ib_client.placeOrder(parent_id, contract, parent)
            self.ib_client.placeOrder(parent_id + 1, contract, stop)
            self.ib_client.placeOrder(parent_id + 2, contract, target)
            user_order = order_registry.UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="LMT", lmt_price=lmt_price,
                parent_id=parent_id, oca_group=f"bracket-{parent_id}",
                transmit=False,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(
                parent_id, action, qty, "Bracket Submitted"
            )

    def _on_open_order(self, orderId: int, contract, order, orderState):
        self._update_order_status(orderId, getattr(orderState, "status", ""))

    def _on_exec_details(self, reqId: int, contract, execution):
        oid = getattr(execution, "orderId", None)
        if oid is not None:
            self._update_order_status(oid, "Filled")

    def _on_order_status(self, orderId: int, status: str, filled: float,
                           remaining: float, avgFillPrice: float,
                           permId: int, parentId: int, lastFillPrice: float,
                           clientId: int, whyHeld: str):
        self._update_order_status(orderId, status)

    def _on_account_summary(self, reqId: int, account: str, tag: str, value: str):
        """Collect account summary key/values."""
        summary = dict(getattr(self, "_account_summary", {}))
        summary[tag] = value
        self._account_summary = summary
        self.portfolio_panel.set_account_summary(summary)

    def _on_account_summary_end(self, reqId: int):
        """Finalize account summary once IBKR signals the end marker."""
        summary = getattr(self, "_account_summary", None)
        if summary is not None:
            self.portfolio_panel.set_account_summary(dict(summary))
            self.status_bar.showMessage(
                f"Account summary received for {self._current_symbol or '—'}", 4000
            )

    def _on_position_update(self, account: str, contract, pos: float, avg_cost: float):
        """Persist and render a single position update."""
        from ibkr.account import build_position_from_ib
        from data.db import db

        contract_type = getattr(contract, "class_", "stock") or "stock"
        multiplier = float(getattr(contract, "multiplier", 1.0) or 1.0)
        expiry = getattr(contract, "lastDateOrMonth", None)
        strike = getattr(contract, "strike", None)
        right = getattr(contract, "putCall", None)
        right = "P" if right == "P" else ("C" if right == "C" else None)

        position = build_position_from_ib(
            symbol=getattr(contract, "localSymbol", None) or getattr(contract, "symbol", ""),
            account=account,
            con_id=getattr(contract, "conId", None),
            contract_type=contract_type,
            local_symbol=getattr(contract, "localSymbol", ""),
            multiplier=multiplier,
            expiry=expiry,
            strike=strike,
            right=right,
            avg_cost=avg_cost,
            qty=pos,
        )
        position.market_price = self._last_chart_price or 0.0
        self._upsert_position(position)
        self.portfolio_panel.add_position(position)

    def _on_position_end(self):
        """Load the full persisted position set after IBKR finishes streaming."""
        from data.db import db

        rows = db.conn.execute(
            "SELECT symbol, account, con_id, contract_type, qty, avg_cost, "
            "local_symbol, multiplier, expiry, strike, right, stop_loss, "
            "take_profit, trade_group_id FROM positions"
        ).fetchall()
        positions = [Position(
            symbol=row[0], account=row[1], con_id=row[2],
            contract_type=row[3], qty=row[4], avg_cost=row[5],
            local_symbol=row[6], multiplier=row[7], expiry=row[8],
            strike=row[9], right=row[10], stop_loss=row[11],
            take_profit=row[12], trade_group_id=row[13],
        ) for row in rows]
        self.portfolio_panel.set_positions(positions)

    def _upsert_position(self, position: Position) -> None:
        """Persist a position update (upsert by symbol + con_id)."""
        from data.db import db

        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO positions
                (symbol, account, con_id, contract_type, qty, avg_cost,
                 local_symbol, multiplier, expiry, strike, right,
                 stop_loss, take_profit, trade_group_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, con_id) DO UPDATE SET
                account=excluded.account,
                contract_type=excluded.contract_type,
                qty=excluded.qty,
                avg_cost=excluded.avg_cost,
                local_symbol=excluded.local_symbol,
                multiplier=excluded.multiplier,
                expiry=excluded.expiry,
                strike=excluded.strike,
                right=excluded.right,
                stop_loss=excluded.stop_loss,
                take_profit=excluded.take_profit,
                trade_group_id=excluded.trade_group_id,
                updated_at=excluded.updated_at
            """,
            (
                position.symbol,
                position.account,
                position.con_id,
                position.contract_type,
                position.qty,
                position.avg_cost,
                position.local_symbol,
                position.multiplier,
                position.expiry,
                position.strike,
                position.right,
                position.stop_loss,
                position.take_profit,
                position.trade_group_id,
                int(__import__("time").time()),
            ),
        )
        db.conn.commit()

    def _update_order_status(self, orderId: int, status: str):
        order = order_registry.get(orderId)
        if order:
            order.status = status
            self.active_trader.set_order_status(
                orderId, order.action, order.total_qty, status
            )

    # ── Portfolio SL/TP and close handlers (Phase 7) ────────────────────────────

    def _on_portfolio_sltp_changed(self, position_id: int, stop_loss: float, take_profit: float) -> None:
        """Persist SL/TP to DB when dialog confirms for a single position."""
        from data.db import db

        cursor = db.conn.cursor()
        cursor.execute(
            "UPDATE positions SET stop_loss=?, take_profit=?, updated_at=? WHERE id=?",
            (stop_loss if stop_loss > 0 else None, take_profit if take_profit > 0 else None, int(__import__("time").time()), position_id),
        )
        db.conn.commit()
        self.status_bar.showMessage(f"SL/TP updated for position {position_id}", 3000)

    def _on_portfolio_group_sltp_changed(self, group_id: int, stop_loss: float, take_profit: float) -> None:
        """Persist SL/TP to DB when dialog confirms for a trade group."""
        from data.db import db

        cursor = db.conn.cursor()
        cursor.execute(
            "UPDATE trade_groups SET stop_loss=?, take_profit=? WHERE id=?",
            (stop_loss if stop_loss > 0 else None, take_profit if take_profit > 0 else None, group_id),
        )
        db.conn.commit()
        self.status_bar.showMessage(f"SL/TP updated for group {group_id}", 3000)

    def _on_portfolio_close_position(self, position_id: int) -> None:
        """Close a single position via offsetting market order."""
        self._close_position_by_id(position_id)

    def _on_portfolio_close_group(self, group_id: int) -> None:
        """Close all positions in a trade group."""
        from data.db import db

        # Get all positions in this group
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM positions WHERE trade_group_id=?", (group_id,))
        position_ids = [row[0] for row in cursor.fetchall()]
        for pos_id in position_ids:
            self._close_position_by_id(pos_id)

    def _on_portfolio_flatten_all(self) -> None:
        """Close all open positions (flatten portfolio)."""
        from data.db import db

        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM positions WHERE qty != 0")
        position_ids = [row[0] for row in cursor.fetchall()]
        for pos_id in position_ids:
            self._close_position_by_id(pos_id)

    def _close_position_by_id(self, position_id: int) -> None:
        """Place an offsetting market order to close a position by its DB ID."""
        from data.db import db
        from ibkr.contracts import get_contract_for_symbol
        from ibkr.id_manager import id_manager
        from ibkr.pacing import pacing_manager
        from ibkr.orders import orders as order_registry

        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT symbol, account, con_id, contract_type, qty, avg_cost, "
            "local_symbol, multiplier, expiry, strike, right FROM positions WHERE id=?",
            (position_id,),
        )
        row = cursor.fetchone()
        if not row:
            return

        symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier, expiry, strike, right = row
        if qty == 0:
            return

        # Build offsetting order
        action = "SELL" if qty > 0 else "BUY"
        close_qty = abs(qty)

        # Use the stored con_id if available for options/futures, else stock
        contract = get_contract_for_symbol(symbol)
        if con_id is not None:
            contract.conId = con_id
        if contract_type != "stock":
            contract.secType = contract_type.upper()
            if local_symbol:
                contract.localSymbol = local_symbol
            if expiry:
                contract.lastTradeDateOrContractMonth = expiry
            if strike is not None:
                contract.strike = strike
            if right:
                contract.right = right
            contract.multiplier = str(int(multiplier)) if multiplier != 1.0 else ""

        pacing_manager.throttle_realtime()
        order_id = id_manager.get_id()
        order = order_registry.market_order(action, close_qty)
        self.ib_client.placeOrder(order_id, contract, order)
        self.status_bar.showMessage(
            f"Closing position {position_id}: {action} {close_qty} {symbol} @ MKT", 4000
        )

    def closeEvent(self, event):
        # Persist watchlist dock width (D13)
        try:
            if getattr(self, "watchlist_dock", None) is not None:
                self._watchlist_width = save_watchlist_width(
                    self._settings, self.watchlist_dock.width(), self.width()
                )
        except Exception:
            pass
        # Cancel realtime bar subscription
        if self._rt_req_id is not None:
            self.rt_manager.unsubscribe(self._rt_req_id)
            self._rt_req_id = None
        # Cancel historical data request
        if self._current_req_id is not None:
            self.md_manager.cancel_historical_data(self._current_req_id)
            self._current_req_id = None
        # Cancel market depth subscription
        if self._depth_req_id is not None:
            self.depth_manager.cancel(self._depth_req_id)
            self._depth_req_id = None
        # Cancel all depth subscriptions
        self.depth_manager.cancel_all()
        # Cancel all realtime bar subscriptions across tracked symbols
        self.rt_manager.cancel_all()
        # Clear watchlist panel
        self.watchlist_panel.clear()
        # Disconnect from IBKR
        try:
            self.ib_client.disconnect()
        except Exception:
            pass
        event.accept()
