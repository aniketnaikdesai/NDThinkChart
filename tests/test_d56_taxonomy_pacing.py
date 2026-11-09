"""P17-T3 — error taxonomy + pacing gate for the retry (D56.3, D56.5).

Offscreen, clock-controlled suites (no live TWS):

- T31 / AC1: error injection parametrized over every inventoried
  historical-request code (162, 321, 200, 399, 504) on a cancel-tagged
  superseded reqId — debug-only, no status-bar message, no shortfall entry,
  no pacing event.
- T32 / AC1: a 162 on the re-issued (silence-retried) reqId finalizes short
  under existing error semantics with exactly two total issues (no third).
- T33 / AC2: pacing-spy wave with one silent chunk — both the cancelled and
  the re-issued reqIds consumed pacing slots; the post-issue cancel refunded
  nothing.
- T34 / AC2: PacingExceeded at re-issue time with no slot freeing before the
  watchdog horizon — the wave falls through to the unchanged watchdog
  strand-finalization (counted); no historical request is ever issued outside
  the pacing budget.

Harness follows tests/test_d56_silence_retry.py (offscreen MainWindow,
stubbed transport, clock control via the session's ``_silence_now`` seam).
"""

from __future__ import annotations

import logging
from collections import namedtuple

import pytest

from ibkr.pacing import PacingExceeded, pacing_manager
from ui.main_window import _SUPERSEDED_HISTORICAL_ACK_CODES

Plan = namedtuple("Plan", ["endDateTime", "bar_size", "duration"])

_INVENTORIED = (162, 321, 200, 399, 504)


class _ReqStub:
    """Captures ``req_historical_data`` calls and cancelled reqIds."""

    def __init__(self, first_id: int = 7000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, bar_size=None, duration=None):
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


class _PacingMirrorStub(_ReqStub):
    """Stub transport that mirrors the real pacing gate per issue.

    The real ``MarketDataManager.req_historical_data`` records one rolling
    budget slot per accepted request; the mirror does the same so the
    pacing-spy case (T33) observes genuine slot consumption.
    """

    def req(self, *args, **kwargs):
        req_id = super().req(*args, **kwargs)
        pacing_manager.record_historical_slot()
        return req_id


class _PacingLimitedStub(_ReqStub):
    """Stub transport whose budget is exhausted after the first issue."""

    def req(self, *args, **kwargs):
        if self.calls:
            raise PacingExceeded(3600.0)  # no slot frees pre-watchdog
        return super().req(*args, **kwargs)


