"""D98 — one outage baseline, one resume path (AC-D98.1, AC-D98.2, P29).

Owner context: the TWS-gone path already re-seeded every session and
recorded per-symbol intervals; the transient path called only
``reconcile()``, so ``prev_price`` survived the drop and the first
post-reconnect tick was evaluated against a pre-outage price. P29 gives
every outage the same treatment: ``AlarmMonitor.begin_outage()`` records
the interval on every drop that follows a live session, every reconnect
runs ``reconcile()`` → ``resume_all()``, and the one existing formatter
reports the window.

The record is gated twice so a failed launch never counts as an outage:
``begin_outage()`` returns immediately when no session exists (a pre-
handshake ``connectionClosed()`` on an "app started before TWS" launch
records nothing — the first ``nextValidId`` keeps D25.2's 1m-cache seed),
and ``resume_all()`` re-seeds only when a drop was recorded. The pause
**flags** stay TWS-gone-only; ``_outage_active`` is set only by
``begin_outage()`` and cleared only by ``resume_all()``.

**G6 is owner-run and is not claimed here.** No case in this file opens a
live TWS socket, drops a real connection, or fires an alarm from live
data. What these cases proxy: the interval ledger, the re-seed, the
first-tick suppression, the gap line and the cold-start ordering.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

import services.alarm_monitor as alarm_monitor_module
from data.alarm_store import AlarmStore
from data.bar_cache import BarCache
from data.models import Alarm, Bar
from ibkr.client import ConnectionState, DisconnectClass, IBApiClient

SYM_A = "D98A"
SYM_NOMON = "D98B"
TF_1M = "1m"
BASE_TS = 1_760_000_000
PAUSED_TEXT = "Monitoring paused — TWS disconnected"
_REPO = Path(__file__).resolve().parent.parent


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


class _Clock:
    """Controlled wall clock for the monitor's interval ledger."""

    def __init__(self, start: float = 1_760_400_000.0):
        self.now = start

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _TimeShim:
    """Stand-in for the ``time`` module inside ``services.alarm_monitor``.

    Only ``time()`` is controlled; ``strftime``/``localtime`` stay real so
    ``format_gap_report`` keeps its owner-approved local-HH:MM wording.
    """

    def __init__(self, clock: _Clock):
        self._clock = clock

    def time(self) -> float:
        return self._clock.time()

    def strftime(self, *a, **k):
        return time.strftime(*a, **k)

    def localtime(self, *a, **k):
        return time.localtime(*a, **k)


