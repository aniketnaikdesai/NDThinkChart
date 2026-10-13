"""Debounced IBKR symbol search (D39.1).

``reqMatchingSymbols(pattern)`` answers with ``symbolSamples`` — up to 16
``ContractDescription`` objects (``.contract`` + ``.derivativeSecTypes``;
note: no company name at this stage — the full details resolve on
selection via ``reqContractDetails``).

The service owns the debounce (≤1 request per ``debounce_ms`` of typing)
and the in-flight correlation map, mirroring ``ContractLookupService``:

    type_ahead(text)          # every keystroke; restarts the debounce timer
        -> md_manager.req_matching_symbols(pattern)
        -> IBBridge.symbol_samples / error_msg
        -> search_finished(reqId, pattern, ok, samples|reason)  # exactly once

Resolution rules:

* **ok=True** — ``symbolSamples`` for a pending reqId (capped at 16).
* **ok=False** — ``error_msg`` correlated to a pending reqId, or the
  per-request timeout expiring.
* **Exactly once** — the pending entry is dropped before the signal is
  emitted; late/duplicate events for a resolved reqId are ignored.
* **Disconnected** — ``set_connected(False)`` drops in-flight requests and
  stops the debounce; a ``type_ahead`` while disconnected resolves
  immediately with ``ok=False, reason="disconnected"`` (the panel also
  disables the box — this is the backstop).
* Empty pattern → no request and no emission (the panel clears locally).
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

#: Debounce window — at most one request per window of typing (AC-D39.2).
DEBOUNCE_MS = 300
#: Upper bound on a single search (AC-D39.1 "no indefinite hang").
SEARCH_TIMEOUT_MS = 5000
#: IBKR caps symbolSamples at 16; enforced defensively as well.
MAX_SAMPLES = 16

REASON_ERROR = "error"
REASON_TIMEOUT = "timeout"
REASON_DISCONNECTED = "disconnected"

__all__ = [
    "DEBOUNCE_MS",
    "SEARCH_TIMEOUT_MS",
    "MAX_SAMPLES",
    "SymbolSearchService",
]


class SymbolSearchService(QObject):
    """Debounce + correlate ``reqMatchingSymbols`` searches."""

    #: reqId, pattern, ok, samples (list) on ok / reason (str) on failure.
    #: Synthetic resolutions (disconnected) use reqId 0.
    search_finished = pyqtSignal(int, str, bool, object)

    def __init__(self, md_manager=None, bridge=None, debounce_ms: int = DEBOUNCE_MS,
                 parent=None):
        super().__init__(parent)
        self._md_manager = md_manager
        self._bridge = bridge
        self._pending: dict[int, str] = {}  # reqId -> pattern
        self._connected = True

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self._fire)
        self._staged = ""

        if bridge is not None:
            bridge.symbol_samples.connect(self.on_symbol_samples)
            bridge.error_msg.connect(self.on_error)

    # ------------------------------------------------------------------ API
    def set_connected(self, connected: bool) -> None:
        """Transport state — drops in-flight searches when disconnected."""
        self._connected = bool(connected)
        if not self._connected:
            self.cancel_all()

    def type_ahead(self, text: str) -> None:
        """Register one keystroke; restarts the debounce window."""
        pattern = (text or "").strip()
        if not self._connected:
            self.search_finished.emit(0, pattern, False, REASON_DISCONNECTED)
            return
        if not pattern:
            # Cleared: stop any staged keystroke; the panel already hid the
            # popup locally. No request, no emission.
            self._debounce.stop()
            self._staged = ""
            return
        self._staged = pattern
        self._debounce.start()  # restart — one request per window of typing

    def cancel_all(self) -> None:
        """Invalidate in-flight searches and the staged keystroke."""
        self._debounce.stop()
        self._staged = ""
        self._pending.clear()

    def pending_count(self) -> int:
        return len(self._pending)

    # ------------------------------------------------------------- handlers
    def on_symbol_samples(self, req_id: int, descriptions) -> None:
        """Resolve a search: ok with ≤16 samples."""
        pattern = self._pending.pop(req_id, None)
        if pattern is None:
            return  # late / unknown reqId
        samples = list(descriptions or [])[:MAX_SAMPLES]
        self.search_finished.emit(req_id, pattern, True, samples)

    def on_error(self, req_id: int, code: int, msg: str) -> None:
        """Reject a search only when the errored reqId is still pending."""
        if self._pending.get(req_id) is None:
            return  # unrelated reqId — must not touch any pending search
        pattern = self._pending.pop(req_id)
        self.search_finished.emit(
            req_id, pattern, False, f"{REASON_ERROR} {code}: {msg}")

    def on_timeout(self, req_id: int) -> None:
        """Bounded-wait expiry for a still-pending search."""
        pattern = self._pending.pop(req_id, None)
        if pattern is None:
            return  # already resolved/cancelled
        self.search_finished.emit(req_id, pattern, False, REASON_TIMEOUT)

    # -------------------------------------------------------------- internal
    def _fire(self) -> None:
        """Debounce expiry — issue the staged search exactly once."""
        pattern = self._staged
        self._staged = ""
        if not pattern or self._md_manager is None:
            return
        if not self._connected:
            self.search_finished.emit(0, pattern, False, REASON_DISCONNECTED)
            return
        req_id = self._md_manager.req_matching_symbols(pattern)
        self._pending[req_id] = pattern
        QTimer.singleShot(
            SEARCH_TIMEOUT_MS, lambda rid=req_id: self.on_timeout(rid))
