from ibkr.pacing import PacingExceeded, pacing_manager
from ibkr.id_manager import id_manager
from ibapi.contract import Contract
from datetime import datetime, timezone

# Map timeframe strings to IBKR duration and bar-size strings
TIMEFRAME_CONFIG = {
    "1 min":  {"duration": "1 D",  "bar_size": "1 min"},
    "5 mins": {"duration": "5 D",  "bar_size": "5 mins"},
    "15 mins":{"duration": "5 D",  "bar_size": "15 mins"},
    "1 hour": {"duration": "10 D", "bar_size": "1 hour"},
    "4 hours":{"duration": "30 D", "bar_size": "4 hours"},
    "1 day":  {"duration": "1 Y",  "bar_size": "1 day"},
}

class MarketDataManager:
    def __init__(self, client):
        self.client = client

    def req_historical_data(
        self,
        contract: Contract,
        timeframe: str = "5 mins",
        endDateTime: str = "",
        whatToShow: str = "TRADES",
        useRTH: int = 1,
        extended_hours: bool = False,
        bar_size: str | None = None,
        duration: str | None = None,
    ) -> int:
        """
        Request historical bars for a contract.
        Uses the TIMEFRAME_CONFIG to automatically set duration and bar size.
        Returns the reqId so the caller can correlate incoming bars.

        Args:
            extended_hours: If True, fetch pre/post-market data (useRTH=0)
            bar_size: override the config bar size (D27.9: "5 secs" priming)
            duration: override the config duration (D27.9: current period span)
        """
        cfg = TIMEFRAME_CONFIG.get(timeframe, TIMEFRAME_CONFIG["5 mins"])
        req_id = id_manager.get_id()
        # D28.3: rolling 600s historical window, non-blocking. Never sleeps:
        # when the budget is exhausted the caller defers (the backfill wave
        # caps chunks and continues via singleShot; see TickerSession).
        wait = pacing_manager.historical_wait_seconds()
        if wait > 0:
            raise PacingExceeded(wait)
        # Extended hours overrides useRTH
        effective_useRTH = 0 if extended_hours else useRTH
        self.client.reqHistoricalData(
            req_id,
            contract,
            endDateTime,          # "" = up to now
            duration if duration is not None else cfg["duration"],
            bar_size if bar_size is not None else cfg["bar_size"],
            whatToShow,
            effective_useRTH,
            2,                    # formatDate=2 → unix timestamp
            False,
            []
        )
        # Record only after the request was actually issued (D28.3).
        pacing_manager.record_historical_slot()
        return req_id

    def req_mkt_data(self, contract: Contract, generic_ticks: str = "") -> int:
        """Subscribe to live tick data for a contract. Returns reqId.

        generic_ticks: comma-joined generic tick list for the S0 substrate
        (D37), e.g. "225" (auction) — "" preserves the legacy plain tick
        subscription used by the watchlist.
        """
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMktData(req_id, contract, generic_ticks, False, False,
                               [])
        return req_id

    def cancel_mkt_data(self, req_id: int | None):
        if req_id is None:
            return
        try:
            self.client.cancelMktData(req_id)
        except Exception:
            pass

    def req_contract_details(self, contract: Contract) -> int:
        """Request contract details for a contract. Returns the reqId."""
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqContractDetails(req_id, contract)
        return req_id

    def req_matching_symbols(self, pattern: str) -> int:
        """D39.1: debounced symbol search. Returns the reqId.

        ``reqMatchingSymbols`` answers with ``symbolSamples`` (≤16
        ContractDescriptions). Paced like any other request — the
        debounce in SymbolSearchService keeps the rate at ≤1 per ~300ms
        of typing.
        """
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMatchingSymbols(req_id, pattern)
        return req_id

    def cancel_contract_details(self, req_id: int | None):
        """Best-effort, capability-guarded cancel of a contract-details request.

        Three facts motivate the shape of this method:

        (a) The pinned ``ibapi`` API surface exposes **no**
            ``EClient.cancelContractDetails`` on the wire client, so a bare
            attribute access would raise ``AttributeError``. We therefore
            resolve the method via
            ``getattr(self.client, 'cancelContractDetails', None)`` and invoke
            it only when the capability is actually present. This absence is a
            property of the pinned API, not of any one version string: it was
            verified on both ``9.81.1.post1`` and the current pin ``10.51.1``,
            and no single version is load-bearing here.
        (b) The wire-side ``reqContractDetails`` request is normally ended by
            TWS's own ``contractDetailsEnd`` callback (or an error message), so
            there is nothing reliable to cancel from this side anyway.
        (c) The real safety net for stale requests is
            ``ContractLookupService``'s local invalidation — a bounded QTimer
            plus ``cancel_all`` on disconnect — which guarantees a late (or
            absent) response cannot leak into the UI.

        The call stays inside the containment (``try/except Exception: pass``)
        so that a present-but-raising implementation is swallowed as well.
        """
        if req_id is None:
            return
        cancel = getattr(self.client, "cancelContractDetails", None)
        if cancel is None:
            return
        try:
            cancel(req_id)
        except Exception:
            pass

    def cancel_historical_data(self, req_id: int | None):
        if req_id is None:
            return
        try:
            self.client.cancelHistoricalData(req_id)
        except Exception:
            pass
