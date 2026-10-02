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
