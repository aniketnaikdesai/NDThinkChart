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
import math
import time

from PyQt6.QtCore import QObject, pyqtSignal as Signal, QTimer

from data.bar_aggregator import BarAggregator, TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.alarm_store import AlarmStore
from data.models import Bar
from ibkr.contracts import get_contract_for_symbol
from ibkr.contracts import footprint_cache_key  # D39: resolved-contract key
from ibkr.error_codes import IBKRNotReady
from ibkr.pacing import PacingExceeded, pacing_manager
from ibkr.stream_health import StreamHealth
from ibkr.subscription_manager import RT_BARS
from ibkr.utils import parse_ibkr_date
from services.alarm_service import evaluate_alarms, evaluate_volume_burst
from services.backfill_service import floor_bar_budget  # D42/S18 cap budget
from services.volume_baseline import (
    VolumeBaselineService,
    minutes_for_timeframe,
)

# D27.9 / ESC-036: IBKR accepts `bar_size='5 secs'` historical requests only
# for a duration in [60 S, 3600 S]. The old ceiling of 7200 S asked for a
# combination IBKR rejects (TWS error 321 "Historical data requested duration
# is invalid"), which failed open and left the aggregator UNPRIMED on the
# '4 hours'/'1 day' timeframes. Clamp the priming span into the accepted
# window instead.
_PRIME_MIN_SPAN_S = 60
_PRIME_MAX_SPAN_S = 3_600
# D43/ESC-036 (second clause): the coarse timeframes ('4 hours' = 14400 s,
# '1 day' = 86400 s) have forming-period spans past the 3600 S ceiling that
# `'5 secs'` bars accept, so they cannot be primed with 5-second bars at all.
# They prime with `'1 min'` bars instead — IBKR accepts a `'1 min'` duration up
# to `'1 D'` — with the duration clamped into [60 S, 1 D].
_PRIME_MAX_SPAN_1MIN_S = 86_400

_LOG = logging.getLogger(__name__)

