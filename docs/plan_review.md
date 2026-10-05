# Plan Review — NDThinkChart D19 (toolbar scroll/elide wrapper)

## Review Status
Status: APPROVED

## Validation Summary
This is validation **pass 1 (retry 0 of 3)** for the **D19 increment**. It validates
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and
`docs/architecture_proposal.md` against `docs/requirements/requirements.md`
(`Status: READY_FOR_PLAN`, revised 2026-10-05 with D19 / Journey 20 /
`AC-D19.1`–`AC-D19.7`, A37–A38, R32–R34, DG27–DG28, B5–B6 answered).

**Scope.** D19 — the toolbar's ~1716px `minimumSizeHint` sat inside the central widget and
pinned it, so the already-built D17/D18 dock-width behaviour was not effective in the real
(toolbar-visible) app; the D17/D18 harnesses hid the toolbar, masking the constraint. D19
wraps the existing toolbar in a horizontal `QScrollArea` in place. It is planned on top of the
**as-built D1–D18 baseline** (commit `5bd7c93`, full offscreen suite **566 passed**). D1–D18
are frozen and are **not** re-planned. Existing-repo mode (the marker sentence and Current Tech
Stack are present in `requirements.md`).

**Independently verified against the live repository** (not proposal prose):
- `ui/main_window.py:100–211` — the toolbar `QWidget` is built exactly as the proposal states
  (fixed-width controls; `setFixedHeight(36)`; trailing `addStretch()` then `conn_badge`).
  `ui/main_window.py:213–223` — `central = QWidget(); vbox.addWidget(toolbar);
  vbox.addWidget(self.chart_panel); setCentralWidget(central)`. Confirms the toolbar is a
  direct `QVBoxLayout` child inside the central widget.
- **Offscreen probe (Validator, 2026-10-05)** reproduced the proposal's core numbers:
  `centralWidget().minimumSizeHint().width()` **1716** pre-fix; after simulating the proposed
  wrapper it is **88** (≤ 750 = 400+150+200); wrapper/toolbar height **36**; toolbar remains a
  descendant of `centralWidget()`; with the toolbar visible the watchlist reaches
  `floor(0.50 × chart_area)` (622 at chart_area 1244) instead of pinning at 150; the right
  region stays in-window with width > 0; `centralWidget().width()` shrinks with the window
  (2400→2038, 1800→1438, 1200→838, 900→538) — i.e. `AC-D19.1`–`AC-D19.5` are satisfiable.
- `ui/main_window.py:1027–1168` — `_chart_area_width()` returns `centralWidget().width()`;
  `_apply_dock_widths()` is the single apply entry point delegating to the pure
  `ui/dock_layout.plan_dock_widths`. Matches the proposal's `[existing]` claims.
- The five masking sites are exactly as `DG28` records: `tests/test_dock_widths_d17.py:67–72`,
  `tests/test_dock_widths_d18.py:111–116`, `tests/test_dock_widths_d18_impl.py:67–72`,
  `tests/test_dock_d18_region.py:46–51`, `tests/test_dock_layout.py:315–319`, each hiding the
  widget at `centralWidget().layout().itemAt(0).widget()`.
- `tests/test_d10_d13_integration.py` does **not** hide the toolbar (it hides only the right
  region, `:35`/`:52–54`) and derives `max_w` from the live `centralWidget().width()`. A
  Validator probe applying the D19 wrapper confirmed all its assertions still hold
  (`dock ∈ [150, max]`, `cp.width() >= 400`, `price_plot.width() >= 400`, central `>= 400`,
  including the overshoot drag). **Phase 2's harness changes do not break it.**
- **AC-D19.6 discrimination confirmed:** pre-fix with the toolbar visible, `centralWidget()`
  is pinned at 1716, so the D17 cap assertion (`abs(dock_w - floor(0.50 × chart_area)) <= 1`)
  and the D18 40%-cap assertion (`abs(region_w - floor(0.40 × chart_area)) <= 1`) both fail;
  post-fix they pass. Baseline: the six affected test files currently pass (masked).

**Graphify.** The proposal states the Codebase Summary was gathered with **graphify**
(`graphify-out/graph.json`, 2366 nodes, refreshed 2026-10-05) and validated against source.
This Validator confirmed the graph exists and the relevant symbols resolve; every claim in the
D19 Codebase Summary was independently confirmed against the source above.

