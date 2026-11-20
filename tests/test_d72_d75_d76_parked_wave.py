"""P26/D72 + D75 + D76: a cap-parked wave is a healthy, resumable state and a
readiness episode stays bounded.

One lifecycle, three faces:

* D72 — the per-load cap yield is a **parked** state. When the last issued
  member ends, the strand bound and the continuation timer are settled
  (nothing is left to bound); a member that never answers keeps the bound and
  is still finalised once, exactly as before.
* D75 — the parked queue survives the identical-triple load (coalesce) and
  resumes from its own oldest plan; a genuine triple change still cancels,
  advances the generation and clears the old queue.
* D76 — a client that reports not-ready defers on the unchanged fallback with
  the strand bound armed **once** per episode, so an indefinitely not-ready
  client ends through one bounded finalise whose reason names the transport.

Fake-transport note: the stub transport owns reqId issue order and cancels and
never touches ``pacing_manager``; the pacing budget is an explicit counter, so
the suites are hermetic. Real ``MainWindow`` + real ``TickerSession`` wiring
throughout — no production logic is re-implemented in the doubles.

Clock note: the session's timers are driven directly (``_on_wave_continue_timeout``
for a continuation tick, ``_on_history_wave_timeout`` for the bound elapsing).
That is the deterministic equivalent of advancing ``QTimer`` time offscreen and
is the same seam ``tests/test_p7_w2_watchdog.py`` uses.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

from ibkr.error_codes import IBKRNotReady
from ibkr.pacing import pacing_manager
from services.backfill_service import MissingSpan
from ui.ticker_session import (
    _WATCHDOG_BASE_WINDOW_FRACTION,
    per_load_historical_cap,
)

CAP = per_load_historical_cap()
SYMBOL = "AAPL"
TF = "5 mins"
MODE = True


# ── Fakes ────────────────────────────────────────────────────────────────────

class _Plan:
    """Minimal backfill plan: identity plus the fields the wave forwards."""

    def __init__(self, tag: int):
        self.tag = tag
        self.endDateTime = f"2026{tag:06d}-00:00:00"
        self.bar_size = "5 mins"
        self.duration = "1 D"

    def __repr__(self) -> str:  # diagnostics only
        return f"<Plan {self.tag}>"


class _PacingBudget:
    """Admission counter: every issued request spends one unit."""

    def __init__(self, budget: int):
        self.budget = int(budget)
        self.admitted = 0

    def admit(self) -> None:
        self.admitted += 1
        assert self.admitted <= self.budget, (
            f"pacing budget exceeded: {self.admitted} > {self.budget}"
        )


class _Transport:
    """Recording fake transport: issue order, cancels, readiness switch."""

    def __init__(self, pacing: _PacingBudget):
        self.pacing = pacing
        self.requests: list[tuple[int, str]] = []
        self.cancels: list[int] = []
        self.attempts = 0
        self.not_ready = False
        self._next = 7000

    def req_historical_data(self, contract, **kwargs):
        self.attempts += 1
        if self.not_ready:
            raise IBKRNotReady("handshake pending")
        self.pacing.admit()
        self._next += 1
        self.requests.append((self._next, kwargs.get("endDateTime", "")))
        return self._next

    def cancel_historical_data(self, req_id: int) -> None:
        self.cancels.append(req_id)


class _StatusBar:
    """Status-bar double: records every surfaced line."""

    def __init__(self):
        self.messages: list[str] = []

    def showMessage(self, text, timeout: int = 0) -> None:
        self.messages.append(str(text))

    def currentMessage(self) -> str:
        return self.messages[-1] if self.messages else ""

    def clearMessage(self) -> None:
        self.messages.clear()


class _FakeBarCache:
    """In-memory mode-aware bar store (mirrors the BarCache call shape)."""

    store: dict = {}

    @classmethod
    def _key(cls, symbol, timeframe, ext_hours):
        return (symbol, timeframe, bool(ext_hours))

    @classmethod
    def save_bars(cls, bars, ext_hours=True):
        if not bars:
            return
        key = cls._key(bars[0].symbol, bars[0].timeframe, ext_hours)
        bucket = cls.store.setdefault(key, {})
        for bar in bars:
            bucket[bar.ts] = bar

    @classmethod
    def get_bars(cls, symbol, timeframe, ext_hours=True):
        bucket = cls.store.get(cls._key(symbol, timeframe, ext_hours), {})
        return [bucket[ts] for ts in sorted(bucket)]

    @classmethod
    def prune(cls, symbol, timeframe, ext_hours=True, keep=5000):
        bucket = cls.store.get(cls._key(symbol, timeframe, ext_hours), {})
        for ts in sorted(bucket)[:-keep]:
            del bucket[ts]

    @classmethod
    def reset(cls):
        cls.store = {}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def window(qapp, monkeypatch):
    """A real MainWindow: socket stubbed, fake transport, fake bar cache."""
    from ibkr.client import IBApiClient
    from ui import main_window as mw_mod
    from ui import ticker_session as ts_mod

    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    monkeypatch.setattr(ts_mod, "BarCache", _FakeBarCache)
    monkeypatch.setattr(mw_mod, "BarCache", _FakeBarCache)
    _FakeBarCache.reset()
    pacing_manager.reset_for_tests()

    win = mw_mod.MainWindow()
    win.status_bar = _StatusBar()
    win._current_symbol = SYMBOL
    win._current_tf = TF
    win.show()
    qapp.processEvents()
    try:
        yield win
    finally:
        win.close()
        pacing_manager.reset_for_tests()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _install_transport(window, monkeypatch, budget: int, not_ready=False):
    transport = _Transport(_PacingBudget(budget))
    transport.not_ready = not_ready
    monkeypatch.setattr(
        window.md_manager, "req_historical_data",
        transport.req_historical_data,
    )
    monkeypatch.setattr(
        window.md_manager, "cancel_historical_data",
        transport.cancel_historical_data,
    )
    return transport


def _park(window, plans, *, symbol=SYMBOL, timeframe=TF, mode=MODE):
    """Queue ``plans`` on a session: the cap yield parks the remainder."""
    session = window.get_or_create_session(symbol)
    session._wave_timeframe = timeframe
    session._wave_extended_hours = mode
    session.queue_wave_plans(plans, object(), timeframe, mode)
    return session


def _end_all(window, session):
    for req_id in list(session._history_req_ids):
        window._on_historical_data_end(req_id)


def _spy_finalize(window, monkeypatch):
    """Record every finalise with its (soon consumed) stranded reason."""
    seen: list[tuple] = []
    real = window._finalize_history_wave

    def spy(session=None):
        seen.append((session, session._history_stranded_reason))
        return real(session)

    monkeypatch.setattr(window, "_finalize_history_wave", spy)
    return seen


def _shortfall_span() -> MissingSpan:
    """A Mon–Fri span with no cached bars: the AC-D16.4 shortfall is certain."""
    start = int(datetime(2026, 11, 9, 12, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2026, 11, 13, 12, tzinfo=timezone.utc).timestamp())
    return MissingSpan(start, end)


def _spy_arm(session, monkeypatch):
    """Record every watchdog arm's ``wait_s`` argument."""
    arms: list[float] = []
    real = session._arm_history_wave_watchdog

    def spy(wait_s: float = 0.0):
        arms.append(wait_s)
        return real(wait_s)

    monkeypatch.setattr(session, "_arm_history_wave_watchdog", spy)
    return arms


