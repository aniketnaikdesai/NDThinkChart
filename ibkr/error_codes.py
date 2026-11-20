class IBKRNotReady(Exception):
    """Raised when an API request is attempted before the TWS handshake.

    The socket being open is NOT readiness: TWS rejects pre-handshake
    requests (e.g. reqHistoricalData) with 504. Only ``nextValidId``
    marks the API ready. Callers defer (like pacing) instead of sending.
    """


def require_api_ready(client) -> None:
    """Raise IBKRNotReady when the TWS handshake hasn't completed.

    The one readiness seam: ``MarketDataManager._require_api_ready`` and
    ``RealtimeBarsManager.subscribe`` both call this function, so a request
    path can never drift from another. The duck-typing is the original
    market-data body: a client exposing ``api_ready`` is asked for it, a
    legacy client exposing ``_connected`` is asked for that, a test double
    with neither is assumed ready, and a callable readiness is called.

    Checked BEFORE allocating a reqId, touching pacing or sending: TWS
    rejects pre-handshake requests with 504.
    """
    if hasattr(client, "api_ready"):
        ready = client.api_ready
    elif hasattr(client, "_connected"):
        ready = client._connected
    else:
        # Test double with no readiness signal: assume ready.
        return
    if callable(ready):
        ready = ready()
    if not ready:
        raise IBKRNotReady("IBKR API not ready (handshake pending)")


def classify_error(error_code: int) -> str:
    """
    Returns 'info', 'warning', or 'fatal'.
    """
    # 2104, 2106, 2158 are data farm connection ok messages
    if error_code in (2104, 2106, 2158):
        return 'info'
    # 2103, 2105, 2108 are data farm connection broken
    if error_code in (2103, 2105, 2108):
        return 'warning'
    # Fatal errors (invalid order, pacing violation, duplicate reqId)
    if error_code in (504, 200, 399, 100, 162):
        return 'fatal'
    # D26.9: order and connectivity failures are first-class, not warnings.
    # 201 order rejected, 103 duplicate order id, 1100 connectivity lost,
    # 502/503/509 couldn't connect. (202 order cancelled stays 'warning':
    # a cancellation is a normal lifecycle event, and 'warning' rather than
    # 'info' is what keeps IBApiClient.error emitting it, so _on_error shows
    # the generic status-bar line.)
    if error_code in (201, 103, 1100, 502, 503, 509):
        return 'fatal'

    return 'warning'
