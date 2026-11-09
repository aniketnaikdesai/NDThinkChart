"""P19-T4 — prefetch honesty: incremental render, in-flight state, strand shortfall, closures.

Verifies the joint P19-T2/P19-T3 behaviour with no production edits:

* T01 — per-chunk incremental render: across a chained two-step prefetch wave
  the chart bar count grows as each chunk lands; while the older step is still
  missing (wave 2 in flight) the D53 indicator stays raised (never complete)
  and the freshness gate reports not-current; strand finalization keeps the
  verbatim AC-D16.4 shortfall; genuine closures stay empty.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import find_missing_spans
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


def _prev_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _trading_days_back(end: date, n: int) -> list[date]:
    assert is_trading_day(end)
    days = [end]
    while len(days) < n:
        days.append(_prev_trading_day(days[-1]))
    return sorted(days)


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
    """Seed recent + older blocks with an interior trading-day hole."""
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
# T01 — incremental render + in-flight honesty across a chained prefetch
# ---------------------------------------------------------------------------
def test_t01_per_chunk_incremental_render_and_in_flight_honesty(
        monkeypatch, qapp):
    """T01: each landed chunk grows the chart; the missing region stays
    in-flight (D53 raised, freshness gate closed) until the chain completes.
    """
    from services.backfill_service import plan_requests

    symbol = "P19H_A"
    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts, CHAIN_TF)
    try:
        hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=65,
                                         tf=CHAIN_TF)
        assert len(hole) == 65
        visible = _recent_edge(symbol, recent, CHAIN_TF)
        # The main chart renders this session's waves (production wiring).
        win._set_primary_session(session)

        cached_ts = [b.ts for b in BarCache.get_bars(symbol, CHAIN_TF)]
        plans = plan_requests(
            find_missing_spans(cached_ts, now_ts, CHAIN_TF,
                               trailing_days=260, ext_hours=True), CHAIN_TF)
        assert len(plans) == 2

        # Wave 1 issues; the user scrolls mid-wave (marker set, no cancel).
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        expected = _expected_bars(symbol, hole, CHAIN_TF)
        first_anchor = _parse_end(stub.calls[0]["endDateTime"])
        step = _duration_seconds(TIMEFRAME_CONFIG[CHAIN_TF]["duration"])
        first_window = {b.ts for b in expected
                        if first_anchor - step < b.ts <= first_anchor}
        assert first_window
        scrolled = min(first_window)
        assert scrolled < visible
        win._on_viewport_settled(scrolled, False)
        assert session._pending_prefetch is True

        # Wave 1 lands: the chart grows by exactly the first chunk
        # (incremental per-chunk render), and wave 2 is already in flight.
        c0 = len(win.chart_panel._bars)
        delivered = _drive_new_calls(win, stub, expected,
                                     stub.calls[:1], CHAIN_TF)
        assert delivered == first_window
        qapp.processEvents()
        c1 = len(win.chart_panel._bars)
        # The landed chunk renders with the cache: recent + older + wave 1.
        assert c1 > c0
        assert c1 == len(BarCache.get_bars(symbol, CHAIN_TF))
        assert session._pending_prefetch is False
        assert len(stub.calls) == 2
        assert len(session._history_req_ids) == 1
        # In-flight honesty: D53 stays raised and the freshness gate stays
        # closed while the older step is still missing — the region is never
        # presented as complete.
        assert win._backfill_state is not None
        assert win._backfill_state["in_flight"] == 1
        assert "idle" not in win._backfill_indicator.text()
        assert win._is_cache_current(symbol, CHAIN_TF, True) is False
        assert "Cache current" not in win.status_bar.currentMessage()

        # Wave 2 lands: the chart grows again and the wave goes idle.
        delivered2 = _drive_new_calls(win, stub, expected,
                                      stub.calls[1:], CHAIN_TF)
        assert delivered | delivered2 == {b.ts for b in expected}
        qapp.processEvents()
        c2 = len(win.chart_panel._bars)
        assert c2 > c1
        assert c2 == len(BarCache.get_bars(symbol, CHAIN_TF))
        assert session._history_req_ids == set()
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
    finally:
        win.close()


def test_t01_strand_finalization_keeps_verbatim_shortfall(
        monkeypatch, qapp, caplog):
    """T01: a stranded prefetch wave keeps the verbatim AC-D16.4 shortfall."""
    symbol = "P19H_B"
    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        hole, recent, _ = _hole_fixture(symbol, now_ts, hole_days=1,
                                        older_days=3)
        visible = _recent_edge(symbol, recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        gen = session._history_generation
        session._pending_prefetch = True  # a mid-wave trigger had arrived
        with caplog.at_level("WARNING"):
            session._on_history_wave_timeout()
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == set() or \
            session._wave_plan_queue == []
        assert session._history_generation == gen + 1
        assert session._pending_prefetch is False
        assert stub.cancelled == [rid]
        assert win._backfill_indicator.text() == "Backfill: idle"
        # Verbatim AC-D16.4 shortfall shape, stranded-cause suffix allowed.
        msg = win.status_bar.currentMessage()
        assert msg.startswith(f"{symbol} — backfill incomplete: ")
        assert re.search(r"\d+ trading day\(s\) still missing \([^)]*\)",
                         msg) is not None
        assert "Cache current" not in msg
        shortfall_records = [
            r for r in caplog.records
            if "Historical backfill shortfall for" in r.getMessage()
        ]
        assert shortfall_records, "expected the WARNING shortfall record"
        assert shortfall_records[0].getMessage().startswith(
            f"Historical backfill shortfall for {symbol} [{TF}]: ")
    finally:
        win.close()


def test_t01_genuine_closures_stay_empty(monkeypatch, qapp):
    """T01: weekend closures are never reported missing, never fetched, and
    an empty (closure) chunk answer finalizes one shortfall with no loop."""
    friday = date(2026, 9, 25)
    monday = date(2026, 9, 28)
    assert is_trading_day(friday) and is_trading_day(monday)
    now_ts = _et_ts(monday.year, monday.month, monday.day, 20, 0)

    # A weekend-only gap: the planner reports nothing, the trigger is silent.
    symbol = "P19H_C"
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        cache_bars = (_session_bars(symbol, friday)
                      + _session_bars(symbol, monday))
        BarCache.save_bars(cache_bars)
        cached_ts = [b.ts for b in BarCache.get_bars(symbol, TF)]
        assert find_missing_spans(cached_ts, now_ts, TF,
                                  ext_hours=True) == []
        v_ts = _session_bars(symbol, monday)[2].ts
        assert win.maybe_prefetch(v_ts, False) is False
        assert win.maybe_issue_prefetch_wave(v_ts, False) is False
        assert stub.calls == []
        # The genuine closure holds no cached rows at all.
        for ts in cached_ts:
            assert is_trading_day(_et_date(ts)), ts
    finally:
        win.close()

    # An empty chunk answer (genuine closure): one shortfall, no retry loop,
    # and no fabricated bars for the missing days.
    symbol2 = "P19H_D"
    win, stub, session = _setup(monkeypatch, qapp, symbol2, now_ts)
    try:
        hole, recent, _ = _hole_fixture(symbol2, now_ts, hole_days=1,
                                        older_days=3)
        visible = _recent_edge(symbol2, recent)
        win._on_viewport_settled(visible, False)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        win._on_historical_data_end(rid)  # genuine closure: zero bars
        assert len(stub.calls) == 1
        assert session._history_req_ids == set()
        assert session._pending_prefetch is False
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "still missing" in win.status_bar.currentMessage()
        hole_ts = {b.ts for b in _expected_bars(symbol2, hole)}
        assert not (hole_ts & {b.ts for b in BarCache.get_bars(
            symbol2, TF)})
    finally:
        win.close()
