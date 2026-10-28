"""D27.3 — reconnect must work: both halves (R53).

(a) ``_do_reconnect`` uses the stored ``connect(host, port, clientId)`` —
    never the nonexistent ``eConnect``; ``_poll`` does not re-arm while a
    reconnect is pending (otherwise backoff is defeated).
(b) every live subscription (chart RT bars, watchlist mkt-data) is
    registered with type tags and replayed on reconnect with rebound
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
    win.md_manager.client = fake
    # ESC-046: pop-out records are process-global — the per-process temp DB is
    # shared across the suite, and a pop-out's deferred geometry save can
    # outlive the per-test ``popouts`` wipe. ``_on_connected()`` would then
    # restore such a record, and the restored pop-out's session subscribes
    # through this same fake, inflating the per-session RT and market-data
    # counts below. This suite proves the *chart* session's replay/rebinding,
    # so neutralise pop-out restore here: every subscription the fake records
    # is then the chart session's own.
    win._restore_popouts = lambda: None
    # Historical requests never reach the fake: stub at the manager.
    _req_ids = iter(range(9001, 9999))
    win.md_manager.req_historical_data = lambda **k: next(_req_ids)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win, fake


def _seed_watchlist_db():
    from data import db as db_mod
    db_mod.db.set_watchlist(["WATCH"])
    return db_mod.db


def test_d27_3_drop_reconnect_reissues_with_rebound_reqids(monkeypatch, qapp):
    """Full drop/reconnect: RT + watchlist re-issued, reqIds rebound, bars flow
    on the new RT reqId, stale ids ignored — no manual reload."""
    from ibkr.contracts import get_contract_for_symbol

    win, fake = _make_window(monkeypatch, qapp)
    db = _seed_watchlist_db()
    try:
        win._now_ts = lambda: 1_760_000_000

        # Establish live subscriptions: watchlist (via connect->restore) and
        # chart RT (via load_chart). D41: the DOM depth feed is gone.
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

        # Pre-drop sanity: bars flow on the live RT reqId.
        win._on_realtime_bar(rt_id_1, 1_760_000_000, 10, 11, 9, 10.5,
                             100, 10.5, 5)
        assert win._last_chart_price == 10.5

        # ---- simulated TWS drop + reconnect ----
        win._on_disconnected()
        win._on_connected()

        # Every live subscription re-issued with a NEW reqId...
        assert len(fake.rt_bars) == 2 and fake.rt_bars[1] != rt_id_1
        # The only surviving market-data line is the watchlist row: the
        # session's S0 generic-tick line went with its last consumer (the D38
        # dividend markers), so nothing else is issued or re-issued.
        _surviving_mkt_lines = len(win.watchlist_panel._req_to_row)
        assert _surviving_mkt_lines == 1
        assert len(fake.mkt_data) == 2 * _surviving_mkt_lines
        first_row_req, rebound_req = fake.mkt_data
        assert rebound_req != first_row_req, "the market-data line reused its reqId"
        rt_id_2 = fake.rt_bars[1]

        # ...and rebound to the live routing state.
        assert win._rt_req_id == rt_id_2, "stale RT reqId not rebound"
        assert list(win.watchlist_panel._req_to_row)[0] == rebound_req
        assert len(win.watchlist_panel._req_to_row) == 1

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


# ---------------------------------------------------------------------------
# Q-54 (b): reconnect failures are visible (exception + retry delay) with
# backoff flood protection; (c): logical-map extend failures log once.
# ---------------------------------------------------------------------------


def test_Q54_do_reconnect_logs_exception_and_delay(quiet_client, monkeypatch,
                                                  caplog):
    """A failed connect attempt warns with the exception and retry delay,
    and the retry loop keeps going (a backoff timer stays pending)."""
    import logging

    client = quiet_client
    client._conn_host = "127.0.0.1"
    client._conn_port = 7496
    client._conn_client_id = 7

    def _boom(self, host, port, clientId):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(EClient, "connect", _boom)
    with caplog.at_level(logging.WARNING, logger="ibkr.client"):
        client._do_reconnect()

    warns = [r for r in caplog.records
             if r.name == "ibkr.client" and r.levelname == "WARNING"]
    assert warns, "reconnect failure logged nothing at warning"
    assert "RuntimeError" in warns[0].message
    assert "retrying in 1s" in warns[0].message  # 2**0, uncapped
    assert client._reconnect_timer is not None, "retry loop stopped"


def test_Q54_do_reconnect_backoff_flood_protection(quiet_client, monkeypatch,
                                                  caplog):
    """Repeats at the capped backoff delay warn once, then drop to debug —
    the retry loop itself never stops."""
    import logging

    from ibkr import client as client_mod

    client = quiet_client
    client._conn_host = "127.0.0.1"
    client._conn_port = 7496
    client._conn_client_id = 7
    # Pin the backoff at the cap: delay stays 16s across attempts.
    client._reconnect_attempt = 6
    assert min(client._backoff_base ** 6, client._max_backoff) == 16

    def _boom(self, host, port, clientId):
        raise RuntimeError("still down")

    monkeypatch.setattr(EClient, "connect", _boom)
    with caplog.at_level(logging.DEBUG, logger="ibkr.client"):
        client._do_reconnect()  # first at cap -> warns
        client._do_reconnect()  # repeat at same delay -> debug
        client._do_reconnect()  # repeat at same delay -> debug

    warns = [r for r in caplog.records
             if r.name == "ibkr.client" and r.levelname == "WARNING"]
    debugs = [r for r in caplog.records
              if r.name == "ibkr.client" and r.levelname == "DEBUG"]
    assert len(warns) == 1, [r.message for r in warns]
    assert len(debugs) == 2, [r.message for r in debugs]
    assert client._reconnect_timer is not None, "retry loop stopped"

    # A successful handshake clears the flood-protection memory so the
    # next outage warns again.
    client.nextValidId(1)
    assert client._last_reconnect_log_delay is None


def test_Q54_extend_failure_logged_once_not_per_bar(monkeypatch, qapp, caplog):
    """A logical-map extend failure keeps the rebuild fallback but warns
    once per series (timeframe + exception type); repeats drop to debug."""
    import logging
    from datetime import datetime, timezone

    from data.bar_aggregator import TIMEFRAME_SECONDS
    from data.models import Bar
    from services.time_collapse_service import TimeCollapseMap
    from ui import lwc_view as LV

    period = TIMEFRAME_SECONDS["5 mins"]
    # Monday 2026-09-28 RTH open (EDT) — plain contiguous 5-min bars.
    base = int(datetime(2026, 9, 28, 13, 30,
                        tzinfo=timezone.utc).timestamp())

    def _bar(ts):
        return Bar(symbol="Q54", timeframe="5 mins", ts=ts, open=100.0,
                   high=101.0, low=99.0, close=100.5, volume=1000.0)

    view = LV.LwcChartView()
    view.set_timeframe("5 mins")
    view.bridge.set_ready(True)
    view.set_series("candles", [_bar(base + i * period) for i in range(4)])
    assert view._cmap is not None

    def _boom(self, ts):
        raise ValueError("bad map state")

    monkeypatch.setattr(TimeCollapseMap, "extend", _boom)
    last = view._bars[-1].ts
    with caplog.at_level(logging.DEBUG, logger="ui.lwc_view"):
        view.update_live_bar(_bar(last + period))
        view.update_live_bar(_bar(last + 2 * period))

    warns = [r for r in caplog.records
             if r.name == "ui.lwc_view" and r.levelname == "WARNING"]
    debugs = [r for r in caplog.records
              if r.name == "ui.lwc_view" and r.levelname == "DEBUG"]
    assert len(warns) == 1, [r.message for r in caplog.records]
    assert "5 mins" in warns[0].message
    assert "ValueError" in warns[0].message
    assert len(debugs) == 1, [r.message for r in caplog.records]
    # The fallback still rebuilt: both new bars are plotted.
    assert len(view.plotted_bars) == 6