@pytest.fixture
def clock(monkeypatch):
    c = _Clock()
    monkeypatch.setattr(alarm_monitor_module, "time", _TimeShim(c))
    return c


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
    """MainWindow with a stubbed RT subscribe (D40 pattern) and no timers."""
    from ibkr.client import IBApiClient as _C

    monkeypatch.setattr(threading, "Timer", _NoopTimer)
    monkeypatch.setattr(_C, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter(range(8101, 8999))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    win.md_manager.req_historical_data = lambda *a, **k: 8999
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


def _bar(symbol: str, ts: int, close: float) -> Bar:
    return Bar(
        symbol, TF_1M, ts, close, close + 0.5, close - 0.5, close, 100.0
    )


def _drop(win, classification: str) -> None:
    """Deliver one transport drop of the named classification."""
    if classification == "tws_gone":
        _go_live(win)
        win.ib_client.connectionClosed()
    else:
        # The socket was already gone (the poll path records it): the
        # server never closed it, so no classification is set.
        win.ib_client._connected = False
        win.ib_client._connection_state = ConnectionState.RECONNECTING
        win._on_disconnected()


def _hm(ts: float) -> str:
    return time.strftime("%H:%M", time.localtime(ts))


# ---------------------------------------------------------------------------
# AC-D98.1 — transient drop: one ledger, one seed, one line
# ---------------------------------------------------------------------------


def test_p29_t3_01_transient_drop_records_interval_and_seeds(
    monkeypatch, qapp, clock
):
    """AC-D98.1 (transient): the drop records the symbol's interval, the
    first post-reconnect tick seeds with no evaluation, the status line
    reports the unmonitored window, and the pause UI stays TWS-gone-only.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]
        session.last_chart_price = 99.0
        _go_live(win)

        drop_time = clock.time()
        _drop(win, "transient")
        qapp.processEvents()

        assert win.ib_client.last_disconnect_class is None
        assert win.alarm_monitor._outage_active is True
        assert win.alarm_monitor._outage_start == {SYM_A: drop_time}
        # The pause UI is TWS-gone-only.
        assert win._tws_paused is False
        assert win.alarm_monitor.is_paused is False
        assert session.monitoring_paused is False
        assert win.conn_badge.text() == "● Disconnected"

        fired: list = []
        win.toast.show_message = lambda msg: fired.append(msg)
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert session.last_chart_price is None
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}
        msg = win.status_bar.currentMessage()
        assert "unmonitored" in msg
        assert SYM_A in msg and _hm(drop_time) in msg

        # The first bar lands beyond the level: a seed, never a fire.
        session._on_aggregated_bar(_bar(SYM_A, BASE_TS, 102.0), True)
        assert session.alarms[0].triggered is False
        assert not any(SYM_A in m for m in fired)
    finally:
        _clear(SYM_A)
        win.close()


def test_p29_t3_02_tws_gone_drop_records_interval_and_seeds(
    monkeypatch, qapp, clock
):
    """AC-D98.1 (TWS_GONE): the same ledger/seed/gap-line assertions, plus
    the pause flags and badge ON during the outage and OFF after resume.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]
        session.last_chart_price = 99.0
        _go_live(win)

        drop_time = clock.time()
        _drop(win, "tws_gone")
        qapp.processEvents()

        assert win.ib_client.last_disconnect_class == DisconnectClass.TWS_GONE
        assert win.alarm_monitor._outage_active is True
        assert win.alarm_monitor._outage_start == {SYM_A: drop_time}
        assert win._tws_paused is True
        assert win.alarm_monitor.is_paused is True
        assert session.monitoring_paused is True
        assert win.conn_badge.text() == PAUSED_TEXT

        fired: list = []
        win.toast.show_message = lambda msg: fired.append(msg)
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert win.ib_client.last_disconnect_class is None
        assert session.last_chart_price is None
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}
        assert win._tws_paused is False
        assert win.alarm_monitor.is_paused is False
        assert session.monitoring_paused is False
        msg = win.status_bar.currentMessage()
        assert "unmonitored" in msg and SYM_A in msg

        session._on_aggregated_bar(_bar(SYM_A, BASE_TS, 102.0), True)
        assert session.alarms[0].triggered is False
        assert not any(SYM_A in m for m in fired)
    finally:
        _clear(SYM_A)
        win.close()


# ---------------------------------------------------------------------------
# AC-D98.2 — the crossing rule after the seed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("classification", ["transient", "tws_gone"])
def test_p29_t3_03_post_seed_crossing_fires_once(
    monkeypatch, qapp, clock, classification
):
    """AC-D98.2 (both classifications): the seed tick beyond the level does
    nothing, a tick at/below it does not fire, and the next strictly-beyond
    tick fires exactly once.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]
        session.last_chart_price = 99.0
        _go_live(win)

        _drop(win, classification)
        qapp.processEvents()

        fired: list = []
        win.toast.show_message = lambda msg: fired.append(msg)
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert session.last_chart_price is None

        # Seed tick beyond the level — no evaluation, no fire.
        session._on_aggregated_bar(_bar(SYM_A, BASE_TS, 102.0), True)
        assert session.alarms[0].triggered is False
        # A tick at/below the level crosses nothing in the alarm's direction.
        session._on_aggregated_bar(_bar(SYM_A, BASE_TS + 60, 100.0), True)
        assert session.alarms[0].triggered is False
        # Strictly beyond the level: fires exactly once.
        session._on_aggregated_bar(_bar(SYM_A, BASE_TS + 120, 101.0), True)
        assert session.alarms[0].triggered is True
        assert len([m for m in fired if SYM_A in m]) == 1
    finally:
        _clear(SYM_A)
        win.close()


# ---------------------------------------------------------------------------
# AC-P29-03-LEDGER — one ledger, one setter, one clearer, no legacy name
# ---------------------------------------------------------------------------


def test_p29_t3_04_one_ledger_earliest_start_no_legacy_name(
    monkeypatch, qapp, clock
):
    """AC-P29-03-LEDGER: two drops without a successful connect keep the
    earliest start; one resume clears the ledger and the flag; the legacy
    ``_pause_start`` exists neither as an attribute nor in the three named
    files.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        _go_live(win)
        monitor = win.alarm_monitor
        assert not hasattr(monitor, "_pause_start")

        first = clock.time()
        _drop(win, "tws_gone")
        qapp.processEvents()
        assert monitor._outage_start[SYM_A] == first

        # A second drop with no successful connect between: setdefault
        # keeps the earliest start.
        clock.advance(90)
        monitor.begin_outage()
        assert monitor._outage_start[SYM_A] == first

        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert monitor._outage_start == {}
        assert monitor._outage_active is False
        # The report carried the earliest start, not the second drop's.
        msg = win.status_bar.currentMessage()
        assert "unmonitored" in msg and _hm(first) in msg

        for rel in (
            "services/alarm_monitor.py",
            "ui/main_window.py",
            "tests/test_d40_tws_lifecycle.py",
        ):
            text = (_REPO / rel).read_text(encoding="utf-8")
            assert "_pause_start" not in text, rel
    finally:
        _clear(SYM_A)
        win.close()


