"""D27.4 — stream health: no unconditional "Live stream active".

Each live RT subscription carries stream-health state
(subscribed/awaiting-first-bar/live/failed+code) with a persistent,
non-transient indicator; failed RT subs retry with backoff.

AC-D27.4: failed reqRealTimeBars -> persistent indicator with the error
code + a scheduled backoff retry.
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient
from ibkr.stream_health import StreamHealth, StreamState


# ---------------------------------------------------------------------------
# Value object (pure)
# ---------------------------------------------------------------------------


def test_stream_health_transitions():
    h = StreamHealth()
    assert h.state == StreamState.SUBSCRIBED
    h.mark_first_bar()
    assert h.state == StreamState.LIVE
    h.mark_failed(162, "pacing violation")
    assert h.state == StreamState.FAILED
    assert h.fail_code == 162
    # A new subscription resets to awaiting.
    h.mark_subscribed()
    assert h.state == StreamState.AWAITING_FIRST_BAR
    assert h.fail_code is None
    assert h.retry_attempt == 0


# ---------------------------------------------------------------------------
# Window wiring
# ---------------------------------------------------------------------------


class _FakeTws:
    def reqRealTimeBars(self, reqId, *a, **k):
        pass

    def cancelRealTimeBars(self, reqId):
        pass


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.client = _FakeTws()
    _req_ids = iter(range(9001, 9999))
    win.md_manager.req_historical_data = lambda **k: next(_req_ids)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win):
    win._now_ts = lambda: 1_760_000_000
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()


def _complete_priming(win):
    """D27.9: the live feed attaches only after priming completes. Drive the
    (bar-less) priming end so tests reach the subscribed state."""
    assert win._prime_req_id is not None, "expected a priming request in flight"
    win._on_historical_data_end(win._prime_req_id)
    assert win._rt_req_id is not None


def test_d27_4_failed_rt_sub_marks_failed_with_code_and_retry(monkeypatch,
                                                             qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _complete_priming(win)
    rt_id = win._rt_req_id
    assert rt_id is not None
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR

    # The RT subscription fails (e.g. pacing 162 / no market-data perms).
    win._on_error(rt_id, 162, "Historical data request pacing violation")

    h = win._stream_health
    assert h.state == StreamState.FAILED
    assert h.fail_code == 162
    # Persistent, non-transient indicator carries the code.
    assert "162" in win.stream_badge.text()
    # A backoff retry is scheduled.
    assert win._rt_retry_timer.isActive()


def test_d27_4_retry_resubscribes_and_live_on_first_bar(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _complete_priming(win)
    win._ibkr_connected = True  # failure struck a live connection
    rt_id_1 = win._rt_req_id
    win._on_error(rt_id_1, 162, "pacing violation")
    assert win._stream_health.state == StreamState.FAILED

    # Fire the scheduled retry directly (no waiting on the timer).
    win._rt_retry_timer.stop()
    win._retry_rt_subscribe()

    rt_id_2 = win._rt_req_id
    assert rt_id_2 != rt_id_1, "retry must issue a new subscription"
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR

    # First bar on the new subscription -> live.
    win._on_realtime_bar(rt_id_2, 1_760_000_000, 10, 11, 9, 10.5,
                         100, 10.5, 5)
    assert win._stream_health.state == StreamState.LIVE
    assert "live" in win.stream_badge.text().lower()
    # Retry timer disarmed once live.
    assert not win._rt_retry_timer.isActive()


def test_d27_4_stale_retry_after_reload_is_noop(monkeypatch, qapp):
    """A retry scheduled for a previous load must not resurrect it."""
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _complete_priming(win)
    win._on_error(win._rt_req_id, 162, "pacing violation")
    assert win._rt_retry_timer.isActive()

    # User loads a different symbol before the timer fires.
    win.symbol_input.setText("OTHER")
    win.load_chart()
    _complete_priming(win)
    other_rt_id = win._rt_req_id

    # The stale retry fires: must not touch the new subscription.
    win._retry_rt_subscribe()
    assert win._rt_req_id == other_rt_id


def test_mark_subscribed_reset_backoff_flag():
    """Fix-B (unit): mark_subscribed() accepts reset_backoff; False keeps the
    attempt count so consecutive failures keep progressing the backoff."""
    h = StreamHealth()
    h.next_retry_delay_s()  # attempt 1 -> 5s
    h.next_retry_delay_s()  # attempt 2 -> 10s
    assert h.retry_attempt == 2
    # A backoff retry re-subscribes WITHOUT resetting the counter.
    h.mark_subscribed(reset_backoff=False)
    assert h.state == StreamState.AWAITING_FIRST_BAR
    assert h.retry_attempt == 2
    # Default (fresh user-initiated subscription) still resets.
    h.mark_subscribed()
    assert h.retry_attempt == 0


def test_d27_4_backoff_progresses_across_consecutive_failures(monkeypatch,
                                                             qapp):
    """Fix-B (wiring): two consecutive RT failures must schedule increasing
    delays (5s then 10s) — the retry must not restart the backoff at 5s."""
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _complete_priming(win)
    win._ibkr_connected = True  # failure struck a live connection

    win._on_error(win._rt_req_id, 162, "pacing violation")
    delay_1_ms = win._rt_retry_timer.interval()

    # Fire the scheduled retry directly, then fail the new subscription too.
    win._rt_retry_timer.stop()
    win._retry_rt_subscribe()
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    win._on_error(win._rt_req_id, 162, "pacing violation")
    delay_2_ms = win._rt_retry_timer.interval()

    assert delay_1_ms == 5000, f"first retry should be 5s, got {delay_1_ms}ms"
    assert delay_2_ms > delay_1_ms, (
        f"backoff must progress: first {delay_1_ms}ms, second {delay_2_ms}ms"
    )
    win.close()
