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
        # D37 heatmap: refcounted SMART depth feeds, one reqMktDepth per
        # symbol regardless of holder count. Kept separate from _books so
        # the DOM's cancel_all() can never nuke session heatmap feeds.
        self._shared: dict[str, tuple[int, int]] = {}  # symbol -> (req_id, holders)

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

    # ── D37 heatmap: refcounted SMART feeds ───────────────────────────

    def subscribe_shared(self, symbol: str, contract,
                         num_levels: int = 10) -> int:
        """Refcounted SMART depth feed for heatmap sessions.

        One reqMktDepth per symbol regardless of holder count (main chart +
        pop-outs share). SMART aggregation per the D37 requirements. The
        DOM's private feed (subscribe/cancel_all) is untouched.
        """
        existing = self._shared.get(symbol)
        if existing is not None:
            req_id, holders = existing
            self._shared[symbol] = (req_id, holders + 1)
            return req_id
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMktDepth(req_id, contract, num_levels, True, [])
        self._shared[symbol] = (req_id, 1)
        return req_id

    def release_shared(self, symbol: str) -> None:
        """Release one hold on a shared feed; cancel at zero holders."""
        existing = self._shared.pop(symbol, None)
        if existing is None:
            return
        req_id, holders = existing
        if holders > 1:
            self._shared[symbol] = (req_id, holders - 1)
            return
        try:
            self.client.cancelMktDepth(req_id)
        except Exception:
            pass

    def shared_req_id(self, symbol: str) -> int | None:
        existing = self._shared.get(symbol)
        return existing[0] if existing is not None else None

    def resubscribe_shared(self, symbol: str, contract,
                           num_levels: int = 10) -> int:
        """D27 replay: force a fresh reqMktDepth, preserving holder count.

        (subscribe_shared would return the dead req_id on a refcount hit —
        replay needs a new wire subscription.)
        """
        old = self._shared.pop(symbol, None)
        holders = old[1] if old is not None else 1
        if old is not None:
            try:
                self.client.cancelMktDepth(old[0])
            except Exception:
                pass
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMktDepth(req_id, contract, num_levels, True, [])
        self._shared[symbol] = (req_id, holders)
        return req_id

    def active_feed_count(self) -> int:
        """Live depth feeds (shared heatmap + DOM-private) — 37.4 budget."""
        return len(self._shared) + len(self._books)

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