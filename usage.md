# NDThinkChart — Usage Guide

A PyQt6 + pyqtgraph + official `ibapi` trading terminal for Interactive Brokers TWS.

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

```bash
# Example: custom port + client ID
IBKR_PORT=7496 IBKR_CLIENT_ID=123 python main.py
```

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
| **Watchlist (Left Dock)** | Symbol list with live ticks; double-click to load chart |
| **Portfolio (Right Dock)** | Account summary, positions, P&L, SL/TP, close/flatten actions |

---

## Key Workflows

### Load a Chart
1. Type symbol (e.g., `AAPL`) in toolbar
2. Select timeframe (1 min – 1 day)
3. Click **Load Chart** or press Enter

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

### Portfolio & SL/TP
1. Open **Portfolio** dock
2. Right-click a position → **Set Stop/Target**
   - Long: `stop < market < target`
   - Short: `stop > market > target`
   - Min-tick validation enforced
3. Right-click → **Close Position** / **Close Group** / **Close All Positions**
4. Group positions auto-detected by option strategy (PCS, PDS, CCS, CDS, IC)

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
- `positions` / `trade_groups` — portfolio state with SL/TP

---

## Testing

```bash
# Full suite -- run it for the current total (~25s offscreen)
python -m pytest tests/ -v

# Phase 10 core logic tests only (~0.2s)
python -m pytest tests/test_indicator_service.py tests/test_gap_vix_service.py \
  tests/test_ict_service.py tests/test_alarm_service.py tests/test_bar_aggregator.py \
  tests/test_strategy_detection.py tests/test_order_builders.py tests/test_ui_smoke.py -v
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
| `ModuleNotFoundError: ibapi` | `pip install ibapi` (official IBKR package) |

---

## Architecture Notes

- **Pure logic services** (`services/*.py`) — no Qt, no I/O, fully tested
- **IBKR layer** (`ibkr/*.py`) — `IBApiClient` (EWrapper/EClient), pacing, subscriptions
- **Data layer** (`data/*.py`) — SQLite, cache, models, aggregation
- **UI layer** (`ui/*.py`) — PyQt6 widgets, chart panel, docks
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
- **No automated order logic** — every order requires explicit user action
- **Confirm dialogs** on close/flatten actions
- **Read-Only API** recommended in TWS for extra safety

---

## Support

- Check `docs/phase-changelog.md` for the phase-by-phase change record
  (`PENDING_IMPLEMENTATION_PLAN.md`, the old Phases 1-10 roadmap, was deleted 2026-10-15)
- Run `python -m pytest` to verify environment
- TWS must be running before app launch