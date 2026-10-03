# Plan Review — NDThinkChart D17 + D18 (panel layout / dock sizing in full screen)

## Review Status
Status: APPROVED

## Validation Summary
This is validation **pass 1 (retry 0 of 3)** for the **D17 + D18 increment**. It validates
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and
`docs/architecture_proposal.md` against `docs/requirements/requirements.md`
(`Status: READY_FOR_PLAN`, revised 2026-10-03 with `AC-D17.1`–`AC-D17.6`,
`AC-D18.1`–`AC-D18.8`, A34–A36, R28–R31, DG23–DG25, B1–B4 answered).

**Scope.** D17 (Watchlist dock resize not effective in full screen) and D18 (Active Trader +
Portfolio right dock not visible in full screen; one right-dock region, 40% cap, equal
widths), on top of the **as-built D1–D16 baseline** (commit `fd0bb0a`, full offscreen suite
green). D1–D16 are frozen and are **not** re-planned. Existing-repo mode (the marker sentence
and Current Tech Stack are present in `requirements.md`).

**Independently verified against the live repository** (not proposal prose):
- `ui/main_window.py` `:205–252` — the central `QWidget`/`QVBoxLayout(toolbar, ChartPanel)`
  is the chart area; the Watchlist dock sets `setMinimumWidth(150)` and is restored with a
  single `resizeDocks`; the two right docks (`QDockWidget("Active Trader")`,
  `QDockWidget("Portfolio")`) are separate `RightDockWidgetArea` docks with **no min/max and
  no `resizeDocks`**. Matches the proposal's `[existing]` claims exactly (B2/DG24).
- `ui/main_window.py` `resizeEvent` (`:959–970`) — calls
  `watchlist_max_width(self.width())` and re-clamps only when already over max; fires on
  **window** resize, and no `splitterMoved`/`dockLocationChanged` handler exists anywhere.
  Confirms the D17 root cause (DG23) and the window-width denominator.
- `ui/watchlist_panel.py` `:29–62` — `watchlist_max_width(window_width)` /
  `clamp_watchlist_width` are parameterised on **window width** and ignore the right docks;
  `CHART_MIN_WIDTH = 400`, `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`.
  Confirms the B1 denominator defect.
- `ui/main_window.py` `_on_dom_toggled` (`:1011–1020`) — resolves the dock by
  `findChild(QDockWidget, "Active Trader")`; a **title-based** lookup the D18 reshape must
  preserve.
- No full-screen handling exists in `ui/` (no `showFullScreen`/`setWindowState`/
  `WindowFullScreen`).
- `tests/test_d10_d13_integration.py:33,50–52`, `tests/test_watchlist_d14_midrag.py:34,80–81`,
  `tests/test_history_backfill.py:192–193`, `tests/test_crosshair_axis_lane.py:101–105` all
  key the right docks on `windowTitle()` `"Active Trader"`/`"Portfolio"`; the crosshair test
  asserts the D2 chip does not intersect **either** dock's `frameGeometry()`. Confirms the
  four-test compatibility surface the proposal flags.
- `tests/test_watchlist.py:24–35` asserts the old window-width clamp math
  (`watchlist_max_width(1400) == 700`) — correctly identified for lockstep update (R28).

**Graphify.** The proposal reports the Codebase Summary was gathered with **graphify**
(`graphify-out/graph.json`, ~2183 nodes, refreshed 2026-10-03) and then validated against the
current source. This Validator confirmed `graphify-out/graph.json` exists and contains the
relevant symbols (`watchlist_max_width`, the D2 dock-nonoverlap test node). Every claim in
the Codebase Summary was independently confirmed against the source above. No staleness
issue for the D17/D18 surface.

