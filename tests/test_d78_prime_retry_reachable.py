"""D78 (P27-02): the prime's backstop is armed for the retry's own deadline.

DG135 / Journeys 72 / AC-D78.1-AC-D78.3 / AC-P27-02-4. A pacing refusal
schedules one retry at ``max(1000, wait_s * 1000)`` ms; before this fix the
backstop was a flat 15 s, so every wait > 15 s was pre-empted by the backstop
and the retry became a no-op. The backstop is now
``max(15_000, retry_ms + 1_000)`` for the deferral, while an issued prime
keeps the flat 15 s answer bound.

Both timers are modelled on a fake clock: the module-level
``QTimer.singleShot`` is captured, and the backstop is the session's real
``_prime_timer`` read through ``interval()`` and fired by hand. Nothing here
sleeps or waits on the wall clock, and the ticker_session module's clock is
pinned mid-period (the Q-80 device) so the retry's ``int(time.time())``
re-entry primes a real span.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QTimer as _RealQTimer

from ibkr.pacing import PacingExceeded

# A '5 mins' instant 260 s into its forming period: mid-period, so the prime
# (first attempt and retry alike) has a span to fetch. Same constant and
# rationale as Q-80's clock freeze in tests/test_d28_3_historical_pacing.py.
_PRIME_NOW_TS = 1_700_000_060

_SYMBOL = "D78"


# ── Fake clock / host harness ─────────────────────────────────────────


class _Clock:
    """Deterministic millisecond clock driving both of the prime's timers.

    Stands in for ``ui.ticker_session.time`` (``time()`` returns a frozen
    instant) and for ``ui.ticker_session.QTimer`` (only ``singleShot`` is
    reached from the prime path, and its call shape is one delay + one
    callback).
    """

    def __init__(self, ts=_PRIME_NOW_TS):
        self._ts = ts
        self.now_ms = 0
        self._entries: list[tuple[int, int, str, object]] = []
        self._seq = 0

    # -- ui.ticker_session.time --
    def time(self):
        return self._ts

    def __getattr__(self, name):
        return getattr(time, name)

    # -- ui.ticker_session.QTimer --
    def singleShot(self, ms, fn):
        self.schedule(ms, "retry", fn)

    # -- scheduling --
    def schedule(self, delay_ms, kind, callback):
        self._seq += 1
        self._entries.append(
            (self.now_ms + delay_ms, self._seq, kind, callback)
        )

    def due(self, kind):
        return sorted(
            due for due, _seq, k, _fn in self._entries if k == kind
        )

    def kinds(self):
        return {k for _due, _seq, k, _fn in self._entries}


class _FakeMD:
    """Stub md_manager: counts priming requests, raises per ``waiter``."""

    def __init__(self, waiter):
        self.waiter = waiter
        self.requests: list[dict] = []
        self.cancels: list[int] = []
        self._next = 5000

    def req_historical_data(self, **kwargs):
        self.requests.append(kwargs)
        outcome = self.waiter(len(self.requests))
        if isinstance(outcome, BaseException):
            raise outcome
        self._next += 1
        return self._next

    def cancel_historical_data(self, req_id):
        self.cancels.append(req_id)


class _StatusBar:
    def __init__(self):
        self.messages: list[str] = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _Harness:
    """One TickerSession on a fake clock, with attach/request spies."""

    def __init__(self, monkeypatch, waiter, symbol=_SYMBOL):
        import ui.ticker_session as ts_mod
        from ui.ticker_session import TickerSession

        self.ts_mod = ts_mod
        self.clock = _Clock()
        self.md = _FakeMD(waiter)
        self.attach_calls: list[str] = []          # fail-open / timeout attach
        self.prime_completions: list[str] = []
        self._req_table: dict[int, object] = {}

        host = SimpleNamespace()
        host.md_manager = self.md
        host.rt_manager = SimpleNamespace(
            subscribe=lambda *a, **k: 1,
            unsubscribe=lambda *a, **k: None,
        )
        host.sub_manager = SimpleNamespace(
            unsubscribe=lambda *a, **k: None,
        )
        host.status_bar = _StatusBar()
        host._register_req_id = (
            lambda req_id, sess: self._req_table.__setitem__(req_id, sess)
        )
        host._unregister_req_id = (
            lambda req_id: self._req_table.pop(req_id, None)
        )
        host._on_session_prime_complete = (
            lambda sess: (
                self.prime_completions.append(sess.symbol),
                self.attach_calls.append(sess.symbol),
            )
        )
        host._on_session_prime_timeout = (
            lambda sess: self.attach_calls.append(sess.symbol)
        )
        host._on_session_wave_complete = lambda sess: None
        host._on_session_wave_timeout = lambda sess: None
        self.host = host

        # Construct on the real Qt classes and clock first (a harness built
        # later in the same test must not inherit the previous fake), then
        # swap in the fake clock/QTimer for the prime path. The session's own
        # QTimers (_prime_timer included) stay real so interval() is readable.
        monkeypatch.setattr(ts_mod, "QTimer", _RealQTimer)
        monkeypatch.setattr(ts_mod, "time", time)
        self.session = TickerSession(symbol, host)
        self.session.aggregator_for("5 mins")
        self.contract = object()

        monkeypatch.setattr(ts_mod, "time", self.clock)
        monkeypatch.setattr(ts_mod, "QTimer", self.clock)

    # -- driving the prime --
    def prime(self, retrying=False):
        result = self.session.prime_aggregator(
            self.contract, "5 mins", _PRIME_NOW_TS, False, retrying=retrying
        )
        self.arm_backstop()
        return result

    def arm_backstop(self):
        """Mirror the session's armed backstop onto the fake clock.

        The fake clock models a one-shot QTimer: ``advance_to`` stops the
        real timer before invoking ``_on_prime_timeout``, and re-arms from
        the current instant after any callback that started it again.
        """
        self.clock._entries = [
            e for e in self.clock._entries if e[2] != "backstop"
        ]
        timer = self.session._prime_timer
        if timer.isActive():
            self.clock.schedule(
                timer.interval(), "backstop", self.session._on_prime_timeout
            )

    def advance_to(self, target_ms):
        assert target_ms >= self.clock.now_ms
        while True:
            due = sorted(
                e for e in self.clock._entries if e[0] <= target_ms
            )
            if not due:
                break
            entry = due[0]
            self.clock._entries.remove(entry)
            self.clock.now_ms = entry[0]
            if entry[2] == "backstop":
                self.session._prime_timer.stop()  # single-shot semantics
            entry[3]()
            self.arm_backstop()
        self.clock.now_ms = target_ms

    def fire_pending(self, kind):
        """Fire the earliest pending callback of ``kind`` at the current instant."""
        pending = sorted(e for e in self.clock._entries if e[2] == kind)
        assert pending, f"no pending {kind}"
        entry = pending[0]
        self.clock._entries.remove(entry)
        if kind == "backstop":
            self.session._prime_timer.stop()
        entry[3]()
        self.arm_backstop()


def _refuse_then_issue(wait_s):
    """First priming request refused with ``wait_s``; the retry issues."""
    def waiter(attempt):
        if attempt == 1:
            return PacingExceeded(wait_s)
        return None
    return waiter


def _always_refuse(wait_s):
    def waiter(attempt):
        return PacingExceeded(wait_s)
    return waiter


def _issue_always(attempt):
    return None


# ── AC-D78.1: the deferral backstop never pre-empts the retry ─────────


def test_p27_t2_01_retry_survives_past_the_old_flat_backstop(
    monkeypatch, qapp
):
    """wait=40: the retry is still pending at 15 s and at wait-epsilon."""
    h = _Harness(monkeypatch, _refuse_then_issue(40.0))

    assert h.prime() is True, "a deferred prime must hold the live feed back"
    assert len(h.md.requests) == 1, "exactly the first (refused) attempt"
    assert h.session._prime_retry_pending is True
    assert h.session._prime_timer.interval() == 41_000, (
        "the backstop is armed for the retry's own deadline (40 s + grace)"
    )
    assert h.clock.due("retry") == [40_000]
    assert h.clock.due("backstop") == [41_000]

    # 15 s: the old flat backstop instant. It must do nothing.
    h.advance_to(15_000)
    assert h.attach_calls == [], "the backstop pre-empted the retry"
    assert h.session._prime_retry_pending is True
    assert len(h.md.requests) == 1

    # wait - epsilon: still pending, still nothing attached.
    h.advance_to(39_999)
    assert h.attach_calls == []
    assert h.session._prime_retry_pending is True
    assert len(h.md.requests) == 1

    # The reported wait: the retry runs and the prime issues.
    h.advance_to(40_000)
    assert len(h.md.requests) == 2, "the retry must issue one priming request"
    assert h.session._prime_req_id is not None
    assert h.session._prime_retry_pending is False
    assert h.attach_calls == [], "a successful retry is not a fail-open"


# ── AC-P27-02-4: short waits keep today's flat 15 s ───────────────────


def test_p27_t2_02_short_wait_keeps_the_flat_backstop(monkeypatch, qapp):
    """wait=2 s: the interval is exactly 15_000 and the retry fires at 2 s."""
    from config import settings
    from ui import ticker_session as ts_mod

    # No pacing constant retuned, no new settings key: the priming delay is
    # derived, and the existing tunables keep their values.
    assert ts_mod._PRIME_BACKSTOP_MS == 15_000
    assert ts_mod._PRIME_RETRY_GRACE_MS == 1_000
    assert settings.HISTORICAL_MIN_INTERVAL_S == 0.5

    h = _Harness(monkeypatch, _refuse_then_issue(2.0))
    assert h.prime() is True
    assert h.session._prime_timer.interval() == 15_000, (
        "a wait at or below 14 s preserves today's backstop"
    )
    assert h.clock.due("retry") == [2_000]

    h.advance_to(2_000)
    assert len(h.md.requests) == 2, "the retry fires at 2 s and issues"
    assert h.session._prime_req_id is not None
    assert h.attach_calls == []


def test_p27_t2_03_fifteen_second_wait_gives_the_retry_the_grace_tick(
    monkeypatch, qapp
):
    """wait == 15 s (the grace tick's reason): 16_000 ms, retry first."""
    h = _Harness(monkeypatch, _refuse_then_issue(15.0))
    assert h.prime() is True
    assert h.session._prime_timer.interval() == 16_000
    assert h.clock.due("retry") == [15_000]
    assert h.clock.due("backstop") == [16_000]

    h.advance_to(15_000)
    assert h.attach_calls == [], "nothing is attached at the 15 s instant"
    assert len(h.md.requests) == 2, "the retry fired first and issued"
    assert h.session._prime_req_id is not None


# ── AC-D78.2: an issued prime attaches exactly once ──────────────────


def test_p27_t2_04_issued_prime_never_answers_attaches_once(
    monkeypatch, qapp
):
    """An unanswered issued prime: one attach, one request, no second try."""
    h = _Harness(monkeypatch, _issue_always)
    assert h.prime() is True
    assert h.session._prime_req_id is not None
    assert h.session._prime_timer.interval() == 15_000, (
        "an issued prime keeps the flat 15 s answer bound"
    )
    assert len(h.md.requests) == 1

    h.advance_to(15_000)  # the backstop elapses
    assert h.attach_calls == [_SYMBOL], "the live feed attaches exactly once"
    assert len(h.md.requests) == 1, "no second priming request follows"

    h.advance_to(200_000)  # nothing re-arms
    assert h.attach_calls == [_SYMBOL]
    assert len(h.md.requests) == 1


# ── AC-D78.3: refusal -> issue/attach is bounded by wait + grace + 15 ─


@pytest.mark.parametrize("wait_s", [1.0, 2.0, 14.0, 15.0, 40.0, 600.0])
def test_p27_t2_05_refusal_to_attach_bound(monkeypatch, qapp, wait_s):
    """Never unbounded: bounded by the reported wait (+ grace + 15 s)."""
    h = _Harness(monkeypatch, _refuse_then_issue(wait_s))
    assert h.prime() is True

    retry_ms = max(1000, int(wait_s * 1000))
    expected_backstop = max(15_000, retry_ms + 1_000)
    assert h.session._prime_timer.interval() == expected_backstop
    if wait_s == 600.0:
        # The historical-wait ceiling: the 600 s rolling window reports at
        # most ~600 s, so the deferral backstop arms at 601 s.
        assert h.session._prime_timer.interval() == 601_000

    h.advance_to(retry_ms)
    assert h.session._prime_req_id is not None, "the retry issued the prime"
    issue_ms = h.clock.now_ms
    assert h.session._prime_timer.interval() == 15_000, (
        "the issued-prime bound stays 15 s"
    )

    h.advance_to(retry_ms + 15_000)  # the issued prime never answers
    attach_ms = h.clock.now_ms
    assert len(h.attach_calls) == 1

    bound_ms = (wait_s + 1.0 + 15.0) * 1000
    assert issue_ms <= bound_ms
    assert attach_ms <= bound_ms, (
        "refusal-to-attach must stay within wait + grace + 15 s"
    )
    assert h.clock.kinds() == set(), "nothing is left armed"


# ── Journey 72's edges ───────────────────────────────────────────────


def test_p27_t2_06_journey72_edges(monkeypatch, qapp):
    """A refused retry, a superseding load, and a disconnect mid-deferral."""

    # (a) The retry is itself pacing-limited: fail open exactly once, no
    #     third attempt and no loop, however far the clock runs.
    h = _Harness(monkeypatch, _always_refuse(40.0))
    assert h.prime() is True
    h.advance_to(40_000)
    assert len(h.md.requests) == 2, "exactly one retry, never a loop"
    assert h.attach_calls == [_SYMBOL], "the refused retry fails open once"
    assert h.session._prime_skipped_count == 1
    assert h.session._prime_retry_pending is False
    assert h.clock.due("retry") == [], "no third attempt is ever scheduled"
    h.advance_to(10_000_000)
    assert len(h.md.requests) == 2
    assert h.attach_calls == [_SYMBOL]

    # (b) A new load during the deferral: its own prime governs and the
    #     stale singleShot callback is a no-op.
    h = _Harness(monkeypatch, _refuse_then_issue(40.0))
    assert h.prime() is True
    h.session.prepare_load("5 mins")
    assert h.session._prime_retry_pending is False
    h.arm_backstop()
    assert h.prime() is True, "the new load primes on its own"
    new_req_id = h.session._prime_req_id
    assert new_req_id is not None
    requests_before = len(h.md.requests)
    h.fire_pending("retry")  # the stale callback from the previous load
    assert len(h.md.requests) == requests_before
    assert h.session._prime_req_id == new_req_id
    assert h.attach_calls == [], "the stale callback attaches nothing"

    # (c) A disconnect during the deferral: the pending callback is harmless.
    h = _Harness(monkeypatch, _refuse_then_issue(40.0))
    assert h.prime() is True
    h.session.teardown()
    assert h.session._prime_retry_pending is False
    h.arm_backstop()
    assert h.session._prime_timer.isActive() is False
    requests_before = len(h.md.requests)
    h.fire_pending("retry")
    assert len(h.md.requests) == requests_before
    assert h.attach_calls == [], "a disconnect's stale callback attaches nothing"
    assert h.session._prime_req_id is None
