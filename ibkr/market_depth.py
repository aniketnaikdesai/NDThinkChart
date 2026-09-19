"""MarketDepthManager: subscribes/cancels Level I/II depth per symbol.

Routes updateMktDepth callbacks into per-request OrderBook instances and lets
the UI pull snapshots for the ladder/book views.
"""

from ibkr.order_book import OrderBook
from ibkr.pacing import pacing_manager
from ibkr.id_manager import id_manager


class MarketDepthManager:
    def __init__(self, client):
        self.client = client
        self._req_to_symbol: dict[int, str] = {}
        self._books: dict[int, OrderBook] = {}

    def subscribe(self, symbol: str, contract, num_levels: int = 10) -> int:
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMktDepth(req_id, contract, num_levels, False, [])
        self._req_to_symbol[req_id] = symbol
        self._books[req_id] = OrderBook()
        return req_id

    def cancel(self, req_id: int | None) -> None:
        if req_id is None:
            return
        if req_id in self._books:
            try:
                self.client.cancelMktDepth(req_id)
            except Exception:
                pass
            self._books.pop(req_id, None)
            self._req_to_symbol.pop(req_id, None)

    def cancel_all(self) -> None:
        for req_id in list(self._books):
            self.cancel(req_id)

    def has_subscription(self, req_id: int | None) -> bool:
        return req_id is not None and req_id in self._books

    def on_update(self, req_id: int, position: int, operation: int,
                  side: int, price: float, size: int) -> str | None:
        """Apply an updateMktDepth bookmark; returns the symbol if known."""
        book = self._books.get(req_id)
        if book is None:
            return None
        book.apply(operation, side, position, price, size)
        return self._req_to_symbol.get(req_id)

    def snapshot(self, req_id: int, num_levels: int = 10) -> dict:
        book = self._books.get(req_id)
        if book is None:
            return {"symbol": "", "asks": [], "bids": [], "top": {}}
        asks = [{"price": l.price, "size": l.size} for l in book.ask_levels()[:num_levels]]
        bids = [{"price": l.price, "size": l.size} for l in book.bid_levels()[:num_levels]]
        return {
            "symbol": self._req_to_symbol.get(req_id, ""),
            "asks": asks,
            "bids": bids,
            "top": book.top_of_book(),
        }