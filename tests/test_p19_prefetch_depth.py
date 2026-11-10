"""P19-T3 — fetch-while-fetchable chaining with honest stops (D58.5), offscreen.

Proves the P19 prefetch loop on a real, shown ``MainWindow`` with stubbed
transport and clock control (``IBApiClient.connect`` monkeypatched, the
market-data managers stubbed), building on the P19-T2 issuance + marker:

* T01 — deep-scroll chaining: several successive settled reports across a
  three-planner-step hole chain wave-after-wave (each completion issues
  exactly one older step), at most one wave in flight at every instant,
  coverage extending window by window, with no depth cap cutting the chain
  short and a clean stop once the cache covers the viewport.
* T02 — honest stops: a weekend-closure-only gap fires no wave and stays
  empty; a beyond-retention (oldest, empty-answer) chunk finalizes exactly
  one AC-D16.4 shortfall with no retry loop and no D56 allowance consumed;
  a pacing-exhausted fire falls through to watchdog strand-finalization
  fail-open without blocking bar delivery.

No test here weakens, skips or rewrites an existing test. P19-T1
(``tests/test_p19_prefetch_trigger.py``) and P19-T2
(``tests/test_p19_prefetch_wave.py``) stay green.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.market_calendar import is_trading_day

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


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _parse_end(end: str) -> int:
    """Parse a planned IBKR ``endDateTime`` (``yyyyMMdd-HH:mm:ss`` UTC)."""
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
    """Seed ``recent_days`` + ``older_days`` complete blocks with a
    ``hole_days``-long trading-day hole directly between them (interior, so
    the planner reports it). Returns (hole, recent, now_ts)."""
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


def _window_ts(call: dict, expected: list[Bar], tf: str) -> set[int]:
    """Timestamps of ``expected`` covered by one call's planner window."""
    chunk = _duration_seconds(TIMEFRAME_CONFIG[tf]["duration"])
    anchor = _parse_end(call["endDateTime"])
    return {b.ts for b in expected if anchor - chunk < b.ts <= anchor}


