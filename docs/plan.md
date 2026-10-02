# Implementation Plan — NDThinkChart Stabilization (Batch 10: D16 historical-bar gap backfill; ESC-023 calendar correction)

Scope: the current stabilization batch is **D16 only** — backfill of missing historical
bars across a cache/reopen gap (reported 2026-10-02). It is planned on top of the
**as-built, frozen D1–D15 baseline** (383 passed, verified 2026-09-28). D1–D15 are **not**
re-planned. This is an existing-repo run: items are labelled `[existing]`, `[new]`, or
`[new/changed]`; the existing tech stack is a hard constraint and nothing existing is
replaced. No new product features, no schema changes, no new external integrations.

D16 Phases 1–3 below are **built** (tasks T37–T41, all `done`). The sole **active
increment** in this pass is **Phase 4 — the ESC-023 New Year's trading-day calendar
correction** (`AC-D16.7`, A33, R27, DG22), which is a behaviour/acceptance-criterion
correction, not a new subsystem. It does **not** re-plan any other part of D16.

> Companion architecture: `docs/architecture.md` (Codebase Summary, D16 tech-stack rows,
> D16 components/data-model/integration/non-functional/risk sections). Requirements:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D16 / Journey 17 /
> `AC-D16.1`–`AC-D16.7` / A27–A33 / R22–R27 / DG19–DG22; ESC-023 correction 2026-10-02).

## Completed baseline — D1–D15 (as-built, frozen)
D1–D15 (session shading, crosshair chip, zoom controls/magnifier, zoom label/position,
linear volume axis with the pinned scaling nice-max + live ceiling, price-coloured volume,
volume/price width alignment, volume show/hide, inner-right drawing labels, zone and
horizontal-line double-click dialogs, resizable/persistent watchlist with double-click load,
and the `RouterMode` gesture state machine incl. the ESC-002/003/006/007 revision and the
ESC-013…ESC-021 rework) are **built and verified** (tasks T1–T36 `done`; full offscreen
suite green). They remain frozen and are not modified by D16. See `docs/architecture.md`
for the as-built description.

## Phases

> **Build status:** Phases 1–3 are **built** (T37–T41, all `done`) and are listed for
> completeness; **Phase 4 is the one active increment** in this pass (ESC-023 /
> `AC-D16.7`). Nothing else in D16 is re-planned.

### Phase 1 — Backfill planning (pure services) `[new]`
- **Goal:** Add the pure, Qt-free decision layer that says *which* historical spans are
  missing and *how* to request them — the trading calendar and the missing-span/request
  planner. No UI, no TWS.
- **Deliverables:**
  - `services/market_calendar.py` — ET trading-day/holiday calendar (holidays by rule;
    New Year's carries the `AC-D16.7` year-end accounting exception — Dec 31 stays a
    trading day when the next Jan 1 is a Saturday); `is_trading_day`,
    `trading_days(start_ts, end_ts)`, `session_windows(...)`.
  - `services/backfill_service.py` — `bar_period_seconds`, `find_missing_spans(
    cached_ts, now_ts, timeframe)`, `plan_requests(missing_spans, timeframe)` (chunk step =
    `TIMEFRAME_CONFIG[timeframe]["duration"]`; anchors formatted with the existing
    `ui.main_window._ibkr_end_date` behaviour, factored so the pure service does not import
    Qt).
- **Requirements / journeys covered:** Journey 17; D16; `AC-D16.1`, `AC-D16.3`,
  `AC-D16.4`, `AC-D16.5` (planning halves); A27, A29, A32; DG21; DG19.
- **Dependencies on earlier phases:** none.

### Phase 2 — Load-path backfill orchestration (multi-request) `[new/changed]`
- **Goal:** Make `MainWindow` issue and correlate the chunk set, accumulate results, and
  finalise with a single save + re-read + render — keeping the single-request path
  behaviourally intact as a set of one.
- **Deliverables:** `[new/changed] ui/main_window.py`:
  - `load_chart` calls the planner; empty plan + current cache → **no redundant request**
    (edge case "cache end already at now"); otherwise issues one `req_historical_data` per
    `RequestPlan` using the existing `endDateTime` parameter (no `market_data.py` change).
    Empty cache → the configured-window fallback.
  - Multi-id state: `_history_req_ids: set[int]`, `_history_generation: int`,
    `_backfill_missing_spans`, `_backfill_failed_req_ids`; `_on_historical_bar` /
    `_on_historical_data_end` accept members and finalise only when the set empties.
  - Symbol/timeframe switch and `closeEvent` cancel **every** id in the set (extend the
    current single-id cancellation).
  - `_on_error` correlates a failed backfill reqId with its span and removes it from
    `_history_req_ids` so the wave can still finalise (required by `AC-D16.4`).
  - **Shortfall surfacing** (`AC-D16.4`): status-bar message + log when a backfill request
    errors or a trading day is still empty after the wave; never fabricate a bar.
- **Requirements / journeys covered:** Journey 17; `AC-D16.1`, `AC-D16.2`, `AC-D16.4`,
  `AC-D16.5`; edge cases (internal hole, tail gap, closures, Ext Hours, switch mid-flight,
  empty cache, fresh cache, retention shortfall); A28, A31.
