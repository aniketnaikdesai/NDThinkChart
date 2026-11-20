"""P28-03 / D89 + D90 — a stream owns its health and budget.

One reset on a replayed subscription (D89), a retry schedule that is monotonic
and finite (D90), and a terminal state distinct from FAILED that only a reload
or a reconnect clears.

Harness: a real offscreen ``MainWindow`` (the shipped suites' idiom), a fake
TWS client that records realtime subscribes/cancels, and a recording
replacement for ``_rt_retry_timer`` — the timer's deadline is observed by
recording ``start()`` calls and its callback is fired by calling
``_retry_rt_subscribe`` directly (no wall-clock waits).
"""

from __future__ import annotations

from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient
from ibkr.stream_health import MAX_RETRY_ATTEMPTS, StreamHealth, StreamState


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------


class _FakeTws:
    """Records what actually reached the wire."""

    def __init__(self) -> None:
        self.rt_subscribes: list[int] = []
        self.rt_cancels: list[int] = []

    def reqRealTimeBars(self, reqId, *a, **k):
        self.rt_subscribes.append(int(reqId))

    def cancelRealTimeBars(self, reqId):
        self.rt_cancels.append(int(reqId))


class _RecordingTimer:
    """A single-shot timer double: records every start, never runs."""

    def __init__(self) -> None:
        self.starts: list[int] = []
        self.active = False

    def start(self, ms: int) -> None:
        self.starts.append(int(ms))
        self.active = True

    def stop(self) -> None:
        self.active = False

    def isActive(self) -> bool:  # noqa: N802 - Qt's spelling
        return self.active

    def interval(self) -> int:
        return self.starts[-1] if self.starts else 0


class _StatusSpy:
    """Forwards to the real status bar and records every line."""

    def __init__(self, inner) -> None:
        self.messages: list[tuple[str, int]] = []
        self._inner = inner

    def showMessage(self, message: str, timeout: int = 0) -> None:  # noqa: N802
        self.messages.append((message, int(timeout)))
        self._inner.showMessage(message, timeout)

    def __getattr__(self, name):
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(
        pacing_mod.pacing_manager, "throttle", lambda *, stamp=True: None
    )

    from ui.main_window import MainWindow

    win = MainWindow()
    # P28 readiness: `_transport_ready()` reads exactly these two signals and
    # in production they agree (both set by nextValidId).
    win._ibkr_connected = True
    win.ib_client._connected = True
    win.rt_manager.client = _FakeTws()
    _req_ids = iter(range(9001, 9999))
    win.md_manager.req_historical_data = lambda **k: next(_req_ids)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.objectName() in ("Option Spreads",):
            dock.hide()
    qapp.processEvents()
    win.status_bar = _StatusSpy(win.status_bar)
    win._rt_retry_timer = _RecordingTimer()
    return win


def _load(win) -> None:
    win._now_ts = lambda: 1_760_000_000
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()
    assert win._prime_req_id is not None, "expected a priming request"
    win._on_historical_data_end(win._prime_req_id)
    assert win._rt_req_id is not None


def _fail(win, code: int = 162, message: str = "pacing violation") -> None:
    """An RT error for the current live line, through the real ingress."""
    win._on_error(win._rt_req_id, code, message)


def _fire(win) -> None:
    """Fire the scheduled retry: the timer is one-shot, so stop then run."""
    win._rt_retry_timer.stop()
    win._retry_rt_subscribe()


def _exhaust(win) -> None:
    """Drive the stream through every retry until it stops."""
    for _ in range(MAX_RETRY_ATTEMPTS):
        _fail(win)
        _fire(win)
    _fail(win)
    assert win._stream_health.state == StreamState.EXHAUSTED


def _leave_failed(win, attempt: int) -> None:
    """Drive the stream to FAILED with exactly ``attempt`` retries counted."""
    for _ in range(attempt - 1):
        _fail(win)
        _fire(win)
    _fail(win)
    assert win._stream_health.state == StreamState.FAILED
    assert win._stream_health.retry_attempt == attempt


def _wire_counts(win) -> tuple[int, int, int]:
    """(subscribes, cancels, timer starts) — what a no-op must not move."""
    client = win.rt_manager.client
    return (
        len(client.rt_subscribes),
        len(client.rt_cancels),
        len(win._rt_retry_timer.starts),
    )


def _reconnect(win) -> None:
    """The real `_on_connected` with its unrelated collaborators silenced.

    The assertions are about the retry timer and the replay; watchlist,
    pop-out restore and alarm reconcile are separate owners.
    """
    win._restore_watchlist = lambda: None
    win._restore_popouts = lambda: None
    win.alarm_monitor.reconcile = lambda: None
    win._on_connected()


# ---------------------------------------------------------------------------
# P28-T6-01 / AC-D90.1 — an error storm cannot move the deadline
# ---------------------------------------------------------------------------


