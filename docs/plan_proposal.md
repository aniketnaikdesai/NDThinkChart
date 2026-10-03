# Plan Proposal — NDThinkChart D17 + D18 (incremental panel-layout change)

> Draft proposal owned by **Plan**. Not canonical. Plan Artifact Editor & Validator
> checks this against `docs/requirements/requirements.md` (Status: `READY_FOR_PLAN`,
> Batch 11 D17+D18) and writes `docs/plan.md`.
>
> **Scope:** incremental change on top of the built, green D1–D16 system. **D1–D16 are
> not re-planned.** Existing-repo run: `docs/architecture.md` is the as-built baseline,
> PyQt6 + pyqtgraph is a hard constraint, no stack change, no schema change, no new
> dependency, no new integration, no live-order-path change.
>
> Companion: `docs/architecture_proposal.md` (component/data/integration design).

---

## Coverage map (requirements → phases)

| Requirement / journey / AC | Phase |
|---|---|
| Shared width model + constants (`ui/dock_layout.py`) | **Phase 1** |
| D13 helpers re-denominated to chart area (B1); `AC-D13.1`–`AC-D13.3` updated in lockstep | **Phase 1** |
| D17 live watchlist clamp during the drag (min 150 / cap 50% chart area), both directions; `AC-D17.1`–`AC-D17.3`; Journey 18 | **Phase 2** |
| D17 chart-minimum/cross-clamp hook on both dock regions (B3); `AC-D17.5` | **Phase 2** |
| D17 persistence re-clamped to the new cap; `AC-D17.4` | **Phase 2** |
| D18 single right-dock region (Active Trader + Portfolio stacked, equal width); `AC-D18.3`; Journey 19 | **Phase 3** |
| D18 right-region 40% cap + grow/reduce + content-bounded (`AC-D18.2`, `AC-D18.4`, `AC-D18.6`) | **Phase 4** |
| D18 full-screen visibility / normalize (`AC-D18.1`) | **Phase 4** |
| D18 combined cross-clamping (`AC-D18.5`) | **Phase 4** |
| D18 not-persisted default (`AC-D18.7`) | **Phase 4** |
| Regression: D13/D14/D10/D2 dock-lookup tests + full suite (`AC-D17.6`, `AC-D18.8`) | **Phase 5** |

---

## Phases

Each phase is a milestone, coarser than Task Manager’s per-task decomposition. Files
touched are listed so Task Manager can populate `touches_files` and Build can schedule
waves without file overlap.

### Phase 1 — Shared width model and re-denominated D13 helpers (pure, no UI behaviour yet)

- **Goal:** introduce the single source of truth for dock widths and the chart-minimum
  rule, measured against the **chart area** (B1/B3), before any live wiring.
- **Requirements covered:** the numerical foundations of D13 (corrected denominator),
  D17 and D18; enables `AC-D13.1`–`AC-D13.3`, `AC-D17.1`–`AC-D17.5`, `AC-D18.2`,
  `AC-D18.5`.
- **Files touched:** `ui/dock_layout.py` (**new**), `ui/watchlist_panel.py`
  (re-parameterise `watchlist_max_width`/`clamp_watchlist_width`/`load_`/`save_` to the
  chart-area denominator, delegating to `ui/dock_layout`), and the pure-function tests
  `tests/test_watchlist.py` (update clamp-math assertions to the chart-area cap in
  lockstep per R28).
- **Deliverables:** `watchlist_max_width(chart_area_w)`,
  `right_dock_max_width(chart_area_w)`, and `plan_dock_widths(chart_area_w,
  requested_left, requested_right)` returning `(left, right)` that guarantees
  `chart_area ≥ 400px`; constants for min/default/cap fractions.
- **Dependencies:** none (pure functions; safe first wave).
- **Exit condition:** pure-function unit tests pass for all six timeframes-independent
  edge cases (tiny window, cap < min, both docks near max, one side over budget);
  pre-existing tests that do not depend on the denominator stay green.

### Phase 2 — D17: live watchlist clamp + chart-minimum hook

- **Goal:** enforce the watchlist cap **during the drag** and on window resize, in both
  directions, against the corrected chart-area denominator, and re-clamp the persisted
  width on restore.
