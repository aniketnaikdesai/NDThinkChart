from ibkr.pacing import pacing_manager, PacingExceeded
from ibkr.id_manager import id_manager
from ibapi.contract import Contract


class RealtimeBarsManager:
    """
    Manages reqRealTimeBars subscriptions.
    IBKR only supports 5-second real-time bars natively.
    The bar_aggregator rolls these up into wider timeframes.
    """

    def __init__(self, client):
        self.client = client
        # Map reqId → (symbol, contract) so we can replay on reconnect
        self._subscriptions: dict[int, tuple[str, Contract]] = {}

    def subscribe(self, symbol: str, contract: Contract) -> int:
        """
        Start a 5-second real-time bar subscription.
        Returns the reqId.

        D28.1: never sleeps. Raises PacingExceeded (with wait_seconds) when
        the realtime budget is exhausted; the caller defers via
        QTimer.singleShot. The budget slot is recorded only after the
        request is actually issued.
        """
        wait = pacing_manager.realtime_wait_seconds()
        if wait > 0:
            raise PacingExceeded(wait)
        req_id = id_manager.get_id()
        self.client.reqRealTimeBars(
            req_id,
            contract,
            5,          # barSize — IBKR only accepts 5 here
            "TRADES",
            False,      # useRTH=False → include extended hours
            []
        )
        pacing_manager.record_realtime_slot()
        self._subscriptions[req_id] = (symbol, contract)
        return req_id

    def unsubscribe(self, req_id: int):
        self.client.cancelRealTimeBars(req_id)
        self._subscriptions.pop(req_id, None)

    def cancel_all(self) -> None:
        """Cancel all active real-time bar subscriptions."""
        for req_id in list(self._subscriptions):
            try:
                self.client.cancelRealTimeBars(req_id)
            except Exception:
                pass
            self._subscriptions.pop(req_id, None)

    def replay_all(self):
        """Re-subscribe all active streams after a reconnect."""
        items = list(self._subscriptions.items())
        self._subscriptions.clear()
        for _old_id, (symbol, contract) in items:
            self.subscribe(symbol, contract)
