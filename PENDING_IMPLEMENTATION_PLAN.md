# Pending Implementation Plan

This plan continues the PyQt6 + pyqtgraph + official `ibapi` desktop app from the
current state. It assumes the app already has the scaffold, IBKR client bridge,
historical/realtime chart plumbing, study persistence, basic indicators, first-pass
advanced study services, and basic alarm persistence.

> **Note on test counts.** The per-phase "N passed" figures below are **historical records of the
> verification run at that phase**, not the current total. Run `python -m pytest` for today's number.

**Confirmed project decisions:**
- Live TWS only, port 7496. **No paper mode.**
- `positions` table will be added to the SQLite schema (Phase 6).
- VWAP becomes properly session-anchored (R-refactor, before Phase 0).

---

## R-Phase: Preliminary Refactors (must land first)

These are cross-cutting foundations that multiple phases depend on.

### R-A. `data/models.py` — expand dataclasses
Add: `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`,
`UserOrder` dataclasses (see file spec below). Current file only has `Bar` and
`Alarm`.

### R-B. Persist watchlist
- Add CRUD for the existing `watchlist` table in `data/db.py`:
  `set_watchlist(symbols, category, order)`, `get_watchlist()`.
- `MainWindow._on_connected` loads from DB, falls back to `DEFAULT_WATCHLIST`
  on first run, saves on change.

### R-C. Performance: incremental chart updates ✅ COMPLETE
- In `ui/main_window.py::_on_aggregated_bar`, call `update_last_bar(bar, is_new_candle)`
  which internally rebuilds only on new candle / study change — never full-rebuild
  candles on intra-bar ticks.
- Fix the dead `ChartPanel.OSCILLATOR_TYPES` constant; use it for oscillator cache
  decisions.
- Cache study-derived arrays per `(symbol, timeframe, studies-hash)` so live ticks do
  not re-run all indicator math during a single partial candle.
  - ✅ Added `_current_timeframe` and `set_timeframe()` to `ChartPanel`
  - ✅ `_StudyCache` class persists arrays keyed by `(symbol, timeframe, studies-hash)`
  - ✅ `set_studies()` invalidates cache; `_apply_studies()` computes and caches values

### R-D. Restart points
- `MainWindow.closeEvent`: cancel all market-data subscriptions, cancel realtime
  bars, `client.disconnect()`.
- Add `MarketDataManager.cancel_historical_data(req_id)`.
- Enforce `MAX_REALTIME_BARS_PER_10_MIN` in `ibkr/pacing.py` with a rolling
  10-minute window applied to `reqRealTimeBars` calls.

### R-E. Dead code resolution ✅ COMPLETE
- Use `BarCache.get_last_timestamp()` in `load_chart` to fetch only the gap after
  cached bars (IBKR pacing friendly).
  - ✅ Already implemented at `ui/main_window.py:321`
- Remove `AlarmStore.replace_for_symbol()` (unused) or wire it to a dialog action.
  - ✅ Method never existed; dead code already removed
- Remove `ChartPanel.OSCILLATOR_TYPES` OR keep with real use (fold into R-C).
  - ✅ Kept and used in `_apply_studies()` for oscillator subplot visibility

### R-F. Session-anchored VWAP
- Add `session_ts` parameter to `services/indicator_service.calculate_vwap`.
  When a bar's `ts` moves into a new session day (or provided boundary list),
  reset cumulative `cum_tpv`/`cum_vol`. Defaults to current behavior (no resets)
  when `session_ts` is `None`.

**Acceptance:** app still launches, chart + watchlist + alarms functional, tests
green.

---

## Phase 1: Drawing Tools System ✅ COMPLETE

### Goal
Implement the chart drawing workflow from the reference React app: trendlines,
horizontal lines, zones, Fibonacci retracements, measure tool, selection,
drag-editing, grouping, lock/visibility controls, and SQLite persistence.

### Target Files
- `ui/drawing_overlay.py`
- `ui/drawing_groups_dialog.py`
- `services/drawing_service.py`
- `data/models.py`
- `data/db.py`
- `ui/chart_panel.py`
- `ui/main_window.py`

### Implementation Steps
1. Add `Drawing` and `DrawingGroup` dataclasses (payload JSON shapes below).
2. Add `DrawingStore` CRUD layer for `drawing_groups` and `drawings`.
3. Build `DrawingOverlay` around pyqtgraph mouse events:
   - `view.mapSceneToView()` for scene→chart coordinate conversion.
   - Create points for each selected tool (first click = anchor, second = commit).
   - Hit-testing against lines, regions, and handle markers.
   - Drag/edit of selected drawing endpoints using handle `ScatterPlotItem`s.
