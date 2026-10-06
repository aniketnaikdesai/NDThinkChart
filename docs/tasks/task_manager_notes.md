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
