"""D28.3 — rolling 600s historical pacing window (AC-D28.3).

reqHistoricalData gets a rolling 600-second / ~60-request pacing window
(non-blocking): the issuer raises PacingExceeded when the budget is
exhausted instead of sleeping; the history wave caps chunks per wave
(~60) and continues across waves via a deferred re-issue; IBKR error 162
retries once before the wave finalises short.
"""
import time

import pytest

from ibkr import pacing as pacing_mod
from ibkr.pacing import PacingExceeded, PacingManager
from ibkr.market_data import MarketDataManager
from services.backfill_service import RequestPlan

MAX_HIST = 60


def _exhaust_hist_budget(pm: PacingManager, wait_s: float = 600.0) -> None:
    """Fill the 60-slot historical budget so the next request must wait.

    wait_s controls how long the caller would wait (backdate entries).
    """
    now = time.time()
    pm._hist_times.clear()
    for _ in range(MAX_HIST):
        pm._hist_times.append(now - (600.0 - wait_s))


class _FakeHistClient:
    def __init__(self):
        self.hist: list[int] = []

    def reqHistoricalData(self, reqId, *a, **k):
        self.hist.append(reqId)

    def cancelHistoricalData(self, reqId):
        pass


def _plan(i: int) -> RequestPlan:
    return RequestPlan(
        endDateTime=f"2024010{i % 9 + 1}  16:00:00",
        duration="5 D",
        bar_size="5 mins",
        span_start_ts=1_700_000_000 + i,
        span_end_ts=1_700_100_000 + i,
    )


