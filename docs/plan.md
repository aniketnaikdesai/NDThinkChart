# Implementation Plan — NDThinkChart Stabilization (Batch 11: D17 + D18 panel-layout / dock sizing in full screen)

Scope: the current stabilization batch is **D17 + D18** — panel-layout / resizing defects
reported 2026-10-03. It is planned on top of the **as-built, frozen D1–D16 baseline**
(commit `fd0bb0a`; full offscreen suite green). D1–D16 are **not** re-planned. This is an
existing-repo run: items are labelled `[existing]`, `[new]`, or `[new/changed]`; the
existing tech stack (PyQt6 + pyqtgraph + `ibapi`) is a hard constraint and nothing existing
is replaced. No new product features, no schema change, no new dependency, no new external
integration, and no live-order-path change.

> Companion architecture: `docs/architecture.md` (Codebase Summary, D17/D18 tech-stack rows,
> and D17/D18 components/data-model/integration/non-functional/risk sections).
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D17/D18 /
> Journeys 18–19 / `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`; A34–A36; R28–R31; B1–B4
> answered 2026-10-03; DG23–DG25).

## Completed baseline — D1–D16 (as-built, frozen)
D1–D15 (session shading, crosshair chip in the Y-axis lane, zoom controls/magnifier,
zoom label/position, linear volume axis with the pinned scaling nice-max + live ceiling,
price-coloured volume, volume/price width alignment, volume show/hide, inner-right drawing
labels, zone and horizontal-line double-click dialogs, resizable/persistent watchlist with
double-click load, and the `RouterMode` gesture state machine incl. the ESC-002/003/006/007
revision and the ESC-013…ESC-021 rework) plus **D16** (historical-bar cache-gap backfill,
including the ESC-023 New Year's year-end calendar correction) are **built and verified**;
the full offscreen suite is green. They remain frozen and are not modified by D17/D18. See
`docs/architecture.md` for the as-built description.

## Phases

Each phase is a milestone, coarser than Task Manager's per-task decomposition. Files
touched are listed so Task Manager can populate `touches_files` and Build can schedule waves
without file overlap.

### Phase 1 — Shared width model and re-denominated D13 helpers (pure, no UI behaviour yet) `[new]`

- **Goal:** introduce the single source of truth for dock widths and the chart-minimum rule,
  measured against the **chart area** (B1/B3), before any live wiring.
- **Deliverables:**
  - `ui/dock_layout.py` (**new**) — constants (`CHART_MIN_WIDTH = 400`,
    `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`, `RIGHT_DOCK_MIN_WIDTH`,
    cap fractions `0.50`/`0.40`), `watchlist_max_width(chart_area_w)`,
    `right_dock_max_width(chart_area_w)`, and `plan_dock_widths(chart_area_w,
    requested_left, requested_right) -> (left, right)` guaranteeing `chart_area ≥ 400px`.
  - `ui/watchlist_panel.py` (**`[new/changed]`**) — re-parameterise
    `watchlist_max_width` / `clamp_watchlist_width` / `load_` / `save_` to the chart-area
    denominator, delegating to `ui/dock_layout` (one-argument signature shape preserved).
  - `tests/test_watchlist.py` — update the clamp-math assertions to the chart-area cap in
    lockstep (R28).
- **Requirements / journeys covered:** numerical foundations of D13 (corrected
  denominator), D17 and D18; enables `AC-D13.1`–`AC-D13.3`, `AC-D17.1`–`AC-D17.5`,
  `AC-D18.2`, `AC-D18.5`.
- **Dependencies on earlier phases:** none (pure functions; safe first wave).
- **Exit condition:** pure-function unit tests pass for the edge cases (tiny window, cap <
  min, both docks near max, one side over budget); pre-existing tests that do not depend on
  the denominator stay green.

### Phase 2 — D17: live watchlist clamp + chart-minimum hook `[new/changed]`

- **Goal:** enforce the watchlist cap **during the drag** and on window resize, in both
  directions, against the corrected chart-area denominator, and re-clamp the persisted width
  on restore.
- **Deliverables (`ui/main_window.py`):** add `_apply_dock_widths`, the
  `splitterMoved`/dock-change hook, a two-directional `resizeEvent` re-clamp, and the
  persistence re-clamp on restore/`closeEvent`; **no right-region changes yet**. (`ui/dock_layout.py`
  only if Phase 1 surfaced a needed helper.)
- **Requirements / journeys covered:** D17 (`AC-D17.1`–`AC-D17.5`), Journey 18; keeps D13
  semantics (min 150px, default ~220px, Q26 persistence).
- **Dependencies on earlier phases:** Phase 1 (the width model and corrected denominator).
- **Exit condition:** the watchlist handle moves freely between 150px and the cap; the cap
  stops the drag **without any window resize** (`AC-D17.3`); width restored clamped to the
  current cap; no recursion/jitter; `AC-D17.1`–`AC-D17.4` pass in an offscreen `MainWindow`;
  `tests/test_watchlist.py` and `tests/test_d10_d13_integration.py` updated to the new
  denominator and green.

### Phase 3 — D18: single right-dock region (Active Trader + Portfolio stacked) `[new/changed]`

- **Goal:** re-shape the two right `QDockWidget`s into **one** right-dock region whose
  stacked sections are inherently equal width (B2), without changing ladder/portfolio
  behaviour or signals.
- **Deliverables:**
  - `ui/main_window.py` — replace `:234–252` two-dock setup with one region; keep the
    title/`objectName` resolvable by `_on_dom_toggled` and the four tests.
  - `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py` — container-friendly layout
    only; **no width bound or cap yet** (that is Phase 4).
- **Requirements / journeys covered:** D18 `AC-D18.3`, and the container prerequisite for
  `AC-D18.1`–`AC-D18.2`; Journey 19.
- **Dependencies on earlier phases:** Phase 1 (constants/model), Phase 2 (so only one region
  is wired to the shared clamp and the left side is already correct).
- **Exit condition:** `AC-D18.3` passes (section widths equal within 1px); the pre-existing
  tests that hide/seek `"Active Trader"`/`"Portfolio"` are updated in lockstep and green;
  ladder/portfolio signal wiring untouched.

### Phase 4 — D18: 40% cap, cross-clamp, content bound, and full-screen visibility `[new/changed]`

- **Goal:** give the single right region the live 40%-of-chart-area cap, the grow/reduce
  behaviour, the content bound that keeps it on-screen, and the full-screen normalize; wire
  it into the **same** `_apply_dock_widths` so B3 cross-clamping is coherent.
- **Deliverables:**
  - `ui/main_window.py` — right region in `_apply_dock_widths`; the full-screen
    `changeEvent(WindowStateChange)` + `resizeEvent` normalize; no persistence for the
    region.
  - `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py` — bounded minimum/ideal
    width; tables scroll/clip internally.
  - `ui/dock_layout.py` — only if a helper needs adjustment.
- **Requirements / journeys covered:** D18 `AC-D18.1`, `AC-D18.2`, `AC-D18.4`, `AC-D18.5`,
  `AC-D18.6`, `AC-D18.7`; B3.
- **Dependencies on earlier phases:** Phase 1 (model), Phase 2 (shared apply path), Phase 3
  (single region exists).
- **Exit condition:** right region grows up to `floor(0.40 × chart_area)` and shrinks to its
  minimum; both regions enlarged still keeps `chart_area ≥ 400px` and one shrinking when the
  other grows (`AC-D18.5`); region `geometry()` inside the window `rect()` with `width() > 0`
  in a full-screen-sized offscreen window; wide content does not push it off-screen; not
  persisted; no recursion between the two regions' rescale.

### Phase 5 — Regression, lookups, and full-suite green `[new/changed]`

- **Goal:** prove no D1–D16 regression and reconcile every dock-lookup test with the new
  shape.
- **Deliverables (tests):** `tests/test_d10_d13_integration.py`,
  `tests/test_watchlist_d14_midrag.py`, `tests/test_history_backfill*.py`,
  `tests/test_crosshair_axis_lane.py` (dock lookup by title/`objectName` against the single
  region; D2 chip non-overlap assertion), plus any remaining test touched by the denominator
  change.
- **Requirements / journeys covered:** `AC-D17.6`, `AC-D18.8`, global acceptance criteria
  (full pre-existing suite green; no live-TWS test).
- **Dependencies on earlier phases:** Phases 1–4.
- **Exit condition:** `QT_QPA_PLATFORM=offscreen python -m pytest tests/` is green with no
  test connecting to live TWS or transmitting an order (Q9); the D2 chip/dock non-overlap
  assertion (`AC-D2.1`) still holds against the single right region. Per project memory, if
  an intermittent failure appears, confirm it against a clean full-suite run before treating
  it as a regression (shared test-DB contention).

## Parallel sequencing (`touches_files` contract)
The Task Manager must add a **`touches_files`** field to every task so Build's Lead can
dispatch non-conflicting tasks in parallel up to `max_parallel_tasks` (default 4; optional
user-owned `docs/build/build_config.json`). The Lead is the sole writer of task status.

| File | Phase | Consequence |
|---|---|---|
| `ui/dock_layout.py` | 1 (new), 4 (maybe) | Authored in Phase 1; after that read-only unless Phase 4 adjusts a helper |
| `ui/watchlist_panel.py` | 1 | Re-parameterised to the chart-area denominator; serial per file |
| `ui/main_window.py` | 2, 3, 4 | **Serial chain** — must not share a wave with another task touching it |
| `ui/active_trader_panel.py` | 3, 4 | Serial with itself; may parallelise with Phase-2 `main_window.py` work (disjoint files) |
| `ui/active_portfolio_panel.py` | 3, 4 | Serial with itself; same as above |
| `tests/test_watchlist.py` | 1 | Denominator update; serial per file |
| `tests/test_d10_d13_integration.py` | 1/2 (denominator), 5 (lookup) | Serial per file |
| `tests/test_crosshair_axis_lane.py` | 5 | Single-region dock lookup + chip non-overlap; serial per file |
| `tests/test_watchlist_d14_midrag.py`, `tests/test_history_backfill*.py` | 5 | Right-dock title lookup updates; serial per file |

Practical rule: `ui/main_window.py` is the single shared production file whose three phases
(2, 3, 4) must serialise; the two right-panel files can parallelise with Phase-2
`main_window.py` work but serialise against each other; Phase-5 test-file updates may
parallelise across the four test modules. This is an architecture-level constraint on the
task graph, not a task decomposition — the Task Manager populates `touches_files` accurately
and the Lead enforces the wave rule (no two tasks with overlapping `touches_files` in one
wave).

## Assumptions
These are plan-level assumptions not already captured in `requirements.md`'s Assumptions Log
(A34–A36 already cover the D17/D18 geometry decisions).

- **PA-D17D18-1 (chart-area denominator = central widget width).** `chart_area` is measured
  as `MainWindow.centralWidget().width()` (the toolbar + `ChartPanel` region, excluding both
  dock regions). No separate "chart plot" width is used, because the central widget is the
  region the docks take space from. (Consistent with the Glossary "Chart area" definition in
  `requirements.md`.)
- **PA-D17D18-2 (right-region minimum ≈ 200px).** The requirement specifies the 40% cap and
  that a minimum exists (`AC-D18.4`) but not its value; a ~200px min is proposed so the
  ladder/portfolio remain usable, mirroring the watchlist's 150px role.
- **PA-D17D18-3 (the "stacked splitter" is optional).** B2 requires one region with the two
  sections **equal width**; a vertical `QSplitter` between them is allowed (so the user can
  adjust the vertical split) but is not required — a plain `QVBoxLayout` is the default.
  Either way, width equality is guaranteed by the single region.
- **PA-D17D18-4 (splitterMoved source may fall back).** The exact Qt-internal handle signal
  for dock areas is version/layout dependent; the design permits an event-filter fallback,
  with the pure width rule verified independently (see architecture risks).
- **PA-D17D18-5 (no `showFullScreen` call is added).** Full screen remains an OS/WM state;
  the fix is to react to the state change and resize, so the region fits the **visible**
  window.
- **PA-D17D18-6 (D13 helper names/signatures preserved where possible).** Only the
  denominator semantics change (B1), so the D14/D10 test surface updates minimally.
- **PA-D17D18-7 (the right region is not persisted).** A36 — no new `QSettings` key is added
  and `AC-D18.7` is satisfied by the default.
- **PA-D17D18-8 (regression policy unchanged).** Every fix ships with an offscreen check
  that fails before and passes after (Q8), and no automated test touches live TWS (Q9).

No open requirements escalations for this batch. Requirements `AC-D17.1`–`AC-D17.6`,
`AC-D18.1`–`AC-D18.8`, Journeys 18–19, A34–A36 and R28–R31 are **satisfiable as written**;
B1–B4 are answered and no blocking question remains. The one compatibility surface — B2's
"one region" necessarily changes the dock structure that four existing tests key on by title
— is handled inside this plan (Phase 3 + Phase 5 update those tests in lockstep), and
`AC-D18.8` explicitly permits that. No requirement is narrowed, reinterpreted, or left
unsatisfied.

---

Status: READY_FOR_TASK_MANAGER
