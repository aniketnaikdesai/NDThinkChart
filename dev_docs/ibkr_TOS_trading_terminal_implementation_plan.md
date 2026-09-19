# IBKR Trading Terminal — Technical Implementation Plan
### Target: macOS (Apple Silicon) · Official `ibapi` · TWS Desktop · PyQt6 + pyqtgraph

This document is written to be handed directly to a coding LLM (e.g. Claude Code) as
a build spec. It combines two source materials:

1. `trading_app_architecture.txt` — the intended Python/PyQt6 architecture (process
   model, folder layout, packaging).
2. `github.com/aniketnaikdesai/NDThinkChart` — an existing prototype that defines
   the actual **feature set** to reach parity with. Section 2 below is a full
   inventory of what that repo does, since it changes the scope significantly
   beyond what the architecture doc alone described (chart, watchlist, one
   indicator, alarms, zones, DOM — the repo turns out to contain a much deeper
   studies library, drawing-tools system, and options-aware portfolio manager).

Two decisions already made and locked into this plan (confirmed with you directly):
official **`ibapi`** (not ib_insync/ib_async), connecting to **TWS Desktop**
(not IB Gateway), targeting **Apple Silicon only**.

---

## 0. Assumptions & Open Items

| Assumption | Default used | Why it matters |
|---|---|---|
| macOS chip | Apple Silicon (arm64) only | Single-arch PyInstaller build, single TWS download |
| macOS min version | macOS 13 (Ventura)+ | PyQt6 wheel support baseline |
| Python version | 3.11 | Best wheel coverage for PyQt6 + `ibapi` on macOS as of this writing |
| Connection target | **TWS Desktop**, live trading, port 7496 | Confirmed — default dev target is Live on Port 7496 |
| Market data entitlements | **Level II/depth confirmed** | The DOM/ladder panel (Section 8.5) will be fully functional |
| Options trading permission | **Confirmed** | The multi-leg strategy grouping and option chains will be fully supported |
| Single IBKR account, single client app instance | Yes | Simplifies `clientId` management |

---

## 1. What the Architecture Doc Specifies (baseline, still valid)

Unchanged from `trading_app_architecture.txt`: single-process Python app, PyQt6 for
UI, pyqtgraph for charting, SQLite for local persistence, PyInstaller for
packaging, no bundled broker software. What changes is *how* the IBKR connection
is implemented (Section 3) and *how much* UI/feature surface is being built
(Section 2).

---

## 2. What `NDThinkChart` Actually Contains (repo inventory)

**Stack**: React 19 + TypeScript + Vite, chart rendering via TradingView's
`lightweight-charts` library, styled with Tailwind, icons via `lucide-react`. It
was scaffolded through Google's AI Studio (there's an unused `@google/genai`
dependency in `package.json` — grepping the source confirms it is **not
referenced anywhere in `src/`**; there is no AI feature to port, safe to ignore).

**Critically: 100% of its market data is simulated.** `services/marketData.ts`
hardcodes a default ticker list (`/ES`, `/NQ`, `/RTY`, SPY, NVDA, AAPL, TSLA, AMD)
and procedurally generates candles with sine-wave price action plus noise; live
"streaming" is a `setInterval` random-walk in `App.tsx`. There is no broker
integration of any kind in this repo — the entire IBKR/`ibapi` layer in this plan
is new work, not a port. What *does* transfer directly is the UI structure, the
indicator/study math, the drawing-tools/alarm/portfolio logic, and the exact
interaction design — all of which are UI-framework-agnostic and translate cleanly
to PyQt6 + pyqtgraph.

Persistence today is browser `localStorage` (alarms, drawings, drawing groups,
sidebar width, positions) — Section 12's SQLite schema is the direct replacement.

### 2.1 Chart (`TradingViewChart.tsx`, `ChartHeader.tsx`)
- 5 chart types: candles, hollow candles, Heikin-Ashi, line, area (source doc's
  plan only covered plain candlesticks — this is a scope increase)
- Volume histogram subplot, X-axis linked to price panel
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1D, 1W
- Crosshair with a live "data window" showing OHLC + every enabled indicator's
  value at the hovered bar
- A separate canvas overlay drawn on top of the price series (not part of the
  charting library itself) is what renders zones, alarms, drawings, and ICT
  markers — this maps directly to pyqtgraph's approach of layering
  `LinearRegionItem`/`TextItem`/custom `GraphicsObject`s over the plot, which the
  architecture doc already anticipated
- "Magnet mode" (snap drawing points to OHLC values) and fullscreen toggle

### 2.2 Indicators / Studies (`marketData.ts`, `StudiesModal.tsx`)
A studies browser lets the user add/configure any of:
- **SMA, EMA** — arbitrary period, source (close/open/high/low/hl2/hlc3)
- **VWAP** — session-anchored
- **Bollinger Bands** — period + std-dev multiplier, upper/middle/lower
- **RSI** — period
- **MACD** — fast/slow/signal periods, histogram coloring
- `atr` exists as a declared `IndicatorType` but is **not exposed as a standalone
  study** — it's only used internally as a helper inside the ICT calculations
  (displacement/sizing thresholds). Don't build a user-facing ATR study unless you
  want to add one beyond parity.