def _spy_continuation(session, monkeypatch):
    """Record every continuation start (one per deferred tick)."""
    calls: list[tuple] = []
    real = session._schedule_wave_continuation

    def spy(wait_s, *, transport_not_ready: bool = False):
        calls.append((wait_s, transport_not_ready))
        return real(wait_s, transport_not_ready=transport_not_ready)

    monkeypatch.setattr(session, "_schedule_wave_continuation", spy)
    return calls


# ── AC1 — an ended parked wave is never stranded ─────────────────────────────

def test_p26_t2_ac1_parked_wave_is_healthy_not_stranded(window, monkeypatch):
    """Every issued member ended at the cap yield: twice the bound later the
    wave is still parked, the queue is intact, the indicator says so and no
    finalise (and no shortfall line) ever ran."""
    transport = _install_transport(window, monkeypatch, budget=2 * CAP)
    finalised = _spy_finalize(window, monkeypatch)

    plans = [_Plan(i) for i in range(CAP + 4)]
    session = _park(window, plans)
    assert session._wave_parked is True
    assert len(session._history_req_ids) == CAP
    assert len(session._wave_plan_queue) == 4
    # The load path arms the bound for a wave with members in flight.
    session._arm_history_wave_watchdog()
    assert session._history_wave_timer.isActive() is True

    queue_obj = session._wave_plan_queue
    queued = list(queue_obj)

    _end_all(window, session)

    # Every issued member ended: parked and idle, queue untouched.
    assert finalised == []
    assert session._history_req_ids == set()
    assert session._wave_parked is True
    assert session._wave_plan_queue is queue_obj
    assert len(session._wave_plan_queue) == len(queued)
    assert all(a is b for a, b in zip(session._wave_plan_queue, queued))
    assert session._history_wave_timer.isActive() is False
    assert session._wave_continue_timer.isActive() is False

    # The D53 indicator reports the parked/queued state.
    text = window._backfill_indicator.text()
    assert "parked" in text
    assert f"{len(queued)} queued" in text

    # Twice the watchdog bound later: no stranded finalise, no shortfall.
    twice_bound = 2 * session._history_wave_watchdog_bound_ms(0.0)
    assert twice_bound > 0
    session._on_history_wave_timeout()
    session._on_history_wave_timeout()

    assert finalised == []
    assert session._wave_plan_queue is queue_obj
    assert len(session._wave_plan_queue) == len(queued)
    assert session._history_wave_timer.isActive() is False
    assert not any(
        "timed out" in m or "backfill incomplete" in m
        or "chart may be incomplete" in m
        for m in window.status_bar.messages
    )
    assert len(transport.requests) == CAP  # nothing re-issued, nothing spent


