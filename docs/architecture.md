# Architecture — NDThinkChart Stabilization (as-built D1–D15 + ESC revision + post-document rework ESC-013…ESC-021, verified 2026-09-28, 383 passed; **increment D16 historical-bar gap backfill, validated 2026-10-02; ESC-023 trading-day calendar correction, validated 2026-10-02; increment D17 + D18 panel-layout / full-screen dock sizing, validated 2026-10-03; as-built D1–D18 at commit `5bd7c93` — 566 passed; increment D19 toolbar scroll/elide wrapper, validated 2026-10-05**) — commit baseline `5bd7c93`

## Summary
An **as-built** description of a stabilization change-set against an existing
PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal. **All of D1–D15 are
built and verified**, together with the ESC-002/003/006/007 revision and a
post-document rework wave (ESC-013…ESC-021): session shading, the crosshair chip in
the Y-axis lane, zoom controls/magnifier, the zoom label/position, a **linear**
volume axis with a dynamic scaling nice max (pinned family + live ceiling) and
price-coloured bars, volume bars that track the price body width, a volume-panel
hide/show toggle, inner-right drawing price labels, two double-click drawing
settings popups (zone `Rectangle`, horizontal line), a resizable/persistent
watchlist with double-click-to-load, and an explicit `RouterMode` gesture state
machine. The full offscreen suite is green (**383 passed**).

**Revision lineage:** the validated 2026-09-27 revision added (1) an explicit
`RouterMode` state machine for gesture precedence (**ESC-002**,
`AC-D3.7`–`AC-D3.9`), (2) the pinned continuous volume nice-number formula plus a
live intra-bar ceiling (**ESC-003/ESC-007/ESC-008**, `AC-D8.1`–`AC-D8.7`),
(3) the relocated crosshair price chip in the Y-axis lane with independently
verified dock-open visibility (**D2/Q33**, `AC-D2.1`–`AC-D2.3`), and (4) the
`AC-D11.4` re-scope to label-vs-label (**ESC-006**). A subsequent post-document
rework wave (ESC-013, ESC-014, ESC-015, ESC-016, ESC-017, ESC-020, ESC-021 — see
“Post-document rework” below) is folded into this as-built description. In
existing-repo mode every item below is labelled `[existing]`, `[new]`, or
`[new/changed]`.

**D16 increment (validated 2026-10-02):** two new pure services —
`services/market_calendar.py` (ET trading-day/holiday calendar) and
`services/backfill_service.py` (missing-span + chunk-request planner) — let
`ui/main_window.py::load_chart` detect the missing trading sessions between the cached
series and *now* and backfill them with a correlated set of historical requests,
finalising with one save + re-read + render. The `ui/chart_panel.py` render path and the
`bars` schema are **unchanged**: a continuous `_bars` list fixes the price **and** volume
panels, and genuine closures (weekend/holiday/overnight) stay empty. D1–D15 are frozen
and are **not** re-planned.

