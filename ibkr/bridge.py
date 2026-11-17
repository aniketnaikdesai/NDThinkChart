from PyQt6.QtCore import QObject, pyqtSignal


class IBBridge(QObject):
    # Connection / Lifecycle
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_msg = pyqtSignal(int, int, str)           # reqId, errorCode, errorString

    # Historical data
    historical_bar = pyqtSignal(int, object)        # reqId, BarData
    historical_data_end = pyqtSignal(int)           # reqId

    # Contract details
    contract_details = pyqtSignal(int, object)      # reqId, ContractDetails
    contract_details_end = pyqtSignal(int)          # reqId

    # D39.1: symbol search — reqMatchingSymbols → symbolSamples (≤16).
    symbol_samples = pyqtSignal(int, object)        # reqId, [ContractDescription]

    # Live ticks
    tick_price = pyqtSignal(int, int, float)        # reqId, tickType, price
    tick_size = pyqtSignal(int, int, int)           # reqId, tickType, size

    # D65: SPX 0DTE option chain discovery + per-leg greeks (strictly additive).
    # Values are passed through UNMODIFIED — sentinel screening is the engine's.
    option_params = pyqtSignal(int, object)         # reqId, chain-response dict
    option_params_end = pyqtSignal(int)             # reqId
    option_computation = pyqtSignal(int, int, object, object)
    # reqId, tickType, delta, gamma

    # Generic ticks — D37 substrate S0 (shared with D38). Strictly additive.
    tick_generic = pyqtSignal(int, int, float)      # reqId, tickType, value
    tick_string = pyqtSignal(int, int, str)        # reqId, tickType, value
    tick_news = pyqtSignal(int, int, str, str, str)
    # reqId, timeStamp, providerCode, articleId, headline

    # News API — D38 digest (strictly additive).
    news_providers = pyqtSignal(object)          # ListOfNewsProviders
    historical_news = pyqtSignal(int, str, str, str, str)
    # reqId, time, providerCode, articleId, headline
    historical_news_end = pyqtSignal(int, bool)  # reqId, hasMore
    news_article = pyqtSignal(int, int, str)    # reqId, articleType, articleText

    # Real-time 5-second bars
    realtime_bar = pyqtSignal(int, int, float, float, float, float, float, float, int)
    # reqId, time, open, high, low, close, volume, wap, count


