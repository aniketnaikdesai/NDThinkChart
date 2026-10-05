# Implementation Plan — NDThinkChart Stabilization (Batch 13: D19 toolbar scroll/elide wrapper)

Scope: the current stabilization batch is **D19** — the toolbar's ~1716px
`minimumSizeHint` sat inside the central widget and pinned it, so the already-built
D17/D18 dock-width behaviour was not effective in the real (toolbar-visible) app, and the
D17/D18 test harnesses hid the toolbar, masking the constraint. It is planned on top of the
**as-built, frozen D1–D18 baseline** (commit `5bd7c93`; full offscreen suite **566 passed**).
D1–D18 are **not** re-planned. This is an existing-repo run: items are labelled `[existing]`,
`[new]`, or `[new/changed]`; the existing tech stack (PyQt6 + pyqtgraph + `ibapi`) is a hard
constraint and nothing existing is replaced. No new product features, no schema change, no new
dependency, no new external integration, and no live-order-path change.

> Companion architecture: `docs/architecture.md` (Codebase Summary, D19 tech-stack rows, and
> the D19 components/data-model/integration/non-functional/risk sections).
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D19 /
> Journey 20 / `AC-D19.1`–`AC-D19.7`; A37–A38; R32–R34; B5–B6 answered 2026-10-05;
> DG27–DG28).

## Completed baseline — D1–D18 (as-built, frozen)
D1–D15 (session shading, crosshair chip in the Y-axis lane, zoom controls/magnifier, zoom
label/position, linear volume axis with the pinned scaling nice-max + live ceiling,
price-coloured volume, volume/price width alignment, volume show/hide, inner-right drawing
labels, zone and horizontal-line double-click dialogs, resizable/persistent watchlist with
double-click load, and the `RouterMode` gesture state machine incl. the ESC-002/003/006/007
revision and the ESC-013…ESC-021 rework), **D16** (historical-bar cache-gap backfill,
including the ESC-023 New Year's year-end calendar correction), and **D17/D18** (shared
chart-area dock-width model in the pure `ui/dock_layout.py`; live `_apply_dock_widths` clamp;
single right-dock region holding Active Trader + Portfolio stacked; full-screen visibility)
are **built and verified** at commit `5bd7c93` (full offscreen suite **566 passed**). They
remain frozen and are not modified by D19. See `docs/architecture.md` for the as-built
description.

## Phases

Each phase is a milestone, coarser than Task Manager's per-task decomposition. Files touched
are listed so Task Manager can populate `touches_files` and Build can schedule waves without
file overlap.

### Phase 1 — Toolbar scroll/elide wrapper in place `[new/changed]`

- **Goal:** remove the toolbar's ~1716px width from the central widget's minimum while keeping
  the toolbar **inside the central widget** as a single ~36px row, so the already-built
  D17/D18 width model becomes effective in a toolbar-visible window (B5).