## Requirements Coverage
| Requirement / journey / AC | Proposal treatment | Verdict |
|---|---|---|
| D17 — watchlist drag both directions (B4), 50%-of-chart-area cap (B1), min 150 / default ~220 | Phase 2; architecture watchlist-cap row, non-functional | Covered |
| `AC-D17.1` (drag wider to 50% of chart area) | Phase 2; `watchlist_max_width(chart_area_w)`; coverage map | Covered |
| `AC-D17.2` (drag narrower to 150px, both directions) | Phase 2 (two-sided `_apply_dock_widths` on `splitterMoved`/resize) | Covered |
| `AC-D17.3` (cap enforced **during the drag** in full screen) | Phase 2 (`splitterMoved` hook); architecture "where the live clamp is enforced" row; risk row | Covered |
| `AC-D17.4` (persistence re-clamped to the new cap) | Phase 2 (`closeEvent`/restore re-clamp); data-model row | Covered |
| `AC-D17.5` (re-clamp on available-space change; B3) | Phase 2 + Phase 4 (`plan_dock_widths` cross-clamp) | Covered |
| `AC-D17.6` (D13 regression; test lockstep) | Phases 2 and 5 | Covered |
| `AC-D13.1`–`AC-D13.3` (denominator corrected B1) | Phase 1 (re-denominated helpers) | Covered |
| D18 — one right region (B2), 40% cap, equal width | Phase 3 (one region) + Phase 4 (cap/wiring); architecture single-region row | Covered |
| `AC-D18.1` (full-screen visibility) | Phase 4 (`changeEvent(WindowStateChange)` + resize normalize); risk row | Covered |
| `AC-D18.2` (grow to 40% cap; chart narrows) | Phase 4 (`right_dock_max_width` + `_apply_dock_widths`) | Covered |
| `AC-D18.3` (equal width by construction) | Phase 3 (single region, stacked sections) | Covered |
| `AC-D18.4` (reduce direction + stop at cap/min) | Phase 4; `RIGHT_DOCK_MIN_WIDTH` (PA-D17D18-2) | Covered |
| `AC-D18.5` (combined cross-clamp; chart ≥ 400px; B3) | Phase 1 (`plan_dock_widths`) + Phase 4 wiring | Covered |
| `AC-D18.6` (content must not push the dock off-screen) | Phase 4 (bounded panel min/ideal width); risk row | Covered |
| `AC-D18.7` (right region not persisted; A36) | Phase 4; data-model row | Covered |
| `AC-D18.8` (D18 regression; suite green) | Phase 5 | Covered |
| Journeys 18–19 | Phases 2 and 3/4 | Covered |
| A34–A36 (D17/D18 geometry + persistence default) | Phases 1–4; data-model + non-functional | Covered |
| R28 (D13 test lockstep), R29 (chart minimum), R30 (full-screen visibility), R31 (handle moves freely) | Phase 2/4/5; risk rows | Covered |
| DG23–DG25 (drag enforcement, right-dock governance, testability) | Phases 2/3/4; architecture | Covered |
| D1–D16 | Frozen, re-affirmed; not re-planned | Covered |

## Architecture Findings
- **Complete.** The proposal addresses tech stack (unchanged, with the `[new]`/`[new/changed]`
  additions labelled), major components + responsibilities, relationships, data model,
  integrations, interfaces/boundaries, security (live-order path untouched; Q9), performance
  (O(1) apply, recursion guard), scalability/small-display handling, operational constraints
  and risks — each with an explicit rationale in the Tech Stack Decisions table.
- **Internally consistent.** The chart-area denominator, the two cap formulas, and the
  `plan_dock_widths` cross-clamp all agree; the single-region decision (B2) is the stated
  prerequisite for `AC-D18.3`/`AC-D18.1`/`AC-D18.2`; the full-screen normalize (D18) does not
  add a `showFullScreen` call and is coherent with the OS-window-state model.
- **No contradiction with the requirements.** D17's denominator correction (B1) is applied in
  lockstep to D13's criteria, Journey 14, A17 and R15 — consistent with the requirements'
  supersession note; nothing in the architecture weakens or reinterprets a criterion.
- **Rationale present for every meaningful decision.** Notably the rejection of a
  custom-`QDockWidget`-only or `setMaximumWidth`-only approach (which would not enforce the
  cap mid-drag or the chart-minimum cross-clamp), and the choice of a pure, unit-testable
  `plan_dock_widths` over relying on Qt's `resizeDocks` negotiation.
- **Task-manager-completable.** The design fixes where the clamp is enforced
  (`splitterMoved` + `resizeEvent` + full-screen normalize via one `_apply_dock_widths`), how
  the right region is shaped, how width equality is guaranteed, how content is bounded, and
  how the title-based lookups are preserved — no architectural decision is left for Task
  Manager.

## Plan Findings
- **Phases are correctly structured.** Five ordered milestone phases (Phase 1 pure width
  model; Phase 2 D17 live clamp; Phase 3 single right region; Phase 4 D18 cap/cross-clamp/
  full-screen; Phase 5 regression), each with a goal, covered requirements/journeys, explicit
  dependencies, and an exit condition.