## Requirements Coverage
| Requirement / journey / AC | Proposal treatment | Verdict |
|---|---|---|
| D19 — toolbar no longer pins the central widget (in place, one row) | Phase 1; architecture D19 summary + components | Covered |
| `AC-D19.1` — toolbar-visible watchlist reaches `floor(0.50 × chart_area)` (B6) | Phase 2 assertion; Phase 1 enables; probe-confirmed | Covered |
| `AC-D19.2` — right region fully visible with toolbar visible | Phase 2 assertion; Phase 1 enables; probe-confirmed | Covered |
| `AC-D19.3` — chart minimum preserved (`>= 400`) | Phase 2 assertion; `_apply_dock_widths` unchanged | Covered |
| `AC-D19.4` — toolbar no longer pins; single `<= ~40px` row; controls reachable (B5) | Phase 1 implementation; Phase 2 assertions; exit condition | Covered |
| `AC-D19.5` — central widget can shrink | Phase 1 implementation; Phase 2 assertion; probe-confirmed | Covered |
| `AC-D19.6` — test-masking regression guard (≥1 D17 and ≥1 D18 red pre-fix, green post-fix) | Phase 2 (masking removal + pre-fix evidence); discrimination confirmed | Covered |
| `AC-D19.7` — regression; D13/D17/D18 hold in a toolbar-visible window | Phase 3 | Covered |
| Journey 20 — resize the watchlist in the real (toolbar-visible) app | Phases 1–3 | Covered |
| A37/A38 (diagnosis; D19 covers both symptoms; B6 cap unchanged) | Phase 1; architecture | Covered |
| R32 (height/reachability), R33 (intentional intermediate red), R34 (offscreen vs real min hint) | Phases 1–3; risks | Covered |
| DG27/DG28 (toolbar pinning; test masking) | Phases 1/2; architecture | Covered |
| D1–D18 | Frozen, re-affirmed; not re-planned | Covered |

## Architecture Findings
- **Complete.** The proposal addresses tech stack (unchanged, with `[new]`/`[new/changed]`
  additions labelled), the component and its responsibility, relationships, data model,
  integrations, interfaces/boundaries, security (live-order path untouched; Q9), performance
  (O(1) layout change), high-DPI, operational constraints and risks — each with an explicit
  rationale in the Tech Stack Decisions table.
- **Internally consistent.** The wrapper mechanism, the fixed 36px row, the in-place insertion,
  the untouched width model (B6), and the `objectName` strategy all agree. No section makes an
  incompatible technology or design choice.
- **No contradiction with the requirements.** D19 only lowers the central widget's minimum;
  the watchlist cap, `ui/dock_layout.py`, `_apply_dock_widths`, and D1–D18 behaviour are
  untouched. Nothing weakens or reinterprets an `AC-D19.*` criterion.
- **Rationale present for every meaningful decision.** Notably the adoption of `QScrollArea`
  over wrap-to-multiple-rows / overflow-menu / `addToolBar` (all excluded by B5), the fixed
  36px height with an overlay scrollbar, and keeping `conn_badge` inside the scroll region.
- **Task-manager-completable.** The design fixes the wrapper class and policies, its insertion
  point, the objectNames, the fixed height, and the test-masking removal — no architectural
  decision is left for Task Manager.

## Plan Findings
- **Phases are correctly structured.** Three ordered milestone phases (Phase 1 wrapper in
  place; Phase 2 masking removal + toolbar-visible guard; Phase 3 regression + real-app check),
  each with a goal, covered requirements/journeys, explicit dependencies, and an exit condition.
- **Coarse enough for decomposition.** Phases describe meaningful bodies of work, not
  individual tasks. There is no task-level dependency graph and no per-task test specification
  beyond naming the test files a verification phase naturally names.
- **Ordering is logical.** Phase 1 is a single self-contained production change; Phase 2 makes
  the tests exercise the real (toolbar-visible) window and captures the pre-fix red against the
  pre-Phase-1 tree; Phase 3 verifies. The one ordering constraint (Phase 2 pass-after depends
  on Phase 1) is stated.
- **`touches_files` sequencing is derivable.** Phase 1 touches only `ui/main_window.py`; Phase 2
  touches five disjoint test files (plus an optional new file) that may parallelise; Phase 3
  adds no file. Sufficient for Task Manager to populate the graph without a new decision.
