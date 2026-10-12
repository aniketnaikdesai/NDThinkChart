"""Tests for ibkr/orders.py — pure order builders and registry."""

import pytest
from ibapi.order import Order

from ibkr.orders import orders, Orders, UserOrder
from ibkr.id_manager import id_manager


# ── Builder tests ─────────────────────────────────────────────

def test_market_order():
    order = orders.market_order("BUY", 100)
    assert isinstance(order, Order)
    assert order.action == "BUY"
    assert order.orderType == "MKT"
    assert order.totalQuantity == 100


def test_market_order_sell():
    order = orders.market_order("SELL", 50)
    assert order.action == "SELL"
    assert order.orderType == "MKT"
    assert order.totalQuantity == 50


def test_limit_order():
    order = orders.limit_order("BUY", 100, 150.25)
    assert isinstance(order, Order)
    assert order.action == "BUY"
    assert order.orderType == "LMT"
    assert order.totalQuantity == 100
    assert order.lmtPrice == 150.25


def test_limit_order_sell():
    order = orders.limit_order("SELL", 50, 200.0)
    assert order.action == "SELL"
    assert order.orderType == "LMT"
    assert order.lmtPrice == 200.0


def test_stop_order():
    order = orders.stop_order("SELL", 100, 145.0)
    assert isinstance(order, Order)
    assert order.action == "SELL"
    assert order.orderType == "STP"
    assert order.totalQuantity == 100
    assert order.auxPrice == 145.0


def test_stop_order_buy():
    order = orders.stop_order("BUY", 50, 155.0)
    assert order.action == "BUY"
    assert order.orderType == "STP"
    assert order.auxPrice == 155.0


def test_bracket_order_structure():
    parent_id = 1000
    parent, stop, target = orders.bracket_order(
        parent_id, "BUY", 100, 150.0, 145.0, 160.0
    )

    # Parent (entry)
    assert parent.orderType == "LMT"
    assert parent.action == "BUY"
    assert parent.totalQuantity == 100
    assert parent.lmtPrice == 150.0
    assert parent.transmit is False

    # Stop child — D26.1: protective legs trade OPPOSITE the entry side.
    # A same-side stop would add to the position instead of protecting it.
    assert stop.orderType == "STP"
    assert stop.action == "SELL"
    assert stop.totalQuantity == 100
    assert stop.auxPrice == 145.0
    assert stop.parentId == parent_id
    assert stop.ocaGroup == f"bracket-{parent_id}"
    assert stop.ocaType == 1
    assert stop.transmit is False

    # Target child — opposite side of the BUY entry.
    assert target.orderType == "LMT"
    assert target.action == "SELL"
    assert target.totalQuantity == 100
    assert target.lmtPrice == 160.0
    assert target.parentId == parent_id
    assert target.ocaGroup == f"bracket-{parent_id}"
    assert target.ocaType == 1
    assert target.transmit is True


def test_bracket_order_sell():
    parent_id = 1001
    parent, stop, target = orders.bracket_order(
        parent_id, "SELL", 200, 150.0, 155.0, 145.0
    )
    assert parent.action == "SELL"
    assert parent.lmtPrice == 150.0
    # D26.1: SELL entry → protective children are BUY.
    assert stop.action == "BUY"
    assert stop.auxPrice == 155.0
    assert target.action == "BUY"
    assert target.lmtPrice == 145.0
    assert target.transmit is True


def test_bracket_order_all_transmit_false_except_last():
    """Only the target child has transmit=True."""
    parent_id = 1002
    parent, stop, target = orders.bracket_order(
        parent_id, "BUY", 100, 150.0, 145.0, 160.0
    )
    assert parent.transmit is False
    assert stop.transmit is False
    assert target.transmit is True


# ── Registry tests ─────────────────────────────────────────────

def test_register_and_get():
    registry = Orders()
    uo = UserOrder(order_id=1, symbol="AAPL", action="BUY", total_qty=100, order_type="MKT")
    registry.register(uo)
    assert registry.get(1) is uo


def test_get_missing():
    registry = Orders()
    assert registry.get(999) is None


def test_update_status():
    registry = Orders()
    uo = UserOrder(order_id=1, symbol="AAPL", action="BUY", total_qty=100, order_type="MKT")
    registry.register(uo)
    registry.update_status(1, "Submitted")
    assert registry.get(1).status == "Submitted"


def test_clear_filled():
    registry = Orders()
    uo = UserOrder(order_id=1, symbol="AAPL", action="BUY", total_qty=100, order_type="MKT")
    registry.register(uo)
    registry.clear_filled(1)
    assert registry.get(1) is None


def test_all():
    registry = Orders()
    uo1 = UserOrder(order_id=1, symbol="AAPL", action="BUY", total_qty=100, order_type="MKT")
    uo2 = UserOrder(order_id=2, symbol="TSLA", action="SELL", total_qty=50, order_type="LMT", lmt_price=200.0)
    registry.register(uo1)
    registry.register(uo2)
    all_orders = registry.all()
    assert len(all_orders) == 2
    assert 1 in all_orders and 2 in all_orders


# ── Global singleton access ────────────────────────────────────

def test_global_singleton():
    """The global orders singleton should be accessible."""
    assert hasattr(orders, "market_order")
    assert hasattr(orders, "limit_order")
    assert hasattr(orders, "stop_order")
    assert hasattr(orders, "bracket_order")
    assert hasattr(orders, "register")
    assert hasattr(orders, "get")
    assert hasattr(orders, "update_status")
    assert hasattr(orders, "clear_filled")


# ── UserOrder dataclass ────────────────────────────────────────

def test_user_order_defaults():
    uo = UserOrder(order_id=1, symbol="AAPL", action="BUY", total_qty=100, order_type="MKT")
    assert uo.status == ""
    assert uo.parent_id == 0
    assert uo.oca_group == ""
    assert uo.transmit is True
    assert uo.lmt_price is None
    assert uo.aux_price is None


def test_user_order_fields():
    uo = UserOrder(
        order_id=1, symbol="AAPL", action="BUY", total_qty=100,
        order_type="LMT", lmt_price=150.25, status="Submitted",
        transmit=False,
    )
    assert uo.order_id == 1
    assert uo.symbol == "AAPL"
    assert uo.action == "BUY"
    assert uo.total_qty == 100
    assert uo.order_type == "LMT"
    assert uo.lmt_price == 150.25
    assert uo.status == "Submitted"
    assert uo.transmit is False
