"""Q-12 — the deferred aggregator-prime retry must be genuinely single-shot.

Q-3 (defect B) added exactly ONE deferred retry for a pacing-limited
``prime_aggregator``: the wait is non-zero after any historical request, so a
load that follows a backfill wave almost always lands there.

The retry identified itself through mutable instance state
(``_prime_retry_used``) instead of an explicit argument, so anything else that
entered ``prime_aggregator`` between the defer and the scheduled retry (a chart
reload calling ``prepare_load``, a second view's load) could leave the retry
looking like a first-time call. A first-time call that is still pacing-limited
logs the same warning, restarts the 15 s backstop timer and schedules another
1-second retry: with pacing still closed the live feed never attaches and the
backfill wave never starts ("Aggregator priming pacing-limited; retrying once
in 1.0s" repeating forever).

These tests pin the contract: the retry is an explicit ``retrying=True`` call,
it never re-arms itself, a still-closed budget fails open exactly once, and a
reload's stale scheduled callback is a no-op.
"""
import logging

import pytest

from ibkr.pacing import PacingExceeded

# 200 s into a 300 s '5 mins' candle, so a prime always has a span to fetch.
FIXED_TS = 1_700_000_200
PRIME_LOGGER = "ui.ticker_session"
PACED_WARNING = "Aggregator priming pacing-limited"


class _StubHost:
    """Minimal host: reqId routing + the prime-complete callback."""

    def __init__(self):
        self.prime_completions: list[str] = []

    def _register_req_id(self, req_id, session):
        pass

    def _unregister_req_id(self, req_id):
        pass

    def _on_session_prime_complete(self, session):
        self.prime_completions.append(session.symbol)


class _StubMD:
    """md_manager double: counts every attempt and answers from ``waiter``."""

    def __init__(self, waiter):
        self.waiter = waiter
        self.attempts: list[dict] = []

    def req_historical_data(self, **kwargs):
        self.attempts.append(kwargs)
        return self.waiter(len(self.attempts))


def _always_paced(_attempt):
    raise PacingExceeded(1.0)


@pytest.fixture
def prime_env(monkeypatch, qapp):
    """Session with a '5 mins' aggregator and a captured retry scheduler."""
    import ui.ticker_session as ts_mod
    from ui.ticker_session import TickerSession

    def _build(waiter):
        host = _StubHost()
        session = TickerSession("AAA", host)
        md = _StubMD(waiter)
        host.md_manager = md
        agg = session.aggregator_for("5 mins")
        # Deterministic span for both the first call and the retry (which
        # stamps its own now): 100 s into the candle, always prime-able.
        agg.period_start = lambda ts: ts - 100
        scheduled: list[tuple[int, object]] = []

        class _FakeQTimer:
            @staticmethod
            def singleShot(ms, fn):
                scheduled.append((ms, fn))

        # Patched after construction: _prime_timer stays a real QTimer.
        monkeypatch.setattr(ts_mod, "QTimer", _FakeQTimer)
        return host, session, md, scheduled

    return _build


def _paced_warnings(caplog) -> list[str]:
    return [
        rec.getMessage() for rec in caplog.records
        if PACED_WARNING in rec.getMessage()
    ]


def test_prime_retry_fails_open_after_exactly_two_attempts(prime_env, caplog):
    """(a) two attempts, (b) one fail-open, (c) nothing re-armed, (d) one warning.

    With pacing closed on both attempts the retry must fail open: attach the
    live feed, stop the backstop timer and leave no retry pending. Anything
    else is the Q-12 loop.
    """
    caplog.set_level(logging.WARNING, logger=PRIME_LOGGER)
    host, session, md, scheduled = prime_env(_always_paced)

    assert session.prime_aggregator(object(), "5 mins", FIXED_TS, False) is True
    assert len(md.attempts) == 1
    assert len(scheduled) == 1, "exactly one retry may be scheduled"
    assert session._prime_retry_pending is True
    assert session._prime_timer.isActive(), "the 15 s backstop is armed"

    scheduled[0][1]()  # the deferred retry fires

    assert len(md.attempts) == 2, "initial attempt + exactly one retry, never N"
    assert len(scheduled) == 1, "a retry that cannot issue must not reschedule"
    assert host.prime_completions == ["AAA"], "a still-closed budget fails open"
    assert session._prime_retry_pending is False
    assert session._prime_retry_args is None
    assert not session._prime_timer.isActive(), \
        "the retry must not restart the backstop it cannot honour"
    assert session._prime_req_id is None
    assert len(_paced_warnings(caplog)) == 1, \
        "the pacing-limited warning is logged once per load, not per attempt"


def test_prime_retry_issues_when_the_budget_freed_up(prime_env):
    """The retry is a real second attempt: when the budget freed it issues."""
    def _freed_on_retry(attempt):
        if attempt == 1:
            raise PacingExceeded(1.0)
        return 4_242

    host, session, md, scheduled = prime_env(_freed_on_retry)

    assert session.prime_aggregator(object(), "5 mins", FIXED_TS, False) is True
    scheduled[0][1]()

    assert len(md.attempts) == 2
    assert session._prime_req_id == 4_242, "the retry registered its request"
    assert host.prime_completions == [], "a successful retry is not fail-open"
    assert session._prime_retry_pending is False
    assert session._prime_timer.isActive(), "the backstop guards the issued request"


def test_prepare_load_cancels_a_stale_scheduled_retry(prime_env, caplog):
    """A reload must make the superseded load's scheduled retry a no-op.

    Without this the stale callback primes a load that no longer exists and
    fails open for the wrong generation — and, while pacing is still closed,
    it re-enters as a first-time attempt and re-arms itself (the Q-12 loop).
    """
    caplog.set_level(logging.WARNING, logger=PRIME_LOGGER)
    host, session, md, scheduled = prime_env(_always_paced)

    assert session.prime_aggregator(object(), "5 mins", FIXED_TS, False) is True
    assert len(scheduled) == 1

    session.prepare_load("5 mins")
    assert session._prime_retry_pending is False
    assert session._prime_retry_args is None

    scheduled[0][1]()  # stale callback from the superseded load

    assert len(md.attempts) == 1, "the stale retry must not issue"
    assert len(scheduled) == 1, "and must not re-arm"
    assert host.prime_completions == [], "and must not attach a feed for it"
    assert not session._prime_timer.isActive()
