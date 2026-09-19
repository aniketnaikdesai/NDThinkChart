"""
subscription_manager.py
Manages a registry of IBKR subscriptions (watchlist, chart realtime bars, depth)
and handles replay on reconnection.
"""

from collections import defaultdict
from typing import Optional


class SubscriptionManager:
    """Registry of active IBKR subscriptions keyed by symbol/timeframe."""

    def __init__(self):
        # symbol -> set of reqIds
        self._subscriptions: dict[str, set[int]] = defaultdict(set)
        # reqId -> (symbol, req_type) mapping for replay
        self._req_to_info: dict[int, tuple[str, str]] = {}

    def subscribe(self, symbol: str, req_id: int, req_type: str = "market_data") -> None:
        """Record a new subscription."""
        self._subscriptions[symbol].add(req_id)
        self._req_to_info[req_id] = (symbol, req_type)

    def unsubscribe(self, symbol: str, req_id: int) -> None:
        """Remove a subscription."""
        self._subscriptions[symbol].discard(req_id)
        self._req_to_info.pop(req_id, None)

    def unsubscribe_all_for_symbol(self, symbol: str) -> None:
        """Remove all subscriptions for a given symbol."""
        req_ids = self._subscriptions.pop(symbol, None)
        if req_ids:
            for req_id in req_ids:
                self._req_to_info.pop(req_id, None)

    def get_req_ids(self, symbol: str) -> set[int]:
        """Return all reqIds associated with a symbol."""
        return self._subscriptions.get(symbol, set())

    def has_subscription(self, symbol: str) -> bool:
        """Check if any subscription exists for a symbol."""
        return bool(self._subscriptions.get(symbol))

    def replay_all(self, client, subscribe_fn) -> None:
        """Replay all active subscriptions via the provided subscribe function."""
        for symbol, req_ids in list(self._subscriptions.items()):
            for req_id in req_ids:
                subscribe_fn(symbol, req_id)
            # Clear and re-subscribe (idempotent)
            self._subscriptions[symbol].clear()
            self._req_to_info.pop(symbol, None)