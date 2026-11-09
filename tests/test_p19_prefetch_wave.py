"""P19-T2 — ordinary-wave prefetch issuance with coalesce seam (D58.2), offscreen.

Proves the P19-2 issuance seam on a real, shown ``MainWindow`` with stubbed
transport and clock control (``IBApiClient.connect`` monkeypatched, the
market-data managers stubbed), consuming the P19-T1 fire decision:

* T01 — ordinary-wave lifecycle: a fired trigger issues exactly one planner
  window through ``queue_wave_plans``; a second trigger for the same triple
  never puts a second wave in flight; pacing defers (never fails) with the
  watchdog covering wait + margin; the watchdog strand finalizes; the D53
  indicator raises on issue and idles on every terminal path; the D56 162
  retry and the silence retry each fire exactly once per chunk; late arrivals
  after a generation bump are fenced.
* T02 — DG111 coalesce seam: a mid-wave second trigger never cancels the
  running wave and sets the pending-prefetch marker; completion consumes the
  marker with a fresh-viewport re-evaluation (multi-step chain while
  fetchable); the marker is cleared on completion/strand/cancel/disconnect;
  mode-switch/symbol-switch/disconnect abandon the wave plus the marker with
  no bars leaking across triples; a nothing-fetchable trigger issues no wave
  and an empty answer finalizes one shortfall with no retry loop.

No test here weakens, skips or rewrites an existing test. P19-T1
(``tests/test_p19_prefetch_trigger.py``) stays decision-only and green.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.market_calendar import is_trading_day
from ui.ticker_session import TickerSession

EASTERN = ZoneInfo("America/New_York")

TF = "5 mins"
CHAIN_TF = "4 hours"


def _duration_seconds(duration: str) -> int:
    units = {"S": 1, "D": 86_400, "W": 7 * 86_400, "M": 30 * 86_400,
             "Y": 365 * 86_400}
    token = (duration or "").strip().upper()
    if token and token[-1] in units and token[:-1].strip().isdigit():
        return int(token[:-1]) * units[token[-1]]
    return int(token)

_NOW = None  # fixed per test via _now_ts()


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _parse_end(end: str) -> int:
    """Parse a planned IBKR ``endDateTime`` (``yyyyMMdd-HH:mm:ss`` UTC)."""
    from datetime import timezone

    return int(
        datetime.strptime(end, "%Y%m%d-%H:%M:%S").replace(
            tzinfo=timezone.utc).timestamp()
    )


def _trading_days_back(end: date, n: int) -> list[date]:
    assert is_trading_day(end)
    days = [end]
    while len(days) < n:
        days.append(_prev_trading_day(days[-1]))
    return sorted(days)


def _prev_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _session_bars(symbol: str, day: date, tf: str = TF,
                  base: float = 100.0) -> list[Bar]:
    """One complete ETH session (04:00-20:00) of ``tf`` bars, like the feed."""
    if not is_trading_day(day):
        return []
    period = TIMEFRAME_SECONDS[tf]
    start = _et_ts(day.year, day.month, day.day, 4, 0)
    close = _et_ts(day.year, day.month, day.day, 20, 0)
    bars: list[Bar] = []
    ts, i = start, 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(Bar(symbol, tf, ts, price, price + 0.5, price - 0.5,
                        price, 1000.0 + (ts % 500)))
        ts += period
        i += 1
    assert bars, f"no {tf} bars for {day}"
    return bars


def _seed_days(symbol: str, days: list[date], tf: str = TF,
               base: float = 100.0) -> None:
    bars: list[Bar] = []
    for i, d in enumerate(days):
        bars.extend(_session_bars(symbol, d, tf, base + i))
    BarCache.save_bars(bars)


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _ReqStub:
    """Captures ``req_historical_data`` calls and cancelled reqIds."""

    def __init__(self, first_id: int = 5000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id
        self.fail_next: Exception | None = None

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None):
        if self.fail_next is not None:
            exc, self.fail_next = self.fail_next, None
            raise exc
        req_id = self._next
        self._next += 1
        self.calls.append({
            "reqId": req_id,
            "contract": contract,
            "timeframe": timeframe,
            "endDateTime": endDateTime,
            "whatToShow": whatToShow,
            "useRTH": useRTH,
            "extended_hours": extended_hours,
            "bar_size": bar_size,
            "duration": duration,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    return win


def _setup(monkeypatch, qapp, symbol: str, now_ts: int, tf: str = TF):
    """Window with stubbed transport, current triple fixed, no load issued."""
    win = _make_window(monkeypatch, qapp)
    stub = _ReqStub()
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win._current_symbol = symbol
    win._current_tf = tf
    # The toolbar widgets always mirror the current triple after a real load
    # (load_chart reads them on widget-driven reloads, e.g. the ext-hours
    # toggle path with no explicit args). Sync them here so widget-driven
    # reloads resolve the same triple the test established directly.
    win.symbol_input.setText(symbol)
    idx = win.tf_combo.findText(tf)
    if idx >= 0:
        win.tf_combo.setCurrentIndex(idx)
    win.ext_hours_btn.setChecked(True)
    win._now_ts = lambda: now_ts
    session = win.get_or_create_session(symbol)
    return win, stub, session


def _drive_new_calls(win, stub, expected: list[Bar],
                     calls: list[dict], tf: str = TF) -> set[int]:
    """Deliver ``expected`` bars through each call's window, then end it."""
    chunk_seconds = _duration_seconds(TIMEFRAME_CONFIG[tf]["duration"])
    delivered: set[int] = set()
    for call in calls:
        if call.get("bar_size") == "5 secs":
            continue
        rid = call["reqId"]
        anchor = _parse_end(call["endDateTime"])
        lo, hi = anchor - chunk_seconds, anchor
        for bar in expected:
            if bar.ts in delivered:
                continue
            if lo < bar.ts <= hi:
                win._on_historical_bar(
                    rid, _FakeIbBar(bar.ts, bar.close, bar.volume))
                delivered.add(bar.ts)
        win._on_historical_data_end(rid)
    return delivered