**ESC-023 correction (validated 2026-10-02):** the D16 trading-day calendar's New Year's
observed-day rule is corrected to carry the **NYSE Rule 7.2 year-end accounting-period
exception** (`AC-D16.7`, A33, R27, DG22). The D16 batch (T37–T41) is **built**, but its
`services/market_calendar.py::_observed` naively shifted a Saturday Jan 1 onto the
preceding Friday **Dec 31**, marking that genuine trading day (e.g. `2021-12-31`,
`2027-12-31`, `2032-12-31`, `2038-12-31`) as a closure — so a real bar hole there would be
misclassified as a "genuine closure" and left a silent hole. The correction makes the New
Year's observed shift **New-Year's-specific**: when Jan 1 is a Saturday **no New Year's
closure is observed**, Dec 31 stays a trading day, and no substitute closure is created
(Jan 1 itself remains non-trading as an ordinary weekend). All other observed shifts
(Independence Day, Christmas, Juneteenth, New Year's-on-a-Sunday) are unchanged. The
existing `T37-T03` acceptance criterion and `tests/test_market_calendar.py` encode the old
(wrong) convention and are corrected under this increment.

Persistence and the live-order path remain untouched — no new tables, no new external
integrations, and no new IBKR call *type*. D16 adds **additional historical requests per
load** (chunked backfill through the existing `reqHistoricalData` path) plus the two pure
services above.

**D17/D18 (built) + D19 increment (validated 2026-10-05):** the D17/D18 dock-width
increment (shared chart-area width model in the pure `ui/dock_layout.py`; live clamp via
`MainWindow._apply_dock_widths`; single right-dock region) is **built and green** at
commit `5bd7c93` (full offscreen suite **566 passed**). The **D19** increment fixes the
residual real-app failure: the toolbar's ~1716px `minimumSizeHint` sat **inside the
central widget** (`ui/main_window.py:100–211`, `:217–223`), so the central widget could
not shrink and the D17/D18 clamp had no slack; the D17/D18 test harnesses hid the toolbar,
masking it (`DG27`/`DG28`). D19 wraps the existing toolbar `QWidget` in a horizontal
`QScrollArea` **in place** (no frame, `setWidgetResizable(False)`, horizontal
`ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, fixed 36px row) inserted into the
central `QVBoxLayout` where the bare toolbar was. The toolbar stays **inside the central
widget** as a single ~36px row; its minimum width no longer pins the layout, so the
**already-built** D17/D18 model becomes effective in a **toolbar-visible** window. The
watchlist cap stays `floor(0.50 × chart_area)` (B6) and the width model is untouched. D19
also removes the `toolbar.hide()` masking from the five D17/D18 harnesses and adds the
`AC-D19.6` pre-fix-red/post-fix-green regression guard. D1–D18 remain frozen and are **not**
re-planned.

## Codebase Summary (existing repository — D16 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`) and then
> **validated against the current source files** (the repository is authoritative). Only
> the parts D16 touches are listed here; the full existing layer inventory is under
> *System Components*.
>
> **Graphify staleness (D16 increment).** The committed graph (`graph.json`, 1969 nodes)
> predates the D16 modules: it contains **no `market_calendar` and no `backfill_service`
> node** (confirmed by direct grep of `graphify-out/graph.json`, 2026-10-02). Per the
> existing-repo rule, the D16 sections below were therefore inventoried and validated by
> **direct source inspection** of the current tree, not from the graph.

**Existing bar-load path (the D16 surface):**
- `[existing] ui/main_window.py::MainWindow.load_chart` — cancels the previous RT
  subscription, sets `_current_symbol`/`_current_tf`, shows cached bars
  (`BarCache.get_bars` → `ChartPanel.update_chart`), then issues **one**
  `MarketDataManager.req_historical_data(endDateTime="", whatToShow="TRADES", useRTH=1,
  extended_hours=…)` with the fixed `TIMEFRAME_CONFIG` duration, then starts the RT
  stream. `_on_historical_bar` filters `reqId != self._current_req_id` and appends to
  `_pending_bars`; `_on_historical_data_end` filters the single reqId, `BarCache.save_bars`,
  re-reads **all** cached bars, and renders. `closeEvent` cancels the single
  `_current_req_id`; `_on_error` is already connected to `bridge.error_msg`.
- `[existing] ibkr/market_data.py` — `TIMEFRAME_CONFIG` (per-timeframe
  `duration`/`bar_size`: `1 min`→`1 D`, `5 mins`→`5 D`, `15 mins`→`5 D`, `1 hour`→`10 D`,
  `4 hours`→`30 D`, `1 day`→`1 Y`). `req_historical_data()` already accepts an
  `endDateTime` and already applies `id_manager.get_id()` + `pacing_manager.throttle()`
  per request; it has **no caller besides `load_chart`** outside tests.
- `[existing] ibkr/client.py` / `ibkr/bridge.py` — `historicalData` → `bridge.historical_bar`;
  `historicalDataEnd` → `bridge.historical_data_end`; `historical_bar`/`historical_data_end`/
  `error_msg` are the signals `MainWindow` consumes.
- `[existing] data/bar_cache.py` — `save_bars` (`INSERT OR REPLACE`; PK
  `(symbol, timeframe, ts)`), `get_bars` (all cached, ascending), `get_last_timestamp`
  (`MAX(ts)`; **present but unused by `load_chart`**).
- `[existing] data/bar_aggregator.py` — `TIMEFRAME_SECONDS` maps every timeframe to its
  per-bar period in seconds.
- `[existing] ui/main_window.py::_ibkr_end_date` — formats a unix ts as the IBKR
  `yyyyMMdd-HH:mm:ss` **UTC hyphenated** `endDateTime`; currently has **no caller**.
- `[existing] services/session_service.py` — pure, Qt-free ET
  (`ZoneInfo("America/New_York")`) session math. **Before D16 there was no
  trading-day/holiday logic anywhere in the repo**; D16 added the separate
  `services/market_calendar.py` module inventoried under “D16 additions/changes”
  below (validated by direct source inspection).
- `[existing] ui/chart_panel.py` — `update_chart` sets `self._bars`; `_refresh_candles`
  builds **both** the candle data and the volume `BarGraphItem` from the same `self._bars`
  list, so a continuous `_bars` list fixes candles **and** volume.

**Existing data models / tables:** `Bar` (symbol, timeframe, ts, open, high, low, close,
volume); SQLite `bars` table with `PRIMARY KEY (symbol, timeframe, ts)`. No migration is
needed.

**Existing components / integrations:** `config/`, `data/`, `services/` (pure), `ibkr/`
(client/bridge/market_data/pacing/id_manager/contracts/realtime_bars/…), `ui/`
(main_window/chart_panel/…); external integrations in play: IBKR historical/RT data,
SQLite, Qt signals, `pacing_manager`, `id_manager`. **No new external integration is
introduced by D16.**

**Existing relevant test pattern:** `tests/test_watchlist_d14_midrag.py` boots a real
offscreen `MainWindow` with `IBApiClient.connect` monkeypatched and
`md_manager.req_historical_data`/`rt_manager.subscribe` stubbed — the established pattern
for the D16 integration test. No test currently drives the historical load/backfill path.

## Tech Stack Decisions
| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | Unchanged: Python 3.11+, PyQt6, pyqtgraph | Stabilization run; changing the stack is a stated non-goal | New charting library or embedded web view |
| Session boundary math (Batch 1) | Pure `services/session_service.py` using `ZoneInfo("America/New_York")` | Qt-free, unit-testable, DST-correct | Inline math in `ChartPanel` (untestable); `pandas_market_calendars` (holidays unneeded) |
| Session shading primitive (Batch 1) | `pg.LinearRegionItem(orientation=Vertical, movable=False)` per band, z below candles | Full-height, no price range needed, one item per band | `StudyOverlay.add_band` (needs bottom/top); `fillBetween` (sentinel y); 2×`InfiniteLine` per band |
| Zoom controls / magnifier (Batch 1) | `ui/chart_controls.py` (signal-emitting `QFrame`) + `ui/zoom_overlay.py`, mediated by `ChartMouseRouter` | Logic-free widget, testable; fits existing overlay-precedence pattern | Main-toolbar buttons; pyqtgraph ViewBox zoom modes (no persistent tool state) |
| **Gesture routing (ESC-002, revision)** | **`[new/changed]` `RouterMode { IDLE, DRAWING, ZOOMING, ALARM_PLACING }` with a single `ChartMouseRouter._active_mode` and a normative, total transition table (see “Router state machine” below)** | Precedence was implicit (three booleans resolved by call order); a single enum makes zoom/drawing mutually exclusive by construction and encodes `AC-D3.7`–`AC-D3.9` | Keep booleans + documented order (still allows both true); `(zoom,draw,alarm)` tuple + `sum<=1` assert (8 states, unreachable combos); overlays aware of each other (N×N coupling) |
| **Crosshair chip (D2, revised Q33 2026-09-27)** | **Grey pill (`TextItem`) with WHITE text in the Y-axis lane outside the plot**, left-anchored at the plot’s vertical axis line (`anchor=(0,0.5)`, scene `x >= view_rect.right()`); axis-tick-label overlap permitted. The lane width is reserved up-front (`_reserve_price_tag_lane()` probes a `TextItem` of `PRICE_TAG_LANE_SAMPLE = "123,456.78"`, stores `_price_lane_width`, and folds it into the zoom-control offset) so a long price never grows the axis mid-hover (audit `D-13`). **Dock-open visibility** is a separately verified acceptance criterion (`AC-D2.1`) requiring **independent Code Reviewer verification after Build** (A25; verification performed and closed via ESC-016/T35). Supersedes the Batch-1 inside-plot right-align | Re-opened D2: the Batch-1 inside-plot position at `view_rect.right()-2` put the chip under the right-hand dock; the lane keeps it out of the data area while remaining visible | Keep the inside-plot right-align (the original defect); widen the axis; deconflict against tick labels (explicitly not required) |
| **D4 zoom label/position** | `-`/`+`/`Reset` 14px/700, `⌕` 21px/700 (14×1.5), button 28×24; cluster `x = panel.width - ctrl.width - axis_width - 12` (fallback 50, `x>=8`), `y=10` | `Reset` was legible at 14px but `⌕` looked small; a fixed margin still overlapped the axis, so position relative to the dynamic axis width keeps the outline inside | One size for all four; larger buttons; fixed 28px margin (clips) |
| **D5 volume log → superseded by D8** | D5 shipped volume log Y (`setLogMode('y',True)`, `0→1.0`, `yRange=(1, max*1.1)`); **D8 supersedes it** | D5 was confirmed Q17 but the new screenshot (D8/Q20) rejects log and negatives | n/a — D8 is the current decision |
| **D6 wick rendering** | Wick: body-coloured `QPen`, `widthF=1.0`, **`setCosmetic(True)`**, `FlatCap`, drawn **before** the body; body cosmetic 1px outline with data half-width **clamped to ≥4-device-px** via `ViewBox px_per_sec`; `ChartPanel._refresh_candles` applies `vb.setRange(...)` **before** generating the candle picture so the clamp binds on a first auto-range load (ESC-013 ordering contract, audit `D-12`) | `CandlestickItem` paints into a `QPicture` in data coordinates; non-cosmetic pens scale with the ViewBox and go sub-pixel at high density. Cosmetic pens are device-pixel stable. The clamp reads `px_per_sec` at generation time, hence the generate-after-`setRange` order | Non-cosmetic pens with larger `w` (no pixel ratio); pixel-space drawing without `QPicture` (more invasive, loses caching) |
| **D7 inter-candle gap** | Body half-width `w = median_diff * 0.325` (gap 35%), keep `0.25` single-bar fallback, keep D6 ≥4-device-px minimum; `xRange` padding `-2*bar_w / +8*bar_w` unchanged | Q19 confirmed “go 35% gap for now” as a modest, testable increase from today’s `0.40` (20% gap); only inter-candle gap grows (~75% more gap) | `0.30` (40% gap, airier); widen `xRange` (adds outer framing, not gap) |
| **D8 volume scale (revises D5; family pinned by RG-002, 2026-09-27)** | Volume `ViewBox` **linear Y** (`setLogMode(y=False)`), `yRange=(0, nice_max)` where `nice_max` is the **smallest member of the single continuous family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` (floor `100`, no fixed ceiling) that is `>= max_vol*1.1`**; `max_vol == 0 → 100`; `y0=0`; ticks `500.0K / 1.0M`, no negatives; bars **price-coloured** (`#34d399` / `#f87171` by `close>=open`). The old fixed list `[10k, …, 10M]` is **retained only as a test fixture** | Current log gives negative ticks and hides the desired `500.0K–2.5M` look; the reference is linear with a dynamic nice max and price-coloured bars (Q20). The pinned family reproduces every confirmed value (`750K`, `1.5M`) and the `10.5M→15M`, `45M→50M`, `50M→75M` cases. `0` lower bound matches “volume cannot go below zero” | Keep log with `0→1.0` floor (rejected); a log/linear toggle (more UI than requested); the fixed list (coarse above 10M, `10k` floor) |
| **D9 volume bar width** | `volume_bars.width = w*2` (same `w` as price post-D7 = 65% of `median_diff`), `y0=0` (the implicit `BarGraphItem` default — `y0` is not supplied), X stays `setXLink`ed; the volume half-width is derived from the **final** view range **after** `vb.setRange` (ESC-020 ordering contract, audit `D-12`) | Fixed `width=0.6` drifts from the price 35% gap; sharing `w` guarantees vertical alignment including the dense 4px minimum. Deriving `w_vol` after `setRange` is required because the shared ≥4-device-px clamp reads `px_per_sec` at generation time | Fixed `0.6`; `0.9×price` (subtly narrower, not requested) |
| **D10 volume toggle** | **Top left of the volume panel** (bottom-left of the price chart) — a **checkable text label `Volume`** (not an eye icon), default **visible**, toggles `volume_plot.setVisible()` and rebalances the `QSplitter` so `price_plot` expands; **not persisted** | Q22 confirmed the placement (A23, 2026-09-27); Q31 confirmed the affordance is the **text label `Volume`** (A22); not persisted was the proposal | Toolbar `Volume` button; `QSettings` persistence (future); splitter-handle-only hiding; an eye icon (explicitly rejected) |
| **D11 drawing price labels (ESC-006 re-scoped)** | Inside-plot `TextItem` at `x = view_rect.right() - 4`, `anchor=(1,0.5)`, `Z=10`, colour = drawing colour; one per price (zone top+bottom, trendline/Fib per level); stacked by the **measured label bounding-box height** — `offset = max(15 px, bbox_height, previous_bbox_height)` so consecutive label boxes never intersect (ESC-014, audit `D-7`); added to the price plot scene. **`AC-D11.4` now covers label-vs-label stacking only** — the crosshair chip is in the Y-axis lane (D2/Q33) and is out of scope for D11 collision accounting | Q23 confirmed inner-right inside the plot; Q33 (2026-09-27) moved the chip to the axis lane, so chip-vs-label deconfliction is retired. A real ~23 px label overlaps a hard-coded 15 px offset, so the offset is measured from the emitted label bbox | Axis-area labels (clipped by dock); left-side labels; keeping the chip in the label lane (the ESC-006 defect) |
| **D12 zone settings popup** | Modal `Rectangle` dialog (pencil + `X`), 4 tabs **Style / Text / Coordinates / Visibility**; **Style: `Extend` omitted** (zone always both sides), `Border` + `Middle line` (unchecked) + `Background` (checked) remain; `#1/#2 (price, bar)` steppers; 8-row Visibility timeframes | Q24 “Extend is omitted” confirmed; the reference’s `Extend right` is the only control to drop | Keep `Extend right` (contradicts user); `Extend both` disabled |
| **D15 horizontal line popup** | Modal `Horizontal line` dialog, same 4-tab pattern; **Style:** `Line` (white solid); **Text:** `12`, `B`/`I`, `Add text`, `Top`/`Right`; **Coordinates:** single `#1 (price)` stepper; Visibility = same 8 rows as zone | Q30 confirmed — four screenshots are the spec; single coordinate is the only structural difference from the zone | Reuse the zone dialog with hidden `#2` (shows an irrelevant field) |
| **D13 watchlist width** | Docked Watchlist freely draggable to `min(floor(0.50×W), W−400)` with min `150px` and chart min `400px`; width persisted as an `int` pixel value via **`QSettings` `watchlist/width`** (default ~220px), clamped on restore and window resize; floating geometry unconstrained | Q25/Q26 confirmed the 50% cap and persistence; `QSettings` avoids a `watchlist` table migration and is per-user | Store width in SQLite (migration cost); no persistence (user asked for it) |
| **D14 watchlist double-click** | `cellDoubleClicked` → set `symbol_input` to the row symbol (uppercased) → call the existing `MainWindow.load_chart()` with current `tf_combo`/`ext_hours_btn`; no-op if same `_current_symbol` (case-insensitive) or IBKR disconnected (`status_bar` message); header/empty area no-op | Q27–Q29 confirmed “identical to Load Chart” semantics with no-ops | A separate load path (duplicates logic); single-click load (loses selection) |
| **D14 mid-drag mode reset (ESC-010)** | A symbol change (including the mid-drag double-click path, `AC-D14.4`) clears the drawing draft/drag **and** returns the router to `IDLE` (transition TR-17) | `DrawingOverlay.set_data()` already clears the draft defensively (`:112–118`); without the mode reset `_active_mode` can read `DRAWING` after the tool was implicitly cleared | Rely on `set_data()` alone (leaves the router mode stale) |
| Drawing drag stability (runtime fix 2026-09-19) | `DrawingOverlay._apply_drag` mutates items **in place**; `_remove_items`/`_clear_all_items` defensively clear `GraphicsScene.dragItem` before `removeItem`; `fibonacci` rebuilds only on level-count change | Remove+rebuild mid-drag left `dragItem` dangling → `sendDragEvent` → `InfiniteLine.mouseDragEvent` on a deleted C++ object → `RuntimeError`. In-place mutation preserves C++ identity | Suppress the warning (hides bug); fork pyqtgraph (maintenance); retain refs (leaks) |
| Testing | pytest + pytest-qt, offscreen, no live TWS | Repo standard; confirmed Q8/Q9 | Manual-only (rejected) |
| **D16 backfill planning service** `[new]` | **`services/backfill_service.py`** — pure, Qt-free: `bar_period_seconds`, `find_missing_spans(cached_ts, now_ts, timeframe)`, `plan_requests(missing_spans, timeframe)` | Matches the repo's pure-service pattern (`session_service`, `indicator_service`); unit-testable offscreen with no Qt/TWS; keeps `MainWindow` orchestration-only | Inline in `load_chart` (untestable, duplicates logic); inside `MarketDataManager` (mixes transport with planning, needs an `ibapi` Contract); inside `BarCache` (data layer must not know fetch windows) |
| **D16 trading-day/holiday calendar** `[existing]` / `[new/changed]` | **`services/market_calendar.py`** — ET weekday + US equity holidays **by rule** (fixed-date, nth-weekday, Good Friday), no external dependency. `[new/changed]` for the ESC-023 correction: the New Year's observed shift is **New-Year's-specific** and carries the **NYSE Rule 7.2 year-end accounting exception** (`AC-D16.7`) — when Jan 1 is a Saturday, **no New Year's closure is observed** and **Dec 31 stays a trading day** (no substitute closure) | Required by `AC-D16.3` (holidays are genuine closures), `AC-D16.1`/`AC-D16.5` (only trading-session bars required) and `AC-D16.7` (Dec 31 of a Jan-1-Saturday year is a trading day, never a closure); by-rule avoids a dead fixed year list. The year-end exception prevents a genuine Dec 31 bar hole from being misclassified as a closure and left silent (`AC-D16.1`/`AC-D16.4`) | Weekday-only (flags every US holiday as a hole — violates `AC-D16.3`); "empty response = closure" (cannot distinguish a real shortfall without error codes); `pandas_market_calendars` — rejected (new dependency; A7/DG1 already accept a hand-rolled ET model); changing the **generic** `_observed` for all holidays (would scramble the still-correct Independence Day/Christmas/Juneteenth shifts) — **rejected** |
| **D16 missing-span detection granularity** | **Trading-day/session presence**: a trading day between `min(cached_ts)` and `now` with **zero** cached bars is missing; adjacent missing days merge into one span; the tail (`last cached day`→`now`) uses the same rule | The reported defect is a whole-session hole (DG21/`AC-D16.5`); day presence avoids false positives from illiquid periods and from Ext-Hours toggling (an RTH-only cache still has bars that day) | Per-period cadence (illiquid/empty pre-market periods look like holes → churn + false shortfall); fetch-window threshold (fails for `1 day`, whose window is `1 Y`); `MAX(ts)` tail-only anchor (**rejected by DG21** — leaves the reported internal hole) |
| **D16 anchoring/chunking** | Reuse `[existing] MarketDataManager.req_historical_data(endDateTime=…)` **unchanged**, stepping `endDateTime` back by `TIMEFRAME_CONFIG[timeframe]["duration"]` until the span start is covered; anchor format = existing `_ibkr_end_date` UTC-hyphenated | The method already accepts `endDateTime` and already throttles/allocates a reqId per request; the configured duration is the natural chunk size; no new IBKR call shape and no signature change | Enlarging `duration` (may exceed IBKR per-request limits; still one request); adding a `duration` parameter (unnecessary) |
| **D16 multi-request correlation** | `[new/changed] ui/main_window.py`: keep `_current_req_id` as the primary id; add `_history_req_ids: set[int]`, a `_history_generation` token, `_backfill_missing_spans`, `_backfill_failed_req_ids`; accept bars from any id in the set; finalise (save + re-read + render) only when the set empties | Preserves single-request behaviour as a set-of-one (no D1–D15 regression); one write + one render per load avoids flicker; generation token + cancel prevents cross-contamination on symbol/timeframe switch | Per-chunk save/render (multiple re-reads + flicker); a dedicated controller class (more surface for little gain) |
| **D16 shortfall surfacing** | Status-bar message + log when a backfill reqId errors or a trading day is still empty after the wave; **never** fabricate a bar | Required by `AC-D16.4` ("surfaced explicitly … never a silent hole") | Silent acceptance of empty chunks (violates `AC-D16.4`) |
| **D16 persistence** | **No schema change**; chunk overlap deduped by `INSERT OR REPLACE` on the existing `(symbol,timeframe,ts)` PK | The `bars` table already keys by symbol/timeframe/ts, so overlapping chunks are idempotent | New `spans`/job table (unneeded) |

## System Components

### Existing layers (unchanged)
- **`config/`** — `settings` (env), `paths` (bundle-aware DB/resource paths), `theme.qss`.
- **`data/`** — `models`, `db` (SQLite singleton), `bar_cache`, `bar_aggregator`, `alarm_store`, `drawing_store`, `study_store`.
- **`services/`** (pure, Qt-free, tested) — `indicator_service`, `gap_vix_service`, `ict_service`, `drawing_service`, `alarm_service`, `sound_service`, `strategy_detection`, plus Batch-1 `session_service`.
- **`ibkr/`** — `client`, `bridge` (Qt signals), `id_manager`, `pacing`, `contracts`, `market_data`, `realtime_bars`, `market_depth`, `order_book`, `orders`, `account`, `subscription_manager`.
- **`ui/`** — `main_window` (orchestrator), `chart_panel`, `candlestick_item`, `chart_mouse_router`, `drawing_overlay`, `alarm_overlay`, `studies_dialog`, `active_trader_panel`, `active_portfolio_panel`, `watchlist_panel`, `overlays/{base,gap_overlay,vix_overlay,ict_overlay}`.

### Built (D1–D6, runtime fix)
- **`services/session_service.py`** `[existing]` — `session_bands(bars, timeframe)`; ET pre/post intervals (DST-aware), clipped to the loaded range; `[]` for `1 day`.
- **`ui/overlays/session_overlay.py`** `[existing]` — `SessionOverlay(StudyOverlay)`; one vertical region per band, owned via `clear()`.
- **`ui/chart_controls.py`** `[existing]` — `ChartControls(QFrame)`; emits `zoom_in`, `zoom_out`, `magnify_toggled(bool)`, `reset`; stylesheet `-`/`+`/`Reset` 14px/700, `⌕` 21px/700.
- **`ui/zoom_overlay.py`** `[existing]` — rubber-band area zoom; sets both axes on release; cancels on `Esc`/right-click; **stays active** after a completed zoom (`AC-D3.4`).
- **`ui/chart_mouse_router.py`** `[new/changed]` — the promoted `RouterMode` state machine (271 lines): the enum, single `_active_mode`, guard-clause dispatch, intent helpers and the RC-3 property-setter reconciliation (see “Router state machine” below). It supersedes the former 51-line tri-boolean router (audit `D-2`).
- **`ui/chart_panel.py`** `[new/changed]` — `_position_zoom_controls()` left-of-axis and lane-aware; crosshair chip relocated to the Y-axis lane (`anchor=(0,0.5)`, D2/Q33); volume `ViewBox` linear with the pinned scaling generator (`_nice_volume_max`, D8); volume `BarGraphItem` `width = w*2` (D9); live `_vol_max`/`_ensure_volume_range` ceiling (ESC-007); the `Volume` text-label toggle (D10); `_reserve_price_tag_lane()` (audit `D-13`) (audit `D-3`).
- **`ui/candlestick_item.py`** `[new/changed]` — cosmetic body-coloured wick behind the body; body cosmetic outline + the ≥4-device-px minimum; `w = median_diff*0.325` (D7; `0.25` single-bar fallback) (audit `D-4`).
- **`ui/drawing_overlay.py`** `[existing]` — in-place drag mutation + defensive `GraphicsScene.dragItem` clearing (runtime fix 2026-09-19); D11 measured-bbox labels and the D12/D15 dialogs are listed under “Implemented changes” below.

### Implemented changes (Batch 3–9: D7–D15 + revision)
- **`ui/chart_mouse_router.py`** `[new/changed]` — `RouterMode` enum, single `_active_mode`, guard clauses in `view_mouse_press`/`view_mouse_drag`/`view_mouse_click`, the normative transition table, intent helpers (`enter_zoom`, `enter_drawing`, `enter_alarm_placing`, `exit_to_idle`) and the RC-3 property-setter reconciliation (see “Router state machine”).
- **`ui/chart_panel.py`** `[new/changed]` — router adapters (`set_zoom_mode`/`set_drawing_tool`/`set_alarm_mode` delegate to the router and keep widget state in sync; signatures unchanged); a `zoom_refused` signal for the `AC-D3.9` status hint; D2/Q33 chip in the Y-axis lane; volume `BarGraphItem` `width = w*2` (D9); volume `ViewBox` linear `yRange=(0, nice_max)` via the scaling generator, price-coloured brushes, `500.0K / 1.0M` tick formatter (D8); live ceiling via a cached running max (ESC-007); D10 `Volume` text-label toggle + splitter handling.
- **`ui/main_window.py`** `[new/changed]` — one status-bar connection for `ChartPanel.zoom_refused` (`AC-D3.9`); D13/D14 watchlist wiring and `QSettings` persistence; ESC-017 `_on_drawing_tool_mode_changed`/`_reset_draw_combo_to_cursor` mirror the overlay’s `mode_changed("cursor")` back into the toolbar combo on TR-4/TR-17.
- **`ui/candlestick_item.py`** `[new/changed]` — `w` factor `0.325` (D7); single-bar `0.25` fallback and D6 4px minimum unchanged.
- **`ui/drawing_overlay.py`** `[new/changed]` — `mouseDoubleClickEvent` hit-test → open the matching settings dialog (D12 zone, D15 horizontal); inner-right `TextItem` labels (`view_rect.right()-4`, `anchor=(1,0.5)`, measured-bbox label-vs-label stacking) for all drawing kinds (D11); symbol-change mode reset support (TR-17 / `AC-D14.4`).
- **Dialogs** `[new]` — `ui/zone_settings_dialog.py` (`Rectangle`, 4 tabs, `Extend` omitted) and `ui/horizontal_line_settings_dialog.py` (`Horizontal line`, 4 tabs, single `#1 (price)`). Shared helpers (`ui/drawing_settings_common.py`) for colour swatches, numeric steppers, and the 8-row Visibility grid.
- **`ui/watchlist_panel.py`** `[new/changed]` — splitter min/max `[150, min(floor(0.50×W), W−400)]`, `QSettings watchlist/width` persistence + restore clamp, and `cellDoubleClicked` → `load_chart()` with same-symbol/disconnected no-ops (D13/D14).

### Router state machine (ESC-002, `AC-D3.7`–`AC-D3.9`)
`[new/changed] ui/chart_mouse_router.py` introduces an explicit, single-valued state:

```python
class RouterMode(Enum):
    IDLE = auto()            # default; cursor/pan; alarm & drawing still hit-tested
    DRAWING = auto()         # a drawing tool is armed (draft may be in progress)
    ZOOMING = auto()         # magnifier active; rubber-band selection armed
    ALARM_PLACING = auto()   # alarm placement mode armed
```

`_active_mode` is the **single source of truth**; an enum value is mutually exclusive
by construction (`DRAWING ∧ ZOOMING` can never be true). Every high-level handler
begins with a **guard clause** that dispatches on `_active_mode`, not on three
independent `is_active()`/`tool_active()` probes. The overlay pointers
(`drawing`/`alarm`/`zoom`) are retained as dispatch handlers.

**Dispatch by mode** (`view_mouse_click` in `DRAWING` reaches the drawing overlay only —
documented behaviour, RC-4b; alarm mode is force-cleared whenever a drawing tool is
armed, so alarm click is unreachable there in production wiring):

| `_active_mode` | `view_mouse_press` | `view_mouse_drag` | `view_mouse_click` |
|---|---|---|---|
| `IDLE` | alarm → drawing (alarm-first, miss falls through) | alarm → drawing | alarm → drawing (prefers alarm then drawing) |
| `DRAWING` | drawing only | drawing only | drawing only |
| `ZOOMING` | zoom only | zoom only | zoom only (returns `False`; view unchanged) |
| `ALARM_PLACING` | alarm only | alarm only | alarm only |

**Normative transition table** (`from` = mode before, `to` = mode after):

| # | From | Trigger | To | Side effects (required) | AC |
|---|---|---|---|---|---|
| TR-1 | `IDLE` | drawing tool selected | `DRAWING` | `drawing.set_tool(tool)`; `zoom.set_active(False)`; alarm mode off | existing |
| TR-2 | `IDLE` | magnifier toggled on | `ZOOMING` | `zoom.set_active(True)` | AC-D3.2/3.4 |
| TR-3 | `IDLE` | alarm placement activated | `ALARM_PLACING` | `alarm.set_alarm_mode(True)`; drawing tool forced to `Cursor` | existing |
| TR-4 | `DRAWING` | magnifier invoked | `ZOOMING` | cancel the in-progress drawing and **discard the draft** (no half-drawn artefact); clear the drawing tool; `zoom.set_active(True)`; uncheck the draw combo | **AC-D3.7 forward (Q35 (a))** |
| TR-5 | `ZOOMING` | drawing tool selected | `DRAWING` | exit `ZOOMING` (`zoom.set_active(False)` + `zoom.cancel()`); activate the tool | **AC-D3.7 reverse (A26)** |
| TR-6 | `ZOOMING` | alarm placement activated | `ALARM_PLACING` | exit `ZOOMING` (`zoom.set_active(False)` + `zoom.cancel()`); enter alarm placement (not blocked by zoom) | **AC-D3.8** |
| TR-7 | `DRAWING` | alarm placement activated | `ALARM_PLACING` | drawing tool forced to `Cursor` (draft discarded); `alarm.set_alarm_mode(True)` | existing |
| TR-8 | `ALARM_PLACING` | drawing tool selected | `DRAWING` | alarm mode off; `drawing.set_tool(tool)` | existing |
| **TR-9** | **`ALARM_PLACING`** | **magnifier invoked** | **unchanged (`ALARM_PLACING`)** | **REFUSE:** do NOT enter `ZOOMING`; do not touch the zoom overlay; the pending alarm placement is NOT cancelled; a status-bar hint is shown; the magnifier control is left unchecked | **AC-D3.9 (Q36 (b))** |
| TR-10 | `DRAWING` | tool set back to `Cursor` | `IDLE` | `drawing.set_tool(TOOL_CURSOR)` | existing |
| TR-11 | `ZOOMING` | magnifier toggled off | `IDLE` | `zoom.set_active(False)` + `zoom.cancel()` | AC-D3.3/3.4 |
| TR-12 | `ZOOMING` | symbol / timeframe change | `IDLE` | `zoom.set_active(False)` (A6) | A6 |
| TR-13 | `ALARM_PLACING` | alarm mode off | `IDLE` | `alarm.set_alarm_mode(False)` | existing |
| TR-14 | any | Esc during a magnifier drag | unchanged (`ZOOMING`) | `zoom.cancel()` only — the selection is cancelled, the mode stays active | **AC-D3.3 + AC-D3.4** |
| TR-15 | any | right-click during a magnifier drag | unchanged (`ZOOMING`) | `zoom.cancel()` only | AC-D3.3 |
| TR-16 | any | Reset clicked | unchanged | view refit only; mode not changed | AC-D3.5 |
| TR-17 | `DRAWING` | symbol change (incl. D14 mid-drag double-click) | `IDLE` | clear the drawing draft/drag; reset router mode to `IDLE` | AC-D14.4 / D3 edge case |

The table is **total** for every `(mode, trigger)` pair the router exposes;
`ALARM_PLACING + magnifier → ALARM_PLACING` (TR-9) is the cell that closes it.

**`_active_mode` derivation / synchronisation (RC-3).** The router is the single writer
of `_active_mode`; `ChartPanel` routes user intent through the router. Because the five
preserved router tests construct the router by **direct attribute assignment**
(`router.drawing = …; router.alarm = …`) and never call an intent API:

1. `drawing`, `alarm`, `zoom` are **properties** backed by `_drawing`/`_alarm`/`_zoom`;
   each setter stores the overlay and calls `_reconcile_mode_from_overlays()`.
2. `_reconcile_mode_from_overlays()` derives `_active_mode` with precedence
   **`DRAWING > ZOOMING > ALARM_PLACING > IDLE`**, probing each overlay defensively
   (`getattr(overlay, "tool_active", lambda: False)()` etc.) because the test
   `FakeOverlay` implements only `tool_active()`.
3. Hot handlers **do not re-derive** the mode; they dispatch only on `_active_mode`.
   In `IDLE`, `view_mouse_press`/`view_mouse_drag` keep the defensive
   `not drawing.tool_active()` guard around the alarm-first attempt; `view_mouse_click`
   tests only `if self._alarm is not None`. This is *not* a behavioural difference:
   `_active_mode == IDLE` implies `_reconcile_mode_from_overlays()` found no
   `tool_active()` overlay (a drawing tool would have forced `DRAWING`), so the guarded
   and unguarded conditions are equal in every reachable state (audit `D-11`).

`[existing] AlarmOverlay` / `DrawingOverlay` keep their accessors; the router consults
them only inside `_reconcile_mode_from_overlays()` (the wiring boundary). `enter_zoom()`
returns `False` (no mode change) in `ALARM_PLACING`; the `ChartPanel` adapter re-unchecks
the magnifier button (`blockSignals`) and emits `zoom_refused`, which `MainWindow`
connects to `status_bar.showMessage(...)` — satisfying `AC-D3.9` without the router
touching any widget.

### Volume nice-number generator (ESC-003 / ESC-008, RG-002 pinned)
`[new/changed] ui/chart_panel.py::_nice_volume_max` is a **pure, importable**
generator over the **single** family **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`**
(`10 × 10^k` is the next decade’s `1`), floored at **`100`**, with **no fixed ceiling**:

```
nice_max = min { v in family, v >= 100 : v >= max_vol * 1.1 }
max_vol == 0  ->  100
```

Testable properties: monotonic non-decreasing; tight coverage
`nice_max / (max_vol * 1.1) <= 2` where the ceiling is above the `100` floor
(`max_vol >= 100/2.2 ≈ 45.5`); the `40M–50M` cases come from the family
(`45M → 50M`, `50M → 75M`). Worked examples that all agree: `0→100`, `800→1_000`,
`3_000→5_000`, `8_000→10_000`, `10_000→15_000`, `80_000→100_000`,
`1_050_000→1_500_000`, `2_200_000→2_500_000`, `10_500_000→15_000_000`,
`45_000_000→50_000_000`, `50_000_000→75_000_000`. The validated axis set
(`0, 500.0K, 1.0M, 1.5M, 2.0M, 2.5M` ticks per Q20) and the `500.0K / 1.0M` formatter
(`AC-D8.3`) are preserved. The original fixed list
`[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` is retained
**only as a test fixture** (every entry is a family member). `_nice_volume_max(0)`
returns the floor `100` (`AC-D8.4`); the retained fixture cross-checks the family
(see `tests/test_volume_linear.py`).

### Live volume ceiling (ESC-007, `AC-D8.6`/`AC-D8.7`)
`w` (candle body half-width) is computed **O(N) once per data load**, and the volume
`nice_max` is computed **O(N) once per data load** from `max(bar.volume)` using the
generator above — **with one explicit exception**: because the **forming last bar’s
volume grows live**, the volume Y ceiling must track the live maximum or the tallest
bar is clipped. The ceiling is therefore **also updated on real-time volume changes**,
but that update is **O(1) against a cached running max**: keep a cached `_vol_max` (the
load-time maximum); on an intra-bar tick compute
`live_max = max(cached_max, last_bar.volume)` and **only widen** the ceiling when
`live_max` crosses the current `nice_max` (a non-crossing tick performs no range write).
On a new bar / new load, `_vol_max` is refreshed O(N). `auto_range=False` refresh paths
(`set_timezone()`) re-apply the cached ceiling rather than being gated on `auto_range`.
This is the documented exception to the per-load rule, and it never clips the forming
bar. *(Corrects the earlier canonical claim that `nice_max` is “not per intra-bar
tick”.)*

### D16 additions/changes (increment validated 2026-10-02; ESC-023 calendar correction 2026-10-02)
> The D16 batch (T37–T41) is **built**. Every D16 component below is therefore
> `[existing]`; the one active change in this pass is the `[new/changed]` New Year's rule in
> `services/market_calendar.py` (ESC-023 / `AC-D16.7`) and its test.
- **`[existing] services/market_calendar.py`** (built T37) — pure, Qt-free ET calendar:
  `is_trading_day(date)`, `trading_days(start_ts, end_ts)`, and
  `session_windows(start_ts, end_ts, ext_hours)` (intraday `04:00–20:00 ET` on trading
  days; one window per trading day for `1 day`). Holidays computed **by rule** (fixed-date
  + nth-weekday + Good Friday) so future years need no data edit.
- **`[new/changed] services/market_calendar.py` — ESC-023 correction (`AC-D16.7`).** The
  New Year's observed shift becomes **New-Year's-specific** and gains an explicit
  **year-end accounting-period exception**: when Jan 1 is a **Saturday** it returns **no
  closure** — so nothing is shifted onto Dec 31, Dec 31 stays a trading day, and **no
  substitute closure is created** (Jan 1 itself is a weekend and remains non-trading). Jan 1
  on a **Sunday** still observes the following Monday; a **weekday** Jan 1 stays a closure.
  `_observed` for Juneteenth / Independence Day / Christmas is **unchanged**, and the
  remaining observed-shift assertions stay as regression guards. `_holidays_for_year`'s
  adjacent-year union is retained as a defensive guard, with its stale “New Year's observed
  on the preceding Dec 31” docstring/comment corrected.
- **`[existing] services/backfill_service.py`** (built T37/T38) — pure, Qt-free planner:
  `bar_period_seconds(timeframe)` (from `data.bar_aggregator.TIMEFRAME_SECONDS`);
  `find_missing_spans(cached_ts, now_ts, timeframe) -> list[MissingSpan]` (trading-day
  presence → merged spans; empty cache → `[]` and the caller falls back to the configured
  window); `plan_requests(missing_spans, timeframe) -> list[RequestPlan]` (each plan =
  `{endDateTime, bar_size, duration}` from `TIMEFRAME_CONFIG` + the `_ibkr_end_date` anchor
  format; ordered newest chunk first; chunk count bounded by the span). In-memory
  dataclasses only (`MissingSpan`, `RequestPlan`); nothing persisted.
- **`[existing] ui/main_window.py`** (built T39; unchanged by this correction) — `load_chart` shows cached bars, calls the pure
  planner, then either skips redundant history requests (empty plan **and** cache current)
  or issues one `req_historical_data(endDateTime=…)` per `RequestPlan` (empty cache → the
  configured-window fallback). `_on_historical_bar` / `_on_historical_data_end` accept any
  reqId in `_history_req_ids` and finalise (save + re-read + render) only when the set
  empties; stale `_history_generation` is dropped. `_on_error` correlates a failed backfill
  reqId with its span, removes it from the set so the wave can finalise, and the shortfall
  is surfaced (status bar + log). `closeEvent` and symbol/timeframe switch cancel every id
  in the set.
- **`[existing] ibkr/market_data.py` — no change required.** Chunking reuses `endDateTime`
  + the configured duration; `pacing_manager.throttle()` and `id_manager.get_id()` are
  already applied per request.
- **`[existing] data/bar_cache.py`** — reused as-is (`get_bars`/`save_bars`);
  `get_last_timestamp` remains available but is **not** required (DG21).
- **`[existing] ui/chart_panel.py`** — unchanged; continuity of `_bars` fixes both panels
  (`AC-D16.2`).

**D16 design flow:** `MainWindow.load_chart` calls
`services.backfill_service.find_missing_spans` + `plan_requests` (pure), then issues one
`MarketDataManager.req_historical_data` per `RequestPlan`. `IBBridge.historical_bar` /
`historical_data_end` feed `MainWindow`, which accumulates `Bar` objects in `_pending_bars`,
saves once via `BarCache.save_bars`, re-reads with `BarCache.get_bars`, and calls
`ChartPanel.update_chart`; `ChartPanel._refresh_candles` drives both candles and volume.
`services.market_calendar` is consumed only by `backfill_service` (via `find_missing_spans`).

### Component relationships
`MainWindow` owns `ChartPanel`, the Watchlist dock, and the Ext-Hours state.
`ChartPanel` owns the price plot, `CandlestickItem`, `SessionOverlay`, `ZoomOverlay`,
the child `ChartControls`, the `ChartMouseRouter`, and the volume `ViewBox` (plus the
D10 toggle and D11 labels). `ChartMouseRouter` is the **single writer of `_active_mode`**
and mediates ViewBox gestures between `ZoomOverlay`, `AlarmOverlay`, and
`DrawingOverlay`. `DrawingOverlay` owns its items, opens the D12/D15 dialogs, and renders
D11 labels. `WatchlistPanel` emits a double-click that `MainWindow` maps to the existing
`load_chart()` path. `reDrawings` payloads persist through `DrawingStore`. The D2 chip’s
Y-axis lane width is reserved up-front (`_reserve_price_tag_lane()` → `_price_lane_width`,
folded into the zoom-control offset) so the chip never grows the axis on hover
(audit `D-13`); `MainWindow` mirrors the overlay’s `mode_changed("cursor")` back into the
toolbar draw combo via `_reset_draw_combo_to_cursor()` on TR-4/TR-17 (ESC-017,
audit `D-14`).

## Data Model
**No schema changes.** D7–D11 are ephemeral view state (candle width, volume scale,
volume visibility, label geometry). D12/D15 read/write the existing `drawings` table
via `DrawingStore` (`payload` JSON: horizontal `{"y": …}` and zone
`{"x1","x2","y1","y2"}`, each plus additive `style`/`text`/`visibility` sub-objects
written by the D12/D15 dialogs and round-tripped on load) with
`services.drawing_service.normalize_payload` still validating. D13 persists a single
`int` pixel width via `QSettings` (not SQLite).
The router mode is **ephemeral runtime state**; the volume running max is an **in-memory
field** on `ChartPanel`. The existing models (`Bar`, `Alarm`, `Drawing`, `DrawingGroup`,
`Position`, `TradeGroup`, `OrderBookLevel`, `UserOrder`) and tables (`bars`, `watchlist`,
`alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `positions`,
`trade_groups`, `position_group_map`) are unchanged.

**D16 (no schema change).** The `bars` table and `Bar` model are unchanged; chunk overlap
is deduped by the existing `(symbol,timeframe,ts)` primary key. D16 adds only in-memory
value types in `services/backfill_service.py` (`MissingSpan {start_ts, end_ts}`,
`RequestPlan {endDateTime, duration, bar_size, span_start_ts, span_end_ts}`) and ephemeral
`MainWindow` runtime state (`_history_req_ids`, `_history_generation`,
`_backfill_missing_spans`, `_backfill_failed_req_ids`); the existing `_pending_bars`
retains its role, now shared across the chunk set.

*As-built note:* `data/db.py` defines `_init_schema` **once** (`data/db.py:14–111`;
the file is 154 lines), followed by `_migrate_schema` (`:113–121`) and
`_table_columns` (`:118`). T26/ESC-001 removed the former shadowed second definition;
`tests/test_db_schema.py` guards the single-definition/schema contract. The previously
flagged latent hygiene debt (audit `D-6`) is **resolved** — no behaviour change.

## Integration Points
- **IBKR historical / RT data** — no new calls. D13/D14 reuse the existing
  `MainWindow.load_chart()` sequence (cancel prior RT `reqId` → `BarCache` → delta
  `reqHistoricalData` → RT `subscribe`); D8/D9 read `Bar.volume`/`close`/`open` only.
- **SQLite** — D12/D15 use `DrawingStore.update_drawing`; no schema change.
- **Qt signal bus / QSettings** — D10 toggle `toggled(bool) → volume_plot.setVisible`;
  `ChartPanel.zoom_refused → status_bar.showMessage` (`AC-D3.9`); D13 uses
  `QSettings("watchlist/width")`; `DrawingOverlay.mode_changed("cursor") →
  MainWindow._reset_draw_combo_to_cursor()` (ESC-017); `IBBridge` unchanged.
- **pyqtgraph GraphicsScene** — `DrawingOverlay` touches `scene.dragItem` only via
  defensive nulling before `removeItem` (runtime fix). No fork.
- **D16 IBKR historical data** — now invoked **one request per chunk** instead of one per
  load, through the same `reqHistoricalData` call shape (`whatToShow="TRADES"`, current
  `useRTH`/`extended_hours`); pacing via the existing `pacing_manager.throttle()` and
  reqIds via `id_manager`. The IBKR error stream (`bridge.error_msg`) is correlated to
  backfill reqIds for `AC-D16.4` shortfall surfacing. **No new external service, no new
  dependency, no new IBKR request type.**
- **D16 trading-day calendar (ESC-023)** — internal to `services/market_calendar.py`; the
  year-end correction adds **no** integration, dependency, or persisted state.

## Non-Functional Approach
- **Correctness (gesture routing):** the `RouterMode` enum makes `DRAWING` and
  `ZOOMING` mutually exclusive; the transition table is total and implemented as
  router intent helpers so code and table cannot drift; the five preserved router tests
  pass verbatim via the property-setter reconciliation.
- **Correctness (chart geometry):** D7’s 35% gap is proportional (`0.325× median_diff`)
  with the D6 4px minimum so dense 1-min stays positive; D9 shares the same `w`;
  D8 ticks are `0`-based linear with nice rounding (3–5 ticks) and no negatives.
  Because both the D6 body clamp and the D9 shared-width minimum read
  `ViewBox px_per_sec` at generation time, `ChartPanel._refresh_candles` applies
  `vb.setRange(...)` **before** generating the candle picture and derives `w_vol` from
  the **final** view range (ESC-013/ESC-020 ordering contract, audit `D-12`).
- **Correctness (drawings):** D11 labels are `anchor=(1,0.5)` inside
  `view_rect.right()-4`, repositioned on `sigRangeChanged`, so they are never clipped
  by the right axis/dock; nearby labels are stacked by their **measured bbox height**
  (`max(15, height, previous height)`, ESC-014 — audit `D-7`) so consecutive boxes never
  intersect; D12/D15 dialogs pre-fill from the drawing payload and
  persist via `DrawingStore`. D2 chip renders in the Y-axis lane (grey pill, white
  text) with axis-tick overlap permitted (`AC-D2.1`–`AC-D2.3`).
- **Correctness (watchlist):** D13 clamps `[150, min(floor(0.50×W), W−400)]` on
  restore and resize; D14 mirrors `load_chart` exactly and no-ops on same
  symbol/disconnected; a mid-drag symbol change also resets the router mode
  (`AC-D14.4`).
- **Performance:** `w` is O(N) once per data load; volume `nice_max` is O(N) once per
  data load **with the documented live-ceiling exception** (`AC-D8.6`) where the
  intra-bar update is O(1) against a cached running max (see “Live volume ceiling”).
  Router dispatch is O(1) (one enum compare per handler); mode reconciliation runs only
  at wiring boundaries; dialog creation is on demand; labels are bounded by drawing
  count.
- **High-DPI:** D6 cosmetic pens and D11 label placement are device-pixel aware
  (`AC-D6.4`, `AC-D11.5`); the D2 chip is a scene `TextItem` and inherits existing
  scaling.
- **Security:** live-order path untouched; Q9 holds — no automated test connects to
  live TWS or transmits an order.
- **Scalability:** overlay/label counts bound to drawing count; volume/price item
  counts bound to bar count; no per-frame allocation added.
- **Correctness (D16 backfill, `AC-D16.1`/`AC-D16.5`):** the planner's outcome is "every
  trading day between the oldest displayed bar and *now* has cached bars" (a tail gap is
  the special case where the missing days run to the end). DG21's internal hole is healed
  because detection is on **trading-day presence**, not `MAX(ts)`. Detection is O(trading
  days in `[min(ts), now]`) + O(N) over cached bars; chunk count is bounded by
  span/configured duration; `pacing_manager` spaces requests; residual empty trading days
  + IBKR errors produce an explicit status-bar/log shortfall and **no bar is ever
  fabricated** (`AC-D16.4`). Both panels are fixed by the single continuous `_bars` list
  (no `ChartPanel` change, `AC-D16.2`). Symbol/timeframe switch is made safe by
  `_history_generation` + cancelling every id in `_history_req_ids`. Genuine closures are
  defined by `market_calendar`; **Dec 31 of a year whose next Jan 1 is a Saturday is
  explicitly *not* a closure** (`AC-D16.7`, ESC-023) — it is a trading day, so a genuine
  hole there is backfilled (`AC-D16.1`) or its shortfall surfaced (`AC-D16.4`), never left
  as a silent hole.