def test_p29_t3_05_pause_all_alone_arms_no_reseed(monkeypatch, qapp, clock):
    """AC-P29-03-LEDGER: ``pause_all()`` alone leaves ``_outage_active``
    False, and the following ``resume_all()`` changes no session baseline
    (no re-seed without a recorded outage).
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]
        session.last_chart_price = 99.0
        monitor = win.alarm_monitor

        monitor.pause_all()
        assert monitor._outage_active is False
        assert monitor._paused is True
        assert session.monitoring_paused is True

        gaps = monitor.resume_all()
        assert monitor._outage_active is False
        # pause_all still records the interval it always did.
        assert [g[0] for g in gaps] == [SYM_A]
        assert monitor._outage_start == {}
        assert monitor._paused is False
        assert session.monitoring_paused is False
        # No recorded drop → no re-seed.
        assert session.last_chart_price == 99.0
    finally:
        _clear(SYM_A)
        win.close()


# ---------------------------------------------------------------------------
# AC-P29-03-COVERAGE — no alarm, mid-outage session, no-session drop
# ---------------------------------------------------------------------------


def test_p29_t3_06_no_live_alarm_no_entry_no_line(monkeypatch, qapp, clock):
    """AC-P29-03-COVERAGE (i): a symbol with no live alarm is recorded
    nowhere and reported nowhere, and its own seed is untouched.

    The alarm-less session is created while the transport is down, after a
    drop that recorded nothing because no session existed — so there is no
    outage to resume. (A session that *does* exist at a recorded drop is
    re-seeded by AC-D98.1's every-session rule even when it carries no
    alarm; the ledger stays per-symbol either way — see the next case.)
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_NOMON)
        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()
        assert win.alarm_monitor._outage_active is False

        session = win.get_or_create_session(SYM_NOMON)
        session.monitored = False
        session.last_chart_price = 123.0

        win._replay_subscriptions = lambda: None
        win.ib_client._connected = False
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        assert SYM_NOMON not in win.alarm_monitor._outage_start
        assert "unmonitored" not in win.status_bar.currentMessage()
        assert win._sessions[SYM_NOMON] is session
        assert session.last_chart_price == 123.0
    finally:
        _clear(SYM_NOMON)
        win.close()


