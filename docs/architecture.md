# Architecture — NDThinkChart Stabilization (as-built D1–D15 + ESC revision + post-document rework ESC-013…ESC-021, verified 2026-09-28, 383 passed; **increment D16 historical-bar gap backfill, validated 2026-10-02; ESC-023 trading-day calendar correction, validated 2026-10-02; increment D17 + D18 panel-layout / full-screen dock sizing, validated 2026-10-03; as-built D1–D18 at commit `5bd7c93` — 566 passed; increment D19 toolbar scroll/elide wrapper, validated 2026-10-05; increment D20 toolbar scrollbar lane, validated 2026-10-06 — as-built D1–D19 at commit `4d8952a`; increment D21 (Batch 15) UI repairs, validated 2026-10-06 — as-built D1–D20 at commit `04397d9`; **increment D22 in-app watchlist "Add symbol" / "Remove symbol" affordance, validated 2026-10-07 — as-built D1–D21 at commit `286341e`, 673 passed**) — commit baseline `286341e`; Phase 1 (D26) as-built update 2026-10-12 — merged to main at `5d4daf4` (review APPROVED), 779 passed; Phase 2 (D27) as-built update 2026-10-12 — branch `d27-correctness` at `69a2313` (re-review PASSED), 819 passed; Phase 3 (3a pacing off GUI thread + 3b TickerSession keystone + 3c pop-outs/D24.9 + 3d headless alarm monitor) as-built update 2026-10-12 — branch `phase3-sessions-popouts` at `ba28c08`, 855 passed, unmerged per R52 (Phase 4 perf gate owns the merge); Phase 4 (4a rolling 600s historical pacing + 4b D28.4 render split/study-cache/bisection/retention + 4c explicit teardown + 4d test hardening) as-built update 2026-10-13 — branch `phase4-pacing-perf-teardown` at `3d12821`, 898 passed, unmerged (the AC-D28.4 10-chart gate passes, clearing Phase 3's merge per R52); **D36 footprint charts as-built update 2026-10-13 — branch `feat/d36-footprint` at `89fe152`, 927 passed, Code Reviewer APPROVED, unmerged**`

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

---

## D20 increment — toolbar scrollbar lane (validated 2026-10-06)

> **Increment scope.** An *incremental* change on top of the **built, green D1–D19** system
> (commit `4d8952a`; the D19 toolbar scroll/elide wrapper is in place and green). D1–D19 are
> **frozen** and are **not** re-planned. This is an existing-repo run: the marker sentence and
> Current Tech Stack are preserved in `requirements.md`; **PyQt6 + pyqtgraph is a hard
> constraint**. No stack change, no schema change, no new dependency, no new external
> integration, and no live-order-path change. Items are labelled `[existing]`, `[new]`, or
> `[new/changed]`.

**Summary.** D20 is a **minimal, in-place height change** to the D19 wrapper. The toolbar
**content widget stays fixed at 36px**; the `ToolbarScroll` `QScrollArea`'s fixed height is
changed from the literal **36px** to the **derived strip height
`TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()`** (36px content row + the
horizontal scrollbar's own reserved lane). A `QScrollArea` lays its horizontal scrollbar out
**inside its own geometry** and shrinks the viewport above it; sizing the wrapper to
`content + extent` therefore gives the scrollbar a lane **entirely below** the content, so the
viewport always equals the 36px content row when the scrollbar is shown and no label glyph
(including descenders) can be clipped. When the content fits, the scrollbar is hidden and the
lane stays reserved but empty, so the strip height is **stable in both states** (B8). The
wrapper keeps `NoFrame`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical
`ScrollBarAlwaysOff`, and its `"ToolbarScroll"` objectName, so the toolbar's ~1716px width is
still held inside the scroll content and the **central widget's horizontal minimum is unchanged
from D19** (the D19 benefit is preserved). Nothing else changes: `ui/dock_layout.py`,
`_chart_area_width`, `_apply_dock_widths`, the watchlist cap, the single right-dock region, and
all D1–D19 behaviour are untouched.

**Validator probe (offscreen, 2026-10-06 — independently reproduced by the Plan Artifact
Editor & Validator, not taken from the proposal).** On the real `MainWindow`
(`QT_QPA_PLATFORM=offscreen`, `IBApiClient.connect` monkeypatched):

| Wrapper height | `horizontalScrollBar().sizeHint().height()` | `viewport().height()` (shown) | `viewport().height()` (hidden) | `mapTo(wrapper, QPoint(0,0)).y()` (shown) | `centralWidget().minimumSizeHint().width()` |
|---|---|---|---|---|---|
| 36 (as-built D19) | 18 | **18** | 36 | 18 | 88 |
| 52 (literal-52 variant — **not adopted**) | 18 | **34** | 52 | 34 | 88 |
| **54 (`36 + extent`, adopted)** | 18 | **36** | 54 | **36** | **88** |

The offscreen horizontal scrollbar extent is **18px**, not the ~16px the literal-52 arithmetic
assumed, so a 52px wrapper leaves a 34px viewport — 2px short of the 36px content row — and
`viewport().height() >= toolbar.height()` is false; the literal-52 variant is therefore **not
used** (RC-D20-1). The requirement's `~50–52px` is the **macOS** figure (extent ~16px → 52px);
the offscreen derived strip is 54px. `geometry()` is unusable for the lane assertion (offscreen
it reports `QRect(0, 0, …, 18)`, `top == 0`); the **mapped** form is used instead (RC-D20-2).

### Codebase Summary (existing repository — D20 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, refreshed
> 2026-10-06) and then **validated against the current source files** (the repository is
> authoritative). The graph surfaced the D19 concept node *"Toolbar scroll/elide wrapper
> (ToolbarScroll QScrollArea)"* and its edges to `AC-D19.4` / `AC-D19.5` / `PA-D19-1` / the
> "Known Gotcha — toolbar QWidget minimumSizeHint pinning (D19)", plus the `ui/main_window.py`
> and `tests/test_toolbar_scroll_d19.py` symbols. Every claim below was confirmed by direct
> inspection of the current tree on 2026-10-06 (the graph node `QScrollArea (no frame,
> setWidgetResizable False, fixed 36px)` matches the source exactly) and re-confirmed by the
> Validator's offscreen probe.

**Toolbar construction — `[existing] ui/main_window.py:100–211`**
- `toolbar = QWidget()`; `toolbar.setObjectName("MainToolbar")`; `toolbar.setFixedHeight(36)`
  (`:100–102`); inline stylesheet `background: #101218; border-bottom: 1px solid #232938;`
  (`:103`).
- `tb_layout = QHBoxLayout(toolbar)`, margins `(8, 0, 8, 0)`, spacing `6` (`:104–106`).
- Fixed-width controls: `symbol_input` 120, `tf_combo` 90, `mode_combo` 110, `sound_btn` 56,
  `ext_hours_btn` 80, `tz_combo` 110, `draw_combo` 110, `draw_set_combo` 140,
  `draw_delete_btn` 38; plus variable-width buttons/labels (`Load Chart`, `Studies…`,
  `Alarms (0)`, `Alarm Mode`, `DOM`, `Sets…`, `Symbol:`, `TF:`, `Mode:`, `Draw:`, `|`).
- Layout ends with `tb_layout.addStretch()` then `conn_badge` (`QLabel("● Connecting")`,
  `:187–188`, `:210–212`). The toolbar's natural `minimumSizeHint().width()` is ≈ **1716px**.

**D19 toolbar scroll wrapper — `[existing] ui/main_window.py:223–234`**
- `toolbar_scroll = QScrollArea()`; `setObjectName("ToolbarScroll")`;
  `setFrameShape(QFrame.Shape.NoFrame)`; `setWidgetResizable(False)`;
  horizontal `ScrollBarAsNeeded`; vertical `ScrollBarAlwaysOff`;
  **`setFixedHeight(36)`** (`:233`); `toolbar_scroll.setWidget(toolbar)` (`:234`).
- **Consequence (the reported defect):** the `QScrollArea` is fixed at the **same 36px** as the
  content widget, and its horizontal scrollbar is laid out within that 36px, shrinking the
  viewport and clipping the bottom of the toolbar content (label descenders).

**Central-widget composition — `[existing] ui/main_window.py:236–242`**
- `central = QWidget()`; `vbox = QVBoxLayout(central)` (margins `0`, spacing `0`);
  `vbox.addWidget(toolbar_scroll)` (`:240`); `vbox.addWidget(self.chart_panel)` (`:241`);
  `self.setCentralWidget(central)` (`:242`).
- **Consequence:** the wrapper — not the bare toolbar — is `layout.itemAt(0).widget()`; the
  toolbar's ~1716px width lives inside the scroll content, so
  `centralWidget().minimumSizeHint().width()` is small (D19 probe: **1716 → 88**) and the
  central widget can shrink. The wrapper's **height** has no effect on that horizontal minimum
  (Validator probe: 88 at both wrapper 36 and wrapper 54).

**D17/D18 width model — `[existing]` (unchanged by D20)**
- `MainWindow._chart_area_width()` returns `centralWidget().width()` (fallback `self.width()`);
  `MainWindow._apply_dock_widths()` is the single apply entry point (dock event filter,
  `resizeEvent`, `changeEvent(WindowStateChange)`, deferred normalize, right-dock visibility).
- `ui/dock_layout.py` (`[existing]`, pure, Qt-free): `CHART_MIN_WIDTH = 400`,
  `WATCHLIST_MIN_WIDTH = 150`, `RIGHT_DOCK_MIN_WIDTH = 200`, `WATCHLIST_CAP_FRACTION = 0.50`,
  `RIGHT_DOCK_CAP_FRACTION = 0.40`; `watchlist_max_width`, `right_dock_max_width`,
  `plan_dock_widths` (B3 cross-clamp). **Not touched by D20.**

**Affected test — `[existing] tests/test_toolbar_scroll_d19.py`** (the **only** height-asserting
test in the suite — re-confirmed by a repo-wide sweep on 2026-10-06):
- `T53-T02` (`:106–158`) asserts `toolbar.height() <= 40` at both the narrow (`:130`) and wide
  (`:156`) sizes — this bounds the **content widget**, which D20 keeps at 36px.
- `T53-T04` (`:183–211`) asserts `wrapper.height() == 36` (`:199`) and
  `wrapper.minimumHeight() == 36 and wrapper.maximumHeight() == 36` (`:200`) — this bounds the
  **container**, which D20 raises to the derived `TOOLBAR_CONTENT_HEIGHT + scrollbar extent`
  (offscreen 54px) and therefore **must** be updated in lockstep (`AC-D20.6` / R36).
- `T53-T01` (`:72–101`) asserts `centralWidget().minimumSizeHint().width() <= 750` and that
  `layout.itemAt(0).widget()` is the `"ToolbarScroll"` `QScrollArea` — **unchanged** by D20.
- `T53-T03` (`:163–178`) asserts the central width tracks the window — **unchanged** by D20.

**D17/D18 harnesses — `[existing] tests/` (unchanged by D20)**
- `tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`,
  `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`
  locate the toolbar by the stable `"MainToolbar"` objectName and assert it is **visible** and
  that no `toolbar.hide()` / `itemAt(0)` masking remains. They assert **widths / visibility**,
  not heights, so D20's vertical change does not touch them (A40); only the chart's *height*
  shrinks by the reserved lane (~16px macOS / ~18px offscreen).