- **D16 testability:** the two new services are **pure and parameterized** over all six
  timeframes and ≥2 symbols (Q39); one offscreen `MainWindow` integration test stubs the
  historical feed (pattern from `tests/test_watchlist_d14_midrag.py`), so no test connects
  to live TWS or transmits an order (Q9).

## Parallel-Build Sequencing Constraint (`touches_files`)
The pipeline now runs Build as a **Lead + Worker pair**: the Lead dispatches only tasks
whose per-task `touches_files` do not overlap within a wave, up to `max_parallel_tasks`
(default **4**; optional user-owned `docs/build/build_config.json`), and is the sole
writer of task status. This is an architecture-level constraint on the task graph:

- `ui/chart_panel.py` is touched by **R1, R2, Phase 1, and Phase 3** → **serial chain**
  (they must not share a wave).
- `ui/main_window.py` is touched by **R1** (status-bar connection) and **Phase 4**
  (watchlist wiring) → serial with each other.
- `ui/chart_mouse_router.py` is touched by **R1 only**.
- `ui/drawing_overlay.py` is touched by **Phase 2** and the Phase-4 mode-reset
  amendment → serial.
- `ui/candlestick_item.py` (Phase 1, D7) may run in parallel with `chart_panel`-based
  tasks; Phase-2 new dialog files may run in parallel; Phase-4
  `watchlist_panel.py`/`QSettings` work may run in parallel (its `main_window.py` part
  serializes with R1).
