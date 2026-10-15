"""D25 — headless alarm monitor (AC-D25.1–D25.5).

Test names follow the requirement numbering (not test order): the AC in
each name is the criterion the test actually verifies. See DG57 —
"the test docstrings assign the AC numbers in test order, which maps
differently to the criteria".

AC→test mapping:
- AC-D25.1 (headless firing / one RT sub / teardown): the *_d25_1_* tests.
- AC-D25.2 (no historical requests + 1m-cache seed): *_d25_2_*.
- AC-D25.3 (no phantom trigger): *_d25_3_*.
- AC-D25.4 (re-arm + alarm added while disconnected): *_d25_4_*.
- AC-D25.5 (regression) is the batch-regression convention (cf.
  AC-D39.5 / AC-D40.5) — the whole offscreen suite is its check; there
  is no dedicated function (a self-referential one would be a tautology).
"""

from __future__ import annotations

import threading

import pytest

from data.alarm_store import AlarmStore
from data.bar_cache import BarCache
from data.models import Alarm, Bar
from ibkr.client import ConnectionState, DisconnectClass

SYM_MON = "MONA"
SYM_NOMON = "MONB"
TF_1M = "1m"
BASE_TS = 1_760_000_000


class _NoopTimer:
    """threading.Timer double that never spawns a thread (D40 pattern)."""

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


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.execute("DELETE FROM bars WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(threading, "Timer", _NoopTimer)
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([5001, 5002, 5003, 5004, 5005])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    win.md_manager.req_historical_data = lambda *a, **k: 5999
    win.show()
    qapp.processEvents()
    return win


def _add_alarm(symbol: str, price: float) -> int:
    a = Alarm(
        id=None, symbol=symbol, price=price, direction="cross_above",
        active=True, sound=False,
    )
    return AlarmStore.add(a)


def _go_live(win) -> None:
    """Simulate a live connection (socket up, handshake done)."""
    win.ib_client._connected = True
    win.ib_client._connection_state = ConnectionState.CONNECTED


# ---------------------------------------------------------------------------
# AC-D25.1 — headless firing, one RT sub, teardown
# ---------------------------------------------------------------------------


def test_d25_1_active_alarms_select_monitored_set():
    """AC-D25.1 (Given): the monitor's input — symbols with active,
    untriggered alarms — is exactly what AlarmStore reports."""
    _clear(SYM_MON)
    _clear(SYM_NOMON)
    try:
        _add_alarm(SYM_MON, 100.0)
        # Triggered alarm doesn't count.
        t = Alarm(
            id=None, symbol=SYM_NOMON, price=200.0, direction="cross_above",
            active=True, triggered=True,
        )
        AlarmStore.add(t)

        symbols = AlarmStore.symbols_with_active_alarms()
        assert SYM_MON in symbols
        assert SYM_NOMON not in symbols
    finally:
        _clear(SYM_MON)
        _clear(SYM_NOMON)


def test_d25_1_headless_session_monitors(monkeypatch, qapp):
    """AC-D25.1 (Then): exactly one RT subscription exists for X; the
    headless session has no views and a 1m aggregator."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        _add_alarm(SYM_MON, 100.0)

        win.alarm_monitor.reconcile()
        qapp.processEvents()

        session = win._sessions.get(SYM_MON)
        assert session is not None
        assert session.monitored is True
        assert session.views == []
        # One RT subscription, 1m aggregator ready.
        assert session.rt_req_id == 5001
        assert "1m" in session._aggregators
        # Zero historical requests from the headless session — asserted
        # properly in test_d25_2_no_history_and_cache_seed (AC-D25.2).
    finally:
        _clear(SYM_MON)
        win.close()


def test_d25_1_headless_firing_on_push(monkeypatch, qapp):
    """AC-D25.1 (When): driving X's price through the level fires the
    toast exactly once and marks the store triggered."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        _add_alarm(SYM_MON, 100.5)

        # Seed the 1m cache so prev_price is known.
        bars = [
            Bar(SYM_MON, TF_1M, BASE_TS - 60, 99.0, 99.5, 98.5, 100.0, 1000.0),
        ]
        BarCache.save_bars(bars)

        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_MON]
        assert session.last_chart_price == pytest.approx(100.0)

        fired = []
        win.toast.show_message = lambda msg: fired.append(msg)

        # Tick across the level (5-sec pushes aggregate to 1m).
        req_id = session.rt_req_id
        for i, price in enumerate([100.0, 101.0]):
            win._on_realtime_bar(
                req_id, BASE_TS + i * 5, price - 0.1, price + 0.1,
                price - 0.2, price, 100.0, price, 5,
            )
        qapp.processEvents()

        # The alarm fired via the headless session.
        assert session.alarms[0].triggered is True
        assert any(SYM_MON in m for m in fired)
        # Persisted.
        assert AlarmStore.load(SYM_MON)[0].triggered is True
    finally:
        _clear(SYM_MON)
        win.close()


