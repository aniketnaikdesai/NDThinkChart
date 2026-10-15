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
from PyQt6.QtGui import QKeySequence, QShortcut

from config import settings
from ibkr.client import IBApiClient, ConnectionState, DisconnectClass
from ibkr.market_data import MarketDataManager, TIMEFRAME_CONFIG
from ibkr.tick_history import TickHistoryManager
from data.footprint_cache import FootprintCache
from data.db import db as _app_db
from ibkr.market_depth import MarketDepthManager
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.contracts import get_contract_for_symbol
from ibkr.utils import parse_ibkr_date
from ibkr.orders import orders as order_registry, UserOrder
from ibkr.validation import validate_order
from ibkr.id_manager import id_manager
from ibkr.pacing import pacing_manager, order_limiter, PacingExceeded
from ibkr.subscription_manager import (
    DEPTH,
    DEPTH_HEATMAP,
    RT_BARS,
    S0_TICKS,
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
from ui.ticker_session import TickerSession
from data.alarm_store import AlarmStore
from data.models import Bar, Position
from data.bar_cache import BarCache
from data.bar_aggregator import BarAggregator, TIMEFRAME_SECONDS
from data.study_store import StudyStore
from data.drawing_store import DrawingStore
from data.db import db
from services.alarm_service import evaluate_alarms
from services.drawing_service import DEFAULT_DRAWING_COLOR
from services.sound_service import SoundService
from services.backfill_service import (
    RequestPlan, find_missing_spans, plan_requests,
)
from services.market_calendar import trading_days
from services.contract_lookup_service import ContractLookupService
from services.md_line_guard import assess as md_assess

# D37: depth feed budget — IBKR allows 3–60 simultaneous depth feeds
# (scales with market-data lines); warn + refuse past the cap.
DEPTH_FEED_CAP = 60

_LOG = logging.getLogger(__name__)

#: D27.9: upper bound (seconds) on the trailing 5-sec priming fetch. Sub-2h
#: periods are covered exactly; larger periods prime the trailing window.
_PRIME_MAX_SPAN_S = 7_200

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


def conn_badge_text(
    account_id: str | None,
    account_type: str | None,
    monitoring_paused: bool = False,
) -> tuple[str, str]:
    """D26.5: derive the connection badge from the verified port + account.

    The port is fail-fast verified at startup (settings.check_live_port), so
    reaching this point means the live port — but the account itself may still
    be paper/demo (IBKR paper accounts carry DU-prefixed IDs). Returns
    (text, stylesheet-color); never a hardcoded claim.

    D40: ``monitoring_paused`` adds the owner-approved monitoring state —
    "Monitoring paused — TWS disconnected". Amber (warning), never green:
    the badge must not keep a connected appearance while paused.
    """
    if monitoring_paused:
        return "Monitoring paused — TWS disconnected", "#fbbf24"
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
        # D28.5: once set, IBKR/timer slots early-return so teardown never
        # touches cleared widgets.
        self._closing: bool = False
        self._reader_thread: threading.Thread | None = None

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("MainToolbar")
        toolbar.setFixedHeight(TOOLBAR_CONTENT_HEIGHT)
        # The base look is scoped with the #MainToolbar selector so it composes
        # with the VIS-D21.2 shared stylesheet below into one parseable sheet
        # (a bare declaration list fails to parse once further rules are added).
        # The font is re-declared here too: with a widget-local stylesheet Qt
        # resolves this subtree against it, so the app-level `*` rule in
        # config/theme.qss (Inter 11px) did not reach the toolbar controls --
        # observed: they rendered the 9pt Qt default instead of the theme font.
        toolbar.setStyleSheet(
            "#MainToolbar { background: #101218; border-bottom: 1px solid #232938;"
            ' font-family: "Inter", "Segoe UI", sans-serif; font-size: 11px; }'
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
        # D24: pop-out button (Ctrl/Cmd+P). Snapshots the current symbol /
        # timeframe / mode / ext-hours into a read-only pop-out window.
        self.popout_btn = QPushButton("Pop out")
        self.popout_btn.setToolTip(
            f"Open a read-only pop-out chart (Ctrl/Cmd+P, max {settings.MAX_POPOUTS})"
        )
        self.popout_btn.clicked.connect(self._open_popout)
        tb_layout.addWidget(self.popout_btn)
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
        # D36: footprint UI signals → the active session.
        self.chart_panel.footprint_toggled.connect(self._on_fp_toggled)
        self.chart_panel.footprint_viewport_changed.connect(
            self._on_fp_viewport)
        # D37: depth heatmap toggle → the active session.
        self.chart_panel.depth_toggled.connect(self._on_depth_toggled)
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
        # D40: True while TWS is gone (nightly close) and monitoring is
        # paused — the connection badge shows the paused state instead
        # of Paper/Live/Disconnected. Set in _on_disconnected on a
        # TWS-gone classification, cleared in _on_connected.
        self._tws_paused = False
        self.watchlist_panel.set_add_enabled(False)
        # D39.1: search starts disabled; enabled on connect.
        self.watchlist_panel.set_search_enabled(False)
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
        # ── D38 news digest dock (38a.2) ──────────────────────────────────
        # Repositionable, closable, reopenable from the View menu (or the
        # Ctrl+Shift+N shortcut). Hidden until first opened.
        from ui.news_digest_dock import NewsDigestDock
        self.news_digest_dock = NewsDigestDock(self, self)
        self.news_digest_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                           self.news_digest_dock)
        # Minimal menubar (the app previously had none): View → News Digest.
        # The dock's toggleViewAction keeps menu/dock/shortcut in sync.
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")
        self._news_digest_action = self.news_digest_dock.toggleViewAction()
        self._news_digest_action.setText("News Digest")
        self._news_digest_action.setShortcut("Ctrl+Shift+N")
        view_menu.addAction(self._news_digest_action)
        self.news_digest_dock.visibilityChanged.connect(
            self._on_news_digest_visibility)
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
        # D36: historical-tick manager (footprint) + persistent cache.
        self.tick_history_manager = TickHistoryManager(self.ib_client)
        self.footprint_cache = FootprintCache(_app_db.conn)
        self.rt_manager = RealtimeBarsManager(self.ib_client)
        self.depth_manager = MarketDepthManager(self.ib_client)
        self.sub_manager = SubscriptionManager()
        # D38: news API client (38a.1) — headline backfill + article fetch.
        from ibkr.news import NewsManager
        self.news_manager = NewsManager(self.ib_client)
        # D38: yfinance event source (38b.1) — the sole approved secondary
        # source. Shared cache + worker across sessions (one throttle point).
        from data.events.yfinance_source import (
            YFinanceCache, YFinanceEventSource)
        self._yf_cache = YFinanceCache(_app_db.db_path)
        self.yf_event_source = YFinanceEventSource(self._yf_cache)
        self.yf_event_source.bind_refresh(self._on_yfinance_events)

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

        # D39.1: debounced symbol search (watchlist header box).
        from services.symbol_search import SymbolSearchService

        self._symbol_search = SymbolSearchService(
            self.md_manager, self.ib_client.bridge
        )
        self._symbol_search.search_finished.connect(
            self._on_search_finished
        )
        self.watchlist_panel.search_text_changed.connect(
            self._symbol_search.type_ahead
        )
        self.watchlist_panel.search_sample_selected.connect(
            self._on_search_sample_selected
        )
        # Search-result contract resolution reuses the bounded D22 lookup;
        # results are keyed separately from watchlist adds.
        self._pending_search_select: dict[int, object] = {}

        # Inject md_manager into watchlist
        self.watchlist_panel.set_market_data_manager(self.md_manager)
        # D27.3: the panel type-tags its live subs for the reconnect replay.
        self.watchlist_panel.set_subscription_manager(self.sub_manager)
        # D27.5: watchlist ticks feed the central symbol -> last_price map.
        self.watchlist_panel.set_price_sink(self._record_symbol_price)
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
        # D28.2: toast is parented to the window, not the chart panel — alarm
        # triggers for background symbols must toast from the main window.
        self.toast = Toast(self)

        # Bridge signal wiring
        b = self.ib_client.bridge
        b.connected.connect(self._on_connected)
        b.disconnected.connect(self._on_disconnected)
        b.error_msg.connect(self._on_error)
        b.historical_bar.connect(self._on_historical_bar)
        b.historical_data_end.connect(self._on_historical_data_end)
        # D36 footprint: historical ticks, routed by reqId.
        b.historical_ticks_bid_ask.connect(self._on_fp_ticks_bid_ask)
        b.historical_ticks_last.connect(self._on_fp_ticks_last)
        b.tick_price.connect(self.watchlist_panel.on_tick_price)
        b.tick_size.connect(self.watchlist_panel.on_tick_size)
        # D37 S0: route price/size ticks to sessions too (auction 34/35/36/61
        # arrive on the session's S0 reqMktData). The watchlist keeps its own
        # table; both consumers filter by reqId.
        b.tick_price.connect(self._on_session_tick_price)
        b.tick_size.connect(self._on_session_tick_size)
        # D37 S0 substrate: generic/string/news ticks, routed by reqId.
        b.tick_generic.connect(self._on_s0_tick_generic)
        b.tick_string.connect(self._on_s0_tick_string)
        b.tick_news.connect(self._on_s0_tick_news)
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
        # D27.6: not subscribed until the first connect.
        self.portfolio_panel.set_account_unavailable(True)

        # Portfolio panel signal wiring
        self.portfolio_panel.position_close_requested.connect(self._on_portfolio_close_position)
        self.portfolio_panel.group_close_requested.connect(self._on_portfolio_close_group)
        self.portfolio_panel.flatten_all_requested.connect(self._on_portfolio_flatten_all)
        self.portfolio_panel.position_sltp_changed.connect(self._on_portfolio_sltp_changed)
        self.portfolio_panel.group_sltp_changed.connect(self._on_portfolio_group_sltp_changed)

        # Active trader order entry
        self.active_trader.order_place_requested.connect(self._on_order_place_requested)

        # State
        # D28.2: per-symbol sessions. Chart data-plane state (_rt_req_id,
        # _aggregator, _current_alarms, _last_chart_price, _rt_seen,
        # _stream_health) lives on TickerSession now; the properties below
        # delegate to the primary session for the current symbol.
        self._sessions: dict[str, TickerSession] = {}
        self._req_to_session: dict[int, TickerSession] = {}
        self._primary_session: TickerSession | None = None
        # D24: open pop-out windows (capped at MAX_POPOUTS).
        self._popouts: list = []
        # D25: headless alarm monitor (wired to the session registry).
        from services.alarm_monitor import AlarmMonitor

        self.alarm_monitor = AlarmMonitor(self)
        # D39: shared volume baseline (one per app — sessions share nothing
        # across tapes because the key already holds the resolved contract).
        from services.volume_baseline import VolumeBaselineService

        self.volume_baseline = VolumeBaselineService()
        self._depth_req_id: int | None = None
        self._current_symbol: str = ""
        self._current_tf: str = "5 mins"
        # D27.9: in-flight aggregator-priming request (trailing 5-sec bars
        # for the current partial period). The live feed attaches only after
        # D28.2: priming + history-wave state lives on TickerSession now.
        # The properties below delegate to the current symbol's session for
        # test compatibility.
        # D28.2: studies config lives on TickerSession (_current_studies facade
        # below delegates to the current symbol's session).
        # D27.5: central symbol -> last_price map (chart + watchlist feeds).
        # Position market prices look up the position's own symbol here —
        # never the chart's _last_chart_price.
        self._symbol_last_prices: dict[str, float] = {}
        # D27.6: account-data subscription state (positions + summary).
        self._account_subscribed: bool = False
        self._account_summary_req_id: int | None = None
        # D27.4: RT retry timer. The StreamHealth object itself lives on the
        # TickerSession now (self._stream_health delegates to the primary
        # session); this timer stays window-level.
        self._rt_retry_timer = QTimer(self)
        self._rt_retry_timer.setSingleShot(True)
        self._rt_retry_timer.timeout.connect(self._retry_rt_subscribe)
        self._active_draw_group_id: int | None = None

        # D24: Ctrl/Cmd+P opens a pop-out of the current chart.
        popout_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        popout_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        popout_shortcut.activated.connect(self._open_popout)

        # Start connection
        self.ib_client.connect(settings.IBKR_HOST, settings.IBKR_PORT, settings.IBKR_CLIENT_ID)
        # D28.5: keep a handle so closeEvent can join the reader thread.
        self._reader_thread = threading.Thread(
            target=self.ib_client.run, daemon=True, name="ibkr-reader")
        self._reader_thread.start()

    # ── Session registry (D28.2) ──────────────────────────────────────────────

    def get_or_create_session(self, symbol: str) -> TickerSession:
        """Return the TickerSession for an uppercase symbol, creating it."""
        key = symbol.upper()
        if not key:
            raise ValueError("get_or_create_session requires a symbol")
        session = self._sessions.get(key)
        if session is None:
            session = TickerSession(key, self)
            # DEC-1: alarm triggers are window-global. The main window
            # toasts + sounds for ANY session's alarms (even when the main
            # chart shows another ticker); only the badge is primary-only.
            session.alarm_triggered.connect(self._on_session_alarm_triggered)
            self._sessions[key] = session
        return session

    def _register_req_id(self, req_id: int, session: TickerSession) -> None:
        """Maintain the reqId → TickerSession routing table (subscribe time)."""
        self._req_to_session[req_id] = session

    def _unregister_req_id(self, req_id: int) -> None:
        self._req_to_session.pop(req_id, None)

    def _teardown_session(self, symbol: str) -> None:
        """Drop a session whose last view detached and which is not monitored."""
        session = self._sessions.pop(symbol.upper(), None)
        if session is None:
            return
        if self._primary_session is session:
            self._primary_session = None
        session.teardown()
        session.deleteLater()

    def _session_for_req_id(self, req_id: int) -> TickerSession | None:
        return self._req_to_session.get(req_id)

    # ── D37 budget guards (37.4 depth budget, 37.5 MD-line guard) ────────

    def _md_line_count(self) -> int:
        """Active market-data lines (owns the §7 accounting — C37.1).

        Counts RT-bar lines, S0 lines (new in D37), depth feeds, and
        watchlist rows explicitly. Called before new D37 subscriptions.
        """
        rt = sum(1 for s in self._sessions.values()
                 if s.rt_req_id is not None)
        s0 = sum(1 for s in self._sessions.values()
                 if s.s0_req_id is not None)
        depth = (self.depth_manager.active_feed_count()
                 if self.depth_manager is not None else 0)
        watchlist = self.watchlist_panel.active_row_count()
        return rt + s0 + depth + watchlist

    def _guard_md_lines(self, symbol: str, purpose: str) -> bool:
        """Warn (never silently drop) near the 100-line cap; refuse past it.

        Returns True when the subscription may proceed.
        """
        projected = self._md_line_count() + 1
        level, message = md_assess(projected, symbol, purpose)
        if level == "ok":
            return True
        self.status_bar.showMessage(message, 8000)
        return level != "exceeded"

    def _guard_depth_budget(self, symbol: str) -> bool:
        """Refuse a new depth feed past DEPTH_FEED_CAP with a named warning."""
        if self.depth_manager.active_feed_count() >= DEPTH_FEED_CAP:
            self.status_bar.showMessage(
                f"Depth feed budget exceeded ({DEPTH_FEED_CAP}) — "
                f"no depth for {symbol}.", 8000)
            return False
        return True

    # ── Pop-outs (D24) ──────────────────────────────────────────────────

    def _register_popout(self, popout) -> None:
        if popout not in self._popouts:
            self._popouts.append(popout)

    def _unregister_popout(self, popout) -> None:
        if popout in self._popouts:
            self._popouts.remove(popout)

    def _open_popout(self) -> None:
        """Snapshot the current chart into a read-only pop-out window."""
        from ui.popout_window import PopoutChartWindow

        if not self._current_symbol:
            self.status_bar.showMessage(
                "Load a symbol before popping out.", 3000
            )
            return
        if len(self._popouts) >= settings.MAX_POPOUTS:
            self.status_bar.showMessage(
                f"Pop-out limit reached ({settings.MAX_POPOUTS}). "
                "Close one to open another.",
                5000,
            )
            return
        popout = PopoutChartWindow(
            symbol=self._current_symbol,
            timeframe=self._current_tf,
            mode=self.mode_combo.currentText(),
            extended_hours=self.ext_hours_btn.isChecked(),
            host=self,
            parent=self,
        )
        popout.attach()
        popout.show()
        self.status_bar.showMessage(
            f"Popped out {self._current_symbol} [{self._current_tf}].", 3000
        )

    def _restore_popouts(self) -> None:
        """D24.9: re-open persisted pop-outs after connect.

        Lazy attach, cache-first render: the session syncs from cache on
        attach; the RT subscription follows the normal pacing path.

        Runs on every (re)connect: records whose symbol/timeframe/mode is
        already open are skipped so a reconnect never duplicates windows
        or breaches the pop-out cap.
        """
        from ui.popout_window import PopoutChartWindow

        try:
            from data.popout_store import PopoutStore

            saved = PopoutStore.load_all()
        except Exception as exc:
            _LOG.warning("Pop-out restore failed: %s", exc)
            return
        open_keys = {
            (p.symbol.upper(), p.timeframe, p.mode) for p in self._popouts
        }
        for record in saved:
            if len(self._popouts) >= settings.MAX_POPOUTS:
                break
            key = (
                str(record["symbol"]).upper(),
                record["timeframe"],
                record["mode"],
            )
            if key in open_keys:
                continue
            try:
                popout = PopoutChartWindow(
                    symbol=record["symbol"],
                    timeframe=record["timeframe"],
                    mode=record["mode"],
                    extended_hours=record["ext_hours"],
                    host=self,
                    parent=self,
                )
                popout.attach()
                popout.apply_geometry(record["geometry"])
                popout.show()
                open_keys.add(key)
            except Exception as exc:
                _LOG.warning(
                    "Pop-out restore failed for %s: %s",
                    record.get("symbol"),
                    exc,
                )

    @property
    def primary_session(self) -> TickerSession | None:
        return self._primary_session

    def _set_primary_session(self, session: TickerSession | None) -> None:
        """Point the main chart at a session, rewiring the view signals."""
        if self._primary_session is session:
            return
        # Note: alarm_triggered is connected once per session at creation
        # (get_or_create_session) — it is window-global, not primary-only.
        old = self._primary_session
        if old is not None:
            for sig, slot in (
                (old.bar_updated, self._on_primary_bar_updated),
                (old.bars_refreshed, self._on_primary_bars_refreshed),
                (old.stream_health_changed,
                 self._on_primary_stream_health_changed),
                (old.footprint_updated,
                 self._on_primary_footprint_updated),
            ):
                try:
                    sig.disconnect(slot)
                except (RuntimeError, TypeError):
                    pass
        self._primary_session = session
        if old is not None:
            self.chart_panel.unbind_d37_session(old)
            self.chart_panel.unbind_d38_session(old)
        if session is not None:
            session.bar_updated.connect(self._on_primary_bar_updated)
            session.bars_refreshed.connect(self._on_primary_bars_refreshed)
            session.stream_health_changed.connect(
                self._on_primary_stream_health_changed
            )
            # D36: footprint data changed → re-render the footprint layer.
            session.footprint_updated.connect(
                self._on_primary_footprint_updated)
            # D37: heatmap/auction/imbalance UI binds to the primary session.
            self.chart_panel.bind_d37_session(session)
            # D38: event markers bind to the primary session (38b.2). The
            # shared yfinance source feeds the async refresh.
            self.chart_panel.bind_d38_session(session, self.yf_event_source)
            # D37: the depth toggle defaults ON — sync the feed now (the
            # toggle only emits on user interaction).
            if self.chart_panel.depth_enabled:
                session.ensure_depth_subscribed()

    def _on_depth_toggled(self, enabled: bool) -> None:
        """Depth heatmap toggle → refcounted session feed."""
        session = self.primary_session
        if session is None:
            return
        if enabled:
            session.ensure_depth_subscribed()
        else:
            session.release_depth()

    def _on_primary_bar_updated(self, bar: Bar, is_new_candle: bool) -> None:
        if bar.timeframe != self._current_tf:
            return
        self.chart_panel.update_last_bar(bar, is_new_candle)

    def _on_primary_bars_refreshed(self, timeframe: str, bars: list) -> None:
        if timeframe != self._current_tf:
            return
        self.chart_panel.update_chart(bars)
        # D36: keep footprint in step with the new bar set.
        if self.primary_session is not None and self.primary_session.fp_enabled:
            self.primary_session.footprint_resync(timeframe)

    def _on_fp_toggled(self, enabled: bool, style: str, metric: str) -> None:
        """Footprint control → session enable/disable + style/metric."""
        if self.primary_session is None:
            return
        if enabled:
            self.primary_session.footprint_enable(style=style, metric=metric)
            self.primary_session.footprint_resync()
        else:
            self.primary_session.footprint_disable()

    def _on_fp_viewport(self, first_ts: float, last_ts: float) -> None:
        """Scroll → lazy-fill bars lacking footprint data (bounded)."""
        if self.primary_session is None or not self.primary_session.fp_enabled:
            return
        self.primary_session.sync_footprint_viewport(first_ts, last_ts)

    def _on_primary_footprint_updated(self, timeframe: str) -> None:
        # D36: pull the snapshot from the session and re-render footprint.
        if timeframe != self._current_tf:
            return
        session = self._primary_session
        if session is None:
            return
        self.chart_panel.refresh_footprint(session.footprint_snapshot(timeframe))

    def _on_primary_stream_health_changed(self) -> None:
        self._update_stream_badge()

    # Facade properties: the chart data-plane attributes that tests and
    # legacy call sites read. They delegate to the primary session (the
    # session backing the main chart's current symbol), falling back to the
    # _current_symbol session when the primary isn't wired yet (tests set
    # _current_symbol directly).
    def _session_for_facade(self) -> TickerSession | None:
        s = self._primary_session
        if s is None and self._current_symbol:
            s = self._sessions.get(self._current_symbol.upper())
        return s

    @property
    def _aggregator(self) -> BarAggregator | None:
        s = self._session_for_facade()
        return s.aggregator_for(self._current_tf) if s else None

    @property
    def _rt_req_id(self) -> int | None:
        s = self._session_for_facade()
        return s.rt_req_id if s else None

    @_rt_req_id.setter
    def _rt_req_id(self, value: int | None) -> None:
        # Legacy direct assignment (tests, teardown paths). Routes into the
        # primary session without touching the routing table — subscribe-time
        # registration is the table's only writer.
        if self._primary_session is not None:
            self._primary_session._rt_req_id = value

    @property
    def _last_chart_price(self) -> float | None:
        s = self._session_for_facade()
        return s.last_chart_price if s else None

    @_last_chart_price.setter
    def _last_chart_price(self, value: float | None) -> None:
        self.get_or_create_session(self._current_symbol).last_chart_price = value

    @property
    def _current_alarms(self) -> list:
        s = self._session_for_facade()
        return s.alarms if s is not None else []

    @_current_alarms.setter
    def _current_alarms(self, value: list) -> None:
        self.get_or_create_session(self._current_symbol).set_alarms(value)

    @property
    def _stream_health(self) -> StreamHealth | None:
        s = self._session_for_facade()
        return s.stream_health if s is not None else None

    @property
    def _rt_seen(self) -> bool:
        # D27.1 guard: True once a realtime bar was observed since load.
        s = self._session_for_facade()
        return s._rt_seen if s is not None else False

    @_rt_seen.setter
    def _rt_seen(self, value: bool) -> None:
        if self._primary_session is not None:
            self._primary_session._rt_seen = value

    # D28.2 history-wave facades (tests read these; the state lives on the
    # session). Setters route into the current symbol's session.
    @property
    def _history_req_ids(self) -> set[int]:
        s = self._session_for_facade()
        return s._history_req_ids if s is not None else set()

    @property
    def _pending_bars(self) -> list:
        s = self._session_for_facade()
        return s._pending_bars if s is not None else []

    @_pending_bars.setter
    def _pending_bars(self, value: list) -> None:
        s = self._session_for_facade()
        if s is not None:
            s._pending_bars = value

    @property
    def _history_wave_timer(self):
        s = self._session_for_facade()
        return s._history_wave_timer if s is not None else None

    @property
    def _history_generation(self) -> int:
        s = self._session_for_facade()
        return s._history_generation if s is not None else 0

    @_history_generation.setter
    def _history_generation(self, value: int) -> None:
        s = self._session_for_facade()
        if s is not None:
            s._history_generation = value

    @property
    def _backfill_failed_req_ids(self) -> set[int]:
        s = self._session_for_facade()
        return s._backfill_failed_req_ids if s is not None else set()

    def _history_event_accepted(self, req_id: int) -> bool:
        """Test seam: True only for a reqId in the current wave generation."""
        s = self._session_for_facade()
        return s._history_event_accepted(req_id) if s is not None else False

    @property
    def _current_studies(self) -> list[dict]:
        s = self._session_for_facade()
        return s.studies if s is not None else []

    @_current_studies.setter
    def _current_studies(self, value: list[dict]) -> None:
        s = self._session_for_facade()
        if s is not None:
            s.set_studies(value)

    @property
    def _prime_req_id(self) -> int | None:
        s = self._session_for_facade()
        return s._prime_req_id if s is not None else None

    @_prime_req_id.setter
    def _prime_req_id(self, value: int | None) -> None:
        s = self._session_for_facade()
        if s is not None:
            s._prime_req_id = value

    # ── Connection slots ──────────────────────────────────────────────────────

    def _update_conn_badge(self):
        """D26.5: badge text/color derive from the verified port + account.

        D40: while TWS is gone the badge shows the paused monitoring
        state (owner-approved wording), never a green "connected".
        """
        summary = getattr(self, "_account_summary", {}) or {}
        text, color = conn_badge_text(
            getattr(self, "_account_id", None),
            summary.get("AccountType"),
            monitoring_paused=self._tws_paused,
        )
        self.conn_badge.setText(text)
        self.conn_badge.setStyleSheet(f"color: {color};")

    def _on_connected(self):
        self._ibkr_connected = True
        # D40.3: capture the resume-before-clear — a TWS-gone pause needs
        # the reconcile + gap report below; a transient drop must not
        # get them (40.4).
        _resuming_from_pause = self._tws_paused
        self._tws_paused = False
        self.watchlist_panel.set_add_enabled(True)
        # D39.1: search box enabled on connect.
        self.watchlist_panel.set_search_enabled(True)
        self._symbol_search.set_connected(True)
        self._update_conn_badge()
        self.load_btn.setEnabled(True)
        self.status_bar.showMessage(f"Connected — IBKR port {settings.IBKR_PORT}")
        self._restore_watchlist()
        self._replay_subscriptions()
        # D36/A4: restart footprint backfill waves stranded by the drop.
        for session in list(self._sessions.values()):
            session.on_fp_reconnect()
        self._subscribe_account_data()
        # D24.9: restore pop-outs after connect (lazy attach, cache-first).
        self._restore_popouts()
        # D40.3: resume from a TWS-gone pause — the D27 replay above
        # already re-issued subscriptions. When resuming from pause,
        # reconcile FIRST so sessions created for active alarms take the
        # staged path (last_chart_price=None while _paused is still True —
        # no phantom triggers on resume), then resume_all() clears pause
        # flags, re-seeds every session (including staged ones) with the
        # first-tick-no-eval guard, and finishes pending subscribes.
        # (Reviewer B1, D40: the old order let reconcile-created sessions
        # take the normal path with a stale cache seed and phantom-fire.)
        # Gap accounting is surfaced last so it stays visible.
        if _resuming_from_pause:
            self.alarm_monitor.reconcile()
            _gaps = self.alarm_monitor.resume_all()
        else:
            # D25: reconcile headless alarm monitors on (re)connect.
            self.alarm_monitor.reconcile()
            _gaps = []
        if _gaps:
            self.status_bar.showMessage(
                self.alarm_monitor.format_gap_report(_gaps), 30000
            )

    def _subscribe_account_data(self):
        """D27.6: subscribe positions + account summary on (re)connect.

        The whole signal chain (EWrapper -> bridge -> panel) already exists;
        only the subscription calls were missing, leaving the portfolio
        panel permanently empty.
        """
        try:
            self.ib_client.reqPositions()
        except Exception as exc:  # pragma: no cover - transport-level
            _LOG.warning("reqPositions failed: %s", exc)
        try:
            req_id = id_manager.get_id()
            self.ib_client.reqAccountSummary(
                req_id,
                "All",
                "AccountType,AvailableFunds,BuyingPower,"
                "TotalCashValue,NetLiquidation",
            )
            self._account_summary_req_id = req_id
        except Exception as exc:  # pragma: no cover - transport-level
            _LOG.warning("reqAccountSummary failed: %s", exc)
        self._account_subscribed = True
        self.portfolio_panel.set_account_unavailable(False)

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

        D39.1: search-result selections share the bounded lookup; they are
        keyed in ``_pending_search_select`` and branch to chart loading.
        """
        if request_id in self._pending_search_select:
            self._on_search_sample_validated(request_id, ok, reason)
            return
        self._on_watchlist_symbol_validated(request_id, symbol, ok, reason)

    # ── Symbol search (D39.1) ────────────────────────────────────────────

    def _on_search_finished(
        self, req_id: int, pattern: str, ok: bool, samples_or_reason
    ) -> None:
        """Show search results, or a clear failure state (never silent)."""
        if ok:
            # The box may have been cleared while the request was in flight —
            # never pop results over an empty query.
            if not self.watchlist_panel.search_box.text().strip():
                self.watchlist_panel.clear_search_results()
                return
            self.watchlist_panel.show_search_results(samples_or_reason or [])
        else:
            self.watchlist_panel.clear_search_results()
            reason = samples_or_reason or "search failed"
            self.status_bar.showMessage(f"Symbol search: {reason}.", 4000)

    def _on_search_sample_selected(self, desc) -> None:
        """A search result was picked → resolve its contract, then chart it.

        Contract resolution reuses the bounded D22 ``ContractLookupService``
        (exactly-once, 5s cap, cancelled on disconnect).
        """
        contract = getattr(desc, "contract", None)
        if contract is None:
            self.status_bar.showMessage(
                "Symbol search: no contract on the selected result.", 4000)
            return
        symbol = (getattr(contract, "symbol", "") or "").upper()
        if not symbol:
            self.status_bar.showMessage(
                "Symbol search: empty symbol on the selected result.", 4000)
            return
        if not self._ibkr_connected:
            self.status_bar.showMessage(
                "Not connected to IBKR — cannot resolve the selection.", 4000)
            return
        req_id = self._contract_lookup.request(symbol, contract)
        self._pending_search_select[req_id] = desc
        self.status_bar.showMessage(f"Resolving {symbol}…", 3000)

    def _on_search_sample_validated(
        self, request_id: int, ok: bool, reason: str
    ) -> None:
        """Apply a resolved search selection: load its chart (AC-D39.1)."""
        desc = self._pending_search_select.pop(request_id, None)
        if desc is None:
            return  # late / unknown — never mutate state
        contract = getattr(desc, "contract", None)
        symbol = (getattr(contract, "symbol", "") or "").upper()
        if not ok or not symbol:
            self.status_bar.showMessage(
                f"Could not resolve {symbol or 'selection'}: "
                f"{reason or 'contract not found'}",
                5000,
            )
            return
        if not self._ibkr_connected:
            self.status_bar.showMessage(
                f"Could not load {symbol}: disconnected.", 5000)
            return
        self.load_chart(symbol)
        self.status_bar.showMessage(f"Loaded {symbol}.", 3000)

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

    def _rebind_depth_req_id(self, new_req_id: int) -> None:
        """D27.3: point DOM routing at the replayed subscription's reqId."""
        self._depth_req_id = new_req_id

    def _replay_subscriptions(self):
        """Re-issue live subscriptions after reconnection (D27.3).

        Chart RT bars, DOM depth, session depth feeds, and S0 generic-tick
        subscriptions replay through the subscription registry, which
        rebinds the new reqIds into the routing state.
        Watchlist market-data is re-issued by ``_restore_watchlist``'s
        clear+re-add path (pinned by AC-D22.7.2), so MARKET_DATA stays
        excluded here — replaying it too would double-subscribe every row.

        D28.1: the replay is all-or-nothing under pacing pressure
        (SubscriptionManager.replay_all raises PacingExceeded before any
        reissue); defer the whole replay via singleShot — never sleep.
        """
        try:
            self.sub_manager.replay_all(
                include_types={RT_BARS, DEPTH, DEPTH_HEATMAP, S0_TICKS})
        except PacingExceeded as e:
            self.status_bar.showMessage(
                f"Subscription replay pacing-limited, "
                f"retrying in {e.wait_seconds:.0f}s…",
                15000,
            )
            QTimer.singleShot(
                int(e.wait_seconds * 1000), self._replay_subscriptions
            )

    # ── Stream health (D27.4) ───────────────────────────────────────────────

    def _update_stream_badge(self) -> None:
        """Refresh the persistent stream-health indicator (D27.4)."""
        h = self._stream_health
        if h is None:
            # No primary session (e.g. headless monitor only) — nothing to show.
            return
        if h.state == StreamState.LIVE:
            text, color = "● Stream live", "#34d399"
        elif h.state == StreamState.FAILED:
            code = f" [{h.fail_code}]" if h.fail_code is not None else ""
            text, color = f"● Stream failed{code}", "#f87171"
        else:
            text, color = "○ Stream awaiting first bar", "#fbbf24"
        self.stream_badge.setText(text)
        self.stream_badge.setStyleSheet(f"color: {color};")

    def _on_rt_stream_error(self, session: TickerSession, code: int,
                            message: str) -> None:
        """D27.4: the live RT subscription failed — persist + backoff retry."""
        session.stream_health.mark_failed(code, message)
        _LOG.warning("Realtime stream failed [%s]: %s", code, message)
        # Badge + retry scheduling are primary-chart concerns; a background
        # session just records the FAILED health for its views.
        if session is self._primary_session:
            self._update_stream_badge()
            self.status_bar.showMessage(
                f"Realtime stream failed [{code}]: {message} — retrying…",
                15000,
            )
            self._schedule_rt_retry()
        else:
            self.status_bar.showMessage(
                f"{session.symbol} realtime stream failed [{code}]: {message}",
                15000,
            )

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
        session = self.get_or_create_session(symbol)
        # D28.2: the session drops the failed subscription and starts a fresh
        # one (sub_manager re-registration + reqId routing inside). Fix-B is
        # preserved: the retry path never resets the backoff counter.
        # D28.1: pacing-limited retry defers via singleShot — never sleep.
        try:
            session.resubscribe_rt()
        except PacingExceeded as e:
            self.status_bar.showMessage(
                f"Realtime pacing-limited, retrying in {e.wait_seconds:.0f}s…",
                15000,
            )
            QTimer.singleShot(
                int(e.wait_seconds * 1000), self._retry_rt_subscribe
            )
            return
        self._update_stream_badge()
        self.status_bar.showMessage(
            f"{symbol} — realtime stream re-subscribed, awaiting first bar…",
            8000,
        )

    def _on_disconnected(self):
        self._ibkr_connected = False
        # D27.6: the transport drop kills the server-side account subs.
        self._account_subscribed = False
        self.portfolio_panel.set_account_unavailable(True)
        self.watchlist_panel.set_add_enabled(False)
        # D39.1: search disabled while disconnected (box greys out).
        self.watchlist_panel.set_search_enabled(False)
        self._symbol_search.set_connected(False)
        self._pending_search_select.clear()
        # D22 Phase 4: a transport drop invalidates every in-flight contract
        # lookup so none can resolve an add once (re)connected.
        self._contract_lookup.cancel_all()
        # D40: classify the drop. TWS-gone (nightly close) → the paused
        # monitoring state (badge + no evaluation); anything else keeps
        # the existing red "Disconnected" badge and fast D27 path.
        if self.ib_client.last_disconnect_class == DisconnectClass.TWS_GONE:
            self._enter_tws_paused_state()
        else:
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
        # D28.2: strand every session's in-flight wave on disconnect.
        stranded_any = False
        for session in list(self._sessions.values()):
            # D36/A4: a transport drop strands every in-flight footprint
            # tick request (the NO_VALID_ID error cannot be routed back) —
            # reset the wave state now; the reconnect restarts it.
            session.on_fp_disconnect()
            if self._finalize_stranded_history_wave(
                session, reason="Disconnected from IBKR"
            ):
                stranded_any = True
        if not stranded_any and not self._tws_paused:
            # D40: while TWS-gone the paused message (set by
            # _enter_tws_paused_state above) stays the visible cue.
            self.status_bar.showMessage("Disconnected from IBKR")
        # D22-08: an add that was mid-flight can never complete now — surface the
        # rejection last so it is the visible cue (AC-D22.8.4). Nothing is added,
        # subscribed or persisted.
        self._reject_pending_watchlist_adds()

    def _enter_tws_paused_state(self):
        """D40.2: TWS is gone — enter the paused-monitoring state.

        The AlarmMonitor marks every alarmed symbol paused (no
        evaluation, no triggers) and records pause-start per symbol for
        gap accounting. The connection badge shows the owner-approved
        wording — never a green "connected" appearance while paused.
        The client's backoff loop keeps running so the morning TWS
        login reconnects without an app restart.
        """
        self._tws_paused = True
        self.alarm_monitor.pause_all()
        self._update_conn_badge()
        self.status_bar.showMessage(
            "Monitoring paused — TWS disconnected", 15000
        )

    def _finalize_stranded_history_wave(
        self, session: TickerSession, reason: str = ""
    ) -> bool:
        """Drop and finalise an in-flight backfill wave that can no longer complete.

        Used by ``_on_disconnected`` and the wave watchdog. Returns True when a
        wave was actually stranded and finalised, False when there was nothing to
        do — so callers never run ``_finalize_history_wave`` twice and never
        fabricate a bar. Cancels every tracked reqId, advances the generation so
        late responses for pre-drop reqIds are rejected, then finalises exactly
        once through ``_finalize_history_wave`` so AC-D16.4's shortfall is surfaced.
        """
        if not session._history_req_ids:
            return False
        session._cancel_history_requests()
        # Advance the generation: any late historical_bar / historical_data_end
        # for a pre-drop reqId now fails _history_event_accepted and can neither
        # accumulate bars nor finalise the wave a second time.
        session._history_generation += 1
        # Make the cause live for the shortfall diagnostics. Held on the
        # session (rather than passed as an argument) so ``_finalize_history_wave``
        # keeps its contract for normal-path callers and spies; the real
        # finaliser reads and clears it. Empty for a normal finalise.
        session._history_stranded_reason = reason
        self._finalize_history_wave(session)
        return True

    def _on_session_history_wave_timeout(self, session: TickerSession) -> None:
        """Watchdog: a wave that never yields historical_data_end is bounded.

        ESC-024: a request that never ends must not strand the wave forever. The
        stalled wave is finalised through the same path as a disconnect (cancel
        remaining reqIds, advance the generation, surface the shortfall once).
        """
        self._finalize_stranded_history_wave(
            session, reason="Historical backfill timed out"
        )

    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        if self._closing:
            return  # D28.5: teardown never touches cleared widgets.
        # D28.2: session-owned reqIds (RT, priming, wave members) route via
        # the table; the session owns the priming/wave/error semantics.
        session = self._session_for_req_id(reqId)
        if session is not None:
            if reqId == session.rt_req_id:
                # D27.4: an error on the live RT subscription marks the
                # stream failed (persistent indicator + backoff retry).
                self._on_rt_stream_error(
                    session, errorCode, errorString
                )
                return
            if reqId == session.depth_req_id:
                # D37: depth feed errors (354 = no entitlement) drive the
                # heatmap's explicit degradation state.
                session.on_depth_error(errorCode, errorString)
                self.status_bar.showMessage(
                    f"Depth [{errorCode}]: {errorString}", 8000
                )
                return
            session.on_historical_error(reqId, errorCode, errorString)
            self.status_bar.showMessage(
                f"Error [{errorCode}]: {errorString}", 8000
            )
            return
        if reqId == self._depth_req_id:
            # D37: DOM depth feed entitlement failure — explicit, not silent.
            self.status_bar.showMessage(
                f"DOM depth [{errorCode}]: {errorString} — "
                "depth subscription required.", 8000
            )
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

    def load_chart(self, symbol=None, timeframe=None, extended_hours=None):
        # D28.2: parameterised — pop-outs, the alarm monitor and tests call
        # with explicit values; the toolbar path falls back to the widgets.
        if symbol is None:
            symbol = self.symbol_input.text().strip().upper()
        else:
            symbol = symbol.strip().upper()
        if timeframe is None:
            timeframe = self.tf_combo.currentText()
        if extended_hours is None:
            extended_hours = self.ext_hours_btn.isChecked()
        if not symbol:
            self.status_bar.showMessage("Enter a symbol first.", 3000)
            return

        # D28.2: move the primary view to the symbol's session. The old
        # session loses the primary's RT hold and view; it tears down when
        # orphaned (no views and not monitored).
        new_session = self.get_or_create_session(symbol)
        old_session = self._primary_session
        if old_session is not None and old_session is not new_session:
            old_session.release_rt()
            old_session.detach_view(self.chart_panel)
        # D27.9: a previous load's priming is stale now — its late responses
        # are ignored (reqId no longer matches) and the timer is disarmed.
        # D28.2: priming lives on the session.
        new_session._prime_req_id = None
        new_session._prime_symbol = ""
        new_session._prime_timer.stop()

        self._current_symbol = symbol
        self._current_tf = timeframe

        # D16: cancel any in-flight backfill wave from the previous load and
        # advance the generation so its late responses cannot mix series.
        # D28.2: the wave lives on the session now.
        new_session._disarm_history_wave_watchdog()
        new_session._cancel_history_requests()
        new_session._history_generation += 1
        new_session._backfill_failed_req_ids = set()
        new_session._backfill_missing_spans = []
        new_session._wave_timeframe = timeframe

        # Wire the primary view to the session (idempotent on same session).
        self._set_primary_session(new_session)

        self.chart_panel.set_symbol(symbol)
        self.chart_panel.set_timeframe(timeframe)
        self.chart_panel.set_extended_hours(extended_hours)
        # D28.2: drawings + studies live on the session; the session fans out
        # to attached views (the primary chart here; 3c pop-outs read-only).
        new_session.reload_drawings()
        new_session.sync_drawings_to_views()
        # Keep the active draw group valid for the new symbol's groups.
        groups = DrawingStore.groups_for_symbol(symbol)
        if self._active_draw_group_id not in {g.id for g in groups}:
            self._active_draw_group_id = None
        self._apply_active_draw_group()
        self._refresh_drawing_groups(symbol)
        new_session.set_studies(self._load_studies_for_symbol(symbol))

        # D28.2: per-load data-plane reset lives on the session now (fresh
        # aggregator, rt_seen=False, alarms reloaded from the store).
        new_session.prepare_load(timeframe)
        self._refresh_alarm_badge()
        # Register the primary view (sync=False — the set_bars below drives
        # the initial render through bars_refreshed).
        new_session.attach_view(self.chart_panel, timeframe, sync=False)

        # Step 1: Show cached bars immediately (session-owned, capped).
        cached = BarCache.get_bars(symbol, timeframe)
        new_session.last_chart_price = cached[-1].close if cached else None
        new_session.set_bars(timeframe, cached)  # emits bars_refreshed → renders
        if cached:
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
        # D27.7: bar-level gap detection uses the load's ext-hours toggle so
        # the session window matches what the wave fetches.
        missing_spans = (
            find_missing_spans(
                cached_ts, now_ts, timeframe,
                ext_hours=extended_hours,
            ) if cached else []
        )
        plans = plan_requests(missing_spans, timeframe)
        new_session._backfill_missing_spans = list(missing_spans)

        contract = get_contract_for_symbol(symbol)

        if plans:
            # D28.3: the session issues chunks ~60 per wave and continues
            # across waves when the 600s historical budget is exhausted
            # (non-blocking — never sleeps, never storms TWS with 162s).
            new_session.queue_wave_plans(
                plans, contract, timeframe, extended_hours,
            )
            self.status_bar.showMessage(
                f"{symbol} — backfilling {len(plans)} historical chunk(s)…"
            )
        elif not cached:
            # Empty cache: preserve the configured-window single-request path
            # (endDateTime="" = up to now) as a one-plan wave.
            cfg = TIMEFRAME_CONFIG.get(timeframe, TIMEFRAME_CONFIG["5 mins"])
            new_session.queue_wave_plans(
                [RequestPlan(
                    endDateTime="",
                    duration=cfg["duration"],
                    bar_size=cfg["bar_size"],
                    span_start_ts=0,
                    span_end_ts=now_ts,
                )],
                contract, timeframe, extended_hours,
            )
            self.status_bar.showMessage(
                f"Requesting {symbol} [{timeframe}]…"
            )
        else:
            # The cache already reaches now: no redundant request is issued.
            self.status_bar.showMessage(
                f"{symbol} — {len(cached)} cached bars. Cache current."
            )

        # ESC-024: bound the wave — a request that never yields an end marker
        # must not strand the chart indefinitely.
        if new_session._history_req_ids:
            new_session._arm_history_wave_watchdog()

        # Step 3: prime the aggregator, then attach the live feed.
        # D27.9: replay trailing 5-sec history through the fresh aggregator
        # before the live feed attaches, so the forming candle's OHLCV isn't
        # fabricated from the first live tick. Attaches immediately when
        # there is nothing to prime (period boundary / 5-sec timeframe).
        # D28.2: priming lives on the session now.
        if not new_session.prime_aggregator(
            contract, timeframe, self._now_ts(), extended_hours
        ):
            self._attach_live_feed(symbol, contract)

    def _attach_live_feed(self, symbol: str, contract) -> None:
        """Start the real-time bar stream (+ DOM). Step 3 of load_chart."""
        # D28.2: the session owns the RT subscription (refcounted). The
        # sub_manager type-tagged registration, reqId routing table, and
        # stream-health transition all happen inside the session.
        # D28.1: pacing-limited subscribes defer via singleShot — never sleep.
        session = self.get_or_create_session(symbol)
        try:
            session.ensure_rt_subscribed()
        except PacingExceeded as e:
            self.status_bar.showMessage(
                f"Realtime pacing-limited, retrying in {e.wait_seconds:.0f}s…",
                15000,
            )
            QTimer.singleShot(
                int(e.wait_seconds * 1000),
                lambda: self._retry_attach_live_feed(symbol, contract),
            )
            return
        # D27.4: new subscription -> awaiting first bar; disarm any retry
        # timer left over from a previous load/failure.
        self._rt_retry_timer.stop()
        self._update_stream_badge()

        # DOM subscription (only if DOM panel is visible)
        if self.dom_btn.isChecked():
            self._subscribe_dom()

    def _retry_attach_live_feed(self, symbol: str, contract) -> None:
        """D28.1: pacing-deferred live-feed attach. Skips if the user moved on
        to another symbol while the retry was pending."""
        if self._current_symbol != symbol:
            return
        self._attach_live_feed(symbol, contract)


    def _attach_live_feed_if_current(self, session: TickerSession) -> None:
        """Attach the live feed for the primed session if still current."""
        if session.symbol != self._current_symbol:
            return
        self._attach_live_feed(
            session.symbol, get_contract_for_symbol(session.symbol)
        )

    def _now_ts(self) -> int:
        """Wall-clock epoch seconds; a seam for deterministic load-path tests."""
        return int(time.time())

    # ── Drawing slots ─────────────────────────────────────────────────────────

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
        # D28.2: the main chart is the sole writer of drawings; the session
        # fans the new state out to all attached views (3c pop-outs read-only).
        drawing_id = DrawingStore.create_drawing(drawing)
        drawing.id = drawing_id
        session = self._session_for_facade()
        if session is not None:
            session.reload_drawings()
            session.sync_drawings_to_views()
        self.status_bar.showMessage(
            f"Drawing added ({drawing.kind}) on {drawing.symbol}.", 3000
        )

    def _on_drawing_updated(self, drawing_id: int, payload: dict, color: str):
        # D27.10: persist the edited colour alongside the payload so a reload
        # shows the edited colour (AC-D27.10).
        DrawingStore.update_drawing(drawing_id, payload, color=color)
        session = self._session_for_facade()
        if session is not None:
            session.reload_drawings()
            session.sync_drawings_to_views()

    def _on_drawing_deleted(self, drawing_id: int):
        DrawingStore.delete_drawing(drawing_id)
        session = self._session_for_facade()
        if session is not None:
            session.reload_drawings()
            session.sync_drawings_to_views()
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
        session = self._session_for_facade()
        if session is not None:
            session.reload_drawings()
            session.sync_drawings_to_views()
        self._refresh_drawing_groups(self._current_symbol)

    # ── Historical data slots ─────────────────────────────────────────────────

    def _on_historical_bar(self, reqId: int, bar):
        if self._closing:
            return  # D28.5: teardown never touches cleared widgets.
        # D28.2: route by reqId → session (priming vs wave handled inside).
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_historical_bar(reqId, bar)

    def _on_historical_data_end(self, reqId: int):
        if self._closing:
            return  # D28.5
        # D28.2: route by reqId → session.
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_historical_data_end(reqId)

    # ── D36 footprint slots ─────────────────────────────────────────────

    def _on_fp_ticks_bid_ask(self, reqId: int, ticks, done: bool):
        if self._closing:
            return  # D28.5
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_fp_ticks_bid_ask(reqId, ticks, done)

    def _on_fp_ticks_last(self, reqId: int, ticks, done: bool):
        if self._closing:
            return  # D28.5
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_fp_ticks_last(reqId, ticks, done)

    # ── D37 S0 routing ───────────────────────────────────────────────

    def _on_session_tick_price(self, reqId: int, tickType: int,
                               price: float) -> None:
        if self._closing:
            return
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_tick_price(reqId, tickType, price)

    def _on_session_tick_size(self, reqId: int, tickType: int,
                              size: int) -> None:
        if self._closing:
            return
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_tick_size(reqId, tickType, size)

    def _on_s0_tick_generic(self, reqId: int, tickType: int,
                            value: float) -> None:
        if self._closing:
            return
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_s0_tick_generic(reqId, tickType, value)

    def _on_s0_tick_string(self, reqId: int, tickType: int,
                           value: str) -> None:
        if self._closing:
            return
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_s0_tick_string(reqId, tickType, value)

    def _on_s0_tick_news(self, reqId: int, timeStamp: int, providerCode: str,
                         articleId: str, headline: str) -> None:
        if self._closing:
            return
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        session.on_s0_tick_news(reqId, timeStamp, providerCode, articleId,
                                headline)

    def _on_session_wave_complete(self, session: TickerSession) -> None:
        """A session's backfill wave emptied — finalize (persist + render)."""
        # In 3b only the primary session backfills; a non-primary completion
        # still persists (its data is real) but doesn't drive the chart.
        self._finalize_history_wave(session)

    def _on_session_prime_complete(self, session: TickerSession) -> None:
        """A session's priming finished (or failed open) — attach live feed."""
        if session.symbol == self._current_symbol:
            self._attach_live_feed_if_current(session)

    def _on_session_prime_timeout(self, session: TickerSession) -> None:
        # Backstop: priming never answered — fail open to the live feed.
        session._prime_req_id = None
        session._prime_timer.stop()
        self._on_session_prime_complete(session)

    def _finalize_history_wave(self, session: TickerSession | None = None) -> None:
        """Persist, re-read and render once the last backfill request ends.

        If the wave was *stranded* (watchdog timeout or transport disconnect),
        ``_finalize_stranded_history_wave`` has set the session's
        ``_history_stranded_reason``. That cause is purely diagnostic: it
        fabricates no bar and changes no behaviour — it is appended to the
        AC-D16.4 shortfall line and the WARNING record so a timeout and a
        disconnect are distinguishable. For a normal (non-stranded) finalise
        the reason is empty and the wording is unchanged.

        The session defaults to the current symbol's session (test seam).
        """
        if session is None:
            session = self._session_for_facade()
            if session is None:
                return
        session._disarm_history_wave_watchdog()
        new_count = len(session._pending_bars)
        if session._pending_bars:
            BarCache.save_bars(session._pending_bars)
        timeframe = session._wave_timeframe or self._current_tf
        # D28.4: keep the on-disk cache bounded per (symbol, timeframe).
        BarCache.prune(session.symbol, timeframe)
        all_bars = BarCache.get_bars(session.symbol, timeframe)
        # D28.2: session-owned bars; the emit drives the view render.
        session.set_bars(timeframe, all_bars)
        # D27.1: _last_chart_price must never move backward. If realtime bars
        # were observed since load, the live price is newer than the historical
        # close — rewinding would fabricate a discontinuous (prev, curr) pair
        # and phantom-fire alarms. Skip the assignment in that case.
        if not session._rt_seen:
            session.last_chart_price = (
                all_bars[-1].close if all_bars else None
            )
        # D27.1 (second clause): update_chart is a full refresh that wipes the
        # live forming candle appended by update_last_bar. Re-apply the
        # aggregator's forming bar so the live candle survives finalize.
        # Primary-chart only: background sessions have no live forming bar
        # on the main chart.
        if session is self._primary_session:
            agg = session.aggregator_for(timeframe)
            forming = agg.current_bar() if agg is not None else None
            if forming is not None:
                if all_bars:
                    self.chart_panel.update_last_bar(forming, False)
                else:
                    # No history at all: the forming bar is the only bar.
                    self.chart_panel.update_chart([forming])
        session._pending_bars = []

        # Read and clear the stranded-wave cause (diagnostic suffix only).
        reason = session._history_stranded_reason
        session._history_stranded_reason = ""
        cause = f" [{reason}]" if reason else ""

        missing_days = self._missing_backfill_trading_days(session, all_bars)
        failed_count = len(session._backfill_failed_req_ids)
        if missing_days:
            preview = ", ".join(d.isoformat() for d in missing_days[:5])
            self.status_bar.showMessage(
                f"{session.symbol} — backfill incomplete: "
                f"{len(missing_days)} trading day(s) still missing ({preview})."
                f"{cause}",
                10000,
            )
            _LOG.warning(
                "Historical backfill shortfall for %s [%s]: %s%s",
                session.symbol,
                timeframe,
                [d.isoformat() for d in missing_days],
                cause,
            )
        elif failed_count:
            self.status_bar.showMessage(
                f"{session.symbol} — {failed_count} historical request(s) "
                f"failed; chart may be incomplete.{cause}",
                10000,
            )
            _LOG.warning(
                "Historical backfill failed requests for %s [%s]: %s%s",
                session.symbol,
                timeframe,
                sorted(session._backfill_failed_req_ids),
                cause,
            )
        else:
            # D27.4: never declare "live" unconditionally — report the
            # actual stream-health state (usually "awaiting first bar" here;
            # the badge flips to live when the first bar arrives).
            stream_note = session.stream_health.describe()
            self.status_bar.showMessage(
                f"{session.symbol} — {len(all_bars)} bars "
                f"({new_count} new). Stream {stream_note}{cause}."
            )

    def _missing_backfill_trading_days(
        self, session: TickerSession, bars
    ) -> list:
        """Trading days the completed wave left empty (no bar fabricated)."""
        if not session._backfill_missing_spans:
            return []
        present_days = {
            datetime.fromtimestamp(b.ts, tz=_EASTERN).date() for b in bars
        }
        missing = []
        for span in session._backfill_missing_spans:
            for day in trading_days(span.start_ts, span.end_ts):
                if day not in present_days:
                    missing.append(day)
        return missing

    # ── Real-time bar slot ────────────────────────────────────────────────────

    def _on_realtime_bar(self, reqId: int, time: int, o: float, h: float,
                         l: float, c: float, vol: float, wap: float, count: int):
        if self._closing:
            return  # D28.5: teardown never touches cleared widgets.
        # D28.2: route by reqId → TickerSession. Unknown reqIds (stale,
        # pre-extraction, or foreign) are ignored.
        session = self._session_for_req_id(reqId)
        if session is None:
            return
        was_live = session.stream_health.is_live
        session.on_realtime_bar(reqId, time, o, h, l, c, vol)
        if not was_live and session.stream_health.is_live:
            # D27.4: first bar on the subscription -> the stream is live.
            self._rt_retry_timer.stop()
            self._update_stream_badge()

    def _on_aggregated_bar(self, bar: Bar, is_new_candle: bool):
        """Legacy entry point: route into the current symbol's session.

        Production flow goes aggregator -> session._on_aggregated_bar
        directly; this router exists for tests driving the window.
        """
        self.get_or_create_session(self._current_symbol)._on_aggregated_bar(
            bar, is_new_candle
        )

    def _record_symbol_price(self, symbol: str | None, price: float) -> None:
        """D27.5: record a last price in the central symbol -> price map."""
        if symbol and price and price > 0:
            self._symbol_last_prices[symbol.upper()] = float(price)

    def _on_session_alarm_triggered(self, symbol: str, triggered: list) -> None:
        """Toast + sound exactly once per trigger event (A57).

        The badge reflects the main-chart symbol only (FR-4.3); a trigger
        for a background symbol still toasts + sounds.
        """
        lines = [self._alarm_toast_line(a) for a in triggered]
        self.toast.show_message(f"Alarm: {symbol} @ " + ", ".join(lines))
        if any(a.sound for a in triggered):
            self.sound_service.play_alarm()
        if symbol == self._current_symbol:
            self._refresh_alarm_badge()

    @staticmethod
    def _alarm_toast_line(alarm) -> str:
        """D39: burst alarms toast with their tape attribution and z-score."""
        if getattr(alarm, "kind", "price") == "volume_burst":
            text = "Volume burst"
            proxy_label = (alarm.params or {}).get("proxy_label")
            if proxy_label:
                text += f" on {proxy_label}"
            z = getattr(alarm, "trigger_z", None)
            if z is not None:
                text += f" (z={z:.1f})"
            if alarm.note:
                text += f" ({alarm.note})"
            return text
        if alarm.note:
            return f"{alarm.price:.4f} ({alarm.note})"
        return f"{alarm.price:.4f}"

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
        # D28.2: the main chart is the sole writer of studies; the session
        # fans the new config out to all attached views (3c pop-outs).
        session = self._session_for_facade()
        if session is not None:
            session.set_studies(studies)
        if self._current_symbol:
            StudyStore.save(self._current_symbol, deepcopy(studies))
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
        # D25: alarm CRUD → reconcile headless monitors.
        self.alarm_monitor.on_alarm_changed()

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

    # ── D38 news digest (38a.2) ──────────────────────────────────────────

    def _on_news_digest_visibility(self, visible: bool) -> None:
        """Dock shown/hidden — open drives the backfill, close tears down.

        The toggleViewAction (menu / shortcut) and the dock's own close
        button both funnel through visibility.
        """
        dock = self.news_digest_dock
        if visible and not dock.is_digest_open():
            dock.open_digest()
        elif not visible and dock.is_digest_open():
            dock.close_digest()

    def _on_yfinance_events(self, symbol: str) -> None:
        """Background yfinance fetch finished — merge into the session."""
        session = self._sessions.get(symbol.upper())
        if session is not None:
            try:
                session.on_yfinance_refresh(symbol, self.yf_event_source)
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
                      side: int, price: float, size: int,
                      is_smart_depth: bool):
        """Handle incoming market-depth updates."""
        # is_smart_depth (10.51.1) is carried for D37's SMART-aggregated-row
        # disambiguation; the DOM path below is unchanged.
        if req_id == self._depth_req_id:
            symbol = self.depth_manager.on_update(req_id, position, operation, side, price, size)
            if symbol is None:
                return
            # Update last price for the ladder mid-row display
            if price > 0:
                self.active_trader.set_last_price(price)
            snapshot = self.depth_manager.snapshot(req_id)
            on_depth_callback(self.active_trader, snapshot)
            return
        # D37: session heatmap feeds (shared SMART subscriptions) route by
        # reqId to the owning session; the service owns the book model.
        session = self._session_for_req_id(req_id)
        if session is not None:
            session.on_depth_update(position, operation, side, price, size,
                                    is_smart_depth)

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

        # D28.1: orders no longer share the realtime-bar throttle (which could
        # sleep the GUI thread for up to 10 minutes). They get their own
        # token-bucket limiter; when empty the order defers via singleShot —
        # never blocks, never silently dropped.
        if not order_limiter.try_acquire():
            delay_ms = max(200, int(order_limiter.retry_delay_s() * 1000))
            msg = "Order pacing-limited, retrying…"
            self.status_bar.showMessage(msg, 4000)
            self.active_trader.order_entry.status_label.setText(msg)
            QTimer.singleShot(
                delay_ms,
                lambda: self._place_order(
                    contract=contract, symbol=symbol, action=action, qty=qty,
                    order_type=order_type, lmt_price=lmt_price,
                    stop_price=stop_price, target_price=target_price,
                ),
            )
            return

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
                           clientId: int, whyHeld: str, mktCapPrice):
        # mktCapPrice (10.51.1, None on old servers) is not consumed yet —
        # carried for the D26 safety layer's future use.
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
            # D27.5 drive-by: the call was missing these required args, so
            # every position update raised TypeError (masked until D27.6
            # subscribes reqPositions and updates actually flow).
            stop_loss=None,
            take_profit=None,
        )
        # D27.5: the position's OWN symbol price — never the chart's price.
        # Unknown symbol -> 0.0 (honest unknown), not a wrong symbol's price.
        position.market_price = self._symbol_last_prices.get(
            (position.symbol or "").upper(), 0.0
        )
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
            # D28.6: the stored 'option'/'future' must map to IBKR's
            # OPT/FUT secTypes — a bare .upper() yields the invalid
            # OPTION/FUTURE and the close order would be rejected.
            contract.secType = {"option": "OPT", "future": "FUT"}.get(
                contract_type, contract_type.upper())
            if local_symbol:
                contract.localSymbol = local_symbol
            if expiry:
                contract.lastTradeDateOrContractMonth = expiry
            if strike is not None:
                contract.strike = strike
            if right:
                contract.right = right
            contract.multiplier = str(int(multiplier)) if multiplier != 1.0 else ""

        # D28.1: close orders use the order-path token bucket, never the
        # realtime-bar throttle. Defer via singleShot when the bucket is empty.
        if not order_limiter.try_acquire():
            delay_ms = max(200, int(order_limiter.retry_delay_s() * 1000))
            self.status_bar.showMessage(
                "Close-order pacing-limited, retrying…", 4000
            )
            QTimer.singleShot(
                delay_ms, lambda: self._close_position_by_id(position_id)
            )
            return
        order_id = id_manager.get_id()
        order = order_registry.market_order(action, close_qty)
        self.ib_client.placeOrder(order_id, contract, order)
        self.status_bar.showMessage(
            f"Closing position {position_id}: {action} {close_qty} {symbol} @ MKT", 4000
        )

    #: D28.5: bound for joining the ibkr-reader thread at close.
    READER_JOIN_TIMEOUT_S = 5.0

    def closeEvent(self, event):
        # D28.5: idempotent — a second closeEvent after teardown is a no-op.
        if self._closing:
            event.accept()
            return
        self._closing = True
        # Explicit teardown order: persist prefs → cancel lookups → disarm
        # timers → cancel subs → disconnect → join reader → clear UI.
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
        # Cancel in-flight contract lookups so no stale result resolves
        # an add after the widgets are gone.
        try:
            self._contract_lookup.cancel_all()
        except Exception:
            pass
        # Disarm retry timers, then teardown every session (cancels RT +
        # wave, disarms watchdog, advances generation). Sessions stay
        # registered (torn down) so post-close test seams can still reach
        # them.
        try:
            self._rt_retry_timer.stop()
        except Exception:
            pass
        for session in list(self._sessions.values()):
            session._history_generation += 1
            session.teardown()
        self._primary_session = None
        # Cancel market depth subscription
        if self._depth_req_id is not None:
            self.depth_manager.cancel(self._depth_req_id)
            self._depth_req_id = None
        # Cancel all depth subscriptions
        self.depth_manager.cancel_all()
        # Cancel all realtime bar subscriptions across tracked symbols
        self.rt_manager.cancel_all()
        # Disconnect from IBKR, then join the reader thread with a timeout
        # so close never hangs on a wedged socket read.
        try:
            self.ib_client.disconnect()
        except Exception:
            pass
        reader = self._reader_thread
        if reader is not None and reader.is_alive():
            reader.join(timeout=self.READER_JOIN_TIMEOUT_S)
        # Clear watchlist panel
        self.watchlist_panel.clear()
        event.accept()
