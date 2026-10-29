"""Q-35 — IBKR pre-handshake 504 gate: API readiness on nextValidId only.

Ordering regression with a fake EClient socket: socket open + handshake
pending -> ``connected`` is False, no CONNECTED emission,
``req_historical_data`` raises IBKRNotReady and
``EClient.reqHistoricalData`` is NOT called; after ``nextValidId`` ->
``connected`` is True and the request sends.
"""

from __future__ import annotations

import threading

import pytest
from ibapi.client import EClient
from ibapi.contract import Contract

from ibkr.client import ConnectionState, IBApiClient
from ibkr.error_codes import IBKRNotReady
from ibkr.market_data import MarketDataManager, TIMEFRAME_CONFIG


class _NoopTimer:
    """threading.Timer double that never spawns a thread."""

    def __init__(self, *a, **k):
        pass

    def start(self):
        pass

    def cancel(self):
        pass

    @property
    def daemon(self):
        return True

    @daemon.setter
    def daemon(self, value):
        pass


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(threading, "Timer", _NoopTimer)
    monkeypatch.setattr(EClient, "isConnected", lambda self: True)
    return IBApiClient()


@pytest.fixture
def unsent(monkeypatch):
    """Record every wire send; fail loudly if one slips through."""
    sent = []
    monkeypatch.setattr(
        EClient, "reqHistoricalData",
        lambda self, *a, **k: sent.append(("historical", a, k)),
    )
    monkeypatch.setattr(
        EClient, "reqMktData",
        lambda self, *a, **k: sent.append(("mkt", a, k)),
    )
    monkeypatch.setattr(
        EClient, "reqContractDetails",
        lambda self, *a, **k: sent.append(("details", a, k)),
    )
    monkeypatch.setattr(
        EClient, "reqMatchingSymbols",
        lambda self, *a, **k: sent.append(("symbols", a, k)),
    )
    return sent


def test_socket_open_pre_handshake_is_not_ready(client):
    """Socket up + no nextValidId: not connected, no CONNECTED emission."""
    assert client.socket_connected is True
    assert client.connected is False
    assert client.api_ready is False

    emitted = []
    client.bridge.connected.connect(lambda: emitted.append(True))
    client._poll()

    assert client.connected is False
    assert emitted == []
    assert client.connection_state == ConnectionState.CONNECTING


def test_historical_gated_until_next_valid_id(client, unsent):
    """Pre-handshake historical raises IBKRNotReady and sends nothing;
    post-handshake the same request sends."""
    md = MarketDataManager(client)
    contract = Contract()

    with pytest.raises(IBKRNotReady):
        md.req_historical_data(contract=contract)
    assert unsent == []

    client.nextValidId(1)
    assert client.connected is True

    req_id = md.req_historical_data(contract=contract)
    assert isinstance(req_id, int)
    assert len(unsent) == 1
    assert unsent[0][0] == "historical"


def test_all_request_paths_gated_pre_handshake(client, unsent):
    """mkt/contract-details/matching-symbols share the handshake gate."""
    md = MarketDataManager(client)
    contract = Contract()

    with pytest.raises(IBKRNotReady):
        md.req_mkt_data(contract)
    with pytest.raises(IBKRNotReady):
        md.req_contract_details(contract)
    with pytest.raises(IBKRNotReady):
        md.req_matching_symbols("AAPL")
    assert unsent == []


def test_next_valid_id_promotes_to_connected(client):
    """_poll never promotes; nextValidId emits CONNECTED exactly once."""
    emitted = []
    client.bridge.connected.connect(lambda: emitted.append(True))

    client._poll()
    assert emitted == []
    assert client.connection_state == ConnectionState.CONNECTING

    client.nextValidId(42)
    assert client.connected is True
    assert client.connection_state == ConnectionState.CONNECTED
    assert emitted == [True]


def test_close_clears_readiness(client):
    client.nextValidId(7)
    assert client.connected is True
    client.close()
    assert client.connected is False


def test_timeframe_config_untouched():
    """Q-35 must not change TIMEFRAME_CONFIG durations (Q-48: approved widening;
    Q-61: approved P12 30-min addition).

    Pins the owner-approved widened set (P7 widening, approval 2026-10-28,
    owned by the T06 gate in test_p7_w3_wide.py) plus the approved P12 30-min
    row (added-never-widened, so no new approval record — same treatment as
    the P8 1 week/1 month additions): any duration drift fails
    here, and every widened duration must name its approval record — a
    widening without the record fails closed.
    """
    import os

    assert {k: v["duration"] for k, v in TIMEFRAME_CONFIG.items()} == {
        "1 min": "30 D",
        "5 mins": "30 D",
        "15 mins": "30 D",
        "30 mins": "30 D",
        "1 hour": "60 D",
        "4 hours": "60 D",
        "1 day": "1 Y",
        "1 week": "2 Y",
        "1 month": "10 Y",
    }
    for timeframe in ("1 min", "5 mins", "15 mins", "1 hour", "4 hours"):
        slug = timeframe.replace(" ", "")
        path = f"docs/build/approvals/P7-T06-{slug}.md"
        assert os.path.exists(path), (
            f"{timeframe} widened duration without owner approval {path}"
        )
