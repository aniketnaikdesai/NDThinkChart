"""Tests for ibkr/account.py — pure account model helpers."""

import pytest

from ibkr.account import Account, Position, build_position_from_ib, _parse_contract_type


class TestParseContractType:
    def test_uppercase(self):
        assert _parse_contract_type("STOCK") == "stock"

    def test_lowercase(self):
        assert _parse_contract_type("option") == "option"

    def test_mixed(self):
        assert _parse_contract_type("FuTUrE") == "future"

    def test_whitespace(self):
        assert _parse_contract_type("  stock  ") == "stock"


class TestBuildPositionFromIB:
    def test_stock_position(self):
        pos = build_position_from_ib(
            symbol="AAPL",
            account="DU12345",
            con_id=12345,
            contract_type="STOCK",
            local_symbol="AAPL",
            multiplier=1.0,
            expiry=None,
            strike=None,
            right=None,
            avg_cost=150.25,
            qty=100,
            stop_loss=None,
            take_profit=None,
        )
        assert pos.symbol == "AAPL"
        assert pos.account == "DU12345"
        assert pos.con_id == 12345
        assert pos.contract_type == "stock"
        assert pos.qty == 100
        assert pos.avg_cost == 150.25
        assert pos.multiplier == 1.0
        assert pos.right is None
        assert pos.expiry is None

    def test_option_position(self):
        pos = build_position_from_ib(
            symbol="AAPL",
            account="DU12345",
            con_id=99999,
            contract_type="OPTION",
            local_symbol="AAPL 240119C00150000",
            multiplier=100.0,
            expiry="20240119",
            strike=150.0,
            right="C",
            avg_cost=2.50,
            qty=2,
            stop_loss=None,
            take_profit=None,
        )
        assert pos.contract_type == "option"
        assert pos.right == "C"
        assert pos.strike == 150.0
        assert pos.expiry == "20240119"
        assert pos.multiplier == 100.0
        assert pos.qty == 2

    def test_short_position(self):
        pos = build_position_from_ib(
            symbol="AAPL",
            account="DU12345",
            con_id=1,
            contract_type="stock",
            local_symbol="AAPL",
            multiplier=1.0,
            expiry=None,
            strike=None,
            right=None,
            avg_cost=150.0,
            qty=-50,
            stop_loss=None,
            take_profit=None,
        )
        assert pos.qty == -50  # signed short

    def test_defaults(self):
        pos = build_position_from_ib(
            symbol="TSLA",
            account="DU12345",
            con_id=None,
            contract_type="stock",
            local_symbol="TSLA",
            multiplier=1.0,
            expiry=None,
            strike=None,
            right=None,
            avg_cost=200.0,
            qty=10,
            stop_loss=None,
            take_profit=None,
        )
        assert pos.con_id is None
        assert pos.trade_group_id is None
        assert pos.stop_loss is None
        assert pos.take_profit is None
        assert pos.market_price == 0.0


class TestAccountDataclass:
    def test_basic(self):
        acc = Account(account="DU12345", tag="NetLiquidation", value="100000", currency="USD")
        assert acc.account == "DU12345"
        assert acc.tag == "NetLiquidation"
        assert acc.value == "100000"
        assert acc.currency == "USD"

    def test_default_currency(self):
        acc = Account(account="DU12345", tag="NetLiquidation", value="100000")
        assert acc.currency == ""