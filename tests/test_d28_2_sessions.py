"""D28.2 — TickerSession extraction (data-plane cluster).

AC-D28.2: per-symbol sessions own bars/aggregators/RT subscriptions/alarms;
realtime bars route by reqId → session with zero cross-talk; load_chart
works with explicit parameters (no toolbar reads).
"""

from __future__ import annotations

import itertools

import pytest

from config import settings
from data.alarm_store import AlarmStore
from data.models import Alarm, Bar

SYM_A = "SESA"
SYM_B = "SESB"
TF = "5 mins"
BASE_TS = 1_760_000_000  # fixed 5-min period


def _clear_alarms(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    # Deterministic RT reqIds: first subscribe -> 7001, second -> 7002.
    ids = iter([7001, 7002, 7003, 7004])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    # Never hit the network for historical requests in these tests. The D42
    # floor span (S17) can issue many chunks from one load, so hand out ids
    # unbounded rather than exhausting a fixed list.
    hids = itertools.count(8001)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


NOW_TS = (BASE_TS // 300) * 300  # 5-min period boundary


def _load(win, symbol: str, timeframe: str = TF) -> None:
    # now_ts on a 5-min period boundary -> priming is a no-op, the live feed
    # attaches immediately (D27.9).
    win._now_ts = lambda: NOW_TS
    win.load_chart(symbol, timeframe)


def _rt_bar(win, req_id: int, ts: int, price: float) -> None:
    win._on_realtime_bar(
        req_id, ts, price - 0.2, price + 0.2, price - 0.3, price, 100.0,
        price, 5,
    )


def _keep_alive_with_second_view(sess) -> None:
    """Simulate a 3c pop-out view so the session survives a symbol switch."""
    from unittest.mock import MagicMock

    sess.attach_view(MagicMock(), TF)
    sess.ensure_rt_subscribed()


def test_two_sessions_route_bars_with_zero_crosstalk(monkeypatch, qapp):
    """AC-D28.2: RT bars for A and B land in their own sessions only."""
    win = _make_window(monkeypatch, qapp)
    try:
        _load(win, SYM_A)   # rt reqId 7001
        sess_a = win._sessions[SYM_A]
        _keep_alive_with_second_view(sess_a)
        _load(win, SYM_B)   # rt reqId 7002; A kept alive by the second view
        assert win._rt_req_id == 7002
        assert set(win._sessions) == {SYM_A, SYM_B}

        _rt_bar(win, 7001, NOW_TS + 1, 10.0)   # A ticks
        _rt_bar(win, 7002, NOW_TS + 1, 20.0)   # B ticks

        sess_b = win._sessions[SYM_B]
        assert sess_a.last_chart_price == pytest.approx(10.0)
        assert sess_b.last_chart_price == pytest.approx(20.0)
        # B is the primary session; A's bars never leaked into it.
        assert win._last_chart_price == pytest.approx(20.0)
        # Unknown reqIds are ignored, never routed.
        _rt_bar(win, 424242, NOW_TS + 1, 999.0)
        assert sess_a.last_chart_price == pytest.approx(10.0)
        assert sess_b.last_chart_price == pytest.approx(20.0)
    finally:
        win.close()


def test_two_sessions_alarm_isolation(monkeypatch, qapp):
    """AC-D28.2: an alarm firing on A does not touch B's alarms or badge."""
    win = _make_window(monkeypatch, qapp)
    try:
        for s in (SYM_A, SYM_B):
            _clear_alarms(s)
        a = Alarm(id=None, symbol=SYM_A, price=10.5, direction="cross_above",
                  active=True, sound=False)
        a.id = AlarmStore.add(a)
        b = Alarm(id=None, symbol=SYM_B, price=99.0, direction="cross_above",
                  active=True, sound=False)
        b.id = AlarmStore.add(b)

        _load(win, SYM_A)   # sessions reload alarms in prepare_load
        sess_a = win._sessions[SYM_A]
        _keep_alive_with_second_view(sess_a)
        _load(win, SYM_B)

        sess_b = win._sessions[SYM_B]
        assert len(sess_a.alarms) == 1 and len(sess_b.alarms) == 1

        fired = []
        win.toast.show_message = lambda msg: fired.append(msg)
        # Tick A across its level (prev 10.0 -> 11.0 crosses 10.5).
        _rt_bar(win, 7001, NOW_TS + 1, 10.0)
        _rt_bar(win, 7001, NOW_TS + 6, 11.0)

        assert sess_a.alarms[0].triggered is True
        assert sess_b.alarms[0].triggered is False
        assert any(SYM_A in m for m in fired)
        assert not any(SYM_B in m for m in fired)
        # Badge reflects the main-chart symbol only: B has 1 active,
        # 0 triggered (A's trigger doesn't touch it).
        assert win.alarms_btn.text() == "Alarms (1)"
    finally:
        for s in (SYM_A, SYM_B):
            _clear_alarms(s)
        win.close()


def test_load_chart_explicit_params_no_toolbar_read(monkeypatch, qapp):
    """AC-D28.2: load_chart(symbol, timeframe) ignores the toolbar widgets."""
    win = _make_window(monkeypatch, qapp)
    try:
        win.symbol_input.setText("WRONG")
        win.tf_combo.setCurrentText("1 min")
        win.load_chart("EXPL", "15 mins")
        assert win._current_symbol == "EXPL"
        assert win._current_tf == "15 mins"
        assert "EXPL" in win._sessions
        # Toolbar widgets untouched.
        assert win.symbol_input.text() == "WRONG"
    finally:
        win.close()


def test_session_bar_cap(monkeypatch, qapp):
    """D28.4/D42-S18: per-session bars are capped at the floor-aware budget.

    The cap is the DERIVED budget for this session's ``(timeframe, ext_hours)``
    — ``floor_bar_budget`` — not the flat ``settings.SESSION_BAR_CAP``. In ETH
    mode the ``5 mins`` floor exceeds the flat 5000, so the derivation binds and
    the assertion is a discriminating guard (a revert to the flat cap fails).
    """
    from services.backfill_service import floor_bar_budget

    win = _make_window(monkeypatch, qapp)
    try:
        sess = win.get_or_create_session("CAPT")
        sess._wave_extended_hours = True  # ETH — the app's default mode
        budget = floor_bar_budget(TF, sess._wave_extended_hours)
        assert budget > settings.SESSION_BAR_CAP  # the correction is observable
        bars = [
            Bar("CAPT", TF, BASE_TS + i * 300, 1.0, 1.0, 1.0, 1.0, 10.0)
            for i in range(budget + 500)
        ]
        sess.set_bars(TF, bars)
        kept = sess.get_bars(TF)
        assert len(kept) == budget
        # Oldest dropped, newest kept.
        assert kept[0].ts == BASE_TS + 500 * 300
        assert kept[-1].ts == BASE_TS + (len(bars) - 1) * 300
    finally:
        win.close()


def test_session_teardown_on_symbol_switch(monkeypatch, qapp):
    """Switching symbols tears down the orphaned session (RT cancelled)."""
    win = _make_window(monkeypatch, qapp)
    try:
        unsubscribed = []
        orig_unsub = win.rt_manager.unsubscribe
        win.rt_manager.unsubscribe = lambda rid: unsubscribed.append(rid)

        _load(win, SYM_A)   # rt reqId 7001
        assert SYM_A in win._sessions
        _load(win, SYM_B)   # A orphaned -> teardown

        assert SYM_A not in win._sessions
        assert 7001 in unsubscribed
        assert win._primary_session is win._sessions[SYM_B]
    finally:
        win.rt_manager.unsubscribe = orig_unsub
        win.close()