- Verification tasks touching the same test file must be serialized per file.

This constraint was honoured through Build: tasks **T1–T36** all completed `done`, with
no two overlapping-file tasks in the same wave.

## Post-document rework (ESC-013…ESC-021)
After the 2026-09-27 revision was written, Build executed a second rework wave; this
as-built description folds it in. Each item refines D6/D9/D11
(or their tests) **without altering any decision’s intent**:

| Rework | Nature | Where it lands | Doc basis |
|---|---|---|---|
| ESC-013 (T32) | D6 dense-view clamp ordering — apply `vb.setRange(...)` before generating the candle picture | `ui/chart_panel.py:_refresh_candles`; `ui/candlestick_item.py` clamp | D6 ordering contract (audit `D-12`) |
| ESC-014 (T33) | D11 stacking by **measured bbox height**, `offset = max(15, height, last_height)` | `ui/drawing_overlay.py:_update_inner_labels` | D11 (audit `D-7`) |
| ESC-015 (T34) | test expectation update only (volume log) | `tests/test_volume_log.py` | n/a |
| ESC-016 (T35) | test assertions retargeted to the lane contract | `tests/test_chart_crosshair.py`, `tests/test_crosshair_chip_bounds.py` | D2/Q33 |
| ESC-017 (T36) | `draw_combo` sync on router tool-clear (TR-4/TR-17) via `mode_changed("cursor")` | `ui/main_window.py` | “Component relationships” (audit `D-14`) |
| ESC-020 (T13 rework) | D9 volume-width ordering — derive `w_vol` from the final view range after `setRange` | `ui/chart_panel.py:_refresh_candles` | D9 ordering contract (audit `D-12`) |
| ESC-021 (T13 rework) | D9 test measures the rendered body | `tests/test_volume_width.py` | n/a |

