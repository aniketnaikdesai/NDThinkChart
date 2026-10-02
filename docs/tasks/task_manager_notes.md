# Task Manager Notes — Batch 3–9 revision (T21–T31)

Revision date: 2026-09-27. Source of truth: `docs/plan.md` (APPROVED, validation pass 2)
and `docs/architecture.md`.

## Scope added
T21–T31 extend the existing T1–T20 graph (all `done`, unchanged) with the approved
revision work and the Code Reviewer escalations that the plan now covers:
ESC-002 (T21), ESC-003/ESC-008 (T22), ESC-007 (T23), ESC-006/D2 (T24, T25),
ESC-001 (T26), RC-4a D10 (T27), ESC-005 (T28), ESC-009 (T29), ESC-010 (T30),
plus a revision-wide verification task (T31).

## Sequencing / `touches_files`
- `ui/chart_panel.py` is touched by T21, T22, T23, T24, T27, T28 and T30. Because the
  Lead must not run two tasks with overlapping `touches_files` in one wave, the chain is
  encoded as explicit dependency edges — `T21 → T22 → T23 → T24 → T27 → T28 → T30` — in
  addition to the per-task `touches_files` field, so wave scheduling is deterministic.
- T25 (`tests/test_drawing_labels.py`), T26 (`data/db.py`, `tests/test_db_schema.py`) and
  T29 (`tests/test_chart_dpi.py`, `tests/conftest.py`) share no file with the
  `chart_panel.py` chain and may be scheduled concurrently with it.
- T28 also depends on the already-built T17 (watchlist clamp); T30 on the already-built
  T18 (D14 double-click path). Done tasks are treated as satisfied dependencies.
- T31 (`touches_files: []`) depends on all of T21–T30 and is the single terminal
  verification node for this revision.

## Flagged items (no requirements gap)
1. **A25 — D2 dock-open visibility needs independent Code Reviewer verification.** T24's
   Build tests cover the chip lane/style/tracking and a dock-open layout assertion, but
   per `Architecture Risks` and `requirements.md#D2/A25` the re-opened D2 defect surface
   (decimals covered by the right-hand dock) must be **independently verified by the Code
   Reviewer after Build**. The task graph cannot make this a Build-only pass; T24's
   acceptance criteria record the requirement so the Code Reviewer can key off it.
2. **ESC-005 may need a minimal rebalance change.** T28 is scoped as a combined
   integration test, but `ui/chart_panel.py` is included in its `touches_files` so Build
   may add a single rebalance helper if hiding the volume panel plus a max-clamp watchlist
   drag can drop the price panel below its 400px minimum. No architecture decision beyond
   the plan's "consider a single `rebalance()` helper" is required.
3. **TR-17 ownership.** The Phase-4 symbol-change mode reset (router → `IDLE`) is wired in
   T30 (`ui/chart_panel.py`), which depends on T21's `exit_to_idle()` API. `DrawingOverlay.set_data()`
   already clears the draft/drag defensively (`:112–118`); T30 only adds the router reset
   and the ESC-010 regression test.

No architecture assumptions were invented and no requirements ambiguity was found; the
items above are coordination/verification notes carried from the approved plan and the
escalations file.

## Revision — ESC-013..ESC-019 follow-ups (T32-T36) and the ESC-018 wording fix

Revision date: 2026-09-28. Source: docs/code_review/escalations.md (ESC-013..ESC-019) and
docs/code_review/review_log.md (Revision 2 review). Scope: close the five BUILD escalations that
block T31, correct the one Task-Manager-owned wording defect (ESC-018), and make T31 reachable.