- **Coarse enough for decomposition.** Phases describe meaningful bodies of work
  (`Authentication and user accounts`-style), not individual tasks (`create users table`).
  There is no task-level dependency graph and no per-task test specification beyond naming
  the test files a verification phase naturally names.
- **Ordering is logical.** Phase 1 is pure and dependency-free; Phase 2 fixes the left side
  before the right is wired; Phase 3 creates the single region before Phase 4 caps it; Phase
  5 verifies. The serial `main_window.py` chain (Phases 2→3→4) is stated.
- **`touches_files` sequencing is derivable.** The plan's sequencing table identifies the
  serial `ui/main_window.py` chain, the per-file serialisation of the two panel files, and
  which Phase-5 test modules may parallelise — sufficient for Task Manager to populate the
  graph without a new decision.
- **Assumptions are plan-level implementation details** (chart-area = central widget width,
  right-region min ≈ 200px, optional stacked splitter, splitterMoved fallback, no
  `showFullScreen` call, helper signature preservation, right region not persisted, unchanged
  regression policy). None embeds a requirements decision; the requirement-level geometry is
  in A34–A36.
- **No Task Manager-level task breakdown** is present. The "Files touched" and sequencing
  notes are the architecture-level `touches_files` guidance the pipeline contract expects,
  not a decomposition.
- **No scope drift.** D17 corrects D13's denominator (which requirements mandate in lockstep),
  D18 is the new clarified requirement; nothing is added or removed.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + `ibapi` terminal; `requirements.md` contains the
literal marker sentence `This is an existing repository.` and the Current Tech Stack. Checks:

- **Codebase Summary present and substantive — PASS.** The proposal carries a *Codebase
  Summary (existing repository — D17/D18 surface)* that inventories the central + dock setup
  (with line ranges), `resizeEvent`, persistence, `_on_dom_toggled`, the full-screen absence,
  the D13 helpers, both right panels, `ChartPanel`, and the four affected tests, plus the
  existing data models/tables and integrations. It is detailed, source-verified, and not a
  placeholder.
- **Graphify-based, stated, and validated — PASS.** The summary states graphify was used and
  every claim validated against source; the graph exists and the claims independently check
  out.
- **Existing stack respected — PASS.** Tech Stack Decisions keeps Python 3.11+ / PyQt6 /
  pyqtgraph / `ibapi` / SQLite / pytest-qt as **unchanged** (`[existing]`), listed before the
  D17/D18 additions; "Changing the tech stack" is a Non-Goal. Nothing existing is replaced or
  deprecated. No new dependency.
- **Labels present — PASS.** System Components mark every item `[existing]`, `[new]`, or
  `[new/changed]`; Data Model labels its entries; Integration Points label every entry.
- **Additive-only — PASS.** Existing components (`ChartPanel`, D1–D16 modules, the live-order
  path) are untouched; the watchlist helpers are re-parameterised only as B1 requires; the
  right-dock reshape is the requirement's own mandate (B2); new/changed work is clearly
  separated.
- **Codebase Summary consistent with the proposal — PASS.** Every component the proposal
  treats as `[existing]` (`main_window`, `watchlist_panel`, `active_trader_panel`,
  `active_portfolio_panel`, `chart_panel`, `QSettings`, the four tests) appears in the
  Codebase Summary.

## Required Changes
None.

## Requirements Escalations
None open. `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`, A34–A36, R28–R31 and DG23–DG25 are
settled (B1–B4 answered 2026-10-03) and satisfiable as written. No requirement needed
Requirements Analyst intervention this cycle, so no `ESCALATED_TO_REQUIREMENTS` entry was
added to `docs/plan_notes.md`. (The historical `plan_notes.md` entries RG-001/RG-002/RG-003
and FI-D16-1/FI-D16-2 remain resolved/addressed and are not reopened.)

## Task Manager Readiness
**Yes.** The canonical `docs/architecture.md` fixes the shared chart-area width model, the
single right-dock region shape, the cap formulas and the cross-clamp rule, the full-screen
normalize approach, and the title-based lookup preservation; `docs/plan.md` gives five
ordered phases with goals, covered requirements/journeys, dependencies, and the
`touches_files` sequencing. Task Manager can produce a valid task graph with per-task
`touches_files` — reconciling the four title-keyed tests in lockstep and serialising the
`ui/main_window.py` chain — without making a new architectural decision.

## Final Decision
Status: APPROVED
