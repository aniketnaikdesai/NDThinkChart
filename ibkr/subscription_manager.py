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
``MainWindow._replay_subscriptions`` replays the ``rt_bars``, ``s0_ticks``
and ``option_legs`` tags but never ``market_data`` — replaying that too
would double-subscribe every row.
Watchlist entries are still registered (and unregistered on clear/remove)
so the registry is the single source of truth for what is live.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from ibkr.pacing import pacing_manager, PacingExceeded

_LOG = logging.getLogger(__name__)

# Type tags for registry entries.
RT_BARS = "rt_bars"
MARKET_DATA = "market_data"
S0_TICKS = "s0_ticks"  # D37 substrate: per-session generic-tick reqMktData
#: D65: the Option Spreads panel's per-leg lines (and its single spot line).
#: Excluded from the watchlist's MARKET_DATA tag so ``_replay_subscriptions``
#: can re-issue option legs without replaying the AC-D22.7.2 watchlist path.
OPTION_LEGS = "option_legs"


@dataclass
class _Entry:
    symbol: str
    req_type: str
    reissue: Optional[Callable[[], int]] = None
    rebind: Optional[Callable[[int], None]] = None


class SubscriptionManager:
    """Registry of active IBKR subscriptions keyed by reqId (D27.3, D71).

    ``replay_all`` is one transaction over the union of every pacing budget
    a reconnect pass will spend: realtime-bar slots for ``RT_BARS`` entries
    and the generic minimum-interval gate for every other pending entry
    (whose reissue goes through ``reqMktData``). If either is short, one
    ``PacingExceeded`` is raised before anything is re-issued or mutated.
    The coupling is deliberate (DG131): one throttled option leg defers the
    chart's RT lines too, because a pass that reissues some entries and
    defers the rest is exactly the partial replay this transaction exists
    to prevent — a split pass must never be used to "fix" the coupling.

    Every send happens inside one ``PacingManager.generic_batch``
    reservation; only after the last reissue returns are entries rebound,
    their superseded reqIds retired through ``set_cancel_hook`` resolvers,
    and the registry keys moved. A raise during the reissue phase retires
    the new ids, rebinds every entry to its old id and re-raises, leaving
    the registry and every old live line exactly as they were.
    """

    def __init__(self):
        self._entries: dict[int, _Entry] = {}
        # P26/D71: one retire resolver per replayed type, installed once by
        # the window. A type without a resolver retires nothing (the replay
        # still moves its registry key; the owning manager remains the only
        # process allowed to invent a cancel path).
        self._cancel_hooks: dict[str, Callable[[int], None]] = {}

    def set_cancel_hook(self, req_type: str, fn: Callable[[int], None]) -> None:
        """Install the replay's retire resolver for one subscription type.

        ``replay_all`` calls the hook with the superseded reqId after every
        reissue has succeeded, so a cancelled line can never outlive its
        replacement. Best-effort at the call site: a raising hook is logged
        and the pass continues.
        """
        self._cancel_hooks[req_type] = fn

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
        """Re-issue registered subscriptions as one all-or-nothing pass.

        Returns ``[(old_req_id, new_req_id)]``. Only entries whose type is in
        ``include_types`` (default: all) and that carry a ``reissue`` hook are
        re-issued, in registry (registration) order.

        Three phases, no mutation before phase three:

        1. **Union pre-check.** ``rt_n`` is the ``RT_BARS`` count and
           ``generic_n`` every other pending entry (S0 ticks and option legs
           reissue through ``reqMktData``'s minimum-interval gate). One
           ``PacingExceeded(max(rt_wait, generic_wait))`` covers both budgets
           and is raised before any reissue or registry change.
        2. **Reissue phase.** Every entry's ``reissue()`` runs inside one
           ``generic_batch(generic_n)`` reservation. If any call raises,
           every reqId issued so far is retired through its type's resolver,
           every entry's routing is rebound to its old reqId, and the
           exception re-raises: the registry is byte-identical to its
           pre-pass state and no old line was cancelled.
        3. **Retire phase.** Each entry is rebound to its new reqId, its
           superseded old reqId is retired through ``set_cancel_hook``'s
           resolver for its type (best-effort, logged; a type with no
           resolver retires nothing), and the registry key moves last.

        D28.1: never sleeps — the batch is bookkeeping, and the caller defers
        the whole pass via ``QTimer.singleShot`` when the union gate refuses.
        """
        pending = [
            (old_id, entry)
            for old_id, entry in list(self._entries.items())
            if (include_types is None or entry.req_type in include_types)
            and entry.reissue is not None
        ]
        rt_n = sum(1 for _, e in pending if e.req_type == RT_BARS)
        generic_n = len(pending) - rt_n
        wait = max(
            pacing_manager.realtime_wait_for_slots(rt_n),
            pacing_manager.generic_wait_for_batch(generic_n),
        )
        if wait > 0:
            raise PacingExceeded(wait)

        issued: list[tuple[int, _Entry, int]] = []
        try:
            with pacing_manager.generic_batch(generic_n):
                for old_id, entry in pending:
                    new_id = entry.reissue()
                    issued.append((old_id, entry, new_id))
        except BaseException:
            # Phase 2 failed: retire only what this pass issued, then put
            # every entry's routing back on its pre-pass reqId. The registry
            # was never touched and no old line was cancelled.
            for _old_id, entry, new_id in issued:
                self._retire(entry.req_type, new_id)
            for old_id, entry in pending:
                if entry.rebind is not None:
                    try:
                        entry.rebind(old_id)
                    except Exception:  # best-effort unwind
                        _LOG.warning(
                            "replay unwind: rebind to %s failed for %s",
                            old_id, entry.req_type, exc_info=True,
                        )
            raise

        replayed: list[tuple[int, int]] = []
        for old_id, entry, new_id in issued:
            if entry.rebind is not None:
                entry.rebind(new_id)
            self._retire(entry.req_type, old_id)
            del self._entries[old_id]
            self._entries[new_id] = entry
            replayed.append((old_id, new_id))
        return replayed

    def _retire(self, req_type: str, req_id: int) -> None:
        """Retire one superseded reqId through its type's resolver."""
        hook = self._cancel_hooks.get(req_type)
        if hook is None:
            return
        try:
            hook(req_id)
        except Exception:  # best-effort: the pass must still settle
            _LOG.warning(
                "replay: retire of %s reqId %s failed", req_type, req_id,
                exc_info=True,
            )