- **Dependencies on earlier phases:** Phase 1 (its planner is the input).

### Phase 3 — Verification & regression `[new]`
- **Goal:** Prove D16 end-to-end offscreen (no live TWS) and prove no D1–D15 regression.
- **Deliverables (tests):**
  - `tests/test_market_calendar.py` — weekends/holidays (incl. Good Friday, Juneteenth,
    observed-day shifts) are non-trading; trading days are correct.
  - `tests/test_backfill_service.py` — **parameterized over all six timeframes × ≥2
    symbols** (Q39): seeded `ts` lists with a tail gap and an internal hole →
    `find_missing_spans` returns the expected missing weekdays; `plan_requests` covers the
    span and chunks when it exceeds the configured duration.
  - `tests/test_history_backfill.py` — offscreen real `MainWindow` (stubbed
    `IBApiClient.connect`/managers, pattern from `tests/test_watchlist_d14_midrag.py`):
    seed `BarCache` with the `AC-D16.5` repro, drive the stubbed historical feed, assert
    `ChartPanel._bars` has the expected per-trading-day counts for 2026-09-21…09-25,
    **no** weekend bars, and the volume `height` array is non-zero wherever a candle
    exists (`AC-D16.2`); assert chunking (`AC-D16.4`); assert switch-mid-flight does not
    mix symbols/timeframes.
  - `tests/test_history_backfill.py` also covers the `AC-D16.5` date range (2026-09-19 →
    2026-09-28 modulo closures) and an empty-cache fetch.
  - Full offscreen suite re-run must stay green (`AC-D16.6`).
- **Requirements / journeys covered:** `AC-D16.1`–`AC-D16.6` (as built). The `AC-D16.7`
  calendar correction and its test updates are delivered by Phase 4.
- **Dependencies on earlier phases:** Phase 1 and Phase 2.

### Phase 4 — ESC-023 New Year's calendar correction `[new/changed]`
> **Active increment.** D16 is built; this is the only open work. It is a behaviour/AC
> correction, not a new subsystem: the D16 architecture otherwise stays as built.

- **Goal:** Correct the trading-day calendar so **Dec 31 is a trading day** whenever the
  next Jan 1 falls on a Saturday (NYSE Rule 7.2 year-end accounting exception), and update
  the `T37-T03` acceptance criterion/test that deliberately encoded the wrong convention —
  so a genuine bar hole on such a Dec 31 is backfilled (`AC-D16.1`) or its shortfall
  surfaced (`AC-D16.4`), never silently treated as a genuine closure.
- **Deliverables:**
  - **Task Manager (task graph only):** correct the `T37-T03` acceptance criterion in
    `docs/tasks/task-graph.json` — replace “New Year's 2022-01-01 Saturday gives 2021-12-31
    Friday closed” with the year-end accounting exception; its test description and
    `expected_result` must assert `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31` are
    **trading days**.
  - **`[new/changed] services/market_calendar.py`:** make the New Year's observed shift
    **New-Year's-specific** and add the year-end exception. When Jan 1 is a **Saturday**,
    add **no** New Year's closure (nothing is shifted onto Dec 31; Jan 1 remains
    non-trading as a weekend); Jan 1 on a **Sunday** still observes the following Monday; a
    **weekday** Jan 1 stays a closure. `_observed` for Juneteenth / Independence Day /
    Christmas is unchanged. Correct the stale “New Year's observed on the preceding Dec 31”
    docstring/comment.
  - **`[new/changed] tests/test_market_calendar.py`:** update T37-T03 — `is_trading_day`
    is **True** for `2021-12-31` (and `2027-12-31`, `2032-12-31`, `2038-12-31`); drop the
    wrong `date(2021, 12, 31)` entry from the “weekend legal dates” loop (its Saturday
    legal date is `2022-01-01`); keep every other observed-shift assertion (Independence
    Day Sat→Fri, Christmas Sun→Mon, Juneteenth Sat→Fri, New Year's Sun→Mon) as the
    unchanged regression guard.
  - **Regression:** re-run the full offscreen suite; it must stay green (`AC-D16.6`).
- **Requirements / journeys covered:** D16 / Journey 17; `AC-D16.7` (primary), plus the
  `AC-D16.3` “not a genuine closure” carve-out and the `AC-D16.1`/`AC-D16.4`
  backfill-or-surface consequence; A33; R27; DG22; ESC-023.
- **Dependencies on earlier phases:** Phase 1 (the calendar this corrects). The corrected
  `T37-T03` acceptance criterion must be written by Task Manager **before** Build edits the
  module/test, so the module implements the corrected criterion rather than the old one.

## Parallel sequencing (`touches_files` contract)
The Task Manager must add a **`touches_files`** field to every task so Build's Lead (a
Lead + Worker pair) can dispatch non-conflicting tasks in parallel up to
`max_parallel_tasks` (default 4; optional user-owned `docs/build/build_config.json`). The
Lead is the sole writer of task status, so concurrent workers never race on the graph.
D16 sequencing consequences:

