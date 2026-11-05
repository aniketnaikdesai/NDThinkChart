"""P17-T1 — silence detection + cancel/re-issue core (D56.1, D56.2-guard).

Offscreen clock-controlled waves driven directly on ``TickerSession`` with a
stubbed transport. The session's monotonic clock (``_silence_now``) is
replaced by a fake so the 30 s silence windows are deterministic; the
sweeper is invoked explicitly (no QTimer waits).

No test here weakens, skips or rewrites an existing test.
"""

from __future__ import annotations

from collections import namedtuple

import pytest

Plan = namedtuple("Plan", ["endDateTime", "bar_size", "duration"])


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))  # 10-digit epoch string -> parse_ibkr_date
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


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


def _make_session(monkeypatch, qapp, symbol: str):
    """A live ``TickerSession`` on a shown ``MainWindow`` with stub transport."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()

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


# ---------------------------------------------------------------------------
# T11 / AC1 — zero-bar-silent chunk: cancel + exactly-once identical re-issue
# ---------------------------------------------------------------------------
def test_t11_zero_bar_silent_chunk_cancelled_and_reissued_once(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T56A")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])

        # Zero bars, no END, no error: advance past 30 s of silence.
        clock["t"] += 31.0
        session._sweep_silent_chunks()

        assert stub.cancelled == [old_id]
        assert len(stub.calls) == 2
        first, second = stub.calls
        # Identical plan: same symbol/timeframe/mode/span at a new reqId.
        assert second["reqId"] != old_id
        for key in ("timeframe", "endDateTime", "extended_hours",
                    "bar_size", "duration"):
            assert second[key] == first[key], key
        new_id = second["reqId"]
        # Same plan position under the current generation.
        assert session._req_to_plan[new_id] is plan
        assert (session._history_req_generation[new_id]
                == session._history_generation)
        # In-flight set drops the old reqId and tracks the new one.
        assert old_id not in session._history_req_ids
        assert session._history_req_ids == {new_id}
        # Superseded tagging with the post-issue slot kept (no refund).
        assert old_id in session._cancelled_history_req_ids
        # Shared allowance records the retried plan.
        assert plan in session._retried_plans
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 / AC2 — partial-then-stalled chunk; trailing window restarts on bars
# ---------------------------------------------------------------------------
def test_t12_partial_chunk_stalled_retried_once(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T56B")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])

        # Two bars, then stall with no END/error.
        session.on_historical_bar(old_id, _FakeIbBar(1_700_000_000))
        clock["t"] += 10.0
        session.on_historical_bar(old_id, _FakeIbBar(1_700_000_300))
        assert len(session._pending_bars) == 2

        clock["t"] += 30.0
        session._sweep_silent_chunks()

        assert stub.cancelled == [old_id]
        assert len(stub.calls) == 2
        new_id = stub.calls[1]["reqId"]
        # Identity-removal: the old partial bars leave _pending_bars.
        assert session._pending_bars == []
        assert session._history_req_ids == {new_id}
        assert session._req_to_plan[new_id] is plan
    finally:
        win.close()


def test_t12_bar_at_30s_minus_epsilon_restarts_trailing_window(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T56C")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])

        session.on_historical_bar(old_id, _FakeIbBar(1_700_000_000))
        # A bar 29.9 s after the previous one restarts the trailing window.
        clock["t"] += 29.9
        session.on_historical_bar(old_id, _FakeIbBar(1_700_000_300))
        # 30 s after ISSUE but only 0.1 s after the last accepted bar.
        session._sweep_silent_chunks()

        assert stub.cancelled == []
        assert len(stub.calls) == 1
        assert session._history_req_ids == {old_id}
        # The delivered bar was processed normally.
        assert len(session._pending_bars) == 2
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T13 / AC3 — re-issue silence never re-issues (no third issue)
# ---------------------------------------------------------------------------
def test_t13_silent_reissue_never_retried_again(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T56D")
    try:
        plan = _plan("20260105-20:00:00")
        (first_id,) = _issue(session, stub, [plan])

        clock["t"] += 31.0
        session._sweep_silent_chunks()
        assert len(stub.calls) == 2
        second_id = stub.calls[1]["reqId"]
        assert plan in session._retried_plans

        # The re-issue is itself silent past 30 s under the same rules.
        clock["t"] += 31.0
        session._sweep_silent_chunks()

        assert len(stub.calls) == 2  # no third issue
        assert stub.cancelled == [first_id]  # re-issue never cancelled
        assert session._history_req_ids == {second_id}
        assert second_id in session._history_req_last_activity
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T14 / AC1 — silent at 30 s minus epsilon then delivering: no retry
# ---------------------------------------------------------------------------
def test_t14_zero_bar_silent_until_just_before_bound_then_bar_no_retry(
        monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T56E")
    try:
        plan = _plan("20260105-20:00:00")
        (old_id,) = _issue(session, stub, [plan])

        # Silent until just before the bound, then a bar arrives.
        clock["t"] += 29.9
        session._sweep_silent_chunks()
        assert stub.cancelled == []
        session.on_historical_bar(old_id, _FakeIbBar(1_700_000_000))
        session._sweep_silent_chunks()

        assert stub.cancelled == []
        assert len(stub.calls) == 1
        assert session._history_req_ids == {old_id}
        # The delivered bar is processed normally.
        assert len(session._pending_bars) == 1
    finally:
        win.close()