ESC-015/ESC-016/ESC-021 changed tests/docs only; ESC-013/ESC-014/ESC-017/ESC-020
changed behaviour but only to enforce an existing decision’s intent, so **no
architectural decision changed**. Full offscreen suite: **383 passed**.

## Architecture Risks
| Risk | Severity | Mitigation |
|---|---|---|
| Watchlist 50% cap crowds the chart on small screens; persisted width may exceed a new window size | L | Clamp to `min(floor(0.50×W), W−400)`, `min 150px`, `chart ≥400px`, on restore and `resizeEvent`; floating unconstrained |
| ESC-002 regression: switching to an enum changes routing order for an existing tested path | M | The five existing router tests are the regression fence; dispatch table preserves alarm-first in `IDLE`; RC-3 property-setter reconciliation makes `test_drawing_tool_blocks_alarm_press` pass verbatim |
| RC-3 mechanism mis-implemented (mode not derived on direct wiring) | M | Property setters + `_reconcile_mode_from_overlays()`; `test_reconcile_mode_from_wired_overlays` + the five preserved tests |
| `AC-D3.9` refusal accidentally cancels the pending alarm placement or enters `ZOOMING` | M | TR-9 explicit side effects; `test_magnifier_refused_during_alarm_placement` asserts mode unchanged and placement intact |
| D2 dock-open visibility regresses despite the lane move | M | `AC-D2.1` + edge case; Build test + **independent Code Reviewer verification** — performed and closed via ESC-016/T35 (A25) |
| D2 chip clipped at narrow widths / long prices in the axis lane | L | `AC-D2.1` edge cases; PA-R6 right-edge guard; `test_crosshair_chip_renders_in_axis_lane` |
| D8 nice-max just above a boundary leaves extra headroom | L | `max_vol×1.1` before rounding; tight coverage `<= 2`; 3–5 ticks |
| D11 label overlap when many zones share a price | L | Measured-bbox offset `max(15 px, bbox height, previous bbox height)` (ESC-014, audit `D-7`); `AC-D11.4` label-vs-label (chip lane-separated); offscreen test at dense zones |
| D12/D15 dialog duplication (zone vs horizontal) | L | Two dedicated dialogs for AC isolation, or one parameterized dialog — either satisfies |
| D6 ratio inverts at extreme density if the body minimum applies before layout | M | Clamp against live `ViewBox px_per_sec`; generate-after-`setRange` ordering contract (ESC-013); dense-1-min test |
| D6/D9 geometry computed **before** `vb.setRange` leaves dense bars sub-pixel on a first load | L | `_refresh_candles` applies the range first, then generates the candle picture and derives `w_vol` (ESC-013/ESC-020, audit `D-12`); `tests/test_volume_width.py` measures the rendered body |
| D2 chip lane width not reserved up-front would grow the axis mid-hover, leaving the pill on a stale lane | L | `_reserve_price_tag_lane()` probes `PRICE_TAG_LANE_SAMPLE` up-front; `_price_lane_width` folded into the zoom-cluster offset (audit `D-13`) |
| D4 stylesheet specificity / left-of-axis clamp on very narrow windows | L | Scope override to `btn_magnify`; `x>=8`, `y<=15`; geometry test at 500px |
| Volume log `0→1.0` (D5) misreads as data | L | D8 reverted to linear `0` lower bound; D5 decision superseded — **resolved in Build** |
| Nice-number generator changes tick values of already-built Batch-4 behaviour | L | Old list kept as fixture (all members of the pinned family); only the `(0)` expectation updated (`AC-D8.4`, A24) |
| Only-widen ceiling leaves headroom after the live bar shrinks on a partial/out-of-order tick | L | `AC-D8.6` satisfied (no clipping); refreshed O(N) on the next load/new bar |
| Router and `ChartPanel` both writing mode state (drift) | M | Router is the single writer of `_active_mode`; `ChartPanel` methods are adapters; `test_router_mode_is_mutually_exclusive` |
| `chart_panel.py` touched by R1/R2/Phase 1/Phase 3 → serial build chain | L (schedule) | `touches_files` populated per the constraint above; Lead serializes overlapping waves |
| DST / UTC-vs-ET band misplacement | M | `ZoneInfo` boundaries plus DST tests |
| `data/db.py` duplicate `_init_schema` (latent hygiene debt) | — **resolved** | T26/ESC-001 deduplicated it: `_init_schema` is defined once (`data/db.py:14–111`), guarded by `tests/test_db_schema.py` (audit `D-6`) |
| Drawing `InfiniteLine` use-after-free during drag (fixed 2026-09-19) | L (was H) | In-place mutation + defensive `scene.dragItem` clear; 26 drawing tests; suite green |
| `fibonacci` rebuild on level-count change still calls `_restore_drawing_style` mid-drag | L | Guarded by defensive `dragItem` clear; rebuild only when count changes |
| D16 holiday calendar drifts for future years | M | Holidays computed **by rule** (nth-weekday/fixed-date/Good Friday), not a fixed list; `tests/test_market_calendar.py` pins known holidays incl. Good Friday, Juneteenth, observed-day shifts |
| Observed-day shift misclassifies a genuine trading day (Dec 31) as a closure → silent hole (ESC-023 / R27) | M | `AC-D16.7` states the NYSE Rule 7.2 year-end accounting exception; the New Year's-specific rule never shifts a closure onto Dec 31 (no substitute closure); `tests/test_market_calendar.py` asserts `is_trading_day` is **True** for `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31`, and keeps every other observed shift (Independence Day/Christmas/Juneteenth/New Year's-Sunday) as a regression guard |
| D16 IBKR long-ago data beyond retention returns nothing/errors → chart still has a hole | M | Chunk requests respect `pacing_manager`; residual missing trading days + `error_msg` on a backfill reqId are **surfaced** (status bar + log); never fabricate (`AC-D16.4`) |
| D16 many chunks hit IBKR's historical pacing limit | M | Chunk count bounded by span/configured duration; every request already goes through `pacing_manager.throttle()`; a rate-limit `error_msg` is surfaced, not retried in a tight loop |
| D16 stale in-flight responses after a symbol/timeframe switch | H | `_history_generation` token + cancel every id in `_history_req_ids` on switch/close; `_on_historical_bar`/`_on_historical_data_end` drop non-current generation and non-member reqIds |
| D16 reusing `_pending_bars` for the chunk set regresses the single-request path | M | The set-of-one case is behaviourally identical; the existing reqId filter becomes set membership; D1–D15 tests must stay green |
| D16 equity calendar mis-models futures (which trade some US holidays) | L | Consistent with the accepted `session_service`/DG1/A7 default (equity sessions for all symbols); recorded as PA-D16-3 and flagged (FI-D16-2, accepted with the futures caveat) |
| D16 illiquid symbols have legitimately empty trading sessions → false "missing" | M | Day presence needs only **≥1** bar; a wholly empty day is the reported defect class; the shortfall is surfaced (not fatal), and the per-day cadence assertion applies only to the stubbed liquid scenarios (FI-D16-1) |
| D16 detection window grows unbounded if the cache is very old | L | Detection is bounded by `min(cached_ts)`; chunking is bounded by the span; shortfall surfaced when retention is exceeded |

---

## D17 + D18 increment — panel layout / dock sizing in full screen (validated 2026-10-03)

> **Increment scope.** An *incremental* change on top of the built, green D1–D16 system
> (commit `fd0bb0a`). D1–D16 are **frozen** and are **not** re-planned. This is an
> existing-repo run: the marker sentence and Current Tech Stack are preserved in
> `requirements.md`; PyQt6 + pyqtgraph is a **hard constraint**. No stack change, no
> schema change, no new dependency, no new integration, and no live-order-path change.
> Items below are labelled `[existing]`, `[new]`, or `[new/changed]`.

**Summary.** D17/D18 are **pure UI-layout changes within the existing PyQt6 dock
architecture**. The change introduces **one shared, chart-area-relative width model** and
applies it **live, during dock drags and dock/resize events**, to two regions: the **left
watchlist dock** (cap `floor(0.50 × chart_area)`, min 150px, default ~220px, persisted) and
a **single right dock region** holding the Active Trader ladder and the Portfolio section
**stacked vertically** (cap `floor(0.40 × chart_area)`, inherently equal width by
construction). Both caps are further clamped by a **shared chart-minimum rule** (~400px) so
enlarging one region can force the other to shrink (B3 / `AC-D18.5`), and the right region
is made **fully visible in full screen** (`AC-D18.1`) by bounding its content minimum width
and by an explicit full-screen / `resizeEvent` normalize step. The D13 helpers are
**re-parameterised from window width to chart area** as the single source of the cap (B1),
and the affected D13 tests are updated in lockstep. D1–D16 modules are untouched except as
noted.

### Codebase Summary (existing repository — D17/D18 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2183 nodes,
> refreshed 2026-10-03) and then **validated against the current source files** (the
> repository is authoritative). The graph surfaced the relevant symbols
> (`watchlist_max_width`, `clamp_watchlist_width`, `ActiveTraderPanel`,
> `ActivePortfolioPanel`, `MainWindow.__init__`, `test_d10_d13_integration`); every claim
> below was confirmed by direct inspection of the current tree on 2026-10-03.

- **`[existing] ui/main_window.py` — `MainWindow.__init__` central + dock setup** (`:205–252`):
  - Central widget is a `QWidget` (`central`) with a `QVBoxLayout` holding the toolbar and
    `ChartPanel`. The **chart area** for D17/D18 purposes is this central region.
  - **Watchlist dock** (`:217–232`): `QDockWidget("Watchlist")` in `LeftDockWidgetArea`;
    `watchlist_panel.setMinimumWidth(150)` (`:225`); width restored via
    `load_watchlist_width(...)` and applied with **one** `resizeDocks([watchlist_dock],
    [width], Horizontal)`. No `setMaximumWidth` anywhere.
  - **Right docks** (`:234–252`): **two separate `QDockWidget`s** —
    `QDockWidget("Active Trader")` and `QDockWidget("Portfolio")`, **both** in
    `RightDockWidgetArea`, with no min/max width and **no `resizeDocks` call**. This is the
    exact shape B2 says must become **one region**.