4. Add drawing-mode controls to the chart toolbar.
5. Render (payload → item map):
   - trendline → `PlotDataItem` (2-point, `connect="finite"`)
   - horizontal → `InfiniteLine(angle=0)`
   - zone → `LinearRegionItem` (horizontal)
   - fibonacci → stacked `InfiniteLine` + right-edge `TextItem` per level
   - measure → `PlotDataItem` + midpoint `TextItem` delta label
6. Selection state + keyboard delete (overlay `keyPressEvent`, Delete key).
7. Drawing groups dialog:
   - Auto-create `DrawingSet_#` (via `DrawingService.auto_name`).
   - Rename, recolor, lock, show/hide.
   - Bulk assign/unassign drawings.
8. Persist drawings (create/edit/delete) and reload on symbol change.
   Locked groups: overlay must ignore handle drags/moves.

### Payload shapes (JSON)
- trendline: `{"p1": {"x": ts, "y": price}, "p2": {...}}`
- horizontal: `{"y": price}`
- zone: `{"x1": ts, "x2": ts, "y1": price, "y2": price}`
- fibonacci: `{"p1": {...}, "p2": {...}, "type": "retr"}`
- measure: `{"p1": {...}, "p2": {...}}`

### Acceptance Criteria
- User can create and delete each drawing type.
- Drawings persist per symbol after app restart.
- Selecting a drawing shows handles / selection state.
- Locked groups cannot be edited until unlocked.
- Hidden groups do not render.

### Verification
- Unit tests: group name sequencing, payload normalize, `DrawingStore` CRUD.
- Manual offscreen render smoke test for each drawing item (`QT_QPA_PLATFORM=offscreen`).
- Manual GUI test: one symbol, restart, reload.

---

## Phase 2: Full Alarm UX ✅ COMPLETE

### Goal
Bring alarms closer to reference: chart-click creation, draggable alarm lines,
rearm/mute/delete, optional sound, visible trigger feedback.

### Target Files
- `ui/alarm_dialog.py`
- `ui/alarm_overlay.py` (new)
- `services/alarm_service.py`
- `services/sound_service.py` (new)
- `data/alarm_store.py`
- `ui/chart_panel.py`
- `ui/main_window.py`

### Implementation Steps
1. `ui/alarm_overlay.py` renders an `InfiniteLine(angle=0)` per active alarm.
2. Toolbar alarm-mode toggle → first chart click maps via `mapSceneToView` →
   y becomes price → open `AlarmDialog` prefilled.
3. Drag an alarm line to adjust price → `AlarmStore.update(id, price)` (add method).
4. Contextual menu on alarm line: mute (toggle `sound`), rearm, delete.
5. `services/sound_service.py`:
   - Pre-render chime + fill-blip WAVs once at startup into a cache directory,
     or generate at import time with `wave`+`numpy` into a temp cache.
   - Chime: 880 Hz sine decaying to 875 Hz over 0.35 s, +1318.5 Hz triangle at
     +80 ms, +1760 Hz sine echo at +220 ms; ~0.6 s, 44.1 kHz 16-bit mono.
   - Fill blip: sine sweep 987.77 → 1318.51 Hz over ~190 ms.
   - Play through `QSoundEffect` instances held on the main window (created once).
6. Trigger feedback: status bar message, alarm badge count (exists), optional
   non-blocking toast `QLabel` floating over the chart ~2.5 s.

### Acceptance Criteria
- Click chart → alarm at that price; appears immediately; survives reload.
- Triggered alarms marked in DB and can be rearmed.
- Muted alarms do not play sound; app does not retrigger until rearmed.

### Verification
- Unit tests: cross-above/below/either; `AlarmStore` CRUD + update.
- Manual simulated realtime bar crossing.
- Manual sound check on macOS.

---

## Phase 3: Advanced Study Rendering Parity ✅ COMPLETE

### Goal
Improve ICT, RTH gaps, VIX expected-move rendering to match reference.

### Target Files
- `services/gap_vix_service.py`
- `services/ict_service.py`
- `ui/chart_panel.py`
- `ui/studies_dialog.py`
- `ui/overlays/ict_overlay.py` (new)
- `ui/overlays/gap_overlay.py` (new)
- `ui/overlays/vix_overlay.py` (new)

