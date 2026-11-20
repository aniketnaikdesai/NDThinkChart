from ibkr.error_codes import require_api_ready
from ibkr.pacing import pacing_manager, PacingExceeded
from ibkr.id_manager import id_manager
from ibapi.contract import Contract


class RealtimeBarsManager:
    """
    Manages reqRealTimeBars subscriptions.
    IBKR only supports 5-second real-time bars natively.
    The bar_aggregator rolls these up into wider timeframes.

    This manager only subscribes, unsubscribes and cancels. Reconnect
    replay is ``SubscriptionManager.replay_all`` (P26's transactional
    pass), which carries the reissue/rebind hooks every session needs; it
    is the single replay implementation.
    """

    def __init__(self, client):
        self.client = client
        # Map reqId → (symbol, contract) for unsubscribe/cancel bookkeeping.
        self._subscriptions: dict[int, tuple[str, Contract]] = {}

    def subscribe(self, symbol: str, contract: Contract) -> int:
        """
        Start a 5-second real-time bar subscription.
        Returns the reqId.

        Readiness comes first, through the same seam the market-data
        manager uses: before pacing, before the id — a not-ready transport
        allocates no reqId, records no pacing slot and never sends.

        D28.1: never sleeps. Raises PacingExceeded (with wait_seconds) when
        the realtime budget is exhausted; the caller defers via
        QTimer.singleShot. The budget slot is recorded only after the
        request is actually issued.
        """
        require_api_ready(self.client)
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