- **`[existing] ui/main_window.py` — `resizeEvent`** (`:959–970`): calls
  `watchlist_max_width(self.width())` and re-clamps **only when the dock is already wider
  than max**. `resizeEvent` fires on **window** resize, not on a dock-splitter drag; there
  is **no `splitterMoved` / `dockLocationChanged` handler**.
- **`[existing] ui/main_window.py` — persistence**: the watchlist width is persisted via
  `save_watchlist_width(...)` (`QSettings("NDThinkChart","NDThinkChart")`, key
  `watchlist/width`) — **no SQLite change**.
- **`[existing] ui/main_window.py` — DOM toggle** (`:1011–1020`): `_on_dom_toggled` finds
  the dock by `findChild(QDockWidget, "Active Trader")` and flips its visibility. A
  **title-based lookup** that the D18 reshaping must keep working.
- **`[existing] ui/main_window.py` — full-screen handling: NONE.** No `showFullScreen`,
  `setWindowState`, `WindowFullScreen`, or full-screen branch exists anywhere in `ui/`
  (confirmed by grep). Full screen is an OS window state.
- **`[existing] ui/watchlist_panel.py`** (`:29–62`): the D13 helpers —
  `WATCHLIST_MIN_WIDTH = 150`, `CHART_MIN_WIDTH = 400`, `DEFAULT_WATCHLIST_WIDTH = 220`,
  `WATCHLIST_WIDTH_KEY = "watchlist/width"`;
  `watchlist_max_width(window_width) = max(150, min(int(W*0.50), W-400))`;
  `clamp_watchlist_width(width, window_width)`;
  `load_/save_watchlist_width`. **Parameterised on window width**, not the chart area, and
  **do not account for the right docks** — the B1 denominator defect and the DG24
  unaccounted-consumer gap. `WatchlistPanel` emits `row_double_clicked` (D14).
- **`[existing] ui/active_trader_panel.py` — `ActiveTraderPanel(QWidget)`** (`:410`):
  `QVBoxLayout` (margins 6) with a header row (`QSpinBox` qty 1..100000), a `QTabWidget`
  (`LadderTable`, `BookTable`, `OrderEntryWidget`), and the ladder click wiring. **No
  `setMinimumWidth` / `setMaximumWidth` / `setMinimumSize` / `sizeHint` override** — the
  ladder/book tables' natural size can demand unbounded width.
- **`[existing] ui/active_portfolio_panel.py` — `ActivePortfolioPanel(QWidget)`** (`:27`):
  `QVBoxLayout` with a summary label, a **10-column** `QTableWidget`
  (`horizontalHeader().setSectionResizeMode(Stretch)`) and a `Refresh` button. **No width
  governance** either.
- **`[existing] ui/chart_panel.py` — `ChartPanel`**: owns a vertical `QSplitter`
  (`price_plot`, `volume_plot`, `osc_plot`) — **inside** the chart area, unrelated to the
  dock widths. `resizeEvent` (`:438`) only repositions the zoom controls and the volume
  toggle. Unchanged by D17/D18.
- **`[existing] tests/`** — four integration/regression tests depend on the right docks:
  - `tests/test_d10_d13_integration.py` (`:33,50–52`): hides docks whose `windowTitle()` is
    `"Active Trader"` / `"Portfolio"`; asserts the **old window-width clamp math**.
  - `tests/test_watchlist_d14_midrag.py` (`:34,80–81`) and `tests/test_history_backfill.py`
    (`:192–193`): hide the same two titles to isolate their own concern.
  - `tests/test_crosshair_axis_lane.py` (`:101–105`): resolves `docks["Active Trader"]` and
    `docks["Portfolio"]` by **`windowTitle()`** and asserts the D2 chip does not intersect
    either `frameGeometry()`.
  - `tests/test_watchlist.py` (`:24–35`): asserts the helper maths
    `watchlist_max_width(1400)==700`, `watchlist_max_width(600)`, `watchlist_max_width(100)`.

