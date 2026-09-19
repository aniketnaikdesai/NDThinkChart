# IBKR Trading Terminal - Detailed Technical Specification

This document provides deep technical specifications for the core architecture, data schemas, service contracts, test fixtures, and task breakdowns required to build the trading terminal.

---

## 1. API Contract and DDL Schema

### DDL Schema (SQLite)
The application relies on a local SQLite database for fast caching and offline persistence. It must be accessed **exclusively** from the Qt main thread.

```sql
-- data/schema.sql
CREATE TABLE bars (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts INTEGER NOT NULL,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    PRIMARY KEY (symbol, timeframe, ts)
);

CREATE TABLE watchlist (
    symbol TEXT PRIMARY KEY,
    category TEXT NOT NULL,      -- 'FUTURES' | 'EQUITIES' | 'INDICES' | 'CRYPTO'
    sort_order INTEGER NOT NULL
);

CREATE TABLE alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    direction TEXT NOT NULL,      -- 'cross_above' | 'cross_below' | 'cross_either'
    active INTEGER NOT NULL DEFAULT 1,
    triggered INTEGER NOT NULL DEFAULT 0,
    triggered_at INTEGER,
    sound INTEGER NOT NULL DEFAULT 1,
    note TEXT
);

CREATE TABLE zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price_low REAL NOT NULL,
    price_high REAL NOT NULL,
    kind TEXT NOT NULL,           -- 'supply' | 'demand'
    label TEXT,
    color TEXT,
    visible INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE drawing_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    seq_number INTEGER NOT NULL,
    color TEXT,
    visible INTEGER NOT NULL DEFAULT 1,
    locked INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE TABLE drawings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    kind TEXT NOT NULL,           -- 'trendline','horizontal','zone','fibonacci','measure'
    payload TEXT NOT NULL,        -- JSON blob of points/config
    color TEXT,
    label TEXT,
    group_id INTEGER REFERENCES drawing_groups(id)
);

CREATE TABLE studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,           -- 'sma','ema','vwap','bollinger','rsi','macd', etc.
    enabled INTEGER NOT NULL DEFAULT 1,
    params TEXT NOT NULL          -- JSON blob of that study's config
);

CREATE TABLE trade_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,  -- 'PCS','PDS','CCS','CDS','IC','CUSTOM'
    underlying TEXT NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE TABLE position_group_map (
    ibkr_position_id TEXT NOT NULL,
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
```

### Internal API Contract (`ibkr/bridge.py`)
Since `ibapi` callbacks fire on a background thread, `ibkr/bridge.py` defines the API contract between the network layer and the UI layer using `pyqtSignal`.

```python
from PyQt6.QtCore import QObject, pyqtSignal

class IBBridge(QObject):
    # Connection / Lifecycle
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_msg = pyqtSignal(int, int, str) # reqId, errorCode, errorString

    # Market Data
    tick_price = pyqtSignal(int, int, float) # reqId, tickType, price
    tick_size = pyqtSignal(int, int, int) # reqId, tickType, size
    historical_bar = pyqtSignal(int, object) # reqId, BarData
    historical_data_end = pyqtSignal(int) # reqId
    realtime_bar = pyqtSignal(int, int, float, float, float, float, int, float, int) # reqId, time, o, h, l, c, vol, wap, count
    
    # Market Depth (DOM)
    update_mkt_depth = pyqtSignal(int, int, int, int, float, int) # reqId, position, operation, side, price, size
    
    # Account & Orders
    position_update = pyqtSignal(str, object, float, float) # account, Contract, pos, avgCost
    order_status = pyqtSignal(int, str, float, float, float, int, int, float, int, str) # orderId, status, filled, remaining, avgFillPrice...
```

---

## 2. File Module Layout

