"""P7-W2 (S-P7-3): watchdog/pacing coherence — the stranded-wave watchdog
covers pacing deferrals, and a strand finalise stops the continuation timer
and clears the plan queue so a finalised wave can never resume.

T11 — schedule continuations with waits from ~1 s up to the full
       budget-window wait; arm the watchdog and show the armed bound is at
       least W + margin (so advancing time past the old fixed 120 s bound
       while still inside W + margin cannot strand the wave); a wait beyond
       the computed bound still strands exactly once.
T12 — force a strand (watchdog timeout, plus a disconnect) with queued
       plans and an armed continuation timer; then advance timers and
       deliver a late end marker: timer stopped, queue empty, exactly one
       finalise; late markers and timer ticks after the strand change
       nothing.

Fake-transport note: the stub counts/issues reqIds without touching
``pacing_manager``, so the suites are hermetic. Real ``MainWindow`` +
real ``TickerSession`` wiring throughout — no production logic re-implemented
in the doubles.
"""

from __future__ import annotations

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


class _ReqStub:
    """Counting fake transport: issues reqIds, records cancels."""

    def __init__(self, first_id: int = 9500):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None):
        req_id = self._next
        self._next += 1
        self.calls.append({"reqId": req_id, "endDateTime": endDateTime})
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _arm_wave(win, stub, symbol: str, n_inflight: int = 2,
              n_queued: int = 2, continue_ms: int = 60_000):
    """Register a live wave on a fresh session: in-flight reqIds, queued
    plans, an armed continuation timer and an armed watchdog."""
    sess = win.get_or_create_session(symbol)
    sess._wave_timeframe = "5 mins"
    sess._wave_extended_hours = False
    for _ in range(n_inflight):
        rid = stub._next
        stub._next += 1
        sess._register_history_request(rid)
    sess._wave_plan_queue = [object() for _ in range(n_queued)]
    sess._wave_continue_timer.start(continue_ms)
    sess._arm_history_wave_watchdog()
    return sess


# ---------------------------------------------------------------------------
# T11 — the watchdog bound covers pacing deferrals up to the full window
# ---------------------------------------------------------------------------
def test_t11_watchdog_covers_pacing_deferral(monkeypatch, qapp):
    from ibkr import pacing as pacing_mod
    from ui.ticker_session import (
        _WATCHDOG_BASE_WINDOW_FRACTION,
        _WATCHDOG_MARGIN_WINDOW_FRACTION,
    )

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel

        window_s = float(pacing_mod.pacing_manager._hist_window)
        assert window_s >= 600.0 - 1e-9  # the rolling budget window
        base_ms = int(window_s * _WATCHDOG_BASE_WINDOW_FRACTION * 1000.0)
        margin_ms = int(window_s * _WATCHDOG_MARGIN_WINDOW_FRACTION * 1000.0)
        assert base_ms == 120_000  # old fixed bound, now a window fraction

        sess = win.get_or_create_session("P7W2A")

        # Waits from ~1 s up to the full budget-window continuation.
        waits = [1.0, 30.0, 90.0, 119.0, 120.0, 300.0, window_s]
        for wait in waits:
            sess._schedule_wave_continuation(wait)
            bound = sess._history_wave_bound_ms
            assert sess._history_wave_timer.isActive()
            assert sess._history_wave_timer.interval() == bound
            # Never below the scheduled delay + margin ...
            assert bound >= int(wait * 1000.0) + margin_ms
            assert bound == max(base_ms, int(wait * 1000.0) + margin_ms)
            # ... and past the old fixed 120 s bound while still inside
            # W + margin, the wave is NOT stranded: time may advance past
            # 120 s with the watchdog still pending.
            if int(wait * 1000.0) + margin_ms > 120_000:
                assert bound > 120_000
                assert sess._history_wave_timer.remainingTime() > 120_000

        # A wait beyond the computed bound still strands — exactly once.
        sess2 = _arm_wave(win, stub, "P7W2B")
        calls: list = []
        real_finalize = win._finalize_history_wave

        def spy_finalize(session=None):
            calls.append(session)
            return real_finalize(session)

        monkeypatch.setattr(win, "_finalize_history_wave", spy_finalize)
        sess2._on_history_wave_timeout()  # past the bound: strands
        assert calls == [sess2]
        sess2._on_history_wave_timeout()  # second fire: no-op
        assert calls == [sess2]

        # The bound is window-relative, never literal: halving the window
        # halves both the base and the margin (tunables untouched).
        monkeypatch.setattr(
            pacing_mod.pacing_manager, "_hist_window", window_s / 2
        )
        assert sess._history_wave_watchdog_bound_ms(0.0) == base_ms // 2
        assert sess._history_wave_watchdog_bound_ms(window_s / 2) == (
            max(base_ms // 2, int(window_s / 2 * 1000.0) + margin_ms // 2)
        )
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 — a strand stops the timer, clears the queue, finalises exactly once
# ---------------------------------------------------------------------------
def test_t12_strand_clears_timer_and_queue_finalises_once(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel

        calls: list = []
        real_finalize = win._finalize_history_wave

        def spy_finalize(session=None):
            calls.append(session)
            return real_finalize(session)

        monkeypatch.setattr(win, "_finalize_history_wave", spy_finalize)

        # ---- timeout strand with queued plans + armed continuation timer --
        sess = _arm_wave(win, stub, "P7W2C")
        in_flight = set(sess._history_req_ids)
        assert len(in_flight) == 2
        assert len(sess._wave_plan_queue) == 2
        assert sess._wave_continue_timer.isActive()

        sess._on_history_wave_timeout()

        assert calls == [sess]  # exactly one finalise
        assert sess._wave_continue_timer.isActive() is False  # timer stopped
        assert sess._wave_plan_queue == []  # queue cleared
        assert sess._history_req_ids == set()

        # Late end marker for a pre-drop reqId: fenced, changes nothing.
        late_rid = next(iter(in_flight))
        win._on_historical_data_end(late_rid)  # routing table dropped it
        sess.on_historical_data_end(late_rid)  # generation fence rejects it
        assert calls == [sess]
        assert sess._pending_bars == []
        assert sess._wave_plan_queue == []

        # Late continuation tick after the strand: no resume, no re-finalise.
        n_transport_calls = len(stub.calls)
        sess._on_wave_continue_timeout()
        assert len(stub.calls) == n_transport_calls  # no further chunk issues
        assert calls == [sess]  # no second finalise
        assert sess._wave_continue_timer.isActive() is False

        # ---- disconnect strand behaves identically ------------------------
        sess2 = _arm_wave(win, stub, "P7W2D")
        assert sess2._wave_continue_timer.isActive()
        assert len(sess2._wave_plan_queue) == 2

        win._on_disconnected()

        assert calls == [sess, sess2]  # exactly one more finalise
        assert sess2._wave_continue_timer.isActive() is False
        assert sess2._wave_plan_queue == []
        assert sess2._history_req_ids == set()
        # The armed-then-stranded timer never resurrects the wave either.
        sess2._on_wave_continue_timeout()
        assert calls == [sess, sess2]
        assert len(stub.calls) == n_transport_calls
    finally:
        win.close()
