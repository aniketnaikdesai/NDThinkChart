import logging
import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibkr.bridge import IBBridge
from ibkr.id_manager import id_manager
from ibkr.error_codes import classify_error

_LOG = logging.getLogger(__name__)


class ConnectionState:
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"


class DisconnectClass:
    """D40.1: classification of a lost connection.

    TRANSIENT — the reconnect loop is driven by ``_poll``/``_do_reconnect``
    without ``connectionClosed`` ever firing (the client already
    believes it is down, or IBKR connectivity codes 1100/1101/1102
    arrive with the API socket still up). Keeps the fast D27 reconnect
    path: no pause UI, no gap accounting.

    TWS_GONE — the API server closed the socket (``connectionClosed``).
    On a localhost TWS connection the peer only does this when the TWS
    process goes away: the nightly close, a manual shutdown, or TWS's
    daily auto-restart. Enters the D40 paused-monitoring state.
    """

    TRANSIENT = "transient"
    TWS_GONE = "tws_gone"


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
        # D40.1: classification of the most recent disconnect
        # (DisconnectClass.TRANSIENT / TWS_GONE / None if never dropped).
        # Set BEFORE the disconnected signal is emitted so the
        # MainWindow slot can read it synchronously.
        self._last_disconnect_class: str | None = None

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

    @property
    def last_disconnect_class(self) -> str | None:
        """D40.1: how the last disconnect was classified, or None."""
        return self._last_disconnect_class

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
        """Schedule a reconnection attempt with exponential backoff.

        D40/A2: cancel any timer already pending before arming a new one —
        a transient backoff in flight plus connectionClosed would otherwise
        leak a second timer and double EClient.connect.
        """
        self.stop_polling()
        old = self._reconnect_timer
        if old is not None:
            try:
                old.cancel()
            except Exception:
                pass
            self._reconnect_timer = None
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
            # D40/A1: clear the disconnect classification on a successful
            # connect — a stale TWS_GONE would otherwise downgrade a
            # legitimate mid-day transient 502 to a debug log and hide
            # the status-bar message.
            self._last_disconnect_class = None
            self._set_state(ConnectionState.CONNECTED)

    def error(self, *args, **kwargs):
        """Handle error callbacks from both old and new TWS API signatures."""
        errorTime = 0
        if len(args) >= 5:
            reqId, errorTime, errorCode, errorString, advancedOrderRejectJson = args[:5]
        elif len(args) >= 4:
            # 10.51.1: (reqId, errorTime, errorCode, errorString)
            reqId, errorTime, errorCode, errorString = args[:4]
            advancedOrderRejectJson = kwargs.get('advancedOrderRejectJson', '')
        elif len(args) >= 3:
            reqId, errorCode, errorString = args[:3]
            advancedOrderRejectJson = kwargs.get('advancedOrderRejectJson', '')
        else:
            reqId = args[0] if args else kwargs.get('reqId', 0)
            errorCode = args[1] if len(args) > 1 else kwargs.get('errorCode', 0)
            errorString = args[2] if len(args) > 2 else kwargs.get('errorString', '')
            advancedOrderRejectJson = kwargs.get('advancedOrderRejectJson', '')

        # TWS API versions differ: 10.51+ passes errorTime, older ones don't.
        # Try the full signature, then fall back if the parent only accepts fewer args.
        try:
            super().error(reqId, errorTime, errorCode, errorString,
                          advancedOrderRejectJson)
        except TypeError:
            try:
                super().error(reqId, errorCode, errorString,
                              advancedOrderRejectJson)
            except TypeError:
                try:
                    super().error(reqId, errorCode, errorString)
                except TypeError:
                    super().error(reqId, errorCode)

        severity = classify_error(errorCode)
        # D40.1: while TWS-gone and paused, error 502 ("Couldn't connect
        # to TWS") fires on every failed backoff attempt — expected
        # noise, not news. The badge already shows the paused state, so
        # downgrade to a debug log instead of spamming the status bar
        # all night. A 502 with no prior connection (TWS simply not up
        # at startup) still emits normally.
        if (
            errorCode == 502
            and self._last_disconnect_class == DisconnectClass.TWS_GONE
            and not self._connected
        ):
            _LOG.debug(
                "D40: TWS-gone backoff attempt refused (502) — still paused"
            )
            return
        if severity != 'info':
            self.bridge.error_msg.emit(reqId, errorCode, errorString)

    def connectionClosed(self):
        """D40.1: the API server closed the socket → TWS is gone.

        Build-time observation notes (per the D40 plan, exact codes are a
        build-time observation item):

        - ibapi documents this callback as firing "when TWS closes the
          sockets connection ... or when TWS is shut down". On a
          localhost TWS connection the peer only closes the socket when
          the TWS process goes away — the nightly close, a manual
          shutdown, TWS's daily auto-restart. (The D27 ``_poll`` path,
          which acts when the client already believes it is down
          without a server close, stays TRANSIENT.)
        - IBKR error codes 1100/1101/1102 ("Connectivity between IB and
          Trader Workstation ...") describe the IB↔TWS link while the
          API socket stays up — those are transient flaps, handled by
          the existing fast path, never TWS-gone.
        - Error 502 ("Couldn't connect to TWS") fires on every failed
          backoff attempt while TWS is down; it confirms TWS-gone
          rather than reclassifying it (see ``error()`` — it is
          downgraded to a debug log while paused so the status bar
          isn't spammed all night).

        Two behavior changes vs the old code:

        1. The classification is recorded BEFORE ``disconnected`` is
           emitted so the UI slot can branch on it.
        2. The backoff reconnect loop is (re)started. The old code
           stopped polling here and scheduled nothing — the app would
           never notice the morning TWS login without a restart.
        """
        super().connectionClosed()
        was_connected = self._connected
        self._connected = False
        self.stop_polling()
        if was_connected:
            self._last_disconnect_class = DisconnectClass.TWS_GONE
        self._set_state(ConnectionState.DISCONNECTED)
        if was_connected:
            # D40: keep trying so the morning login reconnects on its
            # own. The pause UI (MainWindow) carries the visible state.
            self._schedule_reconnect()

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

    # ── D37 substrate S0: generic ticks (shared by D37 auction + D38 news) ──
    # Strictly additive: super() first, then the bridge signal. Signatures
    # verified against the 10.51.1 wheel — tickNews takes 6 args (extraData
    # last); the bridge carries the 5 D38 needs.

    def tickGeneric(self, reqId: int, tickType: int, value: float):
        super().tickGeneric(reqId, tickType, value)
        self.bridge.tick_generic.emit(reqId, tickType, value)

    def tickString(self, reqId: int, tickType: int, value: str):
        super().tickString(reqId, tickType, value)
        self.bridge.tick_string.emit(reqId, tickType, value)

    def tickNews(self, tickerId: int, timeStamp: int, providerCode: str,
                 articleId: str, headline: str, extraData: str):
        super().tickNews(tickerId, timeStamp, providerCode, articleId,
                         headline, extraData)
        self.bridge.tick_news.emit(tickerId, timeStamp, providerCode,
                                   articleId, headline)

    # ── D38 news API: providers / historical headlines / articles ────
    # Strictly additive: super() first, then the bridge signal. Signatures
    # verified against the 10.51.1 wheel.

    def newsProviders(self, newsProviders):
        super().newsProviders(newsProviders)
        self.bridge.news_providers.emit(newsProviders)

    def historicalNews(self, requestId: int, time: str, providerCode: str,
                       articleId: str, headline: str):
        super().historicalNews(requestId, time, providerCode, articleId,
                               headline)
        self.bridge.historical_news.emit(requestId, time, providerCode,
                                         articleId, headline)

    def historicalNewsEnd(self, requestId: int, hasMore: bool):
        super().historicalNewsEnd(requestId, hasMore)
        self.bridge.historical_news_end.emit(requestId, hasMore)

    def newsArticle(self, requestId: int, articleType: int, articleText: str):
        super().newsArticle(requestId, articleType, articleText)
        self.bridge.news_article.emit(requestId, articleType, articleText)

    def contractDetails(self, reqId: int, contractDetails):
        super().contractDetails(reqId, contractDetails)
        self.bridge.contract_details.emit(reqId, contractDetails)

    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        self.bridge.contract_details_end.emit(reqId)

    def symbolSamples(self, reqId: int, contractDescriptions):
        # D39.1: verified against the 10.51.1 wheel — (reqId, [ContractDescription]).
        super().symbolSamples(reqId, contractDescriptions)
        self.bridge.symbol_samples.emit(reqId, contractDescriptions)

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