- **Supply/Demand Zones** — manually defined price bands (top/bottom/label/color),
  editable, toggleable
- **RTH Gap Tracker** — detects regular-trading-hours session gaps and tracks
  "staircase" mitigation as price fills them back in, with configurable
  extend-bars/min-ticks/max-gaps/colors
- **VIX Standard Deviation (expected move)** — computes a daily expected-move band
  from a volatility index (VIX/VXN/RVX/VXD, or a manual override %), anchored to
  previous close or session open, drawn at ±0.5σ/1σ/2σ/3σ
- **ICT Concepts** (LuxAlgo-style, the single largest study — `ictStudies.ts`,
  868 lines): market structure lines (MSS/BOS), order blocks + "breaker" blocks,
  Fair Value Gaps + Balanced Price Range, buyside/sellside liquidity pools,
  volume imbalance zones, New Week/New Day opening gaps (NWOG/NDOG), displacement
  markers, and killzone time ranges (NY/London Open/London Close/Asian) — each
  with its own show/hide flags, colors, and thresholds (~35 configurable params)

This is a substantial, self-contained calculation library with no UI dependency —
port the math into `services/indicator_service.py` (SMA/EMA/VWAP/Bollinger/RSI/
MACD), `services/gap_vix_service.py` (RTH gaps + VIX bands), and
`services/ict_service.py` (the ICT suite), each a near-line-for-line translation
from the TS since the algorithms are pure numeric transforms.

### 2.3 Drawing Tools (`DrawingActionBar.tsx`, `DrawingGroupsModal.tsx`, `drawingService.ts`)
- Tools: cursor, crosshair, trendline, horizontal line, zone (rectangle),
  Fibonacci, measure
- Drawings can be grouped into named, colored, lockable **Drawing Sets** per
  ticker (auto-numbered `DrawingSet_1`, `DrawingSet_2`, ... or user-renamed)
- Bulk actions: group selection, ungroup, delete selection, recolor, toggle a
  group's visibility, rename a group

### 2.4 Alarms (`AlarmModal.tsx`, `alarmStorage.ts`)
- Price alarms per symbol with condition `cross_above` / `cross_below` /
  `cross_either`, optional note, optional sound, active/inactive toggle
- "Alarm mode": click directly on the chart to open the alarm dialog pre-filled
  with that price
- Persisted per-ticker (their `localStorage` → our SQLite `alarms` table),
  auto-seeded with a sensible default alarm set the first time a ticker is opened
- Trigger produces a toast notification plus an optional chime; a triggered
  alarm can be "rearmed" (reset to untriggered)

### 2.5 Watchlist / Sidebar (`Sidebar.tsx`)
- Resizable sidebar (drag handle, persisted width) with tabs: **Watchlist**,
  **Active Trader**, **Depth**
- Ticker categories: FUTURES, EQUITIES, INDICES, CRYPTO
- Symbol search that adds a new symbol on the fly if not already in the list
- A vertically resizable split between the watchlist and the Active Portfolio
  panel underneath it

### 2.6 Market Depth / DOM (`MarketDepth.tsx`)
- Ladder view and book view, switchable
- Configurable depth (number of rows), cumulative-size toggle, price flash
  animation on level updates, "institutional block" highlighting for unusually
  large size at a level
- **Click-to-trade**: clicking a price on the bid column places a BUY limit at
  that price; clicking the ask column places a SELL limit; dedicated MKT
  buy/sell buttons; an order-quantity stepper shared with the rest of the app
- In the source repo this is entirely simulated (deterministic pseudo-random
  size generator) — the real version replaces that generator with live
  `reqMktDepth` data (Section 9.5) and keeps the same interaction model

### 2.7 Active Portfolio / Positions (`ActivePortfolio.tsx`, `StopLossTargetModal.tsx`, `TradeContextMenu.tsx`, `types/portfolio.ts`)
- Positions table: symbol, qty (signed, long/short), avg price, contract type
  (futures/stock/option), point multiplier, per-position stop-loss/take-profit
- Multi-select + right-click context menu
- **Automatic multi-leg option strategy detection** (`detectOptionStrategy`):
  given 2 selected option legs on the same underlying it identifies Put Credit
  Spread (PCS), Put Debit Spread (PDS), Call Credit Spread (CCS), or Call Debit
  Spread (CDS) by comparing strikes and long/short sides; 4 legs (2 puts + 2
  calls) are identified as an Iron Condor; anything else falls back to a
  "Custom Group." Grouped legs get a `TradeGroup` with a shared name/strategy
  label and an optional group-level stop-loss/take-profit.
- Actions: close one position, close several selected, close an entire group,
  "Flatten All," open the stop-loss/take-profit dialog per position or per group
- A position's stop-loss/take-profit maps to a real **bracket order** in IBKR
  terms — see Section 9.4 for how that's implemented with `ibapi` (which, unlike
  a broker-native "bracket order" button, requires you to construct the linked
  orders yourself via an OCA group).

### 2.8 Title Bar (`TitleBar.tsx`)
Custom top bar with app-level tabs and a clock. Also has stream-control affordances
(play/pause, stream speed, "flash spike," "reset data") — **these four are
artifacts of the mock data engine and should not be ported as-is.** The one worth
keeping in spirit is play/pause, repurposed as "pause/resume live UI updates"
(stop repainting without unsubscribing from IBKR) — see Section 18 for the full
do-not-port list.