def test_P28_T6_01_error_storm_keeps_one_deadline_and_one_attempt(
        monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    timer = win._rt_retry_timer
    timer.starts.clear()
    subscribes = len(win.rt_manager.client.rt_subscribes)

    # Five errors at t=0..4 s with the first delay 5 s.
    for _ in range(5):
        _fail(win)

    assert timer.starts == [5000]        # exactly one start, first delay
    assert timer.interval() == 5000      # unchanged by the later errors
    assert win._stream_health.retry_attempt == 1
    h = win._stream_health
    assert h.state == StreamState.FAILED

    _fire(win)
    assert len(win.rt_manager.client.rt_subscribes) == subscribes + 1
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-02 / AC-D90.2 — the budget is finite and the terminal state distinct
# ---------------------------------------------------------------------------


def test_P28_T6_02_budget_spent_ends_in_a_distinct_terminal_state(
        monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)

    _exhaust(win)
    h = win._stream_health

    assert h.state == StreamState.EXHAUSTED
    assert h.state != StreamState.FAILED
    assert h.retry_attempt == MAX_RETRY_ATTEMPTS
    assert h.retry_budget_spent
    assert h.describe() == "stopped"

    stopped = [m for m in win.status_bar.messages if "stream stopped" in m[0]]
    assert len(stopped) == 1, "the terminal state is surfaced exactly once"
    assert stopped[0] == (
        "TEST — realtime stream stopped after 6 retries; reload the chart "
        "or wait for a reconnect.",
        15000,
    )
    assert not win._rt_retry_timer.isActive()
    assert win.stream_badge.text() == "● Stream stopped"

    # A later clock advance — and even a late echo for the dead line — issues
    # no subscribe, arms nothing and repeats no line.
    counts = _wire_counts(win)
    _fire(win)
    _fail(win)
    assert _wire_counts(win) == counts
    stopped = [m for m in win.status_bar.messages if "stream stopped" in m[0]]
    assert len(stopped) == 1
    assert win._stream_health.state == StreamState.EXHAUSTED
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-10 / AC-P28-03-4 — ESC-135: a post-drop storm cannot exhaust
# ---------------------------------------------------------------------------


def test_P28_T6_10_disconnected_error_storm_never_reaches_terminal(
        monkeypatch, qapp):
    """The terminal state is unreachable while the transport is not ready."""
    from ui.main_window import _RT_RECHECK_MS

    win = _make_window(monkeypatch, qapp)
    _load(win)
    # One attempt short of the cap, reached through the ready path.
    _leave_failed(win, MAX_RETRY_ATTEMPTS - 1)
    attempt_before = win._stream_health.retry_attempt

    # The drop: the window stops the timer; the RT reqId stays routable, so
    # late errors still reach the handler (ESC-135's ingress).
    win._on_disconnected()
    assert not win._ibkr_connected
    assert win._stream_health.state == StreamState.FAILED
    wired = _wire_counts(win)
    lines_before = len(win.status_bar.messages)
    starts_before = len(win._rt_retry_timer.starts)

    # Six late errors interleaved with the retry callback — well past the
    # budget the connected path would have spent.
    for _ in range(MAX_RETRY_ATTEMPTS):
        _fail(win)
        _fire(win)

    h = win._stream_health
    assert h.retry_attempt == attempt_before, "a disconnected re-arm spends no attempt"
    assert h.state == StreamState.FAILED
    assert h.state != StreamState.EXHAUSTED
    assert not h.retry_budget_spent

    # No subscribe, no cancel: nothing reached the wire.
    after = _wire_counts(win)
    assert after[0] == wired[0]
    assert after[1] == wired[1]
    # Every transport-gated re-arm is the fixed readiness re-check.
    assert win._rt_retry_timer.starts[starts_before:] == (
        [_RT_RECHECK_MS] * MAX_RETRY_ATTEMPTS
    )

    # No terminal line and no "retrying" line for the late errors.
    late = [text for text, _ in win.status_bar.messages[lines_before:]]
    assert not [t for t in late if "stream stopped" in t]
    assert not [t for t in late if "retrying" in t]
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-03 / AC-D90.3 — the reload recovers a terminal stream, once
# ---------------------------------------------------------------------------


def test_P28_T6_03_terminal_stream_recovers_on_reload(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    session = win._primary_session
    _exhaust(win)
    old_id = win._rt_req_id
    subscribes = len(win.rt_manager.client.rt_subscribes)

    session.prepare_load("5 mins")
    win._attach_live_feed("TEST", None)

    assert len(win.rt_manager.client.rt_subscribes) == subscribes + 1
    assert win._rt_req_id is not None and win._rt_req_id != old_id
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    assert win._stream_health.retry_attempt == 0
    assert win.stream_badge.text() == "○ Stream awaiting first bar"
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-04 / AC-D90.3 — the reconnect replay recovers it the same way
# ---------------------------------------------------------------------------


def test_P28_T6_04_terminal_stream_recovers_on_reconnect(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _exhaust(win)
    old_id = win._rt_req_id
    subscribes = len(win.rt_manager.client.rt_subscribes)

    _reconnect(win)

    assert len(win.rt_manager.client.rt_subscribes) == subscribes + 1
    assert win._rt_req_id is not None and win._rt_req_id != old_id
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    assert win._stream_health.retry_attempt == 0
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-05 / AC-P28-03-1 — the recovery is terminal-only
# ---------------------------------------------------------------------------


def test_P28_T6_05_failed_nonterminal_stream_is_reused_not_reset(
        monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    session = win._primary_session
    _leave_failed(win, 3)
    req_id = win._rt_req_id
    holders = session._rt_holders
    subscribes = len(win.rt_manager.client.rt_subscribes)

    session.prepare_load("5 mins")
    win._attach_live_feed("TEST", None)

    assert len(win.rt_manager.client.rt_subscribes) == subscribes
    assert win._rt_req_id == req_id
    assert win._stream_health.retry_attempt == 3   # nothing reset
    assert win._stream_health.state == StreamState.FAILED
    assert session._rt_holders == holders + 1      # the ordinary bump
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-06 / AC-D89.1 — a replayed subscription is a fresh subscription
# ---------------------------------------------------------------------------


def test_P28_T6_06_replay_resets_health_and_updates_the_badge(
        monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)
    _leave_failed(win, 3)
    assert "failed" in win.stream_badge.text()

    win._replay_subscriptions()

    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    assert win._stream_health.retry_attempt == 0
    # The health signal fired: the badge followed the reset.
    assert win.stream_badge.text() == "○ Stream awaiting first bar"
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-07 / AC-D89.2 — a pre-drop deadline cannot touch the replayed line
# ---------------------------------------------------------------------------


def test_P28_T6_07_stale_pre_reconnect_callback_is_a_noop(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)

    # Armed directly, with no preceding drop.
    win._schedule_rt_retry()
    assert win._rt_retry_timer.isActive()

    _reconnect(win)

    assert not win._rt_retry_timer.isActive()
    counts = _wire_counts(win)
    win._retry_rt_subscribe()          # fire the stale callback
    assert _wire_counts(win) == counts  # no unsubscribe, no subscribe, no re-arm
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-08 / AC-P28-03-3 — Journey 77: same tick, superseded, reconnect
# ---------------------------------------------------------------------------


def test_P28_T6_08_retry_proceeds_once_and_superseded_callbacks_are_silent(
        monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _load(win)

    # A reconnect while FAILED with attempts spent resets the budget.
    _leave_failed(win, 3)
    subscribes = len(win.rt_manager.client.rt_subscribes)
    _reconnect(win)
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    assert win._stream_health.retry_attempt == 0
    assert len(win.rt_manager.client.rt_subscribes) == subscribes + 1

    # An error in the same tick as a scheduled retry: the deadline does not
    # move and the retry proceeds exactly once.
    _fail(win)
    starts = list(win._rt_retry_timer.starts)
    _fail(win)
    assert win._rt_retry_timer.starts == starts
    assert win._stream_health.retry_attempt == 1
    subscribes = len(win.rt_manager.client.rt_subscribes)
    _fire(win)
    assert len(win.rt_manager.client.rt_subscribes) == subscribes + 1

    # A first bar moves the stream off FAILED: the pending callback is silent.
    _fail(win)                          # arms a retry for this line
    win._on_realtime_bar(win._rt_req_id, 1_760_000_000, 10, 11, 9, 10.5,
                         100, 10.5, 5)
    assert win._stream_health.state == StreamState.LIVE
    counts = _wire_counts(win)
    win._retry_rt_subscribe()
    assert _wire_counts(win) == counts

    # A reload of another symbol supersedes the callback just the same.
    _fail(win)
    win.symbol_input.setText("OTHER")
    win.load_chart()
    win._on_historical_data_end(win._prime_req_id)
    assert win._stream_health.state == StreamState.AWAITING_FIRST_BAR
    counts = _wire_counts(win)
    win._retry_rt_subscribe()
    assert _wire_counts(win) == counts

    # ... and a callback left over when the stream stops is silent too.
    _exhaust(win)
    counts = _wire_counts(win)
    win._retry_rt_subscribe()
    assert _wire_counts(win) == counts
    win.close()


# ---------------------------------------------------------------------------
# P28-T6-09 / AC-P28-03-2 — the backoff contract is unchanged
# ---------------------------------------------------------------------------


def test_P28_T6_09_backoff_progression_and_terminal_value_object():
    # The six shipped delays, byte-for-byte (tests/test_d27_stream_health.py
    # and tests/test_p7_w4_streaming.py pin the same arithmetic unchanged).
    h = StreamHealth()
    assert [h.next_retry_delay_s() for _ in range(6)] == [
        5.0, 10.0, 20.0, 40.0, 60.0, 60.0,
    ]

    # The terminal state is additive and distinct, and keeps the cause.
    h.mark_failed(162, "pacing violation")
    h.mark_exhausted()
    assert h.state == StreamState.EXHAUSTED
    assert h.state != StreamState.FAILED
    assert h.fail_code == 162
    assert h.retry_budget_spent
    assert h.describe() == "stopped"

    # Only a reset clears it.
    h.mark_subscribed(reset_backoff=True)
    assert h.state == StreamState.AWAITING_FIRST_BAR
    assert h.retry_attempt == 0
    assert not h.retry_budget_spent