- **Deliverables (`ui/main_window.py`):**
  - Wrap the existing `toolbar` widget in a `QScrollArea`: no frame,
    `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
    wrapper height fixed at **36px** (FI-D19-1: overlay/transient horizontal scrollbar).
  - Add the wrapper to the central `QVBoxLayout` **in the toolbar's place**
    (`vbox.addWidget(scroll)` instead of `vbox.addWidget(toolbar)`); the toolbar remains the
    scroll area's widget. **Do not** move it to a `QMainWindow` toolbar area (`addToolBar` is
    explicitly not adopted, B5).
  - Give the toolbar and the wrapper stable `objectName`s (`"MainToolbar"` / `"ToolbarScroll"`)
    so tests can locate them after the wrap.
  - Keep `conn_badge` inside the scroll region (FI-D19-2) and keep the trailing stretch; the
    toolbar's control set and signal wiring are unchanged.
  - **Do not touch** `ui/dock_layout.py`, `_chart_area_width`, `_apply_dock_widths`, or the cap
    constants (B6).
- **Requirements / journeys covered:** D19; `AC-D19.4`, `AC-D19.5` (implementation); enables
  `AC-D19.1`–`AC-D19.3`, `AC-D19.7`; Journey 20; A37/A38; DG27; R32.
- **Dependencies on earlier phases:** none (a single self-contained change in
  `ui/main_window.py`).
- **Exit condition:** with the toolbar visible, `centralWidget().minimumSizeHint().width() <=
  CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH` (750px), the toolbar's laid-out
  height is `<= ~40px`, the toolbar is still a descendant of `centralWidget()`, and driving the
  watchlist to its cap reaches `floor(0.50 × chart_area)` rather than staying at
  `WATCHLIST_MIN_WIDTH`.

### Phase 2 — Remove test masking + toolbar-visible regression guard `[new/changed]`

- **Goal:** make the D17/D18 acceptance tests exercise a **toolbar-visible** window so the D19
  regression cannot recur, and prove the guard genuinely discriminates (`AC-D19.6`).
- **Deliverables (tests):**
  - `tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`,
    `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py`,
    `tests/test_dock_layout.py`: **remove the `toolbar.hide()` masking** (and the
    `centralWidget().layout().itemAt(0).widget()` lookup that now returns the wrapper) or pair
    it with a toolbar-visible variant.
  - Add/convert **at least one D17 test and at least one D18 test** to run with the toolbar
    visible and assert the real-app outcomes: `AC-D19.1` (watchlist reaches
    `floor(0.50 × chart_area)`), `AC-D19.2` (right region fully on-screen), `AC-D19.3`
    (`chart_area >= CHART_MIN_WIDTH`).
  - Optionally add a focused `tests/test_toolbar_scroll_d19.py` for the wrapper-specific
    `AC-D19.4`/`AC-D19.5` assertions (central min hint bound, `<= ~40px` row, toolbar still a
    descendant of the central widget, controls reachable via a non-zero horizontal scroll
    range, central width shrinks with the window).
- **Pre-fix evidence (`AC-D19.6` / R33):** run the new/updated toolbar-visible tests against the
  **pre-fix tree** (commit `5bd7c93`, e.g. a temporary worktree/stash before Phase 1's change is
  in place) and record that ≥1 D17 and ≥1 D18 test **fail** there, then **pass** after Phase 1.
  The intermediate red is intentional, not a regression. (The Validator independently confirmed
  the discrimination: pre-fix, the toolbar-visible window pins `centralWidget().width()` at
  1716 and the watchlist cannot reach `floor(0.50 × chart_area)`, so the D17 cap assertion and
  the D18 40%-cap assertion fail; post-fix they pass.)
- **Requirements / journeys covered:** `AC-D19.1`, `AC-D19.2`, `AC-D19.3`, `AC-D19.6`;
  Journey 20; DG28; R33.
- **Dependencies on earlier phases:** Phase 1 (the wrapper must exist for the tests to pass;
  the pre-fix failure is captured against the pre-Phase-1 tree).
- **Exit condition:** no D17/D18 harness hides the toolbar to sidestep the constraint; the
  guard's pre-fix red and post-fix green are both recorded; the updated harnesses pass with the
  toolbar visible.

### Phase 3 — Regression + real-app verification `[new/changed]`

- **Goal:** prove no D1–D18 regression and confirm the fix in the real dev build (R34).
- **Deliverables:** no production change expected. Re-run the full offscreen suite; re-confirm
  the D2 chip/dock non-overlap (`AC-D2.1`) and the D13/D17/D18 criteria in a toolbar-visible
  window; record a manual `python main.py` check that the toolbar scrolls/elides in place as one
  row and the watchlist grows to its cap (R34).
- **Requirements / journeys covered:** `AC-D19.7`; R34; global acceptance criteria (full suite
  green; no live-TWS test).
- **Dependencies on earlier phases:** Phases 1–2.
- **Exit condition:** `QT_QPA_PLATFORM=offscreen python -m pytest tests/` is green with no test
  connecting to live TWS or transmitting an order (Q9); the D13/D17/D18 criteria hold in a
  toolbar-visible window; the manual dev-build check is recorded. Per project memory, confirm
  any intermittent failure with a clean full-suite run before treating it as a regression
  (shared test-DB / collection-order noise).

## Parallel sequencing (`touches_files` contract)
The Task Manager must add a **`touches_files`** field to every task so Build's Lead can
dispatch non-conflicting tasks in parallel up to `max_parallel_tasks` (default 4; optional
user-owned `docs/build/build_config.json`). The Lead is the sole writer of task status.

| File | Phase | Consequence |
|---|---|---|
| `ui/main_window.py` | 1 | Single production change (toolbar wrapper). One task; serial with any other `main_window.py` task (none in this batch) |
| `tests/test_dock_widths_d17.py` | 2 | Masking removal + toolbar-visible guard; serial per file |
| `tests/test_dock_widths_d18.py` | 2 | Masking removal + toolbar-visible guard; serial per file |
| `tests/test_dock_widths_d18_impl.py` | 2 | Masking removal; serial per file |
| `tests/test_dock_d18_region.py` | 2 | Masking removal; serial per file |
| `tests/test_dock_layout.py` | 2 | Masking removal; serial per file |
| `tests/test_toolbar_scroll_d19.py` (optional, new) | 2 | Wrapper-specific `AC-D19.4`/`AC-D19.5` assertions; disjoint from the five above |
| `ui/dock_layout.py`, `ui/watchlist_panel.py` | — | **Not touched** (B6 keeps the cap; D19 does not change the width model) |

Practical rule: Phase 1's `ui/main_window.py` change is the only production edit and is
self-contained. Phase 2's test-file updates are disjoint files and **may parallelise** across
the five modules (and the optional new file). Phase 3 adds no file. The one ordering constraint
is that Phase 2's pass-after assertions depend on Phase 1; the pre-fix red evidence is captured
against the pre-Phase-1 tree.

## Assumptions
These are plan-level assumptions not already captured in `requirements.md`'s Assumptions Log
(A37/A38 already record the diagnosis, the B5 fix choice, and the B6 cap decision).

- **PA-D19-1 (wrapper mechanism).** The toolbar is wrapped in a `QScrollArea` with no frame,
  `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
  inserted into the central `QVBoxLayout` in the toolbar's place. This is the adopted mechanism
  (independently reproduced offscreen: central `minimumSizeHint` 1716 → 88; watchlist grows to
  622 at chart_area 1244; right dock stays on-screen; central width shrinks with the window).
