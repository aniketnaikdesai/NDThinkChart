# Project Memory

## User Preferences
*(No preferences recorded yet.)*

## Technical Notes & Quirks
*(No technical notes recorded yet.)*

## Locked Decisions
*(No locked decisions recorded yet.)*

## Known Gotchas
*(No gotchas recorded yet.)*

## Orchestrator Log — Auto-Appended Entries

### 2026-10-02 — discovered during Build (D16 historical-bar gap backfill)
**Category:** Technical Note
**Finding:** The chart's historical-bar load path (`ui/main_window.py::load_chart`) originally issued a single `req_historical_data` anchored to *now* with a fixed `TIMEFRAME_CONFIG` window (e.g. `5 mins` → `5 D`), not anchored to the last cached bar. Any app closure longer than that window — or any *internal* hole in the cache — left unfetched spans, and `_refresh_candles` drives both the candle and volume panels from the same `_bars` list, so a hole showed in both. The fix adds `services/market_calendar.py` (trading-day presence detection) + `services/backfill_service.py` (missing-span/chunk planner) and correlated multi-request orchestration in `MainWindow`. Detection must use trading-day presence between `min(cached_ts)` and now — a literal `MAX(ts)` tail anchor does NOT heal internal holes (this was the DG21 judgment call).
**Source:** Tasks T37–T40 (D16).

### 2026-10-02 — discovered during Code Review (D16)
**Category:** Known Gotcha
**Finding:** `services/market_calendar.py` must apply the NYSE Rule 7.2 year-end accounting-period exception to the New Year's observed shift: when Jan 1 falls on a **Saturday**, US equities do **not** close the preceding Friday (Dec 31 stays a trading day — the market was open Fri 2021-12-31). A naive Saturday→preceding-Friday shift misclassifies such a Dec 31 as a "genuine closure", so a real data hole there is never requested and never surfaced (a silent hole). The generic shift remains correct for Independence Day / Christmas / Juneteenth; only New Year's carries this exception.
**Source:** Escalation ESC-023 (rework T37/T42).

### 2026-10-02 — discovered during Code Review (D16, environment)
**Category:** Known Gotcha
**Finding:** The offscreen pytest suite intermittently reports spurious failures (e.g. `test_t40_t05_switch_mid_flight_isolated`, `test_t39_t05_switch_and_close_cancel_all`, `test_T30_T03_existing_d14_noop_paths_unchanged`) because `tests/conftest.py` seeds a **single shared on-disk SQLite DB** at `tempfile.gettempdir()/tos_charting_test.sqlite3`, so concurrent/interleaved runs contend on it. All such failures pass in isolation and in a clean full-suite run. Treat non-reproducible ibapi-mock / module-not-found failures in this suite as test-DB contention, not regressions — but always re-run the full suite to confirm before declaring green.
**Source:** Escalations ESC-024/ESC-025 rounds (Build verification).

### 2026-10-02 — discovered during Build (D16 robustness)
**Category:** Technical Note
**Finding:** The backfill wave lifecycle in `MainWindow` must be finalised on **every** wave-terminating path, including a transport drop (`_on_disconnected`) and a stalled request (a bounded watchdog `QTimer`), not just normal completion / switch / close. Each path must cancel tracked reqIds, advance `_history_generation` (so late responses are ignored), and run `_finalize_history_wave` exactly once so the AC-D16.4 shortfall is surfaced — never a silent hole. Arm the watchdog when a wave is issued and disarm it on every terminating path (including `closeEvent`); pass `reason` through so timeout vs. disconnect is distinguishable in diagnostics.
**Source:** Escalations ESC-024/ESC-025 (tasks T43/T44).

