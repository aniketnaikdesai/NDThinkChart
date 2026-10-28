# NDThinkChart — Usage Guide

A PyQt6 trading terminal for Interactive Brokers TWS with two chart engines — **pyqtgraph** (the default) and **Lightweight Charts** (served through QtWebEngine) — and the official `ibapi`.

---

## Prerequisites

- **macOS 11+ (Big Sur)** on Apple Silicon (ARM64)
- **Python 3.11+** (managed via pyenv recommended)
- **Interactive Brokers TWS** installed and running
- **TWS API port 7496** enabled (Live trading — *no paper mode*)

---

## Quick Start (Development)

```bash
# 1. Clone / cd into project
cd NDThinkChart

# 2. Create venv and install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
# requirements.txt pins PyQt6-WebEngine to the installed PyQt6 version.
# Keep those two in step when you upgrade PyQt6.

# 3. Ensure TWS is running on port 7496
#    TWS → Edit → Global Configuration → API → Settings
#    ✅ Enable ActiveX and Socket Clients
#    Socket port: 7496
#    ✅ Allow connections from localhost only

# 4. Run the app
QT_QPA_PLATFORM=offscreen python main.py   # headless (CI)
python main.py                              # normal GUI
```

---

## Production Build (macOS .app)

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build the .app bundle
pyinstaller --windowed --onedir \
  --name "NDThinkChart" \
  --osx-bundle-identifier com.ndthinkchart.app \
  --add-data "config/theme.qss:config" \
  main.py

# 3. Find the bundle
open dist/TOS\ Charting.app
```

The bundle is self-contained:
- **Theme**: `Contents/Resources/config/theme.qss`
- **Database**: `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`
- **Logs**: same directory as DB

---

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `IBKR_HOST` | `127.0.0.1` | TWS host |
| `IBKR_PORT` | `7496` | TWS socket port (Live only) |
| `IBKR_CLIENT_ID` | `1` | Unique client ID per session |
| `DB_PATH` | `charting_app.sqlite3` | SQLite path (dev); overridden in bundle |
| `NDT_CHART_ENGINE` | unset (pyqtgraph) | Chart engine. Set to `lwc` for the Lightweight Charts engine; any other value — including unset — keeps pyqtgraph |

```bash
# Example: custom port + client ID
IBKR_PORT=7496 IBKR_CLIENT_ID=123 python main.py
```

---

## Chart Engines

The app ships two renderers behind one `create_chart_view` seam:

- **pyqtgraph** — the default. Unchanged behaviour, and what every run uses unless you opt in.
- **Lightweight Charts (LWC)** — the new renderer, served through an offline QtWebEngine page. Feature parity is complete, but it has not yet been through a live trading session, so pyqtgraph stays the default until that cutover is accepted and pyqtgraph is removed.

Opt in per run:

```bash
NDT_CHART_ENGINE=lwc python main.py
```

An unset, blank or unknown `NDT_CHART_ENGINE` value keeps the pyqtgraph engine, so a typo never blanks the chart.

**Size:** the LWC engine needs `PyQt6-WebEngine`, which adds about **292 MB** of QtWebEngine/Chromium frameworks to the packaged app — roughly **661 MB** versus **369 MB** without it (measured before PyInstaller packing). `PyQt6-WebEngine` must match the installed `PyQt6` version.

One live trading session is still owed before pyqtgraph is removed. Until then both engines are present, and pyqtgraph remains the default.

---

## TWS Setup Checklist

1. **Install TWS** from IBKR website (not IB Gateway)
2. **Login** with live credentials
3. **Enable API**:
   - Edit → Global Configuration → API → Settings
   - ✅ Enable ActiveX and Socket Clients
   - Socket port: **7496**
   - ✅ Allow connections from localhost only
   - ✅ Read-Only API (optional, for safety)
4. **Market Data Subscriptions** — ensure you have subscriptions for symbols you'll chart (e.g., US Equities, Options)

---

## UI Overview

| Area | Purpose |
|------|---------|
| **Toolbar** | Symbol input, timeframe, chart mode, studies, alarms, drawing tools |
| **Chart Panel** | Candlestick/Hollow/Heikin-Ashi/Line/Area charts with studies, drawings, alarms |
| **Watchlist (Left Dock)** | Symbol list with live ticks; double-click to load chart; collapse to a thin vertical bar via the **Watchlist** header button, click the bar to expand |
| **Portfolio (Right Dock)** | View-only: account summary, positions and P&L from TWS; no order entry, close or cancel controls |

---

## Key Workflows

### Load a Chart
1. Type symbol (e.g., `AAPL`) in toolbar
2. Select timeframe (1 min – 1 month, including 1 week and 1 month)
3. Click **Load Chart** or press Enter

### Collapse / Expand the Watchlist (Phase D44)
1. Click the **Watchlist** header button to collapse the dock — it shrinks to a thin vertical bar showing the rotated `WATCHLIST` label
2. Click the bar (or its handle) to expand it back to the width it held before collapsing
3. The collapse state is not persisted — the app always starts with the watchlist expanded

### Add Studies
1. Click **Studies…** button
2. Enable/disable indicators (SMA, EMA, Bollinger, RSI, MACD, VWAP, etc.)
3. Adjust parameters per study
4. Click **Apply** — cached automatically per symbol/timeframe

### Create Price Alarms
1. Click **Alarms (n)** button or press **Alarm Mode** then click chart
2. Set price, direction (above/below/either), sound, note
3. Alarms persist in DB and evaluate on live ticks

### Drawing Tools
1. Select tool from **Draw** dropdown: Trendline, Horizontal, Zone, Fibonacci, Measure
2. Click chart to place anchor points
3. Right-click drawing → **Delete** or drag handles to edit
4. Use **Sets…** to create named groups with color/lock/visibility

### Portfolio (view-only)
1. Open the **Portfolio** dock — it shows your account summary, positions and P&L
2. The panel is a readout only — there is no right-click action, no close/flatten control and no stop/target dialog
3. To close a position, cancel an order or close everything, do it in **TWS**: the app places, cancels and closes nothing
4. Group positions are auto-detected by option strategy (PCS, PDS, CCS, CDS, IC) for display only

---

## Database

- **Dev**: `./charting_app.sqlite3` (project root)
- **Bundle**: `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`

Tables:
- `bars` — cached historical data
- `watchlist` — persisted symbol list
- `alarms` — price alerts
- `drawings` / `drawing_groups` — chart annotations
- `studies` — per-symbol study configs
- `positions` / `trade_groups` — portfolio state. The stop-loss / take-profit (SL/TP) columns are dropped by a one-time migration the first time this version opens the database: nothing is settable, displayed or stored, and a pre-D46 database survives with every row intact and only those two values lost

---

## Testing

```bash
# Full suite -- run it for the current total (~25s offscreen)
python -m pytest tests/ -v

