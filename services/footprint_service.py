"""Footprint aggregation service (D36, plan item 36.2). Qt-free.

Buckets historical ticks into the chart's bar boundaries to produce
per-price-level footprint data:

- BID_ASK ticks → ``{price: [bidVol, askVol]}`` (bid volume at the bid price,
  ask volume at the ask price; delta = askVol − bidVol per level)
- TRADES ticks  → ``{price: [tradeVol, tradeCount]}``

One dataset feeds both heatmap metrics (owner decision 2026-10-13): the
*volume* metric renders bid/ask size sums, the *tick-count* metric renders
the per-level trade count. Selecting a metric is pure presentation — zero
new requests either way.

Completed bars are backfilled with a **bounded wave** (≤60 requests/wave,
newest bars first — the visible viewport wins), paginating backward in
1000-tick windows until the bar's start is covered or a page returns
``done``. Bars entering the viewport without data trigger a bounded
lazy-fill. Per-bar states are structural: ``ready`` | ``loading`` |
``unavailable`` — the chart never blocks on footprint data.

The forming bar refreshes incrementally: re-issue the trailing window
(bar start → "") at most once per 15s per symbol, and only when no
completed-bar backfill is pending (forming yields to backfill, plan §7
priority order) and the shared historical budget has a free slot.

``reqTickByTickData`` is never used (AC-D36.3) — all data comes from
``reqHistoricalTicks`` pages issued by the owning session through
``ibkr/tick_history.py``.

No PyQt6 import appears anywhere in this module.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from ibapi.const import UNSET_DECIMAL

from data.bar_aggregator import TIMEFRAME_SECONDS

# ── Wave / refresh bounds (plan 36.2, binding) ───────────────────────────────
MAX_REQUESTS_PER_WAVE = 60
FORMING_REFRESH_MIN_S = 15.0
TICKS_PER_PAGE = 1000

# ── Per-bar states (structural loading) ──────────────────────────────────────
READY = "ready"
LOADING = "loading"
UNAVAILABLE = "unavailable"

# Consecutive completed bars whose first tick page comes back empty before
# the symbol is declared to have no tick history ("no tick data" state).
EMPTY_BARS_BEFORE_UNAVAILABLE = 3


def _num(value) -> float:
    """Decimal-safe float conversion; the UNSET_DECIMAL sentinel → 0.0."""
    if value is None or value == UNSET_DECIMAL:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def format_tick_end(ts: int) -> str:
    """Format a unix ts as IBKR ``yyyyMMdd-HH:mm:ss`` in UTC."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d-%H:%M:%S")


def bucket_bid_ask_levels(ticks, start_ts: int, end_ts: int) -> dict[float, list]:
    """Bucket BID_ASK ticks into ``{price: [bidVol, askVol]}``.

    Bid volume accrues at the tick's bid price, ask volume at its ask price.
    Ticks outside ``[start_ts, end_ts)`` are ignored (defensive: the last
    page of a backward pagination may overlap the window edge).
    """
    levels: dict[float, list] = {}
    for t in ticks:
        ts = int(t.time)
        if ts < start_ts or ts >= end_ts:
            continue
        bid = _num(t.sizeBid)
        ask = _num(t.sizeAsk)
        if bid:
            lvl = levels.setdefault(float(t.priceBid), [0.0, 0.0])
            lvl[0] += bid
        if ask:
            lvl = levels.setdefault(float(t.priceAsk), [0.0, 0.0])
            lvl[1] += ask
    return levels


def bucket_trade_levels(ticks, start_ts: int, end_ts: int) -> dict[float, list]:
    """Bucket TRADES ticks into ``{price: [tradeVol, tradeCount]}``."""
    levels: dict[float, list] = {}
    for t in ticks:
        ts = int(t.time)
        if ts < start_ts or ts >= end_ts:
            continue
        size = _num(t.size)
        lvl = levels.setdefault(float(t.price), [0.0, 0])
        lvl[0] += size
        lvl[1] += 1
    return levels


@dataclass
class PageSpec:
    """One historical-tick page request the session should issue."""

    kind: str  # "BID_ASK" | "TRADES"
    bar_ts: int
    end_str: str  # page backward from here; start_str is always ""
    what_to_show: str = "BID_ASK"


@dataclass
class FormingSpec:
    """Marker spec for forming-bar refresh requests (not wave members).

    The session binds these directly; ``_on_page`` ignores them — the
    session routes forming ticks through ``apply_forming_ticks``.
    """

    kind: str  # "BID_ASK" | "TRADES"
    forming: bool = True