class _StubStatusBar:
    def __init__(self):
        self.messages: list[str] = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _StubHost:
    """Minimal TickerSession host: md wiring + reqId routing + status."""

    def __init__(self, client):
        from ibkr.id_manager import id_manager
        self.md_manager = MarketDataManager(client)
        self.status_bar = _StubStatusBar()
        self._req_table: dict[int, object] = {}
        self.wave_completions: list[str] = []
        self._id_manager = id_manager

    def _register_req_id(self, req_id, session):
        self._req_table[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_table.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        self.wave_completions.append(session.symbol)


def _make_session(qapp, client, symbol="AAA"):
    from ui.ticker_session import TickerSession
    host = _StubHost(client)
    session = TickerSession(symbol, host)
    return host, session


# ── Pacing math ──────────────────────────────────────────────────────

def test_historical_wait_zero_when_budget_free():
    pm = PacingManager()
    assert pm.historical_wait_seconds() == 0.0


def test_historical_wait_positive_when_budget_exhausted():
    pm = PacingManager()
    _exhaust_hist_budget(pm, wait_s=120.0)
    wait = pm.historical_wait_seconds()
    assert 100.0 < wait <= 120.0


def test_historical_window_rolls_with_time():
    pm = PacingManager()
    _exhaust_hist_budget(pm, wait_s=600.0)
    assert pm.historical_wait_seconds() > 590.0
    # Age every slot by 300s: half the window has rolled off.
    now = time.time()
    pm._hist_times = type(pm._hist_times)(t - 300.0 for t in pm._hist_times)
    wait = pm.historical_wait_seconds()
    assert 280.0 < wait <= 300.0
    # Age past the window: budget fully free.
    pm._hist_times = type(pm._hist_times)(t - 600.0 for t in pm._hist_times)
    assert pm.historical_wait_seconds() == 0.0


def test_record_historical_slot_consumes_budget():
    pm = PacingManager()
    for _ in range(MAX_HIST):
        assert pm.historical_wait_seconds() == 0.0
        pm.record_historical_slot()
    assert pm.historical_wait_seconds() > 0.0


# ── Issuer behaviour ─────────────────────────────────────────────────

def test_req_historical_data_raises_without_sleep(monkeypatch):
    """Budget exhausted -> PacingExceeded; never time.sleep; no request."""
    from ibkr.contracts import get_contract_for_symbol
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    _exhaust_hist_budget(pacing_mod.pacing_manager)
    fake = _FakeHistClient()
    mgr = MarketDataManager(fake)
    with pytest.raises(PacingExceeded) as excinfo:
        mgr.req_historical_data(get_contract_for_symbol("AAPL"), "5 mins")
    assert excinfo.value.wait_seconds > 0
    assert fake.hist == [], "no request may be issued while pacing-limited"
    assert sleeps == [], "pacing must never sleep the calling thread"


def test_req_historical_data_records_slot_on_success():
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    mgr = MarketDataManager(fake)
    req_id = mgr.req_historical_data(get_contract_for_symbol("AAPL"), "5 mins")
    assert fake.hist == [req_id]
    assert len(pacing_mod.pacing_manager._hist_times) == 1


# ── Wave chunking ────────────────────────────────────────────────────

def test_wave_caps_chunks_and_continues(monkeypatch, qapp):
    """75 plans -> 60 issued now, continuation deferred, rest issued later."""
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    continued: list[float] = []
    monkeypatch.setattr(
        session._wave_continue_timer, "start",
        lambda ms: continued.append(ms),
    )
    contract = get_contract_for_symbol("AAA")
    session.queue_wave_plans([_plan(i) for i in range(75)],
                             contract, "5 mins", False)
    assert len(fake.hist) == 60, "wave must cap chunks at ~60"
    assert len(session._wave_plan_queue) == 15
    assert len(continued) == 1 and continued[0] > 0, \
        "continuation must be scheduled with a positive delay"
    assert any("pacing-limited" in m.lower() for m in host.status_bar.messages)
    # Free the budget, fire the deferred continuation.
    pacing_mod.pacing_manager.reset_for_tests()
    session._on_wave_continue_timeout()
    assert len(fake.hist) == 75, "continuation must issue the remaining plans"
    assert session._wave_plan_queue == []
    assert len(continued) == 1, "no further continuation once drained"


def test_wave_continuation_never_sleeps(monkeypatch, qapp):
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    continued: list[float] = []
    monkeypatch.setattr(
        session._wave_continue_timer, "start",
        lambda ms: continued.append(ms),
    )
    # Only 40 slots free: the wave must stop mid-list and defer.
    _exhaust_hist_budget(pacing_mod.pacing_manager, wait_s=600.0)
    for _ in range(20):
        pacing_mod.pacing_manager._hist_times.popleft()
    session.queue_wave_plans([_plan(i) for i in range(50)],
                             get_contract_for_symbol("AAA"), "5 mins", False)
    assert len(fake.hist) == 20
    assert sleeps == []
    assert len(continued) == 1


def test_error_162_retries_once_then_finalises_short(monkeypatch, qapp):
    """A 162'd chunk is retried exactly once; the second 162 finalises short."""
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    continued: list[float] = []
    monkeypatch.setattr(
        session._wave_continue_timer, "start",
        lambda ms: continued.append(ms),
    )
    session.queue_wave_plans([_plan(0)],
                             get_contract_for_symbol("AAA"), "5 mins", False)
    assert len(fake.hist) == 1
    req_id = fake.hist[0]
    # First 162: retry scheduled, wave NOT completed.
    session.on_historical_error(req_id, 162, "pacing violation")
    assert host.wave_completions == []
    assert len(continued) == 1, "a retry must be scheduled after backoff"
    # Fire the retry: the same chunk is re-issued exactly once.
    pacing_mod.pacing_manager.reset_for_tests()
    session._on_wave_continue_timeout()
    assert len(fake.hist) == 2, "162 chunk must be retried exactly once"
    req_id2 = fake.hist[1]
    # Second 162: no more retries — the wave finalises short.
    session.on_historical_error(req_id2, 162, "pacing violation")
    assert len(fake.hist) == 2, "no third attempt after retry-once"
    assert host.wave_completions == ["AAA"], "wave must finalise short"
    assert req_id2 in session._backfill_failed_req_ids


def test_non_162_error_finalises_without_retry(qapp):
    """Other errors keep the existing fail-fast behaviour (no retry)."""
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    session.queue_wave_plans([_plan(0)],
                             get_contract_for_symbol("AAA"), "5 mins", False)
    req_id = fake.hist[0]
    session.on_historical_error(req_id, 200, "no security definition")
    assert len(fake.hist) == 1, "non-162 errors must not retry"
    assert host.wave_completions == ["AAA"]


def test_rapid_symbol_switching_no_162_storm(monkeypatch, qapp):
    """Three waves in quick succession stay within the 600s budget."""
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    sessions = []
    for sym in ("AAA", "BBB", "CCC"):
        host, session = _make_session(qapp, fake, symbol=sym)
        monkeypatch.setattr(
            session._wave_continue_timer, "start", lambda ms: None,
        )
        sessions.append(session)
    contract = get_contract_for_symbol("AAA")
    for session in sessions:
        session.queue_wave_plans([_plan(i) for i in range(30)],
                                 contract, "5 mins", False)
    # 90 plans requested; the rolling window must have capped issuance.
    assert len(fake.hist) <= MAX_HIST, \
        f"{len(fake.hist)} requests in one window would storm TWS with 162s"
    queued = sum(len(s._wave_plan_queue) for s in sessions)
    assert queued == 90 - len(fake.hist), \
        "every unissued plan must remain queued for continuation"
