from PyQt6.QtCore import QObject, pyqtSignal


class IBBridge(QObject):
    # Connection / Lifecycle
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_msg = pyqtSignal(int, int, str)           # reqId, errorCode, errorString

    # Historical data
    historical_bar = pyqtSignal(int, object)        # reqId, BarData
    historical_data_end = pyqtSignal(int)           # reqId

    # Historical ticks — D36 footprint (one tape, two metrics).
    historical_ticks_bid_ask = pyqtSignal(int, object, bool)
    # reqId, [HistoricalTickBidAsk], done
    historical_ticks_last = pyqtSignal(int, object, bool)
    # reqId, [HistoricalTickLast], done
    # (A1: the histogram_data signal was removed — reqHistogramData takes no
    # date parameter, so per-bar histograms are impossible; the heatmap's
    # tick-count metric comes from TRADES tick pages instead.)

    # Contract details
    contract_details = pyqtSignal(int, object)      # reqId, ContractDetails
    contract_details_end = pyqtSignal(int)          # reqId

    # Live ticks
    tick_price = pyqtSignal(int, int, float)        # reqId, tickType, price
    tick_size = pyqtSignal(int, int, int)           # reqId, tickType, size

    # Real-time 5-second bars
    realtime_bar = pyqtSignal(int, int, float, float, float, float, float, float, int)
    # reqId, time, open, high, low, close, volume, wap, count

    # Market Depth (DOM)
    update_mkt_depth = pyqtSignal(int, int, int, int, float, int, bool)
    # reqId, position, operation, side, price, size, isSmartDepth
    # (isSmartDepth False for plain updateMktDepth; D37 disambiguates SMART rows)

    # Account & Orders
    account_summary = pyqtSignal(int, str, str, str)  # reqId, account, tag, value
    account_summary_end = pyqtSignal(int)             # reqId
    position_update = pyqtSignal(str, object, float, float)  # account, Contract, pos, avgCost
    position_end = pyqtSignal()                       # end of positions list
    order_status = pyqtSignal(int, str, float, float, float, int, int, float, int, str, object)
    # orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice
    # (mktCapPrice is object-typed: None on pre-10.51 servers; 10.51.1 always passes 11 args)

    open_order = pyqtSignal(int, object, object, object)
    # orderId, Contract, Order, OrderState

    exec_details = pyqtSignal(int, object, object)
    # reqId, Contract, Execution