### 2026-10-03 — discovered during Build (D17/D18 UI layout)
**Category:** Technical Note
**Finding:** Panel-width caps are measured against the **chart area** (`MainWindow.centralWidget().width()`), NOT the whole window. The shared single source of truth is the pure Qt-free `ui/dock_layout.py` (`watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths`, constants incl. `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `RIGHT_DOCK_MIN_WIDTH=200`). `plan_dock_widths` cross-clamps the watchlist (<=50% of chart area) and the single right dock (Active Trader + Portfolio, <=40%) so the chart keeps >=400px, with the chart minimum yielding before any dock minimum is crossed. `MainWindow._apply_dock_widths` is the single apply entry point and must be wired to BOTH a window `resizeEvent` AND a dock-drag hook — a window-resize-only clamp does not fire during a splitter drag in full screen, which was the D17 defect.
**Source:** Tasks T45–T49 (D17/D18).

### 2026-10-03 — discovered during Build/Code Review (PyQt6 dock layout)
**Category:** Known Gotcha
**Finding:** PyQt6 does **not** expose the `QMainWindow` dock-area internal `QSplitter` via the public object tree — `findChildren(QSplitter)` returns only `ChartPanel`'s vertical splitter, and wiring to that would be wrong. To enforce a live clamp during a dock drag, use an event-filter fallback plus the `resizeEvent`/`changeEvent(WindowStateChange)` normalize path. Also, dock lookup in tests/MainWindow is by `windowTitle()`/`objectName` — consolidating two right docks ("Active Trader" + "Portfolio") into one region must keep the stable title/objectName or title-keyed lookups break.
**Source:** Tasks T47/T48 (D17/D18); ESC-026 round.

### 2026-10-03 — discovered during Code Review (ESC-026)
**Category:** Known Gotcha
**Finding:** A cross-clamp shrink loop that decrements dock widths without re-flooring can drive a width **below its own dock minimum** (e.g. `plan_dock_widths(750, 100000, 200) -> (350, 0)`). Any "shrink until it fits" loop must re-check the floor each iteration and fall through to the other dock when the preferred one is already at its minimum. A temporary workaround in a consumer (`MainWindow`) can mask such a helper defect and creates two divergent implementations — fix the pure helper and keep it the single source of truth.
**Source:** Escalation ESC-026 (task T52).

### 2026-10-03 — environment note (full offscreen suite)
**Category:** Known Gotcha
**Finding:** The offscreen suite occasionally reports a full-suite **SIGSEGV** (exit 139) at `tests/test_session_overlay.py::panel` (`qapp.processEvents()`) and/or order-dependent `ModuleNotFoundError: tests.test_watchlist` (`test_watchlist_d14_midrag.py`, no `tests/__init__.py`), triggered by collection-order changes from new test files. Both are non-deterministic and pre-existing: they pass in isolation and in clean full-suite runs (566 passed observed). Treat such non-reproducible failures as test-DB/teardown/collection-order noise, not regressions — but always confirm with a clean full-suite run before declaring green.
**Source:** Batch-11 rounds (Build verification, T47/T50/T51/T52).

### 2026-10-05 — discovered during Build/Review (D19 UI layout)
**Category:** Known Gotcha
**Finding:** A `QWidget` toolbar containing many fixed-width controls, placed inside `MainWindow`'s **central widget** layout, gives the central widget a huge `minimumSizeHint` (here ~1716px). `QMainWindow` refuses to shrink the central area below it, so the dock-area splitter has **no slack** — the left watchlist is pinned at its minimum and the right dock is pushed off-screen. The fix is to wrap the toolbar in a `QScrollArea` (`setFrameShape(NoFrame)`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, fixed 36px) inserted in the toolbar's place inside the central layout — the central `minimumSizeHint` then drops to the chart's own (~88px) and the docks can grow. Do not "fix" this by setting a smaller `minimumWidth` on the toolbar: the layout's minimum still propagates and controls would clip unreachably. Do not move the toolbar to a `QMainWindow` toolbar area (rejected in D19/B5).
**Source:** Defect D19 (tasks T53–T60).

### 2026-10-05 — discovered during Build/Review (D19 test masking)
**Category:** Known Gotcha
**Finding:** UI test harnesses that call `toolbar.hide()` to make dock geometry settle **mask** the real-app constraint — the offscreen suite then exercises a window unlike the app and cannot catch the toolbar-pinning regression. When a harness hides a widget to work around a layout minimum, treat it as a red flag: add a **toolbar-visible** variant and a guard asserting the widget is visible and no masking remains. A regression guard is only credible if it fails on the pre-fix tree and passes post-fix (D19's guard: 10 red at pre-fix commit, 10 green after).
**Source:** Defect D19 / AC-D19.6 (tasks T54–T59).

### 2026-10-05 — host/environment note
**Category:** Known Gotcha
**Finding:** In this repo `.venv/bin/pytest` has a **stale shebang** pointing at the pre-rename `TOS_Charting` path, so the `pytest` entry point fails; always run the suite as `.venv/bin/python -m pytest`. Also, the installed `ibapi` is **9.81.1.post1** and its `serverVersion()` returns `None` under the test mocks (causing intermittent `TypeError` in `ibapi/client.py`); and there is **no** `site-packages/tests/__init__.py` shadow — the local `tests/` is a namespace package. These three explain the recurring non-reproducible "environment" failures; confirm with a clean full-suite run before treating them as regressions.
**Source:** Batch-13 rounds (ESC-027; Build/Code Reviewer verification).

### 2026-10-06 — discovered during Build/Review (D20 toolbar height)
**Category:** Known Gotcha
**Finding:** When a `QScrollArea` wraps content whose fixed height equals the scroll area's fixed height (D19 set both the toolbar and its `ToolbarScroll` wrapper to `setFixedHeight(36)`), the horizontal scrollbar is laid out **inside** that height and overlaps the bottom of the content — clipping the label descenders. Size the scroll area to the **derived** height `content_height + horizontalScrollBar().sizeHint().height()` (e.g. 36 + 18 = 54 offscreen, ~52 macOS) so the scrollbar gets its own reserved lane below the content, and keep the content widget at its own fixed height. Do not use a literal total height, and do not assert the lane with `scrollBar.geometry()` (offscreen `geometry().top()` is 0) — use the mapped form `scrollBar.mapTo(wrapper, QPoint(0,0)).y() >= content.height()` or `viewport().height() >= content.height()`.
**Source:** Defect D20 (tasks T61–T64).

### 2026-10-06 — discovered during Build/Review (D21 UI batch)
**Category:** Technical Note
**Finding:** pyqtgraph: to stop a user dragging a `ViewBox` axis below a floor, use `viewbox.setLimits(yMin=0)` (the volume pane, D21.1) — the limit is enforced inside `ViewBox.setRange`, which every interactive y-change routes through. The volume Y **ceiling** is `1.10 × max(volume of bars whose x lies in the visible x-range)` recomputed on `sigXRangeChanged` + bar updates (D21.2); the `[0, 100]` nice floor applies **only when the visible max is 0**, never for a small non-zero max (ESC-028). This supersedes the D8 nice-max / ESC-007 only-widen rule for zoom.
**Source:** Defect D21 (D21-01/D21-02, ESC-028).

### 2026-10-06 — discovered during Build/Review (D21 time collapse)
**Category:** Technical Note
**Finding:** Collapsing non-trading time is a **display-only** transform (never mutates `Bar.ts`, never drops/fabricates bars). The predicate must account for bar coverage: bar timestamps are period **starts** (`data/bar_aggregator.py`), so collapse a gap `a < b` iff `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty — the un-adjusted `session_windows(a, b)` wrongly keeps the ordinary overnight/weekend/holiday gap because the last bar (15:55 RTH / 19:55 ext) sits inside the window that closes at 16:00/20:00. Within-session holes and missing full sessions stay visible. Consumers (candles, volume, session bands, time-anchored drawings, alarm labels, date axis/crosshair) all map through the same `TimeCollapseMap` (`services/time_collapse_service.py`).
**Source:** Defect D21 (D21-14/D21-15/D21-16; RC-D21-1).

### 2026-10-06 — discovered during Build (D21 shared visual convention)
**Category:** Technical Note
**Finding:** UI "hidden/off" and "active" affordances are centralised in `ui/visual_conventions.py`: `DiagonalStrikeButton` (a single cosmetic top-left→bottom-right strike, auto-applied when a checkable button is unchecked) and `set_button_active(button, active)` / a `#MainToolbar`-keyed stylesheet for the active highlight. The stylesheet must target the toolbar **objectName**, not position, so it works inside the D19/D20 scroll wrapper. Reuse these rather than re-implementing per panel.
**Source:** Defect D21 (D21-04, VIS-D21; consumed by D21-07/08/11/12/13).

### 2026-10-07 — discovered during Code Review (D23; ibapi surface)
**Category:** Known Gotcha
**Finding:** The pinned `ibapi` (9.81.1.post1) `EClient` has **no** `cancelContractDetails` method (only `reqContractDetails`). Calling `client.cancelContractDetails(...)` raises `AttributeError`, which a surrounding `try/except Exception: pass` silently swallows — making the cancel a no-op on the real TWS path (tests passed only because the fake client defined it). Guard capability access: `cancel = getattr(self.client, "cancelContractDetails", None); if cancel: cancel(req_id)`. On the pinned dep the wire request is ended by TWS's own `contractDetailsEnd`/error; the real safety net is `ContractLookupService`'s bounded QTimer + `cancel_all` on disconnect. Verify `hasattr(EClient, "<method>")` before relying on any ibapi EClient method.
**Source:** Escalations ESC-030 (task D23-01).

### 2026-10-07 — discovered during Code Review (D23; row-keyed UI state)
**Category:** Known Gotcha
**Finding:** When a `QTableWidget`-backed panel keeps parallel row-indexed maps (`_row_data`, `_req_to_row`, `_prev_close`, `_last_price`, flash timers), a remove that re-indexes by shifting (`{(r-1 if r > row else r): v ...}`) leaves a **stale key for the removed row when it is the last/max-index row** (no later key overwrites it). Always `map.pop(row, None)` before the shift, and assert the invariant `set(keys) == set(range(rowCount()))` after first/middle/last/only-row removals — a middle-row-only test does not catch this.
**Source:** Escalations ESC-031 (task D23-02).

### 2026-10-07 — tooling note (`build_wave.py`)
**Category:** Known Gotcha
**Finding:** `~/.config/opencode/scripts/build_wave.py advance` crashes in its circuit-breaker loop (`AttributeError: 'list' object has no attribute 'get'`) when `docs/build/failures.json` contains **list-valued** keys (`blocked`, `pending_routing`, `notes`) instead of task dicts. It crashes after the consolidation writes but before finalizing `wave.json`; mark the wave `CONSOLIDATED` and re-run to complete deterministically. Global tool — do not edit from within a repo. Recorded for the tool author.
**Source:** D22/D23 Build consolidations (ESC-030/031 rounds).

### 2026-10-14 — discovered during Build/verification (toolbar + font environment)
**Category:** Known Gotcha
**Finding:** The startup notice `qt.qpa.fonts: Populating font family aliases took ~45 ms. Replace uses of missing font family "Sans Serif" with one that exists` is **Qt-internal and cannot be fixed from this codebase**. `"Sans Serif"` is Qt's own placeholder family (`QFont().family()` returns it before anything is set); the first widget that renders text makes Qt populate its alias table and log the notice once (~45 ms, one-time, harmless). Verified NOT fixed by: (a) replacing the generic `sans-serif`/`monospace` families in `config/theme.qss` with real ones (Inter/.AppleSystemUIFont/Menlo); (b) setting a real application font via `app.setFont(...)` — that fixes a bare `QLineEdit` but not the full `MainWindow`; (c) adding a font family to the toolbar's local `#MainToolbar` stylesheet. It is only **silenceable** via `QT_LOGGING_RULES=qt.qpa.fonts=false` (verified), which the owner has declined (2026-10-14) because it would also hide genuine font-loading warnings. It does **not** appear in pytest output (pytest captures stderr), so a green suite never shows it. **Do not re-investigate; accepted as-is.**
**Source:** Toolbar font investigation (post-D40 verification)

### 2026-10-14 — discovered during Build (toolbar)
**Category:** Known Gotcha
**Finding:** The toolbar (`#MainToolbar`) sets a **widget-local stylesheet**, so the app-level `* { font-family: "Inter", ... }` rule in `config/theme.qss` does **not** reach its controls — they render the Qt default (9pt) unless the font is re-declared inside `#MainToolbar`. Fixed in `ui/main_window.py` (font re-declared in that rule). Consequence for tests: the toolbar's intrinsic width is **font-dependent** (measured 1965px with the 9pt default, 1921px once Inter 11px applies) — the D19/D20 geometry fixtures (`_WIDE_SIZE`) must be sized for both. Also note `ui/main_window.py` is edited often and the docs cite `main_window.py:NNN` line numbers, so any edit above a cited line invalidates them (a 5-line change shifted ~10 citations).
**Source:** Toolbar font fix (`99fb8fa`) + DG56

### 2026-10-15 — discovered during Code Review (offscreen probe isolation)
**Category:** Known Gotcha
**Finding:** `config/paths.py::get_db_path()` returns the **user-space** production DB (`~/Library/Application Support/NDThinkChart/charting_app.sqlite3`) whenever the `DB_PATH` env var is **unset**. `tests/conftest.py` sets `DB_PATH` to a temp file, so pytest runs are hermetic — but a **non-pytest offscreen/REPL probe** that drives `MainWindow._on_position_update` (or any DB-writing path) will write into the owner's REAL database. This is exactly how two junk rows (`HELD` from the `test_d27_account_subs.py` fixture, `conId=999`, account `DU123`; and a probe-written `H`, `conId=1`, `DU1`) ended up in the production `positions` table and were then rendered by the portfolio panel, whose `_on_position_end` `SELECT`s the whole table with no account/qty filter. **Rule: every offscreen probe MUST export `DB_PATH=<tempfile>` before importing the app** (tracked as ESC-043, which also covers scoping the render to the live account).
**Source:** ESC-043 (portfolio `HELD`/`H` rows investigation)

### 2026-10-15 — discovered during Build (D41 waves 10/11/14; worker step budget)
**Category:** Known Gotcha
**Finding:** A `build_worker` invocation has a **hard step budget**, and an **L-size delete-only task** (removing ~150–500 lines spread across many members, plus import cleanup, call sites and probes) can exceed it. Three D41 workers died this way (`P1-T09`, `P1-T10`, `P1-T11`): two left their file **non-importable** mid-edit (`chart_panel.py` lost `QTimer`/`QMenu` while code still referenced them; `ticker_session.py` kept a call to the just-deleted `on_fp_error`), and one finished every edit and test but never wrote its result/log. The task file's `size` hint is a poor predictor for deletions — **lines removed** is what matters. Mitigations: (a) expect the orchestrator to finish such a task in place when a worker dies (record provenance in `footprint_flags` so the reviewer sees it); (b) after **any** worker death, run a syntax/import check **and** a residue grep for the removed tokens on the touched file before trusting it; (c) split future delete-only tasks by **member group**, not by file.
**Source:** D41 waves 10/11/14 (P1-T09, P1-T10, P1-T11)

### 2026-10-16 — discovered during Build (D42; `load_chart` symbol normalisation)
**Category:** Known Gotcha
**Finding:** `MainWindow.load_chart` **upper-cases** the symbol, so any test or probe that drives the load path with a lowercase symbol never matches the rows the app actually stored (the cache/DB is keyed on the upper-cased form). A D42 worker lost time to exactly this and had to add `.upper()` in its `_symbol_for` helper. Rule: when driving `load_chart` from a test, either use an already-upper-case symbol or normalise before comparing against stored rows.
**Source:** Task P2-T22 (D42 wave 58)

### 2026-10-16 — discovered during Build (D42; the depth floor issues MANY requests)
**Category:** Known Gotcha
**Finding:** D42's `min_sessions` depth floor means a single `load_chart` now issues **many** historical requests instead of one. Any test that stubs `req_historical_data` with a **small fixed reqId iterator** will raise `StopIteration` (it hit `tests/test_d28_2_sessions.py`, fixed by widening the stub to `itertools.count(...)`). Rule: stubs for the historical-request path must use an **unbounded** id source.
**Source:** Tasks P2-T14 / P2-T19 (D42 waves 53/58)

### 2026-10-16 — discovered during Build/Code Review (D44; task-graph decomposition)
**Category:** Known Gotcha
**Finding:** Five of six D44 build workers exhausted their step budget, and every one had either finished its work or was recoverable by verifying it — but the two tasks that genuinely needed the orchestrator to FINISH them (`P3-T02`, `P3-T05`) were both caused by defects in the **task graph**, not by the worker. `P3-T02`'s `AC1`/`T11` demanded `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`, which is **unsatisfiable until `P3-T05`** swaps the dock's title bar (the header strip pins the collapsed dock at 128px) — so the assertion was assigned to a task that could not satisfy it. `P3-T01`'s `touches_files` omitted `ui/watchlist_panel.py` while its **own AC4** mandated editing it, which made the precheck fire a spurious blocking `fail_fast` and would have sent the task to a rework that could only have reverted required code. Both defects were found only by verifying the handoffs against the code rather than trusting them. Rules for the next batch: (a) when an AC's measurable depends on a **later** task's output, assign the assertion to that later task; (b) before declaring `touches_files`, resolve **where each named symbol actually lives** (`grep -n "def <name>"`) instead of trusting the plan's file table — `clamp_watchlist_width` is defined in `ui/watchlist_panel.py`, not `ui/dock_layout.py`; (c) a precheck `fail_fast` is a **claim to verify, not an order** — read the task's own ACs before re-dispatching a rework.
**Source:** D44 waves 92–98 (P3-T01, P3-T02, P3-T05; ESC-056)

### 2026-10-23 — the orchestrator's four process failures (migrated from run state before untracking)
**Category:** Known Gotcha
**Finding:** Four failures from the D41/D42/D44 runs, recorded here because `docs/orchestrator_state.json` is no longer tracked. (1) A Code Reviewer was launched **without** running `verify_tests.py` first; the whole-suite gate then caught a real regression that every per-task command had passed — always run `review_precheck.py` AND `verify_tests.py` before the reviewer. (2) A user decision (ESC-043 `qty==0`) was asked **after** dispatching the Task Manager and never relayed, so the graph recorded it as undecided (ESC-053) — relay every user answer to the agent that needs it **before** dispatch. (3) A BUILD escalation's `task_id` determines `build_wave.py`'s rework target; creating a NEW task for the same fix duplicated it (P2-T36 removed) — reuse the task the escalation names. (4) A behaviour change (P2-T38 persisting a pre-summary update) **invalidated an assertion in a file outside its `touches_files`**, which pinned the old behaviour — enumerate the assertions a change invalidates, not just the files it edits, and run the full suite.
**Source:** D41/D42/D44; migrated from `docs/orchestrator_state.json` 2026-10-23

### 2026-10-23 — `pipeline_state.py`'s "plan proposal not current" is benign in a batch-based run
**Category:** Known Gotcha
**Finding:** For a batch-based legacy run `docs/plan_proposal.md` is a **superseded per-batch draft**, but `pipeline_state.py`'s freshness rule compares it against `requirements.md` — so after any later requirements wording change it permanently reports `next=INVOKE agent=plan reason="plan proposal not current"`. Clearing it needs the Plan to refresh the proposal, whose handoff re-appends `READY_FOR_VALIDATION` and cascades a full Plan → Validator → Task Manager → Build → Review cycle for a wording-only change. **Owner decision (2026-10-16): treat the flag as benign** unless `requirements.md` gains a *substantive* change rather than a restatement. The canonical `docs/plan.md` / `docs/architecture.md` are the authoritative artifacts and must be synced directly.
**Source:** D44 / ESC-057 follow-up

### 2026-10-23 — Task Manager graph rewrites can silently reset `done` tasks
**Category:** Known Gotcha
**Finding:** A Task Manager graph rewrite can reset delivered tasks' statuses (observed: P2-T14/P2-T15 `done`→`in_progress`, P2-T23 `blocked`→`not_started`) even when its report claims existing tasks were byte-identical. Recovery: copy the task's archived result from `docs/build/results/_archive/waveNN_<id>.json` into `docs/build/results/<id>.json`, then `advance` (consolidates it back to `done`). The `cp` sets a fresh mtime, which then makes `build_wave` treat the task as "already re-run since escalation X opened" and stop re-dispatching it.
**Source:** D42/D44 build consolidations

### 2026-10-23 — `docs/codebase-map.md` is a per-batch Plan artifact
**Category:** Technical Note
**Finding:** `docs/codebase-map.md` is **Plan-owned** and written/refreshed as the first step of every batch: `update_codebase_map.py` generates the module index between the `MAP-SKELETON` markers, and Plan owns the annotations **outside** them (the script provably never touches those). D42 predates the convention, so its map is absent — expected, not a defect. D44 was the first batch to write one, by hand (before the generator existed), so it has no skeleton region.
**Source:** Contract change 2026-10-16; D44

### 2026-10-16 — owner decision (architecture; the chart stack)
**Category:** Locked Decision
**Finding:** The owner evaluated replacing the pyqtgraph chart layer with `QWebEngineView` + TradingView Lightweight Charts (Python/IBKR backend unchanged; ticks and alerts pushed over Qt WebChannel or a local WebSocket) and **declined it on 2026-10-16 — do not re-propose the migration.** Rationale recorded at decision time, so the analysis need not be redone: the *transport* half is cheap (`MainWindow` → `ChartPanel` is a narrow seam — 14 call sites, ~20 public methods; `ibkr/`, `data/` and most of `services/` are renderer-agnostic, and `data/events/provider.py` already abstracts event sources via an `EventProvider` ABC), but the *chart* half is not a renderer — `ui/chart_panel.py` (1683) + `ui/drawing_overlay.py` (926) + `ui/popout_window.py` (295) + `ui/chart_mouse_router.py` (271) + `ui/candlestick_item.py` (251) + `ui/alarm_overlay.py` (263) + `ui/event_marker_overlay.py` (182) + `ui/overlays/*` ≈ **4,244 lines**, with **75 of 129 test files chart-adjacent**. Lightweight Charts covers roughly the candle/volume/crosshair third only (no drawing tools, no study engine, no collapsed time axis — `TimeCollapseMap` is a display-only x-remap every overlay must honour), and it would add Chromium to the .app bundle plus a JS toolchain to a pure-Python repo. **If ever revisited, the sanctioned route is a strangler:** a second chart mode behind the existing `ChartPanel` interface, ported feature-by-feature, keeping pyqtgraph until parity.
**Source:** Owner Q&A, 2026-10-16 (graphify-assisted assessment of `ui/`, `services/`, `data/events/`)

### [2026-10-25] — discovered during Code Review (D45 / P4)
**Category:** Known Gotcha
**Finding:** The retained `positions.stop_loss` / `positions.take_profit` values do NOT survive a live position update. `MainWindow._on_position_update` builds `Position(stop_loss=None, take_profit=None)` (`ui/main_window.py:3093-3094`) and `_upsert_position`'s `ON CONFLICT ... DO UPDATE` writes `stop_loss=excluded.stop_loss, take_profit=excluded.take_profit` (`:3198-3199`), so the first update of a row clears both columns. The bulk `_on_position_end` load does carry them (`row[12]`), which is why the loss is easy to miss. Since D45 removed every setter, the clear is permanent. Owner decided (ESC-060) to keep the behaviour and correct the docs rather than preserve the columns — do not re-introduce a "values stay in SQLite" claim anywhere.
**Source:** Escalation ESC-060

### [2026-10-26] — discovered during Build + Code Review (D46 / P5)
**Category:** Technical Note
**Finding:** D46 removed every order-related coding path. `ibkr/orders.py` is gone (builders, `Orders` registry, singleton), as are the three `EWrapper` order overrides, the three bridge signals and their window observers, `data/models.UserOrder`, `IdManager.reserve`, `OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL` and the order-fill sound. `IdManager.get_id()` survives and serves **six** market-data reqId callers; `nextValidId` is the CONNECTED transition, not order plumbing. The residue instrument is `tests/test_d45_removal.py`: `_SURVIVORS` 16, `_FORBIDDEN` 80, `_EXACT_ONLY = {orders, Orders}`. It has exactly **one** authorised carve-out — `_ALLOWED_IN_FILE = {"stop_loss": {"data/db.py"}, "take_profit": {"data/db.py"}}` — because `_migrate_schema` must name the columns it drops; a persisted AST test enforces that those tokens appear only as the `DROP COLUMN` loop's subject tuple and never as a name/attribute/arg/keyword or other SQL.
**Source:** Escalations ESC-059, ESC-060, ESC-064, ESC-065, ESC-066, ESC-067

### [2026-10-26] — SUPERSEDES the ESC-060 note above (D46 / A99)
**Category:** Known Gotcha
**Finding:** The retained SL/TP storage is **dropped**, not kept. `_migrate_schema()` runs four guarded `ALTER TABLE … DROP COLUMN` statements (positions/trade_groups × stop_loss/take_profit) after the unique-index statement, and the `CREATE TABLE` DDL no longer declares them; the four model fields and `build_position_from_ib`'s two params are gone. A pre-D46 database keeps its rows, ids/`sqlite_sequence`, the unique index and the FK; a second open is a no-op. Any document claiming "columns kept / values cleared" is stale — say "dropped by a one-time migration".
**Source:** Escalation ESC-060 → A99 / D46.12

### [2026-10-26] — discovered during Build (D46 / P5)
**Category:** Known Gotcha
**Finding:** `tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green` runs a **stable subset** of 1000/1022 tests (118/124 modules, ~28 s) through `_inner_pytest_args` / `_run_inner_suite`, excluding six modules by name: three wall-clock gates (`test_d24_smoke_gate`, `test_d28_4_gate`, `test_d28_tick_burst_baseline`) and three Qt-teardown crashers (`test_session_overlay`, `test_d28_5_teardown`, `test_watchlist_addflow_d22`). Do not "restore" the whole-suite child — that reintroduces a nondeterministic SIGSEGV and cost four gate runs across two batches. Do not add a temp cwd either: three suite modules read repo-relative paths.
**Source:** Escalation ESC-065 / task P5-T11

### [2026-10-26] — discovered during Build (D46 / P5)
**Category:** Known Gotcha
**Finding:** Pipeline-tooling edges that cost time: (1) `build_wave.py reset` only handles `in_progress` and `packfix` only accepts PACK_FIX-flagged tasks, so a **blocked-but-repaired** task has no script verb — it needs a manual `status: not_started` in `task-graph.json` plus clearing its `failures.json` entry. (2) A rework dispatch is skipped when the task's result is newer than the escalation's `opened`, which is what stops `advance` looping while the reviewer catches up. (3) `worker_selfcheck.py` reads only `touches_files`, so a verification-only task must declare its own result file or every build artifact counts as a footprint violation. (4) `gen_changelog.py` counts wave-log entries, not tasks: a re-dispatched task appears twice and a transient block still prints under "Blocked" — correct the entry by hand.
**Source:** D46 build/review cycle

### [2026-10-26] — discovered by the owner running the app (Q-2)
**Category:** Known Gotcha
**Finding:** IBKR cancels historical data requests that are issued in a burst — error 162 "API historical data query cancelled" — and the chart then silently keeps whatever the cache holds (symptom: the 1-min chart stuck on an old date showing one day of bars). The cause was structural: `ibkr/market_data.py::req_historical_data` is the only request path that never called `pacing_manager.throttle()`, and `TickerSession._issue_wave_chunks(max_per_wave=60)` loops synchronously, so up to 60 `reqHistoricalData` calls for one contract hit TWS within microseconds. Fixed by `settings.HISTORICAL_MIN_INTERVAL_S = 1.0` feeding `PacingManager.historical_wait_seconds()` (so the existing `PacingExceeded` → `_schedule_wave_continuation` path spaces the wave at one request/second) and by lowering `MAX_HISTORICAL_PER_600S` from 60 to 50. Anything that issues historical requests must go through `req_historical_data`; do not add a second path that bypasses the interval.
**Source:** Quick task Q-2

### [2026-10-26] — owner decision (D47 / P6, chart stack)
**Category:** Locked Decision
**Finding:** Owner reversed the 2026-10-16 decision declining a Lightweight Charts migration. The chart stack migrates to QWebEngineView + Lightweight Charts v5 via a strangler behind a ChartView interface; pyqtgraph is retained until parity is accepted. No soak period: cutover happens on owner acceptance plus full parity, gated on one live trading session with no engine defect before any pyqtgraph deletion. Phase 0 spike in spikes/lwc/ allowed as the single exception to the no-prototype rule.
**Source:** Owner answers 2026-10-26 (Q-reversal, no-soak, spike exception); D47 requirements

### [2026-10-26] — worker-death recovery (owner directive, P6)
**Category:** Technical Note
**Finding:** Before re-dispatching a dead build worker, inspect what it left: `docs/build/results/<id>.json`, its `touches_files` for edits on disk, and whether the task's `test_command` passes. Then **resume the same worker session** with the `sessionID` and a short delta prompt (what landed, what is pending) instead of starting a fresh worker — a fresh dispatch discards its context and risks duplicating or contradicting work already written. A `state: error` handoff is not proof of failure: the platform can fail only the closing message (`only "auto" is supported for tool_choice`), so P6-T04 arrived "failed" with a complete, green result. Check the tree first, always.
**Source:** Owner directive 2026-10-26; P6-T04/P6-T05 worker deaths

### [2026-10-26] — discovered across P6 waves (D47)
**Category:** Known Gotcha
**Finding:** The LWC migration's residue/parity guards each wrote a *wave-local* expectation that a later wave must widen — five instances in one batch: a hardcoded "19 open parity rows" count (breaks on every completed row), a hardcoded stdlib allowlist in the import-boundary test (broke when P6-T09 added `bisect`), the renderer import boundary itself, a forbidden `session_service` token (P6-10 legitimately consumes it), and five `TestRendererBoundary` scans forbidding the raw word `pyqtgraph` anywhere in `ui/lwc_view.py`, which a docstring tripped. The durable shape is to assert the *invariant* (row set + per-row disposition; `sys.stdlib_module_names` + project packages; AST/import-level checks, not raw substrings) rather than the current instance count or a literal list.
**Source:** D47 P6-02/P6-07/P6-09/P6-10/P6-11 review waves

### [2026-10-26] — owner decision (D47 / Q61, packaging)
**Category:** Locked Decision
**Finding:** Owner accepted the measured Lightweight Charts size cost: `PyQt6-WebEngine` adds **298,932 KB (~292 MB)** of frameworks, taking the `.app` from **378,400 KB (369.5 MB) to ~661 MB (+79%)** — measured with `du` on the installed frameworks, before PyInstaller packing. The vendored JS tree is only 0.34 MB, so the Chromium engine is the whole cost. Signing remains an obligation rather than a solved item: the spec builds with `codesign_identity=None`, and QtWebEngine's nested Mach-O binaries need nested signing plus hardened-runtime entitlements before any signed distribution.
**Source:** Owner 2026-10-26 ("yes -- +292 MB acceptable"); Q61, A109, DG89, P6-T12/Q-7 measurements

### [2026-10-26] — verification rule (owner directive)
**Category:** Technical Note
**Finding:** A fix is not "done" until the real application has been exercised and the user-facing result inspected. Root-cause analysis + code change + a green unit test has twice been reported as fixed while the app still misbehaved: the LWC chart stayed black after a `HAS_WEBENGINE` probe said the host was fine (the probe never rendered), and the priming loop was "fixed" from a test that never launched the app. For renderer changes, render the real widget and check the pixels/image; for data-path changes, run the app against live TWS and read the status line. Unit tests are the floor, not the proof.
**Source:** Owner directive 2026-10-26; D47 Q-12/Q-13

### [2026-10-27] — debugging rule (owner directive)
**Category:** Technical Note
**Finding:** Root-cause analysis is the Orchestrator's own work, not a subagent's. A subagent may implement a fix whose cause is already proven, or run a scoped repair, but the *determination of what is wrong* must be reproduced first-hand — in the running app where possible, or with a probe that prints the actual state, never by relaying a worker's explanation. Twice in D47 a worker's diagnosis was accepted as fact and the "fix" treated the wrong thing (the black-chart round: three separate causes, only one found at a time; and the axis regression where a bar count passed while the dates read 1970).
**Source:** Owner directive 2026-10-27; D47 Q-19..Q-21

### [2026-10-27] — authority over validation method (owner directive)
**Category:** Technical Note
**Finding:** The owner names the validation method and it is binding. Perform it exactly as asked; if it is blocked, or a different check seems better, ask permission **before** reporting — never substitute. The Orchestrator is not the decision-maker on how something is verified: a probe, a green test or a fixture is not an acceptable stand-in for the validation that was requested. Additional checks are welcome after the requested one, not instead of it.
**Source:** Owner directive 2026-10-27 ("you are not any decision maker")

### [2026-10-27] — discovered during Build (handshake gate + page-load lifecycle)
**Category:** Known Gotcha
**Finding:** Two backend/frontend lifecycle defects with the same shape (a shared-global object owned by a short-lived view): (1) `IBApiClient.connected` delegated to the raw socket and `_poll` promoted socket-open to CONNECTED before `nextValidId`, so pre-handshake `reqHistoricalData` earned TWS 504 — readiness is now handshake-gated (`connected`/`api_ready` only after `nextValidId`; `IBKRNotReady` in `ibkr/error_codes.py` so `market_data.py` stays Qt-free). (2) `create_host` installed the `ndt://` scheme handler per view on the shared default profile; after create/destroy cycles the registration dangles and every later page load silently never finishes (empty page, `readyState: complete`) — the handler and interceptor are now app-lifetime singletons. Symptom signature for (2): `typeof window.lwSnapshot` undefined + `chart: None` with a complete readyState, green in subsets, red in full runs.
**Source:** Bug report 2026-10-27; Q-35/Q-38/Q-40