```text
trading_app/
├── main.py                       # App entry point, sets up QApplication, instantiates IBApiClient, mounts MainWindow.
├── config/
│   ├── settings.py               # Env vars, host/port configs, rate limit constants.
│   └── theme.qss                 # Global Tailwind-inspired dense dark mode stylesheet.
├── ibkr/
│   ├── client.py                 # Subclasses EWrapper & EClient. Manages the socket and reader thread.
│   ├── bridge.py                 # (See API Contract) QObject defining pyqtSignals.
│   ├── id_manager.py             # Thread-safe ID sequencer (reqId, orderId).
│   ├── pacing.py                 # Rate-limiter intercepting all outbound client.req* calls.
│   ├── error_codes.py            # Dictionary and classification logic for IBKR error codes.
│   ├── contracts.py              # Helpers for building Contract objects and reqContractDetails.
│   ├── market_data.py            # Wrappers for reqMktData, reqHistoricalData, reqRealTimeBars.
│   ├── market_depth.py           # Wrappers for reqMktDepth.
│   ├── orders.py                 # Helpers for building single and OCA bracket Orders.
│   └── account.py                # Wrappers for reqPositions, reqAccountSummary.
├── ui/
│   ├── main_window.py            # Main QMainWindow. Orchestrates dock layouts.
│   ├── title_bar.py              # Custom dense top navigation (app tabs, connection status).
│   ├── chart_panel.py            # Core pyqtgraph implementation (price plot + volume plot).
│   ├── candlestick_item.py       # Custom pg.GraphicsObject handling 5 render modes (candles/hollow/HA/line/area).
│   ├── overlays/                 # pyqtgraph overlays (zones, drawings, alarms, indicators).
│   ├── dialogs/                  # Modal windows (studies config, drawing groups, alarms).
│   ├── active_trader_panel.py    # DOM ladder rendering and click-to-trade logic.
│   └── active_portfolio_panel.py # Positions table and multi-leg grouping UI.
├── data/
│   ├── db.py                     # SQLite connection manager and CRUD operations.
│   ├── bar_cache.py              # Logic to stitch SQLite cached bars with live IBKR backfill.
│   ├── bar_aggregator.py         # Rolling 5s realtime bars into 1m, 5m, 15m, 1h timeframes.
│   └── models.py                 # Dataclasses (Bar, Alarm, Drawing, Position, etc.).
├── services/
│   ├── indicator_service.py      # Pure math functions for SMA, EMA, VWAP, Bollinger, RSI, MACD.
│   ├── gap_vix_service.py        # Math for RTH gaps and VIX expected-move SD bands.
│   ├── ict_service.py            # Math for LuxAlgo-style ICT concepts (FVG, Order Blocks, Liquidity).
│   ├── alarm_service.py          # State machine evaluating live prices against active alarms.
│   └── strategy_detection.py     # Logic to group options legs (PCS, PDS, CCS, CDS, Iron Condor).
└── packaging/
    └── build.spec                # PyInstaller spec for macOS arm64.
```

---

## 3. IBKR Connection and Config Schema

### Config Schema (`config/settings.py`)
```python
import os

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", 7496)) # Live TWS target
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", 1))

DB_PATH = os.getenv("DB_PATH", "charting_app.sqlite3")

# Pacing & Rate Limits
MAX_REQ_PER_SEC = 50
MAX_REALTIME_BARS_PER_10_MIN = 60
```

### Connection Lifecycle
1. **Init**: `client = IBApiClient(bridge)`
2. **Connect**: `client.connect(IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID)`
3. **Thread Start**: `threading.Thread(target=client.run, daemon=True).start()`
4. **Handshake**: Wait for `EWrapper.nextValidId` callback. This seeds `id_manager.py`.
5. **Ready**: `bridge.connected.emit()` is fired, enabling UI functionality.

### Disconnect & Reconnect Schema
- The UI contains a `QTimer` polling `client.isConnected()` every 3 seconds.
- If disconnected (or if `connectionClosed` fires), the app enters a reconnect state.
- **Backoff**: Attempts `connect()` at 2s, 4s, 8s, 16s intervals.
- **Replay**: Upon successful reconnect, a `SubscriptionManager` class iterates through active symbols and re-issues `reqMktData`, `reqRealTimeBars`, and `reqMktDepth` to restore state (IBKR drops all subscriptions on socket close).

---

## 4. Service Spec

Services are pure Python modules devoid of UI or Networking logic. They take data in, compute, and return data out.

### `services/indicator_service.py`
```python
def calculate_sma(prices: List[float], period: int) -> List[float]:
    """Returns a list of SMA values matching the length of the input prices."""
    
def calculate_bollinger_bands(prices: List[float], period: int, std_dev: float) -> Tuple[List[float], List[float], List[float]]:
    """Returns (Upper Band, Middle Band, Lower Band) lists."""
    
def calculate_macd(prices: List[float], fast: int, slow: int, signal: int) -> Tuple[List[float], List[float], List[float]]:
    """Returns (MACD Line, Signal Line, Histogram)."""
```

### `services/strategy_detection_service.py`
```python
def detect_option_strategy(legs: List[Position]) -> str:
    """
    Evaluates 2 or 4 option legs on the same underlying.
    Returns: 'PCS' (Put Credit Spread), 'PDS', 'CCS', 'CDS', 'IRON_CONDOR', or 'CUSTOM'.
    Logic checks strike widths and long/short sides matching standard spread criteria.
    """
```

### `services/alarm_service.py`
```python
def evaluate_alarms(symbol: str, prev_price: float, curr_price: float, active_alarms: List[Alarm]) -> List[Alarm]:
    """
    Evaluates price crossings. 
    If direction == 'cross_above' and prev_price < alarm.price <= curr_price, mark triggered.
    Returns a list of alarms that just triggered.
    """
```