# ── AC2 — a stalled member of a parked wave is still bounded ────────────────

def test_p26_t2_ac2_stalled_member_of_parked_wave_strands_once(
    window, monkeypatch
):
    """One member of a cap-yielded wave never answers: the bound elapses,
    finalises exactly once with the stranded reason and the AC-D16.4 line,
    and drops the queue exactly as before the change."""
    _install_transport(window, monkeypatch, budget=2 * CAP)
    finalised = _spy_finalize(window, monkeypatch)

    plans = [_Plan(i) for i in range(CAP + 1)]
    session = _park(window, plans)
    session._backfill_missing_spans = [_shortfall_span()]
    session._arm_history_wave_watchdog()

    in_flight = sorted(session._history_req_ids)
    assert len(in_flight) == CAP
    assert len(session._wave_plan_queue) == 1

    # Every member but one ends; the parked wave keeps its bound (R166).
    for req_id in in_flight[:-1]:
        window._on_historical_data_end(req_id)
    assert len(session._history_req_ids) == 1
    assert session._history_wave_timer.isActive() is True

    session._on_history_wave_timeout()

    assert len(finalised) == 1
    _, reason = finalised[0]
    assert reason == "Historical backfill timed out"
    assert session._history_req_ids == set()
    assert session._wave_plan_queue == []
    assert session._history_wave_timer.isActive() is False
    assert any(
        "backfill incomplete" in m and "[Historical backfill timed out]" in m
        for m in window.status_bar.messages
    )

    # A second bound fire changes nothing: the strand finalised exactly once.
    session._on_history_wave_timeout()
    assert len(finalised) == 1