# ---------------------------------------------------------------------------
# T01 — fetch-while-fetchable chaining across several planner steps
# ---------------------------------------------------------------------------
def test_t01_deep_scroll_chains_step_by_step_no_cap(monkeypatch, qapp):
    """T01: three successive settled reports chain three older steps (one
    wave in flight at every instant, coverage extending window by window)
    with no depth cap, then stop once the cache covers the viewport."""
    from services.backfill_service import find_missing_spans, plan_requests

    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    symbol = "P19DCHN"
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts,
                                CHAIN_TF)
    try:
        # A ~100-trading-day hole: three 60 D planner steps on 4-hours,
        # with the oldest cached day still inside the 126-session lookahead
        # so the initial report fires.
        hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=100,
                                        older_days=3, tf=CHAIN_TF)
        assert len(hole) == 100
        cached_ts = [b.ts for b in BarCache.get_bars(symbol, CHAIN_TF)]
        plans = plan_requests(
            find_missing_spans(cached_ts, now_ts, CHAIN_TF,
                               trailing_days=260, ext_hours=True),
            CHAIN_TF)
        assert len(plans) == 3
        expected = _expected_bars(symbol, hole, CHAIN_TF)
        visible = _recent_edge(symbol, recent, CHAIN_TF)

        # Wave 1: the newest pending step, exactly one wave in flight.
        assert win.maybe_prefetch(visible, False) is True
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid1,) = tuple(session._history_req_ids)
        assert session._req_to_plan[rid1] == plans[0]
        window1 = _window_ts(stub.calls[0], expected, CHAIN_TF)
        assert window1
        anchor1 = _parse_end(stub.calls[0]["endDateTime"])

        # Scroll further while wave 1 is in flight: coalesce, never cancel.
        scrolled2 = min(window1)
        assert scrolled2 < visible
        assert win.maybe_prefetch(scrolled2, False) is True
        win._on_viewport_settled(scrolled2, False)
        assert len(stub.calls) == 1
        assert set(session._history_req_ids) == {rid1}
        assert stub.cancelled == []
        assert session._pending_prefetch is True

        # Wave 1 lands: exactly one older step chains (one in flight).
        delivered1 = _drive_new_calls(win, stub, expected,
                                      stub.calls[:1], CHAIN_TF)
        assert delivered1 == window1
        assert session._pending_prefetch is False
        assert len(stub.calls) == 2
        assert len(session._history_req_ids) == 1
        (rid2,) = tuple(session._history_req_ids)
        assert rid2 != rid1
        assert "idle" not in win._backfill_indicator.text()
        anchor2 = _parse_end(stub.calls[1]["endDateTime"])
        assert anchor2 < anchor1  # the next older step
        window2 = _window_ts(stub.calls[1], expected, CHAIN_TF)
        assert window2 and window2.isdisjoint(window1)
        # Coverage extended window by window: wave-2's window not yet cached.
        assert min(window2) not in {
            b.ts for b in BarCache.get_bars(symbol, CHAIN_TF)}

        # Scroll further while wave 2 is in flight: the chain has no cap —
        # a third link still issues exactly one older step.
        scrolled3 = min(window2)
        assert scrolled3 < scrolled2
        assert win.maybe_prefetch(scrolled3, False) is True
        win._on_viewport_settled(scrolled3, False)
        assert len(stub.calls) == 2
        assert set(session._history_req_ids) == {rid2}
        assert session._pending_prefetch is True
        delivered2 = _drive_new_calls(win, stub, expected,
                                      stub.calls[1:2], CHAIN_TF)
        assert delivered2 == window2
        assert session._pending_prefetch is False
        assert len(stub.calls) == 3
        assert len(session._history_req_ids) == 1
        (rid3,) = tuple(session._history_req_ids)
        assert rid3 not in (rid1, rid2)
        anchor3 = _parse_end(stub.calls[2]["endDateTime"])
        assert anchor3 < anchor2  # older still
        window3 = _window_ts(stub.calls[2], expected, CHAIN_TF)
        assert window3 and window3.isdisjoint(window1 | window2)

        # Wave 3 lands: the hole is covered — no wave 4, idle, marker clear.
        delivered3 = _drive_new_calls(win, stub, expected,
                                      stub.calls[2:], CHAIN_TF)
        assert delivered3 == window3
        assert delivered1 | delivered2 | delivered3 == {
            b.ts for b in expected}
        assert len(stub.calls) == 3
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
        # The whole hole is cached at full 4-hour cadence (4 bars/day).
        cached = BarCache.get_bars(symbol, CHAIN_TF)
        by_day: dict[date, list] = {}
        for b in cached:
            by_day.setdefault(_et_date(b.ts), []).append(b)
        for d in hole:
            assert len(by_day.get(d, [])) == 4, d
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T02 — honest stops
# ---------------------------------------------------------------------------
def test_t02_closure_gap_stays_empty_and_silent(monkeypatch, qapp):
    """T02: a weekend-only gap fires no wave and the closures stay empty."""
    from services.backfill_service import find_missing_spans

    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    symbol = "P19DCLS"
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        # Two complete Mon-Fri blocks with only a weekend between them.
        recent = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30),
                  date(2026, 10, 1), date(2026, 10, 2)]
        older = [date(2026, 9, 21), date(2026, 9, 22), date(2026, 9, 23),
                 date(2026, 9, 24), date(2026, 9, 25)]
        _seed_days(symbol, recent, base=200.0)
        _seed_days(symbol, older, base=100.0)
        # The planner reports nothing fetchable: closures are never spans.
        cached_ts = [b.ts for b in BarCache.get_bars(symbol, TF)]
        assert find_missing_spans(cached_ts, now_ts, TF,
                                  trailing_days=60,
                                  ext_hours=True) == []
        visible = _recent_edge(symbol, recent)
        assert win.maybe_prefetch(visible, False) is False
        win._on_viewport_settled(visible, False)
        assert stub.calls == []
        assert session._pending_prefetch is False
        assert session._history_req_ids == set()
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
        # The weekend closures hold no cached rows at all.
        by_day = {_et_date(b.ts) for b in BarCache.get_bars(symbol, TF)}
        assert date(2026, 9, 26) not in by_day
        assert date(2026, 9, 27) not in by_day
    finally:
        win.close()


