"""D28.1 — pacing never sleeps on the GUI thread (AC-D28.1).

Throttlers return a wait duration (or raise PacingExceeded); callers defer via
QTimer.singleShot with a persistent "pacing-limited, retrying" status. Orders
use their own token-bucket limiter, never the realtime throttle.
"""
import time

import pytest
from PyQt6.QtTest import QTest

from ibkr import pacing as pacing_mod
from ibkr.pacing import PacingExceeded, PacingManager, OrderRateLimiter
from ibkr.realtime_bars import RealtimeBarsManager


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
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
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
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
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


def test_place_order_defers_when_limiter_empty(monkeypatch, qapp):
    """Order path: limiter empty -> no sleep, no transmit, status; retry sends."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    win, _fake = _make_window(monkeypatch, qapp)
    try:
        win._ibkr_connected = True
        calls: list = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        lim = pacing_mod.order_limiter
        for _ in range(5):
            assert lim.try_acquire()
        win._place_order(contract=object(), symbol="AAPL", action="BUY",
                         qty=10, order_type="MKT", lmt_price=0.0,
                         stop_price=0.0, target_price=0.0)
        qapp.processEvents()
        assert calls == [], "rate-limited order must not transmit immediately"
        assert sleeps == [], "no sleep on the GUI thread"
        assert "pacing-limited" in win.status_bar.currentMessage().lower()
        QTest.qWait(1200)  # bucket refills at 5/s; deferred retry fires
        assert len(calls) == 1, "deferred order must transmit exactly once"
    finally:
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