- **PA-D19-2 (stable object names).** The toolbar and its scroll wrapper carry stable
  `objectName`s (`"MainToolbar"` / `"ToolbarScroll"`) so the updated tests locate them by name;
  `centralWidget().layout().itemAt(0).widget()` now resolves to the wrapper.
- **PA-D19-3 (one-row height, overlay scrollbar).** The wrapper height is fixed at 36px and the
  horizontal scrollbar is overlay/transient (FI-D19-1) so the laid-out toolbar height stays
  `<= ~40px`; vertical scrolling is always off. (Where a platform/style reserves a scrollbar
  lane, the fixed wrapper height bounds the row; R34's real dev-build check covers the macOS
  target, whose overlay scrollbars are the default.)
- **PA-D19-4 (`conn_badge` stays in the scroll region).** The trailing stretch and `conn_badge`
  remain inside the scrollable toolbar content (FI-D19-2); the control set is unchanged.
- **PA-D19-5 (width model untouched).** `ui/dock_layout.py`, `_chart_area_width`,
  `_apply_dock_widths`, and the cap constants are unchanged (B6); D19 only lowers the central
  widget's minimum.
- **PA-D19-6 (pre-fix evidence method).** `AC-D19.6`'s "fail pre-fix / pass post-fix" is
  evidenced by running the updated toolbar-visible tests against the pre-Phase-1 tree (commit
  `5bd7c93`, via a temporary worktree/stash) and recording the red, then re-running after
  Phase 1.
- **PA-D19-7 (manual real-app check is a user step).** R34's real-macOS-window verification is
  a manual `python main.py` check recorded in the build log; the automated guard is the
  offscreen toolbar-visible test (`AC-D19.6`).
- **PA-D19-8 (regression policy unchanged).** Every fix ships with an offscreen check that
  fails before and passes after (Q8), and no automated test touches live TWS (Q9).

No open requirements escalations for this batch. Requirements D19 / Journey 20 /
`AC-D19.1`–`AC-D19.7`, A37–A38, R32–R34 and DG27–DG28 are **satisfiable as written**; B5–B6 are
answered and no blocking question remains. No requirement is narrowed, reinterpreted, or left
unsatisfied.

Validation: `docs/plan_review.md` — Status: APPROVED (validation pass 1, retry 0 of 3).
Canonical companions: `docs/architecture.md` (D19 increment), `docs/plan_review.md`.

---

Status: READY_FOR_TASK_MANAGER
