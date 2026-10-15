"""D28.1 — pacing never sleeps on the GUI thread (AC-D28.1).

Throttlers return a wait duration (or raise PacingExceeded); callers defer via
QTimer.singleShot with a persistent "pacing-limited, retrying" status. Orders
use their own token-bucket limiter, never the realtime throttle.
"""
import threading
import time

import pytest
from PyQt6.QtTest import QTest

from ibkr import pacing as pacing_mod
from ibkr.pacing import PacingExceeded, PacingManager, OrderRateLimiter
from ibkr.realtime_bars import RealtimeBarsManager


def _capture_gui_sleeps(monkeypatch) -> list[float]:
    """Record ``time.sleep`` calls made on the GUI thread, and never sleep.

    D28.1's guarantee is about the GUI thread only, so the capture is scoped to
    it: a sleep issued by an unrelated thread — e.g. the D38 yfinance event
    worker's ``time.sleep(gap)`` on its own QThread
    (``data/events/yfinance_source.py``) — must not be mistaken for a
    GUI-thread sleep, or the assertion fails on another thread's work
    (ESC-047). The GUI thread is the process main thread, since Qt requires
    ``QApplication`` to be created on it.
    """
    gui_thread = threading.main_thread()
    sleeps: list[float] = []

    def _record(seconds: float) -> None:
        if threading.current_thread() is gui_thread:
            sleeps.append(seconds)

    monkeypatch.setattr(time, "sleep", _record)
    return sleeps


def _exhaust_realtime_budget(pm: PacingManager, wait_s: float = 600.0) -> None:
    """Fill the 60-slot realtime budget so the next subscribe must wait.

    wait_s controls how long the caller would wait (backdate entries).
    """
    now = time.time()
    pm._rt_times.clear()
    for _ in range(60):
        pm._rt_times.append(now - (600.0 - wait_s))


class _FakeClient:
    def __init__(self):
        self.rt_bars: list[int] = []

    def reqRealTimeBars(self, reqId, *a, **k):
        self.rt_bars.append(reqId)

    def cancelRealTimeBars(self, reqId):
        pass


def test_realtime_wait_zero_when_budget_free():
    pm = PacingManager()
    assert pm.realtime_wait_seconds() == 0.0
    assert pm.realtime_wait_for_slots(5) == 0.0


def test_realtime_wait_positive_when_budget_exhausted():
    pm = PacingManager()
    _exhaust_realtime_budget(pm, wait_s=120.0)
    wait = pm.realtime_wait_seconds()
    assert 100.0 < wait <= 120.0


def test_subscribe_raises_pacing_exceeded_without_sleep(monkeypatch):
    """Budget exhausted -> PacingExceeded, and time.sleep is never called."""
    sleeps = _capture_gui_sleeps(monkeypatch)
    # Use the real singleton: the conftest fixture resets it per test.
    _exhaust_realtime_budget(pacing_mod.pacing_manager)
    fake = _FakeClient()
    mgr = RealtimeBarsManager(fake)
    with pytest.raises(PacingExceeded) as excinfo:
        mgr.subscribe("AAPL", object())
    assert excinfo.value.wait_seconds > 0
    assert fake.rt_bars == [], "no subscription may be issued while pacing-limited"
    assert sleeps == [], "pacing must never sleep the calling thread"


def test_subscribe_records_slot_when_budget_free():
    fake = _FakeClient()
    mgr = RealtimeBarsManager(fake)
    req_id = mgr.subscribe("AAPL", object())
    assert fake.rt_bars == [req_id]
    assert len(pacing_mod.pacing_manager._rt_times) == 1


def test_order_limiter_allows_burst_then_denies():
    lim = OrderRateLimiter(rate_per_sec=5.0, capacity=5)
    assert all(lim.try_acquire() for _ in range(5))
    assert not lim.try_acquire()
    assert lim.retry_delay_s() > 0


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow
    win = MainWindow()
    fake = _FakeClient()
    win.rt_manager.client = fake
    win.show()
    qapp.processEvents()
    return win, fake


