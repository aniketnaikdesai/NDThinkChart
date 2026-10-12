"""D26.8: kill switch cancels every open order, including bracket children.

Pre-fix behaviour: zero cancelOrder/reqGlobalCancel call sites; bracket
children were never registered, so even a naive "cancel every registry
ID" would miss the protective legs.

AC-D26.8: kill switch -> reqGlobalCancel + cancelOrder for every tracked
ID (parent + both bracket children); pre/post counts surfaced.
"""

import pytest

from ibkr.orders import Orders, UserOrder


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def _fresh_registry(monkeypatch):
    fresh = Orders()
    monkeypatch.setattr("ui.main_window.order_registry", fresh)
    return fresh


def _bracket_legs(reg):
    # parent 100 + stop 101 + target 102, as _place_order registers them.
    for oid, otype, action in ((100, "BRACKET", "BUY"),
                              (101, "STP", "SELL"),
                              (102, "LMT", "SELL")):
        reg.register(UserOrder(order_id=oid, symbol="AAPL", action=action,
                               total_qty=10, order_type=otype,
                               status="Submitted"))
    return [100, 101, 102]


def test_kill_switch_cancels_all_legs(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        leg_ids = _bracket_legs(reg)
        cancelled, globals_ = [], []
        monkeypatch.setattr(win.ib_client, "cancelOrder",
                            lambda oid: cancelled.append(oid))
        monkeypatch.setattr(win.ib_client, "reqGlobalCancel",
                            lambda: globals_.append(True))
        pre, post = win._kill_switch()
        assert globals_ == [True], "reqGlobalCancel must be issued"
        assert sorted(cancelled) == leg_ids, (
            f"every leg must be cancelled, got {cancelled}")
        assert (pre, post) == (3, 3)
        assert all(reg.get(oid).status == "Cancelled" for oid in leg_ids)
    finally:
        win.close()


def test_kill_switch_reports_counts(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        _bracket_legs(reg)
        monkeypatch.setattr(win.ib_client, "cancelOrder", lambda oid: None)
        monkeypatch.setattr(win.ib_client, "reqGlobalCancel", lambda: None)
        win._kill_switch()
        msg = win.status_bar.currentMessage()
        assert "3" in msg and "cancel" in msg.lower(), f"counts not shown: {msg!r}"
    finally:
        win.close()


def test_bracket_place_registers_all_three_legs(monkeypatch, qapp):
    # VALIDATOR: children must be registered at transmit time, or the kill
    # switch (and _update_order_status) cannot see them.
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        win._ibkr_connected = True
        placed = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda oid, _c, _o: placed.append(oid))
        from ibkr.id_manager import IdManager
        fake_ids = IdManager()
        monkeypatch.setattr("ui.main_window.id_manager", fake_ids)
        win._place_order(contract=object(), symbol="AAPL", action="BUY",
                         qty=10, order_type="BRACKET", lmt_price=150.0,
                         stop_price=145.0, target_price=160.0)
        assert sorted(placed) == [1, 2, 3]
        for oid in (1, 2, 3):
            assert reg.get(oid) is not None, f"leg {oid} not registered"
        assert reg.get(1).action == "BUY"
        assert reg.get(2).action == "SELL"  # protective children opposite
        assert reg.get(3).action == "SELL"
    finally:
        win.close()


def test_flatten_all_kills_first(monkeypatch, qapp):
    # _on_portfolio_flatten_all must cancel working orders BEFORE closing.
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        _bracket_legs(reg)
        order = []
        monkeypatch.setattr(win, "_kill_switch",
                            lambda: order.append("kill") or (3, 3))
        monkeypatch.setattr(win, "_close_position_by_id",
                            lambda pid: order.append(("close", pid)))
        # _on_portfolio_flatten_all does `from data.db import db` locally.
        monkeypatch.setattr("data.db.db", _FakeDb([]))
        win._on_portfolio_flatten_all()
        assert order and order[0] == "kill", (
            f"kill switch must run before closes, got {order}")
    finally:
        win.close()


class _FakeDb:
    def __init__(self, rows):
        self.conn = self
        self._rows = rows

    def cursor(self):
        return self

    def execute(self, *a, **k):
        return self

    def fetchall(self):
        return self._rows
