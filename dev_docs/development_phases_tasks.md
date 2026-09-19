# IBKR Trading Terminal - Detailed Technical Implementation by Phase

This document breaks down the implementation plan into actionable phases with deep technical details, acting as a direct build guide for an LLM or developer.

## Phase 0: Scaffold repo, venv, config
### Technical Details:
- **Project Structure**: Create the folder tree (`ibkr/`, `ui/`, `data/`, `services/`, `config/`, `packaging/`).
- **Dependencies**: Setup venv and run `pip install PyQt6 pyqtgraph ibapi`. (Ensure `PyQt6` installs arm64 native wheels for Apple Silicon. Install `ibapi` from TWS API source or verify PyPI compatibility).
- **Entrypoint (`main.py`)**: Scaffold `QMainWindow`, setup the global Qt app, and initialize `IBApiClient`.
- **Configuration (`config/settings.py`)**: Define `HOST = "127.0.0.1"`, `PORT = 7496` (live trading target), and `CLIENT_ID = 1`.
- **Styling (`config/theme.qss`)**: Implement the Tailwind-inspired dense dark mode. Base font size 10-11px. App background `#0d0f14`, panels `#101218`, borders `#232938`, text `#a3a3a3`. Configure `pyqtgraph`: `pg.setConfigOption('background', '#0d0f14')`, `pg.setConfigOption('foreground', '#a3a3a3')`. Force `QApplication.setStyle("Fusion")`.

## Phase 1: Connection + Threading Bridge
### Technical Details:
- **`ibkr/client.py`**: Subclass `IBApiClient(EWrapper, EClient)`. In `main.py`, instantiate this, call `connect()`, and start a background socket reading thread: `threading.Thread(target=client.run, daemon=True)`.
- **`ibkr/bridge.py`**: Create a `QObject` with a `pyqtSignal` for every IBKR callback type (e.g. `tick_price = pyqtSignal(int, int, float, int)`). `EWrapper` overrides in `client.py` must **never** touch UI/DB directly; they must only call `self.bridge.<signal>.emit(...)`. This leverages Qt's queued connections for thread safety.
- **`ibkr/id_manager.py`**: Store the `orderId` provided by `nextValidId`. Use a `threading.Lock()`-guarded class to safely generate auto-incrementing `reqId` and `orderId`s for all subsequent requests.
- **`ibkr/pacing.py`**: Implement a token-bucket or min-interval throttle. IBKR limits to ~50 req/sec total, and max 60 `reqRealTimeBars` per 10 minutes. Route outbound requests through this gate.
- **`ibkr/error_codes.py`**: Classify `error(reqId, errorCode, errorString)` callbacks. Route codes 2104/2106/2158 to a status bar, warn for others, and surface fatal errors (e.g., pacing violations) clearly.

