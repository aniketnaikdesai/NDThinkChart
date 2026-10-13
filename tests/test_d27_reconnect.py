"""D27.3 — reconnect must work: both halves (R53).

(a) ``_do_reconnect`` uses the stored ``connect(host, port, clientId)`` —
    never the nonexistent ``eConnect``; ``_poll`` does not re-arm while a
    reconnect is pending (otherwise backoff is defeated).
(b) every live subscription (chart RT bars, DOM depth, watchlist mkt-data)
    is registered with type tags and replayed on reconnect with rebound
    reqIds.

AC-D27.3: simulated drop/reconnect (mocked client) -> reconnect without
restart, subs re-issued with rebound reqIds, bars flow, no manual reload.
"""

from __future__ import annotations

import threading

import pytest
from PyQt6.QtWidgets import QDockWidget
from ibapi.client import EClient

from ibkr.client import ConnectionState, IBApiClient


# ---------------------------------------------------------------------------
# (a) client half
# ---------------------------------------------------------------------------


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
def quiet_client(monkeypatch):
    monkeypatch.setattr(threading, "Timer", _NoopTimer)
    return IBApiClient()


def test_d27_3_do_reconnect_uses_stored_connect_params(quiet_client, monkeypatch):
    """_do_reconnect must call connect(host, port, clientId), not eConnect."""
    calls: list[tuple] = []
    monkeypatch.setattr(
        EClient, "connect",
        lambda self, host, port, clientId: calls.append((host, port, clientId)),
    )
    client = quiet_client
    assert not hasattr(client, "eConnect"), "eConnect must not exist (ibapi)"

    client.connect("127.0.0.1", 7496, 7)
    assert calls == [("127.0.0.1", 7496, 7)]
    calls.clear()

    client._do_reconnect()
    assert calls == [("127.0.0.1", 7496, 7)], (
        "reconnect must reuse the stored connection params"
    )


def test_d27_3_do_reconnect_without_prior_connect_is_noop(quiet_client,
                                                          monkeypatch):
    """No stored params (never connected) -> no attempt, no crash."""
    calls: list[tuple] = []
    monkeypatch.setattr(
        EClient, "connect",
        lambda self, host, port, clientId: calls.append((host, port, clientId)),
    )
    quiet_client._do_reconnect()
    assert calls == []


def test_d27_3_poll_does_not_rearm_while_reconnect_pending(quiet_client,
                                                           monkeypatch):
    """While RECONNECTING, _poll must not restart the poll timer (backoff)."""
    client = quiet_client
    polls: list = []
    reconnects: list = []
    monkeypatch.setattr(client, "start_polling", lambda *a, **k: polls.append(1))
    monkeypatch.setattr(
        client, "_schedule_reconnect", lambda *a, **k: reconnects.append(1))
    client._connected = False
    client._connection_state = ConnectionState.RECONNECTING

    client._poll()

    assert reconnects, "_poll must keep the backoff attempt scheduled"
    assert not polls, (
        "_poll re-armed while a reconnect is pending (defeats backoff)"
    )


# ---------------------------------------------------------------------------
# (b) subscription replay half
# ---------------------------------------------------------------------------


class _FakeTws:
    """Records subscription calls; hands out nothing (managers use id_manager)."""

    def __init__(self):
        self.rt_bars: list[int] = []
        self.mkt_data: list[int] = []
        self.mkt_depth: list[int] = []

    def reqRealTimeBars(self, reqId, *a, **k):
        self.rt_bars.append(reqId)

    def cancelRealTimeBars(self, reqId):
        pass

    def reqMktData(self, reqId, *a, **k):
        self.mkt_data.append(reqId)

    def cancelMktData(self, reqId):
        pass

    def reqMktDepth(self, reqId, *a, **k):
        self.mkt_depth.append(reqId)

    def cancelMktDepth(self, reqId):
        pass

    def reqHistoricalData(self, *a, **k):
        pass


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    # No pacing sleeps in tests.
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    fake = _FakeTws()
    win.rt_manager.client = fake
    win.depth_manager.client = fake
    win.md_manager.client = fake
    # Historical requests never reach the fake: stub at the manager.
    _req_ids = iter(range(9001, 9999))
    win.md_manager.req_historical_data = lambda **k: next(_req_ids)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Active Trader",):
            dock.hide()
    qapp.processEvents()
    return win, fake


def _seed_watchlist_db():
    from data import db as db_mod
    db_mod.db.set_watchlist(["WATCH"])
    return db_mod.db


def test_d27_3_drop_reconnect_reissues_with_rebound_reqids(monkeypatch, qapp):
    """Full drop/reconnect: RT + DOM + watchlist re-issued, reqIds rebound,
    bars flow on the new RT reqId, stale ids ignored — no manual reload."""
    from ibkr.contracts import get_contract_for_symbol

    win, fake = _make_window(monkeypatch, qapp)
    db = _seed_watchlist_db()
    try:
        win._now_ts = lambda: 1_760_000_000

        # Establish live subscriptions: watchlist (via connect->restore),
        # chart RT (via load_chart), DOM (via _subscribe_dom).
        win._on_connected()
        assert fake.mkt_data, "watchlist restore issued no mkt-data sub"
        md_id_1 = fake.mkt_data[-1]

        win.symbol_input.setText("TEST")
        win.tf_combo.setCurrentText("5 mins")
        win.load_chart()
        # D27.9: the live feed attaches after priming completes.
        win._on_historical_data_end(win._prime_req_id)
        assert fake.rt_bars, "load_chart issued no RT sub"
        rt_id_1 = win._rt_req_id
        assert rt_id_1 == fake.rt_bars[-1]

        win._subscribe_dom()
        assert fake.mkt_depth, "DOM subscribe issued nothing"
        depth_id_1 = win._depth_req_id
        assert depth_id_1 == fake.mkt_depth[-1]

        # Pre-drop sanity: bars flow on the live RT reqId.
        win._on_realtime_bar(rt_id_1, 1_760_000_000, 10, 11, 9, 10.5,
                             100, 10.5, 5)
        assert win._last_chart_price == 10.5

        # ---- simulated TWS drop + reconnect ----
        win._on_disconnected()
        win._on_connected()

        # Every live subscription re-issued with a NEW reqId...
        assert len(fake.rt_bars) == 2 and fake.rt_bars[1] != rt_id_1
        assert len(fake.mkt_depth) == 2 and fake.mkt_depth[1] != depth_id_1
        assert len(fake.mkt_data) == 2 and fake.mkt_data[1] != md_id_1
        rt_id_2, depth_id_2, md_id_2 = (
            fake.rt_bars[1], fake.mkt_depth[1], fake.mkt_data[1])

        # ...and rebound to the live routing state.
        assert win._rt_req_id == rt_id_2, "stale RT reqId not rebound"
        assert win._depth_req_id == depth_id_2, "stale depth reqId not rebound"
        assert list(win.watchlist_panel._req_to_row) == [md_id_2]

        # Bars flow on the rebound id with no manual reload...
        win._on_realtime_bar(rt_id_2, 1_760_000_005, 10, 12, 9, 11.5,
                             100, 11.5, 5)
        assert win._last_chart_price == 11.5
        # ...and the stale pre-drop id is ignored.
        win._on_realtime_bar(rt_id_1, 1_760_000_010, 10, 12, 9, 99.0,
                             100, 99.0, 5)
        assert win._last_chart_price == 11.5
        # No manual chart reload happened.
        assert win._current_symbol == "TEST"
    finally:
        db.set_watchlist([])
