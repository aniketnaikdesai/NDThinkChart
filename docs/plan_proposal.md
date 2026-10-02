# Plan Proposal — NDThinkChart D16 (historical-bar gap backfill)

> **Status: DRAFT for Plan Artifact Editor & Validator. Not canonical.**
> **Revision 2 (2026-10-02) — ESC-023 correction increment.** The D16 batch (T37–T41) is now
> **built**; this revision adds the one corrective increment the `AC-D16.7` / A33 / R27 / DG22
> requirements change implies (New Year's year-end accounting exception) and records the rest
> of D16 as built/unchanged. It does **not** re-plan D1–D15 or any other part of D16.
> Incremental plan for **D16 only**, on top of the **as-built** D1–D15 baseline
> (`docs/architecture.md`; 383 passed, verified 2026-09-28). D1–D15 are frozen and are
> **not** re-planned. Companion proposal: `docs/architecture_proposal.md` (read the
> Codebase Summary there; it is the first section by requirement).

## Context / baseline

- **Defect:** `SPY` `5 mins` shows price candles 09/14–09/18, nothing 09/19–09/27, then
  09/28–10/02; the volume panel is empty over the same span. `_refresh_candles` drives
  both panels from the same `_bars`, so one bar-list fix serves both (AC-D16.2).
- **Root cause (A27, DG21):** `load_chart` issues **one** `req_historical_data` with
  `endDateTime=""` (up to now) and the fixed `TIMEFRAME_CONFIG` duration (`5 mins` →
  `5 D`). Any closure longer than that leaves an unfetched span. The reported hole is an
  **internal** discontinuity (newer bars are already cached after it), so a literal
  `BarCache.get_last_timestamp`/`MAX(ts)` tail anchor would **not** heal it (A32).
- **Outcome required:** the bar series is **continuous over its displayed span**; genuine
  market closures stay empty; backfill is chunked when the span exceeds one IBKR request;
  all six timeframes and any symbol (Q37–Q39 / AC-D16.1–AC-D16.5).
- **Build status:** D16 Phases 1–3 below are **built** (T37–T41, all done). This pass adds
  the **ESC-023 correction** (Phase 4): the D16 trading-day calendar wrongly marks **Dec 31**
  closed in every year whose next Jan 1 is a Saturday (a naive Saturday→preceding-Friday New
  Year's shift). `AC-D16.7` / A33 / R27 / DG22 record the corrected convention — per NYSE Rule
  7.2's year-end accounting-period exception **no New Year's holiday is observed and Dec 31
  stays a trading day**; the `T37-T03` acceptance criterion and `services/market_calendar.py`
  must both change, so a genuine bar hole on such a Dec 31 is backfilled (AC-D16.1) or its
  shortfall surfaced (AC-D16.4), never silently classified as a closure.

## Phases

> **Build status:** Phases 1–3 are **built** (T37–T41, all done) and are listed for
> completeness; **Phase 4 is the one active increment** in this pass (ESC-023 / `AC-D16.7`).
> Nothing else in D16 is re-planned.

### Phase 1 — Backfill planning (pure services) `[new]`
- **Goal:** Add the pure, Qt-free decision layer that says *which* historical spans are
  missing and *how* to request them — the trading calendar and the missing-span/request
  planner. No UI, no TWS.
- **Deliverables:**
  - `services/market_calendar.py` — ET trading-day/holiday calendar (holidays by rule;
    New Year's carries the `AC-D16.7` year-end accounting exception — Dec 31 stays a
    trading day when the next Jan 1 is a Saturday);
    `is_trading_day`, `trading_days(start_ts, end_ts)`, `session_windows(...)`.
  - `services/backfill_service.py` — `bar_period_seconds`, `find_missing_spans(
    cached_ts, now_ts, timeframe)`, `plan_requests(missing_spans, timeframe)`
    (chunk step = `TIMEFRAME_CONFIG[timeframe]["duration"]`; anchors formatted with the
    existing `ui.main_window._ibkr_end_date` behaviour, factored so the pure service does
    not import Qt).
- **Requirements/journeys covered:** Journey 17; D16; AC-D16.1, AC-D16.3, AC-D16.4,
  AC-D16.5 (planning halves); A27, A29, A32; DG21; DG19.
- **Dependencies:** none.

### Phase 2 — Load-path backfill orchestration (multi-request) `[new/changed]`
- **Goal:** Make `MainWindow` issue and correlate the chunk set, accumulate results, and
  finalise with a single save + re-read + render — keeping the single-request path
  behaviourally intact as a set of one.
- **Deliverables:** `[new/changed] ui/main_window.py`:
  - `load_chart` calls the planner; empty plan + current cache → **no redundant request**
    (edge case "cache end already at now"); otherwise issues one `req_historical_data`
    per `RequestPlan` using the existing `endDateTime` parameter (no `market_data.py`
    change).
  - Multi-id state: `_history_req_ids: set[int]`, `_history_generation: int`,
    `_backfill_missing_spans`, `_backfill_failed_req_ids`; `_on_historical_bar` /
    `_on_historical_data_end` accept members and finalise only when the set empties.
  - Symbol/timeframe switch and `closeEvent` cancel **every** id in the set (extend the
    current single-id cancellation).
  - `_on_error` correlates a failed backfill reqId with its span.
  - **Shortfall surfacing** (AC-D16.4): status-bar message + log when a backfill request
    errors or a trading day is still empty after the wave; never fabricate a bar.
- **Requirements/journeys covered:** Journey 17; AC-D16.1, AC-D16.2, AC-D16.4, AC-D16.5;
  edge cases (internal hole, tail gap, closures, Ext Hours, switch mid-flight, empty
  cache, fresh cache, retention shortfall); A28, A31.
- **Dependencies:** Phase 1 (its planner is the input).

### Phase 3 — Verification & regression `[new]`
- **Goal:** Prove D16 end-to-end offscreen (no live TWS) and prove no D1–D15 regression.
- **Deliverables (tests):**
  - `tests/test_market_calendar.py` — weekends/holidays (incl. Good Friday, Juneteenth,
    observed-day shifts) are non-trading; trading days are correct; **plus the `AC-D16.7`
    guard** — `is_trading_day` is **True** for `2021-12-31`, `2027-12-31`, `2032-12-31` and
    `2038-12-31`, and the other observed shifts (Independence Day/Christmas/Juneteenth/New
    Year's-on-a-Sunday) remain unchanged.
  - `tests/test_backfill_service.py` — **parameterized over all six timeframes × ≥2
    symbols** (Q39): seeded `ts` lists with a tail gap and an internal hole →
    `find_missing_spans` returns the expected missing weekdays; `plan_requests` covers
    the span and chunks when it exceeds the configured duration.
  - `tests/test_history_backfill.py` — offscreen real `MainWindow` (stubbed
    `IBApiClient.connect`/managers, pattern from `tests/test_watchlist_d14_midrag.py`):
    seed `BarCache` with the AC-D16.5 repro, drive the stubbed historical feed, assert
    `ChartPanel._bars` has the expected per-trading-day counts for 2026-09-21…09-25,
    **no** weekend bars, and the volume `height` array is non-zero wherever a candle
    exists (AC-D16.2); assert chunking (AC-D16.4); assert switch-mid-flight does not mix
    symbols/timeframes.
  - `tests/test_history_backfill` also covers the AC-D16.5 date range (2026-09-19 →
    2026-09-28 modulo closures) and an empty-cache fetch.
  - Full offscreen suite re-run must stay green (AC-D16.6).
- **Requirements/journeys covered:** AC-D16.1–AC-D16.6 (as built); the `AC-D16.7` calendar
  correction and its test updates are delivered by Phase 4.
- **Dependencies:** Phase 1 and Phase 2.

### Phase 4 — ESC-023 New Year's calendar correction `[new/changed]`
> **Active increment.** D16 is built; this is the only open work. It is a behaviour/AC
> correction, not a new subsystem: the D16 architecture otherwise stays as built.

- **Goal:** Correct the trading-day calendar so **Dec 31 is a trading day** whenever the next
  Jan 1 falls on a Saturday (NYSE Rule 7.2 year-end accounting exception), and update the
  `T37-T03` acceptance criterion/test that deliberately encoded the wrong convention — so a
  genuine bar hole on such a Dec 31 is backfilled (`AC-D16.1`) or its shortfall surfaced
  (`AC-D16.4`), never silently treated as a genuine closure.
- **Deliverables:**
  - **Task Manager (task-graph only):** correct the `T37-T03` acceptance criterion
    (`docs/tasks/task-graph.json`), test description and `expected_result` — replace "New
    Year's 2022-01-01 Saturday gives 2021-12-31 Friday closed" with the year-end exception;
    assert `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31` are **trading days**.
  - **`[new/changed] services/market_calendar.py`:** add the New Year's year-end exception to
    the observed-day rule. When Jan 1 is a **Saturday**, add **no** New Year's closure (so
    nothing is shifted onto Dec 31; Jan 1 remains non-trading as a weekend); Jan 1 on a
    **Sunday** still observes the following Monday; a **weekday** Jan 1 stays a closure.
    `_observed` for Juneteenth / Independence Day / Christmas is unchanged. Correct the stale
    "New Year's observed on the preceding Dec 31" docstring/comment.
  - **`[new/changed] tests/test_market_calendar.py`:** update T37-T03 — `is_trading_day`
    is **True** for `2021-12-31` (+ `2027-12-31`, `2032-12-31`, `2038-12-31`); drop the wrong
    `date(2021, 12, 31)` entry from the "weekend legal dates" loop (the Saturday legal date is
    `2022-01-01`); keep every other observed-shift assertion (Independence Day Sat→Fri,
    Christmas Sun→Mon, Juneteenth Sat→Fri, New Year's Sun→Mon) as the unchanged regression
    guard.
  - **Regression:** re-run the full offscreen suite; it must stay green (`AC-D16.6`).
- **Requirements/journeys covered:** D16 / Journey 17; `AC-D16.7` (primary), plus the
  `AC-D16.3` "not a genuine closure" carve-out and the `AC-D16.1`/`AC-D16.4`
  backfill-or-surface consequence; A33; R27; DG22; ESC-023.
- **Dependencies:** Phase 1 (the calendar this corrects). The corrected `T37-T03` AC must be
  written by Task Manager **before** Build edits the module/test, so Build implements the
  corrected criterion rather than the old one.

## Assumptions
Plan-level assumptions not already in `requirements.md`'s Assumptions Log (A27–A33):

- **PA-D16-1 (detection granularity):** missing-span detection operates at **session/day
  presence** (a trading day with zero cached bars is missing), which matches the reported
  whole-session defect and avoids false positives from illiquid periods and from toggling
  Extended Hours on an RTH-only cache. Within-session partial holes below one trading day
  are out of D16's scope.
- **PA-D16-2 (`now` seam):** `now_ts = int(time.time())` is captured at load time in
  `MainWindow` and passed into the pure planner as a parameter, so the planner is
  deterministic under test.
- **PA-D16-3 (calendar applies to all symbols):** the ET equity holiday/session calendar
  is used for every symbol, consistent with the accepted D1/`session_service`/DG1 default;
  futures that trade some US holidays are not specially modelled.
- **PA-D16-4 (chunk size):** the chunk step is the existing
  `TIMEFRAME_CONFIG[timeframe]["duration"]`; `MarketDataManager.req_historical_data` and
  its signature are unchanged.
- **PA-D16-5 (anchor format):** chunk `endDateTime` uses the existing
  `ui/main_window._ibkr_end_date` UTC hyphenated format (avoids TWS warning 2174),
  reimplemented as a tiny pure helper so `backfill_service` stays Qt-free.
- **PA-D16-6 (shortfall trigger):** a shortfall is surfaced when a backfill reqId raises
  an `error_msg`, or when a trading day in the target span is still empty after all
  requests complete. It is a status-bar + log message; requests are not retried in a loop.
- **PA-D16-7 (day presence):** a day counts as present if it holds at least one cached
  bar; the per-day cadence assertion in AC-D16.1 is applied to the stubbed, liquid test
  scenarios, not to illiquid symbols.
- **PA-D16-8 (idempotence):** chunk overlap is deduped by the existing
  `(symbol, timeframe, ts)` primary key; no migration is required.
- **PA-D16-9 (render path):** `ui/chart_panel.py` is unchanged; continuity of `_bars`
  fixes both the price and volume panels (AC-D16.2).
- **PA-D16-10 (out of scope):** DG18 (persisting live/RT bars to the cache) remains out
  of D16's scope, as the Requirements Analyst recorded; the load-time backfill covers the
  visible hole either way.
- **PA-D16-11 (year-end exception is New-Year's-specific):** the `AC-D16.7` exception is
  implemented as a **New Year's-specific** observed-day rule, not by changing the generic
  `_observed` used by the other fixed-date holidays (Independence Day / Christmas /
  Juneteenth). When Jan 1 is a Saturday the corrected rule adds **no** closure at all — Dec 31
  stays a trading day and Jan 1 is non-trading as an ordinary weekend — so no substitute
  closure is introduced. This keeps the still-correct observed shifts untouched and is the
  minimal change to the built module.

## Flagged Issues
Requirements the proposal cannot satisfy cleanly as written with any reasonable
architecture. Each has a suggested direction; the Validator turns accepted ones into the
official `plan_notes.md` escalation (Plan does not file it).

- **FI-D16-1 — AC-D16.1's measurable "maximum inter-bar gap within a trading session does
  not exceed one bar period" cannot hold for all symbols.**
  - *Which requirement:* AC-D16.1 (measurable clause), against Q39's "any symbol".
  - *Why it cannot be satisfied as written:* IBKR omits bars for periods with no trades,
    so a thinly traded symbol (or an empty pre-market period) legitimately has
    inter-bar gaps larger than one bar period even with a complete, correct bar list.
    Asserting cadence for "any symbol" would fail on correct data and would push the fix
    toward fabricating/interpolating bars — which AC-D16.3 and AC-D16.4 explicitly forbid.
  - *Suggested direction:* apply the cadence assertion to the stubbed/liquid scenarios
    (the SPY 5-min repro and a liquid second symbol per timeframe), and assert
    **session-presence** continuity for illiquid symbols. This keeps the fix honest and
    matches the defect class.

- **FI-D16-2 — "all timeframes and any symbol" vs. an equity holiday calendar for
  instruments that trade on US equity holidays.**
  - *Which requirement:* Q39 / A30 ("any symbol"), AC-D16.3 (holidays are closures).
  - *Why it cannot be satisfied as written:* a calendar that treats a US equity holiday
    as non-trading is wrong for futures (which trade some of those days), while a
    per-instrument calendar is not feasible from the current contract model. One calendar
    cannot be simultaneously correct for equities and for all futures.
  - *Suggested direction:* scope D16's continuity guarantee to the accepted equity-session
    model (the existing DG1/A7 default) and record the futures caveat; or, if truly
    symbol-generic behaviour is required, escalate to the Requirements Analyst to define
    per-instrument session handling.

**ESC-023 correction pass — no new Flagged Issues.** `AC-D16.7` is satisfiable as written:
it is a self-contained holiday-rule correction with clear, measurable offscreen assertions
(`is_trading_day(2021-12-31/2027-12-31/2032-12-31/2038-12-31) is True`) plus an unchanged
observed-shift regression guard. It requires no requirements escalation, and the earlier
FI-D16-1 / FI-D16-2 remain accepted and unchanged.

## Handoff
`docs/architecture_proposal.md` and this file are complete pending validation. The
Validator reads both, checks them against `requirements.md`, and — if they pass — writes
the canonical `docs/architecture.md` / `docs/plan.md` itself. Nothing here is canonical
until then.

Status: READY_FOR_VALIDATION
