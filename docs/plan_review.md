# Plan Review — NDThinkChart D16 (historical-bar gap backfill) — ESC-023 correction increment

## Review Status
Status: APPROVED

## Validation Summary
This is validation **pass 1 (retry 0 of 3)** for the **D16 ESC-023 correction increment**.
It validates `docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`, revision 2, 2026-10-02
15:24) and `docs/architecture_proposal.md` (revision 2, 2026-10-02 15:24) against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, rewritten 2026-10-02 with
`AC-D16.7` / A33 / R27 / DG22 added).

**Scope.** D16 only, on top of the **as-built D1–D15 baseline** (383 passed, verified
2026-09-28) and the **built D16 batch** (T37–T41, all `done`). D1–D15 are frozen and are
**not** re-planned; nothing in D16 is re-planned except the one active increment. Existing-
repo mode (the marker sentence and Current Tech Stack are present in `requirements.md`).

**What is new in this cycle.** The Plan revision folds in the single corrective increment
the requirements change implies — the **ESC-023 New Year's year-end accounting exception**
(`AC-D16.7`): when Jan 1 is a Saturday, **no New Year's closure is observed and Dec 31 stays
a trading day**, so a genuine bar hole there is backfilled (`AC-D16.1`) or its shortfall
surfaced (`AC-D16.4`), never misclassified as a closure and left silent.

**Independently verified against the live repository** (not proposal prose):
- `services/market_calendar.py` — `_observed()` (`:82–92`) naively shifts a Saturday
  fixed-date holiday to the preceding Friday and is applied to New Year's Day at `:112`
  without any year-end exception; `is_trading_day()` unions adjacent (year−1, year, year+1)
  holiday sets (`:152–154`). So the as-built defect (`is_trading_day(date(2021,12,31)) is
  False`) is real, exactly as ESC-023 states.
- `tests/test_market_calendar.py` — `test_t37_t03_observed_shifts_are_non_trading` asserts
  `is_trading_day(date(2021, 12, 31)) is False` (`:114`) and includes `2021-12-31` in the
  “weekend legal dates” loop (`:116`). Both encode the wrong convention and are correctly
  identified for correction.
