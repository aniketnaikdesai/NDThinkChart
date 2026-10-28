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
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.contracts import get_contract_for_symbol
from ibkr.utils import parse_ibkr_date
from ibkr.id_manager import id_manager
from ibkr.pacing import PacingExceeded
from ibkr.subscription_manager import (
    RT_BARS,
    S0_TICKS,
    SubscriptionManager,
)
from ibkr.stream_health import StreamHealth, StreamState
from ui.chart_view import create_chart_view
from services.chart_model import ChartMode
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
    WATCHLIST_COLLAPSED_WIDTH,
    right_dock_max_width,
    plan_dock_widths,
    plan_watchlist_width,
)
from ui.studies_dialog import StudiesDialog, DEFAULT_STUDIES
from ui.alarm_dialog import AlarmDialog
from ui.drawing_groups_dialog import DrawingGroupsDialog
from ui.visual_conventions import apply_toolbar_stylesheet, set_button_active
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
    find_missing_spans, floor_bar_budget, plan_requests, present_days,
)
from services.time_collapse_service import is_daily_or_coarser
from services.market_calendar import trading_days
from services.contract_lookup_service import ContractLookupService
from services.md_line_guard import assess as md_assess

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


def chart_engine_failure_message(engine_name: str) -> str:
    """ESC-070: user-facing status text when the chart engine cannot start.

    Named in one place so the window's status bar and the visibility tests
    cannot drift on the wording; it always names the engine that failed.
    """
    return (
        f"Chart engine '{engine_name}' could not start — the chart is blank. "
        "See the log for details."
    )



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


