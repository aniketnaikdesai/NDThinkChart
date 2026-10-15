"""
subscription_manager.py

Registry of live IBKR subscriptions (chart realtime bars, watchlist market
data) and their replay on reconnection (D27.3).

Each entry is keyed by reqId and carries a type tag plus the reissue/rebind
hooks the reconnect replay needs:

- ``reissue() -> new_req_id`` re-subscribes through the owning manager.
- ``rebind(new_req_id)`` points the live routing state (``_rt_req_id``,
  ``_req_to_row``) at the new reqId.

The API is deliberately session-agnostic (type-tagged entries keyed by
symbol); Phase 3b migrates ownership into ``TickerSession`` without changing
the mechanism.

Reconnect division of labour (D27.3): chart RT bars are re-issued here via
``replay_all``; watchlist market-data is re-issued by the existing
``_restore_watchlist`` clear+re-add path (pinned by AC-D22.7.2), so
``MainWindow._replay_subscriptions`` replays only the ``rt_bars`` type —
replaying ``market_data`` too would double-subscribe every row.
Watchlist entries are still registered (and unregistered on clear/remove)
so the registry is the single source of truth for what is live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from ibkr.pacing import pacing_manager, PacingExceeded

# Type tags for registry entries.
RT_BARS = "rt_bars"
MARKET_DATA = "market_data"
S0_TICKS = "s0_ticks"  # D37 substrate: per-session generic-tick reqMktData


@dataclass
class _Entry:
    symbol: str
    req_type: str
    reissue: Optional[Callable[[], int]] = None
    rebind: Optional[Callable[[int], None]] = None


class SubscriptionManager:
    """Registry of active IBKR subscriptions keyed by reqId."""

    def __init__(self):
        self._entries: dict[int, _Entry] = {}

    def subscribe(
        self,
        symbol: str,
        req_id: int,
        req_type: str = MARKET_DATA,
        *,
        reissue: Optional[Callable[[], int]] = None,
        rebind: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Record a live subscription with its type tag and replay hooks."""
        self._entries[req_id] = _Entry(
            symbol=symbol, req_type=req_type, reissue=reissue, rebind=rebind
        )

    def unsubscribe(self, req_id: int) -> None:
        """Drop one subscription by reqId (idempotent)."""
        self._entries.pop(req_id, None)

    def unsubscribe_all_of_type(self, req_type: str) -> None:
        """Drop every subscription with the given type tag."""
        for req_id in [
            rid for rid, e in self._entries.items() if e.req_type == req_type
        ]:
            del self._entries[req_id]

    def has_subscription(self, symbol: str, req_type: str | None = None) -> bool:
        """Check whether a live subscription exists for a symbol."""
        return any(
            e.symbol == symbol and (req_type is None or e.req_type == req_type)
            for e in self._entries.values()
        )

    def entries_of_type(self, req_type: str) -> list[tuple[int, str]]:
        """[(reqId, symbol)] for every entry with the given type tag."""
        return [
            (req_id, e.symbol)
            for req_id, e in self._entries.items()
            if e.req_type == req_type
        ]

    def replay_all(
        self, include_types: Optional[set[str]] = None
    ) -> list[tuple[int, int]]:
        """Re-issue registered subscriptions; rebind the new reqIds.

        Returns [(old_req_id, new_req_id)]. Only entries whose type is in
        ``include_types`` (default: all) and that carry a ``reissue`` hook are
        re-issued; each entry's ``rebind`` hook then points the live routing
        state at the new reqId, and the registry bookkeeping moves with it.

        D28.1: all-or-nothing under pacing pressure. Realtime-bar reissues
        consume pacing slots, so the budget for ALL of them is checked up
        front; if it is short, PacingExceeded is raised before anything is
        re-issued (a partial replay followed by a retry would double-subscribe
        the already-replayed entries). The caller defers via QTimer.singleShot.
        """
        pending = [
            (old_id, entry)
            for old_id, entry in list(self._entries.items())
            if (include_types is None or entry.req_type in include_types)
            and entry.reissue is not None
        ]
        rt_needed = sum(1 for _, e in pending if e.req_type == RT_BARS)
        wait = pacing_manager.realtime_wait_for_slots(rt_needed)
        if wait > 0:
            raise PacingExceeded(wait)
        replayed: list[tuple[int, int]] = []
        for old_id, entry in pending:
            new_id = entry.reissue()
            if entry.rebind is not None:
                entry.rebind(new_id)
            del self._entries[old_id]
            self._entries[new_id] = entry
            replayed.append((old_id, new_id))
        return replayed