---

## 3. Critical Architecture Deviation: `ibapi` vs `ib_insync`

The original architecture doc's Section 3 says qasync lets asyncio and Qt's loop
run together "so no manual thread-safety plumbing (queues, locks) is needed."
**That statement is true only for ib_insync/ib_async, not for the official API**,
and does not hold here.

`ibapi` works like this:

- You subclass `EWrapper` (receives callbacks) and `EClient` (sends requests) into
  one class, e.g. `IBApiClient(EWrapper, EClient)`.
- `client.connect(host, port, clientId)` opens the socket; `client.run()` starts a
  **blocking** read loop that must live on its own thread — never the Qt main thread.
- Every callback (`tickPrice`, `historicalData`, `orderStatus`, `updateMktDepth`, …)
  fires **on that background reader thread**, not on the GUI thread.
- There is no event-loop merging available (no asyncio involved at all), so the
  "single event loop" simplification from the source doc does not apply.

Consequences this plan bakes in from the start:

1. **Thread bridge is mandatory.** A `QObject` subclass (`ibkr/bridge.py`) exposes a
   `pyqtSignal` per callback type. `EWrapper` overrides call `self.bridge.tick_price.emit(...)`
   instead of touching UI/DB directly. Because the receiving `QObject`s live on the
   GUI thread (which runs an event loop), PyQt automatically delivers the signal via
   a **queued connection** — this is the thread-safety mechanism that replaces
   qasync in the original design. All widget updates and all SQLite writes happen
   in slots on the main thread only.
2. **Request pacing is your responsibility.** `ib_insync`/`ib_async` internally
   throttle and dedupe requests; the official API does not. You must implement a
   pacing layer (`ibkr/pacing.py`) — see Section 10.
3. **`reqId` / `orderId` sequencing is manual.** The API hands you the first valid
   order id via `nextValidId(orderId)`; every subsequent unique request needs a
   locally-incremented id. Centralize this in `ibkr/id_manager.py`.
4. **No native multi-timeframe real-time bars.** `reqRealTimeBars` only ever returns
   5-second bars. Any other timeframe (1m, 5m, 15m, 4h, …) must be aggregated
   client-side: `data/bar_aggregator.py`.
5. **Error routing is manual.** `error(reqId, errorCode, errorString, ...)` fires for
   everything from benign status info (market data farm connection messages) to
   fatal problems (duplicate reqId, pacing violations, rejected orders). You need a
   classification table (`ibkr/error_codes.py`).
6. **Bracket / OCA orders are manual.** The repo's per-position and per-group
   stop-loss/take-profit UI (Section 2.7) implies bracket orders. With `ibapi` you
   build this yourself: place the parent order with `transmit=False`, then the
   stop and limit child orders sharing an `ocaGroup` string (One-Cancels-All) with
   the last one `transmit=True`. There's no single "bracket order" call.

Net effect: expect noticeably more networking/plumbing code than the original doc
implied, in exchange for zero third-party runtime dependency risk and an API
surface IBKR guarantees to support. (Context: `ib_insync`'s original author passed
away in 2024 and the repo is now archived; the community continues it as
`ib_async`. Neither is official — this plan uses neither.)

---

## 4. Revised Tech Stack

| Layer | Choice | macOS notes |
|---|---|---|
| UI framework | PyQt6 | Native wheels for arm64 via pip |
| Charting | pyqtgraph (custom `CandlestickItem`, plus Heikin-Ashi/line/area render modes) | OpenGL via Qt's `QGraphicsView` |
| IBKR connectivity | **`ibapi`** (official) | Install from IBKR's TWS API installer bundle (`IBJts/source/pythonclient`, `pip install .`) to guarantee version-matching with your installed TWS build; the PyPI `ibapi` package can lag behind — verify compatibility before relying on it alone |
| Concurrency | `threading` (reader thread) + Qt signals/slots (queued cross-thread delivery) | Replaces qasync entirely — do not add qasync as a dependency |
| Local persistence | SQLite via `sqlite3` (stdlib) or SQLAlchemy | All access from the Qt main thread only (Section 6) |
| Styling | QSS + hand-rolled dark theme | Force `QApplication.setStyle("Fusion")` + explicit palette so macOS light/dark system mode never overrides the ToS-style theme |
| Packaging | PyInstaller → `.app` bundle, arm64 only | No universal2/x86_64 target needed |
| IBKR connection software | **TWS Desktop**, installed separately by the user | Native Apple Silicon build from a recent release; keep it running and logged in while the app is used |

---

## 5. macOS Environment Setup