def _hole_fixture(symbol: str, now_ts: int, hole_days: int,
                  recent_days: int = 5, older_days: int = 5,
                  tf: str = TF) -> tuple[list[date], list[date], int]:
    """Seed ``recent_days`` complete days ending at now's week plus an
    ``older_days`` complete block, with a ``hole_days``-long trading-day
    hole directly between them (interior, so the planner reports it).
    Returns (hole, recent, now_ts)."""
    now_day = _et_date(now_ts)
    recent = _trading_days_back(now_day, recent_days)
    hole: list[date] = []
    cur = _prev_trading_day(recent[0])
    while len(hole) < hole_days:
        hole.append(cur)
        cur = _prev_trading_day(cur)
    hole = sorted(hole)
    older: list[date] = []
    cur = _prev_trading_day(hole[0])
    while len(older) < older_days:
        older.append(cur)
        cur = _prev_trading_day(cur)
    older = sorted(older)
    _seed_days(symbol, recent, base=200.0, tf=tf)
    _seed_days(symbol, older, base=100.0, tf=tf)
    return hole, recent, now_ts


def _expected_bars(symbol: str, days: list[date],
                   tf: str = TF) -> list[Bar]:
    bars: list[Bar] = []
    for d in days:
        bars.extend(_session_bars(symbol, d, tf))
    return bars


def _recent_edge(symbol: str, recent: list[date], tf: str = TF) -> int:
    """First bar of the recent block's oldest day (the fire-shaped report)."""
    day0 = [b.ts for b in BarCache.get_bars(symbol, tf)
            if _et_date(b.ts) == recent[0]]
    return min(day0)


# ---------------------------------------------------------------------------
# T01 — ordinary-wave lifecycle
# ---------------------------------------------------------------------------
def _one_chunk_hole(monkeypatch, qapp, symbol: str):
    """A 1-trading-day hole (one 30 D planner step) with 5 recent days and a
    3-day older block.

    The settled report sits at the recent edge (just newer than the hole) —
    the P19-T1 fire shape: within-T of the cache edge (the oldest cached day
    is 4 sessions back, inside the 5-session ``5 mins`` table entry) with the
    next older step fetchable.
    """
    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=1,
                                    older_days=3)
    recent_bars = BarCache.get_bars(symbol, TF)
    recent_day0 = [b.ts for b in recent_bars
                   if _et_date(b.ts) == recent[0]]
    visible = min(recent_day0)
    return win, stub, session, now_ts, hole, visible