- **Requirements covered:** D17 (`AC-D17.1`–`AC-D17.5`), Journey 18; keeps D13
  semantics (min 150px, default ~220px, Q26 persistence).
- **Files touched:** `ui/main_window.py` (add `_apply_dock_widths`, the
  `splitterMoved`/dock-change hook, a two-directional `resizeEvent` re-clamp, and the
  persistence re-clamp on restore/`closeEvent`; **no right-region changes yet**),
  `ui/dock_layout.py` (only if Phase 1 surfaced a needed helper).
- **Deliverables:** the watchlist handle moves freely between 150px and the cap; the
  cap stops the drag **without any window resize**; width restored clamped to the
  current cap; no recursion/jitter.
- **Dependencies:** Phase 1 (the width model and corrected denominator).
- **Exit condition:** `AC-D17.1`–`AC-D17.4` pass in an offscreen `MainWindow` with no
  `resizeEvent` during the drag (`AC-D17.3`); `tests/test_watchlist.py` and
  `tests/test_d10_d13_integration.py` updated to the new denominator and green.

### Phase 3 — D18: single right-dock region (Active Trader + Portfolio stacked)

- **Goal:** re-shape the two right `QDockWidget`s into **one** right-dock region whose
  stacked sections are inherently equal width (B2), without changing ladder/portfolio
  behaviour or signals.
- **Requirements covered:** D18 `AC-D18.3`, and the container prerequisite for
  `AC-D18.1`–`AC-D18.2`; Journey 19.
- **Files touched:** `ui/main_window.py` (replace `:234–252` two-dock setup with one
  region; keep the title/`objectName` resolvable by `_on_dom_toggled` and tests),
  `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py` (container-friendly
  layout only; **no width bound or cap yet** — that is Phase 4).
- **Deliverables:** one right region containing `ActiveTraderPanel` over
  `ActivePortfolioPanel`; both sections render at equal width; the DOM toggle and
  existing dock-title lookups still resolve.
- **Dependencies:** Phase 1 (constants/model), Phase 2 (so only one region is wired to
  the shared clamp and the left side is already correct).
- **Exit condition:** `AC-D18.3` passes (section widths equal within 1px); the
  pre-existing tests that hide/seek `"Active Trader"`/`"Portfolio"` are updated in
  lockstep and green; ladder/portfolio signal wiring untouched.

### Phase 4 — D18: 40% cap, cross-clamp, content bound, and full-screen visibility

- **Goal:** give the single right region the live 40%-of-chart-area cap, the grow/reduce
  behaviour, the content bound that keeps it on-screen, and the full-screen normalize;
  wire it into the **same** `_apply_dock_widths` so B3 cross-clamping is coherent.
- **Requirements covered:** D18 `AC-D18.1`, `AC-D18.2`, `AC-D18.4`, `AC-D18.5`,
  `AC-D18.6`, `AC-D18.7`; B3.
- **Files touched:** `ui/main_window.py` (right region in `_apply_dock_widths`; the
  full-screen `changeEvent(WindowStateChange)` + `resizeEvent` normalize; no
  persistence for the region), `ui/active_trader_panel.py`,
  `ui/active_portfolio_panel.py` (bounded minimum/ideal width; tables scroll/clip
  internally), `ui/dock_layout.py` (only if a helper needs adjustment).
- **Deliverables:** right region grows up to `floor(0.40 × chart_area)` and shrinks to
  its minimum; both regions enlarged still keeps `chart_area ≥ 400px` and one shrinking
  when the other grows; region `geometry()` inside the window `rect()` with
  `width() > 0` in a full-screen-sized offscreen window; wide content does not push it
  off-screen; not persisted.
- **Dependencies:** Phase 1 (model), Phase 2 (shared apply path), Phase 3 (single
  region exists).
- **Exit condition:** `AC-D18.1`–`AC-D18.7` pass offscreen; no recursion between the
  two regions’ rescale.

### Phase 5 — Regression, lookups, and full-suite green

- **Goal:** prove no D1–D16 regression and reconcile every dock-lookup test with the new
  shape.
- **Requirements covered:** `AC-D17.6`, `AC-D18.8`, global acceptance criteria
  (full pre-existing suite green; no live-TWS test).
