"""P17-T2 — generation fencing + identity-removal exactly-once (D56.4, D56.7).

Offscreen, clock-controlled TickerSession suites (no live TWS):

- T21 / AC1: retry a silent chunk, then deliver late bars + a late END on the
  superseded reqId; assert counts, cache, wave/completion state equal a
  control run with no late arrivals (fenced, no resurrection, no double-count).
- T22 / AC2: partial chunk (N bars) retried, re-issue yields the same N bars;
  assert the in-memory wave total credits each bar exactly once and the cache
  holds one row per (symbol, timeframe, ts) with a clean re-read.

Harness follows tests/test_history_backfill.py (offscreen qapp, hermetic DB,
_REQ_ stub doubles); the silence clock is controlled by monkeypatching the
session's _silence_now seam (P17-T1, S-P17-2 / AP-P17-2).
"""

from __future__ import annotations

from data.bar_cache import BarCache
from data.models import Bar
from services.backfill_service import RequestPlan
from ui.ticker_session import TickerSession, _SILENCE_RETRY_AFTER_S

_TF = "5 mins"
_EXT = True  # app default mode; the mode-aware PK scopes every assertion
_BASE_TS = 1_759_000_000
_PLAN = RequestPlan(
    endDateTime="20261002-20:00:00", duration="1 D", bar_size="5 mins",
    span_start_ts=_BASE_TS, span_end_ts=_BASE_TS + 16 * 3600,
)
_N = 5