# ── AC3 — the identical reload resumes the parked queue ─────────────────────

def test_p26_t2_ac3_identical_reload_resumes_from_queue_head(
    window, monkeypatch
):
    """A parked wave reloaded on the identical triple issues its oldest queued
    plan first, leaves the parked state, re-arms the bound and spends no
    duplicate request across both loads."""
    transport = _install_transport(window, monkeypatch, budget=2 * CAP)
    finalised = _spy_finalize(window, monkeypatch)

    plans = [_Plan(i) for i in range(CAP + 3)]
    session = _park(window, plans)
    _end_all(window, session)  # parked and idle

    assert "parked" in window._backfill_indicator.text()
    queue_head = session._wave_plan_queue[0]
    queued = list(session._wave_plan_queue)
    issued_before = len(transport.requests)
    assert issued_before == CAP
    cancelled_before = list(transport.cancels)

    window.load_chart(SYMBOL, TF, MODE)

    # No cancel, no generation advance: the queue itself is the resume.
    assert transport.cancels == cancelled_before
    # Oldest queued plan issued first.
    first_after_reload = transport.requests[issued_before]
    assert first_after_reload[1] == queue_head.endDateTime
    # The indicator leaves the parked state and the bound is re-armed.
    assert "parked" not in window._backfill_indicator.text()
    assert session._history_wave_timer.isActive() is True
    # The whole queued remainder issued, oldest-first, exactly once each.
    issued_after = [end for _, end in transport.requests[issued_before:]]
    assert issued_after == [plan.endDateTime for plan in queued]
    assert session._wave_plan_queue == []
    # Inside the pacing budget, and no duplicate request across both loads.
    ends = [end for _, end in transport.requests]
    assert len(ends) == len(set(ends)) == len(plans)
    assert transport.pacing.admitted == len(plans) <= transport.pacing.budget
    assert finalised == []


# ── AC4 — the coalesce keeps the queue's identity and the prefetch ──────────

def test_p26_t2_ac4_coalesce_keeps_queue_identity_and_prefetch(
    window, monkeypatch
):
    """Coalescing a parked wave cancels nothing, keeps the very same queue
    object and contents through the decision, preserves ``_pending_prefetch``
    and issues only the queued plans, one request each."""
    transport = _install_transport(window, monkeypatch, budget=2 * CAP)
    _spy_finalize(window, monkeypatch)

    plans = [_Plan(i) for i in range(CAP + 2)]
    session = _park(window, plans)
    _end_all(window, session)

    session._pending_prefetch = True
    queue_obj = session._wave_plan_queue
    queued = list(queue_obj)
    cancelled_before = list(transport.cancels)
    issued_before = len(transport.requests)

    # Observe the queue exactly at the instant the coalesce branch resumes.
    observed: dict = {}
    real_issue = session._issue_wave_chunks

    def spy_issue(max_per_wave=None):
        observed["queue"] = session._wave_plan_queue
        observed["contents"] = list(session._wave_plan_queue)
        observed["parked"] = session._wave_parked
        observed["allowance"] = session._wave_issued_this_load
        observed["armed"] = session._history_wave_timer.isActive()
        return real_issue(max_per_wave)

    monkeypatch.setattr(session, "_issue_wave_chunks", spy_issue)

    window.load_chart(SYMBOL, TF, MODE)

    assert transport.cancels == cancelled_before  # no cancel occurred
    assert observed["queue"] is queue_obj  # same object, not a copy
    assert len(observed["contents"]) == len(queued)
    assert all(a is b for a, b in zip(observed["contents"], queued))
    assert observed["parked"] is False  # the park is cleared before issuing
    assert observed["allowance"] == 0  # a fresh per-load allowance
    assert observed["armed"] is True  # the resumed work is bounded again
    assert session._pending_prefetch is True
    # The queued plans themselves, each once, and no extra request.
    issued_after = [end for _, end in transport.requests[issued_before:]]
    assert issued_after == [plan.endDateTime for plan in queued]
    assert len(transport.requests) == len(plans)


