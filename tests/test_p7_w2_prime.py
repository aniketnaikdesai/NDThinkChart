"""P7-W2 (S-P7-4): aggregator-prime precedence over the backfill wave.

T11 — start a multi-chunk wave and the D27.9 prime together with a closed
       shared historical-interval gate; the prime retry holds an explicit
       reservation and the wave continuation slips by exactly one
       HISTORICAL_MIN_INTERVAL_S, so the prime issues instead of starving.
       Ordering (prime before the wave continuation) is preserved across
       repeated runs.
T12 — force the prime retry to also find the gate closed; the fail-open
       live-feed attach carries a warning naming the skipped prime for its
       symbol/timeframe plus a skip counter, while the existing
       one-retry/fail-open semantics are otherwise unchanged (D27.9 intact).

Fake-transport note: the stub gates req_historical_data behind a flag
without touching ``pacing_manager``, so the suites are hermetic. Real
``MainWindow`` + real ``TickerSession`` wiring throughout — no production
logic re-implemented in the doubles.
"""

from __future__ import annotations

import logging
import time
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDockWidget


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.rt_manager.unsubscribe = lambda *a, **k: None
    win.rt_manager.cancel_all = lambda *a, **k: None
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


class _GateStub:
    """Fake transport with a controllable historical-interval gate.

    Closed: every ``req_historical_data`` raises ``PacingExceeded`` with the
    configured wait (the shared interval gate both the wave and the prime
    hit). Open: issues reqIds and records the call shape so the suite can
    tell prime requests (``5 secs`` bars) from wave chunks (``1 min``).
    """

    def __init__(self, wait_s: float = 0.5, first_id: int = 7100):
        self.closed = True
        self.wait_s = wait_s
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None):
        from ibkr.pacing import PacingExceeded

        if self.closed:
            raise PacingExceeded(self.wait_s)
        req_id = self._next
        self._next += 1
        self.calls.append({
            "reqId": req_id,
            "timeframe": timeframe,
            "bar_size": bar_size,
            "duration": duration,
            "endDateTime": endDateTime,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _wave_plans(n: int = 3) -> list:
    """Wave chunks shaped like the planner's RequestPlans (1-min bars)."""
    return [
        SimpleNamespace(
            endDateTime=f"2025010{i + 1}-00:00:00",
            bar_size="1 min",
            duration="1 D",
        )
        for i in range(n)
    ]


def _prime_now(sess, timeframe: str = "5 mins") -> int:
    """A ``now`` 120 s into the current forming period (primeable span)."""
    agg = sess.aggregator_for(timeframe)
    start = agg.period_start(int(time.time()))
    now = start + 120
    assert agg.period_start(now) == start  # same forming period
    return now


# ---------------------------------------------------------------------------
# T11 — prime precedence: the wave slips by exactly one interval
# ---------------------------------------------------------------------------
def test_t11_prime_precedence_defers_wave_by_exactly_one_interval(
    monkeypatch, qapp
):
    from config import settings

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _GateStub(wait_s=0.5)
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel

        interval = settings.HISTORICAL_MIN_INTERVAL_S
        assert interval == 0.5  # the delay under test is this tunable

        for run in range(3):
            symbol = f"P7W2P{run}"
            sess = win.get_or_create_session(symbol)
            stub.closed = True  # every run starts with the gate closed
            contract = object()
            base = len(stub.calls)

            # A full wave starts alongside the prime with the gate closed:
            # nothing issues; the wave parks on a continuation for the
            # gate wait while the remainder stays queued.
            sess.queue_wave_plans(_wave_plans(3), contract, "5 mins", False)
            assert len(stub.calls) == base
            assert len(sess._wave_plan_queue) == 3
            assert sess._wave_continue_timer.isActive()
            interval_before = sess._wave_continue_timer.interval()
            assert interval_before == sess._continuation_delay_ms(0.5)

            # The prime starts alongside and hits the same closed gate: it
            # defers (one retry) instead of skipping, and takes an explicit
            # reservation against the gate.
            prime_now = _prime_now(sess)
            assert sess.prime_aggregator(
                contract, "5 mins", prime_now, False
            ) is True
            assert sess._prime_retry_pending is True
            assert sess._prime_reserved is True

            # The wave continuation slips by exactly one interval — never a
            # new literal, always the tunable.
            expected = sess._continuation_delay_ms(
                0.5 + settings.HISTORICAL_MIN_INTERVAL_S
            )
            assert sess._wave_continue_timer.interval() == expected
            assert expected != interval_before

            # The gate opens: the prime retry fires first and issues (the
            # reservation releases), then the wave continuation issues its
            # chunks. Ordering holds on every run.
            stub.closed = False
            monkeypatch.setattr(time, "time", lambda: prime_now)
            sess._on_prime_retry()
            assert sess._prime_req_id is not None
            assert sess._prime_reserved is False
            prime_rid = sess._prime_req_id

            sess._on_wave_continue_timeout()
            new_calls = stub.calls[base:]
            prime_calls = [c for c in new_calls if c["bar_size"] == "5 secs"]
            wave_calls = [c for c in new_calls if c["bar_size"] == "1 min"]
            assert [c["reqId"] for c in prime_calls] == [prime_rid]
            assert len(wave_calls) == 3
            order = [c["reqId"] for c in new_calls]
            assert order.index(prime_rid) < order.index(
                wave_calls[0]["reqId"]
            )
            assert sess._wave_plan_queue == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 — a skipped prime is a counted warning; fail-open otherwise unchanged
# ---------------------------------------------------------------------------
def test_t12_skipped_prime_warns_counts_and_fails_open(monkeypatch, qapp,
                                                      caplog):
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _GateStub(wait_s=0.5)
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel

        sess = win.get_or_create_session("P7W2S")
        win._current_symbol = "P7W2S"  # the prime belongs to the shown chart
        contract = object()
        prime_now = _prime_now(sess)

        # First attempt hits the closed gate: deferred, not skipped.
        assert sess.prime_aggregator(
            contract, "5 mins", prime_now, False
        ) is True
        assert sess._prime_retry_pending is True
        assert sess._prime_reserved is True
        assert sess._prime_skipped_count == 0

        # The retry also finds the gate closed: fail open to the live feed.
        attached: list = []
        real_complete = win._on_session_prime_complete

        def spy_complete(session):
            attached.append(session)
            return real_complete(session)

        monkeypatch.setattr(
            win, "_on_session_prime_complete", spy_complete
        )
        with caplog.at_level(logging.WARNING, logger="ui.ticker_session"):
            monkeypatch.setattr(time, "time", lambda: prime_now)
            sess._on_prime_retry()

        # The live feed attaches fail-open (D27.9 intact) ...
        assert attached == [sess]
        assert sess.rt_req_id == 4242
        # ... the retry machinery is spent — never a second retry ...
        assert sess._prime_retry_pending is False
        assert sess._prime_retry_args is None
        assert sess._prime_reserved is False
        assert sess._prime_req_id is None
        # ... and the skip is a counted warning naming symbol + timeframe.
        assert sess._prime_skipped_count == 1
        prime_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "prime" in r.message.lower()
        ]
        assert any(
            "P7W2S" in r.message and "5 mins" in r.message
            for r in prime_warnings
        )

        # A stale retry after the fail-open is a no-op: no second attach,
        # no second count (the existing one-retry semantics are unchanged).
        sess._on_prime_retry()
        assert attached == [sess]
        assert sess._prime_skipped_count == 1
    finally:
        win.close()
