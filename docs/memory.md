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