# ── AC5 — a genuine triple change still cancels and clears ──────────────────

@pytest.mark.parametrize("change", ["symbol", "timeframe", "mode"])
def test_p26_t2_ac5_triple_change_cancels_and_clears_parked_queue(
    window, monkeypatch, change
):
    """A different symbol, timeframe or mode runs the existing cancel path,
    advances the generation and clears the old parked queue."""
    transport = _install_transport(window, monkeypatch, budget=4 * CAP)
    _spy_finalize(window, monkeypatch)

    plans = [_Plan(i) for i in range(CAP + 2)]
    session = _park(window, plans)
    window._primary_session = session
    queue_obj = session._wave_plan_queue
    assert queue_obj  # the old queue is populated
    generation_before = session._history_generation
    assert session._history_req_ids  # members in flight: the cancel is visible

    if change == "symbol":
        target_symbol, target_tf, target_mode = "MSFT", TF, MODE
    elif change == "timeframe":
        target_symbol, target_tf, target_mode = SYMBOL, "15 mins", MODE
    else:
        target_symbol, target_tf, target_mode = SYMBOL, TF, not MODE

    window.load_chart(target_symbol, target_tf, target_mode)

    # The existing cancel path ran for the parked wave's members.
    assert transport.cancels, (
        "the load path must cancel the previous wave's in-flight requests"
    )
    # The old queue is cleared (same list object, emptied), never resumed.
    assert queue_obj == []
    # The generation advanced for the new wave (or the new session's did).
    target = window.get_or_create_session(target_symbol)
    if target is session:
        assert target._history_generation == generation_before + 1
        assert session._wave_parked is False
    else:
        assert target._history_generation == 1
        assert session._wave_parked is False


# ── AC6 — an indefinitely not-ready client is bounded and named ─────────────

def test_p26_t2_ac6_not_ready_client_is_bounded_and_named(
    window, monkeypatch
):
    """Every issue raises IBKRNotReady: the bound is armed once with the base
    bound and never re-armed by the 1 s ticks; past the bound the wave ends in
    exactly one finalise whose reason names the transport, and the retry count
    no longer grows."""
    transport = _install_transport(
        window, monkeypatch, budget=CAP, not_ready=True
    )
    finalised = _spy_finalize(window, monkeypatch)

    session = window.get_or_create_session(SYMBOL)
    session._wave_timeframe = TF
    session._wave_extended_hours = MODE
    session._backfill_missing_spans = [_shortfall_span()]
    arms = _spy_arm(session, monkeypatch)
    continuations = _spy_continuation(session, monkeypatch)

    base = int(
        float(pacing_manager._hist_window) * _WATCHDOG_BASE_WINDOW_FRACTION
        * 1000.0
    )
    assert base > 0
    assert session._history_wave_watchdog_bound_ms(0.0) == base

    session.queue_wave_plans([_Plan(i) for i in range(4)], object(), TF, MODE)

    # One episode: the base bound armed once, one surfaced line, one timer.
    assert arms == [0.0]
    assert session._history_wave_bound_ms == base
    assert session._history_wave_timer.isActive() is True
    assert continuations == [(1.0, True)]
    attempts_after_first = transport.attempts
    episode_lines = [
        m for m in window.status_bar.messages if "IBKR not ready" in m
    ]
    assert len(episode_lines) == 1

    # Many fixed 1 s ticks: never re-armed, never a second continuation.
    for _ in range(200):
        session._on_wave_continue_timeout()
        assert session._history_wave_timer.isActive() is True
    assert arms == [0.0]  # armed once per episode, not per tick
    assert session._history_wave_bound_ms == base
    assert transport.attempts == attempts_after_first + 200
    assert len(continuations) == 201  # exactly one continuation per tick
    assert len(
        [m for m in window.status_bar.messages if "IBKR not ready" in m]
    ) == 1

    # The bound elapses: one finalise, reason names the transport.
    session._on_history_wave_timeout()
    assert len(finalised) == 1
    _, reason = finalised[0]
    assert reason == "IBKR not ready"
    assert session._wave_plan_queue == []
    assert session._history_wave_timer.isActive() is False
    assert any(
        "[IBKR not ready]" in m and "backfill incomplete" in m
        for m in window.status_bar.messages
    )

    # After the bounded end the retry count no longer grows at all.
    attempts_at_end = transport.attempts
    for _ in range(10):
        session._on_wave_continue_timeout()
    assert transport.attempts == attempts_at_end
    assert len(finalised) == 1
    assert arms == [0.0]