1. Install Python 3.11 (python.org universal2 installer, or `pyenv install 3.11.x`).
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install PyQt6 pyqtgraph`
4. Install `ibapi`:
   - Preferred: download the TWS API installer from IBKR's API page, then
     `cd IBJts/source/pythonclient && pip install .`
   - Alternative: `pip install ibapi` from PyPI, but confirm the version matches
     (or is compatible with) your installed TWS version.
5. Install **TWS Desktop** for macOS (Apple Silicon build) — the app the terminal
   connects to as a local socket client; never bundled into the app itself; must
   be running and logged in whenever the terminal is used.
6. In TWS: **Configure → Settings → API → Settings**:
   - Check "Enable ActiveX and Socket Clients"
   - Leave "Read-Only API" **checked** through Phases 1–5; uncheck only once
     Phase 6 (order placement) is ready to test
   - Confirm socket port: `7496` (live)
   - Add `127.0.0.1` to "Trusted IPs"
7. Use a current stable TWS release — IBKR has raised the minimum supported
   version over time (10.30+ as of the March 2025 changelog).
8. TWS Desktop shows its own full trading UI and will periodically prompt to
   auto-restart/update — configure **Configure → Lock and Exit** to a predictable
   daily restart time, and plan for the reconnect logic in Section 9.7 to absorb
   that restart gracefully rather than treating it as an error. Also check for an
   option to suppress update-check popups, since an unattended dialog can block
   the API connection.
9. `pip freeze > requirements.txt` once the above is working; commit it.

---

## 6. Concurrency & Threading Model

```
┌─────────────────────────────── Main (Qt/GUI) thread ───────────────────────────────┐
│  QApplication event loop                                                            │
│  ┌───────────────┐   queued signal   ┌────────────────────┐                         │
│  │  UI widgets    │◄──────────────────│  IBBridge (QObject) │                        │
│  │ (chart, table, │   connections     │  pyqtSignal per     │                        │
│  │  alarms, DOM,  │                   │  EWrapper callback  │                        │
│  │  portfolio)    │                   │                     │                        │
│  └───────┬───────┘                   └──────────▲──────────┘                        │
│          │                                       │ .emit(...) called from            │
│  ┌───────▼───────┐                               │ the OTHER thread, safely          │
│  │ SQLite writer  │                               │ queued by Qt                     │
│  │ (main-thread   │                               │                                  │
│  │  only access)  │                               │                                  │
│  └───────────────┘                               │                                  │
└───────────────────────────────────────────────────┼──────────────────────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼──────────────────── Reader thread ─┐
│  IBApiClient(EWrapper, EClient)                      │                                    │
│  client.run()  — blocking socket read loop  ─────────┘  (EWrapper overrides call          │
│                                                            self.bridge.<signal>.emit(...)) │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Rules to enforce in code review / tests:

- Nothing in `ibkr/*` may import from `PyQt6.QtWidgets`. It may only emit signals
  via `bridge.py`.
- No SQLite connection object is ever created on the reader thread.
- `id_manager.py` uses a `threading.Lock`-guarded counter, seeded by `nextValidId`.

---

## 7. Revised Module / Folder Structure

```
trading_app/
├── main.py                       # creates QApplication, IBApiClient, starts reader thread, shows MainWindow
├── config/
│   ├── settings.py               # host/port/clientId, defaults to live trading on 7496, env-based
│   └── theme.qss
├── ibkr/
│   ├── client.py                 # IBApiClient(EWrapper, EClient); connect/run/reconnect lifecycle
│   ├── bridge.py                 # QObject subclass; one pyqtSignal per callback type
│   ├── id_manager.py             # thread-safe reqId / orderId sequencing
│   ├── pacing.py                 # request throttler (Section 10)
│   ├── error_codes.py            # classify info / warning / fatal error codes
│   ├── market_data.py            # reqMktData / reqHistoricalData wrappers
│   ├── realtime_bars.py          # reqRealTimeBars (5s bars only)
│   ├── market_depth.py           # reqMktDepth for DOM
│   ├── orders.py                 # Order/Contract building; single, bracket (OCA), and multi-leg combo orders
│   ├── contracts.py              # reqContractDetails-based qualification/lookup, incl. option chains
│   └── account.py                # reqAccountSummary, reqPositions
├── ui/
│   ├── main_window.py
│   ├── title_bar.py               # app tabs, clock, pause/resume live updates
│   ├── chart_header.py            # symbol search, timeframe, chart type, studies, zones, drawing tool, crosshair, alarm mode
│   ├── bottom_toolbar.py          # range bar / zoom controls
│   ├── watchlist_panel.py
│   ├── chart_panel.py             # pyqtgraph chart + volume subplot
│   ├── candlestick_item.py        # candles / hollow candles / Heikin-Ashi / line / area render modes
│   ├── price_scale_overlay.py     # floating current-price tag + crosshair data window (OHLC + live indicator values)
│   ├── zone_overlay.py            # supply/demand zones
│   ├── alarm_overlay.py           # alarm lines + alarm-mode click-to-set
│   ├── drawing_overlay.py         # trendline / horizontal / zone(rect) / fibonacci / measure tools
│   ├── drawing_groups_dialog.py   # drawing-set management (group/ungroup/rename/recolor/visibility)
│   ├── studies_dialog.py          # studies browser + per-study parameter forms (mirrors StudiesModal.tsx)
│   ├── alarm_dialog.py            # add/edit alarm
│   ├── active_trader_panel.py     # DOM / order ladder, click-to-trade
│   ├── active_portfolio_panel.py  # positions table, multi-select, context menu, flatten all
│   ├── stop_loss_target_dialog.py # per-position / per-group bracket SL/TP entry
│   └── trade_context_menu.py      # right-click menu on a position/group
├── data/
│   ├── db.py                      # SQLite schema + access layer (main-thread only)
│   ├── bar_cache.py
│   ├── bar_aggregator.py          # builds 1m/5m/15m/1h/4h/... from 5s real-time bars
│   └── models.py                  # Bar, Alarm, Zone, DrawingGroup, UserDrawing, Position, TradeGroup, OptionDetails dataclasses
├── services/
│   ├── alarm_service.py           # evaluates price vs alarm levels, cross_above/below/either
│   ├── indicator_service.py       # SMA, EMA, VWAP, Bollinger, RSI, MACD
│   ├── gap_vix_service.py         # RTH gap tracker + VIX standard-deviation expected-move bands
│   ├── ict_service.py             # market structure, order blocks, FVG/BPR, liquidity, volume imbalance, NWOG/NDOG, displacement, killzones
│   ├── strategy_detection_service.py  # port of detectOptionStrategy: PCS/PDS/CCS/CDS/Iron Condor/Custom
│   └── sound_service.py           # order-fill sound, alarm chime (QSoundEffect)
└── packaging/
    └── build.spec                 # PyInstaller, macOS .app target, arm64
```

