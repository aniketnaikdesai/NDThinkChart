"""D87/D93 — the client's own connection lifecycle (AC-D87.1, D93).

D87: a close that arrives before the handshake is a transient failure, not
TWS-gone — it still schedules a retry through the existing backoff, and the
classification stays inside the ``was_connected`` branch (so no ``TWS_GONE``,
no pause UI, no gap accounting).

D93: ``close()`` is a deliberate teardown — it leaves no connection state
behind and announces no outage; ``connect()`` disarms a pending backoff
timer before it starts a new attempt.

No socket and no TWS: ``EClient.connect`` is replaced with a recorder and
``threading.Timer`` with a recorder that never spawns a thread.
"""

from __future__ import annotations

import threading

import pytest
from ibapi.client import EClient

from ibkr.client import ConnectionState, DisconnectClass, IBApiClient


class _RecordingTimer:
    """``threading.Timer`` double: records schedule/cancel, never runs."""

    instances: list["_RecordingTimer"] = []
    events: list[tuple] = []

    def __init__(self, interval, function, args=None, kwargs=None):
        self.interval = interval
        self.function = function
        self.args = args if args is not None else ()
        self.kwargs = kwargs if kwargs is not None else {}
        self.daemon = False
        self.started = False
        self.cancelled = False
        _RecordingTimer.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True
        _RecordingTimer.events.append(("cancel", self))

    @property
    def pending(self) -> bool:
        """Armed and not disarmed — the timer that would actually fire."""
        return self.started and not self.cancelled


@pytest.fixture
def harness(monkeypatch):
    """A client on a fake transport plus the connect-call and timer records."""
    calls: list[tuple] = []
    _RecordingTimer.instances = []
    _RecordingTimer.events = []

    def fake_connect(self, host, port, clientId):
        calls.append(("connect", host, port, clientId))
        _RecordingTimer.events.append(("connect", host, port, clientId))

    monkeypatch.setattr(threading, "Timer", _RecordingTimer)
    monkeypatch.setattr(EClient, "connect", fake_connect)
    client = IBApiClient()
    return client, calls, _RecordingTimer.instances


def _pending(timers) -> list:
    return [timer for timer in timers if timer.pending]


# ---------------------------------------------------------------------------
# P28-T1-01 — AC-D87.1: a pre-handshake close still retries
# ---------------------------------------------------------------------------


def test_p28_t1_01_pre_handshake_close_schedules_first_backoff(harness):
    client, calls, timers = harness
    client.connect("127.0.0.1", 7496, 1)
    assert client.connection_state == ConnectionState.CONNECTING
    assert client._connected is False
    assert client._reconnect_timer is None

    client.connectionClosed()

    timer = client._reconnect_timer
    assert timer is not None, "a pre-handshake close must still schedule a retry"
    assert timer.pending, "the scheduled retry must be armed, not cancelled"
    assert client.connection_state == ConnectionState.DISCONNECTED
    assert client._last_disconnect_class is None, (
        "a pre-handshake close is transient — it must not be recorded as TWS_GONE"
    )
    # First backoff step: base ** 0 (the exponent starts at 0).
    first_step = min(client._backoff_base ** 0, client._max_backoff)
    assert timer.interval == first_step == 1
    assert client._poll_timer is None, "polling must not survive the close"
    # Nothing stopped with nothing pending: exactly one armed timer remains.
    assert _pending(timers) == [timer]


# ---------------------------------------------------------------------------
# P28-T1-02 — AC-D87.1: no duplicate schedule when _poll already armed one
# ---------------------------------------------------------------------------


def test_p28_t1_02_pre_handshake_close_does_not_duplicate_poll_backoff(harness):
    client, calls, timers = harness
    client.connect("127.0.0.1", 7496, 2)

    # Arm a backoff exactly as _poll does on a socket-down, pre-handshake poll.
    client._poll()
    first = client._reconnect_timer
    assert first is not None and first.pending
    assert client.connection_state == ConnectionState.RECONNECTING

    client.connectionClosed()

    assert first.cancelled and not first.pending, (
        "_schedule_reconnect must cancel the timer _poll armed"
    )
    assert client._reconnect_timer is not None
    assert client._reconnect_timer is not first
    assert client._reconnect_timer.pending
    # Exactly one timer exists after the call — no duplicate schedule.
    assert _pending(timers) == [client._reconnect_timer]
    assert client._last_disconnect_class is None