def test_t01_single_step_issue_and_in_flight_cap(monkeypatch, qapp):
    """T01: exactly one planner window issued; a second wave never in flight;
    D53 raises; the watchdog arms the 120 s window-relative bound."""
    win, stub, session, _now, hole, visible = _one_chunk_hole(
        monkeypatch, qapp, "P19W_A")
    try:
        assert win.maybe_prefetch(visible, False) is True
        win._on_viewport_settled(visible, False)
        # Exactly one planner window through the existing wave path.
        assert len(stub.calls) == 1
        call = stub.calls[0]
        assert call["timeframe"] == TF
        assert call["duration"] == TIMEFRAME_CONFIG[TF]["duration"]
        assert session._wave_plan_queue == []
        (rid,) = tuple(session._history_req_ids)
        assert rid == call["reqId"]
        # D53 raises on issue (in-flight, never complete while running).
        assert win._backfill_state is not None
        assert win._backfill_state["in_flight"] == 1
        assert "idle" not in win._backfill_indicator.text()
        # 120 s watchdog armed (one fifth of the 600 s budget window).
        assert session._history_wave_bound_ms == 120_000
        assert session._history_wave_timer.isActive()
        # A second fired trigger for the same triple issues nothing.
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        assert set(session._history_req_ids) == {rid}
        assert session._pending_prefetch is True
        assert stub.cancelled == []
        # The issued plan is the planner's own step for the hole.
        from services.backfill_service import find_missing_spans, plan_requests

        cached_ts = [b.ts for b in BarCache.get_bars("P19W_A", TF)]
        spans = find_missing_spans(
            cached_ts, _now, TF, trailing_days=60, ext_hours=True)
        plans = plan_requests(spans, TF)
        assert len(plans) == 1
        assert session._req_to_plan[rid] == plans[0]

        # Drive the chunk: completes, indicator idles, marker stays clear.
        expected = _expected_bars("P19W_A", hole)
        delivered = _drive_new_calls(win, stub, expected, stub.calls)
        assert delivered == {b.ts for b in expected}
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert win._backfill_state is None
        assert len(stub.calls) == 1  # no chained wave: nothing left fetchable
    finally:
        win.close()


def test_t01_pacing_defers_with_watchdog_cover(monkeypatch, qapp):
    """T01: a pacing-limited issue defers (fail-open) with the watchdog
    covering wait + margin; the continuation then issues the single step."""
    from ibkr.pacing import PacingExceeded

    win, stub, session, _now, hole, visible = _one_chunk_hole(
        monkeypatch, qapp, "P19W_B")
    try:
        stub.fail_next = PacingExceeded(200.0)
        win._on_viewport_settled(visible, False)
        # Nothing issued, nothing failed: the plan waits its turn.
        assert stub.calls == []
        assert session._history_req_ids == set()
        assert len(session._wave_plan_queue) == 1
        assert session._wave_continue_timer.isActive()
        # The watchdog covers the deferral + margin (never a false strand).
        assert session._history_wave_bound_ms == 200_000 + 30_000
        # D53 still raises for the queue-only wave.
        assert win._backfill_state is not None
        assert win._backfill_state["queued"] == 1
        # The continuation issues the single step once the budget clears.
        session._on_wave_continue_timeout()
        assert len(stub.calls) == 1
        assert len(session._history_req_ids) == 1
        assert session._wave_plan_queue == []
    finally:
        win.close()


def test_t01_162_retries_exactly_once(monkeypatch, qapp):
    """T01: D56 162 axis — one retry of the identical plan, then a short
    finalise with no third issue."""
    win, stub, session, _now, hole, visible = _one_chunk_hole(
        monkeypatch, qapp, "P19W_C")
    try:
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        plan = session._req_to_plan[rid]
        # First 162: re-queue at the front, retry via the continuation path.
        win._on_error(rid, 162, "pacing violation")
        assert plan in session._retried_plans
        session._on_wave_continue_timeout()
        assert len(stub.calls) == 2
        (rid2,) = tuple(session._history_req_ids)
        assert rid2 != rid
        assert session._req_to_plan[rid2] == plan
        # Second 162 for the same plan: finalise short, never a third issue.
        win._on_error(rid2, 162, "pacing violation")
        assert len(stub.calls) == 2
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert win._backfill_indicator.text() == "Backfill: idle"
        # Terminal state is the AC-D16.4 shortfall (the failed plan's day is
        # still missing), not a transient error line.
        assert "still missing" in win.status_bar.currentMessage()
    finally:
        win.close()