---

## 8. Feature Specs Ported From the Repo

Each subsection maps a repo feature (Section 2) to its concrete Python
implementation approach.

### 8.1 Multi chart-type rendering
`candlestick_item.py` needs 5 render modes sharing one `CandleData` model:
candles, hollow candles (body outline-only when close ≥ open), Heikin-Ashi
(computed transform: `haClose=(o+h+l+c)/4`, `haOpen` recursive from prior HA
bar), line (close-only), area (close-only, filled). Compute Heikin-Ashi as a
derived series in `bar_aggregator.py` or a small `heikin_ashi.py` helper, not
inside the paint code, so it can be unit-tested against the TS version's math.

### 8.2 Indicators / Studies dialog
`studies_dialog.py` is a `QDialog` with two tabs — Studies and Zones — mirroring
`StudiesModal.tsx`: a browsable list of available studies (SMA, EMA, VWAP,
Bollinger, RSI, MACD, RTH Gap Tracker, VIX SD, ICT Concepts) each opening a
parameter form specific to that study (period/source for SMA/EMA, std-dev for
Bollinger, fast/slow/signal for MACD, the ~10 RTH-gap params, the ~10 VIX-SD
params, the ~35 ICT params). Store the active list as `IndicatorConfig`-equivalent
dataclasses in `data/models.py`; persist enabled studies + their params per
symbol in SQLite so they survive restarts (the repo currently seeds sensible
defaults on first load — replicate that with a `DEFAULT_INDICATORS` constant).

### 8.3 Drawing tools + groups
`drawing_overlay.py` handles mouse interaction for trendline/horizontal/zone/
fibonacci/measure directly against the pyqtgraph `ViewBox` coordinate transform
(chart-time ↔ pixel, price ↔ pixel) — this is the same problem the repo solves
with a canvas overlay synced to the TradingView chart's time/price scale, just
with Qt's coordinate APIs instead of canvas ones. `drawing_groups_dialog.py` and
`data/models.py`'s `DrawingGroup`/`UserDrawing` are near-direct ports of
`drawingService.ts` and `types/market.ts`'s equivalents — group numbering,
default naming (`DrawingSet_#`), color palette, lock/visibility flags all
translate as-is.

### 8.4 Alarms
`services/alarm_service.py` ports the exact crossing logic from `App.tsx`'s
`checkAndTriggerAlarms`: compare `prevPrice`/`newPrice` against each active,
untriggered alarm's condition, fire on `cross_above`/`cross_below`/`cross_either`,
play a chime via `sound_service.py` if enabled, and mark triggered (with a
"rearm" action to reset it). `alarm_dialog.py` replicates `AlarmModal.tsx`
including alarm-mode (click the chart to prefill a price). Persist via the
`alarms` SQLite table (Section 12) instead of `localStorage`, keyed by symbol.

### 8.5 DOM / Active Trader (real data + click-to-trade)
`active_trader_panel.py` keeps the repo's ladder/book toggle, depth-level
selector, cumulative-size display, and click-to-trade interaction model, but the
underlying rows are populated from `ibkr/market_depth.py`'s `reqMktDepth`
callbacks instead of the repo's pseudo-random generator. Clicking a bid/ask row
builds a `LMT` order at that price via `ibkr/orders.py`; the MKT buy/sell buttons
build `MKT` orders. This **requires a live market-depth/Level II entitlement** on
the account — confirm before investing UI polish here (Section 0).

