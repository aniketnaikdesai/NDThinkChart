import logging
import threading
import time
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
    QStatusBar, QDockWidget, QSplitter, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QEvent

from config import settings
from ibkr.client import IBApiClient, ConnectionState
from ibkr.market_data import MarketDataManager, TIMEFRAME_CONFIG
from ibkr.market_depth import MarketDepthManager
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.contracts import get_contract_for_symbol
from ibkr.utils import parse_ibkr_date
from ibkr.orders import orders as order_registry, UserOrder
from ibkr.validation import validate_order
from ibkr.id_manager import id_manager
from ibkr.pacing import pacing_manager
from ibkr.subscription_manager import (
    DEPTH,
    RT_BARS,
    SubscriptionManager,
)
from ibkr.stream_health import StreamHealth, StreamState
from ui.chart_panel import ChartPanel
from ui.candlestick_item import ChartMode
from ui.watchlist_panel import (
    WatchlistPanel,
    WATCHLIST_MIN_WIDTH,
    DEFAULT_WATCHLIST_WIDTH,
    WATCHLIST_WIDTH_KEY,
    load_watchlist_width,
    save_watchlist_width,
    clamp_watchlist_width,
    watchlist_max_width,
    should_load_on_double_click,
    normalise_symbol,
    symbol_in_list,
)
from ui.dock_layout import (
    CHART_MIN_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    right_dock_max_width,
    plan_dock_widths,
)
from ui.studies_dialog import StudiesDialog, DEFAULT_STUDIES
from ui.alarm_dialog import AlarmDialog
from ui.drawing_groups_dialog import DrawingGroupsDialog
from ui.visual_conventions import apply_toolbar_stylesheet, set_button_active
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
from services.backfill_service import find_missing_spans, plan_requests
from services.market_calendar import trading_days
from services.contract_lookup_service import ContractLookupService

_LOG = logging.getLogger(__name__)

# Default watchlist symbols — used only on first run before DB persistence
DEFAULT_WATCHLIST = ["AAPL", "TSLA", "SPY", "QQQ", "NVDA"]

#: QSettings sentinel (A52/DG44) marking the watchlist as configured. It is set
#: once the list has been persisted (seeded or explicitly saved) so that an
#: intentionally emptied watchlist is not re-seeded with ``DEFAULT_WATCHLIST``
#: on the next launch.
WATCHLIST_CONFIGURED_KEY = "watchlist/configured"

# Single source of truth for the toolbar content row height (px). The
# ToolbarScroll wrapper is sized as this content height PLUS the horizontal
# scrollbar's own height, so the scrollbar gets a reserved lane entirely below
# the content instead of overlapping the label descenders (D20).
TOOLBAR_CONTENT_HEIGHT = 36

#: D21.13 — baseline minimum width of the right region once BOTH of its panels
#: are collapsed to just their toggle buttons. The live value additionally
#: accounts for the two buttons' own ``sizeHint`` plus margins (see
#: ``MainWindow._compute_right_dock_collapsed_min_width``) but is always kept
#: below ``RIGHT_DOCK_MIN_WIDTH`` so the chart reclaims the vacated space.
RIGHT_DOCK_COLLAPSED_MIN_WIDTH = 150

#: Horizontal margins (px, per side) added to the collapsed region's buttons when
#: computing the collapsed minimum width (D21.13).
RIGHT_DOCK_COLLAPSED_MARGIN = 12

# D21.8 / AC-D21.8.2 — the status-bar hint shown while Alarm Mode is armed. It
# is shown with no timeout (persistent) so it stays visible until the mode ends,
# and is cleared/replaced on every exit path (button off, alarm placed, drawing
# tool selected, mode otherwise exited) so it never permanently masks a later
# status message. Single source of truth for the text (also imported by tests).
ALARM_MODE_STATUS_MESSAGE = "Alarm mode: click the chart to place a price alarm."


