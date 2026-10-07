"""Bounded, exactly-once IBKR contract-details lookup correlation (D22 Phase 2).

``reqContractDetails`` is asynchronous and, on some paths, never answers at all
(a bad symbol can leave a request open). This service owns the pending map that
turns the bridge's raw callbacks back into a single, correlated, *bounded*
result per request:

    request(symbol, contract) -> reqId
        -> IBBridge.contract_details / contract_details_end / error_msg
        -> lookup_finished(reqId, symbol, ok, reason)   # exactly once

Resolution rules (design S4 / AC-D22.3.1 .. AC-D22.3.6):

* **ok=True** — at least one ``contract_details`` followed by
  ``contract_details_end`` for the reqId.
* **ok=False** — ``contract_details_end`` with zero preceding details, an
  ``error_msg`` correlated to a pending reqId, or the per-request
  ``QTimer(CONTRACT_LOOKUP_TIMEOUT_MS)`` expiring.
* **Exactly once** — the pending entry is dropped *before* the signal is
  emitted, so a late/duplicate event for a resolved reqId is ignored.
* **Unknown reqIds are ignored** — in particular ``error_msg`` only rejects a
  lookup whose reqId is still pending, so unrelated market-data errors (which
  share the same bridge signal) never resolve an add.
* **cancel(req_id) / cancel_all()** invalidate in-flight lookups without
  emitting anything; a later callback or timer for them is a no-op.

The service is injected with the ``MarketDataManager`` (to issue the paced
request and obtain the reqId) and the ``IBBridge`` (to receive callbacks). It
imports no Qt widgets, touches no TWS connection and opens no database, so it is
fully unit-testable with a fake bridge and a fake market-data manager.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

#: Upper bound on a single lookup (AC-D22.3.4 requirement "no indefinite hang").
CONTRACT_LOOKUP_TIMEOUT_MS = 5000

# Diagnostic reason strings carried on ``lookup_finished``.
REASON_OK = "ok"
REASON_NO_DETAILS = "no_contract_details"
REASON_ERROR = "error"
REASON_TIMEOUT = "timeout"

__all__ = [
    "CONTRACT_LOOKUP_TIMEOUT_MS",
    "REASON_OK",
    "REASON_NO_DETAILS",
    "REASON_ERROR",
    "REASON_TIMEOUT",
    "PendingLookup",
    "ContractLookupService",
]


@dataclass
class PendingLookup:
    """One in-flight ``reqContractDetails`` request.

    ``got_any`` flips to True on the first ``contract_details`` so that the
    ``contract_details_end`` handler can distinguish a real match (>= 1 detail)
    from a zero-detail rejection. ``timer`` is the single-shot bounded-wait timer
    armed at request time and disarmed on every resolution/cancellation.
    """

    symbol: str
    got_any: bool = False
    timer: Optional[QTimer] = field(default=None, repr=False)


class ContractLookupService(QObject):
    """Correlate ``reqContractDetails`` callbacks into one bounded result."""

    #: reqId, symbol, ok, reason
    lookup_finished = pyqtSignal(int, str, bool, str)

    def __init__(self, md_manager=None, bridge=None, parent=None):
        super().__init__(parent)
        self._md_manager = md_manager
        self._bridge = bridge
        self._pending: dict[int, PendingLookup] = {}

        if bridge is not None:
            bridge.contract_details.connect(self.on_contract_details)
            bridge.contract_details_end.connect(self.on_contract_details_end)
            bridge.error_msg.connect(self.on_error)

    # ------------------------------------------------------------------ API
    def request(self, symbol: str, contract) -> int:
        """Issue a contract-details request and register it as pending.

        The reqId is allocated by ``MarketDataManager.req_contract_details``
        (paced), then recorded ``{reqId: PendingLookup(symbol)}`` with a
        single-shot timeout timer armed. Returns the reqId so the caller can
        correlate the eventual ``lookup_finished``.
        """
        if self._md_manager is None:
            raise RuntimeError(
                "ContractLookupService.request requires an md_manager"
            )
        req_id = self._md_manager.req_contract_details(contract)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(CONTRACT_LOOKUP_TIMEOUT_MS)
        timer.timeout.connect(lambda rid=req_id: self.on_timeout(rid))
        self._pending[req_id] = PendingLookup(symbol=symbol, timer=timer)
        timer.start()
        return req_id

    def cancel(self, req_id: int) -> None:
        """Invalidate one in-flight lookup; emits nothing."""
        pending = self._pending.pop(req_id, None)
        if pending is None:
            return
        if pending.timer is not None:
            pending.timer.stop()

    def cancel_all(self) -> None:
        """Invalidate every in-flight lookup; emits nothing."""
        for req_id in list(self._pending):
            self.cancel(req_id)

    def is_pending(self, req_id: int) -> bool:
        """True while ``req_id`` is still awaiting resolution."""
        return req_id in self._pending

    def pending_lookup(self, req_id: int) -> Optional[PendingLookup]:
        """Read-only view of a pending entry (None once resolved/cancelled)."""
        return self._pending.get(req_id)

    def pending_count(self) -> int:
        return len(self._pending)

    # ------------------------------------------------------------- handlers
    def on_contract_details(self, req_id: int, details) -> None:
        """Record that at least one matching contract arrived (no resolution)."""
        pending = self._pending.get(req_id)
        if pending is None:
            return  # late / unknown reqId
        pending.got_any = True

    def on_contract_details_end(self, req_id: int) -> None:
        """Terminate a lookup: success iff >= 1 detail preceded the end."""
        pending = self._pending.get(req_id)
        if pending is None:
            return  # late / unknown reqId
        if pending.got_any:
            self._resolve(req_id, True, REASON_OK)
        else:
            self._resolve(req_id, False, REASON_NO_DETAILS)

    def on_error(self, req_id: int, code: int, msg: str) -> None:
        """Reject a lookup only when the errored reqId is still pending."""
        if self._pending.get(req_id) is None:
            return  # unrelated reqId — must not touch any pending lookup
        self._resolve(req_id, False, f"{REASON_ERROR} {code}: {msg}")

    def on_timeout(self, req_id: int) -> None:
        """Bounded-wait expiry for a still-pending lookup."""
        if self._pending.get(req_id) is None:
            return  # already resolved/cancelled
        self._resolve(req_id, False, REASON_TIMEOUT)

    # -------------------------------------------------------------- internal
    def _resolve(self, req_id: int, ok: bool, reason: str) -> None:
        """Drop the pending entry and emit exactly once (idempotent)."""
        pending = self._pending.pop(req_id, None)
        if pending is None:
            return
        if pending.timer is not None:
            pending.timer.stop()
        self.lookup_finished.emit(req_id, pending.symbol, ok, reason)
