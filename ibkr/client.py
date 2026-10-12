import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibkr.bridge import IBBridge
from ibkr.id_manager import id_manager
from ibkr.error_codes import classify_error


class ConnectionState:
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"


class IBApiClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.bridge = IBBridge()
        self._connected = False
        self._connection_state = ConnectionState.DISCONNECTED
        self._reconnect_timer = None
        self._reconnect_attempt = 0
        self._max_backoff = 16
        self._backoff_base = 2
        self._poll_timer = None
        # D27.3: last connect() params, so _do_reconnect can re-issue the
        # real EClient.connect instead of the nonexistent eConnect.
        self._conn_host: str | None = None
        self._conn_port: int | None = None
        self._conn_client_id: int | None = None

    def connect(self, host: str, port: int, clientId: int):
        """Connect and remember the params for reconnect (D27.3)."""
        self._conn_host = host
        self._conn_port = port
        self._conn_client_id = clientId
        super().connect(host, port, clientId)
        self.start_polling()

    @property
    def connected(self) -> bool:
        try:
            return EClient.isConnected(self)
        except Exception:
            return self._connected

    @property
    def connection_state(self) -> str:
        return self._connection_state

    def _set_state(self, new_state: str) -> None:
        prev = self._connection_state
        self._connection_state = new_state
        if new_state == ConnectionState.CONNECTED:
            self.bridge.connected.emit()
        elif new_state == ConnectionState.DISCONNECTED:
            self.bridge.disconnected.emit()
        elif new_state == ConnectionState.RECONNECTING and prev != new_state:
            self.bridge.error_msg.emit(0, 2106, "Reconnecting to TWS...")

    def start_polling(self, interval: float = 3.0) -> None:
        """Start polling connection state. Called on connect."""
        self.stop_polling()
        self._poll_timer = threading.Timer(interval, self._poll)
        self._poll_timer.daemon = True
        self._poll_timer.start()

    def stop_polling(self) -> None:
        """Stop polling connection state."""
        if self._poll_timer is not None:
            self._poll_timer.cancel()
            self._poll_timer = None

    def _poll(self) -> None:
        """Poll connection state and trigger reconnect if needed."""
        try:
            if self.connected and not self._connected:
                self._connected = True
                self._reconnect_attempt = 0
                self._set_state(ConnectionState.CONNECTED)
                self.start_polling()
                return
        except Exception:
            pass

        if not self._connected:
            self._connected = False
            if self._connection_state != ConnectionState.RECONNECTING:
                self._set_state(ConnectionState.RECONNECTING)
            self._schedule_reconnect()
            # D27.3: a reconnect attempt is now pending on the backoff timer.
            # Do NOT re-arm the poll timer here — re-arming every poll
            # interval defeats the backoff and piles up doomed attempts.
            return

        if self._connection_state == ConnectionState.CONNECTED:
            try:
                self.start_polling()
            except Exception:
                pass

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt with exponential backoff."""
        self.stop_polling()
        delay = min(
            self._backoff_base ** min(self._reconnect_attempt, 6),
            self._max_backoff,
        )
        self._reconnect_attempt += 1
        self._reconnect_timer = threading.Timer(delay, self._do_reconnect)
        self._reconnect_timer.daemon = True
        self._reconnect_timer.start()

    def _do_reconnect(self) -> None:
        """Attempt to reconnect to TWS (D27.3).

        Re-issues the real ``EClient.connect`` with the params stored by
        ``connect()`` — the old ``eConnect()`` call never existed on ibapi's
        EClient, so every attempt died with AttributeError.
        """
        if self._conn_host is None:
            # Never connected: nothing to reconnect to.
            return
        try:
            super().connect(
                self._conn_host, self._conn_port, self._conn_client_id
            )
        except Exception:
            self._schedule_reconnect()
            return
        # The attempt is issued; resume polling so the outcome is observed:
        # nextValidId (or the connected check) drives CONNECTED, otherwise
        # _poll schedules the next backoff attempt.
        self.start_polling()

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        id_manager.set_next_valid_id(orderId)
        if not self._connected:
            self._connected = True
            self._reconnect_attempt = 0
            self._set_state(ConnectionState.CONNECTED)

    def error(self, *args, **kwargs):
        """Handle error callbacks from both old and new TWS API signatures."""
        if len(args) >= 5:
            reqId, _errorTime, errorCode, errorString, advancedOrderRejectJson = args[:5]
        elif len(args) >= 4:
            reqId, errorCode, errorString, advancedOrderRejectJson = args[:4]
        elif len(args) >= 3:
            reqId, errorCode, errorString = args[:3]
            advancedOrderRejectJson = kwargs.get('advancedOrderRejectJson', '')
        else:
            reqId = args[0] if args else kwargs.get('reqId', 0)
            errorCode = args[1] if len(args) > 1 else kwargs.get('errorCode', 0)
            errorString = args[2] if len(args) > 2 else kwargs.get('errorString', '')
            advancedOrderRejectJson = kwargs.get('advancedOrderRejectJson', '')

        # TWS API versions differ: some pass errorTime, some don't.
        # Try the full signature, then fall back if the parent only accepts 3 args.
        try:
            super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        except TypeError:
            try:
                super().error(reqId, errorCode, errorString)
            except TypeError:
                super().error(reqId, errorCode)

        severity = classify_error(errorCode)
        if severity != 'info':
            self.bridge.error_msg.emit(reqId, errorCode, errorString)

    def connectionClosed(self):
        super().connectionClosed()
        self._connected = False
        self.stop_polling()
        self._set_state(ConnectionState.DISCONNECTED)

    def close(self) -> None:
        """Clean disconnect."""
        self.stop_polling()
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None
        try:
            super().close()
        except Exception:
            pass

    def historicalData(self, reqId: int, bar):
        super().historicalData(reqId, bar)
        self.bridge.historical_bar.emit(reqId, bar)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        self.bridge.historical_data_end.emit(reqId)

    def contractDetails(self, reqId: int, contractDetails):
        super().contractDetails(reqId, contractDetails)
        self.bridge.contract_details.emit(reqId, contractDetails)

    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        self.bridge.contract_details_end.emit(reqId)

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        self.bridge.tick_price.emit(reqId, tickType, price)

    def tickSize(self, reqId: int, tickType: int, size: int):
        super().tickSize(reqId, tickType, size)
        self.bridge.tick_size.emit(reqId, tickType, size)

    def realtimeBar(self, reqId: int, time: int, open_: float, high: float,
                    low: float, close: float, volume: float, wap: float, count: int):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        self.bridge.realtime_bar.emit(reqId, time, open_, high, low, close, volume, wap, count)

    def updateMktDepth(self, reqId: int, position: int, operation: int,
                       side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)
        self.bridge.update_mkt_depth.emit(reqId, position, operation, side, price, size)

    def updateMktDepthL2(self, reqId: int, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: int):
        super().updateMktDepthL2(reqId, position, marketMaker, operation, side, price, size)
        self.bridge.update_mkt_depth.emit(reqId, position, operation, side, price, size)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        self.bridge.account_summary.emit(reqId, account, tag, value)

    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        self.bridge.account_summary_end.emit(reqId)

    def position(self, account: str, contract, pos: float, avgCost: float):
        super().position(account, contract, pos, avgCost)
        self.bridge.position_update.emit(account, contract, pos, avgCost)

    def positionEnd(self):
        super().positionEnd()
        self.bridge.position_end.emit()

    def orderStatus(self, orderId: int, status: str, filled: float,
                     remaining: float, avgFillPrice: float, permId: int,
                     parentId: int, lastFillPrice: float, clientId: int,
                     whyHeld: str):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                            permId, parentId, lastFillPrice, clientId, whyHeld)
        self.bridge.order_status.emit(orderId, status, filled, remaining,
                                       avgFillPrice, permId, parentId,
                                       lastFillPrice, clientId, whyHeld)

    def openOrder(self, orderId: int, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        self.bridge.open_order.emit(orderId, contract, order, orderState)

    def execDetails(self, reqId: int, contract, execution):
        super().execDetails(reqId, contract, execution)
        self.bridge.exec_details.emit(reqId, contract, execution)
