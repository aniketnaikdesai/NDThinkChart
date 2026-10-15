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