class _FakeIbBar:
    """Minimal ibapi BarData double (epoch-string date, like the D16 suite)."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _StubMd:
    """Captures req_historical_data calls and cancelled reqIds."""

    def __init__(self, first_id: int = 7000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req_historical_data(self, **kwargs):
        req_id = self._next
        self._next += 1
        self.calls.append({"reqId": req_id, **kwargs})
        return req_id

    def cancel_historical_data(self, req_id):
        self.cancelled.append(req_id)


class _StubHost:
    """Duck-typed TickerSession host: routing table + completion record."""

    status_bar = None

    def __init__(self):
        self.md_manager = _StubMd()
        self.reg: dict[int, TickerSession] = {}
        self.wave_complete: list[TickerSession] = []

    def _register_req_id(self, req_id, session):
        self.reg[req_id] = session

    def _unregister_req_id(self, req_id):
        self.reg.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        self.wave_complete.append(session)


def _make_session(qapp, symbol: str):
    host = _StubHost()
    session = TickerSession(symbol, host)
    now = [1000.0]
    session._silence_now = lambda: now[0]  # clock control (AP-P17-2)
    return session, host, now


def _issue_one(session: _StubHost, host: _StubHost, plan: RequestPlan,
               contract: object = None) -> int:
    session.queue_wave_plans([plan], contract, _TF, _EXT)
    assert len(host.md_manager.calls) == 1
    return host.md_manager.calls[0]["reqId"]


def _retry_by_silence(session: TickerSession, now: list[float]) -> None:
    now[0] += _SILENCE_RETRY_AFTER_S + 1.0
    session._sweep_silent_chunks()


def _wave_state(session, host, symbol):
    """Observable wave snapshot for fenced-vs-control equality (T21)."""
    return (
        len(session._pending_bars),
        sorted(b.ts for b in BarCache.get_bars(symbol, _TF, ext_hours=_EXT)),
        sorted(session._history_req_ids),
        len(host.wave_complete),
        len(host.md_manager.calls),
        list(host.md_manager.cancelled),
    )


def _deliver(session: TickerSession, req_id: int, ts_list: list[int],
             price: float = 100.0) -> None:
    for ts in ts_list:
        session.on_historical_bar(req_id, _FakeIbBar(ts, price))


# ---------------------------------------------------------------------------
# T21 / AC1 — late arrivals on the superseded reqId are fenced
# ---------------------------------------------------------------------------
def test_t21_late_bars_and_end_on_superseded_req_id_change_nothing(qapp):
    """T21: silent chunk retried, then late bars + late END on the old reqId.

    Fenced expectation: counts, cache rows and wave/completion state match a
    control run with no late arrivals (no resurrection, no double-count).
    """
    plan = _PLAN
    ts_list = [_BASE_TS + i * 300 for i in range(3)]

    # Subject run: retry, then late arrivals on the superseded reqId.
    s1, h1, now1 = _make_session(qapp, "FENCE1")
    old1 = _issue_one(s1, h1, plan)
    _retry_by_silence(s1, now1)
    new1 = h1.md_manager.calls[-1]["reqId"]
    assert old1 in s1._cancelled_history_req_ids
    assert old1 not in s1._history_req_ids
    assert s1._history_req_ids == {new1}
    base1 = _wave_state(s1, h1, "FENCE1")

    _deliver(s1, old1, ts_list)          # late bars on the superseded reqId
    s1.on_historical_data_end(old1)      # late END on the superseded reqId

    assert _wave_state(s1, h1, "FENCE1") == base1
    assert old1 not in s1._req_bars
    # Control run: identical retry, no late arrivals.
    s2, h2, now2 = _make_session(qapp, "FENCE2")
    old2 = _issue_one(s2, h2, plan)
    _retry_by_silence(s2, now2)

    assert _wave_state(s1, h1, "FENCE1") == _wave_state(s2, h2, "FENCE2")
    assert s1._history_generation == s2._history_generation == 0


# ---------------------------------------------------------------------------
# T22 / AC2 — exactly-once counting across the supersede + re-issue
# ---------------------------------------------------------------------------
def test_t22_partial_chunk_retried_counts_each_bar_once(qapp):
    """T22: partial chunk retried; re-issue yields the same N bars.

    In-memory wave total credits each bar exactly once (identity-removal, not
    object equality); the cache holds one row per ts under the mode-aware PK
    with a clean re-read.
    """
    symbol = "EXACT1"
    ts_list = [_BASE_TS + i * 300 for i in range(_N)]
    plan = _PLAN

    session, host, now = _make_session(qapp, symbol)
    old = _issue_one(session, host, plan)

    # Partial chunk: N bars, no END (trailing-silence rule will fire).
    _deliver(session, old, ts_list)
    assert len(session._pending_bars) == _N
    old_bars = list(session._req_bars[old])
    assert len(old_bars) == _N

    # One bar already persisted per-chunk (identical values): the identical
    # re-fetch must leave it unchanged under the mode-aware PK.
    BarCache.save_bars([old_bars[0]], ext_hours=_EXT)

    _retry_by_silence(session, now)
    new = host.md_manager.calls[-1]["reqId"]
    assert new != old
    assert old not in session._req_bars
    # Identity-removal: exactly those Bar objects are gone from the wave total.
    pending_ids = {id(b) for b in session._pending_bars}
    assert not any(id(b) in pending_ids for b in old_bars)
    assert len(session._pending_bars) == 0
    # Persisted cache rows survive the supersede untouched.
    assert [b.ts for b in BarCache.get_bars(symbol, _TF, ext_hours=_EXT)] == [
        ts_list[0]
    ]

    # Re-issue yields the same N bars as genuinely new objects.
    _deliver(session, new, ts_list)
    new_bars = list(session._req_bars[new])
    assert len(new_bars) == _N
    assert not any(id(b) in {id(o) for o in old_bars} for b in new_bars)
    assert len(session._pending_bars) == _N
    assert sorted(b.ts for b in session._pending_bars) == sorted(ts_list)

    # One per-chunk persist on the re-issued END: PK-idempotent, clean re-read.
    session.on_historical_data_end(new)
    rows = BarCache.get_bars(symbol, _TF, ext_hours=_EXT)
    assert sorted(b.ts for b in rows) == sorted(ts_list)
    assert len(rows) == _N
    first = next(b for b in rows if b.ts == ts_list[0])
    assert (first.open, first.high, first.low, first.close, first.volume) == (
        old_bars[0].open, old_bars[0].high, old_bars[0].low,
        old_bars[0].close, old_bars[0].volume,
    )
    reread = session.get_bars(_TF)
    assert [b.ts for b in reread] == sorted(ts_list)
    assert len(reread) == _N
    # In-memory wave total still credits each bar exactly once.
    assert sorted(b.ts for b in session._pending_bars) == sorted(ts_list)
    # Mode-aware PK: the other mode holds no rows.
    assert BarCache.get_bars(symbol, _TF, ext_hours=not _EXT) == []
    # Last member ended: the host finalised.
    assert host.wave_complete == [session]
    assert session._history_req_ids == set()