# ── AC7 — readiness lands: issue immediately, one continuation at a time ────

def test_p26_t2_ac7_readiness_lands_and_issues_immediately(window, monkeypatch):
    """Two seconds of not-ready then readiness: the queued plans issue as soon
    as readiness lands, one continuation was pending at a time, and every arm
    used the base bound for the episode the deferral actually covered."""
    transport = _install_transport(
        window, monkeypatch, budget=CAP, not_ready=True
    )
    _spy_finalize(window, monkeypatch)

    session = window.get_or_create_session(SYMBOL)
    session._wave_timeframe = TF
    session._wave_extended_hours = MODE
    arms = _spy_arm(session, monkeypatch)
    continuations = _spy_continuation(session, monkeypatch)

    plans = [_Plan(i) for i in range(4)]
    session.queue_wave_plans(plans, object(), TF, MODE)
    base = session._history_wave_watchdog_bound_ms(0.0)
    assert arms == [0.0]
    assert session._history_wave_bound_ms == base

    # Two seconds of not-ready: one continuation pending at a time.
    for tick in range(2):
        session._on_wave_continue_timeout()
        assert len(continuations) == tick + 2  # one per tick, never stacked
        assert session._wave_continue_timer.isActive() is True
    assert arms == [0.0]
    assert transport.requests == []

    # Readiness lands: the pending tick issues the queue immediately.
    transport.not_ready = False
    session._on_wave_continue_timeout()

    assert session._wave_plan_queue == []
    assert [end for _, end in transport.requests] == [
        plan.endDateTime for plan in plans
    ]
    assert session._wave_deferral_reason == ""
    assert session._wave_not_ready_announced is False
    # No per-tick re-arm, and no continuation left for an empty queue.
    assert arms == [0.0]
    assert len(continuations) == 3
    assert session._history_wave_bound_ms == base


# ── AC8 — a disconnect still strands and drops the parked queue ─────────────

def test_p26_t2_ac8_disconnect_strands_parked_queue_once(window, monkeypatch):
    """A parked wave ends through the unchanged disconnect strand path: queue
    dropped, generation advanced, exactly one finalise — the parked guard
    exists only in the watchdog timeout handler."""
    _install_transport(window, monkeypatch, budget=2 * CAP)
    finalised = _spy_finalize(window, monkeypatch)

    session = _park(window, [_Plan(i) for i in range(CAP + 3)])
    session._backfill_missing_spans = [_shortfall_span()]
    session._arm_history_wave_watchdog()
    generation_before = session._history_generation
    assert session._wave_parked is True
    assert session._wave_plan_queue

    window._on_disconnected()

    assert session._wave_plan_queue == []
    assert session._history_req_ids == set()
    assert session._history_generation == generation_before + 1
    assert len(finalised) == 1
    _, reason = finalised[0]
    assert reason == "Disconnected from IBKR"
    assert session._history_wave_timer.isActive() is False

    # Supporting source assertion: the parked guard is not on this path.
    source = inspect.getsource(
        type(window)._finalize_stranded_history_wave
    )
    assert "_wave_parked" not in source
