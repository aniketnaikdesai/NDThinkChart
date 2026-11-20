"""P29-06 self-check: the hermetic IBKR connect guard.

``tests/conftest.py`` installs one session-scoped autouse fixture that
replaces ``ibapi.connection.Connection.connect`` with a function raising
``ConnectionRefusedError`` before a socket exists. Raising at the **socket
layer** (never replacing ``EClient.connect`` with a no-op) is deliberate: it
drives ``EClient.connect``'s own ``except socket.error`` path
(error 502 -> ``disconnect()`` -> ``connectionClosed()`` -> ``reset()`` ->
DISCONNECTED) while ``IBApiClient.connect``'s bookkeeping still runs, which is
the exact environment every green run has had with TWS stopped.

Nothing here is skipped or relaxed: a suite that needs the backend to be DOWN
is the defect this module guards.
"""

from __future__ import annotations

import threading

import pytest

from ibapi.client import EClient
from ibapi.connection import Connection


class _RecordingWrapper:
    """Records the two wrapper callbacks a refused connect produces."""

    def __init__(self) -> None:
        self.errors: list[tuple] = []
        self.closed = 0

    def error(self, *args, **kwargs) -> None:
        self.errors.append(args)

    def connectionClosed(self) -> None:
        self.closed += 1


def test_guard_refuses_before_a_socket_exists() -> None:
    """AC-P29-06-GUARD: the refused-connect state, for a plain test."""
    assert getattr(Connection.connect, "_hermetic_guard", False), (
        "tests/conftest.py must install the socket-layer guard for the session"
    )

    wrapper = _RecordingWrapper()
    client = EClient(wrapper)
    before = threading.active_count()

    client.connect("127.0.0.1", 7496, 1)

    assert threading.active_count() == before, (
        "the refused connect must not create an ibapi reader thread"
    )
    assert len(wrapper.errors) == 1, "exactly one wrapper error, from EClient"
    assert wrapper.errors[0][2] == 502, "EClient's own except socket.error path"
    assert wrapper.closed == 1, "EClient.disconnect() closes the wrapper once"
    assert client.isConnected() is False
    assert client.conn is None, "reset() must drop the connection object"
    assert client.connState == EClient.DISCONNECTED, (
        "the client must end DISCONNECTED, not stuck in CONNECTING"
    )
    assert client.reader is None, "no reader may survive a refused connect"


@pytest.mark.parametrize(
    "site",
    ["eclient", "ibapi_client"],
    ids=["EClient.connect", "IBApiClient.connect"],
)
def test_a_test_own_patch_wins_and_the_guard_returns(site: str) -> None:
    """AC-P29-06-PRECEDENCE: a test's own patch wins, then the guard returns."""
    calls: list[tuple] = []

    if site == "eclient":
        # The recorder pattern shipped in tests/test_d87_d93_client_lifecycle.py.
        wrapper = _RecordingWrapper()
        client = EClient(wrapper)
        target = EClient
    else:
        # The window pattern shipped in tests/test_d98_outage_baseline.py.
        from ibkr.client import IBApiClient

        client = IBApiClient()
        wrapper = _RecordingWrapper()
        target = IBApiClient

    def recorder(self, host, port, clientId):
        calls.append((host, port, clientId))

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(target, "connect", recorder)
        if site == "ibapi_client":
            # IBApiClient is its own wrapper; spy on the callbacks EClient
            # would have driven had the guard been reached.
            mp.setattr(client, "error", wrapper.error)
            mp.setattr(client, "connectionClosed", wrapper.connectionClosed)

        client.connect("127.0.0.1", 7496, 9)

        assert calls == [("127.0.0.1", 7496, 9)], (
            "the test's own patch must be the effective implementation"
        )
        assert wrapper.errors == [], "the guard must not emit error 502"
        assert wrapper.closed == 0, "no connectionClosed() inside the patch"

    assert getattr(Connection.connect, "_hermetic_guard", False), (
        "the guard must still be installed once the test's patch is undone"
    )

    fresh_wrapper = _RecordingWrapper()
    fresh = EClient(fresh_wrapper)
    fresh.connect("127.0.0.1", 7496, 2)

    assert len(fresh_wrapper.errors) == 1
    assert fresh_wrapper.errors[0][2] == 502
    assert fresh_wrapper.closed == 1
    assert fresh.isConnected() is False
    assert fresh.conn is None
    assert fresh.connState == EClient.DISCONNECTED