### ESC-018 — T22 wording fix (definition only)
T22's 5th acceptance criterion replaced the unachievable "Fixture fixed points"
(_nice_volume_max(v) == v) predicate with the achievable "Fixture mappings (ESC-018)" statement:
every retained tests/test_volume_linear.py expectation is reproduced as an input -> output
mapping (8_000 -> 10_000, 80_000 -> 100_000, 2_200_000 -> 2_500_000, 1_050_000 -> 1_500_000);
every legacy fixed-list entry and every confirmed output is a member of the pinned family
1 / 1.5 / 2 / 2.5 / 5 / 7.5 x 10^k; and only _nice_volume_max(0) changes to 100. Tests T22-T02
and T22-T06 were updated to assert family membership plus the reproduced mappings (no "fixed
point" language). Under nice_max = smallest family value >= v*1.1, no positive v is a fixed
point — every positive value advances — so the old wording was mathematically unachievable.
T22's status and implemented code are unchanged.

### New tasks (ESC mapping / touches_files)
- T32 (ESC-013, blocking): D6 dense-view body-clamp ordering fix. touches_files:
  ui/chart_panel.py, ui/candlestick_item.py. deps [T30].
- T33 (ESC-014, blocking): D11 label stacking by measured bbox height. touches_files:
  ui/drawing_overlay.py. deps [].
- T34 (ESC-015): update tests/test_volume_log.py to the pinned family (1_500). touches_files:
  tests/test_volume_log.py. deps [].
- T35 (ESC-016): update the four stale inside-plot crosshair assertions to the D2/Q33
  Y-axis-lane contract. touches_files: tests/test_chart_crosshair.py,
  tests/test_crosshair_chip_bounds.py. deps [].
- T36 (ESC-017): sync MainWindow.draw_combo to Cursor when the router clears the draw tool
  (blockSignals), plus tests/test_draw_combo_sync.py. touches_files: ui/main_window.py,
  tests/test_draw_combo_sync.py. deps [T21].

### Sequencing
ui/chart_panel.py remains the serial hot file; T32 (chart_panel.py + candlestick_item.py) runs
after T30, so no wave has two writers on chart_panel.py. T33, T34, T35 and T36 touch disjoint
files (drawing_overlay.py; test_volume_log.py; the two crosshair test files; main_window.py plus
the new test) and may run in parallel with T32 and with each other.

### T31 reachability reconciliation
T31 (the single terminal verification node) now depends on
[T21,T22,T23,T24,T26,T27,T28,T30,T32,T33,T34,T35,T36]: the two blocked tests-only tasks (T25,
T29) were dropped from its dependency list — they depend on the code fixes rather than gating
them — and the five fixes T32-T36 were added. T31's title, description, expected_artifacts,
inputs and T31-T03 were extended to cover the ESC-013..ESC-017 modules. T25 and T29 remain in
the graph and remain blocked; edges T25 -> T33 and T29 -> T32 record that their failing criteria
close once the fixes land.

### Out of scope for Task Manager
- ESC-011 (root-doc test counts/markers in usage.md / PENDING_IMPLEMENTATION_PLAN.md and the
  orphaned .pyc): root-level docs are owned by no pipeline agent — a user/owner dependency, not
  a task-graph change.
- ESC-019 (stale eye-glyph "Volume" prose in the Plan-owned docs/plan.md, docs/plan_review.md,
  docs/architecture_proposal.md): Plan/Validator territory; already fixed by Plan/Validator.
  Not a task-graph change.

## D16 — historical-bar gap backfill (T37–T41)

Revision date: 2026-10-02. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`, D16 approved) and `docs/architecture.md` (canonical as-built +
D16 additions). Scope: the D16 delta only, on top of the frozen, built-and-green D1–D15
baseline (tasks T1–T36 are `done` and are deliberately **not** re-listed in the rebuilt
graph). No open `ESCALATED_TO_TASK_MANAGER` entry exists.

**No architecture assumptions were invented and no requirements ambiguity was found.**
The architecture fixes both new service APIs, the MainWindow multi-request state
(`_history_req_ids`, `_history_generation`, `_backfill_missing_spans`,
`_backfill_failed_req_ids`), the unchanged `bars` schema and `req_historical_data`
signature, and the shortfall surface, so every task is `architecture_dependency: false`.

### Tasks and `touches_files`
- **T37** — `services/market_calendar.py` + `tests/test_market_calendar.py`.
- **T38** — `services/backfill_service.py` + `tests/test_backfill_service.py`.
- **T39** — `ui/main_window.py` + `tests/test_history_backfill_loadpath.py`.
- **T40** — `tests/test_history_backfill.py` (the plan's Phase-3 integration file).
- **T41** — `touches_files: []` (full-suite regression gate; writes only Build's own log).

### Sequencing (why the batch is a serial chain)
- The dependency edges `T38 → T37 → … `, `T39 → T38`, `T40 → T39`, `T41 → T40` encode the
  real build order: the planner needs the calendar's trading-day behaviour to compute (and
  test) the missing spans, the load path needs the planner, the end-to-end proof needs the
  load path, and the regression gate runs last. The plan's Phase-1 note that the two new
  services "may run in parallel" was **not** followed: `find_missing_spans` and its tests
  consume `market_calendar`'s holiday/trading-day results, so T38's correctness assumes the
  contract T37 establishes. Per the dependency-mapping rules, correctness wins over the
  optimistic parallelism note; the edge costs only parallelism in an inherently serial batch.
- `ui/main_window.py` remains the single shared production file and is touched by T39 only,
  so at most one task writes it per wave; `tests/test_history_backfill.py` is touched only
  by T40. No wave contains two writers on the same file.

### Deviation from the plan's phase-to-file mapping (test placement)
- The plan lists `tests/test_market_calendar.py`, `tests/test_backfill_service.py` and
  `tests/test_history_backfill.py` as Phase-3 deliverables. The task schema requires every
  task's acceptance criteria to carry matching tests *within that task*, so each
  implementation task ships its own tests: T37 and T38 own the two pure-service unit-test
  files (their subjects' verification), and T39 ships focused offscreen load-path tests in a
  new `tests/test_history_backfill_loadpath.py` so the orchestration behaviour is verifiable
  independently of the end-to-end proof. T40 then owns the plan's
  `tests/test_history_backfill.py` for the whole-path e2e verification (the AC-D16.5 repro,
  both panels, closures, chunking over all six timeframes × ≥2 symbols, switch-mid-flight,
  empty cache). This is a decomposition/testing decision only; it changes no architecture and
  drops no plan deliverable.
- `ui/chart_panel.py`, `data/bar_cache.py`, `ibkr/market_data.py`, `data/bar_aggregator.py`
  and `services/session_service.py` are consumed unchanged and appear in no task's
  `touches_files`; T41 explicitly verifies `ui/chart_panel.py` and `ibkr/market_data.py`
  stay untouched.

### Acceptance-criteria coverage (AC-D16.1–AC-D16.6)
- `AC-D16.1`: T38-T02/T03/T04 (planning halves, all six timeframes, internal hole + tail gap)
  and T40-T04 (end-to-end, six timeframes × ≥2 symbols).
- `AC-D16.2`: T40-T02 (price candles and volume heights across the backfilled span).
- `AC-D16.3`: T37-T02/T03/T04/T05 (closures/holidays are non-trading) and T40-T03
  (no fabrication across a closure, no axis compression).
- `AC-D16.4`: T38-T06 (chunking/coverage/anchors), T39-T06/T07 (error + residual shortfall
  surfaced, never fabricated), T40-T04 (chunking end-to-end).
- `AC-D16.5`: T40-T01 (reported repro 2026-09-19→09-28 modulo closures).
- `AC-D16.6`: T41-T01 (full offscreen suite stays green, no D1–D15 regression), with T41-T02
  confirming the render path/request signature were reused unchanged.

### Out of scope / carried forward
- D1–D15 tasks (T1–T36) are `done` and intentionally absent from the rebuilt graph.
- DG18 (persisting live/RT bars) remains out of D16 scope per PA-D16-10; no task covers it.
- A28 (IBKR may not return the missing bars) is a data-availability risk handled by the
  `AC-D16.4` shortfall path, not a task-graph item.

## ESC-023 — New Year's year-end calendar correction (T37 corrected, T42 added)

Revision date: 2026-10-02. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`, Phase 4 — ESC-023) and `docs/architecture.md` (ESC-023 correction,
validated 2026-10-02). Input: `docs/code_review/escalations.md` ESC-023, routed through the
Requirements Analyst and resolved in requirements as `AC-D16.7` / A33 / R27 / DG22. No
`ESCALATED_TO_TASK_MANAGER` entry exists — this correction arrives via the
requirements/plan cascade.