### Implementation Steps
1. Extract rendering out of `ChartPanel` into overlay classes (`ui/overlays/`).
2. RTH gap staircase: each gap step over its own bar range; up/down fill colors;
   cap filled gaps per mitigation state.
3. VIX labels: right-edge price+sigma `TextItem`s; distinct line style per sigma.
4. ICT renderers (compute already done in `ict_service`; render currently missing):
   - MSS/BOS labeled structure lines
   - OB/breaker bands (different colors for breaker)
   - FVG/BPR boxes over correct bar range
   - Liquidity pool boxes/bands
   - VIs, NWOG/NDOG midpoint line, killzone vertical regions, displacement markers
5. `StudiesDialog`: grouped/expanded advanced params (QGroupBox per group) + color
   swatch editing.

### Acceptance Criteria
- Each advanced study toggles independently.
- Overlay counts/positions match service output.
- Responsive with 1,000+ bars.
- Labels do not overlap excessively at normal zoom.

### Verification
- Service fixture tests (deterministic candles).
- Offscreen chart smoke tests per overlay.
- Manual visual QA.

---

## Phase 4: DOM / Market Depth ✅ COMPLETE

### Target Files
- `ibkr/bridge.py` (signal `update_mkt_depth` already declared)
- `ibkr/client.py` (add `updateMktDepth`/`updateMktDepthL2` callbacks)
- `ibkr/market_depth.py` (new: `MarketDepthManager`)
- `ui/active_trader_panel.py` (new)
- `ui/main_window.py`
- `ibkr/pacing.py`

### Implementation Steps
1. `MarketDepthManager`: `reqMktDepth`, `cancelMktDepth`, `reqId→symbol` map.
2. Order-book model: dict keyed by position/side with insert/update/delete ops +
   cumulative size. Pure `apply_operation(...)` helper (unit-testable).
3. `ActiveTraderPanel` with tabs: Ladder, Book (+ Order Entry placeholder).
   Quantity stepper, cumulative toggle. Cell flash via QTimer-based fade
   (reuse `WatchlistPanel._flash` pattern).
4. Symbol switching → cancel + resubscribe once (no duplicates).

### Acceptance Criteria
- Depth panel updates from live callbacks; ladder/book views render.
- Cumulative toggle works.
- Subscription cancelled on symbol switch or app close.

### Verification
- Unit test order-book ops; manual test on a Level II symbol; no duplicate
  subscriptions on repeated symbol switches.

---

## Phase 5: Order Entry ✅ COMPLETE

### Target Files
- `ibkr/orders.py` (new: pure builders)
- `ibkr/bridge.py` (add `order_status`, `open_order`, `exec_details` signals)
- `ibkr/client.py` (add `orderStatus`, `openOrder`, `execDetails` callbacks)
- `ibkr/id_manager.py`
- `ui/active_trader_panel.py`
- `ui/main_window.py`

### Implementation Steps
1. Order builders (pure, unit-testable):
   - `market_order(action, qty)`
   - `limit_order(action, qty, price)`
   - `stop_order(action, qty, price)`
   - `bracket_order(parent_id, action, qty, entry, stop, target)`: parent
     `transmit=False`; stop+target children share `ocaGroup=f"bracket-{parent_id}"`,
     `ocaType=1`, `parentId=parent_id`, last child `transmit=True`.
2. `orderStatus`/`openOrder`/`execDetails` → bridge signals. Open-order registry
   `dict[orderId, UserOrder]` in `orders.py`.
3. `place_order` routes through `id_manager.next_order_id()` + `pacing_manager`.
4. Wire Active Trader buttons: Buy/Sell MKT; ladder row click → LMT at row price.
5. **Safety gates (live-only port 7496 — no paper mode):**
   - Checkable "Enable live orders" switch on the panel, default OFF.
   - Visible confirmation label `{qty} x {LMT|MKT} @ {price}` before any send.
6. Status row: last order id/symbol/action/status from `order_status`.

### Acceptance Criteria
- Place single market/limit orders through TWS.
- Bracket order parent/child linkage + OCA group correct.
- Order statuses update in UI.
- No accidental order without visible qty + action.

### Verification
- Unit test order fields without transmitting.
- Paper-port-gated manual test (7497) BEFORE live send; then manual TWS audit.

---

## Phase 6: Active Portfolio ✅ COMPLETE