def test_attach_live_feed_defers_with_status_and_retries(monkeypatch, qapp):
    """Chart load while pacing-limited: no sleep, status shown, sub fires later."""
    sleeps = _capture_gui_sleeps(monkeypatch)
    win, fake = _make_window(monkeypatch, qapp)
    try:
        from ibkr.contracts import get_contract_for_symbol
        # Backdate the budget so the wait is ~0.3s (singleShot-testable).
        _exhaust_realtime_budget(pacing_mod.pacing_manager, wait_s=0.3)
        win._current_symbol = "TEST"
        win._attach_live_feed("TEST", get_contract_for_symbol("TEST"))
        qapp.processEvents()
        assert fake.rt_bars == [], "subscription must be deferred, not issued"
        assert sleeps == [], "no sleep on the GUI thread"
        assert "pacing-limited" in win.status_bar.currentMessage().lower()
        # Let the budget free and the deferred retry fire.
        QTest.qWait(900)
        assert fake.rt_bars, "deferred subscription never fired"
        assert len(fake.rt_bars) == 1, "must subscribe exactly once"
    finally:
        win.close()


def _seed_position(symbol="AAPL", qty=10.0):
    """Seed a positions row so the retained close path can be driven."""
    from data.db import db
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions (symbol, account, con_id, contract_type, qty,"
        " avg_cost, local_symbol, multiplier, expiry, strike, right,"
        " updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (symbol, "DU123", None, "stock", qty, 100.0, None, 1.0,
         None, None, None, 1_760_000_000),
    )
    db.conn.commit()
    return cur.lastrowid


def _clear_position(pid):
    from data.db import db
    cur = db.conn.cursor()
    cur.execute("DELETE FROM positions WHERE id=?", (pid,))
    db.conn.commit()


def test_close_position_defers_when_limiter_empty(monkeypatch, qapp):
    """D28.1 retained close path: limiter empty -> no sleep, no transmit,
    status; the deferred retry transmits exactly once.

    Also pins the D41-S5 ordering: the D26.7 gate runs BEFORE the pacing
    deferral, so a gate-rejected close never shows the pacing status.
    """
    sleeps = _capture_gui_sleeps(monkeypatch)
    win, _fake = _make_window(monkeypatch, qapp)
    pid = _seed_position()
    bad_pid = None
    try:
        win._ibkr_connected = True
        calls: list = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        lim = pacing_mod.order_limiter
        for _ in range(5):
            assert lim.try_acquire()

        # (a) S5 gate order: a gate-rejected close (blank symbol) returns at
        # the gate -- no transmit, and crucially no pacing status, which it
        # would show if the deferral ran before validation.
        bad_pid = _seed_position(symbol="")
        win._close_position_by_id(bad_pid)
        qapp.processEvents()
        assert calls == [], "a rejected close must not transmit"
        assert "pacing-limited" not in win.status_bar.currentMessage().lower(), (
            "the validation gate must run before the pacing deferral")

        # (b) the retained close emitter defers when the bucket is empty.
        win._close_position_by_id(pid)
        qapp.processEvents()
        assert calls == [], "rate-limited close must not transmit immediately"
        assert sleeps == [], "no sleep on the GUI thread"
        assert "pacing-limited" in win.status_bar.currentMessage().lower()

        # (c) the deferred retry transmits exactly once once the bucket refills.
        QTest.qWait(1200)  # bucket refills at 5/s; deferred retry fires
        assert len(calls) == 1, "deferred close must transmit exactly once"
    finally:
        if bad_pid is not None:
            _clear_position(bad_pid)
        _clear_position(pid)
        win.close()


def test_replay_all_defers_without_partial_reissue(monkeypatch, qapp):
    """Reconnect replay is all-or-nothing under pacing pressure: no doubles."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        from ibkr.contracts import get_contract_for_symbol
        from ibkr.subscription_manager import RT_BARS
        for sym in ("AAA", "BBB"):
            req_id = win.rt_manager.subscribe(sym, get_contract_for_symbol(sym))
            win.sub_manager.subscribe(
                sym, req_id, RT_BARS,
                reissue=lambda s=sym, c=get_contract_for_symbol(sym):
                    win.rt_manager.subscribe(s, c),
                rebind=lambda _new: None,
            )
        n_before = len(fake.rt_bars)
        assert n_before == 2
        # Exhaust the budget with a short (~0.3s) wait.
        _exhaust_realtime_budget(pacing_mod.pacing_manager, wait_s=0.3)
        win._replay_subscriptions()
        qapp.processEvents()
        assert len(fake.rt_bars) == n_before, \
            "pacing-limited replay must not partially reissue"
        assert "pacing-limited" in win.status_bar.currentMessage().lower()
        QTest.qWait(900)
        assert len(fake.rt_bars) == n_before + 2, \
            "deferred replay must reissue each subscription exactly once"
    finally:
        win.close()