def test_d25_1_reconcile_on_trigger_stops_monitor(monkeypatch, qapp):
    """AC-D25.1 (Then): once X's last alarm has triggered, reconcile
    releases the monitor and tears the orphaned session down."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        _add_alarm(SYM_MON, 100.5)
        bars = [
            Bar(SYM_MON, TF_1M, BASE_TS - 60, 99.0, 99.5, 98.5, 100.0, 1000.0),
        ]
        BarCache.save_bars(bars)

        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_MON]
        assert session.monitored is True

        # Fire the alarm.
        req_id = session.rt_req_id
        for i, price in enumerate([100.0, 101.0]):
            win._on_realtime_bar(
                req_id, BASE_TS + i * 5, price - 0.1, price + 0.1,
                price - 0.2, price, 100.0, price, 5,
            )
        qapp.processEvents()

        # The trigger reconciled → no active alarms → monitor released.
        assert SYM_MON not in win._sessions or not win._sessions[
            SYM_MON
        ].monitored
    finally:
        _clear(SYM_MON)
        win.close()


def test_d25_1_delete_alarm_tears_down_headless_session(monkeypatch, qapp):
    """AC-D25.1 (Then, teardown): deleting X's alarm with no view open
    releases the RT subscription and tears the session down."""
    win = _make_window(monkeypatch, qapp)
    cancelled: list[int] = []
    win.rt_manager.unsubscribe = lambda req_id: cancelled.append(req_id)
    try:
        _clear(SYM_MON)
        aid = _add_alarm(SYM_MON, 100.0)

        win.alarm_monitor.reconcile()
        qapp.processEvents()
        session = win._sessions.get(SYM_MON)
        assert session is not None and session.monitored is True
        # Exactly one RT subscription for X.
        assert session.rt_req_id == 5001

        # Delete the alarm with no view open → reconcile stands down.
        AlarmStore.delete(aid)
        win.alarm_monitor.on_alarm_changed()
        qapp.processEvents()

        # Session torn down (sub cancelled).
        assert SYM_MON not in win._sessions
        assert 5001 in cancelled
    finally:
        _clear(SYM_MON)
        win.close()


# ---------------------------------------------------------------------------
# AC-D25.2 — no historical requests + 1m-cache seed
# ---------------------------------------------------------------------------


def test_d25_2_no_history_and_cache_seed(monkeypatch, qapp):
    """AC-D25.2: headless monitoring issues ZERO historical-data requests
    (asserted on the session's request registry) and seeds prev_price
    from the 1m cache."""
    win = _make_window(monkeypatch, qapp)
    hist_calls: list[tuple] = []

    def _rec_hist(*a, **k):
        hist_calls.append((a, k))
        return 5999

    win.md_manager.req_historical_data = _rec_hist
    try:
        _clear(SYM_MON)
        # Present 1m cache → prev_price must seed from it.
        BarCache.save_bars([
            Bar(SYM_MON, TF_1M, BASE_TS - 60, 99.0, 99.5, 98.5, 100.0, 1000.0),
        ])
        _add_alarm(SYM_MON, 200.0)  # far from the seed; no evaluation matter

        win.alarm_monitor.reconcile()
        qapp.processEvents()
        session = win._sessions[SYM_MON]

        # Request registry: no historical-data request was issued.
        assert hist_calls == [], (
            "headless monitoring must issue zero req_historical_data calls"
        )
        assert session._history_req_ids == set(), (
            "the session's history-request registry must stay empty"
        )
        # Seed came from the 1m cache (not from history/first tick).
        assert session.last_chart_price == pytest.approx(100.0)
        # 1m aggregator + one RT subscription (the cache path's companions).
        assert "1m" in session._aggregators
        assert session.rt_req_id == 5001
    finally:
        _clear(SYM_MON)
        win.close()


# ---------------------------------------------------------------------------
# AC-D25.3 — no phantom trigger
# ---------------------------------------------------------------------------


def test_d25_3_no_cache_no_phantom(monkeypatch, qapp):
    """AC-D25.3: no cache → first tick seeds, no phantom trigger."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        # Alarm BELOW the first tick price (would phantom-fire if evaluated
        # with prev=None).
        _add_alarm(SYM_MON, 90.0)

        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_MON]
        # No cache: prev_price starts None.
        assert session.last_chart_price is None

        fired = []
        win.toast.show_message = lambda msg: fired.append(msg)

        # First tick at 100.0 (above the 90.0 alarm).
        req_id = session.rt_req_id
        win._on_realtime_bar(
            req_id, BASE_TS, 99.9, 100.1, 99.8, 100.0, 100.0, 100.0, 5
        )
        qapp.processEvents()

        # No evaluation on the seeding tick → no trigger.
        assert session.alarms[0].triggered is False
        assert fired == []
        # But the price is now seeded.
        assert session.last_chart_price == pytest.approx(100.0)
    finally:
        _clear(SYM_MON)
        win.close()