**Existing data models / tables (unchanged by D17/D18):** `Bar`, `Alarm`, `Drawing`,
`DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`, `UserOrder`; tables `bars`,
`watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `positions`,
`trade_groups`, `position_group_map`. **No schema change** — width is ephemeral view state
plus the existing `QSettings` key.

**Existing integrations in play (unchanged):** IBKR, SQLite, Qt signal bus, **`QSettings`**
(watchlist width), `PyQt6.QtWidgets` dock geometry APIs. **No new external integration.**

**Key structural facts the D17/D18 design must respect.**
1. There is **no live width enforcement during a dock drag** anywhere — the cap runs only at
   construction and on window `resizeEvent` (DG23).
2. The watchlist cap uses **window width** and **ignores the right docks** (DG24 / B1).
3. The two right docks are **un-owned horizontally** (no min/max, no `resizeDocks`, no cap)
   and are a **separate region each**, not one region (DG24).
4. **Title-based dock lookups** exist in production (`_on_dom_toggled`) and in four tests —
   the reshaping must not silently break `findChild(QDockWidget, "Active Trader")` or the
   `windowTitle()`-keyed test helpers, or, if it must, the tests are updated in lockstep
   (R28 / `AC-D18.8`).

### Tech Stack Decisions (D17/D18 increment)

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged** `[existing]`: Python 3.11+, PyQt6 (≥6.6), pyqtgraph (≥0.13). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D17/D18 are layout fixes only | A nested `QSplitter` layout replacing docks entirely — rejected (out of scope, would re-open D2/D14/QSettings behaviour) |
| Where the live clamp is enforced | **`[new/changed]`** a single `MainWindow._apply_dock_widths()` that reads the **current chart-area width** from `centralWidget().width()` and calls `resizeDocks(...)` for both regions; invoked from a **`QSplitter.splitterMoved`** handler on the dock areas' internal splitter **and** from `MainWindow.resizeEvent`, plus a one-shot `QTimer.singleShot(0, …)` normalize on show/state change. Reuses the D13 helpers as the cap source | The D17 root cause is that nothing hooks the *dock-splitter drag* — only `resizeEvent`. Connecting the actual handle signal enforces the cap **during** the drag (`AC-D17.3`); one shared function makes left/right cross-clamping coherent (`AC-D18.5`) | A per-dock `eventFilter` on the splitter handle (more fragile, duplicate wiring); a custom `QDockWidget` subclass overriding `resizeEvent` (Qt's internal splitter still drives the dock, so the cap would still be missed mid-drag); `setMaximumWidth` only (**rejected as sole mechanism** — no chart-minimum cross-clamp, and it constrains the widget but not the drag behaviour D18 needs) |
| Cap denominator | **`[new/changed]`** both caps measured against **`chart_area` = the central widget width** (the region holding the chart, excluding both dock regions), per B1/B2 — **not** `MainWindow.width()` as in D13's Q25 | B1 corrects D13's denominator in lockstep; once the right region exists, the point the cap is measured from must exclude both dock regions or the chart starves | Keep window-width denominator (R28: contradicts D17, starves chart with a visible right dock) |
| Watchlist cap formula | **`[new/changed]`** `watchlist_max_width(chart_area_w)` = `max(150, min(floor(0.50 × chart_area_w), chart_area_w − 400))`; the **400px chart minimum is the shared constant** `CHART_MIN_WIDTH` | Preserves the D13 helper name/signature shape (one-arg → int) so tests update minimally; keeps the chart-minimum clamp | A two-argument `(width, chart_area, right_dock_w)` — more call sites to thread; preferred alternative is the *shared* function below |
| Right region cap | **`[new]`** `right_dock_max_width(chart_area_w)` = `max(RIGHT_MIN, min(floor(0.40 × chart_area_w), chart_area_w − 400))` with `RIGHT_DOCK_MIN_WIDTH = 200` | New requirement (D18); symmetric with the watchlist helper; same chart-minimum rule | A hard-coded 40% of window (ignores cross-clamp) |
| Combined cross-clamp (B3) | **`[new]`** one pure function `plan_dock_widths(chart_area_w, requested_left, requested_right)` → `(left, right)` that applies each cap, subtracts both from the chart area, and **shrinks whichever dock is over budget** (preferring to shrink the dock being resized less) until `chart_area ≥ 400` | Makes `AC-D18.5` ("enlarging one forces the other to shrink") a **pure, unit-testable** rule rather than emergent Qt behaviour; the D13/D17 cap helpers remain the per-dock cap source | Rely on Qt's own `resizeDocks` negotiation (non-deterministic across platforms; cannot guarantee `chart_area ≥ 400`); clamp only the resized dock (fails `AC-D18.5`) |
| Single right region shape (B2) | **`[new/changed]`** replace the two right `QDockWidget`s with **one** `QDockWidget` containing a `QWidget` whose `QVBoxLayout` stacks **ActiveTraderPanel** over **ActivePortfolioPanel** (optionally via a `QSplitter(Vertical)` so the user can adjust the vertical split, with equal **width** guaranteed by the single region) | B2: one region ⇒ the two sections are **inherently equal width** (`AC-D18.3`) and the 40% cap applies to the region; keeps D2/D10 title lookups working by keeping an identifiable title and a stable object name | Keep two docks and force equal widths via `resizeDocks` on both (fragile; a drag on one still leaves the other ungoverned; violates the "one region" intent) |
| Full-screen visibility (D18) | **`[new]`** (a) bound the **content minimum** of both right panels so the ladder/portfolio tables cannot demand unbounded width (`AC-D18.6`); (b) an explicit **full-screen / `changeEvent(WindowStateChange)` + `resizeEvent` normalize** that re-applies the cap against the *visible* window rect and calls `resizeDocks` so the region is on-screen with non-zero width (`AC-D18.1`) | The reported defect is the region being clipped off-screen; `AC-D18.6` requires content not to force it off-screen; a measurable geometry assertion (dock `geometry()` within window `rect()`, `width() > 0`) is the test condition | Pure content-`sizeHint` change (does not guarantee on-screen geometry); auto-hide (violates "visible in full screen") |
| Persistence | **`[existing]` for the watchlist** (`QSettings watchlist/width`, re-clamped to the new chart-area cap); **`[new]` explicit "not persisted" for the right region** (A36 / `AC-D18.7`) | Q26 still required for the watchlist (B4); the user did not request right-region persistence | Persist the right region too (not requested; broader than the requirement) |
| Tests | **`[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS; add pure-function unit tests for the new helpers + offscreen `MainWindow` geometry tests; **update the D13 clamp-math assertions in lockstep** | Repo standard (Q8/Q9); `AC-D17.6`/`AC-D18.8` require the existing suite green (or updated where B1 changes the denominator) | Manual-only (rejected) |

### System Components (D17/D18 increment)

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout(toolbar, ChartPanel)`; its
  `width()` **is** `chart_area` for all D17/D18 maths. Unchanged structurally.
- **`[existing]` left watchlist dock** — `QDockWidget("Watchlist")` in
  `LeftDockWidgetArea`, min 150px. Kept; gains no new widget of its own.
- **`[new/changed]` single right dock region** — one `QDockWidget` (e.g.
  `QDockWidget("Active Trader")`, with the Portfolio section inside it) whose widget is a
  container `QWidget` with a vertical layout stacking `ActiveTraderPanel` over
  `ActivePortfolioPanel`. This **replaces** the two separate right `QDockWidget`s
  (`ui/main_window.py:234–252`). The container sets a bounded `minimumWidth`, and inside it
  each panel's scrollable content is width-bounded so neither can force the region
  off-screen (`AC-D18.6`).
- **`[new]` `ui/dock_layout.py`** (pure, Qt-free where possible) — the shared width model:
  - constants `CHART_MIN_WIDTH = 400` (kept in agreement with `watchlist_panel`),
    `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`, `RIGHT_DOCK_MIN_WIDTH`,
    right cap fraction `0.40`, watchlist cap fraction `0.50`;
  - `watchlist_max_width(chart_area_w) -> int`;
  - `right_dock_max_width(chart_area_w) -> int`;
  - `plan_dock_widths(chart_area_w, requested_left, requested_right) -> (left, right)` —
    the **B3 cross-clamp** (`AC-D18.5`), pure and exhaustively unit-testable.
  
  Rationale: keeps the chart-minimum rule in one place and off the widget layer, matching
  the repo's established **pure-service** pattern (`session_service`, `backfill_service`).
- **`[new/changed]` `ui/watchlist_panel.py`** — the D13 helpers (`watchlist_max_width` /
  `clamp_watchlist_width` / `load_/save_watchlist_width`) are **re-parameterised to the
  chart-area denominator** (B1), delegating to `ui/dock_layout`. Their one-argument
  signature shape is preserved so callers and tests update minimally.
- **`[new/changed]` `ui/main_window.py`**:
  - `_apply_dock_widths()` — reads `centralWidget().width()`, computes the plan via
    `plan_dock_widths`, and issues `resizeDocks([watchlist_dock], [left], Horizontal)` +
    `resizeDocks([right_dock], [right], Horizontal)`. Idempotent; guarded with
    `blockSignals`/re-entrancy flags so an applied resize does not recurse.
  - A **`splitterMoved` connection** to the dock areas' internal `QSplitter` → 
    `_apply_dock_widths`. This is the piece that makes the cap bind **during** the drag
    (`AC-D17.3`).
  - `resizeEvent` — re-clamps **both** regions (not only when already over max) and in
    **both directions** (`AC-D17.2`/B4), via `_apply_dock_widths`.
  - `changeEvent(WindowStateChange)` — a full-screen normalize step (`AC-D18.1`).
  - `closeEvent` — persists the watchlist width (`[existing]` behaviour retained, re-clamped
    to the new cap).
  - `_on_dom_toggled` — keeps the title-based `findChild(QDockWidget, "Active Trader")`
    lookup valid against the new single region.
- **`[new/changed]` `ui/active_trader_panel.py` / `ui/active_portfolio_panel.py`** — add a
  **bounded minimum/ideal width** to each panel (and make the tables' horizontal sizing
  respect the available width rather than demanding the sum of column widths) so content
  cannot push the region off-screen (`AC-D18.6`). No behavioural change to ladder/portfolio
  logic or signals.
- **`[existing]` `ui/chart_panel.py`** — the in-chart vertical `QSplitter` is a separate
  concern; no change. The D2 chip's Y-axis-lane geometry is unaffected by dock *width*
  beyond the already-verified "not covered by the dock" property.
- **`[existing]` D1–D16 modules and the live-order path** — untouched.

### Data Model (D17/D18 increment)

**No schema change.** D17/D18 are ephemeral view state.

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width` (int, px) —
  retained; restore re-clamped to the **new chart-area cap** (`AC-D17.4`). No new key.
- `[new]` Right region width/visibility is **explicitly not persisted** (A36 / `AC-D18.7`).
- `[new]` In-memory-only runtime fields on `MainWindow`: `_watchlist_width`,
  `_right_dock_width`, and re-entrancy guards for `_apply_dock_widths` (no model/table
  changes).
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

### Integration Points (D17/D18 increment)

- **`[existing]` `QSettings`** — watchlist width persistence; re-clamped on restore.
- **`[existing]` Qt signal bus / dock geometry APIs** — `QSplitter.splitterMoved`,
  `QMainWindow.resizeEvent`, `changeEvent(WindowStateChange)`, `QMainWindow.resizeDocks`
  drive the live clamp. No new external service.
- **`[new]` `MainWindow._apply_dock_widths` ↔ dock widgets** — the single wiring point
  connecting drag/resize/full-screen events to the shared width model.
- **`[existing]` test dock lookups** — `findChild(QDockWidget, "Active Trader")` and the
  `windowTitle()`-keyed helpers in four tests must keep resolving the right region (or the
  tests are updated in lockstep).
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema, no
  dependency.

### Non-Functional Approach (D17/D18 increment)

- **Correctness (live cap, D17):** the cap binds **during the drag** because the width plan
  is recomputed from `centralWidget().width()` on every `splitterMoved`, using the D13
  helpers as the cap source (`AC-D13.1`, `AC-D17.1`–`AC-D17.3`). Both directions work
  because the clamp is two-sided (min 150px, cap) (`AC-D17.2`/B4).
- **Correctness (single right region + equal width, D18):** one region ⇒ the stacked Active
  Trader and Portfolio sections share the region width by construction (`AC-D18.3`); the
  40% cap applies to the region (`AC-D18.2`).
- **Correctness (chart minimum / cross-clamp, B3):** `plan_dock_widths` guarantees
  `chart_area ≥ 400px`; enlarging one region shrinks the other when needed (`AC-D18.5`). The
  rule is a pure function, so it is unit-testable independent of Qt.
- **Correctness (full-screen visibility, D18):** `AC-D18.1` is made measurable — the right
  region's `geometry()` lies within the window `rect()` with `width() > 0`, and content
  minimums cannot force it off-screen (`AC-D18.6`). **No `showFullScreen` call is added**;
  the normalize hook reacts to the OS full-screen/WM state change and to resize.
- **Persistence (`AC-D17.4`):** the watchlist width survives restart, restored as an int px
  value clamped to the current chart-area cap (default ~220px, never <150px); the right
  region is not persisted (`AC-D18.7`).
- **Performance:** `_apply_dock_widths` is O(1) (no bar/table iteration); it runs on
  drag/resize events only, and is guarded against recursive resize loops. No per-frame cost
  added to chart rendering.
- **High-DPI / small displays:** the ~400px chart minimum plus the per-dock minimum yields
  gracefully on a small full-screen display (D18 edge case); when
  `floor(0.40 × chart_area) < region minimum`, the region minimum wins and the chart-minimum
  rule still applies.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to live
  TWS or transmits an order. D18's reshaping changes only the container around the ladder,
  not any order signal or handler.
- **Regression (`AC-D17.6`/`AC-D18.8`):** D1–D16 stay frozen; the D13 clamp-math assertions
  in `tests/test_watchlist.py` and `tests/test_d10_d13_integration.py` are updated **in
  lockstep** to the chart-area denominator (never left contradicting D17), and the
  title-based dock helpers keep working.

### Architecture Risks (D17/D18 increment)

| Risk | Severity | Mitigation |
|---|---|---|
| Hooking the dock-area internal `QSplitter.splitterMoved` is Qt-version-layout dependent and may not fire as expected | M | Obtain the splitter defensively after `show()`; **fall back to a `QDockWidget.eventFilter` on the dock/its handle** and to `resizeEvent`; unit-test the pure `plan_dock_widths` independently of the event source so the *rule* is verified even if a wiring path is Qt-dependent |
| `_apply_dock_widths` calling `resizeDocks` re-triggers `splitterMoved`/`resizeEvent` → recursion / jitter | M | Re-entrancy guard flag around the apply; only call `resizeDocks` when the computed sizes differ from current by >1px; `blockSignals` on the splitter during application |
| Re-shaping two docks into one region breaks title-based lookups (`_on_dom_toggled`, `test_crosshair_axis_lane.py`, `test_d10_d13_integration.py`, `test_watchlist_d14_midrag.py`, `test_history_backfill.py`) (R28/`AC-D18.8`) | M | Keep a stable, identifiable dock title (and an `objectName`); update the four tests in lockstep where the shape genuinely changes; assert the D2 chip/dock non-overlap (`test_crosshair_axis_lane`) still holds against the single region |
| Content minimum width (wide ladder / 10-column portfolio table) forces the region off-screen despite the cap (`AC-D18.6`) | M | Bound each panel's `minimumWidth`/`sizeHint` and let the tables scroll/clip internally; the geometry test asserts the region stays within the window and within the cap with wide content |
| `chart_area ≥ 400px` cannot be honoured on a tiny window when both dock minimums plus chart minimum exceed the width | L | Document the precedence (chart minimum wins; docks yield to their minimums) as the D13/D18 edge case already allows; assert no crash and stable geometry |
| Existing D13 tests encode the **old window-width** clamp math and could be left contradicting D17 (R28) | M | Update the assertions in `tests/test_watchlist.py` and `tests/test_d10_d13_integration.py` to the chart-area denominator as part of the same change set; treat "green but contradicting" as a failure |
| Full-screen normalize fires before the window is laid out and computes against a stale rect | L | Use a one-shot `QTimer.singleShot(0, …)` after the state change plus the `resizeEvent` path; the geometry assertion catches a missed normalize |

### Parallel-build sequencing constraint (D17/D18 increment)

- `ui/dock_layout.py` is **new** and should be authored in Phase 1; after that it is
  read-only unless Phase 4 adjusts a helper.
- `ui/main_window.py` is touched by **Phases 2, 3, and 4** → a **serial chain** for those
  phases (they must not share a wave).
- `ui/active_trader_panel.py` / `ui/active_portfolio_panel.py` are touched by **Phases 3 and
  4** → serial with each other; Phase 3 may run in parallel with the Phase 2
  `main_window.py` work only if their `touches_files` do not overlap (panel files vs
  `main_window.py`), but Phase 4 depends on both.
- Test-file updates in Phase 5 may parallelise across the four test modules.
- Build must not run two tasks with overlapping `touches_files` in one wave.

---

## D19 increment — toolbar scroll/elide wrapper (validated 2026-10-05)

> **Increment scope.** An *incremental* change on top of the **built, green D1–D18** system
> (commit `5bd7c93`; full offscreen suite **566 passed**). D1–D18 are **frozen** and are
> **not** re-planned. This is an existing-repo run: the marker sentence and Current Tech
> Stack are preserved in `requirements.md`; **PyQt6 + pyqtgraph is a hard constraint**. No
> stack change, no schema change, no new dependency, no new external integration, and no
> live-order-path change. Items are labelled `[existing]`, `[new]`, or `[new/changed]`.

**Summary.** D19 is a **minimal, in-place UI change**. The existing toolbar `QWidget` is
wrapped in a horizontal `QScrollArea` (no frame, `setWidgetResizable(False)`, horizontal
`ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`) whose height is fixed at **36px**, and
the wrapper is inserted into the central widget's `QVBoxLayout` **where the bare toolbar
was**. The toolbar therefore contributes only a small minimum width to the central widget,
which can now shrink; the **already-built** D17/D18 width model then becomes effective in a
toolbar-visible window. Nothing else changes: the watchlist cap (`floor(0.50 × chart_area)`,
B6), the pure `ui/dock_layout.py` model, `_apply_dock_widths`, the single right-dock region,
and all D1–D18 behaviour are untouched.

### Codebase Summary (existing repository — D19 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2366 nodes,
> refreshed 2026-10-05) and then **validated against the current source files** (the
> repository is authoritative). The graph surfaced the relevant symbols (`MainWindow`,
> `_apply_dock_widths`, `_chart_area_width`, `WatchlistPanel`, `test_dock_widths_d18`,
> `test_dock_layout`); every claim below was confirmed by direct inspection of the current
> tree on 2026-10-05, and independently re-confirmed by the Validator's offscreen probe.

**Toolbar construction — `[existing] ui/main_window.py:100–211`**
- `toolbar = QWidget()`; `toolbar.setFixedHeight(36)`; inline stylesheet
  (`background: #101218; border-bottom: 1px solid #232938;`).
- `tb_layout = QHBoxLayout(toolbar)`, margins `(8, 0, 8, 0)`, spacing `6`.
- Fixed-width controls: `symbol_input` 120, `tf_combo` 90, `mode_combo` 110, `sound_btn` 56,
  `ext_hours_btn` 80, `tz_combo` 110, `draw_combo` 110, `draw_set_combo` 140,
  `draw_delete_btn` 38; plus variable-width buttons/labels (`Load Chart`, `Studies…`,
  `Alarms (0)`, `Alarm Mode`, `DOM`, `Sets…`, `Symbol:`, `TF:`, `Mode:`, `Draw:`, `|`).
- Layout order ends with `tb_layout.addStretch()` then `conn_badge` (`QLabel("● Connecting")`,
  `:186–187`, `:210–211`). The stretch means the badge is pushed to the right edge.
- **Consequence:** the toolbar's `minimumSizeHint().width()` is ≈ **1716px** (sum of the
  fixed widths + labels + spacings + button size hints).

**Central-widget composition — `[existing] ui/main_window.py:213–223`**
- `self.chart_panel = ChartPanel(tz_offset=…)`; `central = QWidget()`;
  `vbox = QVBoxLayout(central)` (margins `0`, spacing `0`); `vbox.addWidget(toolbar)`;
  `vbox.addWidget(self.chart_panel)`; `self.setCentralWidget(central)`.
- **Consequence:** `centralWidget().minimumSizeHint().width()` is therefore ≈ 1716px, so
  `QMainWindow` cannot shrink the central area below it and the dock splitter has no slack.

**Chart-area denominator + D17/D18 width model — `[existing]`**
- `MainWindow._chart_area_width()` (`:1027–1038`) returns `centralWidget().width()`, falling
  back to `self.width()` when the central widget is absent/not yet laid out.
- `MainWindow._apply_dock_widths()` (`:1101–1168`) is the **single apply entry point**; it
  reads `_chart_area_width()`, plans via `_plan_dock_widths()` (`:1055–1099`, delegating to
  the pure `ui/dock_layout.plan_dock_widths`), and issues `resizeDocks`. It is driven by the
  dock event filter, `resizeEvent`, `changeEvent(WindowStateChange)`, the deferred normalize
  (`_deferred_dock_setup`), and `right_dock.visibilityChanged`
  (`_on_right_dock_visibility_changed`).
- `ui/dock_layout.py` (`[existing]`, pure, Qt-free) is the single source of truth:
  `CHART_MIN_WIDTH = 400`, `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`,
  `RIGHT_DOCK_MIN_WIDTH = 200`, `WATCHLIST_CAP_FRACTION = 0.50`,
  `RIGHT_DOCK_CAP_FRACTION = 0.40`; `watchlist_max_width`, `right_dock_max_width`,
  `plan_dock_widths` (B3 cross-clamp).
- Single right dock region — `[existing]`: one `QDockWidget("Active Trader")` (objectName
  `"Active Trader"`) whose container stacks `ActiveTraderPanel` over `ActivePortfolioPanel`;
  the region keeps the title/objectName so `_on_dom_toggled`'s
  `findChild(QDockWidget, "Active Trader")` resolves it.
