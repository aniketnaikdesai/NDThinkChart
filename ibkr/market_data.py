from ibkr.error_codes import IBKRNotReady, require_api_ready
from ibkr.pacing import PacingExceeded, pacing_manager
from ibkr.id_manager import id_manager
from ibapi.contract import Contract
from datetime import datetime, timezone

__all__ = ["IBKRNotReady", "MarketDataManager", "TIMEFRAME_CONFIG"]

# Map timeframe strings to IBKR duration and bar-size strings
TIMEFRAME_CONFIG = {
    "1 min":  {"duration": "30 D",  "bar_size": "1 min"},
    "5 mins": {"duration": "30 D", "bar_size": "5 mins"},
    "15 mins":{"duration": "30 D", "bar_size": "15 mins"},
    "30 mins":{"duration": "30 D", "bar_size": "30 mins"},
    "1 hour": {"duration": "60 D", "bar_size": "1 hour"},
    "4 hours":{"duration": "60 D", "bar_size": "4 hours"},
    "1 day":  {"duration": "1 Y",  "bar_size": "1 day"},
    "1 week": {"duration": "2 Y",  "bar_size": "1 week"},
    "1 month": {"duration": "10 Y", "bar_size": "1 month"},
}

class MarketDataManager:
    def __init__(self, client):
        self.client = client

    def _require_api_ready(self) -> None:
        """Raise IBKRNotReady when the TWS handshake hasn't completed.

        Checked BEFORE allocating a reqId or touching pacing so nothing
        is sent (or budgeted) pre-handshake — TWS rejects such requests
        with 504.

        The one seam; the realtime manager calls the same function.
        """
        require_api_ready(self.client)

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
        self._require_api_ready()
        # D28.3 / D81: the gate runs before the id is allocated, so a refusal
        # defers the caller without burning a reqId for a request that was
        # never sent.
        wait = pacing_manager.historical_wait_seconds()
        if wait > 0:
            raise PacingExceeded(wait)
        req_id = id_manager.get_id()
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

        Q-41 / D28.1: never sleeps. When the minimum-interval budget is
        exhausted ``pacing_manager.throttle()`` raises PacingExceeded with
        the seconds to wait; the caller defers via QTimer.singleShot and
        retries (same wait/defer contract as historical requests).

        D81: the gate is read before the id is allocated and the interval
        clock is stamped only after the send crossed the wire, so a refused
        or failing send consumes neither budget nor id (the same rule the
        historical path already follows).
        """
        self._require_api_ready()
        reserved = pacing_manager.throttle(stamp=False)
        req_id = id_manager.get_id()
        try:
            self.client.reqMktData(req_id, contract, generic_ticks, False,
                                   False, [])
        except Exception:
            id_manager.release_id(req_id)
            raise
        if not reserved:
            pacing_manager.record_request_slot()
        return req_id

    def cancel_mkt_data(self, req_id: int | None):
        if req_id is None:
            return
        try:
            self.client.cancelMktData(req_id)
        except Exception:
            pass

    def req_contract_details(self, contract: Contract) -> int:
        """Request contract details for a contract. Returns the reqId.

        Q-41 / D28.1: never sleeps — pacing-limited calls raise
        PacingExceeded (defer via QTimer.singleShot), same wait/defer
        contract as historical requests.

        D81: gate before the id, stamp after the send; a raising send rolls
        its id back (see :meth:`req_mkt_data`).
        """
        self._require_api_ready()
        reserved = pacing_manager.throttle(stamp=False)
        req_id = id_manager.get_id()
        try:
            self.client.reqContractDetails(req_id, contract)
        except Exception:
            id_manager.release_id(req_id)
            raise
        if not reserved:
            pacing_manager.record_request_slot()
        return req_id

    def req_sec_def_opt_params(
        self,
        underlying_symbol: str,
        fut_fop_exchange: str,
        underlying_sec_type: str,
        underlying_con_id: int,
    ) -> int:
        """D65: request the option chain for an underlying. Returns the reqId.

        ``reqSecDefOptParams`` answers with ``securityDefinitionOptionParameter``
        callbacks (exchange / tradingClass / expirations / strikes) ended by
        ``securityDefinitionOptionParameterEnd``. For SPX the underlying is its
        IND contract, so the caller passes that conId.

        Order matters: readiness first (a pre-handshake request is rejected with
        504 and must not consume a reqId or pacing budget), then the gate
        (``throttle(stamp=False)``, which may raise without spending
        anything), then ``get_id``, then the send. D81: the interval clock is
        stamped only after the send crossed the wire and a raising send rolls
        its id back. Q-41 / D28.1: never sleeps — when the pacing budget
        is exhausted ``PacingExceeded`` propagates for the caller to defer
        (``QTimer.singleShot``), the same contract as historical requests.
        """
        self._require_api_ready()
        reserved = pacing_manager.throttle(stamp=False)
        req_id = id_manager.get_id()
        try:
            self.client.reqSecDefOptParams(
                req_id,
                underlying_symbol,
                fut_fop_exchange,
                underlying_sec_type,
                underlying_con_id,
            )
        except Exception:
            id_manager.release_id(req_id)
            raise
        if not reserved:
            pacing_manager.record_request_slot()
        return req_id

    def req_matching_symbols(self, pattern: str) -> int:
        """D39.1: debounced symbol search. Returns the reqId.

        ``reqMatchingSymbols`` answers with ``symbolSamples`` (≤16
        ContractDescriptions). Paced like any other request — the
        debounce in SymbolSearchService keeps the rate at ≤1 per ~300ms
        of typing.

        Q-41 / D28.1: never sleeps — pacing-limited calls raise
        PacingExceeded (defer via QTimer.singleShot), same wait/defer
        contract as historical requests.

        D81: gate before the id, stamp after the send; a raising send rolls
        its id back (see :meth:`req_mkt_data`).
        """
        self._require_api_ready()
        reserved = pacing_manager.throttle(stamp=False)
        req_id = id_manager.get_id()
        try:
            self.client.reqMatchingSymbols(req_id, pattern)
        except Exception:
            id_manager.release_id(req_id)
            raise
        if not reserved:
            pacing_manager.record_request_slot()
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