# ---------------------------------------------------------------------------
# AC-D25.4 — re-arm + alarm added while disconnected
# ---------------------------------------------------------------------------


def test_d25_4_rearm_reenables_monitoring(monkeypatch, qapp):
    """AC-D25.4: a triggered, re-armed alarm re-enters monitoring on the
    next reconcile."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        aid = _add_alarm(SYM_MON, 90.0)

        # Triggered → not "active" → never monitored.
        AlarmStore.mark_triggered(aid)
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        assert SYM_MON not in win._sessions or not win._sessions[
            SYM_MON
        ].monitored

        # Re-arm → reconcile (alarm CRUD hook) re-enables monitoring.
        AlarmStore.rearm(aid)
        win.alarm_monitor.on_alarm_changed()
        qapp.processEvents()

        session = win._sessions[SYM_MON]
        assert session.monitored is True
        assert session.rt_req_id == 5001
    finally:
        _clear(SYM_MON)
        win.close()


def test_d25_4_alarm_added_while_disconnected(monkeypatch, qapp):
    """AC-D25.4: an alarm added while TWS is gone is staged (monitored,
    no subscribe yet, subscribe pending) and completes on resume."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()
        # TWS-gone → the monitor is paused.
        assert win.ib_client.last_disconnect_class == DisconnectClass.TWS_GONE
        assert win.alarm_monitor.is_paused is True

        # Alarm added while disconnected → reconcile takes the staged path.
        _add_alarm(SYM_MON, 200.0)
        win.alarm_monitor.on_alarm_changed()
        qapp.processEvents()

        session = win._sessions.get(SYM_MON)
        # Intermediate paused state (not just the end state).
        assert session is not None
        assert session.monitored is True
        assert session.rt_req_id is None
        assert session._monitor_subscribe_pending is True
        assert session.monitoring_paused is True

        # Morning login: resume finishes the pending subscribe.
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert session._monitor_subscribe_pending is False
        assert session.monitoring_paused is False
        assert session.rt_req_id is not None
    finally:
        _clear(SYM_MON)
        win.close()