**Existing data models / tables — unchanged by D20**
`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`,
`UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. **No schema change.**

**Existing integrations in play — unchanged by D20**
IBKR historical/RT data, SQLite, the Qt signal bus, `QSettings("NDThinkChart","NDThinkChart")`
key `watchlist/width`, and `PyQt6.QtWidgets` layout/scroll-area APIs. **No new external
integration.**

**Key structural fact the D20 design must respect.**
A `QScrollArea` lays its horizontal scrollbar out **inside its own geometry** and shrinks the
viewport above it. The D19 overlap exists purely because the wrapper's height equals the
content widget's height (36px). Giving the wrapper a height of **content row + the scrollbar's
own extent** makes the scrollbar occupy a lane *below* the content in both states — the
scrollbar is never drawn over the content, and `setWidgetResizable(False)` keeps the toolbar at
its full natural width so the central widget's minimum width (the D19 benefit) is untouched.

### Tech Stack Decisions (D20 increment)

Existing constrained choices first, then the D20 additions/changes.

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged `[existing]`:** Python 3.11+, PyQt6 (`≥6.6`), pyqtgraph (`≥0.13`). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D20 is a layout-height fix only | A new toolbar/scroll framework or web view (out of scope; no new dependency allowed) |
| Dock width model | **Unchanged `[existing]`** `ui/dock_layout.py` — cap constants and `plan_dock_widths` are **not** touched | A40/B6: D20 is vertical-only and does not alter the horizontal dock model | Change a cap (explicitly not adopted) |
| Test stack | **Unchanged `[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS | Repo standard (Q8/Q9); the D20 legibility/lane checks are offscreen | Manual-only (rejected) |
| Toolbar overflow mechanism | **Unchanged `[existing]`** the D19 `QScrollArea` wrapper (`NoFrame`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`) | D20 does not change the mechanism; it only changes the wrapper's height | Replacing the wrapper — not adopted; D19/B5 settled it |
| **Toolbar content-row height** | **Unchanged `[existing]`** `toolbar.setFixedHeight(36)` (`ui/main_window.py:102`) | B7: the **content row does not grow**; `AC-D20.2` requires the content widget to stay ~36px | (b) grow the content row to ~44–48px — **explicitly rejected by B7** |
| **Scrollbar-lane height / wrapper height** | **`[new/changed]`** raise `toolbar_scroll.setFixedHeight(36)` → **`TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()`** (`ui/main_window.py:233`) — the **36px content row + the horizontal scrollbar's own reserved lane**, derived at construction time; keep `setWidgetResizable(False)`. Named constant `TOOLBAR_CONTENT_HEIGHT = 36`; the strip height is a derived value (`36 + extent`), so code and test share one source of truth | The `QScrollArea` lays its horizontal scrollbar inside its own geometry; sizing the wrapper to `content + scrollbar extent` gives the scrollbar a lane **entirely below** the content, so the viewport always equals the content row when the scrollbar is shown and no glyph can be clipped (`AC-D20.1`–`AC-D20.3`). **Measured offscreen (2026-10-06): `sizeHint().height()` = 18px → strip 54px, viewport 36px; the requirement's `~50–52px` is the macOS figure (extent ~16px → 52px).** One-line change; no new widget | **Literal 52px fixed height** — **not adopted (RC-D20-1):** offscreen the scrollbar is 18px, so a 52px wrapper leaves a 34px viewport — the lane still overlaps the content row's bottom 2px and `viewport().height() >= toolbar.height()` is false. **Explicit separate lane widget** below the scroll area — **passed over:** the scrollbar belongs to the `QScrollArea` and is laid out inside it, so a separate widget cannot move the scrollbar out of the scroll area; the scroll area would still have to be `36 + extent` (redundant widget + second layout). **`setWidgetResizable(True)`** — rejected (lets the toolbar reflow/resize, breaks the single row). **Always-visible scrollbar** — rejected (B8 option b). **Overlay / auto-hiding macOS-style scrollbar** — rejected (B8 option c; can still cover the labels). **User-named total height** — rejected (B7 option c) |
| **Scrollbar visibility** | **`[new/changed]`** keep horizontal `ScrollBarAsNeeded`; the **lane is reserved** regardless of visibility so the strip height stays the derived value (offscreen 54px; macOS ~52px) in both states | B8: show the scrollbar only on overflow, never overlapping the labels; reserving the lane keeps the strip height stable (`AC-D20.3`) | Always-visible (B8 b) / overlay (B8 c) — **not adopted** |
| **Wrapper background (cosmetic, optional)** | **`[new]`** optionally style the `ToolbarScroll` background to match the toolbar strip (`#101218`) so the empty reserved lane is not a differently-coloured band | Keeps the reserved lane visually seamless; not required by any AC (D20's requirement is legibility + no overlap) | Leave the default palette background (a visible band below the toolbar) — acceptable but less coherent |
| Persistence | **No change:** `[existing]` `QSettings watchlist/width`; no new key | D20 adds no user-visible persisted state | Persist the toolbar scroll position — not requested |

### System Components (D20 increment)

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout` in `ui/main_window.py`
  (`:236–242`). Structurally unchanged; it holds the (now taller) scroll wrapper above the
  chart. Its `width()` remains `chart_area` for the D17/D18 maths; only its height loses the
  reserved lane (~16px macOS / ~18px offscreen).
- **`[new/changed]` toolbar scroll wrapper** — the D19 `ToolbarScroll` `QScrollArea` created in
  `ui/main_window.py` (`:223–234`). **Changed:** fixed height `36 → TOOLBAR_CONTENT_HEIGHT +
  horizontalScrollBar().sizeHint().height()` (the 36px content row + the scrollbar's own
  reserved lane; measured **54px offscreen**, **~52px on macOS**). **Unchanged:** `NoFrame`,
  `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical
  `ScrollBarAlwaysOff`, `objectName "ToolbarScroll"`, the toolbar as its widget. This is the
  whole D20 mechanism.
- **`[existing]` toolbar `QWidget` and controls** (`ui/main_window.py:100–211`) — construction,
  fixed widths, `setFixedHeight(36)`, stylesheet, signal wiring, and `conn_badge` are
  **unchanged**; the widget stays the scroll area's content at its full natural width.
- **`[existing]` D17/D18 width model** — `ui/dock_layout.py`, `MainWindow._chart_area_width`,
  `MainWindow._apply_dock_widths`, the dock event filter, `resizeEvent`,
  `changeEvent(WindowStateChange)`. **Unchanged.** D20's height change does not affect the
  horizontal minimum or the clamp.
- **`[existing]` watchlist dock** and **`[existing]` single right dock region** — unchanged.
- **`[new/changed]` D19 test module + D20 assertions** — `tests/test_toolbar_scroll_d19.py`:
  `T53-T04`'s container-height assertions (`height() == 36`, `min/max == 36`) are updated in
  lockstep to the **derived relation** (`height() == toolbar.height() +
  horizontalScrollBar().sizeHint().height()`; `min/max == height()`), with the content row
  asserted at `TOOLBAR_CONTENT_HEIGHT` (36px); D20 adds the label-legibility / reserved-lane /
  as-needed assertions (`AC-D20.1`–`AC-D20.5`).

### Data Model (D20 increment)

**No schema change. No new persisted state.**

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width` (int, px) —
  retained unchanged.
- `[new]` none. D20 adds only in-memory widget geometry (the wrapper's fixed height) and a
  named height constant — ephemeral view state, not a model.
- `[existing]` Right-region width/visibility is still not persisted (A36); no new key.
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

### Integration Points (D20 increment)

- **`[new]` none.** D20 adds no external service, dependency, IBKR call shape, or signal.
- **`[existing]` Qt layout / scroll-area APIs** — `QScrollArea.setFixedHeight`, the scroll
  area's own horizontal scrollbar extent (`horizontalScrollBar().sizeHint().height()`) and
  **mapped** position (`horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y()` — offscreen
  `geometry()` reports `top == 0`, so `geometry()` must **not** be used for the lane
  assertion), `QVBoxLayout`, `QMainWindow.setCentralWidget` — the only APIs involved.
- **`[existing]` D17/D18 clamp path** — `_chart_area_width()` → `_apply_dock_widths()`
  unchanged; the central widget's **width** is unchanged by D20.
- **`[existing]` `QSettings`** — unchanged.
- **`[existing]` test toolbar/wrapper lookups** — the D19 `"MainToolbar"` / `"ToolbarScroll"`
  objectNames are retained; the D17/D18 harnesses need no change.
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema, no
  dependency.

### Non-Functional Approach (D20 increment)

- **Correctness (labels not clipped — `AC-D20.1`):** the wrapper is sized to the content row
  plus the horizontal scrollbar's own extent, so the scrollbar is laid out **entirely below**
  the content and the viewport equals the content row (`>= 36px`) when the scrollbar is shown;
  no label glyph (including descenders) intersects the scrollbar's lane. Measured offscreen:
  strip 54px, viewport 36px, scrollbar mapped to y = 36 (`>= toolbar.height()`). Verify in
  **both** states (scrollbar shown and hidden).
- **Correctness (height supersession — `AC-D20.2`):** container height is the **derived**
  `content row + scrollbar extent` (offscreen **54px**, macOS **~52px** — the requirement's
  `~50–52px` figure); content widget height `TOOLBAR_CONTENT_HEIGHT` = **36px** (unchanged from
  D19); the reserved lane (equal to the scrollbar's extent) is present **entirely below** the
  content; the strip stays `< 60px` (R35). `AC-D19.4`'s `<= ~40px` bound is explicitly
  superseded, not silently contradicted.
- **Correctness (as-needed in a reserved lane — `AC-D20.3`):** horizontal `ScrollBarAsNeeded`
  retained; at a wide width `horizontalScrollBar().isVisible()` is `False` while the strip
  height is **unchanged** (still the derived height — offscreen 54px); at a narrow width it is
  `True` and its **mapped** lane sits below the content row.
- **Correctness (D19 behaviour preserved — `AC-D20.4`, `AC-D20.5`):** the toolbar keeps its
  full natural width inside the scroll content, so at a narrow window every control stays
  reachable via horizontal scrolling (scroll range `> 0`; Validator probe: `maximum() = 966` at
  the narrow size); the content stays a **single row** and inside the central widget. The
  central-widget minimum-width benefit (D19 probe 1716 → 88) is unchanged — D20 changes only
  the wrapper's **height**.
- **Correctness (D17/D18 unaffected — `AC-D20.6`, A40):** only vertical space changes (~16px
  macOS / ~18px offscreen shorter chart); the horizontal dock model, caps, and clamp are
  untouched; the D17/D18 criteria hold in a toolbar-visible window.
- **Performance:** O(1) layout change; no per-frame cost, no bar/table iteration, no change to
  the dock clamp's cost profile.
- **High-DPI / font scaling:** the reserved lane is a real reserved space (not an overlay), so
  labels stay unclipped as fonts grow. The lane is **not** a fixed ~16px constant: the strip
  height is derived from `horizontalScrollBar().sizeHint().height()` (`content + extent`), so a
  taller scrollbar on a high-DPI/font-scaled platform automatically widens the lane and the
  viewport still equals the content row when the scrollbar is shown.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to live TWS
  or transmits an order.
- **Regression (`AC-D20.6`):** D1–D19 stay frozen; the D19 height assertions are updated in
  lockstep rather than left contradicting D20 (R36).

### Architecture Risks (D20 increment)

| Risk | Severity | Mitigation |
|---|---|---|
| A platform's horizontal scrollbar extent exceeds a fixed reserved lane, so the viewport is < 36px when shown and clips the content | L | **Mitigated by the chosen mechanism:** the strip height is derived from `horizontalScrollBar().sizeHint().height()` (`content + extent`), so the lane always equals the scrollbar's own extent and the viewport equals the content row when shown; the test asserts `viewport().height() >= toolbar.height()` and the **mapped** lane position (`AC-D20.1` edge case) |
| The D19 height assertions (`T53-T04` `height() == 36`, `min/max == 36`) are left stale, leaving the suite red / contradictory (R36) | M (H impact) | Update them in lockstep to the **derived relation** (`height() == toolbar.height() + horizontalScrollBar().sizeHint().height()`; `min/max == height()`) with the content row asserted at 36px (`AC-D20.6`); the supersession is recorded explicitly on `AC-D19.4` |
| The reserved lane is visible as a differently-coloured band below the toolbar when the scrollbar is hidden | L | Optional: style the `ToolbarScroll` background to match the strip (`#101218`); not required by any AC, and the B7/B8 reserved lane is the accepted outcome |
| The offscreen scrollbar extent (18px) differs from the real macOS window (~16px), so an offscreen-only check misses a real clip (R34-style) | L | The chosen derivation uses the **actual** `sizeHint().height()`, so the strip adapts per platform (54px offscreen, ~52px macOS); the assertions test the viewport/content relation (not a literal height); record a manual `python main.py` check with the scrollbar both hidden and shown |
| The +extent wrapper height shrinks the chart and a D17/D18 assertion is height-sensitive | L | The D17/D18 harnesses assert widths/visibility only; re-run the full offscreen suite (Phase 3) and confirm no horizontal-model change |
| A D1–D19 behaviour regresses because the central widget is a scrollbar-lane shorter | L | No D1–D19 production file other than the D19 wrapper height is modified; full offscreen suite re-run (`AC-D20.6`) |
| Full-suite flakiness (shared on-disk test DB / collection-order SIGSEGV) is mistaken for a D20 regression | L | Per project memory, confirm any non-reproducible failure with a clean full-suite run before treating it as a regression |

---

## D21 increment — Batch 15: 13 UI defects/issues (validated 2026-10-06)

> **Increment scope.** An *incremental* change on top of the **built, green D1–D20** system
> (commit `04397d9`, 585 tests). D1–D20 are **frozen** and are **not** re-planned. This is an
> existing-repo run: `requirements.md` contains the marker sentence
> `This is an existing repository.` and a Current Tech Stack; **PyQt6 + pyqtgraph is a hard
> constraint**. No stack change, no schema change, no new dependency, no new external integration,
> and no live-order-path change. Items are labelled `[existing]`, `[new]`, or `[new/changed]`.

**Summary.** D21 is a batch of 13 UI repairs to an already-built PyQt6/pyqtgraph terminal. The
approach is **additive and targeted**: the volume pane gets a hard `yMin=0` limit, a zoom-driven
`1.10 × max-visible` ceiling, and a larger height cap with a price-pane minimum; the toolbar gains a
single shared `VIS-D21.2` active-highlight mechanism (a Qt dynamic property + one stylesheet) and the
Ext-Hours/RTH label swap; a small reusable `DiagonalStrikeButton` (`VIS-D21.1`) is introduced and
consumed by the watchlist, volume, and right-dock toggles; the watchlist gains a field-identity
column model persisted in `QSettings` and a single header toggle; the right dock gains per-panel
hide/show with in-height and horizontal collapse; the alarm dialog gains a row Edit dialog and the
smart-setup preview line + condition default; and the x-axis gains a pure, gap-aware
**time-collapse map** that removes only between-session non-trading time on intraday timeframes
(`1 day` no-op), superseding the display part of `AC-D16.3`. **No stack change, no new dependency,
no schema change, and the live-order path is untouched.**

**Validator probe (2026-10-06 — independently reproduced by the Plan Artifact Editor & Validator,
not taken from the proposal).** The coverage-adjusted collapse predicate was re-measured on the real
`services.market_calendar.session_windows` helper with `bar_period = TIMEFRAME_SECONDS["5 mins"] =
300`. A gap between consecutive bars `a < b` is collapsed **iff**
`session_windows(a + bar_period, b, ext_hours)` is empty:

| Boundary case (5-min bars) | `session_windows(a+300, b, ext)` | Verdict | Raw `session_windows(a, b, ext)` |
|---|---|---|---|
| RTH overnight `Fri 15:55 → Mon 09:30` (`ext=False`) | empty | **collapse** | non-empty → would wrongly keep |
| Ext overnight `Fri 19:55 → Mon 04:00` (`ext=True`) | empty | **collapse** | non-empty → would wrongly keep |
| Weekend `Sat 16:00 → Mon 09:30` | empty | **collapse** | empty |
| Holiday `Fri 15:55 → Tue 09:30` (Labor Day Mon) | empty | **collapse** | non-empty → would wrongly keep |
| Within-session hole `11:00 → 13:00` | non-empty | **keep** | non-empty |
| Missing full session `Mon close → Wed open` (Tue absent) | non-empty | **keep** | non-empty |
| Partial half-day afternoon hole `11:00 → 13:30` | non-empty | **keep** | non-empty |
| Adjacent bars `11:00 → 11:05` | empty | collapse (no-op) | non-empty |

This confirms `RC-D21-1` (the previous `CHANGES_REQUIRED`) is resolved: the coverage-adjusted
predicate collapses every ordinary between-session gap (which the un-adjusted `session_windows(a, b)`
predicate would have wrongly kept, because the last bar's own session window overlaps the gap start)
while preserving within-session holes and missing trading sessions (`AC-D21.4.1`–`AC-D21.4.4`).

### Codebase Summary (existing repository — D21 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2416 nodes, refreshed
> 2026-10-06) and then **validated against the current source files** (the repository is
> authoritative). The graph resolved the volume, watchlist, dock, toolbar, alarm and session
> symbols; every claim below was confirmed by direct source inspection on 2026-10-06.

**Volume pane / volume axis — `[existing] ui/chart_panel.py`**
- `ChartPanel.__init__` (`:185–344`) builds a **vertical `QSplitter`** holding `price_plot`,
  `volume_plot`, `osc_plot` (`:207`, `:317–321`), sized `setSizes([600, 120, 120])` (`:320`).
- `volume_plot = pg.PlotWidget()` with **`setMaximumHeight(120)`** (`:288`) — the D21.6 cap;
  `osc_plot` also `setMaximumHeight(120)` (`:309`); the price plot has **no minimum height**.
- The volume ViewBox is linear (`setLogMode('y', False)`, `:303`); right axis is `_VolumeAxisItem`
  (`:104–108`) with `_format_volume_tick` (`500.0K / 1.0M`, `:92–101`); `setXLink(price_plot)`
  (`:295`).
- Ceiling machinery: `_vol_max` cached running max (`:199`), `_volume_nice_max` (`:200`),
  `_recompute_vol_max` (`:876–883`, O(N) per load/new bar), `_ensure_volume_range` (`:885–896`,
  writes `setRange(yRange=(0, nice), padding=0)` **only-widen**), `_widen_volume_for`
  (`:898–906`, O(1) intra-bar), `_nice_volume_max` (`:68–89`, the D8 pinned family
  `1/1.5/2/2.5/5/7.5×10^k`, floor 100).
- **No mouse-y clamp exists** on the volume ViewBox, so the user can drag the volume Y below 0
  (D21.1). The ceiling is derived from the **whole** bar list and only widens, so zoom never lowers
  it (D21.2).
- Volume toggle `_volume_toggle = QPushButton("Volume")`, checkable, default checked
  (`:326–335`), positioned top-left of the volume pane (`_position_volume_toggle`, `:401–420`);
  `_on_volume_toggled` (`:422–436`) calls `volume_plot.setVisible`, axis visibility, splitter
  `refresh()`. The label/appearance does not change when unchecked (D21.12).

**Toolbar (inside the D19/D20 scroll wrapper) — `[existing] ui/main_window.py`**
- `toolbar` `QWidget` `setFixedHeight(TOOLBAR_CONTENT_HEIGHT=36)` (`:86`, `:106–108`); wrapped in a
  frameless `QScrollArea` `objectName "ToolbarScroll"`, `setWidgetResizable(False)`, horizontal
  `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, height
  `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` (`:232–246`), inserted into
  the central `QVBoxLayout` above `chart_panel` (`:248–254`).
- Buttons: `studies_btn` (`:135`, plain, opens a modal dialog), `alarms_btn` (`:138`, plain),
  `alarm_mode_btn` (`:141–143`, checkable), `sound_btn` (`:145–150`, checkable),
  `dom_btn` (`:153–157`, checkable), `ext_hours_btn = QPushButton("Ext Hours")` fixed width 80
  (`:160–165`, checkable, default checked). **No active/highlight styling** beyond Qt's default
  checked look (D21.7); `ext_hours_btn` text never changes (D21.3).
- `_on_ext_hours_toggled` (`:1443–1449`) reloads the chart; `_on_alarm_mode_toggled` (`:1030–1037`)
  shows `status_bar.showMessage("Alarm mode: click the chart to place a price alarm.", 4000)`
  — **4s timeout** (D21.8) — and relies on default checked styling.
- `_open_studies_dialog` (`:976`) and `_open_alarm_dialog` (`:980`) build a dialog and call
  `exec()`; no active state on the invoking button. `_open_alarm_dialog` pre-fills
  `AlarmDialog(symbol, self._last_chart_price, self)` (`:984`).

**Watchlist — `[existing] ui/watchlist_panel.py`, `[existing] ui/main_window.py`**
- `HEADERS = ["Symbol","Last","Bid","Ask","Chg","Chg %","Vol"]` with fixed `COL_*` indices
  (`:10–19`); `QTableWidget(0, 7)` (`:127–141`); tick handlers write cells by **hard-coded index**
  (`_set_cell`, `on_tick_price` `:206–239`, `on_tick_size` `:241–247`).
- Internal header strip `header_bar` with `QLabel("Watchlist")` (`:117–124`).
- The dock itself is `QDockWidget("Watchlist", self)` with a **second** "Watchlist" title bar
  (`ui/main_window.py:258`) — the duplicate D21.11 removes. Dock is `Movable|Floatable`
  (`:260–263`); width model D13/D17 (`dock_layout.py`) is unchanged.
- Persistence precedent: `QSettings("NDThinkChart","NDThinkChart")` key `watchlist/width` via
  `load_watchlist_width`/`save_watchlist_width` (`:58–72`, `main_window.py:271`, `:280–284`).
- `row_double_clicked` → `MainWindow._on_watchlist_row_double_clicked` → `load_chart` (D14, `:293`).

**Right dock (Active Trader + Portfolio) — `[existing] ui/main_window.py`, `[existing] ui/active_trader_panel.py`, `[existing] ui/active_portfolio_panel.py`**
- One `RightDockWidgetArea` region: `right_dock = QDockWidget("Active Trader")` with
  `setObjectName("Active Trader")` (`:313–314`), containing `right_dock_container` (a `QWidget`
  with a `QVBoxLayout` holding `ActiveTraderPanel` then `ActivePortfolioPanel`, `:305–311`).
- `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH=200)` (`:323`); in-memory `_right_dock_width`
  (`:327`); `visibilityChanged → _on_right_dock_visibility_changed` (`:335–337`, `:1290`).
- `ActivePortfolioPanel.summary_label = QLabel("Account summary — disconnected")` (`:68`) is the
  first widget of the portfolio panel (the "Account Summary" label that becomes a toggle in D21.13).
- `_on_dom_toggled` (`:1462–1471`) hides/shows the **whole** region via
  `findChild(QDockWidget, "Active Trader")`.
- Dock width model: `[existing] ui/dock_layout.py` (pure, Qt-free) — `plan_dock_widths`,
  `watchlist_max_width`, `right_dock_max_width`, `CHART_MIN_WIDTH=400`, `RIGHT_DOCK_MIN_WIDTH=200`;
  `MainWindow._apply_dock_widths` (`:1132–1199`) is the single apply entry point (uses
  `_right_dock_available()` `:1071–1084` to fall back to the watchlist-only rule when the region is
  hidden; the hidden branch at `:1189–1194` resizes **only** the watchlist dock via
  `_resize_docks_guarded` `:1201–1224`).

**Alarms — `[existing] ui/alarm_dialog.py`, `[existing] ui/alarm_overlay.py`, `[existing] data/alarm_store.py`, `[existing] ui/main_window.py`**
- `AlarmDialog` (`:28–163`): `QTableWidget(0, 6)` columns
  `["Price","Condition","Active","Triggered","Sound","Note"]` (`:40–47`); an entry row with
  `price_input` (`QDoubleSpinBox`), `condition_input` (`QComboBox` of
  `Cross Above/Cross Below/Cross Either` → `cross_above/cross_below/cross_either`), `sound_input`,
  `note_input`, and Add/Rearm/Mute/Delete/Close buttons (`:49–89`). **No per-row Edit button** and
  no edit dialog (D21.9). `_reload`/`_append_row` rebuild rows (`:94–118`).
- `AlarmOverlay` (`:34–226`): renders each alarm as an `InfiniteLine` (price-only) + `TextItem`
  label at `_label_x() = max(bar_count-1, 0)`; emits `create_requested(price)` on a left click in
  alarm mode (`:148–162`); supports drag/right-click menu. **No preview line** (D21.10).
- `AlarmStore` (`data/alarm_store.py`) already exposes `load/add/update/set_price/set_sound/
  rearm/delete/mark_triggered`; `update(alarm_id, **fields)` (`:63–79`) edits
  `price/direction/active/triggered/triggered_at/sound/note` **atomically** — the D21.9 edit path
  needs **no new store method** (it deliberately leaves `active/triggered/triggered_at` untouched).
- `MainWindow._on_alarm_create_requested(price)` (`:1502–1509`) unchecks alarm mode, opens the
  modal `AlarmDialog(symbol, price)` (price prefilled), `exec()`, then reloads. `_reload_current_alarms`
  updates `alarms_btn` text and `chart_panel.set_alarms`.

**Sessions / x-axis / non-trading time — `[existing] services/session_service.py`, `[existing] ui/overlays/session_overlay.py`, `[existing] services/market_calendar.py`, `[existing] ui/chart_panel.py`**
- `session_bands(bars, timeframe)` (`session_service.py:33–86`) returns ET pre `04:00–09:30` and
  post `16:00–20:00` intervals clipped to the bar range; `[]` for `1 day`. Pure, Qt-free, DST-aware.
- `SessionOverlay.render(bands)` draws one `pg.LinearRegionItem(values=(start_ts, end_ts))` per
  band at `Z=-10` (`session_overlay.py:13–34`).
- `market_calendar.py` (D16) is the pure ET trading-day/holiday calendar (`is_trading_day`,
  `trading_days`, `session_windows(start_ts, end_ts, ext_hours)` — `:195–216`, 04:00–20:00 ET when
  `ext_hours` else 09:30–16:00, one clipped window per trading day; `clipped_end > clipped_start`
  excludes empty windows).
- The chart x-axis is **linear wall-clock time**: `_custom_date_axis(utc, tz_offset)` (`chart_panel.py:24`)
  wraps `pg.DateAxisItem`; `_refresh_candles` plots bars at `bar.ts` (`:802–874`); the ViewBox
  x-range is `(t0-2*bar_w, t1+8*bar_w)` (`:827`). So overnight/weekend/holiday spans render as
  empty horizontal space (D21.4).
- `_render_sessions` (`:722–734`) calls `session_bands(self._bars, tf)` then
  `_session_overlay.render(bands)`.
- `DrawingOverlay` anchors time-anchored drawings to bar timestamps (`self._bar_ts`, `:80`, `:110`,
  `:345`, `:816`) and maps scene↔view for drag (`:205`, `:491`, `:643`). Alarm lines are
  price-only; the alarm label x uses the bar count.
- **Bar timestamps are period starts** — `data/bar_aggregator.py`: `TIMEFRAME_SECONDS`
  (`:6–14`), `_period_start(ts, seconds) = (ts // seconds) * seconds` (`:30–32`), and
  `Bar.ts = self._state.period_start` (`:93`). A 5-min RTH session therefore ends with a bar at
  **15:55** (extended hours **19:55**), while the session window closes at **16:00** (ext **20:00**).
  This is the fact the D21.4 collapse predicate must account for.

**Data models / tables — `[existing]`**
`Bar {symbol, timeframe, ts, open, high, low, close, volume}`; SQLite tables `bars`
(PK `(symbol,timeframe,ts)`), `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. `Alarm` model
(`data/models.py:17`) carries `id, symbol, price, direction, active, triggered, triggered_at,
sound, note, created_at`. **No D21 change requires a schema change.**

**Integrations in play — `[existing]`**
IBKR historical/RT data via `ibkr/market_data.py` + `ibkr/client.py` + `ibkr/bridge.py` (Qt
signals `historical_bar`/`historical_data_end`/`error_msg`/market-data ticks); SQLite via
`data/db.py`; `QSettings` (watchlist width); Qt signal/slot bus; pyqtgraph `GraphicsScene`.

**Relevant existing tests (the D21 surface)**
`tests/test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`,
`test_volume_toggle.py`, `test_volume_width.py` (volume axis/toggle);
`tests/test_watchlist.py`, `test_watchlist_d14_midrag.py` (watchlist);
`tests/test_alarm_interaction.py`, `test_alarm_overlay.py`, `test_alarm_store.py` (alarms);
`tests/test_dock_layout.py`, `test_dock_widths_d17.py`, `test_dock_widths_d18.py`,
`test_dock_widths_d18_impl.py`, `test_dock_d18_region.py` (dock model);
`tests/test_session_service.py`, `test_session_overlay.py` (session bands);
`tests/test_toolbar_scroll_d19.py`, `test_toolbar_d20.py` (toolbar wrapper);
`tests/test_history_backfill.py`, `test_backfill_service.py`, `test_market_calendar.py` (D16).
**Note:** `test_volume_linear.py`/`test_volume_log.py`/`test_volume_ceiling.py` assert the D8
**nice-max** ceiling and the ESC-007 **only-widen** rule, both of which **D21.2 supersedes** — they
must be updated in lockstep.

### Tech Stack Decisions (D21 increment)

Constrained (existing) choices first, then the D21 additions.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+, PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Stabilization run; changing the stack is a stated Non-Goal | New charting library / embedded web view — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` live port 7496 only; numpy; SQLite (`config/paths.get_db_path()`); PyInstaller `.app`; pytest + pytest-qt offscreen | Existing-repo hard constraint; live-order path gated at TWS | Paper mode / new broker / new DB — rejected |
| S3 | **Volume Y lower clamp (D21.1)** `[new]` | `volume_plot.getViewBox().setLimits(yMin=0)` | pyqtgraph enforces `yMin` in `_checkBounds` on **interactive** drag/zoom, so the min never goes below 0 without a custom event handler; programmatic `setRange(yRange=(0, …))` stays inside the limit | Override `ViewBox.mouseDragEvent`/`wheelEvent` to clamp (more code, easy to miss a path); a custom ViewBox subclass (heavier) |
| S4 | **Volume ceiling formula (D21.2)** `[new/changed]` | `ceiling = 1.10 × max(volume of bars whose x lies in the visible x-range)`; `0` visible → D8 floor `100`; recompute on **every visible-x-range change** (and on bar updates). Supersedes D8's nice-max ceiling and ESC-007's only-widen-for-zoom | Requirement is explicit (`AC-D21.2.1`); recomputing both directions is what fixes "bars squashed on zoom" | Keep the D8 nice max (does not follow the visible max); keep only-widen (the reported defect); nice-round the `1.10×` value (violates the literal measurable) |
| S5 | **Volume ceiling trigger** `[new]` | Connect `price_plot.getViewBox().sigXRangeChanged` → `_recompute_visible_volume_range()` (O(N) numpy scan over bar x), coalesced by a 0-ms `QTimer` if needed | `sigXRangeChanged` fires for zoom, pan and the magnifier area-zoom (which sets the x-range); the price ViewBox is the x master (`volume_plot.setXLink`) | Poll `viewRange()` on a timer (laggy); per-overlay hooks (misses pan) |
| S6 | **Volume pane height (D21.6)** `[new]` | `volume_plot.setMaximumHeight(VOLUME_PANE_MAX_HEIGHT)` with `VOLUME_PANE_MAX_HEIGHT = 480` (≥ 360 headroom) and `price_plot.setMinimumHeight(PRICE_PANE_MIN_HEIGHT = 200)`; splitter stays vertical, `osc_plot` cap unchanged | `AC-D21.6.1` requires the volume pane to reach **≥360px** while the price pane keeps **~200px**; a 480 cap gives margin so 360 is always reachable; the price minimum bounds the squeeze (R39) | Cap exactly 360 (no headroom; may fail to reach if the splitter distributes unevenly); remove the cap entirely (price pane can be starved) |
| S7 | **Shared active highlight (D21.7/D21.8)** `[new]` | One stylesheet on the toolbar (`#MainToolbar QPushButton:checked {…}` for checkable toggles, `#MainToolbar QPushButton[active="true"] {…}` for popup buttons) + a helper `set_button_active(btn, active)` that sets the Qt dynamic property and repolishes | `VIS-D21.2` requires one persistent, distinguishable highlight; a dynamic property + a single stylesheet is consistent, testable (property + style), and independent of scroll position in the D19 wrapper | Per-button ad-hoc `setStyleSheet` (inconsistent, hard to clear); a custom button class per toggle (duplication) |
| S8 | **Shared diagonal strike-through (D21.11/D21.12/D21.13)** `[new]` | A small reusable `DiagonalStrikeButton(QPushButton)` (new `ui/visual_conventions.py`) overriding `paintEvent` to draw a top-left→bottom-right line over the text area when a `struck` flag is set (checkable buttons auto-strike when unchecked) | `VIS-D21.1` is one convention reused by three defects; Qt stylesheets cannot draw a diagonal line, so a painted line is the reliable primitive; cosmetic pen keeps it device-pixel stable | A `QStyledItemDelegate`/`border-image` (stylesheets do not support diagonals); a separate overlay `QWidget` line (fragile, geometry-dependent) |
| S9 | **Watchlist column model (D21.5)** `[new/changed]` | A `COLUMN_DEFS` list of `(field_key, header_label)` over the existing 7 fields; an ordered `active_field_keys` list; cells created per active field; tick handlers address cells by **field key** (index resolved through the layout); `Symbol` cannot be removed; a right-click header popup (checkable add/remove + move left/right) rebuilds the table | `AC-D21.5.1`–`AC-D21.5.4` (B10): reorder/remove must not corrupt values (`DG32`); the existing 7 fields are the whole addable set | Keep index-based writes (corrupts on reorder — the DG32 failure mode); introduce new data fields (explicitly not adopted, B10) |
| S10 | **Watchlist column persistence (D21.5)** `[new]` | `QSettings("NDThinkChart","NDThinkChart")` key `watchlist/columns` (ordered, comma-joined field keys), restored on launch and sanitised (drop unknown keys, force `symbol` present) | Matches the existing D13 width persistence (`watchlist/width`); avoids a SQLite migration, consistent with the repo's "no schema change" norm | A `watchlist_columns` SQLite table (migration cost, no benefit); per-symbol layouts (not requested) |
| S11 | **Watchlist single header toggle (D21.11)** `[new/changed]` | The in-panel header strip becomes the dock's **title-bar widget** (`watchlist_dock.setTitleBarWidget(header_strip)`) and its label becomes a `DiagonalStrikeButton("Watchlist")`; "hide" collapses the panel **body** (table) while the header/title bar stays visible; Qt forwards mouse events from a custom title-bar widget to the dock, preserving drag/float | `AC-D21.11.1`–`AC-D21.11.3` (B12): exactly one "Watchlist" label, kept as the toggle, **visible when collapsed**, duplicate dock title deleted (`DG37`); a title-bar widget keeps the dock movable without a bespoke drag handle | `setTitleBarWidget(QWidget())` blank + an in-panel header (loses the drag affordance, `DG37`); hide the whole dock (the button would disappear — violates `AC-D21.11.2`) |
| S12 | **Right-dock panel toggles + collapse (D21.13)** `[new/changed]` | "Active Trader" = a `DiagonalStrikeButton` placed as the right dock's **title-bar widget**; "Account Summary" = the portfolio's `summary_label` replaced by a `DiagonalStrikeButton`. Hiding a panel hides its **body** and keeps its button; one hidden → the other expands (layout stretch). **Both hidden → horizontal collapse, driven explicitly:** `MainWindow` enters a *collapsed* state in which it (a) **relaxes the right dock's minimum width** (`right_dock.setMinimumWidth(RIGHT_DOCK_COLLAPSED_MIN_WIDTH)`, computed from the two buttons' `sizeHint()` + margins, replacing the pinned `RIGHT_DOCK_MIN_WIDTH = 200` at `ui/main_window.py:323`) and (b) **explicitly resizes the dock to the button strip** (`_resize_docks_guarded([right_dock], [collapsed_width])`), because the hidden branch of `_apply_dock_widths` only resizes the watchlist and cannot shrink the right dock. `_apply_dock_widths` **additionally treats the collapsed region as hidden for the cross-clamp** (so the watchlist regains its own cap and the chart minimum holds). **Showing either panel restores `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)` and re-applies the normal B3 cross-clamp.** | `AC-D21.13.1`–`AC-D21.13.4` (B12) and `DG35`/`DG38`: in-height collapse with a surviving button, horizontal collapse to the button strip when both are hidden, and the D17/D18 chart-minimum rule preserved. The pinned 200px minimum (`:323`) is why the collapse must relax the minimum and resize the dock explicitly — outcome-only wording is unreachable | Hide the whole region (that is the DOM button's job; loses per-panel control); a fixed narrow width without cross-clamp integration (breaks R41); rely on `_apply_dock_widths`' hidden branch alone (it never shrinks the right dock — the pinned minimum keeps it at ≥200) |
| S13 | **Alarm row edit (D21.9)** `[new]` | A per-row `Edit` `QPushButton` cell at the row's right end (Note column stretched up to it); clicking opens a small modal `AlarmEditDialog` (price/condition/sound/note + Save/Cancel) that calls the **existing** `AlarmStore.update(id, price=…, direction=…, sound=…, note=…)` on Save | `AC-D21.9.1`–`AC-D21.9.4` (B13); `AlarmStore.update` already exists and edits only the four fields, leaving `active`/`triggered`/`triggered_at` untouched, so a triggered alarm **keeps its state** (R42) | Reuse the inline entry row (cannot target a row); add a new store method (unnecessary) |
| S14 | **Smart-alarm preview line (D21.10)** `[new]` | A dedicated yellow dashed `pg.InfiniteLine` owned by `ChartPanel` (or the alarm overlay), created **only on the chart-click path** (`_on_alarm_create_requested`) — **not** on the Alarms-button path (`_open_alarm_dialog`) — and **removed on popup close**; connected to the dialog's `price_input.valueChanged` so it follows live; after Add the real `AlarmOverlay` line replaces it | `AC-D21.10.2`–`AC-D21.10.4` (B13); the preview line is required only "Given the alarm popup is open **from a chart click**", and the D21.10 edge case gives the Alarms-button popup **no** preview line (it uses the last chart price). A dedicated item with an explicit add/remove lifecycle tied to that path cannot leak onto the chart (R43) | Reuse an `AlarmOverlay` line (would be re-rendered by `set_data` and could leak); add the line on every popup open (wrong for the Alarms-button path — violates the D21.10 edge case) |
| S15 | **Smart-alarm condition default (D21.10)** `[new]` | On popup open only: `Cross Below` if `last_price > alarm_price`, `Cross Above` if `last_price < alarm_price` or `last_price is None`; user-overridable | `AC-D21.10.5` (B13), including the unknown-current-price case | Recompute on every spinbox change (contradicts "only on open") |
| S16 | **Time-collapse mechanism (D21.4)** `[new]` | A new pure, Qt-free `services/time_collapse_service.py` building a **piecewise-linear display-x map** from bar ts: a gap between consecutive bars `a < b` is collapsed **iff** `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty — i.e. no session window overlaps the gap **after accounting for bar coverage**. A bar at `ts` covers `[ts, ts + bar_period)`; bar timestamps are period **starts** (`data/bar_aggregator.py:30–32,93`), so the last RTH bar is at **15:55** and the last ext-hours bar at **19:55**, whose coverage ends exactly at the **16:00 / 20:00** session close. Testing the raw interval `[a, b]` would let the closing session's window overlap the ordinary overnight/weekend/holiday gap and wrongly keep it; testing `[a + bar_period, b]` removes the last bar's own period from the tested interval, so the ordinary between-session gap collapses while a within-session hole or a missing trading session (session time strictly between `a + bar_period` and `b`) is kept. `bar_period` is read from the existing `data/bar_aggregator.TIMEFRAME_SECONDS` map (single source of truth). `1 day` → identity. The chart plots at display-x and a `CollapsedDateAxis` maps display-x → ts for labels | `AC-D21.4.1`–`AC-D21.4.4` (B9): collapse only **between-session** non-trading time on intraday timeframes, preserve within-session spacing, keep trading-session holes visible (`AC-D16.4`), `1 day` no-op. A pure map is unit-testable and keeps `Bar.ts` (the SQLite key) untouched. Verified by the Validator's probe (see the increment header) | Pure index-based x (collapses within-session holes too — violates the "partial/half-day missing afternoon is not collapsed" edge case and D16 no-silent-hole); mutate `Bar.ts` (corrupts persistence/drawings/backfill); a per-timeframe axis hack (no hole awareness); the un-coverage-adjusted `session_windows(a, b)` predicate (fails the ordinary overnight/weekend/holiday case — reproduced by the Validator's probe) |
| S17 | **Collapse consumers** `[new/changed]` | `ChartPanel` stores the map and uses display-x for candles/volume/x-range; `SessionOverlay` bands, time-anchored drawings (`DrawingOverlay._bar_ts`) and the alarm label x are mapped through it; the date axis and crosshair time tag inverse-map to ts | `AC-D21.4.1` edge cases require drawings/bands/alarms to land on the correct bars (`DG31`, R37) | Leave drawings/bands in wall-clock ts (they would misalign after collapse) |
| S18 | Testing `[existing]` | pytest + pytest-qt, offscreen, no live TWS; each fix ships a pre-fix-red/post-fix-green check | Repo standard (Q8/Q9) | Manual-only — rejected |

**No new dependency is introduced by D21.**

### System Components (D21 increment)

**Existing components touched (unchanged responsibilities):**
- `[existing] ui/main_window.py` — toolbar construction, Ext-Hours/Alarm-Mode slots, watchlist dock,
  single right dock region, `_apply_dock_widths` / `_chart_area_width` / `_right_dock_available`,
  alarm-dialog and DOM slots.
- `[existing] ui/chart_panel.py` — price/volume/oscillator splitter, volume ViewBox + ceiling,
  volume toggle, x-axis, `_refresh_candles`, `_render_sessions`.
- `[existing] ui/watchlist_panel.py` — table, header strip, tick handlers, D14 double-click.
- `[existing] ui/alarm_dialog.py`, `[existing] ui/alarm_overlay.py`, `[existing] data/alarm_store.py`.
- `[existing] ui/active_trader_panel.py`, `[existing] ui/active_portfolio_panel.py`.
- `[existing] ui/dock_layout.py` (pure width model), `[existing] services/session_service.py`,
  `[existing] ui/overlays/session_overlay.py`, `[existing] services/market_calendar.py`,
  `[existing] ui/drawing_overlay.py`.

**New components:**
- `[new] ui/visual_conventions.py` — the shared `VIS-D21` primitives: `DiagonalStrikeButton`
  (`VIS-D21.1`), the `VIS-D21.2` toolbar stylesheet string/constant, and `set_button_active(button,
  active)`. Consumed by D21.7/D21.8 (toolbar), D21.11 (watchlist), D21.12 (volume), D21.13 (right
  dock).
- `[new] ui/alarm_edit_dialog.py` — the small modal `AlarmEditDialog` (price/condition/sound/note,
  Save/Cancel) used by D21.9. (May instead live inside `alarm_dialog.py`; the module split is a
  Build detail — either way it is `[new]`.)
- `[new] services/time_collapse_service.py` — the pure, Qt-free collapse map for D21.4:
  `build_collapse_map(bars, timeframe, ext_hours) -> TimeCollapseMap` with
  `to_display(ts)`, `to_ts(x)`, `x_values`, `is_identity`; and
  `gap_is_non_trading(a, b, ext_hours, bar_period) -> bool` returning True (collapse) iff
  `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty.
  `bar_period` is `TIMEFRAME_SECONDS[timeframe]`.

**Changed components:**
- `[new/changed] ui/chart_panel.py` — volume ViewBox `setLimits(yMin=0)` (D21.1); visible-max
  ceiling + `sigXRangeChanged` hook (D21.2); `VOLUME_PANE_MAX_HEIGHT`/`PRICE_PANE_MIN_HEIGHT`
  (D21.6); `_volume_toggle` → `DiagonalStrikeButton` (D21.12); preview-line add/remove + price-follow
  (D21.10, chart-click path only); display-x plotting + `CollapsedDateAxis` + map storage (D21.4).
- `[new/changed] ui/main_window.py` — Ext-Hours/RTH label (D21.3); active-highlight wiring for
  `studies_btn`/`alarms_btn` and `:checked` styling for the toggles (D21.7); persistent Alarm-Mode
  status message (D21.8); watchlist dock title-bar widget + toggle wiring (D21.11); right-dock
  title-bar toggle + per-panel hide/show + the **collapsed-state minimum-width relaxation and
  explicit dock resize** (D21.13); alarm edit wiring (D21.9) and preview-line creation **only on the
  `_on_alarm_create_requested` chart-click path** (D21.10).
- `[new/changed] ui/watchlist_panel.py` — field-identity column model, header context popup,
  `QSettings watchlist/columns`, `DiagonalStrikeButton` header toggle (D21.5/D21.11).
- `[new/changed] ui/alarm_dialog.py` — per-row Edit button + stretched Note column; condition
  default on open; preview-line signal (D21.9/D21.10).
- `[new/changed] ui/alarm_overlay.py` — expose the preview-line add/remove lifecycle if the item is
  owned there (D21.10); label x uses the display-x of the last bar (D21.4).
- `[new/changed] ui/active_trader_panel.py`, `[new/changed] ui/active_portfolio_panel.py` —
  `summary_label` → `DiagonalStrikeButton`; body-hide support (D21.13).
- `[new/changed] ui/overlays/session_overlay.py` — accept display-x band values (D21.4).
- `[new/changed] ui/drawing_overlay.py` — map ts anchors ↔ display-x for time-anchored drawings
  (D21.4).
- `[new/changed] services/session_service.py` — may gain a helper to expose session windows for the
  collapse rule; the existing `session_bands` contract is otherwise unchanged (D21.4).

**Component relationships (D21):** `MainWindow` remains the orchestrator: it owns the toolbar
(inside the D19/D20 wrapper), the watchlist dock, the single right dock region, and the
Ext-Hours/Alarm-Mode/DOM state. `ChartPanel` owns the price/volume/oscillator splitter, the volume
ViewBox (now `yMin=0` + the visible-max ceiling), the volume strike toggle, the x-axis and the
collapse map, and the alarm preview line. `WatchlistPanel` owns the column model and the header
strike toggle. `AlarmDialog`/`AlarmEditDialog` write through the existing `AlarmStore`;
`AlarmOverlay` renders the result. `visual_conventions` is a leaf module consumed by the toolbar,
watchlist, volume, and right-dock components. `dock_layout` + `_apply_dock_widths` remain the single
width-clamp entry point and gain a "right region collapsed" input.

### Data Model (D21 increment)

- `[existing]` `Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`,
  `OrderBookLevel`, `UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`,
  `drawings`, `studies`, `positions`, `trade_groups`, `position_group_map` — **unchanged**.
- `[existing]` `alarms` row via `AlarmStore.update` — D21.9 edits `price/direction/sound/note` and
  deliberately leaves `active/triggered/triggered_at` untouched (state preserved).
- `[new]` **Watchlist column layout** — persisted as a single `QSettings` string key
  `watchlist/columns` (ordered field keys from the fixed 7). Not a SQLite table; no migration.
- `[new]` **Time-collapse map** — an in-memory value object (`TimeCollapseMap`) on `ChartPanel`;
  ephemeral, rebuilt per load/ext-hours change; `Bar.ts` (the persisted key) is never mutated.
- `[new]` **D21 view state** — `DiagonalStrikeButton.struck`, per-panel visibility flags
  (Active Trader / Account Summary), the alarm preview line, and the volume ceiling/height
  constants are ephemeral view state (no persistence), consistent with D10's volume-visibility
  precedent.

### Integration Points (D21 increment)

- `[existing]` **IBKR historical/RT data** — no new call type, no signature change, no new request
  shape. D21.4 is a **display** change only; the D16 backfill/no-silent-hole path is untouched.
- `[existing]` **SQLite (`AlarmStore`)** — D21.9 uses the existing `update()`; no schema change.
- `[existing]` **QSettings** — D21.5 adds the `watchlist/columns` key alongside `watchlist/width`.
- `[existing]` **Qt signal bus** — D21.2 adds a `sigXRangeChanged` connection on the price ViewBox;
  D21.10 connects the alarm dialog's `price_input.valueChanged` to the preview line; D21.7/D21.13
  use `toggled`/`clicked` as today. No new bus.
- `[existing]` **pyqtgraph GraphicsScene** — the D21.10 preview line is a normal scene item
  (add/remove); no fork.
- **No new external service, dependency, or persisted table is introduced.**

### Non-Functional Approach (D21 increment)

- **Correctness — volume axis (D21.1/D21.2).** The lower bound is enforced structurally by
  `setLimits(yMin=0)` (pyqtgraph `_checkBounds` on every interactive range change), so
  `viewRange()[1][0] >= 0` holds after any drag/zoom; the ceiling is `1.10 × max visible` computed
  from the visible x-range, with the D8 `[0, 100]` floor when no visible bar has positive volume.
  D8's linear scale, no-negatives, min-0 and price-coloured bars are preserved; the D8 **nice-max**
  ceiling and the ESC-007 **only-widen-for-zoom** rule are superseded (recorded), while ESC-007's
  core intent (a growing forming bar must not be clipped) is preserved by recomputing on bar
  updates too.
- **Performance (D21.2).** The visible-max recompute is an O(N) numpy scan over the bar x array per
  x-range change; a 0-ms `QTimer` coalesces bursts of pan events so at most one recompute runs per
  event-loop turn. The intra-bar path stays O(1) against the cached running max. N is the loaded bar
  count (thousands), so the scan is negligible.
- **Correctness — collapse (D21.4).** The map is a pure function, unit-testable without Qt; a gap
  between consecutive bars `a < b` is collapsed **iff** `session_windows(a + bar_period, b, ext_hours)`
  is empty. Because bar timestamps are period **starts** and a bar at `ts` covers `[ts, ts + bar_period)`,
  the tested interval starts at the **end of the last bar's coverage**, not at the bar's own timestamp —
  so the previous session's window (which closes exactly at `a + bar_period` for the last bar) no longer
  overlaps the ordinary overnight/weekend/holiday gap and that gap **is** collapsed. A genuine
  trading-session hole (session time strictly between `a + bar_period` and `b`) keeps its window and
  stays as empty space (D16 `AC-D16.1`/`AC-D16.4` unchanged); a within-session hole is likewise kept.
  `1 day` is identity. Drawings, session bands, alarm labels and the date axis all consume the same map
  so they stay aligned (R37). Verified by the Validator's probe (see the increment header).
- **Correctness — watchlist (D21.5).** Columns bind by field identity, not index, so a reorder or
  removal cannot misroute a tick (the `DG32` failure mode); `Symbol` is forced present; the layout
  is sanitised on restore; D14's double-click resolves the Symbol field by key.
- **Correctness — toggles (D21.7/D21.8/D21.11/D21.12/D21.13).** One highlight mechanism and one
  strike primitive keep the states consistent; the highlight is a property/stylesheet (scroll-
  independent); the strike is a painted cosmetic line (device-pixel stable); the right dock's
  collapsed state **relaxes the dock's minimum width and resizes it to the button strip** (so
  `AC-D21.13.3`'s horizontal collapse is reachable despite the pinned `RIGHT_DOCK_MIN_WIDTH = 200`)
  and **also** feeds `_apply_dock_widths` as hidden/collapsed for the cross-clamp, so the D17/D18
  chart-minimum rule still holds (R41).
- **Security.** The live-order path is untouched; Q9 holds — no automated test connects to live TWS
  or transmits an order.
- **High-DPI.** The `VIS-D21.1` strike uses a cosmetic pen (device-pixel width); the volume toggle
  and strike buttons inherit existing scaling.
- **Scalability.** No per-frame allocation added beyond the O(N) scan and the per-load map build;
  overlay/label counts remain bound to drawing/bar counts.

### Architecture Risks (D21 increment)

| Risk | Severity | Mitigation |
|---|---|---|
| D21.4 collapse is an x-axis model change: it supersedes `AC-D16.3`'s display rule and can affect session shading (D1), time-anchored drawings, alarm positioning and D7/D9 spacing (R37). A collapse predicate that ignores bar coverage would keep the ordinary overnight/weekend/holiday gap (the last bar's own session window overlaps the gap start) | **H** | Collapse only **between-session** gaps on intraday timeframes (`1 day` no-op); define the predicate on **bar coverage** — `session_windows(a + bar_period, b, ext_hours)` empty — so the last bar's own period is not mistaken for missing session time; keep D16 backfill/no-silent-hole unchanged; route drawings/bands/alarm labels/date axis through the same pure map; update the affected D16/D1 tests in lockstep; verify drawings/bands/alarms after collapse. Validator probe reproduced all five boundary cases (2026-10-06) |
| D21.2 supersedes D8's nice-max ceiling and ESC-007's only-widen rule; stale volume tests (`test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`) assert the old behaviour | **M** | Update those tests in lockstep (assert `≈ 1.10 × visible max`); keep `_nice_volume_max` as the all-zero-floor/fixture helper; record the supersession (already on `AC-D21.2.1`) |
| D21.5 column configuration can break D14 double-click binding or lose values after reorder (R38) | **M** | Bind by field identity (not index); force `Symbol` present; persist/sanitise via `QSettings`; test reorder-then-live-tick and double-click-after-reorder |
| D21.6 raising the volume cap can squeeze the price pane below a usable height on short windows (R39) | **M** | `price_plot.setMinimumHeight(200)` + a bounded `VOLUME_PANE_MAX_HEIGHT`; verify at the target height and at a short window; no regression to D10 |
| D21.13 collapsing the right dock can conflict with the D17/D18 width model and `_apply_dock_widths` (R41) | **M** | Relax `right_dock.setMinimumWidth(...)` to the button-strip minimum and explicitly resize the dock to that strip when both panels are hidden (the hidden branch of `_apply_dock_widths` only resizes the watchlist); treat the fully-collapsed region as hidden for the cross-clamp (as `visibilityChanged` does); restore the 200px minimum and the normal cross-clamp when a panel is shown; assert the chart minimum in collapsed and expanded states; reconcile with `_on_dom_toggled` |
| D21.9 editing a set/triggered alarm could silently re-arm or disable a live alarm (R42) | **M** | Edit via Save/Cancel; persist via `AlarmStore.update` (leaves `active/triggered/triggered_at`); re-render the overlay/badge; test editing a triggered alarm |
| D21.7/D21.8 highlight may be low-contrast or clipped in the D19 wrapper (R40) | **L** | High-contrast accent style (A41); verify in the dev build and offscreen; assert active vs inactive style differs |
| D21.10 preview line must coexist with the modal dialog and not leak after close (R43), and must appear **only** on the chart-click path | **L** | Dedicated item with an explicit add-on-open/remove-on-close lifecycle **tied to `_on_alarm_create_requested`** (the chart-click path); the Alarms-button path (`_open_alarm_dialog`) creates **no** preview line (D21.10 edge case); replace with the real alarm line after Add; test open/close on both paths and live price changes |
| Batch size (13 sub-defects) touching shared chart/toolbar/dock/alarm code — one fix can regress another (R44) | **M** | Keep every fix independently tested (pre-fix red / post-fix green); re-run the full offscreen suite per wave; treat D1–D20 criteria as frozen |
| `setLimits(yMin=0)` could interfere with programmatic volume range writes | **L** | Programmatic `setRange(yRange=(0, ceiling))` stays inside the limit (min == 0); assert `viewRange()` after load, zoom and drag in the D21.1 tests |
| Removing the watchlist dock title bar removes the drag/float affordance (DG37) | **L** | Use the in-panel header strip as the dock's title-bar widget so Qt forwards drag events; assert the dock stays movable and the button stays visible when the body is collapsed |
| The right dock title bar becomes the "Active Trader" toggle (DG38) | **L** | Custom title-bar widget containing the strike button; keep a drag region (Qt forwarding); reconcile with the DOM button; treat a fully-collapsed region as hidden for the cross-clamp |
| Existing offscreen suite intermittently reports spurious failures (shared test DB) — known gotcha | **L** | Confirm with clean full-suite runs; isolate DB per test where the repo already does |
| D21.4 + D21.2 interaction: the visible-max scan must use display-x after collapse | **M** | Phase 6 must reconcile the D21.2 scan with the collapse map (both read the visible x-range); assert the ceiling after collapse |

### Implementation sequencing (D21 increment)

Detailed phases, dependencies and `touches_files` notes are in `docs/plan.md`. At the architecture
level the sequence is: (1) volume axis/pane, (2) shared `VIS-D21` primitives + toolbar state,
(3) watchlist columns/header, (4) right-dock panel toggles/collapse, (5) alarm edit/smart setup,
(6) time collapse (the x-model change, sequenced last to minimise churn on the chart while keeping
the earlier volume work correct under the final x model). D1–D20 are frozen throughout.

---

## D22 increment — in-app watchlist "Add symbol" / "Remove symbol" affordance (validated 2026-10-07)

> **Increment scope.** An *incremental* change on top of the **built, green D1–D21** system
> (commit `286341e`, **673 tests**). D1–D21 are **frozen** and are **not** re-planned. This is an
> existing-repo run: `requirements.md` contains the marker sentence
> `This is an existing repository.` and a Current Tech Stack; **PyQt6 + pyqtgraph + official `ibapi`
> + SQLite is a hard constraint**. No stack change, no schema change, no new dependency, and **no
> live-order-path change**. Items are labelled `[existing]`, `[new]`, or `[new/changed]`.

**Summary.** D22 adds two watchlist affordances — an add (a `+` button and a right-click **"Add
symbol…"** on the watchlist header strip) and a remove (a right-click **"Remove symbol"** on a
watchlist row) — that write through the **existing** SQLite `watchlist` table and
subscribe/cancel live ticks through the **existing** `MarketDataManager`. The only genuinely new
infrastructure is the **IBKR `reqContractDetails` request/callback path** (`DG43`) required by
B16: it is added as typed `IBBridge` signals + `IBApiClient` overrides + a `MarketDataManager`
request/cancel pair, with a small `ContractLookupService` that correlates `reqId → pending add`
and resolves **exactly once** (success / error / bounded timeout). Everything is additive: the
existing stack, schema, dock geometry, column layout and D1–D21 behaviour are untouched, and an
explicitly-emptied watchlist stays empty across restarts.

**Validator verification (2026-10-07 — independently checked against the current source and the
repo's own suite, not taken from the proposal).** The baseline is green: `QT_QPA_PLATFORM=offscreen
.venv/bin/python -m pytest -o addopts="" -q` → **673 passed** at commit `286341e`. Every
Codebase-Summary claim below was confirmed by direct source inspection; a tree-wide grep for
`reqContractDetails` / `contractDetails` / `ContractDetails` across all `*.py` returns **0 hits**
(the `DG43` gap is real). `watchlist/configured`, `services/contract_lookup_service.py`,
`ui/add_symbol_dialog.py`, `add_symbol_dialog`, `contract_lookup` do **not** exist today.

### Codebase Summary (existing repository — D22 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2851 nodes, refreshed
> 2026-10-07) and then **validated against the current source files** (the repository is
> authoritative). The D22 surface is small and well-contained: the watchlist panel, its dock setup
> in `MainWindow`, two `DB` methods, the IBKR request/callback plumbing, and the connection
> lifecycle.

**Data models / schema**
- `[existing]` **SQLite `watchlist` table** — `data/db.py:23–27`:
  `watchlist(symbol TEXT PRIMARY KEY, category TEXT NOT NULL, sort_order INTEGER NOT NULL)`.
  There is **no** add/remove helper and **no** "configured"/seed flag column.
- `[existing]` `DB.get_watchlist() -> [(symbol, category)]` (`data/db.py:125–129`), ordered by
  `sort_order ASC`.
- `[existing]` `DB.set_watchlist(symbols, category="EQUITIES", sort_order=None)`
  (`data/db.py:131–150`) — **replaces the whole list** (`DELETE` then `INSERT OR REPLACE`); pass a
  numeric-index `sort_order` (stored as strings, coerced by the column's INTEGER affinity) when
  none is passed. It is the only writer today.
- `[existing]` Module-level singleton `db = DB()` (`data/db.py:154`) created at import;
  `config/paths.get_db_path()` resolves to
  `~/Library/Application Support/NDThinkChart/charting_app.sqlite3` (overridable via `DB_PATH`).
- `[existing]` **No** `reqContractDetails` / `contractDetails` / `contractDetailsEnd` anywhere in
  the repo (grep across the whole tree → 0 hits). This is the `DG43` gap.

**Major components and responsibilities**
- `[existing]` **`ui/watchlist_panel.py::WatchlistPanel`** (585 lines)
  - Header strip: `self.header_bar` (28px `QWidget`, `:254–257`), holding the single
    `self.header_button = DiagonalStrikeButton("Watchlist")` (`:261` — the D21.11 collapse
    toggle) and an `addStretch()` (`:279`). `MainWindow` promotes this strip to the dock's
    **title-bar widget** (`ui/main_window.py:303`), so it stays visible when the body collapses.
  - `self.table` (`QTableWidget`, `:283–295`); `self.body = self.table` (`:298`) is what the
    toggle hides.
  - Column model + D21.5 column menu: `COLUMN_DEFS`/`ALL_FIELDS`/`SYMBOL_FIELD` (`:54–71`),
    `_active_fields` (`:229`), `_build_header_menu` (`:396`), `_on_header_context_menu`
    (`:422`) wired to the **table's horizontal header** only
    (`header.customContextMenuRequested.connect(...)`, `:301–303`). The table body itself has
    **no** context menu today.
  - Live subscriptions: `add_symbol(symbol, contract)` (`:481–497`) — early-returns when
    `_md_manager` is `None`, else inserts a row, renders cells, calls
    `self._md_manager.req_mkt_data(contract)`, and records `_req_to_row[req_id] = row`.
    It does **not** persist and returns nothing. **There is no `remove_symbol`.**
  - `clear()` (`:499–511`) cancels every tracked `reqId` (`cancel_mkt_data`), clears
    `_req_to_row`/`_prev_close`/`_last_price`/`_row_data`/flash timers, and empties the table.
  - Row state: `_req_to_row: dict[int,int]` (`:230`), `_row_data: dict[int, dict]` (`:236`),
    `_prev_close`/`_last_price` (`:231–232`), `set_market_data_manager` (`:469`).
  - D14 double-click: `row_double_clicked` signal (`:222`), `_on_cell_double_clicked`
    (`:456–463`) resolves the Symbol cell **by field key**.
  - Width persistence (D13/D17): `watchlist/width` QSettings key (`:93`); column-layout
    persistence (D21.5): `watchlist/columns` (`:74`).
- `[existing]` **`ui/main_window.py`** (2113 lines)
  - `DEFAULT_WATCHLIST = ["AAPL","TSLA","SPY","QQQ","NVDA"]` (`:81`).
  - Watchlist dock construction (`:291–337`): `WatchlistPanel()`, dock `objectName
    "Watchlist"`, empty window title, `setWidget`, `setTitleBarWidget(header_bar)`
    (`:298–303`), `setMinimumWidth(WATCHLIST_MIN_WIDTH)` (`:308`); D17 live-width clamp
    plumbing (`:310–335`); `row_double_clicked → _on_watchlist_row_double_clicked` (`:337`).
  - `self._settings = QSettings("NDThinkChart","NDThinkChart")` (`:315`) — already the
    persistence store for `watchlist/width` and `watchlist/columns`.
  - IBKR wiring (`:411–467`): `self.ib_client = IBApiClient()` (`:412`),
    `self.md_manager = MarketDataManager(self.ib_client)` (`:413`), `depth_manager`
    (`:415`), `sub_manager` (`:416`); injected into the panel (`:419–420`); bridge signals
    connected (`:456–473`).
  - Connection lifecycle: `_on_connected` (`:523–529`) sets the badge/`load_btn` and calls
    `_restore_watchlist()`; `_restore_watchlist` (`:531–538`) reads `db.get_watchlist()`,
    seeds `DEFAULT_WATCHLIST` via `db.set_watchlist(...)` **only when the DB list is empty**,
    then calls `watchlist_panel.add_symbol(sym, get_contract_for_symbol(sym))` per symbol.
    `_on_disconnected` (`:550–562`) disables `load_btn` and finalises a stranded history wave;
    it does **not** clear the watchlist panel. `watchlist_panel.clear()` is called from
    **`closeEvent`** (`:2107`), not from the disconnect slot.
  - The toolbar `symbol_input` + `Load Chart` (`load_chart`) load a chart but never touch the
    watchlist.
- `[existing]` **`ibkr/client.py::IBApiClient(EWrapper, EClient)`** (223 lines) — `error()`
  (`:114–141`) forwards to `bridge.error_msg` for non-`info` severities (`:139–141`);
  callbacks `historicalData`/`historicalDataEnd`/`tickPrice`/`tickSize`/`realtimeBar`/
  `updateMktDepth(L2)`/`accountSummary(End)`/`position(End)`/`orderStatus`/`openOrder`/
  `execDetails` (`:160–223`), each forwarding to an `IBBridge` signal. **No contract-details
  callbacks.** Connection state via `ConnectionState` (`:10–14`) and `_set_state` (`:40–48`).
- `[existing]` **`ibkr/bridge.py::IBBridge(QObject)`** (39 lines) — the typed signal surface
  (`connected`, `disconnected`, `error_msg`, `historical_bar`, `historical_data_end`,
  `tick_price`, `tick_size`, `realtime_bar`, `update_mkt_depth`, account/order signals).
  Emitted from the EClient reader thread; consumed on the Qt main thread via queued
  connections (the existing pattern for `historical_bar` etc.).
- `[existing]` **`ibkr/market_data.py::MarketDataManager`** (77 lines) — `req_historical_data`
  (`:20`), `req_mkt_data` (`:56–61`, `id_manager.get_id()` + `pacing_manager.throttle()` +
  `client.reqMktData`), `cancel_mkt_data` (`:63`), `cancel_historical_data` (`:71`).
- `[existing]` **`ibkr/contracts.py`** (191 lines) — `get_stock_contract` (`:130`),
  `get_futures_contract` (`:139`), `get_contract_for_symbol` (`:169–191`): auto-detects
  stock vs the small `FUTURES_SCHEDULE` set and builds a fully-qualified front-month
  FUT contract for futures, else a `STK/SMART/USD` contract. **No IBKR lookup; never raises for
  an unknown symbol** (`DG39`).
- `[existing]` **`ibkr/id_manager.py`** — `id_manager.get_id()` (`:13`) (thread-safe reqId
  allocator). **`ibkr/pacing.py`** — `pacing_manager.throttle()` (`:14`).
  **`ibkr/error_codes.py`** — `classify_error` (`:1–15`); **error 200 is `fatal`** (`:12`),
  so a "no security definition" reply reaches `bridge.error_msg` with its `reqId`.
- `[existing]` **`ui/visual_conventions.py`** — `VIS_D21_2_STYLESHEET` / `set_button_active`
  (`:80–92`) and `DiagonalStrikeButton` (`:109`). Reusable for consistent affordance styling.
- `[existing]` **`services/`** — pure/services layer (`market_calendar.py`,
  `backfill_service.py`, `session_service.py`, `time_collapse_service.py`,
  `drawing_service.py`, `sound_service.py`, …). A new sibling service fits the established
  layout.

**Existing integrations already in use**
- `[existing]` **IBKR via `ibapi`** — `reqMktData`/`cancelMktData` (watchlist ticks),
  `reqHistoricalData`/`cancelHistoricalData` (chart + D16 backfill), `reqMktDepth` (DOM),
  realtime bars, account/position/order callbacks. Live port `7496` only.
- `[existing]` **SQLite** via `data/db.py` (singleton `db`).
- `[existing]` **QSettings** `("NDThinkChart","NDThinkChart")` — `watchlist/width`,
  `watchlist/columns`.
- `[existing]` **Qt signal bus** (`IBBridge`) + `pyqtgraph` chart scene.

**Verified facts that shape the design (and one requirements-doc imprecision)**
1. `WatchlistPanel.add_symbol` neither persists nor returns the new row/reqId; `_req_to_row`
   is the **only** reqId↔row index and is row-index-keyed, so a removal must re-index it.
2. The D21.5 column popup is bound to the **table's horizontal header**, while the D21.11
   toggle lives on the **panel header strip**. A new header-strip `+`/context menu and a
   **table-body** row context menu therefore cannot shadow the column popup (`DG42`).
3. `watchlist_panel.clear()` runs in **`closeEvent`**, not in `_on_disconnected`; and
   `_restore_watchlist()` runs on **every** `_on_connected` (initial + every poll reconnect).
   Today a transport drop leaves stale rows and a reconnect would append duplicates. This is a
   pre-existing quirk; D22 must make the persisted set authoritative (`AC-D22.7`), so the plan
   makes `_restore_watchlist` clear-then-repopulate (see S13 / PA-D22-6). *(The requirements
   prose at `requirements.md:2121`/`DG40` says `clear()` is "called on disconnect"; the repo
   shows it is called on close at `:2107`. Informational — no `AC-D22.*` outcome depends on it;
   recorded in `docs/plan_notes.md` and `docs/plan_review.md`.)*
4. Error `200` is classified `fatal` (`error_codes.py:12`) and `error()` forwards it to
   `bridge.error_msg` with the originating `reqId` (`client.py:139–141`), so a
   contract-details rejection is already observable through the existing signal.
5. Test surface (verified): `tests/test_watchlist_columns_d21.py` provides `FakeMdManager`
   (`:47`) and `_isolated_settings` (`:63`); `tests/test_right_dock_d21.py::_boot` (`:40`)
   monkeypatches `IBApiClient.connect` so no TWS is touched. **No existing test calls
   `_restore_watchlist` or `_on_connected`** (grep), so the clear-then-repopulate change has no
   existing watchlist test to regress; `tests/test_history_backfill_disconnect.py` calls
   `_on_disconnected` (`:172`, `:203`, `:241`, `:271`, `:375`, `:457`, `:510`) — the added
   `cancel_all()` / `set_add_enabled(False)` calls there must not raise or change the D16
   assertions.
6. QSettings isolation: `MainWindow._settings` is the real
   `QSettings("NDThinkChart","NDThinkChart")` and is **not injectable**; the existing D17/D18
   tests clean the relevant keys via a local `_clean_settings()` helper. The new
   `watchlist/configured` sentinel must be isolated/cleared by the D22 tests the same way, or
   the suite becomes order-dependent (see risk row AR-D22-9). This is the same class as the
   recorded "shared test DB" gotcha in `docs/memory.md`.

### Tech Stack Decisions (D22 increment)

Constrained (existing) choices first, then the D22 additions. **No new dependency.**

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+, PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Existing-repo hard constraint; the Current Tech Stack is a Non-Goal to change | New charting/UI framework — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` live port `7496` only; numpy; SQLite via `config/paths.get_db_path()`; PyInstaller `.app`; pytest + pytest-qt offscreen (no live TWS) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB — rejected |
| S3 | **Live symbol validation (B16 / `DG43`)** `[new]` | Add a **contract-details request path**: `[new]` `IBBridge.contract_details(reqId, object)` + `contract_details_end(reqId)` signals; `[new]` `IBApiClient.contractDetails` / `contractDetailsEnd` overrides forwarding to them (mirroring the existing callback pattern); `[new]` `MarketDataManager.req_contract_details(contract) -> int` and `cancel_contract_details(req_id)` using `id_manager.get_id()` + `pacing_manager.throttle()` + `client.reqContractDetails` | `reqContractDetails` is the only reliable live check that a symbol resolves to a real instrument (`DG39`); routing it through the existing client→bridge→Qt-signal pattern keeps threading consistent (emitted on the reader thread, delivered queued on the main thread) and reuses `id_manager`/`pacing_manager` | Validate by subscribing with `reqMktData` and waiting for a tick (no deterministic "invalid" outcome; silent hangs); `reqSecDefOptParams` / `reqMatchingSymbols` (wrong tool / extra surface); a blocking `reqContractDetails` on a worker thread (adds a thread + cross-thread DB/UI calls) |
| S4 | **Async correlation + bounded wait (B16)** `[new]` | A `[new]` `services/contract_lookup_service.py::ContractLookupService(QObject)` owns the pending map: `request(symbol, contract) -> request_id` records `{reqId: PendingLookup(symbol, got_any=False)}`, arms a single-shot `QTimer(CONTRACT_LOOKUP_TIMEOUT_MS = 5000)` per request, and resolves **exactly once** via a `lookup_finished(request_id, symbol, ok, reason)` signal — success on `contract_details` (≥1) followed by `contract_details_end`; failure on `contract_details_end` with zero details, on `error_msg` for a pending reqId, or on timeout. Late/unknown events are ignored; the timer is disarmed on every resolution | `AC-D22.4` fixes the observable outcome and requires a **bounded** wait ("no indefinite hang", R46); a reqId-keyed pending map is the repo's established correlation idiom (the D16 history wave correlates the same way). A `QObject` on the main thread receives bridge signals queued, so all state mutation and the DB/UI side effects stay on the main thread | Await in `MainWindow` directly (grows the already-2113-line window and its test harness); `QEventLoop`/blocking wait inside the modal dialog (freezes the UI, violates "no hang"); a global "last error" without reqId correlation (races with unrelated errors such as market-data failures) |
| S5 | **Persistence mechanism for add/remove (`DG41`/R47)** `[new]` | Two explicit, atomic helpers on `[existing] data/db.py` — `add_watchlist_symbol(symbol, category="EQUITIES") -> None` (`INSERT OR IGNORE` with `sort_order = COALESCE(MAX(sort_order), -1) + 1`) and `remove_watchlist_symbol(symbol) -> None` (`DELETE ... WHERE symbol = ? COLLATE NOCASE`, then renumber the remaining rows `0..n-1`). Keep `get_watchlist`/`set_watchlist` unchanged | The requirement fixes the **outcome** (`AC-D22.6`/`AC-D22.7`) and makes the mechanism Plan's call; per-operation helpers are additive, remove the risk that a caller reconstructs the list from the panel's **transient rows** (`DG40`), preserve each row's `category`, and keep `sort_order` contiguous so a later `set_watchlist` stays consistent. Case-insensitive delete matches the A50 case-insensitive duplicate rule | Reuse the replace-all `set_watchlist` with the full desired list (forces the caller to re-derive the persisted list, defaults every `category` to `EQUITIES`, and is exactly the `DG40`/R47 footgun); a new SQLite table (migration — against the repo norm); raw SQL inline in `MainWindow` (untestable, no single owner) |
| S6 | **Seed-if-empty guard (A52/`DG44`)** `[new]` | A persisted boolean sentinel in the **existing** QSettings store: key `watchlist/configured`. `_restore_watchlist` seeds `DEFAULT_WATCHLIST` **only when the DB list is empty AND the sentinel is unset**, then sets the sentinel; a non-empty DB list also sets it; add/remove set it. The sentinel holds **one bit of state, not the symbol list** (the SQLite `watchlist` table remains the sole symbol store) | D22's remove makes an explicitly-emptied list meaningful, but the current seed-if-empty branch would re-seed on the next connect (`DG44`/A52). A mutable persisted sentinel handles the **same-session reconnect** case too, stays within the existing QSettings usage, and needs no schema change | Seed whenever the list is empty (violates `AC-D22.7` + A52); a DB `meta`/flag table (schema migration); a sentinel symbol row filtered out of `get_watchlist` (pollutes every consumer); "DB file was created this run" alone (re-seeds on a same-session reconnect, because `_restore_watchlist` runs on every connect) |
| S7 | **Input surface (B15b)** `[new]` | A small modal `AddSymbolDialog(QDialog)` (new `ui/add_symbol_dialog.py`): one `QLineEdit`, OK/Cancel, `Esc` → `reject()`; the OK handler refuses to accept empty/whitespace input (inline message, dialog stays open). The add path uses a pure `normalise_symbol(text)` helper | B15b says "a small modal dialog (QInputDialog-style) with a text field + OK/Cancel"; a concrete `QDialog` subclass is straightforward to exercise offscreen (construct, `setText`, invoke the accept slot) whereas the `QInputDialog.getText` **static** blocks its own event loop and can only be tested by monkeypatching the static. OK/Cancel/Esc semantics are explicit | `QInputDialog.getText` (blocking static — brittle in pytest-qt; styling constrained); an inline editable row (explicitly not adopted, B15b) |
| S8 | **Remove affordance placement (B14)** `[new]` | A **row context menu** on the **table body** (`self.table.setContextMenuPolicy(CustomContextMenu)` → a menu with **"Remove symbol"**, acting on the row under the cursor). No per-row delete button | B14 fixes the outcome and leaves placement/styling to Plan/Build ("a per-row delete affordance and/or a right-click 'Remove symbol'"). A body context menu needs no extra column width (the D21.5 table already supports a variable column set) and cannot be confused with the header-strip add affordance | A per-row delete button column (competes for width with the D21.5 column layout, and "delete" cells would be index-fragile on reorder/removal); both (extra surface with no requirement gain) |
| S9 | **Panel ↔ window contract** `[new]` | `WatchlistPanel` emits `symbol_add_requested(str)` and `symbol_remove_requested(str)` and exposes `set_add_enabled(bool)` + `remove_symbol(symbol)`. `MainWindow` owns the dialog-free orchestration (DB, connection gate, validation, status messages) | Keeps the panel free of DB/connection knowledge (it has none today), keeps a single persistence owner (`MainWindow`), and makes both halves independently testable | The panel owns the DB/validation (duplicates knowledge across two windows and re-introduces the `DG40` transient-row pitfall) |
| S10 | **Connection gate (B16b)** `[new/changed]` | `MainWindow` tracks `self._ibkr_connected: bool` (False initially, True in `_on_connected`, False in `_on_disconnected`) and calls `watchlist_panel.set_add_enabled(...)`; the add slot also refuses with a status message if invoked while disconnected | `AC-D22.5` requires the add to be **denied** while disconnected, with the affordance reflecting it (disabled **and/or** the confirm refused); disabling both the `+` and the menu entry *and* refusing in the slot covers both readings and is directly assertable | Only disabling the button (a programmatic invocation would still add); only refusing with a message (the affordance would look enabled) |
| S11 | **Contract used for the lookup and the subscription** `[new/changed]` | Both the lookup request and (on success) the `req_mkt_data` subscription use the **existing** `get_contract_for_symbol(symbol)`; the resolved `ContractDetails.contract` is used only as the success evidence | Keeps the add path consistent with `_restore_watchlist`/`_replay_subscriptions` (which already use `get_contract_for_symbol`), avoids inventing a "which of N returned contracts" pick policy for tick subscription, and reuses the existing futures front-month logic; `AC-D22.4` needs only "at least one matching contract" as the success test | Subscribe with the first/primary `ContractDetails.contract` (extra decision + divergence from the restore path); require an exact single match (over-strict for multi-listing stocks) |
| S12 | **Normalisation + guards (A50)** `[new/changed]` | Pure helpers in `[new/changed] ui/watchlist_panel.py`: `normalise_symbol(text) -> str` (strip + upper) and `symbol_in_list(symbol, symbols) -> bool` (case-insensitive). The panel rejects empty input at the dialog; `MainWindow` performs the authoritative case-insensitive duplicate check against `db.get_watchlist()` and treats it as a no-op with a status message | `AC-D22.3` fixes the three guards; one pure implementation shared by both halves keeps the rule identical and unit-testable | Duplicate checks against the panel's visible rows only (misses a persisted-but-not-shown symbol); no normalisation (duplicate `msft`/`MSFT` rows) |
| S13 | **Restore idempotency** `[new/changed]` | `_restore_watchlist()` calls `watchlist_panel.clear()` **before** repopulating from the DB, so a reconnect reproduces exactly the persisted set | `AC-D22.7` requires the watchlist to match the persisted set after a connect; today `clear()` is only called on close, so a reconnect appends duplicates onto stale rows. Clear-then-populate is the minimal change that makes the DB authoritative without touching panels/geometry | Populate only when the table is empty (still leaves stale rows after a drop when the table is non-empty); leave as-is (duplicates; the persisted set is not faithfully reproduced) |
| S14 | Testing `[existing]` | pytest + pytest-qt, offscreen, no live TWS; each new behaviour ships a pre-fix-red / post-fix-green check | Repo standard (Q8/Q9); the market-data and bridge are injectable (the `tests/test_watchlist_columns_d21.py` `FakeMdManager` and `tests/test_right_dock_d21.py::_boot` `IBApiClient.connect` monkeypatch patterns already exist) | Manual-only / live-TWS tests — rejected |

**No new dependency is introduced by D22. No existing tech-stack item is replaced or deprecated.**

> **S3 reconciled by D23 (2026-10-07).** D22's S3 description of `cancel_contract_details(req_id)` as a
> direct `client.cancelContractDetails(...)` call is corrected by the **D23.1** increment: the pinned
> `ibapi 9.81.1.post1` `EClient` exposes **no** `cancelContractDetails`, so the cancel is a
> **capability-guarded, documented best-effort** call (`getattr(self.client, 'cancelContractDetails',
> None)`, called only if present) — see `## D23 increment` → Tech Stack Decisions S3. The
> `reqContractDetails` request path itself is unchanged. This is the binding `AC-D23.1.4`
> reconciliation.

### System Components (D22 increment)

**Existing components touched (responsibilities unchanged):**
- `[existing] ui/watchlist_panel.py` — table, header strip + D21.11 toggle, D21.5 column
  model/menu, tick handlers, D14 double-click, width/column persistence.
- `[existing] ui/main_window.py` — `DEFAULT_WATCHLIST`, watchlist dock/title-bar wiring,
  `_on_connected`/`_restore_watchlist`/`_on_disconnected`, `md_manager`/`depth_manager`
  injection, QSettings.
- `[existing] data/db.py` — `get_watchlist`/`set_watchlist`, the `watchlist` table.
- `[existing] ibkr/client.py`, `[existing] ibkr/bridge.py` — the client→bridge signal surface.
- `[existing] ibkr/market_data.py`, `[existing] ibkr/contracts.py`, `[existing]
  ibkr/id_manager.py`, `[existing] ibkr/pacing.py`, `[existing] ibkr/error_codes.py`.
- `[existing] ui/visual_conventions.py` — available for consistent affordance styling.

**New components:**
- `[new] services/contract_lookup_service.py` — `ContractLookupService(QObject)`:
  `request(symbol, contract) -> int`, the `lookup_finished(int, str, bool, str)` signal,
  `on_contract_details(req_id, details)` / `on_contract_details_end(req_id)` /
  `on_error(req_id, code, msg)` / `on_timeout(req_id)` handlers, `cancel(req_id)` /
  `cancel_all()`, and `CONTRACT_LOOKUP_TIMEOUT_MS`. Injected with `md_manager` + `bridge`;
  resolution is exactly-once; a disconnect invalidates in-flight lookups (`cancel_all` on
  `_on_disconnected`). Pure of Qt widgets → unit-testable with a fake bridge.
- `[new] ui/add_symbol_dialog.py` — the small modal `AddSymbolDialog` (S7).
- `[new]` `IBBridge` `contract_details` / `contract_details_end` signals and
  `MarketDataManager.req_contract_details` / `cancel_contract_details` (S3) — new members on
  existing modules rather than new modules.

**Changed components:**
- `[new/changed] ui/watchlist_panel.py` — a small `+` `QPushButton` added to the header strip's
  `h_layout` **adjacent to** `header_button` (kept as the D21.11 toggle); a header-strip context
  menu with **"Add symbol…"**; a table-body context menu with **"Remove symbol"**; `remove_symbol`
  (cancel the row's subscription + remove the row + re-index `_req_to_row`/`_row_data`/
  `_prev_close`/`_last_price`/flash timers); `set_add_enabled(bool)`; the
  `symbol_add_requested` / `symbol_remove_requested` signals; the pure `normalise_symbol` /
  `symbol_in_list` helpers. **`add_symbol` and `clear` semantics are unchanged** (the
  `clear()`-before-repopulate is called by `MainWindow`).
- `[new/changed] ui/main_window.py` — `self._ibkr_connected`; seed/`configured` sentinel +
  seed guard in `_restore_watchlist` (which now clears first — S13); construct
  `ContractLookupService`, wire its `lookup_finished`, and `cancel_all` on disconnect; the
  add/remove slots (`_on_watchlist_symbol_add_requested` /
  `_on_watchlist_symbol_remove_requested` / the validation-result callback
  `_on_watchlist_symbol_validated`) doing the gate, guards, validation, subscribe + persist, and
  status messages; `set_add_enabled` calls in `_on_connected`/`_on_disconnected`.
- `[new/changed] ibkr/client.py`, `[new/changed] ibkr/bridge.py`,
  `[new/changed] ibkr/market_data.py` — the S3 request/callback plumbing.
- `[new/changed] data/db.py` — `add_watchlist_symbol` / `remove_watchlist_symbol` (S5).

**Component relationships (D22).** `MainWindow` remains the orchestrator and the **sole
persistence/authority owner**: it holds the connection flag, the DB handle (`db`), `md_manager`,
and the `ContractLookupService`. `WatchlistPanel` stays presentation-only: it owns the
affordances, the modal dialog, the visible rows, and the reqId↔row index, and it emits
`symbol_add_requested` / `symbol_remove_requested`. The add flow is
`panel → MainWindow [gate + duplicate guard] → ContractLookupService.request(...) →
bridge.contract_details/end (queued) → lookup_finished → MainWindow [add_symbol + db.add +
configured sentinel + status]`; the remove flow is
`panel (row menu) → MainWindow → panel.remove_symbol (cancel + re-index) + db.remove`. The
new IBKR path is `ContractLookupService → MarketDataManager.req_contract_details →
IBApiClient.reqContractDetails → (EWrapper) contractDetails/contractDetailsEnd →
IBBridge signals → ContractLookupService`.

### Data Model (D22 increment)

- `[existing]` `Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`,
  `OrderBookLevel`, `UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`,
  `drawing_groups`, `drawings`, `studies`, `positions`, `trade_groups`,
  `position_group_map` — **unchanged**.
- `[existing]` `watchlist(symbol PK, category NOT NULL, sort_order NOT NULL)` — **no schema
  change**. New access paths only (S5).
- `[new]` **Watchlist add/remove access methods** on `DB`:
  `add_watchlist_symbol(symbol, category="EQUITIES")` (append with the next `sort_order`),
  `remove_watchlist_symbol(symbol)` (case-insensitive delete + renumber). `get_watchlist` /
  `set_watchlist` keep their signatures.
- `[new]` **QSettings `watchlist/configured`** — a single boolean sentinel distinguishing
  "never configured" from "explicitly emptied" (S6). **Not** the symbol list, and distinct
  from the D21.5 `watchlist/columns` layout key; the two concerns stay un-conflated.
- `[new]` **`ContractLookupService` pending state** — an in-memory
  `{reqId: PendingLookup(symbol, got_any)}` map plus per-request `QTimer`s; ephemeral, never
  persisted.
- `[new]` **D22 view state** — nothing new beyond the above: the `+` button's enabled flag,
  the dialog, and the table-body menu are ephemeral view state (consistent with D10's
  volume-visibility and D21's view-state precedents).

### Integration Points (D22 increment)

- `[new]` **IBKR `reqContractDetails` / `contractDetails` / `contractDetailsEnd`** — the one
  new external call type, required by B16/`DG43` for live symbol validation. Correlated by
  `reqId` from the existing `id_manager`; paced by the existing `pacing_manager`; failures
  surface on the existing `error_msg` signal (error `200` is `fatal`).
- `[existing]` **IBKR `reqMktData` / `cancelMktData`** — the add subscribes via
  `add_symbol → req_mkt_data`; the remove cancels via `cancel_mkt_data`. No signature change.
- `[existing]` **SQLite (`data/db.py`)** — add/remove through the two new helpers; no
  migration, no schema change.
- `[existing]` **QSettings** — adds `watchlist/configured` alongside `watchlist/width` and
  `watchlist/columns`; the symbol list itself is never stored here.
- `[existing]` **Qt signal bus (`IBBridge`)** — adds the two contract-details signals;
  inbox/outbox for the lookup service; `symbol_add_requested`/`symbol_remove_requested` on
  the panel. No new bus.
- **No new external service, dependency, or persisted table is introduced.**

### Non-Functional Approach (D22 increment)

- **Correctness — async validation (B16/R46).** The lookup is **exactly-once** (a
  `resolved` flag per pending entry) and **bounded** (a single-shot 5s `QTimer`); a late
  `contractDetailsEnd` after a timeout resolution is ignored, and `error_msg`/`contractDetails`
  events for reqIds not in the pending map are ignored so unrelated market-data errors cannot
  resolve a lookup. `contractDetailsEnd` with zero details is a rejection. On any non-`ok`
  resolution, **nothing** is added, subscribed, or persisted (`AC-D22.4`).
- **Correctness — threading.** Bridge signals are emitted on the EClient reader thread and
  delivered to the main-thread `ContractLookupService` via Qt's queued connections (the same
  pattern the existing `historical_bar`/`tick_price` wiring relies on), so the pending map,
  the DB writes and the UI updates all happen on the main thread. No new thread is created.
- **Correctness — persistence (`AC-D22.7`/A52).** The DB is the single source of truth: an add
  appends one row and cancels nothing; a remove deletes one row and cancels its subscription;
  a reconnect reproduces exactly the persisted set (`clear()` then repopulate); an
  explicitly-emptied list stays empty because the `watchlist/configured` sentinel suppresses
  re-seeding. Duplicate detection is case-insensitive on both write and read-back.
- **Correctness — `clear()` placement (informational).** The requirements prose
  (`requirements.md:2121`, `DG40`) describes `clear()` as "called on disconnect"; the repo shows
  it is called from `closeEvent` (`ui/main_window.py:2107`). No `AC-D22.*` outcome depends on the
  distinction: B16b denies adding while disconnected, the DB is authoritative, and S13 makes
  `_restore_watchlist` clear-then-repopulate so a reconnect reproduces the persisted set. This is
  an implementation note, not an architectural change (see `docs/plan_notes.md` / `plan_review.md`).
- **Performance.** Contract lookups are on demand (one per add), paced by the existing
  `pacing_manager`; the watchlist is tiny (O(n) re-index on removal); no polling is added.
  `_restore_watchlist` stays O(n) with one `clear()`.
- **Security / safety.** No new dependency; the live-order path
  (`ibkr/orders.py`) is untouched; **no automated test connects to TWS or transmits an order**
  (Q9) — tests inject a fake `md_manager` and drive the bridge handlers directly; the lookup
  is a read-only contract query.
- **UX consistency.** The add affordance reflects the connection state (disabled while
  disconnected, per `AC-D22.5`); the header strip remains the dock's title-bar widget
  (`D21.11`/`DG37`) so both the toggle and the new `+` stay reachable when the body is collapsed;
  add/remove never load a chart (distinct from D14 / Load Chart); status messages use the
  existing `status_bar`.
- **Non-regression (`AC-D22.8`).** The D21.5 column popup stays bound to the table's
  horizontal header; the D21.11 toggle stays on the header strip; D14 double-click and the
  D21.13 right-dock toggles are untouched. The new body context menu and the header-strip
  menu are separate widgets with unambiguous labels ("Add symbol…" / "Remove symbol" vs the
  column menu's field checkboxes).

### Architecture Risks (D22 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D22-1 | New contract-details callbacks could resolve a lookup from the wrong `reqId` (a shared `error_msg` bus) or twice (late `contractDetailsEnd`) | H | reqId-keyed pending map; `error_msg` handled **only** for pending reqIds; a `resolved` flag makes resolution exactly-once; unknown/late reqIds ignored; unit-tested with out-of-order and duplicate events |
| AR-D22-2 | An unbounded/too-long wait hangs the add; too short a timeout false-rejects a slow TWS | M | Single-shot `QTimer` (`CONTRACT_LOOKUP_TIMEOUT_MS = 5000`) as a named constant; the modal dialog closes on OK and the add completes asynchronously with a status message, so the UI never blocks; the timeout is a plan constant (PA-D22-3), adjustable without architectural change |
| AR-D22-3 | The `watchlist/configured` sentinel could be missed, so an emptied list re-seeds (violates `AC-D22.7`/A52) | M | Set on seed, on every non-empty restore, and on every add/remove; a dedicated round-trip test removes the last symbol, re-runs `_restore_watchlist`, and asserts the list stays empty |
| AR-D22-4 | `_restore_watchlist` clear-then-repopulate could regress a D13/D14/D21 watchlist test | M | No existing test calls `_restore_watchlist` or `_on_connected` (verified by grep); the clear only removes rows/dead reqIds that a fresh connect repopulates from the DB; the full offscreen suite is re-run |
| AR-D22-5 | The new header-strip `+`/menu or the body row menu could shadow the D21.5 column popup or the D21.11 toggle (`DG42`/R48) | M | The column popup is wired to the **table's horizontal header**, the toggle to the **panel header strip**; the new add menu is on the header strip and the remove menu on the **table body** — disjoint surfaces; `+` is appended to the existing `h_layout` (the toggle is untouched); explicit non-regression tests assert the column menu and toggle still work, and that the row menu resolves the Symbol by field key (reorder-safe) |
| AR-D22-6 | A futures symbol's computed front month may not resolve (rollover edge), so a legitimate name is rejected | L | `AC-D22.4` explicitly makes an unresolvable contract a rejection with an error and nothing persisted — acceptable per B16; the lookup uses the same `get_contract_for_symbol` builder as the restore/replay paths, so the behaviour is consistent |
| AR-D22-7 | `remove_symbol` row re-indexing could desynchronise `_req_to_row` (ticks landing on the wrong row) | M | The helper re-maps every row index after the removed row across `_req_to_row`/`_row_data`/`_prev_close`/`_last_price` and stops the removed row's flash timers; tested by removing a middle row of three and asserting a later tick lands on the correct symbol row |
| AR-D22-8 | Adding a lookup path touches the shared IBKR client/bridge and could disturb existing callbacks | L | The change is additive (two overrides + two signals + two manager methods); existing callbacks and their tests are untouched; the override-forwarding behaviour is unit-tested by calling the handlers directly |
| AR-D22-9 | The `watchlist/configured` sentinel is read/written through the **real** `QSettings("NDThinkChart","NDThinkChart")` (not injectable), so D22 tests that drive `_restore_watchlist` could couple to one another or leave the sentinel set on the developer machine (the same class as the recorded shared-test-DB gotcha) | L | Use the existing D17/D18 `_clean_settings()`/isolated-settings pattern to clear `watchlist/configured` around each D22 `MainWindow` test; a full clean offscreen suite re-run confirms no order-dependence. This is a test-isolation detail, not an architectural change |
| AR-D22-10 | Two adds for the same symbol could be in flight before the first resolves (the duplicate guard checks the DB, which is written only on success) | L | The requirement's duplicate rule applies to an **existing** watchlist symbol (`AC-D22.3`); the add is initiated from a modal dialog and completes asynchronously on the single main thread, so overlap is not reachable in normal use. No `AC-D22.*` criterion depends on simultaneous same-symbol adds; Task Manager may cover it as an edge in the duplicate guard if desired |

### Implementation sequencing (D22 increment)

Detailed phases, dependencies and `touches_files` notes are in `docs/plan.md`. At the
architecture level the sequence is: (1) watchlist persistence helpers (`data/db.py`), (2) IBKR
contract-details plumbing + the `ContractLookupService`, (3) watchlist panel affordances + the
`AddSymbolDialog` + the connection-reflecting enable state, (4) `MainWindow` add/remove flow +
the restore/seed guard, (5) non-regression and full-suite verification. Phases 1–3 touch fully
disjoint file sets and may run in one wave; Phase 4 depends on all three; Phase 5 follows.
D1–D21 are frozen throughout.

---

## D23 increment — Batch 17: two D22 post-build quality corrections (validated 2026-10-07)

> **Increment scope.** A **small, purely corrective** increment on top of the **built, frozen D1–D22**
> system (D1–D21 at commit `286341e`, 673 tests; **D22 built and green at 712 tests**, uncommitted).
> D1–D22 are **frozen** and are **not** re-planned. This is an existing-repo run:
> `requirements.md` contains the marker sentence `This is an existing repository.` and a Current Tech
> Stack; **PyQt6 + pyqtgraph + official `ibapi` + SQLite is a hard constraint**. **No stack change,
> no schema change, no new dependency, and no live-order-path change.** Items are labelled
> `[existing]`, `[new]`, or `[new/changed]`.
>
> D23 corrects the two **nice-to-have** Code Reviewer findings on the D22 work, both approved by the
> user for a full-pipeline fix: **D23.1 = ESC-030** (a capability-guarded, documented
> contract-details cancel) and **D23.2 = ESC-031** (the `_row_data` row-key invariant in
> `remove_symbol`). D23 **does not reopen D22's feature criteria** (`AC-D22.1`–`AC-D22.9` stand); it
> supersedes only the **task-level** `AC-D22.2.3` wire-cancel mandate (**corrected**) and
> **reconciles the D22 architecture row `S3`**.

**Summary.** D23 is a targeted two-item correctness increment on the built D22 watchlist work.
**(D23.1)** `MarketDataManager.cancel_contract_details` becomes a **capability-guarded best-effort
cancel** (`getattr(self.client, 'cancelContractDetails', None)`, called only if present) with an
in-code note that the pinned `ibapi` (`9.81.1.post1`) lacks the method, that TWS's own
`contractDetailsEnd`/error ends the wire request, and that `ContractLookupService`'s local
invalidation (bounded QTimer + `cancel_all` on disconnect) is the real safety net — no raised and no
silently-swallowed `AttributeError`. **(D23.2)** `WatchlistPanel.remove_symbol` drops the removed
row's own `_row_data` key, so `set(_row_data.keys()) == set(range(table.rowCount()))` after **any**
removal (first / middle / last / only), and the missing last-row (and/or first/only-row) coverage is
added. Both are additive, behaviour-preserving corrections: no stack change, no schema change, no
new dependency, no live-order-path change, and no reopening of `AC-D22.1`–`AC-D22.9`.

**Validator verification (2026-10-07 — independently checked against the current source, not taken
from the proposal).**
- `.venv` `ibapi` is **9.81.1.post1**; `hasattr(EClient, 'cancelContractDetails') is False` while
  `hasattr(EClient, 'reqContractDetails') is True`. `ibkr/market_data.py:78–84` is exactly
  `if req_id is None: return` + `try: self.client.cancelContractDetails(req_id) except Exception:
  pass`.
- **The RC-1 pre-fix-red evidence is genuine.** An AST inspection of
  `inspect.getsource(MarketDataManager.cancel_contract_details)` on the current tree finds an
  `ast.Attribute` node with `attr == 'cancelContractDetails'`; the substring
  `self.client.cancelContractDetails(` is present; and `getattr(self.client, …)` is **absent**. So
  the proposed code-shape/source assertion is **red pre-fix** and green after the guard.
- **The behavioural no-exception case cannot be pre-fix-red** (so the honest classification is a
  post-fix guard): `MarketDataManager(types.SimpleNamespace(reqContractDetails=lambda *a: None))
  .cancel_contract_details(7)` **returns normally on the current (pre-fix) tree** — the bare
  `AttributeError` is raised inside the retained `try` and swallowed — externally identical to the
  guarded form.
- `ui/watchlist_panel.py::remove_symbol` is `:682–728`; `_row_data` re-index at `:716–719` never
  drops the removed row's own key; `_req_to_row` (`:705`) and the flash timers (`:710–711`) are
  handled explicitly. A tree-wide grep confirms `cancel_contract_details` has **no production
  caller** (only its definition and its own tests).

### Codebase Summary (existing repository — D23 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2851 nodes, refreshed
> 2026-10-06 21:47) and then **validated against the current source files** (the repository is
> authoritative). The D23 surface is two functions and their tests: the contract-details cancel in
> `ibkr/market_data.py`, the row re-index in `ui/watchlist_panel.py::remove_symbol`, and the two D22
> test modules that cover them.

**Data models / schema**
- `[existing]` **SQLite `watchlist` table** — `data/db.py:23–27`:
  `watchlist(symbol TEXT PRIMARY KEY, category TEXT NOT NULL, sort_order INTEGER NOT NULL)`. D22 added
  access helpers (`add_watchlist_symbol` / `remove_watchlist_symbol`); D23 needs **no** schema or
  access-path change.
- `[existing]` All other persisted tables (`bars`, `alarms`, `zones`, `drawings`, …) — **unchanged**.
- `[existing]` **`WatchlistPanel` in-memory row-keyed state** (not persisted):
  `_req_to_row: dict[int, int]` (reqId → row), `_row_data: dict[int, dict]` (row → cached field
  values, FieldKey-bound), `_prev_close: dict[int, float]` and `_last_price: dict[int, float]`
  (keyed by **reqId**, not row), and `_flash_timers: dict[tuple[int, str], QTimer]` (keyed by
  `(row, field)`). This is the state D23.2's invariant applies to.
- `[existing]` **`ContractLookupService._pending: dict[int, PendingLookup]`** — the in-flight
  contract-details correlation map (`services/contract_lookup_service.py:85`), ephemeral, never
  persisted. D23.1 does not change it.
- `[existing]` **QSettings `("NDThinkChart","NDThinkChart")`** — keys `watchlist/width`,
  `watchlist/columns` (D21.5), `watchlist/configured` (D22 seed sentinel). D23 adds none.

**Major components and responsibilities**
- `[existing]` **`ibkr/market_data.py::MarketDataManager`** (~92 lines) — `req_historical_data`
  (`:20`), `req_mkt_data`/`cancel_mkt_data` (`:56`/`:63`), **`req_contract_details(contract) -> int`**
  (`:71–76`, D22), **`cancel_contract_details(req_id)`** (`:78–84`, D22 — *the D23.1 target*),
  `cancel_historical_data` (`:86`). `cancel_contract_details` currently does:
  `if req_id is None: return` then `try: self.client.cancelContractDetails(req_id) except
  Exception: pass`.
- `[existing]` **`ibkr/client.py::IBApiClient(EWrapper, EClient)`** (~223 lines) — forwards EWrapper
  callbacks to `IBBridge`; D22 added `contractDetails` / `contractDetailsEnd` overrides mirroring the
  existing callback pattern. `error()` (`:114–141`) forwards non-`info` severities to
  `bridge.error_msg` (error `200` is `fatal`, `ibkr/error_codes.py:12`).
- `[existing]` **`ibkr/bridge.py::IBBridge(QObject)`** — typed signal bus; D22 added
  `contract_details(int, object)` and `contract_details_end(int)`.
- `[existing]` **`services/contract_lookup_service.py::ContractLookupService(QObject)`** (~176
  lines) — owns the reqId-keyed pending map, arms a single-shot `QTimer(CONTRACT_LOOKUP_TIMEOUT_MS
  = 5000)` per request, resolves **exactly once** via `lookup_finished(req_id, symbol, ok, reason)`.
  `cancel(req_id)` (`:114–120`) / `cancel_all()` (`:122–125`) **drop the pending entry and stop the
  timer** — they do **not** call `md_manager.cancel_contract_details`. `_on_disconnected` in
  `MainWindow` calls `cancel_all()`. This is the **real safety net** D23.1 must document.
- `[existing]` **`ui/watchlist_panel.py::WatchlistPanel`** (816 lines) — `QTableWidget`, header strip
  (`self.header_bar`, `:282–289`) + D21.11 collapse toggle, D21.5 column model/menu (`:605`), tick
  handlers, D14 double-click, width/column persistence. `add_symbol(symbol, contract)` (`:664`)
  inserts a row, renders cells, subscribes via `req_mkt_data`, records `_req_to_row`.
  **`remove_symbol(symbol) -> bool`** (`:682–728`) — *the D23.2 target*: finds the row
  case-insensitively, cancels that row's `req_mkt_data` and pops its
  `_req_to_row`/`_prev_close`/`_last_price`, stops the removed row's flash timers,
  `table.removeRow(row)`, then re-indexes `_row_data` (`:716–719`), `_req_to_row` (`:720–723`) and
  `_flash_timers` (`:724–727`). `clear()` (`:730+`) empties all row-keyed state.
- `[existing]` **`ui/main_window.py::MainWindow`** (~2113+ lines, D22-modified) — `DEFAULT_WATCHLIST`,
  watchlist dock + title-bar wiring, `_on_connected` / `_restore_watchlist` / `_on_disconnected` (→
  `self._contract_lookup.cancel_all()`), `ContractLookupService` construction and `lookup_finished`
  wiring, the add/remove slots, the connection gate. Not touched by D23.
- `[existing]` **`data/db.py`** — `get_watchlist` / `set_watchlist` + the D22 `add_watchlist_symbol` /
  `remove_watchlist_symbol` helpers. Not touched by D23.

**Key entry points**
- **Watchlist add** — `+` button / header-strip "Add symbol…" → `MainWindow` gate + duplicate check →
  `ContractLookupService.request` → `reqContractDetails` → bridge callbacks (queued) →
  `lookup_finished` → `WatchlistPanel.add_symbol` + `db.add_watchlist_symbol`.
- **Watchlist remove** — table-body "Remove symbol" → `MainWindow` →
  `WatchlistPanel.remove_symbol` + `db.remove_watchlist_symbol`.
- **Contract-lookup cancellation** — `ContractLookupService.cancel` / `cancel_all` (local
  invalidation). `MarketDataManager.cancel_contract_details` has **no production caller** (grep across
  the tree: only its definition at `ibkr/market_data.py:78` and its own tests).

**External integrations already in use**
- `[existing]` **IBKR via the official `ibapi` (pinned `9.81.1.post1`), live TWS port 7496 only**:
  `reqMktData`/`cancelMktData` (watchlist ticks), `reqHistoricalData`/`cancelHistoricalData` (chart +
  D16 backfill), `reqMktDepth` (DOM), realtime bars, account/position/order callbacks, and (new in
  D22) `reqContractDetails` / `contractDetails` / `contractDetailsEnd`.
- `[existing]` **SQLite** via `data/db.py` (module singleton `db`), path from
  `config/paths.get_db_path()`.
- `[existing]` **QSettings**, the **Qt signal bus** (`IBBridge`), and the **pyqtgraph** chart scene.

**Verified facts that shape D23 (source-validated 2026-10-07)**
1. **The pinned `ibapi` has no cancel.** `.venv` `ibapi 9.81.1.post1`;
   `hasattr(EClient, 'cancelContractDetails') is False` while `hasattr(EClient,
   'reqContractDetails') is True`. Therefore `ibkr/market_data.py:82`'s
   `self.client.cancelContractDetails(req_id)` raises `AttributeError`, which the enclosing
   `except Exception: pass` (`:83–84`) silently swallows → the cancel is a **no-op on the wire**.
   Requirement **D23.1** fixes this as a **capability-guarded, documented** call.
2. **The wire cancel is dead code today.** No production path calls
   `MarketDataManager.cancel_contract_details`; `ContractLookupService.cancel`/`cancel_all` only drop
   the pending entry and stop the bounded timer; `_on_disconnected` calls `cancel_all()`. TWS ends a
   `reqContractDetails` request itself (`contractDetailsEnd` / an `error`). Hence the behaviour change
   is **forward-correctness**, verifiable in isolation, with **no D22 observable behaviour change**
   (`AC-D23.1.4` / A53 / A54).
3. **The D22 test's fake hides the gap.** `tests/test_ibkr_contract_details_d22.py::_FakeClient`
   (`:118–130`) **defines** `cancelContractDetails` (`:127`); `TestD22_02_T03` (`:133`) covers
   "delegates + None-safe" (`:151`) and "swallows client exception" (`:163`) but has **no** case for a
   client that *lacks* the method. D23.1 adds that case and pairs the method-defining fake with a
   fake that does not define it (`AC-D23.1.1`).
4. **`remove_symbol` leaves a stale `_row_data` key only on the last row.**
   `ui/watchlist_panel.py:716–719` re-indexes `_row_data` with `{(r-1 if r > row else r): values…}`
   but **never drops the removed row's own key**. Reproduced: a 3-row panel (AAPL/MSFT/TSLA),
   `remove_symbol('TSLA')` → `rowCount() == 2` but `sorted(_row_data.keys()) == [0, 1, 2]` (stale key
   2). A middle-row removal leaves `[0, 1]` because the shifted-up row overwrites the removed key.
   `_req_to_row`, `_prev_close`/`_last_price` and `_flash_timers` are already handled explicitly, so
   **only `_row_data`** carries the stale key (`AC-D23.2.1`–`AC-D23.2.2` / A55).
5. **The existing remove coverage cannot catch it.**
   `tests/test_watchlist_add_remove_d22.py::test_D22_05_T02` (`:281`) removes the **middle** row and
   asserts `_row_data.keys() == {0, 1}` — it passes pre-fix. There is **no** last/first/only-row
   assertion; `test_D22_05_T03` (`:324`) covers the absent/blank no-op (`AC-D23.2.3`/`AC-D23.2.4`).

### Tech Stack Decisions (D23 increment)

Constrained (existing) choices first, then the D23 additions. **No new dependency.**

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Existing-repo hard constraint; "Changing the tech stack" is an explicit Non-Goal | Any new UI/charting framework — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` (pinned `9.81.1.post1`), live TWS port `7496` only; numpy (`>=1.26`); SQLite via `config/paths.get_db_path()`; PyInstaller `.app`; pytest + pytest-qt offscreen (no live TWS) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB / new test framework — rejected |
| S3 *(reconciled)* | **D23.1 — capability-guarded best-effort contract-details cancel** `[new/changed]` | Rewrite `[existing] ibkr/market_data.py::MarketDataManager.cancel_contract_details` to: keep `if req_id is None: return`; resolve `cancel = getattr(self.client, 'cancelContractDetails', None)`; **call it only if present**, inside the existing containment (`try/except Exception: pass`); carry a docstring/comment documenting that (a) pinned `ibapi 9.81.1.post1` exposes no `EClient.cancelContractDetails`, (b) TWS's own `contractDetailsEnd`/error ends the wire request, and (c) `ContractLookupService`'s local invalidation (bounded 5s QTimer + `cancel_all` on disconnect) is the real safety net. This **reconciles D22 architecture row `S3`** (the request path is unchanged; only the cancel is corrected) and **supersedes the task-level `AC-D22.2.3`** wire-cancel mandate (`AC-D23.1.1`–`AC-D23.1.4`) | `getattr`-guard makes the call **capability-detected**: correct on the pinned dep today (no-op, no exception) and forward-correct if a future `ibapi` adds the method (called once). Keeping the containment preserves the method's existing "never raises" contract (`AC-D23.1.3`), and the documentation makes the no-op **intentional and discoverable** rather than a swallowed `AttributeError`. It also matches the ESC-030 suggested direction exactly | (i) **Leave as-is** — silently swallowed `AttributeError`; dishonest and non-forward-correct (rejected). (ii) **Delete the call + the method** — removes a public-shaped method the D22 architecture names, loses forward-compat, and cannot be asserted (rejected). (iii) **Drop the `try/except` and let it raise** — breaks the established containment contract and could surface on a reader/UI path (rejected). (iv) **Attempt a real wire cancel some other way** — no such API exists on the pinned dep (rejected) |
| S15 | **D23.2 — `_row_data` row-key invariant in `remove_symbol`** `[new/changed]` | In `[existing] ui/watchlist_panel.py::remove_symbol`, drop the removed row's own entry while re-indexing — e.g. `self._row_data.pop(row, None)` alongside the existing `{(r-1 if r > row else r): values …}` re-map — so that after `remove_symbol` returns `True`, `set(self._row_data.keys()) == set(range(self.table.rowCount()))` (and, unchanged, the `_req_to_row` values and `_flash_timers` keys cover exactly the surviving rows). Update the `remove_symbol` docstring's re-index contract to state the invariant | The stale key is caused by the removed row's own index never being overwritten when it is the max index. Popping it first makes the invariant explicit and mirrors the **already-explicit** handling of `_req_to_row` (popped) and `_flash_timers` (removed-row timers stopped). The narrow fix keeps the shift expression and the FieldKey-bound `_row_data` values untouched (DG32), preserving `_rebuild_table`/`_set_cell` behaviour (`AC-D23.2.4`) | (i) **Rely on the shift alone** — leaves the stale last-row key (the defect; rejected). (ii) **Rebuild `_row_data` from the table contents** — discards cached field values and the FieldKey binding, and re-queries widgets (rejected: risks DG32/`_set_cell` regressions and is a larger change). (iii) **Filter with `{k: v for k, v in … if k < rowCount()}`** — works but is less direct than popping the removed key and obscures *why* the key is stale (rejected in favour of the explicit pop) |
| S16 | **D23 test surface** `[new/changed]` | Update two D22 test modules: `tests/test_ibkr_contract_details_d22.py` — (i) a **code-shape/source assertion** (the pre-fix-red evidence for `AC-D23.1.1`): `cancel_contract_details`'s own source contains **no** bare `self.client.cancelContractDetails(...)` attribute access and **does** contain the `getattr(self.client, "cancelContractDetails", None)` capability guard; (ii) a **missing-capability behavioural test** with a fake that does **not** define `cancelContractDetails` (e.g. `types.SimpleNamespace(reqContractDetails=…)`) asserting no exception (a **post-fix guard**, explicitly *not* pre-fix-red); (iii) the **present-method** case with the method-defining `_FakeClient` (invoked once with `req_id`); keep the existing "delegates"/"None-safe"/"raises" cases. `tests/test_watchlist_add_remove_d22.py` — add **last-row** (and/or **first-row** / **only-row**) removal assertions that fail pre-fix | Q8: every fix ships a check that fails before and passes after, runnable offscreen. For D23.2 the last-row assertion is genuinely red pre-fix. For D23.1 the fix retains `try/except Exception: pass` and changes **no externally observable behaviour** (the pre-fix code already returns normally for a client lacking the method — `AttributeError` raised inside the `try`, swallowed — and a `getattr(…, None)` guard still performs the attribute lookup), so **no behavioural or attribute-access-spy test can be red pre-fix**; the genuine pre-fix-red evidence is therefore the **code-shape/source assertion**, and the behavioural cases are honest **post-fix guards** (`AC-D23.1.1`). A method-defining fake no longer matches the pinned surface, so the no-op must also be exercised against a fake that omits the method. The existing middle-row test (`test_D22_05_T02`) passes pre-fix and cannot be the only guard (`AC-D23.2.3`) | Behavioural-only testing of the guard (cannot be red pre-fix — the retained containment makes pre/post behaviour indistinguishable); a live-TWS test (forbidden by Q9); asserting the private attribute's absence at import time (brittle) |
| S14 | Testing `[existing]` | pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS; run as `.venv/bin/python -m pytest` (stale `pytest` shebang is a known gotcha) | Repo standard (Q8/Q9) | Manual-only / live-TWS tests — rejected |

**D23 introduces no new dependency and replaces or deprecates no existing tech-stack item.** The
pinned `ibapi` version is **not** changed — D23 makes the code honest about its actual surface
instead.

### System Components (D23 increment)

**Existing components (responsibilities unchanged):**
- `[existing] services/contract_lookup_service.py` — `ContractLookupService` pending map, bounded
  QTimer, exactly-once resolution, `cancel`/`cancel_all` local invalidation. **Unchanged** — D23.1
  documents it as the safety net.
- `[existing] ibkr/client.py`, `[existing] ibkr/bridge.py` — the contract-details request/callback
  plumbing. **Unchanged** (the request path is untouched; only the cancel is corrected).
- `[existing] ibkr/contracts.py`, `[existing] ibkr/id_manager.py`, `[existing] ibkr/pacing.py`,
  `[existing] ibkr/error_codes.py`. **Unchanged.**
- `[existing] data/db.py`, `[existing] ui/main_window.py`, `[existing] ui/add_symbol_dialog.py`.
  **Unchanged by D23.**
- `[existing] ui/watchlist_panel.py::WatchlistPanel` — all behaviour except the `remove_symbol`
  re-index body. **Unchanged** otherwise (table, header strip, D21.5 column model/menu, D21.11
  toggle, `add_symbol`, `clear`, tick handlers, D14 double-click, persistence).

**Changed components:**
- `[new/changed] ibkr/market_data.py::MarketDataManager.cancel_contract_details` — capability-guard +
  documentation (S3/D23.1). Public signature `cancel_contract_details(req_id: int | None) -> None`
  unchanged; `req_contract_details` unchanged.
- `[new/changed] ui/watchlist_panel.py::WatchlistPanel.remove_symbol` — drop the removed row's
  `_row_data` key while re-indexing; docstring states the row-key invariant (S15/D23.2). Signature
  `remove_symbol(symbol: str) -> bool` unchanged.
- `[new/changed] tests/test_ibkr_contract_details_d22.py`,
  `[new/changed] tests/test_watchlist_add_remove_d22.py` — added/updated cases (S16).

**No new component, module, thread, or dependency is introduced.** The request/response path
(`ContractLookupService → MarketDataManager.req_contract_details → IBApiClient.reqContractDetails →
bridge signals → ContractLookupService`) and all component relationships are unchanged; only the
(uncalled) cancel is corrected and one panel method's internal state bookkeeping is tightened.

### Data Model (D23 increment)

- `[existing]` All persisted entities and tables (`Bar`, `Alarm`, `Drawing`, `Watchlist`, …; tables
  `bars`, `watchlist`, `alarms`, `zones`, `drawings`, …) — **unchanged; no migration, no schema
  change**.
- `[existing]` `ContractLookupService._pending` (reqId → `PendingLookup`) — **unchanged**.
- `[existing]` QSettings keys `watchlist/width`, `watchlist/columns`, `watchlist/configured` —
  **unchanged**.
- `[new/changed]` **Documented row-key invariant on `WatchlistPanel`'s in-memory state** (not
  persisted): after `remove_symbol` returns `True`,
  `set(_row_data.keys()) == set(range(table.rowCount()))`; the `_req_to_row` **values** and the
  `_flash_timers` **keys** likewise cover exactly the surviving rows (no key for a removed row
  survives). `_prev_close` / `_last_price` stay keyed by **reqId** with the removed row's reqIds
  dropped. This is a corrected invariant over existing structures, not a new store.

### Integration Points (D23 increment)

- `[existing]` **IBKR `reqContractDetails` / `contractDetails` / `contractDetailsEnd`** — the D22
  request path is **unchanged**. D23.1 records the externally-verified fact that the pinned `EClient`
  exposes **no** `cancelContractDetails`, so the wire request has no client-side cancel and is ended
  by TWS itself. No new IBKR call type is added.
- `[existing]` **ContractLookupService local invalidation** — the bounded QTimer + `cancel_all()` on
  disconnect remain the safety net for an unresolved lookup (`AC-D23.1.2`).
- `[existing]` **SQLite / QSettings / Qt signal bus / pyqtgraph** — unchanged.
- **No new external service, API, dependency, or persisted table is introduced by D23.**

### Non-Functional Approach (D23 increment)

- **Correctness — capability guard (D23.1).** The cancel performs `getattr(..., None)` and calls the
  method only when present, so on the pinned `ibapi` it is a **clean no-op** rather than a swallowed
  `AttributeError` (`AC-D23.1.1`). Containment is preserved: `req_id is None` is a no-op, and a client
  whose (present) cancel **raises** does not propagate (`AC-D23.1.3`). The documentation requirement
  (`AC-D23.1.2`) makes the pinned-dep absence, TWS's `contractDetailsEnd` termination, and the
  `ContractLookupService` safety net discoverable in-code.
- **Forward correctness (D23.1).** If a future `ibapi` adds `cancelContractDetails`, the guard calls
  it exactly once with `req_id` — the method becomes live with no further change; the D23.1.4
  correction record keeps the task/architecture records consistent with the pinned surface.
- **Correctness — row-key invariant (D23.2).** The re-index stays O(n) over the watchlist (a very
  small n) and now drops the removed row's own `_row_data` key, so reads (all of which go through
  `table.item(row, col)` for `row in range(rowCount())`) and the FieldKey-bound
  `_rebuild_table`/`_set_cell` path are unaffected; the invariant is asserted for first / middle /
  last / only-row removals (`AC-D23.2.1`–`AC-D23.2.4`).
- **Performance.** No change: no polling, no new request, no new thread; the cancel rarely/never runs
  (dead code today) and the re-index is unchanged in cost.
- **Security / safety (Q9).** No new dependency; the live-order path (`ibkr/orders.py`) is untouched;
  no automated test connects to live TWS or transmits an order. The contract lookup is a read-only
  query.
- **Test discipline (Q8).** Both fixes ship a **genuine** pre-fix-red / post-fix-green check, runnable
  offscreen; the pre-existing suite (712 tests) must stay green. D23.2's pre-fix-red evidence is the
  last-row assertion. D23.1's fix retains `try/except Exception: pass` and changes no externally
  observable behaviour, so its pre-fix-red evidence is a **code-shape/source assertion** (the bare
  `self.client.cancelContractDetails(...)` access is gone; the `getattr(self.client,
  "cancelContractDetails", None)` guard is present) rather than a behavioural test — the behavioural
  missing-capability (no exception) and present-method (called once with `req_id`) cases are
  **post-fix guards**, explicitly *not* pre-fix-red. The shared-test-DB and stale-`pytest`-shebang
  gotchas recorded in `docs/memory.md` apply — verify with a clean full-suite run as
  `.venv/bin/python -m pytest`.
- **Non-regression.** `AC-D22.1`–`AC-D22.9` stand; the add/remove flow, persistence, connection gate,
  D21.5 column menu, D21.11 toggle, D14 double-click and D21.13 dock behaviour are untouched.

### Architecture Risks (D23 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D23-1 | The guarded cancel could still swallow a genuine error, or could stop containing one (raising to a caller) | M | Keep the `try/except Exception: pass` around the guarded call and add/keep explicit cases for `req_id is None`, missing attribute, and a raising client (`AC-D23.1.3`); assert `cancel_calls == [7]` only for the present-method case |
| AR-D23-2 | A test that only uses the method-defining `_FakeClient` cannot exercise the pinned (missing) surface, so the guard could regress unnoticed; and because the retained containment makes pre/post behaviour identical, a behavioural test cannot be pre-fix-red | M | Add the **code-shape/source assertion** (pre-fix-red: no bare `self.client.cancelContractDetails(...)` access; `getattr(self.client, "cancelContractDetails", None)` present) **and** pair the method-defining fake with a fake that does **not** define `cancelContractDetails` (`types.SimpleNamespace(reqContractDetails=…)`) as a post-fix no-exception guard (`AC-D23.1.1`) |
| AR-D23-3 | Correcting the task-level `AC-D22.2.3` and its test could conflict with the already-built D22 tests, leaving the suite red if not updated in lockstep (R49) | L | Update `AC-D22.2.3` (Task Manager, `docs/tasks/task-graph.json` task `D22-02`) and `tests/test_ibkr_contract_details_d22.py` **in lockstep** with the guard; keep the None/raises cases; confirm the full 712-test suite stays green |
| AR-D23-4 | Re-indexing `_row_data` incorrectly could shift a symbol's cached values onto the wrong row (R50) | L | Use the narrow fix (pop the removed key around the existing shift) and assert `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/last/only-row removals; leave `_rebuild_table`/`_set_cell` FieldKey binding (DG32) unchanged |
| AR-D23-5 | The `S3` reconciliation could remain doc-only/ambiguous, leaving architecture and the pinned surface inconsistent | L | Rewrite architecture `S3` to the capability-guarded best-effort cancel (recorded in this increment and cross-referenced from the D22 `S3` row); record the reconciliation in `docs/plan_notes.md`; Code Reviewer re-verifies ESC-030 after Build |
| AR-D23-6 | Broadening the fix beyond the two findings (e.g. touching the request path or persistence) could regress D22 | L | Scope guard: D23 touches only `cancel_contract_details` + the test, and `remove_symbol`'s re-index + the test; the request path, DB, `MainWindow`, and the recipe flows are untouched; D1–D22 criteria are re-affirmed |

### Implementation sequencing (D23 increment)

At the architecture level the sequence is: **(1)** the D23.1 capability-guarded, documented cancel
plus its missing-capability test; **(2)** the D23.2 `remove_symbol` `_row_data` stale-key fix plus the
last/first/only-row coverage; **(3)** the record reconciliation (`S3` in `docs/architecture.md`,
`AC-D22.2.3` in `docs/tasks/task-graph.json`) and full-suite non-regression verification. Phases 1 and
2 touch **fully disjoint** file sets and may run in the same wave; Phase 3 follows both. D1–D22 are
frozen throughout. Detailed phases, coverage and `touches_files` notes are in `docs/plan.md`.

## [NEW] Target architecture — `TickerSession` per-symbol model (D24 / D25 / D28)

> **Status: DRAFT 2026-10-12 — target architecture, partially as-built.**
> **[P3 2026-10-12]** The session substrate below is now **as-built**: D28.1 pacing off the
> GUI thread (3a), the `TickerSession` per-symbol model with session registry and reqId
> routing (3b), pop-out chart windows with read-only overlays and D24.9 restore (3c), and
> the headless `AlarmMonitor` (3d) — branch `phase3-sessions-popouts` at `ba28c08`,
> 855 passed, unmerged per R52. The design prose below is retained as the design record;
> it now describes implemented code for the session/pacing/pop-out/monitor parts.
> **[P4 2026-10-13]** The remaining Phase 4 targets are now **as-built**: rolling 600s
> non-blocking historical pacing (D28.3, 4a), static-history + live-bar render layers
> with the study cache actually read (D28.4, 4b), and explicit teardown with the
> reader-thread join (D28.5, 4c) — branch `phase4-pacing-perf-teardown` at `3d12821`,
> 898 passed, unmerged (the AC-D28.4 10-chart gate passes, clearing Phase 3's merge per
> R52). The design prose below is unchanged except where annotated **[P4 2026-10-13]**.
> Open follow-ups, **not** as-built: scroll-back paging, `contract.class_` derivation
> from `contract.secType`, post-teardown singleShot retry cleanup.
> The D1–D23 as-built record above is unchanged. Requirement refs: D24, D25, D28.2–D28.6.

### Why: the as-built data plane has cardinality 1

`ui/main_window.py` owns every piece of chart state as singletons: `load_chart` (`:813`)
reads toolbar widgets; `_on_realtime_bar` (`:1173-1176`) filters on the single
`self._rt_req_id`; `self._aggregator` (`:537`), `_current_symbol/_current_tf` (`:534-535`),
`_current_alarms` (`:553`), `_last_chart_price` (`:554`); the history-wave apparatus
(`_history_req_ids`, `_history_generation`, `_backfill_missing_spans`,
`_backfill_failed_req_ids`, `_pending_bars`, `_history_wave_timer`, `:538-552`) assumes
exactly one chart. A second `ChartPanel` for another symbol has nowhere to attach —
this is the concrete blocker D28.2 names, and D24's `TickerSession` is its fix.

### The session object

New module `ui/ticker_session.py::TickerSession(QObject)`, keyed by uppercase symbol.
One instance per symbol per process, held in a registry on `MainWindow`
(`dict[str, TickerSession]`). It owns, per symbol:

| Owned state | Moved from (as-built) | Notes |
|---|---|---|
| Bar series + `BarAggregator` per timeframe in use | `MainWindow._aggregator` (`:537`), `ChartPanel._bars` stays view-local for render | Aggregator is session-level so N views share one aggregation; views keep their own plotted copies via the existing `update_chart`/`update_last_bar` |
| Realtime-bar reqId + subscription lifecycle | `MainWindow._rt_req_id` (`:922`), `RealtimeBarsManager.subscribe` | Refcounted: first holder (view or alarm monitor) subscribes, last holder releases; never two `reqRealTimeBars` for one symbol (A62) |
| History-wave lifecycle: req-id registry, watchdog `QTimer`, generation fencing, missing-span/backfill plan | `MainWindow` `:709-810`, `:932-956`, `:768-787`, `:1070-1157` | Semantics unchanged (D16 wave), ownership moved; concurrent waves across sessions respect IBKR historical pacing (D28.3) |
| Studies config + `_StudyCache` | `MainWindow._current_studies`, `_load_studies_for_symbol` (`:1255`), `ChartPanel._study_cache` | Cache keyed `(symbol, timeframe, studies-hash)` moves into the session so views share computed arrays; D28.4 additionally requires the cache to actually be **read** (today `_StudyCache.get()` has zero callers). **[P4 2026-10-13]** Now read (4b): `ChartPanel._compute_study_values` takes the incremental path on exact match (`n_bars == len-1`, `last_ts` matches) — shifts cached arrays and computes only the new candle via the new `*_update` fns in `services/indicator_service.py`; `update_chart` invalidates the cache on wholesale bar replacement; ICT capped to trailing `ICT_TRAILING_BARS = 500` |
| Drawings + drawing groups | `MainWindow` `:964-1060` handlers | Main chart is the sole writer (A64); session emits `drawings_changed`; persistence still via `DrawingStore` |
| Alarms + `_last_chart_price` | `MainWindow._current_alarms` (`:553`), `_reload_current_alarms` (`:1267`), `_on_aggregated_bar` (`:1179-1197`) | **Evaluation moves into the session**: every aggregated bar runs `evaluate_alarms`; fixes D27.1 (never move `_last_chart_price` backward on wave finalize) |
| Stream-health state | (new — D27.4) | `subscribed / awaiting-first-bar / live / failed+code` per session; persistent indicator; backoff retry |

Signals (same-process Qt, queued where crossing from IBKR threads as today):
`bars_updated`, `studies_changed`, `drawings_changed`, `alarms_changed`,
`alarm_triggered(alarms)`. Views attach/detach (`session.attach(view)` /
`session.detach(view)`); attach performs an initial full sync
(bars → studies → drawings → alarms) with no IBKR request when the session already
holds the data. Teardown rule (A61): destroy only when `views == 0 AND NOT monitored`.

### reqId → session routing

`_on_realtime_bar`, `_on_historical_bar`, `_on_historical_data_end`, `_on_error` stop
filtering on singletons (`self._rt_req_id`, `reqId in self._history_req_ids`) and route
by a `reqId → TickerSession` table maintained at subscribe time. This also repairs D27.3:
every live subscription (chart RT bars, DOM, watchlist mkt-data) is registered with a
type tag in `SubscriptionManager` (whose `subscribe()` currently has zero callers), and
reconnect replays each via its manager with reqIds rebound to sessions.

### `MainWindow` after extraction

Keeps: the session registry, the primary view, toolbar wiring (now calling
`load_chart(symbol, timeframe, extended_hours)` — parameterised, D28.2 — instead of the
widget-reading path at `:813-820`), watchlist/docks, toast + sound (toast parented to
the window, not `self.chart_panel`; `alarm_triggered` carries the firing symbol —
fixes the single-chart-bound toast), and app lifecycle (`closeEvent` teardown per
D28.5). Extraction order: (1) D27.3 + D27.4 (reconnect routing, stream health —
correctness, needed regardless), (2) D28.1 (pacing off the GUI thread), (3) the session
data-plane cluster, (4) dock-layout controller, (5) remaining clusters — one cluster per
change, offscreen suite green between each.

## [NEW] Pop-out window architecture (D24)

> **Status: DRAFT 2026-10-12 — target architecture.** Requirement ref: D24.

New module `ui/popout_window.py::PopoutChartWindow(QWidget, Qt.Window)`, parented to the
main window (independent top-level window on any monitor; closes with the app).
Layout: `QVBoxLayout`, margins 0; slim header strip (~28px: `SYMBOL · timeframe · mode`
+ close button); body is `ChartPanel(editable=False)` expanding to fill. Native OS frame
retained (resize/drag); no toolbar row, no docks, no status bar.

`ChartPanel` gains a read-only mode via constructor/behaviour flag (not a subclass, not
a fork of the overlay code): drawing tools, alarm-placement mode, and
studies/timeframe/mode controls are disabled — **interaction only**. `drawing_overlay`
and `alarm_overlay` still render everything; crosshair/zoom/pan work normally.
Timeframe/mode/extended-hours are frozen at the pop-out snapshot (A56).

Data flow per pop-out: `registry.get_or_create(symbol)` → build `ChartPanel(editable=False)`
→ set symbol/timeframe/mode/ext-hours → `session.attach(view)` (initial full sync) →
show. Cap: `MAX_POPOUTS = 10` (`config/settings.py`); the toolbar "Pop out" action
(button + hotkey) is disabled at the cap with a status-bar message; closing a pop-out
detaches its view and frees the slot. Same symbol in N pop-outs = one session, one
subscription (A62); main chart may show the same ticker (primary view joins the session).

Performance contract (D28.4, required before pop-outs ship): bars stored once per
`(symbol, timeframe)` and shared; no full chart rebuild on any tick (static-history +
live-bar render layers); one IBKR tick per symbol → one fan-out pass over that
symbol's views; no per-view polling timers.

**[NEW] D24.9 — pop-out restore across restarts (owner-confirmed 2026-10-12).**
Narrow amendment to the D24 "no DB schema changes" constraint: one **additive**
`popouts` table only — `(symbol TEXT, timeframe TEXT, mode TEXT, ext_hours INTEGER,
geometry BLOB, updated_at INTEGER)` — no changes to existing tables (consistent with
the repo's additive-migration precedent; `schema_version` tracking per m-5 if this
is the first structural migration). Write path: `MainWindow` (or the session
registry owner) upserts the pop-out row on open, close, and geometry change
(debounced `moveEvent`/`resizeEvent`, not per-pixel). Read path: on app launch after
TWS connects, rows are re-created as pop-out windows in z-order; each attaches to its
session lazily (cache-first render, then live). If a row's symbol no longer resolves
(contract lookup fails), the pop-out is skipped with a status-bar note — never a
blocking error. Deleting all rows when the user closes every pop-out keeps the table
empty-by-default. QSettings is the documented fallback if the owner rejects the table.

## [NEW] Headless alarm monitor (D25)

> **Status: DRAFT 2026-10-12 — target architecture.** Requirement ref: D25.

New module `services/alarm_monitor.py::AlarmMonitor`, owned by `MainWindow` and wired to
the session registry. It maintains the **monitored set** via a new
`AlarmStore.symbols_with_active_alarms()` query
(`SELECT DISTINCT symbol FROM alarms WHERE active=1 AND triggered=0`).

For each monitored symbol with no open view, the monitor ensures a **headless
`TickerSession`** (`views == 0`, `monitored == True`): one `reqRealTimeBars` (5-sec),
aggregated by the existing `BarAggregator` at fixed `"1m"`, evaluated on every 5-sec
push with `evaluate_alarms(prev_price, curr_price, alarms)` (A58: 1-minute tracking
granularity, second-level firing). `prev_price` seeds from `BarCache.get_bars(symbol,
"1m")` last close, else the first tick seeds with no evaluation until the second tick;
**zero historical requests** from headless sessions (A60). Headless sessions are
ordinary sessions — no parallel data path.

Lifecycle: the monitor reconciles (diff desired vs actual) on TWS connect, alarm
add/update/delete/rearm/trigger, and view attach/detach. Trigger path is identical to
D24 (`mark_triggered` → `alarm_triggered` → exactly-once toast + sound from
`MainWindow`, A57). A symbol gaining a view keeps its session (view-backed, no
duplicate); last live alarm deleted/triggered/deactivated → unmonitored → teardown if
viewless (A61). No phantom trigger when monitoring starts beyond the alarm level (A59).
Pacing guardrail: monitored symbols count against `MAX_REALTIME_BARS_PER_10_MIN = 60`;
overflow → most-recently-active first + status-bar warning naming the unmonitored (A63).

## [NEW] As-built → target delta table (per subsystem)

> **As-built update 2026-10-12 (Phase 1 D26 + Phase 2 D27):** rows whose as-built cell
> starts with **[P1/P2 2026-10-12]** now describe the as-built at `d27-correctness`
> (`69a2313`; Phase 1 merged to main at `5d4daf4`, 779 passed; Phase 2 at 819 passed).
> **As-built update 2026-10-12 (Phase 3: 3a pacing + 3b TickerSession + 3c pop-outs + 3d
> alarm monitor):** rows whose as-built cell starts with **[P3 2026-10-12]** now describe
> the as-built at `phase3-sessions-popouts` (`ba28c08`, 855 passed, unmerged per R52).
> **As-built update 2026-10-13 (Phase 4: 4a historical pacing + 4b D28.4 perf + 4c
> teardown + 4d test hardening):** rows whose as-built cell starts with **[P4 2026-10-13]**
> now describe the as-built at `phase4-pacing-perf-teardown` (`3d12821`, 898 passed,
> unmerged — the AC-D28.4 gate passes, clearing Phase 3's merge per R52).
> Where a target is now implemented, the Target cell is marked **[NOW AS-BUILT]**;
> the one remaining still-target item (scroll-back paging) is an open follow-up, not
> as-built. D1–D23 history above is untouched.

| Subsystem | As-built (D1–D23) | Target (D24/D25/D28) | Requirement |
|---|---|---|---|
| Chart data ownership | **[P3 2026-10-12]** `ui/ticker_session.py::TickerSession(QObject)` keyed by uppercase symbol; `MainWindow` holds `_sessions: dict[str, TickerSession]` registry. Moved in 4 clusters (data plane → history wave → studies → drawings/groups); per-timeframe `BarAggregator`s, per-timeframe bars capped at `SESSION_BAR_CAP=5000` (`config/settings.py:40`). | **[NOW AS-BUILT]** `TickerSession` per symbol; registry on `MainWindow` | D28.2 |
| Bar routing | **[P3 2026-10-12]** `_on_realtime_bar` / `_on_historical_bar` / `_on_historical_data_end` / `_on_error` route by `_req_to_session: dict[int, TickerSession]`, maintained at subscribe time. `load_chart(symbol, timeframe, extended_hours)` is parameterised (no toolbar reads). Dead `_pending_brackets` and `_current_req_id` deleted. | **[NOW AS-BUILT]** `reqId → TickerSession` routing table | D28.2, D27.3 |
| Reconnect | **[P1/P2 2026-10-12]** `_do_reconnect` re-issues the real `connect()` (host/port/clientId stored on the client, D27.3); `SubscriptionManager` rewritten as a reqId-keyed registry with rebind; chart/DOM/watchlist subs are type-tagged at subscribe time and `_replay_subscriptions` replays RT_BARS+DEPTH on reconnect. | `self.connect(host, port, clientId)`; every live sub registered with type tags; replay rebinds reqIds to sessions | D27.3 |
| Alarm evaluation | **[P3 2026-10-12]** Per-session evaluation (DEC-1): the session runs `evaluate_alarms` on every aggregated bar for its own symbol, regardless of which ticker the main chart shows. `alarm_triggered` carries the firing symbol; toast + sound are window-global and fire exactly once per trigger event. | **[NOW AS-BUILT]** Session evaluates its own symbol every aggregated bar; headless sessions evaluate with zero views | D24, D25 |
| Alarm previous-price | **[P1/P2 2026-10-12]** Fixed by D27.1: `_last_chart_price` never moves backward (`_rt_seen` flag set only on live bars for the current reqId); forming bar re-applied after finalize via `update_last_bar`. No phantom triggers on backfill finalize. | Never moves backward; forming bar re-applied after finalize | D27.1 |
| Studies | **[P3 2026-10-12]** Studies config + `_StudyCache` moved into `TickerSession` (3b-3); fan-out to attached views via `studies_changed`. Main chart remains the sole writer. **[P4 2026-10-13]** Cache now actually **read** (4b): `ChartPanel._compute_study_values` takes the incremental path on exact match (fingerprint `n_bars`/`last_ts`) — shifts cached arrays and computes only the new candle via exact-match incremental `sma/ema/vwap/bollinger/rsi/macd_update` fns in `services/indicator_service.py` (tail-verified against batch); `calculate_*` no longer runs per candle. `update_chart` invalidates the study cache on wholesale bar replacement (wholesale backfills could fingerprint-match by coincidence). ICT capped to trailing `ICT_TRAILING_BARS = 500`. | **[NOW AS-BUILT]** Cache in session; cache actually read (shift arrays, compute only new bar) | D24, D28.4 |
| Subscriptions | **[P3 2026-10-12]** `SubscriptionManager` extended with per-symbol refcounting (3c): first holder (view or monitor) subscribes, last holder releases — one IBKR realtime subscription per symbol regardless of window count. | **[NOW AS-BUILT]** Refcounted per symbol; first holder subscribes, last releases | D24 (A62) |
| Pacing | **[P3 2026-10-12]** `throttle_realtime()` (which could `time.sleep` up to 10 min, incl. the order path) replaced by pure `realtime_wait_seconds()` / `realtime_wait_for_slots()` + `record_realtime_slot()` (`ibkr/pacing.py`); `PacingExceeded(wait_seconds)` raised instead of sleeping; all callers defer via `QTimer.singleShot` with a persistent "pacing-limited, retrying in Ns" status. Orders removed from the realtime throttle — new `OrderRateLimiter` token bucket (5/s, burst 5); both order paths defer via singleShot with validation re-run. Short ≤20ms sleeps remain on historical/mkt-data/contract-details paths (pre-existing, out of scope). | **[NOW AS-BUILT]** Never sleeps on GUI thread; deferred retry + status; orders have their own limiter | D28.1 |
| Historical pacing | **[P4 2026-10-13]** `PacingManager` rolling 600s window for `reqHistoricalData` (`ibkr/pacing.py`): `historical_wait_seconds()` pure/non-blocking (expiry at oldest-slot + 600s); `record_historical_slot()` called in `MarketDataManager.req_historical_data` only after the request is issued. `MAX_HISTORICAL_PER_600S = 60` (~60 chunks/wave). `TickerSession.queue_wave_plans` / `_issue_wave_chunks` issues up to 60; `PacingExceeded` → `_schedule_wave_continuation` (singleShot `_wave_continue_timer` + watchdog re-arm); the wave finalises only when nothing is in flight AND nothing queued. IBKR error 162 retried exactly once (`_retried_plans`, re-queued front, newest-first) before finalising short; non-162 errors fail fast. `prime_aggregator` fails open. | **[NOW AS-BUILT]** Rolling 600s window (non-blocking); ~60 chunks/wave cap; retry-once on 162 | D28.3 |
| Rendering | **[P3 2026-10-12]** Interim smoke gate only (3c): gate revised ≤2× → ≤5× the 3b tick-burst baseline (measured 3.6×; linear scaling by construction; Gate 2 zero full QPicture regens per tick holds). **[P4 2026-10-13]** Render split (4b): forming ticks go through `_refresh_live_bar()` — only the 1-bar live layers (`live_candle`, `live_volume`) redraw; the static-history `CandlestickItem` QPicture is untouched unless bar-count/spacing changes. `regen_count` counters on both items. Candle half-width cached per full rebuild (`_compute_candle_half_width` — no O(n log n) sort on ticks). Bisection over cached `_plot_xs` / `_plot_vols` for crosshair, volume ceiling, and the pan/zoom frame path. `TimeCollapseMap.extend(ts)` tail step instead of full rebuild; head-prune path rebuilds the map. `BarCache.prune(symbol, timeframe, keep=5000)` on wave finalize; `ChartPanel._bars` pruned at `SESSION_BAR_CAP` on the new-candle path (prune path also rebuilds the collapse map + invalidates the study cache). **Binding gate (AC-D28.4 / R52):** main + 9 pop-outs × 500 bars, 99 forming ticks → ~4ms/tick (bound ≤50ms), 0 static full regens, exactly one live refresh per tick per chart; one new candle → exactly 10 static regens (one per panel); every panel's `_bars` bounded at `SESSION_BAR_CAP`. | **[NOW AS-BUILT]** Static-history + live-bar layers; bisection over cached display-x; incremental collapse tails; bounded `_bars` (~5k) + cache retention | D28.4 |
| Stream health | **[P3 2026-10-12]** `StreamHealth` migrated from `MainWindow` into `TickerSession` (3b) as the 2.4 ownership seam designed; per-session state + persistent indicator + backoff retry 5→60s (`reset_backoff` flag). | **[NOW AS-BUILT]** Per-session state + persistent indicator + backoff retry | D27.4 |
| Order path | **[P1/P2 2026-10-12]** D26 landed (merged to main `5d4daf4`, review APPROVED): bracket children take the opposite side; `IdManager.reserve(3)` for brackets (thread-safe, contiguous); SL/TP dialog honestly labelled as not placing orders (real legs = follow-up batch); MKT buttons fixed (qty from spinbox, qty≤0 refused); `LIVE_PORT=7496` + `check_live_port()` fail-fast in `main()`; badge derived from verified port + `AccountType`; explicit Buy/Sell selector; pure `validate_order()` gate (`ibkr/validation.py`) at the top of `_place_order` — qty>0, notional ≤ `MAX_ORDER_NOTIONAL=25000`, price>0 per type, bracket geometry, side correctness, rejections surface in UI; kill switch = `reqGlobalCancel()` + per-ID `cancelOrder` for every non-terminal registry entry (all three bracket legs registered at transmit time), wired into `_on_portfolio_flatten_all`; `_on_error` routes registry reqIds to Rejected/Cancelled; 201/103/1100/502/503/509 fatal; entry blocked while disconnected. Drive-bys fixed: `UserOrder` imported directly (was `order_registry.UserOrder` AttributeError — no order could ever transmit); `QHBoxLayout` import added to the SL/TP dialog (it could never open). **[P3 2026-10-12]** D28.1: orders removed from the realtime throttle — `OrderRateLimiter` token bucket (5/s, burst 5, `ibkr/pacing.py`); when empty, `_place_order` defers via `QTimer.singleShot` with a "pacing-limited, retrying…" status and re-runs validation on retry — never blocks, never silently dropped. | Children opposite-side; `reserve(3)`; real legs or honest labelling; qty from input; fail-fast on port; Buy/Sell selector; `validate_order()` gate; `reqGlobalCancel` kill switch; registry updated on reject | D26 |
| Study overlays | **[P1/P2 2026-10-12]** Fixed by D27.2: overlays map bar indices → display-x via the collapse map (`set_collapse_map`/`_index_to_x`); MACD histogram uses `xs[i]`; overlay tests assert x-in-view-range. | All plot in display-x; overlay tests assert x-in-view-range | D27.2 |
| Daily/4h aggregation | **[P1/P2 2026-10-12]** Fixed by D27.8: `BarAggregator.period_start()` floors in `America/New_York` wall time (4h grid 00/04/08/12/16/20 ET); VWAP resets on the ET date change. Caveat flagged in code: IBKR's own 4h anchor unverified vs live TWS — revisit on live comparison. | `America/New_York` wall-time anchoring; VWAP resets on ET date change | D27.8 |
| Backfill gaps | **[P1/P2 2026-10-12]** D27.7: gap-based bar-period-granularity detection for the trailing 5 trading days (`TRAILING_BAR_GRANULARITY_DAYS`); `load_chart` passes the ext-hours toggle. D27.9: aggregator priming — trailing 5-sec history (bounded 7200s) replayed through the fresh `BarAggregator` before live attach, fail-open + 15s backstop. | Bar-period granularity for trailing N days / per-chunk completion | D27.7 |
| Positions/account | **[P1/P2 2026-10-12]** D27.5/D27.6: central `_symbol_last_prices` map fed by chart bars + watchlist ticks; positions use their own symbol's price, 0.0 = honest unknown (no fabricated P&L); `reqPositions` + `reqAccountSummary` issued on connect, with an "unavailable" panel state on disconnect; `positions` table gained `CREATE UNIQUE INDEX IF NOT EXISTS (symbol, con_id)` via additive `_migrate_schema`. | `symbol → last_price` map; subscribe on connect; "unavailable" state | D27.5, D27.6 |
| Teardown | **[P4 2026-10-13]** (4c) `_closing` flag — all four IBKR slots early-return. Explicit `closeEvent` order: persist prefs (watchlist dock width, re-clamped) → cancel in-flight contract lookups → disarm retry timers (`_rt_retry_timer`; per-session teardown cancels RT + wave, disarms the watchdog, stops the wave-continue timer, advances generation) → cancel depth + all RT subscriptions → `disconnect()` → join the `ibkr-reader` thread with a 5s timeout (`READER_JOIN_TIMEOUT_S`, close never hangs on a wedged socket read) → clear UI. `closeEvent` idempotent (second close is a no-op). Pop-outs are Qt children destroyed with the parent. | **[NOW AS-BUILT]** `_closing` flag; explicit order; thread joined with timeout | D28.5 |
| Drawings | **[P1/P2 2026-10-12]** D27.10: `DrawingStore.update_drawing` persists colour/label/group_id (`None` = unchanged, never clobbered); the `updated` signal carries `(id, payload, color)` from all emitters; colour edits survive reload. **[P3 2026-10-12]** Single-writer invariant now enforced: main chart is the sole writer of drawings/alarms/studies; pop-outs render overlays read-only — `ChartPanel(editable=False)` gates drag/click/menu/Delete at the overlay level (`AlarmOverlay`/`DrawingOverlay` `editable` flag; fix `8ef0342` also closed a `DrawingOverlay` drag/settings hole the review missed). Drawings/groups live in the session; `drawings_changed` fans out to views. | **[NOW AS-BUILT]** Colour/label/group persisted; single-writer invariant enforced (A64) | D27.10, D24 |
| Pop-out windows | — (did not exist) | **[NOW AS-BUILT]** `ui/popout_window.py::PopoutChartWindow` (28px header `SYMBOL · timeframe · mode` + close, `ChartPanel(editable=False)`); timeframe/mode/ext-hours frozen at creation; `MAX_POPOUTS = 10` (`config/settings.py:37`), disabled at cap with status message; toolbar "Pop out" action + `Ctrl/Cmd+P`; always-on-top default off with per-window toggle (header context menu). | D24 |
| Pop-out persistence | Pop-outs are session-only (D24 as drafted) | **[NOW AS-BUILT]** Additive `popouts` table + `data/popout_store.py`; upsert on open/close and on 500ms-debounced move/resize end; lazy cache-first restore after connect, with dedup against already-open pop-outs on reconnect (`282aae5`); unresolvable symbols skipped with a non-blocking note | D24.9 |
| Headless alarm monitor | — (did not exist) | **[NOW AS-BUILT]** `services/alarm_monitor.py::AlarmMonitor` (owned by `MainWindow`, wired to the session registry) + `AlarmStore.symbols_with_active_alarms()` (`SELECT DISTINCT symbol FROM alarms WHERE active=1 AND triggered=0`); headless sessions are ordinary `TickerSession`s (`views == 0`, `monitored == True`) with one 5-sec RT subscription, `BarAggregator("1m")`, per-push evaluation; `prev_price` seeded from the 1m cache else first-tick-no-eval (no phantom trigger); **zero history requests**; singleShot retry on pacing exhaustion; detach→headless promotion via `on_session_detached` (a duplicate `detach_view` def that shadowed the notify path was removed, `8383d49`) | D25 |
| Test hardening | **[P4 2026-10-13]** (4d) T-1: alarm E2E assertions verified-not-duplicated (the four assertions live in `test_d24_alarm_full_chain.py` — no second alarm-chain test). T-2: close-path contract reconstruction for stock/option/future with correct IBKR secType vocabulary (`OPT`/`FUT`, not `OPTION`/`FUTURE`) — `ui/main_window.py` close-order path fixed to emit them. T-4: `DrawingStore` → overlay round-trip per drawing kind. T-5: `IdManager` behavioural + concurrency tests. Deleted 3 doc-asserting tests + the phantom `validate_sltp` helper; autouse `_isolate_test_db` fixture makes every test DB-hermetic. Open, not as-built: `contract.class_` is never populated (`_on_position_update` always stores `"stock"` — option/future close unreachable via the real position path; fix = derive from `contract.secType`, own commit). | **[NOW AS-BUILT]** Close-path contracts (OPT/FUT); drawing round-trip; id_manager tests; doc-asserting/phantom tests removed; DB hermeticity | D28.6 |

### Implementation sequencing (target increments)

At the architecture level the sequence is: **(1)** D26 P0 order-path safety (small,
independent, blocks all live use); **(2)** D27.1 + D27.2 (phantom alarms, invisible
overlays — small, high-ROI); **(3)** D27.3 + D27.4 + D28.1 (reconnect routing, stream
health, pacing off the GUI thread); **(4)** D28.2 session extraction (the structural
keystone — unblocks D24/D25); **(5)** D28.3–D28.5 (historical pacing, perf, teardown);
**(6)** D24 pop-outs + D25 alarm monitor on the session substrate; **(7)** D28.6 test
hardening throughout. D1–D23 stay frozen; each step keeps the offscreen suite green.

## D36 increment — footprint charts (as-built 2026-10-13, Code Reviewer APPROVED)

> **Increment scope.** A **new-feature** increment on the built D1–D35 system: footprint charts
> (bid×ask volume-at-price), the P0 item of the D36–D40 program. Built on `feat/d36-footprint` @
> `89fe152` (not pushed, not merged); 927 tests green (898 baseline + 29 new). D1–D35 not reopened.

### Codebase Summary (existing repository — D36 surface)

The D36 code lives in four new modules plus additive changes to existing ones:

- **New `[new]`** `ibkr/tick_history.py::TickHistoryManager` — backward-paging `reqHistoricalTicks`
  client (1000-tick windows, `BID_ASK` + `TRADES`); pacing-counted via `pacing_manager`; never sleeps;
  issues zero `reqTickByTickData`.
- **New `[new]`** `services/footprint_service.py::FootprintService` — per-symbol aggregation owned by
  `TickerSession`; per-level `{bidVol, askVol, delta}` buckets + per-level trade volume/trade count;
  bounded waves, viewport-newest-first, lazy-fill, structural loading states.
- **New `[new]`** `data/footprint_cache.py` — SQLite cache (additive `footprint_cache` table in
  `data/db.py`), one compressed JSON blob per (resolved contract, date, timeframe).
- **New `[new]`** `ui/footprint_item.py` — pyqtgraph render item (classic bars + heatmap shading).
- **`[new/changed]`** `ibkr/bridge.py` (+3 signals), **`[new/changed]`** `ibkr/client.py` (3 overrides +
  10.51.1 signature fixes), **`[new/changed]`** `ibkr/contracts.py` (`INDEX_PROXY`,
  `resolve_footprint_contract`, `footprint_cache_key`), **`[new/changed]`**
  `ui/ticker_session.py` (service ownership, wave pump, forming timer, disconnect/reconnect hooks),
  **`[new/changed]`** `ui/chart_panel.py` (toggle wiring, throttled viewport sync),
  **`[new/changed]`** `ui/main_window.py` (toolbar toggle, `_on_order_status`/`_on_mkt_depth` arity).

### Tech Stack Decisions (D36 increment)

- **ibapi 10.51.01 alignment (38a.0):** `requirements.txt` pins `ibapi-latest==10.51.1` (plain
  `ibapi==10.51.01` is not on PyPI — verified against the index). Full suite re-run green on the
  aligned version before any D36 code.
- **Signature-drift lesson (binding for future upgrades):** the 38a.0 "re-verify signatures" gate
  caught `EWrapper.error` (now 5-arg) but **missed** `orderStatus` (11th param `mktCapPrice`) and
  `updateMktDepthL2` (8th param `isSmartDepth`) — both would have raised `TypeError` in production
  (reviewer B1/B2). On every future API upgrade, re-verify **ALL** `EWrapper` overrides against the
  installed wheel, not just the plan-named ones.
- **Histogram removal:** `reqHistogramData(tickerId, contract, useRTH, timePeriod)` takes **no date
  parameter** — per-bar histograms are impossible. The planned histogram path was removed from code
  and docs; tick-count metric derives from the same TRADES tick pages as volume.

### System Components (D36 increment)

- **TickHistoryManager** (`ibkr/tick_history.py`): pages **backward** from endDateTime in 1000-tick
  windows until startDateTime is covered or a page returns `done` with no ticks; registers each
  request with `pacing_manager` (historical budget); `PacingExceeded` propagates (no sleep).
  Bridge signals: `historical_ticks_bid_ask`, `historical_ticks_last` (+ error routing).
- **FootprintService** (`services/footprint_service.py`, one per `TickerSession`): buckets BID_ASK ticks
  into the session's bar boundaries → per price level `{bidVol, askVol, delta}`; TRADES ticks →
  per-level trade volume + trade count. Completed-bar backfill runs in **bounded waves (≤60
  requests/wave)** scheduled by `pacing_manager` under the binding priority order
  (D27 reconnect replay > D28 backfill > D36 completed-bar backfill > D36 forming-bar refresh >
  D39 baseline prime); within a wave, the visible viewport's newest bars go first; bars entering
  the viewport trigger bounded lazy-fill. The footprint layer renders per-bar-range states
  (ready | loading | unavailable) and never blocks chart render. Forming-bar refresh is
  incremental and follows the selected metric; disconnect resets wave state (no zombie —
  reviewer A4); dataless completed bars → unavailable (never stuck loading — reviewer A3).
- **Index proxy** (`ibkr/contracts.py`): `INDEX_PROXY = {"SPX": "ES", "NDX": "NQ", "DJI": "YM",
  "RUT": "RTY"}`; `resolve_footprint_contract(symbol)` maps an index to the front-month futures
  contract via the existing `_front_month()` schedule (re-resolved on session start and daily).
  **Cache-key rule (binding):** every footprint cache key and per-contract state uses the RESOLVED
  contract (e.g. `ESZ6`), never the continuous symbol — rolls create new keys, old entries stay
  valid history.
- **Renderer** (`ui/footprint_item.py`, live layer in `ui/chart_panel.py`): **display-style toggle**
  — classic bid×ask bars beside each candle vs heatmap-shaded candles — **× metric selector in
  heatmap mode** (per-level volume vs per-level trade count); classic is volume-only. Completed
  bars are static (0 static-layer regenerations on a 100-tick burst — the D28.4 discipline holds);
  forming-bar updates stay incremental. Works on intraday **and** daily timeframes. Default OFF
  (owner, 2026-10-13) — pacing-expensive feature as opt-in.
- **Session ownership:** `TickerSession` owns the `FootprintService`, the wave pump (`_fp_pump`),
  the forming timer, cache preload/persist, and the new-candle hook; enable/disable/resync are
  session operations. Pop-out adoption is a follow-up (service is shared; only the main chart is
  wired this phase).

### Data Model (D36 increment)

- Additive `footprint_cache(resolved_contract TEXT, date TEXT, timeframe TEXT, blob BLOB,
  PRIMARY KEY(resolved_contract, date, timeframe))` — one zlib-compressed JSON blob per key:
  `{bar_ts: {level: [bid, ask]}}`. Read before any paginated backfill; write on backfill
  completion. **Scope:** only SPX/SPY/QQQ/ES-front/NQ-front (owner decision); all other symbols
  are in-memory only (re-fetch per session).
- In-memory per-level aggregates keyed `(resolved_contract, timeframe)` in the service; per-bar
  job states (ready | loading | unavailable) drive the structural loading UI.

### Integration Points (D36 increment)

- **IBKR:** `reqHistoricalTicks` (BID_ASK + TRADES) only — **zero** `reqTickByTickData` for footprint
  (asserted on the request registry + source call-site scan, AC-D36.3). Tick requests count against
  the rolling 600s historical budget (`pacing_manager` is the single owner).
- **Bridge/client:** 3 new signals + 3 overrides, all additive; `super()` called first; routing by
  reqId (D27 pattern). 10.51.1 fixes: `error()` 5-arg, `orderStatus` 11-arg (`mktCapPrice`),
  `updateMktDepthL2` 8-arg (`isSmartDepth`, carried through for D37's SMART-row disambiguation).
- **Render pipeline:** footprint renders in the chart's live layer beside the Phase 4
  static-history/live-bar split; completed-bar footprint data is static (no per-tick regen).

### Non-Functional Approach (D36 increment)

- **Pacing:** ≤60 requests per backfill wave; `PacingExceeded` + `QTimer.singleShot` deferral;
  forming-bar refresh attempted at most once per 15s per symbol (~1/100s effective at 10 charts
  under the shared budget); skip silently when exhausted.
- **Performance:** AC-D28.4 discipline preserved — 100-tick burst → 0 static-layer regenerations
  attributable to footprint (counter-asserted); per-tick cost stays in the live-bar layer.
- **Test safety:** no test touches live TWS or transmits orders; mocked `ib_client` only. Owner
  rule (binding): **no mock endpoint of any kind in production code** — enforced by
  `test_ac_d36_3_production_tree_has_no_mock_endpoint` and the standing Code Reviewer B.6 grep
  (both PASSED for D36).

### Architecture Risks (D36 increment)

- **Tick-volume cost:** one ES day of BID_ASK ticks ≈ 5k requests ≈ 14h at 60/10min — uncapped
  backfill is prohibited by design (wave cap + viewport prioritization + cache); a typical chart
  open costs ~1–2 waves.
- **API-upgrade drift:** B1/B2 showed signature checks must cover ALL `EWrapper` overrides —
  recorded as a binding upgrade procedure above.
- **No-data honesty:** symbols without tick history show an explicit "no tick data" state; the
  footprint layer never renders an empty chart.

### Implementation sequencing (D36 increment)

38a.0 (ibapi alignment + full-suite green) ran **before** any D36 code as a gate precondition.
D36 items built in plan order 36.1 → 36.5 on `feat/d36-footprint`; reviewer rework (B1–B3,
A1–A5) applied on the same branch; single squashed commit `89fe152`. D37–D40 not started.