def test_t02_retention_edge_single_shortfall_no_retry_loop(monkeypatch, qapp):
    """T02: the beyond-retention (oldest, empty-answer) chunk finalizes one
    AC-D16.4 shortfall with no re-issue and no D56 allowance consumed."""
    now_ts = _et_ts(2026, 10, 2, 20, 0)
    symbol = "P19DRET"
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts,
                                CHAIN_TF)
    try:
        hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=65,
                                        tf=CHAIN_TF)
        expected = _expected_bars(symbol, hole, CHAIN_TF)
        visible = _recent_edge(symbol, recent, CHAIN_TF)
        # Wave 1 (newest step) + a mid-wave scroll so wave 2 chains.
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid1,) = tuple(session._history_req_ids)
        window1 = _window_ts(stub.calls[0], expected, CHAIN_TF)
        assert window1
        scrolled = min(window1)
        assert win.maybe_prefetch(scrolled, False) is True
        win._on_viewport_settled(scrolled, False)
        assert session._pending_prefetch is True
        delivered1 = _drive_new_calls(win, stub, expected,
                                      stub.calls[:1], CHAIN_TF)
        assert delivered1 == window1
        assert len(stub.calls) == 2
        (rid2,) = tuple(session._history_req_ids)
        assert rid2 != rid1
        # The retention edge: the oldest chunk answers empty (no bars, no
        # error — past retention, nothing to fetch).
        win._on_historical_data_end(rid2)
        assert len(stub.calls) == 2  # no re-issue, no loop
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert session._pending_prefetch is False
        assert session._retried_plans == set()  # D56 never engaged
        assert session._backfill_failed_req_ids == set()  # no error either
        assert win._backfill_indicator.text() == "Backfill: idle"
        # Exactly one AC-D16.4 shortfall naming the retention-edge days.
        msg = win.status_bar.currentMessage()
        assert "still missing" in msg
        assert hole[0].isoformat() in msg
        # Nothing self-perpetuates: with no new trigger, no further wave.
        qapp.processEvents()
        assert len(stub.calls) == 2
        assert session._history_req_ids == set()
    finally:
        win.close()


def test_t02_pacing_exhaustion_falls_through_to_watchdog(monkeypatch, qapp):
    """T02: a pacing-exhausted fire holds a queue-only wave, then the
    watchdog strand-finalizes fail-open without blocking bar delivery."""
    from ibkr.pacing import PacingExceeded

    now_ts = _et_ts(2026, 10, 2, 20, 0)
    symbol = "P19DPACE"
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        _, recent, _ = _hole_fixture(symbol, now_ts, hole_days=1,
                                     older_days=3)
        seeded = len(BarCache.get_bars(symbol, TF))
        assert seeded > 0
        visible = _recent_edge(symbol, recent)
        # Fire while the pacing budget is exhausted: nothing issued, the
        # single plan waits with watchdog cover (fail-open, never an error).
        stub.fail_next = PacingExceeded(200.0)
        win._on_viewport_settled(visible, False)
        assert stub.calls == []
        assert session._history_req_ids == set()
        assert len(session._wave_plan_queue) == 1
        assert session._wave_continue_timer.isActive()
        assert session._history_wave_bound_ms == 200_000 + 30_000
        assert win._backfill_state is not None
        assert win._backfill_state["queued"] == 1

        # The watchdog fires first: strand-finalize (shortfall once, idle,
        # generation advance, marker cleared, queue dropped, timer stopped).
        gen = session._history_generation
        session._on_history_wave_timeout()
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert session._history_generation == gen + 1
        assert session._pending_prefetch is False
        assert stub.cancelled == []  # nothing was ever issued
        assert not session._wave_continue_timer.isActive()
        assert not win._backfill_expiry_timer.isActive()
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "still missing" in win.status_bar.currentMessage()

        # Fail-open: the seeded cache is intact and the session data path
        # still takes bars (bar delivery was never blocked by the wave).
        assert len(BarCache.get_bars(symbol, TF)) == seeded
        assert len(session.get_bars(TF)) == seeded
        agg = session.aggregator_for(TF)
        agg.push(_et_ts(2026, 10, 2, 19, 55), 101.0, 101.5, 100.5,
                 101.25, 500.0)
        assert len(session.get_bars(TF)) == seeded + 1

        # ... and a later trigger fires a fresh wave (nothing wedged).
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        assert len(session._history_req_ids) == 1
    finally:
        win.close()