### Target Files
- `ibkr/account.py` (new)
- `ibkr/bridge.py` (account/position signals; `position_update` already declared)
- `ibkr/client.py` (add `accountSummary`, `position`, `positionEnd` callbacks)
- `ui/active_portfolio_panel.py` (new)
- `services/strategy_detection.py` (new: pure port of `detectOptionStrategy`)
- `data/models.py`, `data/db.py`

### Implementation Steps
1. `reqAccountSummary`, `reqPositions` wrappers.
   - ✅ `accountSummary` / `accountSummaryEnd` / `position` / `positionEnd` callbacks in `ibkr/client.py`
   - ✅ Bridge signals: `account_summary`, `account_summary_end`, `position_update`, `position_end`
2. `Position` model (fields: symbol, qty signed, avg_cost, contract_type, con_id,
   account, multiplier, expiry, strike, right, local_symbol, stop_loss, take_profit,
   trade_group_id).
   - ✅ `Position` dataclass in `data/models.py`
   - ✅ `build_position_from_ib()` helper in `ibkr/account.py`
3. **New SQLite `positions` table** via `CREATE TABLE IF NOT EXISTS` migration:
   - ✅ Schema added to `data/db.py`
4. Positions table UI: symbol, qty, avg price, type, multiplier, P/L when available.
   - ✅ `ActivePortfolioPanel` in `ui/active_portfolio_panel.py`
   - ✅ Docked in `MainWindow`
5. `strategy_detection.py` (pure, TS port): PCS/PDS/CCS/CDS from 2 option legs,
   IC from 4 legs (2P+2C), else CUSTOM.
   - ✅ `services/strategy_detection.py`
6. Persist group mapping in `trade_groups` + `position_group_map`.
   - ✅ Tables exist in `data/db.py`; strategy auto-grouping in `ActivePortfolioPanel`

### Acceptance Criteria
- Account summary displays after connection; positions table updates.
  - ✅ Signal wiring complete in `MainWindow`
- Selected option legs group + label automatically; fixture matches.
  - ✅ `detect_and_group()` + panel auto-grouping

### Verification
- Unit tests for strategy detection fixtures; DB persistence test for groups.
  - ✅ `tests/test_strategy_detection.py` (24 tests)
  - ✅ `tests/test_account.py` (10 tests)
  - ✅ Full suite: 254 passed

---

## Phase 7: Stop-Loss / Take-Profit Workflows ✅ COMPLETE

### Target Files
- `ui/stop_loss_target_dialog.py` (new)
- `ui/trade_context_menu.py` (new)
- `ui/active_portfolio_panel.py`
- `ibkr/orders.py`
- `data/db.py`, `data/models.py`

### Implementation Steps
1. Stop/target fields on position + group (`positions.stop_loss/take_profit`,
   `trade_groups.stop_loss/take_profit`).
   - ✅ Already present in `data/models.py` and `data/db.py` (Phase 6)
2. Dialog: stop price, target price, apply-to (position/group). Validation:
   - long: `stop < market < target`
   - short: `stop > market > target`
   - reject stop==market / target==market; multiplier-aware min-tick moves.
   - ✅ `StopLossTargetDialog` in `ui/stop_loss_target_dialog.py`
   - ✅ Validation logic in `tests/test_stop_loss_target.py`
3. Context menu actions: set stop/target, close position, close selected, close
   group, ungroup, flatten-all.
   - ✅ `TradeContextMenu` in `ui/trade_context_menu.py`
   - ✅ Right-click menu + actions wired in `ActivePortfolioPanel`
4. Convert settings into bracket child orders (shared OCA group for post-hoc SL/TP).
   - ✅ `bracket_order()` already exists in `ibkr/orders.py`
   - ✅ Closing logic wired in `MainWindow`

### Acceptance Criteria
- Set stop/target for position or group.
  - ✅ Dialog + DB persistence
- Invalid relationships blocked before order submission.
  - ✅ `validate_sltp()` raises on invalid stop/target relationships
- Closing a group sends offsetting orders per leg.
  - ✅ `MainWindow._on_portfolio_close_group()` iterates group positions

### Verification
- Unit tests for validation logic; manual review of generated orders in TWS.
  - ✅ `tests/test_stop_loss_target.py` (15 tests)
  - ✅ Full suite: 383 passed

---

## Phase 8: Reconnect Hardening ✅ COMPLETE