### What changed
- **T37 reopened** (`done` → `not_started`). Task Manager only ever sets `not_started`;
  Build advances the status. T37 remains the sole producer for
  `services/market_calendar.py` + `tests/test_market_calendar.py`.
- **T37's third acceptance criterion corrected.** It previously encoded the wrong
  convention ("New Year's 2022-01-01 Saturday gives 2021-12-31 Friday closed"). It now
  states the **NYSE Rule 7.2 year-end accounting-period exception** (`AC-D16.7`): when
  Jan 1 is a Saturday, no New Year's closure is observed and Dec 31 of that year
  (`2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31`) is a **trading day**; the
  unchanged weekend-falling shifts (Independence Day Sat→Fri, Christmas Sun→Mon,
  Juneteenth Sat→Fri, New Year's Sun→Mon) remain non-trading regression guards.
- **T37-T03 test description and `expected_result` corrected to match** — asserts the four
  Dec-31 dates (and the following Monday `2022-01-03`) are trading days, keeps the
  unchanged observed-shift guards, and drops the wrong `date(2021, 12, 31)` entry from the
  weekend-legal-dates loop (its Saturday legal date is `2022-01-01`). Still 1:1 with the AC.
- **T37 title/description/inputs updated** to reference `AC-D16.7`, ESC-023 and the
  year-end exception.
- **New task T42 — ESC-023 correction regression gate**, `task_type: verification`,
  `touches_files: []`, `dependencies: [T37]`. Re-runs the full offscreen suite for
  `AC-D16.6` and confirms only `services/market_calendar.py` +
  `tests/test_market_calendar.py` changed, so the corrected `is_trading_day` contract is
  consumed with no consumer-side change.

### Why a separate verification task (T42)
`AC-D16.6` (full suite stays green) and the plan's Phase-4 "Regression: re-run the full
offscreen suite" are a distinct verification cluster from T37's module-level unit tests;
per the task-sizing rule they are not merged into T37. The historical D16 gate T41 stays
`done` as the record for the pre-correction batch; T42 is scoped to the ESC-023 correction.

### Dependencies / sequencing
- Edge added: `T42 → T37` (`DEPENDS_ON`). T42 cannot run until the corrected calendar
  lands.
- T38 (`services/backfill_service.py`) consumes `market_calendar.is_trading_day` but is
  **not** reopened: the correction changes only the Dec-31-of-a-Jan-1-Saturday result, the
  interface is unchanged, and T38/T39/T40's seeded scenarios (Sept–Nov 2026) contain no
  year-end/Jan-1 dates (verified by direct inspection of
  `tests/test_backfill_service.py`, `tests/test_history_backfill.py`,
  `tests/test_history_backfill_loadpath.py`). File-level and contract-level independence
  both hold, so no speculative edges were added to T38–T40.
- No wave contains two writers on the same file: T37 writes
  `services/market_calendar.py` + `tests/test_market_calendar.py`; T42 writes nothing
  (`touches_files: []`).

### Verification of the corrected artifacts
Direct source inspection (repository authoritative; the committed graphify graph is stale —
it has no `market_calendar` node):
- `services/market_calendar.py::_observed` (`:82-92`) is applied to New Year's Day at
  `:112`, so a Saturday Jan 1 currently shifts onto Dec 31 — the defect.
- `tests/test_market_calendar.py:112-116` asserts `is_trading_day(date(2021, 12, 31)) is
  False` and includes `date(2021, 12, 31)` in the weekend-legal-dates loop — both to be
  corrected by Build under T37.
- The wrong convention appears in no other source/test file (grep for Dec 31 / year-end /
  accounting returned only these two files plus the test comment at `:124`, which already
  expects `2022-01-03` to be a trading day and stays valid).

No architecture assumptions were invented and no requirements ambiguity was found:
`AC-D16.7`, A33, R27 and DG22 fully specify the corrected convention, and the architecture
fixes the corrected `_observed` rule, so T37 and T42 are both
`architecture_dependency: false`.

### Graph state
`task-graph.json` metadata remains `"status": "READY_FOR_BUILD"`; T37 and T42 are
`not_started`. No dependency cycles; every edge references an existing task id.

## ESC-024 — stranded-wave robustness (T43) [recorded retroactively] and ESC-025 (T44 added)

Revision date: 2026-10-02. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`) and `docs/architecture.md`. Input: `docs/code_review/escalations.md`.

### T43 (ESC-024) — recorded here for graph provenance
T43 ("Cancel and finalise the backfill wave on disconnect or a stalled request so the
shortfall is surfaced (D16 / ESC-024)") was added in the ESC-024 rework round and is now
`done` (built, independently re-verified, and closed by the Code Reviewer). It is the sole
producer for `ui/main_window.py`'s stranded-wave lifecycle and ships
`tests/test_history_backfill_disconnect.py` (T43-T01…T43-T06). `escalation: "ESC-024"`.
No separate Task-Manager note was appended in that round; this entry records the graph
state it left behind.

### ESC-025 — new task T44 (nice-to-have, user-approved)
ESC-025 is a single `ESCALATED_TO_BUILD`, non-blocking quality entry with two items on
T43's new code (both confirmed against the live tree):

1. **`closeEvent` leaves the watchdog armed.** `closeEvent` (`ui/main_window.py:1357–1390`)
   calls `_cancel_history_requests()` + advances `_history_generation` (`:1370–1373`) but
   never calls `_disarm_history_wave_watchdog()`, so `_history_wave_timer.isActive()` stays
   `True` after `win.close()`. Benign today (the empty-set guard in
   `_finalize_stranded_history_wave` makes a late fire a no-op) but not symmetric with the
   finalise (`:763`), disconnect (`:409`), timeout (`:443`) and load_chart (`:497`) disarms.
2. **`reason` is a dead parameter.** `_finalize_stranded_history_wave(reason=...)`
   (`:412`) is passed `"Disconnected from IBKR"` (`:409`) and
   `"Historical backfill timed out"` (`:443`) but never reads/logs it, so a watchdog timeout
   and a transport disconnect produce an identical surfaced message.

- **Task T44** — `bugfix`, `dependencies: [T43]`, `escalation: "ESC-025"`,
  `architecture_dependency: false`, `status: not_started`.
  `touches_files`: `ui/main_window.py`, `tests/test_history_backfill_disconnect.py`.
  Both files are T43's footprint; T44 is a focused follow-up on the same code, so it is
  serialized behind T43 by both the edge and the shared `touches_files`.
- **Acceptance criteria (4) with matching tests:**
  - T44-AC1 → **T44-T01**: `closeEvent` disarms the watchdog (`isActive()` False after close).
  - T44-AC2 → **T44-T02**: `closeEvent` cancels/empties the wave, advances the generation,
    and disarms via the same `_disarm_history_wave_watchdog()` helper the other paths use —
    arm/disarm symmetry confirmed.
  - T44-AC3 → **T44-T03**: the `reason` is read and makes timeout vs disconnect
    distinguishable in the status-bar/log diagnostics, **while preserving** the AC-D16.4
    shortfall wording T43-T03/T43-T05 assert on (`"incomplete"` + a named missing day +
    the `"Historical backfill shortfall"` WARNING). The ESC-025 direction permits either
    "use" or "remove cleanly"; the ACs pin the **use** option because removal would silently
    drop the diagnostic distinction the two call sites already intend, and AC4 keeps it
    behaviour-neutral either way.
  - T44-AC4 → **T44-T04**: behaviour-neutral — no fabricated bar, exact in-flight reqId set
    cancelled, set emptied, finalise once.
- **Sequencing / graph:** edge added `T44 → T43` (`DEPENDS_ON`). T43 is `done`, so T44 is
  immediately ready. No wave contains two writers on the same file (T44 is the only live
  writer of both its files). No dependency cycles; every edge references an existing task id.
- **No requirements ambiguity and no architecture assumption:** ESC-025 is a
  wording-only / small code change with an explicit "no AC change" directive; the
  architecture already fixes `closeEvent`, `_disarm_history_wave_watchdog` and
  `_finalize_stranded_history_wave(reason)`, so T44 is `architecture_dependency: false`.

### Graph state
`task-graph.json` metadata is `"status": "READY_FOR_BUILD"`; T37–T43 remain `done`; T44 is
`not_started`. Unique task/test ids; every acceptance criterion has ≥1 linked test and every
test links an existing criterion; `execution_graph.json` nodes match the task set and all
edges resolve with no cycles.
