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
    
    return 'warning'