- **Files touched:** `tests/test_d10_d13_integration.py`,
  `tests/test_watchlist_d14_midrag.py`, `tests/test_history_backfill*.py`,
  `tests/test_crosshair_axis_lane.py` (dock lookup by title/`objectName` against the
  single region; D2 chip non-overlap assertion), plus any remaining test touched by the
  denominator change.
- **Deliverables:** full offscreen suite green (D1–D16 frozen behaviour preserved);
  the D2 chip/dock non-overlap assertion (`AC-D2.1`) still holds against the single
  right region.
- **Dependencies:** Phases 1–4.
- **Exit condition:** `QT_QPA_PLATFORM=offscreen python -m pytest tests/` is green with
  no test connecting to live TWS or transmitting an order (Q9). Per project memory, if
  an intermittent failure appears, confirm it against a clean full-suite run before
  treating it as a regression (shared test-DB contention).

---

## Sequencing / parallel-build notes (for Task Manager’s `touches_files`)

- `ui/dock_layout.py` is **new** and should be authored in Phase 1; after that it is
  read-only unless Phase 4 adjusts a helper.
- `ui/main_window.py` is touched by **Phases 2, 3, and 4** → a **serial chain** for
  those phases (they must not share a wave).
- `ui/active_trader_panel.py` / `ui/active_portfolio_panel.py` are touched by **Phases 3
  and 4** → serial with each other; Phase 3 may run in parallel with the Phase 2
  `main_window.py` work only if their `touches_files` do not overlap (they do not —
  panel files vs `main_window.py`), but Phase 4 depends on both.
- Test-file updates in Phase 5 may parallelise across the four test modules.
- Build must not run two tasks with overlapping `touches_files` in one wave (the
  existing parallel-build constraint in `docs/architecture.md`).

---

## Assumptions

These are plan-level assumptions not already captured in `requirements.md`’s
Assumptions Log (A34–A36 already cover the D17/D18 geometry decisions).

1. **Chart-area denominator = central widget width.** `chart_area` is measured as
   `MainWindow.centralWidget().width()` (the toolbar + `ChartPanel` region excluding
   both dock regions). No separate “chart plot” width is used, because the central
   widget is the region the docks take space from. (Consistent with the Glossary
   “Chart area” definition in `requirements.md`.)
2. **Right-region minimum ≈ 200px.** The requirement specifies the 40% cap and that a
   minimum exists (`AC-D18.4`) but not its value; a ~200px min is proposed so the
   ladder/portfolio remain usable, mirroring the watchlist’s 150px role.
3. **The “stacked splitter” is optional.** B2 requires one region with the two sections
   **equal width**; a vertical `QSplitter` between them is allowed (so the user can
   adjust the vertical split) but is not required — a plain `QVBoxLayout` is the default.
   Either way, width equality is guaranteed by the single region.
4. **Searching for a `splitterMoved` source is allowed to fall back.** The exact
   Qt-internal handle signal for dock areas is version/layout dependent; the design
   permits an event-filter fallback, with the pure width rule verified independently
   (see Architecture Risks).
5. **No `showFullScreen` call is added.** Full screen remains an OS/WM state; the fix is
   to react to the state change and resize, so the region fits the **visible** window.
6. **D13’s helper names/signatures are preserved where possible** so the D14/D10 test
   surface updates minimally; only the denominator semantics change (B1).
7. **The right region is not persisted** (A36), so no new `QSettings` key is added and
   `AC-D18.7` is satisfied by the default.
8. **Regression policy unchanged** — every fix ships with an offscreen check that fails
   before and passes after (Q8), and no automated test touches live TWS (Q9).

---

## Flagged Issues

None. Requirements `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`, Journeys 18–19,
A34–A36 and R28–R31 are **satisfiable as written** with the architecture above; B1–B4
are answered and no blocking question remains. The one point worth surfacing for the
Validator (not an escalation — a note, not a gap) is that satisfying B2’s “one region”
necessarily changes the dock structure that four existing tests key on by title; this
is handled inside this plan (Phase 3 + Phase 5 update those tests in lockstep), and
`AC-D18.8` explicitly permits that. No requirement is narrowed, reinterpreted, or left
unsatisfied.

---

Status: READY_FOR_VALIDATION