def build_main_chart_view(tz_offset: float, editable: bool = True):
    """Create the main chart on the engine the seam resolves.

    ``ui.chart_view.create_chart_view`` is the single engine-selection
    authority: ``NDT_CHART_ENGINE`` first, then the persisted override, and
    anything other than ``"lwc"`` keeps pyqtgraph (the default). Its LWC
    branch is still the Phase-1a seam stub, so — exactly as
    ``ui.popout_window.popout_view`` does for pop-outs — the real LWC driver
    is re-hosted here when the factory resolves that engine. The pyqtgraph
    path is returned untouched.
    """
    view = create_chart_view(tz_offset=tz_offset, editable=editable)
    if getattr(view, "ENGINE_NAME", None) != "lwc":
        return view
    from ui.lwc_view import LwcChartView as LwcDriverView

    if isinstance(view, LwcDriverView):
        return view
    view.deleteLater()
    return LwcDriverView(tz_offset=tz_offset, editable=editable)


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
        # ESC-033: QPushButton.clicked emits clicked(bool checked=False); binding
        # that bool to load_chart's first parameter (``symbol``) made the button
        # call ``False.strip()``. Decouple the bool-emitting signal from the
        # D28.2 parameterised method (whose signature stays frozen for the
        # explicit-value callers: pop-outs, the alarm monitor, tests).
        self.load_btn.clicked.connect(lambda: self.load_chart())

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
        tb_layout.addWidget(self.ext_hours_btn)
        tb_layout.addWidget(self.tz_combo)
        tb_layout.addWidget(QLabel("|"))
        tb_layout.addWidget(QLabel("Draw:"))
        tb_layout.addWidget(self.draw_combo)
        tb_layout.addWidget(self.draw_set_combo)
        tb_layout.addWidget(self.draw_sets_btn)
        tb_layout.addWidget(self.draw_delete_btn)
        tb_layout.addStretch()
        tb_layout.addWidget(self.stream_badge)
        tb_layout.addWidget(self.conn_badge)

        # ── Central chart area ────────────────────────────────────────────────
        # Dynamic Eastern offset (DST-aware): EDT=14400, EST=18000
        self._tz_offset = _eastern_offset()
        self.chart_panel = build_main_chart_view(
            tz_offset=self._tz_offset, editable=True
        )
        # The LWC driver renders through its own offline host, created lazily
        # exactly as a pop-out does in ``attach``. Engine-less CI has no
        # Chromium: ``ensure_host`` raises, the view still syncs through its
        # bridge, and window start-up never depends on the host existing.
        #
        # ESC-070: start-up stays non-fatal, but a host that cannot start is
        # now VISIBLE — full traceback in the log, an explicit flag, and a
        # status-bar message once the bar exists below. Before this, a failed
        # engine left a blank canvas byte-identical to an empty chart.
        self.chart_engine_failed = False
        self._chart_engine_host = None
        _ensure_host = getattr(self.chart_panel, "ensure_host", None)
        if callable(_ensure_host):
            try:
                self._chart_engine_host = _ensure_host()
            except Exception:
                self.chart_engine_failed = True
                self._chart_engine_host = None
                _LOG.exception(
                    "Chart engine %r could not start — the chart will stay "
                    "blank.",
                    getattr(self.chart_panel, "ENGINE_NAME", "unknown"),
                )
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
        # D44: the collapse transition. When the body collapses/expands the
        # window swaps the dock's title-bar widget, relaxes/restores the
        # minimum widths and re-applies the dock widths — the
        # ``_sync_right_dock_collapse`` sequence. See
        # ``_on_watchlist_collapsed_changed``.
        self.watchlist_panel.collapsed_changed.connect(
            self._on_watchlist_collapsed_changed
        )

        # ── Single right dock: Portfolio-only (D41 / S6) ────────────────────
        # The Active Trader panel (DOM ladder + order-entry ticket), the
        # two-section container and the depth machinery are removed: the right
        # region is now ONE ``QDockWidget`` hosting the retained Portfolio panel
        # directly. Its title **and** objectName are ``"Portfolio"`` — the
        # region's stable title-keyed handle — and its title-bar widget IS the
        # panel's ``summary_label``, so exactly one label is visible and it is
        # the hide/show toggle (AC-D41.7 / AC-D21.13.1).
        self.portfolio_panel = ActivePortfolioPanel()
        self.right_dock = QDockWidget("Portfolio", self)
        self.right_dock.setObjectName("Portfolio")
        self.right_dock.setWidget(self.portfolio_panel)
        self.right_dock.setTitleBarWidget(self.portfolio_panel.summary_label)
        self.right_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        # D18 Phase 4: pin the region's minimum to the shared constant so
        # ``_apply_dock_widths`` can shrink it exactly to RIGHT_DOCK_MIN_WIDTH
        # and the panel's bounded content cannot raise it (AC-D18.4/AC-D18.6).
        self.right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        # D18 Phase 4: in-memory-only right-region width. Never persisted — no new
        # QSettings key (AC-D18.7 / A36), matching D10's volume-toggle precedent.
        self._right_dock_width = RIGHT_DOCK_MIN_WIDTH
        # D21.13/S6: the retained panel's hide/show state. With one section the
        # collapsed state IS the region-collapse state and the collapsed strip is
        # that single button.
        self._right_region_collapsed = False
        self._right_dock_collapsed_min_width = (
            self._compute_right_dock_collapsed_min_width()
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
        if self.chart_engine_failed:
            # ESC-070: the blank chart says why, instead of looking empty.
            self.status_bar.showMessage(
                chart_engine_failure_message(
                    getattr(self.chart_panel, "ENGINE_NAME", "unknown")
                ),
                0,
            )
        else:
            self.status_bar.showMessage("Connecting to IBKR…")

        # ── IBKR client ───────────────────────────────────────────────────────
        self.ib_client = IBApiClient()
        self.md_manager = MarketDataManager(self.ib_client)
        self.rt_manager = RealtimeBarsManager(self.ib_client)
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

        # Drawing overlay wiring — through the seam: the default engine's
        # controller proxies wrap its Qt overlay, and the LWC driver exposes
        # its session-facing surface (signals that engine does not carry are
        # simply absent, so wiring degrades quietly instead of raising).
        drawing = self._view_signal_source("drawing_controller", "drawing_overlay")
        if drawing is not None:
            for signal_name, slot in (
                ("created", self._on_drawing_created),
                ("updated", self._on_drawing_updated),
                ("deleted", self._on_drawing_deleted),
                ("selection_changed", self._on_drawing_selection_changed),
                # ESC-017: when the router clears the drawing tool (TR-4
                # zoom-cancels-draw, TR-17 symbol change) the overlay emits
                # mode_changed("cursor"); mirror it into the toolbar combo so
                # it never goes stale.
                ("mode_changed", self._on_drawing_tool_mode_changed),
            ):
                self._connect_view_signal(drawing, signal_name, slot)

        # AC-D3.9: the magnifier is refused while alarm placement is armed.
        zoom_refused = getattr(self.chart_panel, "zoom_refused", None)
        if zoom_refused is not None:
            zoom_refused.connect(
                lambda: self.status_bar.showMessage(
                    "Finish or cancel alarm placement before zooming", 4000
                )
            )

        # Alarm overlay wiring — same seam rule as drawings.
        aov = self._view_signal_source("alarm_controller", "alarm_overlay")
        if aov is not None:
            for signal_name, slot in (
                ("create_requested", self._on_alarm_create_requested),
                ("moved", self._on_alarm_moved),
                ("mute_toggled", self._on_alarm_mute_toggled),
                ("rearm_requested", self._on_alarm_rearm_requested),
                ("delete_requested", self._on_alarm_delete_requested),
            ):
                self._connect_view_signal(aov, signal_name, slot)

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
        b.tick_price.connect(self.watchlist_panel.on_tick_price)
        b.tick_size.connect(self.watchlist_panel.on_tick_size)
        # D41: TickerSession.on_tick_price/on_tick_size are gone, so price/size
        # ticks reach the watchlist only — there is no session relay to wire.
        # D37 S0 substrate: generic/string/news ticks, routed by reqId.
        b.realtime_bar.connect(self._on_realtime_bar)

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

        # D45: the Portfolio panel is view-only — its close/flatten/SL-TP
        # signals are no longer connected (the order path is gone).

        # State
        # D28.2: per-symbol sessions. Chart data-plane state (_rt_req_id,
        # _aggregator, _current_alarms, _last_chart_price, _rt_seen,
        # _stream_health) lives on TickerSession now; the properties below
        # delegate to the primary session for the current symbol.
        self._sessions: dict[str, TickerSession] = {}
        self._req_to_session: dict[int, TickerSession] = {}
        # P7-W1 (S-P7-2): cancel-tagged history reqIds whose session has
        # been torn down (popped from _sessions). Live sessions carry their
        # own tags; this set keeps teardown from erasing them — a 162 for
        # any of these is still a superseded ack (debug, no status bar).
        self._superseded_history_reqs: set[int] = set()
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
        # ESC-043: the account(s) the current account-summary subscription has
        # reported. `reqAccountSummary(..., "All", ...)` can stream several
        # accounts, so this is a set, not a single id. Empty means "not yet
        # known" — the position render/prune must not act on a guess.
        self._live_accounts: set[str] = set()
        # ESC-052: `_live_accounts` is only AUTHORITATIVE once the
        # account-summary stream has completed (`_on_account_summary_end`).
        # `position_end` (from reqPositions) and `accountSummaryEnd` (from
        # reqAccountSummary) are independent streams with no ordering
        # guarantee, so a non-empty-but-incomplete set must never drive the
        # destructive foreign-row prune — it may hold only SOME of the user's
        # accounts, and deleting the rest would destroy real rows.
        self._account_summary_complete: bool = False
        # ESC-052: whether `_on_position_end` has already loaded/rendered the
        # persisted rows this session — lets the summary completion re-render
        # so the panel converges on the now-complete live set.
        self._positions_rendered: bool = False
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

    # ── Engine seam helpers (D47 / Q-10) ─────────────────────────────────────

    def _view_signal_source(self, controller_name: str, overlay_name: str):
        """Signal source for one overlay: the seam controller, else the view.

        The default engine exposes ``drawing_controller`` / ``alarm_controller``
        proxies over its Qt overlays. The LWC driver exposes its session-facing
        ``drawing_overlay`` surface instead and carries no alarm overlay; a
        missing source returns ``None`` so start-up never raises on an engine
        that does not have that surface.
        """
        controller = getattr(self.chart_panel, controller_name, None)
        if controller is not None:
            return controller
        return getattr(self.chart_panel, overlay_name, None)

    @staticmethod
    def _connect_view_signal(source, name: str, slot) -> bool:
        """Connect ``source.<name>`` when present; never raise on a missing one."""
        signal = getattr(source, name, None)
        if signal is None:
            return False
        try:
            signal.connect(slot)
        except (AttributeError, TypeError, RuntimeError):
            return False
        return True

    def _chart_call(self, name: str, *args, **kwargs):
        """Call a chart-view method when the resolved engine provides it."""
        method = getattr(self.chart_panel, name, None)
        if not callable(method):
            return None
        return method(*args, **kwargs)

    def _drawing_actions(self):
        """The object carrying the default engine's drawing *methods*.

        Signals go through the seam controller; the imperative calls
        (``set_active_group`` / ``delete_selected``) live on the wrapped Qt
        overlay. The LWC driver's drawing surface is read-only fan-out, so
        those calls become no-ops there rather than raising.
        """
        controller = getattr(self.chart_panel, "drawing_controller", None)
        overlay = getattr(controller, "overlay", None)
        if overlay is not None:
            return overlay
        surface = getattr(self.chart_panel, "drawing_overlay", None)
        return surface if hasattr(surface, "set_active_group") else None

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
        # P7-W1 (S-P7-2): the session leaves the registry, but its cancel
        # tags must survive it — merged AFTER teardown, which is what
        # populates them. See _superseded_history_reqs.
        self._superseded_history_reqs |= session._cancelled_history_req_ids
        session.deleteLater()

    def _session_for_req_id(self, req_id: int) -> TickerSession | None:
        return self._req_to_session.get(req_id)

    # ── §7 market-data line guard (37.5) ─────────────────────────────────

    def _md_line_count(self) -> int:
        """Active market-data lines (owns the §7 accounting — C37.1).

        Counts RT-bar lines and watchlist rows explicitly.
        """
        rt = sum(1 for s in self._sessions.values()
                 if s.rt_req_id is not None)
        watchlist = self.watchlist_panel.active_row_count()
        return rt + watchlist

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
            ):
                try:
                    sig.disconnect(slot)
                except (RuntimeError, TypeError):
                    pass
        self._primary_session = session
        if session is not None:
            session.bar_updated.connect(self._on_primary_bar_updated)
            session.bars_refreshed.connect(self._on_primary_bars_refreshed)
            session.stream_health_changed.connect(
                self._on_primary_stream_health_changed
            )

    def _on_primary_bar_updated(self, bar: Bar, is_new_candle: bool) -> None:
        if bar.timeframe != self._current_tf:
            return
        self.chart_panel.update_last_bar(bar, is_new_candle)

    def _on_primary_bars_refreshed(self, timeframe: str, bars: list) -> None:
        if timeframe != self._current_tf:
            return
        self.chart_panel.update_chart(bars)

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
        # ESC-043: a fresh subscription invalidates the previous live-account
        # set — it is unknown again until the first account-summary callback.
        self._live_accounts = set()
        # ESC-052: ... and it is not COMPLETE until this subscription's
        # `accountSummaryEnd` arrives. Never prune on a partial set.
        self._account_summary_complete = False
        self._positions_rendered = False
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

    def _replay_subscriptions(self):
        """Re-issue live subscriptions after reconnection (D27.3).

        Chart RT bars and S0 generic-tick subscriptions replay through the
        subscription registry, which rebinds the new reqIds into the routing
        state.
        Watchlist market-data is re-issued by ``_restore_watchlist``'s
        clear+re-add path (pinned by AC-D22.7.2), so MARKET_DATA stays
        excluded here — replaying it too would double-subscribe every row.

        D28.1: the replay is all-or-nothing under pacing pressure
        (SubscriptionManager.replay_all raises PacingExceeded before any
        reissue); defer the whole replay via singleShot — never sleep.
        """
        try:
            self.sub_manager.replay_all(
                include_types={RT_BARS, S0_TICKS})
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
        # ESC-043: the live-account set is no longer known after a drop.
        self._live_accounts = set()
        # ESC-052: nor is the summary stream complete.
        self._account_summary_complete = False
        self._positions_rendered = False
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
        # P7-W2 (S-P7-3): a finalised wave can never resume — stop the
        # continuation timer and drop the queued plans, so no further chunk
        # issues and no second finalise can occur afterwards. (Late end
        # markers are already fenced by the generation advance below, and a
        # late timer tick finds an empty queue and no-ops.)
        session._wave_continue_timer.stop()
        session._wave_plan_queue.clear()
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
        remaining reqIds, stop the continuation timer, clear the plan queue,
        advance the generation, surface the shortfall once).
        """
        self._finalize_stranded_history_wave(
            session, reason="Historical backfill timed out"
        )

    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        if self._closing:
            return  # D28.5: teardown never touches cleared widgets.
        # P7-W1 (S-P7-2): a 162 acknowledgement for a cancel-tagged
        # (superseded) reqId is the expected TWS echo of our own cancel —
        # debug-level only, never a user-facing error. A 162 on any other
        # reqId keeps the existing warning + status-bar + retry path.
        if errorCode == 162 and self._is_superseded_history_req(reqId):
            _LOG.debug(
                "Historical request %s superseded by cancel; "
                "162 acknowledgement ignored (no status-bar error).",
                reqId,
            )
            return
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
            session.on_historical_error(reqId, errorCode, errorString)
            self.status_bar.showMessage(
                f"Error [{errorCode}]: {errorString}", 8000
            )
            return
        self.status_bar.showMessage(f"Error [{errorCode}]: {errorString}", 8000)

    def _is_superseded_history_req(self, req_id: int) -> bool:
        """True when a session cancel-tagged req_id (its 162 is superseded).

        P7-W1 (S-P7-2): the reqId is already unregistered from the routing
        table by the cancel, so the check reads the cancel tags instead:
        live sessions carry their own, and torn-down sessions merged theirs
        into the window set on teardown. Errors are rare; the scan cost is
        negligible.
        """
        if req_id in self._superseded_history_reqs:
            return True
        return any(
            session.is_superseded(req_id)
            for session in self._sessions.values()
        )

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
        # S-P8-4 / D48.4: daily-and-coarser loads use one canonical
        # full-session mode (ETH) for the cache read/write, the planner call,
        # the wave, and the prime below — the RTH/ETH toggle then converges
        # with identical bars from one shared cache, and a cached toggle
        # reload is a pure cache hit (no extra historical requests).
        if is_daily_or_coarser(timeframe):
            extended_hours = True
        if not symbol:
            self.status_bar.showMessage("Enter a symbol first.", 3000)
            return

        # D28.2: move the primary view to the symbol's session. The old
        # session loses the primary's RT hold and view; it tears down when
        # orphaned (no views and not monitored).
        new_session = self.get_or_create_session(symbol)
        old_session = self._primary_session
        # P7-W1 (S-P7-2): same-chart reload coalescing. An in-flight wave
        # for the identical (symbol, timeframe, ext-hours) triple continues
        # untouched — no cancel, no generation advance, no re-spend for data
        # already in flight. Any change of the triple is a genuine new wave
        # and falls through to the cancel+generation block below exactly as
        # before. ``_current_*`` still hold the previous load here.
        if (
            bool(new_session._history_req_ids)
            and symbol == self._current_symbol
            and timeframe == self._current_tf
            and extended_hours == new_session._wave_extended_hours
        ):
            _LOG.debug(
                "Reload of %s [%s] coalesced into the running wave "
                "(%d in-flight request(s)); no cancel, no re-spend.",
                symbol, timeframe, len(new_session._history_req_ids),
            )
            self.status_bar.showMessage(
                f"{symbol} — already backfilling; reload coalesced into "
                "the running wave…",
                4000,
            )
            return
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
        # P7-W1 (S-P7-1/S-P7-2): the previous load may have yielded at the
        # per-load cap with fetched-but-unfinalized bars still behind it.
        # Flush them to the mode-scoped cache BEFORE cancelling, so the
        # replan below resumes from the persisted depth (oldest-first,
        # monotonic) instead of re-requesting — a reload resumes the wave,
        # never restarts it. Uses the previous load's mode (set below).
        new_session.flush_pending_bars()
        new_session._cancel_history_requests()
        new_session._history_generation += 1
        new_session._backfill_failed_req_ids = set()
        new_session._backfill_missing_spans = []
        new_session._wave_timeframe = timeframe
        # D42/S19 (ESC-049): establish the session's mode from THIS load before
        # the initial cached ``set_bars`` below. ``queue_wave_plans`` was the
        # only setter, so a load that issues NO wave left the mode at its
        # default (RTH) and capped an ETH series at the RTH budget — breaching
        # AC-D16.8's in-memory depth on the no-wave path, and carrying a stale
        # mode across loads. Setting it here makes ``set_bars``/``_append_bar``
        # (and the D39 baseline preload) derive their cap from the CURRENT
        # load's mode; ``queue_wave_plans`` may keep setting it.
        new_session._wave_extended_hours = extended_hours

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
        # D42/S19: the read is scoped to the load's mode (AC-D16.9), so an
        # RTH load never sees ETH rows and vice versa.
        cached = BarCache.get_bars(symbol, timeframe, ext_hours=extended_hours)
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
        # D42/S17+S19: the planner is always consulted (the `if cached else []`
        # guard is bypassed) and is asked for the backwards depth floor
        # (`min_sessions`), in the load's mode. The planner gates the floor on
        # intraday timeframes, and covers an empty cache as one floor span — so
        # the former empty-cache single-window branch is removed (it would
        # otherwise duplicate/override the floor span).
        min_sessions = settings.MIN_INTRADAY_SESSIONS
        missing_spans = find_missing_spans(
            cached_ts, now_ts, timeframe,
            ext_hours=extended_hours,
            min_sessions=min_sessions,
        )
        plans = plan_requests(missing_spans, timeframe)
        new_session._backfill_missing_spans = list(missing_spans)

        contract = get_contract_for_symbol(symbol)

        if plans:
            # P7-W1 (S-P7-1): the session issues at most
            # floor(MAX_HISTORICAL_PER_600S/4) per load and leaves the
            # remainder queued; later loads resume oldest-first from the
            # persisted cache (non-blocking — never sleeps, never storms
            # TWS with 162s).
            new_session.queue_wave_plans(
                plans, contract, timeframe, extended_hours,
            )
            self.status_bar.showMessage(
                f"{symbol} — backfilling {len(plans)} historical chunk(s)…"
            )
        else:
            # The cache already reaches now (and the floor is filled):
            # no redundant request is issued.
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
        drawing_actions = self._drawing_actions()
        if drawing_actions is not None:
            drawing_actions.set_active_group(self._active_draw_group_id, color)

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
        self._chart_call("set_drawing_tool", tool)

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
        drawing_actions = self._drawing_actions()
        if drawing_actions is not None:
            drawing_actions.delete_selected()

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

    # ── D37 S0 routing ───────────────────────────────────────────────

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

        P7-W1 (S-P7-2): completed chunks are already ``save_bars``-persisted
        per chunk by ``TickerSession.on_historical_data_end`` — this final
        save covers only never-completed members' partial bars (failed
        members dropped by ``on_historical_error``), so a full wave still
        costs exactly one save per completed chunk.

        The session defaults to the current symbol's session (test seam).
        """
        if session is None:
            session = self._session_for_facade()
            if session is None:
                return
        session._disarm_history_wave_watchdog()
        new_count = len(session._pending_bars)
        # D42/S18+S19: the wave's mode scopes the save/get/prune, and the
        # retention keep is the floor-aware budget so the fetched depth floor
        # survives retention (a flat RETENTION_BARS would prune it away).
        # P7-W1 (S-P7-2): completed chunks are already persisted per chunk;
        # only never-completed members' partial bars remain in _req_bars.
        mode = session._wave_extended_hours
        remaining = [
            b for bars in session._req_bars.values() for b in bars
        ]
        if remaining:
            BarCache.save_bars(remaining, ext_hours=mode)
        timeframe = session._wave_timeframe or self._current_tf
        # D28.4: keep the on-disk cache bounded per (symbol, timeframe, mode).
        BarCache.prune(
            session.symbol, timeframe,
            ext_hours=mode,
            keep=floor_bar_budget(timeframe, mode),
        )
        all_bars = BarCache.get_bars(session.symbol, timeframe, ext_hours=mode)
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
        """Trading days the completed wave left empty (no bar fabricated).

        D42 / AC-D16.9: presence is the SAME exported mode-aware predicate the
        planner uses (``services.backfill_service.present_days``) — a day whose
        cached bars all lie outside the current mode's session window (a
        present-but-mode-empty day) is reported as missing, so the planner and
        the AC-D16.4 shortfall report cannot disagree about presence.
        """
        if not session._backfill_missing_spans:
            return []
        mode = session._wave_extended_hours
        present = present_days((b.ts for b in bars), mode)
        missing = []
        for span in session._backfill_missing_spans:
            for day in trading_days(span.start_ts, span.end_ts):
                if day not in present:
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
        mode = mode_by_label.get(label, ChartMode.CANDLES)
        # The LWC engine names modes with the shared lower-case strings; the
        # ChartMode enum stays the single mode vocabulary.
        self._chart_call("set_mode", getattr(mode, "value", str(mode)))

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
        except (TypeError, ValueError) as exc:
            # Q-43: corrupt persisted width — logged, falls back to default.
            _LOG.debug("Persisted watchlist width unreadable (%r): %s", raw, exc)
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
        except Exception as exc:
            # Q-43: layout probe best-effort — logged, treated as hidden.
            _LOG.debug("right_dock visibility probe failed: %s: %s",
                       type(exc).__name__, exc)
            return False

    def _compute_right_dock_collapsed_min_width(self) -> int:
        """D21.13: minimum width of the region once the panel is collapsed.

        The collapsed region is a vertical strip holding the Portfolio
        (Account Summary) header button, so its width is that button's
        ``sizeHint`` plus the standard margins, floored at
        :data:`RIGHT_DOCK_COLLAPSED_MIN_WIDTH`. Never raises.
        """
        try:
            button = getattr(self.portfolio_panel, "summary_label", None)
            content = button.sizeHint().width() if button is not None else 0
            return max(
                RIGHT_DOCK_COLLAPSED_MIN_WIDTH,
                int(content) + 2 * RIGHT_DOCK_COLLAPSED_MARGIN,
            )
        except Exception as exc:
            # Q-43: layout probe best-effort — logged, floor value kept.
            _LOG.debug("Collapsed min-width probe failed: %s: %s",
                       type(exc).__name__, exc)
            return RIGHT_DOCK_COLLAPSED_MIN_WIDTH

    def _right_region_is_collapsed(self) -> bool:
        """True when the right-region panel is collapsed to its button."""
        try:
            return bool(self.portfolio_panel.is_collapsed())
        except Exception as exc:
            # Q-43: layout probe best-effort — logged, treated as expanded.
            _LOG.debug("Right-region collapse probe failed: %s: %s",
                       type(exc).__name__, exc)
            return False

    def _on_right_panel_toggled(self, _checked: bool = False) -> None:
        """Re-layout the right region after a per-panel hide/show toggle (D21.13)."""
        try:
            self._sync_right_dock_collapse()
        except Exception as exc:
            # Q-43: layout best-effort — logged, toggle state already applied.
            _LOG.debug("Right-dock collapse sync failed: %s: %s",
                       type(exc).__name__, exc)

    def _sync_right_dock_collapse(self) -> None:
        """Apply the D21.13 right-region collapse state.

        * hidden: relax the dock's (and the panel's) minimum width to the button
          strip and pin the dock to it explicitly via
          ``_resize_docks_guarded`` so the chart reclaims the width
          (AC-D21.13.3);
        * otherwise: restore ``RIGHT_DOCK_MIN_WIDTH`` and re-run the B3
          cross-clamp.
        """
        collapsed = self._right_region_is_collapsed()
        self._right_region_collapsed = collapsed

        right_dock = getattr(self, "right_dock", None)
        widgets = (
            right_dock,
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
        except Exception as exc:
            # Q-43: deferred-apply best-effort — logged.
            _LOG.debug("Right-dock deferred apply scheduling failed: %s: %s",
                       type(exc).__name__, exc)

    def _plan_dock_widths(self, chart_area: int, requested_left, requested_right,
                          left_collapsed: bool = False):
        """Resolve ``(left, right)`` for the chart area, never below a dock minimum.

        ``left_collapsed`` (D44) is forwarded verbatim to the pure helper: when
        the watchlist body is collapsed the left dock is fixed at
        :data:`ui.dock_layout.WATCHLIST_COLLAPSED_WIDTH` and the 150px expanded
        minimum does not apply. The default ``False`` keeps the expanded call
        bit-for-bit unchanged.

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
        except Exception as exc:
            # Q-43: layout probe best-effort — logged, requested widths kept.
            _LOG.debug("Dock width probe failed: %s: %s",
                       type(exc).__name__, exc)
            cur_left = requested_left if requested_left is not None else 0
            cur_right = requested_right if requested_right is not None else 0
        invariant = chart_area + int(cur_left) + int(cur_right)

        ca = chart_area
        left, right = None, None
        previous = None
        for _ in range(24):
            left, right = plan_dock_widths(
                ca, int(requested_left), int(requested_right),
                left_collapsed=left_collapsed,
            )

            if (left, right) == previous:
                break
            previous = (left, right)
            next_ca = invariant - left - right
            if next_ca <= 0:
                break
            ca = next_ca
        return int(left), int(right)

    def _sync_watchlist_min_width(self, collapsed: bool) -> None:
        """D44: relax/restore the watchlist dock minimum for the collapse state.

        The panel carries ``WATCHLIST_MIN_WIDTH`` (150px) as its minimum, which
        would otherwise pin the dock at 150 and defeat the collapsed thin bar.
        Mirrors the D21.13 right-region pin (:meth:`_sync_right_dock_collapse`):
        the minimum is relaxed to
        :data:`ui.dock_layout.WATCHLIST_COLLAPSED_WIDTH` while collapsed and
        restored to ``WATCHLIST_MIN_WIDTH`` when expanded. Idempotent and never
        raises.
        """
        target = WATCHLIST_COLLAPSED_WIDTH if collapsed else WATCHLIST_MIN_WIDTH
        for widget in (
            getattr(self, "watchlist_dock", None),
            getattr(self, "watchlist_panel", None),
        ):
            if widget is None:
                continue
            try:
                if widget.minimumWidth() != target:
                    widget.setMinimumWidth(target)
            except Exception as exc:
                # Q-43: layout best-effort — logged per widget.
                _LOG.debug("Watchlist min-width relax/restore failed: %s: %s",
                           type(exc).__name__, exc)

    def _on_watchlist_collapsed_changed(self, collapsed: bool) -> None:
        """D44: the watchlist collapse transition (title-bar swap + width pin).

        Mirrors :meth:`_sync_right_dock_collapse`:

        * swap the dock's title-bar widget — the thin
          ``panel.collapsed_handle`` while collapsed, the header strip on
          expand (un-hidden as it is restored, so the title bar is never a
          hidden widget) — so the dock stays movable/floatable (A78);
        * relax/restore the minimum widths (panel + dock) via
          :meth:`_sync_watchlist_min_width`;
        * pin the dock to the collapsed width — or, on expand, back to the
          tracked expanded width ``self._watchlist_width`` (the width held
          immediately before collapsing, AC-D44.2) — then re-apply on the next
          event-loop turn, because the dock's layout minimum is only recomputed
          on the next layout pass, so the immediate resize can be clamped back
          to the pre-collapse minimum.

        Never raises.
        """
        try:
            dock = getattr(self, "watchlist_dock", None)
            panel = getattr(self, "watchlist_panel", None)
            if dock is None or panel is None:
                return
            collapsed = bool(collapsed)

            # 1. The title-bar-widget swap (A78).
            if collapsed:
                dock.setTitleBarWidget(panel.collapsed_handle)
            else:
                panel.header_bar.setVisible(True)
                dock.setTitleBarWidget(panel.header_bar)

            # 2. The minimum-width flip (panel + dock -> 30 / 150).
            self._sync_watchlist_min_width(collapsed)

            # 3. Pin the width now, then re-apply on the next event-loop turn.
            target = (
                WATCHLIST_COLLAPSED_WIDTH
                if collapsed
                else int(getattr(self, "_watchlist_width", WATCHLIST_MIN_WIDTH))
            )
            self._resize_docks_guarded([dock], [target])
            QTimer.singleShot(0, self._apply_dock_widths)
        except Exception as exc:
            # Q-43: collapse-transition best-effort — logged.
            _LOG.debug("Watchlist collapse transition failed: %s: %s",
                       type(exc).__name__, exc)

    def _apply_dock_widths(self, requested_left: int | None = None,
                           requested_right: int | None = None) -> int:
        """Shared, idempotent dock-width clamp (D17 watchlist + D18 right region).

        Reads the current chart area (``centralWidget().width()``) and clamps both
        docks against it. When the single right region is visible, the combined
        B3 cross-clamp :meth:`_plan_dock_widths` is used so ``chart_area`` keeps
        its ~400px minimum and enlarging one dock forces the other to shrink
        (AC-D18.5); when it is hidden, only the watchlist rule applies (D17).

        D44: the watchlist body's collapse state is read into a dedicated local
        (``watchlist_collapsed``) and honoured in both branches — a collapsed
        dock sits at its thin bar and the 150px expanded minimum does not apply;
        ``self._watchlist_width`` keeps tracking the expanded width.

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

            # D44: the watchlist body's own collapse state — a *new* local, never
            # the ``collapsed`` below (that one is the RIGHT REGION's state). While
            # collapsed the left dock is fixed at its thin bar and the 150px
            # expanded minimum does not apply.
            try:
                watchlist_collapsed = bool(self.watchlist_panel.is_collapsed())
            except Exception as exc:
                # Q-43: layout probe best-effort — logged, expanded assumed.
                _LOG.debug("Watchlist collapse probe failed: %s: %s",
                           type(exc).__name__, exc)
                watchlist_collapsed = False
            self._sync_watchlist_min_width(watchlist_collapsed)

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
                    chart_area, base_left, base_right,
                    left_collapsed=watchlist_collapsed,
                )
                # D44/AC-D44.2: ``_watchlist_width`` tracks the *expanded* width
                # (the one restored on un-collapse), so it is never overwritten
                # with the collapsed width.
                if not watchlist_collapsed:
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
                # D44: the collapsed/expanded width rule is the pure helper's
                # (single source of truth) — collapsed fixes the thin bar,
                # expanded applies today's max(WATCHLIST_MIN_WIDTH, min(base, cap)).
                desired = plan_watchlist_width(
                    chart_area, base_left, collapsed=watchlist_collapsed
                )
                if not watchlist_collapsed:
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
        except Exception as exc:
            # Q-43: clamp-apply best-effort — logged, widths already read.
            _LOG.debug("Dock-width clamp apply failed: %s: %s",
                       type(exc).__name__, exc)
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
            except Exception as exc:
                # Q-43: teardown/layout guard best-effort — logged.
                _LOG.debug("Splitter blockSignals(True) failed: %s: %s",
                           type(exc).__name__, exc)
                blocked = False
        try:
            self.resizeDocks(docks, sizes, Qt.Orientation.Horizontal)
        finally:
            if blocked:
                try:
                    splitter.blockSignals(False)
                except Exception as exc:
                    _LOG.debug("Splitter blockSignals(False) failed: %s: %s",
                               type(exc).__name__, exc)

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
                    except Exception as exc:
                        # Q-43: splitter wiring best-effort — logged, skipped.
                        _LOG.debug("Dock splitter wiring failed: %s: %s",
                                   type(exc).__name__, exc)
                        continue
                    return splitter
        except Exception as exc:
            # Q-43: splitter acquisition best-effort — logged, fallback used.
            _LOG.debug("Dock splitter acquisition failed: %s: %s",
                       type(exc).__name__, exc)
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
        except Exception as exc:
            # Q-43: splitter probe best-effort — logged, treated as no-match.
            _LOG.debug("Splitter watchlist probe failed: %s: %s",
                       type(exc).__name__, exc)
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
        except Exception as exc:
            # Q-43: deferred setup best-effort — logged, start-up continues.
            _LOG.debug("Deferred dock setup failed: %s: %s",
                       type(exc).__name__, exc)

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
            except Exception as exc:
                # Q-43: deferred clamp pass best-effort — logged.
                _LOG.debug("Deferred dock clamp pass failed: %s: %s",
                           type(exc).__name__, exc)
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

        D44: the check is collapsed-aware — a collapsed watchlist is settled when
        its width equals the collapsed width (``plan_left`` /
        :data:`ui.dock_layout.WATCHLIST_COLLAPSED_WIDTH`), so the deferred clamp
        does not spin against the 150px expanded rule.
        """
        try:
            ca = self._chart_area_width()
            try:
                watchlist_collapsed = bool(self.watchlist_panel.is_collapsed())
            except Exception as exc:
                # Q-43: layout probe best-effort — logged, expanded assumed.
                _LOG.debug("Watchlist collapse probe failed: %s: %s",
                           type(exc).__name__, exc)
                watchlist_collapsed = False
            if self._right_dock_available() and not getattr(
                self, "_right_region_collapsed", False
            ):
                plan_left, plan_right = self._plan_dock_widths(
                    ca, self.watchlist_dock.width(), self.right_dock.width(),
                    left_collapsed=watchlist_collapsed,
                )
                if watchlist_collapsed:
                    return (
                        abs(self.watchlist_dock.width() - plan_left) <= 1
                        and self.right_dock.width() == plan_right
                    )
                return self.right_dock.width() == plan_right and (
                    ca - plan_left - plan_right >= CHART_MIN_WIDTH - 1
                )
            if watchlist_collapsed:
                return (
                    abs(self.watchlist_dock.width() - WATCHLIST_COLLAPSED_WIDTH)
                    <= 1
                )
            invariant = ca + self.watchlist_dock.width()
            return self._watchlist_width == watchlist_max_width(
                invariant - self._watchlist_width
            )
        except Exception as exc:
            # Q-43: consistency probe best-effort — logged, assumed settled
            # so the deferred clamp does not spin.
            _LOG.debug("Dock-width consistency probe failed: %s: %s",
                       type(exc).__name__, exc)
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
        self._chart_call("set_timezone", self._tz_offset)
        self.status_bar.showMessage(f"Timezone: {label}", 3000)

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

    def _on_account_summary(self, reqId: int, account: str, tag: str, value: str):
        """Collect account summary key/values."""
        self._account_id = account  # D26.5: feeds the connection badge
        # ESC-043: "All" can stream several accounts — accumulate the set so
        # the position render/prune knows exactly which accounts are live.
        if account:
            self._live_accounts.add(account)
        summary = dict(getattr(self, "_account_summary", {}))
        summary[tag] = value
        # ESC-045: IBKR sends no 'Account' tag — the account id is the callback
        # argument. Persist it so the panel's Account field shows the same id
        # the connection badge uses (only when known; never fabricated).
        if account:
            summary["Account"] = account
        self._account_summary = summary
        self.portfolio_panel.set_account_id(account or None)
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
        # ESC-052: the end marker is the ONLY signal that the live account set
        # is complete. Before it, `_live_accounts` may hold only SOME of the
        # user's accounts, so the destructive foreign-row prune must not have
        # run and must not run now until we are sure this is the CURRENT
        # subscription's end (ignore a stale end from a superseded one).
        expected = getattr(self, "_account_summary_req_id", None)
        if expected is not None and reqId != expected:
            return
        self._account_summary_complete = True
        self._prune_foreign_positions()
        # ESC-052: `position_end` can beat `accountSummaryEnd`, in which case
        # the panel rendered only the accounts known at that moment. Re-render
        # so it converges on every live account now that the set is complete.
        if getattr(self, "_positions_rendered", False):
            self._on_position_end()

    def _prune_foreign_positions(self) -> None:
        """Delete persisted rows whose ``account`` is not in the live set.

        ESC-052: this is a DESTRUCTIVE write to the real ``positions`` table.
        Callers MUST only invoke it once the account-summary stream has
        completed (``self._account_summary_complete``) — a non-empty but
        partial ``_live_accounts`` would otherwise delete a real account's
        persisted rows merely because its summary callback has not arrived
        yet. No-ops when the live set is empty (nothing is known).
        """
        from data.db import db

        live = getattr(self, "_live_accounts", set())
        if not live:
            return
        placeholders = ",".join("?" for _ in live)
        db.conn.execute(
            f"DELETE FROM positions WHERE account NOT IN ({placeholders})",
            tuple(live),
        )
        db.conn.commit()

    def _on_position_update(self, account: str, contract, pos: float, avg_cost: float):
        """Persist and render a single position update."""
        import sys

        from ibkr.account import build_position_from_ib
        from data.db import db

        # ESC-043: once the live account(s) are known, an update for any other
        # account is not a real broker position — it must be neither persisted
        # nor rendered (otherwise a stray probe write re-leaks a foreign row).
        # While the live set is still unknown (no account-summary callback yet)
        # the update is accepted, exactly as before.
        # ESC-054: `_live_accounts` is AUTHORITATIVE only once the
        # account-summary stream has COMPLETED. In the window between the first
        # `account_summary` callback and `accountSummaryEnd` the set may hold
        # only SOME of the user's accounts, so gating the early-return on a
        # non-empty-but-PARTIAL set would silently discard a real second
        # account's update (neither persisted nor rendered, unrecoverable for
        # the session). A partial set scopes the render only — it never
        # discards a real account's data. The completed-set gate ESC-043/ESC-052
        # established still drops a foreign update AFTER completion.
        if (
            self._live_accounts
            and self._account_summary_complete
            and account not in self._live_accounts
        ):
            return

        # ESC-044 / AC-D27.6: read the REAL `ibapi.Contract` attribute names.
        # `class_` / `lastDateOrMonth` / `putCall` do NOT exist on the contract
        # (it has `secType` / `lastTradeDateOrContractMonth` / `right`), so every
        # option/future used to be persisted as 'stock' with a blank expiry and
        # ibapi's UNSET_DOUBLE sentinel strike. This forward mapping reads
        # ibapi's own attribute names — the only names the broker sends.
        sec_type = (getattr(contract, "secType", "") or "").upper()
        contract_type = {"OPT": "option", "FUT": "future"}.get(sec_type, "stock")
        multiplier = float(getattr(contract, "multiplier", 1.0) or 1.0)
        expiry = getattr(contract, "lastTradeDateOrContractMonth", None) or None
        strike = getattr(contract, "strike", None)
        # ibapi's UNSET_DOUBLE (sys.float_info.max) means "no strike" — never
        # persist the sentinel; the model/panel vocabulary is None.
        if strike is not None and strike == sys.float_info.max:
            strike = None
        right = getattr(contract, "right", None)
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
        # D27.5: the position's OWN symbol price — never the chart's price.
        # Unknown symbol -> 0.0 (honest unknown), not a wrong symbol's price.
        position.market_price = self._symbol_last_prices.get(
            (position.symbol or "").upper(), 0.0
        )
        # ESC-032 / P2-T27 (ESC-062): stamp the REAL `positions.id` row key on the
        # object before it reaches the panel. Strategy/Group derivation keys on
        # `pos.id`, so an id-less object renders '—' in both columns — the live
        # path must carry the row key, not an absent/None placeholder.
        position.id = self._upsert_position(position)
        self.portfolio_panel.add_position(position)

    def _on_position_end(self):
        """Load the persisted positions for the LIVE account(s) after streaming.

        ESC-043: the whole ``positions`` table used to be loaded and rendered
        with no account filter, so junk rows persisted by non-hermetic probes
        (e.g. ``HELD``/``DU123``, ``H``/``DU1``) showed up in the portfolio
        panel. Now only rows whose ``account`` is one of the live accounts are
        rendered. When the live account set is not yet known every row is
        rendered (unchanged).

        ESC-052: the destructive foreign-row prune runs ONLY once the
        account-summary stream has completed (``_account_summary_complete``).
        A non-empty-but-partial ``_live_accounts`` (a ``position_end`` that
        fired before every ``account_summary`` callback arrived) still scopes
        the render — foreign rows stay hidden — but must never delete, or it
        would destroy the persisted rows of a real account whose own summary
        callback has not arrived yet.
        """
        import sqlite3

        from data.db import db

        # ESC-032 / P2-T27 (ESC-062): `id` MUST be selected too — without it
        # every loaded Position is id-less, so the Strategy/Group columns
        # render '—' (the bulk path is degraded, not fixed).
        columns = (
            "symbol, qty, avg_cost, contract_type, con_id, account, "
            "local_symbol, multiplier, expiry, strike, right, "
            "trade_group_id, id"
        )
        # D46 / S48 (DG85): the rows are read BY NAME, never by position. The
        # dropped stop/target columns shift every later index, and such a shift
        # fails silently (a stop value in the Group column reads as a
        # strategy-detection bug), so a dedicated Row cursor removes the
        # positional contract entirely.
        cursor = db.conn.cursor()
        cursor.row_factory = sqlite3.Row
        live = getattr(self, "_live_accounts", set())
        complete = getattr(self, "_account_summary_complete", False)
        if live and complete:
            # AC2: address the foreign rows in the table itself, not just hide
            # them in the render — safe ONLY now that the summary stream has
            # completed and `live` is the full account set. Live-account rows
            # are untouched.
            self._prune_foreign_positions()
        if live:
            # AC1: render only the accounts the summary has reported. A partial
            # set still scopes the render (hiding foreign rows); it just must
            # not delete (see ESC-052 above).
            placeholders = ",".join("?" for _ in live)
            rows = cursor.execute(
                f"SELECT {columns} FROM positions "
                f"WHERE account IN ({placeholders})",
                tuple(live),
            ).fetchall()
        else:
            # AC2: live set unknown -> prune is a no-op; render unchanged.
            rows = cursor.execute(
                f"SELECT {columns} FROM positions"
            ).fetchall()
        positions = [Position(
            symbol=row["symbol"], qty=row["qty"], avg_cost=row["avg_cost"],
            contract_type=row["contract_type"], con_id=row["con_id"],
            account=row["account"], local_symbol=row["local_symbol"],
            multiplier=row["multiplier"], expiry=row["expiry"],
            strike=row["strike"], right=row["right"],
            trade_group_id=row["trade_group_id"], id=row["id"],
        ) for row in rows]
        self.portfolio_panel.set_positions(positions)
        self._positions_rendered = True

    def _upsert_position(self, position: Position) -> int:
        """Persist a position update (upsert by symbol + con_id).

        ESC-032 / P2-T27: returns the ``positions.id`` DB row key so the caller
        can stamp it on the object it hands the panel. ``RETURNING id`` yields
        the existing row's id on the DO UPDATE branch and the new rowid on the
        insert branch (SQLite >= 3.35; this env is 3.53.1).
        """
        from data.db import db

        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO positions
                (symbol, account, con_id, contract_type, qty, avg_cost,
                 local_symbol, multiplier, expiry, strike, right,
                 trade_group_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                trade_group_id=excluded.trade_group_id,
                updated_at=excluded.updated_at
            RETURNING id
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
                position.trade_group_id,
                int(__import__("time").time()),
            ),
        )
        row = cursor.fetchone()
        db.conn.commit()
        return int(row[0]) if row is not None else None

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