| File | Phase | Consequence |
|---|---|---|
| `services/market_calendar.py` | 1 (built), 4 (correction) | Built as a new file; **Phase 4 edits it** → serial with any other task touching it |
| `services/backfill_service.py` | 1 | New file — may run in parallel; depends on `market_calendar` only at import level |
| `ui/main_window.py` | 2 | **Serialization point** — depends on Phase 1; must not share a wave with another task touching it |
| `tests/test_market_calendar.py` | 3 (built), 4 (correction) | Built as a new file; **Phase 4 edits it** → serial per file |
| `tests/test_backfill_service.py` | 3 | New file — serial per file |
| `tests/test_history_backfill.py` | 3 | New file — serial per file |
| `docs/tasks/task-graph.json` | 4 | Task-Manager-owned; the `T37-T03` AC correction precedes the Phase-4 Build edit |

Practical rule: the Phase-1/Phase-2/Phase-3 split is inherently serial (Phase 2 consumes
Phase 1's planner; Phase 3 verifies Phase 2). `ui/main_window.py` is the single shared
production file touched by this batch, so at most one task may touch it per wave. Phase 4
touches `services/market_calendar.py` and `tests/test_market_calendar.py`; the corrected
`T37-T03` acceptance criterion is written by Task Manager before Build edits the module/
test. This is an architecture-level constraint on the task graph, not a task
decomposition — the Task Manager populates `touches_files` accurately and the Lead
enforces the wave rule.

## Assumptions
Derived from `docs/requirements/requirements.md` (A27–A33, confirmed where noted) and Plan's
D16 proposal; these are implementation details only — no requirements gap.

- **PA-D16-1 (detection granularity):** missing-span detection operates at **session/day
  presence** (a trading day with zero cached bars is missing), which matches the reported
  whole-session defect and avoids false positives from illiquid periods and from toggling
  Extended Hours on an RTH-only cache. Within-session partial holes below one trading day
  are out of D16's scope.
- **PA-D16-2 (`now` seam):** `now_ts = int(time.time())` is captured at load time in
  `MainWindow` and passed into the pure planner as a parameter, so the planner is
  deterministic under test.
- **PA-D16-3 (calendar applies to all symbols):** the ET equity holiday/session calendar is
  used for every symbol, consistent with the accepted D1/`session_service`/DG1 default;
  futures that trade some US holidays are not specially modelled (FI-D16-2, accepted with
  this caveat).
- **PA-D16-4 (chunk size):** the chunk step is the existing
  `TIMEFRAME_CONFIG[timeframe]["duration"]`; `MarketDataManager.req_historical_data` and its
  signature are unchanged.
- **PA-D16-5 (anchor format):** chunk `endDateTime` uses the existing
  `ui/main_window._ibkr_end_date` UTC hyphenated format (avoids TWS warning 2174),
  reimplemented as a tiny pure helper so `backfill_service` stays Qt-free.
- **PA-D16-6 (shortfall trigger):** a shortfall is surfaced when a backfill reqId raises an
  `error_msg`, or when a trading day in the target span is still empty after all requests
  complete. It is a status-bar + log message; requests are not retried in a loop.
- **PA-D16-7 (day presence; FI-D16-1 accepted):** a day counts as present if it holds at
  least one cached bar; the per-day cadence assertion in `AC-D16.1` is applied to the
  stubbed, liquid test scenarios, not to illiquid symbols (which are held to session-presence
  continuity). Recorded in `docs/plan_notes.md`.
- **PA-D16-8 (idempotence):** chunk overlap is deduped by the existing
  `(symbol, timeframe, ts)` primary key; no migration is required.
- **PA-D16-9 (render path):** `ui/chart_panel.py` is unchanged; continuity of `_bars` fixes
  both the price and volume panels (`AC-D16.2`).
- **PA-D16-10 (out of scope):** DG18 (persisting live/RT bars to the cache) remains out of
  D16's scope, as the Requirements Analyst recorded; the load-time backfill covers the
  visible hole either way.
- **PA-D16-11 (year-end exception is New-Year's-specific):** the `AC-D16.7` exception is
  implemented as a **New Year's-specific** observed-day rule, not by changing the generic
  `_observed` used by the other fixed-date holidays (Independence Day / Christmas /
  Juneteenth). When Jan 1 is a Saturday the corrected rule adds **no** closure at all — Dec
  31 stays a trading day and Jan 1 is non-trading as an ordinary weekend — so no substitute
  closure is introduced. This keeps the still-correct observed shifts untouched and is the
  minimal change to the built module.

No open requirements escalations: FI-D16-1 and FI-D16-2 were accepted by the Validator with
recorded resolutions (`docs/plan_notes.md`); RG-001/RG-002/RG-003 remain resolved and are
not reopened. **ESC-023** (the New Year's calendar defect) was escalated to the Requirements
Analyst and is now **resolved in requirements** as `AC-D16.7` / A33 / R27 / DG22; Phase 4
implements it. No open escalation remains.

---

Status: READY_FOR_TASK_MANAGER