def test_t01_silence_retries_exactly_once(monkeypatch, qapp):
    """T01: D56 silence axis — one retry per still-silent chunk (clock
    controlled), never a third issue for the retried plan."""
    win, stub, session, _now, hole, visible = _one_chunk_hole(
        monkeypatch, qapp, "P19W_D")
    try:
        clock = [1000.0]
        monkeypatch.setattr(session, "_silence_now", lambda: clock[0])
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        plan = session._req_to_plan[rid]
        # 31 s of silence: cancel + re-issue the identical plan exactly once.
        clock[0] = 1031.0
        session._sweep_silent_chunks()
        assert stub.cancelled == [rid]
        assert len(stub.calls) == 2
        (rid2,) = tuple(session._history_req_ids)
        assert rid2 != rid
        assert session._req_to_plan[rid2] == plan
        assert plan in session._retried_plans
        # The re-issue's own silence never re-issues (shared allowance).
        clock[0] = 1075.0
        session._sweep_silent_chunks()
        assert len(stub.calls) == 2
        assert set(session._history_req_ids) == {rid2}
    finally:
        win.close()


def test_t01_watchdog_strand_fences_late_arrivals(monkeypatch, qapp):
    """T01: the watchdog strand finalizes (shortfall, idle indicator,
    generation advance, marker cleared) and late bars for the dead reqId
    are fenced."""
    win, stub, session, _now, hole, visible = _one_chunk_hole(
        monkeypatch, qapp, "P19W_E")
    try:
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        gen = session._history_generation
        session._pending_prefetch = True  # a mid-wave trigger had arrived
        session._on_history_wave_timeout()
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert session._history_generation == gen + 1
        assert session._pending_prefetch is False
        assert stub.cancelled == [rid]
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "still missing" in win.status_bar.currentMessage()
        # Late bar/end for the dead generation are fenced, never applied.
        session.on_historical_bar(rid, _FakeIbBar(visible))
        assert session._pending_bars == []
        assert win._session_for_req_id(rid) is None
        session.on_historical_data_end(rid)
        assert session._history_req_ids == set()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T02 — DG111 coalesce seam
# ---------------------------------------------------------------------------
def _two_chunk_fixture(monkeypatch, qapp, symbol: str):
    """A ~65-trading-day hole (two 60 D planner steps) with 5 recent days.

    Uses ``4 hours`` (T = 126 sessions): the whole cached span stays within
    the trigger lookahead while the hole spans two planner chunks, so wave 1
    leaves the older step fetchable and the consumed marker chains exactly
    one more wave. Smaller intraday timeframes cannot hold two 30 D chunks
    inside their (much narrower) T window.
    """
    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts,
                                CHAIN_TF)
    hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=65,
                                     tf=CHAIN_TF)
    assert len(hole) == 65
    recent_bars = BarCache.get_bars(symbol, CHAIN_TF)
    recent_day0 = [b.ts for b in recent_bars
                   if _et_date(b.ts) == recent[0]]
    visible = min(recent_day0)
    return win, stub, session, now_ts, hole, visible


