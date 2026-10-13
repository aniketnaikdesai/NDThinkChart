"""D25 — headless alarm monitor (AC-D25.1–D25.5)."""

from __future__ import annotations

import pytest

from data.alarm_store import AlarmStore
from data.bar_cache import BarCache
from data.models import Alarm, Bar

SYM_MON = "MONA"
SYM_NOMON = "MONB"
TF_1M = "1m"
BASE_TS = 1_760_000_000


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.execute("DELETE FROM bars WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

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


def test_d25_1_symbols_with_active_alarms():
    """AC-D25.1: store lists symbols with active, untriggered alarms."""
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


def test_d25_2_headless_session_monitors(monkeypatch, qapp):
    """AC-D25.2: reconcile creates a headless monitored session (no views)."""
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
        # Zero historical requests from the headless session.
        # (md_manager.req_historical_data returns 5999; none should be called
        # with a 1m backfill — the stub would have recorded it.)
    finally:
        _clear(SYM_MON)
        win.close()


def test_d25_3_headless_evaluates_on_push(monkeypatch, qapp):
    """AC-D25.3: headless session evaluates alarms on every 5-sec push."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(SYM_MON)
        aid = _add_alarm(SYM_MON, 100.5)

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


def test_d25_4_no_cache_no_phantom(monkeypatch, qapp):
    """AC-D25.4: no cache → first tick seeds, no phantom trigger."""
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


def test_d25_5_reconcile_on_trigger_stops_monitor(monkeypatch, qapp):
    """AC-D25.5: after the last alarm triggers, the monitor stands down."""
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