# Q-17: a pacing-limited backfill continuation must never fire exactly on the
# pacing gate. The reported wait is authoritative (ibkr.pacing pads the binding
# interval wait with a safety margin); the timer adds its own margin so an
# early-firing Qt coarse timer still lands past the gate. A residual wait under
# 0.2 s means this tick fired a hair early — re-tick in 50 ms instead of
# rescheduling another full second, which a coarse timer would miss again,
# leaving the wave permanently stalled ("continuing backfill in 0s…").
_NEAR_ZERO_WAIT_S = 0.2
_NEAR_ZERO_TICK_MS = 50
_CONTINUATION_MARGIN_MS = 50


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

    def __init__(self, symbol: str, host):
        super().__init__()
        self.symbol = symbol.upper()
        self._host = host  # MainWindow (duck-typed)
        self._views: list[tuple[object, str]] = []  # (view, timeframe)
        self.monitored: bool = False
        # D40: TWS-gone pause — when True, alarm evaluation (price +
        # burst) is skipped: no evaluation, no triggers, no phantoms.
        # Set by AlarmMonitor.pause_all(), cleared by resume_all().
        self.monitoring_paused: bool = False
        # D40: RT subscribe staged while TWS was gone; resume_all()
        # finishes it (reconcile skips already-monitored sessions).
        self._monitor_subscribe_pending: bool = False

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
        # D28.3/D42: the wave's mode — also the session's mode (S19). Every
        # mode-scoped cache read/write and floor-aware cap for this session
        # uses it, so an RTH and an ETH chart (primary vs pop-out) cannot
        # cross-contaminate.
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
        # ESC-036: the current period's start, so priming bars returned from
        # before it (the clamp can over-reach) are not replayed.
        self._prime_period_start: int | None = None
        self._prime_timer = QTimer(self)
        self._prime_timer.setSingleShot(True)
        self._prime_timer.timeout.connect(self._on_prime_timeout)
        # Q-3 (defect B): a pacing-limited priming request is deferred, not
        # skipped. The wait is non-zero for HISTORICAL_MIN_INTERVAL_S after ANY
        # historical request, so a load following a backfill wave almost always
        # hits it. At most ONE retry is in flight (`_prime_retry_pending`) and
        # it identifies itself by the explicit ``retrying=True`` argument — not
        # by instance state (Q-12: a mutable flag could be consumed by an
        # unrelated call, turning the retry into a first-time attempt that
        # logged the warning, restarted the backstop and re-armed itself).
        self._prime_retry_pending: bool = False
        self._prime_retry_args: tuple | None = None

        # ── Studies + drawings (3b-3) ──────────────────────────────────
        self._studies: list[dict] = []  # per-symbol study config
        self._study_cache: dict = {}
        self._drawings: list = []
        self._drawing_groups: list = []

        # ── S0 generic-tick substrate (D37) ───────────────────────────
        # One optional reqMktData per session; the generic list is the union
        # of registered feature needs.

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
            # D25: a view opening promotes a headless monitor.
            monitor = getattr(self._host, "alarm_monitor", None)
            if monitor is not None:
                monitor.on_session_attached(self)

    def detach_view(self, view) -> None:
        """Unregister a view; teardown when orphaned and not monitored."""
        self._views = [(v, tf) for v, tf in self._views if v is not view]
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
        self._prime_period_start = None
        # Q-3/Q-12: an orphaned deferred retry must not re-enter after teardown.
        self._prime_retry_pending = False
        self._prime_retry_args = None
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
        """Replace the in-memory series (capped). Emits bars_refreshed.

        D42/S18: the cap is the floor-aware :func:`floor_bar_budget` for the
        session's mode, not the flat ``SESSION_BAR_CAP`` — otherwise the
        ``AC-D16.8`` 30-session floor would be trimmed back out of memory.
        """
        cap = floor_bar_budget(timeframe, self._wave_extended_hours)
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
        # D42/S18: floor-aware, mode-scoped cap (see set_bars).
        cap = floor_bar_budget(timeframe, self._wave_extended_hours)
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
        triggered = []
        if not self.monitoring_paused:
            # D40: while TWS is gone, evaluation is fully paused — no
            # triggers, no phantom risk. (Data-plane updates below are
            # unaffected; no bars arrive while the feeds are dead.)
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
        if not self.monitoring_paused:
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
            bars = BarCache.get_bars(
                self.symbol, timeframe, ext_hours=self._wave_extended_hours
            )
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
        # Q-12: a reload supersedes the previous load's priming state — its
        # scheduled retry must be a no-op (never a second first-time attempt
        # that re-arms the backstop: the pacing-limited loop) and its stale
        # request/timeout must not push bars into the fresh aggregator or
        # fail open against the new load.
        self._prime_timer.stop()
        self._prime_req_id = None
        self._prime_period_start = None
        self._prime_retry_pending = False
        self._prime_retry_args = None
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
        # Q-3: the backstop fired (fail open) — cancel any deferred priming
        # retry so it cannot re-enter after the live feed has attached.
        self._prime_retry_pending = False
        self._prime_retry_args = None
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
            except (PacingExceeded, IBKRNotReady) as e:
                # IBKRNotReady carries no budget wait — retry shortly after
                # the handshake lands instead of hot-spinning.
                wait = getattr(e, "wait_seconds", None)
                if wait is None:
                    wait = 1.0
                self._schedule_wave_continuation(wait)
                return
            self._wave_plan_queue.pop(0)
            self._register_history_request(req_id)
            self._req_to_plan[req_id] = plan
            issued += 1
        if self._wave_plan_queue:
            # Hit the per-wave cap: space waves out over the rolling window.
            wait = pacing_manager.historical_wait_seconds()
            self._schedule_wave_continuation(max(wait, 1.0))

    def _continuation_delay_ms(self, wait_s: float) -> int:
        """Delay before re-issuing a deferred wave chunk (Q-17).

        The reported wait is authoritative: ``ceil + 50 ms`` guarantees the
        tick lands past the pacing gate even when the timer fires a few ms
        early. A near-zero residual means the previous tick was a hair early —
        retry on a short tick so the wave converges immediately instead of
        spinning on another full second (which would be early again).
        """
        wait_s = max(0.0, float(wait_s or 0.0))
        if wait_s < _NEAR_ZERO_WAIT_S:
            return _NEAR_ZERO_TICK_MS
        return int(math.ceil(wait_s * 1000.0)) + _CONTINUATION_MARGIN_MS

    @staticmethod
    def _format_wait(wait_s: float) -> str:
        """Human-readable wait for the status line — never a misleading '0s'."""
        if wait_s < 0.1:
            return "<0.1s"
        return f"{wait_s:.1f}s"

    def _schedule_wave_continuation(self, wait_s: float) -> None:
        """Defer the rest of the wave (D28.3): never sleeps, re-arms the
        watchdog so the deferred chunks don't trip the strand bound.

        Q-17: the wait is authoritative, not exact (see
        :meth:`_continuation_delay_ms`); a tick that lands a hair early retries
        on a short tick instead of rescheduling a full second forever.
        """
        wait_s = max(0.0, float(wait_s or 0.0))
        ms = self._continuation_delay_ms(wait_s)
        self._status(
            f"{self.symbol} — pacing-limited, continuing backfill in "
            f"{self._format_wait(wait_s)}…"
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
                ts = parse_ibkr_date(bar.date)
                # ESC-036: the clamp can over-reach — the 60 S floor pads a
                # short span up, so IBKR may return bars from BEFORE the current
                # period's start. Dropping them prevents ``BarAggregator.push``
                # from opening a fabricated previous-period candle (AC2).
                if (self._prime_period_start is None
                        or ts >= self._prime_period_start):
                    agg.push(
                        ts,
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
            self._prime_period_start = None
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
        if self._prime_req_id is not None and req_id == self._prime_req_id:
            _LOG.warning(
                "Aggregator priming request %s failed [%s]: %s",
                req_id, code, msg,
            )
            self._prime_req_id = None
            self._prime_period_start = None
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
                        self._continuation_delay_ms(wait)
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
                         extended_hours: bool,
                         retrying: bool = False) -> bool:
        """D27.9: fetch recent bars for the current partial period.

        The priming bar size follows the elapsed forming-period span
        (D43/ESC-036): the fine timeframes prime with `'5 secs'` bars (duration
        clamped into [60 S, 3600 S]) and the coarse timeframes ('4 hours'/
        '1 day'), whose spans exceed that ceiling, prime with `'1 min'` bars
        (duration clamped into [60 S, 1 D]).

        ``retrying=True`` marks the single deferred re-entry (Q-3/Q-12). It is
        an explicit argument, never inferred from instance state: a retry that
        is still pacing-limited can therefore never fall back into the
        first-time branch, reschedule itself or restart the backstop.

        Returns True when a priming request was issued (or a pacing-limited
        request was deferred with one scheduled retry) — the caller must NOT
        attach the live feed yet; it attaches from on_historical_data_end,
        on_historical_error (fail-open), the prime timeout backstop, or the
        failed deferred retry.
        Returns False when there is nothing to prime, or when the one allowed
        retry could not issue (the caller fails open).
        """
        if not retrying:
            # A fresh call supersedes any deferred retry an earlier load on
            # this session scheduled; its stale QTimer.singleShot no-ops.
            self._prime_retry_pending = False
            self._prime_retry_args = None
        agg = self._aggregators.get(timeframe)
        if agg is None:
            return False
        period_s = TIMEFRAME_SECONDS.get(timeframe, 300)
        if period_s <= 5:
            return False
        period_start = agg.period_start(now_ts)
        span_s = now_ts - period_start
        if span_s < 5:
            return False  # at a period boundary: nothing to prime
        # D43/ESC-036: pick the bar size from the span. A span up to the
        # '5 secs' ceiling stays on the fine branch (clamped into
        # [60 S, 3600 S]); a longer span (the coarse timeframes) uses
        # '1 min' bars clamped into [60 S, 1 D]. Either way the duration is
        # inside the accepted window for the chosen bar size, so IBKR never
        # rejects the request (error 321). A span below the floor is padded
        # up; the replay guard drops any resulting pre-period bars.
        if span_s <= _PRIME_MAX_SPAN_S:
            bar_size = "5 secs"
            prime_s = max(_PRIME_MIN_SPAN_S, min(span_s, _PRIME_MAX_SPAN_S))
        else:
            bar_size = "1 min"
            prime_s = max(_PRIME_MIN_SPAN_S, min(span_s, _PRIME_MAX_SPAN_1MIN_S))
        try:
            req_id = self._host.md_manager.req_historical_data(
                contract=contract,
                timeframe=timeframe,
                endDateTime="",
                whatToShow="TRADES",
                useRTH=1,
                extended_hours=extended_hours,
                bar_size=bar_size,
                duration=f"{prime_s} S",
            )
        except (PacingExceeded, IBKRNotReady) as e:
            if retrying:
                # Q-3/Q-12: the one allowed retry was also pacing-limited —
                # no issue, no reschedule, no timer restart. The retry caller
                # fails open (see :meth:`_on_prime_retry`).
                return False
            # Q-3 (defect B): DEFER, don't skip. historical_wait_seconds() is
            # non-zero for HISTORICAL_MIN_INTERVAL_S after ANY historical
            # request, so a load following a backfill wave almost always lands
            # here; skipping would drop the forming period's partial bars.
            # One scheduled retry, never a busy loop; the prime timeout stays
            # the backstop.
            wait_s = max(
                1.0, float(getattr(e, "wait_seconds", 0.0) or 0.0)
            )
            _LOG.warning(
                "Aggregator priming pacing-limited; retrying once in %.1fs",
                wait_s,
            )
            self._prime_retry_pending = True
            self._prime_retry_args = (contract, timeframe, extended_hours)
            self._prime_timer.start(15_000)
            QTimer.singleShot(
                max(1000, int(wait_s * 1000)), self._on_prime_retry
            )
            return True
        self._prime_req_id = req_id
        self._prime_timeframe = timeframe
        self._prime_symbol = self.symbol
        self._prime_period_start = period_start
        self._host._register_req_id(req_id, self)
        # Backstop: a priming request that never answers must not strand the
        # chart without a live feed.
        self._prime_timer.start(15_000)
        return True

    def _fail_open_prime(self) -> None:
        """Q-12: attach the live feed when priming cannot issue.

        Stops the 15 s backstop, drops every priming/retry marker (so neither
        the scheduled callback nor the timeout can act again) and tells the
        host the prime is over. Idempotent: state is cleared first.
        """
        self._prime_timer.stop()
        self._prime_req_id = None
        self._prime_period_start = None
        self._prime_retry_pending = False
        self._prime_retry_args = None
        _LOG.warning(
            "Aggregator priming retry did not issue; attaching live feed"
        )
        self._host._on_session_prime_complete(self)

    def _on_prime_retry(self) -> None:
        """Q-3 (defect B): the single deferred priming retry.

        Re-enters :meth:`prime_aggregator` with an EXPLICIT ``retrying=True``
        (Q-12) — the call cannot schedule another retry, restart the backstop
        or be mistaken for a first-time attempt. Only one retry is ever in
        flight; a teardown, a reload (``prepare_load``) or the prime-timeout
        backstop clears the flag, so a stale scheduled call is a no-op. When
        the retry cannot issue (pacing still closed, period boundary) the live
        feed is attached fail-open, exactly like the old skip path.
        """
        if not self._prime_retry_pending:
            return
        self._prime_retry_pending = False
        args = self._prime_retry_args
        self._prime_retry_args = None
        if args is None:
            return
        contract, timeframe, extended_hours = args
        if not self.prime_aggregator(
            contract, timeframe, int(time.time()), extended_hours,
            retrying=True,
        ):
            self._fail_open_prime()