def test_t02_mid_wave_trigger_coalesces_then_chains(monkeypatch, qapp):
    """T02: a mid-wave second trigger never cancels (marker set); completion
    consumes the marker with a fresh re-evaluation and chains exactly one
    more wave while fetchable, then stops."""
    win, stub, session, now_ts, hole, visible = _two_chunk_fixture(
        monkeypatch, qapp, "P19W_F")
    try:
        from services.backfill_service import find_missing_spans, plan_requests

        cached_ts = [b.ts for b in BarCache.get_bars("P19W_F", CHAIN_TF)]
        plans = plan_requests(
            find_missing_spans(cached_ts, now_ts, CHAIN_TF,
                               trailing_days=260,
                               ext_hours=True), CHAIN_TF)
        assert len(plans) == 2
        # Wave 1: the newest pending step.
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid1,) = tuple(session._history_req_ids)
        assert session._req_to_plan[rid1] == plans[0]
        # The user scrolls further while wave 1 is in flight: the running
        # wave is never cancelled, the marker is set instead.
        expected = _expected_bars("P19W_F", hole, CHAIN_TF)
        first_anchor = _parse_end(stub.calls[0]["endDateTime"])
        first_window = {b.ts for b in expected
                        if first_anchor - _duration_seconds(
                                TIMEFRAME_CONFIG[CHAIN_TF]["duration"]
                        ) < b.ts <= first_anchor}
        assert first_window  # the issued step is real coverage
        scrolled = min(first_window)  # the scrolled-to new oldest edge
        assert scrolled < visible
        assert win.maybe_prefetch(scrolled, False) is True
        win._on_viewport_settled(scrolled, False)
        assert len(stub.calls) == 1
        assert set(session._history_req_ids) == {rid1}
        assert stub.cancelled == []
        assert session._pending_prefetch is True
        assert win._last_prefetch_decision["oldest_visible_ts"] == scrolled
        # Wave 1 lands: the marker is consumed, the fresh viewport still
        # needs data, so exactly one more wave issues (no cancel, no storm).
        delivered = _drive_new_calls(win, stub, expected,
                                       stub.calls[:1], CHAIN_TF)
        assert delivered == first_window
        assert session._pending_prefetch is False
        assert len(stub.calls) == 2
        assert len(session._history_req_ids) == 1
        assert "idle" not in win._backfill_indicator.text()
        # Wave 2 lands: everything fetchable is cached — no wave 3, idle.
        delivered2 = _drive_new_calls(win, stub, expected, stub.calls[1:],
                                     CHAIN_TF)
        assert delivered | delivered2 == {b.ts for b in expected}
        assert len(stub.calls) == 2
        assert session._history_req_ids == set()
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
        cached = BarCache.get_bars("P19W_F", CHAIN_TF)
        by_day: dict[date, list] = {}
        for b in cached:
            by_day.setdefault(_et_date(b.ts), []).append(b)
        for d in hole:
            assert len(by_day.get(d, [])) == 4, d
    finally:
        win.close()


