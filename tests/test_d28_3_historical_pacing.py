"""D28.3 — rolling 600s historical pacing window (AC-D28.3).

reqHistoricalData gets a rolling 600-second pacing window (100 requests,
owner-set in Q-30) plus a 0.5 s minimum interval between requests (Q-2/Q-30),
both non-blocking: the issuer
raises PacingExceeded when either gate is closed instead of sleeping; the
history wave defers the remainder and continues across waves via a deferred
re-issue, so a same-contract burst can never trip IBKR error 162. IBKR error
162 retries once before the wave finalises short.
"""
import time

import pytest

from config import settings
from ibkr import pacing as pacing_mod
from ibkr.pacing import PacingExceeded, PacingManager
from ibkr.market_data import MarketDataManager
from services.backfill_service import RequestPlan

MAX_HIST = settings.MAX_HISTORICAL_PER_600S


def _exhaust_hist_budget(pm: PacingManager, wait_s: float = 600.0) -> None:
    """Fill every historical budget slot so the next request must wait.

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
        self.prime_completions: list[str] = []
        self._id_manager = id_manager

    def _register_req_id(self, req_id, session):
        self._req_table[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_table.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        self.wave_completions.append(session.symbol)

    def _on_session_prime_complete(self, session):
        self.prime_completions.append(session.symbol)


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
    assert pm.historical_wait_seconds() == 0.0
    # Q-2: the first request closes the min-interval gate for the next one.
    pm.record_historical_slot()
    assert 0.0 < pm.historical_wait_seconds() <= settings.HISTORICAL_MIN_INTERVAL_S
    # Backdate the interval clock so only the budget can block, then fill it.
    stale = time.time() - 2 * settings.HISTORICAL_MIN_INTERVAL_S
    pm._last_hist_time = stale
    for _ in range(MAX_HIST - 1):
        assert pm.historical_wait_seconds() == 0.0
        pm.record_historical_slot()
        pm._last_hist_time = stale
    assert pm.historical_wait_seconds() > 0.0


# ── Q-30: owner-set pacing constants ─────────────────────────────────

def test_q30_owner_constants_are_in_force():
    """Q-30: 0.5 s spacing and a 100-request window are the live values."""
    assert settings.HISTORICAL_MIN_INTERVAL_S == 0.5
    assert settings.MAX_HISTORICAL_PER_600S == 100
    # At 0.5 s spacing the interval ceiling is 1200/600s, so the budget
    # is the gate that binds first.
    assert (600.0 / settings.HISTORICAL_MIN_INTERVAL_S
            > settings.MAX_HISTORICAL_PER_600S)


def test_q30_interval_gate_reports_half_a_second_not_one():
    """Q-30: the interval gate must reflect 0.5 s, not the old 1.0 s."""
    pm = PacingManager()
    pm.record_historical_slot()
    wait = pm.historical_wait_seconds()
    # A fresh request reports one interval (capped at HISTORICAL_MIN_INTERVAL_S).
    assert 0.4 < wait <= settings.HISTORICAL_MIN_INTERVAL_S
    assert wait < 0.9, f"interval gate still reports the old ~1 s ({wait})"
    # The Q-17 safety margin still pads a hair-early residual.
    pm._last_hist_time = time.time() - (
        settings.HISTORICAL_MIN_INTERVAL_S - 0.0004)
    assert pm.historical_wait_seconds() > 0.02
    # 0.6 s after a request the gate is open; a 1.0 s interval would still hold.
    pm._last_hist_time = time.time() - 0.6
    assert pm.historical_wait_seconds() == 0.0


def test_q30_budget_gate_closes_after_100_requests_in_the_window():
    """Q-30: exactly MAX_HISTORICAL_PER_600S requests fit in the window."""
    pm = PacingManager()
    for _ in range(settings.MAX_HISTORICAL_PER_600S):
        pm.record_historical_slot()
        pm._last_hist_time = 0.0  # isolate the budget gate from the interval
    assert pm.historical_wait_seconds() > 500.0, \
        "the 101st request in the window must be deferred to the window edge"
    # The old 50-request budget would have closed here; the new one has not.
    pm2 = PacingManager()
    for _ in range(settings.MAX_HISTORICAL_PER_600S // 2):
        pm2.record_historical_slot()
        pm2._last_hist_time = 0.0
    assert pm2.historical_wait_seconds() == 0.0, \
        "50 requests must no longer exhaust the budget"


def test_q30_budget_gate_uses_the_constant_not_a_literal():
    """Q-30: the budget maths must read settings.MAX_HISTORICAL_PER_600S."""
    import inspect
    src = inspect.getsource(pacing_mod.PacingManager.historical_wait_seconds)
    assert "settings.MAX_HISTORICAL_PER_600S" in src


def test_q30_wave_continuation_ticks_at_550ms(qapp):
    """Q-30: at 0.5 s spacing a deferred chunk re-issues after ~550 ms."""
    fake = _FakeHistClient()
    _host, session = _make_session(qapp, fake)
    delay = session._continuation_delay_ms(
        settings.HISTORICAL_MIN_INTERVAL_S)
    assert delay == 550, "0.5 s interval -> ceil(500 ms) + 50 ms margin"
    assert delay < 1000, "the old 1.0 s interval's tick must be gone"


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

def test_wave_spaces_chunks_and_continues(monkeypatch, qapp):
    """One request per interval; the rest queue and continue via the timer."""
    from ibkr.contracts import get_contract_for_symbol
    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    continued: list[float] = []
    monkeypatch.setattr(
        session._wave_continue_timer, "start",
        lambda ms: continued.append(ms),
    )
    contract = get_contract_for_symbol("AAA")
    session.queue_wave_plans([_plan(i) for i in range(25)],
                             contract, "5 mins", False)
    assert len(fake.hist) == 1, \
        "same-contract requests must be spaced, not burst"
    assert len(session._wave_plan_queue) == 24
    assert len(continued) == 1 and continued[0] > 0, \
        "continuation must be scheduled with a positive delay"
    assert any("pacing-limited" in m.lower() for m in host.status_bar.messages)
    # Simulate the interval elapsing, then fire the deferred continuation.
    for _ in range(24):
        pacing_mod.pacing_manager._last_hist_time = 0.0
        session._on_wave_continue_timeout()
    assert len(fake.hist) == 25, "every spaced chunk must be issued"
    assert session._wave_plan_queue == []
    assert len(continued) == 24, "one continuation per spaced chunk"


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
    # Budget exhausted: the wave must defer (not sleep, not issue).
    _exhaust_hist_budget(pacing_mod.pacing_manager, wait_s=600.0)
    session.queue_wave_plans([_plan(i) for i in range(50)],
                             get_contract_for_symbol("AAA"), "5 mins", False)
    assert len(fake.hist) == 0
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


# ── Q-3: deferred aggregator priming ─────────────────────────────────

def _deferred_prime_setup(monkeypatch, qapp, waiter):
    """Session + md stub whose priming requests are pacing-limited per ``waiter``.

    Returns (host, session, contract, attempts, scheduled, fake_timer_cls).
    ``waiter`` is called with the attempt count and may raise PacingExceeded.
    """
    from ibkr.contracts import get_contract_for_symbol
    import ui.ticker_session as ts_mod

    fake = _FakeHistClient()
    host, session = _make_session(qapp, fake)
    session.aggregator_for("5 mins")
    contract = get_contract_for_symbol("AAA")

    attempts: list[dict] = []

    def _req_historical_data(**kwargs):
        attempts.append(kwargs)
        return waiter(len(attempts))

    monkeypatch.setattr(
        host.md_manager, "req_historical_data", _req_historical_data
    )

    scheduled: list[tuple[int, object]] = []

    class _FakeQTimer:
        @staticmethod
        def singleShot(ms, fn):
            scheduled.append((ms, fn))

    monkeypatch.setattr(ts_mod, "QTimer", _FakeQTimer)
    return host, session, contract, attempts, scheduled


def test_prime_aggregator_defers_once_on_pacing(monkeypatch, qapp):
    """Q-3 (defect B): a pacing-limited prime is DEFERRED, then retried once.

    With HISTORICAL_MIN_INTERVAL_S the wait is non-zero after ANY historical
    request, so a load following a backfill wave would previously skip priming
    outright and lose the forming candle's partial-period bars.
    """
    def _waiter(attempt):
        if attempt == 1:
            raise PacingExceeded(1.0)
        return 4_242

    host, session, contract, attempts, scheduled = _deferred_prime_setup(
        monkeypatch, qapp, _waiter
    )
    assert session.prime_aggregator(
        contract, "5 mins", 1_700_000_000, False
    ) is True, "a deferred prime must hold the live feed back"
    assert len(attempts) == 1
    assert session._prime_retry_pending is True
    assert len(scheduled) == 1, "exactly one retry may be scheduled"
    assert scheduled[0][0] == 1000, "retry delay is max(1000, wait*1000) ms"
    assert session._prime_timer.isActive(), \
        "the prime timeout must remain the backstop"
    scheduled[0][1]()
    assert len(attempts) == 2, "the retry must re-enter prime_aggregator"
    assert session._prime_req_id == 4_242
    assert session._prime_retry_pending is False
    assert host.prime_completions == [], "a successful retry is not fail-open"


def test_prime_aggregator_fails_open_when_retry_also_paced(monkeypatch, qapp):
    """Q-3 (defect B): a second PacingExceeded fails open (no third attempt)."""
    def _waiter(attempt):
        raise PacingExceeded(1.0)

    host, session, contract, attempts, scheduled = _deferred_prime_setup(
        monkeypatch, qapp, _waiter
    )
    assert session.prime_aggregator(
        contract, "5 mins", 1_700_000_000, False
    ) is True
    scheduled[0][1]()
    assert len(attempts) == 2, "exactly one retry, never a busy loop"
    assert scheduled and len(scheduled) == 1, "no second retry may be scheduled"
    assert host.prime_completions == ["AAA"], \
        "fail open must attach the live feed after the retry is also paced"
    assert session._prime_retry_pending is False
