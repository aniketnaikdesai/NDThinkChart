"""Tests for DOM/Market Depth (Phase 4)."""

import pytest
from unittest.mock import MagicMock

from ibkr.order_book import apply_operation, OrderBook, Level, SIDE_ASK, SIDE_BID
from ibkr.market_depth import MarketDepthManager


# ── order_book.py ─────────────────────────────────────────────────

class TestApplyOperation:
    def test_insert_at_position_zero(self):
        rows = []
        result = apply_operation(rows, 0, 0, 100.0, 50)
        assert len(result) == 1
        assert result[0].price == 100.0
        assert result[0].size == 50
        assert result[0].position == 0

    def test_insert_at_position_one(self):
        rows = [Level(position=0, price=100.0, size=50)]
        result = apply_operation(rows, 0, 1, 101.0, 30)
        assert len(result) == 2
        assert result[0].price == 100.0
        assert result[1].price == 101.0
        assert result[1].position == 1

    def test_insert_renumbers_positions(self):
        rows = [
            Level(position=0, price=100.0, size=50),
            Level(position=1, price=101.0, size=30),
        ]
        result = apply_operation(rows, 0, 1, 100.5, 40)
        assert result[0].position == 0
        assert result[1].position == 1
        assert result[2].position == 2

    def test_update_existing(self):
        rows = [Level(position=0, price=100.0, size=50)]
        result = apply_operation(rows, 1, 0, 102.0, 55)
        assert result[0].price == 102.0
        assert result[0].size == 55

    def test_update_out_of_range_no_op(self):
        rows = [Level(position=0, price=100.0, size=50)]
        result = apply_operation(rows, 1, 5, 102.0, 55)
        assert len(result) == 1
        assert result[0].price == 100.0

    def test_delete_first(self):
        rows = [
            Level(position=0, price=100.0, size=50),
            Level(position=1, price=101.0, size=30),
        ]
        result = apply_operation(rows, 2, 0, 0, 0)
        assert len(result) == 1
        assert result[0].price == 101.0
        assert result[0].position == 0

    def test_delete_out_of_range_no_op(self):
        rows = [Level(position=0, price=100.0, size=50)]
        result = apply_operation(rows, 2, 5, 0, 0)
        assert len(result) == 1

    def test_delete_last(self):
        rows = [
            Level(position=0, price=100.0, size=50),
            Level(position=1, price=101.0, size=30),
        ]
        result = apply_operation(rows, 2, 1, 0, 0)
        assert len(result) == 1
        assert result[0].price == 100.0


class TestOrderBook:
    def test_apply_ask(self):
        book = OrderBook()
        book.apply(0, SIDE_ASK, 0, 100.0, 50)
        asks = book.ask_levels()
        assert len(asks) == 1
        assert asks[0].price == 100.0
        assert asks[0].size == 50

    def test_apply_bid(self):
        book = OrderBook()
        book.apply(0, SIDE_BID, 0, 99.0, 30)
        bids = book.bid_levels()
        assert len(bids) == 1
        assert bids[0].price == 99.0

    def test_delete_maintains_order(self):
        book = OrderBook()
        book.apply(0, SIDE_BID, 0, 99.0, 30)
        book.apply(0, SIDE_BID, 1, 98.0, 20)
        book.apply(2, SIDE_BID, 0, 0, 0)
        bids = book.bid_levels()
        assert len(bids) == 1
        assert bids[0].price == 98.0
        assert bids[0].position == 0

    def test_best_ask_empty(self):
        book = OrderBook()
        assert book.best_ask() is None

    def test_best_bid_empty(self):
        book = OrderBook()
        assert book.best_bid() is None

    def test_top_of_book(self):
        book = OrderBook()
        book.apply(0, SIDE_ASK, 0, 100.0, 50)
        book.apply(0, SIDE_BID, 0, 99.0, 30)
        top = book.top_of_book()
        assert top["bestAsk"] == 100.0
        assert top["bestBid"] == 99.0
        assert top["askSize"] == 50
        assert top["bidSize"] == 30


# ── MarketDepthManager ────────────────────────────────────────────

class TestMarketDepthManager:
    def test_subscribe_returns_req_id(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        req_id = mgr.subscribe("AAPL", MagicMock(), num_levels=10)
        assert isinstance(req_id, int)
        assert req_id in mgr._books
        assert req_id in mgr._req_to_symbol
        assert mgr._req_to_symbol[req_id] == "AAPL"
        client.reqMktDepth.assert_called_once()

    def test_subscribe_uses_throttle(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        mgr.subscribe("AAPL", MagicMock())
        client.reqMktDepth.assert_called_once()

    def test_cancel(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        req_id = mgr.subscribe("AAPL", MagicMock())
        mgr.cancel(req_id)
        assert req_id not in mgr._books
        assert req_id not in mgr._req_to_symbol
        client.cancelMktDepth.assert_called_once()

    def test_cancel_none(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        mgr.cancel(None)
        client.cancelMktDepth.assert_not_called()

    def test_cancel_all(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        id1 = mgr.subscribe("AAPL", MagicMock())
        id2 = mgr.subscribe("TSLA", MagicMock())
        mgr.cancel_all()
        assert len(mgr._books) == 0
        assert client.cancelMktDepth.call_count == 2

    def test_has_subscription(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        req_id = mgr.subscribe("AAPL", MagicMock())
        assert mgr.has_subscription(req_id) is True
        assert mgr.has_subscription(None) is False
        assert mgr.has_subscription(9999) is False

    def test_on_update_unknown_req_id(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        result = mgr.on_update(999, 0, 0, 0, 100.0, 50)
        assert result is None

    def test_snapshot_no_book(self):
        client = MagicMock()
        mgr = MarketDepthManager(client)
        snap = mgr.snapshot(999)
        assert snap == {"symbol": "", "asks": [], "bids": [], "top": {}}
