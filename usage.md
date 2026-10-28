# NDThinkChart — Usage Guide

> **As of 2026-10-28.** Canonical user guide. Short version: `USAGE.txt` (pointer + quick start).
> Change record: `docs/phase-changelog.md`.

A PyQt6 trading terminal for Interactive Brokers TWS with the **Lightweight Charts** engine
(served through an offline QtWebEngine page) and the official `ibapi`.

---

## Prerequisites

- **macOS 11+ (Big Sur)** on Apple Silicon (ARM64)
- **Python 3.11+** (managed via pyenv recommended)
- **Interactive Brokers TWS** installed and running
- **TWS API port 7496** enabled (the app refuses any other port; account type comes from the TWS login)

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
# requirements.txt pins PyQt6-WebEngine to the installed PyQt6 version (the chart
# engine runs on it — it is required, not optional). Keep those two in step
# when you upgrade PyQt6.

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
| `NDT_CHART_ENGINE` | ignored (legacy) | Older versions used this to select a chart engine. The app is now Lightweight-Charts-only; the variable is read by nothing that selects a renderer, so setting it has no effect |

```bash
# Example: custom port + client ID
IBKR_PORT=7496 IBKR_CLIENT_ID=123 python main.py
```

---

## Chart Engine

The app renders with **Lightweight Charts (LWC)** through an offline QtWebEngine page behind the
`create_chart_view` seam. The legacy pyqtgraph renderer was removed (P6-T13, owner-approved); there is
no engine switch and no opt-in — one engine, always on.

- `PyQt6-WebEngine` is **required** (it hosts the chart) and must match the installed `PyQt6` version.
- A `NDT_CHART_ENGINE` value left over from an older version is **ignored** — it cannot blank the chart.
- The LWC assets ship vendored (`chart_assets/lwc/`, v5.2.1) and are bundled with the app, so the chart
  works fully offline.

---

## TWS Setup Checklist

1. **Install TWS** from IBKR website (not IB Gateway)
2. **Login** — live account for live trading. The app connects only to `127.0.0.1:7496` and refuses
   any other port; a paper (DU) TWS login on that same port works too (connection badge shows amber
   `Paper`), since the guard is on the port, not the account type
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

### Pop-out Charts
1. The toolbar **Pop out** button (or Ctrl/Cmd+P) detaches the current ticker into a slim standalone chart window — up to 10 total
2. Pop-outs follow their ticker in real time (bars, studies, zones, lines, alarms stay in sync); there is only one IBKR market-data subscription per symbol no matter how many windows show it
3. Timeframe, mode and extended-hours are frozen at pop-out time; drawing, alarm placement and study changes happen in the main chart only (pop-outs are read-only views — zoom, pan and crosshair still work)
4. Header context menu toggles always-on-top per window (off by default); pop-outs are restored after an app restart
5. Alarms are evaluated per ticker, so an alarm fires even while the main chart shows a different symbol — including tickers with no visible chart, which are monitored headlessly

### Event Markers (removed — Q-34, commit `1a30d41`)

> The D38 earnings/dividend/split markers were removed; the chart shows no event markers.

### Volume-Burst Alerts & Symbol Search (Phase D39)
- The search box sits in the watchlist header: type part of a ticker (requests at most ~once per 300ms, up to 16 matches as symbol/security-type/exchange); while disconnected the box is disabled
- A `volume_burst` alarm compares each bar's volume against the typical volume for that time of day (robust median/MAD baseline over the last 30 bars of the same minute-of-day) and fires when the z-score reaches your threshold (default 4.0, minimum 1.0)
- The baseline needs 5 bars before it can evaluate (`warming up (n/5)`); symbols under 1.0 contracts/shares per minute are never evaluated; a fired burst behaves exactly like a price alarm (toast + sound once, re-arm works, headless tickers included)
- Index alarms trade the proxy tape (e.g. SPX watches ES front-month volume) and the baseline resets on futures roll

### TWS Daily Lifecycle (Phase D40)
- When TWS goes away (e.g. overnight close), the badge shows amber `Monitoring paused — TWS disconnected` — never green; while paused no alarm is evaluated and nothing can fire
- Log into TWS in the morning with no app restart: the app reconnects, resubscribes, and resumes monitoring; the status bar reports the gap (e.g. `ES, NQ unmonitored 22:14–09:40`)
- Resume never triggers alarms by itself — prices re-seed quietly and an alarm fires only if the live price then crosses its level; brief intraday drops reconnect in the background with no pause badge

### Weekly & Monthly Timeframes (Phase D48)
- The timeframe picker offers `1 week` (2 years of history) and `1 month` (10 years of history) after `1 day`; daily-and-coarser loads ignore the Ext Hours toggle

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
3. Right-click drawing → **Delete** (drawings are delete-only until D50 drag-editing lands)
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
# Full suite -- run it for the current total (~75s offscreen)
.venv/bin/python -m pytest tests/ -v

# Core logic tests only (~0.2s)
.venv/bin/python -m pytest tests/test_indicator_service.py tests/test_gap_vix_service.py \
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
| Duplicate bars after reconnect | Fixed — `_last_pushed_ts` guard in `BarAggregator` |
| `ModuleNotFoundError: ibapi` | `pip install -r requirements.txt` (the dist is `ibapi-latest`, which provides the `ibapi` module) |

---

## Architecture Notes

- **Pure logic services** (`services/*.py`) — no Qt, no I/O, fully tested
- **IBKR layer** (`ibkr/*.py`) — `IBApiClient` (EWrapper/EClient), pacing, subscriptions
- **Data layer** (`data/*.py`) — SQLite, cache, models, aggregation
- **UI layer** (`ui/*.py`) — PyQt6 widgets, docks, and the chart behind the
  `create_chart_view` seam (Lightweight Charts only — the legacy pyqtgraph renderer was removed)
- **Reconnect hardening** (D27.3) — connection state machine (DISCONNECTED /
  CONNECTING / CONNECTED / RECONNECTING); `_do_reconnect` re-issues the real
  `EClient.connect` with the stored host/port/clientId on exponential backoff
  (the poll timer does not re-arm while a reconnect is pending); live
  subscriptions are type-tagged in `SubscriptionManager` and replayed with
  rebound reqIds — chart RT bars via the registry replay,
  watchlist market-data via `_restore_watchlist`'s clear+re-add

---

## Safety

- **Port guard: only 7496** — the app refuses to start on any other port (live TWS port; a paper TWS login on the same port shows amber `Paper`)
- **No order entry in the app** — the app places, cancels and closes nothing; place, cancel and close orders in TWS
- **Read-Only API** recommended in TWS for extra safety

---

## Support

- Check `docs/phase-changelog.md` for the phase-by-phase change record
  (`PENDING_IMPLEMENTATION_PLAN.md`, the old Phases 1-10 roadmap, was deleted 2026-10-15)
- Run `.venv/bin/python -m pytest` to verify environment
- TWS must be running before app launch