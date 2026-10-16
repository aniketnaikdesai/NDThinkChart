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

## Batch 11 — D17 (watchlist live resize) + D18 (single right-dock region) (T45–T51)

Revision date: 2026-10-03. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`, Batch 11, 5 phases) and `docs/architecture.md` (D17/D18 increment,
validated 2026-10-03). Input: `docs/requirements/requirements.md` (`AC-D17.1`–`AC-D17.6`,
`AC-D18.1`–`AC-D18.8`, Journeys 18–19, A34–A36, R28–R31, B1–B4 answered). No open
`ESCALATED_TO_TASK_MANAGER` entry exists. D1–D16 (T1–T44) are `done` and are deliberately
**not** re-listed in the rebuilt graph.

**No architecture assumptions were invented and no requirements ambiguity was found.**
The architecture fixes the new pure module (`ui/dock_layout.py`, its constants, and the
three function signatures `watchlist_max_width` / `right_dock_max_width` /
`plan_dock_widths`), the single shared `MainWindow._apply_dock_widths()`, the
`splitterMoved` / `resizeEvent` / `changeEvent(WindowStateChange)` wiring, the single
right-region container, and the panel width bound, so every task is
`architecture_dependency: false`.

### Tasks and `touches_files`
- **T45** (Phase 1) — `ui/dock_layout.py` + `tests/test_dock_layout.py` (pure width model). No deps.
- **T46** (Phase 1) — `ui/watchlist_panel.py` + `tests/test_watchlist.py` (chart-area denominator). deps [T45].
- **T47** (Phase 2, D17) — `ui/main_window.py` + `tests/test_d10_d13_integration.py` + new
  `tests/test_dock_widths_d17.py`. deps [T46].
- **T48** (Phase 3, D18 shape) — `ui/main_window.py` (one right region) + new
  `tests/test_dock_d18_region.py` + right-dock lookup updates in
  `tests/test_crosshair_axis_lane.py`, `tests/test_d10_d13_integration.py`,
  `tests/test_watchlist_d14_midrag.py`, `tests/test_history_backfill.py`,
  `tests/test_history_backfill_loadpath.py`, `tests/test_history_backfill_disconnect.py`.
  deps [T47].
- **T49** (Phase 4, D18 cap/bound) — `ui/main_window.py`, `ui/active_trader_panel.py`,
  `ui/active_portfolio_panel.py`, new `tests/test_dock_widths_d18_impl.py`. deps [T48].
- **T50** (Phase 4/5, e2e) — new `tests/test_dock_widths_d18.py`. deps [T49].
- **T51** (Phase 5, regression gate) — `touches_files: []` (writes only Build's own log).
  deps [T49, T50].

### Sequencing (why this is an inherently serial chain)
- `ui/main_window.py` is the single shared production file and is touched by **T47, T48 and
  T49**. Per the dependency-mapping rules and the plan's explicit architecture constraint,
  those three are a serial chain: `T47 → T48 → T49`. T48 assumes T47's `_apply_dock_widths`
  / width model exist and wires the single region into that shared path; T49 assumes T48's
  single right region exists before it can cap/cross-clamp it. The edges are logical
  (assumed interface/contract), not merely file-overlap.
- **T46 → T45** is a real contract dependency: `ui/watchlist_panel.py` delegates its cap to
  `ui/dock_layout.watchlist_max_width`, so T46's correctness assumes T45's function
  signature and formula. **T47 → T46** is likewise real: T47's live clamp reads the corrected
  chart-area denominator and (for the D18 cross-clamp to come) the shared `plan_dock_widths`
  rule.
- **T45 and T46 are disjoint files** (`ui/dock_layout.py`/its test vs
  `ui/watchlist_panel.py`/`tests/test_watchlist.py`) but still get an edge for the
  contract reason above (a missing edge here would be a semantic race, not a file race).
- No wave contains two writers on the same file: each `id` row above is the only live writer
  of its files (T47/T48/T49's shared `ui/main_window.py` is serialized by the edges).

### Compatibility surface (D18 reshape) — why the test updates sit in T48
The single right region necessarily changes the dock structure that existing tests key on:
- `_on_dom_toggled` does `findChild(QDockWidget, "Active Trader")`; the architecture keeps a
  stable title/`objectName` on the one region, so the production lookup keeps working.
- `tests/test_crosshair_axis_lane.py` uses `docks["Portfolio"]` (**dict indexing**) — this
  **breaks** with the reshape and must be updated to resolve the single region. It is
  updated in T48, not deferred, because T48 cannot satisfy its own regression AC otherwise.
- `tests/test_d10_d13_integration.py`, `tests/test_watchlist_d14_midrag.py`,
  `tests/test_history_backfill*.py` use **membership** hides (`if title in (...)`), which are
  tolerant of the removed "Portfolio" dock. They are updated in T48 anyway, per the plan's
  Phase-3/Phase-5 lockstep intent and `AC-D18.8`, so the single-region shape is explicit
  rather than implicitly tolerated.

Deviation from the plan's literal phase table (documented, not a scope change): the plan
lists the right-dock lookup updates as Phase 5. They are placed in **T48** (Phase 3) because
the reshape that removes the "Portfolio" dock and the reconciliation of the tests that
reference it are one independently-verifiable unit — leaving them in a later phase would make
T48 fail its own regression criterion. `tests/test_d10_d13_integration.py` is therefore
touched by both T47 (denominator, Phase 1/2) and T48 (lookup, Phase 3); they are already
serial (`T48 → T47`), so there is no file race and the denominator update lands first.

### Acceptance-criteria coverage
- `AC-D13.1`–`AC-D13.3` (denominator corrected by B1): T46-T01/T02/T03 (helpers/round-trip)
  and T47-T07 (`test_d10_d13_integration.py` in lockstep).
- `AC-D17.1`: T47-T01. `AC-D17.2`: T47-T02. `AC-D17.3`: T47-T03. `AC-D17.4`: T47-T04.
  `AC-D17.5`: T47-T05 (and cross-checked e2e in T50-T04's cross-clamp). `AC-D17.6`: T51-T01.
- `AC-D18.1`: T49-T04 (implementation) and T50-T01 (e2e). `AC-D18.2`: T49-T01 / T50-T02.
  `AC-D18.3`: T48-T01 / T50-T03. `AC-D18.4`: T49-T02 / T50-T02. `AC-D18.5`: T45-T05
  (pure rule) + T49-T03 (applied) + T50-T04 (e2e). `AC-D18.6`: T49-T05 / T50-T05.
  `AC-D18.7`: T49-T06 / T50-T06. `AC-D18.8`: T48-T04 + T51-T01.
- `AC-D2.1` (unchanged D2 chip/dock non-overlap, now against the single region): T48-T04 and
  T51-T02.

### Carried assumptions (from the approved plan, not invented here)
- `RIGHT_DOCK_MIN_WIDTH = 200` follows plan assumption **PA-D17D18-2** (the requirements
  specify that a right-region minimum exists — `AC-D18.4` — but not its value; the plan
  proposes ~200px). T45 encodes 200.
- The single right region keeps the title **"Active Trader"** with the Portfolio section
  stacked inside, per the architecture's chosen shape (`QDockWidget("Active Trader")`), which
  is what preserves `_on_dom_toggled` and the tolerant test lookups.
- The `splitterMoved` source may fall back to an event filter after `show()` (PA-D17D18-4);
  T47 explicitly carries the deferred acquisition + fallback so the Qt-version-dependent
  wiring is not a correctness gap, and T45 verifies the pure rule independently of the event
  source.

### Graph state
`task-graph.json` metadata is `"status": "READY_FOR_BUILD"`; T45–T51 are `not_started`.
Unique task/test ids; every acceptance criterion has >=1 linked test and every test links an
existing criterion (36 tests, 1:1); `execution_graph.json` nodes match the task set and all 7
edges resolve with no cycles.

## ESC-026 — plan_dock_widths below-minimum dock width (T52 added)

Revision date: 2026-10-03. Source of truth: `docs/plan.md` (`Status: READY_FOR_TASK_MANAGER`,
Batch 11) and `docs/architecture.md` (D17/D18 increment). Input: `docs/code_review/escalations.md`
**ESC-026** (`Status: open`, routed to BUILD, user-approved for a proper fix). No open
`ESCALATED_TO_TASK_MANAGER` entry exists — this reconciliation adds the missing task that ESC-026's
`kind: dock_layout_plan_below_minimum` finding requires.

### Diagnosis (root cause is a code bug — AC and architecture are correct)
ESC-026 is classified `code_bug`: `AC-D18.4` ("never below the minimum") and the architecture
cross-clamp row both specify the correct behaviour, and `plan_dock_widths`'s own docstring
(`ui/dock_layout.py:79–81`) promises it. The implementation violates it: the
`while left + right > budget:` shrink loop (`:100–114`) decrements `left`/`right` **without
re-flooring**, so a dock already capped-floored at `:89–90` can be pushed below its own minimum.
Independently reproduced against the live tree this round:
`plan_dock_widths(750, 100000, 200) -> (350, 0)` (right `0 < RIGHT_DOCK_MIN_WIDTH = 200`) and
`plan_dock_widths(750, 200, 0) -> (175, 175)` (both below their minimums). T45 legitimately
reported `done` with green tests because its one over-budget case (`(1200, 100000, 10)`) is
feasible at chart_area 1200 — a **coverage gap**, not an incorrect AC. The T49
`MainWindow._plan_dock_widths` in-place repair (`ui/main_window.py:1055–1118`, verified sound:
0/4340 violations) currently masks the defect at the MainWindow layer, but leaves two divergent
cross-clamp implementations in the repo.

### New task T52 (bugfix) — `escalation: "ESC-026"`
- `dependencies`: `["T45", "T49"]`. **T52 → T45** is the logical ordering edge: T52 corrects the
  function T45 created, so it assumes T45's signature/contract. **T52 → T49** is a real assumed-
  contract edge, not a file-overlap shortcut: T52 removes the T49 workaround, so the correctness
  of the T49 `MainWindow` path (cap + cross-clamp) is re-established by T52 and the earlier T49
  tests must still pass. `touches_files`: `ui/dock_layout.py`, `tests/test_dock_layout.py`,
  `ui/main_window.py` — the three files the fix writes (`tests/test_dock_layout.py` is
  `tests/test_dock_layout.py`'s existing T45 test file extended in place; `ui/main_window.py`'s
  shared footprint is serialized by the T52 → T49 edge).
- `architecture_dependency`: `false`. ESC-026 explicitly proposes **no AC, architecture, or
  task-breakdown change**; the fix is confined to the shrink loop and the workaround removal, so no
  architectural choice is required.
- **Acceptance criteria (4) with matching tests, 1:1:**
  - **T52-AC1 → T52-T01**: `plan_dock_widths` never returns below `WATCHLIST_MIN_WIDTH` (150) /
    `RIGHT_DOCK_MIN_WIDTH` (200) for any input, including one-sided and both-over-budget requests
    (grid enumeration clears the 108/1475 coarse-grid violations).
  - **T52-AC2 → T52-T02**: the exact reproduced cases `(750, 100000, 200)` and `(750, 200, 0)`
    return values `>=` the dock minimums (not `(350, 0)` / `(175, 175)`).
  - **T52-AC3 → T52-T03**: documented precedence is preserved — infeasible window returns exactly
    the dock minimums; a feasible over-budget window keeps `chart_area_w - left - right >=
    CHART_MIN_WIDTH` and never crosses a dock minimum, matching the unchanged docstring.
  - **T52-AC4 → T52-T04**: after the T49 repair is removed, the `MainWindow` shared apply path
    still enforces the 40% cap (`right <= floor(0.40 * chart_area)`) and the chart-area cross-clamp,
    so the retained T49/T50 tests still pass with `plan_dock_widths` as the single source of truth.
- **Status is `not_started`** (Task Manager only ever initializes to `not_started`; Build advances
  it). `escalation: "ESC-026"` is carried on the task so Build sees the diagnosis and evidence.

### Graph state
`task-graph.json` metadata remains `"status": "READY_FOR_BUILD"`; T45–T51 stay `done`/`done`/`done`/
`done`/`done`/`done`/`done` and T52 is `not_started`. `execution_graph.json` gains node `T52` and
edges `T52 → T45`, `T52 → T49` (9 edges total). Validation this round: unique task ids (8) and
test ids (40); every acceptance criterion has `>=1` linked test and every test links an existing
criterion (1:1); every edge references an existing task id; acyclicity confirmed via DFS — no
cycles. No wave can contain two writers on the same file: T52 is the only live writer of
`ui/dock_layout.py` and `tests/test_dock_layout.py`, and its `ui/main_window.py` write is serialized
behind T49 by the dependency edge.

### Out of scope (unchanged)
All other ESC-001…ESC-025 entries remain `addressed` and are not touched. T45's acceptance criteria
are **not** reworded: ESC-026's own root-cause classification confirms the AC is correct and only
the code and its test coverage were deficient.

## Batch 13 — D19 (toolbar scroll/elide wrapper) (T53–T60)

Revision date: 2026-10-05. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`, Batch 13, 3 phases) and `docs/architecture.md` (D19 increment,
validated 2026-10-05). Input: `docs/requirements/requirements.md` (`AC-D19.1`–`AC-D19.7`,
Journey 20, A37–A38, R32–R34, B5–B6 answered, DG27–DG28). No open
`ESCALATED_TO_TASK_MANAGER` entry exists. D1–D18 (T1–T52) are `done` and are deliberately
**not** re-listed in the rebuilt graph; this graph is the **D19 delta only**.

