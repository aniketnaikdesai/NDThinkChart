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
