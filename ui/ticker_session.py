"""ui/ticker_session.py — per-symbol session model (D24 / D25 / D28.2).

A TickerSession owns everything about one symbol's chart data plane:

- bar series + BarAggregator per timeframe in use (bars capped per session),
- the realtime-bar subscription (refcounted: first holder subscribes, last
  releases — never two reqRealTimeBars for one symbol),
- _last_chart_price with the D27.1 never-move-backward rule,
- alarms + per-session trigger evaluation (DEC-1),
- the history-wave lifecycle (req-id registry, watchdog, generation fencing),
- studies config + _StudyCache, drawings + groups,
- stream-health state (migrated from D27.4).

MainWindow holds the registry (dict[str, TickerSession]) and the reqId →
session routing table. Views (ChartPanel) attach/detach; the main chart is
the primary view. A session is destroyed when its last view detaches AND it
is not alarm-monitored (views > 0 OR monitored).

Only the host (MainWindow) is referenced, duck-typed — never imported, to
avoid a ui.main_window import cycle.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal as Signal, QTimer

from config import settings
from data.bar_aggregator import BarAggregator, TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.alarm_store import AlarmStore
from data.models import Bar
from ibkr.contracts import FUTURES_SCHEDULE, get_contract_for_symbol
from ibkr.contracts import footprint_cache_key  # D39: resolved-contract key
from ibkr.pacing import PacingExceeded, pacing_manager
from ibkr.stream_health import StreamHealth
from ibkr.subscription_manager import RT_BARS, DEPTH_HEATMAP, S0_TICKS
from ibkr.utils import parse_ibkr_date
from services.alarm_service import evaluate_alarms, evaluate_volume_burst
from services.depth_heatmap import DepthHeatmapService, BUCKET_SECONDS
from services.volume_baseline import (
    VolumeBaselineService,
    minutes_for_timeframe,
)
from services.footprint_service import (
    FootprintService,
    FormingSpec,
    FORMING_REFRESH_MIN_S,
    MAX_REQUESTS_PER_WAVE,
    PageSpec,
)

# D27.9: cap the priming span — a full day of 5-sec bars on every daily-chart
# load would burn pacing for little gain.
_PRIME_MAX_SPAN_S = 7_200

_LOG = logging.getLogger(__name__)


class TickerSession(QObject):
    """Per-symbol data plane. One instance per uppercase symbol per process."""

    # Live data for views.
    bar_updated = Signal(object, bool)   # (Bar, is_new_candle) — incremental tick
    bars_refreshed = Signal(str, list)   # (timeframe, bars) — full series replace
    # Config / overlay data.
    studies_changed = Signal()           # study config replaced
    drawings_changed = Signal()
    alarms_changed = Signal()
    # Trigger events. Carries the firing symbol (D28.2); MainWindow adds
    # toast + sound exactly once per trigger event.
    alarm_triggered = Signal(str, list)     # (symbol, [alarms])
    stream_health_changed = Signal()
    # D36: footprint data changed for a timeframe — the panel re-renders.
    footprint_updated = Signal(str)         # (timeframe)
    # D37: depth feed state transitions (live / no_entitlement / ...).
    depth_state_changed = Signal(str)       # (state)
    # D37: auction ticks (34/35/36/61) arrived — the header chip re-renders.
    auction_updated = Signal()
    # D38: tick-59 dividend string arrived — event state re-rendered.
    dividend_updated = Signal()
    # D38: corporate events (markers) changed for the symbol.
    events_updated = Signal()

    def __init__(self, symbol: str, host):
        super().__init__()
        self.symbol = symbol.upper()
        self._host = host  # MainWindow (duck-typed)
        self._views: list[tuple[object, str]] = []  # (view, timeframe)
        self.monitored: bool = False

        # ── Data plane (3b-1) ──────────────────────────────────────────
        self._aggregators: dict[str, BarAggregator] = {}
        self._bars: dict[str, list[Bar]] = {}
        self._rt_req_id: int | None = None
        self._rt_holders: int = 0
        self._last_chart_price: float | None = None
        self._rt_seen: bool = False  # D27.1: live bar observed since (re)load
        self._alarms: list = []  # own alarms (AlarmStore.load(symbol))
        # D39.4: burst alarms from index symbols evaluated on this tape
        # (e.g. SPX alarms on the ES session). Survive reload_alarms().
        self._proxy_alarms: list = []
        # D39: last forming bar seen per timeframe — when a new candle
        # starts, the previous bar is complete and feeds the baseline.
        self._burst_forming: dict[str, Bar] = {}
        # D39: resolved contract key currently feeding the baseline; a
        # change means the front month rolled → invalidate the old key.
        self._burst_key: str | None = None
        # D39: per-session fallback when the host has no shared baseline
        # service (tests / stub hosts). Production MainWindow owns one.
        self._vb_fallback: VolumeBaselineService | None = None
        self.stream_health = StreamHealth()

        # ── History wave (3b-2) ────────────────────────────────────────
        self._history_req_ids: set[int] = set()
        self._history_req_generation: dict[int, int] = {}
        self._history_generation: int = 0
        self._pending_bars: list[Bar] = []
        self._backfill_missing_spans: list = []
        self._backfill_failed_req_ids: set[int] = set()
        self._history_stranded_reason: str = ""
        self._wave_timeframe: str | None = None
        self._history_wave_timer = QTimer(self)
        self._history_wave_timer.setSingleShot(True)
        self._history_wave_timer.timeout.connect(self._on_history_wave_timeout)
        self._history_wave_timeout_ms: int = 120_000
        # D28.3: pacing-aware wave issuing. Plans are issued ~60 per wave;
        # when the 600s historical budget is exhausted the remainder stays
        # queued and continues via the timer below (never sleeps).
        self._wave_plan_queue: list = []
        self._req_to_plan: dict[int, object] = {}
        self._wave_contract = None
        self._wave_extended_hours: bool = False
        self._retried_plans: set = set()  # error-162 retry-once tracking
        self._wave_continue_timer = QTimer(self)
        self._wave_continue_timer.setSingleShot(True)
        self._wave_continue_timer.timeout.connect(
            self._on_wave_continue_timeout
        )
        # D27.9 aggregator priming state (per load).
        self._prime_req_id: int | None = None
        self._prime_symbol: str = ""
        self._prime_timeframe: str | None = None
        self._prime_timer = QTimer(self)
        self._prime_timer.setSingleShot(True)
        self._prime_timer.timeout.connect(self._on_prime_timeout)

        # ── Studies + drawings (3b-3) ──────────────────────────────────
        self._studies: list[dict] = []  # per-symbol study config
        self._study_cache: dict = {}
        self._drawings: list = []
        self._drawing_groups: list = []

        # ── Footprint (D36) ────────────────────────────────────────────
        self._footprint = FootprintService(symbol)
        self._fp_enabled: bool = False
        self._fp_style: str = "classic"   # "classic" | "heatmap"
        self._fp_metric: str = "volume"   # "volume" | "count" (heatmap only)
        self._fp_timeframe: str | None = None
        self._fp_contract = None
        self._fp_cache_key: str = ""
        self._fp_proxy_label: str = ""
        self._fp_wave_issued: int = 0
        self._fp_wave_active: bool = False
        self._fp_continue_timer = QTimer(self)
        self._fp_continue_timer.setSingleShot(True)
        self._fp_continue_timer.timeout.connect(self._on_fp_continue_timeout)
        # Forming-bar incremental refresh (15s self-limit, plan 36.2).
        self._fp_forming_timer = QTimer(self)
        self._fp_forming_timer.setSingleShot(True)
        self._fp_forming_timer.timeout.connect(self._on_fp_forming_timeout)

        # ── S0 generic-tick substrate (D37; shared with D38) ──────────
        # One optional reqMktData per session; the generic list is the union
        # of registered feature needs. D37 registers "225" (auction) while
        # views are attached; D38 will add "292"/"456" the same way.
        self._s0_req_id: int | None = None
        self._s0_needs: dict[str, set[str]] = {}
        self._s0_union: str = ""
        # D38: headless S0 — the news digest keeps an S0 subscription on
        # sessions with no views (headless digest sessions). Never set for
        # charted/monitored sessions.
        self._s0_headless: bool = False
        # D38: live news-push (tick 292) fan-out for the digest dock.
        self._news_push_listeners: list = []

        # ── D38 dividends (tick 59 via S0 generic "456") ───────────────
        self._dividend_info: dict = {}

        # ── D38 corporate events (markers) ────────────────────────────
        self._events: list = []          # merged IBKR + yfinance Events
        self._events_unavailable: bool = False

        # ── Auction state (D37: ticks 34/35/36/61 via S0) ─────────────
        self._auction: dict = {
            "volume": None,       # 34, tickSize
            "price": None,        # 35, tickPrice
            "imbalance": None,    # 36, tickSize (signed shares)
            "reg_imbalance": None,  # 61, tickSize
        }

        # ── Depth heatmap (D37) ──────────────────────────────────────
        self._depth = DepthHeatmapService(symbol)
        self._depth_req_id: int | None = None
        self._depth_holders: int = 0
        self._depth_state: str = "idle"  # idle|live|no_entitlement|budget_exceeded
        self._depth_roll_timer = QTimer(self)
        self._depth_roll_timer.setInterval(BUCKET_SECONDS * 1000)
        self._depth_roll_timer.timeout.connect(self._on_depth_roll_timeout)

    # ── Identity / lifecycle ───────────────────────────────────────────

    @property
    def view_count(self) -> int:
        return len(self._views)

    @property
    def views(self) -> list:
        """Attached views (for the alarm monitor's headless check)."""
        return [v for v, _tf in self._views]

    @property
    def rt_req_id(self) -> int | None:
        return self._rt_req_id

    @property
    def last_chart_price(self) -> float | None:
        return self._last_chart_price

    @last_chart_price.setter
    def last_chart_price(self, value: float | None) -> None:
        self._last_chart_price = value

    @property
    def alarms(self) -> list:
        return self._alarms

    def attach_view(self, view, timeframe: str, sync: bool = True) -> None:
        """Register a view on this session. No RT side effects.

        sync=True performs the initial full sync (bars → studies → drawings
        → alarms) so the view is correct on first paint (FR-5.5). The main
        chart passes sync=False — its load flow syncs via
        set_bars → bars_refreshed. The RT subscription is managed separately
        via ensure_rt_subscribed/release_rt so the host can order it after
        aggregator priming.
        """
        if all(v is not view for v, _ in self._views):
            self._views.append((view, timeframe))
            if sync:
                self._sync_view(view, timeframe)
            # D37: the auction chip lives on chart views — register the S0
            # "225" need while views are attached.
            # D38: IBKR dividends (tick 59 via generic "456") feed the event
            # markers on charted symbols — same view-bound lifecycle.
            # Futures have no dividend stream (plan A38.4): skip the need.
            # One resync for both (no double re-subscribe).
            _needs = {"auction": {"225"}}
            if self.symbol.split()[0] not in FUTURES_SCHEDULE:
                _needs["dividends"] = {"456"}
            self.s0_register_many(_needs)
            # D25: a view opening promotes a headless monitor.
            monitor = getattr(self._host, "alarm_monitor", None)
            if monitor is not None:
                monitor.on_session_attached(self)

    def detach_view(self, view) -> None:
        """Unregister a view; teardown when orphaned and not monitored."""
        self._views = [(v, tf) for v, tf in self._views if v is not view]
        # D37: last view gone → drop the auction S0 need (S0 cancels).
        # D38: same for the dividend need. Single resync.
        if not self._views:
            self.s0_deregister_many(("auction", "dividends"))
        # D25: the last view closing may start headless monitoring.
        monitor = getattr(self._host, "alarm_monitor", None)
        if monitor is not None:
            monitor.on_session_detached(self)
        if not self._views and not self.monitored:
            self._host._teardown_session(self.symbol)

    def ensure_rt_subscribed(self) -> int:
        """Refcounted RT subscribe; returns the reqId. May raise
        PacingExceeded — the caller defers and retries (the view stays
        registered; the retry re-enters here without re-syncing)."""
        if self._rt_req_id is not None:
            self._rt_holders += 1
            return self._rt_req_id
        self._subscribe_rt()
        self._rt_holders = 1
        return self._rt_req_id

    def release_rt(self) -> None:
        """Release one RT hold; unsubscribe at zero holders."""
        if self._rt_holders > 0:
            self._rt_holders -= 1
        if self._rt_holders == 0:
            self._unsubscribe_rt()

    def _sync_view(self, view, timeframe: str) -> None:
        """Initial full sync for a newly attached view (FR-5.5)."""
        bars = self.get_bars(timeframe)
        if bars:
            view.update_chart(bars)
        if self._studies:
            view.set_studies(self._studies)
        if self._drawings or self._drawing_groups:
            view.drawing_overlay.set_data(
                self.symbol, self._drawings, self._drawing_groups
            )
        view.set_alarms(self._alarms)

    def teardown(self) -> None:
        """Cancel the RT subscription and the in-flight history wave.

        SQLite caches and persisted state are untouched (FR-1.5).
        """
        self._rt_holders = 0
        self._unsubscribe_rt()
        self._cancel_history_requests()
        self._disarm_history_wave_watchdog()
        self._wave_continue_timer.stop()  # D28.5: no deferred wave chunks
        self._prime_timer.stop()
        self._prime_req_id = None
        # D37: cancel S0 and release the depth feed.
        self._s0_needs.clear()
        self._s0_cancel()
        self._s0_union = ""
        self._depth_holders = 0
        self._cancel_depth()
        # D36: stop footprint timers and forget in-flight tick requests.
        self._fp_enabled = False
        self._fp_wave_active = False
        self._fp_continue_timer.stop()
        self._fp_forming_timer.stop()
        try:
            self._fp_cancel_inflight()
        except Exception:
            pass

    # ── Bars / aggregators (data plane) ────────────────────────────────

    def aggregator_for(self, timeframe: str) -> BarAggregator:
        agg = self._aggregators.get(timeframe)
        if agg is None:
            agg = BarAggregator(
                symbol=self.symbol,
                timeframe=timeframe,
                on_bar_update=self._on_aggregated_bar,
            )
            self._aggregators[timeframe] = agg
        return agg

    def get_bars(self, timeframe: str) -> list[Bar]:
        return self._bars.get(timeframe, [])

    def set_bars(self, timeframe: str, bars: list[Bar]) -> None:
        """Replace the in-memory series (capped). Emits bars_refreshed."""
        cap = settings.SESSION_BAR_CAP
        if len(bars) > cap:
            bars = bars[-cap:]
        self._bars[timeframe] = list(bars)
        self.bars_refreshed.emit(timeframe, self._bars[timeframe])

    def _append_bar(self, timeframe: str, bar: Bar, is_new_candle: bool) -> None:
        """Fold an aggregated bar into the series (capped)."""
        series = self._bars.setdefault(timeframe, [])
        if is_new_candle or not series:
            series.append(bar)
        else:
            series[-1] = bar
        cap = settings.SESSION_BAR_CAP
        if len(series) > cap:
            del series[: len(series) - cap]

    # ── Realtime subscription (refcounted) ─────────────────────────────

    def _subscribe_rt(self, reset_backoff: bool = True) -> None:
        """Subscribe the 5-sec realtime bars. May raise PacingExceeded."""
        contract = get_contract_for_symbol(self.symbol)
        req_id = self._host.rt_manager.subscribe(self.symbol, contract)
        self._rt_req_id = req_id
        self._host._register_req_id(req_id, self)
        self._host.sub_manager.subscribe(
            self.symbol,
            req_id,
            RT_BARS,
            reissue=self._reissue_rt,
            rebind=self._rebind_rt_req_id,
        )
        # Fix-B: a backoff retry must NOT reset the attempt counter, or the
        # backoff never progresses past the first delay.
        self.stream_health.mark_subscribed(reset_backoff=reset_backoff)
        self.stream_health_changed.emit()

    def _unsubscribe_rt(self) -> None:
        if self._rt_req_id is None:
            return
        self._host._unregister_req_id(self._rt_req_id)
        self._host.sub_manager.unsubscribe(self._rt_req_id)
        try:
            self._host.rt_manager.unsubscribe(self._rt_req_id)
        except Exception:
            pass
        self._rt_req_id = None

    def _reissue_rt(self) -> int:
        """Reconnect replay hook: re-subscribe, return the new reqId."""
        if self._rt_req_id is not None:
            self._host._unregister_req_id(self._rt_req_id)
        contract = get_contract_for_symbol(self.symbol)
        req_id = self._host.rt_manager.subscribe(self.symbol, contract)
        self._rt_req_id = req_id
        self._host._register_req_id(req_id, self)
        return req_id

    def _rebind_rt_req_id(self, new_req_id: int) -> None:
        """SubscriptionManager rebind hook (post-reissue safety net)."""
        self._rt_req_id = new_req_id
        self._host._register_req_id(new_req_id, self)

    def resubscribe_rt(self) -> int:
        """D27.4 retry path: drop the failed subscription, start fresh."""
        self._unsubscribe_rt()
        self._subscribe_rt(reset_backoff=False)
        return self._rt_req_id

    # ── S0 generic-tick substrate (D37; shared with D38) ─────────────

    def s0_register(self, feature: str, ticks: set[str]) -> None:
        """Register a feature's generic-tick needs; resubscribe on change."""
        self._s0_needs[feature] = set(ticks)
        self._s0_resync()

    def s0_deregister(self, feature: str) -> None:
        """Drop a feature's needs; resubscribe (or cancel) on change."""
        self._s0_needs.pop(feature, None)
        self._s0_resync()

    def s0_register_many(self, needs: dict[str, set[str]]) -> None:
        """Register several features' needs with a single resync (avoids
        one cancel+re-subscribe per feature)."""
        for feature, ticks in needs.items():
            self._s0_needs[feature] = set(ticks)
        self._s0_resync()

    def s0_deregister_many(self, features) -> None:
        """Drop several features' needs with a single resync."""
        for feature in features:
            self._s0_needs.pop(feature, None)
        self._s0_resync()

    @property
    def s0_req_id(self) -> int | None:
        return self._s0_req_id

    def _s0_union_str(self) -> str:
        merged: set[str] = set()
        for ticks in self._s0_needs.values():
            merged |= ticks
        return ",".join(sorted(merged, key=int)) if merged else ""

    def _s0_resync(self) -> None:
        """Reconcile the S0 subscription with registered needs.

        One reqMktData per session; the generic list is the union of needs.
        Re-subscribes only when the union changes; cancels when empty.
        Never silently drops: MD-budget refusal surfaces via the host.
        """
        want = self._s0_union_str() if (self.view_count > 0
                                       or self._s0_headless) else ""
        if want == self._s0_union:
            return
        self._s0_cancel()
        self._s0_union = want
        if not want:
            return
        if not self._host._guard_md_lines(self.symbol, "S0 ticks"):
            self._s0_union = ""
            return
        contract = get_contract_for_symbol(self.symbol)
        req_id = self._host.md_manager.req_mkt_data(
            contract, generic_ticks=want)
        self._s0_req_id = req_id
        self._host._register_req_id(req_id, self)
        self._host.sub_manager.subscribe(
            self.symbol,
            req_id,
            S0_TICKS,
            reissue=self._s0_reissue,
            rebind=self._s0_rebind,
        )

    def _s0_cancel(self) -> None:
        if self._s0_req_id is None:
            return
        self._host._unregister_req_id(self._s0_req_id)
        self._host.sub_manager.unsubscribe(self._s0_req_id)
        try:
            self._host.md_manager.cancel_mkt_data(self._s0_req_id)
        except Exception:
            pass
        self._s0_req_id = None

    def _s0_reissue(self) -> int:
        """D27 replay hook — replay_all moves the registry entry itself, so
        this must not touch sub_manager (mirrors _reissue_rt)."""
        if self._s0_req_id is not None:
            self._host._unregister_req_id(self._s0_req_id)
            try:
                self._host.md_manager.cancel_mkt_data(self._s0_req_id)
            except Exception:
                pass
            self._s0_req_id = None
        self._s0_union = ""
        want = self._s0_union_str() if (self.view_count > 0
                                       or self._s0_headless) else ""
        if not want:
            return 0
        self._s0_union = want
        contract = get_contract_for_symbol(self.symbol)
        self._s0_req_id = self._host.md_manager.req_mkt_data(
            contract, generic_ticks=want)
        return self._s0_req_id

    def _s0_rebind(self, new_req_id: int) -> None:
        self._s0_req_id = new_req_id
        self._host._register_req_id(new_req_id, self)

    # ── S0 tick ingress (D37 auction; D38 news later) ─────────────────

    # Auction tick types (generic "225"): 34 volume + 36 imbalance + 61
    # regulatory imbalance arrive via tickSize; 35 auction price via tickPrice.
    _AUCTION_SIZE_TICKS = {34: "volume", 36: "imbalance", 61: "reg_imbalance"}

    def on_tick_price(self, req_id: int, tick_type: int, price: float) -> None:
        if req_id != self._s0_req_id or tick_type != 35:
            return
        self._auction["price"] = price
        self.auction_updated.emit()

    def on_tick_size(self, req_id: int, tick_type: int, size: int) -> None:
        if req_id != self._s0_req_id:
            return
        key = self._AUCTION_SIZE_TICKS.get(tick_type)
        if key is None:
            return
        self._auction[key] = size
        self.auction_updated.emit()

    def on_s0_tick_generic(self, req_id: int, tick_type: int,
                           value: float) -> None:
        """Plumbing for D38 (generic ticks beyond auction)."""
        if req_id != self._s0_req_id:
            return

    def on_s0_tick_string(self, req_id: int, tick_type: int,
                          value: str) -> None:
        """D38: tick 59 (IB Dividends) arrives here — generic "456" was the
        request code (plan B1). Parsed defensively; never raises."""
        if req_id != self._s0_req_id:
            return
        if tick_type != 59:
            return
        try:
            from data.events.provider import parse_ib_dividend_string
            parsed = parse_ib_dividend_string(value)
        except Exception:
            return
        if parsed.get("next_date") is None and parsed.get("past12m") is None:
            return
        self._dividend_info = parsed
        self.dividend_updated.emit()
        self._merge_ibkr_dividend_event()

    def on_s0_tick_news(self, req_id: int, time_stamp: int,
                        provider_code: str, article_id: str,
                        headline: str) -> None:
        """D38: live news push via generic "292". Forwarded to digest
        listeners registered via ``add_news_push_listener``."""
        if req_id != self._s0_req_id:
            return
        for cb in list(self._news_push_listeners):
            try:
                cb(self.symbol, time_stamp, provider_code, article_id, headline)
            except Exception:
                pass

    # ── D38 dividends + corporate events ─────────────────────────────

    def dividend_info(self) -> dict:
        """Latest parsed tick-59 dividend info ({} when none yet)."""
        return dict(self._dividend_info)

    def set_s0_headless(self, enabled: bool) -> None:
        """Digest sessions: keep the S0 subscription with no views attached.

        Used by the news digest for holdings that are neither charted nor
        monitored (plan 38a.2). Re-run the resync so the change takes effect.
        """
        self._s0_headless = bool(enabled)
        self._s0_resync()

    def add_news_push_listener(self, cb) -> None:
        """Register a callable(symbol, ts, provider, article_id, headline)."""
        if cb not in self._news_push_listeners:
            self._news_push_listeners.append(cb)

    def remove_news_push_listener(self, cb) -> None:
        try:
            self._news_push_listeners.remove(cb)
        except ValueError:
            pass

    def _merge_ibkr_dividend_event(self) -> None:
        """Fold the latest tick-59 dividend into the event list (IBKR-first
        source priority). yfinance dividend events for the same date do not
        duplicate it — see ``refresh_events``."""
        from data.events.ibkr_source import IBKREventSource
        from datetime import date as _date
        src = IBKREventSource(lambda _s: self)
        ibkr_events = src.get_events(
            self.symbol, _date(1970, 1, 1), _date(2100, 1, 1))
        self._merge_events(ibkr_events, source="ibkr")

    def _merge_events(self, new_events: list, source: str) -> None:
        """Merge one source's events: replace that source's entries, keep the
        other's. Emits ``events_updated`` when the merged set changes."""
        from data.events.provider import Event
        kept = [e for e in self._events
                if isinstance(e, Event) and e.source != source]
        # IBKR-first priority: a yfinance dividend on the same date as an
        # IBKR dividend is dropped (IBKR is live; yfinance is the fallback).
        if source == "yfinance":
            ibkr_dividend_dates = {
                e.date for e in kept
                if e.type == "dividend" and e.source == "ibkr"
            }
            new_events = [e for e in new_events
                          if not (e.type == "dividend"
                                  and e.date in ibkr_dividend_dates)]
        merged = kept + [e for e in new_events if isinstance(e, Event)]
        old_ids = {e.id for e in self._events if isinstance(e, Event)}
        new_ids = {e.id for e in merged}
        self._events = sorted(merged, key=lambda e: (e.date, e.type, e.id))
        if old_ids != new_ids:
            self.events_updated.emit()

    def refresh_events(self, yf_source=None) -> None:
        """Rebuild the event list: IBKR dividends (sync, from tick-59 state)
        + yfinance earnings/splits/dividends (async, cache-first).

        ``yf_source`` is a ``YFinanceEventSource`` (host-provided, shared).
        Never raises; never blocks on the network.
        """
        self._merge_ibkr_dividend_event()
        if yf_source is not None:
            from datetime import date as _date
            try:
                yf_events = yf_source.get_events(
                    self.symbol, _date(1970, 1, 1), _date(2100, 1, 1))
            except Exception:
                yf_events = []
            self._merge_events(yf_events, source="yfinance")
            self._events_unavailable = yf_source.unavailable(self.symbol)
        self.events_updated.emit()

    def on_yfinance_refresh(self, symbol: str, yf_source) -> None:
        """Worker finished a background yfinance fetch — merge if ours."""
        if symbol.upper() != self.symbol:
            return
        self.refresh_events(yf_source)

    def events(self) -> list:
        """Current merged corporate events (sorted by date)."""
        return list(self._events)

    def events_unavailable(self) -> bool:
        """True when yfinance cannot serve this symbol and no cache exists —
        the UI shows the explicit "event data unavailable" state."""
        return self._events_unavailable

    def auction_state(self) -> dict:
        """Current auction values; None fields mean 'no data yet'."""
        return dict(self._auction)

    # ── Depth heatmap feed (D37) ─────────────────────────────────────

    @property
    def depth_state(self) -> str:
        return self._depth_state

    @property
    def depth_req_id(self) -> int | None:
        return self._depth_req_id

    @property
    def depth_service(self) -> DepthHeatmapService:
        return self._depth

    def ensure_depth_subscribed(self) -> int | None:
        """Refcounted SMART depth subscribe. Returns reqId or None.

        Returns None (with an explicit state + host warning) when the
        depth budget or MD-line budget refuses the feed — never silently.
        """
        if self._depth_req_id is not None:
            self._depth_holders += 1
            return self._depth_req_id
        if not self._host._guard_md_lines(self.symbol, "depth"):
            self._set_depth_state("budget_exceeded")
            return None
        if not self._host._guard_depth_budget(self.symbol):
            self._set_depth_state("budget_exceeded")
            return None
        contract = get_contract_for_symbol(self.symbol)
        req_id = self._host.depth_manager.subscribe_shared(
            self.symbol, contract, num_levels=10)
        self._depth_req_id = req_id
        self._depth_holders = 1
        self._host._register_req_id(req_id, self)
        self._host.sub_manager.subscribe(
            self.symbol,
            req_id,
            DEPTH_HEATMAP,
            reissue=self._reissue_depth,
            rebind=self._rebind_depth_req_id,
        )
        self._set_depth_state("live")
        if not self._depth_roll_timer.isActive():
            self._depth_roll_timer.start()
        return req_id

    def release_depth(self) -> None:
        """Release one depth hold; cancel the feed at zero holders."""
        if self._depth_holders > 0:
            self._depth_holders -= 1
        if self._depth_holders == 0:
            self._cancel_depth()

    def _cancel_depth(self) -> None:
        if self._depth_req_id is not None:
            self._host._unregister_req_id(self._depth_req_id)
            self._host.sub_manager.unsubscribe(self._depth_req_id)
            self._depth_req_id = None
        try:
            self._host.depth_manager.release_shared(self.symbol)
        except Exception:
            pass
        self._depth_roll_timer.stop()
        if self._depth_state == "live":
            self._set_depth_state("idle")

    def _reissue_depth(self) -> int:
        """D27 replay hook — replay_all moves the registry entry itself, so
        this must not touch sub_manager (mirrors _reissue_rt). Forces a fresh
        wire subscription: the old reqMktDepth died with the connection."""
        if self._depth_req_id is not None:
            self._host._unregister_req_id(self._depth_req_id)
            self._depth_req_id = None
        contract = get_contract_for_symbol(self.symbol)
        req_id = self._host.depth_manager.resubscribe_shared(
            self.symbol, contract, num_levels=10)
        self._depth_req_id = req_id
        self._host._register_req_id(req_id, self)
        return req_id

    def _rebind_depth_req_id(self, new_req_id: int) -> None:
        self._depth_req_id = new_req_id
        self._host._register_req_id(new_req_id, self)

    def on_depth_update(self, position: int, operation: int, side: int,
                        price: float, size: int,
                        is_smart_depth: bool = False) -> None:
        """Depth op ingress — data only; rendering is timer-driven."""
        self._depth.on_depth_op(position, operation, side, price, size,
                                is_smart_depth)

    def on_depth_error(self, error_code: int, error_string: str) -> None:
        """354 (no entitlement) → explicit state; the feed is dead.

        Known limitation (reviewer A1, D37): TWS sometimes delivers *delayed*
        depth instead of erroring 354. That path is unhandled — delayed rows
        would render with no "delayed" label. If observed, add a delayed-data
        state here.
        """
        if error_code == 354:
            self._set_depth_state("no_entitlement")
        else:
            self._set_depth_state("unavailable")
        self._cancel_depth()

    def _set_depth_state(self, state: str) -> None:
        if state != self._depth_state:
            self._depth_state = state
            self.depth_state_changed.emit(state)

    def depth_imbalance(self, n: int = 5) -> float:
        return self._depth.imbalance(n)

    def _on_depth_roll_timeout(self) -> None:
        self._depth.roll_bucket()

    # ── Realtime bar ingress ───────────────────────────────────────────

    def on_realtime_bar(self, req_id: int, ts: int, o: float, h: float,
                        l: float, c: float, vol: float) -> None:
        """Route a 5-sec realtime bar into every active aggregator."""
        if req_id != self._rt_req_id:
            return
        self._rt_seen = True  # D27.1: a live bar was observed
        if not self.stream_health.is_live:
            self.stream_health.mark_first_bar()
            self.stream_health_changed.emit()
        for agg in self._aggregators.values():
            agg.push(ts, o, h, l, c, vol)

    def _on_aggregated_bar(self, bar: Bar, is_new_candle: bool) -> None:
        """BarAggregator callback (main thread). Data-plane update + per-
        session alarm evaluation (DEC-1: fires even with zero views)."""
        self._append_bar(bar.timeframe, bar, is_new_candle)
        # D36: a new candle needs its footprint backfill — sync the bar set
        # and restart the wave if it's idle. (AC-D36.4: per-tick chart
        # updates don't touch the footprint items; this path emits only the
        # same footprint_updated the wave pump uses.)
        if (is_new_candle and self._fp_enabled
                and bar.timeframe == self._fp_timeframe):
            self._footprint.sync_bars(self.get_bars(bar.timeframe),
                                      bar.timeframe)
            if not self._fp_wave_active:
                self._fp_start_wave()
        triggered = evaluate_alarms(
            self._last_chart_price, bar.close, self._alarms
        )
        for alarm in triggered:
            if alarm.id is not None:
                AlarmStore.mark_triggered(alarm.id)
            alarm.triggered = True
        if triggered:
            self.alarm_triggered.emit(self.symbol, triggered)
            self.alarms_changed.emit()
            # D25: a trigger may leave the symbol with no active alarms →
            # reconcile headless monitors.
            monitor = getattr(self._host, "alarm_monitor", None)
            if monitor is not None:
                monitor.on_alarm_changed()
        # D39: volume-burst evaluation on the same per-push path.
        self._evaluate_burst_alarms(bar, is_new_candle)
        self._last_chart_price = bar.close
        self._host._record_symbol_price(self.symbol, bar.close)
        self.bar_updated.emit(bar, is_new_candle)

    # ── Alarms ─────────────────────────────────────────────────────────

    def set_alarms(self, alarms: list) -> None:
        self._alarms = list(alarms)
        self.alarms_changed.emit()

    def reload_alarms(self) -> None:
        # D39.4: proxy burst alarms (e.g. SPX on the ES tape) survive the
        # reload — they are owned by the AlarmMonitor, not the store query.
        self.set_alarms(AlarmStore.load(self.symbol) + self._proxy_alarms)

    def set_proxy_alarms(self, alarms: list) -> None:
        """D39.4: attach burst alarms from index symbols to this tape."""
        self._proxy_alarms = list(alarms)
        self.reload_alarms()

    # ── D39 volume-burst alarms ──────────────────────────────────────────

    @property
    def _volume_baseline(self) -> VolumeBaselineService:
        """Shared baseline service (host-owned); per-session fallback."""
        vb = getattr(self._host, "volume_baseline", None)
        if vb is None:
            if self._vb_fallback is None:
                self._vb_fallback = VolumeBaselineService()
            vb = self._vb_fallback
        return vb

    def _prime_volume_baseline(self, resolved_key: str) -> None:
        """One-time prime of same-time-of-day buckets from BarCache."""
        vb = self._volume_baseline
        if vb.is_primed(resolved_key):
            return
        for timeframe in ("1 min", "5 mins", "15 mins", "1 hour"):
            bars = BarCache.get_bars(self.symbol, timeframe)
            if bars:
                vb.prime_from_bars(resolved_key, bars)
                return

    def _evaluate_burst_alarms(self, bar: Bar, is_new_candle: bool) -> None:
        """D39.3: per-push volume-burst evaluation alongside price alarms.

        The forming bar is *evaluated* every push (real-time burst
        detection, conservative early in the bar since its volume is still
        accumulating) but only *completed* bars are recorded into the
        baseline: when a new candle starts, the previous bar for that
        timeframe is complete.
        """
        burst_alarms = [
            a for a in self._alarms
            if a.kind == "volume_burst" and a.active and not a.triggered
        ]
        # Baseline bookkeeping runs even with no burst alarms so the
        # baseline is warm if one is created later.
        prev = self._burst_forming.get(bar.timeframe)
        self._burst_forming[bar.timeframe] = bar
        resolved_key = footprint_cache_key(self.symbol)
        # C39.2: the key embeds the front-month contract — a change means a
        # roll, so the old contract's baseline is invalidated, never reused.
        if self._burst_key != resolved_key:
            if self._burst_key is not None:
                self._volume_baseline.invalidate(self._burst_key)
            self._burst_key = resolved_key
        if is_new_candle and prev is not None and prev.ts != bar.ts:
            self._volume_baseline.record(
                resolved_key, prev.ts, prev.timeframe, prev.volume or 0.0)
        if not burst_alarms:
            return
        self._prime_volume_baseline(resolved_key)
        per_min = bar.volume / minutes_for_timeframe(bar.timeframe)
        baseline = self._volume_baseline.baseline(resolved_key, bar.ts)
        fired = evaluate_volume_burst(per_min, baseline, burst_alarms)
        for alarm in fired:
            if alarm.id is not None:
                AlarmStore.mark_triggered(alarm.id)
            alarm.triggered = True
        if fired:
            # Group by alarm symbol: proxy alarms (SPX on the ES tape)
            # toast under their own symbol, not the session's.
            by_symbol: dict[str, list] = {}
            for alarm in fired:
                by_symbol.setdefault(alarm.symbol, []).append(alarm)
            for sym, group in by_symbol.items():
                self.alarm_triggered.emit(sym, group)
            self.alarms_changed.emit()
            monitor = getattr(self._host, "alarm_monitor", None)
            if monitor is not None:
                monitor.on_alarm_changed()

    # ── Footprint (D36) ────────────────────────────────────────────────

    @property
    def _fp_host_managers(self):
        """(tick_history_manager, footprint_cache) from the host.

        Production MainWindow provides both; the tick manager talks to the
        real client, the cache persists to SQLite. Tests inject fakes on
        their stub host (fakes live in tests/ only — never here).
        """
        thm = getattr(self._host, "tick_history_manager", None)
        if thm is None:  # pragma: no cover - production always provides
            from ibkr.tick_history import TickHistoryManager
            thm = TickHistoryManager(getattr(self._host, "ib_client", None))
            self._host.tick_history_manager = thm
        cache = getattr(self._host, "footprint_cache", None)
        if cache is None:  # pragma: no cover - production always provides
            from data.db import db as _db
            from data.footprint_cache import FootprintCache
            cache = FootprintCache(_db.conn)
            self._host.footprint_cache = cache
        return thm, cache

    # -- enable / disable ------------------------------------------------

    def footprint_enable(self, style: str = "classic", metric: str = "volume",
                         timeframe: str = "5 mins") -> None:
        """Enable footprint for the chart timeframe (D36).

        Resolves the tape contract (index proxy), preloads the persistent
        cache, syncs the bar series into the service and starts the bounded
        backfill wave. Emits footprint_updated so the panel re-renders.
        """
        from ibkr.contracts import resolve_footprint_contract
        from data.footprint_cache import is_cacheable
        self._fp_enabled = True
        self._fp_style = style
        self._fp_metric = metric
        self._fp_timeframe = timeframe
        key, contract, label = resolve_footprint_contract(self.symbol)
        self._fp_cache_key = key
        self._fp_contract = contract
        self._fp_proxy_label = label
        self._fp_preload_cache(timeframe, is_cacheable(self.symbol))
        bars = self.get_bars(timeframe)
        if bars:
            self._footprint.sync_bars(bars, timeframe)
        self._fp_start_wave()
        self._fp_arm_forming_timer()
        self.footprint_updated.emit(timeframe)

    def footprint_resync(self, timeframe: str | None = None) -> None:
        """Idempotent re-entry for symbol/timeframe changes (D36).

        Re-resolves the tape contract (a new front month → new cache key →
        a fresh FootprintService, so old entries are never read for the new
        front month), re-syncs the current bar series and restarts the
        bounded wave if the backfill is idle. No-op when footprint is off.
        """
        if not self._fp_enabled:
            return
        from ibkr.contracts import resolve_footprint_contract
        from data.footprint_cache import is_cacheable
        tf = timeframe or self._fp_timeframe
        key, contract, label = resolve_footprint_contract(self.symbol)
        if key != self._fp_cache_key:
            # Contract rollover: fresh service, fresh cache preload.
            self._footprint = FootprintService(self.symbol)
            self._fp_cache_key = key
            self._fp_contract = contract
            self._fp_proxy_label = label
            self._fp_preload_cache(tf, is_cacheable(self.symbol))
        self._fp_timeframe = tf
        bars = self.get_bars(tf)
        if bars:
            self._footprint.sync_bars(bars, tf)
        if not self._fp_wave_active:
            self._fp_start_wave()
        self.footprint_updated.emit(tf)

    def footprint_disable(self) -> None:
        """Stop footprint: timers off, in-flight requests forgotten.

        Bucketed levels stay in the service (cheap); the persistent cache
        is untouched. Re-enabling re-syncs from the current series.
        """
        self._fp_enabled = False
        self._fp_wave_active = False
        self._fp_continue_timer.stop()
        self._fp_forming_timer.stop()

    def footprint_set_style(self, style: str, metric: str) -> None:
        """Display-style toggle × metric selector (D36, owner decision).

        Pure presentation — both metrics derive from the same tick buckets,
        so no refetch is needed; the panel just re-renders.
        """
        self._fp_style = style
        self._fp_metric = metric
        if self._fp_timeframe:
            self.footprint_updated.emit(self._fp_timeframe)

    @property
    def fp_style(self) -> str:
        return self._fp_style

    @property
    def fp_metric(self) -> str:
        return self._fp_metric

    @property
    def fp_enabled(self) -> bool:
        return self._fp_enabled

    @property
    def fp_proxy_label(self) -> str:
        """e.g. "ES tape" when viewing SPX; "" for own-tape symbols."""
        return self._fp_proxy_label

    def footprint_snapshot(self, timeframe: str) -> dict:
        """Data for the panel render layer: ready levels, per-bar states,
        the proxy label and the no-tick-data flag."""
        bars = self.get_bars(timeframe)
        levels = {}
        states = {}
        for bar in bars:
            lv = self._footprint.levels(bar.ts)
            if lv:
                levels[bar.ts] = lv
            states[bar.ts] = self._footprint.state(bar.ts)
        return {
            "levels": levels,
            "states": states,
            "proxy_label": self._fp_proxy_label,
            "no_tick_data": self._footprint.no_tick_data,
            "style": self._fp_style,
            "metric": self._fp_metric,
        }

    # -- cache preload / persist ------------------------------------------

    def _fp_preload_cache(self, timeframe: str, cacheable: bool) -> None:
        """Load persistent blobs for the series' dates before any backfill
        (36.4): a cache hit means zero IBKR requests for that symbol+date."""
        if not cacheable:
            return
        from zoneinfo import ZoneInfo
        from datetime import datetime
        _eastern = ZoneInfo("America/New_York")
        _, cache = self._fp_host_managers
        bars = self.get_bars(timeframe)
        if not bars:
            return
        by_date: dict[str, list[int]] = {}
        for bar in bars[:-1]:  # completed bars only
            day = datetime.fromtimestamp(
                bar.ts, tz=_eastern).strftime("%Y%m%d")
            by_date.setdefault(day, []).append(bar.ts)
        preloaded: dict[int, dict] = {}
        for day, ts_list in by_date.items():
            blob = cache.get(self._fp_cache_key, day, timeframe)
            if not blob:
                continue
            for ts in ts_list:
                if ts in blob:
                    preloaded[ts] = blob[ts]
        if preloaded:
            self._footprint.inject_cached(preloaded)

    def _fp_persist_cache(self, timeframe: str) -> None:
        """Write one blob per (contract, date, timeframe) on wave completion
        (36.4). Only for the five owner-approved symbols."""
        from data.footprint_cache import is_cacheable
        from zoneinfo import ZoneInfo
        if not is_cacheable(self.symbol):
            return
        _eastern = ZoneInfo("America/New_York")
        _, cache = self._fp_host_managers
        by_date: dict[str, dict] = {}
        for bar_ts in self._footprint.ready_bars():
            lv = self._footprint.levels(bar_ts)
            if not lv:
                continue
            day = datetime.fromtimestamp(
                bar_ts, tz=_eastern).strftime("%Y%m%d")
            by_date.setdefault(day, {})[bar_ts] = {
                str(price): vals for price, vals in lv.items()
            }
        for day, data in by_date.items():
            cache.put(self._fp_cache_key, day, timeframe, data)

    # -- backfill wave ------------------------------------------------------

    def _fp_start_wave(self) -> None:
        if not self._fp_enabled:
            return
        self._fp_wave_issued = 0
        self._fp_wave_active = True
        self._fp_pump()

    def _fp_pump(self) -> None:
        """Issue footprint page specs while the wave budget allows (≤60).

        Never sleeps: on PacingExceeded the remainder defers via singleShot
        (D28.3 pattern). When the burst is spent but bars remain pending, the
        continuation timer spaces the next wave.
        """
        if not self._fp_wave_active or not self._fp_enabled:
            return
        # A4: never issue while disconnected — the client no-ops with
        # wrapper.error(NO_VALID_ID), which cannot be routed back to this
        # session, stranding the specs (pending_count() > 0 forever,
        # forming refresh suppressed forever). Stop the wave here;
        # on_fp_reconnect() restarts it.
        if not getattr(self._host, "_ibkr_connected", True):
            self._fp_wave_active = False
            return
        from ibkr.pacing import pacing_manager
        while self._fp_wave_issued < MAX_REQUESTS_PER_WAVE:
            specs = self._footprint.next_wave(
                MAX_REQUESTS_PER_WAVE - self._fp_wave_issued)
            if not specs:
                break
            for spec in specs:
                if not self._fp_issue_spec(spec):
                    return  # pacing-exceeded → deferred; wave stays active
        self._fp_wave_active = False
        if self._footprint.pending_count() > 0:
            wait = pacing_manager.historical_wait_seconds()
            ms = max(1000, int(wait * 1000))
            self._status(
                f"{self.symbol} — footprint backfill continuing…")
            self._fp_continue_timer.start(ms)
        elif self._fp_timeframe:
            # Wave fully drained: persist the cacheable dates.
            self._fp_persist_cache(self._fp_timeframe)

    def _fp_issue_spec(self, spec) -> bool:
        """Issue one page spec.

        False → pacing exhausted (deferred via the continue timer; the wave
        stays active) OR unexpected failure (no client / not connected; the
        wave is stopped and the next enable/timeframe sync retries).
        """
        from ibkr.pacing import PacingExceeded, pacing_manager
        thm, _ = self._fp_host_managers
        try:
            req_id = thm.req_historical_ticks(
                self._fp_contract,
                startDateTime="",
                endDateTime=spec.end_str,
                numberOfTicks=1000,
                whatToShow=spec.what_to_show,
                useRTH=1,
            )
        except PacingExceeded as e:
            self._status(
                f"{self.symbol} — pacing-limited, "
                f"continuing footprint in {int(e.wait_seconds)}s…")
            self._fp_continue_timer.start(max(1000, int(e.wait_seconds * 1000)))
            return False
        except Exception:
            # B3: No client / not connected: stop the wave quietly; the next
            # enable or timeframe sync retries. Never raise into the UI.
            # Return False (not True): the spec was never issued, so
            # next_wave() would re-return it and _fp_pump would spin
            # forever on the main thread.
            self._fp_wave_active = False
            return False
        self._fp_wave_issued += 1
        self._footprint.note_issued(req_id, spec)
        self._host._register_req_id(req_id, self)
        return True

    def _on_fp_continue_timeout(self) -> None:
        self._fp_wave_active = True
        self._fp_pump()

    def _fp_cancel_inflight(self) -> None:
        thm, _ = self._fp_host_managers
        for req_id in list(self._footprint._req_to_spec):
            try:
                thm.cancel_historical_ticks(req_id)
            except Exception:
                pass
            self._host._unregister_req_id(req_id)
        self._footprint._req_to_spec.clear()

    def on_fp_disconnect(self) -> None:
        """A4: reset footprint wave state on a transport drop.

        In-flight tick requests will never be answered, and the client's
        ``wrapper.error(NO_VALID_ID)`` cannot be routed back to this
        session (reqId −1 is in no table) — so without a reset the specs
        would strand in ``_req_to_spec`` forever, ``pending_count()``
        would stay > 0, and the forming-bar refresh would be suppressed
        permanently. Drop the wave state now; queued jobs survive in the
        service and ``on_fp_reconnect`` restarts the wave.
        """
        self._fp_wave_active = False
        self._fp_continue_timer.stop()
        try:
            self._fp_cancel_inflight()
        except Exception:
            pass

    def on_fp_reconnect(self) -> None:
        """Restart the footprint backfill wave after a reconnect, when
        footprint is enabled and bars are still pending."""
        if (
            self._fp_enabled
            and not self._fp_wave_active
            and self._footprint.pending_count() > 0
        ):
            self._fp_start_wave()

    # -- bridge-routed callbacks (via MainWindow reqId routing) -------------

    def on_fp_ticks_bid_ask(self, req_id: int, ticks, done: bool) -> None:
        # Forming-bar refreshes are bound with FormingSpec — route first.
        if self.on_fp_forming_ticks(req_id, ticks, done, "BID_ASK"):
            return
        result = self._footprint.on_ticks_bid_ask(req_id, ticks, done)
        self._after_fp_page(req_id, result)

    def on_fp_ticks_last(self, req_id: int, ticks, done: bool) -> None:
        if self.on_fp_forming_ticks(req_id, ticks, done, "TRADES"):
            return
        result = self._footprint.on_ticks_last(req_id, ticks, done)
        self._after_fp_page(req_id, result)

    def _after_fp_page(self, req_id: int, result: dict) -> None:
        self._host._unregister_req_id(req_id)
        if not self._fp_enabled:
            return
        if result.get("completed") and self._fp_timeframe:
            self.footprint_updated.emit(self._fp_timeframe)
        # Keep pumping while the wave is active (followup pages count
        # against the same 60-request burst).
        if self._fp_wave_active:
            self._fp_pump()
        elif self._footprint.pending_count() == 0 and self._fp_timeframe:
            self._fp_persist_cache(self._fp_timeframe)

    def on_fp_error(self, req_id: int, code: int) -> bool:
        """Route an IBKR error on a footprint reqId. Returns True when the
        reqId belonged to footprint (handled). Error 162 (pacing) is left
        for the wave continuation; other errors fail the bar's phase so one
        bad bar never strands the wave."""
        spec = self._footprint.spec_for(req_id)
        if spec is None:
            return False
        # A2: forming specs must be unregistered + forgotten too — otherwise
        # the reqId leaks into _req_to_spec and the host table forever.
        # The next forming-timer tick re-issues the refresh.
        self._host._unregister_req_id(req_id)
        self._footprint.forget_request(req_id)
        if getattr(spec, "forming", False):
            return True
        job = self._footprint._jobs.get(spec.bar_ts)
        if job is not None and code != 162:
            # Fail the in-flight phase for this bar; the other phase (if any)
            # still completes and the bar renders with partial data.
            if spec.kind == "BID_ASK":
                job.bidask_cursor = None
            elif spec.kind == "TRADES":
                job.trades_cursor = None
        return True

    # -- viewport lazy-fill ---------------------------------------------------

    def sync_footprint_viewport(self, first_ts: int, last_ts: int) -> None:
        """Bars scrolled into view without data trigger a bounded fill."""
        if not self._fp_enabled:
            return
        queued = self._footprint.set_visible_range(first_ts, last_ts)
        if queued and not self._fp_wave_active:
            self._fp_start_wave()

    # -- forming-bar incremental refresh ----------------------------------------

    def _fp_arm_forming_timer(self) -> None:
        if not self._fp_enabled:
            return
        self._fp_forming_timer.start(int(FORMING_REFRESH_MIN_S * 1000))

    def _on_fp_forming_timeout(self) -> None:
        import time as _time
        if not self._fp_enabled:
            return
        # Re-arm first so the cadence holds even if this refresh skips.
        self._fp_forming_timer.start(int(FORMING_REFRESH_MIN_S * 1000))
        # A4: never issue while disconnected — the client no-ops with
        # wrapper.error(NO_VALID_ID), which cannot be routed back, so the
        # forming specs would strand in _req_to_spec. The wave restarts on
        # reconnect via on_fp_reconnect().
        if not getattr(self._host, "_ibkr_connected", True):
            return
        # Daily rollover check: a new front month (cache-key change) means
        # the old tape entries must never be read for the new front month.
        from ibkr.contracts import resolve_footprint_contract
        from data.footprint_cache import is_cacheable
        key, contract, label = resolve_footprint_contract(self.symbol)
        if key != self._fp_cache_key:
            self._footprint = FootprintService(self.symbol)
            self._fp_cache_key = key
            self._fp_contract = contract
            self._fp_proxy_label = label
            self._fp_preload_cache(self._fp_timeframe,
                                   is_cacheable(self.symbol))
            self._footprint.sync_bars(self.get_bars(self._fp_timeframe),
                                      self._fp_timeframe)
            self._fp_start_wave()
        if not self._footprint.forming_due(_time.time()):
            return  # backfill pending (yields) or <15s since last refresh
        window = self._footprint.forming_window()
        if window is None or self._fp_contract is None:
            return
        from ibkr.pacing import PacingExceeded, pacing_manager
        if pacing_manager.historical_wait_seconds() > 0:
            return  # skip silently; fills in on the next refresh
        thm, _ = self._fp_host_managers
        start_str, _ = window
        issued = 0
        for what in ("BID_ASK", "TRADES"):
            try:
                req_id = thm.req_historical_ticks(
                    self._fp_contract, startDateTime=start_str, endDateTime="",
                    numberOfTicks=1000, whatToShow=what, useRTH=1)
            except PacingExceeded:
                return
            except Exception:
                return
            # Forming refreshes are not wave members: bind directly with a
            # synthetic spec the service recognises as forming-only.
            self._footprint.note_issued(req_id, FormingSpec(what))
            self._host._register_req_id(req_id, self)
            issued += 1
        if issued:
            self._footprint.note_forming_refreshed(_time.time())

    def on_fp_forming_ticks(self, req_id: int, ticks, done: bool,
                            kind: str) -> bool:
        """Returns True when the reqId was a forming-bar refresh."""
        spec = self._footprint.spec_for(req_id)
        if not isinstance(spec, FormingSpec):
            return False
        self._host._unregister_req_id(req_id)
        self._footprint.forget_request(req_id)
        bar_ts = self._footprint.apply_forming_ticks(
            ticks, "BID_ASK" if spec.kind == "BID_ASK" else "TRADES")
        if bar_ts is not None and self._fp_timeframe:
            self.footprint_updated.emit(self._fp_timeframe)
        return True

    # ── Studies ──────────────────────────────────────────────────────

    @property
    def studies(self) -> list:
        return self._studies

    def set_studies(self, studies: list[dict]) -> None:
        """Replace the per-symbol study config; fan out to attached views."""
        from copy import deepcopy

        self._studies = deepcopy(studies)
        for view, _tf in self._views:
            try:
                view.set_studies(self._studies)
            except Exception:
                pass
        self.studies_changed.emit()

    # ── Drawings ─────────────────────────────────────────────────────

    def reload_drawings(self) -> None:
        """Reload drawings + groups from the store (chart (re)load)."""
        from data.drawing_store import DrawingStore

        self._drawings = DrawingStore.drawings_for_symbol(self.symbol)
        self._drawing_groups = DrawingStore.groups_for_symbol(self.symbol)
        self.drawings_changed.emit()

    def sync_drawings_to_views(self) -> None:
        """Push the current drawings/groups to all attached views."""
        for view, _tf in self._views:
            try:
                view.drawing_overlay.set_data(
                    self.symbol, self._drawings, self._drawing_groups
                )
            except Exception:
                pass

    def prepare_load(self, timeframe: str) -> None:
        """Reset per-load data-plane state for a (re)load of the chart.

        Fresh aggregator for the timeframe, no live bar observed yet
        (D27.1), and alarms reloaded from the store.
        """
        self.reset_aggregator(timeframe)
        self._rt_seen = False
        self.reload_alarms()

    def reset_aggregator(self, timeframe: str) -> BarAggregator:
        """Create a fresh aggregator for the timeframe, replacing any."""
        agg = BarAggregator(
            symbol=self.symbol,
            timeframe=timeframe,
            on_bar_update=self._on_aggregated_bar,
        )
        self._aggregators[timeframe] = agg
        return agg

    # ── History wave (3b-2 wires these up) ─────────────────────────────

    def _register_history_request(self, req_id: int) -> None:
        self._history_req_ids.add(req_id)
        self._history_req_generation[req_id] = self._history_generation
        self._host._register_req_id(req_id, self)

    def _history_event_accepted(self, req_id: int) -> bool:
        return (
            req_id in self._history_req_ids
            and self._history_req_generation.get(req_id)
            == self._history_generation
        )

    def _cancel_history_requests(self) -> None:
        for req_id in list(self._history_req_ids):
            self._host._unregister_req_id(req_id)
            try:
                self._host.md_manager.cancel_historical_data(req_id)
            except Exception:
                pass
        self._history_req_ids.clear()
        self._history_req_generation.clear()
        self._pending_bars = []

    def _arm_history_wave_watchdog(self) -> None:
        self._history_wave_timer.stop()
        self._history_wave_timer.start(self._history_wave_timeout_ms)

    def _disarm_history_wave_watchdog(self) -> None:
        self._history_wave_timer.stop()

    def _on_history_wave_timeout(self) -> None:
        self._host._on_session_history_wave_timeout(self)

    def _on_prime_timeout(self) -> None:
        self._host._on_session_prime_timeout(self)

    # ── D28.3 pacing-aware wave issuing ─────────────────────────────────

    def _status(self, msg: str, ms: int = 8000) -> None:
        """Best-effort status line (the host may be a stub in tests)."""
        bar = getattr(self._host, "status_bar", None)
        if bar is not None:
            bar.showMessage(msg, ms)

    def queue_wave_plans(self, plans, contract, timeframe: str,
                         extended_hours: bool) -> None:
        """D28.3: queue backfill plans and issue the first wave.

        Chunks are issued ~60 per wave; when the rolling 600s historical
        budget is exhausted the remainder stays queued and continues via
        the deferred timer (never sleeps, never storms TWS with 162s).
        """
        self._wave_plan_queue = list(plans)
        self._wave_contract = contract
        self._wave_timeframe = timeframe
        self._wave_extended_hours = extended_hours
        self._retried_plans = set()
        self._issue_wave_chunks()

    def _issue_wave_chunks(self, max_per_wave: int = 60) -> None:
        """Issue queued plans while the budget allows (D28.3)."""
        issued = 0
        while self._wave_plan_queue and issued < max_per_wave:
            plan = self._wave_plan_queue[0]
            try:
                req_id = self._host.md_manager.req_historical_data(
                    contract=self._wave_contract,
                    timeframe=self._wave_timeframe,
                    endDateTime=plan.endDateTime,
                    whatToShow="TRADES",
                    useRTH=1,
                    extended_hours=self._wave_extended_hours,
                    bar_size=plan.bar_size,
                    duration=plan.duration,
                )
            except PacingExceeded as e:
                self._schedule_wave_continuation(e.wait_seconds)
                return
            self._wave_plan_queue.pop(0)
            self._register_history_request(req_id)
            self._req_to_plan[req_id] = plan
            issued += 1
        if self._wave_plan_queue:
            # Hit the per-wave cap: space waves out over the rolling window.
            wait = pacing_manager.historical_wait_seconds()
            self._schedule_wave_continuation(max(wait, 1.0))

    def _schedule_wave_continuation(self, wait_s: float) -> None:
        """Defer the rest of the wave (D28.3): never sleeps, re-arms the
        watchdog so the deferred chunks don't trip the strand bound."""
        ms = max(1000, int(wait_s * 1000))
        self._status(
            f"{self.symbol} — pacing-limited, continuing backfill in "
            f"{int(wait_s)}s…"
        )
        self._arm_history_wave_watchdog()
        self._wave_continue_timer.start(ms)

    def _on_wave_continue_timeout(self) -> None:
        self._issue_wave_chunks()

    def _wave_may_complete(self) -> bool:
        """The wave finalises only when nothing is in flight AND nothing
        remains queued for continuation (D28.3)."""
        return not self._history_req_ids and not self._wave_plan_queue

    def register_history_request(self, req_id: int) -> None:
        """Public wrapper: track a backfill-wave member reqId."""
        self._register_history_request(req_id)

    def on_historical_bar(self, req_id: int, bar) -> None:
        """Route one historical bar: priming feeds the aggregator (D27.9),
        wave members append to _pending_bars (D16)."""
        if self._prime_req_id is not None and req_id == self._prime_req_id:
            agg = self._aggregators.get(self._prime_timeframe)
            if agg is not None:
                agg.push(
                    parse_ibkr_date(bar.date),
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    float(bar.volume),
                )
            return
        if not self._history_event_accepted(req_id):
            return
        ts = parse_ibkr_date(bar.date)
        self._pending_bars.append(Bar(
            symbol=self.symbol,
            timeframe=self._wave_timeframe or "",
            ts=ts,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=float(bar.volume),
        ))

    def on_historical_data_end(self, req_id: int) -> None:
        """Route an end marker: priming completion attaches the live feed;
        the last wave member triggers host finalization."""
        if self._prime_req_id is not None and req_id == self._prime_req_id:
            self._prime_req_id = None
            self._prime_timer.stop()
            self._host._on_session_prime_complete(self)
            return
        if not self._history_event_accepted(req_id):
            return
        self._history_req_ids.discard(req_id)
        self._req_to_plan.pop(req_id, None)
        if not self._wave_may_complete():
            return
        # Last member ended: the host finalizes (persist + render + status).
        self._host._on_session_wave_complete(self)

    def on_historical_error(self, req_id: int, code: int, msg: str) -> None:
        """D16: a failed wave member must not strand the wave. Drop it (so
        the set can still empty) and remember it for the shortfall report."""
        # D36: footprint reqIds fail their bar's phase without stranding
        # the footprint wave (handled → return).
        if self.on_fp_error(req_id, code):
            _LOG.warning(
                "Footprint request %s failed [%s]: %s", req_id, code, msg
            )
            return
        if self._prime_req_id is not None and req_id == self._prime_req_id:
            _LOG.warning(
                "Aggregator priming request %s failed [%s]: %s",
                req_id, code, msg,
            )
            self._prime_req_id = None
            self._prime_timer.stop()
            # Fail open: attach the live feed rather than strand the chart.
            self._host._on_session_prime_complete(self)
            return
        if req_id in self._history_req_ids:
            # D28.3: IBKR error 162 (pacing violation) retries once after a
            # backoff before the wave finalises short. The failed request
            # is dropped from the in-flight set; its plan is re-queued at
            # the front so the retry preserves newest-first order.
            if code == 162:
                plan = self._req_to_plan.pop(req_id, None)
                self._history_req_ids.discard(req_id)
                if plan is not None and plan not in self._retried_plans:
                    self._retried_plans.add(plan)
                    self._wave_plan_queue.insert(0, plan)
                    _LOG.warning(
                        "Historical request %s hit pacing violation (162); "
                        "retrying chunk once after backoff", req_id,
                    )
                    self._status(
                        f"{self.symbol} — pacing violation (162); "
                        "retrying chunk once…"
                    )
                    wait = pacing_manager.historical_wait_seconds()
                    self._wave_continue_timer.start(
                        max(1000, int(wait * 1000))
                    )
                    self._arm_history_wave_watchdog()
                    return
                _LOG.warning(
                    "Historical request %s failed [162] after retry; "
                    "finalising short", req_id,
                )
            self._history_req_ids.discard(req_id)
            self._req_to_plan.pop(req_id, None)
            self._backfill_failed_req_ids.add(req_id)
            _LOG.warning(
                "Historical request %s failed [%s]: %s", req_id, code, msg
            )
            if self._wave_may_complete():
                self._host._on_session_wave_complete(self)

    def prime_aggregator(self, contract, timeframe: str, now_ts: int,
                         extended_hours: bool) -> bool:
        """D27.9: fetch trailing 5-sec bars for the current partial period.

        Returns True when a priming request was issued — the caller must NOT
        attach the live feed yet; it attaches from on_historical_data_end,
        on_historical_error (fail-open), or the prime timeout backstop.
        Returns False when there is nothing to prime.
        """
        agg = self._aggregators.get(timeframe)
        if agg is None:
            return False
        period_s = TIMEFRAME_SECONDS.get(timeframe, 300)
        if period_s <= 5:
            return False
        span_s = now_ts - agg.period_start(now_ts)
        if span_s < 5:
            return False  # at a period boundary: nothing to prime
        prime_s = min(span_s, _PRIME_MAX_SPAN_S)
        try:
            req_id = self._host.md_manager.req_historical_data(
                contract=contract,
                timeframe=timeframe,
                endDateTime="",
                whatToShow="TRADES",
                useRTH=1,
                extended_hours=extended_hours,
                bar_size="5 secs",
                duration=f"{prime_s} S",
            )
        except PacingExceeded:
            # D28.3: fail open — skip priming and attach the live feed
            # rather than strand the chart on a pacing-limited request.
            _LOG.warning(
                "Aggregator priming skipped: historical pacing exhausted"
            )
            return False
        self._prime_req_id = req_id
        self._prime_timeframe = timeframe
        self._prime_symbol = self.symbol
        self._host._register_req_id(req_id, self)
        # Backstop: a priming request that never answers must not strand the
        # chart without a live feed.
        self._prime_timer.start(15_000)
        return True
