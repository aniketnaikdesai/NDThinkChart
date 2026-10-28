# Architecture — NDThinkChart Stabilization (as-built D1–D15 + ESC revision + post-document rework ESC-013…ESC-021, verified 2026-09-28, 383 passed; increment D16 historical-bar gap backfill, validated 2026-10-02; ESC-023 trading-day calendar correction, validated 2026-10-02; increment D17 + D18 panel-layout / full-screen dock sizing, validated 2026-10-03 — as-built D1–D18 at commit `5bd7c93`, 566 passed; increment D19 toolbar scroll/elide wrapper, validated 2026-10-05; increment D20 toolbar scrollbar lane, validated 2026-10-06 — as-built D1–D19 at commit `4d8952a`; increment D21 (Batch 15) UI repairs, validated 2026-10-06 — as-built D1–D20 at commit `04397d9`; increment D22 in-app watchlist "Add symbol" / "Remove symbol" affordance, validated 2026-10-07 — as-built D1–D21 at commit `286341e`, 673 passed; increment D23 (Batch 17) two D22 post-build quality corrections, validated 2026-10-07 — as-built D1–D23 at commit `031ea99` (D22 baseline 712 passed); Phase 1 (D26) order-path safety as-built 2026-10-12 — merged to `main` at `5d4daf4` (review APPROVED), 779 passed; Phase 2 (D27) correctness sweep as-built 2026-10-12 — `d27-correctness` at `69a2313` (re-review PASSED), 819 passed; Phase 3 (3a pacing off the GUI thread + 3b `TickerSession` keystone + 3c pop-outs/D24.9 + 3d headless alarm monitor) as-built 2026-10-12 — `ba28c08`, 855 passed; Phase 4 (4a rolling 600 s historical pacing + 4b D28.4 render split/study-cache/bisection/retention + 4c explicit teardown + 4d test hardening) as-built 2026-10-13 — `3d12821`, 898 passed; D36 footprint charts as-built 2026-10-13 — `89fe152` (merged at `efffc51`), 927 passed, Code Reviewer APPROVED; D37 microstructure as-built 2026-10-13 — merged to `main` @ `9958891`, 947 passed, APPROVED; D38 events & news as-built 2026-10-13 — merged to `main` @ `8599ce4`, 970 passed, APPROVED; D39 burst alerts + symbol search as-built 2026-10-13 — merged to `main` @ `83f792a`, 1009 passed, APPROVED; D40 TWS daily-lifecycle pause/resume as-built 2026-10-13 — merged to `main` @ `b366b19`, CHANGES REQUIRED → rework → APPROVED, 1020 passed. **All of D1–D40 are built and merged to `main`; as-built at commit `b366b19` (the D40 merge; `origin/main` is now `262ec81`, after `7566860` → `99fb8fa` → `262ec81`).** **Owner decisions 2026-10-14 (Q41–Q45):** D24–D28 are **approved as-built** (the former "DRAFT, owner review required" markers are cleared); the per-run **"gated in TWS" planning gate is retired** (Q42/DEC-4) so D26 is planned against the live-order path with the retained safety behaviour unchanged; pop-out always-on-top defaults **OFF** (`AC-D24.10`/A66, Q43); the D37 depth heatmap defaults **ON** (A67, Q44); and the D36–D40 acceptance criteria are now **authored** in `requirements.md` (Q45/DG46). **Suite figure (re-verified 2026-10-14 on this checkout):** 1,020 collected, **1,020 passed / 0 failed**. The four offscreen D19/D20 toolbar-geometry assertions that previously failed were fixed by `99fb8fa` (the theme font is now declared inside the `#MainToolbar` rule and the D19/D20 `_WIDE_SIZE` fixture is 2,400 → 2,600px); they are **no longer open** (see the Suite-figure provenance note in the Codebase Summary). **Increment D41 (Batch 18) — removal of the D36 footprint + D37 depth/imbalance/auction + the entire Active Trader panel (DOM ladder + order-entry ticket), with the right dock becoming Portfolio-only, validated 2026-10-15 and approved for build (not yet as-built; supersedes the D36/D37 increments and the D18/B2 two-section dock — see `## D41 increment` at the end of this file).** **Increment D42 (Batch 18b) — density-aware candle/volume body width (ESC-042 → ESC-041) + mode-aware intraday history depth and day presence (ESC-038 → ESC-037), validated 2026-10-15 and approved for build (not yet as-built; revises the *unconditional* `AC-D6.4` body floor, the `AC-D7.1` "positive gap" wording, the RTH-only depth default and D28.4's flat 5000-bar bound, each recorded as a supersession — see `## D42 increment` at the end of this file).** **Increment D44 (Batch 19) — the collapsed Watchlist becomes a thin vertical bar that expands to the full panel (OWNER-REQUESTED 2026-10-16), validated 2026-10-16 and approved for build (not yet as-built; it changes the collapsed *appearance* of the existing D21.11 collapse, revises the collapsed-appearance clauses `AC-D21.11.2`/`AC-D21.11.3` and scopes the 150px minimum of `AC-D13.1`/`AC-D17.2` to the **expanded** state, each recorded as a supersession — see `## D44 increment` at the end of this file).**

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

**As-built currency (2026-10-14, `b366b19`).** On top of the D1–D23 record above, this
document now describes the **as-built D24–D40** work merged to `main`: the D24/D25/D28
session/pacing/pop-out/alarm-monitor increment (the `TickerSession` per-symbol keystone,
`ui/popout_window.py`, `services/alarm_monitor.py`, rolling-600 s historical pacing, the
static-history/live-bar render split, and explicit teardown), D26 order-path safety, D27
correctness sweep, D36 footprint charts, D37 microstructure (depth heatmap + auction chip),
D38 events & news, D39 volume-burst alerts + symbol search, and D40 TWS daily-lifecycle
pause/resume. The suite figures quoted per landing commit (383 → 566 → 673 → 712 → 779 →
819 → 855 → 898 → 927 → 947 → 970 → 1009 → **1,020**) are the *recorded green* runs; see
the **Suite-figure provenance** note in the Codebase Summary below.

**Owner decisions 2026-10-14 (Q41–Q45) — no architectural decision changed.** D24–D28 are
**approved as-built** (`requirements.md` now carries them as `as-built / APPROVED
2026-10-14`; no "DRAFT" / "unmerged" / "pending owner review" wording remains in this
document or in `docs/plan.md`). The per-run **"gated in TWS" planning constraint is
retired** (Q42/DEC-4), so D26 is planned/decomposed against the live-order path — the
retained safety behaviour is unchanged (`config/settings.py::check_live_port` fails fast
unless `IBKR_PORT == 7496`; explicit user action per order; confirm dialogs remain; no
automated test transmits an order or connects to live TWS). Pop-out **always-on-top
defaults OFF** (`AC-D24.10`/A66, Q43 — matches
`ui/popout_window.py::PopoutChartWindow._always_on_top`), the D37 depth
heatmap **defaults ON** (A67, Q44 — matches
`ui/chart_panel.py::ChartPanel.depth_heatmap_item` / `::ChartPanel._depth_enabled_ui`), and the
D36–D40 acceptance criteria **now exist** (Q45, resolving DG46 — see the AC citations in
the D36–D40 increment sections below).

**Citation convention — symbol-first (adopted 2026-10-14; formalizes `DG56`, the `+5`-line
drift found after `99fb8fa`).** The rule for every citation in this document:

- **`path::symbol` is the durable form.** Cite a location by its symbol, not its line:
  `ui/main_window.py::MainWindow._open_popout`, `config/settings.py::MAX_POPOUTS`,
  `ui/ticker_session.py::TickerSession.bar_updated`. A symbol, module path, constant or
  behaviour survives any edit above it and is the contract a reader should follow.
- **A bare `file:line` is *indicative only*.** Any edit above a cited line can drift it —
  `99fb8fa` ("apply the theme font to the toolbar") inserted 5 lines into `ui/main_window.py`
  around ~`:190` and invalidated ~10 downstream references in one stroke, and no test or check
  catches it. Where a line number is retained for convenience it appears **after** the symbol,
  in parentheses, as a secondary pointer — never as the sole citation.
- **Historical line numbers are bounded, not renumbered.** Two regions deliberately describe
  code *as it stood at its own validation/planning commit* and keep those numbers as written
  (inventing current numbers for a past state would itself mislead — the audit trail must stay
  honest):

  1. **The frozen D16–D23 increment sections** — D16 additions/changes (`services/backfill_service.py`,
     `services/market_calendar.py` surface); D17+D18; D19; D20; D21; D22; D23 — plus the
     D16/D17/D18/D19 increment paragraphs in the header area above, which cite `ui/main_window.py`,
     `ui/watchlist_panel.py` and `ibkr/market_data.py` at the lines those files had when the
     increment was validated. All three files have grown since (the D22–D40 work, plus `99fb8fa`).
     Stale examples retained under the bound, **not to be re-derived as current**:
     `ui/main_window.py:100–211` / `:217–223` / `:223–234` / `:236–242` (the D19/D20 toolbar and
     central composition; the toolbar now spans ~`:185–345`), `ui/main_window.py:290` (`conn_badge`,
     now `ui/main_window.py::MainWindow.conn_badge`) and `:840–846` (the pop-out cap refusal, now
     `ui/main_window.py::MainWindow._open_popout`), `ui/watchlist_panel.py:682–728` / `:716–719`
     (the D23 `remove_symbol`, now with the D23 `_row_data.pop` fix), and
     `ibkr/market_data.py:78–84` (`MarketDataManager.cancel_contract_details`).
  2. **The "Moved from (as-built)" column** of the D24/D25/D28 session-extraction table
     (§ *The session object*), whose bare `(:537)`-style refs cite the **pre-extraction**
     `MainWindow` as it was when D28.2 was planned, not today's file.

  In both bounded regions the symbol named is the contract; the line number is at-that-commit.
  Every *symbol, module path, constant and behaviour* in them was re-verified against the current
  source (the repository is authoritative) — only the line numbers bind to the past.

- **Current sections carry current citations.** The **D24/D25/D28, D36–D40** increment sections,
  the header/owner-decision block, the Data Model and the Architecture Risks table are
  symbol-first per the rule above; where a line survives there it was checked against the tree
  on 2026-10-14.

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
> **Graph state (as-built `b366b19`, rebuilt 2026-10-14).** The committed graph
> (`graphify-out/graph.json`) now describes the current as-built tree: **4,776 nodes /
> 10,509 edges / 251 communities**, `built_at_commit = b366b19`. The staleness the earlier
> D16 increment carried (a 1,969-node graph with no `market_calendar`/`backfill_service`
> node) is **cleared**. Per the existing-repo rule the summary below is still **validated
> against the current source files** (the repository is authoritative); graphify is used
> for discovery, not as truth.
>
> **Suite-figure provenance (D1–D40).** The header lineage records the *recorded green*
> offscreen-suite count at each landing commit (`383 → 566 → 673 → 712 → 779 → 819 → 855 →
> 898 → 927 → 947 → 970 → 1009 →` **`1,020`**). **Re-verified on this checkout 2026-10-14**
> (repo `.venv` on the pinned `ibapi-latest==10.51.1`):
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` →
> **1,020 passed / 0 failed** (`pytest tests/` collects 1,020). The previous note recorded
> **1,016 passed / 4 failed** — four offscreen toolbar-geometry assertions
> (`tests/test_toolbar_d20.py::test_T62_T02_labels_legible_scrollbar_hidden`,
> `::test_T62_T04_scrollbar_as_needed_in_lane`, `::test_T62_T05_d19_reachability_preserved`
> and `tests/test_toolbar_scroll_d19.py::test_T53_T02_controls_reachable_via_scroll`, which
> assert viewport-vs-toolbar width under the offscreen platform; e.g. 1950 >= 1965) whose
> "everything visible at the wide size" premise the 2,400px fixture no longer satisfied.
> **`99fb8fa` fixed all four** — it declares the theme font inside the `#MainToolbar` rule and
> raises the fixture's `_WIDE_SIZE` to 2,600px. They are **no longer open**; the suite is
> green. (The changelog agrees with the corrected figure: `docs/phase-changelog.md`, Phase D40,
> "Tests: 1020 passing, 0 failing (offscreen)".)
>
> **Pinned-`ibapi` note (version-neutral).** The D23 capability guard remains **required on
> the current pin**: `EClient.cancelContractDetails` is absent both on the
> `9.81.1.post1` that was installed when D23 was validated and on the current
> `ibapi-latest==10.51.1` (10.51.01) — re-verified 2026-10-14
> (`hasattr(EClient, 'cancelContractDetails') is False`).

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
| **D6 wick rendering** | Wick: body-coloured `QPen`, `widthF=1.0`, **`setCosmetic(True)`**, `FlatCap`, drawn **before** the body; body cosmetic 1px outline with data half-width **clamped to ≥4-device-px** via `ViewBox px_per_sec`; `ChartPanel._refresh_candles` applies `vb.setRange(...)` **before** generating the candle picture so the clamp binds on a first auto-range load (ESC-013 ordering contract, audit `D-12`). **The ≥4-device-px clamp is *superseded by D42*** — it becomes **density-aware** and the body is capped at the inter-bar pitch (`gap >= 0` always); see `## D42 increment` (`S13`). | `CandlestickItem` paints into a `QPicture` in data coordinates; non-cosmetic pens scale with the ViewBox and go sub-pixel at high density. Cosmetic pens are device-pixel stable. The clamp reads `px_per_sec` at generation time, hence the generate-after-`setRange` order | Non-cosmetic pens with larger `w` (no pixel ratio); pixel-space drawing without `QPicture` (more invasive, loses caching) |
| **D7 inter-candle gap** | Body half-width `w = median_diff * 0.325` (gap 35%), keep `0.25` single-bar fallback, keep D6 ≥4-device-px minimum; `xRange` padding `-2*bar_w / +8*bar_w` unchanged. **The ≥4-px minimum *and* this row's "positive gap" reading are *superseded by D42*** — the gap is `gap >= 0` (hard) with `gap > 0` whenever `pitch > F`, and the floor yields at `pitch <= F`; see `## D42 increment` (`S13`, supersessions 1–2). | Q19 confirmed “go 35% gap for now” as a modest, testable increase from today’s `0.40` (20% gap); only inter-candle gap grows (~75% more gap) | `0.30` (40% gap, airier); widen `xRange` (adds outer framing, not gap) |
| **D8 volume scale (revises D5; family pinned by RG-002, 2026-09-27)** | Volume `ViewBox` **linear Y** (`setLogMode(y=False)`), `yRange=(0, nice_max)` where `nice_max` is the **smallest member of the single continuous family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` (floor `100`, no fixed ceiling) that is `>= max_vol*1.1`**; `max_vol == 0 → 100`; `y0=0`; ticks `500.0K / 1.0M`, no negatives; bars **price-coloured** (`#34d399` / `#f87171` by `close>=open`). The old fixed list `[10k, …, 10M]` is **retained only as a test fixture** | Current log gives negative ticks and hides the desired `500.0K–2.5M` look; the reference is linear with a dynamic nice max and price-coloured bars (Q20). The pinned family reproduces every confirmed value (`750K`, `1.5M`) and the `10.5M→15M`, `45M→50M`, `50M→75M` cases. `0` lower bound matches “volume cannot go below zero” | Keep log with `0→1.0` floor (rejected); a log/linear toggle (more UI than requested); the fixed list (coarse above 10M, `10k` floor) |
| **D9 volume bar width** | `volume_bars.width = w*2` (same `w` as price post-D7 = 65% of `median_diff`), `y0=0` (the implicit `BarGraphItem` default — `y0` is not supplied), X stays `setXLink`ed; the volume half-width is derived from the **final** view range **after** `vb.setRange` (ESC-020 ordering contract, audit `D-12`). **`AC-D9.1`/`AC-D9.2` are unchanged by D42**, but the shared `w` is now the **capped** half-width from the one shared helper; see `## D42 increment` (`S13`). | Fixed `width=0.6` drifts from the price 35% gap; sharing `w` guarantees vertical alignment including the dense 4px minimum. Deriving `w_vol` after `setRange` is required because the shared ≥4-device-px clamp reads `px_per_sec` at generation time | Fixed `0.6`; `0.9×price` (subtly narrower, not requested) |
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

### Dependency pins — as-built `b366b19` (D36–D40)

The runtime pins below are the as-built state of `requirements.txt`; the per-increment
rationale lives in the D36–D40 Tech-Stack subsections further down.

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| **`[new/changed]` TWS API client (D36, 38a.0)** | `ibapi-latest==10.51.1` (IBKR TWS API **10.51.01**; the PyPI distribution `ibapi-latest` provides the `ibapi` module) | Aligns the client with the installed TWS API revision; the previous pin (`ibapi>=9.81`, resolving to `9.81.1.post1`) predated the tick/history/news `EWrapper` surface D36–D40 need. Plain `ibapi==10.51.01` is **not on PyPI** (verified against the index); `ibapi-latest` is the published dist name. The full suite was re-run green on the aligned version before any D36 code | Stay on `9.81.1.post1` (missing the newer `EWrapper` surface); vendor the wheel (maintenance) |
| **`[new]` Secondary events/news source (D38)** | `yfinance==1.7.0` — **sole** secondary source | Owner-mandated 2026-10-13. It is the largest external dependency (unofficial Yahoo API, no SLA, breaks a few times a year), so the hygiene is binding: **RE-PIN POLICY — re-pin quarterly or whenever Yahoo breaks the library; every re-pin re-runs the full offscreen suite**, plus a SQLite per-symbol 24 h cache (6 h revalidation for events within 7 days), a polite ≥1 s self-throttle and a lazy import. **No other external API anywhere in the tree** | WSH (dropped from D38 entirely by owner decision 2026-10-13); a second vendor feed (rejected) |
| **`[existing]` UI / numerics stack (unchanged)** | Python 3.11+, PyQt6, pyqtgraph, numpy, SQLite | Stabilization/extension run on the existing stack — changing it is a stated non-goal | New charting library or embedded web view |

**Pinned-`ibapi` capability facts the code depends on** (all worked around in-tree, never
assumed away; the 10.51.01 API-surface research behind them — confidence-tagged as
`verified live` / `client-verified` / `mirror` — is recorded in
`docs/ibkr-api-data-inventory.md`, and each fact below was independently re-verified against
the installed wheel):

- **No `EClient.cancelContractDetails`** — not exposed by the pinned API surface, on
  `9.81.1.post1` **or** on the current `ibapi-latest==10.51.1` pin (re-verified 2026-10-14);
  the contract-details cancel is resolved defensively (`getattr(self.client,
  'cancelContractDetails', None)`) and `ContractLookupService`'s local invalidation is the
  safety net (D22/D23). The guard stays required — a version bump does not remove the need.
- **`EWrapper.error` is 5-arg in 10.51** — `(reqId, errorTime, errorCode, errorString,
  advancedOrderRejectJson)`. `IBApiClient.error` is a multi-signature shim tolerant of the
  3-, 4- and 5-arg variants and of `advancedOrderRejectJson` as a keyword (D36/D40).
- **`orderStatus` has an 11th parameter** `mktCapPrice` (carried as an `object`/`Decimal` on
  `IBBridge.order_status`) — missed by the 38a.0 signature gate and caught in review (D36
  B1). `updateMktDepthL2`'s 8th parameter `isSmartDepth` is likewise carried through (B2).
- **`symbolSamples` carries no company name** — 10.51.1's `ContractDescription` has only
  `contract` + `derivativeSecTypes` (D39).
- **`reqHistogramData(tickerId, contract, useRTH, timePeriod)` takes no date parameter** —
  per-bar histograms are impossible; the planned histogram path was dropped (D36 A1).

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

**Additive tables (D24–D39).** On top of the set above, later increments add four tables —
`popouts` (D24.9), `footprint_cache` (D36), `yfinance_events_cache` (D38), `volume_baseline`
(D39) — plus `alarms.kind`/`alarms.params` (D39) and the `positions(symbol, con_id)` unique
index (D27.5). Each is described in its own increment section and recorded in
`docs/phase-changelog.md` (Phase 3 — D24.9; Phase D36 item 36.4; Phase D38 item 38b.1;
Phase D39 item 39.2); none alters an existing table's columns.

*As-built note (line numbers refreshed 2026-10-14; symbol-first per the citation convention above):*
`data/db.py` defines `_init_schema` **once** (`data/db.py::_init_schema`, `:14–157`; the file is
258 lines), followed by `_migrate_schema` (`data/db.py::_migrate_schema`, `:159–179`) and
`_table_columns` (`data/db.py::_table_columns`, `:181`). T26/ESC-001 removed the former shadowed second
definition; `tests/test_db_schema.py` guards the single-definition/schema contract. The schema
has since grown **additively** (still inside that single `_init_schema` / `_migrate_schema`
pair): the D24/D36/D38/D39 tables `popouts`, `footprint_cache`, `yfinance_events_cache` and
`volume_baseline`, plus the D27 `positions(symbol, con_id)` unique index and the D39
`alarms.kind` / `alarms.params` columns. The previously flagged latent hygiene debt
(audit `D-6`) is **resolved** — no behaviour change.

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
| `data/db.py` duplicate `_init_schema` (latent hygiene debt) | — **resolved** | T26/ESC-001 deduplicated it: `_init_schema` is defined once (`data/db.py::_init_schema`, `:14–157`), guarded by `tests/test_db_schema.py` (audit `D-6`) |
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
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` live port 7496 only; numpy; SQLite (`config/paths.get_db_path()`); PyInstaller `.app`; pytest + pytest-qt offscreen | Existing-repo hard constraint; live-order safety retained (`IBKR_PORT == 7496` fail-fast, explicit user action per order, confirm dialogs, no automated test transmits an order) — the per-run "gated at TWS" planning constraint is **retired** (owner decision 2026-10-14, Q42) | Paper mode / new broker / new DB — rejected |
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

> **S3 reconciled by D23 (2026-10-07; version-neutral re-check 2026-10-14).** D22's S3 description of
> `cancel_contract_details(req_id)` as a
> direct `client.cancelContractDetails(...)` call is corrected by the **D23.1** increment: the pinned
> `ibapi` `EClient` exposes **no** `cancelContractDetails` — true of `9.81.1.post1` (the pin at D23
> time) and **still true of the current `ibapi-latest==10.51.1` pin** (re-verified 2026-10-14), so the
> guard is a permanent fact of the pinned surface, not a temporary workaround — and the cancel is a
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
in-code note that the pinned `ibapi` lacks the method (`9.81.1.post1` at D23 time; **re-verified
2026-10-14** — still absent on the current `ibapi-latest==10.51.1` pin, so the guard remains
required), that TWS's own
`contractDetailsEnd`/error ends the wire request, and that `ContractLookupService`'s local
invalidation (bounded QTimer + `cancel_all` on disconnect) is the real safety net — no raised and no
silently-swallowed `AttributeError`. **(D23.2)** `WatchlistPanel.remove_symbol` drops the removed
row's own `_row_data` key, so `set(_row_data.keys()) == set(range(table.rowCount()))` after **any**
removal (first / middle / last / only), and the missing last-row (and/or first/only-row) coverage is
added. Both are additive, behaviour-preserving corrections: no stack change, no schema change, no
new dependency, no live-order-path change, and no reopening of `AC-D22.1`–`AC-D22.9`.

**Validator verification (2026-10-07 — independently checked against the current source, not taken
from the proposal).**
- `.venv` `ibapi` was **9.81.1.post1** at this validation (the pin at the time);
  `hasattr(EClient, 'cancelContractDetails') is False` while
  `hasattr(EClient, 'reqContractDetails') is True`. **The same fact re-verified 2026-10-14 on the
  current pin (`ibapi-latest==10.51.1` / `10.51.01`)** — still `False` — so the D23.1 guard is not
  obsoleted by the D36 dependency alignment. `ibkr/market_data.py:78–84` was exactly
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
- `[existing]` **IBKR via the official `ibapi`** (pinned `9.81.1.post1` at D23 time; now
  `ibapi-latest==10.51.1` per the D36 alignment), **live TWS port 7496 only**:
  `reqMktData`/`cancelMktData` (watchlist ticks), `reqHistoricalData`/`cancelHistoricalData` (chart +
  D16 backfill), `reqMktDepth` (DOM), realtime bars, account/position/order callbacks, and (new in
  D22) `reqContractDetails` / `contractDetails` / `contractDetailsEnd`.
- `[existing]` **SQLite** via `data/db.py` (module singleton `db`), path from
  `config/paths.get_db_path()`.
- `[existing]` **QSettings**, the **Qt signal bus** (`IBBridge`), and the **pyqtgraph** chart scene.

**Verified facts that shape D23 (source-validated 2026-10-07)**
1. **The pinned `ibapi` has no cancel.** `.venv` `ibapi 9.81.1.post1` (the pin at D23 time;
   **still true on the current `10.51.1` pin — re-verified 2026-10-14**);
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
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` (pinned `9.81.1.post1`, since aligned to `ibapi-latest==10.51.1` by D36/38a.0), live TWS port `7496` only; numpy (`>=1.26`); SQLite via `config/paths.get_db_path()`; PyInstaller `.app`; pytest + pytest-qt offscreen (no live TWS) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB / new test framework — rejected |
| S3 *(reconciled)* | **D23.1 — capability-guarded best-effort contract-details cancel** `[new/changed]` | Rewrite `[existing] ibkr/market_data.py::MarketDataManager.cancel_contract_details` to: keep `if req_id is None: return`; resolve `cancel = getattr(self.client, 'cancelContractDetails', None)`; **call it only if present**, inside the existing containment (`try/except Exception: pass`); carry a docstring/comment documenting that (a) the pinned `ibapi` exposes no `EClient.cancelContractDetails` (`9.81.1.post1` at D23 time; **re-verified 2026-10-14 — still absent on the current `ibapi-latest==10.51.1`**), (b) TWS's own `contractDetailsEnd`/error ends the wire request, and (c) `ContractLookupService`'s local invalidation (bounded 5s QTimer + `cancel_all` on disconnect) is the real safety net. This **reconciles D22 architecture row `S3`** (the request path is unchanged; only the cancel is corrected) and **supersedes the task-level `AC-D22.2.3`** wire-cancel mandate (`AC-D23.1.1`–`AC-D23.1.4`) | `getattr`-guard makes the call **capability-detected**: correct on every pinned dep so far (no-op, no exception) and forward-correct if a future `ibapi` adds the method (called once). Keeping the containment preserves the method's existing "never raises" contract (`AC-D23.1.3`), and the documentation makes the no-op **intentional and discoverable** rather than a swallowed `AttributeError`. It also matches the ESC-030 suggested direction exactly | (i) **Leave as-is** — silently swallowed `AttributeError`; dishonest and non-forward-correct (rejected). (ii) **Delete the call + the method** — removes a public-shaped method the D22 architecture names, loses forward-compat, and cannot be asserted (rejected). (iii) **Drop the `try/except` and let it raise** — breaks the established containment contract and could surface on a reader/UI path (rejected). (iv) **Attempt a real wire cancel some other way** — no such API exists on the pinned dep (rejected) |
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

## D24 / D25 / D28 increment — `TickerSession` per-symbol model, pop-out windows, headless alarm monitor (as-built, merged to `main`)

> **Status: AS-BUILT 2026-10-12/13 — merged to `main`; the D1–D23 as-built record above is unchanged.**
> **[OWNER-APPROVED 2026-10-14 (Q41).]** D24–D28 are approved as-built; the former "DRAFT / owner
> review required" status is cleared. Owner resolutions carried here: **DEC-1** (per-session alarm
> evaluation — X's alarms fire while viewing Y, and with zero X views open, is the intended behaviour),
> **DEC-2** (D25 is event-driven per A58), **DEC-3** (`AC-D24.9` persists the pop-out set; timeframe/
> mode frozen at creation per A56), **DEC-4 → resolved by Q42** (the "gated in TWS" planning gate is
> retired; D26 is planned against the live-order path — the safety behaviour in the Non-Functional /
> Security notes is unchanged), and **Q43** (pop-out always-on-top defaults OFF, `AC-D24.10`/A66).
> **Requirement-vs-code verification (Q41/DG53)** corrected three D24 statements in the requirement
> text; the same corrections are applied here — the session emits **`bar_updated` +
> `bars_refreshed`** (not a single `bars_updated`), there is **no per-pop-out "connecting"
> indicator** (only the main window's `conn_badge`), and the 10-pop-out cap **refuses the 11th with a
> status-bar message** rather than `setEnabled(False)`-ing the affordance. D29–D35 are intentionally
> unassigned (numbering gap; DG50) — nothing in D29–D35 was ever specified.
> **[P3 2026-10-12]** D28.1 pacing off the GUI thread (3a), the `TickerSession` per-symbol
> model with session registry and reqId routing (3b), pop-out chart windows with read-only
> overlays and `AC-D24.9` restore (3c), and the headless `AlarmMonitor` (3d) — branch
> `phase3-sessions-popouts` at `ba28c08`, 855 passed.
> **[P4 2026-10-13]** rolling 600 s non-blocking historical pacing (D28.3, 4a),
> static-history + live-bar render layers with the study cache actually read (D28.4, 4b),
> and explicit teardown with the reader-thread join (D28.5, 4c) — branch
> `phase4-pacing-perf-teardown` at `3d12821`, 898 passed (the AC-D28.4 10-chart gate passes).
> **[MERGED 2026-10-13]** Phases 3 and 4 are both ancestors of `main` @ `b366b19`; the design
> prose below now describes **implemented code** for the session/pacing/pop-out/monitor parts.
> Requirement refs: D24, D25, D28.2–D28.6.
>
> **New/changed modules this increment:** `[new] ui/ticker_session.py::TickerSession`,
> `[new] ui/popout_window.py::PopoutChartWindow`, `[new] data/popout_store.py`,
> `[new] ui/event_marker_overlay.py` (D38), `[new] services/alarm_monitor.py::AlarmMonitor`,
> `[new] ibkr/stream_health.py`, `[new] ibkr/pacing.py` (rolling-600 s `PacingManager` +
> `OrderRateLimiter`), `[new/changed] ibkr/subscription_manager.py` (type-tagged replay),
> `[new/changed] ibkr/validation.py`, `[new/changed] services/time_collapse_service.py`,
> `[new/changed] ui/chart_panel.py`, `[new/changed] ui/main_window.py`.
>
> **Open follow-ups, not as-built:** scroll-back paging, `contract.class_` derivation from
> `contract.secType`, post-teardown `singleShot` retry cleanup.

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
**`bar_updated(Bar, is_new_candle)` (incremental tick) and `bars_refreshed(timeframe, bars)`
(full series replace)** — verified against `ui/ticker_session.py::TickerSession.bar_updated` and
`::TickerSession.bars_refreshed`, which emit **two**
bar signals and not a single `bars_updated` — plus `studies_changed`,
`drawings_changed`, `alarms_changed`, `alarm_triggered(symbol, alarms)`,
`stream_health_changed`, and the D36–D38 feature signals (`footprint_updated`,
`depth_state_changed`, `auction_updated`, `dividend_updated`, `events_updated`). Views
attach/detach (`session.attach_view(view)` /
`session.detach_view(view)`); attach performs an initial full sync
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

## Pop-out window architecture (D24) — as-built

> **Status: AS-BUILT 2026-10-12 — merged to `main` (Phase 3, `3e81f66`/`ba28c08`; ancestors
> of `b366b19`).** Requirement ref: D24. `ui/popout_window.py::PopoutChartWindow` +
> `data/popout_store.py` (`AC-D24.9` persistence) are implemented as described below.

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
→ set symbol/timeframe/mode/ext-hours → `session.attach_view(view)` (initial full sync) →
show. Cap: `config/settings.py::MAX_POPOUTS` (= 10); at the cap the 11th pop-out is
**refused with a status-bar message** ("Pop-out limit reached (10). Close one to open
another." — `ui/main_window.py::MainWindow._open_popout`). **Verified against the shipped code (2026-10-14,
DG53):** the affordance is **not** `setEnabled(False)`-ed — the requirement's earlier
"disabled at the cap" wording is narrower than the code, and the as-built behaviour is the
status-bar refusal. Closing a pop-out
detaches its view and frees the slot. Same symbol in N pop-outs = one session, one
subscription (A62); main chart may show the same ticker (primary view joins the session).
**Opened while disconnected:** cached bars render immediately from the session cache and the
subscription starts on connect via the existing reconnect path — there is **no per-pop-out
"connecting" indicator** (the only connecting affordance is the main window's
`ui/main_window.py::MainWindow.conn_badge`); a per-window indicator would be a new request.
**Always-on-top:** pop-outs are standard windows by default
(`ui/popout_window.py::PopoutChartWindow._always_on_top` = `False`); the user may enable it per
window via the header context menu ("Always on top"), which applies `Qt.WindowStaysOnTopHint` at
runtime (`ui/popout_window.py::PopoutChartWindow._toggle_always_on_top`) — **owner-confirmed
2026-10-14, Q43 / `AC-D24.10` / A66**.

Performance contract (D28.4, required before pop-outs ship): bars stored once per
`(symbol, timeframe)` and shared; no full chart rebuild on any tick (static-history +
live-bar render layers); one IBKR tick per symbol → one fan-out pass over that
symbol's views; no per-view polling timers.

**AC-D24.9 — pop-out restore across restarts (as-built; owner-confirmed 2026-10-12; reconciled 2026-10-14).**
Narrow amendment to the D24 "no DB schema changes" constraint: one **additive**
`popouts` table only — `(symbol TEXT, timeframe TEXT, mode TEXT, ext_hours INTEGER,
geometry TEXT, updated_at INTEGER)` — no changes to existing tables (consistent with
the repo's additive-migration precedent; `schema_version` tracking per m-5 if this
is the first structural migration). Write path: `MainWindow` (or the session
registry owner) upserts the pop-out row on open, close, and geometry change
(debounced `moveEvent`/`resizeEvent`, not per-pixel). Read path: on app launch after
TWS connects, rows are re-created as pop-out windows in z-order; each attaches to its
session lazily (cache-first render, then live). If a row's symbol no longer resolves
(contract lookup fails), the pop-out is skipped with a status-bar note — never a
blocking error. Deleting all rows when the user closes every pop-out keeps the table
empty-by-default. QSettings is the documented fallback if the owner rejects the table.

## Headless alarm monitor (D25) — as-built

> **Status: AS-BUILT 2026-10-12 — merged to `main` (Phase 3, `ce1ef41`/`ba28c08`; ancestors
> of `b366b19`).** Requirement ref: D25. `services/alarm_monitor.py::AlarmMonitor` is
> implemented as described below.

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

## As-built → target delta table (per subsystem) — D1–D23 as-built vs D24/D25/D28, now all as-built

> **As-built update 2026-10-12 (Phase 1 D26 + Phase 2 D27):** rows whose as-built cell
> starts with **[P1/P2 2026-10-12]** describe the as-built at `d27-correctness`
> (`69a2313`; Phase 1 merged to `main` at `5d4daf4`, 779 passed; Phase 2 at 819 passed).
> **As-built update 2026-10-12 (Phase 3):** rows whose as-built cell starts with
> **[P3 2026-10-12]** describe the as-built at `ba28c08` (855 passed).
> **As-built update 2026-10-13 (Phase 4):** rows whose as-built cell starts with
> **[P4 2026-10-13]** describe the as-built at `3d12821` (898 passed; the AC-D28.4 gate passes).
> **[MERGED 2026-10-13]** Phases 3 and 4 are ancestors of `main` @ `b366b19` — every row below
> is now **as-built and merged**; where a target is implemented the Target cell is marked
> **[NOW AS-BUILT]**. The one remaining still-target item (scroll-back paging) is an open
> follow-up, not as-built. D1–D23 history above is untouched.

| Subsystem | As-built (D1–D23) | Target (D24/D25/D28) | Requirement |
|---|---|---|---|
| Chart data ownership | **[P3 2026-10-12]** `ui/ticker_session.py::TickerSession(QObject)` keyed by uppercase symbol; `MainWindow` holds `_sessions: dict[str, TickerSession]` registry. Moved in 4 clusters (data plane → history wave → studies → drawings/groups); per-timeframe `BarAggregator`s, per-timeframe bars capped at `config/settings.py::SESSION_BAR_CAP` (= 5000). **(The flat `SESSION_BAR_CAP` bound is *revised by D42* — the cap becomes floor-aware per `(timeframe, ext_hours)`; see `## D42 increment`, `S18`.)** | **[NOW AS-BUILT]** `TickerSession` per symbol; registry on `MainWindow` | D28.2 |
| Bar routing | **[P3 2026-10-12]** `_on_realtime_bar` / `_on_historical_bar` / `_on_historical_data_end` / `_on_error` route by `_req_to_session: dict[int, TickerSession]`, maintained at subscribe time. `load_chart(symbol, timeframe, extended_hours)` is parameterised (no toolbar reads). Dead `_pending_brackets` and `_current_req_id` deleted. | **[NOW AS-BUILT]** `reqId → TickerSession` routing table | D28.2, D27.3 |
| Reconnect | **[P1/P2 2026-10-12]** `_do_reconnect` re-issues the real `connect()` (host/port/clientId stored on the client, D27.3); `SubscriptionManager` rewritten as a reqId-keyed registry with rebind; chart/DOM/watchlist subs are type-tagged at subscribe time and `_replay_subscriptions` replays RT_BARS+DEPTH on reconnect. | `self.connect(host, port, clientId)`; every live sub registered with type tags; replay rebinds reqIds to sessions | D27.3 |
| Alarm evaluation | **[P3 2026-10-12]** Per-session evaluation (DEC-1): the session runs `evaluate_alarms` on every aggregated bar for its own symbol, regardless of which ticker the main chart shows. `alarm_triggered` carries the firing symbol; toast + sound are window-global and fire exactly once per trigger event. | **[NOW AS-BUILT]** Session evaluates its own symbol every aggregated bar; headless sessions evaluate with zero views | D24, D25 |
| Alarm previous-price | **[P1/P2 2026-10-12]** Fixed by D27.1: `_last_chart_price` never moves backward (`_rt_seen` flag set only on live bars for the current reqId); forming bar re-applied after finalize via `update_last_bar`. No phantom triggers on backfill finalize. | Never moves backward; forming bar re-applied after finalize | D27.1 |
| Studies | **[P3 2026-10-12]** Studies config + `_StudyCache` moved into `TickerSession` (3b-3); fan-out to attached views via `studies_changed`. Main chart remains the sole writer. **[P4 2026-10-13]** Cache now actually **read** (4b): `ChartPanel._compute_study_values` takes the incremental path on exact match (fingerprint `n_bars`/`last_ts`) — shifts cached arrays and computes only the new candle via exact-match incremental `sma/ema/vwap/bollinger/rsi/macd_update` fns in `services/indicator_service.py` (tail-verified against batch); `calculate_*` no longer runs per candle. `update_chart` invalidates the study cache on wholesale bar replacement (wholesale backfills could fingerprint-match by coincidence). ICT capped to trailing `ICT_TRAILING_BARS = 500`. | **[NOW AS-BUILT]** Cache in session; cache actually read (shift arrays, compute only new bar) | D24, D28.4 |
| Subscriptions | **[P3 2026-10-12]** `SubscriptionManager` extended with per-symbol refcounting (3c): first holder (view or monitor) subscribes, last holder releases — one IBKR realtime subscription per symbol regardless of window count. | **[NOW AS-BUILT]** Refcounted per symbol; first holder subscribes, last releases | D24 (A62) |
| Pacing | **[P3 2026-10-12]** `throttle_realtime()` (which could `time.sleep` up to 10 min, incl. the order path) replaced by pure `realtime_wait_seconds()` / `realtime_wait_for_slots()` + `record_realtime_slot()` (`ibkr/pacing.py`); `PacingExceeded(wait_seconds)` raised instead of sleeping; all callers defer via `QTimer.singleShot` with a persistent "pacing-limited, retrying in Ns" status. Orders removed from the realtime throttle — new `OrderRateLimiter` token bucket (5/s, burst 5); both order paths defer via singleShot with validation re-run. Short ≤20ms sleeps remain on historical/mkt-data/contract-details paths (pre-existing, out of scope). | **[NOW AS-BUILT]** Never sleeps on GUI thread; deferred retry + status; orders have their own limiter | D28.1 |
| Historical pacing | **[P4 2026-10-13]** `PacingManager` rolling 600s window for `reqHistoricalData` (`ibkr/pacing.py`): `historical_wait_seconds()` pure/non-blocking (expiry at oldest-slot + 600s); `record_historical_slot()` called in `MarketDataManager.req_historical_data` only after the request is issued. `MAX_HISTORICAL_PER_600S = 60` (~60 chunks/wave). `TickerSession.queue_wave_plans` / `_issue_wave_chunks` issues up to 60; `PacingExceeded` → `_schedule_wave_continuation` (singleShot `_wave_continue_timer` + watchdog re-arm); the wave finalises only when nothing is in flight AND nothing queued. IBKR error 162 retried exactly once (`_retried_plans`, re-queued front, newest-first) before finalising short; non-162 errors fail fast. `prime_aggregator` fails open. | **[NOW AS-BUILT]** Rolling 600s window (non-blocking); ~60 chunks/wave cap; retry-once on 162 | D28.3 |
| Rendering | **[P3 2026-10-12]** Interim smoke gate only (3c): gate revised ≤2× → ≤5× the 3b tick-burst baseline (measured 3.6×; linear scaling by construction; Gate 2 zero full QPicture regens per tick holds). **[P4 2026-10-13]** Render split (4b): forming ticks go through `_refresh_live_bar()` — only the 1-bar live layers (`live_candle`, `live_volume`) redraw; the static-history `CandlestickItem` QPicture is untouched unless bar-count/spacing changes. `regen_count` counters on both items. Candle half-width cached per full rebuild (`_compute_candle_half_width` — no O(n log n) sort on ticks). Bisection over cached `_plot_xs` / `_plot_vols` for crosshair, volume ceiling, and the pan/zoom frame path. `TimeCollapseMap.extend(ts)` tail step instead of full rebuild; head-prune path rebuilds the map. `BarCache.prune(symbol, timeframe, keep=5000)` on wave finalize; `ChartPanel._bars` pruned at `SESSION_BAR_CAP` on the new-candle path (prune path also rebuilds the collapse map + invalidates the study cache). **Binding gate (AC-D28.4 / R52):** main + 9 pop-outs × 500 bars, 99 forming ticks → ~4ms/tick (bound ≤50ms), 0 static full regens, exactly one live refresh per tick per chart; one new candle → exactly 10 static regens (one per panel); every panel's `_bars` bounded at `SESSION_BAR_CAP`. **(Both flat caps — `prune`'s `keep` and `ChartPanel._bars` — are *revised by D42* to the floor-aware budget per `(timeframe, ext_hours)`; the bound stays "the derived budget", and the D28.4 gate is otherwise unchanged. See `## D42 increment`, `S18`.)** | **[NOW AS-BUILT]** Static-history + live-bar layers; bisection over cached display-x; incremental collapse tails; bounded `_bars` (~5k) + cache retention | D28.4 |
| Stream health | **[P3 2026-10-12]** `StreamHealth` (`ibkr/stream_health.py`) migrated from `MainWindow` into `TickerSession` (3b) as the 2.4 ownership seam designed; per-session state + persistent indicator + backoff retry 5→60s (`reset_backoff` flag). | **[NOW AS-BUILT]** Per-session state + persistent indicator + backoff retry | D27.4 |
| Order path | **[P1/P2 2026-10-12]** D26 landed (merged to main `5d4daf4`, review APPROVED): bracket children take the opposite side; `IdManager.reserve(3)` for brackets (thread-safe, contiguous); SL/TP dialog honestly labelled as not placing orders (real legs = follow-up batch); MKT buttons fixed (qty from spinbox, qty≤0 refused); `LIVE_PORT=7496` + `check_live_port()` fail-fast in `main()`; badge derived from verified port + `AccountType`; explicit Buy/Sell selector; pure `validate_order()` gate (`ibkr/validation.py`) at the top of `_place_order` — qty>0, notional ≤ `MAX_ORDER_NOTIONAL=25000`, price>0 per type, bracket geometry, side correctness, rejections surface in UI; kill switch = `reqGlobalCancel()` + per-ID `cancelOrder` for every non-terminal registry entry (all three bracket legs registered at transmit time), wired into `_on_portfolio_flatten_all`; `_on_error` routes registry reqIds to Rejected/Cancelled; 201/103/1100/502/503/509 fatal; entry blocked while disconnected. Drive-bys fixed: `UserOrder` imported directly (was `order_registry.UserOrder` AttributeError — no order could ever transmit); `QHBoxLayout` import added to the SL/TP dialog (it could never open). **[P3 2026-10-12]** D28.1: orders removed from the realtime throttle — `OrderRateLimiter` token bucket (5/s, burst 5, `ibkr/pacing.py`); when empty, `_place_order` defers via `QTimer.singleShot` with a "pacing-limited, retrying…" status and re-runs validation on retry — never blocks, never silently dropped. | Children opposite-side; `reserve(3)`; real legs or honest labelling; qty from input; fail-fast on port; Buy/Sell selector; `validate_order()` gate; `reqGlobalCancel` kill switch; registry updated on reject | D26 |
| Study overlays | **[P1/P2 2026-10-12]** Fixed by D27.2: overlays map bar indices → display-x via the collapse map (`set_collapse_map`/`_index_to_x`); MACD histogram uses `xs[i]`; overlay tests assert x-in-view-range. | All plot in display-x; overlay tests assert x-in-view-range | D27.2 |
| Daily/4h aggregation | **[P1/P2 2026-10-12]** Fixed by D27.8: `BarAggregator.period_start()` floors in `America/New_York` wall time (4h grid 00/04/08/12/16/20 ET); VWAP resets on the ET date change. Caveat flagged in code: IBKR's own 4h anchor unverified vs live TWS — revisit on live comparison. | `America/New_York` wall-time anchoring; VWAP resets on ET date change | D27.8 |
| Backfill gaps | **[P1/P2 2026-10-12]** D27.7: gap-based bar-period-granularity detection for the trailing 5 trading days (`TRAILING_BAR_GRANULARITY_DAYS`); `load_chart` passes the ext-hours toggle. D27.9: aggregator priming — trailing 5-sec history (bounded 7200s) replayed through the fresh `BarAggregator` before live attach, fail-open + 15s backstop. | Bar-period granularity for trailing N days / per-chunk completion | D27.7 |
| Positions/account | **[P1/P2 2026-10-12]** D27.5/D27.6: central `_symbol_last_prices` map fed by chart bars + watchlist ticks; positions use their own symbol's price, 0.0 = honest unknown (no fabricated P&L); `reqPositions` + `reqAccountSummary` issued on connect, with an "unavailable" panel state on disconnect; `positions` table gained `CREATE UNIQUE INDEX IF NOT EXISTS (symbol, con_id)` via additive `_migrate_schema`. | `symbol → last_price` map; subscribe on connect; "unavailable" state | D27.5, D27.6 |
| Teardown | **[P4 2026-10-13]** (4c) `_closing` flag — all four IBKR slots early-return. Explicit `closeEvent` order: persist prefs (watchlist dock width, re-clamped) → cancel in-flight contract lookups → disarm retry timers (`_rt_retry_timer`; per-session teardown cancels RT + wave, disarms the watchdog, stops the wave-continue timer, advances generation) → cancel depth + all RT subscriptions → `disconnect()` → join the `ibkr-reader` thread with a 5s timeout (`READER_JOIN_TIMEOUT_S`, close never hangs on a wedged socket read) → clear UI. `closeEvent` idempotent (second close is a no-op). Pop-outs are Qt children destroyed with the parent. | **[NOW AS-BUILT]** `_closing` flag; explicit order; thread joined with timeout | D28.5 |
| Drawings | **[P1/P2 2026-10-12]** D27.10: `DrawingStore.update_drawing` persists colour/label/group_id (`None` = unchanged, never clobbered); the `updated` signal carries `(id, payload, color)` from all emitters; colour edits survive reload. **[P3 2026-10-12]** Single-writer invariant now enforced: main chart is the sole writer of drawings/alarms/studies; pop-outs render overlays read-only — `ChartPanel(editable=False)` gates drag/click/menu/Delete at the overlay level (`AlarmOverlay`/`DrawingOverlay` `editable` flag; fix `8ef0342` also closed a `DrawingOverlay` drag/settings hole the review missed). Drawings/groups live in the session; `drawings_changed` fans out to views. | **[NOW AS-BUILT]** Colour/label/group persisted; single-writer invariant enforced (A64) | D27.10, D24 |
| Pop-out windows | — (did not exist) | **[NOW AS-BUILT]** `ui/popout_window.py::PopoutChartWindow` (28px header `SYMBOL · timeframe · mode` + close, `ChartPanel(editable=False)`); timeframe/mode/ext-hours frozen at creation; `MAX_POPOUTS = 10` (`config/settings.py::MAX_POPOUTS`), the 11th is **refused with a status-bar message** (`ui/main_window.py::MainWindow._open_popout` — the affordance is *not* `setEnabled(False)`-ed); toolbar "Pop out" action + `Ctrl/Cmd+P`; opened while disconnected → cached bars render and the subscription starts on connect, with **no per-pop-out "connecting" indicator** (main window `conn_badge` only); always-on-top default off with per-window toggle (header context menu) — `AC-D24.10`/A66, owner-confirmed 2026-10-14 | D24, AC-D24.5, AC-D24.10 |
| Pop-out persistence | Pop-outs are session-only (D24 as drafted) | **[NOW AS-BUILT]** Additive `popouts` table + `data/popout_store.py`; upsert on open/close and on 500ms-debounced move/resize end; lazy cache-first restore after connect, with dedup against already-open pop-outs on reconnect (`282aae5`); unresolvable symbols skipped with a non-blocking note | D24 / AC-D24.9 |
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

> **SUPERSEDED BY D41 (2026-10-15)** — the D36 footprint feature is **being removed** by the D41
> increment at the end of this file; `AC-D36.*` carry `SUPERSEDED BY D41` in `requirements.md`
> (DOC-4). This section is kept as the **as-built history** of what was built, not as a live
> mandate. The only D36-derived symbol D41 keeps is `ibkr/contracts.py::footprint_cache_key`
> (D39's burst key).

> **Increment scope.** A **new-feature** increment on the built D1–D35 system: footprint charts
> (bid×ask volume-at-price), the P0 item of the D36–D40 program. Built on `feat/d36-footprint` @
> `89fe152` (merged to `main` at `efffc51`, an ancestor of `b366b19`); 927 tests green
> (898 baseline + 29 new). D1–D35 not reopened. **Acceptance criteria `AC-D36.1`–`AC-D36.5` are now
> authored** in `requirements.md` (`### D36`, Q45/DG46 — they were previously cited while undefined);
> the `AC-D36.3` citation under Integration Points below is consistent with that authored text
> (zero `reqTickByTickData` **and** no mock/stub endpoint anywhere in the production tree).

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
- **`[new/changed]`** `ibkr/bridge.py` (+2 signals: `historical_ticks_bid_ask` /
  `historical_ticks_last`), **`[new/changed]`** `ibkr/client.py` (2 overrides:
  `historicalTicksBidAsk` / `historicalTicksLast` + 10.51.1 signature fixes — the planned
  histogram override was removed with the histogram path, see “Histogram removal” below),
  **`[new/changed]`** `ibkr/contracts.py` (`INDEX_PROXY`,
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
  and docs; tick-count metric derives from the same TRADES tick pages as volume. This is the
  owner-confirmed as-built deviation recorded in `docs/phase-changelog.md` (Phase D36 — Decisions:
  "the planned histogram path was REMOVED from code and docs … one dataset, two metrics, zero new
  requests"; and its review finding A1, "dead histogram plumbing removed"). It is also why this
  increment's bridge/client surface is **2 signals + 2 overrides**, not the 3 + 3 the pre-removal
  plan (and the changelog's own 36.1 row) stated.

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
  `{bar_ts: {level: [bidVol, askVol, tradeVol, tradeCount]}}`. Read before any paginated
  backfill; write on backfill completion. (`docs/phase-changelog.md`, Phase D36 item 36.2 records
  the same two-metric shape — per-level bid/ask volume from `BID_ASK` plus per-level trade volume
  and trade count from `TRADES`.) **Scope:** only SPX/SPY/QQQ/ES-front/NQ-front (owner decision); all other symbols
  are in-memory only (re-fetch per session).
- In-memory per-level aggregates keyed `(resolved_contract, timeframe)` in the service; per-bar
  job states (ready | loading | unavailable) drive the structural loading UI.

### Integration Points (D36 increment)

- **IBKR:** `reqHistoricalTicks` (BID_ASK + TRADES) only — **zero** `reqTickByTickData` for footprint
  (asserted on the request registry + source call-site scan, AC-D36.3). Tick requests count against
  the rolling 600s historical budget (`pacing_manager` is the single owner).
- **Bridge/client:** 2 new signals (`historical_ticks_bid_ask` / `historical_ticks_last`) +
  2 new overrides (`historicalTicksBidAsk` / `historicalTicksLast`), all additive; `super()`
  called first; routing by reqId (D27 pattern). (An earlier "3 signals + 3 overrides" count
  predated the histogram-path removal — see “Histogram removal” above.) 10.51.1 fixes: `error()` 5-arg,
  `orderStatus` 11-arg (`mktCapPrice`),
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
A1–A5) applied on the same branch; single squashed commit `89fe152` (merged at `efffc51`).
D37–D40 followed (see below).

## D37 increment — microstructure (as-built 2026-10-13, Code Reviewer APPROVED)

> **SUPERSEDED BY D41 (2026-10-15)** — D37's depth heatmap / imbalance / auction surface is **being
> removed** by the D41 increment at the end of this file; `AC-D37.*` carry `SUPERSEDED BY D41` in
> `requirements.md` (DOC-4). This section is kept as the **as-built history** of what was built, not
> as a live mandate. **The S0 generic-tick substrate D37 introduced is explicitly KEPT** (D38 reuses
> it for `"292"`/`"456"`), so the supersession removes D37's depth/IMB/AUC/auction surface only.

> **Increment scope.** A **new-feature** increment on the built D1–D36 system: depth heatmap +
> auction imbalance. Built on `feat/d37-microstructure` @ `69c2d66`, merged to `main` @ `9958891`
> (an ancestor of `b366b19`); 947 tests green (927 pre-existing + 20 new). D1–D36 not reopened.
> **Acceptance criteria `AC-D37.1`–`AC-D37.5` are now authored** in `requirements.md` (`### D37`,
> Q45/DG46). **Depth heatmap default ON is owner-confirmed 2026-10-14 (Q44/A67)** — overriding the
> reviewer's OFF suggestion; D36 footprint stays OFF.

### Codebase Summary (existing repository — D37 surface)

The D37 code lives in three new modules plus additive changes to existing ones:

- **New `[new]`** `services/depth_heatmap.py::DepthHeatmapService` — price-keyed live book from the
  depth op stream (insert/update/delete + L2 MPID/exchange rows); 60×30s price×time matrix;
  imbalance `(bidVol−askVol)/(bidVol+askVol)` over top-5 AND top-10 recomputed per op; refcounted
  per symbol (feed lives only while `views > 0` — no headless depth); depth replays on reconnect
  via the D27 path.
- **New `[new]`** `ui/depth_heatmap_item.py` — pyqtgraph overlay item: price-aligned strip at the
  chart's right edge (live layer, Bookmap-style rows = price levels, columns = time buckets,
  intensity = size).
- **New `[new]`** `services/md_line_guard.py` — owns the market-data-line accounting: `ok` <90,
  `approaching` 90–99 (warns naming the symbol), `exceeded` ≥100 (refuses naming the symbol).
- **`[new/changed]`** `ibkr/client.py` (`tickGeneric`/`tickString`/`tickNews` overrides —
  10.51.1-verified, `tickNews` 6-arg incl. `extraData`), **`[new/changed]`** `ibkr/bridge.py`
  (+3 signals), **`[new/changed]`** `ibkr/market_data.py` (`req_mkt_data(contract,
  generic_ticks="")`), **`[new/changed]`** `ibkr/market_depth.py` (refcount hooks),
  **`[new/changed]`** `ibkr/subscription_manager.py` (separate `DEPTH_HEATMAP`/`S0_TICKS`
  sub-manager tags — the DOM's `unsubscribe_all_of_type(DEPTH)` would otherwise wipe session
  feeds), **`[new/changed]`** `ui/ticker_session.py` (S0 union ownership, depth feed lifecycle,
  auction state), **`[new/changed]`** `ui/chart_panel.py` (overlay + auction chip),
  **`[new/changed]`** `ui/main_window.py` (354 status-bar message, backed `primary_session`
  property — the drive-by fix), **`[new/changed]`** `ui/watchlist_panel.py`.

### Tech Stack Decisions (D37 increment)

- **Substrate S0 (shared by D37/D38):** per-symbol generic-tick union (`"225"` auction,
  `"292"` news push, `"456"` IB Dividends — D38 use) merged into the single per-symbol
  `reqMktData` — one IBKR subscription per symbol is preserved; features register/deregister
  their tick needs and the session re-subscribes only when the union changes. New signals are
  strictly additive (no changes to existing `tick_price`/`tick_size` routing).
- **10.51.1 signatures verified arg-for-arg** against the installed wheel for every new override
  (the D36 B1/B2 lesson applied proactively — no drift found).
- **`isSmartDepth` carried as row provenance** (D36 B2 fix) so D37 can disambiguate
  SMART-aggregated rows from exchange rows.

### System Components (D37 increment)

- **DepthHeatmapService** (`services/depth_heatmap.py`, one per `TickerSession`): consumes the
  existing `MarketDepthManager.on_update` op stream → maintains the price-keyed book and the
  60×30s matrix (bounded trailing window — the D28.4 pathology in miniature, avoided by design).
  Imbalance over top-5 and top-10 computed simultaneously on every op; the headlined N is a
  user-facing toggle (default top-5). 100-op burst → 0 static regens (D28 discipline holds).
- **Auction chip** (`ui/chart_panel.py` header): imbalance side + paired shares + indicative price
  from ticks 34/35/36 via the S0 `"225"` generic list (tick 61 regulatory imbalance when present).
  Highlights during 9:25–9:35 / 15:55–16:05 ET; click expands a popover with raw values; absent
  ticks → explicit "no auction data" state.
- **Degradation:** IBKR error **354** on `reqMktDepth` → explicit `no_entitlement` state, feed
  cancelled, panel shows "Depth subscription required" + status bar `Depth [354]: <server message>`.
  Known limitation (in code): delayed-depth-instead-of-354 would render unlabeled — follow-up if
  ever observed.
- **MD line guard** (`services/md_line_guard.py`): warn — never silently drop — when the
  session/monitor line count approaches the 100-line cap; the warning names the symbols that would
  exceed the budget. S0's per-symbol reqMktData lines counted explicitly (§7 worst case ≈ 40).

### Data Model (D37 increment)

- No new tables. In-memory price-keyed book + 60×30s matrix per session (bounded, view-lifetime);
  per-symbol generic-tick union state in `TickerSession`; refcounted depth feeds keyed by symbol
  with `DEPTH_HEATMAP`/`S0_TICKS` tags.

### Integration Points (D37 increment)

- **IBKR:** `reqMktDepth` (3–60 simultaneous, refcounted) + S0 generic ticks (225/292/456) on the
  existing per-symbol `reqMktData`. Depth replays on reconnect via the D27 path (reconnect test
  assertions extended for S0/depth feeds — reviewer signed off, D27 guarantee not weakened).
- **Bridge/client:** 3 new signals + 3 overrides, all additive; `super()` called first; routing by
  reqId (D27 pattern).
- **Render pipeline:** heatmap renders in the chart's live layer as an overlay item; auction chip in
  the chart header. No static-layer regen per depth op (counter-asserted).

### Non-Functional Approach (D37 increment)

- **Pacing:** depth feeds 3–60 (budget-exceeded → status-bar warning naming symbols, same pattern as
  D25's pacing guard); MD lines ≤100 (guard warns at 90, refuses at 100); S0 ticks add zero new MD
  lines per feature.
- **Performance:** 100 depth ops → 0 static-layer regenerations (counter-asserted); matrix bounded
  60×30s.
- **Test safety:** no test touches live TWS or transmits orders; mocked `ib_client` only. Owner
  rule (binding): **no mock endpoint of any kind in production code** — B.6 grep PASSED for D37.
- **Depth heatmap default ON — owner-confirmed 2026-10-14 (Q44/A67), overriding the reviewer's OFF
  suggestion.** `ui/chart_panel.py::ChartPanel.depth_heatmap_item` creates the `DepthHeatmapItem`
  unconditionally and `ui/chart_panel.py::ChartPanel._depth_enabled_ui` sets it `True`, so the panel
  is visible by default; D36 footprint stays **OFF** (owner
  decision 2026-10-13). The reviewer's OFF recommendation (consistency with D36, depth-budget) is
  recorded under Architecture Risks below as an accepted trade-off, not an open question.

### Architecture Risks (D37 increment)

- **Depth-budget burn (accepted trade-off):** the heatmap ships defaulting ON and consumes depth feeds
  (3–60 budget) for every charted symbol. The reviewer recommended OFF for consistency with D36; the
  **owner confirmed ON** (2026-10-14, Q44/A67) and accepted the depth-budget cost. Mitigation remains
  the refcounted `views > 0` lifetime (no headless depth) and the md-line/depth-budget warnings.
- **354 vs delayed depth:** the no-entitlement path handles the 354 error; if TWS instead delivers
  delayed depth, it renders unlabeled today — needs a labeling pass if observed.
- **S0 is shared tick plumbing:** D38 will extend the same union — keep additions strictly additive.

### Implementation sequencing (D37 increment)

37.0 (S0 substrate) built first against D37 as the real consumer, then 37.1 → 37.5 on
`feat/d37-microstructure`; reviewer APPROVED with no blocking findings (no rework cycle);
merged to `main` @ `9958891` (an ancestor of `b366b19`). D38–D40 followed.

---

## D38 increment — events & news (as-built 2026-10-13, Code Reviewer APPROVED)

> **Increment scope.** A **new-feature** increment on the built D1–D37 system: event markers
> (IBKR tick-59 dividends + yfinance earnings/splits/dividends) + news-for-holdings digest.
> Built on `feat/d38-events-news` @ `b893911`, merged to `main` @ `8599ce4`
> (an ancestor of `b366b19`); 970 tests green (947 pre-existing + 23 new). D1–D37 not reopened.
> **Acceptance criteria `AC-D38.1`–`AC-D38.6` are now authored** in `requirements.md` (`### D38`,
> Q45/DG46); the `AC-D38.4` citation below (corporate-events-only guard at the provider boundary)
> matches that authored text.
> **WSH is removed from D38 entirely** (owner decision 2026-10-13); yfinance is the sole
> secondary source.

### Codebase Summary (existing repository — D38 surface)

The D38 code lives in two new modules, one new package, plus additive changes to existing ones:

- **New `[new]`** `ibkr/news.py::NewsManager` — `reqNewsProviders()` → the user's actual
  entitlement list; per-holding `reqHistoricalNews(conId, providerCodes, startDateTime,
  endDateTime, totalResults)` issued **sequentially via a FIFO queue** (no headline-fetch storm
  on digest open), pacing-aware; `reqNewsArticle(providerCode, articleId)` on headline click.
  API news requires API-specific subscriptions — most TWS news services are NOT available via
  the API, hence the honest "No API news subscription" state.
- **New `[new]`** `ui/news_digest_dock.py` — repositionable, closable dock; reopenable from a
  minimal View-only menubar (`View → News Digest`, `Ctrl+Shift+N` — the app had no menubar;
  added, drive-by). Refresh = **backfill on open** + **live push primary** (tick `"292"` via
  S0 → `tickNews` → headline prepended) + **15-min periodic re-query backstop** (QTimer, only
  while the digest is open). Signal wiring is deferred to first open (init-order drive-by fix).
- **New `[new]`** `data/events/` package — the event-provider layer: `provider.py` (`Event`
  dataclass: id/type/symbol/date/source/details; corporate-events-only guard **rejecting
  non-corporate types at the provider boundary** — AC-D38.4; `EventProvider` ABC;
  defensive tick-59 dividend parser `parse_ib_dividend_string` that **never raises**),
  `ibkr_source.py` (dividends from session tick-59 state, **skips futures contracts**),
  `yfinance_source.py` (SQLite per-symbol cache: 24h TTL, **6h revalidation for events within
  7 days** so corrections propagate; single `QThread` worker, **≥1s between calls**, own
  connections — never on the IBKR pacing budget; lazy import; `failed_at` distinguishes
  outage from loading).
- **New `[new]`** `ui/event_marker_overlay.py` — time-axis markers: earnings gold ◆E, dividend
  green ●D, split blue ▲S; countdown label ("Earnings in 3d") for the next upcoming event;
  markers **id-keyed, not date-keyed** (date corrections move the marker).
- **`[new/changed]`** `ibkr/client.py` (4 new news overrides — 10.51.1 arg-for-arg verified),
  **`[new/changed]`** `ibkr/bridge.py` (`news_providers` / `historical_news` /
  `historical_news_end` / `news_article` signals),
  **`[new/changed]`** `ui/ticker_session.py` (S0 register/deregister batching, tick-59 dividend
  state, `_merge_events` — the reviewer A1 re-point target; headless-session lifecycle for
  digest holdings), **`[new/changed]`** `ui/main_window.py` (menubar, dock wiring,
  S0-union routing), **`[new/changed]`** `requirements.txt` (`yfinance==1.7.0` + re-pin
  policy comment).

### Tech Stack Decisions (D38 increment)

- **S0 union extended to `"225,292,456"`** (auction, news push, IB Dividends). New
  `s0_register_many`/`s0_deregister_many` batch helpers issue a single resync (fixes double
  re-subscribe churn); one-subscription-per-symbol is preserved — no standalone `reqMktData`
  outside sessions.
- **yfinance is the sole secondary source** (owner-mandated 2026-10-13). It is the plan's
  largest external dependency (unofficial Yahoo API, no SLA, breaks a few times a year), so
  the hygiene is binding: pinned `yfinance==1.7.0` (re-pin quarterly or whenever Yahoo
  breaks the library — every re-pin re-runs the full offscreen suite), SQLite per-symbol
  cache (24h TTL, 6h revalidation for near-term events), polite throttle (sequential, ≥1s
  between calls, single-digit concurrency), lazy import (no hard dependency at startup).
  **No other external API anywhere in the tree** (reviewer-verified single-source rule).
- **10.51.1 signatures verified arg-for-arg** for the 4 new news overrides (the D36 B1/B2
  lesson applied proactively — no drift found).
- **Source priority IBKR tick-59 dividends → yfinance** (earnings/splits + dividend fallback);
  the IBKR-first merge **drops same-date yfinance dividends** to avoid double-marking.
- **No-data rule (owner):** both sources empty → explicit "no event data" state + logged for
  the owner — the owner decides on feature removal. Every failure mode (429, exception,
  empty frame, no entitlement, no holdings) has an explicit UI state; nothing is ever
  silently empty and no exception ever reaches the UI or blocks the chart.

### System Components (D38 increment)

- **News path:** `NewsManager` (FIFO, pacing-aware) → bridge signals →
  `NewsDigestDock` (backfill → live prepend → 15-min backstop). Non-charted holdings get
  lightweight headless `TickerSession`s while the digest is open (D24 headless semantics),
  torn down on close; their S0 lines are counted in the MD-line budget.
- **Event path:** `TickerSession` merges IBKR tick-59 dividends + yfinance events behind
  the `EventProvider` interface (`_merge_events`) → `EventMarkerOverlay` diffs by event
  id → time-axis markers + countdown. Corporate-events-only guard rejects non-corporate
  types at the provider boundary.
- **yfinance isolation:** `YFinanceSource` runs on a single `QThread` worker with its own
  connections and throttle — entirely off the IBKR pacing budget; `failed_at` distinguishes
  outage from loading so the UI shows the right explicit state.

### Data Model (D38 increment)

- `Event`: `id` (stable key for marker diffing, not the date), `type` (`"earnings" |
  "dividend" | "split"` — `__post_init__` rejects anything else), `symbol`, `date`
  (ex-div for dividends), `source` (`"ibkr" | "yfinance"`), `details` (amount, estimate,
  surprise…).
- yfinance cache: one SQLite row per (symbol, cache-key), 24h TTL; events within 7 days
  re-validate every 6h so corrections propagate.
- Tick-59 dividend parse: documented shape `past12m,next12m,nextDate,nextAmt`
  (YYYYMMDD) — the parser splits on comma or semicolon, takes fields positionally, and
  **never raises** (separators/fields vary by server).

### Integration Points (D38 increment)

- **D37 S0 substrate:** extended, not replaced (union string grew; register/deregister
  batching added). D38 is the first real consumer of the D37-planned `"456"` tick.
- **D24 headless sessions:** digest holdings reuse the headless `TickerSession` semantics
  (create on digest open, teardown on close) — no new session model.
- **D26 safety layer:** untouched. News/event paths are read-only data; no order-path
  interaction.
- **D27 reconnect:** news/event state re-derives on reconnect via the session subscription
  path (S0 union re-issued); yfinance cache survives disconnects (SQLite on disk).

### Non-Functional Approach (D38 increment)

- **Pacing:** headline fetches sequential (FIFO, pacing-aware); yfinance HTTP is never on
  the IBKR budget (own throttle + cache); S0 ticks add zero new MD lines per feature;
  headless digest sessions' lines counted in the MD-line budget.
- **Performance:** marker overlay diffs by event id (no full rebuild on unchanged data);
  digest backstop only fires while the digest is open.
- **Test safety:** no test touches live TWS or transmits orders; mocked `ib_client` only;
  yfinance calls mocked at the boundary. Owner rule (binding): **no mock endpoint of any
  kind in production code** — B.6 grep PASSED for D38.

### Architecture Risks (D38 increment)

- **yfinance fragility:** the largest external dependency — unofficial API, no SLA, breaks a
  few times a year. Mitigations are binding (pinned version, cache, polite throttle,
  graceful degradation, no-data rule); the owner was informed of the terms risk during
  research.
- **Tick-59 shape variance:** the documented `past12m,next12m,nextDate,nextAmt` shape
  varies by server — the parser never raises, but a novel shape could silently drop a
  dividend; yfinance dividend fallback covers the gap.
- **Headless-session MD lines:** digest-open headless sessions consume MD lines — counted
  in the budget, but a large portfolio + open digest approaches the 100-line guard faster.

### Implementation sequencing (D38 increment)

38a.1 (news client) → 38a.2 (digest dock, needs 38a.1) in parallel with 38b.1
(event-provider layer) → 38b.2 (markers, needs 38b.1) on `feat/d38-events-news`;
reviewer APPROVED with no blocking findings (A1 advisory applied post-review — two merge
tests re-pointed at the real `_merge_events`); merged to `main` @ `8599ce4` (an ancestor of
`b366b19`). D39–D40 followed.

## D39 increment — volume-burst alerts + symbol search (as-built 2026-10-13, Code Reviewer APPROVED)

> **Increment scope.** A **new-feature** increment on the built D1–D38 system: symbol
> search (debounced `reqMatchingSymbols` → `symbolSamples` → contract resolution → load
> chart) + `volume_burst` alarm kind (robust median/MAD z-score vs same-time-of-day
> baseline, N=30, user-tunable threshold) + index-proxy burst routing.
> Built on `feat/d39-burst-search` @ `90b01e7` (+ post-review advisories `0b50fb7`),
> merged to `main` @ `83f792a` (an ancestor of `b366b19`); 1009 tests green (970 pre-existing
> + 39 new).
> D1–D38 not reopened. **Acceptance criteria `AC-D39.1`–`AC-D39.5` are now authored** in
> `requirements.md` (`### D39`, Q45/DG46); `AC-D39.5` carries an explicit AMBIGUITY note (the shipped
> tests label only `AC-D39.1`–`AC-D39.4`, so `.5` is the batch regression criterion authored from the
> baseline behaviour plus the `AC-D37.5`/`AC-D38.6` convention).

### Codebase Summary (existing repository — D39 surface)

The D39 code lives in two new services plus additive changes to existing ones:

- **New `[new]`** `services/symbol_search.py` — debounced search service:
  `reqMatchingSymbols(pattern)` (**≤1 request per 300ms** of typing) → `symbolSamples`
  (≤16 results) → bounded contract resolution → chart load. Exactly-once correlation
  (reqId), 5s timeout, disconnected guard (search disabled + message) and empty/no-match
  clear state. The wire path is user-initiated only — never backgrounded.
- **New `[new]`** `services/volume_baseline.py` — the three-tier baseline service:
  **(1)** persisted `volume_baseline` table (additive `data/db.py` migration; **`samples`
  JSON column** carries the exact sample list so recomputation is exact, not approximate);
  **(2)** one-time `BarCache` prime — **local only, zero IBKR requests**; **(3)** rolling-30
  fallback until buckets fill. Keyed per (resolved-contract, ET minute-of-day bucket),
  volumes normalized per-minute. Guards are part of the service contract: **1.0/min volume
  floor** (no evaluation on dust), **5-bar warm-up** (explicit "warming up (n/5)" status —
  the early-session coverage gap is documented, not silent), **5%-of-median MAD floor**
  (flat data scores z=0; real bursts on flat baselines fire finite, never infinity).
  **Roll invalidation:** the key embeds D36's `footprint_cache_key` (front month in the
  key); a key change tombstones the old contract in-session, and `record()` consults the
  tombstone set (post-review A2) — old-contract DB rows **cannot resurrect**.
- **`[new/changed]`** `ibkr/client.py` (`symbolSamples` override — 10.51.1 arg-for-arg
  verified: `(reqId, contractDescriptions)`), **`[new/changed]`** `ibkr/bridge.py`
  (`symbol_samples` signal), **`[new/changed]`** `ui/watchlist_panel.py` (header search
  box — expanding, capped 180px, **zero minimum width**; a 110px minimum broke D17 dock
  tests), **`[new/changed]`** `data/models.py` (`Alarm.kind: str = "price"` +
  `params: dict` — additive, price rows untouched), **`[new/changed]`**
  `services/alarm_service.py` (`evaluate_volume_burst()` — z-score semantics only, never
  K-multiple language, C39.1), **`[new/changed]`** `ui/ticker_session.py`
  (per-push evaluation in `_on_aggregated_bar`: forming bars evaluated conservatively —
  partial volume ÷ full minutes can only understate — completed bars recorded;
  chart overlay skips non-price alarms), **`[new/changed]`** `services/alarm_monitor.py`
  (reconcile routes index burst alarms to the proxy tape's session, ensured headless;
  **no session is created for the index itself**), **`[new/changed]`** `ui/alarm_dialog.py`
  + `ui/alarm_edit_dialog.py` (z-threshold spinbox floor 0.5→**1.0** + tooltip caution —
  post-review A1), **`[new/changed]`** `ibkr/contracts.py` (D36's `INDEX_PROXY` reused,
  not duplicated — SPX→ES front-month for burst alarms).

### Tech Stack Decisions (D39 increment)

- **Robust z-score everywhere: median/MAD, never mean/stddev** (owner, 2026-10-13).
  Same-time-of-day baseline (ET minute-of-day buckets), N=30 samples, per-minute
  normalization so mixed timeframes compare. The threshold is **user-tunable** per alarm
  (`params["z_threshold"]`, default 4.0, floor 1.0 — below 1.0 fires on normal variance).
- **Session bar volumes are the evaluation substrate** (owner-confirmed 2026-10-13:
  existing session-bar volume, not generic ticks 54/55/56 or 63/64/65). This keeps burst
  evaluation on the per-aggregator-push path with **zero new IBKR requests** and zero
  pacing budget impact.
- **Alarm kind is a first-class, additive extension.** `kind`/`params` on `Alarm`;
  `evaluate_alarms` is kind-filtered so a `price=0.0` burst alarm can never fire as a
  price alarm (genuine pre-fix bug — caught during implementation); persist/trigger/rearm
  semantics are identical to price alarms (`AlarmStore.mark_triggered`, grouped
  `alarm_triggered` emission, toast+sound exactly once, headless included).
- **`symbolSamples` carries no company name** — 10.51.1's `ContractDescription` has only
  `contract` + `derivativeSecTypes` (reviewer-verified). The requirement's "company name"
  was an API-docs oversell; results show symbol·secType·exchange, full details resolve
  on selection. The new override was verified arg-for-arg against the wheel (the D36
  B1/B2 lesson is now a standing habit).
- **Index proxy reuses D36's resolver.** Burst alarms on indices carry
  `params.proxy`/`proxy_label`; the baseline keys on the resolved proxy contract and
  invalidates on roll — never compare ESZ5 volume against an ESU5 baseline (C39.2,
  mirror of 36.3's never-compare-across-contracts rule).

### System Components (D39 increment)

- **Search path:** header box (debounced) → `SymbolSearchService` → `reqMatchingSymbols` →
  bridge `symbol_samples` → popup (symbol·secType·exchange) → bounded contract resolution
  (`reqContractDetails`) → `load_chart`. Disconnected → box disabled + message; no match →
  clear state.
- **Burst path:** `_on_aggregated_bar` → `evaluate_alarms` (kind-filtered) →
  `evaluate_volume_burst()` (z vs `VolumeBaselineService` for the bar's ET minute-bucket)
  → z ≥ threshold → `AlarmStore.mark_triggered` → grouped `alarm_triggered` → toast
  (proxy-labelled, e.g. "Volume burst on ES tape (z=9.4)") + sound, exactly once → re-arm
  re-enables. Headless sessions evaluate identically (D25 semantics).
- **Baseline path:** `record(resolved_key, bucket, per_min_volume)` consults the
  in-session tombstone set (A2) → persisted table (`samples` JSON for exact recomputation)
  → lookup by (resolved key, bucket); prime tiers 2/3 fill gaps without touching IBKR.
  Warm-up: <5 bars → "warming up (n/5)", no evaluation. Floor: median <1.0/min → no
  evaluation. MAD floor: 5% of median — flat data scores z=0.
- **Proxy path:** burst alarm with `params.proxy` → `AlarmMonitor.reconcile` ensures the
  proxy tape's session (headless if needed) → evaluation and baseline both run against
  the proxy contract's bars; the index itself never gets a session.

### Data Model (D39 increment)

- `Alarm`: `kind` (`"price"` default — all pre-existing rows unchanged), `params` (JSON;
  burst alarms carry `z_threshold`, window N, `proxy`, `proxy_label`). Additive migration;
  price-alarm rows untouched.
- `volume_baseline` table (additive): `(resolved_contract, bucket)` → `median`, `mad`,
  `n`, **`samples` JSON** (exact sample list — recomputation is exact, not approximate).
  Roll = key change → in-session tombstone; tombstoned keys' `record()` calls are dropped
  and their DB rows never resurface.

### Integration Points (D39 increment)

- **D25 alarm engine:** `volume_burst` is the first new kind since D25 — kind-filtering
  keeps price alarms' behavior bit-identical; the pre-fix kind-unfiltered path would have
  let a burst alarm fire as a price alarm (fixed in 39.3).
- **D26 safety layer:** untouched. Burst/search paths are read-only data; no order-path
  interaction.
- **D27 reconnect:** session bar volumes are the evaluation substrate, so bursts re-derive
  naturally on reconnect; persisted baseline (SQLite) survives disconnects.
- **D36 footprint cache key:** reused as the baseline key (`footprint_cache_key` embeds the
  front month) — the roll-invalidation story is shared, not duplicated.
- **D37 S0 substrate:** untouched. Burst evaluation needs no generic ticks; the baseline
  prime is local-only. Search is a separate debounced request path (user-initiated).

### Non-Functional Approach (D39 increment)

- **Pacing:** D39 adds **zero** IBKR budget load — debounced user-initiated search traffic,
  local-only baseline prime, per-push evaluation on existing session bars. `pacing_manager`
  remains the single owner; nothing sleeps on the GUI thread.
- **Performance:** median/MAD over ≤30 samples is O(1) per push; the persisted-table
  lookup is one indexed query per (contract, bucket); tombstone set is in-memory.
- **Test safety:** no test touches live TWS or transmits orders; mocked `ib_client` only.
  Owner rule (binding): **no mock endpoint of any kind in production code** — B.6 grep
  PASSED for D39.

### Architecture Risks (D39 increment)

- **Warm-up blind spot:** the first 5 bars of a session cannot evaluate bursts — an open
  auction spike is invisible to the feature. Documented as a known gap (explicit
  "warming up (n/5)" status), not a silent one.
- **Proxy-session MD lines:** index burst alarms ensure a headless proxy session whose
  S0/depth lines count in the MD-line budget — counted, but a burst-alarm-heavy watchlist
  approaches the 100-line guard faster.
- **Flat-baseline finiteness:** the 5%-of-median MAD floor guarantees finite z on flat
  baselines, but its calibration (5%) is heuristic — if false bursts appear on flat
  names, revisit the floor before the threshold.

### Implementation sequencing (D39 increment)

39.1 (search) and 39.2 (baseline service — the most intricate logic, tested tier-by-tier
plus guard cases before wiring) → 39.3 (`volume_burst` kind + evaluation wiring) →
39.4 (index proxy) on `feat/d39-burst-search`; reviewer APPROVED with no blocking
findings (A1/A2 advisories applied post-review in `0b50fb7`); merged to `main` @
`83f792a` (an ancestor of `b366b19`).

## D40 increment — TWS daily-lifecycle pause/resume (as-built 2026-10-13, Code Reviewer APPROVED)

Final phase of the D36–D40 program. Owner-approved 2026-10-13: TWS ONLY (never Gateway);
Aniket closes TWS nightly and logs in manually each morning — no 24/7 headless scenario
to protect; D40 is pause/resume around TWS's daily lifecycle. Built on
`feat/d40-tws-lifecycle` @ `4ac2453` (+ review fixes `d6f38e8`); reviewer
CHANGES REQUIRED → rework → APPROVED; merged to `main` @ `b366b19` (the D40 merge; `origin/main` is now `262ec81`).
**Acceptance criteria `AC-D40.1`–`AC-D40.5` are now authored** in `requirements.md`
(`### D40`, Q45/DG46); `AC-D40.5` carries an explicit AMBIGUITY note (the shipped tests label only
`AC-D40.1`–`AC-D40.4`, so `.5` is the batch regression criterion authored from the batch-regression
convention).

### Codebase Summary (D40 increment)

- `ibkr/client.py` — new `DisconnectClass` (`TRANSIENT` / `TWS_GONE`); `connectionClosed()`
  classifies TWS-gone per ibapi's own docstring and **restarts the backoff reconnect loop**
  (drive-by fix: the old code stopped polling and scheduled nothing — the app could never
  notice a morning login without a restart); backoff base 2s capped 16s; 502 downgraded to
  debug during paused backoff (still surfaces at startup with no prior connection).
- `services/alarm_monitor.py` — `pause_all()` (per-symbol pause-start, `monitoring_paused`
  on every alarmed session) and `resume_all()` (clears flags, re-seeds `prev_price` to None
  per AC-D25.3, finishes staged subscribes, returns gap intervals); `_on_connected` runs
  D27 replay → `reconcile()` → `resume_all()` (order swapped post-review — see B1).
- `ui/main_window.py` — `conn_badge_text(..., monitoring_paused=...)`: "Monitoring paused —
  TWS disconnected" in amber `#fbbf24`, never green; gap report surfaced in the status bar.
- `ui/ticker_session.py` — both evaluation entry points gate on `monitoring_paused`
  (headless shares the path); alarms created while TWS is down are staged
  (`_monitor_subscribe_pending`) and covered on resume.
- `tests/test_d40_tws_lifecycle.py` — 11 new tests, including the B1 regression test
  `test_d40_2_resume_session_recreated_mid_pause_no_phantom`.

### Tech Stack Decisions (D40 increment)

- **Classification boundary:** `connectionClosed` → TWS_GONE only if a live session existed;
  poll-driven drops and 1100/1101/1102 stay TRANSIENT. TWS daily auto-restart classifies
  as TWS-gone per the plan's edge cases. Codes are build-time observation items documented
  in code comments.
- **Reconcile-then-resume ordering (B1):** reconcile-created sessions take a staged path
  (`monitoring_paused=True`, `last_chart_price=None`, subscribe deferred) — the old
  resume-then-reconcile order let them take the normal path with a stale cache seed, a
  phantom-trigger hole. The regression test is order-sensitive by construction (fails on
  the old order with the stale 99.0 seed).

### System Components (D40 increment)

- **Disconnect classifier** (`ibkr/client.py::DisconnectClass`): the single place that
  decides TRANSIENT vs TWS_GONE; recorded before `disconnected` is emitted so routing
  decisions see it.
- **Pause engine** (`AlarmMonitor.pause_all`): per-symbol pause-start (gap accounting),
  session flags; evaluation gating is in the session's `_on_aggregated_bar`, so charted,
  headless, and proxy-tape sessions pause identically.
- **Resume sequencer** (`_on_connected` → D27 replay → `reconcile()` → `resume_all()`):
  prev_price re-seed implements the AC-D25.3 first-tick-no-eval guard; staged subscribes
  finish with pacing-aware retry.

### Data Model (D40 increment)

- `AlarmMonitor._pause_start: dict[str, float]` — per-symbol pause-start timestamps;
  `resume_all()` returns `[(symbol, pause_start, pause_end)]` for the gap report.
- `TickerSession.monitoring_paused: bool` + `_monitor_subscribe_pending: bool` — the
  staged path for alarms created while TWS is down. No DB schema change.

### Integration Points (D40 increment)

- **D26 badge:** `conn_badge_text()` gains the monitoring state — the owner-approved
  wording/placement, amber, never green while paused.
- **D27 reconnect:** the as-built replay is reused verbatim for resume; backfill waves in
  flight keep generation fencing; `_last_disconnect_class` is reset on connect so a stale
  TWS_GONE cannot downgrade a later transient drop.
- **D25 alarm semantics:** the first-tick-no-eval guard (AC-D25.3) is the mechanism that
  prevents phantom triggers across the gap — resume alone fires nothing.
- **D39 burst alarms:** proxy burst alarms pause with their tape session; the kind-filtered
  evaluators gate on the same flag.

### Non-Functional Approach (D40 increment)

- No IBKR budget load added: pause emits no requests; the overnight backoff is ~1
  handshake attempt per 16s; resume replays the existing pacing-aware paths. No threads
  added; all timer-driven on the main thread.

### Architecture Risks (D40 increment)

- **Classification heuristic:** the TWS-gone boundary rests on `connectionClosed` + error
  codes observed at build time. If a future IBKR release changes the nightly-shutdown
  signaling, the classifier needs revisiting — the codes are documented in code comments.
- **Gap-blind trading:** alarms cannot fire during the unmonitored gap by design; the gap
  report is the compensation — a symbol that moved 5% overnight shows no alarm, only the
  gap interval. This is the owner's accepted trade-off (TWS is closed; there is no data).
- **Staged-monitor pacing:** a large alarm list resumed at morning login could pace-limit
  (`PacingExceeded` → singleShot retry); a symbol can be left unmonitored for the wait —
  logged, not silent.

### Implementation sequencing (D40 increment)

40.1 (classification + reconnect-loop drive-by fix) → 40.2 (pause) → 40.3 (resume) →
40.4 (transient verification) on `feat/d40-tws-lifecycle`; reviewer CHANGES REQUIRED
(B1: resume/reconcile call order — phantom-trigger hole) → rework in `d6f38e8` (call-order
swap + staged path + regression test + A1/A2) → re-check APPROVED; merged to `main` @
`b366b19` (the D40 merge; `origin/main` is now `262ec81`). Program complete — no D41 without Aniket's explicit go-ahead.

---

## D41 increment — Batch 18: remove the D36 footprint + D37 depth/heatmap/imbalance/auction + the **entire** Active Trader panel; the right dock becomes **Portfolio-only** (validated 2026-10-15, **approved for build**)

> **Status of this increment.** Validated by Plan Artifact Editor & Validator (`Status: APPROVED`,
> 2026-10-15) and **approved for build**. The owner's explicit go-ahead — the thing the D40
> increment's closing line above was waiting for — was given 2026-10-15: **Q48** = also remove the
> Active Trader DOM ladder; **Q49** = delete the persisted `footprint_cache` table **and rows**;
> **Q50** = remove the **entire** Active Trader panel (in-app order-entry UI included) and make the
> right dock **Portfolio-only**.
>
> Unlike the D36–D40 increments above, this one is **planned and approved, not yet as-built**. When
> it lands, this section becomes the as-built record for the removal.
>
> **This increment supersedes the D36 and D37 increments and the D18/B2 two-section-dock model for
> their removed surface** (see § *Supersessions (D41 increment)*). The D36/D37/D18 sections above are
> kept **as-built history** and each now carries a supersession marker; nothing in them is silently
> rewritten.
>
> Requirements of record: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`), `### D41`
> (`:3263`–`:3426`, `AC-D41.1`–`AC-D41.7`), Journey 36 (`:855`–`:882`), assumptions `A68`–`A71`
> (`:3499`–`:3502`), gaps `DG66`–`DG71` (`design_gaps.md:1012`–`:1153`). Companion plan:
> `docs/plan.md` § *D41 — Batch 18 removal* (phases, per-file `touches_files` partition, assumptions).
> Review: `docs/plan_review.md` (D41 cycle 2, `APPROVED`).

### Summary (D41 increment)

D41 is a **removal**, not a feature. Three coupled changes: **(1)** delete the D36 footprint and the
D37 depth/imbalance/auction feature trees (modules, bridge/client surface, subscription tags, chart
controls, session state, DB table); **(2)** delete the **entire** Active Trader panel — DOM ladder
*and* the in-app order-entry ticket — together with the market-depth machinery and the `DOM` toolbar
button, and re-shape the single right dock into a **Portfolio-only** section reusing D21.13's
header/collapse mechanism and the unchanged pure `ui/dock_layout.py` clamp; **(3)** **re-home** the
D26 safety gates whose only caller was the deleted ticket (the disconnected guard and the
`validate_order()` gate, now fed by a retained `ref_price` source) onto the one surviving order
emitter, Portfolio's close/flatten path. Everything else — D1–D35, D38 news/events, D39 bursts/search,
D27/D28 correctness/pacing, the chart, the kill switch, the fail-fast port check — is untouched and
is the non-regression contract.

### Codebase Summary (D41 removal surface — existing repository, source-validated 2026-10-15)

Factual inventory of the surface D41 touches. The repo is **not** greenfield: it is a PyQt6 +
pyqtgraph desktop charting/order terminal (~4,900 graph nodes; 1,028-test offscreen suite green on
the frozen baseline `main` @ `29067af`).

**Data models / schema**

- **`data/db.py::DB`** — SQLite, one connection, `_init_schema()` (DDL script) + `_migrate_schema()`
  (additive `ALTER TABLE`, `CREATE UNIQUE INDEX`, idempotent). Tables: `bars`, `watchlist`, `alarms`,
  `zones`, `drawing_groups`, `drawings`, `studies`, `popouts`, `positions`, `trade_groups`,
  `position_group_map`, **`footprint_cache`** (`:121`–`:127`, D36: one compressed JSON blob per
  `(resolved_contract, date, timeframe)`), `yfinance_events_cache` (D38, `:132`), `volume_baseline`
  (D39, `:144`). `config/paths.py::get_db_path()` returns the **user-space production DB** when
  `DB_PATH` is unset (`tests/conftest.py` sets it to a temp file).
- **`data/models.py`** — dataclasses `Bar`, `Position`, `TradeGroup`, `UserOrder`, **`OrderBookLevel`**
  (`:105`–`:110`; verified referenced by **nothing** in the tree), drawing/study models.
- **`data/footprint_cache.py`** — `FootprintCache` + `is_cacheable` (D36 persistence).
- **In-memory models that matter to D41:** `ui/main_window.py::MainWindow._symbol_last_prices`
  (`dict[str, float]`, the D27.5 central `symbol → last_price` map, `:727`); `TickerSession._s0_needs`
  (refcounted generic-tick need registry); `SubscriptionManager` entries keyed by `req_type`.
- **DB access:** `data/footprint_cache.py::FootprintCache` takes `_app_db.conn`; `positions` rows are
  the Portfolio panel's source (`_on_position_end` selects the whole table).

**Major components and responsibilities (as-built)**

| Component | Responsibility |
|---|---|
| `ui/main_window.py` (~3,700 lines) | toolbar, watchlist + **single right dock region**, session lifecycle, historical/backfill orchestration, RT/DOM/depth wiring, `_md_line_count`/`_guard_md_lines`/`_guard_depth_budget`, order placement + portfolio close/flatten, dock-width clamp |
| `ui/chart_panel.py` (~1,800 lines) | candle + volume plots, crosshair, drawing overlay, **D36 footprint render layers + floating control cluster**, **D37 depth/IMB/AUC controls + 500 ms depth repaint timer**, D38 event markers |
| `ui/ticker_session.py` (~1,800 lines) | per-symbol session: RT bar subscription, `BarAggregator`, alarms, **S0 generic-tick substrate (D37 substrate, reused by D38)**, **D36 footprint service/wave/cache**, **D37 depth refcount + auction**, historical backfill waves |
| `ui/active_trader_panel.py` (658 lines) | `LadderTable`, `BookTable`, **`OrderEntryWidget`** (Buy/Sell MKT/LMT/STP/Bracket + confirm + status), `ActiveTraderPanel` shell + `header_bar`/`header_button` |
| `ui/active_portfolio_panel.py` | `ActivePortfolioPanel`: `summary_label` (`DiagonalStrikeButton("Account Summary")`, its hide/show toggle), `body`, `is_collapsed()`, positions table + Close / Close Group / Flatten All + SL/TP dialogs |
| `ui/dock_layout.py` | **pure, Qt-free** single source of truth for dock widths: `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `RIGHT_DOCK_MIN_WIDTH=200`, `WATCHLIST_CAP_FRACTION=0.50`, `RIGHT_DOCK_CAP_FRACTION=0.40`, `watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths` (B3 cross-clamp) |
| `ibkr/market_depth.py` | `MarketDepthManager`: DOM `subscribe/cancel/cancel_all/on_update/snapshot` **and** the D37 refcounted `subscribe_shared/release_shared/resubscribe_shared` |
| `ibkr/order_book.py` | `Level`, `OrderBook`, `apply_operation`, `SIDE_ASK`/`SIDE_BID` |
| `ibkr/tick_history.py` | `TickHistoryManager.req_historical_ticks` (D36); never uses `reqTickByTickData` |
| `ibkr/bridge.py` / `ibkr/client.py` | Qt signals ↔ `ibapi.EClient` overrides (`historicalTicksBidAsk`/`Last`, `updateMktDepth`, `updateMktDepthL2`, `tickGeneric`/`tickString`/`tickNews`) |
| `ibkr/subscription_manager.py` | replay/rebind registry; tags `RT_BARS`, `MARKET_DATA`, **`DEPTH`**, **`DEPTH_HEATMAP`**, `S0_TICKS` |
| `services/` | `footprint_service.py`, `depth_heatmap.py` (features being removed); `md_line_guard.py::assess`, `volume_baseline.py`, `market_calendar.py`, `backfill_service.py`, `alarm_monitor.py` (kept) |
| `ibkr/orders.py`, `ibkr/validation.py`, `ibkr/id_manager.py`, `ibkr/pacing.py`, `config/settings.py::check_live_port` | **retained** order machinery (builders incl. `bracket_order`, `validate_order()`, id reservation, token buckets, fail-fast live-port check) |

**Key entry points**

`main.py` (imports pyqtgraph **before** `QApplication`, installs a non-abort `sys.excepthook`) →
`MainWindow.__init__` → `load_chart(symbol, timeframe, extended_hours)`; toolbar controls
(`dom_btn` → `_on_dom_toggled` → `_subscribe_dom`; `load_btn` → `load_chart`); the right dock
(`MainWindow.right_dock`, `QDockWidget("Active Trader", self)` + `setObjectName("Active Trader")`,
`setTitleBarWidget(self.active_trader.header_bar)`); order entry via
`active_trader.order_place_requested` → `MainWindow._on_order_place_requested` → `_place_order`;
portfolio closes via `portfolio_panel.group_close_requested`/`flatten_all_requested` →
`_on_portfolio_close_group`/`_on_portfolio_flatten_all` → `_close_position_by_id`.

**External integrations already in use**

IBKR TWS via official `ibapi` (pinned; **live port 7496 only**, fail-fast): `reqRealTimeBars`,
`reqMktData` (incl. S0 generic ticks `"292"` news / `"456"` dividends / **`"225"` auction**),
`reqHistoricalData`, **`reqMktDepth`/`cancelMktDepth`**, **`reqHistoricalTicks`**, `reqPositions`/
`reqAccountSummary`, `reqMatchingSymbols` (D39), `reqNewsProviders`/article fetch (D38),
`placeOrder`/`cancelOrder`/`reqGlobalCancel`, `reqContractDetails`. Secondary approved source:
yfinance (D38 corporate events, cached). Persistence: SQLite via `config/paths.get_db_path()`.
Packaging: PyInstaller `.app` (not exercised here). Tests: pytest + pytest-qt, offscreen only.

**Verified facts that shape D41 (source-validated 2026-10-15)**

1. **The retained order paths never call `validate_order()`.** `validate_order(...)` has exactly
   **one** production call site — `ui/main_window.py:3112`, inside `_place_order` — and `_place_order`'s
   only caller is `_on_order_place_requested` (`:3092`), which exists only for the **`OrderEntryWidget`
   ticket** (`active_trader.order_place_requested`, `:693`). `_close_position_by_id` (`:3446`) builds the
   order itself and calls `placeOrder` directly (`:3505`), with **no** validation and **no** connection
   guard; the D26.9 "never transmit while disconnected" guard also lives only in `_place_order`
   (`:3105`). `ui/stop_loss_target_dialog.py` places **no** orders at all (verified repo-wide: no
   `placeOrder` in the module). ⇒ After D41 the in-app ticket is gone, so both the validate gate and the
   disconnected guard would go with it unless they are **re-homed onto the surviving emitter** (`S5`).
2. **`ref_price`'s only consumer is the ticket path.** `ref_price=self.active_trader.last_price`
   (`:3116`); `last_price` was populated from the DOM depth feed (`_on_mkt_depth` →
   `active_trader.set_last_price`, `:3033`). Both ends are being removed.
3. **A retained, symbol-keyed price source already exists and is fed twice.** `_symbol_last_prices`
   (D27.5) is written by `_record_symbol_price` from (a) the watchlist price sink
   (`watchlist_panel.set_price_sink`, `:609`) and (b) **every aggregated chart bar**
   (`ui/ticker_session.py:863 → _host._record_symbol_price(self.symbol, bar.close)`), and is already
   the D27.5-mandated source for position market prices (`:3313`).
4. **The right dock is one `QDockWidget` titled *and* `objectName`d `"Active Trader"`** containing a
   right-dock container widget with `ActiveTraderPanel` stacked over `ActivePortfolioPanel`; its
   **title bar is the Active Trader header**, and the "both panels collapsed" state
   (`_sync_right_dock_collapse`, `:2494`) is the D21.13 region-collapse. **Title/`objectName`-keyed
   lookups exist in 15 test files** — `test_dock_widths_d17.py:37`/`:73`,
   `test_watchlist_d14_midrag.py:35`/`:82`, `test_crosshair_axis_lane.py:101`–`:106`/`:123`,
   `test_d27_position_prices.py:30`, `test_history_backfill.py:199`,
   `test_history_backfill_disconnect.py:136`, `test_dock_widths_d18.py:177`,
   `test_d10_d13_integration.py:35`/`:53`, `test_d27_account_subs.py:27`,
   `test_watchlist_columns_d21.py:308`/`:322`, `test_d27_phantom_alarms.py:56`,
   `test_d27_stream_health.py:67`, `test_history_backfill_loadpath.py:165`,
   `test_dock_d18_region.py:107`/`:110`, `test_d27_reconnect.py:163` — **plus 2 files asserting the
   dock's title-bar *text*** (`test_right_dock_d21.py:64`, `test_watchlist_nonregression_d22.py:142`)
   — **17 files total**, every one enumerated in the plan's Phase-2 `touches_files` map with the edit
   it needs. This is the repo's known "stable title/`objectName`" trap (the D19 masking trap): a
   title-keyed consumer left out of the map silently stops hiding/renaming anything, so its suite
   passes while exercising a window the app no longer has.
5. **Dock-width guards are pure and reusable unchanged:** `ui/dock_layout.py` imports no Qt symbol;
   `plan_dock_widths` owns the per-dock caps, the combined chart-minimum cross-clamp, and the
   never-below-dock-minimum guarantee (ESC-026 corrected). D41 changes **how many sections** the
   right dock hosts, not the geometry rules.
6. **`_md_line_count` (`:790`) sums RT + S0 + `depth_manager.active_feed_count()` + watchlist rows**;
   `_guard_depth_budget`/`DEPTH_FEED_CAP = 60` gate depth feeds only. `md_line_guard.assess` +
   `_guard_md_lines` are shared with **D38's S0 lines** (`ui/ticker_session.py:485`).
7. **The S0 substrate is shared:** `s0_register_many`/`_s0_needs`/`S0_TICKS`/`tick_generic`/
   `tick_string`/`tick_news` serve D38's `"292"`/`"456"`; only `attach_view`'s `{"auction": {"225"}}`
   registration and the auction ingress (`on_tick_price`/`on_tick_size`, `_auction`, `auction_state`)
   are D37.
8. **`ibkr/contracts.py::footprint_cache_key` + `INDEX_PROXY` are D39 load-bearing**
   (`ui/ticker_session.py:35`, `:922` — inside `_evaluate_burst_alarms`, the D39.3 burst evaluator;
   `services/alarm_monitor.py`, `ui/alarm_dialog.py`) — only `resolve_footprint_contract` is
   D36-exclusive.
9. **Toolbar geometry fixtures pin the control set** (`dom_btn` in `_CONTROL_NAMES` of
   `test_toolbar_scroll_d19.py:42` / `test_toolbar_d20.py:44`, and in `_CHECKABLE_TOGGLES` of
   `test_toolbar_d21.py:152`), and the toolbar's intrinsic width is font-dependent (1965 px @9 pt vs
   1921 px with Inter 11 px) — the D19/D20 hidden-toolbar **masking** trap applies.
10. **`tests/test_db_schema.py` subset-asserts** `EXPECTED_TABLES` (`:13`–`:24`; `footprint_cache` was
    never listed, and the assertion is `EXPECTED_TABLES <= tables`), so removing the DDL alone is
    silent — an explicit absence/drop assertion is needed.

### Tech Stack Decisions (D41 increment)

Constrained (existing) choices first, then the D41 additions/changes.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Existing-repo hard constraint; changing the stack is an explicit non-goal | Any new UI/charting framework — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi`, **live TWS 7496 only** (`check_live_port` fail-fast), numpy, SQLite via `config/paths.get_db_path()`, PyInstaller `.app`, pytest + pytest-qt offscreen (no live TWS, no order transmission) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB / new test framework — rejected |
| S3 | **Removal mechanism** `[new]` | **Whole-file deletion** for the 9 feature-exclusive production modules (`ui/footprint_item.py`, `ui/depth_heatmap_item.py`, `ui/active_trader_panel.py`, `services/footprint_service.py`, `services/depth_heatmap.py`, `data/footprint_cache.py`, `ibkr/tick_history.py`, `ibkr/market_depth.py`, `ibkr/order_book.py`) and the 5 feature/widget-scoped test suites (`S11`); **surgical in-file deletion** for the shared files (bridge/client/subscription/contracts/db/chart_panel/ticker_session/main_window/watchlist_panel/models). **No shim modules, no deprecation stubs, no commented-out code, no `# removed` placeholders** | `AC-D41.3` requires those paths to **no longer exist** and nothing to import or reference them; feature-exclusive modules have a zero-consumer blast radius once the call sites go. Stubs/comments would violate the "no dangling reference" clause and re-invite accidental re-wiring | (i) keep modules, drop call sites — fails `AC-D41.3`; (ii) keep modules with deprecation warnings — same, plus dead code; (iii) leave commented-out blocks as a record — reviewable history belongs to git/docs (DOC-4), not source |
| S4 | **`ref_price` retained source** `[new]` — closes **DG71(1)** | `ref_price` comes from the **D27.5 central `symbol → last_price` map** (`ui/main_window.py::MainWindow._symbol_last_prices`, `:727`), read through one small accessor `MainWindow._ref_price_for(symbol) -> float \| None` (normalises to upper-case; returns `None` when a symbol has no recorded price). No other source is consulted. Rationale: the map is **already the D27.5-mandated price source for position market prices** and is fed by **both** the watchlist tick sink and **every aggregated chart bar** (`ui/ticker_session.py:863`), so it resolves for any symbol that is on the **watchlist** or has a **live chart session** — the map is symbol-keyed, not reqId-keyed or session-scoped, which is what the retained close path needs. A symbol in neither source returns `None`, which is safe: `validate_order` already skips the notional check when no positive price basis exists (`ibkr/validation.py:62`–`:72`), so an unknown price can never fabricate a rejection | (i) session `last_chart_price` — single-symbol, primary-chart-only, and semantically "the chart's price", not the position's own symbol (precisely why D27.5 introduced the map) — rejected; (ii) `WatchlistPanel._last_price` — keyed by `reqId` inside panel internals, not symbol-keyed — rejected; (iii) re-derive from the removed DOM feed — impossible; (iv) `positions.market_price` from the DB — a stale persisted value, not a live reference — rejected |
| S5 | **Retained order path carries the surviving D26 gates** `[new/changed]` — **revises the D26/`_place_order`-scoped arrangement** (its ticket surface is removed by D41) | `MainWindow._close_position_by_id` (the **only** production order emitter after D41) becomes, in order: (1) the **D26.9 disconnected guard** (refuse + status-bar message, never transmit), (2) `validate_order(action=…, order_type="MKT", qty=close_qty, symbol=symbol, ref_price=self._ref_price_for(symbol), risk_reducing=True)`, (3) the existing `order_limiter` pacing/deferral, (4) `placeOrder`. `ibkr/validation.py::validate_order` gains one **additive** keyword `risk_reducing: bool = False`; when `True` the **notional-cap check is skipped** and **every structural check still applies**. `_place_order` and `_on_order_place_requested` (ticket-only) are deleted with the ticket, and `ibkr/validation.py`'s **module docstring** (`:5`, which today says the gate is "Wired at the top of `MainWindow._place_order`") is **re-pointed at the retained emitter** `MainWindow._close_position_by_id` — the symbol it names must still exist after D41 | `AC-D41.4` requires the retained machinery to be "exercised" and the retained paths to "build and validate orders with a **resolving `ref_price`**", and D41's KEEP list says **D26's safety requirements stand**. Today the gate and the disconnected guard are reachable *only* from the deleted ticket, so leaving them in place would make `validate_order`/`ref_price` dead on the retained path while the app's only order emitter ran ungated — the D26.9 defect class (order "Submitted" against a dead socket) reopened. The `risk_reducing` carve-out is required because the cap exists to bound **new** exposure: without it, a position above USD 25,000 could never be flattened from the UI (a real availability regression, not a hypothetical) | (i) **no gate** — `validate_order` becomes production-dead, `ref_price` consumerless, `AC-D41.4`'s `ref_price` clause unmet — rejected; (ii) **gate without the carve-out** — blocks legitimate >25 k flattens — rejected; (iii) **gate with `ref_price=None`** — the notional check is skipped only *incidentally*, `ref_price` stays meaningless, and a future cap change would silently start blocking closes — rejected; (iv) a separate `validate_close_order()` — duplicates the gate (two divergent implementations; the ESC-026 anti-pattern) — rejected; (v) keep `_place_order` alive as a helper — it is ticket-only by construction (`AC-D41.3` forbids the ticket) — rejected |
| S6 | **Portfolio-only right dock** `[new/changed]` — **supersedes D18/B2's two-section region**, `AC-D18.3`, and D21.13's Active-Trader-title-bar clauses | **One** `QDockWidget`, `windowTitle()` **and** `objectName()` = **`"Portfolio"`**, whose widget is the existing `ActivePortfolioPanel` **directly** (the right-dock container widget, `_right_dock_layout` and the two-panel stretch juggling are deleted). Its **title-bar widget IS the Portfolio panel's `summary_label`** (`DiagonalStrikeButton("Account Summary")`) — so there is still exactly one visible label and it is the hide/show toggle — native title hidden (`Movable`/`Floatable` features unchanged). Collapse = that single section's body hidden; the collapsed state is the region-collapse state. `RIGHT_DOCK_MIN_WIDTH` stays **200**; the collapsed floor stays `max(RIGHT_DOCK_COLLAPSED_MIN_WIDTH=150, summary_label.sizeHint().width() + 2×RIGHT_DOCK_COLLAPSED_MARGIN)` (the existing formula, now over **one** button); **`RIGHT_DOCK_CAP_FRACTION` stays 0.40** and **`ui/dock_layout.py` + `plan_dock_widths` are unchanged** | `AC-D41.7` fixes the *outcome* (single Portfolio section, non-zero width, fully visible in full screen, clamped against the chart minimum) and leaves the *mechanism* to Plan (DG71). Reusing D21.13's affordance + the untouched pure clamp means the surviving D18 guarantees (incl. the original D17/D18 full-screen symptom and the ESC-026 floor fix) hold **by construction** rather than by re-derivation. The 40 % cap is an **upper bound** — keeping it removes no user capability, is DG71's explicitly blessed default, and is the only non-regressive choice; the 200 px minimum is what `plan_dock_widths` already enforces. The **rename** is deliberate: a Portfolio-only dock titled/`objectName`d `"Active Trader"` would keep a live "Active Trader" identifier in the UI and code after `AC-D41.1` forbids every Active-Trader affordance; the repo's title-keyed-lookup trap is handled by enumerating **all 17** title/`objectName`/title-bar-text consumers, and the new dock guard asserts exactly one dock titled `"Portfolio"` and **no** `"Active Trader"` dock/widget (neutralising the D19 masking risk) | (i) keep the old title to avoid touching those 17 files — rejected: leaves a live Active-Trader identifier and fails `AC-D41.1`'s intent; (ii) keep both sections with the Active Trader one emptied — rejected: a dead section is not "Portfolio-only" and keeps the container/stretch juggling; (iii) raise the cap or drop it — rejected: `AC-D18.2`'s 0.40 cap survives in the requirement and the chart-minimum clamp is the D17/D18 guarantee |
| S7 | **`footprint_cache` deletion** `[new/changed]` — closes **DG70** / A69 (Q49 = "delete") | Remove the `footprint_cache` **DDL** from `data/db.py::_init_schema` (`:118`–`:127`; fresh DBs never create it) **and** add an idempotent **`DROP TABLE IF EXISTS footprint_cache`** to `data/db.py::_migrate_schema()` (which already runs on every `DB()` open, alongside the existing additive `ALTER TABLE`s and the `idx_positions_symbol_con_id` index). Delete `data/footprint_cache.py`. Net effect on an existing user DB: table + rows gone at the next app start | The requirement asks for a "small migration" (A69/Q49 "delete"), and `_migrate_schema()` **is** this repo's migration mechanism: it already runs unconditionally at open, needs no version table, and `IF EXISTS` makes it a one-time, idempotent, crash-safe no-op afterwards. `DROP TABLE` (not `DELETE FROM`) is the recorded default (DG70 (b)) since the owning feature is removed | (i) **delete rows, keep the empty table** — DG70 (a); rejected per A69/DG70's recorded default (orphan schema for a removed feature); (ii) **standalone one-off script / manual `sqlite3` step** — rejected: there is no migration runner in this repo and an owner-run step would simply never happen for existing installs; (iii) **a versioned migration framework** — over-engineering for one drop — rejected; (iv) **keep the DDL, empty the table** — fresh DBs would recreate dead schema, contradicting A69's DDL-removal clause — rejected |
| S8 | **Subscription/registry surface** `[new/changed]` | Delete `DEPTH` (`ibkr/subscription_manager.py:37`) and `DEPTH_HEATMAP` (`:38`); keep `RT_BARS`, `MARKET_DATA`, `S0_TICKS`. Delete `MainWindow._guard_depth_budget` and `DEPTH_FEED_CAP`; **remove only the `depth` term** from `_md_line_count` (RT + S0 + watchlist terms stay). `services/md_line_guard.py::assess` and `MainWindow._guard_md_lines` are **unchanged** (D38's S0 lines use them) | Nothing subscribes with those tags once the depth feed and the ladder are gone; `S0_TICKS` is D38's (`"292"`/`"456"`). Keeping unused tags/caps would leave dead constants that invite a future mis-subscribe, and the depth term in the line count would reserve budget for a feed that cannot exist | (i) keep the tags/constants — dead surface, no benefit — rejected; (ii) keep the `depth` term in `_md_line_count` — inflates the count against no consumer — rejected; (iii) also drop `md_line_guard` — breaks D38 — rejected |
| S9 | **Bridge / client surface** `[new/changed]` | Delete exactly: `Bridge.historical_ticks_bid_ask`, `Bridge.historical_ticks_last`, `Bridge.update_mkt_depth`, and the overrides `IBApiClient.historicalTicksBidAsk`, `historicalTicksLast`, `updateMktDepth`, `updateMktDepthL2`. **Keep** the S0 overrides (`tickGeneric`, `tickString`, `tickNews`) and their signals (D38) | `AC-D41.2` demands **zero** `reqMktDepth`/`cancelMktDepth` of any kind and zero historical-ticks requests. Removing the overrides also makes a stray `updateMktDepth` callback from `ibapi` a **no-op** at the client boundary instead of a routed DOM update — the removal is enforced at the integration edge, not only at the call sites | (i) keep the overrides but ignore their payloads — silent dead path, still routes nothing but keeps the D37 signal surface — rejected; (ii) keep the signals for symmetry — dead signal — rejected |
| S10 | **Contract resolver surface** `[new/changed]` | Delete `ibkr/contracts.py::resolve_footprint_contract` (`:160`+, D36-only). **Keep `footprint_cache_key` (`:144`) and `INDEX_PROXY` (`:133`)** verbatim — D39's burst baseline key (`ui/ticker_session.py:922`) and D39's `alarm_monitor`/`alarm_dialog` proxy resolution depend on them | `AC-D41.4` names both as required survivors. The D36-derived **name** of `footprint_cache_key` is a recorded naming smell (DG67 → FS17) and a **non-requested refactor**: renaming it is out of D41's scope | (i) rename `footprint_cache_key` to a neutral name as part of D41 — rejected (unrequested refactor, touches D39's tested surface); (ii) inline the key rule into `ticker_session` and delete it — rejected (breaks `AC-D41.4`, duplicates the rule) |
| S11 | **Test surface** `[new/changed]` | **Delete** `tests/test_d36_footprint.py`, `tests/test_d37_microstructure.py`, `tests/test_market_depth.py`, `tests/test_order_entry_mkt.py`, `tests/test_order_entry_side.py` (all five feature/widget-scoped). **Re-point** (not delete): `test_order_validation.py`, `test_order_rejections.py`, `test_dock_d18_region.py`, `test_right_dock_d21.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_dock_widths_d17.py`, `test_watchlist_nonregression_d22.py`, `test_d27_reconnect.py` (Phase 1: drop the D37 session-depth assertions and re-derive the replayed `mkt_data` count, keep RT/S0/watchlist replay **and** the DOM-depth assertions; Phase 2: the dock-title tuple → `"Portfolio"`), **the 15 title/`objectName`-keyed dock consumers**, **`test_d28_pacing.py`** (the D28.1 order-path deferral re-pointed at the retained close emitter), **`test_kill_switch.py`** (D26.8's all-three-bracket-legs assertion re-pointed at the retained builders — never deleted), the four dock-hide helpers (`test_watchlist_d14_midrag.py`, `test_d27_position_prices.py`, `test_history_backfill.py`, `test_history_backfill_disconnect.py`), `test_crosshair_axis_lane.py`, and the toolbar control lists (`test_toolbar_scroll_d19.py`, `test_toolbar_d20.py`, `test_toolbar_d21.py` → drop `dom_btn`). **Add** `tests/test_d41_removal.py`, `tests/test_d41_portfolio_dock.py`, `tests/test_d41_retained_order_path.py`; **extend** `tests/test_db_schema.py`; and **re-home two KEEP-coverage tests** into surviving suites in the phase that deletes the old suite (R2): `test_footprint_cache_key_rollover_isolates_tape` → `tests/test_d39_burst_search.py`, `test_md_line_guard_thresholds` → `tests/test_d38_events_news.py` | The five deleted suites are feature- or widget-scoped (verified: the two order-entry suites import **only** `ui.active_trader_panel`); every suite that also guards a retained path is **re-pointed, never discarded** (`AC-D41.4`'s "remain exercised by their tests"). The title-keyed consumers must move **with** the rename or they silently mask (AR-D41-3). The two re-homes preserve the KEEP list's coverage rather than dropping it with the deleted suites | (i) delete the order-path suites too — drops D26.8's only all-three-legs test and D28.1's order-path deferral — rejected; (ii) leave the title-keyed tuples stale — the D19/D21 masking trap — rejected; (iii) keep the two KEEP tests inside a deleted suite by copying the suite — rejected: dead file with two live tests |
| S12 | Testing `[existing]` | pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), **no live TWS, no transmitted orders**; run as `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale shebang); any non-pytest probe that can reach a DB-writing path **must** export `DB_PATH` to a temp file (ESC-043: an unset `DB_PATH` writes the owner's production DB) | Repo standard (Q8/Q9) + the repo's own recorded gotchas | Manual-only / live-TWS verification — rejected (`AC-G` and Q9) |

### System Components (D41 increment)

**Removed** (`[existing → deleted]`)

| Component | Files | Notes |
|---|---|---|
| Footprint render layer + controls | `ui/footprint_item.py`; the `Footprint`/`Classic`/`Tick count` cluster + `footprint_static`/`footprint_live`/`_fp_*`/`refresh_footprint`/`_fp_status_text` and the `footprint_toggled`/`footprint_viewport_changed` signals in `ui/chart_panel.py` | `AC-D41.1` |
| Footprint service / cache / tick history | `services/footprint_service.py`, `data/footprint_cache.py`, `ibkr/tick_history.py`; the filename/wave/forming/cache state in `ui/ticker_session.py`; the `historical_ticks_*` signals in `ibkr/bridge.py` + the `historicalTicks*` overrides in `ibkr/client.py`; `ibkr/contracts.py::resolve_footprint_contract` | `AC-D41.3` |
| Depth heatmap / IMB / AUC | `ui/depth_heatmap_item.py`, `services/depth_heatmap.py`; the `Depth`/`IMB —`/`AUC —` cluster, heatmap strip, state text, 500 ms repaint timer and `bind_d37_session`/`unbind_d37_session`/`set_depth_state`/`update_auction_chip` in `ui/chart_panel.py`; `_depth`/`_depth_req_id`/`_depth_holders`/`_depth_state`/`ensure_depth_subscribed`/`release_depth`/`_cancel_depth`/`_reissue_depth`/`_rebind_depth_req_id`/`on_depth_update`/`on_depth_error`/`_set_depth_state`/`depth_imbalance`/`_depth_roll_timer` and the `depth_state_changed`/`auction_updated` signals in `ui/ticker_session.py`; the `"225"` auction need + auction ingress; `subscription_manager.DEPTH_HEATMAP` | `AC-D41.1`/`AC-D41.2` |
| Active Trader panel (whole) + DOM ladder | `ui/active_trader_panel.py` (ladder/book **and** `OrderEntryWidget` ticket **and** the panel shell/`header_bar`); `ibkr/market_depth.py`; `ibkr/order_book.py`; the `DOM` toolbar button + `_on_dom_toggled`/`_subscribe_dom`/`_on_mkt_depth`/`_depth_req_id`/`_rebind_depth_req_id`/the depth error branch/`closeEvent`'s depth cancels in `ui/main_window.py`; `ui/watchlist_panel.py::set_depth_manager`/`on_depth_update`/`_depth_manager`; `subscription_manager.DEPTH`; `Bridge.update_mkt_depth` + the `updateMktDepth*` overrides | `AC-D41.1`/`AC-D41.3`; makes ESC-039/ESC-035/ESC-040 moot (DG66) |
| Depth feature's model | `data/models.py::OrderBookLevel` (`:105`–`:110`) | **Dead today** — zero references in the tree (verified). Included as an **explicit scope close-out** under `### D41`'s "all associated code" (a deliberate, named inclusion — not an undeclared extra), machine-checked by the removal guard's token set (**FI-2**, accepted by the Validator) |
| Persisted footprint data | `footprint_cache` DDL in `data/db.py` + `DROP TABLE IF EXISTS` in `_migrate_schema()` (`S7`) | Q49/A69/DG70 |

**Retained, unchanged** `[existing]`

`ibkr/orders.py` (incl. `bracket_order`), `ibkr/validation.py` (**function body unchanged** — one
additive keyword, `S5`), `ibkr/id_manager.py`, the kill switch (`reqGlobalCancel` + per-ID cancels),
the order registry / order-error routing, `config/settings.py::check_live_port` + `MAX_ORDER_NOTIONAL`;
the D38 S0 substrate (`s0_register_many`/`S0_TICKS`/`tick_generic`/`tick_string`/`tick_news` +
overrides), `services/volume_baseline.py` + the `volume_baseline` table,
`ibkr/contracts.py::footprint_cache_key`/`INDEX_PROXY`, `services/md_line_guard.py`, `data/db.py`'s
other tables, and the yfinance event source (D38) — i.e. **nothing D1–D35 or D38–D40 depends on is
redesigned**.

**KEEP-list coverage is preserved, not just the symbols.** Every `AC-D41.4` survivor keeps a test in
the post-D41 tree: `footprint_cache_key` (its only test,
`tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape`, moves to
`tests/test_d39_burst_search.py`) and `services/md_line_guard.py::assess` (its only test,
`tests/test_d37_microstructure.py::test_md_line_guard_thresholds`, moves to
`tests/test_d38_events_news.py`) — both re-homed in the same phase that deletes the suite they lived
in. `INDEX_PROXY`/`S0_TICKS`/`volume_baseline` keep their existing D38/D39 suites; `bracket_order`
keeps `tests/test_order_builders.py`; the kill switch keeps `tests/test_kill_switch.py` with its
all-three-legs assertion re-pointed at the retained builders.

**New / changed** `[new/changed]`

| Component | Change |
|---|---|
| `MainWindow._ref_price_for(symbol)` | New tiny accessor over `_symbol_last_prices` (`S4`) |
| `MainWindow._close_position_by_id` | Gains the disconnected guard + `validate_order(..., risk_reducing=True, ref_price=…)` before the existing pacing + `placeOrder` (`S5`) |
| `ibkr/validation.py::validate_order` | One additive keyword `risk_reducing: bool = False` (default preserves all existing behaviour and tests) (`S5`); its module docstring re-pointed at the retained emitter |
| `MainWindow` right dock | Portfolio-only single-section dock (`S6`); `_compute_right_dock_collapsed_min_width` now reads one button; `_sync_right_dock_collapse` loses the two-panel stretch juggling |
| `data/db.py::_migrate_schema` | Adds `DROP TABLE IF EXISTS footprint_cache` (`S7`) |
| `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`, `ibkr/contracts.py`, `ui/watchlist_panel.py`, `ui/dock_layout.py` | Deletions only (no new behaviour) |
| `ui/active_portfolio_panel.py` | **Not modified.** Its `summary_label`/`body`/`is_collapsed()` are reused as-is by the new dock. (Deliberate: ESC-043/ESC-045 live in this file's render path and are **not** D41's to fix.) |

### Data Model (D41 increment)

| Entity | Status | Key fields / notes |
|---|---|---|
| `footprint_cache` (SQLite) | `[existing → removed]` | `resolved_contract`, `date`, `timeframe`, `blob` (PK on the first three). DDL leaves `data/db.py`; an existing DB's table is dropped by the idempotent `_migrate_schema()` step (`S7`) |
| `data/models.py::OrderBookLevel` | `[existing → removed]` | `position`, `side`, `price`, `size`, `market_maker`; zero references (`S3`; **FI-2**, accepted scope close-out) |
| `data/footprint_cache.py::FootprintCache` / `is_cacheable` | `[existing → removed]` | Module deleted with the DDL |
| `volume_baseline` (SQLite) | `[existing]` | D39; untouched — `AC-D41.4` |
| `yfinance_events_cache` (SQLite) | `[existing]` | D38; untouched |
| `positions`, `trade_groups`, `position_group_map` | `[existing]` | Untouched (D27.5 / Phase 7). `positions.id` remains the SL/TP + close key |
| `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `popouts` | `[existing]` | Untouched |
| `MainWindow._symbol_last_prices` (in-memory) | `[existing]`, **newly consumed** `[new/changed]` | Becomes the retained `ref_price` source (`S4`); already fed by the watchlist sink and every aggregated chart bar |
| `MarketDepthManager._feeds` / `_shared` (in-memory) | `[existing → removed]` | Whole manager deleted |
| `OrderBook` / `Level` (in-memory) | `[existing → removed]` | `ibkr/order_book.py` deleted |
| ladder/book state dicts in `ui/active_trader_panel.py` | `[existing → removed]` | Module deleted |

**No new entity, no new column, no field-level change.** The only schema delta is a **drop**.

### Integration Points (D41 increment)

| Integration | Status | Why |
|---|---|---|
| IBKR `reqMktDepth` / `cancelMktDepth` | `[existing → removed]` | Both the heatmap's refcounted SMART feed and the ladder's direct feed go; `AC-D41.2` requires **zero** of any kind |
| IBKR `reqHistoricalTicks` | `[existing → removed]` | D36 footprint pages |
| IBKR `reqTickByTickData` | `[existing]` — **never used** and still not used | `AC-D41.2` requires zero; removal makes it structurally impossible |
| IBKR generic ticks `"225"` (auction) via `reqMktData` | `[existing → removed]` | `AC-D41.2` |
| IBKR S0 generic ticks `"292"` (news) / `"456"` (dividends) via `reqMktData` | `[existing]` | D38 still needs them (`AC-D41.4`); the S0 substrate stays |
| IBKR `reqRealTimeBars`, `reqHistoricalData`, `reqContractDetails`, `reqPositions`, `reqAccountSummary`, `reqMatchingSymbols` (D39), `reqNewsProviders` (D38) | `[existing]` | Untouched |
| IBKR `placeOrder` / `cancelOrder` / `reqGlobalCancel` | `[existing]` | Retained; after D41 the **only** emitter is Portfolio Close / Close Group / Flatten All (+ the kill switch). `bracket_order` survives as retained machinery, exercised by its own tests |
| yfinance (D38 corporate events) | `[existing]` | Untouched |
| SQLite (`config/paths.get_db_path()`) | `[existing]` | One fewer table; `DB_PATH` hermeticity rules apply to every new test (`S12`) |
| **New integrations** | — | **None.** D41 adds no external dependency |

### Non-Functional Approach (D41 increment)

- **Performance / work per tick** (driven by `AC-D41.1`/`AC-D41.2`). Removing the 500 ms
  `_depth_refresh_timer` repaint, the depth-op ingress, the two `FootprintItem` render layers and the
  footprint backfill wave removes per-tick and per-op work from the chart and the session. The §7
  market-data line count loses its `depth` term and `DEPTH_FEED_CAP` disappears, so a removed feed can
  no longer consume budget. **No** change to the candle/volume rendering math
  (`ui/candlestick_item.py::ChartMode` paint path, the volume width path) — deliberately, because
  **ESC-041/ESC-042 own that defect** (FI-3).
- **Pacing (D28.3/D28.4 guarantees preserved).** The footprint wave's `reqHistoricalTicks` pages and
  the depth subscriptions leave the historical/market-data budget; `ibkr/pacing.py`, the order token
  bucket (`order_limiter`) and the RT-bar budget are untouched. The retained close path keeps using
  `order_limiter` and its `QTimer.singleShot` deferral (`S5` step 3).
- **Safety / security** (driven by D26 standing + `AC-D41.4`). The in-app order ticket goes, so no UI
  path can compose an arbitrary order; the surviving close/flatten path is *gated* rather than
  ungated (`S5`): disconnected ⇒ refuse; structural validation always; notional cap for
  risk-increasing orders only. The kill switch, order-ID reservation, order-error routing and the
  fail-fast live-port check are untouched. No test transmits an order or connects to TWS (`S12`).
- **Scalability / session hygiene.** Depth refcounting per symbol disappears, so
  `SubscriptionManager` carries fewer entries per session and the post-reconnect replay set shrinks
  (`tests/test_d27_reconnect.py` counts are **re-derived**, not weakened — AR-D41-5). Session teardown
  loses the depth/footprint branches, shrinking the teardown surface.
- **Observability.** The removed user-visible states (`Footprint loading…`, `No tick data for …`,
  `Depth unavailable`/`Depth subscription required`, the ladder/book tabs) disappear with their
  features. The **retained** path's feedback is the status bar (rejections, pacing deferral, close
  confirmations) — `MainWindow._on_order_error` already writes
  `status_bar.showMessage(f"Order #{order_id} {status}: {error_string}")` (`:1706`), so the ticket
  line drops without losing the surfaced message (AR-D41-1).
- **Maintainability / docs.** 9 production modules and 5 suites leave the tree. `AC-D41.6`'s
  markdown-history markers (`SUPERSEDED BY D41` on `### D36`/`### D37` + the D18/D21.13 notes) are
  already present in `requirements.md` and are **Requirements-owned** — Build must not edit that file.
  The `footprint_cache_key` naming smell stays recorded as FS17 (`S10`).

### Architecture Risks (D41 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D41-1 | A **retained** path silently depends on something deleted — e.g. `_update_order_status`/`_on_order_error` calling `active_trader.set_order_status`, `closeEvent`'s depth cancels, `_rebind_depth_req_id` in the reconnect replay, or the `depth` term in `_md_line_count` | **H** | Every `active_trader.*`/`depth_manager.*`/`_depth_req_id` reference is enumerated by file in the plan's `touches_files` map; the ticket-line calls become status-bar-only (`:1706` already writes the status bar); the new `tests/test_d41_removal.py` scans the whole production+test tree for the removed identifiers and the reconnect suite re-verifies replay after the edits |
| AR-D41-2 | **Dead imports** left in `ui/main_window.py` (`TickHistoryManager`, `FootprintCache`, `MarketDepthManager`, `DEPTH`/`DEPTH_HEATMAP`, `ActiveTraderPanel`, `on_depth_callback`, `FootprintItem`, `DepthHeatmapItem`, `resolve_footprint_contract`) — the tree imports fine today and would fail only at run time for some, at import for others | **H** | The import guard asserts `importlib.util.find_spec(...) is None` for each deleted module **and** greps `ui/`, `ibkr/`, `services/`, `data/`, `config/`, `tests/`, `main.py` for the identifiers; the UI smoke path (`MainWindow()` construction) runs in the same suite. The `MarketDepthManager` import (`:35`) and the `self.depth_manager` construction (`:560`) go in **Phase 2**, when their last consumers do |
| AR-D41-3 | The dock **rename** quietly defuses the title-keyed dock-hiding helpers, so geometry tests keep passing while exercising a window the app does not have (exactly the D19 masking trap) | **M** | The plan enumerates **all 17** consumer files — 15 `windowTitle()`/`objectName()` lookups + 2 title-bar-text assertions — one by one with the edit each needs (`S11`; `docs/plan.md` Phase 2). The new dock suite asserts **exactly one** right dock, titled/`objectName`d `"Portfolio"`, that it is the Portfolio panel, and that **no** dock/widget titled `"Active Trader"` exists anywhere — a stale tuple is then detectable, not silent |
| AR-D41-4 | Toolbar geometry fixtures pin `dom_btn` **and** a font-dependent intrinsic width (1965 px @9 pt vs 1921 px with Inter 11 px); removing the button changes the fixture baseline | **M** | Drop `dom_btn` from `_CONTROL_NAMES`/`_CHECKABLE_TOGGLES`; re-run the D19/D20/D21 geometry suites; the toolbar only gets **narrower**, so overflow assertions stay satisfiable — never lower an assertion below a measured width |
| AR-D41-5 | `tests/test_d27_reconnect.py` asserts replayed subscription **counts** (`len(fake.mkt_depth)`, `len(fake.mkt_data) == 4`, per-reqId rebinding) that the removal changes | **H** | The D37 session-depth assertions are dropped **and** the replayed `mkt_data` count re-derived from the surviving watchlist row + S0 line **in Phase 1** (where their subjects go); the DOM-depth assertions are kept until **Phase 2** (where `_subscribe_dom`/`_depth_req_id` go) and its one dock-title line moves in Phase 2 with the rename; the RT/S0/watchlist replay + rebinding assertions (the real D27.3 guarantee) are preserved verbatim throughout as a deliberate **two-phase, disjoint-line** edit |
| AR-D41-6 | Deleting `_place_order` takes the D26.9 disconnected guard and the validate gate with it, leaving the surviving close/flatten path ungated (**reopens the defect class the ticket path had fixed**) | **H** | `S5` re-homes both gates onto `_close_position_by_id`, with new tests: disconnected close refuses + no `placeOrder`; invalid close refuses; valid close transmits exactly once with a resolved `ref_price`. The two existing suites that drove the **deleted** `_place_order` are **re-pointed at the retained path**, not left red: the D28.1 order-path deferral (`tests/test_d28_pacing.py`) and D26.8's all-three-bracket-legs transmit-time registration (`tests/test_kill_switch.py`, the only test of that property) |
| AR-D41-7 | The notional cap blocking a legitimate large flatten if the `risk_reducing` carve-out is implemented wrong (or applied where it should not be) | **M** | Carve-out is a single new keyword **defaulting to False** (no existing caller's behaviour changes); asserted both ways: a >USD 25 000 close transmits, and a risk-increasing `validate_order` call above the cap is still rejected (`tests/test_order_validation.py`'s existing notional tests stay untouched) |
| AR-D41-8 | `AC-D41.1`'s ban on any `footprint_*`/`depth_*`/`auction_*` signal or attribute is a **broad** surface — a stray leftover (`_fp_queue_viewport_sync`, `_depth_state_text`, `depth_enabled`, `bind_d37_session`, `auction_state`, `_auction`, `set_depth_state`) fails it | **M** | The guard enumerates the token set (including `hasattr` probes on a real `ChartPanel`/`MainWindow`) and is **red before** the change; the removal tasks are scoped per file so nothing is half-removed |
| AR-D41-9 | D41 is credited with fixing the wide-candle / volume-overlap defect (DG68 still **open**), while the concluded investigation proves the cause is the D6 4-px floor vs inter-bar pitch in `ui/candlestick_item.py:122`–`:138` + the chart volume width path (`ui/chart_panel.py:1688`–`:1690`) and rules the footprint overlay **out** | **M** | Explicitly out of D41's blast radius: `ui/candlestick_item.py` and the volume-width math are **untouched**; **ESC-041 stays open and BUILD-owned and is `blocking` in `escalations.json`**; DG68 is flagged (**FI-3**) so the removal is not sold as a fix. Evidence: `docs/code_review/candle_overlap_investigation.md` §1/§2 (lead 3)/§4 |
| AR-D41-10 | A removal pass touches shared files three times (chart_panel / ticker_session / main_window / bridge / client / subscription_manager), and `ui/main_window.py` line numbers are cited across the docs — churn invalidates citations and invites merge conflicts | **M** | Phases are **strictly ordered** (one phase's wave consolidated before the next opens) and each phase's `touches_files` is **disjoint**, so no two workers edit the same file in a wave; the file map is published per phase; docs citations are re-anchored per the citation convention (`path::symbol` is the durable form) |
| AR-D41-11 | Junk/foreign rows or a non-hermetic probe DB (ESC-043) surfacing as false failures while validating the dock/portfolio geometry | **M** | Every new test constructs its window like the existing suites (monkeypatched `connect`, `tests/conftest.py` sets `DB_PATH` to a temp file); no probe writes to the user-space DB (`S12`) |
| AR-D41-12 | Orphaned `__pycache__` for the deleted modules (the DOC-3/ESC-001 precedent) making an import guard pass or fail confusingly | **L** | The guard asserts on `find_spec`/source paths, not on cached artefacts; the verification phase runs from a clean tree |

### Implementation sequencing (D41 increment)

Three phases, **strictly ordered** — each phase's wave is fully consolidated before the next opens,
because six production files receive edits in more than one phase. The authoritative phase/per-file
partition is `docs/plan.md` § *D41 — Batch 18 removal*.

1. **Phase 1 — remove the D36 footprint *and* D37 depth/heatmap/imbalance/auction feature trees.**
   **20 file entries.** Deletes 6 production modules + 2 suites; surgical deletions in
   `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`, `ibkr/bridge.py`,
   `ibkr/client.py`, `ibkr/subscription_manager.py`, `ibkr/contracts.py`, `data/db.py`; one docstring
   de-reference (`services/md_line_guard.py`); the `footprint_cache` drop; three test edits —
   `tests/test_d27_reconnect.py` (the D37 session-depth assertions + the replayed-count
   re-derivation) and the **two KEEP-coverage re-homes** (`tests/test_d39_burst_search.py`,
   `tests/test_d38_events_news.py`). Depends on: nothing.
2. **Phase 2 — remove the Active Trader panel + DOM ladder + market-depth machinery, re-shape the
   right dock Portfolio-only, and re-home the retained order gates.** **39 file entries.** Deletes 3
   production modules + 3 suites; edits `ui/main_window.py` (incl. the now-dead `MarketDepthManager`
   import and `self.depth_manager` construction), `ui/watchlist_panel.py`, `data/models.py`,
   `ui/dock_layout.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`,
   `ibkr/validation.py`; re-points the dock/toolbar/order suites **and all 17 title/title-bar
   consumers**, plus `tests/test_d28_pacing.py`, `tests/test_kill_switch.py`,
   `tests/test_crosshair_axis_lane.py`, the four dock-hide helpers, and the one dock-title line in
   `tests/test_d27_reconnect.py` (`S11`). Depends on: Phase 1 (shared files).
3. **Phase 3 — non-regression verification.** **4 file entries.** Adds `tests/test_d41_removal.py`
   (widened token set + documented allow-list), `tests/test_d41_portfolio_dock.py`,
   `tests/test_d41_retained_order_path.py`; extends `tests/test_db_schema.py`; full offscreen suite
   green (`AC-D41.5`); D38/D39/D26 spot checks (`AC-D41.4`). Depends on: Phases 1–2.

**Not in D41 (must not be touched):** `ibkr/orders.py`, `ibkr/id_manager.py`, `ibkr/error_codes.py`
(outside the `S5` keyword), `config/settings.py`'s `check_live_port`/`MAX_ORDER_NOTIONAL`/pacing
constants, `services/volume_baseline.py`, `services/md_line_guard.py` (function),
`data/events/*`, `ibkr/news.py`, `ui/news_digest_dock.py`, the D39 search path,
`ui/candlestick_item.py`, `services/backfill_service.py`, `services/market_calendar.py`,
`ui/active_portfolio_panel.py`, and **every** escalation D41 does not moot
(ESC-032/033/034/036/037/**038**/041/042/043/044/045 — **11** `open` entries; ESC-035/039/040 are
mooted by the removal per DG66 and are the **Code Reviewer's** to close after re-verification, not
Build's).

### Supersessions (D41 increment)

| Superseded | By D41 | Posture |
|---|---|---|
| `## D36 increment` (footprint charts) — the whole surface | Removed | The D36 section above stays as the as-built record of what was built; it carries a supersession marker. `AC-D36.*` carry `SUPERSEDED BY D41` in `requirements.md` (DOC-4) |
| `## D37 increment` (microstructure) — the whole surface | Removed | Same; `AC-D37.*` carry `SUPERSEDED BY D41`. The **S0 substrate** D37 introduced is explicitly **kept** (D38 reuses it) — D37's supersession removes its depth/IMB/AUC/auction surface only |
| D18 / B2 two-section right dock; **`AC-D18.3`** (equal width by construction) | Portfolio-only single-section dock (`S6`) | Superseded in `requirements.md` with a reason. **Every surviving D18 outcome still holds** (`AC-D18.1` visibility, `AC-D18.2`'s 0.40 cap — the numeric cap survives *in the AC*, `AC-D18.4`–`AC-D18.7`), asserted by `tests/test_d41_portfolio_dock.py` |
| D21.13's Active-Trader-title-bar clauses | The Portfolio panel's `summary_label` becomes the dock's title-bar widget | The **strike-through / collapse affordance itself** survives on the retained Portfolio toggle |
| D26's order-entry surface (the `_place_order`-scoped arrangement) | `S5`: the surviving gates re-home onto `_close_position_by_id` | D26's **safety requirements stand** and are strengthened onto the only surviving emitter; D26's ticket-scoped tests are re-pointed, not deleted |

### Flagged issues and Validator dispositions (D41 increment)

- **FI-1 — `AC-D41.4`'s "the retained order paths … still build and **validate** orders with a
  resolving `ref_price`" is not what the code does.** Verified 2026-10-15: `validate_order()` has
  exactly one production call site (`ui/main_window.py:3112`, inside the ticket-only `_place_order`),
  while `_close_position_by_id` (`:3446`) calls `placeOrder` (`:3505`) with **no** validation and
  **no** disconnected guard; `ui/stop_loss_target_dialog.py` contains **no** `placeOrder` anywhere
  (verified repo-wide), so the AC's SL/TP limb is vacuous and `tests/test_sltp_honesty.py:16`/`:24`
  asserts only the dialog's disclosure label. **Disposition (Validator, cycle 1): RATIFIED as reading
  (a), NON-BLOCKING** — re-homing the gates (`S4`+`S5`) is what `AC-D41.4` and the KEEP list demand;
  it is not scope addition and not an invention; `DG71`/`A71` bless both the source and the
  mechanism. Recorded as **`RG-D41-1`** in `docs/plan_notes.md` (`Escalation: none`) — **not**
  escalated to Requirements.
- **FI-2 — `OrderBookLevel` is not in D41's named tokens but is the removed feature's model.**
  `data/models.py::OrderBookLevel` (`:105`–`:110`) is referenced by **nothing** in the tree.
  **Disposition: ACCEPTED** — within "all associated code", and inert. Recorded above as an explicit
  scope close-out, machine-checked by the removal guard's token set.
- **FI-3 — D41 must not be credited with the wide-candle / volume-overlap defect (DG68 is still
  open; the investigation proves a different cause).** ESC-041 (`escalations.json`, **`blocking`**,
  routed BUILD) measures the overlap as the D6 4-device-pixel floor exceeding the inter-bar pitch in
  `ui/candlestick_item.py:122`–`:138` plus the chart's volume width path
  (`ui/chart_panel.py:1688`–`:1690`). `docs/code_review/candle_overlap_investigation.md` is
  **concluded** and rules the footprint overlay **out**. **Disposition: ACCEPTED** with the
  labelling/severity correction: D41's phases **do not touch** those files, no task may claim the
  symptom as fixed, ESC-041 stays **blocking** and BUILD-owned, and DG68 is closed as "not resolved
  by D41".
- **FI-4 — the requirements do not say whether the right dock's stable title/`objectName` (used by
  title-keyed lookups in the test tree) may change.** **Resolution (`S6`):** rename the single dock
  to `"Portfolio"` **and** update every title/title-bar consumer in the same phase — **15**
  `windowTitle()`/`objectName()` consumers + **2** title-bar-text files — with a new guard asserting
  exactly one right dock titled `"Portfolio"` and no `"Active Trader"` dock/widget. **Disposition:
  RATIFIED, conditional on the complete consumer list** — now supplied (the round-1 list said "8"/"9";
  the verified count is 15 + 2). The alternative (keep the old title) is recorded and rejected.
- **FI-5 — `footprint_cache_key`'s name survives D41 and will read as a leftover.**
  `AC-D41.4`/DG67 require keeping it (D39's burst-baseline key). Renaming is recorded as **FS17** and
  is **not** part of D41. **Disposition: ACCEPTED** — kept **verbatim**; the guard **allow-lists** the
  token as an intentional survivor; its only test is **re-homed** into
  `tests/test_d39_burst_search.py`.
- **FI-6 — removing `test_order_entry_mkt.py` / `test_order_entry_side.py` deletes D26.4/D26.6
  coverage outright.** Both files import **only** `ui.active_trader_panel` and touch no retained
  machinery, so deletion is the correct reading; their *intent* is carried over to the retained path
  by `tests/test_d41_retained_order_path.py`, and the retained builders keep their coverage in
  `tests/test_order_builders.py` + the re-pointed `tests/test_kill_switch.py`. **Disposition:
  ACCEPTED**.

---

## D42 increment — Batch 18b: density-aware candle/volume body width (ESC-042 → ESC-041) + mode-aware intraday history depth and day presence (ESC-038 → ESC-037) (validated 2026-10-15, **approved for build**)

> **Status of this increment.** Validated by Plan Artifact Editor & Validator (`Status: APPROVED`,
> 2026-10-15, cycle 2 of 3) and **approved for build**. Like the D41 increment above it is
> **planned and approved, not yet as-built**; when it lands, this section becomes the as-built
> record. **D42 is a requirements-decision batch with no new feature**: it resolves the two
> **REQUIREMENTS-routed** Code Reviewer escalations and supplies the normative target that unblocks
> the two corresponding **BUILD** escalations — **ESC-041** and **ESC-037** stay BUILD-owned and are
> **not** absorbed here.
>
> **This increment revises** the *unconditional* `AC-D6.4` body floor, the `AC-D7.1` "the gap
> remains positive" wording (and the D7 dense-view edge case), the RTH-only depth default, and
> D28.4's flat 5000-bar bound — each recorded as a **supersession** in § *Supersessions (D42
> increment)*, none silent. The affected earlier sections of this file carry supersession
> cross-reference markers and are **not** rewritten. **D41 is built, reviewed and committed
> (`b48133d`) and is NOT reopened**; D1–D41 are otherwise unchanged.
>
> Requirements of record: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised
> 2026-10-15 19:06) — `### D42` (`:3529`–`:3617`), `AC-D6.4` (revised `:1288`–`:1293`), `AC-D7.1`
> (revised `:1326`–`:1330`), the `AC-D9.2` note (`:1476`), `AC-D16.8` (extended `:1901`–`:1938`),
> **`AC-D16.9`** (new `:1940`–`:1972`), `A72`–`A73` (`:3694`–`:3695`), `R63`–`R64`
> (`:3813`–`:3814`), `DG68` (resolved, `design_gaps.md:1067`) + `DG72` (`:1162`), and
> `open_questions.md` **Q51/Q52** (answered 2026-10-15). Companion plan: `docs/plan.md` § *D42 —
> Batch 18b*. Review: `docs/plan_review.md` (D42 cycle 3, `APPROVED`).
>
> **`ESC-050` amendment (2026-10-16) — enumeration/accuracy only; no decision below changes.** The D42
> impact analysis **under-enumerated** the suites changed by design in two independent places: **(1)**
> the **six suites that merely *drive* `MainWindow.load_chart`** with a fixed-size
> `req_historical_data` reqId stub (19 cases: `test_d24_popouts.py` 7, `test_phase3_fixpass.py` 7,
> `test_d24_alarm_full_chain.py` 2, `test_d24_smoke_gate.py` 1, `test_d24_9_popout_persistence.py` 1,
> `test_d28_tick_burst_baseline.py` 1), and **(2)** further sites **inside** the three D16 files (so
> all **14** changed test functions there are named). `S21`, `AR-D42-6`, the Codebase Summary and the
> Non-Functional test-fidelity bullet below are amended accordingly: the enumeration is now complete
> **and generated by a rule**, with the **invariant** stated (`S21`), so completeness is checkable
> before dispatch rather than discovered at reconciliation. A **Frozen Interfaces** checklist is added
> below (read-only `[existing]` surfaces only — a disclosure, not a decision). D42's design, `AC`s,
> phases and tasks are unchanged; the batch is built (26/26 tasks, full offscreen suite green).
>
> **Frozen baseline:** `main` after D41 (`b48133d`), full offscreen suite green. Suite invocation
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale
> shebang).

### Summary (D42 increment)

D42 is a **two-workstream correctness increment on existing paths**, with **no new feature and no
stack change**. **(1)** The rendered candle body becomes `body = min( max(0.65 × pitch, F), pitch )`
computed by **one shared, pure helper** that both the candle `QPicture` and the volume
`BarGraphItem` width path call, so the **no-overlap guarantee (`gap >= 0`) wins** over the D6 4-px
legibility floor at extreme density while the floor still binds in the non-dense regime (the wick
stays a cosmetic 1-px line). **(2)** The intraday fetch gains a **backwards-extending depth floor**
(≥ 30 trading sessions before the current session, in **both** RTH and ETH) delivered through the
**existing** D28.3 wave pump as ordinary `RequestPlan`s, driven by a **mode-aware** day-presence
predicate and a **mode-aware** bar cache (`bars.ext_hours`), with **all three `SESSION_BAR_CAP`
sites plus `BarCache.prune`'s `keep`** made floor-aware so the floor survives pruning **and is not
trimmed out of the displayed series on the next live candle**. Every supersession is **recorded**,
and the **five** suites that enshrine the old rule are **corrected, not weakened**.

### Codebase Summary (D42 surface — existing repository, source-validated 2026-10-15)

The repo is **not** greenfield: a PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal
(~4,920 graph nodes; full offscreen suite green after D41 @ `b48133d`). This is a factual inventory
of the surface D42 touches; every item below was read in the tree during planning and re-verified by
the Validator this cycle.

**Data models / schema `[existing]`**

- **`data/db.py::DB`** — SQLite, one connection, `_init_schema()` (DDL script) + `_migrate_schema()`
  (additive `ALTER TABLE`, `CREATE UNIQUE INDEX`, one idempotent `DROP TABLE IF EXISTS
  footprint_cache` from D41). Tables: `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`,
  `drawings`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`,
  `yfinance_events_cache` (D38), `volume_baseline` (D39).
  - **`bars`** (`data/db.py::DB._init_schema`, `:16`–`:22`) — `(symbol TEXT, timeframe TEXT, ts
    INTEGER, open, high, low, close, volume)`, **`PRIMARY KEY (symbol, timeframe, ts)`**. **No
    `useRTH`/mode component** — this is the `useRTH`-blind cache key `AC-D16.9` names.
  - `popouts` (`:76`–`:84`) already persists `ext_hours INTEGER NOT NULL DEFAULT 1` per pop-out.
  - `config/paths.py::get_db_path()` returns the **user-space production DB** when `DB_PATH` is
    unset (`tests/conftest.py` sets it to a temp file).
- **`data/models.py::Bar`** — `@dataclass` with `symbol, timeframe, ts, open, high, low, close,
  volume` (no mode field; plain dataclass, no `__slots__`).
- **`data/bar_cache.py::BarCache`** — `RETENTION_BARS = 5000` (`:8`); `save_bars(bars)` (`:13`,
  `INSERT OR REPLACE`), `get_bars(symbol, timeframe)` (`:27`), `prune(symbol, timeframe,
  keep=RETENTION_BARS)` (`:39`), `get_last_timestamp` (`:55`, unused by the load path).
- **`services/backfill_service.py`** — pure, Qt-free planner: `MissingSpan`, `RequestPlan`,
  `bar_period_seconds` (`:104`), `_duration_to_seconds` (`:113`), `_et_date`/`_et_day_start_ts`/
  `_trading_days`/`_build_span` (`:139`–`:163`), **`find_missing_spans(cached_ts, now_ts, timeframe,
  trailing_days=TRAILING_BAR_GRANULARITY_DAYS, ext_hours=False)`** (`:169`), `_bar_level_missing_spans`
  (`:239`), `plan_requests(missing_spans, timeframe)` (`:299`).
- **`services/market_calendar.py`** — pure ET calendar: `is_trading_day`, `trading_days`,
  **`session_windows(start_ts, end_ts, ext_hours)`** (`:195`–`:216`) with `_EXT_OPEN/_EXT_CLOSE =
  04:00/20:00` and `_RTH_OPEN/_RTH_CLOSE = 09:30/16:00` ET (`:37`–`:40`), and the ESC-023 NYSE
  Rule 7.2 New-Year exception (`:117`–`:121`).
- **`services/time_collapse_service.py::TimeCollapseMap`** — the D21.4 display-only x-transform
  (`_to_display`), which the candle/volume width math is expressed in.
- **In-memory caps:** `config/settings.py::SESSION_BAR_CAP = 5000` (`:45`), applied in
  `TickerSession.set_bars` (`:300`), `TickerSession._append_bar` (`:313`) and
  `ChartPanel.update_last_bar` (`:1150`/`:1157`); `config/settings.py::MAX_HISTORICAL_PER_600S = 60`
  (`:35`) and `ibkr/pacing.py::pacing_manager`.

**Major components and responsibilities (as-built)**

| Component | Responsibility (D42-relevant) |
|---|---|
| `ui/candlestick_item.py` (~200 lines) | `CandlestickItem` 5 render modes; `CandlestickItem._draw_candles` (`:100`–`:163`) computes the half-width (`median_diff * 0.325`, `:111`), reads the ViewBox range and applies the **unconditional 4-px floor** (`min_w = 2.0 / px_per_sec`, `:136`–`:138`), draws the cosmetic 1-px wick + body into a `QPicture`; `set_data(..., width=...)` carries the D28.4 cached half-width override (`:63`–`:71`). |
| `ui/chart_panel.py` (~1,800 lines) | `ChartPanel._compute_candle_half_width` (`:1215`, median of **display-x** diffs × 0.325, cached as `_candle_half_width`), `ChartPanel._clamp_half_width` (`:1229`, the volume-side mirror of the same 4-px floor at `:1242`–`:1244`), `ChartPanel._refresh_candles` (`:1249`; volume `w_vol` at `:1303`, `volume_bars.setOpts(width=w_vol*2)` `:1305`, live volume `:1310`/`:1314`, `candlestick.set_data(..., width=...)` `:1318`/`:1326`), `ChartPanel._refresh_live_bar` (`:1333`), and the `_bars` trim at `SESSION_BAR_CAP` inside `ChartPanel.update_last_bar` (`:1138`, `:1150`–`:1157`). |
| `ui/ticker_session.py` (~1,800 lines) | Per-symbol session: `get_bars` (`:295`), `set_bars` (`:298`, capped at `:300`), `_append_bar` (`:306`, capped at `:313`), `_wave_extended_hours` (`:127`), `queue_wave_plans` (`:843`), `_issue_wave_chunks` (`:858`, `useRTH=1` + `extended_hours=` passed to `md_manager.req_historical_data`), `_schedule_wave_continuation` (`:886`), `_wave_may_complete` (`:900`). |
| `ui/main_window.py` (~3,700 lines) | `MainWindow.load_chart` (`:1560`–`:1705`): cached read (`:1630`), `find_missing_spans(..., ext_hours=extended_hours)` (`:1647`–`:1652`), `plan_requests` (`:1653`), wave queue (`:1662`), **empty-cache single-window branch** (`:1668`–`:1684`); `MainWindow._finalize_history_wave` (`:1950`–`:2044`): `save_bars` (`:1970`), `prune` (`:1973`), `get_bars` (`:1974`), AC-D16.4 shortfall via `MainWindow._missing_backfill_trading_days` (`:2046`–`:2060`, its own mode-blind `present_days` at `:2052`–`:2054`); `MainWindow._on_ext_hours_toggled` (`:2777`–`:2784`, relabels and re-loads); the default mode is **Ext Hours ON** (`ext_hours_btn.setChecked(True)`, `:244`; the `:1570` fallback). |
| `ibkr/market_data.py` | `TIMEFRAME_CONFIG` (`:7`–`:13`) — the **per-request** duration/bar-size caps (`1 min → 1 D`, `5 mins/15 mins → 5 D`, `1 hour → 10 D`, `4 hours → 30 D`, `1 day → 1 Y`); `req_historical_data(..., extended_hours=)` maps to `useRTH` (`:26`–`:58`). |
| `ui/popout_window.py` | `PopoutChartWindow` **attaches a view** to the shared session (`session.attach_view(self.chart, self.timeframe, sync=True)`, `:131`) and issues **no history** of its own. |
| `services/alarm_monitor.py` | `AlarmMonitor` (`:287`) seeds `prev_price` from `BarCache.get_bars(symbol, "1m")` — mode-neutral, never requests history. |
| `tests/` | pytest + pytest-qt offscreen; the **five** suites that enshrine the old width/cap rule are `test_candle_spacing.py` (`:4`–`:10`, a source-string check that never renders), `test_volume_width.py` (`:103`–`:104`), `test_chart_dpi.py` (`:245`–`:250`, `assert body_dev >= 4.0` on the dense 960-bar DPR-2 dataset), `test_d28_2_sessions.py` (`:166`) and `test_d28_4f_panel_bar_cap.py` (`:53`); the D16/D27 planner suites are `test_backfill_service.py`, `test_d27_backfill_granularity.py`, `test_history_backfill*.py`, `test_market_calendar.py`; the cap suites are `test_d28_2_sessions.py`, `test_d28_4e_bar_cache_retention.py`, `test_d28_4f_panel_bar_cap.py`; and the D16 **load-path** suites whose expectations `S17`/`S18` legitimately change are `test_history_backfill_loadpath.py` (`:202`/`:206`, `:238`, `:255`–`:257`, `:431`, `:477`), `test_history_backfill.py` (`:285`, `:388`–`:390`, `:451`–`:457`, `:480`–`:485`, `:590`) and `test_history_backfill_disconnect.py` (`:249`–`:255`, `:362`, `:481`–`:485`). **Load-path-*coupled* by stubbing the feed (`ESC-050` — each boots a `MainWindow`, stubs `md_manager.req_historical_data` with a fixed-size reqId iterator and asserts downstream, so `S17`'s floor span exhausts the stub):** `test_d24_popouts.py`, `test_phase3_fixpass.py`, `test_d24_alarm_full_chain.py`, `test_d24_smoke_gate.py`, `test_d24_9_popout_persistence.py`, `test_d28_tick_burst_baseline.py` — they are **not** D16 suites, which is exactly why the D42 impact analysis missed them. |

**Key entry points / data flow (unchanged shape)**

`MainWindow.load_chart` → `BarCache.get_bars` → `find_missing_spans` → `plan_requests` →
`TickerSession.queue_wave_plans`/`_issue_wave_chunks` → `MarketDataManager.req_historical_data`
(`useRTH`, `endDateTime`, `duration`, `bar_size`) → `IBApiClient.historicalData` →
`_on_historical_bar`/`_on_historical_data_end` → `MainWindow._finalize_history_wave` →
`BarCache.save_bars` → `TickerSession.set_bars` → `ChartPanel.update_chart` →
`ChartPanel._refresh_candles` (price **and** volume).

**External integrations already in use `[existing]`**

IBKR TWS over `ibapi` (historical + realtime bars, market data, contract details, orders) on
**live port 7496 only**; SQLite persistence; `yfinance` (D38, unrelated); no message queue, no cache
server, no auth provider.

**What D42 changes, in one line**

`AC-D16.9`'s two defects are **real and both mode-blind in the same code path**: `present_days =
{_et_date(ts) for ts in ts_values}` (`services/backfill_service.py:208`) decides day presence with
**no** session window, and `BarCache.get_bars/save_bars` key on `(symbol, timeframe)` with **no**
mode (`data/bar_cache.py:13`/`:27`, `data/db.py:21`). The width defect is the same shape:
`ui/candlestick_item.py:136`–`:138` applies `min_w` **unconditionally**, and
`ui/chart_panel.py:1242`–`:1244` mirrors it for volume — at a 3.83-px pitch the floor makes the gap
negative (ESC-041).

### Relationship to prior increments (D42) — every decision carries its label

| Prior decision / component | Relationship | Note |
|---|---|---|
| `AC-D6.4` unconditional 4-device-px body floor; `CandlestickItem._draw_candles` clamp (`:122`–`:140`); `AC-D7.1` "gap remains positive" | **`[revises D6/D7: the body-width clamp]`** | `S13`+`S14`: the floor becomes density-aware and the body is capped at the inter-bar pitch. Supersession **recorded**, never silent. |
| `AC-D9.1`/`AC-D9.2` volume width == price body width; `ChartPanel._clamp_half_width` (`:1229`) / `_refresh_candles` (`:1303`/`:1305`) / `_refresh_live_bar` (`:1352`) | **`[extends D9: the volume width path]`** | Intent unchanged; the volume path consumes the **same** capped `w` from the one shared helper (`S13`). |
| D16 backfill planner (`find_missing_spans`), `data/bar_cache.py`, `services/market_calendar.py`, `MainWindow.load_chart`/`_finalize_history_wave` | **`[extends D16: the missing-span / day-presence / cache path]`** | `S15`–`S19`. `AC-D16.1`/`AC-D16.3`/`AC-D16.4` (no-fill / genuine-closure / shortfall-report) are **unchanged**. |
| D27.7 bar-level trailing pass (`_bar_level_missing_spans`, `:239`–`:297`) | **`[extends D27: the bar-level pass]`** | Already `ext_hours`-aware; unchanged in shape, now fed by the mode-aware presence predicate for consistency (`S15`). |
| D28.3 pacing-aware waves (`_issue_wave_chunks`, `:858`; `MAX_HISTORICAL_PER_600S = 60`) | **`[extends D28: the wave pump]`** | Unchanged. The depth floor is delivered as **more plans** through the existing wave cap + continuation timer — no new transport mechanism (`S17`). |
| D28.4 caps (`SESSION_BAR_CAP = 5000`, `RETENTION_BARS = 5000`) and the D28.4 render split | **`[revises D28.4: the two 5000-bar caps]`** | `S18`: the caps become **floor-aware** (≥ the flat 5000, derived per timeframe × mode) at **all three** `SESSION_BAR_CAP` sites — `TickerSession.set_bars` (`:300`), `_append_bar` (`:313`) and `ChartPanel.update_last_bar` (`:1150`–`:1157`) — plus `BarCache.prune`'s `keep`. A deliberate revision of a D28.4 bound, forced by `AC-D16.8`. |
| D24.9 pop-out `ext_hours` persistence (`popouts.ext_hours`) | **`[extends D24: pop-out mode]`** | The pop-out already knows its mode; it now reaches the cache/planner through the session it attaches to (`S19`). |
| D41 removals | **no relationship** | D42 touches neither the removed surface nor its retained substrate. |

### Tech Stack Decisions (D42 increment)

Constrained (existing) choices first, then the D42 additions/changes. Every row carries a rationale
and the alternatives considered.

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| **Language / UI stack** `[existing]` (`S1`) | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`), numpy (`>=1.26`) | Existing-repo hard constraint; "changing the tech stack" is an explicit non-goal in `requirements.md` | Any new UI/charting/numeric framework — rejected |
| **Broker / persistence / packaging / tests** `[existing]` (`S2`) | Unchanged: official `ibapi` (`ibapi-latest==10.51.1`), **live TWS 7496 only** (`check_live_port` fail-fast), SQLite via `config/paths.get_db_path()`, PyInstaller `.app`, pytest + pytest-qt offscreen, no live TWS and no transmitted orders | Existing-repo hard constraint; Q8/Q9 | Paper mode / new broker / new DB / new test framework — rejected |
| **Testing** `[existing]` (`S3`) | pytest + pytest-qt, `QT_QPA_PLATFORM=offscreen`, run as `.venv/bin/python -m pytest`; any **non-pytest** probe that can reach a DB-writing path exports `DB_PATH` to a temp file (ESC-043) | Repo standard + the repo's own recorded gotchas | Manual / live-TWS verification — rejected |
| **One shared capped-width helper** `[new in D42]` — **revises the D6/D7 clamp** (`S13`) | Add a **pure** module-level function in `ui/candlestick_item.py` (the module that owns the D6 formula): `capped_body_half_width(median_diff, base_half_width, px_per_sec, floor_px=4.0) -> float` implementing `w = min( max(base_half_width, floor_px / 2 / px_per_sec), median_diff / 2 )`, i.e. `body = min(max(0.65×pitch, F), pitch)` with `base_half_width = 0.325 × median_diff` and `F` the existing 4-px constant. **Unit of `F` (`FI-D42-4`/`AP-D42-5`, stated explicitly per `RC-D42-3`):** `floor_px = 4.0` is **4 ViewBox logical px** — the unit `px_per_sec` yields (`vb.width() / x_span`) and the unit the shipped `min_w = 2.0 / px_per_sec` already uses (`ui/candlestick_item.py:136`), i.e. **8 device px at DPR 2**; it is **not** the `AC-D6.4` literal's "4 device pixels at DPR 2". `AC-D6.4`'s operative clause is "measured in the **same** pixel unit" and the shipped constant is kept, so the criterion's outcomes hold unchanged — and the WS1 test evidence applies `F` in **this** unit and asserts the unit-free relations `body <= pitch` / `body == pitch`. **Three call sites, one implementation:** `CandlestickItem._draw_candles` (`:136`–`:138`), `ChartPanel._clamp_half_width` (`:1229`, imported, so the volume path cannot drift), and therefore `_refresh_candles` (`:1303`) / `_refresh_live_bar` (`:1352`) automatically | `AC-D6.4`/`AC-D7.1` (revised) + `AC-D9.1`/`AC-D9.2`'s note require **one shared capped `w`** for candle and volume; **R63** names exactly the risk of the two paths diverging. A single pure function is directly unit-testable (three regimes: `pitch > F`, `pitch == F`, `pitch < F`) without a QApplication, and it keeps the 0.325 / 35 % intent visible in one place | (i) patch the two clamp sites independently — duplicates the rule, R63's failure mode — rejected; (ii) put the cap in `ChartPanel` and pass the capped `w` down to `CandlestickItem` — inverts the D28.4 ownership (`CandlestickItem` clamps at generation time using the ViewBox range; ESC-013 depends on that ordering) — rejected; (iii) a new `ui/candle_width.py` module — an extra module for one 3-line rule — rejected |
| **Pitch plumbing for the D28.4 width override** `[new in D42]` (`S14`) | `ChartPanel` caches the **pitch** alongside the half-width: `_compute_candle_half_width` (`:1215`) already computes `median_diff` over **display-x**; it returns/stores both (`_candle_pitch`). `CandlestickItem.set_data(..., width=…, pitch=…)` gains the optional `pitch`; `_draw_candles` uses the supplied pitch when `_width_override` is set, otherwise computes `median_diff` from `data` exactly as today. `ChartPanel` passes `pitch=self._candle_pitch` at `:1318`/`:1326`/`:1347` | The cap **needs the pitch**, and the D28.4 override exists precisely to skip the O(n log n) median sort on regeneration — recomputing it inside `_draw_candles` would undo D28.4's perf fix. Both the pitch and the width come from the same **display-x** series, so `median_diff`, `px_per_sec` (ViewBox units) and `F` are in the **same pixel unit** (`AC-D6.4`'s "same pixel unit" clause) | (i) always recompute the median inside `_draw_candles` — reintroduces the sort D28.4 removed — rejected; (ii) drop the override and let `CandlestickItem` own the width entirely — a D28.4 perf regression — rejected; (iii) cap in data units only (ignore the ViewBox) — the floor is a **device**-pixel rule and needs `px_per_sec` — rejected |
| **Mode-aware day presence** `[new in D42]` — **extends D16** (`S15`) | A pure predicate in `services/backfill_service.py`: a day is **present** iff ≥ 1 cached bar's timestamp falls inside that day's **current mode's** session window, via `market_calendar.session_windows(day_start, day_end, ext_hours)`. `find_missing_spans`'s `present_days = {_et_date(ts)}` (`:208`) is replaced by the window-membership set; `MainWindow._missing_backfill_trading_days` (`:2052`–`:2054`) — the **AC-D16.4 shortfall report** — calls the **same** exported predicate instead of its own mode-blind `present_days` | `AC-D16.9`'s normative rule and its measurables (a)/(b)/(c); the bar-level pass (`:276`) already uses `session_windows(..., ext_hours)`, so today **one** planner decides presence two different ways. Bar timestamps are period **starts** (recorded gotcha), so the window test applies to the bar's start timestamp — which is exactly why an RTH-empty day can look covered | (i) keep the mode-blind presence set and only fix the bar-level pass — leaves ESC-037's silent RTH hole — rejected; (ii) decide presence per day from the *first/last* bar only — wrong for a day whose bars straddle the window — rejected; (iii) filter the cached series by mode before the planner sees it — conflates cache scoping with presence and would break `AC-D16.9(c)`'s "RTH bars are ETH-present" — rejected |
| **Mode-aware cache key + migration** `[new in D42]` — **extends D16** (`S16`) | `bars` gains **`ext_hours INTEGER NOT NULL DEFAULT 1`** and its key becomes **`(symbol, timeframe, ext_hours, ts)`**; `BarCache.save_bars(bars, ext_hours=True)` / `get_bars(symbol, timeframe, ext_hours=True)` / `prune(symbol, timeframe, ext_hours=True, keep=…)` (the mode is a **keyword with the app's default**, so existing call sites and suites stay valid). SQLite cannot alter a primary key, so `data/db.py::_migrate_schema` **rebuilds** the table once, guarded by `PRAGMA table_info(bars)` (idempotent, crash-safe, the same mechanism D41 used for its drop): create `bars_new` with the new key, `INSERT OR IGNORE … SELECT symbol, timeframe, 1, ts, …`, drop `bars`, rename | `AC-D16.9` and `AC-D16.8`'s mode-isolation clause **explicitly require** a mode-aware cache/key ("keyed on symbol+timeframe+mode") so a mode switch cannot read the other mode's bars as coverage — `requirements.md:1957`–`:1958` ("The bar cache/key is **mode-aware** (RTH vs ETH) … This applies **in both directions**") together with `AC-D16.9`'s measurable (c) at `:1967`–`:1969` (a **presence predicate** on a given bar set: RTH bars lie inside `04:00–20:00 ET`, so the ETH call reports the day present) — the ratified reading of `FI-D42-3`. `ext_hours` (0/1) is the vocabulary the whole pipeline already speaks (`useRTH`, `find_missing_spans(ext_hours=)`, `popouts.ext_hours`), so no new enum is introduced. Legacy rows are tagged **`ext_hours = 1` (ETH)**: the app's default is **Ext Hours ON** (`ext_hours_btn.setChecked(True)`, `:244`), so pre-existing rows were fetched with `useRTH=0`; an RTH load after the migration finds its own (empty) key and fetches the required floor — **no hole, and that fetch is required by `AC-D16.8` anyway** | (i) **no schema change** — keep one `(symbol, timeframe, ts)` cache and make only the *presence* predicate window-based. Passed over: it satisfies every measurable of `AC-D16.9` but fails its explicit "the bar cache/key is mode-aware" clause and `AC-D16.8`'s "in both directions" wording, and it cannot distinguish "the user never loaded ETH for this symbol" from "ETH is covered" — rejected; (ii) wipe the cache on migration — cheapest, but discards a valid cache and forces a full refetch of every symbol/timeframe/mode for no correctness gain (legacy rows are ETH-fetched, i.e. already the widest window) — rejected; (iii) a third `'LEGACY'` mode visible to both — more correct in principle, but adds a tri-state to every read/write/prune for one migration's benefit — rejected; (iv) store mode in a side table keyed by `(symbol, timeframe)` — loses per-bar truth after a mode switch — rejected |
| **Backwards depth floor through the existing planner** `[new in D42]` (`S17`) | `find_missing_spans(cached_ts, now_ts, timeframe, trailing_days=…, ext_hours=False, min_sessions=0)` gains **`min_sessions`** (default `0`). When `min_sessions > 0` **and** the timeframe is intraday, the planner computes the **floor day** = the `min_sessions`-th trading day before the current session and emits **at most one** `MissingSpan` covering `[floor_day_start, earliest_present_day_start)` (or `[floor_day_start, now]` when nothing is present), so the floor is fetched **backwards** and **collapses to empty once filled**. `MainWindow.load_chart` passes `min_sessions=MIN_INTRADAY_SESSIONS` for intraday timeframes in **both** the cached path (`:1647`) and the empty-cache path — the `elif not cached` single-window branch (`:1668`–`:1684`) is **removed** because the floor span already yields plans (the empty-cache case becomes "one span from the floor to now") — which requires that the `find_missing_spans(...) if cached else []` guard at `ui/main_window.py:1647`–`:1652` **and** the empty-cache early return at `services/backfill_service.py:205`–`:206` are both bypassed when `min_sessions > 0` | `AC-D16.8` requires the floor for **all five** intraday timeframes in **both** modes; IBKR caps `1 min` at `1 D` per request, so the depth must come from **chained** requests. Reusing `plan_requests` (`:299`, which already chunks a span newest-first by the configured duration) means the floor needs **no new transport path** and rides D28.3's wave cap + continuation timer unchanged. `min_sessions=0` is the default, so **every existing D16/D27 planner suite keeps its exact semantics**; `R64`'s "the D16 suite stays green" is met by **intent-preserving correction** of the D16 **load-path** suites (enumerated with their cause in `S21` / the plan's correction record), never by weakening an assertion | (i) raise `TIMEFRAME_CONFIG` durations — `1 min` is hard-capped at `1 D` and the chaining is required regardless, so one mechanism serves all five timeframes — rejected; (ii) a separate `depth_service.py` — duplicates `plan_requests`/`_trading_days` — rejected; (iii) a new "floor" request kind in the session — bypasses the pacing accounting — rejected; (iv) keep the empty-cache special branch and add the floor only to the cached path — leaves the ESC-038 repro (fresh `1 min` RTH) at one session — rejected |
| **Floor-aware bar budget (all three `SESSION_BAR_CAP` sites + `prune`'s `keep`)** `[new in D42]` — **revises D28.4** (`S18`) | Add a pure helper (in `services/backfill_service.py`, next to `bar_period_seconds`/`session_windows`): `floor_bar_budget(timeframe, ext_hours) -> int` = `max(SESSION_BAR_CAP, ceil(min_sessions × window_seconds(timeframe, ext_hours) / bar_period) × 1.15)`, where `window_seconds` is 6.5 h (RTH) or 16 h (ETH); `1 day` returns the flat cap (not covered by the floor). The **three** cap sites use it — `TickerSession.set_bars` (`:300`), `TickerSession._append_bar` (`:313`), and **`ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`)** — and the load path passes `keep=floor_bar_budget(...)` to `BarCache.prune` (`:1973`). The panel trim is the site that matters most: `update_chart` seeds `ChartPanel._bars` from the session's (now up to 33,120-bar) series and `update_last_bar` would otherwise re-trim it to the flat 5,000 on the **next new-candle tick**, i.e. the `AC-D16.8` floor would be discarded from the **displayed** series after one live bar (`FI-D42-1`'s failure mode one layer up). **Ownership (`RC-D42-1`):** this edit is owned by the **same phase as `floor_bar_budget`** (Phase 2) and is **sequenced after** the `ui/chart_panel.py` width edit of the other workstream — `ui/chart_panel.py` is the **one** file shared by the two workstreams, so the two `ui/chart_panel.py` tasks must never be `in_progress` in the same wave (`build_wave.py`'s overlapping-`touches_files` rule); see the plan's per-file map. The **flat constants stay** as the default/floor (`RETENTION_BARS = 5000`, `SESSION_BAR_CAP = 5000`) | **`AC-D16.8` is otherwise unsatisfiable on this build.** A `1 min` RTH session is 390 bars, so 30 sessions = **11,700 bars** > the 5000 cap; `1 min` ETH is 960/session → **28,800**; `5 mins` ETH → **5,760**. Both the SQLite `prune` (`RETENTION_BARS`) and the in-memory caps would **delete the floor after fetching it**, so the displayed series could never cover 30 sessions. Keeping the flat constants as the default preserves `prune(sym, tf)`'s existing behaviour and `test_d28_4e_bar_cache_retention.py` unchanged | (i) leave the caps and accept a shortfall — directly contradicts `AC-D16.8`'s "the displayed bar series covers at least 30 trading sessions" — rejected; (ii) lower the floor for dense timeframes — `AC-D16.8` states 30 sessions for **all five** — rejected; (iii) raise the two constants unconditionally to 33,120 — inflates memory for `1 day`/`4 hours` charts that need 5,000 at most, and breaks the flat-cap suites for no reason — rejected; (iv) make the floor count **sessions** rather than bars and fetch lazily per viewport — the chart auto-frames the whole cached series, so the series itself must hold the floor — rejected |
| **Mode threading through the load path** `[new in D42]` (`S19`) | `TickerSession` already owns `_wave_extended_hours` (`:127`); it gains the same value as the **session's mode** for its own cache reads (`get_bars` `:295`, the D39 baseline preload `:684`) and writes (`_finalize_history_wave`'s `save_bars`). `MainWindow.load_chart` passes the mode explicitly at `:1630` (`get_bars`), `:1648` (`find_missing_spans`), `:1662`/`:1672` (wave queue) and `:1970`/`:1973`/`:1974` (finalize). `services/alarm_monitor.py:287`'s `BarCache.get_bars(symbol, "1m")` keeps the default (its prev-price seed is mode-neutral) | One place per hop, no globals, and the mode travels with the session that already owns the wave — so a pop-out (whose `ext_hours` is persisted in `popouts`) and the primary chart cannot cross-contaminate. `get_bars`'s existing `timeframe`-keyed session map is untouched | (i) a module-level "current mode" global — two charts with different modes would corrupt each other — rejected; (ii) re-key the session's `_bars` map by `(timeframe, mode)` — unnecessary: a session is loaded in one mode at a time and `load_chart` resets it — rejected; (iii) make `ext_hours` a required positional argument — forces every legacy test/caller to change for no benefit — rejected |
| **Config surface** `[new in D42]` (`S20`) | **One new constant:** `config/settings.py::MIN_INTRADAY_SESSIONS = 30` (the owner-required floor, `AC-D16.8`, A73). **`ibkr/market_data.py::TIMEFRAME_CONFIG` is NOT changed** — its durations are the **per-request** IBKR caps, and the depth comes from chaining (`S17`). `MAX_HISTORICAL_PER_600S = 60` and the pacing model are unchanged | The floor is an owner-required number that both the planner and the budget derive from, so it belongs in the settings module the pacing/cap constants already live in; changing `TIMEFRAME_CONFIG` would either be a no-op for `1 min` (hard cap) or a redundant second mechanism | (i) hard-code 30 in the planner — a magic number split from its rationale — rejected; (ii) change `TIMEFRAME_CONFIG` durations as the task brief anticipated — rejected for the reason above (recorded as an explicit non-change) |
| **Test surface** `[new in D42]` — **corrects the five enshrining suites + the D16 load-path suites + the six load-path-*driving* suites (`ESC-050`), extends the planner/db suites, adds four** (`S21`) | **Corrected (never weakened, never deleted):** `tests/test_candle_spacing.py` (string-presence → regime/geometry assertions on the shared helper), `tests/test_volume_width.py` (the dense `≈ 4.0 px` legs → `body == pitch`, `gap >= 0`, volume == body), `tests/test_chart_dpi.py` (the dense `body_device_px >= 4.0` leg → the **non-dense** dataset carries the `>= F` claim; the dense dataset carries `body <= pitch`). **Corrected for the floor-aware caps:** `tests/test_d28_2_sessions.py::test_session_bar_cap` and `tests/test_d28_4f_panel_bar_cap.py` (assert the derived budget, keep the oldest-dropped/newest-kept invariant). **Corrected — D16 load-path (`RC-D42-2`; every correction intent-preserving, the cause named in the plan's correction record):** `tests/test_history_backfill_loadpath.py::test_t39_t02` (`:238` — the **floor span**: 5 seeded ETH sessions < 30), `::test_t39_t03` (`:255`–`:257` — the empty-cache branch `S17` **removes**), `::test_t39_t01` (`:202`/`:206` — the test's own planner call must pass the floor), `::test_t39_t06`/`::test_t39_t07` (`:431`/`:477` — the **floor-aware `keep`**), `tests/test_history_backfill.py` (`:285`, `:451`–`:457`, `:590` — the floor span and the removed empty-cache single-window branch) and `tests/test_history_backfill_disconnect.py` (`:362` — the same removed branch). Each keeps its guarantee: "no **redundant** request once the floor is satisfied and the cache reaches *now*"; an empty cache is covered **by the planner** as one floor span rather than by a special branch; the retention invariant becomes the **derived** budget with oldest-dropped/newest-kept. **`ESC-050` completes this enumeration (the list above names 9 sites; the D42 diff changes **14** test functions in the three files):** the **3** further changed sites `ESC-050` records (`tests/test_history_backfill.py::test_t40_t03`, `tests/test_history_backfill_disconnect.py::test_t43_t03`/`::test_t44_t03`) and the **2** found by Plan re-verification (`tests/test_history_backfill_loadpath.py::test_t39_t04` — the `save_bars`/`get_bars` spies must forward `ext_hours`; `::test_t39_t05` — the new session's own floor span makes `_req_ids == set()` false) are named with their cause; `ESC-050`'s fourth site, `test_t40_t05`, is **unchanged** (its correction lands in `test_t40_t04`'s tail assertion). **Corrected — load-path-*driving* suites (`ESC-050`):** **19 cases in six suites** that are **not** D16 suites but **drive `MainWindow.load_chart`** with a **fixed-size** `req_historical_data` reqId stub — `tests/test_d24_popouts.py` (7), `tests/test_phase3_fixpass.py` (7), `tests/test_d24_alarm_full_chain.py` (2), `tests/test_d24_smoke_gate.py` (1), `tests/test_d24_9_popout_persistence.py` (1), `tests/test_d28_tick_burst_baseline.py` (1) — corrected **test-only** by widening each stub to an unbounded `itertools.count` source (no assertion weakened, skipped or xfailed). **The invariant (`ESC-050`):** any test that drives the load path with a stubbed feed must use an **unbounded** reqId source, and any test asserting the **exact number** of historical requests, **one** request/chunk per load, or the **empty-cache single-window branch** changes **by design** — so the set is checkable **by rule** before dispatch. **The generalisable enumeration rule:** enumerate by **call site of the changed entry point, not by the suites the design names**; treat a **fixed-size stub of a changed feed as a defect class** and correct all of them in one scoped task; state the invariant. **Extended:** `tests/test_backfill_service.py` / `tests/test_d27_backfill_granularity.py` (mode-aware presence cases — their **existing** cases keep **exact** semantics because `min_sessions` defaults to `0`, `AP-D42-2`) and `tests/test_db_schema.py` (the new column/key). **Added:** a mode-aware presence suite (`AC-D16.9` (a)/(b)/(c)), a mode-aware cache/migration suite, a **rendered candle-width geometry guard** and a depth-floor/budget suite. `tests/test_d28_4e_bar_cache_retention.py` stays **unchanged** (the flat default is preserved, `S18`) | The D42 correction record names two suites that enshrine the old **width** rule; **five** enshrine the old behaviour in total (`test_candle_spacing.py:4`–`:10`, `test_volume_width.py:103`–`:104`, `test_chart_dpi.py:245`–`:250`, `test_d28_2_sessions.py:166`, `test_d28_4f_panel_bar_cap.py:53`) and the D16 **load-path** suites change by design through `S17`/`S18`. Every change is a **correction to the new normative target**, with the intent of the original test preserved | (i) delete the enshrining tests — forbidden by the correction record — rejected; (ii) relax the assertions to "no exception raised" — that is exactly the "weakened" failure mode — rejected; (iii) leave `test_chart_dpi.py` alone and let it fail — the suite must be green — rejected |

### System Components (D42 increment)

**Existing, unchanged** `[existing]`

`services/market_calendar.py` (windows + the ESC-023 New-Year exception),
`services/time_collapse_service.py`, `ibkr/market_data.py::TIMEFRAME_CONFIG` (`S20`),
`ibkr/pacing.py`, `ui/candlestick_item.py`'s wick/body drawing and the D28.4 render split, the D16
no-fill/no-silent-hole rules (`AC-D16.1`/`AC-D16.3`/`AC-D16.4`), the D27.7 bar-level pass shape, the
D28.3 wave pump, `services/session_service.py`, the drawing/study/alarm overlays — i.e. **nothing
D1–D41 depends on is redesigned**.

**New / changed** `[new/changed]`

| Component | Change |
|---|---|
| `ui/candlestick_item.py::capped_body_half_width` | **New pure helper** — the single source of the density-aware cap (`S13`) |
| `ui/candlestick_item.py::CandlestickItem._draw_candles` | Calls the helper (was the unconditional `min_w` clamp, `:136`–`:138`); reads the pitch from the override when present (`S14`) |
| `ui/candlestick_item.py::CandlestickItem.set_data` | Gains the optional `pitch` (`S14`) |
| `ui/chart_panel.py::ChartPanel._compute_candle_half_width` | Also returns/stores the **display-x pitch** (`S14`) |
| `ui/chart_panel.py::ChartPanel._clamp_half_width` | Delegates to the shared helper (was the mirrored 4-px floor, `:1242`–`:1244`) (`S13`) |
| `ui/chart_panel.py::ChartPanel._refresh_candles` / `::ChartPanel._refresh_live_bar` | Pass the pitch (`S14`); the volume width path delegates through `_clamp_half_width` (`S13`) |
| `ui/chart_panel.py::ChartPanel.update_last_bar` | The `_bars` trim (`:1150`–`:1157`) uses the floor-aware budget (`S18`) — the **third** `SESSION_BAR_CAP` site, without which the floor is re-trimmed out of the displayed series on the next new-candle tick. Owned by the same phase as `floor_bar_budget` and **sequenced after** the `ui/chart_panel.py` width edit of the other workstream (`ui/chart_panel.py` is the one shared file; `RC-D42-1`) |
| `services/backfill_service.py` | **New** mode-aware presence predicate + `floor_bar_budget` + `min_sessions` floor span in `find_missing_spans` (`S15`, `S17`, `S18`) |
| `data/bar_cache.py` | `save_bars`/`get_bars`/`prune` take `ext_hours` (default `True`) (`S16`, `S19`) |
| `data/db.py` | `bars` DDL gains `ext_hours`; `_migrate_schema` gains the guarded table rebuild (`S16`) |
| `ui/ticker_session.py` | Session mode for its own cache reads/writes; the two cap sites use the floor-aware budget (`S18`, `S19`) |
| `ui/main_window.py` | `load_chart` passes the mode + `min_sessions`, the empty-cache branch is removed; `_finalize_history_wave` passes the mode + the derived `keep`; `_missing_backfill_trading_days` uses the shared presence predicate (`S15`, `S17`, `S18`, `S19`) |
| `config/settings.py` | `MIN_INTRADAY_SESSIONS = 30` (`S20`) |

### Data Model (D42 increment)

| Entity | Status | Key fields / change |
|---|---|---|
| `bars` (SQLite) | **`[new/changed]`** | `+ ext_hours INTEGER NOT NULL DEFAULT 1`; key `(symbol, timeframe, ext_hours, ts)` (was `(symbol, timeframe, ts)`). One guarded table rebuild in `_migrate_schema`; legacy rows → `ext_hours = 1` (`S16`) |
| `Bar` (`data/models.py`) | `[existing]` | **Unchanged** — the mode travels as a parameter, not a field, so the aggregator/overlay/study consumers are untouched (`S19`) |
| `MissingSpan` / `RequestPlan` (`services/backfill_service.py`) | `[existing]` | **Unchanged shape** — the floor is expressed as one more `MissingSpan`, so `plan_requests` needs no change (`S17`) |
| `TickerSession._bars[timeframe]` | **`[new/changed]`** | Cap becomes `floor_bar_budget(timeframe, ext_hours)` (`S18`); the map stays timeframe-keyed because a session loads one mode at a time (`S19`) |
| `ChartPanel._bars` | **`[new/changed]`** | Same floor-aware cap at `ChartPanel.update_last_bar`'s `:1150`–`:1157` trim (`S18`) — the **third** `SESSION_BAR_CAP` site, so the floor survives the next live candle |
| `popouts.ext_hours` | `[existing]` | Already persists the pop-out's mode; now consumed by the cache/planner through the attached session (`S19`) |
| `footprint_cache` / other tables | `[existing]` | Untouched (D41's drop stands) |

**Migration semantics (recorded):** on an existing user DB the rebuild runs once at the next `DB()`
open; rows are preserved and tagged `ext_hours = 1`. A subsequent **RTH** load therefore starts from
an empty RTH key and issues its own floor fetch — which `AC-D16.8` requires anyway — and a
subsequent **ETH** load reads the legacy rows and re-derives presence by the ETH window. No row is
lost, no hole is created, and no silent re-classification occurs (`AC-D16.9`).

### Integration Points (D42 increment)

| Integration | Status | Why needed / what changes |
|---|---|---|
| IBKR historical data — `MarketDataManager.req_historical_data(..., useRTH=1, extended_hours=…)` → `IBApiClient.historicalData` | `[existing]` | **Unchanged surface.** The depth floor is delivered as more requests with the **existing** `endDateTime`/`duration`/`bar_size` parameters (`S17`); `extended_hours` already selects the session window, so `AC-D16.8`'s two modes need no new API |
| IBKR pacing (`ibkr/pacing.py::pacing_manager`, `MAX_HISTORICAL_PER_600S = 60`) | `[existing]` | **Unchanged.** A 30-session `1 min` floor is ≤ ~42 `1 D` chunks, within one wave; the remainder defers through `_schedule_wave_continuation`. No new budget accounting (`S17`) |
| SQLite (`config/paths.get_db_path()`, `data/db.py`) | `[existing]` | One new column + one guarded rebuild (`S16`); no new table, no new store, no settings key |
| `services/market_calendar.py::session_windows` | `[existing]` | Now the **single** window authority for presence, the bar-level pass, and the floor arithmetic (`S15`, `S18`) |
| Live TWS / orders / news / burst baseline | `[existing]` | **Untouched** — no D42 path reaches the order machinery or the S0/yfinance surfaces |

### Frozen Interfaces (D42 increment)

Interfaces this increment treats as **read-only**: already settled and unmodified by any D42 phase.
Contracts are **verbatim** from the tree at `b48133d` (never paraphrased), with the owning module, so
Task Manager can hand a worker the contract instead of the implementation. (D42's revised/new
surfaces — `find_missing_spans`, `BarCache.save_bars`/`get_bars`/`prune`,
`ChartPanel.update_last_bar`, `CandlestickItem.set_data`/`_draw_candles`,
`TickerSession.set_bars`/`_append_bar`, `bars` — are deliberately **not** listed: they are under
construction this increment, and freezing them would freeze a contract `S13`–`S19` change.)

| Interface | Verbatim contract | Owning module |
|---|---|---|
| `session_windows` `[existing]` | `def session_windows(start_ts: int, end_ts: int, ext_hours: bool) -> List[Dict[str, int]]` | `services/market_calendar.py` |
| `plan_requests` `[existing]` | `def plan_requests(missing_spans: Iterable[MissingSpan], timeframe: str) -> List[RequestPlan]` | `services/backfill_service.py` |
| `MissingSpan` `[existing]` | `@dataclass(frozen=True) class MissingSpan: start_ts: int` / `end_ts: int` | `services/backfill_service.py` |
| `RequestPlan` `[existing]` | `@dataclass(frozen=True) class RequestPlan: endDateTime: str` / `duration: str` / `bar_size: str` / `span_start_ts: int` / `span_end_ts: int` | `services/backfill_service.py` |
| `bar_period_seconds` `[existing]` | `def bar_period_seconds(timeframe: str) -> int` | `services/backfill_service.py` |
| `Bar` `[existing]` | `@dataclass class Bar: symbol: str` / `timeframe: str` / `ts: int` / `open: float` / `high: float` / `low: float` / `close: float` / `volume: float` | `data/models.py` |
| `TIMEFRAME_CONFIG` `[existing]` | `{"1 min": {"duration": "1 D", "bar_size": "1 min"}, "5 mins": {"duration": "5 D", "bar_size": "5 mins"}, "15 mins": {"duration": "5 D", "bar_size": "15 mins"}, "1 hour": {"duration": "10 D", "bar_size": "1 hour"}, "4 hours": {"duration": "30 D", "bar_size": "4 hours"}, "1 day": {"duration": "1 Y", "bar_size": "1 day"}}` | `ibkr/market_data.py` (`S20` explicit non-change) |
| `popouts.ext_hours` `[existing]` | `ext_hours INTEGER NOT NULL DEFAULT 1` on the `popouts` table | `data/db.py` |

All eight were verified **verbatim** against the tree at `b48133d` (Validator, D42 cycle 3); each
owning module exists, no interface is duplicated, and **nothing under construction this increment
appears** in the list.

### Non-Functional Approach (D42 increment)

- **Correctness over legibility at the limit (from `AC-D6.4`/`AC-D7.1`).** The hard invariant is
  `gap >= 0`; `F` yields to the pitch. The guarantee is unit-consistent by construction because
  `median_diff`, `px_per_sec` and `F` all come from the same display-x series and the same ViewBox
  (`S13`, `S14`) — the property `AC-D6.4`'s "same pixel unit" clause demands. **That shared unit is
  the ViewBox logical px `px_per_sec` yields** (`floor_px = 4.0` logical px = **8 device px at DPR
  2**), so `F` is applied and measured in one unit throughout; the WS1 evidence asserts the unit-free
  relations `body <= pitch` / `body == pitch` and **measures** the repro pitch rather than
  hard-coding the requirement's indicative `3.83` (`RC-D42-3`).
- **Performance (from D28.4 / ESC-013 / ESC-020).** The cap is O(1) per regeneration and adds **no**
  sort: the pitch is cached beside the width (`S14`). The `generate-before-setRange` ordering that
  ESC-013/ESC-020 fixed is **preserved** — the candle picture is still generated *after* the real
  x-range is applied, so the cap reads a real `px_per_sec`. The volume width is still computed from
  the **final** view range (`:1303`), i.e. the same unit as the candle picture.
- **Performance / memory (from `AC-D16.8`).** The floor-aware budget (`S18`) is the **only** new
  memory consumer: ~33,120 bars for a `1 min` ETH chart (**~8–16 MB** — 33,120 `Bar` dataclasses
  without `__slots__` plus the two plot arrays), reached only for `1 min` (both modes) and `5 mins`
  (ETH); `1 day`/`4 hours` keep the flat 5,000. Mitigations: the budget is **per `(symbol,
  timeframe, ext_hours)`**, only **chart** sessions backfill (the D25 headless alarm sessions never
  request history), the D28.4 static-layer discipline (one `QPicture` per full rebuild, forming-bar
  ticks in the live layer only) is unchanged, and the single tunable is `MIN_INTRADAY_SESSIONS`.
- **Pacing (from D28.3, `R64`).** The floor is emitted **only when short** and collapses to empty
  once filled, so the steady-state cost is zero extra requests; the first load of each `(symbol,
  timeframe, mode)` costs one floor's worth of chained requests, and everything above the per-wave
  cap defers through the existing continuation timer. No new request kind, no sleep, no storm.
- **No-silent-hole (from `AC-D16.1`/`AC-D16.4`, unchanged).** A day that is present-but-empty for the
  mode is now a **missing span**, so the AC-D16.4 shortfall line and the WARNING record get *more*
  accurate (a genuine halt / IPO morning that IBKR has no bars for is re-probed and surfaced, never
  fabricated). This is a **user-visible** change to the status text and is recorded as such.
- **Test-suite fidelity (from `R64`; `RC-D42-2`).** **Green** is required, but count parity is not,
  and no assertion may be **weakened or deleted**. The D16 **pure-planner** suites keep their
  **exact** semantics (`min_sessions` defaults to `0`). The D16 **load-path** suites change **by
  design** — because the default load mode is **ETH** (`MainWindow.ext_hours_btn` checked at `:244`,
  with the `:1570` fallback) and because `S17` removes the empty-cache single-window branch while
  `S18` changes `prune`'s `keep` — and each such assertion is **corrected, intent-preserving**, with
  its cause named in the plan's correction record (`S21`, `AR-D42-6`). **`ESC-050`:** the set is not
  only the D16 suites — **19 cases in six suites that merely *drive* `MainWindow.load_chart`** change
  by design too (a fixed-size `req_historical_data` stub cannot cover the floor span's many chunks),
  and they are enumerated in the same record. **The invariant** (an **unbounded** reqId source for any
  test that drives the load path with a stubbed feed; exact-request-count and empty-cache-branch
  assertions change by design) is stated so the set is checkable **by rule**, and the generalisable
  **enumeration rule** — *by call site of the changed entry point, not by the suites the design names*
  — is recorded for future increments.
- **Security / live-order safety.** No D42 path transmits an order, connects to TWS in a test, or
  touches the retained order machinery; `check_live_port` and the confirm dialogs are untouched. No
  new credential, endpoint or dependency.
- **Scalability.** The DB grows by one integer per bar and one floor's worth of rows per
  `(symbol, timeframe, mode)`; `prune` remains per-key and bounded. The graph of loaded chart
  sessions — not the watchlist — bounds the memory cost.

### Architecture Risks (D42 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D42-1 | **The cap is applied to one path only** (candle or volume), so the two diverge — exactly **R63** | H | One shared helper (`S13`) with three call sites, and `AC-D9.1`/`AC-D9.2`-driven tests that measure the **rendered** candle body from the `QPicture` bbox and compare the volume `BarOpts.width` against it (`tests/test_volume_width.py`, corrected) |
| AR-D42-2 | **The enshrining tests are weakened instead of corrected**, so the suite stays green on the bug | H | The correction record (plan) names **each** of the five enshrining suites — and the D16 **load-path** suites — with the intent to preserve; the new geometry guard is **RED pre-fix** (body 4.00 logical px > the measured ≈ 3.83 logical-px pitch) and GREEN post-fix, asserts the unit-free relations (`body <= pitch`, `body == pitch`) and **measures** the repro pitch rather than hard-coding it (`RC-D42-3`); the DPR-2 probe's dense/non-dense split keeps both the `>= F` and the `<= pitch` claims |
| AR-D42-3 | **Floor-aware caps are missed**, so `prune`/the in-memory trim silently deletes the floor after fetching it (`AC-D16.8` unachievable) | H | `S18` + a per-timeframe, per-mode budget guard; **all three** `SESSION_BAR_CAP` sites are converted — including `ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`), the site that would re-trim the **displayed** series on the next live candle — plus `BarCache.prune`'s `keep`; the D28.4 cap suites are corrected to assert the derived budget; the retention suite (flat default) stays green |
| AR-D42-4 | **Chained floor fetches vs pacing** — a `1 min` floor is ~42 `1 D` chunks, consuming most of the 600 s budget; a second symbol/pop-out load defers | M | The floor collapses to empty once filled; the wave cap + continuation timer already handle deferral non-blockingly; the D25 headless sessions are out of the floor's scope; `R64`'s per-mode guard proves the floor is reached without starving the current-session path |
| AR-D42-5 | **Mode-aware cache migration of existing rows** — a wrong tag re-classifies real bars | M | One guarded, idempotent rebuild; legacy rows → `ext_hours = 1` (the app's default fetch mode) with the rationale recorded; **no row deleted**; presence stays window-based, so a mis-tagged row cannot manufacture coverage; a migration test asserts row preservation and per-mode reads |
| AR-D42-6 | **Mode-aware presence changes the AC-D16.4 shortfall text** (more days reported missing), and the D16 **load-path** assertions change **by design** (the floor span, the removed empty-cache branch, the floor-aware prune), so a legitimate correction can read as a regression. **`ESC-050`:** the impact analysis **under-enumerated** the affected set **twice** — the suites that merely **drive** the load path (**19 cases in six suites**) and **4 further sites** inside the D16 files (3 of which changed; the 4th, `t40_t05`, is unchanged — its correction lands in `t40_t04`) — and both under-counts surfaced only at reconciliation time, **after** the batch had been dispatched | M | `AC-D16.9` is the normative target; the D16 **pure-planner** suites seed complete days and keep their **exact** expectations (`min_sessions = 0`). **The enumeration is now complete *and* generated by a rule rather than asserted:** `S21` + the plan's correction record name **all 14 changed test functions** in the three D16 files **and the 19 load-path-*driving* cases in the six suites**, each **with its cause**, and every correction is **intent-preserving** — the guarantee survives, only the expected value/branch changes — never weakened. **The former completeness assertion is replaced by the rule (and is now true as well):** enumerate **by call site of the changed entry point, not by the suites the design names**; treat a **fixed-size stub of a changed feed as a defect class** (grep the suite and correct **all** of them in one scoped task — the `ESC-048`/`ESC-050` pair); and state the **invariant** (`ESC-050`) so completeness is checkable **before dispatch**, not discovered by a reconciliation task. Any residual site not named is covered by the invariant, so the mitigation no longer rests on the enumeration being exhaustive by inspection |
| AR-D42-7 | **The D6 floor interacting with the volume pane / D9 volume math** — a capped `w` shrinks volume bars too, and a zero-volume bar's 1-unit tick could vanish at sub-pixel width | M | `AC-D9.1`/`AC-D9.2`'s note says volume inherits the **same** capped `w`; the zero-volume 1-unit tick and the D21.1/D21.2 ceiling rules are untouched; the dense volume test asserts `volume_width == body_width` and `gap >= 0` |
| AR-D42-8 | **`px_per_sec` is read before the real x-range is applied** (the ESC-013/ESC-020 ordering defect) — the cap would see a default range and mis-yield | M | The cap runs inside the **existing** post-`setRange` generation (`:1291` then `:1318`/`:1326`) and inside `_clamp_half_width` (called at `:1303`, after the auto-range branch); the ordering is explicitly preserved, not re-derived |
| AR-D42-9 | **`TIMEFRAME_CONFIG` is left unchanged** while the brief expected `config/` window edits, so the floor is believed to be "just a constant change" | L | `S20` records the non-change **with its reason** (per-request caps + required chaining); `MIN_INTRADAY_SESSIONS` is the one new constant and the floor's single tunable |
| AR-D42-10 | **Offscreen flakiness / DB contention** (recorded gotcha) masks a real regression | L | Full-suite clean run before declaring green; every non-pytest probe exports `DB_PATH` (ESC-043); the DPR-2 probe stays in its isolated `QT_SCALE_FACTOR=2` subprocess |
| AR-D42-11 | **Scope creep into ESC-041/ESC-037** (BUILD-owned) or into the other open BUILD escalations | M | D42 supplies the normative target only; the Code Reviewer flips ESC-041/ESC-037 after re-verification; ESC-032/033/034/036/043/044/045 are explicitly out of scope |

### Requirements → architecture traceability (D42)

| Requirement / journey | Architecture section | Phase (plan) |
|---|---|---|
| `AC-D6.4` (revised: `body = min(max(0.65×pitch, F), pitch)`, `body <= pitch`, floor yields at `pitch < F`, wick stays 1 device px; the unit of `F` is the ViewBox logical px `px_per_sec` yields — 4 logical px = 8 device px at DPR 2, `S13`/`AP-D42-5`/`FI-D42-4`) | `S13`, `S14`, `S21`; components `ui/candlestick_item.py`, `ui/chart_panel.py`; AR-D42-1/2/8 | **Phase 1** |
| `AC-D7.1` (revised: `gap >= 0` hard, `> 0` whenever `pitch > F`, `0` acceptable at the limit, 35 % intent unchanged) | `S13`; Journey 8 edge case | **Phase 1** |
| `AC-D9.1` / `AC-D9.2` + note (volume == price body width, same capped `w`) | `S13`; components `ChartPanel._clamp_half_width`/`_refresh_candles`/`_refresh_live_bar`; AR-D42-7 | **Phase 1** |
| `AC-D16.8` (≥ 30 trading sessions, RTH **and** ETH; sessions counted by bars inside the mode's window; all five intraday windows fall short; mode isolation) | `S15`, `S17`, `S18`, `S19`, `S20`; components `services/backfill_service.py` (`floor_bar_budget`), `data/bar_cache.py`, `ui/ticker_session.py`, `ui/main_window.py`, and **`ui/chart_panel.py::ChartPanel.update_last_bar`** (the third `SESSION_BAR_CAP` site, `RC-D42-1`); AR-D42-3/4/9 | **Phase 2** — with the `ui/chart_panel.py` trim **sequenced after** Phase 1's `ui/chart_panel.py` width task (one shared file) |
| `AC-D16.9` (mode-aware day presence + mode-aware cache; present-but-empty = missing span; both directions; measurables (a)/(b)/(c)) | `S15`, `S16`, `S19`; Data Model `bars`; AR-D42-5 | **Phase 2** |
| Journey 7 / Journey 8 edge cases (dense view, high-DPI, doji, single-bar fallback) | `S13`, `S14` | **Phase 1** |
| Journey 17 edge cases (internal hole, no-fill, genuine closures, Ext Hours mode switch, empty cache, all timeframes/any symbol) | `S15`–`S19`; Non-Functional "No-silent-hole" | **Phase 2** |
| `AC-D16.1` / `AC-D16.3` / `AC-D16.4` (unchanged: no fill, genuine closures stay empty, shortfall surfaced) | `S15` (presence only), `S17` (`min_sessions=0` default), Non-Functional | **Phase 2** (non-regression) + **Phase 3** |
| `AC-D16.7` (ESC-023 New-Year exception) | `[existing]` `market_calendar._holidays_for_year`; untouched | **Phase 3** (non-regression) |
| `A72`, `R63`, `R64` | `S13`, `S21`, `S18`, `S17`; risks AR-D42-1/2/3/4/6 | Phases 1–2 |
| D42 correction record (Task Manager / Build / Code Reviewer) | `S21` + the plan's correction record | Phases 1–3 |
| `ESC-050` — the load-path-**driving** suites (19 cases in six suites) + the **enumeration invariant** and the generalisable **rule** (impact-analysis completeness) | `S21` (invariant + rule), `AR-D42-6`, Non-Functional test-fidelity bullet; the plan's *Corrected — load-path-**driving** suites* table and *Impact-analysis enumeration rule* | Phase 2 (the suites) + Phase 3 (reconciliation) — and **every future increment** |
| D41 (built/committed) — not reopened | Relationship table (no relationship) | — |

### Supersessions and non-changes (D42 increment — recorded, never silent)

1. **`AC-D6.4`'s *unconditional* "body remains ≥ 4 device pixels wide"** → superseded by the
   **density-aware** rule (`S13`). The wick clause (cosmetic 1 device px) is **unchanged**.
2. **`AC-D7.1`'s "the gap remains positive"** (and the D7 dense-view edge case) → relaxed to
   **`gap >= 0`** with `gap > 0` whenever `pitch > F`; a **zero** gap at `pitch <= F` is acceptable
   (owner-confirmed **Q51**). The 35 %-gap intent in the non-dense regime is **unchanged**.
3. **The RTH-only default of the depth floor** → superseded: `AC-D16.8`/`AC-D16.9` cover
   `ext_hours=False` **and** `ext_hours=True` (owner-confirmed **Q52**), one floor, two modes, no
   cross-contamination.
4. **D28.4's flat `SESSION_BAR_CAP`/`RETENTION_BARS = 5000` as the universal bound** → revised to a
   **floor-aware budget** (`S18`), the flat values retained as the default/minimum, applied at **all
   three** `SESSION_BAR_CAP` sites (`TickerSession.set_bars` `:300`, `TickerSession._append_bar`
   `:313`, `ChartPanel.update_last_bar` `:1150`–`:1157`) plus `BarCache.prune`'s `keep` (`:1973`).
5. **Explicit non-changes (recorded so they are not read as omissions):**
   `ibkr/market_data.py::TIMEFRAME_CONFIG` durations, `MAX_HISTORICAL_PER_600S`, the D28.3 wave
   pump, `services/market_calendar.py`, `AC-D16.1`/`AC-D16.3`/`AC-D16.4`, the `Bar` dataclass, the
   order machinery, and the D41 removals.

### Recorded readings and observations (D42 — for the Requirements Analyst, no escalation)

- **`FI-D42-1` — ratified at the architecture level (`S18`).** `AC-D16.8`'s floor is unsatisfiable
  while the D28.4 caps stay flat (11,700 / 28,800 / 5,760 bars vs 5,000). The requirement's
  **outcome** is achievable and unchanged, so the fix is an architecture revision of a prior bound
  (`S18`, supersession 4) — **no Requirements escalation**.
- **`FI-D42-3` — ratified reading.** `AC-D16.9`'s measurable (c) is read as a statement about the
  **presence predicate** on a given bar set (`requirements.md:1967`–`:1969`), consistent with the
  separately required mode-aware key (`:1957`–`:1958`); the cost is one extra fetch per mode switch,
  with no hole and no cross-contamination. The `'LEGACY'` mode is the recorded fallback if a later
  reader takes the clause otherwise.
- **`FI-D42-4` — ratified (`AP-D42-5`).** `AC-D6.4`'s literal "4 device pixels at DPR 2" vs the
  shipped constant's unit (4 ViewBox logical px = 8 device px at DPR 2): the criterion's operative
  clause is "measured in the **same** pixel unit", the shipped constant and unit are kept, and the
  WS1 evidence now **states** the unit (`S13`) — recorded so it is not read as a silent
  reinterpretation.
- **`FI-D42-2` — the correction set is five suites, not two** (a plan addition, not a requirements
  gap): `test_candle_spacing.py:4`–`:10`, `test_volume_width.py:103`–`:104`,
  `test_chart_dpi.py:245`–`:250`, `test_d28_2_sessions.py:166`, `test_d28_4f_panel_bar_cap.py:53`,
  plus the D16 **load-path** set (14 changed test functions) and — `ESC-050` — the six
  load-path-**driving** suites (19 cases) — all corrected **intent-preserving**, none weakened, none
  deleted.

**Handoff:** this increment is validated `Status: APPROVED` (D42 cycle 3 of 3, incl. the `ESC-050`
enumeration amendment); the companion plan is `docs/plan.md` § *D42 — Batch 18b*
(`Status: READY_FOR_TASK_MANAGER`). ESC-041/ESC-037 remain
BUILD-owned and are re-checked by the Code Reviewer against the revised criteria; ESC-038/ESC-042
are resolved on the requirements side; `ESC-050` is the Code Reviewer's to flip after re-verifying the
enumeration above.

---

## D44 increment — Batch 19: the collapsed Watchlist becomes a thin vertical bar that expands to the full panel (validated 2026-10-16, **approved for build**)

> **Status of this increment.** Validated by Plan Artifact Editor & Validator (`Status: APPROVED`,
> 2026-10-16) on a **legacy single-scope run** (no `Phase: P<n>`; the unsuffixed proposal pair; no
> phase gate applies) and **approved for build**. Like the D41/D42 increments above it is **planned and
> approved, not yet as-built**; when it lands this section becomes the as-built record. **D44 is an
> owner-requested net-new UI feature** (Batch 19, recorded 2026-10-16) — the one explicit exception to
> the `## Non-Goals` "no net-new feature / no restyling" bullets, which the owner **revised in place**
> (dated 2026-10-16) rather than leaving a Non-Goal standing that the feature contradicts.
>
> **The collapse mechanism already exists** (D21.11). D44 changes the collapsed ***appearance*** and
> adds the missing **collapsed width** — it does **not** re-implement collapsing, and it does **not**
> touch the collapse API's signatures or semantics.
>
> **This increment revises** the collapsed-appearance clauses of `AC-D21.11.2`/`AC-D21.11.3` and the
> **150px-minimum clause** of `AC-D13.1`/`AC-D17.2` (now **expanded-state only**), and it is the
> revision the owner's `## Non-Goals` edit authorised — each recorded as a **supersession** in
> § *Supersessions and non-changes (D44 increment)*, none silent. `AC-D21.11.1`, `AC-D22.1` (expanded),
> the D13/D17 cap / persistence / drag-enforcement / re-clamp clauses, `AC-D13.2`/`.3`,
> `AC-D17.1`/`.3`–`.6`, `AC-D18.*` and D21.13 are **unchanged**. **D1–D43 are not reopened** and are
> not re-planned.
>
> Requirements of record: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised
> 2026-10-16 17:28) — the D44 status/audit block (`:118`–`:136`), the revised `## Non-Goals`
> (`:258`–`:267`), the D44 work item (`:353`–`:365`), **Journey 37** (`:976`–`:989`), **`### D44`**
> (`:3782`–`:3925`), **`AC-D44.1`–`AC-D44.8`** (`:3854`–`:3891`), the supersession/revision record
> (`:3892`–`:3905`), the edge cases (`:3906`–`:3913`), the correction record (`:3914`–`:3925`),
> **A75–A78** (`:4005`–`:4008`), **R66–R67** (`:4129`–`:4130`) and the Batch-19 summary
> (`:4239`–`:4246`); `docs/requirements/design_gaps.md` **DG74** (`:1177`–`:1182`, open/non-blocking);
> `docs/requirements/open_questions.md` **Q54** (answered 2026-10-16 — owner confirmation requested,
> non-blocking defaults recorded as A75–A77). Companion plan: `docs/plan.md` § *D44 — Batch 19*.
> Review: `docs/plan_review.md` (D44 cycle, `APPROVED`). Module index: `docs/codebase-map.md`
> (refreshed for this batch).
>
> **Escalation state at validation time.** **No escalation is open against this increment's
> decisions**: no `PLAN`-, `BUILD`- or `REQUIREMENTS`-routed entry is `open` (`ESC-050` is
> `addressed`). The single open entry in `docs/code_review/escalations.json` is **ESC-055**
> (`routed_to: TASK_MANAGER`, `severity: nice-to-have`) — the D42/`ESC-050` enumeration rule's
> *ownership remedy*. D44 **applies** that rule (`S28`, `AP-D44-8`) without absorbing the escalation,
> which stays Task Manager's.
>
> **Frozen baseline:** `main` @ **`0c4d478`** (D43 + the D42/Stage-C follow-ups complete; full
> offscreen suite green). Suite invocation `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the
> `pytest` entry point has a stale shebang).

### Summary (D44 increment)

D44 turns the **already-existing** watchlist collapse (D21.11) into a **thin vertical bar**: the dock
is pinned to `WATCHLIST_COLLAPSED_WIDTH = 30px`, renders a rotated `WATCHLIST` label in the app palette
(`#141822` / `#232938` / `#cbd5e1`), and expands back to the **previous** width when the bar is
clicked. The core fix is a **collapsed-aware width rule in the pure, Qt-free `ui/dock_layout.py`
model** — the 150px minimum becomes **expanded-state only** — consumed by **both** clamp branches of
the single apply entry point `MainWindow._apply_dock_widths`, plus the **D21.13-style minimum-width
relaxation** and a deferred re-apply so Qt's own layout minimum cannot re-impose 150px on the next
resize or dock drag. The visual is a small custom `QWidget` with a `paintEvent` drawing the rotated
label (Qt cannot rotate a `QPushButton`'s text), carried as the panel's **full-height** collapsed body
while the dock's **title-bar slot** keeps a 30×28 handle so the dock stays movable (DG37). The
collapse state is **not persisted** (A76), the header strip / `+` (D22.1) / column-header row are
hidden while collapsed and restored on expand (A77), and every supersession (`AC-D21.11.2`/`.3`, the
150px minimum's scope, the `## Non-Goals` restyling bullet) is **recorded** — the affected suites are
**corrected, never weakened** (R67). No new dependency, no new Qt module, no stack change: the
**pyqtgraph chart stack is a locked decision** (`docs/memory.md`, 2026-10-16) and no D44 path reaches
the renderer.

### Codebase Summary (D44 surface — existing repository, source-validated 2026-10-16 @ `0c4d478`)

The repo is **not** greenfield: a PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal (live
TWS 7496, SQLite persistence, PyInstaller `.app`; `graphify-out/graph.json` reports **4,859 nodes /
10,478 edges**, `built_at_commit = 7b98bb9` — discovery only, the source is authoritative). This is a
factual inventory of the surface D44 touches; every item below was read in the tree during planning
and **re-verified independently by the Validator this cycle**.

**Data models / persisted state `[existing]`**

- **No SQLite change.** D44 touches **no table, no column, no migration**. The persisted surface it
  reads is `QSettings("NDThinkChart", "NDThinkChart")` only:
  - `ui/watchlist_panel.py::WATCHLIST_WIDTH_KEY = "watchlist/width"` (`:96`) — the **expanded** dock
    width, written by `save_watchlist_width` (`:126`) from `MainWindow.closeEvent`
    (`ui/main_window.py:3363`) and read by `load_watchlist_width` (`:116`) /
    `MainWindow._read_persisted_width` (`ui/main_window.py:2300`).
  - `ui/watchlist_panel.py::WATCHLIST_COLUMNS_KEY = "watchlist/columns"` (`:77`) — the D21.5 column
    layout (`load_watchlist_columns` `:179` / `save_watchlist_columns` `:188`, sanitised by
    `sanitise_watchlist_columns` `:150`).
  - **There is no collapse key** — D21.11's collapse is in-memory only (`WatchlistPanel._collapsed`,
    `:280`), and A76 keeps it that way.
- **In-memory state D44 touches:** `WatchlistPanel._collapsed` (`:280`), `MainWindow._watchlist_width`
  (`:421`, the "current/requested" dock width), `MainWindow._persisted_watchlist_width` (`:420`),
  `MainWindow._applying_dock_widths` (`:412`, the re-entrancy guard), `MainWindow._dock_clamp_scheduled`
  (`:413`), `MainWindow._dock_splitter` (`:414`, the defensively acquired dock-area splitter).

**Major components and responsibilities (as-built)**

| Component | Responsibility (D44-relevant) |
|---|---|
| `ui/watchlist_panel.py::WatchlistPanel` (`:239`) | `header_bar` — a 28px `QWidget`, `objectName "WatchlistHeader"`, `background: #141822; border-bottom: 1px solid #232938` (`:294`–`:297`), holding `header_button = DiagonalStrikeButton("Watchlist")` (checkable, checked by default, `:301`–`:318`), `add_button` = the D22.1 `+` (`:323`–`:336`) and `search_box` = the D39.1 search field (`:340`–`:361`); `table` (7 configurable columns, `:402`–`:414`) with `body = self.table` (`:417`) and its `horizontalHeader()` = the column-header row; `_on_header_toggled` (`:435`–`:445`) sets `self._collapsed = not visible` and `self.body.setVisible(visible)`; `is_collapsed` / `set_collapsed` / `toggle_collapsed` (`:447`–`:461`). **Today: collapsed = the horizontal header strip stays (struck), the table hides, and the dock keeps its ~220px width.** |
| `ui/main_window.py` dock wiring (`:369`–`:431`) | `self.watchlist_panel = WatchlistPanel()`; `self.watchlist_dock.setObjectName("Watchlist")`, `setWindowTitle("")` (the duplicate title is deleted, `AC-D21.11.1`), `setWidget(self.watchlist_panel)`, **`setTitleBarWidget(self.watchlist_panel.header_bar)`**, `setFeatures(DockWidgetMovable \| DockWidgetFloatable)`, **`self.watchlist_panel.setMinimumWidth(WATCHLIST_MIN_WIDTH)`**, `addDockWidget(LeftDockWidgetArea, …)`, `installEventFilter(self)`, the persisted-width restore (`:420`–`:424`), `QTimer.singleShot(0, self._deferred_dock_setup)` (`:431`). |
| `ui/main_window.py::MainWindow._apply_dock_widths` (`:2459`) | **The single apply entry point** (`D17/D18`), wired to `resizeEvent` (`:2787`–`:2796`), the acquired splitter's `splitterMoved` (`_on_dock_splitter_moved`, `:2725`), the event-filter fallback (`eventFilter` `:2756`–`:2769` → `_on_dock_drag_event` `:2729` → `_schedule_dock_clamp` `:2741`), `changeEvent(WindowStateChange)` (`:2771`), the deferred normalizes (`_deferred_dock_setup` `:2619`, `_deferred_dock_clamp` `:2677`), `_on_right_dock_visibility_changed` (`:2663`) and `closeEvent` (`:3349`). **Two clamp branches:** the right-dock-visible branch calls `_plan_dock_widths` (`:2413`) → the pure `plan_dock_widths`; the right-dock-hidden branch clamps directly — `desired = max(WATCHLIST_MIN_WIDTH, min(base_left, cap))` (`:2527`). **Both clamp to 150 unconditionally today** (DG74). |
| `ui/dock_layout.py` | The pure, Qt-free width model: `CHART_MIN_WIDTH = 400` (`:21`), `WATCHLIST_MIN_WIDTH = 150` (`:24`), `DEFAULT_WATCHLIST_WIDTH = 220` (`:27`), `RIGHT_DOCK_MIN_WIDTH = 200` (`:30`), the cap fractions (`:33`/`:36`), `watchlist_max_width` (`:41`), `right_dock_max_width` (`:52`), `plan_dock_widths` (`:64`, the B3 cross-clamp: `left = max(WATCHLIST_MIN_WIDTH, min(int(requested_left), left_max))` at `:89`, the combined-budget loop at `:100`–`:137`, the infeasible branch `return WATCHLIST_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH` at `:98`). |
| `ui/watchlist_panel.py` width helpers (`:93`–`:130`) | `WATCHLIST_MIN_WIDTH` / `CHART_MIN_WIDTH` / `DEFAULT_WATCHLIST_WIDTH` **aliased** from `dock_layout` (`:93`–`:95`); `watchlist_max_width` (`:99`, delegates), `clamp_watchlist_width` (`:110`, `max(WATCHLIST_MIN_WIDTH, min(width, cap))`), `load_watchlist_width` (`:116`), `save_watchlist_width` (`:126`). The `CHART_MIN_WIDTH` duplication is documented as an invariant (`ui/dock_layout.py:12`–`:14`). |
| `ui/visual_conventions.py` | `set_button_active(button, active)` (`:80`) — sets the `active` dynamic property and repolishes; `ACTIVE_PROPERTY = "active"` (`:39`); `DiagonalStrikeButton` (`:109`) with `struck` (`:133`/`:138`) / `set_struck` (`:144`) / `is_struck` (`:148`) / `strike_line` (`:175`) / `text_area_rect` (`:180`) / `strike_color` (`:186`) and the auto-strike for checkable buttons. **Consumed, never modified.** |
| `tests/` (128 test modules + `conftest.py`) | The suites that reach this surface are enumerated **by call site** in the companion plan (`AP-D44-8`, the `ESC-050`/`ESC-055` rule): 7 suites call `_apply_dock_widths`/`plan_dock_widths` directly (all **expanded**), 3 suites assert the collapsed appearance, 4 suites read `dock_layout` constants. |

**Key entry points / data flow (unchanged shape)**

Collapse: `header_button.toggled` → `WatchlistPanel._on_header_toggled` → `body.setVisible(False)`
(D21.11) — **D44 adds**: the collapsed visual sync → `collapsed_changed` → `MainWindow` (title-bar
swap + min-width pin) → `_apply_dock_widths()` → `plan_dock_widths`/the direct clamp → `resizeDocks`.
Resize/drag: `resizeEvent` / the splitter hook / the event-filter fallback → `_apply_dock_widths` →
the same clamp.

**External integrations already in use `[existing]`**

IBKR TWS over `ibapi` (live port 7496 only), SQLite (`config/paths.get_db_path()`, `DB_PATH`-
overridable), `QSettings` (INI/registry), `yfinance` (D38). **D44 adds no integration and no
dependency** — it is a dock-layout + widget-paint change using Qt APIs the repo already uses
(`QDockWidget.setTitleBarWidget`, `resizeDocks`, the event filter, a `QWidget.paintEvent`).

**What D44 changes, in one line**

The collapse mechanism already exists; **what is missing is (a) a collapsed *width* the layout model
will honour and (b) a collapsed *appearance***. Today the width is clamped unconditionally to 150px at
**two** sites inside the single apply entry point (`ui/dock_layout.py::plan_dock_widths` at `:89`, and
`ui/main_window.py:2527` in the right-dock-hidden branch) and the panel's minimum width is pinned to
150 (`ui/main_window.py:386`), so a 30px bar is snapped back on the next `resizeEvent` or drag
(R66/DG74); and the collapsed state renders the struck horizontal header button instead of a thin bar
(`AC-D21.11.2`/`.3`).

**Validator's independent verification (2026-10-16, offscreen probes @ `0c4d478`).** The plan's three
load-bearing technical claims were re-run independently rather than accepted (Qt 6.11.0, offscreen,
`DB_PATH` exported to a temp file per ESC-043):

1. **The pre-fix RED is achievable for the right reason.** Collapsing through the existing
   `set_collapsed(True)` API leaves the dock at its **expanded** width (measured 256px with a 1138px
   chart area), and `resizeDocks([dock], [30])` clamps to **150** — the `WATCHLIST_MIN_WIDTH` floor.
   A guard asserting the collapsed width therefore fails on the pre-fix tree on the **width**, not on
   an import.
2. **The collapsed width is reachable exactly with the plan's wiring (`AP-D44-1` verified).** The
   dock's reachable floor is decided by its **widget minimums**, not by `resizeDocks`: with the strip
   visible in the title-bar slot the dock's `minimumSizeHint()` is 128px and 30 is unreachable
   (`resizeDocks([dock],[30])` → 128). With the plan's collapsed wiring — strip and table hidden, a
   30px bar as the panel's content, a 30×28 handle as the title-bar widget, panel **and** dock minimum
   relaxed to 30 — `dock.minimumSizeHint() == QSize(30, -1)` and `resizeDocks([dock], [30])` yields
   **exactly 30**, stable across a subsequent window resize; the expand path restores the previous
   width. (`resizeDocks` rejects a 0 size — *"all sizes need to be larger than 0"* — so the collapsed
   width must stay a positive constant; 30 is.)
3. **The title-bar swap is safe and the title bar cannot hold a full-height bar (`FI-D44-2`).**
   `setTitleBarWidget` lays the widget out at the **top** of the dock at its own `sizeHint` height
   (a 28px widget occupied `QRect(0, 0, 63, 28)`), so a full-height vertical bar is impossible in the
   title-bar slot; and swapping the title-bar widget does **not** destroy the outgoing widget on this
   Qt (both the strip and the handle survive a collapse → expand round trip, including after a real
   event-loop turn and a `DeferredDelete` flush).

### Relationship to prior increments (D44) — every decision carries its label

| Prior decision / component | Relationship | Note |
|---|---|---|
| **D21.11 collapse** — `WatchlistPanel.header_bar` + `header_button` + `_on_header_toggled` (`ui/watchlist_panel.py:294`–`:317`, `:435`–`:445`), the public `set_collapsed`/`toggle_collapsed`/`is_collapsed` (`:447`–`:461`), `setTitleBarWidget(self.watchlist_panel.header_bar)` (`ui/main_window.py:381`), `AC-D21.11.2`/`AC-D21.11.3` | **`[revises D21.11: the collapsed appearance]`** | D44 changes the collapsed ***appearance*, not the mechanism**: the collapsed state renders the thin bar instead of the struck header button. `AC-D21.11.2`/`.3` are **superseded for the collapsed state** (recorded, never silent); `AC-D21.11.1` (single "Watchlist" label; the header strip is the title bar while expanded) is **unchanged**, and the `set_collapsed`/`toggle_collapsed`/`is_collapsed` API is **preserved**. |
| **D13/D17 width model** — `WATCHLIST_MIN_WIDTH = 150` (`ui/dock_layout.py:24`), `plan_dock_widths`'s unconditional clamp (`:89`), `_apply_dock_widths`'s direct clamp in the right-dock-hidden branch (`ui/main_window.py:2527`), `AC-D13.1`/`AC-D17.2`'s 150px minimum, `AC-D13.2`/`.3`/`AC-D17.1`/`.3`–`.6` | **`[revises D13/D17: the 150px minimum's scope]`** | The **150px minimum becomes expanded-state only**; while collapsed the width is `WATCHLIST_COLLAPSED_WIDTH`. The cap (`floor(0.50 × chart_area)`), the `CHART_MIN_WIDTH` cross-clamp, the persistence (`watchlist/width`), the drag enforcement and the re-clamp are **unchanged for the expanded state**. |
| **D21.13 collapsed-region pin** — `_sync_right_dock_collapse` (`ui/main_window.py:2374`–`:2411`): relax the dock's **and** the panel's minimum width, `_resize_docks_guarded`, then re-apply on the next event-loop turn because "the dock's layout minimum is recomputed on the next layout pass, so the immediate resize above can be clamped back to the pre-collapse minimum" | **`[extends D21.13: the collapsed-min-width pin pattern]`** | D44's collapsed watchlist reuses **that proven mechanism** (`S24`) instead of inventing a second one — the same defect class (a stale Qt layout minimum re-imposing the expanded minimum) with the same remedy. |
| **D17/D18/B3 pure dock model** — `ui/dock_layout.py` (`plan_dock_widths`, `watchlist_max_width`, `right_dock_max_width`), `MainWindow._plan_dock_widths`'s fixed-point iteration (`:2413`–`:2457`), the `CHART_MIN_WIDTH` cross-module invariant | **`[extends D17/D18: the pure width model]`** | The collapsed rule lives **in the pure model** (`S23`), for the repo's recorded reason (`docs/memory.md` 2026-10-03; the ESC-026 lesson: the pure helper is the single source of truth and a consumer-side workaround masks helper defects). The new parameter defaults to today's expanded behaviour, so every existing 3-argument caller and suite is untouched. |
| **D21.11's dock title bar (DG37)** — the header strip **is** the dock's title bar; deleting the duplicate title would otherwise leave the dock un-draggable; `DockWidgetMovable \| DockWidgetFloatable` retained | **`[extends D21.11: the title-bar/drag affordance]`** | While collapsed the title-bar slot must still hold a draggable widget, so D44 keeps a 30px handle there (`S25`); the dock's `objectName`/window title and features are unchanged (title-keyed dock lookups stay valid — `docs/memory.md` 2026-10-03). |
| **D21.5 columns / D22.1 `+` / D39.1 search** — all live inside `header_bar`; the table's `horizontalHeader()` is the column-header row | **`[extends D21.5/D22/D39: the header strip's contents]`** | A77: while collapsed the strip, the `+` and the column-header row are hidden and return on expand. **No D22/D39/D21.5 behaviour changes** — they are reachable the instant the user expands. |
| **VIS-D21 conventions** — `ui/visual_conventions.py::set_button_active` (VIS-D21.2), `DiagonalStrikeButton` (VIS-D21.1), `ACTIVE_PROPERTY` | **`[extends D21.7/D21.8: the shared highlight convention]`** | The bar's hover/pressed feedback goes through **`set_button_active`** (`AC-D44.6`) — no hand-rolled highlight; `set_button_active` itself is **unchanged** (frozen, below). VIS-D21.1 keeps applying to genuinely hidden/off **buttons** elsewhere (D21.12 volume, D21.13 portfolio). |
| **D14 double-click / D21.5 popup / D22 add-remove / D39 search** | **`[no relationship]`** | Untouched; the frozen-interface list pins their contracts. |
| **D42 (width/cache/depth) and D43 (priming bar size)** | **`[no relationship]`** | D44 touches neither the chart renderer, the load path, the planner, the bar cache nor the priming path. |
| **D41 (right dock = Portfolio-only) / D40 (TWS lifecycle)** | **`[no relationship]`** | The right dock's cap/header/collapse model is unchanged; D44 only feeds a **fixed** collapsed left width into the existing cross-clamp. |

### Tech Stack Decisions (D44 increment)

Constrained (existing) choices first, then the D44 decisions. Every row carries a rationale and the
alternatives considered.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S22 | **Language / UI stack / broker / persistence / packaging / tests** `[existing]` | Unchanged: Python 3.11+ (`.venv`) on macOS Apple Silicon (arm64), **PyQt6** (`>=6.6`), **pyqtgraph** (`>=0.13`), numpy (`>=1.26`), official `ibapi` (pinned `ibapi-latest==10.51.1`; live TWS **7496 only**), **`yfinance==1.7.0`** (the D38 secondary source), SQLite via `config/paths.get_db_path()`, `QSettings`, PyInstaller windowed `.app`, pytest + pytest-qt offscreen (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`). **No new dependency, no new Qt module, no stack change.** | Existing-repo hard constraint (`requirements.md`'s Current Tech Stack; changing it is a Non-Goal). The **pyqtgraph chart stack is a locked decision** — the Lightweight Charts migration was evaluated and declined (`docs/memory.md`, 2026-10-16). D44 is a dock-layout + `paintEvent` change and needs **no** renderer work. | Any new UI/charting/dependency (e.g. a CSS-animated vertical label, a new widget library, the web-chart migration) — rejected. |
| S23 | **The collapsed-width rule — one pure helper, `WATCHLIST_COLLAPSED_WIDTH = 30`** `[new in D44]` — **revises D13/D17's 150px minimum scope** | In **`ui/dock_layout.py`** (the pure, Qt-free model): add **`WATCHLIST_COLLAPSED_WIDTH = 30`**; add a pure **`plan_watchlist_width(chart_area_w: int, requested_left: int, collapsed: bool = False) -> int`** returning `WATCHLIST_COLLAPSED_WIDTH` when collapsed, else `max(WATCHLIST_MIN_WIDTH, min(int(requested_left), watchlist_max_width(chart_area_w)))`; extend **`plan_dock_widths(chart_area_w, requested_left, requested_right, left_collapsed: bool = False)`** so a collapsed left is **fixed at the collapsed width**: `left = plan_watchlist_width(..., collapsed=left_collapsed)`, the left's own floor becomes `WATCHLIST_COLLAPSED_WIDTH` (`left_min`), the cross-clamp loop may shrink **only** the right dock (`left_can_shrink = not left_collapsed and left > WATCHLIST_MIN_WIDTH`), the combined budget keeps `chart_area_w - left - right >= CHART_MIN_WIDTH`, and the infeasible branch returns `(left_min, RIGHT_DOCK_MIN_WIDTH)` — i.e. **today's `(150, 200)` is preserved exactly** for the expanded state. `clamp_watchlist_width(width, chart_area_w)` **delegates** to `plan_watchlist_width(..., collapsed=False)` (one formula, three consumers). | DG74 names this resolution; the repo's recorded lesson is that **the pure helper is the single source of truth and a consumer-side workaround masks helper defects** (`docs/memory.md` 2026-10-03; the ESC-026 round). The rule must serve **three** consumers — `plan_dock_widths`, `_apply_dock_widths`'s right-dock-hidden branch (which does **not** call `plan_dock_widths` at all), and the persistence clamp — so putting it in the model avoids a second divergent implementation. The default `False` keeps **every existing 3-argument call** and the whole D17/D18/T52 suite green, which is what makes the expanded-state criteria verifiably unaffected (`AC-D44.8`). | (i) Clamp only inside `_apply_dock_widths` — leaves `plan_dock_widths`'s own `max(WATCHLIST_MIN_WIDTH, …)` at `:89` to fight it and duplicates the rule in the two branches (ESC-026's failure mode) — rejected. (ii) Flip `WATCHLIST_MIN_WIDTH` to 30 while collapsed (a global constant mutation) — the cap arithmetic, `watchlist_max_width`, the persistence clamp and every imported alias would change meaning mid-flight; a state-dependent *constant* is a defect generator — rejected. (iii) `dock.setMaximumWidth(30)` while collapsed — Qt does not honour a maximum width for a dock-area splitter section consistently, and the max would have to be cleared exactly on expand or the dock could never grow again — rejected. (iv) A separate `ui/collapsed_layout.py` — a second model beside the one the whole dock system already imports — rejected. |
| S24 | **The collapsed-aware apply path + the minimum-width relaxation + the tracked previous width** `[new in D44]` — **extends D17/D18 (the single apply entry point) and D21.13 (the pin pattern)** | **`ui/main_window.py`:** `_apply_dock_widths` reads the watchlist collapse state (**a new local — `watchlist_collapsed` — so it does not shadow the existing `collapsed`, which is the *right region's* state at `:2490`**) and (a) in the **right-dock-visible** branch forwards it to `_plan_dock_widths(chart_area, base_left, base_right, left_collapsed=watchlist_collapsed)` (which forwards it to the pure helper and keeps its fixed-point iteration), (b) in the **right-dock-hidden** branch computes `desired = plan_watchlist_width(chart_area, base_left, collapsed=watchlist_collapsed)`. **`self._watchlist_width` is never assigned while collapsed** — it is the **tracked previous width** that `AC-D44.2` restores (`MainWindow._watchlist_width` already carries it, `:421`). On the collapse transition (`panel.collapsed_changed`) the window **relaxes the minimum width** — `panel.setMinimumWidth(WATCHLIST_COLLAPSED_WIDTH)` and `dock.setMinimumWidth(WATCHLIST_COLLAPSED_WIDTH)`, restored to `WATCHLIST_MIN_WIDTH` on expand — then `_resize_docks_guarded` + **`QTimer.singleShot(0, self._apply_dock_widths)`**, exactly the `_sync_right_dock_collapse` sequence (`:2392`–`:2411`) whose comment records why. `_dock_widths_consistent` (`:2698`) becomes collapsed-aware (a collapsed dock is settled when its width equals the collapsed width) so the deferred clamp does not spin. | `_apply_dock_widths` **is** the single apply entry point, wired to both `resizeEvent` and the drag hook — so `AC-D44.5` ("the collapsed width survives a resize or a drag") is exactly a requirement on this path (R66/DG74). The minimum-width relaxation is **not optional**: the Validator's independent probe (below) confirms a left dock's width is pinned by its **widget minimums**, not by `resizeDocks` (the dock's floor was 128px with the strip visible and exactly 30 with every visible widget at 30). `_watchlist_width`'s meaning is therefore *tightened, not changed*: it is the **expanded/requested** width, and keeping it is what makes the previous-width restore a one-liner instead of new state. | (i) A second "collapsed clamp" entry point beside `_apply_dock_widths` — two paths fighting on every resize/drag is the D17 defect class — rejected. (ii) A new `MainWindow._watchlist_expanded_width` and letting `_watchlist_width` mean "applied" — inverts a field the close-time persistence, the deferred-consistency check and existing tests already read, for no gain — rejected. (iii) `setMaximumWidth`/`setFixedWidth` on the panel while collapsed — a fixed width blocks the splitter entirely and must be undone exactly; the D21.13 minimum relaxation is the repo's proven equivalent — rejected. (iv) Skip the deferred re-apply — the D21.13 evidence says the immediate resize can be clamped back by the next layout pass — rejected. |
| S25 | **The collapsed bar widget + the collapsed title-bar handle** `[new in D44]` — **extends D21.11 (the collapse mechanism/API) and DG37 (dock movability)** | **`ui/watchlist_panel.py`** gains **`class CollapsedWatchlistBar(QWidget)`**: fixed width `WATCHLIST_COLLAPSED_WIDTH`, `Qt.WidgetAttribute.WA_StyledBackground` set, an object-name-keyed stylesheet (`#WatchlistCollapsedBar { background: #141822; border-right: 1px solid #232938; color: #cbd5e1; }` plus a `[active="true"]` variant), and a **`paintEvent`** that fills the styled background (via `super().paintEvent`) and then draws the text **`WATCHLIST` rotated 90° counter-clockwise** (bottom-to-top) centred, in the palette colour; `mousePressEvent`/`mouseReleaseEvent` drive `set_button_active(self, True/False)` and emit **`expand_requested`**; `enterEvent`/`leaveEvent` drive `set_button_active`. **Two instances of the family, two roles:** `panel.collapsed_bar` — the panel's **full-height** collapsed body (a layout child of the panel, shown only while collapsed); `panel.collapsed_handle` — a 30px-wide, 28px-tall styled `QWidget` that is the **dock's title-bar widget while collapsed** (`dock.setTitleBarWidget(panel.collapsed_handle)` on collapse, `dock.setTitleBarWidget(panel.header_bar)` on expand — the current, D21.11 wiring), so the dock stays movable/floatable (DG37). Clicking **either** expands (`AC-D44.2`). The collapse API (`set_collapsed`/`toggle_collapsed`/`is_collapsed`) keeps its signatures and semantics. | Qt cannot rotate a `QPushButton`'s text, so the label needs a custom `paintEvent` (the requirement records this). **Probe-verified (Plan and Validator independently, 2026-10-16):** for a dock in `LeftDockWidgetArea`, `setTitleBarWidget(w)` lays `w` out at the **top of the dock, at the dock's full width and `w`'s own `sizeHint` height** — even with `setWidget(None)` (i.e. the title bar never fills the dock). A *full-height* vertical bar is therefore impossible in the title-bar slot, so the full-height bar is the dock's **content** and the title-bar slot keeps a small handle for the drag affordance — which is what `A78` means by "the dock's title-bar widget presents the bar **while keeping the dock movable (DG37)**". `WA_StyledBackground` is required for a custom `QWidget` subclass to honour a stylesheet background (the classic Qt gotcha) and keeps the palette in one declared place. | (i) **The bar as the title-bar widget only** (A78's option (i) read literally) — the rotated label would be confined to a ~90px box at the top of the column with bare panel below; recorded as the **fallback** if the handle proves problematic, but it makes the label's position depend on title-bar geometry — rejected as the primary. (ii) **Reorient the existing `header_bar` in place** (A78's option (ii)) — the same title-bar geometry limit applies, and `header_bar` is the widget whose `+`/search contents must hide (A77) — rejected. (iii) **`dock.setWidget(bar)` while collapsed, `setWidget(panel)` on expand** — reparents the live table (subscriptions, flash timers, persisted columns) on every toggle and risks a stray top-level window — rejected. (iv) Painting the label in the **panel's** own `paintEvent` instead of a child widget — spreads the visual across two widgets and makes the "rotated-label widget exists" measurable (`AC-D44.1`) vague — rejected. (v) `set_button_active` on hover/pressed — **chosen** (not an alternative): it is the repo's established convention (`AC-D44.6`). |
| S26 | **The collapsed visual state (A77) + the transition signal + the palette** `[new in D44]` — **extends D21.11** | `WatchlistPanel._apply_collapsed_visual()` runs inside `_on_header_toggled` and **explicitly** `hide()`/`show()`s the strip and the body: while collapsed `header_bar.hide()` (which also hides the D22.1 `+` and the D39.1 search box, its children) and `table.hide()` (whose `horizontalHeader()` is the column-header row), and `collapsed_bar.show()` with the collapsed panel styling (`#141822` + a 1px `#232938` right border so the 30px column reads as one panel, not a bare widget); on expand the reverse (**un-hiding `header_bar` as it is restored to the title-bar slot, so the title bar is never a hidden widget**). A new **`collapsed_changed = pyqtSignal(bool)`** is emitted from `_on_header_toggled` so `MainWindow` does the **dock-level** work (title-bar swap, minimum-width pin, width apply) — `S24`. Palette: background `#141822`, border `#232938`, text `#cbd5e1` (D44's own palette list — **not** the mockup's white pill, which the owner explicitly clarified as mockup-tool styling). Hover/pressed via `set_button_active`. | `AC-D44.4`'s measurable is `isVisible()` on the strip, the `+` and the column-header row — which requires **explicit** hide/show (a title-bar swap alone does not hide `header_bar` deterministically, and a hidden widget is skipped by the layout so it cannot pin the minimum either). The signal keeps the layering honest: the panel owns widget state, the window owns the dock. | (i) The panel reaching into its parent dock for `setTitleBarWidget` — a widget doing its owner's job, and it breaks the bare-panel harness (`tests/test_watchlist_add_remove_d22.py`) — rejected. (ii) `MainWindow` polling `is_collapsed()` in `resizeEvent` only — no transition hook, so the minimum pin and the title-bar swap would never happen — rejected. (iii) `QStackedLayout` swapping the strip for the bar — the strip is the *title bar*, not a stack page; the swap is still needed — rejected. (iv) Leaving the strip visible but empty while collapsed — contradicts A77/`AC-D44.4` — rejected. |
| S27 | **No persistence of the collapse state (A76)** `[new in D44]` | **No new `QSettings` key.** `WatchlistPanel._collapsed` starts `False` (the app starts **expanded**). The D13/D17 key `watchlist/width` keeps holding the **expanded** width: `closeEvent`'s `save_watchlist_width(self._settings, self._watchlist_width, self._chart_area_width())` (`ui/main_window.py:3363`) is **unchanged**, and because `_watchlist_width` is never overwritten while collapsed (`S24`), a session that ends **collapsed** still persists the user's expanded width. | A76 (owner-flagged #2, decided) + the D10/A36 precedent that UI show/hide toggles are not persisted. Recording the **expanded** width is the only choice that keeps "the app starts expanded" meaningful: persisting the applied 30px would be re-clamped to the 150px minimum by `clamp_watchlist_width` on the way out, silently losing the user's width. A76 is silent on the close-while-collapsed case, so the decision is recorded (`AP-D44-2`, `FI-D44-3`, ratified) rather than assumed silently. | (i) Persist a `watchlist/collapsed` key — contradicts A76 and needs a restore-time visual sync before the first layout pass — rejected. (ii) Persist the applied (30px) width while collapsed — the silent-width-loss failure above — rejected. (iii) Persist the collapse state in the existing width key as a sentinel (e.g. `0`) — overloads a documented numeric key and breaks `_read_persisted_width`'s `max(WATCHLIST_MIN_WIDTH, width)` — rejected. |
| S28 | **Test surface** `[new in D44]` — **corrects 3 suites (4 sites + 1 docstring), extends 2, adds 2, verifies the rest unchanged by call site** | **Corrected (never weakened, never deleted — R67):** `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (the collapsed appearance), `::test_D21_10_T03` (the collapsed appearance **and** the collapsed-width leg **and** the title-bar/drag leg), `tests/test_watchlist_nonregression_d22.py`'s D21.11 block **plus its module docstring** (`:10`), `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (`hb.isVisible()` while collapsed). **Extended:** `tests/test_dock_layout.py` (the collapsed pure cases + the constants/agreement test) and `tests/test_watchlist.py` (the collapsed delegate case). **Added:** `tests/test_dock_widths_collapsed_d44.py` (`AC-D44.5`'s pinning guard, `AC-D44.2`'s previous-width restore, `AC-D44.7`'s no-key assertion, `AC-D44.1`'s width measurable) and `tests/test_watchlist_collapsed_bar_d44.py` (`AC-D44.1`/`.3`/`.4`/`.6` — the bar, the rotated label, the palette, the hidden strip/`+`/header row, `set_button_active`). **Verified unchanged (enumerated by call site):** `test_dock_widths_d17.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_right_dock_d21.py`, `test_dock_d18_region.py`, `test_d10_d13_integration.py`, `test_dock_layout.py::test_T52_T04`, `test_toolbar_scroll_d19.py` — all drive the changed entry points with the watchlist **expanded**, and the new parameters default to the expanded rule. **The new guard must be RED at `0c4d478` for the right reason** — the collapsed dock staying at ~220px / the 150px minimum, **not** an `ImportError` on the new constant (so the guard asserts the observable outcome through the existing `set_collapsed` API, with the constant referenced defensively). | R67 names exactly this regression surface; `AC-D44.8` requires the guard to fail pre-fix and the expanded suites to stay green (or be updated in lockstep). The enumeration is by **call site of the changed entry point, not by the suites the design names** — the recorded `ESC-050` rule and `ESC-055`'s ownership remedy (`AP-D44-8`) — because this repo has twice been burned by an under-enumerated impact analysis (`FI-D42-2`, `ESC-050`) and once by an invalidated assertion outside the changing task's file (`ESC-055`). | (i) Delete the collapse-appearance assertions — forbidden (correct, do not weaken) — rejected. (ii) Relax them to "no exception raised" — the exact "weakened" failure mode — rejected. (iii) Leave `test_dock_widths_d17.py`/`d18*` alone *and unverified* — the plan enumerates them explicitly instead, so a green suite is evidence rather than luck — rejected. (iv) Put the new guard in an existing suite — a new file makes the RED-at-`0c4d478` demonstration clean and keeps the D44 evidence in one place — rejected. |

### System Components (D44 increment)

**Existing, unchanged** `[existing]`

`ui/chart_panel.py` and the whole pyqtgraph render stack (**locked**), `ui/candlestick_item.py`,
`ui/ticker_session.py`, `services/*` (the planner, the calendar, the collapse map, the alarms, the
search), `data/*` (no schema change), `ibkr/*`, `ui/active_portfolio_panel.py` and the
D18/D21.13/D41 right-dock model, `ui/popout_window.py`, the D14/D21.5/D22/D39 watchlist behaviour,
`ui/visual_conventions.py`'s conventions (consumed, not modified), `ui/dock_layout.py`'s existing
constants and cap arithmetic — i.e. **nothing D1–D43 depends on is redesigned**.

**New / changed** `[new/changed]`

| Component | Change |
|---|---|
| `ui/dock_layout.py::WATCHLIST_COLLAPSED_WIDTH` | **New constant** `= 30` (the collapsed bar width, A75) (`S23`) |
| `ui/dock_layout.py::plan_watchlist_width` | **New pure helper** — the single collapsed/expanded width rule; three consumers (`S23`) |
| `ui/dock_layout.py::plan_dock_widths` | Gains `left_collapsed: bool = False`; a collapsed left is fixed at the collapsed width, its floor becomes 30, the cross-clamp shrinks only the right; the expanded behaviour (including the infeasible `(150, 200)` branch) is **bit-for-bit preserved** (`S23`) |
| `ui/dock_layout.py::clamp_watchlist_width` | Now **delegates** to `plan_watchlist_width(..., collapsed=False)` — the same formula in one place (`S23`) |
| `ui/watchlist_panel.py::CollapsedWatchlistBar` | **New widget** — rotated `WATCHLIST` label, app palette, `WA_StyledBackground`, `expand_requested`, `set_button_active` hover/pressed (`S25`) |
| `ui/watchlist_panel.py::WatchlistPanel.collapsed_bar` / `::collapsed_handle` | **New widgets** — the full-height collapsed body and the 30×28 collapsed title-bar handle (`S25`) |
| `ui/watchlist_panel.py::WatchlistPanel.collapsed_changed` | **New signal** `pyqtSignal(bool)` emitted from `_on_header_toggled` (`S26`) |
| `ui/watchlist_panel.py::WatchlistPanel._apply_collapsed_visual` | **New** — explicit hide/show of `header_bar` + `table`, show/hide of the bar, the collapsed panel styling (`S26`) |
| `ui/watchlist_panel.py::WATCHLIST_COLLAPSED_WIDTH` | **New alias** of `dock_layout.WATCHLIST_COLLAPSED_WIDTH` (the same pattern as the other width constants, `:93`–`:95`) (`S23`) |
| `ui/main_window.py::MainWindow._apply_dock_widths` | Collapsed-aware in **both** branches; `_watchlist_width` never overwritten while collapsed (`S24`) |
| `ui/main_window.py::MainWindow._plan_dock_widths` | Forwards `left_collapsed` to the pure helper (`S24`) |
| `ui/main_window.py::MainWindow._dock_widths_consistent` | Collapsed-aware (settles in one pass) (`S24`) |
| `ui/main_window.py::MainWindow._on_watchlist_collapsed_changed` | **New** — the title-bar swap + the minimum-width pin + the deferred re-apply; wired to `panel.collapsed_changed` (`S24`, `S25`) |
| `tests/test_dock_widths_collapsed_d44.py`, `tests/test_watchlist_collapsed_bar_d44.py` | **New suites** (`S28`) |

### Data Model (D44 increment)

| Entity | Status | Key fields / change |
|---|---|---|
| `watchlist/width` (`QSettings`, `ui/watchlist_panel.py:96`) | `[existing]` | **Unchanged** — still the **expanded** width; written by `save_watchlist_width` from `closeEvent`; **never written while collapsed** (`S27`) |
| Collapse state | `[existing]` | In-memory only — `WatchlistPanel._collapsed` (`:280`), starts `False` (the app starts expanded); **no new key** (A76/`S27`) |
| `MainWindow._watchlist_width` | **`[new/changed]`** | **Semantics tightened, not changed:** it is the **expanded/requested** dock width and is **never assigned while collapsed** — it *is* the "width held immediately before collapsing" that `AC-D44.2` restores (`S24`) |
| `MainWindow._persisted_watchlist_width` | `[existing]` | Unchanged — the raw persisted request re-applied post-`show()` (`:420`, `_deferred_dock_setup` `:2632`) |
| `ui/dock_layout` constants | **`[new/changed]`** | `+ WATCHLIST_COLLAPSED_WIDTH = 30`; `WATCHLIST_MIN_WIDTH = 150` keeps its value but is now **expanded-state only**; `CHART_MIN_WIDTH` and its cross-module invariant are unchanged (`S23`) |
| `WatchlistPanel.collapsed_bar` / `::collapsed_handle` | **`[new/changed]`** | Two new widgets with no persisted state (`S25`) |
| `bars`, `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline` (SQLite) | `[existing]` | **Untouched** — no DDL, no migration, no row change |
| `Bar` / `MissingSpan` / `RequestPlan` (`data/models.py`, `services/backfill_service.py`) | `[existing]` | Untouched |

### Integration Points (D44 increment)

| Integration | Status | Why needed / what changes |
|---|---|---|
| IBKR TWS over `ibapi` (`ibkr/client.py`, `ibkr/market_data.py`) | `[existing]` | **Untouched.** Collapse/expand is **pure UI state** and works disconnected (Journey 37's precondition); no request, no subscription, no order is affected |
| SQLite (`config/paths.get_db_path()`, `data/db.py`) | `[existing]` | **Untouched** — no schema, no migration, no write |
| `QSettings("NDThinkChart", "NDThinkChart")` | `[existing]` | **Unchanged surface:** `watchlist/width` + `watchlist/columns` only. **No collapse key is added or written** (`AC-D44.7`/A76) |
| Qt dock layout (`QDockWidget.setTitleBarWidget`, `resizeDocks`, `setMinimumWidth`, the dock-area splitter + event filter) | `[existing]` | The same APIs D17/D21.11/D21.13 already use; D44 introduces **no new dependency and no new module import**. `QWidget.paintEvent` + `QPainter` are already in the repo (`ui/visual_conventions.py::DiagonalStrikeButton.paintEvent` `:190`; `ui/candlestick_item.py::CandlestickItem._draw_candles` paints into a `QPicture`, `:135`); `QPainter.rotate` is **new to this codebase** but is a standard Qt painter transform (no import beyond `QtGui`, already imported) |
| `yfinance` (D38), the D39 burst baseline, the D25 alarm monitor, the order machinery | `[existing]` | **Untouched** — no D44 path reaches them |

### Frozen Interfaces (D44 increment)

Interfaces this increment treats as **read-only**: already settled and modified by **no** D44 task.
Contracts are **verbatim** from the tree at `0c4d478` (never paraphrased), with the owning module, so
Task Manager can hand a worker the contract instead of the implementation. (D44's revised/new surfaces
— `plan_dock_widths`'s collapsed mode, `plan_watchlist_width`, `clamp_watchlist_width`,
`MainWindow._apply_dock_widths`/`::_plan_dock_widths`/`::_dock_widths_consistent`,
`WatchlistPanel._on_header_toggled`/`::_apply_collapsed_visual` and the two new widgets — are
deliberately **not** listed: they are under construction this increment, and freezing them would
freeze a contract `S23`–`S26` change.) Every entry was re-verified in source by the Validator this
cycle; every owning module exists and is listed in `docs/codebase-map.md`; there are no duplicates.

| Interface | Verbatim contract | Owning module |
|---|---|---|
| `set_button_active` `[existing]` | `def set_button_active(button: QWidget, active: bool) -> None` | `ui/visual_conventions.py` |
| `ACTIVE_PROPERTY` `[existing]` | `ACTIVE_PROPERTY = "active"` | `ui/visual_conventions.py` |
| `DiagonalStrikeButton` (VIS-D21.1) `[existing]` | `class DiagonalStrikeButton(QPushButton)` with `struck` (property), `def set_struck(self, value: bool) -> None`, `def is_struck(self) -> bool`, `def strike_line(self) -> QLineF`, `def text_area_rect(self) -> QRectF`, `def strike_color(self) -> QColor` | `ui/visual_conventions.py` |
| `WatchlistPanel` signals `[existing]` | `row_double_clicked = pyqtSignal(str)` · `symbol_add_requested = pyqtSignal(str)` · `symbol_remove_requested = pyqtSignal(str)` · `search_text_changed = pyqtSignal(str)` · `search_sample_selected = pyqtSignal(object)` | `ui/watchlist_panel.py` |
| `WatchlistPanel` collapse API `[existing]` | `def is_collapsed(self) -> bool` · `def set_collapsed(self, collapsed: bool) -> None` · `def toggle_collapsed(self) -> None` — **signatures and semantics preserved**; the *collapsed appearance* they gate is revised by D44 (`AC-D21.11.2`/`.3`). The private `_on_header_toggled` that backs them **is** modified (it gains the visual sync + the signal) and is therefore **not** frozen | `ui/watchlist_panel.py` |
| `WatchlistPanel` data API `[existing]` | `def active_row_count(self) -> int` · `def add_symbol(self, symbol: str, contract)` · `def remove_symbol(self, symbol: str) -> bool` · `def clear(self)` · `def set_market_data_manager(self, md_manager)` · `def set_subscription_manager(self, sub_manager)` · `def set_price_sink(self, sink)` · `def set_add_enabled(self, enabled: bool) -> None` · `def set_search_enabled(self, enabled: bool) -> None` | `ui/watchlist_panel.py` |
| Panel width/persistence helpers `[existing]` | `def watchlist_max_width(chart_area_w: int) -> int` · `def load_watchlist_width(settings: QSettings, chart_area_w: int) -> int` · `def save_watchlist_width(settings: QSettings, width: int, chart_area_w: int) -> int` · `WATCHLIST_WIDTH_KEY = "watchlist/width"` | `ui/watchlist_panel.py` |
| Panel pure helpers (D14/D21.5/D22) `[existing]` | `def should_load_on_double_click(current_symbol: str, requested_symbol: str, connected: bool) -> str` · `def normalise_symbol(text) -> str` · `def symbol_in_list(symbol, symbols) -> bool` · `def ensure_symbol_present(fields) -> list[str]` · `def sanitise_watchlist_columns(raw) -> list[str]` · `def load_watchlist_columns(settings: QSettings) -> list[str]` · `def save_watchlist_columns(settings: QSettings, fields) -> list[str]` · `WATCHLIST_COLUMNS_KEY = "watchlist/columns"` | `ui/watchlist_panel.py` |
| Dock-width model constants `[existing]` | `CHART_MIN_WIDTH = 400` · `WATCHLIST_MIN_WIDTH = 150` · `DEFAULT_WATCHLIST_WIDTH = 220` · `RIGHT_DOCK_MIN_WIDTH = 200` · `WATCHLIST_CAP_FRACTION = 0.50` · `RIGHT_DOCK_CAP_FRACTION = 0.40` (the **values** are frozen; `WATCHLIST_MIN_WIDTH`'s *scope* narrows to the expanded state, `S23`) | `ui/dock_layout.py` |
| Dock-width model helpers `[existing]` | `def watchlist_max_width(chart_area_w: int) -> int` · `def right_dock_max_width(chart_area_w: int) -> int` | `ui/dock_layout.py` |
| `plan_dock_widths`'s **expanded contract** `[existing]` | `def plan_dock_widths(chart_area_w: int, requested_left: int, requested_right: int) -> tuple` — **the 3-argument positional call keeps today's behaviour exactly** (the new `left_collapsed` defaults to `False`); the guarantees it documents (`each returned width within its own [min, max] cap`, the chart minimum preserved where feasible, neither width below its dock minimum, stable ints, never raises) are unchanged, and the infeasible branch still returns `(150, 200)`. The **collapsed mode** of the same symbol is new and is **not** frozen | `ui/dock_layout.py` |
| `CHART_MIN_WIDTH` invariant `[existing]` | `ui/dock_layout.py:12`–`:14`: "Constants here are kept in agreement with the pre-existing D13 constants in `ui/watchlist_panel` — in particular `CHART_MIN_WIDTH` must equal `ui/watchlist_panel.CHART_MIN_WIDTH`." | `ui/dock_layout.py` ↔ `ui/watchlist_panel.py` |
| `MainWindow` dock helpers `[existing]` | `def _chart_area_width(self) -> int` · `def _read_persisted_width(self) -> int` · `def _resize_docks_guarded(self, docks, sizes) -> None` | `ui/main_window.py` |
| Watchlist dock identity `[existing]` | `self.watchlist_dock.setObjectName("Watchlist")` · `self.watchlist_dock.setWindowTitle("")` · `setFeatures(DockWidgetMovable \| DockWidgetFloatable)` — title/objectName-keyed lookups and the dock's movability depend on these (`docs/memory.md` 2026-10-03; DG37). The **title-bar widget** is swapped while collapsed (`S25`) — the dock's identity is not | `ui/main_window.py` |

### Non-Functional Approach (D44 increment)

- **Correctness of the width invariant (from `AC-D44.5`, R66).** The hard requirement is that the
  collapsed width **survives both drivers** — a window `resizeEvent` **and** a dock drag — because
  `_apply_dock_widths` is the single apply point for both. The rule is pure and unit-testable (`S23`),
  and the minimum-width relaxation + deferred re-apply (`S24`) is what stops Qt's own layout minimum
  from re-imposing 150px (probe-verified: the dock's floor is exactly 30 with every visible widget at
  30, and 128px with the strip visible). The `CHART_MIN_WIDTH` invariant holds in **both** states (the
  cross-clamp still guarantees `chart_area_w - left - right >= CHART_MIN_WIDTH` where feasible, and on
  an infeasible window the dock minimums still win — with the collapsed left's floor at 30 the
  window's own minimum drops by 120px, which is a *gain*, not a regression).
- **Measurement and tolerance (from the repo's own convention; `FI-D44-1`, ratified).**
  `_apply_dock_widths` re-issues `resizeDocks` only when the delta exceeds 1px (an explicit acceptance
  criterion), and the D17 suite records that "a residual of at most 1px is expected and asserted with
  `+1`" (`tests/test_dock_widths_d17.py:17`–`:21`). The guard asserts the **dock** equality
  (`watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`) **exactly, as the criterion writes it**, and
  keeps the `+1` convention for inner/derived measurements the criteria do not name — probe-verified
  exact offscreen (`resizeDocks([dock], [30])` → 30). The 1px dead-band is itself unchanged behaviour,
  so the guard asserts after the apply path has run and must not manufacture a 1px residual by its own
  driving sequence. Recorded as `AP-D44-4`/`FI-D44-1`.
- **Performance (no regression).** Collapse/expand is **O(1)**: no fetch, no re-render, no table
  rebuild, no sort, no new timer beyond the existing single-shot coalescer; the bar's paint is one
  rotated `drawText` per expose. The dock-width change triggers a Qt layout pass only — the D28.4
  render discipline (one `QPicture` per full rebuild; live ticks in the live layer) is untouched, and
  no chart data path is entered.
- **Visual and accessibility (from `AC-D44.1`/`AC-D44.6`, A75).** 30px is ≥ the 28px header height, so
  the bar is a comfortable click target; the label is rotated 90° **counter-clockwise** (bottom-to-top)
  and centred in the column; the palette is the app's (`#141822` background, `#232938` border, `#cbd5e1`
  text) so the bar reads as **a panel, not the mockup's white pill** (the owner's explicit
  clarification); hover/pressed feedback goes through `set_button_active` so the affordance is
  discoverable and consistent with the D21 conventions; the whole column — not just the label — is the
  click target (`AC-D44.2`). The palette is asserted from the widget's **stylesheet** and the `active`
  property (DPI-independent); the **rendered** palette check ("no white pill") is the Code Reviewer's
  independent verification, which D44's own correction record assigns to it.
- **No persistence, no state leakage (A76).** No new settings key; the collapse state is in-memory and
  starts `False`; the persisted width stays the expanded one (`S27`).
- **Test-suite fidelity (R67; the `ESC-050`/`ESC-055` enumeration rule).** **Green** is required; the
  *collapsed-appearance* and collapsed-width assertions change **by design** and are **corrected with
  their cause**, never weakened or deleted; every suite that merely *drives* a changed entry point is
  enumerated **by call site** and verified unchanged (`S28`, `AP-D44-8`); and the new guard is **RED at
  `0c4d478` for the right reason** (the collapsed dock at its expanded width / the 150px floor, not an
  `ImportError`) — the repo's own credibility rule (`docs/memory.md` 2026-10-05: "a regression guard is
  only credible if it fails on the pre-fix tree and passes post-fix"). Because the changed path is
  **collapsed-gated** and every other suite in the tree runs **expanded**, the enumeration's
  completeness rests on that gate (plus the default-preserving signature) and on the full-suite run as
  the backstop — stated so the claim is checkable by rule rather than by inspection.
- **Live-order safety / security.** No D44 path transmits an order, connects to TWS in a test, touches
  the DB, or reaches the retained order machinery; `check_live_port` and the confirm dialogs are
  untouched; **no new credential, endpoint, dependency or module import**. Offscreen probes honour
  ESC-043 (`DB_PATH` exported to a temp file).
- **Scalability.** None to speak of: a single widget, two integers, one 30px-wide column. The dock
  model stays O(1) per apply, and the fixed-point iteration in `_plan_dock_widths` converges exactly as
  before (the cap contraction is unchanged).

### Architecture Risks (D44 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D44-1 | **The collapsed width is snapped back to `WATCHLIST_MIN_WIDTH`** by the clamp on the next `resizeEvent`/drag, so the thin bar never sticks — the **R66** defect class (and the D17/D19 defect class: a clamp not wired to every driver) | H | The collapsed rule lives in the pure model and is consumed by **both** clamp branches of the single apply entry point (`S23`, `S24`); the minimum-width relaxation + deferred re-apply mirrors the proven D21.13 sequence; and `AC-D44.5`/`AC-D44.8` demand a **RED-at-`0c4d478`** guard that drives **both** a `resizeEvent` and the drag-event path |
| AR-D44-2 | **A stale Qt layout minimum re-imposes 150px** on the layout pass after the transition (the D21.13 comment's exact failure) | M | Relax the panel's **and** the dock's minimum in the transition, then `QTimer.singleShot(0, self._apply_dock_widths)` (`S24`); the guard processes the event loop and re-asserts the collapsed width; the probe establishes that widget minimums (not `resizeDocks`) decide whether 30 is reachable |
| AR-D44-3 | **The title-bar swap breaks the dock's drag/float affordance (DG37)** or the title/objectName-keyed dock lookups | M | The collapsed title-bar slot holds a real widget (`panel.collapsed_handle`), the same mechanism D21.11 proved works; `DockWidgetMovable \| DockWidgetFloatable`, the `objectName` and the empty window title are **unchanged** (frozen list); the corrected `test_D21_10_T03` re-points the double-click-to-float assertion at the handle instead of deleting it; the swap is probe-verified not to destroy the outgoing widget |
| AR-D44-4 | **The enshrining suites are weakened instead of corrected**, so the suite stays green while the behaviour regresses (R67) | H | The correction record names **each** site with its **cause** and the intent it preserves; the collapsed-appearance assertions move to the collapsed state and the expanded-state width assertions move to the expanded state — none deleted; the VIS-D21.1 strike assertions are re-pointed to the buttons where the convention still applies (D21.12/D21.13) rather than dropped |
| AR-D44-5 | **A real splitter drag on a 30px dock does not deliver the events the fallback watches** (the event filter is installed on the dock; the handle sits at the chart's left edge), so the drag-time clamp misses | M | The acquired splitter's `splitterMoved` hook (when reachable) + `MouseButtonRelease` + the `resizeEvent` path + the coalescing deferred clamp all route to the same collapsed-aware apply; the guard drives `resizeEvent` **and** `_on_dock_drag_event` explicitly (`AC-D44.8`'s own words: "a simulated resize/drag") |
| AR-D44-6 | **The expand path restores the wrong width** — `_watchlist_width` overwritten by the collapsed plan, so expanding lands on 30 (clamped to 150) instead of the previous width | M | `_watchlist_width` is never assigned while collapsed (`S24`, `S27`); the guard collapses from a known width `W` and asserts the **tracked** width is restored exactly — `win._watchlist_width == clamp(W)` (by construction) — on expand, including the min-150 and at-cap edge cases, with a **tolerant** rendered-width check (`AC-D44.2`, restated 2026-10-16 per ESC-057 + D44's edge cases) |
| AR-D44-7 | **Scope creep** into the D21.11 API, the D22.1 `+`, the D39.1 search box, the D14 double-click, the D21.5 column popup, or the D18/D21.13/D41 right dock | M | The frozen-interface list pins those contracts; the relationship table records the explicit non-changes; the corrected suites keep asserting them |
| AR-D44-8 | **Offscreen flakiness / `QSettings` leakage between tests** masks a regression (the recorded gotcha class) | L | Full offscreen suite run before declaring green; the D22 harness's per-test `QSettings` ini for the new suites; the palette/hover assertions read the widget's stylesheet and the `active` property rather than rendered pixels (DPI-independent) |
| AR-D44-9 | **The 30px bar is not legible/clickable on a HiDPI display** (the 1px borders and the rotated text at 30px) | L | The width is a named constant (tunable), the whole column is the click target, the label is centred with a 1px right border (29px of fill), and the palette is asserted from the stylesheet rather than from pixels; a strict visual check is left to the Code Reviewer's independent verification |
| AR-D44-10 | **D42's width/`_bars`-trim and D43's priming work are disturbed** by an edit above their cited lines in `ui/main_window.py` (the docs cite line numbers; the file is edited often — `docs/memory.md`) | L | D44 edits no data path; the plan cites **symbols** as the primary pointer (the repo's source-citation convention) and any doc line reference in this increment is **indicative only** |

### Requirements → architecture traceability (D44)

| Requirement / journey | Architecture section | Phase (companion plan) |
|---|---|---|
| **`AC-D44.1`** (collapsed form — a thin vertical bar of `WATCHLIST_COLLAPSED_WIDTH` in `LeftDockWidgetArea` with the rotated `WATCHLIST` label and the app palette, not white) | `S23` (the width), `S25` (the bar widget), `S26` (the palette/visual state); components `ui/dock_layout.py`, `ui/watchlist_panel.py`; AR-D44-1/2/9 | **Phase 1** (width + widget, ordered tasks) |
| **`AC-D44.2`** (click the bar → expand to the **previous** width, re-clamped) | `S24` (`_watchlist_width` = the tracked previous width; the apply path), `S25` (`expand_requested`), `S26` (the transition); AR-D44-6 | **Phase 1** |
| **`AC-D44.3`** (collapse from the retained header button — the existing D21.11 path) | `S26` (the preserved API + `_apply_collapsed_visual`), frozen `set_collapsed`/`toggle_collapsed`/`is_collapsed` | **Phase 1** |
| **`AC-D44.4`** (header strip / `+` (D22.1) / column-header row hidden while collapsed, visible on expand) | `S26` (explicit `hide()`/`show()` of `header_bar` + `table`); AR-D44-7 | **Phase 1** |
| **`AC-D44.5`** (**the core fix** — the collapsed width survives a `resizeEvent` **or** a dock drag) | `S23` (the pure rule), `S24` (both clamp branches + the minimum relaxation + the deferred re-apply); AR-D44-1/2/5 | **Phase 1** |
| **`AC-D44.6`** (palette + hover/pressed via `ui/visual_conventions.py::set_button_active`) | `S25`, `S26`; frozen `set_button_active`/`ACTIVE_PROPERTY`; AR-D44-9 | **Phase 1** |
| **`AC-D44.7`** (collapse state **not** persisted; no `QSettings` key) | `S27`; Data Model; the measurable in the new width guard | **Phase 1** |
| **`AC-D44.8`** (regression guard **RED pre-fix**; the expanded-state width suites green or corrected in lockstep) | `S28`; AR-D44-4; the plan's *Corrected* / *Verified unchanged* / *RED→GREEN* sections | **Phase 1** (the guard + the corrections) + **Phase 2** (the reconciliation + the RED-at-`0c4d478` evidence) |
| **Journey 37** (steps 1–5; postconditions; the edge cases: collapse from the min → restore 150; from the cap → restore the cap; resize/drag while collapsed does not expand; floating dock still clickable; disconnected/empty watchlist; first launch expanded; the `CHART_MIN_WIDTH` invariant in both states) | `S23`–`S28`; Non-Functional (the invariant, the tolerance, the visual); the plan's `AP-D44-3`/`AP-D44-4` | **Phase 1** + **Phase 2** (the edge cases re-checked) |
| **`AC-D21.11.2` / `AC-D21.11.3`** (REVISED — the collapsed appearance) | `S25`, `S26`; § *Supersessions*; AR-D44-4 | **Phase 1** |
| **`AC-D21.11.1`** (unchanged — one "Watchlist" label; the duplicate dock title deleted; the header strip is the title bar **while expanded**) | Frozen *Watchlist dock identity* + `S25` (the single label stays; the bar's painted text is not a label widget); `test_D21_10_T01` verified unchanged | **Phase 1** (non-regression) |
| **`AC-D13.1` / `AC-D17.2`** (REVISED — the 150px minimum is **expanded-state only**) | `S23`; § *Supersessions* | **Phase 1** |
| **`AC-D13.2` / `AC-D13.3` / `AC-D17.1` / `AC-D17.3`–`AC-D17.6`** (cap, persistence, drag enforcement, re-clamp — unchanged for the expanded state) | `S23` (the default `False` keeps the expanded rule), `S24`, `S27`; the *Verified unchanged* suite table | **Phase 1** (non-regression) + **Phase 2** |
| **`AC-D18.*` / D21.13 (right dock)** (unchanged — the cross-clamp with a fixed collapsed left) | `S23` (the collapsed left in the B3 cross-clamp); `[no relationship]` for the right dock's own model | **Phase 1** + **Phase 2** (non-regression) |
| **`AC-D22.1`** (the `+` on the header strip — unchanged **expanded**) | `S26` (hidden while collapsed, restored on expand); AR-D44-7 | **Phase 1** |
| **`AC-D14.*` / `AC-D21.5.*` / `AC-D39.*`** (double-click, columns, search — unchanged) | Frozen *WatchlistPanel data API* / *pure helpers*; the *Verified unchanged* suites | **Phase 2** (non-regression) |
| **`A75`** (the 30px bar width) · **`A76`** (no persistence; starts expanded) · **`A77`** (strip/`+`/column-header hidden while collapsed) · **`A78`** (the mechanism is a Plan-level detail) | `S23` · `S27` · `S26` · `S25` (+ `FI-D44-2`, ruled satisfied) | **Phase 1** |
| **`R66`** (the collapsed width snapped back) · **`R67`** (the collapsed-appearance change regresses D21.11/D13/D17) | AR-D44-1/2/5 · AR-D44-4 + `S28` | **Phase 1** + **Phase 2** |
| **`DG74`** (the clamp fights the collapsed width) | `S23`, `S24` (the resolution DG74 suggests, with the pure model as the owner) | **Phase 1** |
| **`Q54`** (owner confirmation of A75–A77; non-blocking) | A75–A77 are the recorded defaults; no blocking item; an owner override would revise `AC-D44.1`/`.4`/`.7` + `S23`/`S26`/`S27` | — (recorded) |
| **The `## Non-Goals` revision (2026-10-16)** | § *Supersessions* item 3 (permitted **only** for the D44 bar, in the app palette) | **Phase 1** |
| **D42 / D43 / D41 / D40** | `[no relationship]` — not reopened | — |

### Supersessions and non-changes (D44 increment — recorded, never silent)

1. **`AC-D21.11.2` / `AC-D21.11.3`'s collapsed-appearance clause** ("the collapsed state still shows the
   button", with the `VIS-D21.1` diagonal strike on the retained button) → **superseded for the collapsed
   watchlist state**: the collapsed form is the **thin bar with rotated text**, not a struck-through
   horizontal header button. `VIS-D21.1` **still applies** to any genuinely hidden/off **button** state
   elsewhere (D21.12 volume, D21.13 portfolio) and to the header button whenever it is *shown* — it is
   simply not the collapsed-watchlist indicator. **`AC-D21.11.1` is unchanged** (a single "Watchlist"
   label; the duplicate dock title deleted). One **clarification** (not a supersession): the *title-bar
   widget identity* is `panel.header_bar` in the **expanded** state (as today, and as
   `test_D21_10_T01` asserts) and `panel.collapsed_handle` in the **collapsed** state — the swap D44's
   own correction record explicitly authorises ("`setTitleBarWidget` swaps to the bar, or the header
   widget reorients", `A78`).
2. **The 150px minimum of `AC-D13.1` / `AC-D17.2`** → scoped to the **expanded** watchlist only; while
   collapsed the width is `WATCHLIST_COLLAPSED_WIDTH` (~30px). `AC-D13.2`/`AC-D13.3`/`AC-D17.1`/
   `AC-D17.3`–`AC-D17.6` (cap, persistence, drag enforcement, re-clamp) are **unchanged for the expanded
   state**; `AC-D21.11`'s "collapsed-width geometry" edge case is **now specified** by `AC-D44.1`/
   `AC-D44.5`.
3. **The `## Non-Goals` "no restyling" bullet** → **revised by the owner** (D44, dated 2026-10-16) to
   permit **only** the collapsed-bar styling, in the **app palette** (`#141822` / `#232938` /
   `#cbd5e1`) — the mockup's white rounded pill is explicitly **not** the target (the owner's
   clarification). The companion "no net-new feature" Non-Goal is revised the same way (the D44
   exception only).
4. **Explicit non-changes (recorded so they are not read as omissions):** `WATCHLIST_MIN_WIDTH = 150`
   (value), `DEFAULT_WATCHLIST_WIDTH`, the cap fractions, `CHART_MIN_WIDTH` and its cross-module
   invariant, the D21.11 collapse API, the D13/D17 persistence key and re-clamp rules, the
   D14/D21.5/D22/D39 watchlist behaviour, the D18/D21.13/D41 right-dock model, the pyqtgraph rendering
   stack (a **locked** decision), the D42/D43 data paths, and `ui/visual_conventions.py` (consumed,
   never modified).

### Flagged issues and Validator rulings (D44)

The plan surfaced three issues; the Validator **ruled on each** this cycle (recorded in
`docs/plan_notes.md` as `FI-D44-1`–`FI-D44-3`, all `Status: addressed`, `Escalation: none`). **No
`ESCALATED_TO_REQUIREMENTS`**: no requirement is redefined, reinterpreted or left unsatisfied.

- **`FI-D44-1` — exact-equality measurables vs the repo's ±1px tolerance convention → RATIFIED as a
  measurement convention.** `AC-D44.1`/`AC-D44.5` phrase the outcome as exact equality on the dock
  width; the guard asserts exactly that on the **dock** (probe-verified deterministic offscreen:
  `resizeDocks([dock], [30])` → 30) and keeps the `+1` convention only for inner/derived measurements
  the criteria do not name. The requirement's *outcome* ("the bar is 30px and stays 30px") is
  unchanged, so **no Requirements-side clarification is needed**; the 1px dead-band in
  `_apply_dock_widths` is unchanged behaviour, and the guard asserts after the apply path has run.
- **`FI-D44-2` — `A78`'s "the dock's title-bar widget presents the bar" cannot be literal for a
  *full-height* bar → CONFIRMED SATISFIED as an intent, no wording escalation.** Probe-verified (Plan
  and Validator, independently): a title-bar widget is laid out at the top of the dock at its own
  `sizeHint` height, so a full-height bar is impossible in that slot. D44's split affordance — the
  full-height bar as the dock's **content**, a 30×28 handle in the **title-bar slot** — preserves
  everything `A78` fixes: a thin, clickable, app-palette bar that reads as a panel, and a dock that
  stays movable/floatable (DG37). `A78` itself delegates the mechanism ("the widget/title-bar mechanism
  is an implementation choice"), and the requirement's own correction record sanctions the swap. The
  recorded **fallback** (bar-as-title-bar) remains if the handle proves problematic in build.
- **`FI-D44-3` — `A76` is silent on the persisted width when the app closes *while collapsed* →
  CONFIRMED: persist the tracked *expanded* width.** `closeEvent`'s unchanged
  `save_watchlist_width(self._settings, self._watchlist_width, …)` writes the expanded width, because
  `_watchlist_width` is never assigned while collapsed. Persisting the applied 30px would be re-clamped
  to the 150px minimum by `clamp_watchlist_width` on the way out — a silent loss of the user's width.
  A76's own outcome ("no collapse key exists; the app starts expanded") is satisfied either way.

**Handoff:** this increment is validated `Status: APPROVED` (2026-10-16, legacy single-scope D44 cycle
— the only cycle; no `CHANGES_REQUIRED` preceded it); the companion plan is `docs/plan.md`
§ *D44 — Batch 19* (`Status: READY_FOR_TASK_MANAGER`). The Code Reviewer independently re-verifies
(a) the collapsed width surviving a real `resizeEvent` **and** the drag-event path, (b) the palette
matching the app (no white pill), (c) the **expanded** D13/D17/D18/D21.13 criteria and suites being
unaffected, (d) the dock still movable/floatable while collapsed with click-to-expand restoring the
previous width, (e) no collapse key written, and (f) no corrected assertion weakened, skipped or
xfailed. **`ESC-055` stays TASK_MANAGER-owned** and is not absorbed here.

---

## D45 increment — Batch 20: the News Digest dock (+ the `View` menubar), the Trade Context Menu, the **Kill switch** and the **SL/TP dialog** are removed — the app has **zero order interaction** afterwards (validated 2026-10-25, **approved for build**)

> **SUPERSEDED BY D46 / A99 (2026-10-25) — the stop/target *storage* half of this section.** D45 kept the columns
> and the fields ("no migration"); P5 **drops** them with a guarded migration (`S47`). Every sentence below that says
> the storage is kept / unchanged / retained / migration-free is the **D45 record**, not the current end state. The
> trail is **kept (A87) → cleared (ESC-060) → dropped (A99/D46.12)**; the current end state is § *Phase P5*.
>
> **Status of this section.** The canonical D45 architecture. Validated by Plan Artifact Editor &
> Validator (`Status: APPROVED`, 2026-10-25) on a **legacy single-scope run** (no `Phase: P<n>`; the
> unsuffixed proposal pair; no phase gate). Companion plan: `docs/plan.md` § *D45 — Batch 20*;
> module index: `docs/codebase-map.md` (refreshed for this batch). **Approved for build, not yet
> as-built.** **D1–D44 are not reopened** beyond the supersessions recorded at the end of this section.
>
> **Validation history.** Round 1 returned `CHANGES_REQUIRED` on four documentation/test-book findings
> (R1–R4). Round 2 fixed them: R1/R2 changed test-book **wave membership** only (`tests/test_d27_flat_rows.py`
> joins wave 3 with the tracker deletion; the D27.1 AC-3 case's removal moved into wave 2), R3 made the
> residue instrument's claim true (nine panel tokens added, scope stated, `AC-D45.3`'s measurables
> asserted directly), R4 reconciled this section's `tests/test_dock_d18_region.py` row with the plan
> (the loop is **deleted**, not shrunk to three — `RG-D45-1`). **No architectural decision changed**;
> `S29`–`S38` stand as validated **except `S29` (the module is retained) and `S35`'s order half, both superseded
> by P5/D46 on 2026-10-25 — see § *Phase P5*, `S39`/`S40`, and the `SUPERSEDED`/`VOID` markers on `S29`, `S35`,
> `AR-D45-10` and the two frozen rows below.**
>
> **Scope: D45 only** (Batch 20, owner-requested 2026-10-25 **and its later extension the same day**).
> The requirements were **substantively** revised by the extension (kill switch + SL/TP dialog move from
> *retained* to *removed*, `AC-D45.6` inverted, `AC-D45.10` added, A82/A83 reversed) — so the standing
> proposal-staleness flag is **not** benign here (memory 2026-10-23); both proposal documents were
> rewritten, not amended.
>
> **Sources of record** (`docs/requirements/requirements.md`, `Status: READY_FOR_PLAN`, 0 open
> questions): **`### D45`** `:4100`–`:4481` (three removal groups, "Scope — KEEP", six owner-accepted
> consequences, requirements `D45.1`–`D45.6`, `AC-D45.1`–`AC-D45.10` `:4282`–`:4370`, the
> supersession/revision record `:4371`–`:4416`, assumptions A79–A90 `:4417`–`:4560`, correction record
> `:4461`–`:4481`); **Journey 38** `:1086`–`:1119`; **R68–R75** `:4699`–`:4706`; `design_gaps.md`
> **DG75** `:1189`–`:1212`, **DG76** `:1214`–`:1229`, **DG77** `:1231`–`:1260`.
> **Baseline:** `main` @ **`c702be9`** (2026-10-23).
>
> **Escalation state at validation time.** **No `PLAN`-routed escalation is open** —
> `docs/code_review/escalations.json` holds **no `status: "open"` entry at all**; the only `routed_to:
> PLAN` entry ever recorded (`ESC-050`) is `addressed`. `docs/tasks/task_manager_notes.md` carries no
> `ESCALATED_TO_PLAN`. **DG76** is the one open Plan-level question and this section decides it (§ `S29`);
> DG77 is resolved by the named adjustments in `docs/plan.md`.

**The one workstream — subtractive, three groups, one invariant.** D45 removes **all** order
*interaction* from a read-only observation terminal: the news half of D38 (Group A), the whole in-app
close/order path plus the SL/TP setter chain (Group B), and the cancel path (Group C, the owner's later
extension). The invariant that binds them is **reachability, not file count** (`D45.2`, `AC-D45.4`,
`AC-D45.6`): after D45 **no `ui/` module can call `placeOrder`, `cancelOrder` or `reqGlobalCancel`**, and
no `ui/` module imports the three deleted feature modules or the deleted validation module. Two owner
decisions must survive the deletion and are the main risk in the change: the **dividend S0 `"456"`
substrate** (R68 — it shares the `s0_register` mechanism with the news `"292"` line) and the
**stop/target storage** (A87 — the DB columns, model fields and the position upsert are **not** touched;
only the two display columns and every setter go). Nothing is added: no replacement close UI, no
replacement cancel control, no read-only SL/TP fallback, no schema migration. **[SUPERSEDED BY D46 / A99: the
stop/target storage is DROPPED by the P5 guarded migration (§ P5 `S47`); "no schema migration" above is the D45 record.]**

### Relationship to prior increments (D45)

Every decision below carries exactly one relationship label. `[revises …]` names the earlier decision it
changes; an unlabelled decision would be read as new.

| # | Decision | Relationship |
|---|---|---|
| **S29** | **`ibkr/orders.py` is retained, unreferenced by any transmit path, with a module-docstring note.** The `AC-D45.4` measure is **reachability and zero transmits**, not file existence; and the module is **not** in fact orphaned (see § Codebase Summary) — `ui/main_window.py` imports its `orders` singleton as `order_registry` for the **retained, inert inbound observers** (`A90`). Deleting it would force those observers to be rewritten (registry-safe) for **zero** reachability gain and would delete the only unit coverage the builders keep (`tests/test_order_builders.py`). **SUPERSEDED by P5 `S39` (2026-10-25) — the module is DELETED in full, not retained (A91); this row is kept verbatim as the record of the decision that was reversed.** | **`[new in D45]`** — settles DG76 option (a). Supersedes the D41 "Scope — KEEP / retained order machinery" bullet's *intent* (the machinery is no longer retained **for a purpose**) without reversing A80's default. |
| **S30** | **Sever the transmit path at its single call site.** `MainWindow._close_position_by_id` is the **only** `placeOrder` call site in the tree; it goes with `_on_portfolio_close_position`, `_on_portfolio_close_group`, `_on_portfolio_flatten_all`, `_ref_price_for` and the `validate_order` import, and `ibkr/validation.py` is deleted. `placeOrder` itself is **ibapi's inherited `EClient.placeOrder`** — it is not defined in this repo at all, so "removing the transmit" means *removing every written caller*, never editing `ibkr/client.py`. | **`[revises D41: the retained close/flatten order path]`** — D41 kept this path (`validate_order` gate, order-path pacing token, `ref_price`, the D28.6 contract rebuild) for Portfolio closes; D45 deletes it whole. `ref_price`/`_ref_price_for` become source-less and go (`AC-D41.4`'s `ref_price` clause is **moot**). |
| **S31** | **Delete the cancel capability completely, and add none back.** `kill_btn` (+ the `QLabel("|")` separator before it), `_on_kill_switch_clicked`, `_kill_switch` (the `reqGlobalCancel()` call, the per-ID `cancelOrder()` loop, the pre/post status-bar counts and the local `order_registry.update_status(…, "Cancelled")` marking) are deleted. `reqGlobalCancel`/`cancelOrder` then have **no call site anywhere in the app**, and **no** teardown / `closeEvent` / disconnect / reconnect path may acquire one. Cancel surface after D45 = **TWS**. | **`[revises D26.8: the kill switch / AC-D26.8]`** — superseded in full (A88). Reverses A82 (recorded as a reversal, not silently dropped). |
| **S32** | **Delete the SL/TP setter chain end-to-end.** The dialog module, its `confirmed` signal, the panel's `position_sltp_changed`/`group_sltp_changed`, `_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`, and `MainWindow._on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed` (with their `UPDATE positions SET stop_loss=…` / `UPDATE trade_groups SET stop_loss=…` statements) are deleted. **No** read-only fallback dialog (the owner declined replacement UI twice). | **`[revises D26.3: the SL/TP dialog]`** — `AC-D26.3`'s labelling branch has no dialog, so it is **moot** (A89). Reverses A83. |
| **S33** | **Portfolio becomes a view-only 8-column render.** `Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`; the `Stop`/`Target` header, value and alignment slots go; the right-aligned index set becomes `(1, 2, 4, 5)`; the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording is corrected. Storage is **untouched**: the `positions`/`trade_groups` `stop_loss`/`take_profit` columns, the `Position`/`TradeGroup` fields and the `_upsert_position` round-trip stay; **no migration, no destructive schema change**; legacy values are not settable and not displayed — and **not preserved**: `_on_position_update` builds `Position(stop_loss=None, take_profit=None)` and the upsert's `DO UPDATE` writes both columns, so a live update clears them (ESC-060). | **`[revises D41: the Portfolio section's close/flatten/SL-TP controls]`** — `AC-D41.1`'s Portfolio clause becomes "renders view-only"; the D18 width model (`AC-D18.6`, `RIGHT_DOCK_MIN_WIDTH = 200`) is **re-derived, not superseded** — the table only demands *less* width. Storage retention is `[extends D27: position/trade-group SL/TP persistence]` unchanged. **SUPERSEDED BY D46 / A99: the columns and the fields are DROPPED (§ P5 `S47`).** |
| **S34** | **Remove the digest half of D38 and nothing more.** Delete `ui/news_digest_dock`, `ibkr/news`, the `View` menubar (`menuBar()`/`view_menu`/`_on_news_digest_visibility`/`self.news_digest_dock`/the `Ctrl+Shift+N` action), the `NewsManager` use, the `b.tick_news` connection and `_on_s0_tick_news`, and the digest-only session plumbing: the news `"292"` S0 registration, `on_s0_tick_news`, `add_news_push_listener` / `remove_news_push_listener`, and the digest-only `set_s0_headless` / `_s0_headless` flag **including the two `or self._s0_headless` clauses in the S0 line-build paths**. **No menubar replaces the `View` menu** (A86). The dividend substrate (`"456"`, tick 59, `_dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, the marker overlay, the yfinance provider) is **untouched**. | **`[revises D38: the news digest]`** — `AC-D38.2`/`AC-D38.3` **superseded**, `AC-D38.6` revised to the surviving half (A79). `[extends D38]` for the dividend half, which stays byte-for-byte. A86's "no menubar" is new and follows from the section (the app returns to no menubar). |
| **S35** | **Keep the broker-boundary plumbing inert rather than deleting it.** In `ui/main_window.py` the inbound observers (`_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`) and the `order_registry` import stay wired; the registry is never populated by the app any more, so they observe and surface TWS state only. In `ibkr/bridge.py` / `ibkr/client.py` the news signals (`tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article`) and the ibapi callback overrides stay as API-boundary mirrors — they are now **unconnected** (`NewsManager`, their only consumer, is gone). The fail-fast port check, the connection badge and the global no-test-transmits rule are retained. **P5 `S40` reverses the ORDER half of this decision (A92, 2026-10-25): the observers and the `order_registry` import are deleted, not kept inert; the news half and the retained port check/badge/no-test-transmits rule stand untouched.** | **`[extends D26: the connection/error path]`** — `AC-D26.5` (badge + port check) is unchanged and depends on this path; `[extends D38: the ibapi news boundary]` retained unconnected. A90 records the inertness so it is not mistaken for a leftover (R74). |
| **S36** | **The acceptance instrument is a source-scan invariant plus a mocked-client walkthrough, not a convention.** A new `tests/test_d45_removal` asserts: deleted modules are unresolvable and deleted files absent; the removed tokens listed in the plan's residue-verification step appear nowhere in the scanned tree — the **AST** pass reads identifiers **and** string constants over `ui/ services/ data/ ibkr/ config/` (comments are invisible to it, which is why `config/settings.py`'s `validate_order()` *comment* is out of scope in a file no task may edit), and a **`ui/`-only grep** is the prose net — both under an explicit survivor allow-list; `tests/` is covered by neither, so `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in the module; `ibkr/validation` and `ibkr/news` do not exist; and driving a real offscreen `MainWindow` through every remaining affordance issues **zero** `placeOrder`, **zero** `cancelOrder`, **zero** `reqGlobalCancel`. It replaces the **intent** of the five deleted suites (`AC-D45.4`, R70) with a static + behavioural invariant and must be **proven discriminating** against the pre-D45 tree. | **`[new in D45]`** — the mechanism exists (`tests/test_d41_removal.py` is its precedent: AST token scan + allow-list + real offscreen window); the D45 variant is new. Supersedes the *coverage claim* of the deleted order-safety suites (consequence 5 of D45 states the loss plainly). |
| **S37** | **Ordering is forced by three shared files, not chosen for taste.** `ui/main_window.py` is touched by three groups (A, B-main, C) and `ui/active_portfolio_panel.py` by one (B-panel); `tests/test_dock_d18_region.py` and `tests/test_d27_position_id.py` by two each (A `:147` / B `:174`–`:179`; B-main's AC-3 case / B-panel's `8`/`9` index edit). Therefore: **one task per wave on `ui/main_window.py`** (waves 1, 2, 4), **Group B's window half lands before its panel half** (panel-first would leave `MainWindow.__init__` connecting signals that no longer exist → `AttributeError` in every window test, i.e. a wave that cannot pass its own tests), and **both owner-facing docs go in one terminal task** (wave 5, `USAGE.txt` + `usage.md`) instead of three conflicting edits — the map is Plan-owned and already refreshed, so it is not a Build task. The **wave-membership rule** completes the constraint: an assertion whose subject dies in wave *N* is removed or adjusted **in wave *N***. | **`[new in D45]`** — the sequencing constraint, recorded in `docs/plan.md` § *D45 sequencing constraints* (rules 1–4). (The `ESC-055` rule — enumerate assertions invalidated **outside** the edited files — is applied, not restated.) |
| **S38** | **Docs are one batch-scoped step, and the map's skeleton is not hand-edited.** `USAGE.txt`, `usage.md` are cleaned in one task with the three owner-named items removed (`A85`); `docs/codebase-map.md` is refreshed by Plan (this batch) — the generated skeleton is rebuilt from the tree by `update_codebase_map.py`, so it keeps listing the deleted files until the **next** refresh, and the annotation tables describe the **post-D45 target state** (stated in the map's header). | **`[new in D45]`** — `AC-D45.7` makes doc freshness checkable; A85 scopes the files. `[extends the per-batch map convention: memory 2026-10-23 item 5]`. |

---

### Codebase Summary (existing repository — the D45 surface, source-validated 2026-10-25 @ `c702be9`) (D45)

**This is the pointer to `docs/codebase-map.md`, not a second inventory.** The map carries the module
index, the status legend and the test-impact rows; this section records only what D45's decisions rest
on, and every fact below was re-derived from source (graphify `graph.json` (4,947 nodes) used for
discovery; **the source is authoritative** where they disagree).

#### Facts D45's decisions rest on

| Fact | Verified evidence | Consequence |
|---|---|---|
| `placeOrder` has **exactly one** production call site | `ui/main_window.py:3476` inside `_close_position_by_id`; **no `placeOrder` definition exists in `ibkr/`** — it is ibapi's inherited `EClient.placeOrder` (`ibkr/client.py:39 class IBApiClient(EWrapper, EClient)`) | `S30`: deleting that one method makes `placeOrder` uncalled tree-wide. The map's earlier "`IBApiClient.placeOrder` (the only transmit)" was **wrong** and is corrected this batch. |
| `reqGlobalCancel`/`cancelOrder` have **exactly one** call site pair | `ui/main_window.py:3042`, `:3048`, inside `_kill_switch`; no `ibkr/` wrapper; no `closeEvent`/disconnect caller (`closeEvent` teardown order re-read) | `S31`: the cancel capability is removed outright; nothing needs re-homing. |
| `_kill_switch` has exactly **two** callers | the toolbar button (`:3061`) and `_on_portfolio_flatten_all` (`:3385`, deleted by `S30`) | Both callers go inside one batch; neither survives. |
| `_ref_price_for` has **exactly one** caller | definition `:2154`; caller `:3435` (inside `_close_position_by_id`); the `_symbol_last_prices` map it reads **stays** (the Portfolio P/L path reads it directly at `:3207`) | `S30`: delete the accessor, keep the map. R74 names a leftover `_ref_price_for` as residue — this is the removal that prevents it. |
| The SL/TP dialog's **only** entry point is the context menu | `ui/active_portfolio_panel.py:156 self._context_menu.set_sltp_action.triggered.connect(self._on_set_sltp)`; `_on_set_sltp` is the only constructor call of `StopLossTargetDialog` | A89: Groups B and the extension agree — the setter was already unreachable once the menu went; the extension completes the removal. |
| `order_registry` is **not** orphaned by the removal | `ui/main_window.py:36` imports it; consumers: `_update_order_status` (`:3335`), `_on_order_error` (`:1598`), and `_close_position_by_id` (`:3400`, deleted) | `S29`/`S35`: keep the module; the registry stays read/written by the **inert** observers, so it is neither unreferenced code nor a transmit path **[REVERSED BY D46/P5 `S39`: the module and every consumer are deleted — the registry was never populated, so nothing read or wrote it in production]**. |
| `ibkr/orders.py` keeps **real** unit coverage | `tests/test_order_builders.py` covers `market_order`/`limit_order`/`stop_order`/`bracket_order` (structure, OCA groups, `transmit` flags) and the registry (`register`/`get`/`update_status`/`clear_filled`/`all`) | DG77's "left with **no tests at all**" is **wrong for this module**; what the five deleted suites took was the *integration* driver (`_kill_switch` reading the registry, `_close_position_by_id` transmitting), not the builders' unit coverage. Recorded so it is not "discovered" later. **[SUPERSEDED BY D46/P5 `S39`: `tests/test_order_builders.py` and the module are deleted; that unit coverage goes with them, which is the cost the owner accepted]** |
| `tests/test_d41_removal.py` stays green after `ibkr/news` is deleted | its only news reference is `_ALLOWED_ANYWHERE` = `{"footprint_cache_key", "queue_depth"}` (a frozenset **string**, `:105`); its token scan reads `ui/ services/ data/ ibkr/ config/` only and `queue_depth` lives in the allow-list, so no assertion reads `NewsManager` behaviour; its request-absence case still issues its S0/RT lines because `"456"` survives | `AC-D45.8`: **keep unchanged** (verified, not assumed). |
| `tests/test_stop_loss_target.py` survives on its own merits | 3 cases, imports only `data.models.Position`/`TradeGroup`, asserts the four model fields (defaults + explicit values) and no UI | A87: the fields stay → the file stays **unchanged** and still means something. **SUPERSEDED BY D46 / A99: the suite is DELETED (§ P5 wave 7).** |
| The digest test block is contiguous and separable | `tests/test_d38_events_news.py`: NewsManager block `:145`–`:201`; digest block `:419`–`:549` (`_StubNewsManager`, `_StubHost`, `_make_dock`, `test_ac_d38_2_digest_groups_headlines`, `test_ac_d38_3_no_entitlement_state`, `test_ac_d38_2_click_fetches_article`); surviving blocks `:83`–`:143` (tick 59), `:202`–`:417` (yfinance, markers, AC-D38.5), `:551`–`:593` (no-mock-endpoint, md-line guard) | Group A trims by symbol: two whole sections go, the file stays. The md-line guard docstring's `"292"` reference is the "one docstring" the correction record names. |
| The 8-column shift invalidates **exactly two** external files | `tests/test_d27_position_id.py:164-165` and `tests/test_d27_position_prices.py:290-291` address Strategy/Group as `8`/`9`; a scan of `tests/` for `positions_table` shows no other column-index assertion (`test_d27_account_subs.py:102` uses column `0`; the D18 width suites iterate `range(table.columnCount())` and are index-agnostic) | R75/DG77: `6`/`7`, named in the plan's test book. No third file needs touching. |
| `_s0_headless` is digest-only but is read in **two** S0 line-build paths | set only by `ui/news_digest_dock.py:209/:221`; read at `ui/ticker_session.py:437` and `:483` (`want = self._s0_union_str() if (self.view_count > 0 or self._s0_headless) else ""`) | `S34`: deleting the flag is a **three-site** edit, not one — the residue risk a worker would miss. |
| The selection tracker's readers all die with the menu | `ui/active_portfolio_panel.py` — `_selected_position` is read only by `_show_context_menu` (:372), `_on_set_sltp` (:377–379), `_on_close_position` (:400–401), `_on_close_group` (:405–406) and `_on_ungroup` (:410–411); `_on_selection_changed` (:352–368) only assigns it and calls `self._context_menu.set_actions_enabled(...)`; `_selected_row` has no reader at all; the **only** reader outside the panel is `tests/test_d27_flat_rows.py:110`–`:111` | `S33`/`AP-D45-4`: the tracker goes with the menu; the one test reader is adjusted in the **same wave** (R1), so it does not outlive its last reader |

#### Data models / persisted state `[existing]`

- **`positions`** — `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier,
  expiry, strike, right, stop_loss, take_profit, trade_group_id, updated_at` (`data/db.py:117`–`:124`).
  **Unchanged by D45** (A87) — no DDL edit, no migration. **SUPERSEDED BY D46 / A99: both columns are DROPPED by the
  P5 guarded migration (§ P5 `S47`); a row that never updates again keeps its legacy bytes and loses them there.**
- **`trade_groups`** — `id, name, strategy_type, underlying, stop_loss, take_profit, collapsed, created_at`
  (`data/db.py:127`–`:134`). **Unchanged** — **SUPERSEDED BY D46 / A99: both columns DROPPED (§ P5 `S47`).**
- **`data/models.py`** — `Position.stop_loss/take_profit: Optional[float] = None`, `TradeGroup.stop_loss/
  take_profit: Optional[float] = None`. **Unchanged** — **SUPERSEDED BY D46 / A99: both dataclasses' fields DROPPED (§ P5 `S47`).**
- **Not persisted:** dock layout / toolbar state are `QSettings`-free for the right region (A36) and the
  digest dock relies on Qt's restored dock state — a saved state naming a removed dock must be **ignored**
  (Journey 38 edge case), which Qt does when the objectName no longer exists. **No new key, no migration.**

#### Major components and responsibilities (post-D45 target; deltas in the next tables)

`ui/main_window.py` (window, docks, toolbar, load path, sessions, teardown) · `ui/ticker_session.py`
(per-symbol session: bars, waves, pacing, live bars, S0 generic-tick substrate) · `ui/active_portfolio_panel.py`
(the right dock's Portfolio panel, **view-only**) · `ui/chart_panel.py` + `ui/candlestick_item.py` +
`ui/overlays/*` + `ui/event_marker_overlay.py` (render stack, **untouched**) · `ui/watchlist_panel.py` +
`ui/dock_layout.py` (**untouched**) · `services/*` (calendar, backfill, collapse, alarms, search, drawings,
studies, md-line guard — **untouched**) · `data/*` (SQLite, cache, aggregator, stores, event provider —
**untouched**) · `ibkr/*` (client wrapper, bridge, market data, RT bars, pacing, id managers, subscriptions,
stream health, account, contracts, **orders (DELETED by D46/P5 `S39`)**, **news (deleted)**,
**validation (deleted)**).

#### Key entry points / data flow (unchanged shape)

`main.py` → `MainWindow()` → `IBApiClient.connect` (fail-fast port check) → bridge signals → sessions/chart;
account-summary + position callbacks → `_upsert_position` → `ActivePortfolioPanel.set_positions/add_position` →
`_group_and_render` → `_render_table`. **D45 removes three inbound UI paths that branched off this flow** —
the digest dock (news callbacks), the Portfolio context menu/close handlers, and the toolbar kill switch — and
changes nothing on the retained path.

#### External integrations already in use `[existing]`

IBKR TWS via the official `ibapi` (`10.51.1`): historical + realtime bars, market data with S0 generic ticks,
account summary/positions, news API + tick `"292"` (**removed**), dividends tick `"456"`/59 (**retained**),
order transmit (`placeOrder`, inherited `EClient`) + cancel (`cancelOrder`, `reqGlobalCancel`) — **no longer
reachable**; yfinance as the sole approved secondary event source (**retained**); SQLite (**retained**).

#### What D45 changes, in one line

Five modules deleted (`ui/news_digest_dock`, `ibkr/news`, `ui/trade_context_menu`,
`ui/stop_loss_target_dialog`, `ibkr/validation`); **three** production modules edited (`ui/main_window.py`,
`ui/ticker_session.py`, `ui/active_portfolio_panel.py`); five test files deleted and **seven** adjusted; two
docs cleaned; **no file added** to production (one new test module, `S36`).

---

### Summary (D45)

D45 is a **subtractive** increment whose requirement is **unreachability**: after it, no UI path in
NDThinkChart can place, cancel or close an order, and no UI path can set a stop/target — the app observes
TWS and renders. The architecture therefore does not add a component or a seam; it **severs three inbound
UI branches at their single call sites** (`_close_position_by_id` for the transmit; `_kill_switch` for the
cancel; the panel's SL/TP chain for the setter), deletes the four feature modules plus the now-unused
validation module, and leaves the broker boundary, the dividend substrate, and the stop/target storage
untouched and inert. The guarantee is then **structural, not conventional**: a static source-scan
invariant plus a mocked-client zero-transmit walkthrough, both proven discriminating against the pre-D45
tree.

### Tech Stack Decisions (D45)

**Constrained choices first** — these are the existing stack; D45 changes none of them (no requirement
asks for a stack change, and the pyqtgraph decision is **locked**, `docs/memory.md` 2026-10-16).

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| UI toolkit `[existing]` | **PyQt6** (widgets, signals, docks, QSettings) | Entire app is PyQt6; D45 only deletes widgets | — (no change proposed) |
| Chart renderer `[existing]` | **pyqtgraph**, locked | Locked decision (2026-10-16); D45 does not touch the render stack | `QWebEngineView` + Lightweight Charts — **declined by the owner**, do not re-propose |
| Broker client `[existing]` | official **`ibapi`** (`10.51.1.post1`) via `IBApiClient(EWrapper, EClient)` | Order/cancel methods are **inherited** from `EClient`; removing callers needs no client edit | Writing an in-repo transmit wrapper — rejected: adds surface for a path that must not exist |
| Persistence `[existing]` | **SQLite** (`data/db.py`), additive migrations only | A87 keeps the SL/TP columns → **no migration at all** in this batch | Dropping the two column pairs (rejected by the owner: destructive, zero user-visible gain) |
| Secondary data source `[existing]` | **yfinance** (`data/events/`) | The sole approved secondary event source; D45 does not touch the event path (`AC-D38.4`/`.5` stand) | — (no change proposed) |
| Removal mechanism `[new in D45]` | **Delete** the modules + **sever** the three call sites; keep the broker boundary inert | `AC-D45.4`/`.6` measure absence + zero calls; deletion is what makes a future re-wire impossible by accident | Keep modules + runtime guards (rejected: reachability by convention; a stray `.connect` would resurrect the path unnoticed) |
| Verification mechanism `[new in D45]` | **AST/token source scan** (`ui/ services/ data/ ibkr/ config/`) + `ui/`-only grep + **mocked-client offscreen walkthrough** in one new test module | Precedent exists and works (`tests/test_d41_removal.py`); no new dependency; catches string-constant leftovers, not just live lookups | Grep-only in CI (rejected: prose false positives, no behavioural half); mypy/type-level «unreachable» (rejected: new dependency, and `placeOrder` is inherited/duck-typed) |
| `ibkr/orders.py` `[new in D45]` | **Retain**, add a module-docstring note that it is unreachable after D45; keep `tests/test_order_builders.py` | DG76(a) + A80/A90: the registry is *used* by the retained observers; deleting it forces registry-safe rewrites of the error path for zero reachability gain | Delete it (DG76(b)) — rejected: outside the owner's named inventory, breaks `A90`'s retained observers, and discards real unit coverage. **[REVERSED BY D46/P5 `S39`, 2026-10-25: the owner named it in scope — module, `tests/test_order_builders.py` and `data.models.UserOrder` are all deleted; the observers were never fed, so nothing depended on the registry]** |
| Test runner `[existing]` | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` | Repo convention (the `pytest` entry point has a stale shebang) | — |
| New dependencies `[new in D45]` | **None** | Constraint; nothing in D45 needs one | — |

### System Components (D45)

Status is relative to the codebase (`[existing]` = present and **unmodified** by this batch;
`[new/changed]` = present and modified).

**Changed by this batch**

| Component | Status | What changes |
|---|---|---|
| `ui/main_window.py` | **`[new/changed]`** | **Group A:** the digest dock block (`:479`–`:493`), `_on_news_digest_visibility` (`:2757`–`:2763`), the `NewsManager` construction (`:529`–`:530`), `b.tick_news.connect` (`:628`), `_on_s0_tick_news` (`:1968`–`:1976`). **Group B:** the two SL/TP + three close `.connect` lines (`:647`–`:651`), `_on_portfolio_close_position` / `_on_portfolio_close_group` / `_on_portfolio_flatten_all` / `_on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed`, `_close_position_by_id`, `_ref_price_for`, the `validate_order` import, and the `order_limiter` (and now-unused `pacing_manager`, `UserOrder`) import names — `PacingExceeded` and `orders as order_registry` stay. **Group C:** `kill_btn` + its `QLabel("|")` separator + tooltip/style/connect (`:319`–`:330`), `_kill_switch` (`:3028`–`:3057`), `_on_kill_switch_clicked` (`:3059`–`:3061`). **Retained in the same file (A90):** `order_registry`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `_symbol_last_prices`, the fail-fast connect path, the badges, `closeEvent` teardown. **[SUPERSEDED BY D46/P5 `S40`: `order_registry`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error` and `_update_order_status` are deleted — `_symbol_last_prices`, the connect path, the badges and `closeEvent` stand]** |
| `ui/ticker_session.py` | **`[new/changed]`** | The news `"292"` register line + its comments, `on_s0_tick_news`, `add_news_push_listener`, `remove_news_push_listener`, `set_s0_headless`, `_s0_headless` (`:175`) **and the two `or self._s0_headless` clauses** (`:437`, `:483`). **Retained verbatim:** `_needs["dividends"] = {"456"}` (`:232`), `on_s0_tick_string` tick-59 branch, `_dividend_info`, `dividend_updated`, `dividend_info()`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`, the S0 union/resync/cancel machinery. |
| `ui/active_portfolio_panel.py` | **`[new/changed]`** | The `TradeContextMenu` + `StopLossTargetDialog` imports and members, the `CustomContextMenu` policy and its connection, `_show_context_menu`, `_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`, the five signals, the now-dead selection tracking (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection and the two stale comments that name it), and the `Stop`/`Target` columns (**10 → 8**; values list and alignment set `(1,2,4,5)`; the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording). **Retained:** `summary_label`/`_on_header_toggled`/`is_collapsed`/`set_collapsed`/`toggle_collapsed`, `set_account_summary`/`set_account_id`/`set_account_unavailable`, `set_positions`/`add_position`, `refresh`/`_render_summary`/`_group_and_render`, `account_summary_changed`, `positions_changed`, `_unrealized_pnl`. |
| `tests/test_d38_events_news.py` | **`[new/changed]`** | Two sections removed (NewsManager `:145`–`:201`, digest `:419`–`:549`); module docstring trimmed; the md-line-guard docstring's `"292"` reference corrected to the surviving `"456"` line. **Event-marker/dividend blocks kept byte-for-byte** (R68's regression guard). |
| `tests/test_dock_d18_region.py` | **`[new/changed]`** | `:147` drops the `objectName() != "NewsDigest"` filter (Group A); `:174`–`:179` **deletes the five-signal receiver loop outright** (Group B-main). All five signals go, so **no signal survives** — the loop is removed, not narrowed; the surrounding assertions stay (the panel is still the dock's widget, `account_summary_changed` / `positions_changed` are still present, and the `positions_changed` zero-receiver probe still proves the probe is not vacuous), and the wiring comment is restated as the post-D45 truth. This is a **deviation from the register's suggested "three-signal loop"** (`requirements.md:4178`–`:4179`, `DG77` item 4) — recorded in `docs/plan_notes.md` `RG-D45-1` and in the plan's § Exactness note; the deviation **does not weaken `AC-D45.8`**, which requires the file to be *adjusted*. |
| `tests/test_d27_position_id.py` | **`[new/changed]`** | `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row` removed **in wave 2** — its passing path is the window's `position_sltp_changed` connection, removed there (the panel setter it also drives goes in wave 3, so the case cannot outlive either half); `:164`–`:165` `8`/`9` → `6`/`7` **in wave 3** (the columns shift there). **Kept:** the AC1 live-update case and the AC2 bulk-id case (the D27.1 id-correctness property survives there). |
| `tests/test_d27_flat_rows.py` | **`[new/changed]`** | The AC-3 tail only: `:108`–`:111` (the `selectRow` drive plus the two `panel._selected_position` assertions) go with the deleted selection tracker; `:104`–`:106` (**the index-alignment assertions — the property AC3 exists for**) stay verbatim, and the AC3 docstring sentence is restated without naming the removed members. AC1/AC2 untouched. `S37`'s wave-membership rule puts this edit in **wave 3**, the wave that deletes the tracker. |
| `tests/test_d27_position_prices.py` | **`[new/changed]`** | `:290`–`:291` Strategy/Group `8`/`9` → `6`/`7`. Nothing else. |
| `tests/test_order_rejections.py` | **`[new/changed]`** | `test_close_blocked_while_disconnected` deleted (its subject, `_close_position_by_id`, is gone — `AC-D26.9`'s disconnected branch has no order path left to block); the `_fresh_registry`/`_register` helpers and the `_on_order_error`/`classify_error` cases **stay** (they cover the retained observer path, A90). **[SUPERSEDED BY D46/P5 `S40`: the `_fresh_registry`/`_register` helpers and the `_on_order_error` cases are deleted with the observer path; the `classify_error` cases stay (three of five survive)**] |
| `tests/test_d28_pacing.py` | **`[new/changed]`** | `test_close_position_defers_when_limiter_empty` deleted whole (it drives `_close_position_by_id` and pins the gate-before-pacing order). The historical-pacing cases **stay** — they are D28.3, unrelated to the order bucket. |
| `tests/test_d45_removal` (new) | **`[new]`** | The `S36` instrument — the one file this batch adds. |
| `USAGE.txt`, `usage.md` | **`[new/changed]`** (**docs**) | The digest/`View` section, the close/close-group/close-all text, the kill-switch bullet, the SL/TP bullet, the "orders cannot be placed while disconnected" claim; `usage.md`'s `### Portfolio & SL/TP` heading/steps and its Portfolio table row; a Database-section note that the SL/TP **columns** are kept but are no longer settable and their values are cleared by the next position update (ESC-060). Must state plainly that **closes and cancels happen in TWS**. |
| `docs/codebase-map.md` | **`[new/changed]`** (**Plan-owned**) | Refreshed this batch: the three removed modules and `ibkr/validation` no longer listed as live; `_kill_switch`/`StopLossTargetDialog` no longer named as retained; the `placeOrder` ownership error corrected; the D45 test book (5 deleted / **7** adjusted / 1 added) updated. |

**Deleted by this batch (nothing replaces them)**

| Module | Status | Reason |
|---|---|---|
| `ui/news_digest_dock` (`NewsDigestDock`) | **deleted** | `S34`/`AC-D45.1`; owner: its only consumer is the digest |
| `ibkr/news` (`NewsManager`) | **deleted** | `S34`/A79; only consumer was the dock + its tests |
| `ui/trade_context_menu` (`TradeContextMenu`) | **deleted** | `S30`/`AC-D45.3`; the only close/group/flatten/SL-TP entry point |
| `ui/stop_loss_target_dialog` (`StopLossTargetDialog`) | **deleted** | `S32`/A89; local-only setter, unreachable after the menu goes |
| `ibkr/validation` (`validate_order`) | **deleted** | `S30`; gates an order nothing builds (`AC-D26.7` moot) |
| `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py`, `tests/test_kill_switch.py`, `tests/test_sltp_honesty.py` | **deleted** | Their subjects no longer exist (A81/`AC-D45.8`, five named whole-file deletions) |

**Retained and deliberately inert (not leftovers — A90)**

- `ibkr/orders.py` — builders + `Orders` registry + the `orders` singleton; **no transmit caller**, still the
  registry the observers read (`S29`). One permitted edit: a module-docstring note. **[SUPERSEDED BY D46/P5 `S39` — the module is deleted; the registry import and every observer that read it go with it]**
- `MainWindow._on_open_order` / `_on_order_status` / `_on_exec_details` / `_on_order_error` /
  `_update_order_status` + the `order_registry` import — observe TWS, place/cancel nothing, registry never
  populated by the app. **[SUPERSEDED BY D46/P5 `S39` — deleted]**
- `ibkr/bridge.py` news signals + `ibkr/client.py`'s `tickNews`/`newsProviders`/`historicalNews`/
  `historicalNewsEnd`/`newsArticle` overrides — the ibapi boundary mirrors; unconnected, harmless (`S35`).
- `config/settings.py::MAX_ORDER_NOTIONAL` — see *Incidentally affected* in the plan; **not** deleted. **[SUPERSEDED BY D46/P5 `S46` — deleted in wave 4]**
- `ibkr/pacing.py::order_limiter` — the order-path token bucket; no consumer after D45, but `pacing.py` is a
  shared, tested module — **not** edited by this batch. **[SUPERSEDED BY D46/P5 `S46` — `OrderRateLimiter`/`order_limiter` deleted in wave 4; `pacing.py`'s remaining shared substrate stays]**

### Data Model (D45)

No schema change, no migration, no destructive schema change (A87/`D45.6`). The retained `stop_loss`/`take_profit` values are **not** preserved, though: a live position update writes both columns empty (ESC-060). Every entity below is `[existing]`. **SUPERSEDED BY D46 / A99:** the `stop_loss`/`take_profit` columns and fields are
**DROPPED** by one guarded destructive migration (§ P5 `S47`); a row that never receives another live update keeps its
legacy bytes and loses them here — the batch's only byte-destroying step.

| Entity | Status | Key fields | D45 effect |
|---|---|---|---|
| `positions` (SQLite) | `[existing]` | `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier, expiry, strike, right, stop_loss, take_profit, trade_group_id, updated_at` | **none** — `stop_loss`/`take_profit` stay, written by the unchanged upsert. **P5: both columns DROPPED (§ P5 `S47`); the upsert writes 13 columns.** |
| `trade_groups` (SQLite) | `[existing]` | `id, name, strategy_type, underlying, stop_loss, take_profit, collapsed, created_at` | **none** — the `UPDATE trade_groups SET stop_loss=…` statement is deleted, the columns are not. **P5: both columns DROPPED (§ P5 `S47`).** |
| `data.models.Position` | `[existing]` | `symbol, qty, avg_cost, contract_type, con_id, account, local_symbol, multiplier, expiry, strike, right, stop_loss, take_profit, trade_group_id, id` | **none** — `stop_loss`/`take_profit` retained (A87); `tests/test_stop_loss_target.py` keeps asserting them. **P5: the two fields DELETED and that suite DELETED (§ P5 wave 7).** |
| `data.models.TradeGroup` | `[existing]` | `name, strategy_type, underlying, id, stop_loss, take_profit, collapsed, created_at` | **none**. **P5: both columns DROPPED (§ P5 `S47`).** |
| `MainWindow._upsert_position` (`:3283`) | `[existing]` | `INSERT INTO positions (… stop_loss, take_profit …) … ON CONFLICT(symbol, con_id) DO UPDATE SET … stop_loss=excluded.stop_loss, take_profit=excluded.take_profit … RETURNING id` | **none** — the upsert still writes both fields; because `_on_position_update` passes `stop_loss=None, take_profit=None`, the `DO UPDATE` **clears** them on every live update (ESC-060). *(The requirements call this `_persist_position`; the tree names it `_upsert_position` — a naming drift only, recorded in the plan.)* **P5: 13 columns, both names removed (§ P5 `S47`); a row that never updates keeps its legacy bytes and loses them there.** |
| `MainWindow._on_position_end` bulk load (`:3250`–`:3282`) | `[existing]` | SELECTs the 15 columns incl. `stop_loss`/`take_profit`, builds `Position(...)` with `id` | **none** — the bulk load still SELECTs and carries them, but they are only as good as the last write: the live update path clears both columns (ESC-060). They are simply not displayed. **P5: 13 columns, read by name so the shift cannot reoccur (§ P5 `S48`).** |
| **Positions table view model** | `[new/changed]` (**view only — no storage**) | 8 columns, in order: `0 Symbol`, `1 Qty`, `2 Avg Price`, `3 Type`, `4 Multiplier`, `5 P/L`, `6 Strategy`, `7 Group`; right-aligned set `(1, 2, 4, 5)` | `S33`: the `Stop`(6)/`Target`(7) slots go; `Strategy`/`Group` move `8/9 → 6/7` (`AC-D45.10`). This is a render mapping, **not** a persisted entity |

Relationships: `positions.trade_group_id → trade_groups.id` (FK, unchanged); `position_group_map` unchanged;
strategy/group cell derivation (`services.strategy_detection.detect_and_group`) unchanged.

### Integration Points (D45)

| Integration | Status | Why it is needed / what changes |
|---|---|---|
| **IBKR TWS** — historical + realtime bars, market data, account summary/positions (`ibapi` over the local socket, `7496` live / fail-fast port check) | `[existing]` | The app's whole data plane; **unchanged**. `AC-D26.5`'s port check + badge retained. |
| **IBKR S0 generic tick `"456"`** (+ tick 59 string) → `_dividend_info` → `dividend_updated` → dividend marker | `[existing]` | Retained **verbatim** (`S34`, R68, `AC-D45.2`): it is the only live dividend source for the chart's event markers. |
| **IBKR S0 generic tick `"292"`** (live news push) | **removed** | `AC-D45.1`/`.2`: never requested; the digest that consumed it is gone. **The `s0_register` mechanism stays** — only the news need disappears. |
| **IBKR news API** (`reqNewsProviders`, `reqHistoricalNews`, `reqNewsArticle`) + the bridge's news signals | `[existing]` (inert) | The client/bridge overrides stay (`S35`) — deleting them would touch the connection-callback file for no reachability gain; nothing constructs `NewsManager` any more, so they are never requested. |
| **IBKR order transmit** (`EClient.placeOrder`, inherited) / **cancel** (`cancelOrder`, `reqGlobalCancel`) | `[existing]`, **unreachable** | `S30`/`S31`: zero call sites in the tree after D45. `ibapi` still exposes the methods (deleting them is impossible/unwise); the **app never calls them** — proven by `S36`. |
| **IBKR inbound order/execution callbacks** (`openOrder`, `orderStatus`, `execDetails`, `error`) | `[existing]` (inert) | Retained observers (A90): they surface TWS state and order errors on the status bar; registry never populated by the app. **[SUPERSEDED BY D46/P5 `S40`: the three overrides and their observers are deleted; only `IBApiClient.error` remains, surfacing per-code messages on the status bar]** |
| **yfinance** corporate-events provider (`data/events/yfinance_source`, cache in SQLite) | `[existing]` | Sole approved secondary source; drives earnings/split markers when IBKR has none; **untouched** (`AC-D38.4`, `AC-D38.5` stand). |
| **SQLite** (`data/db.py`, `bar_cache`, stores) | `[existing]` | **No migration** this batch; a pre-D45 DB opens unchanged with its legacy stop/target values. **SUPERSEDED BY D46 / A99: one guarded destructive migration runs at `DB()` construction; a pre-P5 DB keeps every row and loses only those two values.** |
| **Qt `QSettings`** (watchlist width/columns) | `[existing]` | Untouched; a stale entry naming the removed dock/toolbar button must be ignored (Journey 38 edge case) — Qt ignores restored state whose objectName no longer exists. |
| *New integrations* | — | **None.** D45 adds no service, no dependency, no endpoint. |

### Frozen Interfaces (D45)

Interfaces this batch treats as **read-only**: settled, and modified by **no** D45 task. Contracts are
**verbatim** from the tree at `c702be9` (never paraphrased), with the owning module, so Task Manager can hand
a worker the contract instead of the implementation. **Nothing under construction this batch is listed** —
the digest/kill-switch/SL-TP/close surfaces (being deleted) and the 8-column render (being changed) are
deliberately absent, and `ibkr/orders.py` is frozen **at its API** with one permitted docstring note (`S29`). **[SUPERSEDED BY D46/P5 — the module is deleted outright, so this freeze is void]**

| Interface | Verbatim contract | Owning module |
|---|---|---|
| Dividend signal `[existing]` | `dividend_updated = Signal()` | `ui/ticker_session.py` |
| Tick-59 ingress `[existing]` | `def on_s0_tick_string(self, req_id: int, tick_type: int,`<br>`                          value: str) -> None:` — tick-59 branch parses defensively, sets `_dividend_info`, emits `dividend_updated`, calls `_merge_ibkr_dividend_event` | `ui/ticker_session.py` |
| Dividend reader `[existing]` | `def dividend_info(self) -> dict:` | `ui/ticker_session.py` |
| S0 registration API `[existing]` | `def s0_register(self, feature: str, ticks: set[str]) -> None:` · `def s0_deregister(self, feature: str) -> None:` · `def s0_register_many(self, needs: dict[str, set[str]]) -> None:` · `def s0_deregister_many(self, features) -> None:` | `ui/ticker_session.py` |
| Event merge / read `[existing]` | `def _merge_ibkr_dividend_event(self) -> None:` · `def _merge_events(self, new_events: list, source: str) -> None:` · `def events(self) -> list:` · `def events_unavailable(self) -> bool:` | `ui/ticker_session.py` |
| Dividend string parser `[existing]` | `def parse_ib_dividend_string(value: str) -> dict[str, Any]:` | `data/events/provider.py` |
| Marker overlay API `[existing]` | `class EventMarkerOverlay(QObject):`<br>`    def __init__(self, plot: pg.PlotWidget):`<br>`    def set_bars(self, bars) -> None:`<br>`    def set_collapse_map(self, collapse_map) -> None:`<br>`    def set_events(self, events, unavailable: bool = False) -> None:`<br>`    def event_count(self) -> int:`<br>`    def clear(self) -> None:`<br>`    def countdown_text(self) -> str:` | `ui/event_marker_overlay.py` |
| MD-line guard `[existing]` | `def assess(projected_count: int, symbol: str, purpose: str`<br>`           ) -> tuple[str, str]:` — level ∈ `{"ok", "approaching", "exceeded"}` | `services/md_line_guard.py` |
| `Position` SL/TP fields **`[existing]` → VOID from P5** | `stop_loss: Optional[float] = None` · `take_profit: Optional[float] = None` (on both `Position` and `TradeGroup`) — **VOID from P5 (`S47`): both fields DELETED** | `data/models.py` |
| Position upsert `[existing]` | `def _upsert_position(self, position: Position) -> int:` — `INSERT INTO positions (… stop_loss, take_profit …) … ON CONFLICT(symbol, con_id) DO UPDATE SET … stop_loss=excluded.stop_loss, take_profit=excluded.take_profit … ` + `RETURNING id` — **VOID from P5 (`S47`/`S48`): the upsert is 13 columns, re-derived in wave 7** | `ui/main_window.py` |
| Position bulk load **`[existing]` → VOID from P5** | `def _on_position_end(self):` — SELECTs the 15 columns incl. `stop_loss`, `take_profit`, stamps `id` — **VOID from P5 (`S47`/`S48`): 13 columns, `trade_group_id` read by name** | `ui/main_window.py` |
| Order registry API `[existing]` | `class Orders:` with `def market_order(self, action: str, qty: float) -> Order:` · `def limit_order(self, action: str, qty: float, price: float) -> Order:` · `def stop_order(self, action: str, qty: float, price: float) -> Order:` · `def bracket_order(`<br>`        self,`<br>`        parent_id: int,`<br>`        action: str,`<br>`        qty: float,`<br>`        entry_price: float,`<br>`        stop_price: float,`<br>`        limit_price: float,`<br>`    ) -> tuple[Order, Order, Order]:` · `def register(self, order: UserOrder) -> None:` · `def get(self, order_id: int) -> Optional[UserOrder]:` · `def update_status(self, order_id: int, status: str) -> None:` · `def clear_filled(self, order_id: int) -> None:` · `def all(self) -> Dict[int, UserOrder]:` · singleton `orders = Orders()` — **API frozen; the only permitted edit is a module-docstring note; no signature and no behaviour change** — **VOID from P5 (`S39`, 2026-10-25): the module and this API are DELETED; nothing may implement or restore them** | `ibkr/orders.py` |
| Inert inbound observers `[existing]` | `def _on_open_order(self, orderId: int, contract, order, orderState):` · `def _on_order_status(self, orderId: int, status: str, filled: float,`<br>`                           remaining: float, avgFillPrice: float,`<br>`                           permId: int, parentId: int, lastFillPrice: float,`<br>`                           clientId: int, whyHeld: str, mktCapPrice):` · `def _on_exec_details(self, reqId: int, contract, execution):` · `def _on_order_error(self, order_id: int, error_code: int, error_string: str):` · `def _update_order_status(self, orderId: int, status: str):` — **VOID from P5 (`S40`, 2026-10-25): all five members are DELETED; nothing may implement or restore them** | `ui/main_window.py` |
| Portfolio render API `[existing]` | `account_summary_changed = pyqtSignal(dict)` · `positions_changed = pyqtSignal(list)` · `def set_account_summary(self, summary: dict[str, str]) -> None:` · `def set_account_id(self, account_id: str \| None) -> None:` · `def set_account_unavailable(self, unavailable: bool) -> None:` · `def set_positions(self, positions: list[Position]) -> None:` · `def add_position(self, position: Position) -> None:` · `def refresh(self) -> None:` | `ui/active_portfolio_panel.py` |
| Portfolio collapse header `[existing]` | `def is_collapsed(self) -> bool:` · `def set_collapsed(self, collapsed: bool) -> None:` · `def toggle_collapsed(self) -> None:` · `self.summary_label` (the right dock's title-bar toggle, D21.13) | `ui/active_portfolio_panel.py` |
| Right-dock minimum `[existing]` | `RIGHT_DOCK_MIN_WIDTH = dock_layout.RIGHT_DOCK_MIN_WIDTH` (= 200, `ui/dock_layout.py`) — the **value** is frozen; only the module docstring's "10-column" wording is corrected | `ui/active_portfolio_panel.py`, `ui/dock_layout.py` |
| Broker boundary `[existing]` | `class IBApiClient(EWrapper, EClient):` — `EClient.__init__(self, self)`, remembered connect params for the D27.3 reconnect (`_do_reconnect` re-issues the real `EClient.connect`), `def connected(self)`, the bridge instance. **No `placeOrder`/`cancelOrder`/`reqGlobalCancel` definition exists here** (all inherited from `EClient`) — this batch must not add one | `ibkr/client.py` |
| Fail-fast port check `[existing]` | `def check_live_port() -> None:` | `config/settings.py` |
| Error classification `[existing]` | `def classify_error(error_code: int) -> str:` — returns `'info' \| 'warning' \| 'fatal'`; drives the connection-alert path (`_on_order_error` is deleted — D46/P5 `S40`) | `ibkr/error_codes.py` |

### Non-Functional Approach (D45)

- **Reachability / zero-transmit (from `D45.2`, `AC-D45.4`, `AC-D45.6`, R70).** The guarantee is delivered by
  **structure** (three call sites severed, five modules deleted) and **verified twice**: a static AST/string
  scan over `ui/ services/ data/ ibkr/ config/` (no `placeOrder`, `cancelOrder`, `reqGlobalCancel`,
  `validate_order`, the deleted module names, or any of the removed member tokens) plus a `ui/`-only grep for
  the prose net, and a behavioural walkthrough over a real offscreen `MainWindow` with a mocked client
  exercising every surviving affordance, asserting
  `placeOrder.call_count == cancelOrder.call_count == reqGlobalCancel.call_count == 0`. Requirement
  `D45.5`/`AC-D45.5` (Portfolio still renders and live-updates, view-only, reflecting a TWS-side close on the
  next position update) is asserted on the same walkthrough so "removed" cannot quietly mean "stopped
  rendering".
- **Dividend preservation (from `AC-D45.2`, `D45.3`, R68 — the batch's highest-risk deletion).** Both halves
  share one `s0_register` mechanism and one file (`ui/ticker_session.py`). Mitigation is procedural **and**
  structural: the S0 union is built from `_s0_needs`, so removing the `"news"` need leaves `"dividends"`
  registering `"456"` unchanged; the surviving event-marker/dividend cases in `tests/test_d38_events_news.py`
  are the regression guard; and the residue list explicitly **forbids** deleting `"456"`, tick 59,
  `_dividend_info`, `dividend_updated`, `_merge_events` (they are the survivor allow-list, not residue).
- **Data safety / no migration (from A87, `D45.6`, `AC-D45.10`).** **SUPERSEDED BY D46 / A99 — there IS a destructive
  migration (§ P5 `S47`); a pre-P5 file keeps every row but loses the two values.** The D45 record: the DB and the ORM fields are untouched, so
  the migration surface is zero: a pre-D45 database opens unchanged, legacy `stop_loss`/`take_profit` values
  survive, and the upsert keeps writing them. The only data-adjacent change is **presentational** (two columns
  not rendered). Verification includes opening a pre-D45 file and confirming the values are still there.
  The verification of the P5 end state is the legacy-fixture test.
- **Worker safety on delete-only work (from memory 2026-10-15, R69).** D41 lost three workers to large
  delete-only tasks. D45 is **split by member group and by file, one wave per `ui/main_window.py` touch**, and
  every wave task ends with an import/syntax check plus its own group's residue grep — so a worker death is
  detected at the file, not at the suite.
- **Importability between waves (from S37).** The window half of Group B lands **before** the panel half,
  because removing the panel's signals first would make `MainWindow.__init__` connect attributes that no
  longer exist — every window test would fail for a reason unrelated to the work in flight. Each wave leaves
  the app importable and its own tests green; the wave-membership rule (an assertion's subject dies in the
  same wave as its removal) keeps that true for the shared test files.
- **Doc freshness (from `D45.5`, `AC-D45.7`, R71).** Two owner-facing docs plus the Plan-owned map; the
  assertion is **grep-checkable** (`News Digest`, `Ctrl+Shift+N`, `Close All Positions`, `Close Group`,
  `Close Position`, `Kill switch`, `Stop-Loss` absent except where the text says the app does not place/cancel
  and that closes/cancels happen in **TWS**), so the Code Reviewer verifies it independently rather than
  trusting the task.
- **Performance / scalability.** No measurable change and none required: the positions table renders two
  fewer cells per row, three scheduled paths disappear (the digest's article fetches, the kill switch's
  per-ID cancel loop, the close path's pacing-deferred retry), and no new request is issued on any path. The
  S0 line for a charted symbol becomes *shorter* (`"456"` only), not longer.
- **Security / blast radius (the point of the batch).** The app's authority over the account **shrinks to
  zero**: it cannot place, cancel or close, so the notional cap, the order pacing bucket and the
  disconnected-order guard stop gating anything (`AC-D26.7`/`D26.9` moot). Accepted and recorded (owner,
  R73): **TWS is the cancel surface**, and the app cannot create the order it would need to cancel. No new
  credential, no new endpoint, no new persistence.
- **Platform side effect (A86).** Removing `menuBar()` means the app creates **no `QMenuBar`** at all — on
  macOS it contributes **no** application-menu items, and no orphan `Ctrl+Shift+N` `QAction` can survive
  because the action object lived on the deleted dock's `toggleViewAction()`.

### Architecture Risks (D45)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| **AR-D45-1** | Removing the news `"292"` line takes the **dividend `"456"`** path (and the markers) with it — one `s0_register` mechanism, one file (R68) | **H** | `AC-D45.2` pins both sides; the surviving event-marker/dividend cases are the guard; the residue list marks `"456"`/tick 59/`_dividend_info`/`dividend_updated` as **survivors**; Build greps `"292"` after each file in the group |
| **AR-D45-2** | A half-finished deletion leaves the app non-importable (dangling import, a signal connected to a deleted handler, a call into the deleted validation module) — the D41 worker-death pattern (R69) | **H** | One wave per `ui/main_window.py` touch; per-file syntax/import check + residue grep; the per-wave test command covers every suite that builds a window |
| **AR-D45-3** | The **suite stays green while proving less** — five order-safety suites deleted (R70) | **H** | `S36`'s static invariant + zero-transmit walkthrough replace the *intent*; the loss is stated in D45 consequence 5 and the plan's test book, never presented as "no change"; the new guard is proven **RED** on the pre-D45 tree |
| **AR-D45-4** | Column shift (`10 → 8`) makes a Strategy/Group assertion read the wrong cell and pass (R75, DG77) | **M** | `AC-D45.10` fixes the shape; the two named files are adjusted `8/9 → 6/7` in the **same wave** as the panel edit; a `tests/`-wide scan confirmed no third column-index assertion exists |
| **AR-D45-5** | A **half-removed** cancel/protection/context-menu path survives (an `order_registry` read in `_on_order_error`, a leftover `_ref_price_for`, an orphan `set_sltp` string, a panel member whose menu is gone) and a later worker "restores" it (R74) | **M** | The residue list is extended beyond D45's own list and **verified live**, and it names the **nine panel members wave 3 deletes** (`_show_context_menu`, `_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_selected_row`, `_selected_position`, `_on_selection_changed`, `set_sltp_action`) alongside `_ref_price_for`, `_s0_headless`, `_on_s0_tick_news`, `NewsDigest`, `menuBar`. Its **scope is stated** so the claim is checkable: AST over `ui/ services/ data/ ibkr/ config/` (comments invisible ⇒ `config/settings.py`'s `validate_order()` comment is out of scope) plus a `ui/`-only grep; `tests/` is covered by neither, which is why `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in `tests/test_d45_removal.py`. `S29`/`S35` record the **intentional** survivors so inertness is not mistaken for a leftover |
| **AR-D45-6** | A wave-2/3 ordering mistake makes the panel's removed signals still connected (or the reverse), producing `AttributeError` at window construction | **M** | `S37`: window-first ordering is mandatory and stated; the panel's signals are removed only after the window stops connecting them |
| **AR-D45-7** | Docs drift — the three files keep advertising the digest, the `View` menu, app-placed closes, an in-app cancel or settable SL/TP (R71) | **M** | `AC-D45.7` is grep-checkable; one doc task owns both owner-facing docs (the map is Plan-owned); the Code Reviewer greps independently |
| **AR-D45-8** | An **unlisted** test/assertion depends on a removed surface and turns red or silently stops testing (R72) | **M** | The plan's test book enumerates **assertions**, not files; the full offscreen suite runs in the final wave; the two "kept by decision" files are justified individually (`test_d41_removal`, `test_stop_loss_target`); sequencing rule 4 puts each assertion's removal in the wave that deletes its subject |
| **AR-D45-9** | **No in-app panic cancel** afterwards — a runaway TWS order cannot be stopped from the app (R73) | **H** *(accepted)* | Owner-accepted and recorded; **TWS is the cancel surface**; `AC-D45.6` forbids re-adding a cancel path without a new requirement; docs say so plainly |
| **AR-D45-10** | `ibkr/orders.py` retained-but-unused invites a future reconnection and contradicts "the app places no orders" (DG76) | **L** | `S29`: retained with a docstring note stating unreachability; `ibkr/orders.py`'s builders keep unit coverage (`tests/test_order_builders.py`); `AC-D45.4`'s scan makes a new caller fail a test, not just a review. **SUPERSEDED by P5 (2026-10-25): the module is deleted, so the risk and its note are both moot — `ESC-061` is closed as moot, not implemented.** |

### Requirements → architecture traceability (D45)

| Requirement / journey | Architecture section | Phase (plan) |
|---|---|---|
| **`AC-D45.1`** (no digest dock; no menubar; no `Ctrl+Shift+N`) | `S34`; System Components (`ui/main_window.py`, `ui/ticker_session.py`, deleted `ui/news_digest_dock`); AR-D45-1/2 | Phase 1 · **Wave 1** |
| **`AC-D45.2`** (news `"292"` never requested; `"456"` retained, tick 59 + markers still work) | `S34` + Frozen *Dividend signal / tick-59 ingress / dividend reader / S0 registration / event merge / parser / marker overlay*; Integration Points; AR-D45-1 | Phase 1 · **Wave 1** |
| **`AC-D45.3`** (no context menu; no close/close-group/flatten affordance) | `S30` + `S32`; System Components (`ui/active_portfolio_panel.py`, deleted `ui/trade_context_menu`); AR-D45-2/5/6 — the `hasattr(...) is False` measurables are asserted **directly** in the wave-6 module (the token list is a net, not a substitute) | Phase 1 · **Waves 2–3**; Phase 2 · **Wave 6** |
| **`AC-D45.4`** (zero order interaction; `placeOrder`/`cancelOrder`/`reqGlobalCancel` unreachable) | `S30` + `S31` + `S36`; Frozen *Order registry API* / *Broker boundary*; Non-Functional (reachability); AR-D45-3/5 | Phase 1 · **Waves 2, 4** + Phase 2 · **Wave 6** |
| **`AC-D45.5`** (Portfolio view-only; data path retained; TWS-side close reflected) | `S33`; Frozen *Portfolio render API*; Data Model (`_on_position_end`); AR-D45-4 | Phase 1 · **Wave 3**; Phase 2 · **Wave 6** |
| **`AC-D45.6`** (INVERTED — kill switch and SL/TP dialog are GONE; no cancel path) | `S31` + `S32`; System Components; AR-D45-5/9 | Phase 1 · **Waves 3 (dialog), 4 (kill switch)** |
| **`AC-D45.7`** (docs cleaned in the same batch) | `S38`; System Components (docs rows); Non-Functional (doc freshness); AR-D45-7 | Phase 2 · **Wave 5** |
| **`AC-D45.8`** (no dangling references; suite green; recorded test book) | `S36` + `S37` (**including the wave-membership rule: an assertion's subject and its removal live in the same wave**); the plan's test book (5 deleted / **7** adjusted / 1 added); AR-D45-2/3/8 | Phase 1 · **Waves 1–4** + Phase 2 · **Wave 6** |
| **`AC-D45.9`** (history preserved; marker + tech stack intact) | `S29`–`S38` relationship table; *Supersessions* below | — (recorded; no production edit) |
| **`AC-D45.10`** (Stop/Target columns gone; storage + no-migration guarantee) | `S33`; Data Model (view model + `positions`/`trade_groups` unchanged); AR-D45-4. **SUPERSEDED BY D46 / A99:** the storage half ("no migration") is replaced — the columns and fields are **dropped** (`S47`) | Phase 1 · **Wave 3**; Phase 2 · **Wave 6** |
| **`D45.1`–`D45.6`** (the six requirements) | `S29`–`S33`, `S36`, `S38` | Phases 1–2 |
| **Journey 38** (steps 1–9; postconditions; the edge cases: stale dock state, orphan shortcut, TWS–cancel, legacy stop/target rows, pre-D45 DB, disconnected) | `S31`, `S33`, `S34`, `S35`, `S38`; Non-Functional (data safety, platform side effect); Data Model | Phase 1 · **Waves 1–4** + Phase 2 · **Waves 5–6** |
| **A79 / A86 / A87 / A88 / A89 / A90** (owner-decided defaults) | `S34` / `S34` / `S33` / `S31` / `S32` / `S35`; Frozen interfaces | Phases 1–2 |
| **A80 + DG76** (`ibkr/orders.py`: delete or retain) | `S29` — **retained**, with the docstring note; DG76 resolved. **SUPERSEDED BY D46 / A99 (`S39`): the module is DELETED** | Phase 1 · **Waves 2–4** (no task touches the module's API) |
| **A81 / A85** (test-book and doc scope) | `S36`, `S38`; the plan's test book | Phases 1–2 |
| **R68 / R69 / R70 / R71 / R72 / R73 / R74 / R75** | AR-D45-1 / 2 / 3 / 7 / 8 / 9 / 5 / 4 | Phases 1–2 |
| **DG75** (the "fourth deleted file" count) | Resolved by supersession — the book is now **five named** whole-file deletions (`AC-D45.8`); no deletion rests on a count | Phase 1 · **Waves 2–4** |
| **DG77** (assertions invalidated in files that stay) | `S37` + AR-D45-4/5; the plan's test book names every adjusted assertion | Phase 1 · **Waves 1–4** |
| **D1–D44** | `[no relationship]` — **not reopened**; only the clauses D45 names are superseded/revised | — |

### Supersessions and non-changes (recorded, never silent) (D45)

1. **`AC-D38.2` / `AC-D38.3` — SUPERSEDED BY D45.** The digest's grouping and its no-entitlement state have no
   surface left (`S34`); `AC-D38.6`'s green-suite rule stands for the surviving half (markers + dividend merge:
   `AC-D38.1`, `.4`, `.5`).
2. **`AC-D41.1`'s Portfolio clause — REVISED.** "Portfolio section (Close / Close Group / Flatten All + the
   SL/TP dialog) still renders" → "renders **view-only** (no close/flatten control, no SL/TP dialog, no
   Stop/Target columns)" (`S30`, `S32`, `S33`).
3. **`AC-D41.4` (retained-order-path / `ref_price`) — REVISED and MOOT in part.** No order-related surface is
   retained: the SL/TP dialog goes too, nothing builds or transmits an order (`S30`), and `ref_price` has no
   consumer — `_ref_price_for` is deleted while its `_symbol_last_prices` source stays for the P/L path.
   D41's "Scope — KEEP: order machinery" bullet is **superseded**: `ibkr/validation` deleted; `ibkr/orders`
   retained **without a caller** (`S29`, A80/A90); only the fail-fast port check and the inert inbound
   observers remain. **[REVERSED BY D46/P5 `S39`/`S40`: `ibkr/orders` is deleted, not retained; the inbound observers and the three bridge signals are deleted too; only the fail-fast port check and `IBApiClient.error`'s generic per-code surfacing remain.]**
4. **D26 order-entry clauses — MOOT / SUPERSEDED.** `AC-D26.3` (SL/TP labelling branch) is **moot** (`S32`);
   `AC-D26.8` (kill switch: `reqGlobalCancel` + per-ID cancels + pre/post counts) is **superseded in full**
   (`S31`); `AC-D26.7` (validate-order gate) and `AC-D26.9`'s order-entry/registry clauses have **no control to
   exercise**; `AC-D26.4`/`AC-D26.6` were already control-less after D41. **Retained:** the fail-fast port
   check + connection badge (`AC-D26.5`) and the connection half of the error alerts (`S35`).
5. **`D21.13` — reviewed, NOT superseded.** It governs the right dock's title-bar toggle and the Portfolio
   panel, which **stays** (view-only). No `AC-D21.13.*` clause names a close/flatten, kill-switch or SL/TP
   control; the frozen *Portfolio collapse header* contract is unchanged.
6. **`AC-D18.6` / D18 width model — NOT superseded, re-derived.** The table drops 10 → 8 columns, which only
   **reduces** its width demand; `RIGHT_DOCK_MIN_WIDTH` keeps its value; the D18 cap/visibility criteria stand.
7. **Glossary.** "Live-order path" **revised** (no live-order path exists); **new** rows "Kill switch" and
   "SL/TP dialog" record both as **removed**. Recorded by Requirements; no production consequence.
8. **The cancelled-draft numbers (`S29`–`S32`, `FI-D45-1`, `AP-D45-*` of the previous, never-activated D45
   draft) carry no authority**; `FI-D45-1` in particular is **moot** — the SL/TP dialog it described as
   "retained with no entry point" is now **deleted** (A89/`S32`). The refreshed `docs/codebase-map.md` no
   longer names `_kill_switch` or `StopLossTargetDialog` as retained (it did in the previous draft's
   annotations — DG77 item 1).
9. **Explicit non-changes (recorded so they are not read as omissions):** the chart render stack, `ui/dock_layout.py`
   constants (values), `ui/watchlist_panel.py`, the chart load/backfill path, alarms, drawings, studies,
   pop-outs, D39/D40/D42/D43/D44 behaviour, `data/db.py`'s schema and migrations, `data/models.py`'s fields,
   the `_upsert_position` upsert, `ibkr/orders.py`'s API, `ibkr/pacing.py`, `config/settings.py` (the now-dead
   `MAX_ORDER_NOTIONAL` constant is **not** deleted — outside the owner's inventory; noted in the plan), and
   the pinned dependency set (**no new dependency**). **[SUPERSEDED BY D46/P5 at the owner's instruction: `data/models.py`'s fields and the `_upsert_position` upsert lose the two SL/TP columns via migration; `ibkr/orders.py`'s API and the module itself are deleted; `ibkr/pacing.py` loses `OrderRateLimiter`/`order_limiter`; `MAX_ORDER_NOTIONAL` **is** deleted. The chart, alarms, drawings, studies, pop-outs, D39/D40/D42/D43/D44 behaviour and the dependency set remain genuine non-changes.]**
10. **The D45 register's suggested "three-signal loop" is recorded as a DEVIATION, not as pending work.** The
    register's correction record (`requirements.md:4178`–`:4179`) and `DG77` item 4 describe the
    `tests/test_dock_d18_region.py` edit as the five-signal loop "shrinking to three". D45 removes **all
    five** signals, so no signal survives and a three-signal loop cannot exist in any wave. The loop is
    **deleted** (wave 2) and the file's remaining assertions stay; `AC-D45.8` requires the file to be
    *adjusted* and is satisfied. Recorded here, in the plan's § Exactness note, and in `docs/plan_notes.md`
    `RG-D45-1` so no later worker "restores" the three close signals.

**Handoff:** this increment is validated `Status: APPROVED` (2026-10-25, legacy single-scope D45 cycle 2 of
3 — round 1 was `CHANGES_REQUIRED` on R1–R4, all closed and re-verified); the companion plan is
`docs/plan.md` § *D45 — Batch 20* (`Status: READY_FOR_TASK_MANAGER`) and the review is
`docs/plan_review.md` (D45 cycle 2). The Code Reviewer independently re-verifies (a) **zero** `placeOrder`,
`cancelOrder`, `reqGlobalCancel` call sites in `ui/` **and** zero issued on the mocked-client walkthrough,
(b) the dividend markers still rendering (`"456"` registered, tick 59 → `dividend_updated`,
`event_count() > 0`), (c) the positions table at 8 columns with no `Stop`/`Target` header and
Strategy/Group at `6`/`7`, (d) a pre-D45 database opening with its stored stop/target values intact and the
upsert still writing them (no migration) — **SUPERSEDED BY D46 / A99: the columns are DROPPED at first open; a pre-P5 DB
keeps every row and loses only those two values (legacy-fixture test)**, (e) the two owner-facing docs advertising nothing removed, (f) the
new guard's recorded RED-on-`c702be9` failures, and (g) that the intentional survivors (A90's observers, the
ibapi news boundary, the dividend path) were not deleted. **`ESC-055` stays TASK_MANAGER-owned.**

---

## Phase P5 — D46 increment (Batch 21): **every** order-related coding path is deleted — the module, the observation chain, the zero-consumer order utilities, `IdManager.reserve`, and the stop/target storage (a real, guarded migration) — **revision 2 (scope EXPANDED by the owner 2026-10-25, Q56–Q59)**

> **Revision 2 (2026-10-25) — why this section was re-drafted.** The requirements were **re-registered** after
> revision 1 was validated and activated: `D46` is no longer "delete the module and its chain" but *all
> order-related code* — `ibkr/orders`, the observation chain, `data.models.UserOrder`, `ibkr/account.py`'s
> `Position` copy, `IdManager.reserve`, `OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL`, the order-fill
> sound, and **the four `stop_loss`/`take_profit` columns dropped by a real migration** (owner-confirmed
> 2026-10-25). The register is now `D46.1`–`D46.13` / `AC-D46.1`–`AC-D46.13` / A91–A104 / R76–R85 / DG78–DG87.
> This section is therefore **not** a revision against a `CHANGES_REQUIRED` list (there is none — revision 1 was
> `APPROVED`); it re-drafts the same phase against a wider register. Every decision revision 1 settled and the
> register did not overturn is **carried forward and marked as such**; what changed is `S46` (the KEEP boundary),
> `S44` (the token set and two of its *rationales*), the wave split (5 → 10), and four new decisions (`S47`–`S50`).
>
> **Every number, every line reference and every feasibility claim below was re-derived by running it against the
> working tree and `.venv` on 2026-10-25** — including the migration itself (a `sqlite3` probe), the removal
> instrument on the pre-P5 tree (**41** AST offences / **40** twin hits) and on a **simulated post-P5 copy of the
> five source trees** (**0 / 0**). Where something could not be verified it is a design gap or a Flagged Issue,
> never an assertion.
>
> **Status of this section.** The canonical **P5** architecture, drafted **in place** (Stage 3.4 — no separate
> proposal file). The companion `docs/plan.md` § *Phase P5* was **demoted to a draft** by the scope-expansion run and
> re-drafted as revision 2; it was then **validated in full and re-activated** by Plan Artifact Editor & Validator
> (`docs/plan_review_P5.md`, `Status: APPROVED`, 2026-10-25) and ends `READY_FOR_TASK_MANAGER`. **This section is
> ACTIVE** (activation corrections are recorded in that review).
>
> **Requirements of record:** `docs/requirements/requirements.md` — `Status: READY_FOR_PLAN` (`:5404` and the batch
> footer at `:5553`). **No blocking question remains** (Q56–Q59 answered verbatim by the owner). Sections consumed:
> **`### D46`** (`D46.1`–`D46.13`, `AC-D46.1`–`AC-D46.13`, the DELETE/RETAIN inventory, the supersession record,
> A91–A104, the correction record), **Journey 39** (steps 1–10 on the expansion), **R76–R85**,
> `docs/requirements/design_gaps.md` **DG78–DG87**, `docs/requirements/open_questions.md` **Q56–Q59**.
>
> **Baseline:** `main` @ **`c702be9`** **plus the delivered, uncommitted D45 working tree** (D45 built, suite green,
> five modules and five suites already deleted). Suite invocation
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale shebang).
> **No new dependency:** PyQt6 / pyqtgraph (locked, `docs/memory.md` 2026-10-16) / `ibapi` 10.51.1 / numpy / SQLite.
>
> **Escalation state at drafting time** (`docs/code_review/escalations.json`, read-only here): **`ESC-063`** (open,
> routed **PLAN**) is **already resolved in the file of record** — `docs/codebase-map.md:25`–`:29` now reads
> **5 deleted / 7 adjusted / 1 added** with the `ESC-063` note; this run keeps the map current for the wider scope
> and does not re-open the arithmetic. **`ESC-061`** (open, **BUILD**) is **MOOT** — it asks for a module-docstring
> note on the retained `ibkr/orders`, and the module is deleted; **no task implements it** and the Code Reviewer
> closes it as moot. **`ESC-062`** (open, **BUILD**) is **folded into this phase** (`S49`) for its four comment sites
> and its one test rename — three of the four comments sit in files this phase already edits, so no separate wave is
> created. **`ESC-059`/`ESC-060`** stay BUILD-owned and are not absorbed: ESC-060's *behavioural* half becomes moot
> when the columns go, and its *documentation* half is superseded by `S50`/`D46.13`.
> `docs/pending_doc_sync.md` is **absent**. `docs/tasks/task_manager_notes.md` carries **no**
> `ESCALATED_TO_PLAN` entry.
>
> **Owner decisions this phase does not re-litigate** (recorded, none blocking): **A91** (module deleted in full,
> reversing A80), **A92** (chain removed, not kept inert — owner-confirmed), **A93** (201/103/202 surface through the
> existing generic line; no order id, no verdict, no 12 s — owner-confirmed), **A94** (error routing not reordered),
> **A96** (`data.models.UserOrder` goes — owner-confirmed), **A99** (**the four columns and all model fields are
> DROPPED by migration**, reversing A87 — owner-confirmed by Q59 *"remove everything"*), **A100**
> (`classify_error` + the generic error surface stay), **A101** (`IdManager` stays, only `reserve` goes — reversing
> A97's first half), **A102** (`nextValidId` retained: it is the CONNECTED transition), **A103** (the inventory is
> the acceptance instrument), **A104** (the two suites are deleted whole). **No replacement order, cancel or
> protection UI** — declined four times now, **not re-proposed anywhere**.

**The one workstream — subtractive, ten member groups, one invariant, one migration.** Since D45 the app has **zero
order interaction**; D46 removes the **fossil that still looks live** and the storage that outlived its only setter.
Every code member it deletes is already inert: `Orders.register()` is never called in production, so the registry is
permanently empty, every `get()` returns `None`, `_update_order_status` is a no-op and `_on_order_error` is
unreachable; `OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL` and `SoundService.play_fill` have **zero**
production readers (re-verified 2026-10-25); `IdManager.reserve` has **tests only**; and the four stop/target columns
are unreachable and unsettable (ESC-060) — a row that never updates again keeps its legacy bytes, which is why
the migration is described as byte-destroying rather than cost-free. The work splits by **member group**, never by "all the order stuff" (the D41
lesson, memory 2026-10-15 / R76), now with a **schema** step in the same batch.

The invariant that binds them is **proven inertness, preserved visibility, preserved rows**:

1. **no order code** — no module, callback, signal, registry, dataclass, builder, limiter, notional cap, order tone
   or `reserve()` in the tree (`D46.1`–`D46.11`);
2. **201 / 103 / 202 still reach the status bar** as `Error [<code>]: <TWS's own message>` for **8000 ms**, exactly
   as the owner sees them today (`D46.3` / `AC-D46.3` — the owner's explicit constraint);
3. **every `positions` and `trade_groups` row survives** the destructive schema step, together with
   `idx_positions_symbol_con_id` and the `trade_group_id` foreign key (`D46.12` / `AC-D46.12`, R82).

### Relationship to prior phases (P5)

Every decision carries exactly one relationship label. `[revises P4: …]` names the earlier decision it changes,
`[extends P4: …]` builds on one without changing it, `[new in P5]` has no prior-phase dependency (or is settled by
the requirements rather than by an earlier architecture decision). An unlabelled row would be read as new. **`P4` is
the D45 phase** — its section is `## D45 increment` above; `docs/plan.md` § *D45* is its plan half.

| # | Decision | Relationship |
|---|---|---|
| **S39** | **`ibkr/orders.py` is DELETED in full** — `UserOrder`, the four `Orders` builders, the five registry methods and the `orders` singleton — with its **only** importer (`ui/main_window.py`'s `from ibkr.orders import orders as order_registry`). No replacement module, no dormant helper, no "un-comment later" seam: a future order path needs a **new requirement**. Safe because the module has **zero** production callers (`register()` is never called, so every `get()` returns `None`). **Unchanged from revision 1.** | **`[revises P4: S29]`** — D45's "retained, unreferenced, with a module-docstring note" is superseded in full (A91). Voids D45's *Order registry API* frozen row and plan `AP-D45-1`/`AP-D45-9`; makes **`ESC-061` moot** and **`DG76` resolved**. |
| **S40** | **The inbound observation chain is REMOVED end-to-end, not kept inert** — (a) `ibkr/client.py`'s `orderStatus`/`openOrder`/`execDetails` overrides; (b) `ibkr/bridge.py`'s `order_status`/`open_order`/`exec_details` signals; (c) `ui/main_window.py`'s three `.connect` lines, `_on_open_order`/`_on_order_status`/`_on_exec_details`, `_update_order_status`, `_on_order_error`, the `order_registry` import and the `order_registry.get(reqId)` branch in `_on_error`. The `ibapi` base `EWrapper` no-ops stay **inherited**. **Unchanged from revision 1.** | **`[revises P4: S35]`** — D45's "keep the broker-boundary plumbing inert" is reversed for the **order** half only (the news half stands). Reverses **A90**; recorded by Requirements as A92. |
| **S41** | **Error surfacing narrows to what the existing generic path already shows, and its routing is untouched.** `_on_error` keeps its ordering — `_closing` guard → session-reqId branch (RT → `_on_rt_stream_error`'s 15 s line; any other session reqId → `session.on_historical_error` **and** the 8000 ms line) → the final `showMessage(f"Error [{errorCode}]: {errorString}", 8000)` — and loses only the registry branch and its D26.9 comment. `_on_order_error`'s mappings (201/103 → `"Rejected"`, 202 → `"Cancelled"`, 12000 ms) are **not** re-homed: they never ran. **Unchanged from revision 1.** | **`[extends P4: S35]`** — the connection/error half of S35 is reused unchanged; A93 records the wording end state and **A94/DG78** the deliberately unfixed orderId↔session-reqId collision. |
| **S42** | **`data/models.py::UserOrder` is deleted together with `tests/test_ui_smoke.py`'s `hasattr` assertion** (a *different* dataclass from the module's, zero consumers, one reference). **Unchanged from revision 1.** | **`[new in P5]`** — A96 / `AC-D46.8` / DG79. |
| **S43** | **Teardown is ordered by the callback graph, and the order is now ten waves.** Five rules: **consumer before subject**; **an emitter never outlives its signal**; **the window's connect/slot half goes first**; **the silent-path members go before the module**; and **the guard's token list may only name code that is already gone** (**invariant I-1**, new in revision 2). The storage wave is the one wave whose *production* half must not be split (R84/DG85). | **`[extends P4: S37]`** — D45's "assertion and subject in the same wave" applied to a larger surface; revision 1's four rules are kept in substance and rule 5 is added for the widened token set. |
| **S44** | **The acceptance instrument is the *existing* removal guard, migrated — no new test module.** `tests/test_d45_removal.py` already owns (i) an AST scan of identifiers **and** string constants over `ui/ services/ data/ ibkr/ config/`, (ii) a `ui/`-only raw-text twin, (iii) `find_spec`/absence checks and (iv) a real offscreen `MainWindow` walkthrough. **Revision 2's token set (all counted):** `_FORBIDDEN` **53 → 80**; `_SURVIVORS` **26 → 16** (the ten names `AC-D46.4` lists leave it: `order_registry`, `orders`, `UserOrder`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `order_limiter`, `MAX_ORDER_NOTIONAL` — `classify_error`, `pacing_manager`, `PacingExceeded` and the dividend/news names stay); `_DELETED_MODULES` + `ibkr.orders`; `_DELETED_SUITES` + the builders and stop-target suites. **Only `orders` and `Orders` are exact-matched** (whole identifier / whole string constant in the AST half; delimited word in the raw-text twin); the other **78** are substring tokens. **`reserve` is deliberately NOT a token** — measured **13 units across 11 files**: `ibkr/id_manager.py`'s own two, ten docstring occurrences of the English word "preserve(s/d)", and `ui/chart_panel.py`'s `_reserve_price_tag_lane`; `IdManager.reserve` is measured by `hasattr(IdManager, "reserve") is False` instead (`AC-D46.10`'s own measurable). `stop_loss`/`take_profit` **must** be substring tokens because the SQL site that reintroduces them is one whole string constant (`"…, right, stop_loss, take_profit, trade_group_id"`), which whole-unit matching cannot see (DG85). | **`[extends P4: S36]`** — one instrument, one token list, so the grep step and the test cannot drift. **Revision 2 corrects revision 1's two *rationales*, not its mechanism:** the exact-match set was justified by two docstrings in files "no task may edit" (`ibkr/pacing.py`'s `OrderRateLimiter`, `ibkr/id_manager.py`'s `reserve`) and **both are deleted by this phase** — that ground is void. The set is retained on a different, stated ground (prose safety: ordinary English words, and exact matching still catches every class/alias/call/attribute reintroduction), and `pacing.py`/`id_manager.py` are now **edited**, not exempt. |
| **S45** | **The Plan-owned prose is corrected in this phase.** `docs/codebase-map.md`: the `ibkr/orders` retention claim, the "retained observers — do not clean up" block and the "(docstring note only)" row are replaced by the post-P5 target; the KEEP/survivor list loses `reserve`, `order_limiter`, `MAX_ORDER_NOTIONAL` and the stop/target storage; the D45 book stays **5 / 7 / 1** (`ESC-063`); the P5 book is rewritten. This section supersedes `S29`/`AR-D45-10` and voids D45's frozen rows for the module and the observers. **Extended in revision 2** to the document trail (`S50`). | **`[revises P4: S29 + AR-D45-10 + the map's D45 annotations]`** — DG81's hazard exactly: a Build worker reading the map would preserve what must go, and no token scan catches prose. |
| **S46** | **The KEEP boundary is re-drawn for the wider register — revision 2's biggest change.** **Frozen:** `classify_error`'s severity table, `Bridge.error_msg`, `IBApiClient.error`'s `severity != 'info'` gate **and** the D40.1 `502` backoff suppression, `_on_error`'s session-first routing and its 8000 ms line, `config/settings.py::check_live_port`, the connection badge, the no-test-transmits rule, **`IdManager` itself with `get_id`/`set_next_valid_id`/`id_manager`** (six `get_id()` callers, incl. **`ui/main_window.py:1095`** — a caller the register does not list), **`IBApiClient.nextValidId`**, **`PacingManager`/`PacingExceeded`/`pacing_manager`**, **ICT `order_blocks`/`orderBlocks`/`_render_order_blocks`**, **`sort_order`**, **`Position`/`positions`/the Portfolio view and the strategy grouping** (`services.strategy_detection` over `Position.id`/`qty`/`strike`/`right`), with the note that **`TradeGroup`, `trade_groups` and `position_group_map` are dead storage** — no reader and no writer anywhere (the audit's R10 correction) — **retained only to avoid widening the batch**, never as a "display grouping" the panel consumes, **`Position`/`positions`/the Portfolio view**, **`play_alarm`/`render_alarm_chime`/`ensure_sound_files`'s `"alarm"` key**, **`advancedOrderRejectJson`**, and the D38 dividend path. **Removed from revision 1's KEEP set** (they are now tasks): `IdManager.reserve`, `OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL`, the order-fill sound, and the `stop_loss`/`take_profit` storage plus the four model fields. | **`[revises P4: S29's KEEP roster and revision 1's S46]`** — the counter-weight to a *wider* delete-only batch: D45 already lost a dividend path once (R68) and the owner's worries here are lost error visibility (R77) and lost rows (R82). Every survivor is frozen **with its consumer named** (`A100`–`A103`, R83). |
| **S47** | **The stop/target storage is dropped by four guarded in-place `ALTER TABLE … DROP COLUMN` statements — not by a table rebuild.** `data/db.py::_migrate_schema()` gains one block, placed **immediately after** the `CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_symbol_con_id` statement and therefore before any read of either table: for each of `positions` and `trade_groups`, read `_table_columns(table)` **once** and drop `stop_loss` and `take_profit` when present. The `CREATE TABLE IF NOT EXISTS` DDL loses the same four lines, so a **fresh** DB never has the columns and all four statements are skipped. **End state is `D46.12`'s, verbatim**; only the mechanism is decided here (DG86 asked for exactly that). **Why DROP COLUMN, measured rather than assumed (probe in `.venv` 2026-10-25):** rows preserved (3 and 1); `sqlite_sequence` preserved (`positions` 3 → 3, so ids are never reissued); `idx_positions_symbol_con_id` still in `sqlite_master` and still enforcing `UNIQUE`; `PRAGMA foreign_key_list(positions)` still reports `trade_group_id → trade_groups.id`; `foreign_key_check` empty; `integrity_check` = `ok`; `trade_group_id`'s value preserved; the **13-column upsert + `ON CONFLICT` + `RETURNING id` still works**; a second open is a no-op. **Crash safety:** each `DROP COLUMN` is a single atomic DDL statement, so an interrupted open leaves only the columns not yet dropped (each `DROP` commits on its own) and the guard finishes the job — no half-built table to salvage. That is the decisive difference from the `bars` precedent (`data/db.py:203`–`:236`), whose salvage branch exists because Python's `sqlite3` runs `CREATE TABLE` **outside** the implicit DML transaction; a rebuild of `positions` would need that machinery *per table* plus hand-recreated index and FK. **Rejected:** the rebuild route (more failure surface, zero benefit); **and** no automatic copy of the DB file — copying the owner's database at launch is a new behaviour with its own failure modes and no row-copy step to interrupt; row preservation is proven by a legacy-fixture assertion instead (`AC-D46.12`). | **`[new in P5]`** — the requirements fix the **end state** and leave the mechanism to Plan (`D46.12`, DG86). It **reverses A87** and records the third step of the trail (**kept → cleared → dropped**, `S50`). |
| **S48** | **The bulk load reads its 13 columns by name, and one new assertion proves the mapping.** `_on_position_end`'s SELECT loses two names, so `trade_group_id` moves from **`row[14]` to `row[12]`** — and a missed index is the batch's only **silent** failure (a stop value or `None` lands in the Portfolio **Group** column and reads as a strategy-detection regression, DG85). Decision: that one call site uses a **dedicated cursor with `sqlite3.Row`** and reads `row["trade_group_id"]`, so the mapping is expressed once and cannot shift again; the shared `db.conn` row factory is **not** changed (every other caller unpacks tuples). A wrong mapping is still caught end-to-end by a new case that seeds a **non-null** `trade_group_id` — measured: **no test seeds one today**, so the trap is currently uncovered. | **`[new in P5]`** — DG85's recorded recommendation applied; **rejected** alternative: keep positional indexing and correct the numbers (smaller diff, same bug class live for the next column change). |
| **S49** | **`ESC-062` is folded into the waves that already touch its files, not given a wave of its own.** (a) `ui/main_window.py:3101`–`:3104` (the `positions.id` comment's "SL/TP dialog persists via `WHERE id=?`") and `:3128`–`:3130` ("the SL/TP dialog early-returns") are reworded in the **storage wave**, which edits both comments' subjects; (b) `ibkr/account.py:40`–`:43` (the `Position.id` comment's dialog clause) is reworded in the same wave; (c) `ui/main_window.py:1543`–`:1545`'s "so the ticket reflects reality" comment is **deleted** with the `_on_error` branch in the consumer wave — incidental, recorded, not claimed as a fix; (d) `tests/test_dock_d18_region.py`'s `test_T48_T03_panel_present_and_signals_wired` is **renamed** for what it now asserts in the **prose wave** (no earlier wave touches that file). Three comments + one rename, zero new tasks. | **`[new in P5]`** — the escalation is BUILD-routed, but its sites are already inside this phase's file set, so absorbing it costs no scope; leaving it out would ship a batch whose deliverable is "no order surface" while four comments still describe one. |
| **S50** | **The document trail reads kept → cleared → dropped, in one direction, and P5 owns the half it may write.** `docs/architecture.md` § P5 and `docs/plan.md` § P5 (this draft) state the dropped end state; `docs/codebase-map.md` is refreshed here; **`USAGE.txt`** (`:88`–`:90`) and **`usage.md`** (`:154`) are corrected in a Build task, because they are the two files that still say the columns are *kept*; the **D45 sections** of `architecture.md`/`plan.md` are **already-activated sections this run may not edit** — their retention sentences are enumerated by line in `docs/plan.md` § *Document trail* so the Validator can attach the supersession markers at activation (revision 1's *Activation note 2* mechanism), and `A87`'s row in `requirements.md` already carries its `REVERSED` note. `D46.13`'s grep is the gate. | **`[revises P4: ESC-060's documentation correction]`** — ESC-060 said *kept, values cleared*; A99 says *dropped*. Both must not stand as live claims (DG84, `R85`). |

---

### Codebase Summary (existing repository — the P5 surface, re-validated 2026-10-25)

**This is the pointer to `docs/codebase-map.md`, not a second inventory.** The map carries the module index,
the status legend and the test-impact rows; this section records only the facts P5's decisions rest on, each
re-derived from source (`graphify-out/graph.json`, 4,947 nodes, used for discovery only — it still describes the
pre-D45 tree; **the source is authoritative** where they disagree).

| Fact | Verified evidence (working tree = `c702be9` + delivered D45) | Consequence |
|---|---|---|
| `ibkr/orders.py` has **exactly one** importer in the tree | `ui/main_window.py:36` → `from ibkr.orders import orders as order_registry`; a repo-wide grep for `ibkr.orders` / `import orders` finds no other production hit and `ibkr/__init__.py` re-exports nothing | `S39`: deleting the module and that line together leaves no dangling import (`AC-D46.1`); wave 1 removes the line, wave 3 the file |
| The registry is **never written** in production | no `register(` call outside `ibkr/orders.py`; the only caller in the tree is the deleted `tests/test_order_builders.py` | every `get()` returns `None` ⇒ `_update_order_status` is a no-op and `_on_error`'s branch is unreachable (`S40`/`S41`) |
| The chain's three emitters live **only** in `ibkr/client.py` | `orderStatus` (:394, emits at :405), `openOrder` (:410, emits :412), `execDetails` (:414, emits :416) | `S43` rule 2: the override and its signal are deleted in **one** task (wave 2) |
| The three signals have **exactly three receivers**, all in `MainWindow.__init__` | `ui/main_window.py:595`–`:597` — `b.open_order` / `b.exec_details` / `b.order_status`; a `tests/`-wide grep finds no other driver | `S43` rule 3: connects + slots leave **first** (wave 1); three zero-receiver signals are harmless and the app still constructs |
| `_on_order_error` has **one** caller | `ui/main_window.py:1547`, inside the `order_registry.get(reqId) is not None` branch (:1546) | wave 1 deletes branch + handler + `_update_order_status` + import as one unit |
| `_update_order_status` has **exactly three** callers | the three slots (`:2952`, `:2957`, `:2965`), all deleted in the same wave | no orphan remains after wave 1 |
| **What the owner sees today is already the generic line** | `IBApiClient.error` emits `error_msg` unless `classify_error` returns `'info'`; `classify_error(201) == classify_error(103) == 'fatal'`, `(202) == 'warning'`; `_on_error` falls through to `showMessage(f"Error [{code}]: {string}", 8000)` | `S41`/`AC-D46.3`: the deletion changes **nothing user-visible**; the positive per-code test pins it |
| `data/models.py::UserOrder` has **zero** consumers | its only reference in the tree is `tests/test_ui_smoke.py:48` (`hasattr`); `data/models.py`'s `dataclass`/`field` imports stay live (`Study` uses `field(default_factory=dict)`) | `S42`: delete the class and the assertion **in one task** |
| The removal guard references the chain in **three** places | `tests/test_d45_removal.py:22` (docstring bullet: "an `_on_order_error` emission"), `:145`–`:147` (`_SURVIVORS`), `:523` (`win._on_order_error(1, 201, …)`) | `S44` + `S43` rule 5: `:523` must be repointed to `_on_error` **in the wave that deletes the handler** (wave 1), or the walkthrough raises `AttributeError` |
| The seven non-`orders` order names occur **4 · 6 · 2 · 2 · 2 · 2 · 4** times in the scanned tree | `order_registry` 4 lines · `UserOrder` 6 · `_on_open_order` 2 · `_on_order_status` 2 · `_on_exec_details` 2 · `_on_order_error` 2 · `_update_order_status` 4 — **all** inside files P5 edits or deletes ⇒ zero post-P5 hits | `R79`: the allow-list→forbidden migration is discriminating by construction (counted 2026-10-25) |
| The bare name `orders` appears on **5 scanned units as a substring (2 as an exact unit), every one inside a file this phase edits or deletes**, and **the exact-match set is no longer needed to keep any surviving file green** | `ui/main_window.py:36` (import, wave 1), `ibkr/id_manager.py:22` (inside `reserve`'s docstring — **`reserve` is deleted in wave 6**), `ibkr/orders.py:136` ("…all tracked orders.") / `:141` (`orders = Orders()`) / `_orders` (all deleted, wave 3) — counted 2026-10-25 | `S44`: `orders` stays **exact-matched**, but on a **new** ground (prose safety) — revision 1's ground ("a file no task may edit") is **void**, because `ibkr/id_manager.py`'s docstring dies with `reserve` |
| The class name `Orders` appears on **2 scanned units as a substring (1 as an exact unit), all inside deleted code**, plus one comment | `ibkr/orders.py:27` (`class Orders:`) / `:141` (both deleted, wave 3); `ibkr/pacing.py:131` (a **docstring** inside `class OrderRateLimiter` — **the class is deleted in wave 4**); `ibkr/bridge.py:42` (`# Account & Orders`, a **comment**: invisible to both nets, and the header for the **retained** account signals) | `S44`: same correction as `orders` — exact matching is kept for prose safety, **not** to protect `pacing.py`, which is now **edited**; the `bridge.py:42` comment is **kept** and is not an offence |
| **`IdManager` is shared, not order-only — the module must stay** | `get_id()` at `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31` **and `ui/main_window.py:1095`** (a sixth caller the register's list omits); `set_next_valid_id()` at `ibkr/client.py:184`; only `reserve()` (`:19`–`:30`, with its `:22` docstring) is order-motivated | `S46`/A101: the module and `get_id` are frozen; deleting the module would take the chart's subscription machinery with it |
| `tests/test_id_manager.py` has **8** cases, **6** of which touch `reserve` | `:10`, `:18`, `:32`, `:39`, `:56`, and — **not named by the register** — `:74` `test_concurrent_allocations_never_duplicate`, which calls `mgr.reserve(3)` at `:85` and asserts `len(seen) == 8 * 203` at `:97` | `AC-D46.10`'s "keeps … test_concurrent_allocations_never_duplicate" is **wrong**: it must be rewritten. **Flagged Issue 1**; the plan rewrites six of eight and lands **8 → 4** |
| `tests/test_sound_service.py` has **four** sites on the fill path, not two | the imports (`:9`, `:15`), `TestFillBlip` (`:43`–`:51`, 2 cases), `TestWavOutput::test_write_wav_is_valid_pcm16` (`:57`), **and `TestEnsureSoundFiles::test_creates_both_files_once`'s `paths["fill"]` assertion (`:76`)** — a `KeyError` once the `"fill"` key goes | `D46.5`'s book under-lists the file. **Flagged Issue 2**; **8 cases → 6** |
| `SoundService._effect` names `_fill_effect` **in a string constant** | `services/sound_service.py:151` — `attr = "_alarm_effect" if key == "alarm" else "_fill_effect"` | the AST scan sees string constants, so the accessor must **collapse to alarm-only** or the guard stays red on a member this phase deletes. Measured: the simulated post-P5 tree only reached 0 after the collapse |
| The removal instrument is **discriminating**, with the revision-2 token set | pre-P5: **41 AST offences across 10 files** (`ui/main_window.py` 14, `ibkr/orders` 7, `services/sound_service.py` 5, `data/models.py` 3, `ibkr/bridge.py` 3, `ibkr/client.py` 3, `ibkr/account.py` 2, `ibkr/pacing.py` 2, `data/db.py` 1, `config/settings.py` 1) and **40 twin hits, all `ui/main_window.py`** (`:36`, `:595`–`:597`, `:1546`–`:1551`, `:1559`, `:2951`–`:2965`, `:3093`–`:3094`, `:3133`–`:3134`, `:3164`–`:3165`, `:3186`, `:3198`–`:3199`, `:3216`–`:3217`, `:3226`–`:3227`) | every one of those lines is inside a region this phase deletes or edits; **a simulated post-P5 copy scores 0 / 0** (measured, not assumed) |
| SQLite is **3.53.1** in the app's interpreter, not 3.54.0 | `.venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"` → `3.53.1`; the system `python3` → `3.54.0`. `DROP COLUMN` needs ≥ 3.35 | `D46.12` cites the wrong interpreter; the capability claim still holds. **Flagged Issue 3** |
| A **legacy** `positions`/`trade_groups` migrates cleanly in place | probe in `.venv` 2026-10-25: rows 3/1 preserved, `sqlite_sequence` 3→3, `idx_positions_symbol_con_id` intact and still enforcing `UNIQUE`, `foreign_key_list` → `trade_group_id → trade_groups.id`, `foreign_key_check` empty, `integrity_check` ok, the 13-column upsert + `RETURNING id` works, second open no-op | `S47`: `DROP COLUMN` is the mechanism; the row/index/FK preservation is measured, not asserted |
| `usage.md:167` names a test file P5 deletes | the "Phase 10 core logic tests" command lists `tests/test_order_builders.py` | A98's "no user-facing doc change expected" is **incomplete** — one line is corrected (plan `AP-D46-9`); `USAGE.txt:84`–`:93` already states the end state ("the app places, cancels and closes nothing… IBKR rejections and cancellations appear in the status bar together with TWS's message") and needs **no** change |

#### Data models / persisted state

- **`positions`** — `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier,
  expiry, strike, right, trade_group_id, updated_at` **after** this phase (15 → 13 columns): `stop_loss`
  and `take_profit` are **dropped by the migration** (`S47`). Every row, `idx_positions_symbol_con_id` and the
  `trade_group_id` FK survive (measured); the two columns' values are lost. **The honest statement of what that
  costs:** a row that receives another live update has its values **cleared first** (ESC-060), so for those rows the
  drop destroys nothing; a row that never updates again (a symbol no longer held or not streamed) **keeps its legacy
  stop/target bytes** and loses them here. That makes this drop the batch's **only byte-destroying step** — it is still
  defensible (the values are invisible, unsettable and unsupported), but it is not the cost-free delete the code groups
  are, and `D46.12`'s row-preservation requirement is what keeps it bounded.
- **`trade_groups`** — `id, name, strategy_type, underlying, collapsed, created_at` after the same migration.
  `strategy_type`/`collapsed`/`created_at` untouched — the strategy grouping is intact.
- **`data/models.py`** — `Bar`, `Alarm`, `Study`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup` **stay**;
  `Position`/`TradeGroup` lose `stop_loss`/`take_profit`, and `UserOrder` **goes** (`S42`).
  **One destructive schema step, no new key, no new table.**
- **`ibkr/account.py::Position`** — a **third** copy of the row; loses the two fields and
  `build_position_from_ib`'s two parameters.
- **In-memory only, removed with the module:** `ibkr/orders.py::Orders._orders` — the registry nothing populated.

#### Major components and responsibilities (post-P5 target; deltas in the next tables)

`ui/main_window.py` (window, docks, toolbar, load path, sessions, error routing, persistence, teardown) ·
`ui/ticker_session.py` (per-symbol sessions: bars, waves, pacing, live bars, S0 substrate — **untouched**) ·
`ui/active_portfolio_panel.py` (view-only Portfolio, 8 columns — **untouched**) · `ui/chart_panel.py` +
`ui/candlestick_item.py` + `ui/overlays/*` + `ui/event_marker_overlay.py` (render stack — **untouched**) ·
`ui/watchlist_panel.py` + `ui/dock_layout.py` (**untouched**) · `services/*` (**untouched except the order-fill
half of `sound_service.py`**) · `data/*` (SQLite, cache, aggregator, stores, event provider — **`db.py`'s schema
drops four columns**, `models.py` loses one class and four fields) · `ibkr/*` (client wrapper, bridge, market data,
RT bars, pacing **minus the order bucket**, id manager **minus `reserve`**, subscriptions, stream health, account
**minus the two fields**, contracts, error codes, **news/validation already deleted by D45**, **orders deleted by
P5**).

#### Key entry points / data flow

`main.py` → `MainWindow()` → `IBApiClient.connect` (fail-fast port check) → bridge signals → sessions/chart;
account-summary + position callbacks → `_on_position_update` → `_upsert_position` (**13 columns**) →
`ActivePortfolioPanel.set_positions`/`add_position` → `_group_and_render` → `_render_table` (8 columns); the bulk
path `position_end` → `_on_position_end` (**13-column SELECT, read by name**). **P5 removes one inbound branch** —
the order-lifecycle callbacks (`openOrder`/`orderStatus`/`execDetails` → three signals → three slots) — **one
outbound response** (the order-error branch in `_on_error`) and **two stored columns** from that position flow.
Nothing else on this flow changes; errors continue to arrive on `error_msg` → `_on_error` → status bar.

#### External integrations already in use `[existing]`

IBKR TWS via the official `ibapi` (`10.51.1`): historical + realtime bars, market data with S0 generic ticks,
account summary/positions, dividends tick `"456"`/59 (**retained**; news `"292"`/news API already removed by D45),
**error callbacks (retained — the sole TWS-error surface)**, order lifecycle callbacks (**no longer overridden or
observed**); `placeOrder`/`cancelOrder`/`reqGlobalCancel` inherited from `EClient` and **called nowhere** (D45's
zero-transmit invariant stands, now enforced from the guard's forbidden set); yfinance as the sole approved
secondary event source (**retained**); SQLite (**retained, one guarded destructive migration**); Qt `QSettings`
(**retained**).

#### What P5 changes, in one line

One module deleted (`ibkr/orders`); **eleven** production modules touched — ten edited (`ui/main_window.py`,
`ibkr/client.py`, `ibkr/bridge.py`, `data/models.py`, `data/db.py`, `ibkr/account.py`, `ibkr/pacing.py`,
`config/settings.py`, `services/sound_service.py`, `ibkr/id_manager.py`) and one **comment-only**
(`ibkr/error_codes.py`); **two** suites deleted (`test_order_builders`, `test_stop_loss_target`) and **thirteen**
files adjusted; two user-facing docs corrected and the Plan-owned map refreshed; **no file added**.

---

### Summary (P5)

P5 is a **subtractive** increment with an **inertness** requirement and, for the first time in this project, **one
destructive schema step**. The owner asked why any order code remains after D45 removed every order interaction, and
the honest answer is that a module with no caller, a chain that writes into a registry nothing populates, three
utilities with no reader, one allocator method with only tests, and four columns nothing could write, display or reach
were all kept by decisions that were never audited for reachability. The architecture adds nothing: it **severs the chain at
its three seams** (window consumers → broker boundary → module) in an order dictated by the callback graph, deletes
the zero-consumer utilities and the unused allocator method, **drops the four columns with four guarded in-place
`ALTER TABLE … DROP COLUMN` statements that preserve every row, the unique index and the FK**, and **freezes the
whole generic error path** so TWS visibility survives exactly as the owner sees it today. The guarantee is
structural — the tree holds no order code and the schema holds no stop/target column, so there is nothing to re-wire
by accident — and it is verified by migrating the existing removal guard rather than by adding a new one, with the
token list landing only when every token names code that is already gone.

### Tech Stack Decisions (P5)

**Constrained choices first** — the existing stack; P5 changes none of it (no requirement asks for a stack
change, and pyqtgraph is a **locked** decision, `docs/memory.md` 2026-10-16).

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| UI toolkit `[existing]` | **PyQt6** (widgets, signals, docks) | The app is PyQt6; P5 only deletes a signal group and its receivers | — (no change proposed) |
| Broker client `[existing]` | official **`ibapi`** (`10.51.1.post1`) via `IBApiClient(EWrapper, EClient)` | The three order callbacks are **inherited** `EWrapper` no-ops; deleting our overrides returns them to the base behaviour, which is the correct end state | Writing an in-repo no-op override "to keep the callback" — rejected: that is the fossil being removed |
| Persistence `[existing]` | **SQLite** (`data/db.py`); additive migrations **plus one guarded in-place column drop** | `DROP COLUMN` is available (3.53.1) and was **measured** to preserve rows, `sqlite_sequence`, the unique index and the FK | The `bars`-style rebuild (rejected: four statements per table, manual index/FK recreation, a salvage branch per table); a whole-file copy before migrating (rejected: new launch behaviour, no row-copy step to interrupt — the row-preservation assertion is the real proof) |
| Chart renderer / secondary source `[existing]` | **pyqtgraph** (locked) / **yfinance** | Untouched by P5 | — (do not re-propose) |
| Removal mechanism `[new in P5]` | **Delete each member group at its own seam** (ten waves); keep the error path frozen | Each group's only effect is a write into something nothing reads; deletion makes a future re-wire fail a test rather than a review | Keep the observers wired against a re-written registry (rejected — inventing a consumer for a module the owner asked to remove); keep the module as a dormant helper (rejected by A91) |
| Migration placement `[new in P5]` | Inside `_migrate_schema()`, guarded by `_table_columns()`, **after** the unique-index statement | The guard makes a fresh DB and every later open no-ops (idempotent by construction); placing it after the index keeps that index valid across the table rewrite | A separate `_migrate_d46()` method (rejected: the file has one migration entry point and every prior step lives in it — a second entry point is a second ordering question) |
| Index-shift mechanism `[new in P5]` | Per-cursor `sqlite3.Row` at the one reshaped SELECT; read `row["trade_group_id"]` | DG85's recommendation; makes the shift impossible rather than corrected | Positional `row[12]` (rejected: correct today, same bug class tomorrow) |
| Verification mechanism `[extends P4: S36]` | The **existing** `tests/test_d45_removal` (AST identifiers + string constants over the five source dirs; `ui/`-only grep twin; `find_spec`/`hasattr`/`__dict__`/`_table_columns`; mocked-client walkthrough) with `_FORBIDDEN` **53 → 80**, `_SURVIVORS` **26 → 16**, `_DELETED_MODULES`/`_DELETED_SUITES` extended, a positive per-code surfacing case, and **the schema end state** | One instrument, one token list — the grep step and the test cannot drift apart; no new dependency; `tests/test_d41_removal.py` is the precedent | A new `tests/test_d46_removal` (rejected: duplicates the same scans and creates a second list to keep in sync — the register's A95 keeps the rejection test file for the same reason) |
| Test runner `[existing]` | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` | Repo convention (stale `pytest` shebang) | — |
| New dependencies `[new in P5]` | **None** | Constraint; nothing in a deletion needs one | — |

### System Components (P5)

Status is relative to the codebase: `[existing]` = present and **unmodified**; `[new/changed]` = present and
modified; `[deleted]` = removed by this phase with nothing replacing it.

**Changed by this phase**

| Component | Status | What changes |
|---|---|---|
| `ui/main_window.py` | **`[new/changed]`** | **Wave 1, one task:** the three `b.open_order` / `b.exec_details` / `b.order_status` `.connect` lines (`:595`–`:597`); `_on_open_order`, `_on_exec_details`, `_on_order_status` (`:2951`–`:2965`); `_update_order_status` (`:3226`–`:3229`); `_on_order_error` (`:1551`–`:1560`); `_on_error`'s D26.9 comment + `order_registry.get(reqId)` branch + its `return` (`:1543`–`:1548`); and the `from ibkr.orders import orders as order_registry` line (`:36`). **Retained byte-for-byte:** `_on_error`'s `_closing` guard, its session-reqId branch (RT vs historical), and its final `self.status_bar.showMessage(f"Error [{errorCode}]: {errorString}", 8000)`; `b.error_msg.connect(self._on_error)`; `_symbol_last_prices`, `_upsert_position`, `_on_position_end`, the fail-fast connect path, the badges, `closeEvent`. |
| `ibkr/client.py` | **`[new/changed]`** | The `orderStatus` (`:394`–`:407`), `openOrder` (`:410`–`:412`) and `execDetails` (`:414`–`:416`) `EWrapper` overrides are deleted whole (with their `super()` calls and comments). **Nothing else in the file changes** — `_do_reconnect`, `connected`, the lifecycle callbacks, and `error` (the D40.1 suppression and the `severity != 'info'` gate) stay **verbatim**. After this, `IBApiClient` defines **no** `orderStatus`/`openOrder`/`execDetails`; the inherited `EWrapper` no-ops are what TWS reaches. Measured as **`"orderStatus" not in IBApiClient.__dict__`** (and the other two) — `hasattr` stays `True` through inheritance before *and* after, so it cannot be the measurable (`AP-D46-14`). |
| `ibkr/bridge.py` | **`[new/changed]`** | The `order_status`, `open_order` and `exec_details` `pyqtSignal`s (`:47`, `:51`, `:54`) and their two comment blocks are deleted. Every other signal stays, including the news-boundary mirrors (D45 `S35`) and `error_msg`. |
| `data/models.py` | **`[new/changed]` (two waves)** | **Wave 3:** the `UserOrder` dataclass (`:104`–`:116`) is deleted. **Wave 7:** `Position.stop_loss`/`take_profit` (`:86`–`:87`) and `TradeGroup.stop_loss`/`take_profit` (`:98`–`:99`) are deleted. `dataclass`/`field` stay (used by `Study`); every other dataclass untouched. |
| `data/db.py` | **`[new/changed]`** | Four DDL lines removed (`positions` `:120`–`:121`, `trade_groups` `:130`–`:131`) and one guarded migration block added to `_migrate_schema()` **immediately after** the `idx_positions_symbol_con_id` statement (`S47`): for each table, `_table_columns(table)` once, then drop `stop_loss`/`take_profit` when present. `_table_columns` and every other table/index/migration untouched. |
| `ibkr/account.py` | **`[new/changed]`** | `Position.stop_loss`/`take_profit` (`:32`–`:33`), `build_position_from_ib`'s two parameters (`:64`–`:65`) and its two kwargs (`:79`–`:80`) deleted; the `Position.id` comment (`:40`–`:43`) reworded to justify `id` by strategy grouping only (**`ESC-062`**). The `ESC-044` field mapping, `_parse_contract_type` and `Account` untouched. |
| `ibkr/pacing.py` | **`[new/changed]`** | `OrderRateLimiter` (`:128`–`:170`) and `order_limiter` (`:172`) deleted; the `# Global singletons` comment becomes `# Global singleton`. `PacingManager`, `PacingExceeded`, `pacing_manager` and `reset_for_tests` untouched. |
| `config/settings.py` | **`[new/changed]`** | `MAX_ORDER_NOTIONAL` (`:37`–`:39`) and its two-line `validate_order()` comment deleted. Every other constant untouched. |
| `services/sound_service.py` | **`[new/changed]`** | The docstring bullet (`:9`), `BLIP_DURATION` (`:22`), `render_fill_blip` (`:75`–`:83`), `blip_path`/`order_fill.wav` and the `"fill"` key (`:118`, `:121`–`:123`), `_fill_effect` (`:135`), **`_effect` collapsed to alarm-only** (`:148`–`:158` — its ternary names `"_fill_effect"` in a **string constant**, which the AST scan sees) and `play_fill` (`:170`–`:175`) deleted. `play_alarm`, `render_alarm_chime`, `ALARM_DURATION`, the `"alarm"` key and `warm` untouched (`AC-D46.11`). |
| `ibkr/id_manager.py` | **`[new/changed]`** | `IdManager.reserve` (`:19`–`:30`) and its D26.2 docstring deleted. `IdManager`, `set_next_valid_id`, `get_id`, `id_manager` untouched and still called from `ui/main_window.py:1095`, `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`, `ibkr/client.py:184`. |
| `ibkr/error_codes.py` | **`[new/changed]` (comment only)** | In `classify_error`, the clause "…`_on_error` still routes it to the registry as Cancelled." is replaced by the post-P5 truth (a cancellation is a normal lifecycle event; `severity != 'info'` is what lets 202 reach the status bar). **No code line, no return value, no threshold changes** (`S46`). |
| `tests/test_order_rejections.py` | **`[new/changed]`** | The two registry cases and their `_fresh_registry`/`_register` helpers and `from ibkr.orders import …` are removed; `test_non_order_error_untouched` is repointed (and renamed) to assert the **generic** line for an unrelated code; both `classify_error` cases stay; **one** parametrised case over `201 / 103 / 202` is added (`AC-D46.3`). Module docstring rewritten — it names `_on_order_error`. |
| `tests/test_d45_removal.py` | **`[new/changed]` (two waves)** | **Wave 1:** the walkthrough's `win._on_order_error(…)` call (`:523`) and the docstring bullet (`:22`) are repointed at `win._on_error(…)`. **Wave 8, one coherent edit (invariant I-1):** the **ten** names leave `_SURVIVORS` (`order_registry`, `orders`, `UserOrder`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `order_limiter`, `MAX_ORDER_NOTIONAL` — `classify_error`, `pacing_manager`, `PacingExceeded` stay); `_FORBIDDEN` **53 → 80** (`orders`/`Orders` exact-matched, the other 25 new tokens substring); `_DELETED_MODULES` += `ibkr.orders`; `_DELETED_SUITES` += the builders and stop-target suites; a new end-state test asserts the five window members and three bridge signals by `hasattr`, the three client overrides by **`__dict__` membership**, `find_spec("ibkr.orders") is None`, the module/builder/stop-target files absent, `data.models.UserOrder` absent, `hasattr(IdManager, "reserve") is False`, member absence in `ibkr.pacing`/`config.settings`/`services.sound_service`, the four model fields absent in all three classes, `build_position_from_ib`'s signature, and **the schema end state** (fresh + legacy fixture + second open). The guard's **own** prose is corrected in the same edit (it documents the D45 retention this phase forbids). |
| `tests/test_account.py`, `tests/test_strategy_detection.py` | **`[new/changed]`** | Four `build_position_from_ib` calls lose the two kwargs and two asserts go (`:36`–`:37`, `:62`–`:63`, `:85`–`:86`, `:103`–`:104`, `:108`–`:109`); `_pos()`'s two `Position(...)` kwargs (`:30`–`:31`) go. Nothing else. |
| `tests/test_d27_position_id.py`, `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py` | **`[new/changed]`** | The three raw-SQL seeders lose the two column names and one placeholder each (`test_d27_position_id` `:97`–`:103`; the other two `:66`–`:72`). `test_d27_position_id` gains **one** case that seeds a non-null `trade_group_id` and asserts it survives the bulk load (`S48`) — the only guard against the silent index shift. |
| `tests/conftest.py`, `tests/test_d28_pacing.py` | **`[new/changed]`** | The two `pacing_mod.order_limiter.reset_for_tests()` lines (`:143`, `:146`) and the fixture docstring's "and a full order-token bucket" clause removed; the `OrderRateLimiter` import (`:14`) and `test_order_limiter_allows_burst_then_denies` (`:97`–`:101`) removed; the pacing module docstring's order-bucket sentence rewritten. Every pacing case stays. |
| `tests/test_sound_service.py`, `tests/test_id_manager.py` | **`[new/changed]`** | Sound: imports (`:9`, `:15`), `TestFillBlip` (`:43`–`:51`) and the `paths["fill"]` assertion (`:76`) removed; `:57` switches to `render_alarm_chime()`; the "both files" case renamed. **9 cases → 7** (executed: `--collect-only` reports 9 today; only `TestFillBlip`'s 2 go). IdManager: four pure `reserve` cases deleted, the monotonic case rewritten (renamed), and **`test_concurrent_allocations_never_duplicate` rewritten** (`:85`–`:86` out, `8 * 203` → `8 * 200`); the module docstring's bracket-order sentence removed. **8 cases → 4.** |
| `tests/test_dock_d18_region.py` | **`[new/changed]`** | `test_T48_T03_panel_present_and_signals_wired` renamed for what it now asserts, its "MainWindow consumes their effect via other slots" comment corrected, and `_receiver_count`'s docstring `>= 1` caller sentence corrected (**`ESC-062` item 5**). No assertion changes. |
| `tests/test_ui_smoke.py` | **`[new/changed]`** | The `assert hasattr(data.models, "UserOrder")` line only; `Position` and `Drawing` stay asserted, the module imports are untouched. |
| `docs/codebase-map.md` | **`[new/changed]` (Plan-owned, this phase)** | Refreshed **in this draft**: the `ibkr/orders.py` retention claim and the "retained observers" block replaced by the post-P5 target; the D45 book arithmetic corrected (`ESC-063`); the pointer sentences moved off the superseded D45 proposal drafts; the P5 touch summary and test-impact rows added. Not a Build task. |

**Deleted by this phase (nothing replaces them)**

| Module / file | Status | Reason |
|---|---|---|
| `ibkr/orders` (`UserOrder`, `Orders`, the four builders, the registry, the `orders` singleton) | **`[deleted]`** | `S39` / A91 / `AC-D46.1` — no production caller, a registry nothing writes, and the owner's explicit ask |
| `ibkr/client.py`'s three order `EWrapper` overrides | **`[deleted]`** | `S40` — the emitters of a chain with no consumer |
| `ibkr/bridge.py`'s three order signals | **`[deleted]`** | `S40` — the channel, removed with its only emitter (wave 2) and after its only receiver (wave 1) |
| `MainWindow`'s five order members + `_on_order_error` + the `_on_error` registry branch + the import | **`[deleted]`** | `S40`/`S41` — the consumers, removed first |
| `data.models.UserOrder` | **`[deleted]`** | `S42` / A96 — a second, unused order dataclass |
| `ibkr.pacing.OrderRateLimiter` + `order_limiter` · `config.settings.MAX_ORDER_NOTIONAL` | **`[deleted]`** | `D46.11` — zero production readers; the notional cap's gate died in D45 |
| `services.sound_service`'s order-fill path (`render_fill_blip`, `BLIP_DURATION`, `_fill_effect`, `play_fill`, the `"fill"` key, `order_fill.wav`) | **`[deleted]`** | `D46.11` — `play_fill` has zero callers; there is no order to fill. The **alarm** chime stays |
| `IdManager.reserve` | **`[deleted]`** | `D46.10`/A101 — tests only; the module and `get_id` stay |
| `tests/test_order_builders.py` (17 cases) · `tests/test_stop_loss_target.py` (3 cases) | **`[deleted]`** | Their whole subject is gone; the loss is stated in the plan's test book, not hidden (R80/A104) |

**Untouched by this phase (deliberately, `S46`):** the chart render stack, `ui/ticker_session.py`,
`ui/active_portfolio_panel.py` (still 8 columns), `ui/watchlist_panel.py`, `ui/dock_layout.py`, `services/*` except
the order-fill half of `sound_service.py`, `data/bar_cache.py`, `data/events/*`, `ibkr/market_data.py`,
`ibkr/realtime_bars.py`, `ibkr/subscription_manager.py`, `ibkr/stream_health.py`, `ibkr/contracts.py`,
`ibkr/utils.py`, `config/paths.py`, `main.py`, `tests/test_d40_tws_lifecycle.py`, `tests/test_port_guard.py`,
`tests/test_d41_removal.py`, `tests/test_db_schema.py`, and every test file not named above.

### Data Model (P5)

**This phase changes the schema — the project's first destructive step (`A99`, reversing A87).** The end state is
`D46.12`'s; the mechanism is `S47`'s and is measured, not asserted.

| Entity | Status | Key fields | P5 effect |
|---|---|---|---|
| `positions` (SQLite) | **`[new/changed]`** | `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier, expiry, strike, right, trade_group_id, updated_at` | Two columns dropped by guarded `ALTER TABLE … DROP COLUMN`; **every row preserved**, `idx_positions_symbol_con_id` and the `trade_group_id` FK preserved, `sqlite_sequence` preserved (ids never reissued). A fresh DB is created without them and the migration no-ops |
| `trade_groups` (SQLite) | **`[new/changed]`** | `id, name, strategy_type, underlying, collapsed, created_at` | Same mechanism; every row preserved. `strategy_type`/`collapsed`/`created_at` untouched — the strategy grouping is intact |
| `data.models.Position` / `TradeGroup` | **`[new/changed]`** | minus `stop_loss`, `take_profit` | Fields deleted; every other field (incl. `trade_group_id`, `id`) unchanged |
| `ibkr.account.Position` + `build_position_from_ib` | **`[new/changed]`** | minus `stop_loss`, `take_profit` (fields **and** the two factory parameters) | Third copy of the row loses the same two; the remaining parameters and `_parse_contract_type` untouched |
| `data.models.UserOrder` | **`[deleted]`** | `order_id, symbol, action, total_qty, order_type, lmt_price, aux_price, status, parent_id, oca_group, transmit` | removed with the smoke assertion (`S42`, `AC-D46.8`) — **zero** consumers |
| `ibkr.orders.UserOrder` + `Orders._orders` | **`[deleted]`** | the module's own copy + the in-memory registry | gone with the module; **no persisted state was ever involved** |
| `MainWindow._symbol_last_prices` | `[existing]` | reqId → last price; read by the Portfolio P/L path | **none** — it is *not* order state and must not be touched (`AP-D45-2` precedent) |
| `MainWindow._upsert_position` / `_on_position_end` | **`[new/changed]`** | `INSERT … ON CONFLICT(symbol, con_id) DO UPDATE … RETURNING id` over **13** columns; the bulk SELECT over the same 13 | Both keep working on the new shape (measured, incl. `RETURNING id` on the DO UPDATE branch) |

Relationships unchanged: `positions.trade_group_id → trade_groups.id`; `position_group_map`; strategy/group
derivation via `services.strategy_detection.detect_and_group`. **No new entity, no new key, no new table, no new
column.**

**What happens to a database at each age (the answer `D46.12` asks for):**

| DB state | First open after P5 | Every later open |
|---|---|---|
| **Fresh** (created by this build) | `CREATE TABLE IF NOT EXISTS` already omits the four columns ⇒ all four `DROP` statements are skipped by the `_table_columns()` guard; nothing raises | No-op |
| **Pre-P5** (columns present, any legacy values) | The four statements run once; rows, `sqlite_sequence`, the unique index and the FK survive (measured); the two columns' values are lost: rows that receive another live update had them cleared first (ESC-060), while a row that never updates again **keeps its legacy bytes and loses them here** — the batch's only byte-destroying step, bounded by the row-preservation requirement | Guard sees no columns ⇒ no-op |
| **Interrupted mid-migration** (crash between two statements) | Only the columns not yet dropped remain (each `DROP` is one atomic, autocommitted DDL statement — measured in `.venv`), so there is no half-built table to salvage and the guard finishes the remainder | No-op once complete |

### Integration Points (P5)

| Integration | Status | Why it is needed / what changes |
|---|---|---|
| **IBKR TWS** — historical + realtime bars, market data, account summary/positions (`ibapi` over the local socket, port `7496`, fail-fast check) | `[existing]` | The app's whole data plane; **unchanged**. |
| **IBKR error callbacks** (`error` → `error_msg` → `_on_error`) | `[existing]` **frozen** | The **only** remaining TWS-error surface and the owner's constraint: 201/103/202 reach the status bar here (`AC-D46.3`). `classify_error`'s gate and the D40.1 `502` suppression are untouched. |
| **IBKR order-lifecycle callbacks** (`openOrder`, `orderStatus`, `execDetails`) | **`[new/changed]` → removed** | No override, no signal, no slot, no registry. `ibapi` still invokes the **inherited** `EWrapper` no-ops; the app observes nothing (`D46.2`). |
| **IBKR order transmit / cancel** (`EClient.placeOrder` / `cancelOrder` / `reqGlobalCancel`) | `[existing]`, **unreachable** | D45's zero-call invariant stands and is made stronger: the names move from the guard's allow-list to its forbidden set (`AC-D46.4`). No definition may be added to `ibkr/client.py`. |
| **IBKR S0 generic tick `"456"`** (+ tick 59) → dividend markers | `[existing]` | Retained verbatim (`AC-D45.2`/R68); P5 does not touch `ui/ticker_session.py`. |
| **IBKR news API / tick `"292"`** | **already removed (D45)** | Nothing to do here; the bridge's news **signals** stay as the ibapi boundary mirror (D45 `S35`), untouched by P5. |
| **yfinance** corporate-events provider | `[existing]` | Sole approved secondary source; **untouched**. |
| **SQLite** (`data/db.py`) | **`[new/changed]`** | One guarded destructive migration, run at `DB()` construction (`S47`); no new file, no new dependency, no new connection. Every other table/index/migration untouched |
| **Qt `QSettings`** (watchlist width/columns) | `[existing]` | Untouched; no layout key ever bound to the removed chain. |
| *New integrations* | — | **None.** No endpoint, no dependency, no credential. |

### Frozen Interfaces (P5)

Interfaces this phase treats as **read-only**: `[existing]` contracts that **no** P5 task modifies. Contracts are
**verbatim** from the tree (never paraphrased), with the owning module, so Task Manager hands a worker the
contract instead of the implementation. **Nothing under construction is listed**: the five window members, the
three signals, the three overrides, the `_on_error` registry branch and `ibkr/orders.py` itself are **being
deleted**, and `_on_error`'s body is edited in wave 1 (its surviving contract is pinned in the plan's per-file
map, not frozen here). D45's frozen rows *Order registry API* and *Inert inbound observers* are **void** —
recorded in § *Supersessions*. One row is a **scope contract, not a file**: *Removal guard scope* freezes the three
instruments' scope **split**, while `tests/test_d45_removal.py` — the module that implements it — **is** edited by
waves 1 and 8. That is deliberate and consistent: the split must not move while the token lists and the absence
test do.

| Interface | Verbatim contract | Owning module |
|---|---|---|
| Error classification `[existing]` | `def classify_error(error_code: int) -> str:` — returns `'info'` for `(2104, 2106, 2158)`; `'warning'` for `(2103, 2105, 2108)`; `'fatal'` for `(504, 200, 399, 100, 162)`; `'fatal'` for `(201, 103, 1100, 502, 503, 509)`; `'warning'` otherwise. **Code frozen; only the 202 comment line is reworded.** | `ibkr/error_codes.py` |
| Error ingress `[existing]` | `def error(self, *args, **kwargs):` — normalises the three TWS signatures, calls `super().error(...)`, then `severity = classify_error(errorCode)`; **D40.1**: returns early (debug log) when `errorCode == 502 and self._last_disconnect_class == DisconnectClass.TWS_GONE and not self._connected`; else `if severity != 'info': self.bridge.error_msg.emit(reqId, errorCode, errorString)` | `ibkr/client.py` |
| Error signal `[existing]` | `error_msg = pyqtSignal(int, int, str)           # reqId, errorCode, errorString` | `ibkr/bridge.py` |
| Window error routing `[existing]` | `b.error_msg.connect(self._on_error)` (the connection is frozen; `_on_error`'s call contract is `(self, reqId: int, errorCode: int, errorString: str)` and it is **under construction** in wave 1) | `ui/main_window.py` |
| Historical-error hand-off `[existing]` | `def on_historical_error(self, req_id: int, code: int, msg: str) -> None:` — the **retained** session branch of `_on_error` calls `session.on_historical_error(reqId, errorCode, errorString)` immediately before the duplicate 8000 ms line; wave 1 must leave the call **and** this method untouched | `ui/ticker_session.py` |
| Realtime-stream error hand-off `[existing]` | `def _on_rt_stream_error(self, session: TickerSession, code: int, message: str) -> None:` — the **retained** RT branch of `_on_error` calls it when `reqId == session.rt_req_id`; it owns the 15 s `Realtime stream failed [<code>]: <message> — retrying…` line, the stream badge and the retry schedule; untouched by wave 1 | `ui/main_window.py` |
| Broker boundary `[existing]` | `class IBApiClient(EWrapper, EClient):` — `EClient.__init__(self, self)`, remembered connect params for the D27.3 reconnect (`_do_reconnect` re-issues the real `EClient.connect`), `def connected(self)`, the bridge instance. **No `placeOrder` / `cancelOrder` / `reqGlobalCancel` definition may exist here** (all inherited from `EClient`; the three *order-lifecycle* overrides are deleted in wave 2) | `ibkr/client.py` |
| Fail-fast port check `[existing]` | `def check_live_port() -> None:` — raises `SystemExit` with a human-readable message unless `IBKR_PORT == LIVE_PORT` | `config/settings.py` |
| ReqId allocation `[existing]` | `class IdManager:` — `def set_next_valid_id(self, order_id: int):` · `def get_id(self) -> int:` (+ the global `id_manager` singleton). **`reserve` is deleted; every other member is frozen** and must keep serving `ui/main_window.py`, `ibkr/market_data.py`, `ibkr/realtime_bars.py` | `ibkr/id_manager.py` |
| Connection transition `[existing]` | `def nextValidId(self, orderId: int):` — `super().nextValidId(orderId)`; `id_manager.set_next_valid_id(orderId)`; then the CONNECTED transition (`_connected = True`, `_reconnect_attempt = 0`, `_last_disconnect_class = None`, `_set_state(ConnectionState.CONNECTED)`). **Retained** (A102/DG82): the only reconnect-success hook, and its name is `EWrapper`'s. Only order-worded **comments** may be reworded | `ibkr/client.py` |
| Alarm tone `[existing]` | `def render_alarm_chime() -> np.ndarray:` · `ALARM_DURATION` · `ensure_sound_files(directory) -> dict` returning the `"alarm"` key · `SoundService.play_alarm(self) -> None:`. **The order-fill half beside it is deleted; the alarm path is frozen and must keep playing** (the D21 alarm calls it at `ui/main_window.py:2114`) | `services/sound_service.py` |
| Table introspection `[existing]` | `def _table_columns(self, table_name: str) -> set[str]:` — `PRAGMA table_info(<table>)` returning the column-name set. Wave 7 **calls** it for the migration guard; its contract and its existing callers (the `alarms` and `bars` migrations) do not change | `data/db.py` |
| Position row shape `[existing]` | `class Position:` in `data.models` — `symbol, qty, avg_cost, contract_type, con_id, account, local_symbol, multiplier, expiry, strike, right, trade_group_id, id` — **and the same 13 names in the SQL**. This is the column order every reader depends on after the drop; `trade_group_id` is the **12th** selected column. Frozen so no task re-orders the SELECT | `data/models.py` + `ui/main_window.py` |
| ICT price structure `[existing]` | `order_blocks = _order_blocks(...)` → `result["orderBlocks"]` → `ICTOverlay._render_order_blocks(...)`. **Not order code** — an ICT price-structure concept; worded like an order, frozen so no sweep "tidies" it (R83) | `services/ict_service.py` + `ui/overlays/ict_overlay.py` |
| Watchlist sequencing `[existing]` | the `sort_order` column of `watchlist` and its readers (`INSERT OR IGNORE INTO watchlist (symbol, category, sort_order)`, `ORDER BY sort_order ASC`, `set_watchlist(..., sort_order=...)`). **Not order code**; frozen (R83) | `data/db.py` + `ui/watchlist_panel.py` |
| Removal guard **scope** `[existing]` | The three instruments' **scope split**, frozen while their contents change: (1) **AST scan** — identifiers **and** string constants over exactly `ui/ services/ data/ ibkr/ config/` (`_SOURCE_DIRS`), comments invisible; (2) **raw-text twin** — `ui/` only, same token list, comments visible; (3) **`tests/` in neither**, so absence is asserted directly (`hasattr`, `name not in IBApiClient.__dict__`, `find_spec`, `Path.exists()`). Two tokens are exact-matched (whole identifier / whole string constant in (1), delimited word in (2)). **What is frozen is the split, not the file**: `tests/test_d45_removal.py` **is** edited by waves 1 and 8 — the split must not move while the token lists and the absence test do | `tests/test_d45_removal.py` |

### Non-Functional Approach (P5)

- **Silent-path safety (the phase's defining risk, R76 — `S43`).** A delete-only batch usually fails **loudly**
  (an import error, a failed constructor). This one can fail **silently**: `emit` on a signal with no receiver is
  a no-op, a slot that is never invoked is dead code, and pyqtgraph installs a **non-abort `sys.excepthook`**, so
  an `AttributeError` raised *inside* a slot is printed and swallowed — and **no test triggers an order
  callback**, so the suite stays green while the app would break on the first TWS order event. Mitigation is
  structural, not hopeful: (i) the consumer half (connects + slots + `_update_order_status` + `_on_order_error` +
  the `_on_error` branch + the import) goes **first**, leaving three live signals with zero receivers — harmless
  and constructible; (ii) each signal is deleted in the **same task** as its only emitters; (iii) the module goes
  **last**, after its sole importer and every reader; (iv) every wave ends with an import check
  (`python -c "import ui.main_window"`) plus a residue grep; (v) the end state is asserted directly —
  `hasattr` on the **eight** window/bridge members, **`name not in IBApiClient.__dict__`** for the **three** client
  overrides (never `hasattr`: the inherited `EWrapper` no-ops keep it `True` before *and* after the override is
  deleted, `AR-D46-2`), and `find_spec` on the module — rather than inferred from a green suite. The expansion adds
  **two more silent paths**: (vi) *the index shift* — a wrong `row[N]` does not raise, it puts a stop value into the
  **Group** column (`S48`, AR-D46-10), mitigated by name-keyed access **plus** a seeded-`trade_group_id` assertion;
  and (vii) *the migration* — a half-done schema does not raise either, mitigated by the `_table_columns()` guard and
  one atomic statement per column (`S47`, AR-D46-9).
- **Error visibility (from `D46.3` / `AC-D46.3`, R77 — the owner's explicit worry).** The requirement is that
  **201 / 103 / 202** still reach the status bar with TWS's own text. It is met by the **existing** generic line —
  `classify_error(201) == classify_error(103) == 'fatal'`, `classify_error(202) == 'warning'`, so
  `IBApiClient.error`'s `severity != 'info'` gate emits all three — and it is proven **positively and per code**
  (three parametrised cases asserting `[201]` / `[103]` / `[202]` **and** the TWS string), never by an absence
  test. The `classify_error` parametrised cases stay in the same file so the gate cannot be "tidied" away
  unnoticed. What the app no longer does — an order id, a "Rejected"/"Cancelled" verdict, a 12-second duration —
  never reached the user (the registry was empty), so the change is documentation, not behaviour.
- **Routing stability (from A94 / DG78).** `_on_error`'s order is unchanged: session reqId first, generic last.
  An orderId that numerically collides with a live session reqId keeps taking the session path — **pre-existing,
  deliberate, and not fixed here** (DG78 item 2 is recorded open and non-blocking; the plan forbids a test that
  would pin the collision as desired behaviour).
- **Importability and greenness between waves.** Wave 1 leaves `ibkr/orders.py` on disk with **no** importer (a
  dormant module is harmless); wave 2 leaves the app with no order signal and no order override; wave 3 removes the
  module *after* nothing references it; waves 4–6 touch files nothing else reads. **Wave 7 is the only wave that
  would leave the suite red until its own test edits land, which is why they are in the same task** (R84/DG85) —
  nothing outside that wave depends on the columns, so no other suite can be reddened by it. Wave 8's instrument
  edit is green the moment it lands (I-1).
- **Worker safety on delete-only work (memory 2026-10-15, R76; R84).** Ten waves, at most **eleven** files each, and
  the one large task (wave 7) is **not** a delete-only sweep: ~40 edited lines across eleven files (4 DDL lines + ~8
  migration lines + 4 field lines + a class + 6 account lines + ~15 `main_window` lines + mechanical test edits),
  well under the L-size deletion profile that killed three D41 workers (R84). Each wave ends with a syntax/import
  check and its own residue grep.
- **Data safety (the destructive step, A99/R82 — `S47`).** What is destroyed is **two columns' bytes** — the batch's
  only byte-destroying step. For a row that receives another live update the values were already cleared (ESC-060:
  `_on_position_update` passed `None` and the `DO UPDATE` wrote both columns; every setter died in D45); for a row that
  never updates again the legacy bytes are lost **at this point and only here**. They are invisible (8-column panel),
  unsettable (no dialog or menu since D45) and unsupported, which is what makes the drop defensible; it is not a
  statement that no byte is destroyed. What must not be destroyed is a **row**, the unique index and the FK — all three measured as preserved. **No
  copy of the database is taken by the app**: copying the owner's DB at launch is a new behaviour with its own failure
  modes and there is no row-copy step to interrupt. The proof is a legacy-fixture test (pre-seeded DDL + rows with a
  non-null `trade_group_id`), a row-count comparison, `sqlite_master`'s index, and a second `DB()` on the same file.
- **Invariant I-1 — the guard may only name what is already gone (new in revision 2).** At **every** wave boundary,
  every token in `_FORBIDDEN` names code that no longer exists, and every name in `_SURVIVORS` still exists. This is
  what makes a **single** token migration (wave 8) correct instead of a staged one: the set is not "allowed to lie"
  in between — it simply does not yet name things that are still there. The interim net for waves 1–7 is the
  mandatory per-wave residue grep, which uses the **final** token list from wave 1 onward.
- **Blast radius / security.** The app loses the only place it could hold order state **and** the only place it
  stored a stop or a target, so nothing in memory or on disk can be mistaken for a live protection. No credential,
  endpoint or persistence is added, and no transmit/cancel capability is created (the guard forbids all three names).
- **Performance / scalability.** No measurable change and none required: three callbacks that did nothing are no
  longer copied, four dead columns are no longer written or read, and the migration runs **once** per database. The
  generic error line is unchanged in shape and duration.
- **Doc freshness (R85/DG84 — `S50`).** The trail must read **kept → cleared → dropped**; two live claims side by
  side is the failure this criterion exists to prevent. P5 owns `architecture.md`/`plan.md`/`codebase-map.md`; Build
  owns `USAGE.txt`/`usage.md` and the code comments. The already-activated D45 sections are enumerated by line for the
  Validator rather than edited here.

### Architecture Risks (P5)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| **AR-D46-1** | A surviving importer of `ibkr.orders` (or of the `orders` singleton) turns the deletion into an `ImportError` at launch, possibly in a module nobody edited (R78) | **H** | The only importer is named and deleted in wave 1 (`S39`); wave 3's gate runs an import-all probe plus `find_spec("ibkr.orders") is None`; every window-building suite constructs the real `MainWindow`, so an unresolved import cannot pass; the guard's token scan covers `ui/ services/ data/ ibkr/ config/` |
| **AR-D46-2** | **A reachable-but-broken intermediate state**: a signal deleted before its emitter, or a slot deleted while its connect remains — an `AttributeError` that only fires on a live TWS order callback, so the suite stays green while the app breaks (R76 — the batch's defining risk) | **H** | `S43`'s four rules, enforced by the wave split: consumers first (wave 1), emitter+signal in **one** task (wave 2), module last (wave 3); per-wave import check; the end state asserted by wave 8's guard — `hasattr` for the **eight** window/bridge members and **`name not in IBApiClient.__dict__`** for the **three** client overrides (the inherited `EWrapper` no-ops make `hasattr` `True` regardless, so `hasattr` proves nothing there) — and re-verified by the Code Reviewer with the same split, not by "the suite is green" |
| **AR-D46-3** | The removal erodes the **error path** — someone "simplifies" `_on_error`, `classify_error` or `IBApiClient.error` while deleting the branch, and 201/103/202 stop surfacing (R77) | **H** | `S46` freezes `classify_error`, `IBApiClient.error` (gate + D40.1 `502`), `error_msg` and the 8000 ms line as **Frozen Interfaces**; the per-code test (`AC-D46.3`) plus the retained `classify_error` cases turn red on any erosion; wave 10's gate and the Code Reviewer reproduce all three codes independently |
| **AR-D46-4** | The guard's token set is wrong in either direction: **not shrunk** (a resurrected `order_registry` passes) or **over-broad** (an offence on code the phase keeps) (R79) | **M** | Counted both ways, by execution: pre-P5 **41 AST offences / 40 twin hits**, post-P5 **0 / 0** on a simulated copy. `AC-D46.4` names the exact ten names that leave `_SURVIVORS`; **78** tokens are substring-matched and **two** (`orders`, `Orders`) are exact-matched; **`reserve` is not a token at all** (measured 13 units / 11 files, all "preserve(s/d)" in docstrings) and is covered by `hasattr(IdManager, "reserve") is False`; `stop_loss`/`take_profit` **must** be substring because the SQL column list is one string constant; the scan going red on a re-added name is the guard |
| **AR-D46-5** | `data/models.UserOrder` is deleted but the smoke assertion is left behind → a red suite that looks like a regression from the module deletion (R81) | **M** | A96 and `AC-D46.8` name the class and the assertion **together**, and both live in **wave 3** (same task); the guard asserts `hasattr(data.models, "UserOrder") is False` |
| **AR-D46-6** | The suite's meaning shrinks (17 builder cases + 3 stop-target cases + 2 fill-blip + 1 order-limiter + 2 registry cases + 4 reserve cases) and a later reader treats a green suite as "order code is fine" (R80, A104) | **M** | Stated as an owner-accepted consequence and recorded in the plan's book **before → after** (**2 deleted / 13 adjusted / 0 added**) — the deleted cases covered code that is itself deleted, so there is **no untested surface left**; the guard's absence assertions plus the **new** schema and index-shift assertions are the replacement meaning, not a coverage claim |
| **AR-D46-7** | **The docs re-instruct the wrong outcome**: the map still says the module "is NOT orphaned and must NOT be deleted" and lists the observers as "do not clean up", while `S29`/`AR-D45-10` mandate a docstring note — a Build worker preserves exactly what must go (DG81) | **H** | `S45`: the map is refreshed and `S29`/`AR-D45-10` superseded **in this draft**, so activation hands Build a truthful map; the Validator checks that no "retained"/"must not be deleted" claim survives; the Code Reviewer greps for it independently; `ESC-061` is recorded **moot** so nobody implements the note |
| **AR-D46-8** | The owner (or a reviewer) reads the deletion as **lost error visibility**, because the "Rejected"/"Cancelled" wording is what they remember being promised (R77/DG78) | **H** *(owner-facing)* | `AC-D46.3` is a positive per-code proof; `S41` and the plan state **exactly** what appears and what no longer does; `USAGE.txt:92`–`:93` already matches the end state ("IBKR rejections and cancellations appear in the status bar together with TWS's message"), so the shipped doc is evidence, not a promise to rewrite |
| **AR-D46-9** | **The first destructive schema step runs on the owner's real database at launch** and a botched migration loses **rows** (not just the two dead columns), or drops the unique index / the FK and silently breaks the upsert and strategy grouping (R82) | **H** | `S47`: four guarded in-place `DROP COLUMN` statements, one atomic statement per column, **measured** to preserve rows, `sqlite_sequence`, `idx_positions_symbol_con_id`, the FK definition, `foreign_key_check`, `integrity_check` and the 13-column upsert with `RETURNING id`; idempotent on fresh and re-opened DBs; a legacy-fixture test asserts row counts and the index; the Code Reviewer reproduces the migration on its own pre-P5 fixture |
| **AR-D46-10** | **The index shift fails silently** — `trade_group_id` reading `row[12]` instead of `row[14]` puts a stop value (or `None`) into the Portfolio **Group** column, which looks like a strategy-detection regression (DG85) | **H** | `S48`: name-keyed access at the one reshaped SELECT, **plus** a new case seeding a non-null `trade_group_id` (measured: **no test seeds one today**), **plus** the legacy-fixture migration test — all in the same task as the schema change (R84) |
| **AR-D46-11** | A token proves **too broad** and the guard goes red on code the register keeps — the measured cases are `reserve` (13 units: `id_manager.py`'s two, ten "preserve(s/d)" docstrings, and `_reserve_price_tag_lane`), `Orders` in prose, and `_fill_effect` inside `_effect`'s ternary string (R79/R83) | **M** | `reserve` is **not** a token (`hasattr` instead); `orders`/`Orders` are exact-matched; `stop_loss`/`take_profit` stay substring because a SQL list is one string; **and `_effect` must collapse to alarm-only**, stated as a named edit because leaving the ternary keeps the scan red on a member this phase deletes |
| **AR-D46-12** | **Test-book drift**: an assertion invalidated by a deleted surface outside the edited files turns red or silently stops testing — measured instances the register's book does **not** list: `test_id_manager`'s concurrent case (calls `reserve`), `test_sound_service`'s `paths["fill"]` (`KeyError`), and the absence of any seeded `trade_group_id` | **M** | The book is enumerated **per assertion with line numbers** in the plan, before → after, and two of the three are raised as **Flagged Issues** so the requirements side can correct the register rather than have a worker discover them; wave 10 runs the full suite and the Code Reviewer re-derives the book from `git diff --stat -- tests/` |

### Requirements → architecture traceability (P5)

| Requirement / journey | Architecture section | Phase (plan) |
|---|---|---|
| **`D46.1` / `AC-D46.1`** (module absent; no importers; no builder/registry name) | `S39`; System Components (deleted); Codebase Summary (single importer); AR-D46-1 | Phase 1 · **W1 + W3**; Phase 2 · **W8**; Phase 3 · W10 |
| **`D46.2` / `AC-D46.2`** (the chain is gone: 3 signals, 3 overrides, 5 members, no registry lookup) | `S40`; System Components (three rows); Integration Points (order lifecycle `removed`); AR-D46-2. **The client half is measured by `__dict__` membership** — `AP-D46-14` / `RG-D46-2`: the AC's `hasattr(...) is False` wording is unsatisfiable because `EWrapper` supplies the three names | Phase 1 · **W1–W2**; Phase 2 · **W8**; Phase 3 · W10 |
| **`D46.3` / `AC-D46.3`** (201/103/202 still surface, per code, 8000 ms, no verdict) | `S41` + `S46`; Frozen *Error classification* / *Error ingress* / *Error signal* / *Window error routing*; Non-Functional (error visibility); AR-D46-3/8 | Phase 1 · **W1**; Phase 2 · **W8**; Phase 3 · W10 |
| **`D46.4` / `AC-D46.4`** (zero order interaction; guard strengthened; the ten survivor names move) | `S44`; Frozen *Broker boundary*; the plan's residue step; AR-D46-4 | Phase 1 · W1–W6; Phase 2 · **W8** |
| **`D46.5` / `AC-D46.5`** (green suite; exact test book; no other file changes) | `S44`; the plan's book (**2 deleted / 13 adjusted / 0 added**); AR-D46-6, AR-D46-12 | Phase 1 · **W1, W3–W7**; Phase 2 · W8–W9; Phase 3 · W10 |
| **`D46.6` / `AC-D46.6`** (prose matches the tree: map, `classify_error` comment, user docs, the comments) | `S45` + `S49` + `S50`; System Components (map, `error_codes`, `account`, `main_window` comments); Non-Functional (doc freshness); AR-D46-7 | Phase 2 · **W9** (+ the Plan-owned map in this draft) |
| **`D46.7` / `AC-D46.7`** (history preserved; A80/A90/A87/A97 keep their wording; marker + tech stack intact) | § *Supersessions and non-changes* below; `S39`/`S40`/`S46`/`S47` relationship labels | — (recorded; no production edit) |
| **`D46.8` / `AC-D46.8`** (no second `UserOrder`; smoke green) | `S42`; Data Model (`data.models.UserOrder [deleted]`); AR-D46-5 | Phase 1 · **W3** |
| **`D46.9` / `AC-D46.9`** (the inventory is closed: DELETE empty, RETAIN present with its consumer) | `S44` (token set) + `S46` (frozen survivors, each with its consumer); the plan's per-name ownership table | Phase 2 · **W8**; Phase 3 · W10 |
| **`D46.10` / `AC-D46.10`** (`IdManager` intact minus `reserve`; 8 cases → 4) | `S46` (module frozen) + `S44` (`reserve` is **not** a token); the plan's Flagged Issue 1 and W6 | Phase 1 · **W6**; Phase 2 · W8 |
| **`D46.11` / `AC-D46.11`** (zero-consumer utilities gone; the alarm chime still plays) | `S46` (alarm path frozen) + System Components (`pacing`, `settings`, `sound_service`, `id_manager`); AR-D46-11 | Phase 1 · **W4–W6**; Phase 2 · W8 |
| **`D46.12` / `AC-D46.12`** (storage gone; rows/index/FK preserved; idempotent; Portfolio 8 columns) | **`S47`** (mechanism) + **`S48`** (readers) + Data Model (the three DB ages); AR-D46-9/10 | Phase 1 · **W7**; Phase 2 · **W8**; Phase 3 · W10 |
| **`D46.13` / `AC-D46.13`** (one-directional doc trail: kept → cleared → dropped) | **`S50`**; the plan's *Document trail* table (site-by-site) | Phase 2 · **W9** (+ the Validator's supersession markers) |
| **Journey 39** (steps 1–10; postconditions; edge cases: `_closing`, session-reqId collision, 202 severity, `reqId=-1`, D40.1 502, stale `__pycache__`, no saved layout, **pre-D46 DB**, **fresh DB**, **second open**, **inventory grep**, **re-add goes red**) | `S40`–`S50`; Non-Functional (routing stability, data safety, I-1); the plan's edge-case list | Phase 1 · W1–W7; Phase 2 · W8–W9; Phase 3 · **W10** |
| **A91 / A92 / A93 / A94 / A96** | `S39` / `S40` / `S41` / `S41` (routing unchanged) / `S42` | Phase 1 · W1–W3 |
| **A95 / A99 / A100 / A101 / A102 / A103 / A104** | `S44` (test book) / **`S47`+`S48`** / `S46` / `S46` (`reserve` only) / `S46` (`nextValidId`) / `S44`+`S46` / the plan's book | Phases 1–3 |
| **R76 / R77 / R78 / R79 / R80 / R81** | AR-D46-2 / 3 + 8 / 1 / 4 + 11 / 6 / 5; `S43`, `S44` | Phases 1–3 |
| **R82 / R83 / R84 / R85** | **AR-D46-9 / AR-D46-11 / AR-D46-10 + `S43`'s wave split / AR-D46-7 + `S50`** | Phase 1 · W7; Phase 2 · W8–W9 |
| **DG78** (wording already unreachable; orderId↔session-reqId collision) | `S41` — (1) pinned by `AC-D46.3`; (2) **deliberately unchanged** (A94) | Phase 1 · W1 (assertion only) |
| **DG79** (second `UserOrder`) | `S42` | Phase 1 · W3 |
| **DG80** (`IdManager.reserve`) | `S46` — **resolved**: `reserve` is deleted, the module stays (A101) | Phase 1 · W6 |
| **DG81** (Plan-owned docs instruct retention) | `S45` + AR-D46-7; the map refresh in this draft | Phase 2 · W8 (verification) |
| **DG82 / DG83** (`nextValidId`, `advancedOrderRejectJson`) | `S46` — both RETAIN, each with its consumer named | — (recorded) |
| **DG84 / DG85 / DG86 / DG87** | **`S50` / `S48` / `S47` / `S44`** (scan scoped to tracked `*.py`; `__pycache__` is untracked residue) | Phase 2 · W9 / Phase 1 · W7 / Phase 1 · W7 / Phase 2 · W8 |
| **`ESC-062`** (four comments + one test name) | **`S49`** | Phase 1 · W1 (deleted comment) + W7 (three); Phase 2 · W9 (rename) |
| **`ESC-063`** (open PLAN: map says D45 "adjusts six") | `S45`, § *Supersessions* item 15 — **already corrected in `docs/codebase-map.md:25`–`:29`** | — (Plan, this draft) |
| **`ESC-061`** (open BUILD: docstring note on the retained module) | `S39` — **moot**, no note is owed | — (no task) |
| **D1–D45** | `[no relationship]` — **not reopened**; only the clauses named in § *Supersessions* change | — |

### Supersessions and non-changes (recorded, never silent) (P5)

1. **`S29` (D45) — SUPERSEDED IN FULL.** "`ibkr/orders.py` is retained, unreferenced by any transmit path, with
   a module-docstring note" is replaced by `S39`: the module is **deleted**. Requirements recorded the reversal
   as **A91** (A80's original wording kept beside it) — this section is the architecture half of that reversal.
2. **`AR-D45-10` — SUPERSEDED.** "`ibkr/orders.py` retained-but-unused invites a future reconnection" described a
   risk of *keeping* the module; with the module gone the risk does not exist. Its mitigation (the docstring note)
   is **moot** — recorded here so `ESC-061` is closed as moot rather than re-dispatched.
3. **`S35`'s observer half + `A90` — REVERSED.** The "keep the broker-boundary plumbing inert rather than deleting
   it" decision covered two things: the ibapi **news** boundary and the **order** observers. The news half
   **stands untouched**; the order half is removed by `S40` (A92). The retained fail-fast port check, badge and
   no-test-transmits rule named in `S35` are exactly what `S46` freezes.
4. **D45's frozen-interface rows — VOID where they named the removed code.** *Order registry API* (`ibkr/orders.py`)
   and *Inert inbound observers* (`ui/main_window.py`) described interfaces that no longer exist; they are not
   carried forward. The *Error classification* row's **role text** is amended: `classify_error` gates **every** TWS
   error through `IBApiClient.error`, not "the retained `_on_order_error` path".
5. **Plan `AP-D45-1` and `AP-D45-9` — SUPERSEDED.** "`ibkr/orders.py` is retained, not deleted" and "`tests/test_order_builders.py`
   stays as the module's residual coverage" are both replaced by `S39` and the deletion of that suite.
6. **`DG76` — RESOLVED** by the deletion (the "unreferenced code that still looks live" question no longer
   exists). **`DG79` — resolved** by `S42`. **`DG81` — resolved** by this draft's map refresh plus `S45`.
   **`DG80`** stays **open (non-blocking)** and deliberately out of scope (A97). **`DG78`** item (2) stays **open
   (non-blocking, pre-existing, deliberately unchanged)** per A94 — no task may reorder the error path.
7. **`AC-D26.9`'s registry half — VACUOUS** (there is no registry); its **surfacing half** is carried forward as
   `AC-D46.3`, exactly as the requirements' supersession record states. No other D26 clause changes.
8. **`AC-D45.4` / `AC-D45.8` — unchanged in substance, strengthened in fact.** The guard's allow-list loses the
   eight order names and its forbidden set gains them, so D45's zero-transmit invariant now also forbids the
   observation seam. Nothing in D45's criteria is weakened.
9. **Deviation record — the register's Build split order is not executable as written.** The correction record
   suggests (1) module deletion + importer cleanup, (2) client/bridge/connects, (3) window slots. Group (1) cannot
   be a standalone wave: deleting `ibkr/orders.py` first leaves `ui/main_window.py`'s import dangling **and**,
   worse, leaves `_on_error`'s registry branch as a live `NameError` on any non-session TWS error. P5 keeps the
   register's **member groups** and forces the **order** (window → boundary → module) — `S43`, plan `AP-D46-1`.
10. **Deviation record — the guard needs four edits across two waves, not one.** `AC-D46.5`/A95 describe
    `tests/test_d45_removal.py` as "allow-list shrink" only; the walkthrough's `win._on_order_error(...)` call and
    its docstring bullet must be repointed in **wave 1** or the walkthrough raises once the handler is gone, and the
    instrument's own retention-era prose and token migration are corrected in **wave 8** (`AP-D46-15`, invariant I-1) —
    two waves, four sub-edits (`AP-D46-6`). The file is named and
    *adjusted* in the AC, so no criterion fails — plan `AP-D46-6` records the full set.
11. **`ESC-063` — RESOLVED (Plan-owned, this draft).** The map's D45 header said the batch "adjusts six" test
    files and omitted the added suite; it now reads **5 deleted / 7 adjusted / 1 added** (matching
    `git diff --stat HEAD -- tests/`: five deletions, seven modifications, and `tests/test_d45_removal.py` added),
    and the file stops pointing workers at the superseded D45 proposal drafts.
12. **Explicit non-changes (recorded so they are not read as omissions):** the chart render stack, `ui/ticker_session.py`,
    `ui/active_portfolio_panel.py`, `ui/watchlist_panel.py`, `ui/dock_layout.py`, `services/*` outside
    `sound_service.py`, `data/bar_cache.py`, `data/events/*`, `ibkr/market_data.py`, `ibkr/realtime_bars.py`,
    `ibkr/subscription_manager.py`, `ibkr/stream_health.py`, `ibkr/contracts.py`, `ibkr/utils.py`,
    `ibkr/error_codes.py`'s **code**, `PacingManager`/`PacingExceeded`/`pacing_manager`, `IdManager`'s remaining API,
    `IBApiClient.nextValidId`, the `"456"`/tick-59 dividend path, the ICT order blocks, `sort_order`,
    `TradeGroup`/strategy grouping, `play_alarm`/`render_alarm_chime`, `advancedOrderRejectJson`, `config/paths.py`,
    `main.py`, `tests/test_d40_tws_lifecycle.py`, `tests/test_port_guard.py`, `tests/test_d41_removal.py`,
    `tests/test_db_schema.py`, `docs/requirements/*` (analyst-owned), and the pinned dependency set (**no new
    dependency**).
13. **No replacement surface.** No order, cancel or protection UI is added anywhere; the Portfolio panel stays
    view-only and stop/target-free. `D46` is a removal, and a future order path needs a new requirement, not an
    un-comment (`R79`).
14. **`S33` (D45) and `AC-D45.6`/`AC-D45.10`'s storage halves — SUPERSEDED BY `S47`/`A99`.** Their *UI* halves stand
    (8 columns, no `Stop`/`Target` header, no setters). Their *storage* halves ("columns and fields retained, no
    migration") are superseded: the columns and the fields are **dropped**. D45's text stays as written so the
    reversal is visible; the trail reads **kept → cleared → dropped**.
15. **`S46` (this phase, revision 1) — REVISED IN PLACE.** Revision 1 froze `IdManager` *including* `reserve`, the
    `positions`/`trade_groups` storage, `order_limiter` and `MAX_ORDER_NOTIONAL` as untouched. Those five are now
    **tasks**; everything revision 1 froze that the register still keeps is frozen again, now **with its consumer
    named**.
16. **`S44` (this phase, revision 1) — MECHANISM KEPT, TWO RATIONALES CORRECTED.** The exact-match set for
    `orders`/`Orders` was justified by two docstrings in files "no task may edit"; **both are deleted by this phase**,
    so that justification is void. The set survives on the prose-safety ground stated in `S44`, and the token set
    grows to the measured 80. `token in parts` remains **not** the AST implementation, and
    `PacingExceeded`/`pacing_manager`/`classify_error` remain survivors.
17. *(merged into item 9 — the same deviation record was written twice in revision 2; removed as duplication, no
    decision changed.)*
18. **Deviation record — the guard gets two edits in two waves, and its token migration is deliberately late.** Waves
    1 and 8 (invariant I-1). `AC-D46.5` names the file as *adjusted*, so no criterion fails; plan `AP-D46-6`.
19. **Deviation record — the storage wave is one task with eleven files, not three tasks.** R84/DG85 require the
    schema and its readers to land together; splitting them would leave the suite red between waves **and** separate
    the schema from its readers, which is exactly the trap. Size measured: ~40 edited lines, four files mechanical.
    Plan `AP-D46-10`.

**Handoff:** this increment is **ACTIVE** — `docs/plan.md` § *Phase P5* ends `READY_FOR_TASK_MANAGER` (validated and
re-activated 2026-10-25, `docs/plan_review_P5.md`). The Code
Reviewer independently re-verifies: (a) `ibkr/orders` absent with **no** importer and `import ibkr.orders` raising
`ModuleNotFoundError`; (b) the chain absent **by the right measure for each half** — the five `MainWindow` members and
three `Bridge` signals by `hasattr`, the three `IBApiClient` overrides by **`name not in IBApiClient.__dict__`**
(never `hasattr`), and no `order_registry` in `_on_error`; (c) `AC-D46.3` reproduced for **201, 103 and 202**, with
`classify_error`'s table and the 8000 ms line unchanged; (d) `data.models` has no `UserOrder`, no
`Position`/`TradeGroup` stop/target field, `ibkr.account.Position` matches it, and `build_position_from_ib` takes
neither; (e) **the migration**: a pre-P5 fixture keeps every row, `sqlite_sequence`, the unique index and the FK, a
second open is a no-op, and a fresh DB has no such columns; (f) the map no longer claims retention and its books read
5/7/1 (D45) and the P5 book; (g) the guard's token set really migrated and its end state fails on the pre-P5 tree
(**41 AST offences / 40 twin hits**, simulated post-P5 **0 / 0**); (h) **no** replacement order/cancel/protection
surface was introduced.

---

## Phase P6 — D47 increment: the chart stack migrates to Lightweight Charts behind a `ChartView` seam (strangler; pyqtgraph retained until parity accepted) — drafted 2026-10-26

> **Status: DRAFT — awaiting Plan Artifact Editor & Validator review.** This section is inert until the Validator
> activates it. D1–D46 are built, reviewed and merged; P5 (D46) ended `READY_FOR_TASK_MANAGER` with Build
> `REVIEW_COMPLETE` and zero open escalations. This phase plans **only** D47 (Batch 22, `Status: READY_FOR_PLAN`,
> Q60 answered-by-default YES, Q61–Q63 ANSWERED 2026-10-26). No D1–D46 criterion is re-planned except by the
> recorded supersessions below (density-cap language → `barSpacing`, pending the Q60 record).

**Relationship to prior phases.** Every decision below carries exactly one relationship label. `[revises P<m>]` /
`[revises D42:]` names the earlier decision it changes, `[extends P5:]` builds on one without changing it,
`[new in P6]` has no prior-phase dependency (or is settled by D47 itself). P6 builds on the **P5 post-deletion
baseline** (no order code anywhere; `ibkr/orders` absent; `ESC-061` moot) and changes **no** P5 decision. The single
revision is the D42 density-cap mechanism (S13), superseded at the requirements level by D47.6/T10 (Q60
answered-by-default YES) and restated here as S56. Components, data-model entities and integration points carry the
existing-repo status labels `[existing]` / `[new]` / `[new/changed]` — no unlabeled items.

### Codebase Summary (existing repository — delta pointer, not a re-inventory)

The full module index is `docs/codebase-map.md` (skeleton regenerated 2026-10-26 for P6; annotations carried forward
and extended below). What P6 touches, as found by graphify discovery (`graphify-out/graph.json`, 4,625 nodes —
used for discovery only) and **validated against the current source files** (the repository is authoritative):

- **Chart render surface (the migration area, ≈ 5,135 lines):** `ui/chart_panel.py` (1,785 L — `ChartPanel.update_chart`,
  `::update_last_bar`, `::set_symbol`, `::set_timeframe`, `::_refresh_candles`, the volume `BarGraphItem`,
  `::_clamp_half_width` via the shared D42 helper), `ui/candlestick_item.py` (274 L — `CandlestickItem.set_data`,
  `capped_body_half_width`), `ui/drawing_overlay.py` (926 L), `ui/alarm_overlay.py` (263 L),
  `ui/event_marker_overlay.py` (182 L), `ui/overlays/` (base/gap/ict/session/vix), `ui/chart_mouse_router.py`
  (271 L — `RouterMode`, the total TR-1…TR-17 table), `ui/popout_window.py` (295 L — `PopoutChartWindow`,
  `editable=False`). Bar path into the surface: `MainWindow::load_chart` → `BarCache` → `MarketDataManager` →
  `ChartPanel.update_chart`. Collapse/time mapping: `services/time_collapse_service.py::TimeCollapseMap`
  (display-only x-remap every overlay honours) + `gap_is_non_trading` as the non-trading source of truth; session
  bands: `services/session_service.py`.
- **Backend that stays untouched:** `ibkr/` (client/bridge/market_data/realtime_bars/pacing/id_manager/
  subscription_manager/stream_health/error_codes — no order code remains after P5), `data/` (SQLite `bars`,
  `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`,
  `position_group_map`, `yfinance_events_cache`, `volume_baseline`), most of `services/` (indicator, alarm,
  drawing, strategy, gap/vix, ict, volume_baseline, market_calendar, backfill, contract_lookup, symbol_search,
  sound), `data/events/provider.py` (`EventProvider` ABC), `ui/watchlist_panel.py`, `ui/dock_layout.py`,
  `ui/main_window.py` dock/toolbar/session wiring, the retained Qt dialogs (zone/horizontal-line/alarm).
- **What does not exist yet:** `ui/chart_view.py`, `services/chart_model.py`, `spikes/lwc/`,
  `docs/lwc_parity_matrix.md`, `docs/lwc_spike_results.md` — all land in P6 waves (named without backticks in the
  codebase map until they exist, per the map lint rule).
- **External integrations in play:** IBKR historical/RT data (TWS 7496), SQLite, Qt signals, `pacing_manager`,
  `id_manager`. **No new external service is introduced by P6** — the vendored lightweight-charts tree is a bundled
  asset, not a service; there is no CDN/npm at runtime.

### Summary

The chart renderer migrates **via strangler behind a `ChartView` protocol**: a `create_chart_view` factory selects
the pyqtgraph view (default through cutover) or the new LWC view on `NDT_CHART_ENGINE`/`QSettings`; a shared Qt-free
`ChartModel` becomes the single value source both engines render from; and a vendored, offline `QWebEngineView` host
with a batched, self-healing `QWebChannel` bridge carries Python → JS updates. pyqtgraph is **retained and default
until parity is accepted**, and its deletion is a **separately gated Phase 11 wave** (explicit owner approval + one
clean live trading session). Python stays the source of truth throughout — JS receives timestamps + prices only.

### Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack (constrained) | `[existing]` Python 3.11+, PyQt6, **pyqtgraph retained and default** | Existing-repo hard constraint; D47 explicitly retains pyqtgraph until parity is accepted — the decline's sanctioned route | Removing pyqtgraph now (rejected: deletion is Phase 11-gated) |
| Broker / numerics / secondary source (constrained) | `[existing]` `ibapi-latest==10.51.1`, numpy, `yfinance==1.7.0`, SQLite, PyInstaller `.app`, pytest + pytest-qt offscreen | Untouched backend; D47.12 out-of-scope list | None — not in migration scope |
| LWC host (new) | `[new]` `QWebEngineView` + **vendored lightweight-charts v5.2.x** via a custom `ndt://` scheme handler registered **before** `QApplication`; an interceptor **blocks non-ndt traffic**; **no CDN/npm at runtime**; attribution kept | Offline determinism + version pin + auditability; the scheme handler + deny-default interceptor make "no network" structural, not a test assertion | CDN load (rejected: network dependency + version drift); npm build step at runtime (rejected: toolchain in the bundle) |
| Python↔JS bridge (new) | `[new]` `QWebChannel` `LwBridge`, batched `{v:1,ops:[]}` ops, column arrays, queue-until-ready, ~33ms live coalesce, gestures local in JS, Python **replays the full op log after `renderProcessTerminated`** | Batching bounds the per-tick crossing cost; replay makes renderer crashes recoverable without state divergence | Per-call synchronous bridge (rejected: latency + fragility); unversioned payloads (rejected: silent schema drift) |
| Shared value source (new) | `[new]` Qt-free `services/chart_model.py` — plotted-index filtering, `floor_bar_budget`, whitespace derivation, studies + `_StudyCache`, Heikin-Ashi, volume formatting; `ChartPanel` delegates with **no behaviour change** | One value source prevents the classic strangler leak (two engines, two mappings, parity declared on looks); Qt-free keeps it unit-testable offscreen | Parallel logic per engine (rejected: divergence); model inside the web host (rejected: untestable without an engine) |
| Time axis (new) | `[new]` **Logical-index** time axis; within-session holes render as whitespace; `gap_is_non_trading` stays the authority in both engines; custom tz formatters (`local = t - offset`); per-mode series; `series.update` for the live bar | Matches the app model (collapsed between-session gaps, D21.4) instead of wall-clock time; one authority avoids mode divergence | Wall-clock axis (rejected: cannot represent collapsed gaps); per-engine gap rules (rejected: divergence) |
| Controls / router / drawings (new) | `[new]` In-HTML controls with Python shims; Python `RouterMode` + JS mirror; drawings via a primitives library (ts-to-fractional-index); **Qt dialogs stay** (zone/horizontal-line/alarm settings, alarm edit) | Keeps the settled TR-1…TR-17 contract and the dialog UX untouched; only the render surface moves | Rebuilding dialogs in HTML (rejected: D12/D15/D21.9 UX churn); JS-owned router (rejected: contract fork) |
| Density language (changed) | `[new/changed]` Library **`barSpacing`** replaces the pyqtgraph density-cap wording of `AC-D6.4`/`AC-D7.1`/`AC-D9.1`; the no-overlap guarantee is restated in `barSpacing` terms (DG94); retirement lands with the Q60 answered-by-default YES via T10 | The engine owns spacing now; keeping both wordings live forces every density case to pass on two contradictory spacings | Keeping the 4-px floor on LWC (rejected: unimplementable — the library controls spacing) |
| JS test runner (new) | `[new]` `node --test` for the JS side; webengine cases are `@pytest.mark.webengine` and **skip (never red)** where no engine exists; the manual checklist is the gate there (A110/DG88) | A red webengine case must mean a real regression, not a missing Chromium | Forcing engine-present CI (rejected: offscreen viability unproven) |

### System Components

| Component | Responsibility | Status |
|---|---|---|
| `ui/main_window.py` load path + sessions + docks + toolbar | Orchestrator; bar path, session lifecycle, dock/toolbar wiring | `[existing]` — untouched (renderer-only migration) |
| `ui/chart_panel.py` + `ui/candlestick_item.py` | pyqtgraph engine: panes, candles, volume, studies, overlays | `[existing]` until cutover; `[new/changed]` only via the ChartModel delegation (Phase 1, no behaviour change) |
| `ui/drawing_overlay.py`, `ui/alarm_overlay.py`, `ui/event_marker_overlay.py`, `ui/overlays/*` | Drawings, alarms, event markers, session/gap/ICT/VIX overlays | `[existing]` (Qt side retained; LWC twins land per phase) |
| `ui/chart_mouse_router.py` (`RouterMode`, TR-1…TR-17) | Single gesture state machine | `[existing]` — Python contract frozen; JS mirror added beside it |
| `ui/popout_window.py` (`PopoutChartWindow`, `editable=False`) | Pop-out charts | `[existing]` (engine-agnostic; re-hosted in Phase 9) |
| `ui/watchlist_panel.py`, `ui/dock_layout.py`, `ui/ticker_session.py` bar/session half, `ui/*_dialog.py`, toolbar | Watchlist, dock widths, sessions, dialogs | `[existing]` — untouched |
| ChartView seam (protocol + `DrawingController`/`AlarmController` + `create_chart_view(tz_offset, editable)`) | Strangler boundary; engine selection on `NDT_CHART_ENGINE`/`QSettings` | `[new]` |
| Shared chart model (plotted-index filtering, budgets, whitespace, studies, Heikin-Ashi, volume) | Single value source for both engines | `[new]` |
| LWC host (web view, vendored v5.2.x tree, `ndt://` handler, interceptor) + `LwBridge` (batched, queue-until-ready, replay) | Offline render + self-healing transport | `[new]` |
| LWC panes/time/drivers (logical-index axis, tz formatters, per-mode series), in-HTML controls + shims, JS router mirror, primitives library | Engine-side parity surface | `[new]` |
| Spike (throwaway 9-API-behaviour proof + results doc) | Phase 0 go/no-go evidence only; never imported | `[new]` |
| `ibkr/`, `data/` (+schemas), most of `services/`, packaging, `config/` | Backend, persistence, tunables | `[existing]` — untouched |

### Data Model

| Entity | Key fields / notes | Status |
|---|---|---|
| `Bar` / `bars` table `(symbol, timeframe, ts)` PK; `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline` | Schemas, stores and persistence paths unchanged (D47.12) | `[existing]` |
| `ChartModel` value objects (plotted-index rows, whitespace runs, study series, budget verdicts) | In-memory only; derived from cached bars; no table, no migration | `[new]` |
| `{v:1,ops:[]}` bridge op log (column arrays; replay source after renderer crash) | In-memory on the Python side; versioned envelope | `[new]` |
| Parity matrix (19 rows, disposition per row) + spike results doc | Docs, not runtime state; matrix kept updated every phase exit | `[new]` |

### Integration Points

| Integration | Why | Status |
|---|---|---|
| IBKR historical/RT data (TWS 7496), SQLite, Qt signals, `pacing_manager`, `id_manager` | Unchanged backend feeds | `[existing]` |
| Vendored lightweight-charts v5.2.x tree (bundled asset) | Render library; resolved locally via `ndt://`, never fetched | `[new]` — asset, not a service; no new network/account/credential surface |
| `QWebChannel` over the embedded view | Python→JS transport | `[new]` — in-process channel, no external endpoint |

### Frozen Interfaces

Every entry below is `[existing]` and **unmodified by every P6 wave** (pyqtgraph stays default through Phase 10; no
pyqtgraph code is deleted before Phase 11). Task Manager gives workers the contract, never the implementation. The
repository is authoritative on conflict.

- **`ibkr/market_data.py::MarketDataManager.req_historical_data`** — contract:
  `req_historical_data(self, contract: Contract, timeframe: str = "5 mins", endDateTime: str = "", whatToShow: str = "TRADES", useRTH: int = 1, extended_hours: bool = False, bar_size: str | None = None, duration: str | None = None) -> int`. Owner: `ibkr/market_data.py`. (TIMEFRAME_CONFIG durations/bar sizes, pacing + reqId allocation per request, and the single-caller `load_chart` shape are unchanged.)
- **`services/backfill_service.py::find_missing_spans`** — contract:
  `find_missing_spans(cached_ts: Iterable[int], now_ts: int, timeframe: str, trailing_days: int = TRAILING_BAR_GRANULARITY_DAYS, ext_hours: bool = False, min_sessions: int = 0) -> List[MissingSpan]`. Owner: `services/backfill_service.py`. (Mode-aware day presence + the 30-session floor stay exactly as D42 left them.)
- **`config/settings.py::check_live_port` + tunables** — contract: `check_live_port() -> None` (fail-fast unless
  `IBKR_PORT == 7496`); `LIVE_PORT = 7496`; `MAX_POPOUTS = 10`; `SESSION_BAR_CAP = 5000`;
  `MIN_INTRADAY_SESSIONS = 30`. Owner: `config/settings.py`. (The pop-out cap stays 10 per Q62/A107; no budget is set per Q61/A109.)
- **`services/time_collapse_service.py::gap_is_non_trading`** — contract:
  `gap_is_non_trading(a: int, b: int, ext_hours: bool, bar_period: int) -> bool`. Owner: `services/time_collapse_service.py`. (The non-trading authority in both engines; D21.4 collapse semantics unchanged.)
- **`ui/dock_layout.py::watchlist_max_width` + width constants** — contract:
  `watchlist_max_width(chart_area_w: int) -> int`; `CHART_MIN_WIDTH = 400`; `WATCHLIST_MIN_WIDTH = 150`. Owner: `ui/dock_layout.py`. (Watchlist/dock geometry untouched — renderer-only migration.)
- **`data/bar_cache.py::BarCache.save_bars` / `::get_bars`** — contract:
  `save_bars(bars: List[Bar], ext_hours: bool = True)`; `get_bars(symbol: str, timeframe: str, ext_hours: bool = True) -> List[Bar]`. Owner: `data/bar_cache.py`. (Aggregation/backfill unchanged per D47.12.)
- **`ui/chart_mouse_router.py::RouterMode` + TR-1…TR-17** — contract: the enum
  (`IDLE`/`DRAWING`/`ZOOMING`/`ALARM_PLACING`) and the total transition table (`AC-D3.7`–`AC-D9` semantics, incl. the
  `ALARM_PLACING + magnifier → ALARM_PLACING` refusal). Owner: `ui/chart_mouse_router.py`. (Python side frozen; the JS mirror must match it, never reinterpret it.)
- **Order-code absence** — contract: `import ibkr.orders` raises `ModuleNotFoundError`; no `orderStatus`/`openOrder`/`execDetails` overrides, no order bridge signals, no order UI. Owner: the P5 end state. (Zero order interaction stands; nothing in P6 reintroduces it.)
- **Drawing/alarm persistence + Qt dialogs** — contract: `data/drawing_store.py`, `data/alarm_store.py`,
  `data/study_store.py` APIs and the zone/horizontal-line/alarm dialogs behave exactly as before. Owner: `data/` + `ui/*_dialog.py`. (D47.7 second half / D47.12.)

### Non-Functional Approach

- **Performance (driven by AC-D47.4/AC-D47.5, DG91, R88):** column-array batches (not per-object calls); ~33ms live
  coalesce; gestures resolve locally in JS without a Python round-trip; `_StudyCache` reuse and the bounded
  `_bars`/`SESSION_BAR_CAP` discipline carry over via the shared model. Bridge backpressure counters (queue depth/age,
  replay size) are instrumented from Phase 2, never retrofitted (A112/DG91); per-pop-out memory is accounted from
  Phase 9 against the D24 cap of 10 (A107/DG90). Phase 0 measures the `.app` size delta and the perf baseline the
  cutover gate holds (`AC-D47.6`); no fixed budget is assumed (A109/DG89).
- **Security (driven by AC-D47.3):** vendored-only assets; the `ndt://` handler is registered before `QApplication`
  and the interceptor denies non-`ndt` traffic by default; no CDN/npm at runtime; attribution kept in-tree.
- **Scalability (driven by Journey 40, Q62):** one `LwBridge` per view, refcounted sessions unchanged (D24/D25
  semantics), pop-out cap stays 10; a higher cap needs the DG90 evidence first.
- **Cutover without soak (driven by AC-D47.6/AC-D47.8, R91):** the triple gate (owner acceptance **and** parity all
  Done/accepted **and** Phase-0 perf holds) replaces the calendar soak by explicit owner decision; Phase 11 additionally
  needs explicit owner approval **and** one live trading session with no engine defect. pyqtgraph is the default through
  Phase 10, so any cutover-candidate defect falls back by flipping the engine selector, not by a code revert.

### Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| R86 — strangler seam leaks: engines diverge (bar mapping, study values, drawing coordinates), parity declared on looks | H / M | `AC-D47.2` (shared `ChartModel` — one value source) + `AC-D47.5` (logical-index parity incl. DST/session boundaries) + the kept-updated matrix (`AC-D47.9`) |
| R87 — Chromium + vendored JS bloat the `.app` or break signing/notarisation (Q61) | M / M | Measure-first (A109/DG89); Phase 10 is a cutover *candidate*, never a silent ship; owner sets the budget from the measured delta |
| R88 — bridge backpressure: unbounded ready-queue, replay duplicates bars, 10 pop-outs exhaust memory (Q62) | H / M | `AC-D47.4` (batch shape + replay identity) + DG91/DG90 counters and caps from Phase 2; per-pop-out memory accounted |
| R89 — density-cap retirement silently drops the ESC-041 no-overlap guarantee | M / H | Retirement only via T10 with the Q60 record; DG94 restates the guarantee in `barSpacing` terms; the rendered-geometry guard survives the engine change (S56) |
| R90 — offscreen QtWebEngine non-viable in CI; webengine cases skip everywhere | M / M | A110/DG88: skipped-never-red marking + the manual checklist as an explicit gate; a skipped case names its manual counterpart |
| R91 — cutover without a soak ships a same-day defect to the live session | H / L | Owner-accepted: triple gate + one-clean-live-session delete gate (`AC-D47.8`); separate explicit approval for Phase 11 |
| R92 — an unmeetable AC is "handled" by weakening it | M / H | Rule 10 (D47.9/`AC-D47.9`): escalate + record as a parity row; Code Reviewer fails any phase whose matrix row regresses without an escalation |

### Architecture Decisions (relationship-labelled)

| # | Decision | Relationship |
|---|---|---|
| S51 | The `ChartView` seam: protocol + `DrawingController`/`AlarmController` exact signal signatures + `create_chart_view(tz_offset, editable)` on `NDT_CHART_ENGINE` (pyqtgraph default, lwc) or `QSettings`. Unknown/unset value falls back to pyqtgraph — never a blank chart. Rationale: the decline's own sanctioned route ("a second chart mode behind the existing interface"); the factory default keeps every existing suite meaningful through Phase 10. Alternative: flag-day swap (rejected: no fallback, no parity gate). | `[new in P6]` — D47.1/`AC-D47.1` |
| S52 | The shared Qt-free `ChartModel`: plotted-index filtering, `floor_bar_budget`, whitespace derivation, studies + `_StudyCache`, Heikin-Ashi, volume formatting. `ChartPanel` delegates with no behaviour change — the full pre-D47 chart suites stay green unmodified. Rationale: one value source (R86); Qt-free keeps it offscreen-testable. Alternative: dual logic (rejected). | `[new in P6]` — D47.2/`AC-D47.2` |
| S53 | The vendored offline host: `QWebEngineView` + lightweight-charts v5.2.x via `ndt://` (registered before `QApplication`) + deny-default interceptor + attribution. Rationale: determinism + auditability (AC-D47.3). Alternative: CDN (rejected). | `[new in P6]` — D47.3/`AC-D47.3` |
| S54 | The batched self-healing bridge: `QWebChannel` `LwBridge`, `{v:1,ops:[]}`, queue-until-ready, ~33ms coalesce, local gestures, full-log replay after `renderProcessTerminated`, with backpressure counters from Phase 2. Rationale: bounded crossing cost + crash recovery without divergence (AC-D47.4, DG91). Alternative: sync per-call bridge (rejected). | `[new in P6]` — D47.4/`AC-D47.4` |
| S55 | Time/panes/series mapping: panes (v5), logical-index axis, whitespace for within-session holes, `gap_is_non_trading` as the authority in both engines, custom tz formatters, per-mode series, `series.update` for the live bar. Rationale: parity on values, not looks (AC-D47.5, DG93). Alternative: wall-clock axis (rejected). | `[new in P6]` — D47.5/`AC-D47.5` |
| S56 | Density language becomes `barSpacing`: the pyqtgraph density-cap wording of `AC-D6.4`/`AC-D7.1`/`AC-D9.1` is retired via T10 on the Q60 answered-by-default YES, with the no-overlap guarantee restated in `barSpacing` terms (DG94) and a rendered-geometry guard that survives the engine change. The pyqtgraph engine keeps satisfying the old ACs until cutover. Rationale: the engine owns spacing (D47.6, R89). Alternative: dual wording (rejected). | `[revises D42: S13]` — D47.6/`AC-D47.6`, recorded supersession, not silent |
| S57 | Controls/router/drawings keep their contracts: in-HTML controls with Python shims, Python `RouterMode` + JS mirror (mirror never reinterprets TR-1…TR-17), drawings via a primitives library (ts-to-fractional-index), Qt dialogs stay. Crosshair drifts to the library-native crosshair + axis label (Q63/A108 — D2/Q33 stands only where still applicable). Rationale: settled UX untouched (AC-D47.7, DG92). Alternative: HTML dialogs / JS-owned router (rejected). | `[new in P6]` — D47.7/`AC-D47.7` |
| S58 | Delivery in Phases 0–11 with the 19-row parity matrix kept updated and rule 10 governing the unmeetable: spike + go/no-go record before Phase 1; each phase exit updates the matrix (`docs/lwc_parity_matrix.md`); an unmeetable AC is escalated + recorded as a parity row, never silently dropped. Rationale: the gate is the product (D47.9, DG95). Alternative: phase exits without matrix updates (rejected). | `[new in P6]` — D47.8/`AC-D47.8`, D47.9/`AC-D47.9` |
| S59 | Cutover and removal gates: cutover = owner accept **and** parity all Done/accepted **and** Phase-0 perf holds (no soak, by explicit owner decision); Phase 11 (pyqtgraph deletion) executes only on explicit owner approval after one live trading session with no engine defect. Out of scope stays out (`ibkr/`, schemas, persistence, watchlist, dock, order code, paid library, aggregation/backfill). History preserved (D41–D46 + reversals, marker sentence, Current Tech Stack extended not replaced, `ESC-061` moot). Rationale: D47.11–D47.13. Alternative: calendar soak (rejected by owner); bundled deletion (rejected). | `[extends P5: end state]` — D47.11–D47.13/`AC-D47.6`/`AC-D47.8`/`AC-D47.9`; builds on the P5 baseline without changing any P5 decision |
| S60 | Pyramid tests + webengine discipline: pure-Python suites, `node --test` JS suites, a few `@pytest.mark.webengine` cases (skip-never-red), the manual checklist as the gate where no engine exists (DG88); the 66 chart-adjacent test files are classified keep/retarget/engine-specific by the Task Manager per the attached plan. Phase 0 additionally reports the measured `.app` size delta + signing-flow finding (A109/DG89). Rationale: D47.10, Q61–Q63. Alternative: engine-mandatory CI (rejected). | `[new in P6]` — D47.10/`AC-D47.10` |

## Phase P7 — data-path batch: historical backfill correct + fast, streaming correct (no holes, no duplicates, no dropped/late bars)

> Companion: `docs/plan.md` § *Phase P7* (waves P7-W1…P7-W4, traceability, assumptions, flagged issues).
> Requirements input: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`); the P7 state brief
> (native-ibapi probe evidence — SPY 1-min 30 D in ~1.1 s, AAPL 1-min 2–3 D complete — proving the 90 s
> zero-bar timeouts were our own bugs: missing reader thread, pre-handshake requests → 504, both understood);
> open Code Reviewer escalations **ESC-075/076/077/078** (`routed_to: BUILD`) and **ESC-079** (`routed_to: PLAN`).
> Existing-repo run: the Current Tech Stack is a hard constraint; every item below carries
> `[existing]` / `[new]` / `[new/changed]`. P7 lands **no new module and no new dependency** — every change is
> in-place inside the modules named below. One phase only: nothing past the P7 build wave is planned here.

### Codebase Summary (existing repository — what P7 changes, verified against the current tree)

- `[existing] ibkr/market_data.py::MarketDataManager` — `TIMEFRAME_CONFIG` per-request durations
  (`"1 min": "1 D"`, `"5 mins"/"15 mins": "5 D"`, `"1 hour": "10 D"`, `"4 hours": "30 D"`, `"1 day": "1 Y"`);
  `req_historical_data(...)` (handshake gate via `IBKRNotReady`, `id_manager.get_id()`, `pacing_manager` throttle,
  `duration`/`bar_size` overrides for D27.9 priming) and `req_mkt_data(contract, generic_ticks="")`
  (Q-41 non-blocking pacing contract, `PacingExceeded` + `QTimer.singleShot` deferral).
- `[existing] config/settings.py` — the pacing tunables P7 budgets against: `MAX_HISTORICAL_PER_600S = 100`,
  `HISTORICAL_MIN_INTERVAL_S = 0.5`, `MIN_INTRADAY_SESSIONS = 30`, `SESSION_BAR_CAP = 5000`
  (note: ESC-075's text cites a 50-slot budget — the tree carries 100; S-P7-1 states the invariant as a
  **fraction of the tunable** so it survives retunes either way).
- `[existing] ui/ticker_session.py::TickerSession` — the history-wave lifecycle P7 reworks in place:
  the req-id registry + `_pending_bars` accumulation, `_wave_plan_queue`, the watchdog
  (`_history_stranded_reason`), generation fencing, and the D27.9 priming state (`_prime_req_id`,
  `_prime_timer`, `_prime_retry_pending`). Finalisation today is all-or-nothing
  (`MainWindow._finalize_history_wave` runs only when the queue and id set drain).
- `[existing] services/backfill_service.py` — the pure planner: `find_missing_spans`, `plan_requests`,
  `floor_bar_budget`, `bar_period_seconds` (`MissingSpan`/`RequestPlan`). P7 keeps the planner pure and
  Qt-free; the **orchestration** around it changes, not its function contracts.
- `[existing] ibkr/realtime_bars.py::RealtimeBarsManager` (`subscribe`/`unsubscribe`/`cancel_all`/`replay_all`),
  `[existing] ibkr/stream_health.py::StreamHealth` (`mark_subscribed`/`mark_first_bar`/`mark_failed`/`is_live`/
  backoff), `[existing] ibkr/pacing.py` (`PacingManager`/`PacingExceeded`), `[existing] data/bar_cache.py`
  (`save_bars`/`get_bars`/mode-aware key), `[existing] services/contract_lookup_service.py` +
  `services/symbol_search.py` (the Q-45 watchlist-add deferral, landed `cd4266a`).
- `[existing]` the landed-and-frozen substrate P7 builds on and does not touch: handshake-gated readiness
  (`IBKRNotReady`, Q-35), the 0.5 s interval + rolling budget (Q-30), error-162 retry, S0/D38 removal end state,
  the Qt-free import boundary (`test_t38_t08`), the per-view WebEngine profile (Q-40), the D27 reconnect-replay
  path, and the LWC chart stack (`ui/chart_view.py`, `services/chart_model.py`, `ui/lwc_host.py`,
  `ui/lwc_bridge.py`, `ui/lwc_view.py`) — the renderer consumes the data path, P7 never edits it.

### Summary

Stop treating a wide backfill as one giant wave: cap what a single load may spend, persist and render every
chunk as it arrives, resume instead of restarting, and express all wave/watchdog bounds in budget-window terms.
Then take the probe's single-shot win (a wide 1-min duration covering the 30-session floor in one request) only
as an explicit, measured, owner-approved decision — and close out streaming (prime precedence, watchdog/pacing
coherence, reconnect replay, the Q-41 deferral contract) without touching the renderer, the schema, or the
order-code absence.

### Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Constrained stack first | Unchanged: Python 3.11+, PyQt6, `ibapi-latest==10.51.1`, SQLite, LWC chart stack | Existing-repo hard constraint; the data path needs no new capability | Any replacement — rejected outright |
| Chunk transport | Unchanged `reqHistoricalData` via `MarketDataManager` ( pacing-counted, handshake-gated) | The probe proves TWS serves wide requests fast; the bug is our orchestration, not the transport | New transport / parallel connections — rejected (pacing budget is per-connection; more sockets burn it faster) |
| Wide durations (S-P7-5) | Additive duration widening (e.g. `"1 min"` → `"30 D"`) as an explicit owner-gated decision with measured before/after, never a silent constants edit | The probe proves one 30 D request replaces ~31 floor chunks; silent edits hide a pacing-behaviour change from the owner | Keep 1 D chunking (rejected: 42 requests/load, 45 s of silence); widen silently (rejected: owner-approval rule from the brief) |

### System Components

- `[new/changed] ui/ticker_session.py::TickerSession` history-wave orchestration — per-chunk persist+render,
  resume-not-restart, coalesced same-chart reloads, watchdog/pacing coherence, prime precedence.
- `[new/changed] ui/main_window.py` load/finalise path — incremental finalisation per chunk instead of
  all-or-nothing `_finalize_history_wave`; cancelled-slot accounting.
- `[existing] services/backfill_service.py` — planner contracts unchanged; called more often (per resume) with
  the same pure semantics.
- `[existing] ibkr/market_data.py` request path — signature and pacing contract unchanged; only the
  `duration` argument values change (owner-gated, S-P7-5).
- `[existing] ibkr/realtime_bars.py` + `ibkr/stream_health.py` + D27 reconnect replay — behaviour re-affirmed,
  no redesign; prime precedence is a scheduling rule, not a new component.
- `[existing] LWC chart stack` (`ui/chart_view.py`, `services/chart_model.py`, `ui/lwc_*`) — untouched consumer.

### Data Model

- `[existing]` `bars` table (`PRIMARY KEY (symbol, timeframe, ts)`, mode-aware key per D42) — **no migration**;
  incremental per-chunk `save_bars` is idempotent by `INSERT OR REPLACE`, which is exactly what makes
  resume-not-restart safe.
- `[existing]` `Bar` dataclass, `SESSION_BAR_CAP = 5000` bound, retention/prune — unchanged.
- `[new]` In-memory wave accounting only (no new table): per-wave spent-slot count, refunded-cancel count,
  162-ack maintained-as-debug classification. Nothing persists beyond the existing cache.

### Integration Points

- `[existing]` TWS historical data (`reqHistoricalData`) — same call shape; fewer, wider requests after S-P7-5.
- `[existing]` TWS real-time bars + `reqMktData` watchlist/watchlist-panel defer (Q-45, landed) — unchanged.
- `[existing]` SQLite bar cache — same API; written incrementally instead of once per wave.
- No new external service, endpoint, credential, or dependency. Live validation stays **read-only**; the owner
  names the validation method.

### Frozen Interfaces

Every entry below is `[existing]` and **unmodified by every P7 wave**. Task Manager gives workers the contract,
never the implementation. The repository is authoritative on conflict.

- **`ibkr/market_data.py::MarketDataManager.req_historical_data`** — contract:
  `req_historical_data(self, contract: Contract, timeframe: str = "5 mins", endDateTime: str = "", whatToShow: str = "TRADES", useRTH: int = 1, extended_hours: bool = False, bar_size: str | None = None, duration: str | None = None) -> int`. Owner: `ibkr/market_data.py`. (Only the *passed* `duration` values change, owner-gated; the signature, handshake gate, and pacing contract do not.)
- **`ibkr/market_data.py::MarketDataManager.req_mkt_data`** — contract:
  `req_mkt_data(self, contract: Contract, generic_ticks: str = "") -> int` with the Q-41 non-blocking
  contract (`PacingExceeded` + `QTimer.singleShot` deferral, never sleeps on the GUI thread).
  Owner: `ibkr/market_data.py`.
- **`services/backfill_service.py` planner contracts** — contracts: `find_missing_spans(cached_ts, now_ts,
  timeframe, trailing_days, ext_hours, min_sessions)`, `plan_requests(missing_spans, timeframe)`,
  `floor_bar_budget(timeframe, ext_hours)`, `bar_period_seconds(timeframe)`. Owner:
  `services/backfill_service.py`. (Pure, Qt-free; orchestration changes around them, signatures do not.)
- **`config/settings.py` pacing tunables exist** — contracts: `MAX_HISTORICAL_PER_600S`,
  `HISTORICAL_MIN_INTERVAL_S`, `MIN_INTRADAY_SESSIONS`, `SESSION_BAR_CAP` exist with current values
  (100 / 0.5 s / 30 / 5000); `check_live_port` fails fast unless `IBKR_PORT == 7496`.
  Owner: `config/settings.py`. (S-P7-5 may change a `TIMEFRAME_CONFIG` *duration value* only, never these.)
- **`ibkr/error_codes.py::classify_error` + `IBApiClient.error`/`error_msg`** — the error ingress, severity
  gate, and status-bar line (incl. error-162 handling). Owner: `ibkr/`. (162-ack-as-debug is a *call-site
  classification*, not a change to the classifier.)
- **`ibkr/realtime_bars.py::RealtimeBarsManager` + `ibkr/stream_health.py::StreamHealth`** — contracts:
  `subscribe`/`unsubscribe`/`cancel_all`/`replay_all`; `mark_subscribed`/`mark_first_bar`/`mark_failed`/
  `is_live`/`describe` + backoff. Owner: `ibkr/`. (Scheduling around them changes; the APIs do not.)
- **`data/bar_cache.py::BarCache.save_bars` / `::get_bars`** — contracts:
  `save_bars(bars, ext_hours=True)`; `get_bars(symbol, timeframe, ext_hours=True)`. Owner: `data/bar_cache.py`.
  (Called per chunk instead of per wave; the API does not change.)
- **Qt-free import boundary** — contract: `data/` + `services/` import without Qt (`test_t38_t08`).
  Owner: the boundary itself. (New wave code in `ui/` must not leak Qt into planner logic.)
- **Order-code absence** — contract: `import ibkr.orders` raises `ModuleNotFoundError`; no `placeOrder`/
  `cancelOrder`/`reqGlobalCancel` call site, no order UI. Owner: the P5 end state. (P7 adds zero order
  interaction; D45/D46 stand.)
- **LWC chart stack seam** — contract: `ui/chart_view.py::create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView`, `services/chart_model.py`
  value objects, `RouterMode` TR-1…TR-17, per-view WebEngine profile (Q-40). Owner: `ui/` + `services/`.
  (The data path feeds the seam; no P7 task edits the renderer.)

### Non-Functional Approach

- **Performance (driven by the probe + ESC-075):** the per-load cap (S-P7-1) bounds worst-case time-to-first-bars;
  per-chunk persist+render bounds time-to-visible-progress to one chunk latency; the wide-duration decision
  (S-P7-5) removes ~31 floor requests for `"1 min"` where TWS proves it serves them in ~1 s, while the 0.5 s
  minimum interval and the rolling budget keep pacing legal. No GUI-thread blocking anywhere (Q-41 deferral
  contract re-affirmed).
- **Correctness (driven by ESC-075/076/077/078 + D16/D42):** no holes (floor + gap repair preserved across
  resumes), no duplicates (`INSERT OR REPLACE` idempotence + oldest-first monotonic fill), no dropped/late bars
  (aggregator priming intact, prime precedence explicit), reconnect replays intact (D27 path untouched).
- **Security/scalability:** no new surface (no dependency, no endpoint, no credential); read-only live
  validation; the budget invariant is per-load so pop-outs, headless alarm sessions, and the watchlist share
  the same rolling window without starving each other.
- **Stability gate:** the full offscreen suite stays green on every wave; live validation is read-only and the
  owner names the method — a red suite or an unapproved live step fails the wave.

### Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| AR-P7-1 — the per-load cap throttles the floor fill so visibly that the chart looks perpetually "catching up" | M / M | Oldest-first monotonic fill + per-chunk render: every load shows progress; the floor completes across loads instead of one 45 s silence (S-P7-1/S-P7-2) |
| AR-P7-2 — incremental persist/render reintroduces flicker or partial-write visibility the all-or-nothing finalise avoided | M / M | Single save + set per completed chunk (never per bar); generation fencing unchanged so a superseded wave cannot paint over the current one |
| AR-P7-3 — wide durations hit an undocumented TWS limit for some symbol/timeframe and return short/empty with no error | M / H | S-P7-5 is measured before/after per affected timeframe with a rollback to chained requests on any shortfall; shortfall stays a surfaced status-bar message, never a silent hole (AC-D16.4) |
| AR-P7-4 — refunding cancelled slots over-counts the budget and trips a real 162 storm | H / L | Refund only slots whose reqId never reached TWS (pre-issue cancel); post-issue cancels keep their slot; pacing_manager stays the single owner |
| AR-P7-5 — prime precedence delays the wave enough to look like a stall, or a skipped prime hides a real defect | L / M | Precedence is exactly one interval (bounded, S-P7-4); a skipped prime is warning-level and counted, never logged as the expected case |
| AR-P7-6 — P7 "fixes" streaming by redesigning D27 reconnect replay or the Q-41 deferral contract | M / H | Both are Frozen Interfaces above; P7 schedules *around* them (watchdog bound ≥ continuation delay + margin) and re-affirms them with tests |

### Architecture Decisions (relationship-labelled)

| # | Decision | Relationship |
|---|---|---|
| S-P7-1 | **Budget invariant + per-load cap (answers ESC-079):** a single chart load consumes at most **one quarter** of `MAX_HISTORICAL_PER_600S` rolling slots; the 30-session depth floor (`AC-D16.8`) is satisfied **monotonically across loads** (persist-and-resume, oldest-first), never inside one wave; wave/watchdog/continuation bounds are expressed in **budget-window terms** (fractions of the 600 s window), not literal seconds. Rationale: binds every historical-request consumer (pop-outs, headless alarm sessions, watchlist, prime) to one rule; survives tunable retunes (50 vs 100). Alternative: a per-timeframe special case (rejected — ESC-079's suggested direction forbids it). | `[new in P7]` — ESC-079; restates the *reading* of `AC-D16.8` (flagged for the Analyst, not rewritten here) |
| S-P7-2 | **Persist-and-render per chunk + resume-not-restart (code side of ESC-075/076):** each completed chunk is `save_bars`-persisted and rendered on arrival; a reload for the same symbol/timeframe/mode **coalesces into** the running wave (no cancel, no re-spend); a genuinely cancelled slot is refunded **only if its request never reached TWS**, and a 162 acknowledgement for a superseded reqId is classified debug, not a user-facing error. Rationale: fetched bars are never thrown away (the measured 42-request/44.7 s/45 s-silence failure); `INSERT OR REPLACE` idempotence makes resume safe. Alternative: keep all-or-nothing finalise (rejected — it is the defect). | `[new in P7]` — ESC-075/076; changes `TickerSession` wave lifecycle + `MainWindow` finalise path |
| S-P7-3 | **Watchdog/pacing coherence (code side of ESC-077):** the stranded-wave watchdog bound is **≥ the scheduled continuation delay + margin**; a strand clears the continuation timer **and** the plan queue so a finalised wave cannot resume. Rationale: a wave legitimately waiting on pacing must never read as stranded. Alternative: longer fixed timeouts (rejected — they rot when tunables change; window-relative bounds do not). | `[new in P7]` — ESC-077; changes watchdog/continuation wiring only |
| S-P7-4 | **Prime precedence (code side of ESC-078):** the D27.9 aggregator prime takes precedence — the backfill wave defers its continuation by **exactly one** `HISTORICAL_MIN_INTERVAL_S` so the prime issues — or the prime holds an explicit reservation; a skipped prime is warning-level and counted. Rationale: the prime must never starve behind the wave it was started alongside. Alternative: prime-inside-wave ordering (rejected — couples the pure planner to transport scheduling). | `[new in P7]` — ESC-078; scheduling rule, no planner/API change |
| S-P7-5 | **Wide-duration decision point (owner-gated):** widening `"1 min"` (and any other) `TIMEFRAME_CONFIG` duration (e.g. `"1 D"` → `"30 D"`, covering the 30-session floor in one shot) lands **only as an explicit decision with measured before/after** (request count, time-to-first-bar, time-to-current, pacing-slot spend) **and owner approval** — never a silent constants edit; pacing (0.5 s interval, rolling budget, no GUI-thread sleep) is re-verified with the wide request in place. Rationale: the probe proves the win (~1.1 s for 11,644 bars) but duration is owner-visible pacing behaviour. Alternative: silent widening (rejected — the brief forbids it). | `[new in P7]` — probe evidence; changes duration *values* only, under gate |
| S-P7-6 | **Streaming re-affirmation, not redesign:** `reqMktData` watchlist/watchlist-panel defer (Q-45, landed), realtime-bars aggregator priming, `StreamHealth` state + backoff, D27 reconnect replay, and the Q-41 pacing-deferral contract keep their current design; P7 adds only the scheduling rules in S-P7-3/S-P7-4 and regression coverage. Rationale: streaming is correct-by-construction today except for the starved-prime and watchdog misreads. Alternative: streaming redesign (rejected — out of scope). | `[extends prior phases: D27/D28 streaming path]` — Q-41/Q-45/D27; re-affirmed, not re-planned |
| S-P7-7 | **Landed substrate stays frozen:** `IBKRNotReady` handshake gate (Q-35), 0.5 s interval + rolling budget (Q-30), error-162 retry, S0/D38 removal end state, Qt-free import boundary (`test_t38_t08`), per-view WebEngine profile (Q-40), zero order code (D45/D46), LWC renderer seam. Rationale: the brief excludes all of them from re-planning. Alternative: none entertained. | `[extends P6: end state]` — all prior phases; frozen |

## Phase P8 — D48 increment: add `1 week` (2Y) and `1 month` (10Y) timeframes — drafted 2026-10-28

> Companion: `docs/plan.md` § *Phase P8* (waves P8-W1…P8-W3, traceability, assumptions, flagged issues).
> Requirements input: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Batch 23 (D48),
> Journey 41, `AC-D48.1`–`AC-D48.7`, lite defaults A113–A120, R93–R95, `design_gaps.md` DG97–DG98.
> Existing-repo run: the Current Tech Stack is a hard constraint; every item below carries
> `[existing]` / `[new]` / `[new/changed]`. **D1–D47 are NOT reopened** beyond the recorded
> timeframe-enumeration extension (`AC-D16.1`'s "all six timeframes" now reads eight; the D43/Q53
> `AC-D27.9` per-span table gains two rows). One phase only — nothing past the P8 build wave is planned.
> Open PLAN escalation check: `docs/code_review/escalations.json` holds exactly one `routed_to: PLAN`
> + `open` entry (**ESC-079**), which Phase P7 already answers (S-P7-1, `Status: READY_FOR_TASK_MANAGER`);
> it is P7 scope and is not re-planned here.

### Codebase Summary (existing repository — what P8 changes, verified against the current tree)

> Pointer: the full module index is `docs/codebase-map.md` (skeleton re-run 2026-10-28 for P8; no new
> modules land in P8, so annotations carry forward). The deltas below are the complete P8 surface,
> each verified in source this run (the repository is authoritative):

- `[existing] ibkr/market_data.py::TIMEFRAME_CONFIG` — six rows (`1 min`→`30 D`/`1 min`,
  `5 mins`→`30 D`/`5 mins`, `15 mins`→`30 D`/`15 mins`, `1 hour`→`60 D`/`1 hour`,
  `4 hours`→`60 D`/`4 hours`, `1 day`→`1 Y`/`1 day`); `req_historical_data` falls back to the
  `5 mins` row for unknown timeframes and already accepts `duration`/`bar_size` overrides.
- `[existing] data/bar_aggregator.py::TIMEFRAME_SECONDS` — seven keys (`5 secs` + the six timeframe
  periods); `_ET_ANCHORED_TIMEFRAMES = frozenset({"1 day", "4 hours"})` (fixed-seconds ET-midnight
  grid); `_period_start(ts, seconds, timeframe)` (UTC-epoch grid for everything else).
- `[existing] services/backfill_service.py` — `floor_bar_budget` returns the flat cap when
  `period >= 86400` (daily+ already excluded); `find_missing_spans` enables the `AC-D16.8` floor only
  when `min_sessions > 0 and bar_period_seconds(timeframe) < 86400` (intraday-only, already generic);
  `plan_requests` chunks by the configured duration via `_duration_to_seconds` (Y units already parse —
  `1 Y` flows through it today); `bar_period_seconds` reads `TIMEFRAME_SECONDS` with a `5 mins` fallback.
- `[existing] ui/ticker_session.py::prime_aggregator` — span-based branches (`span_s <= 3600` →
  `5 secs`/`[60 S, 3600 S]`; longer → `1 min`/`[60 S, 1 D]`), already generic over any span.
- `[existing] ui/main_window.py` load path — `tf_combo.addItems(list(TIMEFRAME_CONFIG.keys()))`
  (picker follows config order); per-load `BarCache.get_bars(symbol, timeframe, ext_hours=mode)`,
  `find_missing_spans(..., ext_hours=mode, min_sessions=30)`, `queue_wave_plans(..., extended_hours)`,
  `prime_aggregator(..., extended_hours)`; `_on_ext_hours_toggled` reloads on every toggle.
- `[existing]` the six `== "1 day"` daily-gates: `services/session_service.py` ×2
  (`session_bands`, `session_bands_for_range`), `services/time_collapse_service.py::IDENTITY_TIMEFRAME`
  (+ `extend` identity branch), `ui/lwc_view.py::session_regions`.
- `[existing] services/chart_model.py` — `plotted_index_rows`/`is_bar_plotted` filter through
  `session_windows` for any timeframe present in `TIMEFRAME_SECONDS`; `collapse_for_bars` delegates
  to `build_collapse_map` for any known timeframe.
- `[existing] services/volume_baseline.py::minutes_for_timeframe` — `"1 day"` → 390.0, else
  `secs/60` with a 1.0 fallback (no crash on unknown keys, but nominal-seconds math).
- `[existing] ui/drawing_settings_common.py::VISIBILITY_ROWS` — six **duration-unit** rows
  (Seconds/Minutes/Hours/Days/Weeks/Months), not per-timeframe rows; `VisibilityTab`
  (`get_visibility`/`set_visibility`) round-trips a checkbox dict into the drawing payload; **no
  render-time consumer** maps the current timeframe to a row (verified: zero readers in `services/`,
  `chart_assets/`, `ui/` outside the two settings dialogs).
- `[existing]` generic timeframe carriers (no enumeration, no change): drawing/alarm/popout/study
  stores keyed by free-form timeframe strings; `services/chart_model.py` value objects.

### Summary

Add two `TIMEFRAME_CONFIG` rows and teach the aggregator Monday-anchored weekly and calendar-month
bucketing; everything downstream already keys off period length, so the planner, the priming table,
and the depth floor need no logic change — only new keys to read. Canonicalise daily-and-coarser
loads to one shared full-session mode so RTH/ETH is a true no-op, extend the existing daily identity
rules to the two new timeframes through one shared predicate, and gate the whole batch on a
standalone IBKR probe plus the green suite.

### Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Constrained stack first | Unchanged: Python 3.11+, PyQt6, `ibapi-latest==10.51.1`, SQLite, LWC chart stack | Existing-repo hard constraint; two timeframe rows need no new capability | Any replacement — rejected outright |
| Bar-size/duration source | IBKR-native `1 week` / `1 month` bar sizes with `2 Y` / `10 Y` durations inside `TIMEFRAME_CONFIG` (A113/A116) | Owner-specified spans; the year-unit spelling is inside IBKR's duration vocabulary (`_duration_to_seconds` already parses `1 Y`) and the probe (`AC-D48.6`) verifies acceptance | Day-count durations (rejected — A116 records year units; a probe rejection escalates per R93, never a silent shrink) |
| No new dependency, no schema migration, no order code | Nothing added, nothing migrated | The batch is pure timeframe-surface; the Qt-free boundary and the P5 order absence stay intact | Any new table/column/dependency — rejected (nothing persists beyond the existing `bars` rows keyed by the new timeframe strings) |

### System Components

- `[new/changed] ibkr/market_data.py::TIMEFRAME_CONFIG` — gains exactly two rows
  (`1 week` → `1 week`/`2 Y`; `1 month` → `1 month`/`10 Y`), appended after `1 day` so the picker,
  which builds from `list(TIMEFRAME_CONFIG.keys())`, orders them per A119 with no picker code change.
- `[new/changed] data/bar_aggregator.py` — gains Monday-00:00-ET weekly bucketing and
  calendar-month-boundary monthly bucketing (S-P8-2); `TIMEFRAME_SECONDS` gains the two nominal keys
  (604800 / 2592000, A115) for fixed-seconds consumers only.
- `[existing] services/backfill_service.py` — planner contracts unchanged; the floor gating is already
  period-based so weekly/monthly skip `AC-D16.8` with no code change (S-P8-3).
- `[new/changed] ui/main_window.py` load path — daily-and-coarser loads canonicalise to one shared
  full-session mode for the cache read/write, the planner call, the wave, and the prime (S-P8-4).
- `[new/changed] services/session_service.py`, `services/time_collapse_service.py`,
  `services/chart_model.py`, `ui/lwc_view.py` — the six `== "1 day"` gates plus the chart-model
  membership branches adopt one shared daily-or-coarser predicate (S-P8-4).
- `[new/changed] services/volume_baseline.py::minutes_for_timeframe` — explicit weekly/monthly
  regular-session minutes (S-P8-7); every other baseline path unchanged.
- `[existing] ui/drawing_settings_common.py::VisibilityTab` + zone/horizontal dialogs — unchanged;
  the unit rows already span Weeks/Months and no consumer maps timeframe→row (S-P8-6).
- `[existing] ui/ticker_session.py::prime_aggregator` — unchanged logic; the docstring per-span table
  gains the two new rows documenting the existing coarse branch (S-P8-5).

### Data Model

- `[existing]` `bars` table (`PRIMARY KEY (symbol, timeframe, ts)`, mode-aware key per D42) — **no
  migration**; weekly/monthly rows persist under the new timeframe strings and share one canonical
  mode (S-P8-4), so no cache fork.
- `[existing]` `Bar` dataclass, `SESSION_BAR_CAP = 5000` bound, retention/prune — unchanged; a 2Y
  weekly series (~104 bars) and a 10Y monthly series (~120 bars) sit far below every cap.
- `[new]` In-memory calendar anchoring only (week-start / month-start ET helpers in the aggregator);
  nothing persists beyond the existing cache.

### Integration Points

- `[existing]` TWS historical data (`reqHistoricalData`) — same call shape; two new
  (`duration`, `bar_size`) combos, both probe-verified before the batch passes (`AC-D48.6`).
- `[existing]` TWS real-time bars — the live 5-sec feed still primes the forming weekly/monthly bar
  through the existing `prime_aggregator` coarse branch; no new subscription type.
- `[existing]` SQLite bar cache — same API; written/read under the canonical daily+ mode.
- No new external service, endpoint, credential, or dependency. Live validation stays **read-only**;
  the probe issues historical requests only.

### Frozen Interfaces

Every entry below is `[existing]` and **unmodified by every P8 wave**. Task Manager gives workers the
contract, never the implementation. The repository is authoritative on conflict.

- **`ibkr/market_data.py::MarketDataManager.req_historical_data`** — contract:
  `req_historical_data(self, contract: Contract, timeframe: str = "5 mins", endDateTime: str = "", whatToShow: str = "TRADES", useRTH: int = 1, extended_hours: bool = False, bar_size: str | None = None, duration: str | None = None) -> int`. Owner: `ibkr/market_data.py`. (Only the *configured* `duration`/`bar_size` values for the two new keys are added; the signature, handshake gate, and pacing contract do not change; the `5 mins` unknown-timeframe fallback is untouched.)
- **`ibkr/market_data.py::TIMEFRAME_CONFIG` existing six rows** — contract: the six
  `duration`/`bar_size` pairs verified above are byte-identical after P8; exactly two rows are added.
  Owner: `ibkr/market_data.py`.
- **`data/bar_aggregator.py::TIMEFRAME_SECONDS` existing seven keys + `_period_start` grid** — contract:
  the seven existing periods and the UTC-epoch-vs-ET-midnight branch keep their values; weekly/monthly
  bucketing is additive calendar logic beside them. Owner: `data/bar_aggregator.py`.
- **`services/backfill_service.py` planner contracts** — contracts: `find_missing_spans` (with the
  `min_sessions > 0 and bar_period_seconds(timeframe) < 86400` intraday-only floor gate),
  `plan_requests` (chunking by configured duration), `floor_bar_budget` (flat cap at
  `period >= 86400`), `bar_period_seconds`. Owner: `services/backfill_service.py`. (Pure, Qt-free;
  no signature or gating change.)
- **`ui/ticker_session.py::prime_aggregator` span branches** — contract: `span_s <= 3600` →
  `5 secs`/`[60 S, 3600 S]`; longer spans → `1 min`/`[60 S, 1 D]`; `period_s <= 5` early-out; replay
  guard on `_prime_period_start`. Owner: `ui/ticker_session.py`. (Weekly/monthly spans land in the
  existing coarse branch; only the docstring table gains rows.)
- **`data/bar_cache.py::BarCache.save_bars` / `::get_bars`** — same API as frozen in P7; called with
  the canonical daily+ mode. Owner: `data/bar_cache.py`.
- **`config/settings.py` pacing tunables + `check_live_port`** — contracts unchanged (P7 frozen row
  carried forward). Owner: `config/settings.py`.
- **Drawing/alarm visibility payload shape** — contract: `VisibilityTab.get_visibility()` /
  `set_visibility()` dict shape (`Ticks`, six unit checkboxes, `Ranges`, `*_lo`/`*_hi` bounds) is
  unchanged; no per-timeframe key exists. Owner: `ui/drawing_settings_common.py`.
- **Qt-free import boundary** — contract: `data/` + `services/` import without Qt (`test_t38_t08`).
  Owner: the boundary itself. (New aggregator calendar math stays in `services/`/`data/`.)
- **Order-code absence** — contract: `import ibkr.orders` raises `ModuleNotFoundError`; no
  `placeOrder`/`cancelOrder`/`reqGlobalCancel` call site, no order UI. Owner: the P5 end state.
  (P8 adds zero order interaction; D45/D46 stand.)
- **LWC chart stack seam** — contract: `ui/chart_view.py::create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView`, `services/chart_model.py` value objects, `RouterMode`
  TR-1…TR-17. Owner: `ui/` + `services/`. (The data path feeds the seam; no P8 task edits the renderer.)

### Non-Functional Approach

- **Performance (driven by D48.3 + the probe):** a 2Y weekly span is ~104 bars and a 10Y monthly span
  ~120 bars — trivially below `SESSION_BAR_CAP`; `plan_requests` chunking by the configured duration
  yields ~1 chunk per span when the probe passes, so the new timeframes cost the budget almost nothing.
  No GUI-thread blocking anywhere (the P7 wave/prime rules are untouched and apply unchanged).
- **Correctness (driven by AC-D48.2/AC-D48.4 + R94):** calendar-anchored bucketing (Monday ET /
  month boundary) with unit cases over a DST fold, February, and a Dec/Jan boundary; the daily+
  predicate keeps bands, collapse, plotted-filtering, and session regions identical under both modes;
  the canonical cache mode makes RTH/ETH parity structural, not asserted-by-luck.
- **Security/scalability:** no new surface (no dependency, no endpoint, no credential); read-only
  live validation; the probe is the only live step and issues historical requests only.
- **Stability gate:** the full offscreen suite stays green on every wave; a 321-class probe rejection
  fails the wave and escalates to Requirements (R93) — durations are never silently shrunk.

### Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| AR-P8-1 — IBKR rejects one of the new combos (321-class, as in ESC-036) | M / L | `AC-D48.6`: the standalone probe verifies both combos before the batch passes; a rejection escalates to Requirements — durations are never silently shrunk (R93, S-P8-5) |
| AR-P8-2 — fixed-seconds month bucketing drifts real month boundaries (28–31-day months, February) | M / L | Calendar-month anchoring (S-P8-2); nominal 30-day seconds only where an API demands fixed seconds, never for bucketing (A115); `AC-D48.2` Feb unit case (R94) |
| AR-P8-3 — a hardcoded six-timeframe enumeration misses the new entries (R95) | M / M | The R95 inventory is the checklist (S-P8-4/S-P8-6): config, aggregator, predicate sites, chart model, session regions, minutes mapping, picker order; `AC-D48.5`/`AC-D48.7` are the gates |
| AR-P8-4 — IBKR's native weekly/monthly anchors differ from Monday-ET / calendar-month (cf. the D27.8 4h-caveat precedent) | L / M | AP-P8-1 records the assumption; first-load bar-to-bar comparison against IBKR history is the check; a systematic phase mismatch becomes a follow-up, never a silent re-anchor |
| AR-P8-5 — weekly/monthly volume-burst baselines stay thin (few buckets, sparse samples) | L / L | Explicit RTH-session minutes keep the per-minute contract honest (S-P8-7); burst evaluation is timeframe-generic and self-consistent; no baseline redesign |

### Architecture Decisions (relationship-labelled)

| # | Decision | Relationship |
|---|---|---|
| S-P8-1 | **Config rows + picker order (D48.1/D48.5):** `TIMEFRAME_CONFIG` gains exactly `1 week` → `1 week`/`2 Y` and `1 month` → `1 month`/`10 Y`, appended after `1 day`; the picker follows config order with no code change (A119). Rationale: owner-specified spans (A113) in IBKR year units (A116); insertion order is the existing ordering mechanism. Alternative: explicit picker list (rejected — a second enumeration is exactly the R95 defect class). | `[new in P8]` — D48.1/D48.5; additive rows only |
| S-P8-2 | **Calendar bucketing (D48.2):** weekly buckets open Monday 00:00 ET (A114); monthly buckets open on the calendar-month boundary (A115); `TIMEFRAME_SECONDS` gains nominal 604800/2592000 keys for fixed-seconds consumers only. Rationale: weeks/months are calendar concepts — the fixed-seconds ET grid would drift month ends (R94). Alternative: extend `_ET_ANCHORED_TIMEFRAMES` (rejected — that set is a fixed-seconds grid, wrong for months). | `[new in P8]` — D48.2; additive functions beside `_period_start` |
| S-P8-3 | **Planner/backfill unchanged (D48.3):** no logic change — the `AC-D16.8` floor gate (`period < 86400`) and the flat-cap rule already exclude daily+; `plan_requests` chunks by configured duration; day-presence is already bar-granular (A117). Rationale: verified in source, not assumed. Alternative: timeframe-name special cases (rejected — period-based gating already covers the new keys). | `[new in P8]` — D48.3; verification, not code |
| S-P8-4 | **Daily+ canonical mode + one shared predicate (D48.4):** loads for any timeframe with `period >= 86400` use one canonical full-session mode for request, cache, planner, and prime (A118); the six `== "1 day"` gates plus the chart-model membership branches adopt one shared daily-or-coarser predicate covering weekly/monthly. Rationale: makes RTH/ETH parity structural with one cache (no fork, no double spend); one predicate kills the R95 enumeration class. Alternative: mode-aware keys for weekly/monthly (rejected — forks two multi-year caches); per-site `in (...)` tuples (rejected — re-creates R95). | `[new in P8]` — D48.4; load-path + five predicate sites |
| S-P8-5 | **Priming table is documentation-only (D48.2/D48.6, DG98):** weekly spans (≤ 604800 s) and monthly spans (≤ ~2.7 Ms) land in the existing coarse branch (`1 min`/`[60 S, 1 D]`); the per-span table gains two rows naming that branch; the probe verifies. Rationale: the span-based code is already generic — inventing a coarser bar would add an unprobed IBKR-validity claim. Alternative: a coarser priming bar (rejected — DG98's own gate is the probe, and the existing branch is already inside accepted ranges). Probe rejection escalates per R93. | `[new in P8]` — DG98; docstring rows + probe, no logic change |
| S-P8-6 | **Visibility grid unchanged (D48.5, DG97):** no new rows — the six rows enumerate duration *units* (Weeks/Months included), not timeframes, and no render consumer maps timeframe→row, so weekly/monthly are visible by construction with every box default-checked (A120). A guard test pins dialog open + all-checked + payload round-trip. Rationale: verified write-only state; adding rows would imply a per-timeframe control that does not exist. Alternative: new per-timeframe rows (rejected — no consumer could honor them). | `[new in P8]` — DG97; guard test only |
| S-P8-7 | **Burst minutes mapping (D48.5-adjacent):** `minutes_for_timeframe` maps `1 week` → 1950.0 (5 × 390) and `1 month` → 8190.0 (21 × 390) regular-session minutes. Rationale: the `"1 day"` → 390 precedent counts RTH-session minutes, not wall-clock; nominal secs/60 (10080/43200) would count weekends/overnights the convention excludes. Alternative: leave the secs/60 fallback (rejected — semantically dishonest per-minute contract). | `[new in P8]` — two mapping lines + unit case |