def conn_badge_text(account_id: str | None, account_type: str | None) -> tuple[str, str]:
    """D26.5: derive the connection badge from the verified port + account.

    The port is fail-fast verified at startup (settings.check_live_port), so
    reaching this point means the live port — but the account itself may still
    be paper/demo (IBKR paper accounts carry DU-prefixed IDs). Returns
    (text, stylesheet-color); never a hardcoded claim.
    """
    acct_id = (account_id or "").upper()
    acct_type = (account_type or "").upper()
    if acct_id.startswith("DU") or "DEMO" in acct_type or "PAPER" in acct_type:
        return "● Paper", "#fbbf24"
    return "● Live", "#34d399"


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
        toolbar.setObjectName("MainToolbar")
        toolbar.setFixedHeight(TOOLBAR_CONTENT_HEIGHT)
        # The base look is scoped with the #MainToolbar selector so it composes
        # with the VIS-D21.2 shared stylesheet below into one parseable sheet
        # (a bare declaration list fails to parse once further rules are added).
        toolbar.setStyleSheet(
            "#MainToolbar { background: #101218; border-bottom: 1px solid #232938; }"
        )
        # D21.7 / VIS-D21.2: give active/selected toolbar buttons a persistent,
        # clearly visible highlight. The shared stylesheet is objectName-keyed
        # (#MainToolbar) and covers both the checkable toggles (:checked) and the
        # popup buttons driven by set_button_active ([active="true"]), so it keeps
        # working at any scroll position inside the D19 ToolbarScroll wrapper.
        apply_toolbar_stylesheet(toolbar)
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

        # Extended Hours toggle. D21.3: the label reflects the state — "Ext Hours"
        # when ON (extended/pre/post-market) and "RTH" when OFF (regular trading
        # hours). The 80px fixed width fits both labels.
        self.ext_hours_btn = QPushButton("Ext Hours")
        self.ext_hours_btn.setCheckable(True)
        self.ext_hours_btn.setChecked(True)  # Default to extended hours
        self.ext_hours_btn.setToolTip("Include pre/post-market data")
        self.ext_hours_btn.setFixedWidth(80)
        self.ext_hours_btn.setText(
            self._ext_hours_label(self.ext_hours_btn.isChecked())
        )
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
        # D27.4: persistent (non-transient) RT stream-health indicator.
        self.stream_badge = QLabel("○ Stream")
        self.stream_badge.setStyleSheet("color: #9ca3af;")

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
        # D26.8: kill switch — panic control, red, immediate (no confirm).
        self.kill_btn = QPushButton("Kill Switch")
        self.kill_btn.setObjectName("KillSwitchButton")
        self.kill_btn.setToolTip(
            "Cancel ALL open orders immediately "
            "(reqGlobalCancel + per-order cancel)."
        )
        self.kill_btn.setStyleSheet(
            "background-color: #b91c1c; color: white; font-weight: bold;")
        self.kill_btn.clicked.connect(self._on_kill_switch_clicked)
        tb_layout.addWidget(QLabel("|"))
        tb_layout.addWidget(self.kill_btn)
        tb_layout.addStretch()
        tb_layout.addWidget(self.stream_badge)
        tb_layout.addWidget(self.conn_badge)

        # ── Central chart area ────────────────────────────────────────────────
        # Dynamic Eastern offset (DST-aware): EDT=14400, EST=18000
        self._tz_offset = _eastern_offset()
        self.chart_panel = ChartPanel(tz_offset=self._tz_offset)
        # D19 Phase 1: keep the toolbar inside the central widget but stop its
        # ~1716px minimumSizeHint from pinning the central widget. A frameless
        # horizontal QScrollArea holds the full-natural-width toolbar so it stays
        # a single row and scrolls horizontally when the window is too narrow to
        # show every control at once. Its height is DERIVED (D20): the 36px
        # content row plus the horizontal scrollbar's own height, so the
        # scrollbar gets a reserved lane below the content and never covers the
        # label descenders.
        toolbar_scroll = QScrollArea()
        toolbar_scroll.setObjectName("ToolbarScroll")
        toolbar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        toolbar_scroll.setWidgetResizable(False)
        toolbar_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        toolbar_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        toolbar_scroll.setFixedHeight(
            TOOLBAR_CONTENT_HEIGHT
            + toolbar_scroll.horizontalScrollBar().sizeHint().height()
        )
        toolbar_scroll.setWidget(toolbar)

        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(toolbar_scroll)
        vbox.addWidget(self.chart_panel)
        self.setCentralWidget(central)

        # ── Watchlist dock ────────────────────────────────────────────────────
        # D21.11: exactly one "Watchlist" label. The duplicate ``QDockWidget``
        # title is deleted (empty window title) and the in-panel header strip —
        # whose label is a ``DiagonalStrikeButton`` — becomes the dock's
        # title-bar widget via ``setTitleBarWidget``. Because the header strip is
        # the title bar, it survives the body collapsing; Qt forwards title-bar
        # events so dock drag/float is preserved.
        self.watchlist_panel = WatchlistPanel()
        self.watchlist_dock = QDockWidget(self)
        self.watchlist_dock.setObjectName("Watchlist")
        self.watchlist_dock.setWindowTitle("")
        self.watchlist_dock.setWidget(self.watchlist_panel)
        self.watchlist_dock.setTitleBarWidget(self.watchlist_panel.header_bar)
        self.watchlist_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.watchlist_panel.setMinimumWidth(WATCHLIST_MIN_WIDTH)
        # D22 Phase 4: the add affordance is gated on a live IBKR connection.
        # Starts disconnected, so the '+' button / "Add symbol…" action are
        # disabled until ``_on_connected`` flips them on.
        self._ibkr_connected = False
        self.watchlist_panel.set_add_enabled(False)
        # D22-08: in-flight add requests, keyed by the ContractLookupService
        # reqId. ``ContractLookupService`` drops its own pending entry before it
        # emits, and cancels silently on a disconnect, so the window keeps this
        # map to correlate a resolution *and* to reject a mid-flight add on a
        # transport drop (AC-D22.8.4).
        self._pending_watchlist_add: dict[int, str] = {}
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.watchlist_dock)
        # D17 Phase 2: live clamp plumbing. ``_apply_dock_widths`` is the single
        # shared entry point that reads the *chart area* (central widget width)
        # and re-clamps the watchlist width; it is driven by the dock-area
        # splitter hook (or the event-filter fallback), the two-directional
        # ``resizeEvent`` and the deferred normalize. See ``_apply_dock_widths``.
        self._settings = QSettings("NDThinkChart", "NDThinkChart")
        self._applying_dock_widths = False       # re-entrancy guard
        self._dock_clamp_scheduled = False       # deferred clamp coalescing
        self._dock_splitter = None               # acquired defensively after show
        # Restore persisted width (clamped for the current chart area). During
        # construction the central widget is not yet laid out, so this is a
        # provisional clamp; the *raw persisted request* is remembered and
        # re-applied by ``_deferred_dock_setup`` once the real chart area exists
        # (AC-D17.4: restore as the persisted value clamped to the current cap).
        self._persisted_watchlist_width = self._read_persisted_width()
        self._watchlist_width = load_watchlist_width(
            self._settings, self._chart_area_width()
        )
        self.resizeDocks([self.watchlist_dock], [self._watchlist_width], Qt.Orientation.Horizontal)
        # D17 Phase 2: enforce the cap *during* the drag. The dock-area's
        # internal QSplitter is not reachable through PyQt6's public API, so the
        # event-filter fallback (per the architecture risk row) is installed on
        # the dock; a deferred attempt to acquire the real splitter runs after
        # show() and, if successful, connects its ``splitterMoved`` signal.
        self.watchlist_dock.installEventFilter(self)
        QTimer.singleShot(0, self._deferred_dock_setup)
        # D14: double-click a row loads the chart
        self.watchlist_panel.row_double_clicked.connect(self._on_watchlist_row_double_clicked)
        # D22 Phase 4: the panel's add/remove intents are decided by the window
        # (gate -> duplicate guard -> bounded live lookup on add; subscription
        # cancel + persist on remove).
        self.watchlist_panel.symbol_add_requested.connect(
            self._on_watchlist_symbol_add_requested
        )
        self.watchlist_panel.symbol_remove_requested.connect(
            self._on_watchlist_symbol_remove_requested
        )

        # ── Single right dock region (D18 Phase 3) ────────────────────────
        # Active Trader and Portfolio used to be two separate RightDockWidgetArea
        # docks; they are now stacked sections of ONE region so they share the
        # region's width by construction (AC-D18.3). The region keeps the
        # "Active Trader" title + objectName so ``_on_dom_toggled``'s
        # ``findChild(QDockWidget, "Active Trader")`` still resolves it. The
        # ladder/portfolio panels and all their signal wiring are unchanged —
        # only the container around them. No width cap is added here (T49).
        self.active_trader = ActiveTraderPanel()
        self.portfolio_panel = ActivePortfolioPanel()
        self.right_dock_container = QWidget()
        self.right_dock_container.setObjectName("RightDockContainer")
        right_layout = QVBoxLayout(self.right_dock_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        # Stretch 1 each while both are shown; ``_sync_right_dock_collapse``
        # re-balances them so a shown panel absorbs the space a hidden one vacates
        # (AC-D21.13.2).
        right_layout.addWidget(self.active_trader, 1)
        right_layout.addWidget(self.portfolio_panel, 1)
        self._right_dock_layout = right_layout

        self.right_dock = QDockWidget("Active Trader", self)
        self.right_dock.setObjectName("Active Trader")
        self.right_dock.setWidget(self.right_dock_container)
        # D21.13: the dock's title bar IS the Active Trader panel's header strip,
        # whose label is a ``DiagonalStrikeButton``. Setting a title-bar widget
        # hides the native dock title (the ``windowTitle`` is kept for
        # windowTitle-keyed lookups elsewhere) so exactly one "Active Trader"
        # label is visible and it is the hide/show toggle (AC-D21.13.1).
        self.right_dock.setTitleBarWidget(self.active_trader.header_bar)
        self.right_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        # D18 Phase 4: pin the single region's minimum to the shared constant so
        # ``_apply_dock_widths`` can shrink it exactly to RIGHT_DOCK_MIN_WIDTH
        # and the panels' bounded content cannot raise it (AC-D18.4/AC-D18.6).
        self.right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        # D18 Phase 4: in-memory-only right-region width. Never persisted — no new
        # QSettings key (AC-D18.7 / A36), matching D10's volume-toggle precedent.
        self._right_dock_width = RIGHT_DOCK_MIN_WIDTH
        # D21.13: per-panel hide/show state. Both panels start shown; when BOTH
        # are collapsed the whole region collapses to a two-button strip and is
        # treated as hidden by the cross-clamp (AC-D21.13.3).
        self._right_region_collapsed = False
        self._right_dock_collapsed_min_width = (
            self._compute_right_dock_collapsed_min_width()
        )
        self.active_trader.header_button.toggled.connect(
            self._on_right_panel_toggled
        )
        self.portfolio_panel.summary_label.toggled.connect(
            self._on_right_panel_toggled
        )
        # The right region participates in the shared clamp via resizeEvent and a
        # second event filter (the watchlist filter above is D17-only).
        self.right_dock.installEventFilter(self)
        # Hide/show re-applies the clamp: with the region hidden the watchlist
        # regains its own cap (D17 behaviour restored); with it shown the B3
        # cross-clamp governs again. This is what keeps D17's watchlist-cap
        # assertions true whenever the right region is not participating.
        self.right_dock.visibilityChanged.connect(
            self._on_right_dock_visibility_changed
        )

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

        # D22 Phase 4: bounded, exactly-once contract-details lookup correlation.
        # The service owns the pending-request map and emits ``lookup_finished``
        # once per add request; the window's validation-result slot (completed in
        # D22-08) consumes it. It is cancelled on disconnect so no stale result
        # can resolve an add after a transport drop.
        self._contract_lookup = ContractLookupService(
            self.md_manager, self.ib_client.bridge
        )
        self._contract_lookup.lookup_finished.connect(
            self._on_contract_lookup_finished
        )

        # Inject md_manager into watchlist
        self.watchlist_panel.set_market_data_manager(self.md_manager)
        # D27.3: the panel type-tags its live subs for the reconnect replay.
        self.watchlist_panel.set_subscription_manager(self.sub_manager)
        self.watchlist_panel.set_depth_manager(self.depth_manager)

        # Drawing overlay wiring
        self.chart_panel.drawing_overlay.created.connect(self._on_drawing_created)
        self.chart_panel.drawing_overlay.updated.connect(self._on_drawing_updated)
        self.chart_panel.drawing_overlay.deleted.connect(self._on_drawing_deleted)
        self.chart_panel.drawing_overlay.selection_changed.connect(self._on_drawing_selection_changed)
        # ESC-017: when the router clears the drawing tool (TR-4 zoom-cancels-draw,
        # TR-17 symbol change) the overlay emits mode_changed("cursor"); mirror it
        # back into the toolbar combo so it never goes stale.
        self.chart_panel.drawing_overlay.mode_changed.connect(
            self._on_drawing_tool_mode_changed
        )

        # AC-D3.9: the magnifier is refused while alarm placement is armed.
        self.chart_panel.zoom_refused.connect(
            lambda: self.status_bar.showMessage(
                "Finish or cancel alarm placement before zooming", 4000
            )
        )

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
        # D16 correlated backfill wave: the reqIds of the in-flight historical
        # request set, the generation token they belong to, the spans that wave
        # is expected to fill, and the reqIds that errored mid-wave.
        self._history_req_ids: set[int] = set()
        self._history_req_generation: dict[int, int] = {}
        self._history_generation: int = 0
        # ESC-024: bounded watchdog for a wave that never yields an end marker,
        # and a one-shot guard so a stranded finalise is never repeated.
        self._history_wave_timeout_ms: int = 30_000
        self._history_wave_timer = QTimer(self)
        self._history_wave_timer.setSingleShot(True)
        self._history_wave_timer.timeout.connect(self._on_history_wave_timeout)
        self._backfill_missing_spans: list = []
        self._backfill_failed_req_ids: set[int] = set()
        self._current_studies: list[dict] = deepcopy(DEFAULT_STUDIES)
        self._current_alarms = []
        self._last_chart_price: float | None = None
        # D27.1: True once any realtime bar has been observed since the last
        # load_chart. Guards _finalize_history_wave against rewinding
        # _last_chart_price to the older historical close (phantom alarms).
        self._rt_seen: bool = False
        # D27.4: health of the chart's live RT subscription. Owned here in
        # Phase 2; migrates into TickerSession in Phase 3b (no window refs).
        self._stream_health = StreamHealth()
        self._rt_retry_timer = QTimer(self)
        self._rt_retry_timer.setSingleShot(True)
        self._rt_retry_timer.timeout.connect(self._retry_rt_subscribe)
        self._active_draw_group_id: int | None = None
        self._pending_brackets: dict[int, tuple[str, float]] = {}  # parent_id -> (action, qty)

        # Start connection
        self.ib_client.connect(settings.IBKR_HOST, settings.IBKR_PORT, settings.IBKR_CLIENT_ID)
        threading.Thread(target=self.ib_client.run, daemon=True, name="ibkr-reader").start()

    # ── Connection slots ──────────────────────────────────────────────────────

    def _update_conn_badge(self):
        """D26.5: badge text/color derive from the verified port + account."""
        summary = getattr(self, "_account_summary", {}) or {}
        text, color = conn_badge_text(
            getattr(self, "_account_id", None),
            summary.get("AccountType"),
        )
        self.conn_badge.setText(text)
        self.conn_badge.setStyleSheet(f"color: {color};")

    def _on_connected(self):
        self._ibkr_connected = True
        self.watchlist_panel.set_add_enabled(True)
        self._update_conn_badge()
        self.load_btn.setEnabled(True)
        self.status_bar.showMessage(f"Connected — IBKR port {settings.IBKR_PORT}")
        self._restore_watchlist()
        self._replay_subscriptions()

    def _restore_watchlist(self):
        """Repopulate the panel from the DB, idempotently (AC-D22.7.2).

        Runs on every connect — the initial one and each reconnect. It clears the
        panel first so a repeat run reproduces exactly the persisted set with no
        duplicate rows.

        ``DEFAULT_WATCHLIST`` is seeded only on a genuine first run: the DB list
        is empty *and* the ``watchlist/configured`` sentinel is unset (A52/DG44).
        An explicitly emptied list (sentinel set) stays empty. A non-empty list
        is authoritative and sets the sentinel so it is never re-seeded later.
        """
        self.watchlist_panel.clear()
        saved = db.get_watchlist()
        symbols = [sym for sym, _cat in saved] if saved else []
        if symbols:
            self._settings.setValue(WATCHLIST_CONFIGURED_KEY, True)
        elif not self._settings.value(
            WATCHLIST_CONFIGURED_KEY, False, type=bool
        ):
            symbols = list(DEFAULT_WATCHLIST)
            db.set_watchlist(symbols)
            self._settings.setValue(WATCHLIST_CONFIGURED_KEY, True)
        for sym in symbols:
            self.watchlist_panel.add_symbol(sym, get_contract_for_symbol(sym))

    def _on_contract_lookup_finished(
        self, request_id: int, symbol: str, ok: bool, reason: str
    ) -> None:
        """Validation-result slot for a bounded contract-details lookup.

        D22 Phase 4 constructs and wires the ``ContractLookupService`` and routes
        its ``lookup_finished`` signal here. The signal is routed to the add-flow
        decision (:meth:`_on_watchlist_symbol_validated`), which applies the
        exactly-once result: add on ``ok`` while still connected, error otherwise.
        """
        self._on_watchlist_symbol_validated(request_id, symbol, ok, reason)

    # ── Add / remove flow (D22 Phase 4) ───────────────────────────────────────

    def _on_watchlist_symbol_add_requested(self, symbol: str) -> None:
        """Handle an "add symbol" intent (AC-D22.8.1 .. AC-D22.8.3).

        Order of refusal: blank input, then a disconnected window
        (AC-D22.5 gate), then a case-insensitive duplicate of the persisted
        watchlist (AC-D22.3). Only a non-empty, non-duplicate symbol while
        connected proceeds to a bounded ``ContractLookupService`` request; the
        row/subscription/persistence happens only once that lookup resolves
        ``ok=True`` (see :meth:`_on_watchlist_symbol_validated`).
        """
        sym = normalise_symbol(symbol)
        if not sym:
            self.status_bar.showMessage("Enter a symbol to add.", 3000)
            return
        if not self._ibkr_connected:
            self.status_bar.showMessage(
                "Not connected to IBKR — cannot add symbols.", 3000
            )
            return
        saved = db.get_watchlist()
        if symbol_in_list(sym, [s for s, _cat in saved]):
            self.status_bar.showMessage(
                f"{sym} is already in the watchlist.", 3000
            )
            return
        req_id = self._contract_lookup.request(sym, get_contract_for_symbol(sym))
        self._pending_watchlist_add[req_id] = sym
        self.status_bar.showMessage(f"Validating {sym}…", 3000)

    def _on_watchlist_symbol_validated(
        self, request_id: int, symbol: str, ok: bool, reason: str
    ) -> None:
        """Apply a resolved contract lookup (AC-D22.8.3 / AC-D22.8.4).

        The pending entry is dropped first, so a duplicate/late result for the
        same reqId is a no-op. ``ok=False`` (no contract / IBKR error / timeout)
        or a disconnected window (a drop mid-flight) surfaces an error and adds,
        subscribes and persists **nothing**. ``ok=True`` while connected adds the
        row (which issues ``req_mkt_data``), persists it and sets the configured
        sentinel so the emptied/added list is never re-seeded.
        """
        sym = self._pending_watchlist_add.pop(request_id, None)
        if sym is None:
            return  # late / unknown / already-rejected lookup — never mutate state
        if not ok:
            self.status_bar.showMessage(
                f"Could not add {sym}: {reason or 'contract not found'}", 5000
            )
            return
        if not self._ibkr_connected:
            self.status_bar.showMessage(
                f"Could not add {sym}: disconnected.", 5000
            )
            return
        self.watchlist_panel.add_symbol(sym, get_contract_for_symbol(sym))
        db.add_watchlist_symbol(sym)
        self._settings.setValue(WATCHLIST_CONFIGURED_KEY, True)
        self.status_bar.showMessage(f"Added {sym}.", 3000)

    def _on_watchlist_symbol_remove_requested(self, symbol: str) -> None:
        """Handle a "remove symbol" intent (AC-D22.8.5).

        Removal is allowed regardless of connection state: the panel drops the
        row and cancels that row's market-data subscription, the DB removal is
        persisted (renumbering survivors), and the configured sentinel is set so
        an emptied list stays empty on the next restore.
        """
        sym = normalise_symbol(symbol)
        if not sym:
            return
        self.watchlist_panel.remove_symbol(sym)
        db.remove_watchlist_symbol(sym)
        self._settings.setValue(WATCHLIST_CONFIGURED_KEY, True)
        self.status_bar.showMessage(f"Removed {sym}.", 3000)

    def _reject_pending_watchlist_adds(self) -> bool:
        """Reject every in-flight add after a transport drop (AC-D22.8.4).

        ``ContractLookupService.cancel_all`` drops its pending requests without
        emitting, so the window's own pending map is what lets the drop be
        surfaced. Clearing it means a late ``lookup_finished`` for a pre-drop
        reqId can neither add nor persist anything. Returns True when at least
        one add was rejected.
        """
        if not self._pending_watchlist_add:
            return False
        symbols = sorted(set(self._pending_watchlist_add.values()))
        self._pending_watchlist_add.clear()
        self.status_bar.showMessage(
            "Connection lost — add cancelled for "
            f"{', '.join(symbols)}. Nothing was added.",
            5000,
        )
        return True

    def _rebind_rt_req_id(self, new_req_id: int) -> None:
        """D27.3: point RT-bar routing at the replayed subscription's reqId."""
        self._rt_req_id = new_req_id

    def _rebind_depth_req_id(self, new_req_id: int) -> None:
        """D27.3: point DOM routing at the replayed subscription's reqId."""
        self._depth_req_id = new_req_id

    def _replay_subscriptions(self):
        """Re-issue live subscriptions after reconnection (D27.3).

        Chart RT bars and DOM depth replay through the subscription
        registry, which rebinds the new reqIds into the routing state.
        Watchlist market-data is re-issued by ``_restore_watchlist``'s
        clear+re-add path (pinned by AC-D22.7.2), so it is excluded here —
        replaying it too would double-subscribe every row.
        """
        self.sub_manager.replay_all(include_types={RT_BARS, DEPTH})

    # ── Stream health (D27.4) ───────────────────────────────────────────────

    def _update_stream_badge(self) -> None:
        """Refresh the persistent stream-health indicator (D27.4)."""
        h = self._stream_health
        if h.state == StreamState.LIVE:
            text, color = "● Stream live", "#34d399"
        elif h.state == StreamState.FAILED:
            code = f" [{h.fail_code}]" if h.fail_code is not None else ""
            text, color = f"● Stream failed{code}", "#f87171"
        else:
            text, color = "○ Stream awaiting first bar", "#fbbf24"
        self.stream_badge.setText(text)
        self.stream_badge.setStyleSheet(f"color: {color};")

    def _on_rt_stream_error(self, code: int, message: str) -> None:
        """D27.4: the live RT subscription failed — persist + backoff retry."""
        self._stream_health.mark_failed(code, message)
        self._update_stream_badge()
        _LOG.warning("Realtime stream failed [%s]: %s", code, message)
        self.status_bar.showMessage(
            f"Realtime stream failed [{code}]: {message} — retrying…",
            15000,
        )
        self._schedule_rt_retry()

    def _schedule_rt_retry(self) -> None:
        """D27.4: schedule a backoff retry of the failed RT subscription."""
        delay_s = self._stream_health.next_retry_delay_s()
        self._rt_retry_timer.start(int(delay_s * 1000))

    def _retry_rt_subscribe(self) -> None:
        """D27.4: re-issue the RT subscription after a backoff delay.

        No-op unless the failure is still current: a new load or a live bar
        since scheduling moves the state off FAILED, which disarms this.
        """
        if self._stream_health.state != StreamState.FAILED:
            return
        if not self._ibkr_connected or not self._current_symbol:
            # Still disconnected (or no symbol): keep backing off.
            self._schedule_rt_retry()
            return
        symbol = self._current_symbol
        contract = get_contract_for_symbol(symbol)
        if self._rt_req_id is not None:
            self.sub_manager.unsubscribe(self._rt_req_id)
        self._rt_req_id = self.rt_manager.subscribe(symbol, contract)
        self.sub_manager.subscribe(
            symbol,
            self._rt_req_id,
            RT_BARS,
            reissue=lambda s=symbol, c=contract: self.rt_manager.subscribe(s, c),
            rebind=self._rebind_rt_req_id,
        )
        self._stream_health.mark_subscribed()
        self._update_stream_badge()
        self.status_bar.showMessage(
            f"{symbol} — realtime stream re-subscribed, awaiting first bar…",
            8000,
        )

    def _on_disconnected(self):
        self._ibkr_connected = False
        self.watchlist_panel.set_add_enabled(False)
        # D22 Phase 4: a transport drop invalidates every in-flight contract
        # lookup so none can resolve an add once (re)connected.
        self._contract_lookup.cancel_all()
        self.conn_badge.setText("● Disconnected")
        self.conn_badge.setStyleSheet("color: #f87171;")
        self.load_btn.setEnabled(False)
        # D16 / ESC-024: a transport drop must not strand an in-flight backfill
        # wave. Cancel every tracked reqId, advance the generation so late
        # responses are rejected, and finalise once so AC-D16.4's shortfall is
        # surfaced rather than leaving a silent hole. With no wave in flight this
        # is a no-op (no second finalise, no exception).
        # The stranded-wave path writes the AC-D16.4 shortfall message; only fall
        # back to the generic disconnected message when there was no wave.
        if not self._finalize_stranded_history_wave(reason="Disconnected from IBKR"):
            self.status_bar.showMessage("Disconnected from IBKR")
        # D22-08: an add that was mid-flight can never complete now — surface the
        # rejection last so it is the visible cue (AC-D22.8.4). Nothing is added,
        # subscribed or persisted.
        self._reject_pending_watchlist_adds()

    def _finalize_stranded_history_wave(self, reason: str = "") -> bool:
        """Drop and finalise an in-flight backfill wave that can no longer complete.

        Used by ``_on_disconnected`` and the wave watchdog. Returns True when a
        wave was actually stranded and finalised, False when there was nothing to
        do — so callers never run ``_finalize_history_wave`` twice and never
        fabricate a bar. Cancels every tracked reqId, advances the generation so
        late responses for pre-drop reqIds are rejected by
        ``_history_event_accepted``, then finalises exactly once through
        ``_finalize_history_wave`` so AC-D16.4's shortfall is surfaced.
        """
        if not self._history_req_ids:
            return False
        self._cancel_history_requests()
        # Advance the generation: any late historical_bar / historical_data_end
        # for a pre-drop reqId now fails _history_event_accepted and can neither
        # accumulate bars nor finalise the wave a second time.
        self._history_generation += 1
        # Make the cause live for the shortfall diagnostics. Held on the instance
        # (rather than passed as an argument) so ``_finalize_history_wave`` keeps
        # its zero-argument contract for normal-path callers and spies; the real
        # finaliser reads and clears it. Empty for a normal finalise.
        self._history_stranded_reason = reason
        self._finalize_history_wave()
        return True

    def _on_history_wave_timeout(self):
        """Watchdog: a wave that never yields historical_data_end is bounded.

        ESC-024: a request that never ends must not strand the wave forever. The
        stalled wave is finalised through the same path as a disconnect (cancel
        remaining reqIds, advance the generation, surface the shortfall once).
        """
        # Finalising through the shared stranded-wave path already surfaces the
        # AC-D16.4 shortfall; leave that message in place (it is the meaningful
        # signal) rather than overwriting it with a generic timeout notice.
        self._finalize_stranded_history_wave(reason="Historical backfill timed out")

    def _arm_history_wave_watchdog(self):
        """(Re)start the bounded timeout for the current backfill wave."""
        timer = getattr(self, "_history_wave_timer", None)
        if timer is not None:
            timer.stop()
            timer.start(self._history_wave_timeout_ms)

    def _disarm_history_wave_watchdog(self):
        timer = getattr(self, "_history_wave_timer", None)
        if timer is not None:
            timer.stop()

    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        # D16: a failure on a backfill member must not strand the wave. Drop the
        # reqId (so the set can still empty and finalise) and remember it so the
        # shortfall is correlated at finalisation. No bar is fabricated.
        if reqId in self._history_req_ids:
            self._history_req_ids.discard(reqId)
            self._backfill_failed_req_ids.add(reqId)
            _LOG.warning(
                "Historical request %s failed [%s]: %s",
                reqId, errorCode, errorString,
            )
            self.status_bar.showMessage(
                f"Error [{errorCode}]: {errorString}", 8000
            )
            if not self._history_req_ids:
                self._finalize_history_wave()
            return
        # D27.4: an error on the live RT subscription marks the stream failed
        # (persistent indicator + backoff retry), not a transient toast.
        if self._rt_req_id is not None and reqId == self._rt_req_id:
            self._on_rt_stream_error(errorCode, errorString)
            return
        # D26.9: TWS reports order errors with the orderId in the reqId field.
        # Route them to the order registry so the ticket reflects reality
        # instead of reading "Submitted" forever.
        if order_registry.get(reqId) is not None:
            self._on_order_error(reqId, errorCode, errorString)
            return
        self.status_bar.showMessage(f"Error [{errorCode}]: {errorString}", 8000)

    def _on_order_error(self, order_id: int, error_code: int, error_string: str):
        """D26.9: surface a TWS order error on the registry and the ticket."""
        if error_code in (201, 103):
            status = "Rejected"
        elif error_code == 202:
            status = "Cancelled"
        else:
            status = f"Error {error_code}"
        order_registry.update_status(order_id, status)
        order = order_registry.get(order_id)
        action = getattr(order, "action", "?")
        qty = getattr(order, "total_qty", 0)
        ticket_text = f"{status}: {error_string}"
        self.active_trader.set_order_status(order_id, action, qty, ticket_text)
        self.status_bar.showMessage(
            f"Order #{order_id} {status}: {error_string}", 12000)

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
            self.sub_manager.unsubscribe(self._rt_req_id)
            self._rt_req_id = None

        self._current_symbol = symbol
        self._current_tf = timeframe
        self._current_req_id = None
        self._pending_bars = []

        # D16: cancel any in-flight backfill wave from the previous load and
        # advance the generation so its late responses cannot mix series.
        self._disarm_history_wave_watchdog()
        self._cancel_history_requests()
        self._history_generation += 1
        self._backfill_failed_req_ids = set()
        self._backfill_missing_spans = []

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
        self._rt_seen = False  # D27.1: new load, no live bar observed yet

        # Step 1: Show cached bars immediately
        cached = BarCache.get_bars(symbol, timeframe)
        self._last_chart_price = cached[-1].close if cached else None
        if cached:
            self.chart_panel.update_chart(cached)
            self.status_bar.showMessage(
                f"{symbol} — {len(cached)} cached bars. Fetching delta…"
            )

        # Step 2: Plan the backfill. The pure planner (services.backfill_service)
        # decides which trading sessions are missing and how to chunk them; the
        # window only issues one historical request per plan and correlates the
        # returned reqIds. market_data.py's signature is unchanged — each chunk
        # rides the existing endDateTime parameter.
        now_ts = self._now_ts()
        cached_ts = [b.ts for b in cached]
        missing_spans = (
            find_missing_spans(cached_ts, now_ts, timeframe) if cached else []
        )
        plans = plan_requests(missing_spans, timeframe)
        self._backfill_missing_spans = list(missing_spans)

        contract = get_contract_for_symbol(symbol)
        ext_hours = self.ext_hours_btn.isChecked()

        if plans:
            # One request per planned chunk, newest-first (the planner's order).
            for plan in plans:
                req_id = self.md_manager.req_historical_data(
                    contract=contract,
                    timeframe=timeframe,
                    endDateTime=plan.endDateTime,
                    whatToShow="TRADES",
                    useRTH=1,
                    extended_hours=ext_hours,
                )
                self._register_history_request(req_id)
            self.status_bar.showMessage(
                f"{symbol} — backfilling {len(plans)} historical chunk(s)…"
            )
        elif not cached:
            # Empty cache: preserve the configured-window single-request path
            # (endDateTime="" = up to now) as a backfill set of one.
            req_id = self.md_manager.req_historical_data(
                contract=contract,
                timeframe=timeframe,
                endDateTime="",
                whatToShow="TRADES",
                useRTH=1,
                extended_hours=ext_hours,
            )
            self._register_history_request(req_id)
            self.status_bar.showMessage(
                f"Requesting {symbol} [{timeframe}]… (hist reqId {req_id})"
            )
        else:
            # The cache already reaches now: no redundant request is issued.
            self.status_bar.showMessage(
                f"{symbol} — {len(cached)} cached bars. Cache current."
            )

        # ESC-024: bound the wave — a request that never yields an end marker
        # must not strand the chart indefinitely.
        if self._history_req_ids:
            self._arm_history_wave_watchdog()

        # Step 3: Start real-time bar stream
        # D27.3: register the live subscription (type-tagged) so the
        # reconnect replay can re-issue it and rebind the reqId.
        self._rt_req_id = self.rt_manager.subscribe(symbol, contract)
        self.sub_manager.subscribe(
            symbol,
            self._rt_req_id,
            RT_BARS,
            reissue=lambda s=symbol, c=contract: self.rt_manager.subscribe(s, c),
            rebind=self._rebind_rt_req_id,
        )
        # D27.4: new subscription -> awaiting first bar; disarm any retry
        # timer left over from a previous load/failure.
        self._rt_retry_timer.stop()
        self._stream_health.mark_subscribed()
        self._update_stream_badge()

        # DOM subscription (only if DOM panel is visible)
        if self.dom_btn.isChecked():
            self._subscribe_dom()

    def _now_ts(self) -> int:
        """Wall-clock epoch seconds; a seam for deterministic load-path tests."""
        return int(time.time())

    def _register_history_request(self, req_id: int) -> None:
        """Track one in-flight backfill request against the current generation."""
        self._history_req_ids.add(req_id)
        self._history_req_generation[req_id] = self._history_generation
        self._current_req_id = req_id

    def _cancel_history_requests(self) -> list[int]:
        """Cancel every tracked backfill request and drop the wave state.

        Returns the ids that were cancelled so callers/tests can assert the
        exact set. The generation token is *not* advanced here; callers advance
        it when they invalidate the wave (symbol/timeframe switch, close).
        """
        req_ids = list(self._history_req_ids)
        for req_id in req_ids:
            try:
                self.md_manager.cancel_historical_data(req_id)
            except Exception:
                pass
        self._history_req_ids.clear()
        self._history_req_generation.clear()
        self._pending_bars = []
        return req_ids

    def _history_event_accepted(self, req_id: int) -> bool:
        """True only for a reqId belonging to the current backfill wave."""
        if req_id not in self._history_req_ids:
            return False
        return self._history_req_generation.get(req_id) == self._history_generation

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

    def _reset_draw_combo_to_cursor(self):
        """Show "Cursor" in the drawing combo without re-arming the tool (ESC-017).

        The router clears the drawing overlay tool when the magnifier is invoked
        mid-draw (TR-4) or when the symbol changes (TR-17). The combo must follow,
        or the stale label swallows the next ``currentTextChanged`` and the same
        tool can never be re-armed. ``blockSignals`` keeps this programmatic reset
        from looping back into ``_on_draw_tool_changed`` mid-transition.
        """
        combo = getattr(self, "draw_combo", None)
        if combo is None or combo.currentText() == "Cursor":
            return
        combo.blockSignals(True)
        try:
            combo.setCurrentText("Cursor")
        finally:
            combo.blockSignals(False)

    def _on_drawing_tool_mode_changed(self, tool: str):
        """Mirror the overlay's active tool: fall back to Cursor when it clears."""
        if tool == "cursor":
            self._reset_draw_combo_to_cursor()

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
        # D16: accept bars from any member of the in-flight backfill wave; a
        # non-member or stale-generation response is ignored outright.
        if not self._history_event_accepted(reqId):
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
        if not self._history_event_accepted(reqId):
            return
        self._history_req_ids.discard(reqId)
        # Finalise exactly once, only after the last member has ended.
        if self._history_req_ids:
            return
        self._finalize_history_wave()

    def _finalize_history_wave(self) -> None:
        """Persist, re-read and render once the last backfill request ends.

        If the wave was *stranded* (watchdog timeout or transport disconnect),
        ``_finalize_stranded_history_wave`` has set ``_history_stranded_reason``.
        That cause is purely diagnostic: it fabricates no bar and changes no
        behaviour — it is appended to the AC-D16.4 shortfall line and the
        WARNING record so a timeout and a disconnect are distinguishable. For a
        normal (non-stranded) finalise the reason is empty and the wording is
        unchanged.
        """
        self._disarm_history_wave_watchdog()
        new_count = len(self._pending_bars)
        if self._pending_bars:
            BarCache.save_bars(self._pending_bars)
        all_bars = BarCache.get_bars(self._current_symbol, self._current_tf)
        self.chart_panel.update_chart(all_bars)
        # D27.1: _last_chart_price must never move backward. If realtime bars
        # were observed since load, the live price is newer than the historical
        # close — rewinding would fabricate a discontinuous (prev, curr) pair
        # and phantom-fire alarms. Skip the assignment in that case.
        if not self._rt_seen:
            self._last_chart_price = all_bars[-1].close if all_bars else None
        # D27.1 (second clause): update_chart is a full refresh that wipes the
        # live forming candle appended by update_last_bar. Re-apply the
        # aggregator's forming bar so the live candle survives finalize.
        forming = (
            self._aggregator.current_bar()
            if self._aggregator is not None
            else None
        )
        if forming is not None:
            if all_bars:
                self.chart_panel.update_last_bar(forming, False)
            else:
                # No history at all: the forming bar is the only bar.
                self.chart_panel.update_chart([forming])
        self._pending_bars = []

        # Read and clear the stranded-wave cause (diagnostic suffix only).
        reason = getattr(self, "_history_stranded_reason", "")
        self._history_stranded_reason = ""
        cause = f" [{reason}]" if reason else ""

        missing_days = self._missing_backfill_trading_days(all_bars)
        failed_count = len(self._backfill_failed_req_ids)
        if missing_days:
            preview = ", ".join(d.isoformat() for d in missing_days[:5])
            self.status_bar.showMessage(
                f"{self._current_symbol} — backfill incomplete: "
                f"{len(missing_days)} trading day(s) still missing ({preview})."
                f"{cause}",
                10000,
            )
            _LOG.warning(
                "Historical backfill shortfall for %s [%s]: %s%s",
                self._current_symbol,
                self._current_tf,
                [d.isoformat() for d in missing_days],
                cause,
            )
        elif failed_count:
            self.status_bar.showMessage(
                f"{self._current_symbol} — {failed_count} historical request(s) "
                f"failed; chart may be incomplete.{cause}",
                10000,
            )
            _LOG.warning(
                "Historical backfill failed requests for %s [%s]: %s%s",
                self._current_symbol,
                self._current_tf,
                sorted(self._backfill_failed_req_ids),
                cause,
            )
        else:
            # D27.4: never declare "live" unconditionally — report the
            # actual stream-health state (usually "awaiting first bar" here;
            # the badge flips to live when the first bar arrives).
            stream_note = self._stream_health.describe()
            self.status_bar.showMessage(
                f"{self._current_symbol} — {len(all_bars)} bars "
                f"({new_count} new). Stream {stream_note}{cause}."
            )

    def _missing_backfill_trading_days(self, bars) -> list:
        """Trading days the completed wave left empty (no bar fabricated)."""
        if not self._backfill_missing_spans:
            return []
        present_days = {
            datetime.fromtimestamp(b.ts, tz=_EASTERN).date() for b in bars
        }
        missing = []
        for span in self._backfill_missing_spans:
            for day in trading_days(span.start_ts, span.end_ts):
                if day not in present_days:
                    missing.append(day)
        return missing

    # ── Real-time bar slot ────────────────────────────────────────────────────

    def _on_realtime_bar(self, reqId: int, time: int, o: float, h: float,
                         l: float, c: float, vol: float, wap: float, count: int):
        if reqId != self._rt_req_id or self._aggregator is None:
            return
        self._rt_seen = True  # D27.1: a live bar was observed since load
        if not self._stream_health.is_live:
            # D27.4: first bar on the subscription -> the stream is live.
            self._stream_health.mark_first_bar()
            self._rt_retry_timer.stop()
            self._update_stream_badge()
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
        # D21.7 / VIS-D21.2: keep the invoking button visibly active while its
        # modal popup is open, and clear the highlight when it closes.
        set_button_active(self.studies_btn, True)
        try:
            dialog.exec()
        finally:
            set_button_active(self.studies_btn, False)

    def _open_alarm_dialog(self):
        if not self._current_symbol:
            self.status_bar.showMessage("Load a symbol before creating alarms.", 3000)
            return
        dialog = AlarmDialog(self._current_symbol, self._last_chart_price, self)
        dialog.alarms_changed.connect(self._reload_current_alarms)
        # D21.7 / VIS-D21.2: highlight the invoking button while the modal popup
        # is open; clear it (even on an exception) once the dialog closes.
        set_button_active(self.alarms_btn, True)
        try:
            dialog.exec()
        finally:
            set_button_active(self.alarms_btn, False)
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
            # ESC-017: same signal-blocked reset the router-driven path uses.
            self._reset_draw_combo_to_cursor()
            # D21.8 / AC-D21.8.2: no timeout — the hint stays visible for as long
            # as Alarm Mode is armed (not the previous 4000 ms).
            self.status_bar.showMessage(ALARM_MODE_STATUS_MESSAGE)
        else:
            # D21.8 / AC-D21.8.2: clear the persistent hint when the mode ends.
            # Every exit path (button toggled off, an alarm placed, a drawing
            # tool selected, the mode otherwise exited) funnels through this
            # signal, so the hint cannot outlive the mode and mask later messages.
            self._clear_alarm_mode_status()

    def _clear_alarm_mode_status(self):
        """Remove the persistent Alarm-Mode hint if it is still on screen.

        Guarded on the current message so an unrelated, later status message is
        never wiped when Alarm Mode ends (AC-D21.8.2: the hint must not
        permanently mask later messages).
        """
        if self.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE:
            self.status_bar.clearMessage()

    def _on_sound_toggled(self, enabled: bool):
        self.sound_service.set_enabled(enabled)

    # ── D17 Phase 2: live dock-width clamp + Watchlist width slots ───────────

    def _read_persisted_width(self) -> int:
        """The raw persisted watchlist width (default ~220, never <150).

        Kept separately from the provisional clamped value so the deferred
        post-``show()`` setup can re-apply the *user's request* against the real
        chart area rather than merely re-clamping the provisional width.
        """
        try:
            raw = self._settings.value(WATCHLIST_WIDTH_KEY)
            width = int(raw) if raw is not None else DEFAULT_WATCHLIST_WIDTH
        except (TypeError, ValueError):
            width = DEFAULT_WATCHLIST_WIDTH
        return max(WATCHLIST_MIN_WIDTH, width)

    def _chart_area_width(self) -> int:
        """The chart-area width: ``centralWidget().width()`` (B1).

        Falls back to the window width when the central widget is absent or not
        yet laid out (e.g. during ``__init__``, before ``show()``), so the
        helpers never see a zero denominator.
        """
        central = self.centralWidget()
        width = central.width() if central is not None else 0
        if width <= 0:
            width = self.width()
        return int(width)

    def _right_dock_available(self) -> bool:
        """True when the single right region exists and is visible on screen.

        When it is hidden/detached (D17's tests hide the right docks) the shared
        clamp must fall back to the watchlist-only rule so a phantom right region
        does not reserve chart-area budget it is not using.
        """
        dock = getattr(self, "right_dock", None)
        if dock is None:
            return False
        try:
            return bool(dock.isVisible())
        except Exception:
            return False

    def _compute_right_dock_collapsed_min_width(self) -> int:
        """D21.13: minimum width of the region once BOTH panels are collapsed.

        The collapsed region is a vertical strip of the two toggle buttons (the
        Active Trader title-bar button and the Account Summary header button), so
        its width is the widest button's ``sizeHint`` plus the standard margins,
        floored at :data:`RIGHT_DOCK_COLLAPSED_MIN_WIDTH`. Never raises.
        """
        try:
            buttons = [
                getattr(self.active_trader, "header_button", None),
                getattr(self.portfolio_panel, "summary_label", None),
            ]
            widths = [b.sizeHint().width() for b in buttons if b is not None]
            content = max(widths) if widths else 0
            return max(
                RIGHT_DOCK_COLLAPSED_MIN_WIDTH,
                int(content) + 2 * RIGHT_DOCK_COLLAPSED_MARGIN,
            )
        except Exception:
            return RIGHT_DOCK_COLLAPSED_MIN_WIDTH

    def _right_region_is_collapsed(self) -> bool:
        """True when BOTH right-region panels are collapsed to their buttons."""
        try:
            return bool(
                self.active_trader.is_collapsed()
                and self.portfolio_panel.is_collapsed()
            )
        except Exception:
            return False

    def _on_right_panel_toggled(self, _checked: bool = False) -> None:
        """Re-layout the right region after a per-panel hide/show toggle (D21.13)."""
        try:
            self._sync_right_dock_collapse()
        except Exception:
            pass

    def _sync_right_dock_collapse(self) -> None:
        """Apply the D21.13 right-region collapse state.

        * vertical stretch: only a shown panel absorbs slack, so the panel that
          stays visible expands into the space the hidden one vacates
          (AC-D21.13.2);
        * both hidden: relax the region's (and the two panels') minimum width to
          the button strip and pin the dock to it explicitly via
          ``_resize_docks_guarded`` so the chart reclaims the width
          (AC-D21.13.3);
        * otherwise: restore ``RIGHT_DOCK_MIN_WIDTH`` and re-run the B3
          cross-clamp.
        """
        collapsed = self._right_region_is_collapsed()
        self._right_region_collapsed = collapsed

        layout = getattr(self, "_right_dock_layout", None)
        if layout is not None:
            try:
                layout.setStretchFactor(
                    self.active_trader,
                    0 if self.active_trader.is_collapsed() else 1,
                )
                layout.setStretchFactor(
                    self.portfolio_panel,
                    0 if self.portfolio_panel.is_collapsed() else 1,
                )
            except Exception:
                pass

        right_dock = getattr(self, "right_dock", None)
        widgets = (
            right_dock,
            getattr(self, "active_trader", None),
            getattr(self, "portfolio_panel", None),
        )
        if collapsed:
            collapsed_w = self._right_dock_collapsed_min_width
            for widget in widgets:
                if widget is not None:
                    widget.setMinimumWidth(collapsed_w)
            if right_dock is not None:
                self._resize_docks_guarded([right_dock], [collapsed_w])
        else:
            for widget in widgets:
                if widget is not None:
                    widget.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)
            self._apply_dock_widths()
        # The dock's layout minimum is recomputed on the next layout pass, so the
        # immediate resize above can be clamped back to the pre-collapse minimum.
        # Re-apply on the next event-loop turn (when the new minimum has settled)
        # so the collapsed width actually sticks.
        try:
            QTimer.singleShot(0, self._apply_dock_widths)
        except Exception:
            pass

    def _plan_dock_widths(self, chart_area: int, requested_left, requested_right):
        """Resolve ``(left, right)`` for the chart area, never below a dock minimum.

        Delegates to the pure :func:`ui.dock_layout.plan_dock_widths` (B3
        cross-clamp, single source of truth). The pure helper owns *all* of the
        clamp logic — per-dock caps, the combined chart-minimum cross-clamp, and
        the hard guarantee that neither width drops below its dock minimum (its
        shrink loop was corrected under T52/ESC-026). This method adds no repair
        of its own: the D18 guarantees rest solely on the helper.

        Because the cap denominator is the **post-resize** chart area
        (``centralWidget().width()`` changes as the docks resize), a single pass
        would leave the dock over ``floor(0.40 × chart_area_after)`` — the
        accepted reading of AC-D18.2 is the chart area *after* the resize. The
        plan is therefore iterated to a fixed point: each pass plans against the
        chart area that the previous pass would produce, using the invariant
        ``S = chart_area + current_left + current_right`` (the region housing the
        chart and both docks). The cap contraction (0.4 / 0.5 < 1) makes this
        converge, so the returned width is self-consistent with the chart area it
        leaves behind.
        """
        try:
            cur_left = self.watchlist_dock.width()
            cur_right = self.right_dock.width()
        except Exception:
            cur_left = requested_left if requested_left is not None else 0
            cur_right = requested_right if requested_right is not None else 0
        invariant = chart_area + int(cur_left) + int(cur_right)

        ca = chart_area
        left, right = None, None
        previous = None
        for _ in range(24):
            left, right = plan_dock_widths(
                ca, int(requested_left), int(requested_right)
            )

            if (left, right) == previous:
                break
            previous = (left, right)
            next_ca = invariant - left - right
            if next_ca <= 0:
                break
            ca = next_ca
        return int(left), int(right)

    def _apply_dock_widths(self, requested_left: int | None = None,
                           requested_right: int | None = None) -> int:
        """Shared, idempotent dock-width clamp (D17 watchlist + D18 right region).

        Reads the current chart area (``centralWidget().width()``) and clamps both
        docks against it. When the single right region is visible, the combined
        B3 cross-clamp :meth:`_plan_dock_widths` is used so ``chart_area`` keeps
        its ~400px minimum and enlarging one dock forces the other to shrink
        (AC-D18.5); when it is hidden, only the watchlist rule applies (D17).

        ``requested_left`` / ``requested_right`` are the widths the user is
        dragging toward; ``None`` means "clamp whatever the dock currently is"
        (the drag/resize path). ``resizeDocks`` is issued only when a computed
        size differs from the dock's current width by more than 1px, and
        re-entrant invocations are suppressed by ``_applying_dock_widths`` so an
        applied resize cannot recurse or jitter (AC-D17.6 / T49-T07).

        Returns the applied (clamped) watchlist width. Never raises.
        """
        if getattr(self, "_applying_dock_widths", False):
            return getattr(self, "_watchlist_width", WATCHLIST_MIN_WIDTH)
        dock = getattr(self, "watchlist_dock", None)
        if dock is None:
            return getattr(self, "_watchlist_width", WATCHLIST_MIN_WIDTH)
        self._applying_dock_widths = True
        try:
            chart_area = self._chart_area_width()
            current_left = dock.width()
            base_left = current_left if requested_left is None else int(requested_left)

            right_dock = getattr(self, "right_dock", None)
            collapsed = bool(getattr(self, "_right_region_collapsed", False))
            # D21.13: a fully-collapsed region (both panels hidden) is treated as
            # hidden for the cross-clamp — it reserves no chart-area budget, so
            # the watchlist regains its own cap. The dock itself is pinned to the
            # button strip below.
            use_right = (
                self._right_dock_available()
                and right_dock is not None
                and not collapsed
            )

            if use_right:
                current_right = right_dock.width()
                base_right = (
                    current_right
                    if requested_right is None
                    else int(requested_right)
                )
                plan_left, plan_right = self._plan_dock_widths(
                    chart_area, base_left, base_right
                )
                self._watchlist_width = plan_left
                self._right_dock_width = plan_right
                # Both docks are passed together whenever anything changes:
                # ``resizeDocks`` distributes slack among the *listed* docks, so
                # resizing only one would hand it all the leftover space and
                # overshoot the cap. Listing both with their exact planned sizes
                # keeps each dock at its plan value.
                if (
                    abs(current_left - plan_left) > 1
                    or abs(current_right - plan_right) > 1
                ):
                    self._resize_docks_guarded(
                        [dock, right_dock], [plan_left, plan_right]
                    )
            else:
                cap = watchlist_max_width(chart_area)
                desired = max(WATCHLIST_MIN_WIDTH, min(base_left, cap))
                self._watchlist_width = desired
                if collapsed and right_dock is not None:
                    # D21.13: pin the collapsed region to its button strip in the
                    # same resize so the chart keeps the reclaimed width.
                    collapsed_w = getattr(
                        self, "_right_dock_collapsed_min_width",
                        RIGHT_DOCK_COLLAPSED_MIN_WIDTH,
                    )
                    if (
                        abs(current_left - desired) > 1
                        or abs(right_dock.width() - collapsed_w) > 1
                    ):
                        self._resize_docks_guarded(
                            [dock, right_dock], [desired, collapsed_w]
                        )
                elif abs(current_left - desired) > 1:
                    self._resize_docks_guarded([dock], [desired])
        except Exception:
            pass
        finally:
            self._applying_dock_widths = False
        return self._watchlist_width

    def _resize_docks_guarded(self, docks, sizes) -> None:
        """Issue ``resizeDocks`` with the acquired splitter's signals blocked.

        The dock-area splitter is normally not reachable via PyQt6's public API
        (see ``_acquire_dock_splitter``); when it was acquired, block its signals
        for the duration of the resize so the programmatic change cannot
        re-enter ``_apply_dock_widths``.
        """
        splitter = getattr(self, "_dock_splitter", None)
        blocked = False
        if splitter is not None:
            try:
                splitter.blockSignals(True)
                blocked = True
            except Exception:
                blocked = False
        try:
            self.resizeDocks(docks, sizes, Qt.Orientation.Horizontal)
        finally:
            if blocked:
                try:
                    splitter.blockSignals(False)
                except Exception:
                    pass

    def _acquire_dock_splitter(self):
        """Defensively obtain the dock-area internal ``QSplitter`` (D17 risk).

        Qt's ``QMainWindowLayout`` owns the dock-area splitter at the C++ level
        and it is **not** exposed as a ``QSplitter`` in PyQt6's object tree
        (``findChildren(QSplitter)`` only finds the chart's own vertical
        splitter). Picking that one would wire the watchlist clamp to chart
        layout changes — wrong. So a candidate is only accepted when it actually
        governs the watchlist dock: it must not belong to the ``ChartPanel`` and
        one of its sections must be the dock's ancestor chain. In practice this
        returns ``None`` on the current PyQt6, and the event-filter fallback
        (``eventFilter``) carries the live clamp. The connection is still
        attempted so a future Qt that *does* expose the splitter is covered.
        """
        try:
            for splitter in self.findChildren(QSplitter):
                if splitter is getattr(self.chart_panel, "_splitter", None):
                    continue
                if self._splitter_contains_watchlist(splitter):
                    try:
                        splitter.splitterMoved.connect(self._on_dock_splitter_moved)
                    except Exception:
                        continue
                    return splitter
        except Exception:
            pass
        return None

    def _splitter_contains_watchlist(self, splitter) -> bool:
        """True when ``splitter`` has a section that contains the watchlist dock."""
        try:
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                if widget is None:
                    continue
                if widget is self.watchlist_dock:
                    return True
                if widget.isAncestorOf(self.watchlist_dock):
                    return True
        except Exception:
            pass
        return False

    def _deferred_dock_setup(self) -> None:
        """Post-``show()`` normalize + deferred splitter acquisition (D17).

        Runs once the event loop has laid the window out: acquires the
        dock-area splitter if Qt exposes it, then re-applies the persisted width
        clamped for the now-real chart area. Swallows all exceptions so a
        Qt-version-dependent wiring path can never break window start-up.
        """
        try:
            if getattr(self, "_dock_splitter", None) is None:
                self._dock_splitter = self._acquire_dock_splitter()
            # Re-apply the persisted request (not just the provisional clamp) so
            # the restore honours AC-D17.4 against the now-real chart area.
            self._apply_dock_widths(
                requested_left=getattr(
                    self, "_persisted_watchlist_width", DEFAULT_WATCHLIST_WIDTH
                )
            )
        except Exception:
            pass

    def _on_right_dock_visibility_changed(self, _visible: bool) -> None:
        """Re-clamp after the right region is shown/hidden.

        A dock's ``visibilityChanged`` fires before the main layout has
        re-assigned the central widget's new width, so the apply is deferred
        until the layout settles. Hiding the region lets the watchlist regain its
        own cap (D17), so the *persisted/requested* width is re-honoured rather
        than the momentarily-clamped width; showing it re-applies the B3
        cross-clamp. Several deferred passes are used because a single
        event-loop turn can still see the dock as visible and the old chart area.
        """
        requested = getattr(self, "_persisted_watchlist_width", None)
        self._deferred_dock_clamp(requested, passes=8)

    def _deferred_dock_clamp(self, requested_left, passes: int = 8) -> None:
        """Apply the shared clamp over deferred event-loop turns until settled.

        A dock's ``visibilityChanged`` fires before the layout has re-assigned the
        central widget's width, so a single apply can read a stale chart area and
        the applied resize can itself change that area. Each pass is therefore
        followed by another until the dock widths are self-consistent with the
        chart area they leave behind (or ``passes`` is exhausted). Hiding the
        region lets the watchlist regain its own cap; showing it re-applies the
        B3 cross-clamp.
        """
        def _pass(remaining: int):
            try:
                self._apply_dock_widths(requested_left=requested_left)
            except Exception:
                pass
            if remaining > 1 and not self._dock_widths_consistent():
                QTimer.singleShot(0, lambda: _pass(remaining - 1))

        QTimer.singleShot(0, lambda: _pass(passes))

    def _dock_widths_consistent(self) -> bool:
        """True when the applied dock widths self-consistently match the chart area.

        The comparison is *predictive*: applying a width ``L`` leaves the chart
        area at ``T - L`` (with ``T`` the invariant chart-plus-docks width), so
        the width is settled when it equals its own cap for the chart area it
        would produce. This avoids reading a chart area that Qt has not yet
        re-laid-out after the previous ``resizeDocks``.
        """
        try:
            ca = self._chart_area_width()
            if self._right_dock_available() and not getattr(
                self, "_right_region_collapsed", False
            ):
                plan_left, plan_right = self._plan_dock_widths(
                    ca, self.watchlist_dock.width(), self.right_dock.width()
                )
                return self.right_dock.width() == plan_right and (
                    ca - plan_left - plan_right >= CHART_MIN_WIDTH - 1
                )
            invariant = ca + self.watchlist_dock.width()
            return self._watchlist_width == watchlist_max_width(
                invariant - self._watchlist_width
            )
        except Exception:
            return True

    def _on_dock_splitter_moved(self, pos: int, index: int) -> None:
        """``QSplitter.splitterMoved`` hook: clamp live during the drag (AC-D17.3)."""
        self._apply_dock_widths()

    def _on_dock_drag_event(self) -> None:
        """Event-filter fallback clamp while the dock handle is being dragged.

        Called from :meth:`eventFilter` on the watchlist dock for the mouse
        move/release sequence, so the cap binds **during** the drag even when the
        dock-area internal splitter cannot be acquired. The apply is deferred
        with a coalescing single-shot because an event filter runs *before* the
        dock consumes the drag, so the dock width is only settled on the next
        event-loop turn.
        """
        self._schedule_dock_clamp()

    def _schedule_dock_clamp(self) -> None:
        """Coalesce deferred ``_apply_dock_widths`` calls (one per event loop turn)."""
        if getattr(self, "_dock_clamp_scheduled", False):
            return
        self._dock_clamp_scheduled = True

        def _run():
            self._dock_clamp_scheduled = False
            try:
                self._apply_dock_widths()
            except Exception:
                pass

        QTimer.singleShot(0, _run)

    def eventFilter(self, obj, event):
        # D17/D18: fallback enforcement for the dock-area splitter on both dock
        # regions. ``resizeDocks`` cannot re-enter us (guard), and this only
        # observes — never consumes — the drag events.
        try:
            if obj is getattr(self, "watchlist_dock", None) or obj is getattr(
                self, "right_dock", None
            ):
                et = event.type()
                if et in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease):
                    self._on_dock_drag_event()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        """Full-screen / window-state normalize (D18, AC-D18.1).

        No ``showFullScreen`` is added (PA-D17D18-5): full screen remains an
        OS/WM state. When the window state changes — in particular into/out of
        full screen — the right region's cap is re-applied against the now-real
        window rect via a deferred one-shot, so the region is laid out on-screen
        with a non-zero width without manual repositioning.
        """
        super().changeEvent(event)
        try:
            if event.type() == QEvent.Type.WindowStateChange:
                self._schedule_dock_clamp()
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # D17/D18 Phase 2/4: re-clamp in *both* directions on any window resize
        # (the shared ``_apply_dock_widths`` shrinks over-cap widths and never
        # lets either dock fall below its minimum).
        try:
            if getattr(self, "watchlist_dock", None) is not None:
                self._apply_dock_widths()
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

    @staticmethod
    def _ext_hours_label(enabled: bool) -> str:
        """D21.3: toolbar label for the extended-hours state.

        ON (extended hours) -> "Ext Hours"; OFF (regular trading hours) -> "RTH".
        """
        return "Ext Hours" if enabled else "RTH"

    def _on_ext_hours_toggled(self, enabled: bool):
        """Relabel and reload chart with/without extended hours when toggled."""
        self.ext_hours_btn.setText(self._ext_hours_label(enabled))
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
        self.sub_manager.unsubscribe_all_of_type(DEPTH)
        contract = get_contract_for_symbol(self._current_symbol)
        self._depth_req_id = self.depth_manager.subscribe(
            self._current_symbol, contract, num_levels=10
        )
        # D27.3: register for the reconnect replay (rebinds _depth_req_id).
        self.sub_manager.subscribe(
            self._current_symbol,
            self._depth_req_id,
            DEPTH,
            reissue=lambda s=self._current_symbol, c=contract: (
                self.depth_manager.subscribe(s, c, num_levels=10)
            ),
            rebind=self._rebind_depth_req_id,
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
        # D21.10 / AC-D21.10.1-5: chart-click path only. Pre-fill the clicked
        # level (``initial_price``); keep the current market price separate so
        # the dialog can default the condition against the alarm price. A yellow
        # dashed preview line is drawn at the clicked level, follows the price
        # spinbox live, and is removed on every close path — after Add,
        # ``_reload_current_alarms`` draws the real alarm line in its place.
        dialog = AlarmDialog(
            self._current_symbol,
            self._last_chart_price,
            self,
            initial_price=price,
        )
        dialog.alarms_changed.connect(self._reload_current_alarms)
        self.chart_panel.show_alarm_preview(price)
        dialog.price_input.valueChanged.connect(
            self.chart_panel.update_alarm_preview
        )
        try:
            dialog.exec()
        finally:
            self.chart_panel.hide_alarm_preview()
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
        # D26.9: never transmit while disconnected — a dead socket used to
        # show "Submitted" before TWS error 504 arrived.
        if not self._ibkr_connected:
            msg = "Order not placed: not connected to TWS."
            self.status_bar.showMessage(msg, 8000)
            self.active_trader.order_entry.status_label.setText(msg)
            return
        # D26.7: validate BEFORE anything else — rejected orders never reach
        # placeOrder and never raise; the rejection is surfaced in the UI.
        problems = validate_order(
            action=action, order_type=order_type, qty=qty,
            lmt_price=lmt_price, stop_price=stop_price,
            target_price=target_price, symbol=symbol,
            ref_price=self.active_trader.last_price,
        )
        if problems:
            msg = "Order rejected: " + "; ".join(problems)
            self.status_bar.showMessage(msg, 8000)
            self.active_trader.order_entry.status_label.setText(msg)
            return

        pacing_manager.throttle_realtime()

        if order_type == "MKT":
            order = order_registry.market_order(action, qty)
            parent_id = id_manager.get_id()
            self.ib_client.placeOrder(parent_id, contract, order)
            user_order = UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="MKT", transmit=True,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(parent_id, action, qty, "Submitted")

        elif order_type == "LMT":
            order = order_registry.limit_order(action, qty, lmt_price)
            parent_id = id_manager.get_id()
            self.ib_client.placeOrder(parent_id, contract, order)
            user_order = UserOrder(
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
            user_order = UserOrder(
                order_id=parent_id, symbol=symbol, action=action,
                total_qty=qty, order_type="STP", aux_price=stop_price,
                transmit=True,
            )
            order_registry.register(user_order)
            self.active_trader.set_order_status(parent_id, action, qty, "Submitted")

        elif order_type == "BRACKET":
            # D26.2: reserve all three leg IDs up front so no later get_id()
            # (order or reqId) can reissue a live bracket-leg order ID.
            parent_id = id_manager.reserve(3)
            parent, stop, target = order_registry.bracket_order(
                parent_id, action, qty, lmt_price, stop_price, target_price,
            )
            self.ib_client.placeOrder(parent_id, contract, parent)
            self.ib_client.placeOrder(parent_id + 1, contract, stop)
            self.ib_client.placeOrder(parent_id + 2, contract, target)
            # D26.8 / VALIDATOR: register EVERY transmitted leg at transmit
            # time, or the kill switch and _update_order_status cannot see
            # the protective children. (The old code registered only the
            # parent, with a self-referential parent_id and transmit=False.)
            child_action = "SELL" if action == "BUY" else "BUY"
            for leg_id, leg_type, leg_action, leg_price in (
                (parent_id, "BRACKET", action, lmt_price),
                (parent_id + 1, "STP", child_action, stop_price),
                (parent_id + 2, "LMT", child_action, target_price),
            ):
                order_registry.register(UserOrder(
                    order_id=leg_id, symbol=symbol, action=leg_action,
                    total_qty=qty, order_type=leg_type,
                    lmt_price=leg_price if leg_type != "STP" else None,
                    aux_price=leg_price if leg_type == "STP" else None,
                    status="Submitted",
                    parent_id=0 if leg_id == parent_id else parent_id,
                    oca_group=f"bracket-{parent_id}", transmit=True,
                ))
            self.active_trader.set_order_status(
                parent_id, action, qty, "Bracket Submitted"
            )

    def _on_open_order(self, orderId: int, contract, order, orderState):
        self._update_order_status(orderId, getattr(orderState, "status", ""))

    def _kill_switch(self) -> tuple[int, int]:
        """D26.8: cancel EVERY open order immediately.

        Issues reqGlobalCancel() plus a per-ID cancelOrder for each tracked
        open order (belt-and-braces: the global cancel is a request, not a
        guarantee). Returns (open_before, cancel_requests_sent). Registry
        entries are marked Cancelled locally; TWS orderStatus updates will
        confirm or correct.
        """
        terminal = {"Filled", "Cancelled", "Rejected", "Inactive"}
        open_ids = [oid for oid, o in order_registry.all().items()
                    if o.status not in terminal]
        pre = len(open_ids)
        try:
            self.ib_client.reqGlobalCancel()
        except Exception:  # noqa: BLE001 — a kill switch must not raise
            _LOG.exception("reqGlobalCancel failed")
        sent = 0
        for oid in open_ids:
            try:
                self.ib_client.cancelOrder(oid)
                sent += 1
            except Exception:  # noqa: BLE001
                _LOG.exception("cancelOrder(%s) failed", oid)
        for oid in open_ids:
            order_registry.update_status(oid, "Cancelled")
        msg = (f"Kill switch: {sent}/{pre} cancel requests sent "
               f"(reqGlobalCancel + per-order cancel).")
        self.status_bar.showMessage(msg, 12000)
        self.active_trader.order_entry.status_label.setText(msg)
        return pre, sent

    def _on_kill_switch_clicked(self):
        """Toolbar kill-switch button: cancel all open orders, show counts."""
        self._kill_switch()

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
        self._account_id = account  # D26.5: feeds the connection badge
        summary = dict(getattr(self, "_account_summary", {}))
        summary[tag] = value
        self._account_summary = summary
        self.portfolio_panel.set_account_summary(summary)
        self._update_conn_badge()

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
        # D26.8: kill working orders FIRST so no protective/stale order can
        # fire against the closes that follow (_kill_switch surfaces counts).
        self._kill_switch()
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
        # Persist watchlist dock width (D13/D17): re-clamp to the current
        # chart-area cap before saving so an over-cap width cannot leak into
        # the next session (AC-D17.4).
        try:
            if getattr(self, "watchlist_dock", None) is not None:
                self._apply_dock_widths()
                self._watchlist_width = save_watchlist_width(
                    self._settings, self._watchlist_width, self._chart_area_width()
                )
        except Exception:
            pass
        # Cancel realtime bar subscription
        if self._rt_req_id is not None:
            self.rt_manager.unsubscribe(self._rt_req_id)
            self._rt_req_id = None
        # Cancel every in-flight backfill request and invalidate the generation
        # so late responses cannot mix symbols/timeframes. Disarm the backfill
        # watchdog too, so arm/disarm stays symmetric with the other
        # wave-terminating paths (finalise, disconnect, watchdog timeout,
        # load_chart/switch) and the timer cannot outlive the window.
        self._disarm_history_wave_watchdog()
        self._cancel_history_requests()
        self._history_generation += 1
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