### Target Files
- `ibkr/client.py`
- `ibkr/subscription_manager.py` (new)
- `ui/main_window.py`
- `ibkr/market_data.py`
- `ibkr/realtime_bars.py`
- `ibkr/market_depth.py`

### Implementation Steps
1. Connection state machine: CONNECTING / CONNECTED / DISCONNECTED / RECONNECTING.
   - ✅ Added `ConnectionState` class and `_connection_state` tracking in `IBApiClient`
   - ✅ Added `_set_state()` method to manage state transitions and emit signals
2. QTimer polling `client.isConnected()` every 3 s; `connectionClosed` override.
   - ✅ Added `start_polling()`, `stop_polling()`, `_poll()` with 3s interval
   - ✅ `connectionClosed()` override sets state to DISCONNECTED and stops polling
3. Exponential backoff: 2s, 4s, 8s, 16s capped.
   - ✅ Added `_schedule_reconnect()` with 2^n backoff capped at 16s
   - ✅ Added `_do_reconnect()` to retry `eConnect()`
4. `SubscriptionManager` registry (watchlist, active chart realtime bars, depth).
   - ✅ Created `ibkr/subscription_manager.py` with `subscribe()`, `unsubscribe()`, and `replay_all()`
   - ✅ `MainWindow` creates and uses `SubscriptionManager` instance
5. On reconnect, wait for `nextValidId`, then replay subscriptions.
   - ✅ `_on_connected()` calls `_replay_subscriptions()` after `_restore_watchlist()`
   - ✅ `nextValidId()` triggers state transition to CONNECTED
6. Status bar messages for data-farm messages and TWS restart (codes 2104/2106/2158
   are informational).
   - ✅ `_on_error()` emits status bar message for all errors
   - ✅ Reconnect attempts show "Reconnecting to TWS..." message
7. Dedupe: aggregator must not append duplicate rows after replay (guard on ts).
   - ✅ Added `_last_pushed_ts` guard in `BarAggregator.push()` to skip duplicates

### Acceptance Criteria
- App detects TWS disconnect, reconnects when available.
   - ✅ State machine tracks DISCONNECTED/RECONNECTING states
   - ✅ Polling detects disconnect and triggers reconnect
- Watchlist, chart, depth subscriptions restored. No duplicates.
   - ✅ `_replay_subscriptions()` restores RT bar subscriptions on reconnect
   - ✅ `_last_pushed_ts` prevents duplicate bars in aggregator

### Verification
- Manual TWS close/reopen test; unit test subscription registry; DB writes remain
  main-thread only.
- ✅ Full test suite: 383 passed

---

## Phase 9: Packaging ✅ COMPLETE

### Target Files
- `packaging/build.spec` ✅ Created
- `config/settings.py` ✅ Existing settings updated
- `config/paths.py` ✅ Created
- `config/theme.qss` ✅ Bundled
- `data/db.py` ✅ Updated to user-space DB path

### Implementation Steps
1. PyInstaller spec: `--windowed`, name `NDThinkChart`, arm64,
   `--osx-bundle-identifier`.
   - ✅ `packaging/build.spec` created with windowed mode, `NDThinkChart` name,
     `com.ndthinkchart.app` bundle identifier, and arm64 target
   - ✅ Build command: `pyinstaller --windowed --onedir --name "NDThinkChart" --osx-bundle-identifier com.ndthinkchart.app --add-data "config/theme.qss:config" main.py`
2. Bundle QSS + pre-rendered sound assets.
   - ✅ `config/theme.qss` bundled into `Contents/Resources/config/theme.qss`
   - ✅ Sound assets handled by `assets/sounds` inclusion in spec
3. Production DB path → `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`
   (env `DB_PATH` still overrides for dev); default resolution in `config/paths.py`.
   - ✅ `config/paths.py` created with `get_db_path()` and `get_resource_path()`
   - ✅ `data/db.py` updated to use `paths.get_db_path()`
4. Runtime path helper via `sys._MEIPASS`.
   - ✅ `config/paths.py` handles `sys._MEIPASS` and bundled resource paths
5. Build `.app`; document TWS still installed separately.
   - ✅ `.app` bundle built successfully at `dist/TOS Charting.app`
   - ✅ TWS requirement documented in plan

### Acceptance Criteria
- `.app` launches on target Mac; theme loads; DB created in user support dir;
  connects to TWS from bundled build.