**No architecture assumptions were invented and no requirements ambiguity was found.**
The architecture fixes the `QScrollArea` mechanism and its exact properties (no frame,
`setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
fixed 36px, objectNames `"MainToolbar"`/`"ToolbarScroll"`), the `conn_badge` placement
(FI-D19-2), the untouched width model (B6 keeps `floor(0.50 × chart_area)`), and the five
affected harnesses, so every task is `architecture_dependency: false`.

### Tasks and `touches_files`
- **T53** (Phase 1) — `ui/main_window.py` + new `tests/test_toolbar_scroll_d19.py`. deps [].
- **T54** (Phase 2, D17) — `tests/test_dock_widths_d17.py`. deps [T53].
- **T55** (Phase 2, D18 e2e) — `tests/test_dock_widths_d18.py`. deps [T53].
- **T56** (Phase 2, D18 impl) — `tests/test_dock_widths_d18_impl.py`. deps [T53].
- **T57** (Phase 2, D18 region) — `tests/test_dock_d18_region.py`. deps [T53].
- **T58** (Phase 2, dock layout) — `tests/test_dock_layout.py`. deps [T53].
- **T59** (Phase 2, `AC-D19.6` guard) — `touches_files: []` (writes only Build's own log).
  deps [T53, T54, T55, T56, T57, T58].
- **T60** (Phase 3, regression + real dev) — `touches_files: []`. deps [T53…T59].

### Sequencing / why the edges are logical, not file-overlap
- T54–T58 each remove `toolbar.hide()` masking and (T54/T55) add the toolbar-visible
  `AC-D19.1`/`AC-D19.2`/`AC-D19.3` guards. They depend on **T53** because they locate the
  toolbar/wrapper by the stable `objectName`s T53 introduces and their toolbar-visible
  assertions only pass once T53's wrapper exists. This is an **assumed-interface** dependency
  even though the harness files are disjoint from `ui/main_window.py` — a missing edge would
  let a harness task run in the same wave as T53 and read a tree without the wrapper.
- T54–T58 are mutually disjoint test files and may parallelise across waves.
- **T59** depends on all five harnesses plus T53: `AC-D19.6` is a whole-guard property
  (≥1 D17 and ≥1 D18 toolbar-visible test **fails pre-fix at `5bd7c93`** and **passes
  post-fix**), so it cannot be verified until the guard tests exist and the fix lands. The
  intermediate red is intentional (R33), not a regression.
- **T60** depends on everything; it is the terminal regression + real-dev gate
  (`AC-D19.7`, `AC-D2.1`, R34/Q9).

### Test-placement deviation from the plan (documented, not a scope change)
The plan lists the optional `tests/test_toolbar_scroll_d19.py` in Phase 2. It is placed in
**T53** (Phase 1) instead because the task schema requires every task's acceptance criteria
to carry matching tests *within that task*: T53 owns `AC-D19.4`/`AC-D19.5`, so it ships its
own wrapper-specific offscreen tests. This changes no architecture, drops no plan
deliverable, and keeps the file disjoint from the five Phase-2 harnesses (no two writers on
one file).

### AC coverage
- `AC-D19.1`: T54-T02 (toolbar-visible watchlist reaches the cap). `AC-D19.2`: T55-T02.
  `AC-D19.3`: T55-T03.
- `AC-D19.4`: T53-T01 (i: central min-hint bound, still a central descendant), T53-T02
  (ii: controls reachable / scroll range > 0), T53-T04 (mechanism + `conn_badge`). 
- `AC-D19.5`: T53-T03.
- `AC-D19.6`: T54-T01/T55-T01/T56-T01/T57-T01/T58-T01 (masking removed, toolbar-visible)
  + T59-T01 (pre-fix red / post-fix green discrimination) + T59-T02 (no masking remains).
- `AC-D19.7`: T60-T01 (full suite) and T60-T03 (real dev build, R34). `AC-D2.1`: T60-T02.

### Graph state
`task-graph.json` metadata is `"status": "READY_FOR_BUILD"`; T53–T60 are `not_started`.
Unique task ids (8) and test ids (22); every acceptance criterion has ≥1 linked test and
every test links an existing criterion (1:1). `execution_graph.json` nodes match the task
set; 18 edges resolve to existing ids with no cycles (every edge points to a strictly lower
task number).

## Batch 14 — D20 (toolbar scrollbar lane) (T61–T64)

Revision date: 2026-10-06. Source of truth: `docs/plan.md` (`Status:
READY_FOR_TASK_MANAGER`, Batch 14, 3 phases) and `docs/architecture.md` (D20 increment,
validated 2026-10-06, incl. the Validator probe table). Input:
`docs/requirements/requirements.md` (`AC-D20.1`–`AC-D20.6`, Journey 21, A39–A40, R35–R36,
B7–B8 answered, DG29–DG30). No open `ESCALATED_TO_TASK_MANAGER` entry exists. D1–D19
(T1–T60) are `done` and are deliberately **not** re-listed in the rebuilt graph; this
graph is the **D20 delta only** (baseline commit `4d8952a`, D19 wrapper green).

**No architecture assumptions were invented.** The architecture fixes the whole D20
mechanism (the derived `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()`
wrapper height, the unchanged D19 wrapper properties, the measured offscreen 54px / macOS
~52px figures, the mapped-lane contract, and the untouched D17/D18 width model), so every
task is `architecture_dependency: false`. No requirement is narrowed or reinterpreted by
this decomposition; the one recorded supersession (`AC-D19.4`'s `<= ~40px` bound) is
carried on `AC-D19.4` by the Requirements Analyst and handled in lockstep in T61/T62.

### Tasks and `touches_files`
- **T61** (Phase 1 + the lockstep half of Phase 2) — `ui/main_window.py` +
  `tests/test_toolbar_scroll_d19.py`. deps `[]`.
- **T62** (Phase 2, new D20 assertions) — new `tests/test_toolbar_d20.py`. deps `[T61]`.
- **T63** (Phase 2, `AC-D20.6`/R36 discriminator) — `touches_files: []` (writes only
  Build's own log). deps `[T61, T62]`.
- **T64** (Phase 3, regression + real dev) — `touches_files: []`. deps `[T61, T62, T63]`.

### Why the production change and the D19 assertion update are one task (T61)
The D20 production change (wrapper height `36` → derived `36 + scrollbar extent`) makes the
pre-existing `tests/test_toolbar_scroll_d19.py::T53-T04` assertion `wrapper.height() == 36`
(and `minimumHeight() == maximumHeight() == 36`) **false**. `AC-D20.6`/R36 requires those
assertions be updated *in lockstep* — never left contradicting D20. Therefore the two edits
cannot be split into separate waves: a production-only task would leave the suite red with
no test of its own to run. T61 is exactly the D19 `T53` precedent (production file + the
phase's own assertion file in one task), scoped to the derived height plus the two existing
height assertions. Its acceptance criteria are the structural/mechanism outcome and the
`AC-D20.6` lockstep outcome; the new D20 behaviour assertions live in T62.

### Why the new D20 assertions are a separate, disjoint file (T62)
The plan sanctions the D20 assertions "in `tests/test_toolbar_scroll_d19.py` or a new
disjoint `tests/test_toolbar_d20.py`" (Phase 2 deliverable; parallel-sequencing table lists
the new file as disjoint and parallelisable). The new disjoint file keeps T61's footprint
narrow (`ui/main_window.py` + the existing D19 test only), separates the "keep the existing
assertions truthful" concern from the "prove the new D20 outcome" concern, and gives
`AC-D20.1`–`AC-D20.5` a dedicated, independently verifiable task. T62 depends on T61 because
its derived-height/lane assertions assume the contract T61 establishes (a logical
assumed-contract edge across disjoint files, per the dependency-mapping rules) and would
fail against the pre-fix tree.

### Sequencing / no file races
- `ui/main_window.py` is the only production file and is touched by **T61 only** — at most
  one writer per wave.
- `tests/test_toolbar_scroll_d19.py` is touched by **T61 only**; the new
  `tests/test_toolbar_d20.py` is touched by **T62 only**. No two live tasks share a file.
- T63 and T64 write no source/test file (`touches_files: []`); they record evidence in the
  Build-owned `docs/build/build_log.md` (Build's own artifact, not a Task-Manager file).
- Every edge points to a strictly lower task number: `T62→T61`, `T63→T61/T62`,
  `T64→T61/T62/T63`. No cycles; every edge references an existing task id.

### AC coverage
- `AC-D20.1`: T62-T01 (shown state) + T62-T02 (hidden state).
- `AC-D20.2`: T61-T01 (mechanism, derived height + 36px content row) and T62-T03 (derived
  relation + `< 60px` + lane below the content).
- `AC-D20.3`: T62-T04.
- `AC-D20.4`: T62-T05.
- `AC-D20.5`: T62-T06.
- `AC-D20.6`: T61-T02/T61-T03 (D19 height assertions updated in lockstep, module green),
  T63-T01 (pre-fix red / post-fix green discrimination), T64-T01 (full-suite regression +
  D17/D18 in a toolbar-visible window).
- `R35`: T64-T02 (and T62-T03's `< 60px`). `Q9`: T64-T03.

### Flagged interpretation (plan-resolved, encoded to keep Build from writing a failing bound)
**`AC-D20.2`'s measurable clause reads `container height <= ~52px and >= ~50px`, but the
adopted offscreen derived height is 54px.** The approved plan resolves this (RC-D20-1
direction a): the requirement's `~50–52px` is the **macOS** figure (scrollbar extent ~16px →
~52px); offscreen the extent is **18px**, so the derived strip is **54px**. The plan states
there is **no hard `[50, 52]` bound** and the assertions must use the **derived relation**
(`wrapper.height() == toolbar.height() + horizontalScrollBar().sizeHint().height()`) plus
`< 60px` (R35). T62-T03 encodes exactly that — it must **not** assert the literal
`[50, 52]` interval, which would fail at every offscreen run. This is the plan's explicit
resolution, not a Task-Manager reinterpretation.

**Mapped-lane form only.** The lane/overlap assertions use
`horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()` together with
`viewport().height() >= toolbar.height()` when the scrollbar is shown (plan RC-D20-2).
`geometry()` is disallowed — offscreen it reports `QRect(0, 0, …, 18)` (`top == 0`), which
would fail at every height. T62's tests and the T63 discriminator both carry this.

### Graph state
`task-graph.json` metadata is `"status": "READY_FOR_BUILD"`; T61–T64 are `not_started`.
Unique task ids (4) and test ids (13); every acceptance criterion has ≥1 linked test and
every test links an existing criterion (1:1). `execution_graph.json` nodes match the task
set; 6 edges resolve to existing ids with no cycles. No wave can contain two writers on the
same file.

## ESC-029 — D21-13-T05 condition-default wording correction (Batch 15)

Revision date: 2026-10-06. Source of truth: `docs/requirements/requirements.md` `AC-D21.10.5`
(`:1987`) and the live implementation/test. Input: `docs/code_review/escalations.md`
**ESC-029** (`Status: ESCALATED_TO_TASK_MANAGER`, open; user-approved nice-to-have, wording-only).

### What was wrong
The **task-graph prose only** for `D21-13-T05` was inverted versus the authoritative
`AC-D21.10.5`. The task description read
`alarm price 110 -> Cross Below, 90 -> Cross Above` for `last_price=100`, i.e. it stated the
condition backwards. The acceptance criterion (`task-graph.json` `:767`), the implementation
(`AlarmDialog` on-open `default_condition`), and the actual test
(`tests/test_alarm_d21.py::test_d21_13_t05_condition_default_on_open`, `:314-338`) were all
**correct** — the test asserts: current (100) below the alarm (110) -> **Cross Above**;
current (100) above the alarm (90) -> **Cross Below**; unknown -> **Cross Above** (matching the
user's original Issue 10). Only the D21-13-T05 description contradicted them.

### What changed (definition only)
- `docs/tasks/task-graph.json`, `D21-13-T05.description` corrected to:
  `Assert the on-open condition default for last_price=100: alarm price 110 -> Cross Above,
  90 -> Cross Below, None/unknown -> Cross Above; assert the user can override and the default
  is not recomputed on spinbox change.`
- Nothing else changed. `test_id`, `linked_acceptance_criterion` (`AC-D21.10.5`), `type`
  (`unit`), and `expected_result` are untouched; every other task and every `status` field is
  unchanged; the graph metadata remains `"status": "READY_FOR_BUILD"`.
- Swept the task graph for other repetitions of the inverted wording: the only other
  Cross-Below/Cross-Above prose is the `D21-13` task description (`:754`) and the copied
  `AC-D21.10.5` text (`:767`), both of which already read correctly. `execution_graph.json`
  carries no condition wording. No other location needed a change.

### Why no AC/test/code change
Per ESC-029 (and the Code Reviewer's own diagnosis), the AC, the implementation and the test
were already correct; the defect was confined to the Task-Manager-owned task-graph wording.
No task was reopened, no dependency edge changed, and no acceptance criterion was reworded.
The Code Reviewer (not Task Manager) flips ESC-029 to `addressed` after independently
re-verifying.

---

## D41 (Batch 18) — task graph regenerated 2026-10-15 (`fresh_graph`)

**Status:** graph written and validated; `docs/tasks/task-graph.json` + `docs/tasks/execution_graph.json`
carry `"status": "READY_FOR_BUILD"`. **63 tasks**, **999 dependency edges**, `check_tasks.py` exit 0.

### 1. Task-id convention (and a tooling flag)

`check_tasks.py` **requires** ids matching `^(P\d+)-` and enforces **one phase per graph**. The repo's
previous graph used batch-prefixed ids (`D22-02`, `D23-01`, …) — **those now FAIL the validator**
(`ERROR: task id must be phase-prefixed as P<n>-T<m>`), so this graph uses **`P1-T01` … `P1-T63`**.

- The D41 batch is **one graph** under the **`P1`** prefix (the legacy unsuffixed `plan_proposal.md`
  maps to `P1` in `pipeline_state.py`; `requirements.md` has no `## Phase P<n>` sections).
- The plan's **three internal phases are encoded as dependency barriers**, not as separate prefixes
  (a second prefix would fail the validator's one-phase rule):
  - every Phase-2 task (`P1-T21`–`P1-T59`) depends on **all 20** Phase-1 tasks;
  - every Phase-3 task (`P1-T60`–`P1-T63`) depends on **all 39** Phase-2 tasks.
- **Flag (tooling owner):** the id convention changed under the repo's existing graph; anyone
  re-running `check_tasks.py` on the committed `D2x-*` graph will see it fail. Not a D41 defect.

### 2. Phase / file / parallelism model

Phase-1 has **20 tasks** (one per file), Phase-2 **39 tasks** (one per file), Phase-3 **4 tasks**.
`ui/main_window.py` is a single task per phase (`P1-T11`, `P1-T27`). `tests/test_d27_reconnect.py` is
edited in **Phase 1** (`P1-T18`) and **Phase 2** (`P1-T59`) on disjoint line sets — the two tasks sit
in different phases and never share a wave.

Read-only simulation of the rolling frontier (`max_parallel_tasks` = 6, `touches_files` overlap rule)
gives **13 waves**: Phase 1 in waves 1–4, Phase 2 in waves 5–12, Phase 3 in wave 13 — i.e. **no wave
mixes two phases** (strict sequencing holds), and `P1-T27` (the long pole) sits alone in its wave.

### 3. Intra-phase dependency edges (why each exists)

Beyond the phase barriers, edges encode only load-bearing **contract / reference** relationships
(not file overlap — that is `touches_files`' job):

- **Deletion after the last referrer's removal:** `P1-T01←T09`; `T02←T09,T10,T11`; `T03←T10,T11`;
  `T04←T10,T11`; `T05←T09`; `T06←T10,T11` (Phase 1); `T21←T27,T25,T26,T35,T36`; `T22←T27,T24`;
  `T23←T22,T24` (Phase 2). Deleting a module while a same-phase referrer still imports it would break
  the tree mid-wave; this makes "remove the reference, then delete" explicit rather than incidental.
- **Provider-removal after its consumers' removal:** `T12←T11,T13` (bridge tick signals ← main_window
  connects + client emitter); `T14←T10` (`DEPTH_HEATMAP` ← session); `T15←T10,T11`
  (`resolve_footprint_contract` ← its callers); `T16←T11` (`footprint_cache` DDL ← main_window holder);
  `T28←T27,T29` (`update_mkt_depth` ← main_window connect + client emitter); `T30←T27,T22` (`DEPTH` ←
  main_window DOM + market_depth).
- **Contract assumption:** `P1-T27←T31` (the phase-2 gates call the new `validate_order(risk_reducing=)`
  keyword, so the keyword must land first); `P1-T32←T27` (main_window drops the
  `watchlist_panel.set_depth_manager` call); every Phase-2 test re-point that asserts the renamed dock,
  the removed `DOM` button or the removed `_place_order`/`active_trader` surface (`P1-T35`…`P1-T59`)
  depends on `P1-T27`.
- **Plan-directed:** `P1-T18←T10` — the plan's sequencing note says the depth-assertion drops "must
  land with the code they assert".

### 4. KEEP-list protection (AC-D41.4) — every survivor keeps an AC + a test

| Retained symbol (AC-D41.4 KEEP) | Task(s) that assert it survives |
|---|---|
| `footprint_cache_key` + `INDEX_PROXY` (S10) | `P1-T15` (kept verbatim) + `P1-T19` (rollover test re-homed into `test_d39_burst_search.py`) |
| `services/md_line_guard.py::assess` + `MainWindow._guard_md_lines` (S8) | `P1-T11` (guard kept), `P1-T17` (body unchanged), `P1-T20` (thresholds test re-homed into `test_d38_events_news.py`) |
| S0 generic-tick substrate (`S0_TICKS`, `s0_register_many`, `on_s0_*`, `tick_generic/tick_string/tick_news`) | `P1-T10`, `P1-T12`, `P1-T13`, `P1-T14`, `P1-T30` |
| `volume_baseline` + `yfinance_events_cache` tables | `P1-T16`, `P1-T63` |
| Retained order machinery: `ibkr/orders.py::bracket_order`, `validate_order`, id reservation, kill switch, registry/error routing, `check_live_port` | `P1-T31` (additive keyword; structural checks unchanged), `P1-T53` (D26.8 all-three-legs re-point), `P1-T54`, `P1-T55`, `P1-T62` |
| Retained `ref_price` source (`_symbol_last_prices` via `_ref_price_for`) | `P1-T27`, `P1-T62` |
| D27/D28 + chart; `ui/candlestick_item.py` and the volume-width math **untouched** (ESC-041 is separate) | `P1-T09` (explicit "unchanged + file untouched" AC), `P1-T52` (D28.1 order-path deferral re-pointed) |
| Deck/geometry rules (`ui/dock_layout.py::plan_dock_widths`, cap constants) | `P1-T34` (unchanged), `P1-T61` (re-asserted) |

### 5. Flags (no requirements ambiguity found; no Plan escalation)

- **F1 — plan-map imprecision (non-blocking), scoped and flagged, not silently resolved.** The plan's
  **Phase-2** `tests/test_d27_reconnect.py` row says *"edit (1 line) … Only this line changes in this
  phase"*, but its own **Phase-1** row and the **sequencing note** say the **DOM-depth** assertions are
  *kept until Phase 2* — and Phase 2 removes their subjects (`_subscribe_dom`, `_depth_req_id`,
  `self.depth_manager`). Dropping only the dock-title line would leave the suite red in Phase 2,
  violating `AP-11` (per-phase green). **Scoping taken:** `P1-T59` drops the DOM-depth assertions
  **and** re-points the dock title, on the basis of the plan's sequencing note + `AP-11`. **Plan should
  confirm** the Phase-2 row's "1 line" wording was shorthand. No requirements change implied.
- **F2 — `AC-D41.6` is deliberately not a Build task.** The `requirements.md` history markers are
  Requirements-owned and already applied (`AP-5`/`FI-3`); `P1-T60`'s scan excludes `docs/`.
- **F3 — three validator WARNs, not errors.** `P1-T60/T61/T62` create new files
  (`tests/test_d41_{removal,portfolio_dock,retained_order_path}.py`) that cannot appear in
  `context.read_files` (they do not exist yet); `check_tasks.py` labels this "ok if pure-output file".
- **F4 — escalation posture (not D41's work).** ESC-035/ESC-039/ESC-040 go **moot** by removal (DG66)
  and are **not** tasks; the **Code Reviewer** flips them after re-verification. The 11 unrelated open
  escalations (ESC-032/033/034/036/037/038/041/042/043/044/045, incl. **blocking ESC-041**) are out of
  scope and untouched. `P1-T09` explicitly keeps `ui/candlestick_item.py` / the volume-width math as-is.
- **F5 — graph status location.** `task-graph.json` carries `"status": "READY_FOR_BUILD"` **both** at the
  top level and under `"metadata"` (`pipeline_state.py` reads `metadata.status`; the pre-existing graph
  had it only top-level).
- **F6 — no undecided architectural choice and no requirements ambiguity** was encountered: the D41
  plan's `S1`–`S12`, `AP-1`–`AP-11` and the `FI-1`–`FI-6` dispositions settle every decision the
  decomposition needed (`ref_price` source = `S4`; dock model = `S6`; table drop = `S7`; re-homed gates
  = `S5`). **No Plan escalation.**

### 6. Verification (exact result)

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P1-T60: touches_files 'tests/test_d41_removal.py' not in context read_files (ok if pure-output file)
WARN: P1-T61: touches_files 'tests/test_d41_portfolio_dock.py' not in context read_files (ok if pure-output file)
WARN: P1-T62: touches_files 'tests/test_d41_retained_order_path.py' not in context read_files (ok if pure-output file)
OK: 63 tasks validated, execution_graph.json written.
(exit 0)
```

Cross-checks (read-only): `execution_graph.json` = **63 nodes / 999 edges**, equal to the sum of every
task's `dependencies`; all tasks `not_started`; all `agent == "Build"`; every acceptance criterion has
≥1 linked test; the P2→P1 and P3→P2 barriers hold; no backward edge from Phase 1.

### 7. Additional flag — mechanical `PAUSE` from a stale Requirements-owned file (tooling false positive)

`pipeline_state.py` computes `open_questions = open_questions.md.count("Status: open")`. The file's only
match is **prose**, not a live item — `docs/requirements/open_questions.md:828`: *"…without opening a
`Status: open (blocking)` item…"*. So `open_questions` reads as **1** and `pipeline_state` mechanically
returns `next: PAUSE — reason: open blocking questions for the user`, **before** it ever evaluates
`graph_current`. There is **no real blocking question** (`requirements.md` carries `Status: READY_FOR_PLAN`
and D41's Q48/Q49/Q50 are recorded answered; the batch-17 `open_questions.md` is a stale Requirements-owned
artifact with no D41 section). This is **not** a D41 decomposition issue and **not** mine to fix — flagged
for the **Requirements Analyst** / tooling owner (either refresh `open_questions.md` for D41, or make the
counter marker-aware so prose cannot fabricate a blocking question). The task graph itself is unaffected:
`check_tasks.py` passes and `task_manager_escalated` is `False`.

---

## D41 revision — P1-T27 split into P1-T64 + P1-T65 (`fresh_graph`, 2026-10-15)

**Trigger.** `P1-T27` was dispatched, its Build Worker **exhausted its 25-step budget mid-edit** and the task is now
abandoned. The user's directive: split it so no single worker can exhaust its budget, then finish it. This is a
**targeted revision of one task**, not a new phase: the other 62 tasks (24 `done` / 38 `not_started`) keep their
scope, acceptance criteria and `touches_files` unchanged.

### 1. The partial-application state the split must start from

`ui/main_window.py` **parses and imports cleanly** but is **incomplete and not functionally correct**. Already applied
by the abandoned worker (the new tasks must treat these as the starting state and **verify, not redo**): the
`MarketDepthManager`/`ActiveTraderPanel`/`on_depth_callback` imports and `DEPTH` from the `subscription_manager` import;
the `dom_btn` + its toolbar add; the single `QDockWidget("Portfolio")` (widget = `portfolio_panel`, title bar =
`portfolio_panel.summary_label`, `active_trader`/`right_dock_container`/`_right_dock_layout` deleted, collapse wiring on
`summary_label` only); `self.depth_manager` + `watchlist_panel.set_depth_manager(...)`; the
`update_mkt_depth`/`order_place_requested` connects and `self._depth_req_id`'s assignment; `_rebind_depth_req_id`; the
`DEPTH` replay tag; the `_on_error` depth branch and the `_on_order_error` ticket line; the `_attach_live_feed` DOM
block; the re-written `_compute_right_dock_collapsed_min_width` / `_right_region_is_collapsed` /
`_sync_right_dock_collapse`; the whole `# ── DOM / Active Trader slots ──` and `# ── Order Entry ──` sections; and the
`_kill_switch` ticket line.

Still broken / not done (the new tasks' whole scope): **(1)** `_update_order_status` still calls the removed
`self.active_trader.set_order_status(...)`; **(2)** `closeEvent` still cancels the removed depth machinery via
`self._depth_req_id` / `self.depth_manager`; **(3)** `_ref_price_for` was never added; **(4)** the re-homed D26 gates
were never added to `_close_position_by_id`; **(5)** no AC probe was ever run, so the ACs were never verified.

### 2. The split (2 tasks — the rationale for not making it 3)

- **`P1-T64`** — *ui/main_window.py residual dead-reference cleanup: drop the Active Trader ticket call and the
  closeEvent depth cancels* (`size: S`). Leftovers 1–2. `touches_files: ["ui/main_window.py"]`.
- **`P1-T65`** — *ui/main_window.py — add `_ref_price_for` and re-home the D26 order gates onto
  `_close_position_by_id`* (`size: M`). Leftovers 3–4. `touches_files: ["ui/main_window.py",
  "tests/test_d28_6_close_contracts.py"]`. `dependencies: [Phase-1 barrier (20), P1-T31, P1-T64]`.

**Why two, not three.** The suggested third slice would have been "`_ref_price_for` alone" — a ~4-line method on the
same file as the gate task. Per the task-sizing rules, two tasks that share `touches_files` and context (and where one
is only minutes of work) merge rather than serialising on the same file and paying worker startup twice;
`_ref_price_for` is also the gate's own argument (`ref_price=self._ref_price_for(symbol)`), so it is one
independently-verifiable unit only when split from the gate by intent, not by file. The failure mode being fixed is
**worker exhaustion**, and the honest step count is what sizes the tasks: T64 is two small deletions plus a source scan
and one close-path suite run (~8 steps); T65 is one new method plus one insertion point plus one test-file re-point plus
its own gate probes (~15 steps). Both sit inside the ~20-step budget with headroom; the abandoned L-sized T27 tried to
carry all five leftovers at once.

**Why `P1-T65 → P1-T64` is a real edge, not a file-overlap shortcut.** Bit-for-bit the two tasks do not need each
other's edits to be *written*, but the 38 dependents must gate on the **complete** T27 deliverable, and Build serialises
them on `ui/main_window.py` regardless. Making T64 the head of an explicit chain means "the last task in the chain"
(T65) is a sound single dependency for every dependent: depending on T65 implies depending on T64 transitively. Without
the edge, a wave could complete T65 (the gate) while T64's cleanup was still outstanding, and a dependent would start
against a file that is not in its final T27 shape. The edge costs nothing (they cannot run in parallel anyway) and makes
the barrier correct.

### 3. Re-pointing the 38 dependents

All **38** former `P1-T27` dependents now list **`P1-T65`** in `dependencies`, exactly as before otherwise:

`P1-T21, P1-T22, P1-T23, P1-T28, P1-T29, P1-T30, P1-T32 … P1-T63` (38 tasks; `P1-T32`–`P1-T63` contiguous).
`P1-T27` appears in **no** `dependencies` list any more (`grep`/programmatic check: `any("P1-T27" in deps) == False`).

The **Phase-3 barrier** (`P1-T60`–`P1-T63`, each previously listing all 39 Phase-2 tasks) now reaches the complete
Phase-2 set as `P1-T21`–`P1-T59` + `P1-T65`, with **`P1-T64` covered transitively through `P1-T65`** — so the barrier
stays literally true for frontier computation without adding four redundant edges. Recorded in `metadata.notes`.

**Stale prose references left in place (deliberate).** Eight non-dependency mentions of the old id remain inside other
tasks' text — `P1-T21`/`P1-T22` read_files `why`, `P1-T22`/`P1-T28` acceptance-criteria prose, one `P1-T26` test
description, one `P1-T65`-adjacent `P1-T32` read_files `why`, and `P1-T59`'s description. They are not edited because the
directive for this revision is dependency-only and explicitly forbids changing another task's acceptance criteria; they
are inert strings that nothing parses. **Old → new mapping for a reader: any surviving `P1-T27` reference means
`P1-T64` (residual cleanup) followed by `P1-T65` (the complete deliverable).**

### 4. `test_command` defect fixed (it was self-referential)

`P1-T27`'s declared `test_command` was
`pytest tests/test_dock_widths_d18.py tests/test_d41_portfolio_dock.py -q` — but `tests/test_d41_portfolio_dock.py` is
**created by `P1-T61`** and `tests/test_dock_widths_d18.py` is **re-pointed by `P1-T38`**, both *downstream* of T27. T27
could therefore never make its own command pass. Each new task now carries a command that is runnable at its own
dispatch point:

- **`P1-T64`** — `source scan for the three leftover tokens` **&&** `pytest tests/test_d28_6_close_contracts.py -q`.
  Both are red before the task (the tokens are present; the suite's fixture closes a real window, so `closeEvent`'s
  leftover `AttributeError` fails it) and green after.
- **`P1-T65`** — `pytest tests/test_d28_6_close_contracts.py -q` (existing file), plus the task's own gate probes
  described in its `tests` block.

**Deferral recorded in each task's AC/tests** (so a red downstream command is not read as an implementation defect):
`P1-T64`'s `AC4`/`P1-T64-T41` (manual) and `P1-T65`'s `AC5`/`P1-T65-T51` (manual) state that
`tests/test_dock_widths_d18.py` (re-pointed by `P1-T38`) and `tests/test_d41_portfolio_dock.py` (created by `P1-T61`)
are **downstream**, that the new tasks' commands name only files that exist at dispatch, and that the AC-D41.5
full-suite/dock evidence is deferred to `P1-T38`/`P1-T61` and the Phase-3 gates (`P1-T60`–`P1-T63`).

### 5. New finding — a missed consumer of the retained close path, folded into `P1-T65`

The approved plan's Phase-2 `touches_files` map omits `tests/test_d28_6_close_contracts.py`, and no task in the graph
covered it. It is the **only existing suite that executes the real `_close_position_by_id`** (stock/option/future
contract reconstruction, four tests). Its `_make_window` stubs `IBApiClient.connect`, so the window's `_ibkr_connected`
stays `False` (set `False` in `__init__`, flipped only by `_on_connected` on the bridge's `connected` signal) — therefore
**`P1-T65`'s disconnected guard would blank all four tests**. That is a decomposition defect of exactly the kind the
escalation path exists for: on its own the task could not keep the retained suite green.

Resolution (mechanical, no re-scope of any other task): the file became part of **`P1-T65`'s `touches_files`**, its
fixture window is marked connected in that task, and the file is that task's `test_command`. Full-suite evidence belongs
to `P1-T60`/`AC-D41.5` regardless; this only keeps a retained, previously-green suite truthful between T65 and Phase 3.
(The Batch-14 `T61` precedent — production change plus the assertion it invalidates in one task — applies.)

### 6. Two supporting checks run this round

- **Source verification of the leftovers** (read-only `grep`): `self.active_trader` occurs only at
  `ui/main_window.py:3006`; `self.depth_manager` only at `:3170`/`:3173`; `self._depth_req_id` only at `:3169`/`:3171`
  (nothing assigns it) — i.e. exactly leftovers 1–2 and nothing else. `main_window.py` is touched by `P1-T11` (`done`)
  and the new chain only, so no other live task shares the file.
- **Two cross-checks** for features that would be named as *kept*: `ibkr/validation.py` already carries the additive
  `risk_reducing` keyword and its docstring already points at `_close_position_by_id` (`P1-T31`, `done`), and
  `MainWindow._symbol_last_prices` is declared (`:669`) and written through the upper-cased key (`:2093`) — so
  `_ref_price_for` has a real source and needs no new architecture.

### 7. Stale `context.read_files` cleared on 13 `done` tasks (validator gate, not a re-scope)

`check_tasks.py` requires every `context.read_files` path to exist. Thirteen **`done`** Phase-1/Phase-2 tasks still
listed the file their own task (or a sibling) **deleted**, so the validator reported
`context read_files path does not exist` for `P1-T01`–`P1-T08`, `P1-T19`, `P1-T20`, `P1-T24`, `P1-T25` and `P1-T26`. This
was not caused by this revision — it is a consequence of the build having landed those deletions — but it blocked the
"must exit 0" gate. Those thirteen stale entries were removed from `context.read_files` only; **no** `status`,
`dependencies`, acceptance criterion or `touches_files` of any of those tasks was touched, and each now produces the
benign "touches_files … not in context read_files (ok if pure-output file)" warning instead of an error. The removal is
recorded here in full so the change is auditable.

### 8. No Plan escalation and no requirements ambiguity

The decomposition needed no undecided choice: the `ref_price` source is `S4` (the D27.5 `_symbol_last_prices` map), the
re-homed gate set/order is `S5`, the guard/validate/pacing ordering is `S5`'s step list, and the dock model is `S6` —
all already in `docs/architecture.md`/`docs/plan.md`. **No `ESC-PLAN-*` entry is open.** No requirements ambiguity was
found; nothing here is flagged for the Requirements Analyst beyond what the graph already notes.

### 9. Graph state and exact verification result

Revision totals: **64 tasks** (was 63: `P1-T27` → `P1-T64` + `P1-T65`), **1020 dependency edges**, **40** tasks
`not_started` (`P1-T64`/`P1-T65` among them) and **24** `done` (`P1-T64`/`P1-T65` initialized to `not_started`;
Task Manager never advances a status). `P1-T65`'s dependents = 38; `P1-T64`'s dependents = `["P1-T65"]`. No dependency
cycles; every edge resolves to an existing id; `P1-T64` is immediately ready (its 20 Phase-1 dependencies are `done`)
and `P1-T65` is ready once `P1-T64` and `P1-T31` (both satisfied except T64) are `done`.

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P1-T01: touches_files 'ui/footprint_item.py' not in context read_files (ok if pure-output file)
WARN: P1-T02: touches_files 'services/footprint_service.py' not in context read_files (ok if pure-output file)
WARN: P1-T03: touches_files 'data/footprint_cache.py' not in context read_files (ok if pure-output file)
WARN: P1-T04: touches_files 'ibkr/tick_history.py' not in context read_files (ok if pure-output file)
WARN: P1-T05: touches_files 'ui/depth_heatmap_item.py' not in context read_files (ok if pure-output file)
WARN: P1-T06: touches_files 'services/depth_heatmap.py' not in context read_files (ok if pure-output file)
WARN: P1-T07: touches_files 'tests/test_d36_footprint.py' not in context read_files (ok if pure-output file)
WARN: P1-T08: touches_files 'tests/test_d37_microstructure.py' not in context read_files (ok if pure-output file)
WARN: P1-T24: touches_files 'tests/test_market_depth.py' not in context read_files (ok if pure-output file)
WARN: P1-T25: touches_files 'tests/test_order_entry_mkt.py' not in context read_files (ok if pure-output file)
WARN: P1-T26: touches_files 'tests/test_order_entry_side.py' not in context read_files (ok if pure-output file)
WARN: P1-T60: touches_files 'tests/test_d41_removal.py' not in context read_files (ok if pure-output file)
WARN: P1-T61: touches_files 'tests/test_d41_portfolio_dock.py' not in context read_files (ok if pure-output file)
WARN: P1-T62: touches_files 'tests/test_d41_retained_order_path.py' not in context read_files (ok if pure-output file)
OK: 64 tasks validated, execution_graph.json written.
(exit 0)
```

`docs/tasks/execution_graph.json` regenerated by the script: **64 nodes / 1020 edges**; `task-graph.json` carries
`"status": "READY_FOR_BUILD"` both at the top level and under `"metadata"`. Task-manager escalation state: **none**
(`ESC-PLAN-*` is not open; nothing flagged to requirements).

---

## D41 revision — `P1-T66` added: test-harness determinism (`fresh_graph` addition, 2026-10-15)

This is a **targeted graph addition, not a re-scope**: one new infrastructure task was inserted because the
harness itself reddened suites wave-wide during the D41 build. Nothing else in the graph was re-scoped.

### 1. The defect (reported independently by five wave workers)

**1a. PRIMARY — one shared test DB across concurrent pytest processes.** `tests/conftest.py:8-13` derived a
single hard-coded path, `tempfile.gettempdir()/tos_charting_test.sqlite3`, and `os.remove()`d it **at import**:

```python
_TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "tos_charting_test.sqlite3")
try:
    os.remove(_TEST_DB_PATH)
except OSError:
    pass
os.environ["DB_PATH"] = _TEST_DB_PATH
```

With up to ~20 concurrent Build Workers, one process deletes the file another is mid-use on, producing
`sqlite3.OperationalError: attempt to write a readonly database` (SQLITE_READONLY_DBMOVED) in the autouse
`_isolate_test_db` teardown — **test bodies pass, the teardown races**. Evidence, verbatim from the
`P1-T35`/`P1-T36`/`P1-T38`/`P1-T41`/`P1-T43` workers:

- *"the raw command's failures are cross-worker shared-temp-DB contention, not assertions"*
- *"concurrent wave workers share the hard-coded temp DB path"*
- *"with a private TMPDIR the run is deterministically 4 passed"*

This is the **pytest-process variant** of the already-recorded ESC-043 gotcha (`docs/memory.md`), and it is a
prior-recorded gotcha too (ESC-024/ESC-025: *"`tests/conftest.py` seeds a single shared on-disk SQLite DB …
so concurrent/interleaved runs contend on it"*). Left unfixed it hands the Code Reviewer **false failures**
across Phases 2–3.

**1b. SECONDARY — dock-clamp timing flake.** `test_T28_T01_volume_hidden_and_watchlist_max_clamp_keeps_price_panel`
(`tests/test_d10_d13_integration.py`) asserts a chart width after an overshoot drag and can observe the
**pre-clamp** value (`assert 88 >= 400`) under load, because `MainWindow._deferred_dock_clamp` applies its
re-clamp through **chained `QTimer.singleShot(0)`** passes that may not have run when the assertion fires.
Evidence that it is pre-existing and load-dependent, **not** a product bug: it failed in `P1-T41`'s **baseline**
run *before* that task's edit, and passes **20/20** with no concurrent load.

### 2. The new task (`P1-T66`)

- **Title:** *Test-harness determinism — per-process pytest DB path and a load-proof D10/D13 overshoot assertion*
- **Files (`touches_files`):** `tests/conftest.py`, `tests/test_d10_d13_integration.py` — no other task's file
  is overlapped (`tests/conftest.py` is touched by nothing else in the graph; the D10/D13 file is also edited by
  `P1-T41`, which now depends on `P1-T66`, so Build serializes them in that order).
- **Size `L`** (two fixes, two files; directive order inside the task: conftest DB isolation **first**, because
  it reddens the most suites, then the timing flake).
- **Directive:** a process-unique `DB_PATH` (PID and/or a per-process temp directory) with no removal of a path
  the process did not create; and a **bounded** drain/settled-wait before the overshoot assertions, with the
  `>= CHART_MIN_WIDTH` assertions **not weakened, narrowed, skipped, xfailed or deleted**.
- **ACs/tests:** 4 ACs / 6 tests, incl. the **concurrency acceptance test** (AC2/`P1-T66-T21`: two simultaneous
  pytest processes of a DB-touching suite, both must exit 0, 3 consecutive pair-runs) and AC4/`P1-T66-T41`, a
  scope-guard check on the task's own write footprint.
- **Requirement anchor:** `AC-D41.5` ("app starts and charts normally; suite green"). `P1-T66` introduces no new
  requirement — it is harness hygiene that makes the D41 evidence trustworthy.

### 3. Dependency edges added (exhaustive — old → new)

The new task is a **dependency of every remaining task that executes pytest**, so nothing re-runs its suite
against the racy conftest (edges are `P1-T66 → <task>`):

```
P1-T66 -> P1-T21, P1-T35, P1-T36, P1-T38, P1-T41,
          P1-T51, P1-T52, P1-T53, P1-T54, P1-T55, P1-T56, P1-T57, P1-T58, P1-T59,
          P1-T60, P1-T61, P1-T62, P1-T63
```

plus the edge that orders the new task itself:

```
P1-T65 -> P1-T66      (the D10/D13 suite constructs MainWindow; it must be verified against the
                       final ui/main_window.py state, i.e. after the P1-T64 -> P1-T65 chain)
```

**19 edges total.** No remaining task was left independent: every one of the 18 executes pytest —
`P1-T21` via its `P1-T21-T21` test (`pytest --collect-only` on the re-pointed dock/order suites, which imports
`tests/conftest.py`), `P1-T35`/`P1-T36`/`P1-T38`/`P1-T41`/`P1-T51`–`P1-T59` by running their own module, and
`P1-T60`–`P1-T63` (the new/extended suites) by running themselves. Because all 18 depend on `P1-T66`, it is
**alone on the wave frontier** — which is also why AC4's `git`-delta footprint check is reliable.

### 4. The timing flake: scoped as **test determinism**, with a conditional plan flag

`P1-T66` fixes determinism **in the test** (bounded drain of the pending `singleShot(0)` passes before the
assertion). `ui/main_window.py` is listed in the task's `context.read_files` as **READ-ONLY** and AC4 forbids
editing it. Rationale: the assertion observes a *pre-clamp* value because the clamp is *deferred*, so waiting for
the deferral is the correct fix; the product's clamp logic is not wrong, and the D41 design must not be touched
by an infrastructure fix.

**Conditional flag (not an escalation).** If the worker finds that determinism genuinely cannot be reached from
the test side, it must **stop and report** rather than edit `ui/main_window.py`. That outcome would make
"is the deferred dock clamp itself under-specified?" an **open plan-level question** for Plan — it would be
raised in the next revision of this file. **No `ESC-PLAN-*` entry is open now**: the decomposition of this task
needs no undecided architectural choice (the harness-fix strategy is a test detail, not an architecture
decision). No requirements ambiguity was found either.

### 5. What was deliberately **not** touched (graph integrity)

- All 46 `done` tasks keep their status; the 18 remaining tasks keep their scope, ACs, tests and `touches_files`
  — they only gained the `P1-T66` dependency.
- **`P1-T65`'s dependents: the original 38 are intact.** `P1-T65` now has **39** dependents only because
  `P1-T65 → P1-T66` was added deliberately (section 3); no pre-existing edge was removed or re-pointed.
- `P1-T64 → P1-T65` intact (the chain still ends at `P1-T65`, the complete `P1-T27` deliverable).
- The **Phase-3 barrier** is intact: `P1-T60`–`P1-T63` still depend on every Phase-2 task (`P1-T21`–`P1-T59`
  incl. `P1-T64`/`P1-T65`), with `P1-T66` added on top.
- `ui/main_window.py` remains one task per phase; this revision adds no consumer of it.

### 6. Gate-only edits to two `done` task context packs (not a re-scope)

`check_tasks.py` requires every `context.read_files` path to exist. Two `done` tasks still listed **the module
their own task deleted**, so the gate errored:

```
ERROR: P1-T22: context read_files path does not exist: ibkr/market_depth.py
ERROR: P1-T23: context read_files path does not exist: ibkr/order_book.py
```

These were the last two of the class the earlier revision cleared 13 of (section 7 of the `P1-T27`-split
revision). Both stale entries were removed from `context.read_files` **only**; no `status`, `dependencies`,
acceptance criterion or `touches_files` of `P1-T22`/`P1-T23` was touched, and each now yields the benign
`touches_files … not in context read_files (ok if pure-output file)` warning instead of an error.
A `metadata.revision` key and a `notes[]` entry were added to record this revision.

### 7. Graph state and exact verification result

Totals after this revision: **65 tasks** (was 64), **1039 dependency edges** (was 1020), **46 `done` /
19 `not_started`** (`P1-T66` initialized to `not_started`; Task Manager never advances a status). No dependency
cycles; every edge resolves to an existing id; every AC has a matching test; `P1-T66` carries a well-formed
context pack. `task-graph.json` carries `"status": "READY_FOR_BUILD"` both at the top level and under
`"metadata"`. Task-manager escalation state: **none** (`ESC-PLAN-*` is not open; nothing flagged to requirements
— the timing-flake plan question above is conditional and not yet triggered).

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P1-T01: touches_files 'ui/footprint_item.py' not in context read_files (ok if pure-output file)
WARN: P1-T02: touches_files 'services/footprint_service.py' not in context read_files (ok if pure-output file)
WARN: P1-T03: touches_files 'data/footprint_cache.py' not in context read_files (ok if pure-output file)
WARN: P1-T04: touches_files 'ibkr/tick_history.py' not in context read_files (ok if pure-output file)
WARN: P1-T05: touches_files 'ui/depth_heatmap_item.py' not in context read_files (ok if pure-output file)
WARN: P1-T06: touches_files 'services/depth_heatmap.py' not in context read_files (ok if pure-output file)
WARN: P1-T07: touches_files 'tests/test_d36_footprint.py' not in context read_files (ok if pure-output file)
WARN: P1-T08: touches_files 'tests/test_d37_microstructure.py' not in context read_files (ok if pure-output file)
WARN: P1-T22: touches_files 'ibkr/market_depth.py' not in context read_files (ok if pure-output file)
WARN: P1-T23: touches_files 'ibkr/order_book.py' not in context read_files (ok if pure-output file)
WARN: P1-T24: touches_files 'tests/test_market_depth.py' not in context read_files (ok if pure-output file)
WARN: P1-T25: touches_files 'tests/test_order_entry_mkt.py' not in context read_files (ok if pure-output file)
WARN: P1-T26: touches_files 'tests/test_order_entry_side.py' not in context read_files (ok if pure-output file)
WARN: P1-T60: touches_files 'tests/test_d41_removal.py' not in context read_files (ok if pure-output file)
WARN: P1-T61: touches_files 'tests/test_d41_portfolio_dock.py' not in context read_files (ok if pure-output file)
WARN: P1-T62: touches_files 'tests/test_d41_retained_order_path.py' not in context read_files (ok if pure-output file)
OK: 65 tasks validated, execution_graph.json written.
(exit 0)
```

`docs/tasks/execution_graph.json` was regenerated by the script: **65 nodes / 1039 edges**.

---

## D41 revision — `P1-T35`/`P1-T36`/`P1-T38`/`P1-T41` already-applied re-dispatch guard (`fresh_graph`, 2026-10-15)

**Trigger.** Four Build Workers **exhausted their 25-step budget after applying their edits but before writing their handoff pair** (`docs/build/results/<id>.json` + `docs/build/logs/<id>.md`): `P1-T35`, `P1-T36`, `P1-T38`, `P1-T41`. The Orchestrator reset those four tasks to `not_started` so they can be re-dispatched. **Their edits are still on disk.** This is a **small DESCRIPTIVE revision** to four existing tasks: no new task, no status change, no dependency change, no acceptance-criterion change, no `test_id` change, no `touches_files` change. `P1-T66` (the test-harness fix, `in_progress`) is **untouched**.

### 1. What was applied (verified on disk this round, `git diff`)

| Task | File | Applied edits (verify, do not redo) |
|---|---|---|
| `P1-T35` | `tests/test_dock_d18_region.py` | docstring → single Portfolio region; `ActiveTraderPanel` import dropped; `findChild(..., "Active Trader")` → `findChild(..., "Portfolio")` + `objectName() == "Portfolio"`; `active_trader`/`right_dock_container` geometry → `right_dock.widget()`; `_on_dom_toggled` flip → retained `summary_label` collapse/restore; two test fns renamed (`T48_T01_sections_equal_width_within_region` → `T48_T01_portfolio_section_fills_region`, `T48_T03_panels_present_and_signals_wired` → `T48_T03_panel_present_and_signals_wired`) |
| `P1-T36` | `tests/test_right_dock_d21.py` | `ActiveTraderPanel` import dropped; every `win.active_trader.*` → `win.portfolio_panel`; title assertions → `windowTitle()/objectName() == "Portfolio"` + `titleBarWidget() is summary_label`; D21.13 strike/collapse → retained `summary_label`; `_on_dom_toggled` → `right_dock.setVisible(...)`; test fns renamed (`T02`/`T03`/`T05`) |
| `P1-T38` | `tests/test_dock_widths_d18.py` | `_RIGHT_PERSISTENCE_HINTS` drops `"active_trader"`; `objectName() == "Portfolio"` + negative pre-D41-title check; equal-width two-section → single section fills region; wide-content probe `active_trader.ladder` → `portfolio_panel.positions_table`; cap/min/chart-minimum assertions kept |
| `P1-T41` | `tests/test_d10_d13_integration.py` | exactly two hunks — module docstring → "the single Portfolio section, D41 / S6"; `_RIGHT_DOCKS = ("Active Trader",)` → `("Portfolio",)`; probe-verified the title-keyed lookup now finds/hides the renamed dock |

### 2. The descriptive change made (and nothing else)

- An **"ALREADY APPLIED BY A PREVIOUS WORKER — VERIFY, DO NOT REDO"** preamble was **prepended** to each of the four tasks' `description`, enumerating that task's applied edits, the step-exhaustion context, and that the **ONLY outstanding deliverable is verification plus the two handoff artifacts** (`docs/build/results/<id>.json`, `docs/build/logs/<id>.md`). Each retains its original description after "Original scope for reference: ".
- `P1-T41`'s preamble additionally states its edit is **correct and probe-verified**, that its earlier `blocked` report was caused **solely** by the shared-temp-DB / deferred-dock-clamp issues now owned by `P1-T66` (which it depends on), and that **after `P1-T66` lands the command should be re-run, not the file re-edited**.
- Each of the four tasks' `context.memory_notes` gained one entry: `tests/conftest.py`'s cross-process shared-temp-DB race is being fixed by `P1-T66`; a mid-run teardown `sqlite3.OperationalError: attempt to write a readonly database` (SQLITE_READONLY_DBMOVED) is **environmental**, not that task's failure.
- `metadata.revision` updated to `2026-10-15c — P1-T35/T36/T38/T41 already-applied re-dispatch guard (descriptions + memory_notes only; no status/dependency/AC/touches_files change), under fresh_graph`.

### 3. Invariants held (mechanically verified this round)

A script reversed the nine insertions and the one `metadata.revision` swap; the reversed text parsed as valid JSON with the same 65-task set, 0 preambles, 0 notes, 3 memory-notes per target, and the old revision restored — proving **the only content changed is the 4 description preambles + 4 memory_notes + `metadata.revision`**. Additionally asserted: every task's `status`, `dependencies`, `acceptance_criteria`, `tests`, `touches_files`, `expected_artifacts`, `inputs`, `outputs`, `title`, `agent`, `task_type`, `size` and every non-`memory_notes` context field are **unchanged**; all `test_id`s unchanged; **`P1-T66` byte-identical** to before; top-level and `metadata` status both `READY_FOR_BUILD`.

### 4. Graph state and exact verification result

**65 tasks**, **1039 dependency edges** (unchanged), **46 `done` / 18 `not_started` / 1 `in_progress`** (`P1-T66`). `P1-T35`/`P1-T36`/`P1-T38`/`P1-T41` remain `not_started` (Task Manager never advances a status) and each still depends on `P1-T65` and `P1-T66`.

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P1-T01: touches_files 'ui/footprint_item.py' not in context read_files (ok if pure-output file)
... (the same 16 benign pure-output warnings as the prior revision: P1-T01..T08, P1-T22..T26, P1-T60..T62) ...
OK: 65 tasks validated, execution_graph.json written.
(exit 0)
```

`docs/tasks/execution_graph.json` regenerated: **65 nodes / 1039 edges** (identical to the prior revision — no edge moved). Task-manager escalation state: **none** (`ESC-PLAN-*` not open; no requirements ambiguity — this revision is purely descriptive).

---

# Task Manager Notes — D42 (Batch 18b), `fresh_graph`

Revision date: 2026-10-15. Source of truth: `docs/plan.md` § *D42 — Batch 18b* (`Status: READY_FOR_TASK_MANAGER`)
and `docs/architecture.md` § *D42 increment* (`S13`–`S21`, `AR-D42-1`–`AR-D42-11`). D41 is built/reviewed/committed
(`b48133d`) and its 65-task graph is history — this graph **replaces** it.

## 1. Id convention

`P<n>-T<m>`, **single phase per graph**, as `check_tasks.py` requires. **D42 uses `P2-T<m>`.**

- D41's delivered graph used `P1-T<m>` (recorded in git at `b48133d`). D42 continues the phase counter as **`P2`**:
  it satisfies the `P<n>-T<m>` requirement, keeps one phase per graph, and **cannot collide** with the D41 `P1-T*` ids.
- The plan's **three internal phases** (Phase 1 WS1 / Phase 2 WS2 / Phase 3 reconciliation) are encoded as
  **dependency edges inside the one `P2` prefix**, not as separate prefixes (the pipeline derives the build phase from
  the id prefix; `pipeline_state.py` treats this repo as a legacy single-scope doc — no `## Phase P<n>` headers — so
  `build_phase` becomes `P2` once this graph lands).
- `P2-T01`–`P2-T06` = plan Phase 1 (WS1); `P2-T07`–`P2-T22` = plan Phase 2 (WS2); `P2-T23` = plan Phase 3.

## 2. Wave sequencing (the review's central finding, encoded as edges)

**The one shared file across Phase 1 and Phase 2 is `ui/chart_panel.py`.**
- Phase 1's **width** path = **`P2-T02`**; Phase 2's `update_last_bar` **`_bars` trim** (the third
  `SESSION_BAR_CAP` site, `RC-D42-1`) = **`P2-T13`**.
- Edge **`P2-T13 → P2-T02`** forces the two into **different waves** (Phase 2's trim after Phase 1's width edit).
  `build_wave.py`'s overlapping-`touches_files` rule would also serialize them, but the edge makes the order
  deterministic and explicit.
- **Phase 2's other files are NOT barriered against Phase 1** (plan `AP-D42-1`): the wave frontier confirms
  `P2-T07`/`P2-T08`/`P2-T10` co-schedule with `P2-T01` in wave 1.

**Phase 2 internal ordering (plan):**
- `floor_bar_budget` (in **`P2-T09`**) lands **before its four consumers**: the two session cap sites (**`P2-T12`**),
  the panel trim (**`P2-T13`**) and `prune`'s `keep` (**`P2-T14`**) — each depends on `P2-T09`.
- The mode-aware **presence predicate** (**`P2-T08`**) and the mode-aware **cache key** (**`P2-T10`→`P2-T11`**) land
  **before the floor span is wired** (**`P2-T14`** depends on `P2-T08`/`P2-T09`/`P2-T11`/`P2-T12`).
- `services/backfill_service.py` is **split** into `P2-T08` (presence predicate) and `P2-T09` (floor span +
  `floor_bar_budget`), sequenced `P2-T09 → P2-T08`, to keep each within the Build Worker step budget (one file, so
  they serialize regardless).
- **Phase 3** (`P2-T23`) is a **full barrier** over every Phase 1 + Phase 2 task (`P2-T01`..`P2-T22`).

Simulated frontier (no-overlap + deps): **W1** T01,T07,T08,T10 · **W2** T02,T03,T09,T11,T17,T20 ·
**W3** T04,T05,T06,T12,T13,T16,T21 · **W4** T14,T18,T19 · **W5** T15,T22 · **W6** T23.

## 3. Corrected suites and KEEP protections

**The five suites that enshrine the old unconditional floor are CORRECTED, not weakened** (plan correction record /
`FI-D42-2` / `AR-D42-2`):
- `tests/test_candle_spacing.py` → **`P2-T03`** (string-presence → regime/geometry on the shared helper; 35% intent kept).
- `tests/test_volume_width.py` → **`P2-T04`** (dense `≈4.0 px` legs → `body == pitch`, `gap >= 0`, `volume == body`).
- `tests/test_chart_dpi.py` → **`P2-T05`** (its dense `body_dev >= 4.0` leg **will fail post-fix**; the `>= F`/`> wick`
  claims move to the non-dense dataset, the dense dataset asserts `body <= pitch`).
- `tests/test_d28_2_sessions.py::test_session_bar_cap` → **`P2-T19`** (flat cap → derived budget; oldest/newest kept).
- `tests/test_d28_4f_panel_bar_cap.py` → **`P2-T18`** (flat cap → derived budget; oldest/newest kept).

**The nine D16 load-path corrections (`RC-D42-2`) are owned by `P2-T15`**, each **intent-preserving with its cause
named**: `test_t39_t02` (floor span), `test_t39_t03` (removed empty-cache branch), `test_t39_t01` (the test's own
planner call passes `min_sessions`), `test_t39_t06`/`test_t39_t07` (floor-aware `keep`), `test_t40_t01` (floor span),
`test_t40_t04` (planner `min_sessions`), `test_t40_t06` (removed branch), `test_t43_t06` (removed branch).

**Extensions:** `tests/test_backfill_service.py` + `tests/test_d27_backfill_granularity.py` → **`P2-T16`**;
`tests/test_db_schema.py` → **`P2-T17`**.

**The four new suites:** `tests/test_d42_candle_width.py` → **`P2-T06`** (measures the repro pitch, **no** hard-coded
`3.83`, **no** `F == 4.0` device-px assertion — `F` is in the ViewBox logical-px unit `px_per_sec` yields);
`tests/test_d42_day_presence.py` → **`P2-T20`**; `tests/test_d42_mode_cache.py` → **`P2-T21`**;
`tests/test_d42_depth_floor.py` → **`P2-T22`**.

**RED→GREEN evidence for BOTH `ext_hours=False` and `ext_hours=True`:** WS2 carries it in `P2-T20` (presence (a)/(b)/(c))
and `P2-T22` (the per-timeframe/per-mode session count), plus `P2-T15` (the load path) and `P2-T21` (mode isolation).
WS1's RED→GREEN is carried by `P2-T06` (pre-fix body 4.0 > the measured ≈3.83 pitch).

**KEEP / non-regression protections:** `tests/test_d28_4e_bar_cache_retention.py` (flat default preserved, `S18`),
`tests/test_d28_4a_render_layers.py` / `tests/test_volume_ceiling.py` / `tests/test_volume_d21.py` /
`tests/test_candlestick_wick.py` (width-formula-free, must stay green), `tests/test_d39_burst_search.py` (the baseline
preload now passes the mode — re-verified), and the `AC-D16.7` / `AC-D16.1`/`AC-D16.3`/`AC-D16.4` guards in `P2-T23`.

## 4. Assumptions / ambiguities (flagged, not resolved)

- **No `ESC-PLAN-*` escalation and no requirements ambiguity.** Every architectural choice D42 needs is already settled
  in `architecture.md` (`S13`–`S21`) and `plan.md`; nothing was invented.
- **Phase 3 artifact (Task-Manager encoding, recorded for the record).** The plan's Phase 3 "adds no production edit
  (reconciliation + docs only)" and its deliverable is "the full-suite green run + the correction-record entries". Since
  Build does not own `requirements.md`/`plan.md`/`architecture.md`, `P2-T23` encodes Phase 3 as a **new non-regression
  guard suite** (`tests/test_d42_nonregression.py`) for `AC-D16.7` and `AC-D16.1`/`AC-D16.3`/`AC-D16.4` under
  mode-aware presence, plus the full offscreen-suite green run. This is a faithful reading of the plan's stated
  coverage, not new scope.
- **`AP-D42-3` (the floor is scoped to chart loads)** and **`AP-D42-4` (legacy cache rows tagged ETH)** are plan-level
  assumptions already ratified by the Validator; the tasks encode them (the floor is requested only by
  `MainWindow.load_chart`; the migration tags legacy rows `ext_hours = 1`).
- **Out of scope (no tasks):** ESC-032, ESC-033, ESC-034, ESC-036, ESC-043, ESC-044, ESC-045, and the **BUILD halves**
  of ESC-041/ESC-037 (D42 supplies their normative target only; the Code Reviewer flips them after re-verification,
  along with ESC-038/ESC-042).

## 5. Graph state and exact verification result

**23 tasks**, **52 dependency edges**, all `status: "not_started"` (Task Manager never advances a status). Top-level
`status` and `metadata.status` both `READY_FOR_BUILD`.

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P2-T06: touches_files 'tests/test_d42_candle_width.py' not in context read_files (ok if pure-output file)
WARN: P2-T20: touches_files 'tests/test_d42_day_presence.py' not in context read_files (ok if pure-output file)
WARN: P2-T21: touches_files 'tests/test_d42_mode_cache.py' not in context read_files (ok if pure-output file)
WARN: P2-T22: touches_files 'tests/test_d42_depth_floor.py' not in context read_files (ok if pure-output file)
WARN: P2-T23: touches_files 'tests/test_d42_nonregression.py' not in context read_files (ok if pure-output file)
OK: 23 tasks validated, execution_graph.json written.
(exit 0)
```

The five warnings are the expected, benign "pure-output file" warnings for the **new** suites (they do not exist yet,
so they cannot be `read_files` — `check_tasks.py` fails on a non-existent `read_files` path and warns on a
`touches_files` path that is not a `read_files` path). `docs/tasks/execution_graph.json` regenerated: **23 nodes /
52 edges**.

---

## D42 `fresh_graph` repair — circular `test_command` (P2-T02) + sibling sweep (2026-10-15)

**Trigger.** The Orchestrator confirmed one defect on the live tree: **`P2-T02`'s declared `context.test_command` was
circular.** Its command named `tests/test_volume_width.py`, which is owned by **`P2-T04`** — and `P2-T04.dependencies`
is `['P2-T01', 'P2-T02']`, i.e. **`P2-T04` DEPENDS ON `P2-T02`**. So T02's command could only go green *after* a task
that depends on it had already run: unsatisfiable at T02's own dispatch point, by construction. The concrete red leg
is exactly the superseded criterion (`assert measured_body * px_per_sec == pytest.approx(4.0)`; obtained
`0.7954125046232603`): D42's revised `AC-D6.4` makes the floor **density-aware**, so at high density `body == pitch`
and the body is deliberately ~0.8 logical px, not 4. `P2-T04` exists precisely to correct that assertion. Same defect
class as D41's `P1-T27` (section 4 of the `P1-T27`-split revision above); same remedy.

**Scope of this run: repair only.** No new task, no status change, no dependency change, no `touches_files` change, no
`title` / `agent` / `task_type` / `size` change, no acceptance criterion or `test_id` added or removed. The graph
carries `"status": "READY_FOR_BUILD"` at the top level and under `metadata`.

### 1. What was true of the work (so the replacement commands reflect reality)

`P2-T02`'s implementation is complete and its three ACs verify independently on the live tree
(`ui/chart_panel.py`, +66/−32, inside its `touches_files`):

- **AC1** — `_clamp_half_width(w)` is **bit-identical** to `capped_body_half_width(median_diff, w, px_per_sec)` for
  w = 97.5, 5.0, 100.0, 0.1;
- **AC2** — in the dense case the rendered body width **equals** the volume width (60.0 == 60.0);
- **AC3** — on a 960-bar dense load `_candle_pitch / px_per_sec == 60.0`, `_candle_half_width == 19.5 == 0.325 × 60`,
  and the volume width is 60.0 — i.e. pitch and width are derived from the **post-`setRange`** range.

Those three **direct probes** are now named as the AC evidence in the task itself, so the Code Reviewer does not read
the deferred downstream red as a defect here.

### 2. `P2-T02` — the repair

- **`context.test_command`** was
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_volume_width.py tests/test_d28_4a_render_layers.py -q`
  and is now
  **`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d28_4a_render_layers.py tests/test_candlestick_wick.py -q`**.
  Both named files exist and are green at T02's dispatch point: `tests/test_d28_4a_render_layers.py` is the D28.4
  render-layer suite that exercises `_candle_half_width`'s cache/reuse (T02's own AC1/AC3 surface) and is touched by
  **no** task; `tests/test_candlestick_wick.py` is untouched by every task and stays green (its dense-view leg asserts
  only the cosmetic-wick source strings plus a non-null picture). `tests/test_volume_width.py` and
  `tests/test_chart_dpi.py` are named nowhere in it.
- **Deferral recorded in the ACs and tests** (documentation only; every existing AC and `test_id` is intact):
  - **AC1** gains the delegation-probe evidence and states that `tests/test_volume_width.py` (owned by `P2-T04`) and
    `tests/test_chart_dpi.py` (owned by `P2-T05`) are **deliberately RED until those tasks land** — they enshrine the
    superseded dense `measured_body * px_per_sec == 4.0` / `body_device_px >= 4.0` criterion — and that a red
    downstream command is **NOT** an implementation defect here.
  - **AC2** gains the dense `body == volume == 60.0` probe evidence + the `P2-T04` deferral.
  - **AC3** gains the 960-bar probe evidence (`_candle_pitch / px_per_sec == 60.0`, `_candle_half_width == 19.5`).
  - `P2-T02-T11` / `P2-T02-T21` / `P2-T02-T31` descriptions and `expected_result`s now name the direct probe and the
    `P2-T04` deferral.
  - `context.read_files`'s `tests/test_volume_width.py` entry is kept (the worker should read the suite its change
    reddens) with its `why` marked **context only — deliberately RED until `P2-T04`, not this task's command**.

### 3. Sibling sweep — method

Every one of the 23 tasks' `context.test_command` was checked programmatically for the two mechanical signatures of
the defect: (a) a named `tests/*.py` **owned by a task that depends on this one**, directly or transitively; (b) a
named `tests/*.py` that does not exist yet and is **created by a downstream task**. Transitive dependents were
computed from the `dependencies` edges; file ownership from `touches_files`. Each mechanical match was then verified
against the live tree (does the named file actually go red because of *this* task's own change?), because the defect is
**unsatisfiability**, not merely shared ownership — a suite that is green at dispatch is not a defect.

**Three offenders were found and repaired** (T02 plus two siblings). Two tasks are **self-created output files** (not
the defect: the task itself creates the file, which is the standard "pure-output file" pattern `check_tasks.py`
already tolerates). Five are **mechanical matches verified green at dispatch** and were deliberately left unchanged.

| Task | Named file(s) | Owner (downstream?) | Verdict | Action |
|---|---|---|---|---|
| `P2-T02` | `tests/test_volume_width.py` | `P2-T04` (depends on T02) | **DEFECT** — T02's cap reddens its `≈4.0` dense leg | **re-pointed** |
| `P2-T13` | `tests/test_d28_4f_panel_bar_cap.py` | `P2-T18` (depends on T13) | **DEFECT** — T13's floor-aware trim reddens `len(panel._bars) == settings.SESSION_BAR_CAP` | **re-pointed** |
| `P2-T14` | `tests/test_history_backfill_loadpath.py`, `tests/test_history_backfill.py`, `tests/test_history_backfill_disconnect.py` | `P2-T15` (depends on T14) | **DEFECT** — T14's `min_sessions` floor reddens nine assertions (e.g. `test_t39_t02`'s `stub.calls == []` with 5 present days < 30) | **re-pointed** |
| `P2-T01` | `tests/test_candle_spacing.py` | `P2-T03` (depends on T01) | mechanical match, **verified GREEN** — the pre-correction suite was a source-string check (`"median_diff * 0.325"`), and that literal survives T01's edit at `ui/candlestick_item.py:153`; `test_candlestick_wick.py`'s `min_w` check also survives (docstring `:57`) | **unchanged** |
| `P2-T08` | `tests/test_backfill_service.py`, `tests/test_d27_backfill_granularity.py` | `P2-T16` (depends on T08) | mechanical match, **verified GREEN** — T16 **extends** both suites (`git diff --numstat` vs `b48133d`: `+69 −0` and `+49 −0`), so no pre-existing assertion was corrected; T08's edits change only the presence predicate behind `min_sessions=0` defaults | **unchanged** |
| `P2-T09` | same two files | `P2-T16` (depends on T09) | mechanical match, **verified GREEN** — same pure-addition evidence; T09's `min_sessions` defaults to 0, so the existing cases keep their exact semantics | **unchanged** |
| `P2-T10` | `tests/test_db_schema.py` | `P2-T17` (depends on T10) | mechanical match, **verified GREEN** — T17 is a pure addition (`+145 −0`); the pre-T10 assertions are table-set membership, `_init_schema` defined once, and the D41 `footprint_cache` drop — none is touched by adding the `ext_hours` column/key | **unchanged** |
| `P2-T12` | `tests/test_d28_2_sessions.py` | `P2-T19` (depends on T12) | mechanical match, **verified GREEN** — `TickerSession._wave_extended_hours` defaults to `False`, and `floor_bar_budget("5 mins", False) == 5000 == SESSION_BAR_CAP` (RTH 23400 s ÷ 300 s × 30 × 1.15 = 2691, floored by the flat cap), so `test_session_bar_cap`'s `len(kept) == settings.SESSION_BAR_CAP` still holds after T12's edit **and** after T19's correction | **unchanged** |
| `P2-T06`, `P2-T22` | `tests/test_d42_candle_width.py`, `tests/test_d42_depth_floor.py` | self (`touches_files`) | not the defect — the file does not exist yet because **this task creates it** (the pure-output-file pattern; `check_tasks.py` warns benignly) | **unchanged** |
| `P2-T23` | (whole suite, `pytest -q`) | — | depends on every Phase-1/2 task, so it runs last and is green by construction | **unchanged** |

### 4. `P2-T13` — the repair

- **`context.test_command`** was
  `... -m pytest tests/test_d28_4f_panel_bar_cap.py tests/test_d28_4a_render_layers.py -q`
  and is now **`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d28_4a_render_layers.py -q`**
  (`tests/test_d28_4a_render_layers.py` is touched by no task and its 50-bar panels never reach the trim's budget, so
  it is green at T13's dispatch; it exercises `update_last_bar`'s tick/regen/cache paths directly).
- **Why T13's old command was unsatisfiable:** `tests/test_d28_4f_panel_bar_cap.py::test_panel_bars_pruned_at_session_cap`
  seeds 100 bars (with `settings.SESSION_BAR_CAP` monkeypatched to 100) and asserts
  `len(panel._bars) == settings.SESSION_BAR_CAP` plus `panel._bars[0].ts == BASE + 5*300`. After T13's floor-aware trim
  the budget is `floor_bar_budget("5 mins", ext_hours)` (≥ 2691), so **no** prune occurs and both assertions fail. The
  file is owned by `P2-T18`, whose whole scope is that correction.
- **Deferral recorded:** AC1 gains the direct-probe evidence (seed >5000 bars, push past `floor_bar_budget`) and the
  explicit statement that `tests/test_d28_4f_panel_bar_cap.py` (owned by `P2-T18`) is deliberately RED until `P2-T18`
  lands; AC2 gains the dispatch-point evidence note; `P2-T13-T11`'s and `P2-T13-T21`'s `expected_result`s carry the
  deferral; the `read_files` `why` for that suite is marked context-only.

### 5. `P2-T14` — the repair

- **`context.test_command`** was the three `tests/test_history_backfill*.py` suites and is now
  **`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d28_2_sessions.py tests/test_d39_burst_search.py -q`**.
  Both are green at T14's dispatch point: they exercise `MainWindow.load_chart` against an **empty** cache, and T14's
  change preserves "one request" there (the removed empty-cache branch also issued one), while the suites stub the
  historical feed; neither file is owned by a task downstream of T14 (`P2-T19` owns the first but does not depend on
  T14, and its correction leaves the file green per §3).
- **Why T14's old command was unsatisfiable:** T14 passes `min_sessions=MIN_INTRADAY_SESSIONS` (30), so
  `tests/test_history_backfill_loadpath.py::test_t39_t02_cache_current_issues_no_request` — 5 seeded present days, all
  trading days — now yields the floor span and therefore a request, failing its `stub.calls == []` assertion. That is
  one of the **nine** D16 load-path assertions enumerated in `P2-T15`'s AC1, all three files of which are owned by
  `P2-T15` (which DEPENDS ON T14).
- **Deferral recorded:** AC1 names the direct probe and states the three suites (owned by `P2-T15`) are deliberately
  RED until `P2-T15` lands; AC2 and AC3 carry the same deferral for the retention and shortfall cases;
  `P2-T14-T11`/`T21`/`T31` `expected_result`s name the downstream correction; the `read_files` `why` for
  `tests/test_history_backfill_loadpath.py` is marked context-only.

### 6. What was deliberately NOT touched

- **`P2-T04` and `P2-T05` keep their own commands** (`tests/test_volume_width.py -q`, `tests/test_chart_dpi.py -q`):
  they own those suites and run at the right time.
- **`P2-T12`'s command is unchanged** despite being a mechanical match (§3) — it is provably green at dispatch and
  stays green after `P2-T19`'s correction; re-pointing it would have dropped the only existing suite that exercises
  the `set_bars`/`_append_bar` cap sites.
- **No `status`, `dependencies`, `touches_files`, `title`, `agent`, `task_type` or `size` value changed on any task**
  (mechanically verified against the pre-repair values: 23/23 tasks identical). No acceptance criterion and no
  `test_id` was added, removed or renumbered; AC and test counts per task are unchanged.
- `metadata.revision` records this repair and one `notes[]` entry describes the defect class, so a later reader can
  audit it.

### 7. Exact verification result

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
/Users/aniket-desai/.pyenv/.../python3: can't open file
  '/Users/aniket-desai/.config/opencode/scripts/check_tasks.py': [Errno 2] No such file or directory
```

**Tooling flag (not a D42 defect): `~/.config/opencode/scripts/check_tasks.py` does not exist on this host** — the
live scripts directory contains only `build_wave.py` and `review_precheck.py`. The validator was therefore run from
its archived identical copy, `~/.config/opencode/Archive/opencode_v6/scripts/check_tasks.py` (same schema checks:
dependency existence, acyclicity, AC↔test, `touches_files`, context-pack well-formedness, the `P<n>-T<m>` phase rule,
and `execution_graph.json` generation):

```
$ python3 ~/.config/opencode/Archive/opencode_v6/scripts/check_tasks.py
WARN: P2-T06: touches_files 'tests/test_d42_candle_width.py' not in context read_files (ok if pure-output file)
WARN: P2-T20: touches_files 'tests/test_d42_day_presence.py' not in context read_files (ok if pure-output file)
WARN: P2-T21: touches_files 'tests/test_d42_mode_cache.py' not in context read_files (ok if pure-output file)
WARN: P2-T22: touches_files 'tests/test_d42_depth_floor.py' not in context read_files (ok if pure-output file)
WARN: P2-T23: touches_files 'tests/test_d42_nonregression.py' not in context read_files (ok if pure-output file)
OK: 23 tasks validated, execution_graph.json written.
(exit 0)
```

`docs/tasks/execution_graph.json` was regenerated by the validator and is **byte-identical** to the pre-repair file
(**23 nodes / 52 edges**) — independent confirmation that no dependency edge changed. The five warnings are the
pre-existing benign "pure-output file" warnings for the new suites. `task-graph.json` carries
`"status": "READY_FOR_BUILD"` both at the top level and under `metadata`. Task-manager escalation state: **none**
(`ESC-PLAN-*` is not open; no requirements ambiguity found — this run needed no architectural decision).

---

## D42 `pack_fix` — `P2-T22` context pack repaired after a worker `pack_deficiency` block (2026-10-15)

**Trigger.** The Build Worker for **`P2-T22`** (`tests/test_d42_depth_floor.py`, the per-timeframe/per-mode
depth-floor + budget guard) returned `status: blocked` with `pack_deficiency`, naming four files the pack
did not list: `tests/test_history_backfill_loadpath.py`, `tests/conftest.py`, `data/bar_cache.py`,
`config/settings.py`. It had read every `read_file` the pack *did* list and still could not write the suite
faithfully. This is a **pack repair, not a re-scope** — the pack was thin, the map was fine.

### 1. Why the pack was thin

`P2-T22` is the **only** new suite in the batch that drives the *real* load path (`MainWindow.load_chart` →
`_finalize_history_wave`) with a stubbed historical feed, so — unlike `P2-T20`/`P2-T21` (pure predicate / cache
tests) — it must copy the existing load-path harness. The pack listed the *implementation* surfaces
(`ui/main_window.py`, `ui/ticker_session.py`, `services/backfill_service.py`) and the two prose docs, but **not
the harness it must model on** (`tests/test_history_backfill_loadpath.py`), **not the fixture/DB plumbing** it
depends on (`tests/conftest.py`), and **not the cache API** it asserts against (`data/bar_cache.py`), nor the
settings constants (`config/settings.py`). It also carried no contract for the symbols it must call
(`floor_bar_budget`, `MIN_INTRADAY_SESSIONS`, `SESSION_BAR_CAP`, the mode-aware cache API, `present_days`) and
no note for the **`P2-T14` cross-suite hazard** (a load now issues many historical requests).

`docs/codebase-map.md` **does not exist** — expected and deliberate for D42 (the new codebase-map convention
postdates this batch's Plan run; it applies from the NEXT batch). The pack therefore could not be built from a
map; it was built from the live tree. **This is not a map defect** (`MAP_CAUSED` does not apply — there is no
map to misdirect) and **not a non-pack issue** (all four named files exist).

### 2. What was added to `P2-T22.context` (only the `context` object changed)

**`read_files` (8 — at the ~8-file budget):**

| path | lines | why |
|---|---|---|
| `tests/test_history_backfill_loadpath.py` | 40-190 | the load-path harness to model on: `PRESENT_DAYS`/`NOW`, `_seed` (complete 04:00-20:00 ET days), `_FakeIbBar`, the **unbounded** `_ReqStub`, `_make_window`, `_load` |
| `tests/conftest.py` | 1-146 | hermetic `DB_PATH` temp setup, the session `qapp` fixture, the autouse `_isolate_test_db` / `_reset_pacing_state` fixtures |
| `services/backfill_service.py` | 117-148, 256-398 | `floor_bar_budget` + `bar_period_seconds`; `find_missing_spans`/`_floor_missing_span` (the `min_sessions` floor span) |
| `ui/main_window.py` | 1560-1670, 1955-1976 | `load_chart` passes mode + `min_sessions`; `_finalize_history_wave` saves/gets/prunes with `ext_hours=mode` and `keep=floor_bar_budget(...)` |
| `ui/ticker_session.py` | 288-326 | `set_bars`/`_append_bar` — two of the three floor-aware cap sites, using `self._wave_extended_hours` |
| `ui/chart_panel.py` | 1143-1185 | `update_last_bar` — the third floor-aware `SESSION_BAR_CAP` site (the `_bars` head-trim) |
| `data/bar_cache.py` | 1-83 | the mode-aware cache API (`save_bars`/`get_bars`/`prune` `ext_hours` keyword) + `RETENTION_BARS` |
| `config/settings.py` | 44-53 | `MIN_INTRADAY_SESSIONS=30` (the floor's tunable) and `SESSION_BAR_CAP=5000` (the lower bound) |

**Dropped (to hold the ~8-file budget):** the two existing prose entries `docs/plan.md` (1081-1165) and
`docs/architecture.md` (4041-4055). Their content is carried verbatim in `context.plan_excerpt` /
`context.architecture_excerpt`, so nothing was lost — the `plan_excerpt` was **extended** to include the WS2
RED→GREEN evidence **(c)/(d)/(e)** verbatim (`docs/plan.md:1226-1235`), which the dropped `docs/plan.md`
`read_files` entry had pointed at.

**`contracts` (13, all `[existing]`, signatures copied verbatim from the tree):** `MIN_INTRADAY_SESSIONS = 30`;
`SESSION_BAR_CAP = 5000`; `floor_bar_budget(timeframe, ext_hours) -> int` (formula, 6.5h RTH / 16h ETH windows,
`1 day` → flat cap); `bar_period_seconds` (the five intraday timeframes `1 min`/`5 mins`/`15 mins`/`1 hour`/
`4 hours`, `1 day` excluded); `find_missing_spans(..., min_sessions=0)`; `present_days(cached_ts, ext_hours)`;
`BarCache.save_bars`/`get_bars`/`prune` + `RETENTION_BARS`; the two `TickerSession` cap sites;
`MainWindow._finalize_history_wave`'s mode-scoped prune/keep; the **unbounded-reqId stub rule**; and the
sibling-suite convention anchors (`tests/test_d42_mode_cache.py` / `tests/test_d42_day_presence.py`).

**`memory_notes` (5):** kept ESC-043 (`DB_PATH` temp rule), the D21 "bar timestamps are period starts" note and
the stale-shebang note; **added** (a) the **`P2-T14` cross-suite hazard** — a load now issues MANY historical
requests, so a stub with a small FIXED reqId iterator raises `StopIteration` and must draw ids from
`itertools.count`; and (b) the harness subtlety that `_seed` writes complete 04:00-20:00 ET days, so a session
is RTH-valid only if it holds a bar inside 09:30-16:00 ET — count mode-valid sessions with
`present_days(cached_ts, ext_hours=<mode>)`, not by calendar day.

### 3. What was NOT changed (pack repair only)

Mechanically asserted before writing the file: `P2-T22`'s `acceptance_criteria`, `tests`, `touches_files`,
`dependencies`, `status` and `size` are **byte-identical** to their pre-repair values. **No other task was
touched** (only `metadata.revision` was bumped, to `2026-10-15e`, recording this repair). `P2-T22` remains
`dependencies: [P2-T12, P2-T14]`, `status: blocked`, `size: M`, `touches_files: [tests/test_d42_depth_floor.py]`.

### 4. Exact verification result

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P2-T06: touches_files 'tests/test_d42_candle_width.py' not in context read_files (ok if pure-output file)
WARN: P2-T20: touches_files 'tests/test_d42_day_presence.py' not in context read_files (ok if pure-output file)
WARN: P2-T21: touches_files 'tests/test_d42_mode_cache.py' not in context read_files (ok if pure-output file)
WARN: P2-T22: touches_files 'tests/test_d42_depth_floor.py' not in context read_files (ok if pure-output file)
WARN: P2-T23: touches_files 'tests/test_d42_nonregression.py' not in context read_files (ok if pure-output file)
OK: 23 tasks validated, execution_graph.json written.
(exit 0)
```

The five warnings are the pre-existing benign "pure-output file" warnings for the new suites (they do not exist
yet). `execution_graph.json` regenerated: **23 nodes / 52 edges** (no edge moved). Task-manager escalation
state: **none**. Classification: **`MAP_OK`** — the pack was thin, not misdirected; no codebase map exists for
this batch by design.

---

## D42 `pack_fix` — `P2-T06` context pack repaired after a worker `pack_deficiency` block (2026-10-15)

**Trigger.** The Build Worker for **`P2-T06`** (`tests/test_d42_candle_width.py`, the ESC-041 density-aware
candle/volume geometry guard) returned `status: blocked` with `pack_deficiency`, naming four files the pack did
not list — `tests/conftest.py`, `tests/test_chart_dpi.py`, `tests/test_candle_spacing.py`,
`tests/test_volume_width.py` — plus the `ChartPanel` **constructor / chart-load range** it needed in order to
render a real panel in the test. It had read every `read_file` the pack *did* list and still could not write the
suite faithfully. This is a **pack repair, not a re-scope** — the pack was thin, the map was fine.

### 1. Why the pack was thin

`P2-T06` is the **only** new suite in the batch that must **render a real `CandlestickItem` at DPR 2 and measure
the body from the recorded `QPicture` bbox**. Unlike the corrected siblings it is meant to match, its pack listed
the *implementation* under test (`ui/candlestick_item.py`, `ui/chart_panel.py`) and three prose docs, but **not**:

- the file that owns the measurement conventions it must follow — `tests/test_chart_dpi.py` (the `body_geometry`
  QPicture-bbox helper, `px_per_sec` from the ViewBox, `dpr`, and the isolated `QT_SCALE_FACTOR=2` `_probe`
  subprocess the DPR-2 repro has to run in);
- the two **corrected** suites whose regime/geometry assertion style and measured-body convention it must match —
  `tests/test_candle_spacing.py` and `tests/test_volume_width.py` (the AC4 volume-equality leg is literally the
  `test_volume_width.py` pattern);
- the fixture/DB plumbing — `tests/conftest.py`;
- the `ChartPanel` constructor + chart-load range (`__init__`, `set_symbol`, `set_extended_hours`,
  `update_chart`) needed to render a panel at all.

It also carried **no contract** for the symbols it must call (`capped_body_half_width`, `set_data(..., pitch=)`,
`_pitch`, `_clamp_half_width`, `_compute_candle_half_width`, `_view_px_per_sec`, `volume_bars.opts['width']`) and
no statement of the **unit rule** (the floor `F` is in ViewBox logical px, not device px).

`docs/codebase-map.md` **does not exist** — expected and deliberate for D42 (the codebase-map convention
postdates this batch's Plan run; the user decided it applies from the NEXT batch). The pack therefore could not
be built from a map; it was built from the live tree. **This is not a map defect** (`MAP_CAUSED` does not apply —
there is no map to misdirect) and **not a non-pack issue** (all four named files exist and were read this round).

### 2. What was added to `P2-T06.context` (only the `context` object changed)

**`read_files` (8 — at the ~8-file budget):**

| path | lines | why |
|---|---|---|
| `tests/test_chart_dpi.py` | 56-98, 139-173, 213-236 | the DPR-2 measurement conventions to copy verbatim: `make_panel`, the `body_geometry` QPicture-bbox helper (`pic.width() - data_span`; `px_per_sec = vb.width()/x_span`; `dpr = panel.devicePixelRatioF()`; `median_diff` from `_raw_data`), the dense/sparse datasets in `main()`, and the isolated `QT_SCALE_FACTOR=2` `_probe` subprocess harness |
| `tests/test_candle_spacing.py` | 1-94 | the corrected regime/geometry assertion style to match: `FLOOR_PX = 4.0` stated in ViewBox logical px, `_body_width` via `capped_body_half_width`, the `pitch > F` / `== F` / `< F` regime tests, the preserved 0.325 / 35 % gap intent |
| `tests/test_volume_width.py` | 1-131 | the corrected measured-body convention + the AC4 volume-width equality: `_measured_body_width` from `boundingRect()`, `_measured_pitch` from `_raw_data`, `_px_per_sec`, `vol_width == pytest.approx(measured_body, rel=0.02)`, dense `body == pitch` / `gap >= 0` |
| `tests/conftest.py` | 1-146 | the hermetic `DB_PATH` temp setup, the session `qapp` fixture, the autouse `_isolate_test_db` / `_reset_pacing_state` fixtures |
| `ui/chart_panel.py` | 249-304, 380, 971-985, 1029-1031, 1112-1141 | the `ChartPanel(tz_offset=0, editable=True)` constructor, `self._ext_hours = True` (:380 — Ext Hours ON is the **default**), `set_symbol`, `set_extended_hours`, `update_chart` (the chart-load entry point) |
| `ui/chart_panel.py` | 1230-1355 | the volume width path: `_view_px_per_sec`, `_compute_candle_half_width` (the `_candle_pitch` cache), `_clamp_half_width`, `_refresh_candles` (`width=w_vol*2`) |
| `ui/candlestick_item.py` | 47-105, 135-214 | the renderer under test: `capped_body_half_width`, `_median_time_diff`, the `_pitch` cache + `set_data(..., pitch=)`, `_draw_candles`'s cap application |
| `docs/requirements/requirements.md` | 1288-1293 | `AC-D6.4` (revised) and its measurable paragraph — the repro, consequences (i)/(ii)/(iii), the supersession |

**Dropped (to hold the ~8-file budget):** the two existing prose entries `docs/plan.md` (1063-1141) and
`docs/architecture.md` (3920-3940). Their content is carried verbatim in `context.plan_excerpt` /
`context.architecture_excerpt`, so nothing was lost — the `plan_excerpt` was **extended** to include the **WS1
RED→GREEN evidence verbatim** (`docs/plan.md:1209-1225`), which the dropped `docs/plan.md` entry had pointed at,
and the `architecture_excerpt` was **extended** with the `S13`/non-functional **unit paragraph**
(`docs/architecture.md:3999-4006`). Same move as the `P2-T22` repair.

**`contracts` (16, all `[existing]`, signatures copied verbatim from the tree):**
`capped_body_half_width(median_diff, base_half_width, px_per_sec, floor_px=4.0)` with its exact body;
`CandlestickItem.set_data(data, mode=None, width=None, pitch=None)` + the `_pitch` / `_raw_data` fields +
`boundingRect()`; the D28.4 static-vs-live render split (measure `candlestick._raw_data`, not the input list);
`ChartPanel.__init__` / `set_symbol` / `update_chart` / `set_extended_hours` (+ the `_ext_hours = True` default);
`_view_px_per_sec` / `_compute_candle_half_width` / `_clamp_half_width` / `volume_bars.opts['width']`; the
**unit rule** (floor `F = 4.0` is in **ViewBox logical px** — the unit `px_per_sec` yields, i.e.
`min_w = 2.0 / px_per_sec` — **not** device px; 4 logical px = 8 device px at DPR 2; never assert `F == 4.0`
device px); the unit-free relations (`body <= pitch`, `body == pitch`, `gap > 0` when `pitch > F`); the repro
figures (192 bars → pitch ≈ 3.83 logical px; 78 bars → ≈ 8.86) marked **indicative, measure don't hard-code**;
and the two corrected sibling suites as the convention anchors.

**`memory_notes` (5):** kept ESC-043 (`DB_PATH` temp rule — sharpened for this task: the DPR-2 probe is a
`python -c` child process and must set `DB_PATH` itself), the stale-shebang note and the test-DB-contention note;
**added** (a) the **D19/D20 masking lesson** — a harness that hides or stubs a widget to make geometry settle
measures a window the app never renders; the guard must measure a **genuinely rendered** panel, and a regression
guard is only credible if it fails pre-fix and passes post-fix; and (b) the D21 note that **bar timestamps are
period starts**.

### 3. What was NOT changed (pack repair only)

Mechanically asserted before writing the file: `P2-T06`'s `acceptance_criteria`, `tests`, `touches_files`,
`dependencies`, `status` and `size` are **byte-identical** to their pre-repair values; every **other** task is
byte-identical (deep JSON comparison of the whole task list minus `P2-T06`); the top-level `notes` and
`metadata.status` are unchanged. Only `metadata.revision` was bumped, to `2026-10-15f`, recording this repair.
`P2-T06` remains `dependencies: [P2-T01, P2-T02]`, `status: blocked`, `size: M`,
`touches_files: [tests/test_d42_candle_width.py]`.

### 4. Exact verification result

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P2-T06: touches_files 'tests/test_d42_candle_width.py' not in context read_files (ok if pure-output file)
WARN: P2-T20: touches_files 'tests/test_d42_day_presence.py' not in context read_files (ok if pure-output file)
WARN: P2-T21: touches_files 'tests/test_d42_mode_cache.py' not in context read_files (ok if pure-output file)
WARN: P2-T22: touches_files 'tests/test_d42_depth_floor.py' not in context read_files (ok if pure-output file)
WARN: P2-T23: touches_files 'tests/test_d42_nonregression.py' not in context read_files (ok if pure-output file)
OK: 23 tasks validated, execution_graph.json written.
(exit 0)
```

The five warnings are the pre-existing benign "pure-output file" warnings for the new suites (they do not exist
yet). `execution_graph.json` regenerated: **23 nodes / 52 edges** (no edge moved). Task-manager escalation
state: **none**. Classification: **`MAP_OK`** — the pack was thin, not misdirected; no codebase map exists for
this batch by design.

---

## D42 `reviewer_escalation` — three BUILD-routed escalations from batch D42 review (2026-10-16)

**Trigger.** The Code Reviewer finished reviewing batch **D42** and left three **BUILD-routed**, `open`
escalations belonging to this batch: **ESC-048** (blocking), **ESC-049** (should-fix), **ESC-051**
(nice-to-have). The seven pre-existing BUILD escalations (**ESC-032/033/034/036/043/044/045**) are a later
stage and were **not** tasked here; **ESC-050** is PLAN-routed and was **not** touched. This run is an
**additive repair**: it appends three tasks and changes no existing task.

### 1. The three tasks added

| id | Escalation | One-line scope |
|---|---|---|
| **`P2-T24`** | **ESC-048** (blocking) | Widen the six D42-broken suites' fixed-size `req_historical_data` stubs to unbounded sources (the 19 `StopIteration` regressions) + prove the full offscreen suite green. |
| **`P2-T25`** | **ESC-049** (should-fix) | Set the session's `_wave_extended_hours` from the load's `extended_hours` **before** the initial `set_bars` (no-wave ETH path capped at the RTH budget), + a no-wave depth-floor guard. |
| **`P2-T26`** | **ESC-051** (nice-to-have) | Restore the exact `assert len(plans) == 1` in `tests/test_history_backfill.py` (`t40_t01`, `:285`). |

### 2. `touches_files` (and the deliberate scope widening)

- **`P2-T24`** — `tests/test_d24_popouts.py`, `tests/test_phase3_fixpass.py`, `tests/test_d24_alarm_full_chain.py`,
  `tests/test_d24_smoke_gate.py`, `tests/test_d24_9_popout_persistence.py`, `tests/test_d28_tick_burst_baseline.py`.
  **These six files lie OUTSIDE `P2-T23`'s footprint** (which is `tests/test_d42_nonregression.py` only) — the
  scope is widened deliberately here, and the six files overlap **no** other task's `touches_files` (verified
  against all 26 tasks).
- **`P2-T25`** — `ui/main_window.py` + `ui/ticker_session.py` + `tests/test_d42_depth_floor.py`. The fix is one line
  (`new_session._wave_extended_hours = extended_hours` in `load_chart`, `ui/main_window.py`); the escalation leaves the
  location open, so the equivalent `set_bars` route (`ui/ticker_session.py`) is declared too rather than risk the worker
  editing a file outside its footprint. The guard extends `P2-T22`'s suite and its harness. `P2-T12`, `P2-T14` and
  `P2-T22` are `done`, so the file overlaps are not races.
- **`P2-T26`** — `tests/test_history_backfill.py` (one assertion, restored).

### 3. How the two required ACs are encoded

- **`P2-T24`'s suite-green AC (`AC3`):** the full offscreen suite exits **0 with zero failures** —
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` — **including**
  `tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green`; with no assertion weakened, skipped or
  deleted. `AC2` additionally requires **each of the six suites green ON ITS OWN**, and `AC1` pins the correction
  (each stub → `itertools.count(<first>)` + `import itertools`, the `lambda *a, **k: next(hids)` form unchanged) —
  the **P2-T19** precedent. Tests `P2-T24-T11`/`T21`/`T31` map 1:1 to `AC1`/`AC2`/`AC3`.
- **`P2-T25`'s guard AC (`AC2`):** a guard that **fails on the no-wave ETH path pre-fix** — seed a cache that
  satisfies the floor, load in **ETH with no wave issued**, and assert the in-memory series length
  `== floor_bar_budget(timeframe, True)` (RED pre-fix: **5,000** = the RTH budget, vs **6,624** = the ETH budget).
  `AC1` covers the fix (mode set before the initial `set_bars`; no stale mode across loads). Tests
  `P2-T25-T11`/`T21` map 1:1.

### 4. Sequencing / dependency shape

- **`P2-T24`** `dependencies: [P2-T14]` — the suites broke because `P2-T14`'s load path always consults the depth
  floor (many historical chunks); the edge expresses "the correction assumes the D42 load path". All deps are `done`.
- **`P2-T25`** `dependencies: [P2-T12, P2-T14, P2-T22]` — it builds on `P2-T12` (`ui/ticker_session.py` mode +
  floor-aware caps), `P2-T14` (`load_chart`), and `P2-T22` (the depth-floor suite whose harness the guard reuses).
  Sequenced **after** the D42 tasks it builds on.
- **`P2-T26`** `dependencies: [P2-T15]` — the relaxation it reverses was made by `P2-T15`.
- `P2-T24` and `P2-T26` are mutually independent and file-disjoint (no shared `touches_files`); `P2-T25` shares
  `tests/test_d42_depth_floor.py` only with the **done** `P2-T22`.

### 5. `P2-T23` reset note (for the Orchestrator — not acted on here)

**`P2-T23` is `blocked`** and its status was **left unchanged** (Task Manager only ever initializes `not_started`;
`build_wave.py` is the sole writer of `status`). `P2-T23`'s `T31` guard runs the whole suite. Once **`P2-T24`**
lands the six stub widenings, that full-suite guard should pass — but **a blocked task is not re-run
automatically**. **Action for the Orchestrator: reset `P2-T23`** (e.g. `build_wave.py packfix` / a status reset to
`not_started`) so its full-suite guard re-runs after `P2-T24` is `done`.

### 6. What was NOT changed

No existing task's `acceptance_criteria`, `tests`, `touches_files`, `dependencies`, `status` or `size` changed
(verified: the 23 original tasks are byte-identical). `P2-T23` stays `blocked`. Only `metadata.revision`, one
`metadata.escalations` sentence, one top-level `notes[]` entry, and three appended tasks were added. Top-level
`status` and `metadata.status` both remain `READY_FOR_BUILD`. Task-manager escalation state: **none** (no
`ESC-PLAN-*` open; no requirements ambiguity — the three fixes are code/test corrections with the production
behaviour already requirements-mandated by `AC-D16.8`).

### 7. Exact verification result

```
$ python3 ~/.config/opencode/scripts/check_tasks.py
WARN: P2-T06: touches_files 'tests/test_d42_candle_width.py' not in context read_files (ok if pure-output file)
WARN: P2-T20: touches_files 'tests/test_d42_day_presence.py' not in context read_files (ok if pure-output file)
WARN: P2-T21: touches_files 'tests/test_d42_mode_cache.py' not in context read_files (ok if pure-output file)
WARN: P2-T22: touches_files 'tests/test_d42_depth_floor.py' not in context read_files (ok if pure-output file)
WARN: P2-T23: touches_files 'tests/test_d42_nonregression.py' not in context read_files (ok if pure-output file)
OK: 26 tasks validated, execution_graph.json written.
(exit 0)
```

The five warnings are the pre-existing benign "pure-output file" warnings for the D42 new suites; the three new
tasks produce **no** warnings. `docs/tasks/execution_graph.json` regenerated: **26 nodes / 57 edges** (52 + the five
new edges: `P2-T14 → P2-T24`; `P2-T12`, `P2-T14`, `P2-T22 → P2-T25`; `P2-T15 → P2-T26`).

## Reviewer-escalation batch — the seven open BUILD escalations (8 new tasks, P2-T27..P2-T34)

Revision date: 2026-10-16. Source: `docs/code_review/escalations.json` (the entries with `"routed_to": "BUILD"` and
`"status": "open"` — ESC-032, ESC-033, ESC-034, ESC-036, ESC-043, ESC-044, ESC-045). All other escalations are
`addressed` and were not touched. Requirements source: the `AC-D26.*` / `AC-D27.*` / `AC-D28.*` / `AC-D14.1` /
`AC-D21.5.*` clauses and the D24–D28 as-built record in `docs/plan.md` / `docs/architecture.md` (the plan's
D42 section lists these seven as explicitly out of scope: "separate work with no task yet").

### Scope added / id convention
Eight new tasks, `P2-T27` … `P2-T34`, all `not_started`. **Ids continue the `P2` sequence** because
`check_tasks.py` enforces **one phase prefix per graph** (`P2-T01`…`P2-T26` are D42's, all `done`); a fresh `P3-`
prefix would fail validation. No id collides. The four stale `task_id`s in the escalation records (`D27-06`,
`D28-02`, `D21-05`, `D27-09`) refer to tasks that no longer exist, so fresh tasks were created rather than
reopened.

| Escalation | Sev | Task | Files |
|---|---|---|---|
| ESC-032 Position `id` | blocking | **P2-T27** | `ibkr/account.py`, `ui/main_window.py`, `tests/test_d27_account_subs.py`, `tests/test_d27_position_id.py` (new) |
| ESC-033 Load Chart button | blocking | **P2-T28** | `ui/main_window.py`, `tests/test_d28_2_load_chart_button.py` (new) |
| ESC-034 watchlist flash timer | should-fix | **P2-T29** | `ui/watchlist_panel.py`, `tests/test_d21_flash_lifetime.py` (new) |
| ESC-036 priming `5 secs` | should-fix | **P2-T30** | `ui/ticker_session.py`, `tests/test_d27_aggregator_priming.py` |
| ESC-043 (core: account-scoped render + junk-row prune) | should-fix | **P2-T31** | `ui/main_window.py`, `tests/test_d27_account_scoping.py` (new) |
| ESC-043 (limb 2: user-space-DB isolation) | should-fix | **P2-T32** | `data/db.py`, `config/paths.py`, `main.py`, `tests/test_db_path_isolation.py` (new) |
| ESC-044 option contract fields | should-fix | **P2-T33** | `ui/main_window.py`, `tests/test_d27_position_prices.py` |
| ESC-045 Account field | should-fix | **P2-T34** | `ui/main_window.py`, `ui/active_portfolio_panel.py`, `tests/test_d27_account_subs.py` |

**ESC-043 is split into two tasks** (the only split; the other six are one task per escalation). The
account-scoping/prune fix (P2-T31) and the DB-path isolation guard (P2-T32) touch disjoint files, and together
they would exceed a Build Worker's ~20-step budget (3 limbs, 4 files, 3+ guards). They are independent, so the
split also widens the first wave instead of lengthening it.

### Sequencing / `touches_files`
`ui/main_window.py` is the hot file — edited by **P2-T28, P2-T27, P2-T33, P2-T31, P2-T34**. The sequencing is
encoded as dependency edges (not prose), in this order:

```
P2-T28 → P2-T27 → P2-T33 → P2-T31 → P2-T34
```

- `P2-T28 → P2-T27`: hot-file sequencing only (the `load_btn` wiring at `:213` vs the position paths at
  `:2925-3027`). No logical dependency.
- `P2-T27 → P2-T33`: **logical** — ESC-044's guard drives the real chain (`_on_position_update` →
  `_upsert_position` → the panel render), which requires ESC-032's populated `id`; both also edit
  `_on_position_update`.
- `P2-T33 → P2-T31`: hot-file sequencing (`_on_position_update` is edited by both) plus the ordering that
  keeps P2-T31's prune guard running against correctly mapped contracts.
- `P2-T27 → P2-T31`: **logical** — `_on_position_end`'s SELECT must carry `id` (ESC-032) before the
  account-scoping rewrite of that same query (ESC-043).
- `P2-T31 → P2-T34`: hot-file sequencing (`_on_account_summary` / the account-id handling region).

First wave (depth 0) is **file-disjoint**: P2-T28 (`ui/main_window.py`), P2-T29 (`ui/watchlist_panel.py`),
P2-T30 (`ui/ticker_session.py`), P2-T32 (`data/db.py`, `config/paths.py`, `main.py`) — 4 tasks, under the
`max_parallel_tasks` default of 6. Waves: 4 → 1 → 1 → 1 → 1 (5 waves, 8 tasks).

`tests/test_d27_account_subs.py` is written by both P2-T27 and P2-T34; the chain already serializes them.
`tests/test_d27_position_prices.py` (P2-T33) and `tests/test_d27_aggregator_priming.py` (P2-T30) are owned by
exactly one task each.

### Regression guards — how each AC is encoded
Every AC carries a guard that is **RED on the pre-fix tree**; none is a "passes either way" guard.

- **P2-T27 (ESC-032):** drives the real signal chain (`bridge.position_update`) and asserts the *rendered*
  result (`positions_table.rowCount() == 1` + populated cells) **and** a non-None `id`, plus an SL/TP-by-id
  persistence assertion (the id must be the real DB row key). The existing
  `test_d27_6_positions_populate_panel` is strengthened, because the escalation records that its
  `_positions`-membership assertion is insufficient (it passes while the render throws).
- **P2-T28 (ESC-033):** the guard calls the **real `load_btn.click()`** (the `clicked(bool)` signal), never
  `load_chart()` directly — the existing suite's direct calls are exactly why this was never caught. A third
  test pins `load_chart`'s D28.2 signature so the fix cannot narrow it.
- **P2-T29 (ESC-034):** flash → `_apply_columns()` → event loop past 400 ms, with a **temporary
  `sys.excepthook` recording unhandled exceptions** (pyqtgraph's hook swallows slot exceptions, so the test
  must not rely on propagation) plus an observable background assertion. AC2 is a **source-shape** criterion
  (no `try/except RuntimeError`, no `shiboken6.isValid`) because no observable distinguishes a lazy reset from
  an exception-swallowing mask — precedent: the D23-01/D23-03 AST source-shape guards.
- **P2-T30 (ESC-036):** parses the issued request's duration for every timeframe (4h/1d must be `3600 S`, not
  `7200 S`), guards the clamp's own side effect (a pre-period bar must not fabricate a previous-period candle),
  and **corrects** `test_d27_9_prime_span_bounded` (it currently asserts `duration == '7200 S'`, i.e. it
  enshrines the bug) rather than weakening it.
- **P2-T31 (ESC-043):** seeds a foreign-account row (`DU123`/`HELD`) + a live-account row, drives
  `account_summary` then `position_end`, and asserts the foreign row is neither rendered **nor left in the
  `positions` table** (the owner's existing junk rows must be addressed by the fix, not hidden), with a no-op
  guard when the live account set is unknown.
- **P2-T32 (ESC-043 limb 2):** a subprocess with `DB_PATH` unset must fail loudly instead of creating/opening
  the user-space DB; separate guards prove the real-app path still works and that pytest (which sets `DB_PATH`)
  is unaffected.
- **P2-T33 (ESC-044):** builds a **real `ibapi.contract.Contract`** (the existing `_held_contract` fake mirrors
  the production code's wrong attribute names, so it cannot fail), asserts option/stock/future mapping, the
  UNSET_DOUBLE → `None` normalisation, and that option legs render `OPTION` and group.
- **P2-T34 (ESC-045):** asserts `'Account: <id>'` renders after an `account_summary` callback (no test covered
  the field), plus the untouched disconnected/unavailable states.

### Flagged items (nothing decided here that belongs upstream)
1. **ESC-036 — the deeper mismatch is a REQUIREMENTS question, flagged for the Requirements Analyst (no
   escalation status; the user relays).** The clamp task (P2-T30) delivers the escalation's first `expected`
   clause — a `(durationStr, barSizeSetting)` combination IBKR accepts. The second clause ("`AC-D27.9` met on
   every timeframe, including 4h/1d") is **not** deliverable by clamping: 5-sec bars cannot cover a 4 h
   (14 400 s) or daily (86 400 s) forming period at all, and `requirements.md`'s D27.9 mandates "trailing
   5-second history". The escalation's own `suggested_direction` calls the choice ("prime with a coarser bar
   size, e.g. `1 min`" vs "seed from the historical partial bar") *a requirements decision*, and no such
   escalation is on file. **Judged not a Plan escalation:** it does not gate the blocking work, and the
   delivered scope is fully specified by the escalation. A requirements decision is needed before 4h/1d can be
   called primed.
2. **ESC-043 — `qty == 0` (flat) live rows: a product call, not decided here.** The escalation records that
   account-scoping removes `HELD`/`H` but **not** the six flat SPXW rows, and that hiding flat rows is "a small
   product call". P2-T31's ACs therefore scope by account only; whether flat live holdings should be hidden is
   left to the owner.
3. **ESC-032 — judged a code fix, not an architecture decision.** The escalation's `expected` is behavioural
   ("one position object on the wire, carrying a POPULATED `id`"), and its concrete direction is additive (give
   `ibkr.account.Position` an `id`, populate it from the DB, add `id` to the bulk SELECT). The ACs assert the
   behaviour and do **not** require converging the two dataclasses into one canonical model — so no architecture
   is invented; the additive path the escalation names is sufficient to satisfy every AC.
4. **ESC-043 limb 2 (P2-T32) — enforcement, not a new decision.** Architecture `S12` and `docs/memory.md`
   already record the rule ("any non-pytest probe that can reach a DB-writing path must export `DB_PATH`");
   P2-T32 moves that rule into code at the shape the escalation prescribes (`DB.__init__` refuses the
   user-space production path unless the real app opts in). Recorded here for Plan/Validator visibility: if the
   enforcement change is judged an architecture change rather than the implementation of a decided rule, this
   task alone is the one to re-scope — it is file-disjoint, so the other seven tasks are unaffected.
5. **ESC-033 — the same latent class was checked, not assumed.** The escalation notes that any
   `clicked(bool)`/`toggled(bool)`/`triggered(bool)` signal wired to a slot whose first positional parameter is
   a value has this defect. No other such wiring exists in the toolbar today; P2-T28's AC3 pins the parameterised
   signature so a future narrowing cannot silently reintroduce it.

### Verification of this revision
- `python3 ~/.config/opencode/scripts/check_tasks.py` → `OK: 34 tasks validated, execution_graph.json written.`
  (warnings are only the expected "new test file not in read_files" ones, the same class as the pre-existing
  P2-T06/P2-T20–P2-T23 warnings).
- Pre-existing tasks: the 26 D42 tasks' `status`, `dependencies` and `touches_files` were snapshotted **before**
  the write and re-read from the file **after** it — **all 26 are byte-identical on those three fields and all
  26 remain `done`**. No existing task's `acceptance_criteria`/`tests` was edited either. Top-level and
  `metadata` `"status"` remain `READY_FOR_BUILD`.
- `docs/plan.md`, `docs/architecture.md`, `docs/requirements/**` and `docs/code_review/**` were read only.

---

## D43 / ESC-036 (second clause) — P2-T30 AC/test revision + new follow-up task P2-T35 (`fresh_graph`)

Revision date: 2026-10-16. Source of truth: `docs/requirements/requirements.md` **`### D43`** (ESC-036 second
clause, decided 2026-10-16, `~:3638`) and the **revised `AC-D27.9`** (`~:3134`), plus A74 / R65 / DG73 / Q53.
Input: the Requirements Analyst's D43 resolution. No architecture assumption was invented and no requirements
ambiguity was found — D43 fully specifies the priming bar-size selection and both duration windows.

### What D43 changes (recorded, not silent)
D27.9's "trailing 5-second history" is **superseded** (the wording is unsatisfiable for the coarse timeframes:
`4 hours` = 14400 s and `1 day` = 86400 s exceed IBKR's `3600 S` ceiling for `5 secs` bars, so the built
`bar_size='5 secs'` / `duration='7200 S'` request returns TWS **error 321**). D43.1 replaces it with a
**per-elapsed-span bar-size selection**:

- **`5 secs`** when the elapsed span is **<= 3600 S** — the **`1 min`/`5 mins`/`15 mins`/`1 hour`** timeframes;
  `duration` = the span clamped into **`[60 S, 3600 S]`**.
- **`1 min`** when the elapsed span **> 3600 S** — the **`4 hours`/`1 day`** timeframes; `duration` = the span
  clamped into **`[60 S, 1 D]`**.

### 1. `P2-T30` revised (fine-timeframe branch only) — status left untouched
`P2-T30` (ESC-036 first clause; `ui/ticker_session.py` + `tests/test_d27_aggregator_priming.py`) is
`in_progress` with a dead worker; its `status` was **not** changed (the orchestrator resets it). Only its
AC/test wording was revised:

- **`AC1`** now asserts the **fine-timeframe branch only**: for `1 min`/`5 mins`/`15 mins`/`1 hour` the priming
  request uses `bar_size='5 secs'` with a `duration` inside `[60 S, 3600 S]`. The **4h/1d assertions were
  removed** (they belong to the follow-up), and the task states that the coarse-timeframe behaviour is
  delivered by `P2-T35`.
- **`P2-T30-T11`** now drives only the four fine timeframes (plus a first-minute case exercising the 60 S floor).
  The pre-fix RED is the **fine-branch floor** (pre-fix `min(span, 7200)` left a first-minute span at a sub-60 s
  duration, which IBKR rejects); the 4h/1d cases are explicitly out of scope here.
- **`AC3` / `P2-T30-T31` revised — this is the "D43 requires otherwise" case.** The invocation said to keep
  `AC3` (correcting `test_d27_9_prime_span_bounded` rather than weakening it) *unless D43 requires otherwise*.
  **D43 does require otherwise**: its Build correction record states `test_d27_9_prime_span_bounded` "must assert
  the accepted **`1 min`/`1 D`**-bounded combination for `1 day`, not the enshrined `5 secs`/`7200 S`" — i.e.
  the **coarse** branch, which `P2-T30` does not implement. So `AC3`/`T31` were **retargeted to the fine
  branch** (the corrected test asserts a fine load's `5 secs` duration is inside `[60 S, 3600 S]`), no 4h/1d
  assertion remains in `P2-T30`, and the `1 day` case's final shape is explicitly assigned to `P2-T35`. This is
  a **translation of D43**, not a re-diagnosis: keeping the old `3600 S`-for-`1 day` assertion would have
  encoded the superseded behaviour that D43 exists to remove.
- **`AC2` / `P2-T30-T21`** (the no-fabrication replay guard for a pre-period priming bar) are **unchanged**, as
  instructed — D43 requires no change to them.
- `P2-T30.description` gained a D43 note; `inputs` gained the D43 and revised-`AC-D27.9` references.

### 2. New task `P2-T35` (coarse-timeframe branch) — `not_started`
- **Title:** "D43/ESC-036 — coarse-timeframe aggregator priming: `4 hours`/`1 day` must prime with
  `bar_size='1 min'` and a duration in `[60 S, 1 D]`".
- **`touches_files`:** `ui/ticker_session.py`, `tests/test_d27_aggregator_priming.py`.
- **`dependencies`: `["P2-T30"]`.** Both tasks write `ui/ticker_session.py::prime_aggregator` **and**
  `tests/test_d27_aggregator_priming.py`, so they must not share a wave. The edge is also **logical**, not just
  file-overlap: `P2-T30` runs **first** because it establishes the accepted-window clamp and retargets
  `test_d27_9_prime_span_bounded` to the fine branch; `P2-T35` then adds the per-span bar-size selection and
  **supersedes** the coarse assertion, re-correcting that test to the `1 min`/`[60 S, 1 D]` shape. Reversing the
  order would leave the test asserting a shape neither task produces.
- **ACs (trace to the revised `AC-D27.9` / D43):**
  - `AC1` (→ `P2-T35-T11`): `4 hours`/`1 day` issue `bar_size='1 min'` with `duration` in `[60 S, 1 D]`; the fine
    timeframes keep `5 secs`/`[60 S, 3600 S]` (`P2-T30`'s branch, unchanged).
  - `AC2` (→ `P2-T35-T21`): the D43 correction record — `test_d27_9_prime_span_bounded` asserts the accepted
    coarse combination for a `1 day` load and the module docstring no longer says "trailing 5-sec history".
  - `AC3` (→ `P2-T35-T31`): the no-fabrication replay guard for the `1 min` bars at a coarse period boundary.
- **RED-before-fix guard:** `P2-T35-T11` asserts each coarse load issues exactly **one `bar_size == '1 min'`**
  priming request with duration in `[60, 86400]` s and **no `5 secs`** priming request. Against the current tree
  (and after `P2-T30`) the coarse loads issue `5 secs`/`3600 S`, so there is **no `1 min` request → RED**;
  `P2-T35-T21` is RED for the same reason (the `1 day` load is not a `1 min` request).

### Verification of this revision
- `python3 ~/.config/opencode/scripts/check_tasks.py` → `OK: 35 tasks validated, execution_graph.json written.`
  (exit 0; the 10 `WARN`s are the pre-existing "new test file not in read_files" class).
- **Status fidelity:** all **34** pre-existing tasks' `status`, `dependencies` and `touches_files` were
  snapshotted **before** the write and re-read from the file **after** it — **zero mismatches**; `P2-T30`
  remains `in_progress` (unchanged), the 26 D42 tasks remain `done`, and `P2-T27`/`P2-T31`/`P2-T33`/`P2-T34`
  keep their prior states. No other task's `acceptance_criteria`/`tests`/`touches_files`/`dependencies`/`status`
  was edited. Top-level and `metadata` `"status"` remain `READY_FOR_BUILD`.
- `docs/requirements/**`, `docs/code_review/**`, `docs/plan.md` and `docs/architecture.md` were **read only**.

---

## ESC-052 + ESC-053 — reviewer-escalation batch (P2-T36, P2-T37)

Revision date: 2026-10-16. Input: `docs/code_review/escalations.json` — the two entries the Code Reviewer
opened on the Stage-C backlog batch (`P2-T27`–`P2-T35`): **ESC-052** (BUILD, should-fix, DATA-LOSS) and
**ESC-053** (routed to REQUIREMENTS). Source of truth for decomposition: the escalation entries themselves
plus the live tree (`ui/main_window.py`, `ui/active_portfolio_panel.py`); `docs/plan.md` remains
`Status: READY_FOR_TASK_MANAGER`. No `ESCALATED_TO_PLAN` entry exists — neither task needs an undecided
architectural choice (ESC-052's fix is a gating change on code P2-T31 already built; ESC-053 is a render
filter with the owner's decision supplied).

### P2-T36 — ESC-052: gate the foreign-row prune on a COMPLETE live-account set
- **Diagnosis (from the escalation, not re-derived):** `ui/main_window.py::_on_position_end` runs
  `DELETE FROM positions WHERE account NOT IN (<live>)` (+ commit) at `:3040` as soon as
  `self._live_accounts` is non-empty, without consulting `_on_account_summary_end` (`:2941`).
  `_live_accounts` is filled one callback at a time in `_on_account_summary`, and `position_end`
  (`reqPositions`) and `accountSummaryEnd` (`reqAccountSummary`) are **independent streams with no ordering
  guarantee**, so a `position_end` arriving on a **partial** live set deletes a real second account's
  persisted rows.
- **Scope of the fix:** keep the `DELETE`-rather-than-hide behaviour exactly as P2-T31 built it; only the
  **gating** changes — mark the live-account set complete in `_on_account_summary_end` and gate the prune on
  that, resetting the completion flag on (re)subscribe (`:1102`) and on disconnect (`:1437`), and ensuring
  the prune still runs once the set is complete regardless of the two streams' arrival order.
- **Task:** `P2-T36`, `task_type: bugfix`, `dependencies: ["P2-T31"]` (P2-T31 is the code this task revises;
  the edge is a logical assumed-contract edge, not a file-overlap shortcut).
  `touches_files`: `ui/main_window.py`, `tests/test_d27_account_scoping.py` (P2-T31's own test file, extended
  with the partial-set and order-independence cases; P2-T31's T11/T21/T31 are kept and unweakened).
- **RED-before-fix guard:** `P2-T36-T11` seeds two REAL live accounts, delivers an `account_summary` callback
  for only one, fires `position_end`, and asserts **both** rows survive. Pre-fix the
  `DELETE ... WHERE account NOT IN ({U13148604})` removes the second account's row → **RED**. This is the
  whole point of the task. `P2-T36-T31` additionally discriminates an *incomplete* fix (gating only
  `_on_position_end` on completeness, without driving the prune from the end marker, leaves the junk row
  unpruned when `position_end` precedes `account_summary_end` → RED).
- **Out of this task's ACs (recorded, not silently dropped):** the escalation also notes that the same
  partial-state window makes `_on_position_update`'s foreign-account early-return drop real updates. ESC-052's
  `expected` scopes the required change to the **destructive prune**, so this task does not re-scope the
  update path; the observation is carried in P2-T36's description for the reviewer.

### ESC-053 — provenance correction (recorded for the reviewer)
**The batch brief's claim that P2-T31 "hides qty == 0 rows (the owner's decision)" was not supported by the
repository, and that discrepancy was an ORCHESTRATOR HANDOFF ERROR — not a Task Manager invention and not a
product call left open.** The owner's answer had been given but was never relayed to Task Manager, so the
decision was recorded as undecided: `docs/tasks/task-graph.json`'s `P2-T31` description carries
*"NOT IN SCOPE (a product call, flagged for the owner, not decided here): whether flat (`qty == 0`) live rows
such as the six SPXW legs should also be hidden"*, and this file repeated it under the ESC-043 entry. The Code
Reviewer correctly flagged the mismatch (ESC-053). **The owner has now answered explicitly and verbatim:
"Hide qty==0 positions".** Consequences recorded here:
1. The decision is **made** — the earlier "NOT IN SCOPE (a product call)" note on `P2-T31` is **superseded**
   (the P2-T31 task record itself is left byte-for-byte unchanged, per the do-not-edit instruction; this note
   is the supersession record).
2. The portfolio panel must **hide zero-quantity positions from the render** — task `P2-T37` below.
3. **Flag for Requirements Analyst:** the decision is **not yet recorded in
   `docs/requirements/requirements.md`** (no `qty == 0` / flat-holding AC exists there). ESC-053 was routed to
   REQUIREMENTS; the analyst should record the decision as a requirement/AC so the panel's expected content is
   defined rather than implicit. This is a record-keeping gap, not a blocking ambiguity — the owner's decision
   is unambiguous, so the task is decomposed now.

### P2-T37 — ESC-053: hide `qty == 0` (flat) positions from the portfolio render
- **Task:** `P2-T37`, `task_type: bugfix`, `dependencies: []`.
  `touches_files`: `ui/active_portfolio_panel.py`, `tests/test_d27_flat_rows.py` (new).
- **Scope decision (documented):** the filter is applied in the **panel render path only**. The flat rows
  **stay in the `positions` table** (they are real broker holdings at flat size — only the render hides them),
  so `ui/main_window.py` is **not** touched and P2-T37's footprint stays disjoint from P2-T36's.
- **RED-before-fix guards:** `P2-T37-T11` (`set_positions([flat, long])` → `rowCount() == 1`, flat symbol
  absent) and `P2-T37-T21` (`add_position(flat)` renders no row) are both **RED** pre-fix, because
  `_render_table` currently renders every entry in `self._positions`. `P2-T37-T41` pins the row/list alignment
  so a render-only filter (which would desync `_on_selection_changed`'s `self._positions[row]`) is caught.

### Sequencing / `touches_files` (no shared file → no dependency edge)
- `P2-T36` writes `ui/main_window.py` + `tests/test_d27_account_scoping.py`; `P2-T37` writes
  `ui/active_portfolio_panel.py` + `tests/test_d27_flat_rows.py`. The two footprints are **disjoint**, and
  neither task assumes a contract the other establishes (P2-T36 changes *when* the DB prune runs; P2-T37
  changes *what the panel renders* — independent of each other), so **no dependency edge is added** and both
  are ready in the **same wave**. The only edge in this batch is `P2-T36 → P2-T31`.
- Every pre-existing task is `done`, so neither new task shares a wave with a live writer of its files.

### Verification of this revision
- `python3 ~/.config/opencode/scripts/check_tasks.py` → `OK: 37 tasks validated, execution_graph.json written.`
  (exit 0; the 11 `WARN`s are the pre-existing "new test file not in read_files" class, incl. the new
  `tests/test_d27_flat_rows.py`).
- **Status fidelity:** all **35** pre-existing tasks' `status`, `dependencies` and `touches_files` were
  snapshotted **before** the write and re-read from the file **after** it — **zero mismatches**; all 35 remain
  `done`. No other task's `acceptance_criteria`/`tests`/`touches_files`/`dependencies`/`status` was edited.
  Top-level and `metadata` `"status"` remain `READY_FOR_BUILD`.
- `docs/requirements/**`, `docs/code_review/**`, `docs/plan.md` and `docs/architecture.md` were **read only**.

---

## 2026-10-16e — `fresh_graph` removal: `P2-T36` (ESC-052) DELETED as redundant

**Trigger:** dispatch collision. `P2-T36` was created to carry the `ESC-052` fix, but `ESC-052` is a **BUILD**
escalation whose `task_id` names `P2-T31` — the task whose code the escalation revises. `build_wave.py` routes a
BUILD escalation to the task its `task_id` names, so it had **already reset `P2-T31` and re-dispatched it as a
rework**, and `P2-T31`'s wave file already carries `ESC-052`'s full diagnosis (`observed` / `expected` /
`suggested_direction`, incl. *"cover a partial-live-set case with a test"*). The same fix was therefore
scheduled **twice**: once as `P2-T31`'s in-flight rework, and once as `P2-T36`.

**Action taken (exactly one task removed):**
- `P2-T36` deleted from `docs/tasks/task-graph.json` (37 → 36 tasks).
- No dependency edge named it: verified programmatically that **no task's `dependencies` contains `P2-T36`**
  (its own sole dependency, `P2-T31`, is unaffected and left in flight).
- Metadata `revision` prepended with a removal note; top-level and `metadata` `"status"` kept `READY_FOR_BUILD`.
- Nothing else changed — `P2-T31` (`in_progress`), `P2-T37` (`in_progress`) and all 34 `done` tasks are
  byte-identical in `status` / `dependencies` / `touches_files` (see status-fidelity check below).

**Genaralisable lesson (record this):** *a `BUILD` escalation's `task_id` determines the script's rework
target.* Creating a **new** task for an escalation that **already names a task** produces a **duplicate** — the
script will independently reset and re-dispatch the named task. When decomposing an escalation, first check
whether it already names a task (`task_id`): if so, **prefer reusing the named task** (let the script's rework
carry it), or at minimum **expect the script's rework and do not add a second task** for the same fix. Only
escalations with **no** named task (or ones explicitly routed to TASK_MANAGER / PLAN / REQUIREMENTS, which the
script does not rework) warrant a new task.

### Verification of this revision
- `python3 ~/.config/opencode/scripts/check_tasks.py` → see result recorded at the end of this run (36 tasks
  validated; `execution_graph.json` regenerated).
- **Status fidelity:** every remaining task's `status` / `dependencies` / `touches_files` was snapshotted
  **before** the write and re-read from the file **after** it — **zero mismatches**; the only difference is the
  absence of `P2-T36`. `P2-T31` and `P2-T37` remain `in_progress`; all 34 others remain `done`.
- `docs/requirements/**`, `docs/code_review/**`, `docs/plan.md` and `docs/architecture.md` were **read only**.

---

## 2026-10-16f — ESC-054 reviewer escalation (`P2-T31` AC2 wording correction + `P2-T38`)

**Trigger:** `docs/code_review/escalations.json#ESC-054` — the **single open** entry and the only one routed to
`TASK_MANAGER` (the other 24 are `addressed`). Input: the escalation entry itself plus a bounded read of the live
tree (`ui/main_window.py` :2941–:3130, `tests/test_d27_account_scoping.py`); `docs/plan.md` remains
`Status: READY_FOR_TASK_MANAGER`. **No `ESCALATED_TO_PLAN` entry** — the fix is a gating change on code `P2-T31`
already shipped (the reviewer names the exact condition), not an undecided architectural choice. No
`ESC-052`-style duplication risk either: `ESC-054` names `P2-T31` but is routed to **TASK_MANAGER**, so
`build_wave.py` does **not** rework it (per the 2026-10-16e lesson, only a **BUILD** escalation's `task_id` drives
the script's rework) — a new task is the correct vehicle for the behavioural half.

### 1. `P2-T31` `AC2` — wording correction (the trap; fixed FIRST)
`AC2`'s second clause read the live-account set as **known** the moment any `account_summary` callback arrived, so
it asserted a **PARTIAL** set prunes. The shipped (correct, `ESC-052`-reworked) behaviour is the opposite: a
partial set **scopes the render only and must never prune** — the prune runs only once `_on_account_summary_end`
sets `_account_summary_complete`. Read literally, the old wording invited a reworker to **revert the safety gate**.

- **Before (verbatim):** `AC2 — ESC-043 (the production positions table holds only real broker positions) —
  Given persisted positions rows whose account is not one of the live accounts, When _on_position_end runs, Then
  those rows are removed … while live-account rows are untouched; and Given the live account set is not yet known
  (no account-summary callback has arrived), Then the prune is a no-op — no row is deleted.`
- **After (verbatim):** `AC2 — ESC-043 / ESC-052 (the production positions table holds only real broker
  positions) — Given persisted positions rows whose account is not one of the live accounts, When
  _on_position_end runs AFTER the account-summary stream has COMPLETED (_on_account_summary_end has set
  _account_summary_complete), Then those rows are removed … while live-account rows are untouched; and Given the
  account-summary stream has NOT COMPLETED — whether no callback has arrived yet OR only a PARTIAL set of accounts
  has, because the live-account set is authoritative ONLY once the stream completes — Then the prune is a no-op:
  no row is deleted, and the partial set scopes the render only (it must never prune).`
- **Wording only.** `P2-T31`'s `AC1`, `AC3`, its three `test_id`s (`P2-T31-T11/T21/T31`), its `tests`,
  `description`, `expected_artifacts`, `touches_files`, `dependencies`, `status` and `size` are **untouched**
  (verified programmatically). This is not a re-scope: the AC now describes what `P2-T31` actually shipped.

### 2. `P2-T38` — ESC-054 behavioural half: a pre-summary real-account update must not be silently dropped
- **Diagnosis (from the escalation, not re-derived):** `ui/main_window.py::_on_position_update`'s foreign-account
  early-return (`:3018`, `if self._live_accounts and account not in self._live_accounts: return`) is gated on the
  set being **non-empty**, not on the stream being **complete**. `_live_accounts` fills one callback at a time
  (`_on_account_summary` :2947), and `position_update`/`position_end` (`reqPositions`) and
  `account_summary`/`accountSummaryEnd` (`reqAccountSummary`) are **independent streams with no ordering
  guarantee**. So in the partial window a REAL second account's update is dropped — not persisted, not rendered —
  and is **unrecoverable for the session**, because `_on_position_end` loads only from the `positions` table
  (reviewer probe: the row is absent before **and** after the summary completes).
- **Scope of the fix:** the reviewer's minimal consistent option — gate the early-return on completion too
  (`self._live_accounts and self._account_summary_complete and account not in self._live_accounts`), so a
  pre-summary update is persisted and rendered (still scoped to the accounts known so far) rather than discarded.
  The **completed-set** gate `ESC-043`/`ESC-052` established stays intact (a foreign update *after* completion is
  still dropped) — pinned by `P2-T38-T31` so this task's reworking of the same early-return cannot revert it.
- **Task:** `P2-T38`, `task_type: bugfix`, `size: M`, `dependencies: ["P2-T31"]`.
  `touches_files`: `ui/main_window.py`, `tests/test_d27_account_partial_window.py` (new).
- **RED-before-fix guard (the evidence, encoded):** `P2-T38-T11` — partial set `{U13148604}` (one
  `account_summary` callback, **no** `accountSummaryEnd`), then
  `bridge.position_update.emit('U99999999', MSFT stock, 10.0, 5.0)` — asserts the `U99999999` row **exists** and
  renders. Pre-fix the early-return drops it (`_live_accounts` non-empty) → row count 0 → **RED**.
  `P2-T38-T21` continues to completion (`account_summary` for `U99999999` + `account_summary_end` + `position_end`)
  and asserts the row **still** exists and renders — pre-fix it was never persisted, so the completed set cannot
  recover it → **RED**. `P2-T38-T31` is a green-both-ways non-regression guard pinning the completed-set gate.

### 3. Sequencing / `touches_files`
- `P2-T38` shares `ui/main_window.py` with `P2-T31` (the account-scoping region). Every other task touching
  `ui/main_window.py` (`P2-T14/T25/T27/T28/T33/T34`) is `done`, so there is no live wave conflict. The shared file
  is encoded as a **dependency edge**: `P2-T38 → P2-T31`, i.e. **`P2-T31` runs first** (it is already `done`, so
  `P2-T38` is immediately ready) — and the edge is *also* logically real: `P2-T38`'s gate **assumes** the
  `_account_summary_complete` flag and `_on_account_summary_end` semantics `P2-T31` shipped. `P2-T38`'s new test
  file does not overlap any other task's `touches_files`.

### 4. Recorded, not silently dropped
- **Not re-scoped:** `ESC-054` also notes that `P2-T31`'s **`AC3`** phrasing ("Given the live account(s) are
  known") carries the same "known" ambiguity, and that `P2-T31`'s **description** still carries the superseded
  "NOT IN SCOPE (a product call …)" flat-row sentence (superseded by `ESC-053`/the owner decision, recorded in the
  2026-10-16d section). This invocation scoped the wording correction to **`AC2` only** (per the dispatch
  instruction, "keep the AC's other clauses intact"), so `AC3` and the description were **left byte-for-byte
  unchanged**; `P2-T38` pins the partial-window invariant that makes `AC3`'s "known" reading moot for the update
  path. If the reviewer wants `AC3`/the description reworded too, that is a further, explicitly-requested wording
  pass.
- **Flag for Requirements Analyst (record-keeping, not blocking):** `docs/requirements/requirements.md` carries
  no AC for the **account-summary partial window** (no "the live-account set is authoritative only once the stream
  completes" clause; `AC-D27.6` is generic). The invariant is now pinned in the task graph and the code, but the
  analyst may wish to record it as an AC. Not a blocking ambiguity — the reviewer's `expected` is unambiguous.

### 5. Verification of this revision
- `python3 ~/.config/opencode/scripts/check_tasks.py` → `OK: 37 tasks validated, execution_graph.json written.`
  (exit 0; the 12 `WARN`s are the pre-existing "new test file not in read_files" class, incl. the new
  `tests/test_d27_account_partial_window.py`). `docs/tasks/execution_graph.json` regenerated (37 nodes).
- **Status fidelity (36 → 37):** all **36** pre-existing tasks' `status`, `dependencies` and `touches_files` were
  snapshotted **before** the write (`/tmp/tm_snapshot_before.json`) and re-read from the file **after** it —
  **zero mismatches**; all 36 remain `done`. No other task's `acceptance_criteria` / `tests` / `description` /
  `touches_files` / `dependencies` / `status` / `size` was edited; the only changes to the file are `P2-T31`'s
  `AC2` string, the appended `P2-T38`, and the metadata `revision` note. Top-level and `metadata` `"status"`
  remain `READY_FOR_BUILD`.
- `docs/requirements/**`, `docs/code_review/**`, `docs/plan.md` and `docs/architecture.md` were **read only**.
