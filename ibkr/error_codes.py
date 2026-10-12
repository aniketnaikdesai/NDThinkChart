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
    # cancellation is a normal lifecycle event; _on_error still routes it
    # to the registry as Cancelled.)
    if error_code in (201, 103, 1100, 502, 503, 509):
        return 'fatal'

    return 'warning'