def test_p29_t3_07_session_created_during_outage(monkeypatch, qapp, clock):
    """AC-P29-03-COVERAGE (ii/iii): a session created during a *recorded*
    outage is re-seeded at resume; when no session existed at the drop
    there is no outage to resume and a later session keeps its own seed.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _clear(SYM_NOMON)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        _go_live(win)
        _drop(win, "tws_gone")
        qapp.processEvents()
        assert win.alarm_monitor._outage_active is True

        # Created after the drop, before the resume (not a headless
        # monitor, so reconcile leaves it alone and it reaches the resume).
        late = win.get_or_create_session(SYM_NOMON)
        late.monitored = False
        late.last_chart_price = 55.0

        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        # AC-D98.1's re-seed is every session, not only the ledger's symbols.
        assert win._sessions[SYM_NOMON] is late
        assert late.last_chart_price is None

        # Second half: no session at the drop → nothing recorded.
        _clear(SYM_A)
        win.alarm_monitor._stop_monitoring(late)
        win.alarm_monitor.reconcile()
        assert win._sessions == {}

        _go_live(win)
        win.ib_client.connectionClosed()
        qapp.processEvents()
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}

        own_seed = win.get_or_create_session(SYM_NOMON)
        own_seed.last_chart_price = 77.0
        win._replay_subscriptions = lambda: None
        win.ib_client._connected = False
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert own_seed.last_chart_price == 77.0
        assert "unmonitored" not in win.status_bar.currentMessage()
    finally:
        _clear(SYM_A)
        _clear(SYM_NOMON)
        win.close()


# ---------------------------------------------------------------------------
# AC-P29-03-COLDSTART — a failed launch is not an outage
# ---------------------------------------------------------------------------


def test_p29_t3_08_pre_handshake_close_is_not_an_outage(
    monkeypatch, qapp, clock
):
    """AC-P29-03-COLDSTART: a pre-handshake ``connectionClosed()`` records
    nothing, and the first ``nextValidId(1)`` keeps the reconcile-seeded
    1m close (D25.2's cache seed survives startup).
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        BarCache.save_bars([
            Bar(SYM_A, TF_1M, BASE_TS - 60, 99.0, 99.5, 98.5, 100.0, 1000.0),
        ])
        _add_alarm(SYM_A, 200.0)  # far from the seed; no evaluation matter
        assert win._sessions == {}
        assert win.alarm_monitor._outage_start == {}

        # A failed/pre-handshake attempt: the socket never came up.
        win.ib_client.connectionClosed()
        qapp.processEvents()
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}

        # The first successful handshake reconciles from the 1m cache.
        win._replay_subscriptions = lambda: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()

        session = win._sessions[SYM_A]
        assert session.last_chart_price == pytest.approx(100.0)
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}
        assert "unmonitored" not in win.status_bar.currentMessage()
    finally:
        _clear(SYM_A)
        win.close()


# ---------------------------------------------------------------------------
# AC-P29-03-INERT — a duplicate connect, and a late drop consumed once
# ---------------------------------------------------------------------------


def test_p29_t3_09_duplicate_connect_inert_late_drop_consumed(
    monkeypatch, qapp, clock
):
    """AC-P29-03-INERT: a second ``nextValidId(1)`` with no intervening drop
    leaves every baseline untouched; a ``begin_outage()`` delivered after a
    resume arms exactly one re-seed at the following connect.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_A)
        _add_alarm(SYM_A, 100.5)
        win.alarm_monitor.reconcile()
        session = win._sessions[SYM_A]
        _go_live(win)

        _drop(win, "tws_gone")
        qapp.processEvents()
        win._replay_subscriptions = lambda: None
        win.toast.show_message = lambda msg: None
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert session.last_chart_price is None

        # A later tick seeds the session again.
        session.last_chart_price = 42.0
        # The client ignores a duplicate handshake (``nextValidId`` only
        # marks CONNECTED when it was down) and a duplicate slot delivery
        # follows no recorded drop — neither touches a baseline.
        win.ib_client.nextValidId(1)
        win._on_connected()
        qapp.processEvents()
        assert session.last_chart_price == 42.0
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}

        # A drop delivered after the resume arms exactly one re-seed at the
        # following connect, which resume_all() consumes.
        clock.advance(120)
        late_start = clock.time()
        win.alarm_monitor.begin_outage()
        assert win.alarm_monitor._outage_active is True
        assert win.alarm_monitor._outage_start == {SYM_A: late_start}

        win.ib_client._connected = False
        win.ib_client.nextValidId(1)
        qapp.processEvents()
        assert session.last_chart_price is None
        assert win.alarm_monitor._outage_active is False
        assert win.alarm_monitor._outage_start == {}
        msg = win.status_bar.currentMessage()
        assert "unmonitored" in msg and SYM_A in msg
    finally:
        _clear(SYM_A)
        win.close()