- **Assumptions are plan-level implementation details** (wrapper mechanism, objectNames,
  one-row/overlay height, `conn_badge` placement, width model untouched, pre-fix evidence
  method, manual real-app check, unchanged regression policy). None embeds a requirements
  decision; the requirement-level decisions are in B5/B6 and A37/A38.
- **No Task Manager-level task breakdown** is present. The "Files touched" and sequencing notes
  are the architecture-level `touches_files` guidance the pipeline contract expects.
- **No scope drift.** D19 is the new clarified defect; D1–D18 are frozen. Nothing is added or
  removed.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + `ibapi` terminal; `requirements.md` contains the
literal marker sentence `This is an existing repository.` and the Current Tech Stack. Checks:

- **Codebase Summary present and substantive — PASS.** The proposal carries a *Codebase
  Summary (existing repository — D19 surface)* that inventories the toolbar construction, the
  central-widget composition, the D17/D18 width model (`_chart_area_width`,
  `_apply_dock_widths`, `ui/dock_layout.py`, the single right region, the watchlist dock), the
  five affected harnesses (with line ranges), the existing data models/tables and integrations,
  and the key structural fact. It is detailed, source-verified, and not a placeholder.
- **Graphify-based, stated, and validated — PASS.** The summary states graphify was used and
  every claim validated against source; the graph exists and the claims independently check out.
- **Existing stack respected — PASS.** Tech Stack Decisions keeps Python 3.11+ / PyQt6 /
  pyqtgraph / `ibapi` / SQLite / pytest-qt as **unchanged** (`[existing]`), listed before the
  D19 additions; "Changing the tech stack" is a Non-Goal. Nothing existing is replaced or
  deprecated. No new dependency.
- **Labels present — PASS.** System Components mark every item `[existing]`, `[new]`, or
  `[new/changed]`; Data Model labels its entries; Integration Points label every entry.
- **Additive-only — PASS.** Existing components (`ui/dock_layout.py`, `_apply_dock_widths`,
  the width model, D1–D18 modules, the live-order path) are untouched; the only production
  change wraps the existing toolbar in place. New/changed work is clearly separated.
- **Codebase Summary consistent with the proposal — PASS.** Every component the proposal treats
  as `[existing]` (`main_window`, the toolbar, `dock_layout`, the docks, the five harnesses,
  `QSettings`) appears in the Codebase Summary.

## Required Changes
None.

## Requirements Escalations
None. D19 / Journey 20 / `AC-D19.1`–`AC-D19.7`, A37–A38, R32–R34 and DG27–DG28 are settled
(B5–B6 answered 2026-10-05) and satisfiable as written. No requirement needed Requirements
Analyst intervention this cycle, so no `ESCALATED_TO_REQUIREMENTS` entry was added to
`docs/plan_notes.md`. (The historical `plan_notes.md` entries RG-001/RG-002/RG-003 and
FI-D16-1/FI-D16-2 remain resolved/addressed and are not reopened.)

## Task Manager Readiness
**Yes.** The canonical `docs/architecture.md` fixes the wrapper mechanism (`QScrollArea` with
no frame, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical
`ScrollBarAlwaysOff`, fixed 36px row), its in-place insertion, the `objectName` strategy, and
the untouched width model; `docs/plan.md` gives three ordered phases with goals, covered
requirements/journeys, dependencies, exit conditions, and the `touches_files` sequencing.
Task Manager can produce a valid task graph (Phase 1 `ui/main_window.py`; Phase 2 the five
disjoint test files plus the optional new file; Phase 3 verification) without making a new
architectural decision.

**Residual implementation risk (recorded, not a blocker).** The plan's height design relies on
the horizontal scrollbar being overlay/transient. The Validator probe showed that the offscreen
platform reserves an ~18px scrollbar lane at wrapper height 36, so offscreen the toolbar row is
vertically clipped even though the laid-out height stays 36px (≤ 40px) and horizontal scrolling
works (range > 0) — i.e. `AC-D19.4`'s measurable clauses hold. On the real macOS target, overlay
scrollbars are the default, and R34 already requires a manual dev-build check. This is captured
in the D19 architecture risk table; it is an acknowledged platform risk with a stated
mitigation, not a missing architectural decision.

## Final Decision
Status: APPROVED