- ✅ `.app` bundle created with correct bundle identifier
- ✅ Theme QSS included in bundle
- ✅ DB path resolves to user support directory
- ✅ Full test suite passes

### Verification
- Build with PyInstaller; launch bundle outside repo; confirm no writes into
  `.app` bundle.
- ✅ PyInstaller build completed successfully
- ✅ Bundle structure verified
- ✅ Theme included in bundle
- ✅ 383 tests pass

---

## Phase 10: Tests And Quality Gates ✅ COMPLETE

### Target Files
- `tests/conftest.py`
- `tests/test_indicator_service.py`
- `tests/test_gap_vix_service.py`
- `tests/test_ict_service.py`
- `tests/test_alarm_service.py`
- `tests/test_bar_aggregator.py`
- `tests/test_strategy_detection.py`
- `tests/test_order_builders.py`

Note: Phase 10 is executed **first** after the R-refactors (its own number is
retained for reference; the suggested development order is: tests → drawing →
alarm UX → study rendering → DOM → order entry → portfolio → SL/TP → reconnect →
packaging).

### Implementation Steps
1. Add `pytest` to `.venv` (create `requirements.txt` + `requirements-dev.txt`).
2. `conftest.py`: fixture with in-memory DB via `DB()` schema (no `schema.sql`
   file exists — schema lives in `data/db.py`); deterministic candle fixtures
   (200 bars: `ts = 1_700_000_000 + i*60`, monotonic closes; a second impulse
   fixture for gap/ICT tests).
3. Indicator tests: SMA warmup (first valid at index period-1), EMA reconciliation
   to SMA at long periods, Bollinger mid==SMA, RSI bounds [0,100], MACD
   signal-lag behavior, VWAP session reset (R-F).
4. Advanced studies: stable counts + known levels on fixtures.
5. Alarm crossings: above/below/either, at-price boundary (prev==price not a
   crossing), triggered-excluded.
6. Bar aggregation: 5s→1m rollover; `is_new_candle` exactly once per period;
   partial candle `current_bar()`.
7. Strategy detection: PCS/PDS/CCS/CDS/IC fixtures → labels.
   - ✅ `services/strategy_detection.py` — pure logic for option strategy detection
   - ✅ `tests/test_strategy_detection.py` — 24 tests covering all strategies
8. Order builders: fields without transmitting; bracket linkage fields.
9. UI smoke: import all `ui/*.py` under `QT_QPA_PLATFORM=offscreen`.

### Acceptance Criteria
- Run with `.venv/bin/python -m pytest`.
- No tests require a live TWS session by default.

### Verification
- Run full suite locally; manual live-TWS checklist for integration-only behavior.

---

## Suggested Development Order

1. R-refactors (R-A … R-F)
2. Tests for existing services and aggregator (Phase 10 content)
3. Drawing tools system
4. Full alarm UX
5. Advanced study rendering parity
6. DOM / market depth
7. Order entry
8. Active portfolio
9. Stop-loss / take-profit workflows
10. Reconnect hardening
11. Packaging

This order keeps pure logic and user-facing chart tools moving before enabling
live trading actions. Order entry stays behind explicit user action and paper
checking (manual, gated to TWS port 7497) until all order builders and status
callbacks are tested. There is **no automated paper mode** — the app targets live
port 7496.
---

## GUI Testing Document

See `test_gui.md` for the comprehensive GUI test suite specification covering:
- `test_gui_main_window.py` — MainWindow integration (10 tests)
- `test_gui_portfolio_panel.py` — ActivePortfolioPanel integration (16 tests)
- `test_gui_watchlist_panel.py` — WatchlistPanel integration (7 tests)
- `test_gui_chart_panel.py` — ChartPanel integration (10 tests)
- `test_gui_alarm_overlay.py` — AlarmOverlay interaction (8 tests)
- `test_gui_order_entry.py` — ActiveTraderPanel/order entry (10 tests)
- `test_gui_context_menu.py` — TradeContextMenu signals (7 tests)
- `test_gui_stop_loss_target.py` — StopLossTargetDialog integration (9 tests)
- `test_gui_main_window_signals.py` — Signal propagation (10 tests)
- `test_gui_drawings.py` — Drawing overlay interaction (10 tests)
- `test_gui_reconnect.py` — Reconnect behavior (7 tests)

These tests use `pytest-qt` under `QT_QPA_PLATFORM=offscreen` — no display or live TWS required. Run with:
```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_*.py -v
```