## Phase 2: Historical Data + SQLite Cache + Static Chart
### Technical Details:
- **`data/db.py`**: Use `sqlite3`. Initialize the schema: tables for `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `trade_groups`, `position_group_map`. **Crucial:** SQLite access must only happen on the main Qt thread.
- **`ibkr/contracts.py`**: Use `reqContractDetails` to resolve string symbols into fully qualified `Contract` objects before fetching data.
- **`ibkr/market_data.py`** & **`data/bar_cache.py`**: Wrap `reqHistoricalData`. When opening a chart, load bars from the SQLite `bars` table first. Then issue a `reqHistoricalData` request only for the time gap between the last cached bar and the current time, saving pacing tokens.
- **`ui/chart_panel.py`**: Construct a `pyqtgraph.PlotWidget` for price and a vertically stacked, X-axis-linked `PlotWidget` for volume.
- **`ui/candlestick_item.py`**: Implement a custom `pg.GraphicsObject` that loops through OHLC data to draw green/red bodies and wicks using `QPicture` for high performance.

## Phase 3: Live Updates + Watchlist
### Technical Details:
- **`ibkr/realtime_bars.py`**: Subscribe via `reqRealTimeBars(barSize=5)` (IBKR natively provides only 5s bars in real-time).
- **`data/bar_aggregator.py`**: Aggregate incoming 5s bars into the active chart's timeframe (1m, 5m, 15m, 1h, 4h). Emit a `bridge.bar_updated` signal to repaint the current candle or append a new one on period rollover.
- **`ui/watchlist_panel.py`**: Create a `QTableWidget` (columns: symbol, last, bid, ask, net chg). Subscribe to these symbols via `reqMktData` (`tickPrice`/`tickSize`).
- **UI Performance**: Flash cells green/red on tick updates. Ensure the chart repaints only the last candle on intra-bar ticks to prevent UI stutter.

## Phase 4: Chart-Type Variants + Studies Core
### Technical Details:
- **Chart Render Modes**: Expand `candlestick_item.py` to support 5 modes: candles, hollow candles (outline-only if close >= open), Heikin-Ashi (compute `haClose=(o+h+l+c)/4` in the data layer, not the render layer), line (close-only), and area (close-only with a gradient/alpha fill).
- **`services/indicator_service.py`**: Port pure numeric transforms for SMA, EMA, VWAP, Bollinger Bands, RSI, MACD from the reference TS code.
- **`ui/studies_dialog.py`**: Replicate the studies browser modal. Allow configuration of periods, source (close/open/etc), std-dev multipliers.
- **Overlays**: Draw indicator lines on the `pyqtgraph` ViewBox. Persist active indicators per symbol to the SQLite `studies` table as JSON param blobs.

## Phase 5: Zones, Alarms, Drawing Tools
### Technical Details:
- **`ui/drawing_overlay.py`**: Implement mouse interactions against pyqtgraph's coordinate transform (`mapToView`/`mapFromView`) for cursor, crosshair, trendline, horizontal line, zone (rectangle), Fibonacci, and measure.
- **Drawing Sets**: Persist tools to `drawing_groups` and `drawings` SQLite tables. Build `ui/drawing_groups_dialog.py` to allow bulk recoloring, visibility toggling, and locking of groups.
- **`services/alarm_service.py`**: Track active alarms in memory. On every price tick from `reqMktData`, check `cross_above` / `cross_below` / `cross_either`.
- **`ui/alarm_overlay.py`**: Draw horizontal alarm lines. Implement "alarm mode" (click the chart to pre-fill the dialog with the clicked price). On trigger, show a toast, play a sound (`QSoundEffect`), and update the `alarms` DB table to mark as triggered.

## Phase 6a: Advanced Studies (Gap / VIX / ICT)
### Technical Details:
- **`services/gap_vix_service.py`**: Implement RTH gap tracker (detect regular-trading-hours gaps and track staircase mitigation logic) and VIX expected-move bands (anchor to session open/close, compute ±0.5σ/1σ/2σ/3σ).
- **`services/ict_service.py`**: Port the complex LuxAlgo-style ICT concepts math (MSS/BOS structure lines, order blocks, Fair Value Gaps, liquidity pools, killzones) into pure Python.
- **Rendering**: Map the complex ICT markers to pyqtgraph `TextItem`, `LinearRegionItem`, or custom `GraphicsObject` shapes overlaid on the price plot.

## Phase 6b: DOM + Order Entry (Single + Bracket)
### Technical Details:
- **`ibkr/market_depth.py`**: Subscribe via `reqMktDepth` (utilizing the confirmed Level II entitlement).
- **`ui/active_trader_panel.py`**: Build the ladder DOM. Implement click-to-trade: clicking the bid column builds a BUY LMT order at that price; clicking the ask builds a SELL LMT.
- **`ibkr/orders.py`**: Build `Order` and `Contract` objects. For bracket orders:
  - Parent order: `transmit=False`
  - Child STP order: `parentId=<parent id>`, `ocaGroup=<unique string>`, `transmit=False`
  - Child LMT order: `parentId=<parent id>`, `ocaGroup=<same string>`, `transmit=True`
- **Execution tracking**: Buffer open orders in an in-memory dictionary. Listen to `orderStatus` and `execDetails` to update the UI Active Trader status row.

## Phase 6c: Active Portfolio + Multi-leg Grouping
### Technical Details:
- **`ibkr/account.py`**: Call `reqAccountSummary` for toolbar net-liq/P&L stats. Call `reqPositions` for the portfolio table.
- **`services/strategy_detection_service.py`**: Implement logic to compare option sides and strikes on the same underlying. Auto-label 2-leg spreads (PCS, PDS, CCS, CDS) and 4-leg Iron Condors. Store this mapping locally in SQLite (`trade_groups`, `position_group_map`).
- **Actions**: Implement a right-click context menu. Build a "Flatten All" function that iterates all open positions, constructing and transmitting opposing MKT orders for each.

## Phase 7: Reconnect, Hardening, Packaging
### Technical Details:
- **`ibkr/client.py` Reconnect**: Poll `isConnected()` on a QTimer. On disconnect, trigger exponential backoff reconnect attempts. Upon successful reconnect, immediately replay the subscription registry (active watchlist symbols, active chart `reqRealTimeBars`, active DOM).
- **TWS Daily Restart**: Handle the mandatory daily TWS logoff as a standard expected disconnect event.
- **Packaging**: Configure the PyInstaller `build.spec` targeting macOS arm64 (`--windowed`). Ensure the SQLite DB path resolves safely in user-space (e.g. `~/Library/Application Support/NDThinkChart`) rather than the read-only `.app` bundle, and bundle `theme.qss` via `sys._MEIPASS`.
