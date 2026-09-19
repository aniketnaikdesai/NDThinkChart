from ibkr.pacing import pacing_manager
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
    ) -> int:
        """
        Request historical bars for a contract.
        Uses the TIMEFRAME_CONFIG to automatically set duration and bar size.
        Returns the reqId so the caller can correlate incoming bars.
        
        Args:
            extended_hours: If True, fetch pre/post-market data (useRTH=0)
        """
        cfg = TIMEFRAME_CONFIG.get(timeframe, TIMEFRAME_CONFIG["5 mins"])
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        # Extended hours overrides useRTH
        effective_useRTH = 0 if extended_hours else useRTH
        self.client.reqHistoricalData(
            req_id,
            contract,
            endDateTime,          # "" = up to now
            cfg["duration"],
            cfg["bar_size"],
            whatToShow,
            effective_useRTH,
            2,                    # formatDate=2 → unix timestamp
            False,
            []
        )
        return req_id

    def req_mkt_data(self, contract: Contract) -> int:
        """Subscribe to live tick data for a contract. Returns reqId."""
        req_id = id_manager.get_id()
        pacing_manager.throttle()
        self.client.reqMktData(req_id, contract, "", False, False, [])
        return req_id

    def cancel_mkt_data(self, req_id: int | None):
        if req_id is None:
            return
        try:
            self.client.cancelMktData(req_id)
        except Exception:
            pass

    def cancel_historical_data(self, req_id: int | None):
        if req_id is None:
            return
        try:
            self.client.cancelHistoricalData(req_id)
        except Exception:
            pass