def test_t02_marker_cleared_on_terminal_paths(monkeypatch, qapp):
    """T02: the marker ends cleared on strand, on load-cancel and on
    disconnect — never leaking into the next wave."""
    now_ts = _et_ts(2026, 10, 2, 20, 0)
    # Strand path.
    win, stub, session = _setup(monkeypatch, qapp, "P19W_G1", now_ts)
    try:
        _, recent, _ = _hole_fixture("P19W_G1", now_ts, hole_days=1,
                       older_days=3)
        visible = _recent_edge("P19W_G1", recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        win._on_viewport_settled(visible, False)
        assert session._pending_prefetch is True
        session._on_history_wave_timeout()
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
    finally:
        win.close()
    # Load-cancel path (same session, new triple).
    win, stub, session = _setup(monkeypatch, qapp, "P19W_G2", now_ts)
    try:
        _, recent, _ = _hole_fixture("P19W_G2", now_ts, hole_days=1,
                       older_days=3)
        visible = _recent_edge("P19W_G2", recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        win._on_viewport_settled(visible, False)
        assert session._pending_prefetch is True
        gen = session._history_generation
        win.load_chart("P19W_G2", "15 mins")
        assert session._pending_prefetch is False
        assert session._history_generation == gen + 1
        assert rid in stub.cancelled
        # The new triple loads normally through its own wave — the old
        # prefetch is abandoned, never carried over: any in-flight reqId
        # now belongs to the 15-min triple, never the abandoned one.
        assert session._wave_timeframe == "15 mins"
        assert rid not in session._history_req_ids
    finally:
        win.close()
    # Disconnect path.
    win, stub, session = _setup(monkeypatch, qapp, "P19W_G3", now_ts)
    try:
        _, recent, _ = _hole_fixture("P19W_G3", now_ts, hole_days=1,
                       older_days=3)
        visible = _recent_edge("P19W_G3", recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        win._on_viewport_settled(visible, False)
        assert session._pending_prefetch is True
        win._on_disconnected()
        assert session._pending_prefetch is False
        assert session._history_req_ids == set()
        assert win._backfill_indicator.text() == "Backfill: idle"
    finally:
        win.close()


def test_t02_switch_abandonment_has_no_cross_contamination(monkeypatch, qapp):
    """T02: symbol-switch and mode-switch mid-wave abandon the wave plus the
    marker through the existing cancel+generation paths; late bars never
    leak across triples."""
    now_ts = _et_ts(2026, 10, 2, 20, 0)
    # Symbol switch: wave + marker on A abandoned, B loads clean.
    # The A session must be the primary with the chart view attached —
    # production only ever shows sessions that arrived via load_chart —
    # otherwise the switch path has no old session to detach and teardown.
    win, stub, session_a = _setup(monkeypatch, qapp, "P19W_HA", now_ts)
    try:
        _, recent_a, _ = _hole_fixture("P19W_HA", now_ts, hole_days=1,
                       older_days=3)
        visible_a = _recent_edge("P19W_HA", recent_a)
        win._primary_session = session_a
        session_a.attach_view(win.chart_panel, TF, sync=False)
        win._on_viewport_settled(visible_a, False)
        assert len(stub.calls) == 1
        (rid_a,) = tuple(session_a._history_req_ids)
        win._on_viewport_settled(visible_a, False)
        assert session_a._pending_prefetch is True
        gen_a = session_a._history_generation
        win.load_chart("P19W_HB", TF)
        assert session_a._pending_prefetch is False
        # Cross-symbol abandonment is detach→teardown (registry removal +
        # cancel tags), not a generation bump — fencing holds without one.
        assert session_a._history_generation == gen_a
        assert rid_a in stub.cancelled
        assert "P19W_HA" not in win._sessions
        assert win._current_symbol == "P19W_HB"
        # A's late bars are fenced at the window and the session.
        win._on_historical_bar(rid_a, _FakeIbBar(visible_a))
        session_a.on_historical_bar(rid_a, _FakeIbBar(visible_a))
        assert session_a._pending_bars == []
        # B's chart carries only B bars.
        session_b = win.get_or_create_session("P19W_HB")
        for b in session_b.get_bars(TF):
            assert b.symbol == "P19W_HB"
        assert visible_a not in {b.ts for b in BarCache.get_bars(
            "P19W_HB", TF)}
    finally:
        win.close()
    # Mode switch (ext-hours toggle): same session, new triple, marker dies.
    win, stub, session = _setup(monkeypatch, qapp, "P19W_HC", now_ts)
    try:
        _, recent, _ = _hole_fixture("P19W_HC", now_ts, hole_days=1,
                       older_days=3)
        visible = _recent_edge("P19W_HC", recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        win._on_viewport_settled(visible, False)
        assert session._pending_prefetch is True
        win.ext_hours_btn.setChecked(False)  # emits toggled → reload
        assert session._pending_prefetch is False
        assert rid in stub.cancelled
        assert session._wave_extended_hours is False
    finally:
        win.close()


def test_t02_stops_honestly(monkeypatch, qapp):
    """T02: nothing fetchable issues no wave; an empty answer finalizes one
    shortfall with no retry loop."""
    now_ts = _et_ts(2026, 10, 2, 20, 0)
    # Complete cache: silent verdict, no wave, no marker.
    win, stub, session = _setup(monkeypatch, qapp, "P19W_J1", now_ts)
    try:
        recent = _trading_days_back(_et_date(now_ts), 5)
        _seed_days("P19W_J1", recent)
        visible = min(b.ts for b in BarCache.get_bars("P19W_J1", TF))
        assert win.maybe_prefetch(visible, False) is False
        assert win.maybe_issue_prefetch_wave(visible, False) is False
        assert stub.calls == []
        assert session._pending_prefetch is False
        assert win._backfill_state is None
    finally:
        win.close()
    # Empty answer: one shortfall, no re-issue, no loop.
    win, stub, session = _setup(monkeypatch, qapp, "P19W_J2", now_ts)
    try:
        _, recent, _ = _hole_fixture("P19W_J2", now_ts, hole_days=1,
                       older_days=3)
        visible = _recent_edge("P19W_J2", recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        win._on_historical_data_end(rid)  # genuine closure: zero bars
        assert len(stub.calls) == 1
        assert session._history_req_ids == set()
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "still missing" in win.status_bar.currentMessage()
        # A further settled report re-fires honestly (no latch, no storm —
        # exactly one wave per fired trigger).
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 2
    finally:
        win.close()
