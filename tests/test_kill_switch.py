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
    # parent 100 + stop 101 + target 102, as a bracket transmit must register
    # them (D41: the retained builder + registry are the surviving path).
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


def test_bracket_builder_registers_all_three_legs(monkeypatch, qapp):
    # D26.8 / VALIDATOR: every transmitted bracket leg must be registered, or
    # the kill switch (and _update_order_status) cannot see the children.
    #
    # D41: the ticket-only ``_place_order`` that used to transmit brackets is
    # deleted, so the guarantee is pinned on the RETAINED builder instead --
    # ``Orders.bracket_order`` + ``register`` are exactly what the kill switch
    # reads. Asserting the builder's own contract keeps this non-circular.
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        parent_id = 100
        parent, stop, target = reg.bracket_order(
            parent_id, "BUY", 10, 150.0, 145.0, 160.0)

        # The builder's contract: the entry holds transmit, both children trade
        # opposite the entry, all three share the OCA group, and the LAST child
        # transmits the whole group.
        assert (parent.action, stop.action, target.action) == (
            "BUY", "SELL", "SELL")
        assert parent.transmit is False and stop.transmit is False
        assert target.transmit is True
        assert stop.parentId == parent_id and target.parentId == parent_id
        assert stop.ocaGroup == target.ocaGroup == f"bracket-{parent_id}"

        # Register EVERY leg, exactly as the transmit path must.
        for leg_id, leg_type, leg_action, lmt, aux in (
            (parent_id, "BRACKET", "BUY", 150.0, None),
            (parent_id + 1, "STP", "SELL", None, 145.0),
            (parent_id + 2, "LMT", "SELL", 160.0, None),
        ):
            reg.register(UserOrder(
                order_id=leg_id, symbol="AAPL", action=leg_action,
                total_qty=10, order_type=leg_type,
                lmt_price=lmt, aux_price=aux, status="Submitted",
                parent_id=0 if leg_id == parent_id else parent_id,
                oca_group=f"bracket-{parent_id}", transmit=True,
            ))
        for oid in (parent_id, parent_id + 1, parent_id + 2):
            assert reg.get(oid) is not None, f"leg {oid} not registered"
        assert reg.get(parent_id).action == "BUY"
        assert reg.get(parent_id + 1).action == "SELL"  # protective children
        assert reg.get(parent_id + 2).action == "SELL"

        # ...and the kill switch must now see and cancel all three.
        cancelled = []
        monkeypatch.setattr(win.ib_client, "cancelOrder",
                            lambda oid: cancelled.append(oid))
        monkeypatch.setattr(win.ib_client, "reqGlobalCancel", lambda: None)
        pre, post = win._kill_switch()
        assert (pre, post) == (3, 3)
        assert sorted(cancelled) == [parent_id, parent_id + 1, parent_id + 2]
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
