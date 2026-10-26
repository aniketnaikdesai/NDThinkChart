"""Q-17 — the backfill wave must PROGRESS, not re-schedule forever.

LIVE STALL: the wave issued exactly one chunk, then repeated
``AAPL - pacing-limited, continuing backfill in 0s...`` forever.

Root cause was a rounding race in the pacing gate (Q-2): the continuation timer
was armed with ``max(1000, int(wait_s * 1000))``. Qt's default coarse timer may
fire a few percent early, so the tick landed a hair BEFORE
``HISTORICAL_MIN_INTERVAL_S`` had elapsed; ``req_historical_data`` raised
``PacingExceeded(0.0004)`` without issuing, and the wave scheduled another full
second that missed the gate the same way — forever. ``int(wait_s)`` printed 0.

The fix makes the wait authoritative rather than exact: ``historical_wait_seconds``
pads the binding interval wait with a safety margin, the continuation adds
``ceil + 50 ms``, and a near-zero residual retries on a 50 ms tick instead of a
full second.

This file pins the CONTRACT the stall violated: N queued plans must produce N
requests, driven over a real Qt event loop against a manager that enforces the
interval rule. A wave that schedules continuations without issuing fails here.
"""

from __future__ import annotations

import time

import pytest

from config import settings
from ibkr.pacing import PacingExceeded, PacingManager
from services.backfill_service import RequestPlan

INTERVAL = settings.HISTORICAL_MIN_INTERVAL_S

# Qt's default (coarse) timer may fire up to ~5% early. Reproduce that
# deterministically by arming each continuation slightly short — the wave must
# still converge; the old code spun one full second at a time and never did.
_EARLY_FIRE_MS = 5


def _plan(i: int) -> RequestPlan:
    return RequestPlan(
        endDateTime=f"2024010{i % 9 + 1}  16:00:00",
        duration="5 D",
        bar_size="5 mins",
        span_start_ts=1_700_000_000 + i,
        span_end_ts=1_700_100_000 + i,
    )


class _FakeHistClient:
    def __init__(self) -> None:
        self.ids: list[int] = []

    def reqHistoricalData(self, req_id, *args, **kwargs):
        self.ids.append(req_id)

    def cancelHistoricalData(self, req_id):
        pass


class _StatusBar:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _IntervalMD:
    """md_manager double enforcing the SAME strict interval rule as pacing.

    Every attempt is counted and a too-early attempt raises
    ``PacingExceeded`` with the exact residual wait, exactly like
    ``MarketDataManager.req_historical_data``. A wave that only re-schedules
    (never issues) therefore shows up as ``attempts >> issued``.
    """

    def __init__(self, interval: float = INTERVAL) -> None:
        self.interval = interval
        self.last_issue: float | None = None
        self.attempts = 0
        self.rejections = 0
        self.issued: list[dict] = []

    def req_historical_data(self, **kwargs):
        self.attempts += 1
        now = time.time()
        if self.last_issue is not None:
            residual = self.interval - (now - self.last_issue)
            if residual > 0:
                self.rejections += 1
                raise PacingExceeded(residual)
        self.last_issue = now
        self.issued.append(kwargs)
        return 9_000 + len(self.issued)

    def cancel_historical_data(self, req_id):
        pass