---

## 5. Unit Test Fixtures

Testing requires mocking both the SQLite DB and the asynchronous IBKR callbacks.

```python
# tests/conftest.py
import pytest
import sqlite3
from typing import List

@pytest.fixture
def memory_db():
    """Provides a fresh in-memory SQLite connection with the DDL schema applied."""
    conn = sqlite3.connect(":memory:")
    with open("data/schema.sql") as f:
        conn.executescript(f.read())
    yield conn
    conn.close()

@pytest.fixture
def sample_ohlc_data() -> List[dict]:
    """Returns 100 periods of deterministic sine-wave OHLC data for testing indicators."""
    return [
        {"ts": 1600000000 + (i * 60), "open": 100 + i, "high": 102 + i, "low": 98 + i, "close": 101 + i, "volume": 1000}
        for i in range(100)
    ]

@pytest.fixture
def mock_ib_bridge():
    """Provides an instance of IBBridge without requiring a real socket."""
    from ibkr.bridge import IBBridge
    return IBBridge()
```

### Testing Indicators
```python
def test_sma_calculation(sample_ohlc_data):
    closes = [candle['close'] for candle in sample_ohlc_data]
    sma = calculate_sma(closes, period=10)
    assert len(sma) == 100
    assert sma[9] is not None # 10th period has first valid SMA
```

---

## 6. Task Breakdowns (Jira/Linear Style)

### Epic 1: Scaffolding & Core Architecture
- **TSK-1.1**: Initialize project repo, PyEnv (Python 3.11), PyQT6, pyqtgraph, and IBAPI.
- **TSK-1.2**: Create `main.py` entrypoint and render an empty `QMainWindow` with the custom `config/theme.qss` (Tailwind dark palette).
- **TSK-1.3**: Create `ibkr/bridge.py` defining the `pyqtSignal` events for the API contract.
- **TSK-1.4**: Implement `IBApiClient` in `ibkr/client.py` and verify background thread connection to port 7496.
- **TSK-1.5**: Implement `ibkr/id_manager.py` and `ibkr/pacing.py` for thread-safe request routing.

### Epic 2: Data Persistence & Historical Charting
- **TSK-2.1**: Implement `data/schema.sql` and `data/db.py` for SQLite CRUD operations.
- **TSK-2.2**: Implement `reqHistoricalData` wrapper and wire responses to `bar_cache.py`.
- **TSK-2.3**: Build `ui/chart_panel.py` containing pyqtgraph `PlotWidget` (price & volume).
- **TSK-2.4**: Implement `ui/candlestick_item.py` to draw OHLC data via `QPicture`.

### Epic 3: Real-time Streaming & Watchlist
- **TSK-3.1**: Wire up `reqMktData` to populate the `ui/watchlist_panel.py` `QTableWidget`. Add green/red flash on tick updates.
- **TSK-3.2**: Wire up `reqRealTimeBars` to stream 5s bars.
- **TSK-3.3**: Implement `data/bar_aggregator.py` to transform 5s bars into 1m/5m/15m/1h timeframes.
- **TSK-3.4**: Ensure chart UI repaints the active candle intra-bar efficiently without blocking the main thread.

### Epic 4: Studies, Alarms, and Drawings
- **TSK-4.1**: Implement core math services (`indicator_service.py`) and UI configuration modals (`studies_dialog.py`).
- **TSK-4.2**: Implement complex math services (`gap_vix_service.py`, `ict_service.py`) and overlay logic in `chart_panel.py`.
- **TSK-4.3**: Build `ui/drawing_overlay.py` utilizing pyqtgraph mapping coordinates for trendlines, zones, and fibs.
- **TSK-4.4**: Implement `alarm_service.py` tracking prices and triggering audio/visual alerts on crossing.

### Epic 5: Execution (DOM & Portfolio)
- **TSK-5.1**: Implement `reqMktDepth` and build the ladder DOM UI (`active_trader_panel.py`).
- **TSK-5.2**: Implement `ibkr/orders.py`. Wire click-to-trade in the DOM to submit Single LMT orders.
- **TSK-5.3**: Expand `ibkr/orders.py` to support bracket orders (OCA group generation).
- **TSK-5.4**: Implement `reqPositions` and build the `active_portfolio_panel.py` table.
- **TSK-5.5**: Implement `strategy_detection_service.py` and the context menu for Flatten All.

### Epic 6: Packaging
- **TSK-6.1**: Implement the Reconnection manager (polling `isConnected()` and exponential backoff).
- **TSK-6.2**: Generate the PyInstaller macOS arm64 `build.spec` and verify standalone `.app` execution.