@dataclass
class _BarJob:
    bar_ts: int
    start_ts: int
    end_ts: int
    # Pagination cursors: the endDateTime for the next page of each phase,
    # or None when that phase is complete. Both phases always run — the
    # requirements mandate bid/ask volumes AND trade volume per bar, so the
    # heatmap metric selector stays pure presentation (zero new requests).
    bidask_cursor: str | None = None
    trades_cursor: str | None = None
    first_page_empty: bool = False

    def __post_init__(self):
        if self.bidask_cursor is None:
            self.bidask_cursor = format_tick_end(self.end_ts)
        if self.trades_cursor is None:
            self.trades_cursor = format_tick_end(self.end_ts)

    @property
    def done(self) -> bool:
        return self.bidask_cursor is None and self.trades_cursor is None

    def next_spec(self) -> PageSpec | None:
        if self.bidask_cursor is not None:
            return PageSpec("BID_ASK", self.bar_ts, self.bidask_cursor, "BID_ASK")
        if self.trades_cursor is not None:
            return PageSpec("TRADES", self.bar_ts, self.trades_cursor, "TRADES")
        return None


class FootprintService:
    """Per-symbol footprint aggregation and backfill planning (D36.2).

    The owning ``TickerSession`` drives the Qt side: it calls ``sync_bars``
    when the series changes, issues ``next_wave()`` specs through
    ``TickHistoryManager``, and forwards bridge callbacks into ``on_ticks_*``.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self._jobs: dict[int, _BarJob] = {}          # bar_ts -> job
        self._queue: deque[int] = deque()            # bar_ts, newest first
        self._levels: dict[int, dict[float, list]] = {}  # bar_ts -> merged levels
        # merged level: [bidVol, askVol, tradeVol, tradeCount]
        self._req_to_spec: dict[int, object] = {}   # reqId -> PageSpec|FormingSpec
        self._unavailable_bars: set[int] = set()
        self._no_tick_data: bool = False
        self._empty_streak: int = 0
        self._timeframe: str = "5 mins"
        self._last_forming_refresh: float = 0.0
        self._forming_bar_ts: int | None = None

    # ── Series sync ──────────────────────────────────────────────────────

    def inject_cached(self, levels: dict[int, dict]) -> None:
        """Preload levels restored from the persistent cache (36.4).

        Must be called before ``sync_bars`` — preloaded bars are skipped
        when queueing backfill jobs, so a cache hit means zero IBKR requests.
        """
        for bar_ts, lv in levels.items():
            if bar_ts not in self._levels:
                self._levels[bar_ts] = lv

    def sync_bars(self, bars, timeframe: str) -> None:
        """(Re)register the bar series; queue jobs for completed bars that
        lack footprint data. The last bar is the forming bar — it is never
        backfilled (it uses the incremental refresh path)."""
        self._timeframe = timeframe
        if not bars:
            return
        period = TIMEFRAME_SECONDS.get(timeframe, 300)
        completed = bars[:-1]
        live_ts = {b.ts for b in bars}
        # Drop jobs for vanished bars.
        for ts in list(self._jobs):
            if ts not in live_ts:
                self._jobs.pop(ts, None)
                self._levels.pop(ts, None)
                self._unavailable_bars.discard(ts)
        if completed:
            self._forming_bar_ts = bars[-1].ts
        # Queue newest-first among completed bars missing data.
        for i in range(len(completed) - 1, -1, -1):
            bar = completed[i]
            if bar.ts in self._levels or bar.ts in self._jobs:
                continue
            if bar.ts in self._unavailable_bars:
                continue
            end_ts = completed[i + 1].ts if i + 1 < len(completed) else bar.ts + period
            self._jobs[bar.ts] = _BarJob(
                bar_ts=bar.ts,
                start_ts=bar.ts,
                end_ts=end_ts,
            )
        self._rebuild_queue()

    def set_visible_range(self, first_ts: int, last_ts: int) -> int:
        """Viewport sync (lazy-fill on scroll): missing bars inside the
        visible range jump to the front of the queue, newest first.
        Returns the number of bars queued by this call."""
        queued = 0
        for ts in sorted(self._jobs, reverse=True):
            if self._jobs[ts].done:
                continue
            if first_ts <= ts <= last_ts and ts not in self._queue:
                queued += 1
        self._rebuild_queue(first_ts, last_ts)
        return queued

    def _rebuild_queue(
        self, first_ts: int | None = None, last_ts: int | None = None
    ) -> None:
        visible: list[int] = []
        rest: list[int] = []
        for ts in sorted(self._jobs, reverse=True):
            job = self._jobs[ts]
            if job.done or ts in self._unavailable_bars:
                continue
            if first_ts is not None and first_ts <= ts <= last_ts:
                visible.append(ts)
            else:
                rest.append(ts)
        self._queue = deque(visible + rest)

    # ── Wave planning ────────────────────────────────────────────────────

    def pending_count(self) -> int:
        """Bars still needing at least one page."""
        return sum(1 for ts in self._queue if not self._jobs[ts].done)

    def next_wave(self, max_requests: int = MAX_REQUESTS_PER_WAVE) -> list[PageSpec]:
        """Pop up to ``max_requests`` page specs, newest bars first.

        At most one spec per bar per call — the next page's cursor is only
        known after the callback arrives, so re-issuing for the same bar
        must wait. Bars with an already-outstanding spec are skipped (their
        followup arrives via ``_on_page``). Pure planning — the session
        issues each spec and calls ``note_issued``. The 60-request wave cap
        is binding (plan 36.2).
        """
        specs: list[PageSpec] = []
        outstanding_bars = {
            s.bar_ts for s in self._req_to_spec.values()
            if isinstance(s, PageSpec)
        }
        kept: deque[int] = deque()
        for ts in self._queue:
            job = self._jobs.get(ts)
            if job is None or job.done:
                continue
            if len(specs) < max_requests and ts not in outstanding_bars:
                spec = job.next_spec()
                if spec is not None:
                    specs.append(spec)
                    outstanding_bars.add(ts)
            kept.append(ts)
        self._queue = kept
        return specs

    def note_issued(self, req_id: int, spec: PageSpec) -> None:
        self._req_to_spec[req_id] = spec

    def forget_request(self, req_id: int) -> None:
        self._req_to_spec.pop(req_id, None)

    def spec_for(self, req_id: int):
        """Return the bound spec for a reqId, or None (stale reqId)."""
        return self._req_to_spec.get(req_id)

    # ── Tick callbacks ───────────────────────────────────────────────────

    def on_ticks_bid_ask(self, req_id: int, ticks, done: bool) -> dict:
        return self._on_page(req_id, ticks, done, "BID_ASK")

    def on_ticks_last(self, req_id: int, ticks, done: bool) -> dict:
        return self._on_page(req_id, ticks, done, "TRADES")

    def _on_page(self, req_id: int, ticks, done: bool, kind: str) -> dict:
        """Bucket one page; drive pagination. Returns
        ``{"completed": [bar_ts...], "followup": PageSpec | None}``."""
        result: dict = {"completed": [], "followup": None}
        spec = self._req_to_spec.pop(req_id, None)
        if spec is None or isinstance(spec, FormingSpec):
            return result  # stale reqId, or a forming refresh the
            # session routes through apply_forming_ticks
        bar_ts = spec.bar_ts
        job = self._jobs.get(bar_ts)
        if job is None:
            return result
        ticks = list(ticks or [])
        if kind == "BID_ASK":
            page_levels = bucket_bid_ask_levels(ticks, job.start_ts, job.end_ts)
            self._merge(bar_ts, page_levels, kind="bidask")
            if not ticks and not job.first_page_empty and self._is_first_page(job, kind):
                job.first_page_empty = True
                self._empty_streak += 1
                if self._empty_streak >= EMPTY_BARS_BEFORE_UNAVAILABLE:
                    self._declare_no_tick_data()
                    return result
            elif ticks:
                self._empty_streak = 0
        else:
            page_levels = bucket_trade_levels(ticks, job.start_ts, job.end_ts)
            self._merge(bar_ts, page_levels, kind="trades")

        followup = self._advance(job, ticks, done, kind)
        result["followup"] = followup
        if job.done:
            result["completed"].append(bar_ts)
            self._queue = deque(ts for ts in self._queue if ts != bar_ts)
            if bar_ts not in self._levels:
                # A3: a completed bar with zero levels must not read as
                # LOADING forever — move it to the unavailable set so
                # state() reports UNAVAILABLE.
                self._unavailable_bars.add(bar_ts)
                self._jobs.pop(bar_ts, None)
        return result

    def _is_first_page(self, job: _BarJob, kind: str) -> bool:
        expected = format_tick_end(job.end_ts)
        if kind == "BID_ASK":
            return job.bidask_cursor == expected
        return job.trades_cursor == expected

    def _advance(
        self, job: _BarJob, ticks: list, done: bool, kind: str
    ) -> PageSpec | None:
        """Backward-pagination driver: full page + not done + earliest tick
        still after the bar start → next page ends 1s before the earliest
        tick seen. Anything else completes the phase (AC-D36.2: no gaps —
        pages overlap at most at the 1s step, never skip)."""
        attr = "bidask_cursor" if kind == "BID_ASK" else "trades_cursor"
        if done or not ticks or len(ticks) < TICKS_PER_PAGE:
            setattr(job, attr, None)
            return None
        earliest = min(int(t.time) for t in ticks)
        if earliest <= job.start_ts:
            setattr(job, attr, None)
            return None
        cursor = format_tick_end(earliest - 1)
        setattr(job, attr, cursor)
        return PageSpec(kind, job.bar_ts, cursor, kind)

    def _merge(self, bar_ts: int, page_levels: dict, kind: str) -> None:
        if not page_levels:
            return  # never create an empty entry: a dataless bar must not
            # read as "ready" (it would mask the unavailable state).
        merged = self._levels.setdefault(bar_ts, {})
        for price, vals in page_levels.items():
            slot = merged.setdefault(price, [0.0, 0.0, 0.0, 0])
            if kind == "bidask":
                slot[0] += vals[0]
                slot[1] += vals[1]
            else:
                slot[2] += vals[0]
                slot[3] += vals[1]

    def _declare_no_tick_data(self) -> None:
        """The symbol has no tick history: mark every queued bar unavailable
        and stop requesting (the UI shows the "no tick data" state)."""
        self._no_tick_data = True
        for ts in self._jobs:
            self._unavailable_bars.add(ts)
        self._queue.clear()
        self._req_to_spec.clear()

    def mark_no_tick_data(self) -> None:
        """Explicit signal (e.g. IBKR error on the tick request): the symbol
        has no usable tick history."""
        self._declare_no_tick_data()

    # ── Reads ────────────────────────────────────────────────────────────

    def levels(self, bar_ts: int) -> dict[float, list] | None:
        """Merged per-level ``[bidVol, askVol, tradeVol, tradeCount]``."""
        return self._levels.get(bar_ts)

    def state(self, bar_ts: int) -> str:
        if self._levels.get(bar_ts):  # non-empty levels → ready
            return READY
        if self._no_tick_data or bar_ts in self._unavailable_bars:
            return UNAVAILABLE
        # A5: the forming bar is never a wave member (no _BarJob), so without
        # this it would read UNAVAILABLE before its first refresh — it is
        # LOADING until data (or no-tick-data) says otherwise.
        if bar_ts == self._forming_bar_ts or bar_ts in self._jobs:
            return LOADING
        return UNAVAILABLE

    @property
    def no_tick_data(self) -> bool:
        return self._no_tick_data

    def ready_bars(self) -> list[int]:
        return sorted(self._levels)

    # ── Forming-bar refresh ──────────────────────────────────────────────

    def forming_due(self, now_s: float) -> bool:
        """True when the forming bar may be refreshed: 15s cadence AND no
        completed-bar backfill pending (forming yields to backfill, §7)."""
        if self._forming_bar_ts is None:
            return False
        if self.pending_count() > 0:
            return False
        return (now_s - self._last_forming_refresh) >= FORMING_REFRESH_MIN_S

    def forming_window(self) -> tuple[str, str] | None:
        """(start_str, end_str) for the trailing-window refresh of the
        forming bar, or None when no forming bar is known."""
        if self._forming_bar_ts is None:
            return None
        return format_tick_end(self._forming_bar_ts), ""

    def note_forming_refreshed(self, now_s: float) -> None:
        self._last_forming_refresh = now_s

    def apply_forming_ticks(self, ticks, kind: str) -> int | None:
        """Re-bucket the forming bar from a fresh trailing-window page
        (the window is re-issued whole each refresh, so replace, don't
        accumulate). Returns the forming bar_ts, or None if unknown."""
        if self._forming_bar_ts is None:
            return None
        period = TIMEFRAME_SECONDS.get(self._timeframe, 300)
        start, end = self._forming_bar_ts, self._forming_bar_ts + period
        if kind == "BID_ASK":
            page = bucket_bid_ask_levels(ticks or [], start, end)
            kind_tag = "bidask"
        else:
            page = bucket_trade_levels(ticks or [], start, end)
            kind_tag = "trades"
        merged: dict[float, list] = {}
        for price, vals in page.items():
            slot = [0.0, 0.0, 0.0, 0]
            if kind_tag == "bidask":
                slot[0], slot[1] = vals[0], vals[1]
            else:
                slot[2], slot[3] = vals[0], vals[1]
            merged[price] = slot
        self._levels[self._forming_bar_ts] = merged
        return self._forming_bar_ts