### 8.6 Active Portfolio (positions, multi-leg grouping, bracket SL/TP)
`active_portfolio_panel.py` + `strategy_detection_service.py` port
`ActivePortfolio.tsx` and `detectOptionStrategy` essentially line-for-line — it's
pure logic (compare option type/strike/side across 2 or 4 selected legs) with no
framework dependency. Positions themselves come from `ibkr/account.py`'s
`reqPositions`; the `TradeGroup` label/strategy-type association is **local-only
metadata** (IBKR doesn't have a "labeled spread group" concept) stored in a new
`trade_groups` SQLite table, mapping a set of IBKR position/contract ids to a
group. Per-position/per-group stop-loss/take-profit (`stop_loss_target_dialog.py`,
mirroring `StopLossTargetModal.tsx`) becomes a real bracket order — see Section
9.4 for the OCA mechanics. "Flatten All" iterates open positions and sends
opposing market orders for each.

---

## 9. Data Flow Specs (`ibapi`)

### 9.1 Startup / Connection
1. `main.py` instantiates `IBApiClient`, calls `client.connect(host, port, clientId)`.
2. Start `threading.Thread(target=client.run, daemon=True)`.
3. Wait for `nextValidId(orderId)` → seed `id_manager` → emit
   `bridge.connected.emit()` → toolbar status badge updates.
4. `error()` codes 2104/2106/2158 ("market data farm connection is OK") are
   **status**, not failures — route to the status bar, not an error toast.

### 9.2 Historical Backfill
1. `contracts.py` resolves/qualifies the symbol via `reqContractDetails`.
2. `market_data.py` calls `reqHistoricalData(reqId, contract, endDateTime="",
   durationStr, barSizeSetting, whatToShow="TRADES", useRTH, formatDate=2,
   keepUpToDate=False, chartOptions=[])`.
3. `historicalData(reqId, bar)` fires per bar → buffered; `historicalDataEnd`
   → `bridge.bars_received.emit(reqId, bars)`.
4. Main-thread slot writes to SQLite (`bar_cache.py`) and populates the chart.
5. On reopening a previously-viewed chart, read from SQLite first and only
   request the incremental gap from IBKR (reduces pacing pressure — Section 10).

### 9.3 Live Updates
- **`reqMktData`** → `tickPrice`/`tickSize`: drives the watchlist (last, bid,
  ask, volume) and price-scale overlay.
- **`reqRealTimeBars`** (5s only) → `realtimeBar`: feeds `bar_aggregator.py`,
  which rolls 5-second bars up into the active chart's timeframe, then emits
  `bridge.bar_updated` to repaint just the last candle (or append a new one on
  period rollover).

Update chain per tick/bar: in-memory model → watchlist row (flash green/red) →
chart candle repaint → volume subplot → `AlarmService.check(symbol, price)` →
visual/audio alert if a level is crossed.

### 9.4 Order Placement (single, bracket, multi-leg)
- **Single order**: build `Contract` + `Order`, get the next id from
  `id_manager`, call `client.placeOrder(orderId, contract, order)`.
- **Bracket (stop-loss / take-profit)**: place the parent (entry) order with
  `transmit=False`; place a `STP` order and a `LMT` order as children, both
  referencing `parentId=<parent orderId>` and sharing the same `ocaGroup` string
  with `ocaType=1` (cancel all remaining on fill); the **last** order submitted
  gets `transmit=True` so the whole group releases together. This is the
  official-API equivalent of a broker-native "bracket order" button.
- **Multi-leg (spreads / Iron Condor)**: either (a) submit each leg as its own
  order and rely on `strategy_detection_service.py` purely for local grouping/
  labeling, or (b) build a true combo order using `ComboLeg`s on a `BAG`
  security type for a single-ticket spread fill. Start with (a) for Phase 6b —
  it's simpler and matches how the repo's UI actually behaves (it groups
  already-existing positions after the fact, it doesn't submit a single combo
  ticket) — and treat (b) as a stretch goal.
- Callbacks `orderStatus`, `openOrder`, `execDetails`, `commissionReport` fire on
  the reader thread → bridged to signals → Orders/Positions panel updates.
- Maintain an **open-orders registry** keyed by orderId so `orderStatus` updates
  can find the right UI row without re-querying IBKR.

### 9.5 Market Depth / DOM
1. `market_depth.py` calls `reqMktDepth(reqId, contract, numRows, isSmartDepth,
   mktDepthOptions=[])`.
2. `updateMktDepth`/`updateMktDepthL2` → `bridge.depth_updated` → ladder
   repaints bid/ask rows by `position` index.
3. Requires a real market depth/Level II entitlement (Section 0).

### 9.6 Account / Positions
- `reqAccountSummary(reqId, "All", "NetLiquidation,TotalCashValue,...")` for the
  toolbar's account/net-liq/P&L labels.
- `reqPositions()` → `position(...)`/`positionEnd()` for the Positions panel.

### 9.7 Reconnection
- Poll `client.isConnected()` on a `QTimer` (2–5s) and override
  `connectionClosed()`.
- On disconnect: "Reconnecting…" status, exponential-backoff `connect()` retries.
- On reconnect: **replay a subscription registry** (watchlist symbols, the open
  chart's `reqMktData`/`reqRealTimeBars`, any open DOM) — IBKR does not remember
  prior subscriptions across a fresh socket.
- **TWS-specific**: since TWS (not Gateway) is the target, budget time in Phase 7
  to handle its daily auto-restart/auto-logoff (Configure → Lock and Exit) as a
  routine, expected disconnect rather than an error condition, and to minimize
  update-check popups that could otherwise block the API unattended.

---

## 10. Pacing & Rate Limits

Per IBKR's current documentation:
- Overall request budget: **(Market Data Lines ÷ 2) requests/second** — 50/sec by
  default (100 market data lines default allotment); scales with more lines.
- **5-second real-time bars**: no more than **60 new subscription requests per
  10 minutes**; total active subscriptions capped by market data line allotment.
- **Historical data**: hard caps on bar counts for 1-minute+ bars have been
  lifted, but soft throttling still applies for load balancing — avoid
  re-requesting identical historical data in quick succession; prefer the
  "read cache, request only the gap" pattern from Section 9.2.

Build `ibkr/pacing.py` as a token-bucket/min-interval gate that every outbound
`req*` call passes through, configurable per request type. Treat the numbers
above as current-as-of-writing and re-check IBKR's live "Pacing Limitations" and
"Historical Data Limitations" docs before finalizing constants.

---

## 11. Error Handling

Override:
```python
def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
    ...
```
Route through `error_codes.py`, classifying into:
- **Informational/status** (market data farm connection messages) → status bar only
- **Warnings** (delayed data instead of real-time, order warnings) → toast/log
- **Fatal for the current request** (duplicate reqId, pacing violation, rejected
  order, invalid contract) → surface near the relevant panel (e.g. inline on the
  order ticket) and log with reqId/context

Route unknown codes to "warning" rather than silently swallowing them.

---

## 12. SQLite Schema

```sql
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
    type TEXT NOT NULL,           -- 'sma','ema','vwap','bollinger','rsi','macd','rth_gaps','vix_sd','ict'
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
    ibkr_position_id TEXT NOT NULL,   -- local composite key (account+conId) since IBKR has no native "position id"
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
```

All writes/reads go through `data/db.py` on the main thread only (Section 6). Note
`trade_groups`/`position_group_map` are purely local labeling metadata layered on
top of IBKR's actual positions — IBKR has no concept of a labeled spread group.

---

## 13. UI Layout

```
QMainWindow
 ├── TitleBar (custom top strip): app tabs, clock, pause/resume live updates
 ├── ChartHeader (chart sub-toolbar): symbol search, timeframe buttons,
 │     chart-type dropdown (candles/hollow/heikin/line/area), Studies button,
 │     zones toggle, drawing-tool picker, crosshair toggle, fullscreen toggle,
 │     alarm-mode toggle + alarms manager, drawing-sets manager
 ├── QDockWidget (left, resizable, tabbed): Watchlist / Active Trader / Depth
 │     - Watchlist: QTableWidget (symbol, last, net chg), category grouping
 │     - Active Trader: order entry (qty, MKT/LMT, buy/sell)
 │     - Depth: ladder/book DOM (Section 8.5)
 ├── Active Portfolio panel (below/tabbed with watchlist, resizable split):
 │     positions table, context menu, flatten-all, bracket SL/TP dialog
 ├── Central: Chart Panel
 │     - pyqtgraph PlotWidget (candles + overlays: studies, zones, drawings, alarms)
 │     - pyqtgraph PlotWidget (volume, X-axis linked to chart above)
 │     - crosshair data window (OHLC + live indicator values)
 ├── BottomToolbar: range bar (1D/5D/1M/.../ALL), zoom controls
 └── Status bar: TWS connection status, data reliability indicator
```

All docks remain `QDockWidget` so panels can be rearranged/floated.

---

## 14. Styling (Tailwind-Inspired Look & Feel)

The web UI uses a highly dense, professional dark mode. The QSS should strictly implement this exact palette and typography rather than a generic dark theme.

**Typography (Dense Layout):**
- Base font size is extremely small (10px, 10.5px, 11px) to maximize data density, typical of pro trading software.
- Tabular-figure or monospace font must be used for all numeric columns so digits align vertically.
- Font families: Clean sans-serif (e.g. Inter, Segoe UI) with a monospace fallback for data grids.

**Color Palette (Cool Dark Tones):**
- **App Backgrounds:** Use deep blue-grays: `#0d0f14`, `#101218`, `#141822`.
- **Borders & Separators:** `#232938`, `#2b3345`.
- **Text:** Primary text is a muted neutral (equivalent to Tailwind `neutral-400`), with brighter neutrals (`neutral-200`) for headers/active values.
- **Accents:** 
  - Positive/Up: Tailwind `emerald-400` / `emerald-500`
  - Negative/Down: Tailwind `red-400` / `red-500`
  - Warning/Alert: Tailwind `amber-400` / `amber-500`

**Implementation rules:**
- Global QSS (`config/theme.qss`) implements the palette above.
- Configure pyqtgraph explicitly:
  `pg.setConfigOption('background', '#0d0f14')`
  `pg.setConfigOption('foreground', '#a3a3a3')`
- Force `QApplication.setStyle("Fusion")` with an explicit `QPalette` mapping to these exact hex codes, so macOS Light Mode never overrides the theme.
- Keep native macOS window chrome (traffic-light buttons) but place the `TitleBar.tsx` equivalent (app tabs, clock, status) immediately below it as a dense top toolbar.

---

## 15. Packaging on macOS

1. `pyinstaller --windowed --name "IBKR Terminal" --osx-bundle-identifier
   com.yourname.ibkrterminal --target-arch arm64 main.py`
2. Single arm64 build — no x86_64/universal2 target needed.
3. Code sign (ad-hoc is enough for personal/local use; a real Apple Developer ID
   + notarization is needed to distribute the `.app` to others, or Gatekeeper
   will block it).
4. TWS is **not** bundled — the user installs and logs into it separately.
5. Test the packaged `.app` on a clean macOS user account (no dev Python/venv) to
   catch missing bundled resources (QSS file, icons, SQLite file path assumptions).

---

## 16. Implementation Phases

Build in this order; each phase should be independently testable against live
trading TWS before moving on.

| Phase | Goal | Key files | Acceptance check |
|---|---|---|---|
| 0 | Scaffold repo, venv, config | `main.py`, `config/settings.py` | App launches, empty window |
| 1 | Connection + threading bridge | `ibkr/client.py`, `bridge.py`, `id_manager.py`, `pacing.py`, `error_codes.py` | Connects to live TWS on 7496; `nextValidId` logged; status badge updates |
| 2 | Historical data + cache + static chart | `contracts.py`, `market_data.py`, `data/db.py`, `bar_cache.py`, `chart_panel.py`, `candlestick_item.py` (candles mode only) | Chart renders real historical candles for a test symbol, cached in SQLite |
| 3 | Live updates + watchlist | `realtime_bars.py`, `bar_aggregator.py`, `watchlist_panel.py` | Last candle updates live without UI stutter; watchlist ticks update |
| 4 | Chart-type variants + studies core | `candlestick_item.py` (hollow/heikin/line/area), `indicator_service.py`, `studies_dialog.py` | SMA/EMA/VWAP/Bollinger/RSI/MACD toggle on/off and render correctly across chart types |
| 5 | Zones, alarms, drawing tools | `zone_overlay.py`, `alarm_overlay.py`, `alarm_service.py`, `alarm_dialog.py`, `drawing_overlay.py`, `drawing_groups_dialog.py` | Alarm fires visually/audibly on a live crossing; drawings persist and can be grouped |
| 6a | Advanced studies (Gap/VIX/ICT) | `gap_vix_service.py`, `ict_service.py` | RTH gap tracker and VIX bands render; at least market-structure + order-block ICT markers render correctly on a known test dataset |
| 6b | DOM + order entry (single + bracket) | `market_depth.py`, `active_trader_panel.py`, `orders.py` (single + OCA bracket) | Order round-trips through `orderStatus`/`execDetails`; a bracket SL/TP correctly cancels its sibling on fill (contingent on depth entitlement for the DOM half — Section 0) |
| 6c | Active Portfolio + multi-leg grouping | `account.py`, `active_portfolio_panel.py`, `strategy_detection_service.py`, `stop_loss_target_dialog.py`, `trade_context_menu.py` | Selecting 2 matching option legs auto-labels the correct spread type; Flatten All closes every open position |
| 7 | Reconnect, hardening, packaging | `client.py` reconnect logic, `build.spec` | Survives a manual TWS restart/relogin; packaged `.app` runs on a clean macOS account |

---

## 17. Test / QA Checklist

- [ ] Connects reliably on live TWS port 7496
- [ ] Historical chart loads and correctly reads-through-cache on reopen
- [ ] Live tick/bar stream does not block or stutter the UI thread
- [ ] All 5 chart-type render modes (candles/hollow/heikin/line/area) draw correctly from the same underlying bar data
- [ ] Each study (SMA/EMA/VWAP/Bollinger/RSI/MACD/RTH Gaps/VIX SD/ICT) matches the reference TS math on a fixed test dataset
- [ ] Alarm triggers exactly once per crossing and can be muted/rearmed
- [ ] Drawing tools persist across restart and can be grouped/ungrouped/recolored
- [ ] DOM ladder updates from real `reqMktDepth` data (or is clearly disabled with a message if the account lacks the entitlement)
- [ ] Placing, modifying, and cancelling an order all reflect correctly in the UI
- [ ] A bracket SL/TP order correctly cancels its sibling leg on fill (OCA behavior)
- [ ] Selecting matching option legs correctly auto-detects PCS/PDS/CCS/CDS/Iron Condor
- [ ] App recovers automatically from a TWS restart/relogin without a manual app relaunch
- [ ] Packaged `.app` runs standalone on a clean macOS account with no dev environment
- [ ] No SQLite access or Qt widget mutation ever happens off the main thread (code review item)

---

## 18. Explicitly Out of Scope / Not Ported As-Is

- **`@google/genai` (Gemini) dependency** — present in `package.json` but unused
  anywhere in the repo's source. No AI feature exists to port.
- **Stream-speed slider, "Flash Spike" button, "Reset Data" button**
  (`TitleBar.tsx`) — these exist purely to control/demo the mock random-walk
  price engine. They have no equivalent once real IBKR data is wired in; don't
  build UI for them.
- **The pseudo-random DOM size generator** (`MarketDepth.tsx`) — replaced
  entirely by real `reqMktDepth` data (Section 8.5); none of its "institutional
  block" heuristic logic should be ported.
- **`localStorage` as a persistence mechanism** — replaced by SQLite throughout
  (Section 12); only the *shape* of what's persisted carries over.
- Play/pause **is** worth keeping, just repurposed: "pause/resume live UI
  updates" (stop repainting while staying subscribed) rather than
  starting/stopping a fake data generator.

---

## 19. Confirm Before Starting Heavy Build Work

**(All items confirmed prior to development)**
1. **Market data entitlements:** Level II / Depth enabled (Phase 6b DOM is fully scoped).
2. **Options trading:** Approved and in scope (Phase 6c multi-leg grouping and option chains are fully scoped).
3. **Environment:** Default target is Live trading on port 7496.