def _make_session(monkeypatch, qapp, symbol: str, stub=None):
    """A live ``TickerSession`` on a shown ``MainWindow`` with stub transport."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()

    if stub is None:
        stub = _ReqStub()
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel

    session = win.get_or_create_session(symbol)
    # Clock control: replace the monotonic seam BEFORE the wave issues.
    clock = {"t": 5000.0}
    session._silence_now = lambda: clock["t"]
    return win, session, stub, clock


def _issue(session, stub, plans) -> list[int]:
    session.queue_wave_plans(list(plans), None, "5 mins", False)
    assert session._silence_timer.isActive()
    return [c["reqId"] for c in stub.calls]


def _plan(end: str) -> Plan:
    return Plan(endDateTime=end, bar_size="5 mins", duration="5 D")


def _retry_by_silence(session, clock) -> None:
    clock["t"] += 31.0
    session._sweep_silent_chunks()


# ---------------------------------------------------------------------------
# T31 / AC1 — every inventoried code on a superseded reqId is a cancel-ack
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code", _INVENTORIED)
def test_t31_superseded_req_id_any_inventoried_code_is_debug_only(
        monkeypatch, qapp, caplog, code):
    assert set(_INVENTORIED) == set(_SUPERSEDED_HISTORICAL_ACK_CODES)
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T31X")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])
        _retry_by_silence(session, clock)
        assert len(stub.calls) == 2
        new_id = stub.calls[1]["reqId"]
        assert old_id in session._cancelled_history_req_ids
        assert session._history_req_ids == {new_id}

        pacing_before = len(pacing_manager._hist_times)
        queue_before = list(session._wave_plan_queue)
        failed_before = set(session._backfill_failed_req_ids)
        win.status_bar.showMessage("baseline-marker", 8000)
        baseline = win.status_bar.currentMessage()
        continue_active_before = session._wave_continue_timer.isActive()

        caplog.set_level(logging.DEBUG, logger="ui.main_window")
        caplog.clear()
        win._on_error(old_id, code, f"injected historical error {code}")

        # Debug-only: a debug record naming the superseded reqId...
        assert any(
            r.name == "ui.main_window"
            and r.levelno == logging.DEBUG
            and str(old_id) in r.getMessage()
            for r in caplog.records
        )
        # ...with zero user-facing or budget effect.
        assert win.status_bar.currentMessage() == baseline
        assert session._backfill_failed_req_ids == failed_before
        assert len(stub.calls) == 2  # no third issue
        assert list(session._wave_plan_queue) == queue_before
        assert len(pacing_manager._hist_times) == pacing_before
        assert session._wave_continue_timer.isActive() == continue_active_before
        # The fresh re-issued reqId is untouched by the superseded error.
        assert session._history_req_ids == {new_id}
        assert session._req_to_plan[new_id] is plan
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T32 / AC1 — 162 on the re-issued reqId finalizes short (exactly two issues)
# ---------------------------------------------------------------------------
def test_t32_fresh_req_id_162_after_silence_retry_finalizes_short(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T32X")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])
        _retry_by_silence(session, clock)
        assert len(stub.calls) == 2
        new_id = stub.calls[1]["reqId"]
        assert plan in session._retried_plans

        # Existing error semantics on the fresh reqId: the shared allowance
        # is checked first, so the already-retried plan finalizes short.
        win._on_error(new_id, 162, "Historical data request pacing violation")

        assert len(stub.calls) == 2  # no third issue
        assert new_id not in session._history_req_ids
        assert new_id in session._backfill_failed_req_ids
        assert plan in session._retried_plans
        # ... the terminal failed-requests message stands — a wave-terminating
        # error must not overwrite the finalise surfacing with a transient
        # error line (P19-T2: terminal state wins over transient errors).
        assert "failed" in win.status_bar.currentMessage()
        assert "162" not in win.status_bar.currentMessage()
        # ... and the wave finalised (fail-open, nothing left in flight).
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T33 / AC2 — both issues consumed pacing slots; post-issue cancel: no refund
# ---------------------------------------------------------------------------
def test_t33_silence_retry_consumes_two_slots_with_no_refund(monkeypatch, qapp):
    pacing_manager.reset_for_tests()
    refunds = {"n": 0}
    real_refund = pacing_manager.refund_historical_slot

    def _counting_refund():
        refunds["n"] += 1
        return real_refund()

    monkeypatch.setattr(
        pacing_manager, "refund_historical_slot", _counting_refund
    )
    win, session, stub, clock = _make_session(
        monkeypatch, qapp, "T33X", stub=_PacingMirrorStub()
    )
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])
        assert len(pacing_manager._hist_times) == 1  # first issue: one slot

        _retry_by_silence(session, clock)

        assert stub.cancelled == [old_id]
        assert len(stub.calls) == 2
        new_id = stub.calls[1]["reqId"]
        # Both the cancelled and the re-issued reqIds consumed pacing slots.
        assert len(pacing_manager._hist_times) == 2
        # Post-issue cancel keeps its slot — no refund on either leg.
        assert refunds["n"] == 0
        # The re-issue is marked post-issue issued (its slot is owned).
        assert new_id in session._history_req_issued
        assert plan in session._retried_plans
    finally:
        pacing_manager.reset_for_tests()
        win.close()


# ---------------------------------------------------------------------------
# T34 / AC2 — PacingExceeded at re-issue: counted watchdog fall-through
# ---------------------------------------------------------------------------
def test_t34_pacing_exhaustion_at_reissue_falls_through_watchdog(
        monkeypatch, qapp):
    win, session, stub, clock = _make_session(
        monkeypatch, qapp, "T34X", stub=_PacingLimitedStub()
    )
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])

        # The silence retry attempts the paced re-issue; the budget is
        # exhausted, so it waits via the existing continuation path.
        _retry_by_silence(session, clock)

        assert len(stub.calls) == 1  # no unpaced request ever issued
        assert session._wave_plan_queue == [plan]  # deferred, not dropped
        assert session._wave_continue_timer.isActive()
        assert session._history_req_ids == set()
        assert plan in session._retried_plans  # allowance spent: no 3rd issue

        # Watchdog fires first (no slot frees before the horizon): the
        # unchanged strand-finalization runs — counted and fail-open.
        seen: dict = {}
        real_finalize = win._finalize_history_wave

        def _spy(target=None):
            if target is not None:
                seen["reason"] = target._history_stranded_reason
            return real_finalize(target)

        monkeypatch.setattr(win, "_finalize_history_wave", _spy)
        win._on_session_history_wave_timeout(session)

        assert seen.get("reason") == "Historical backfill timed out"
        assert len(stub.calls) == 1  # the rolling budget was never violated
        assert session._history_req_ids == set()
        assert session._wave_plan_queue == []
        assert win.status_bar.currentMessage()
    finally:
        win.close()