- `docs/tasks/task-graph.json` — the `T37-T03` acceptance criterion (`:15`, `:37`, `:40`)
  encodes “New Year's 2022-01-01 Saturday gives 2021-12-31 Friday closed” / `2021-12-31 …
  return False`, i.e. the wrong convention. The correction is required and correctly routed
  to Task Manager.
- The as-built D16 orchestration in `ui/main_window.py` (`_history_req_ids`,
  `_history_generation`, `_backfill_missing_spans`, `_backfill_failed_req_ids`,
  `_finalize_history_wave`, `_on_error` removing a failed id from the set so the wave can
  finalise, `closeEvent` cancelling every id) matches the proposal's `[existing]` claims.
- `ibkr/market_data.py::TIMEFRAME_CONFIG` is unchanged; `Timing`/`bar_size` per timeframe
  match.

**Graphify.** The Plan agent reported `graphify-out/graph.json` is stale for the D16 modules
and fell back to direct source inspection. This Validator **confirmed** the staleness:
`grep` of `graphify-out/graph.json` (1969 nodes) finds **no `market_calendar` and no
`backfill_service` node**. The direct-source fallback is accepted, and the fallback was
stated explicitly in `architecture_proposal.md`, as the existing-repo rule requires.

## Requirements Coverage
| Requirement / journey | Proposal treatment | Verdict |
|---|---|---|
| `AC-D16.7` (New Year's year-end accounting exception; Dec 31 of a Jan-1-Saturday year is a trading day) | Phase 4 (goal + deliverables); architecture Tech Stack calendar row, System Components correction, Non-Functional closures clause, Risk row | Covered |
| A33 (New Year's-specific year-end exception; only actual holidays/weekends are closures) | Phase 4; PA-D16-11; architecture calendar decision | Covered |
| R27 (naive shift misclassifies Dec 31 → silent hole) | Architecture risk row; Phase 4 goal | Covered (risk + mitigation) |
| DG22 (wrong New Year's convention in `_market_calendar`/`T37-T03`/test) | Phase 4 (all three artifacts) | Covered |
| `AC-D16.1` / `AC-D16.4` consequence (hole on such a Dec 31 backfilled/surfaced, never silent) | Phase 4 goal + Non-Functional + risk | Covered |
| `AC-D16.3` carve-out (Dec 31 is not a genuine closure) | Phase 4; architecture Non-Functional | Covered |
| `AC-D16.1`–`AC-D16.6` / Journey 17 / D16 | Phases 1–3 (built) retained for completeness; no re-plan | Covered |
| A27–A32 / R22–R26 / DG19–DG21 | Carried unchanged from the validated D16 pass | Covered |
| D1–D15 | Frozen, re-affirmed; not re-planned | Covered |

## Architecture Findings
- **Complete.** The proposal addresses tech stack, components + responsibilities,
  relationships, data model, integrations, interfaces, security, performance, scalability,
  operational constraints and risks, each with a rationale. The ESC-023 correction is folded
  into the calendar decision, the System Components correction bullet, the Non-Functional
  closures clause, and a dedicated risk row.
- **The corrected rule is coherent with `AC-D16.7`.** When Jan 1 is a Saturday the New
  Year's-specific rule returns **no closure**: the Saturday Jan 1 is non-trading as a
  weekend (the `weekday() >= 5` guard fires first), nothing is shifted onto Dec 31, and Dec
  31 is a Friday that is in no holiday set — so `is_trading_day(2021-12-31 / 2027-12-31 /
  2032-12-31 / 2038-12-31)` becomes `True`. No substitute closure is created.
- **It does not break the other observed-shift rules.** The change is scoped to the Jan 1
  fixed date only; `_observed` for Juneteenth / Independence Day / Christmas is unchanged
  (Independence Day and Christmas never cross a year boundary anyway). New Year's-on-a-
  Sunday (e.g. `2023-01-01` → `2023-01-02`) still observes the following Monday. The
  adjacent-year union in `is_trading_day` is retained as a harmless defensive guard, and the
  proposal explicitly corrects the stale `_holidays_for_year` docstring. No contradiction
  found.
- **No new external surface.** The correction is internal to `services/market_calendar.py`:
  **no new dependency, integration, schema, or IBKR call type**. It is labelled
  `[new/changed]`, and the built D16 components are now labelled `[existing]` with a clear
  increment note.
- **Task-manager-completable.** The design fixes the corrected calendar semantics (New
  Year's-specific rule, Saturday → no closure), the test changes (assert the four Dec 31
  dates trading; drop the wrong loop entry; keep the other shifts as a regression guard),
  and the `T37-T03` AC correction — no architectural decision is left for Task Manager.

## Plan Findings
- **Phases are correctly structured.** Phases 1–3 (built) plus the active **Phase 4 —
  ESC-023 New Year's calendar correction**, each with a goal, covered requirements/journeys,
  and explicit dependencies. Phase 4 depends on Phase 1 (the calendar it corrects).
- **Coarse enough for decomposition.** Phase 4 describes a meaningful, self-contained body
  of work (a calendar-convention correction plus its AC/test update and regression), not an
  individual implementation task; there is no task-level dependency graph and no per-task
  test specification beyond naming the test file/assertions that a verification phase
  naturally names.
- **Ordering is logical.** The corrected `T37-T03` acceptance criterion must be written by
  Task Manager **before** Build edits the module/test, so the module implements the
  corrected criterion rather than the old one — reproduced in Phase 4's dependency note.
- **`touches_files` sequencing is derivable.** Phase 4 touches
  `services/market_calendar.py` and `tests/test_market_calendar.py` (serial per file);
  `ui/main_window.py` remains the D16 batch's single production serialization point. New
  services/tests remain independent.
- **Assumptions are plan-level implementation details** and do not embed a requirements
  decision. **PA-D16-11** (year-end exception is New-Year's-specific, minimal change to the
  built module) is a faithful restatement of the decision Plan made with rationale and
  rejected alternatives.
- **No Task Manager-level task breakdown** is present. Phase 4's reference to the existing
  `T37-T03` acceptance criterion is the requirements-mandated correction record, not a new
  task decomposition.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + `ibapi` terminal; `requirements.md` contains the
literal marker sentence `This is an existing repository.` and the Current Tech Stack. Checks:

- **Codebase Summary present and substantive — PASS.** `architecture_proposal.md` /
  `architecture.md` carry a *Codebase Summary (existing repository — D16 surface)*
  inventorying the bar-load path and its responsibilities, the existing data models
  (`Bar`/`bars`), the IBKR/SQLite/Qt integrations, the relevant test pattern, and the D16
  as-built modules. It is detailed, source-verified, and not a placeholder.
- **Graphify fallback stated — PASS.** The summary explicitly states the graph predates the
  D16 modules (no `market_calendar`/`backfill_service` node) and that D16 was inventoried by
  direct source inspection. Independently confirmed this cycle.
- **Existing stack respected — PASS.** Tech Stack Decisions keep Python 3.11+ / PyQt6 /
  pyqtgraph / `ibapi` / SQLite / pytest-qt as **Unchanged**; the D16 additions are pure
  Python with **no new dependency**; nothing existing is replaced or deprecated.
- **Labels present — PASS.** System Components label every item (`[existing]`,
  `[new/changed]` for the calendar correction, with a clear increment note); Data Model
  labels its entries (`[existing]` / `[new]` / `[new/changed]`); Integration Points label
  every entry (all `[existing]`, plus an explicit internal-correction note).
- **Additive-only — PASS.** The existing `market_calendar` is not redesigned beyond what
  `AC-D16.7` requires (the change is scoped to the New Year's rule); `backfill_service`,
  `main_window`, `bar_cache`, and `chart_panel` are reused unchanged; new/changed work is
  clearly separated from what already exists.
- **Codebase Summary consistent with the proposal — PASS.** Every component the proposal
  treats as `[existing]` (main_window, market_data, client/bridge, bar_cache,
  bar_aggregator, session_service, market_calendar, backfill_service, chart_panel, the
  `bars`/`Bar` model) appears in the Codebase Summary / D16 additions.

## Required Changes
None.

## Requirements Escalations
None open. `AC-D16.7` / A33 / R27 / DG22 are settled and satisfiable as written. The
previously accepted interpretations `FI-D16-1` and `FI-D16-2` (both `addressed`, no
escalation) remain valid and are not reopened. **ESC-023** was escalated to the Requirements
Analyst and is now **resolved in requirements**; Phase 4 implements it. **ESC-024**
(dropped connection mid-wave) is `ESCALATED_TO_BUILD`, not to Plan, and is outside this
validation's scope.

## Task Manager Readiness
**Yes.** The canonical `docs/architecture.md` fixes the corrected calendar semantics (New
Year's-specific rule: Jan 1 Saturday → no closure → Dec 31 trading), the test changes, and
confirms no new dependency/schema/integration; `docs/plan.md` gives the ordered phases with
Phase 4 as the active increment, its goal, covered requirements, and dependencies. Task
Manager can reconcile the affected task(s) — correcting the `T37-T03` acceptance criterion
before Build edits `services/market_calendar.py` and `tests/test_market_calendar.py` — and
produce a valid task graph with per-task `touches_files`, without making a new architectural
decision.

## Final Decision
Status: APPROVED
