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

    # Live ticks
    tick_price = pyqtSignal(int, int, float)        # reqId, tickType, price
    tick_size = pyqtSignal(int, int, int)           # reqId, tickType, size

    # Real-time 5-second bars
    realtime_bar = pyqtSignal(int, int, float, float, float, float, float, float, int)
    # reqId, time, open, high, low, close, volume, wap, count

    # Market Depth (DOM)
    update_mkt_depth = pyqtSignal(int, int, int, int, float, int)
    # reqId, position, operation, side, price, size

    # Account & Orders
    account_summary = pyqtSignal(int, str, str, str)  # reqId, account, tag, value
    account_summary_end = pyqtSignal(int)             # reqId
    position_update = pyqtSignal(str, object, float, float)  # account, Contract, pos, avgCost
    position_end = pyqtSignal()                       # end of positions list
    order_status = pyqtSignal(int, str, float, float, float, int, int, float, int, str)
    # orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld

    open_order = pyqtSignal(int, object, object, object)
    # orderId, Contract, Order, OrderState

    exec_details = pyqtSignal(int, object, object)
    # reqId, Contract, Execution

