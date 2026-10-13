"""D40 — TWS daily-lifecycle pause/resume (AC-D40.1–D40.5).

Owner context: TWS only (never Gateway); Aniket closes TWS nightly and
logs in manually each morning. On TWS-gone the app must enter a clear
"Monitoring paused — TWS disconnected" state (badge area), pause alarm
evaluation with per-symbol gap accounting, then auto-reconnect,
resubscribe and reconcile on the morning login — no restart, no phantom
alarm triggers across the gap. Transient drops keep the fast D27 path
with no pause UI.
"""

from __future__ import annotations

import threading
import time

import pytest

from data.alarm_store import AlarmStore
from data.models import Alarm, Bar
from ibkr.client import ConnectionState, DisconnectClass, IBApiClient
from services.alarm_monitor import AlarmMonitor

SYM_A = "D40A"
SYM_B = "D40B"
TF_1M = "1m"
BASE_TS = 1_760_000_000
PAUSED_TEXT = "Monitoring paused — TWS disconnected"


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


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.execute("DELETE FROM bars WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    """MainWindow with a stubbed RT subscribe (D25 pattern) and no timers."""
    from ibkr.client import IBApiClient as _C

    monkeypatch.setattr(threading, "Timer", _NoopTimer)
    monkeypatch.setattr(_C, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter(range(7001, 7999))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    win.md_manager.req_historical_data = lambda *a, **k: 7999
    win.show()
    qapp.processEvents()
    return win


def _add_alarm(symbol: str, price: float, direction: str = "cross_above") -> int:
    a = Alarm(
        id=None, symbol=symbol, price=price, direction=direction,
        active=True, sound=False,
    )
    return AlarmStore.add(a)


def _go_live(win) -> None:
    """Simulate a live connection (socket up, handshake done)."""
    win.ib_client._connected = True
    win.ib_client._connection_state = ConnectionState.CONNECTED


# ---------------------------------------------------------------------------
# 40.1 — disconnect classification
# ---------------------------------------------------------------------------


def test_d40_1_connection_closed_classifies_tws_gone(quiet_client):
    """AC-D40.1 (client): a server-side socket close on a live connection
    classifies TWS_GONE — ibapi documents connectionClosed as firing
    "when TWS closes the sockets connection ... or when TWS is shut
    down"."""
    client = quiet_client
    client._connected = True

    client.connectionClosed()

    assert client.last_disconnect_class == DisconnectClass.TWS_GONE
    assert client.connection_state == ConnectionState.DISCONNECTED


def test_d40_1_connection_closed_without_prior_connect_stays_unclassified(
    quiet_client,
):
    """No live session → no TWS_GONE (e.g. TWS simply not up at startup):
    the pause state must not appear."""
    client = quiet_client

    client.connectionClosed()

    assert client.last_disconnect_class is None


def test_d40_1_poll_drop_does_not_classify(quiet_client):
    """A poll-driven drop (no server close) stays unclassified → the fast
    D27 path, never the pause UI (AC-D40.4 classification half)."""
    client = quiet_client
    client._connected = False  # drop noticed without a server close
    client._connection_state = ConnectionState.CONNECTED

    client._poll()

    assert client.last_disconnect_class is None
    assert client.connection_state == ConnectionState.RECONNECTING


def test_d40_1_502_quiet_while_paused_but_loud_at_startup(quiet_client):
    """While TWS-gone, the 502 from each failed backoff attempt is
    downgraded (no all-night status-bar spam); at startup with no prior
    connection it still emits."""
    client = quiet_client
    emitted: list = []
    client.bridge.error_msg.connect(
        lambda req_id, code, msg: emitted.append((code, msg))
    )

    # Paused: 502 swallowed.
    client._connected = True
    client.connectionClosed()
    client.error(-1, 0, 502, "Couldn't connect to TWS")
    assert emitted == []

    # Fresh client, TWS never up: 502 still surfaces.
    fresh = IBApiClient()
    fresh.bridge.error_msg.connect(
        lambda req_id, code, msg: emitted.append((code, msg))
    )
    fresh.error(-1, 0, 502, "Couldn't connect to TWS")
    assert any(code == 502 for code, _ in emitted)


# ---------------------------------------------------------------------------
# AC-D40.1 — pause on TWS close (window level)
# ---------------------------------------------------------------------------


def test_d40_1_pause_on_tws_close(monkeypatch, qapp):
    """AC-D40.1: simulated TWS-gone disconnect → badge shows the
    owner-approved paused wording; the monitor marks all symbols paused
    (assert, mocked client); no evaluation while paused."""
    win = _make_window(monkeypatch, qapp)
    try:
        for sym in (SYM_A, SYM_B):
            _clear(sym)
        _add_alarm(SYM_A, 100.5)
        _add_alarm(SYM_B, 200.5)
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        session_a = win._sessions[SYM_A]
        session_b = win._sessions[SYM_B]
        assert session_a.monitored and session_b.monitored

        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()

        # Badge: exact owner-approved wording, never green.
        assert win.conn_badge.text() == PAUSED_TEXT
        assert "#34d399" not in win.conn_badge.styleSheet()
        # Monitor + sessions paused, pause-start recorded per symbol.
        assert win._tws_paused is True
        assert win.alarm_monitor.is_paused is True
        assert session_a.monitoring_paused is True
        assert session_b.monitoring_paused is True
        assert set(win.alarm_monitor._pause_start) == {SYM_A, SYM_B}

        # No evaluation while paused: drive a bar straight through the
        # alarm level — nothing may trigger.
        session_a.last_chart_price = 99.0
        bar = Bar(SYM_A, TF_1M, BASE_TS, 99.0, 102.0, 98.0, 101.0, 100.0)
        session_a._on_aggregated_bar(bar, True)
        assert session_a.alarms[0].triggered is False
    finally:
        _clear(SYM_A)
        _clear(SYM_B)
        win.close()


# ---------------------------------------------------------------------------
# AC-D40.2 — resume without phantoms
# ---------------------------------------------------------------------------


def test_d40_2_resume_without_phantoms(monkeypatch, qapp):
    """AC-D40.2: morning login after a pause → reconnect without restart;
    every monitored symbol resumes; driving a price through an alarm
    level fires once; resume alone fires nothing (no phantom)."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5, "cross_above")
        _add_alarm(SYM_A, 101.5, "cross_below")
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]

        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()
        assert win._tws_paused is True

        # Morning login: the D27 replay runs, then resume.
        replayed: list = []
        win._replay_subscriptions = lambda: replayed.append(1)
        win.toast.show_message = lambda msg: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert replayed, "resume must run the D27 subscription replay"
        assert win._tws_paused is False
        assert win.alarm_monitor.is_paused is False
        assert session.monitoring_paused is False
        # First-tick-no-eval guard (AC-D25.3): prev_price re-seeded.
        assert session.last_chart_price is None
        # Badge back to a live/paper state, not the paused wording.
        assert win.conn_badge.text() != PAUSED_TEXT

        # Resume alone must not fire: first bar lands BEYOND the
        # cross_above level — with a stale seed this would phantom-fire.
        bar1 = Bar(SYM_A, TF_1M, BASE_TS, 101.0, 103.0, 100.0, 102.0, 100.0)
        session._on_aggregated_bar(bar1, True)
        above = [a for a in session.alarms if a.direction == "cross_above"]
        assert above and all(a.triggered is False for a in above)

        # A genuine live crossing fires exactly once.
        bar2 = Bar(SYM_A, TF_1M, BASE_TS + 60, 102.0, 102.5, 98.0, 99.0, 100.0)
        session._on_aggregated_bar(bar2, True)
        below = [a for a in session.alarms if a.direction == "cross_below"]
        assert below and below[0].triggered is True
    finally:
        _clear(SYM_A)
        win.close()


def test_d40_2_resume_session_recreated_mid_pause_no_phantom(
    monkeypatch, qapp
):
    """Reviewer B1, D40 (regression): a session torn down mid-pause is
    re-created by reconcile() at resume. The recreated session must be
    re-seeded (last_chart_price None) — with the old
    resume_all()-before-reconcile() order it took the normal path with a
    stale cache seed and phantom-fired when the price crossed an alarm
    level during the gap."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_B)
        _add_alarm(SYM_B, 100.5, "cross_above")
        win.alarm_monitor.reconcile()
        assert SYM_B in win._sessions

        _go_live(win)
        # Seed a STALE cached 1m bar (close 99.0, below the alarm): with the
        # old resume order, the recreated session's _start_monitoring takes
        # the normal path and seeds last_chart_price=99.0 from this cache
        # row — the post-resume bar then phantom-fires. The fixed order
        # stages the session (last_chart_price=None) instead.
        from data.db import db
        db.conn.execute(
            "INSERT INTO bars (symbol, timeframe, ts, open, high, low,"
            " close, volume) VALUES (?,?,?,?,?,?,?,?)",
            (SYM_B, TF_1M, BASE_TS - 60, 98.0, 99.5, 97.5, 99.0, 50.0),
        )
        db.conn.commit()

        win.ib_client.connectionClosed()
        qapp.processEvents()
        assert win._tws_paused is True

        # Simulate torn-down-mid-pause: no session when TWS returns.
        win.alarm_monitor._stop_monitoring(win._sessions[SYM_B])
        assert SYM_B not in win._sessions

        # Morning login: D27 replay, then reconcile (recreates the
        # session via the staged path), then resume_all re-seeds.
        replayed: list = []
        win._replay_subscriptions = lambda: replayed.append(1)
        win.toast.show_message = lambda msg: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert replayed
        assert win._tws_paused is False
        session = win._sessions.get(SYM_B)
        assert session is not None, "reconcile must recreate the session"
        assert session.last_chart_price is None, (
            "recreated session must be re-seeded (first-tick-no-eval)"
        )

        # Resume alone must not fire: first bar lands BEYOND the
        # cross_above level — a stale seed would phantom-fire here.
        bar1 = Bar(SYM_B, TF_1M, BASE_TS, 101.0, 103.0, 100.0, 102.0, 100.0)
        session._on_aggregated_bar(bar1, True)
        above = [a for a in session.alarms if a.direction == "cross_above"]
        assert above and all(a.triggered is False for a in above)
    finally:
        _clear(SYM_B)
        win.close()


# ---------------------------------------------------------------------------
# AC-D40.3 — gap report
# ---------------------------------------------------------------------------


def test_d40_3_gap_report_names_symbols_and_interval():
    """AC-D40.3 (unit): the report names the symbols and the paused
    duration in the owner-approved shape."""
    t0 = 1_760_314_440.0  # fixed epochs → deterministic HH:MM
    t1 = t0 + 16 * 3600 + 26 * 60
    report = AlarmMonitor.format_gap_report(
        [("ES", t0, t1), ("NQ", t0, t1)]
    )
    s = time.strftime("%H:%M", time.localtime(t0))
    e = time.strftime("%H:%M", time.localtime(t1))
    assert report == f"ES, NQ unmonitored {s}–{e}"


def test_d40_3_gap_accounting_per_symbol(monkeypatch, qapp):
    """AC-D40.3 (integration): pause records per-symbol starts; resume
    returns the intervals and surfaces them in the status bar."""
    win = _make_window(monkeypatch, qapp)
    try:
        for sym in (SYM_A, SYM_B):
            _clear(sym)
        _add_alarm(SYM_A, 100.5)
        _add_alarm(SYM_B, 200.5)
        win.alarm_monitor.reconcile()

        _go_live(win)
        win.ib_client.connectionClosed()
        starts = dict(win.alarm_monitor._pause_start)
        assert set(starts) == {SYM_A, SYM_B}

        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        msg = win.status_bar.currentMessage()
        assert "unmonitored" in msg
        assert SYM_A in msg and SYM_B in msg
        # Pause bookkeeping cleared after the report.
        assert win.alarm_monitor._pause_start == {}
    finally:
        _clear(SYM_A)
        _clear(SYM_B)
        win.close()


def test_d40_3_alarm_created_mid_pause_stays_paused(monkeypatch, qapp):
    """An alarm added while TWS is gone is staged paused (no eval, no
    subscribe) and completes its subscribe on resume."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _clear(SYM_B)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()

        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()

        # Alarm CRUD during the pause → reconcile stages the monitor.
        _add_alarm(SYM_B, 200.5)
        win.alarm_monitor.on_alarm_changed()
        session_b = win._sessions[SYM_B]
        assert session_b.monitoring_paused is True
        assert session_b._monitor_subscribe_pending is True
        assert SYM_B in win.alarm_monitor._pause_start

        # Resume finishes the staged subscribe (rt_manager.subscribe is
        # the D25 stub handing out reqIds).
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert session_b._monitor_subscribe_pending is False
        assert session_b.monitoring_paused is False
        assert session_b.rt_req_id is not None
    finally:
        _clear(SYM_A)
        _clear(SYM_B)
        win.close()


# ---------------------------------------------------------------------------
# AC-D40.4 — transient unaffected
# ---------------------------------------------------------------------------


def test_d40_4_transient_drop_no_pause_ui(monkeypatch, qapp):
    """AC-D40.4: a non-TWS-gone disconnect keeps the fast path — no
    paused badge, no pause flags, no gap accounting."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]

        _go_live(win)
        # A drop that is NOT a server close: classification stays None.
        win.ib_client._connected = False
        win.ib_client._connection_state = ConnectionState.RECONNECTING
        win._on_disconnected()
        qapp.processEvents()

        assert win.ib_client.last_disconnect_class is None
        assert win._tws_paused is False
        assert win.conn_badge.text() == "● Disconnected"
        assert win.alarm_monitor.is_paused is False
        assert session.monitoring_paused is False
        assert win.alarm_monitor._pause_start == {}

        # Reconnect: no resume bookkeeping, no gap message.
        win._replay_subscriptions = lambda: None
        before = session.last_chart_price
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert session.last_chart_price == before
        assert "unmonitored" not in win.status_bar.currentMessage()
    finally:
        _clear(SYM_A)
        win.close()