# ---------------------------------------------------------------------------
# P28-T1-03 — AC-P28-01-1: the handshake path keeps D40's classification
# ---------------------------------------------------------------------------


def test_p28_t1_03_post_handshake_close_keeps_tws_gone_and_reconnect(harness):
    client, calls, timers = harness
    client.connect("127.0.0.1", 7496, 3)
    client.nextValidId(1001)
    assert client.connected is True

    client.connectionClosed()

    assert client._last_disconnect_class == DisconnectClass.TWS_GONE
    assert client.last_disconnect_class == DisconnectClass.TWS_GONE
    timer = client._reconnect_timer
    assert timer is not None and timer.pending

    calls.clear()
    client._do_reconnect()

    assert calls == [("connect", "127.0.0.1", 7496, 3)], (
        "_do_reconnect must issue exactly one super().connect"
    )
    assert timer.cancelled is False, (
        "_do_reconnect must never cancel its own backoff timer"
    )


# ---------------------------------------------------------------------------
# P28-T1-04 — AC-D93.1: close() leaves nothing stale
# ---------------------------------------------------------------------------


def test_p28_t1_04_close_leaves_no_stale_bookkeeping(harness):
    client, calls, timers = harness
    client.connect("127.0.0.1", 7496, 4)
    client.nextValidId(1002)
    client.connectionClosed()
    timer = client._reconnect_timer
    assert timer is not None and timer.pending
    assert client._last_disconnect_class == DisconnectClass.TWS_GONE
    assert client._reconnect_attempt > 0
    client._last_reconnect_log_delay = 8  # Q-54 backoff flood memory

    client.close()

    assert client.connection_state == ConnectionState.DISCONNECTED
    assert client.connected is False
    assert client._reconnect_timer is None
    assert timer.cancelled, "close() must cancel a pending reconnect"
    assert client._last_disconnect_class is None
    assert client._reconnect_attempt == 0
    assert client._last_reconnect_log_delay is None
    assert _pending(timers) == [], "close() must leave no armed timer"


# ---------------------------------------------------------------------------
# P28-T1-05 — AC-D93.2: connect() disarms a pending reconnect first
# ---------------------------------------------------------------------------


def test_p28_t1_05_connect_disarms_pending_reconnect_before_connecting(harness):
    client, calls, timers = harness
    client.connect("127.0.0.1", 7496, 5)
    client.connectionClosed()  # pre-handshake: arms a backoff timer
    pending = client._reconnect_timer
    assert pending is not None and pending.pending

    calls.clear()
    _RecordingTimer.events.clear()
    client.connect("127.0.0.1", 7496, 6)

    assert pending.cancelled, "connect() must cancel the pending reconnect"
    assert client._reconnect_timer is None
    assert calls == [("connect", "127.0.0.1", 7496, 6)], (
        "exactly one super().connect per connect()"
    )
    cancel_at = _RecordingTimer.events.index(("cancel", pending))
    connect_at = _RecordingTimer.events.index(("connect", "127.0.0.1", 7496, 6))
    assert cancel_at < connect_at, "the timer must be disarmed before the attempt"


# ---------------------------------------------------------------------------
# P28-T1-06 — AC-D93.1: a deliberate close announces no outage
# ---------------------------------------------------------------------------


def test_p28_t1_06_close_emits_no_disconnected_signal(harness):
    client, calls, timers = harness
    out_of_connection = []
    connected = []
    client.bridge.disconnected.connect(lambda: out_of_connection.append(1))
    client.bridge.connected.connect(lambda: connected.append(1))

    client.connect("127.0.0.1", 7496, 7)
    client.nextValidId(1003)
    assert connected == [1]

    client.close()

    assert out_of_connection == [], (
        "a deliberate close must not emit disconnected (the outage path must "
        "not run during teardown)"
    )
    assert client.connection_state == ConnectionState.DISCONNECTED