- Watchlist dock — `[existing]`: `QDockWidget("Watchlist")` in `LeftDockWidgetArea`,
  `setMinimumWidth(WATCHLIST_MIN_WIDTH)`.

**Affected D17/D18 test harnesses (the masking) — `[existing] tests/`**
Five test modules locate the toolbar through the central layout and hide it, exactly as
`DG28` records. After the D19 fix, `centralWidget().layout().itemAt(0).widget()` returns the
**scroll wrapper**, not the toolbar:
- `tests/test_dock_widths_d17.py:67–72` — `_make_window` hides the toolbar (its docstring at
  `:10–14` admits it "pins the central widget … masking the very behaviour under test").
- `tests/test_dock_widths_d18.py:111–116` — same masking.
- `tests/test_dock_widths_d18_impl.py:67–72` — same masking.
- `tests/test_dock_d18_region.py:46–51` — same masking.
- `tests/test_dock_layout.py:315–319` — same masking.
- **Not masked:** `tests/test_d10_d13_integration.py` does **not** hide the toolbar (it hides
  only the right region, `:35`/`:52–54`) and already derives `max_w` from the live
  `centralWidget().width()`, so the D19 fix does not break it (Validator probe confirmed all
  its assertions hold post-fix).

**Existing data models / tables — unchanged by D19**
`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`,
`UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. **No schema change.**

**Existing integrations in play — unchanged by D19**
IBKR historical/RT data, SQLite, the Qt signal bus, `QSettings("NDThinkChart","NDThinkChart")`
key `watchlist/width`, and `PyQt6.QtWidgets` dock/geometry APIs. **No new external
integration.**

**Key structural fact the D19 design must respect.**
The toolbar's width enters the central widget's `minimumSizeHint` purely because the toolbar
is a direct `QVBoxLayout` child with no horizontal-shrink affordance. Wrapping it in a
horizontal `QScrollArea` removes that width from the central minimum without moving the
toolbar out of the central widget and without touching any control's construction or signal
wiring. **Validator probe (offscreen, 2026-10-05):** `centralWidget().minimumSizeHint().width()`
1716 → **88**; with the toolbar visible, driving the watchlist to cap reaches
`floor(0.50 × chart_area)` (e.g. 622 at chart_area 1244) instead of pinning at 150; the right
region stays fully in-window with a positive width; `centralWidget().width()` shrinks with the
window (2400→2038, 1800→1438, 1200→838, 900→538) instead of staying at 1716.

### Tech Stack Decisions (D19 increment)

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged `[existing]`:** Python 3.11+, PyQt6 (`≥6.6`), pyqtgraph (`≥0.13`). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D19 is a layout fix only | A new toolbar framework / embedded web view (out of scope, no dependency allowed) |
| Dock width model | **Unchanged `[existing]`** `ui/dock_layout.py` — cap constants and `plan_dock_widths` are **not** touched | **B6** keeps the watchlist cap at `floor(0.50 × chart_area)`; D19 fixes only the toolbar pinning | Change the cap (explicitly **not** adopted, B6) |
| Test stack | **Unchanged `[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS | Repo standard (Q8/Q9); the regression guard is offscreen | Manual-only (rejected) |
| **Toolbar overflow mechanism** | **`[new/changed]`** wrap the existing toolbar `QWidget` in a **`QScrollArea`** (no frame, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`), inserted into the central `QVBoxLayout` **in place of the bare toolbar** | Standard Qt class, no new dependency; removes the toolbar's ~1716px width from the central widget's minimum while keeping it **inside the central widget** as one row (B5); the pure `QScrollArea` does the shrink/scroll with no per-control changes | (b) wrap to multiple rows, (c) compress/overflow `»` menu, (d) move to `QMainWindow.addToolBar` — **all explicitly not adopted (B5)**. Also: `QScrollArea` with `setWidgetResizable(True)` or a default always-on scrollbar — **passed over** (would let the toolbar reflow/grow or reserve a scrollbar lane and break the single-row height) |
| **Toolbar row height** | **`[new/changed]`** wrapper height fixed at **36px**; the horizontal scrollbar is **overlay/transient** (FI-D19-1) so it does not add height | `AC-D19.4` requires the laid-out toolbar height to stay `<= ~40px` (one row); a reserved scrollbar lane would add ~15px and break it | A normal (non-overlay) horizontal scrollbar lane (~51px total) — rejected |
| **`conn_badge` placement** | **`[existing]` behaviour retained:** `conn_badge` stays **inside the scroll region** and scrolls with the toolbar (FI-D19-2) | Keeps the toolbar a single uniform scrollable row; no split widget | Pin the badge outside the scroll region (splits the row / adds a second layout) — not adopted |
| **Toolbar identification for tests** | **`[new]`** give the toolbar and its scroll wrapper stable `objectName`s (e.g. `"MainToolbar"` / `"ToolbarScroll"`) | After wrapping, `centralWidget().layout().itemAt(0).widget()` is the **wrapper**, not the toolbar; the affected harnesses must locate by name (and stop hiding) | Continue keying on `itemAt(0)` — fragile and semantically wrong once wrapped |
| **Watchlist cap** | **Unchanged `[existing]`** `floor(0.50 × chart_area)` (B1/B6) | B6: the formula was never the problem; D19 fixes only the toolbar pinning | Raise the cap — **not adopted (B6)** |
| Persistence | **No change:** `[existing]` `QSettings watchlist/width` for the watchlist; no new key; right region still not persisted (A36) | D19 adds no user-visible state | Persist the toolbar scroll position — not requested |

### System Components (D19 increment)

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout` in `ui/main_window.py`
  (`:217–223`). Structurally unchanged; it now holds the scroll wrapper instead of the bare
  toolbar. Its `width()` remains `chart_area` for the D17/D18 maths.
- **`[new/changed]` toolbar scroll wrapper** — a `QScrollArea` created in
  `ui/main_window.py`, inserted into the central `QVBoxLayout` in the toolbar's slot. No frame,
  `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
  fixed height **36px**, stable `objectName` (`"ToolbarScroll"`). This is the whole D19
  mechanism.
- **`[existing]` toolbar `QWidget` and controls** (`ui/main_window.py:100–211`) — construction,
  fixed widths, signal wiring, and `conn_badge` are **unchanged**; the widget is reparented
  into the scroll wrapper (and gains `objectName` `"MainToolbar"`).
- **`[existing]` D17/D18 width model** — `ui/dock_layout.py`, `MainWindow._chart_area_width`,
  `MainWindow._apply_dock_widths`, the dock event filter, `resizeEvent`, and
  `changeEvent(WindowStateChange)`. **Unchanged.** D19 only lowers the central widget's
  minimum so this model can take effect in a toolbar-visible window.
- **`[existing]` watchlist dock** and **`[existing]` single right dock region** — unchanged.
- **`[new/changed]` affected D17/D18 test harnesses** — `tests/test_dock_widths_d17.py`,
  `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`,
  `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`: remove the `toolbar.hide()`
  masking and exercise a **toolbar-visible** window, plus at least one D17 and one D18
  toolbar-visible regression guard (`AC-D19.6`).

### Data Model (D19 increment)

**No schema change. No new persisted state.**

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width` (int, px) —
  retained unchanged (B6 keeps the cap; the restore clamp is unchanged).
- `[new]` none. D19 adds only two in-memory `objectName` strings (toolbar, scroll wrapper) —
  ephemeral widget state, not a model.
- `[existing]` Right-region width/visibility is still not persisted (A36); no new key.
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

### Integration Points (D19 increment)

- **`[new]` `MainWindow` ↔ `QScrollArea`** — the one new wiring point: the toolbar is set as
  the scroll area's widget and the scroll area is added to the central `QVBoxLayout` in the
  toolbar's place. Uses only existing PyQt6 widgets; **no new external service, dependency, or
  IBKR call shape**.
- **`[existing]` Qt layout / dock geometry APIs** — `QMainWindow.setCentralWidget`,
  `QVBoxLayout`, `QMainWindow.resizeDocks`, `resizeEvent`, `changeEvent(WindowStateChange)`,
  `QSplitter`/event-filter fallback — unchanged.
- **`[existing]` D17/D18 clamp path** — `_chart_area_width()` → `_apply_dock_widths()` now
  reads a smaller central minimum; the code itself is unchanged. The B3 cross-clamp
  (`plan_dock_widths`) is unaffected.
- **`[existing]` `QSettings`** — unchanged.
- **`[existing]` test dock/toolbar lookups** — the five affected harnesses must resolve the
  toolbar/wrapper by `objectName` (or simply stop hiding it) rather than by
  `itemAt(0).widget()`.
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema, no
  dependency.

### Non-Functional Approach (D19 increment)

- **Correctness (central widget can shrink — `AC-D19.4`/`AC-D19.5`):** wrapping the toolbar in
  a horizontal `QScrollArea` removes its ~1716px width from
  `centralWidget().minimumSizeHint()`. Target: `centralWidget().minimumSizeHint().width() <=
  CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH` (= **750px**); the adopted
  in-memory probe measured **1716 → 88**, and the Validator independently reproduced it.
- **Correctness (single ~36px row — B5 / `AC-D19.4`):** the wrapper's height is fixed at 36px,
  the vertical scrollbar is always off, and the horizontal scrollbar is overlay/transient
  (FI-D19-1) so the laid-out toolbar height stays `<= ~40px`.
- **Correctness (controls stay reachable — B5 / `AC-D19.4`):** the toolbar keeps its full
  natural width inside the scroll content, so at a narrow window every control is reachable by
  horizontal scrolling; no control is removed, elided away permanently, or made unreachable.
- **Correctness (D17/D18 effective in a toolbar-visible window — `AC-D19.1`–`AC-D19.3`,
  `AC-D19.7`):** once the central widget can shrink, `_apply_dock_widths` (unchanged) can drive
  the watchlist to `floor(0.50 × chart_area)` and keep the right region on-screen with the
  chart `>= 400px`. The adopted probe measured the watchlist growing to **622px at chart_area
  1244** with the toolbar visible (pre-fix it was pinned/short of the cap).
- **Performance:** O(1) layout change; the scroll area adds no per-frame cost and no
  bar/table iteration. No change to the dock clamp's cost profile.
- **High-DPI / font scaling:** the toolbar's minimum hint may grow with font scaling, but the
  wrapper still lets the central widget shrink (R34). The single-row height is enforced by the
  fixed container height.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to live TWS
  or transmits an order. The ladder/order signals are unaffected.
- **Regression (`AC-D19.7`):** D1–D18 stay frozen; the affected D17/D18 harnesses are updated
  in lockstep (masking removed) rather than left contradicting D19.

### Architecture Risks (D19 increment)

| Risk | Severity | Mitigation |
|---|---|---|
| The overlay/transient horizontal scrollbar is not honoured on some platform/style, so the scrollbar lane shrinks the viewport and vertically clips the 36px toolbar row (`AC-D19.4` "one ~36px row" / reachability) | M | Fix the wrapper height at 36px and set vertical `ScrollBarAlwaysOff`; assert the laid-out height `<= ~40px` and the horizontal scroll range `> 0` in the toolbar-visible test (FI-D19-1). On the real macOS target overlay scrollbars are the default, so the row is not clipped; the offscreen platform reserves a lane (Validator probe measured an 18px lane at wrapper height 36), which is why R34 requires a real dev-build check in addition to the offscreen guard |
| A control becomes unreachable at the narrowest feasible width (B5's "no control permanently unreachable") | M | Keep the toolbar's full natural width inside the scroll content; assert the horizontal scroll range `> 0` and that all controls remain descendants of the scroll content at a narrow window (`AC-D19.4`) |
| Removing the `toolbar.hide()` masking makes the existing D17/D18 suite fail until the fix lands; the suite is not green in between | M (expected) | R33: the harness change is part of the fix; demonstrate the pre-fix red then green after (Phase 2 / `AC-D19.6`) |
| The offscreen toolbar minimum width differs from the real macOS window, so a scroll fix that only works offscreen could still fail in the real app (R34) | M | `AC-D19.6` requires a toolbar-visible window; also verify in the real dev build (`python main.py`) manually (R34) |
| The five affected harnesses locate the toolbar via `centralWidget().layout().itemAt(0).widget()`, which after the fix is the **wrapper**; a stale lookup could hide the wrong widget or silently no-op | M | Give the toolbar and wrapper stable `objectName`s; update the five harnesses in lockstep to locate by name (or simply stop hiding) |
| The wrapper accidentally changes the chart-area denominator or dock caps, breaking D17/D18 | M | Do not touch `ui/dock_layout.py`, `_chart_area_width`, or `_apply_dock_widths`; B6 keeps the cap constant; D17/D18 tests stay green in a toolbar-visible window |
| `conn_badge`/trailing stretch placement changes when wrapped (e.g. badge pinned outside) | L | Keep `conn_badge` inside the scroll region (FI-D19-2); assert the toolbar's control set is unchanged |
| Full-suite flakiness (shared on-disk test DB / collection-order SIGSEGV) is mistaken for a D19 regression | L | Per project memory, confirm any non-reproducible failure with a clean full-suite run before treating it as a regression |
| A D1–D18 behaviour regresses because the central widget is now smaller in existing tests | M | Full offscreen suite re-run (Phase 3, `AC-D19.7`); no D1–D18 production file is modified; `tests/test_d10_d13_integration.py` (which never hid the toolbar) was independently probe-checked to still hold |