# Phase 10 core logic tests only (~0.2s)
python -m pytest tests/test_indicator_service.py tests/test_gap_vix_service.py \
  tests/test_ict_service.py tests/test_alarm_service.py tests/test_bar_aggregator.py \
  tests/test_strategy_detection.py tests/test_ui_smoke.py -v
```

All tests run **offscreen** (no display required) and **without TWS**.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Connection refused" | Verify TWS running, port 7496, API enabled |
| "Client ID already in use" | Change `IBKR_CLIENT_ID` env var |
| Theme not loading | Ensure `config/theme.qss` bundled (`pyinstaller --add-data`) |
| DB permission error | Check `~/Library/Application Support/NDThinkChart/` writable |
| Duplicate bars after reconnect | Fixed in Phase 8 — `_last_pushed_ts` guard in `BarAggregator` |
| `ModuleNotFoundError: ibapi` | `pip install -r requirements.txt` (the dist is `ibapi-latest`, which provides the `ibapi` module) |

---

## Architecture Notes

- **Pure logic services** (`services/*.py`) — no Qt, no I/O, fully tested
- **IBKR layer** (`ibkr/*.py`) — `IBApiClient` (EWrapper/EClient), pacing, subscriptions
- **Data layer** (`data/*.py`) — SQLite, cache, models, aggregation
- **UI layer** (`ui/*.py`) — PyQt6 widgets, docks, and the chart behind the
  `create_chart_view` seam (pyqtgraph default, Lightweight Charts opt-in)
- **Reconnect hardening** (D27.3) — connection state machine (DISCONNECTED /
  CONNECTING / CONNECTED / RECONNECTING); `_do_reconnect` re-issues the real
  `EClient.connect` with the stored host/port/clientId on exponential backoff
  (the poll timer does not re-arm while a reconnect is pending); live
  subscriptions are type-tagged in `SubscriptionManager` and replayed with
  rebound reqIds — chart RT bars via the registry replay,
  watchlist market-data via `_restore_watchlist`'s clear+re-add

---

## Safety

- **Live port only (7496)** — no paper/simulated mode
- **No order entry in the app** — the app places, cancels and closes nothing; place, cancel and close orders in TWS
- **Read-Only API** recommended in TWS for extra safety

---

## Support

- Check `docs/phase-changelog.md` for the phase-by-phase change record
  (`PENDING_IMPLEMENTATION_PLAN.md`, the old Phases 1-10 roadmap, was deleted 2026-10-15)
- Run `python -m pytest` to verify environment
- TWS must be running before app launch