class _Host:
    def __init__(self, md) -> None:
        self.md_manager = md
        self.status_bar = _StatusBar()
        self._req_table: dict[int, object] = {}
        self.wave_completions: list[str] = []

    def _register_req_id(self, req_id, session):
        self._req_table[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_table.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        self.wave_completions.append(session.symbol)


def _make_session(qapp, md=None):
    from ui.ticker_session import TickerSession

    md = md or _IntervalMD()
    host = _Host(md)
    return host, TickerSession("AAA", host), md


# ── The pacing gate itself: sleeping exactly the reported wait is accepted ──


def test_sleeping_exactly_the_reported_wait_lets_the_next_request_issue(qapp):
    """The returned wait must be authoritative, not an epsilon hole.

    A caller that sleeps exactly ``historical_wait_seconds()`` must find the
    gate open — otherwise every deferred request is rejected on the tick and
    the wave can never progress (the Q-17 stall).
    """
    from ibkr.contracts import get_contract_for_symbol

    from ibkr import pacing as pacing_mod
    from ibkr.market_data import MarketDataManager

    fake = _FakeHistClient()
    mgr = MarketDataManager(fake)
    contract = get_contract_for_symbol("AAPL")

    first = mgr.req_historical_data(contract, "5 mins")
    wait_s = pacing_mod.pacing_manager.historical_wait_seconds()
    assert wait_s > 0.0, "a just-issued request must hold the interval gate"

    time.sleep(wait_s)

    second = mgr.req_historical_data(contract, "5 mins")
    assert fake.ids == [first, second], (
        "sleeping exactly the reported wait must be accepted")


def test_hair_early_interval_reading_is_padded_past_the_gate():
    """A residual of 0.0004 s must not be reported as-is.

    This is the exact live reading: the tick landed a hair before the strict
    interval comparison, raising ``PacingExceeded(0.0004)``. The reported wait
    must carry a real margin so one short sleep clears the gate.
    """
    pm = PacingManager()
    pm._last_hist_time = time.time() - (INTERVAL - 0.0004)

    wait_s = pm.historical_wait_seconds()
    assert wait_s > 0.02, (
        f"a 0.0004 s residual must be padded, got {wait_s}")

    time.sleep(wait_s)
    assert pm.historical_wait_seconds() == 0.0


# ── The continuation delay: never a full second on a near-zero residual ─────


def test_near_zero_continuation_retries_on_a_short_tick(qapp, monkeypatch):
    """A near-zero PacingExceeded must tick in ~50 ms, not reschedule 1 s."""
    host, session, _md = _make_session(qapp)
    armed: list[int] = []
    monkeypatch.setattr(
        session._wave_continue_timer, "start", lambda ms: armed.append(ms)
    )

    # The live stall: 0.0004 s left on the interval gate.
    session._schedule_wave_continuation(0.0004)
    assert armed == [50], f"near-zero wait must tick short, got {armed}"
    assert any("<0.1s" in m for m in host.status_bar.messages)
    assert not any("in 0s" in m for m in host.status_bar.messages), \
        "the status line must never claim a 0 s wait"

    # A real interval wait keeps a ceil + margin delay (must land past it).
    session._schedule_wave_continuation(1.0)
    assert armed[-1] == 1050, f"ceil + 50 ms margin expected, got {armed[-1]}"


# ── The wave: N plans → N requests, over a real event loop ──────────────────


def test_wave_progresses_under_interval_pacing(qapp, monkeypatch):
    """N queued plans must produce N issued requests (Q-17 regression).

    The manager enforces the strict interval rule and the continuation timer
    is armed a few ms short every time — exactly what the production stall
    did. The wave must still issue every plan: one continuation per chunk,
    with the near-zero retry converging immediately instead of spinning.
    A wave that only schedules continuations fails the ``issued == N`` assert.
    """
    from ibkr.contracts import get_contract_for_symbol

    n_plans = 4
    host, session, md = _make_session(qapp)

    original_start = session._wave_continue_timer.start

    def _early_start(ms):
        # Deterministically reproduce a Qt coarse timer firing early.
        original_start(max(0, int(ms) - _EARLY_FIRE_MS))

    monkeypatch.setattr(session._wave_continue_timer, "start", _early_start)

    session.queue_wave_plans(
        [_plan(i) for i in range(n_plans)],
        get_contract_for_symbol("AAA"),
        "5 mins",
        False,
    )

    deadline = time.monotonic() + 10.0
    while len(md.issued) < n_plans and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.002)

    assert len(md.issued) == n_plans, (
        f"the wave stalled: {len(md.issued)}/{n_plans} issued after "
        f"{md.attempts} attempts ({md.rejections} rejected on the interval "
        f"gate)")
    # Each plan after the first costs one immediate rejection (the issuer tries
    # the next chunk at once) plus one accepted deferred attempt. Qt's coarse
    # timer may fire up to 5% early, so allow ONE more near-miss per chunk —
    # the short-tick retry then converges. The old code paid TWO extra
    # attempts per chunk (every continuation re-armed a full second and missed
    # again), so it exceeds this bound.
    assert md.attempts <= 2 * n_plans, (
        f"the wave is spinning, not progressing: {md.attempts} attempts for "
        f"{len(md.issued)} issued chunks ({md.rejections} rejections)")
    assert session._wave_plan_queue == [], "every plan must leave the queue"
    assert not any("in 0s" in m for m in host.status_bar.messages), \
        "no status line may report a 0 s continuation"

    session.teardown()
