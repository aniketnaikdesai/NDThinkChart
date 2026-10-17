# Implementation Plan Proposal — NDThinkChart Batch 19 (**D44**): the collapsed Watchlist becomes a thin vertical bar that expands back to the full panel

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical plan —
> `docs/plan.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/architecture_proposal.md` (relationship table, Codebase Summary, decisions `S22`–`S28`, components,
> data model, integrations, frozen interfaces, non-functional approach, risks `AR-D44-1`–`AR-D44-10`, and the
> requirements→architecture traceability table). Module index: `docs/codebase-map.md` (refreshed for this
> batch).
>
> **Run shape:** **legacy single-scope** — the invocation preamble carries **no `phase: P<n>`**, so these are
> the unsuffixed proposal files and the D44 increment merges into the cumulative canonical
> `docs/architecture.md` / `docs/plan.md` as a `## D44 increment` section (the D16–D42 precedent).
>
> **This file replaces the stale D42 draft** (the previous contents of `docs/plan_proposal.md`). **D42 is
> delivered** — 26/26 tasks, full offscreen suite green, review `REVIEW_COMPLETE`, committed — and its
> Validator cycle ended `Status: APPROVED` (`docs/plan_review.md`, D42 cycle 3 of 3, `ESC-050` amendment
> verified). **D1–D43 are settled and are NOT re-planned or reopened here**; per the repo's per-batch
> convention the previous batch's draft is **superseded**, not extended. This is **Revision 1** of the D44
> draft — no `CHANGES_REQUIRED` cycle precedes it, because the requirements were extended with D44 after the
> D42 review had already approved.
>
> **Scope: D44 only** — an **owner-requested net-new UI feature** (Batch 19, recorded 2026-10-16). Requirements
> of record: `requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-16 17:28) — the D44 status/audit
> block (`:118`–`:136`), the revised `## Non-Goals` (`:258`–`:267`), the D44 work item (`:353`–`:365`),
> **Journey 37** (`:976`–`:989`), **`### D44`** (`:3782`–`:3925`), **`AC-D44.1`–`AC-D44.8`**
> (`:3854`–`:3891`), the supersession/revision record (`:3892`–`:3905`), the edge cases (`:3906`–`:3913`),
> the correction record (`:3914`–`:3925`), **A75–A78** (`:4005`–`:4008`), **R66–R67** (`:4129`–`:4130`), the
> Batch-19 summary (`:4239`–`:4246`); `design_gaps.md` **DG74** (`:1177`–`:1182`); `open_questions.md` **Q54**
> (answered 2026-10-16; owner confirmation requested, non-blocking defaults recorded).
> **Baseline:** `main` @ **`0c4d478`**, full offscreen suite green.
>
> **Supersessions this plan keeps consistent (already recorded by the Requirements Analyst — never silent):**
> `AC-D21.11.2`/`AC-D21.11.3` (the collapsed **appearance**) are **revised**; the **150px-minimum clause** of
> `AC-D13.1`/`AC-D17.2` becomes **expanded-state only**; `AC-D21.11.1` (single "Watchlist" label, duplicate
> dock title deleted), `AC-D22.1` (**expanded**), and the D13/D17 **cap / persistence / drag / re-clamp**
> clauses are **unchanged**; the `## Non-Goals` restyling bullet is revised **only** for the D44 bar, in the
> app palette.
>
> **Escalation state at planning time.** **No escalation is open against this increment's decisions** — no
> `PLAN`-routed entry is open (`ESC-050` is `addressed`), and none is `BUILD`- or `REQUIREMENTS`-routed. The
> only open entry in `docs/code_review/escalations.json` is **ESC-055** (`routed_to: TASK_MANAGER`,
> `severity: nice-to-have`) — the D42/ESC-050 enumeration rule's *ownership remedy* for a production-entry-point
> change invalidating an assertion **outside** the changing task's `touches_files`. D44 **applies** that rule
> (`AP-D44-8`, the per-file map, the *Verified unchanged* table) but does **not** absorb the escalation, which
> is Task Manager's. `docs/plan_review.md` is the **APPROVED** D42 cycle, so this is a normal forward cycle.

**The one workstream.** The collapse mechanism already exists (D21.11); D44 changes the collapsed
**appearance** and adds the missing **collapsed width**. Two halves that must land together for the feature to
be true:

1. **The width (the core fix — `AC-D44.5`, R66/DG74).** A **pure** collapsed-width rule in
   `ui/dock_layout.py` (`WATCHLIST_COLLAPSED_WIDTH = 30`; the 150px minimum becomes **expanded-state only**),
   consumed by **both** clamp branches of the single apply entry point
   `MainWindow._apply_dock_widths` (`ui/main_window.py:2459` — the right-dock-visible branch via
   `plan_dock_widths`, and the right-dock-hidden branch's direct clamp at `:2527`), plus the **D21.13-style
   minimum-width relaxation** (`panel` + `dock` → 30 while collapsed, back to 150 on expand) and the deferred
   re-apply, so a `resizeEvent` **or** a dock drag cannot snap the bar back to 150px. `MainWindow._watchlist_width`
   is **never overwritten while collapsed** — it *is* the "previous width" `AC-D44.2` restores.
2. **The visual + the expand affordance (`AC-D44.1`/`.2`/`.3`/`.4`/`.6`, A77).** A small custom widget with a
   `paintEvent` drawing the rotated `WATCHLIST` label (Qt cannot rotate a `QPushButton`'s text) as the panel's
   **full-height** collapsed body, in the app palette (`#141822` / `#232938` / `#cbd5e1`), with hover/pressed
   feedback through `ui/visual_conventions.py::set_button_active`; a 30×28 handle in the dock's **title-bar
   slot** while collapsed (so the dock stays movable — DG37); the header strip, the D22.1 `+` and the
   column-header row hidden while collapsed and restored on expand; clicking the bar expands to the tracked
   previous width, re-clamped. **No persistence** (A76) — no new `QSettings` key; the app starts expanded.

**Out of scope — do NOT plan these.** Every earlier defect/feature (D1–D43) and their delivered artifacts. No
D44 path reaches the chart renderer (**pyqtgraph is a locked decision** — `docs/memory.md`, 2026-10-16), the
load path, the planner, the bar cache, the alarms, the drawings/studies, the orders machinery, the right dock,
or the D42/D43 data paths. **No new dependency and no stack change.** **ESC-055** stays TASK_MANAGER-owned.

---

## Phases

Two phases. Phase 1 is the whole feature (production change + the suites it invalidates + the new guards) —
a single milestone, because the width rule and the bar are two halves of one user-visible behaviour and
because each corrected suite must ride **with** the production change that invalidates it (the `ESC-055`
lesson). Phase 2 is the batch-level reconciliation the repo always runs (the D19/D20/D42 precedent) and adds
**no production edit**.

### Phase 1 — The collapsed watchlist thin bar: the width model, the apply path, the bar, the expand path, and the corrected + added suites

- **Goal:** collapsing the watchlist renders a **30px vertical bar** with the rotated `WATCHLIST` label in the
  app palette, the header strip / `+` (D22.1) / column-header row hidden; the collapsed width is **honoured by
  the layout** — a window `resizeEvent` or a dock drag does **not** snap it back to the 150px minimum; clicking
  the bar **expands** the panel to the width it held immediately before collapsing (re-clamped to the current
  expanded cap/min); the dock stays **movable/floatable** while collapsed; the collapse state is **not
  persisted**; and the **expanded** D13/D17/D18/D21.13 criteria and their suites are unaffected.
- **Covers:** `AC-D44.1`, `AC-D44.2`, `AC-D44.3`, `AC-D44.4`, **`AC-D44.5`** (the core fix), `AC-D44.6`,
  `AC-D44.7`, `AC-D44.8`; Journey 37 (steps 1–5 + the edge cases); the revised `AC-D21.11.2`/`.3` and the
  revised 150px-minimum clause of `AC-D13.1`/`AC-D17.2`; `A75`–`A78`; `R66`, `R67`; `DG74`. Non-regression
  contract: `AC-D21.11.1`, `AC-D22.1` (expanded), `AC-D13.2`/`.3`, `AC-D17.1`/`.3`–`.6`, `AC-D18.*`, D21.13,
  D14, D21.5, D39.
- **Requirements/journeys:** Journey 37 steps 1–5 and its edge cases (collapse from the 150px minimum → expand
  restores 150; collapse from the cap → expand restores the cap; resize/drag while collapsed does not expand
  it; a floating watchlist is still clickable to expand; disconnected/empty watchlist still collapses/expands;
  first launch starts expanded; the `CHART_MIN_WIDTH` invariant holds in both states; a very narrow window
  where 30px still fits).
- **Dependencies:** none on any other phase. **Internally ordered** (see the per-file map): the pure rule
  (`ui/dock_layout.py`) **before** its consumers; the bar widget **before** the `MainWindow` wiring that swaps
  the title bar; each corrected suite in the **same phase** as the production change that invalidates it. The
  two file-groups that touch `ui/main_window.py`, and the two that touch
  `tests/test_watchlist_columns_d21.py`, must sit in **different waves** (`build_wave.py` forbids two
  `in_progress` tasks with overlapping `touches_files`).
- **Deliverable:** `ui/dock_layout.py` (the collapsed constant + the pure rule + the `left_collapsed` mode),
  `ui/watchlist_panel.py` (the bar widget + the handle + the visual sync + the transition signal),
  `ui/main_window.py` (the collapsed-aware apply path + the minimum-width pin + the wiring), the **two new
  suites**, the **two extended** suites, and the **corrected** sites — full offscreen suite green, with the new
  width guard **RED at `0c4d478`** for the right reason.

### Phase 2 — Reconciliation, non-regression and the correction record

- **Goal:** the whole offscreen suite is green with **every** existing assertion either keeping its **exact**
  expectation or **corrected intent-preserving** to the revised criteria — **none weakened, none deleted** —
  and every such correction recorded **with its cause**; the enumeration of the affected suites is **complete
  by rule** (by call site of the changed entry points, not by the suites the design names — the `ESC-050`
  rule and `ESC-055`'s ownership remedy), so the *Verified unchanged* set is evidence rather than assumption;
  the RED-at-`0c4d478` → GREEN evidence is recorded for the guard; and the D44 increment is ready to merge
  into the canonical docs.
- **Covers:** `AC-D44.8` (the guard's RED→GREEN evidence and the expanded-state suites); `R67`; the D44
  correction record; the non-regression re-check of `AC-D13.2`/`.3`, `AC-D17.1`/`.3`–`.6`, `AC-D18.*`,
  `AC-D21.11.1`, `AC-D22.1` (expanded), D14/D21.5/D39.
- **Dependencies:** Phase 1 complete.
- **Deliverable:** the full-suite green run + the corrected/added/verified-unchanged enumeration with causes +
  the guard's RED→GREEN evidence + the correction-record entries for Task Manager / Build / Code Reviewer.
  **No production edit.**

---

## Per-file `touches_files` map and sequencing constraints

**Sequencing constraint (binding).** Build runs a wave frontier: two tasks with overlapping `touches_files`
must never be `in_progress` in the same wave. Two files are shared by more than one file-group:
**`ui/main_window.py`** (the apply path **and** the transition wiring) and
**`tests/test_watchlist_columns_d21.py`** (the collapsed-width leg **and** the collapsed-appearance legs).
Those pairs **must sit in different waves**, and the wiring must follow the apply path (it calls it).
`ui/watchlist_panel.py` is a **single** file-group (the widget and the visual sync belong to one worker: the
widget's geometry and the panel's layout are the same change).

### Phase 1 — file map

| File | Change | Tests in the same task / touched by the change |
|---|---|---|
| `ui/dock_layout.py` | `+ WATCHLIST_COLLAPSED_WIDTH = 30`; `+ plan_watchlist_width(chart_area_w, requested_left, collapsed=False)` (the **single** collapsed/expanded width rule); `plan_dock_widths(..., left_collapsed=False)` — a collapsed left is **fixed** at the collapsed width, its own floor becomes 30, the cross-clamp loop may shrink **only** the right, the `chart_area_w - left - right >= CHART_MIN_WIDTH` budget is unchanged, and the infeasible branch returns `(left_min, RIGHT_DOCK_MIN_WIDTH)` so today's expanded `(150, 200)` is preserved exactly; `clamp_watchlist_width(width, chart_area_w)` delegates to the new helper with `collapsed=False` (`S23`) | `tests/test_dock_layout.py` (**extend** — the collapsed pure cases + the constants/agreement test, incl. the new constant's cross-module agreement), `tests/test_watchlist.py` (**extend** — the collapsed delegate case); `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_right_dock_d21.py`, `tests/test_d10_d13_integration.py`, `tests/test_dock_layout.py::test_T52_T04`, `tests/test_toolbar_scroll_d19.py` (**verified unchanged** — 3-argument/expanded call sites) |
| `ui/main_window.py` **(file-group A — the collapsed-aware apply path)** | `_apply_dock_widths`: read `collapsed = bool(self.watchlist_panel.is_collapsed())`; the right-dock-visible branch forwards `left_collapsed=collapsed` to `_plan_dock_widths`; the right-dock-hidden branch computes `desired = plan_watchlist_width(chart_area, base_left, collapsed=collapsed)`; **`self._watchlist_width` is not assigned while collapsed**; `_plan_dock_widths` forwards the flag; `_dock_widths_consistent` becomes collapsed-aware (`S24`) | `tests/test_watchlist_columns_d21.py::test_D21_10_T03` (**correct** — the **collapsed-width** leg only: the `>= WATCHLIST_MIN_WIDTH` assertion after `_apply_dock_widths(10**6)` becomes the collapsed-width assertion, and the `>= WATCHLIST_MIN_WIDTH` leg moves to the **expanded** state); `tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_right_dock_d21.py`, `tests/test_d10_d13_integration.py`, `tests/test_dock_d18_region.py` (**verified unchanged** — all drive it with the watchlist expanded) |
| `ui/watchlist_panel.py` **(file-group B)** | `CollapsedWatchlistBar(QWidget)` (fixed width, `WA_StyledBackground`, the object-name stylesheet in the app palette, a `paintEvent` drawing `WATCHLIST` rotated 90° counter-clockwise and centred, `expand_requested`, `set_button_active` hover/pressed); `WatchlistPanel.collapsed_bar` (the **full-height** collapsed body) + `::collapsed_handle` (the 30×28 collapsed title-bar handle); `::_apply_collapsed_visual()` (explicit `hide()`/`show()` of `header_bar` — which carries the `+` and the search box — and `table`, plus the bar and the collapsed panel styling); `collapsed_changed = pyqtSignal(bool)`; `WATCHLIST_COLLAPSED_WIDTH` **aliased** from `dock_layout`; the collapse API preserved (`S25`, `S26`) | `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (**correct** — the collapsed **appearance**) and `::test_D21_10_T03` (**correct** — the appearance + the title-bar/drag legs; a **different wave** from file-group A's edit of the same file), `tests/test_watchlist_nonregression_d22.py` (**correct** — the D21.11 block + the module docstring), `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (**correct** — `hb.isVisible()` while collapsed); `tests/test_watchlist_columns_d21.py::test_D21_10_T01` (**verified unchanged** — expanded only); **`tests/test_watchlist_collapsed_bar_d44.py` is owned here** |
| `ui/main_window.py` **(file-group C — the transition wiring)** | connect `panel.collapsed_changed` → `_on_watchlist_collapsed_changed`: swap the dock's title-bar widget (`collapsed_handle` while collapsed, `header_bar` on expand), relax/restore the minimum widths (`panel` + `dock` → 30 / 150), then `_resize_docks_guarded` + `QTimer.singleShot(0, self._apply_dock_widths)` — the `_sync_right_dock_collapse` sequence (`S24`, `S25`) | **`tests/test_dock_widths_collapsed_d44.py` is owned here** (it asserts the end-to-end transition: collapse → 30px, survive a resize/drag, expand → `clamp(W)`, the min-width flip, no key) — a **different wave** from file-group A (the same production file) |
| `tests/test_dock_widths_collapsed_d44.py` **(new — file-group C)** | `AC-D44.5`/`AC-D44.2`/`AC-D44.7` + `AC-D44.1`'s width measurable: collapse at a known `W` → `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`; still the collapsed width after a window `resizeEvent` **and** after the drag-event path (`_on_dock_drag_event`); expand → `dock.width() == clamp(W)` (incl. the collapse-from-150 and collapse-from-cap edge cases); the dock's min width is 30 while collapsed and 150 after; **no** collapse key in `QSettings`; the `CHART_MIN_WIDTH` invariant in both states. **Must be RED at `0c4d478` for the right reason** | — |
| `tests/test_watchlist_collapsed_bar_d44.py` **(new — file-group B)** | `AC-D44.1`/`.3`/`.4`/`.6`: the collapsed bar exists with the rotated-label widget and the app palette; the header strip / `+` / column-header row are **not** visible while collapsed and are visible on expand; `set_button_active` drives the hover/pressed feedback (the `active` property + a differing stylesheet); `is_collapsed()`/`set_collapsed()`/`toggle_collapsed()` semantics; clicking the bar expands | — |

**Shared-file waves (Phase 1).** The file partition has four single-file groups — **A** the collapsed-aware
apply path (`ui/main_window.py` + `tests/test_watchlist_columns_d21.py`'s **width leg**); **B** the bar widget +
the collapsed visual (`ui/watchlist_panel.py` + `tests/test_watchlist_columns_d21.py`'s **appearance legs** + the
two D22 suites + `tests/test_watchlist_collapsed_bar_d44.py`); **C** the transition wiring (`ui/main_window.py`
+ `tests/test_dock_widths_collapsed_d44.py`); **D** the pure width model (`ui/dock_layout.py` +
`tests/test_dock_layout.py` + `tests/test_watchlist.py`). (These groups are the `touches_files` partition Task
Manager decomposes into tasks — not tasks themselves.) **Ordering:** **D before A and C** (the pure rule
precedes its consumers); **A and B in different waves** (both edit `tests/test_watchlist_columns_d21.py`);
**A and C in different waves** (both edit `ui/main_window.py`); **C after A and B** (it wires the transition and
its guard asserts the end-to-end outcome). B may co-schedule with A and D (disjoint files). Every other file is
single-group.

**Phase 2 adds no production edit** — reconciliation + docs only.

---

## Tests: corrected vs added, verified unchanged, and the RED→GREEN evidence

**Corrected (never weakened, never deleted — R67 and the D44 correction record).** Every correction below
moves an assertion to the **state in which it is still true**; none is deleted, skipped or relaxed to "no
exception raised".

| Suite / case | Assertion today | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (`:386`–`:412`) | while collapsed: `panel.header_bar.isVisible()` (`:398`), `button.isVisible()` (`:399`), `button.is_struck()` (`:400`), `not button.isChecked()` (`:401`) | **The revised collapsed appearance** — `AC-D21.11.2`/`.3` are superseded for the collapsed state by D44 (`S26`): the strip is hidden while collapsed and the thin bar is shown | "Collapsing is reversible and the retained affordance is visible in the state where it is shown; the toggle's checked/struck state tracks the body": while collapsed assert the **bar** is visible + the strip/`+`/column-header row are **not**; on expand assert the strip + button return **checked and unstruck** |
| `::test_D21_10_T03` (`:417`–`:471`) — **the width leg** (Phase-1 file-group A) | `assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH` (`:465`) after `win._apply_dock_widths(10 ** 6)` (`:459`) **while collapsed** | **The collapsed width** (`S23`/`S24`): while collapsed the width is 30, not ≥150 — the 150px minimum is expanded-state only | "The width model holds in the state under test": while collapsed assert the **collapsed** width; the `>= WATCHLIST_MIN_WIDTH` leg **moves to the expanded state** (expand, then clamp, then assert) |
| `::test_D21_10_T03` — **the appearance + drag legs** (Phase-1 file-group B) | `button.isVisible()` (`:431`), `panel.header_bar.isVisible()` (`:433`), `dock.titleBarWidget() is panel.header_bar` (`:440`), the double-click-floats-the-dock on `panel.header_bar` (`:445`–`:453`) | **The revised collapsed appearance** + **the title-bar swap** (`S25`): while collapsed the title-bar widget is `collapsed_handle` | "The dock stays movable/floatable while collapsed (DG37) and the header strip is its title bar **when shown**": re-point the drag/float assertion at `collapsed_handle` and assert `dock.titleBarWidget() is panel.header_bar` **on expand** |
| `tests/test_watchlist_nonregression_d22.py` (`:104`–`:124` + the module docstring `:10`) | `panel.header_bar.isVisible()` (`:114`), `button.isVisible()` (`:115`), `button.is_struck()` (`:116`), `not button.isChecked()` (`:117`) while collapsed | **The revised collapsed appearance** (`S26`) — the same cause as `test_D21_10_T02` | "The D21.11 toggle still collapses/restores and the checked state tracks the body": the visibility assertions move to the **bar**; the expand-side assertions (`:121`–`:124`) are unchanged. The docstring's "the collapsed button stays visible + struck (VIS-D21.1)" is re-worded to the D44 collapsed form |
| `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (`:79`) | `assert hb.isVisible()` while collapsed | **A77** (`S26`): the header strip is hidden while collapsed and returns on expand | "The `+` and the toggle remain in the strip's layout and are reachable": `:63`–`:71` (parent/layout/placement) and the post-expand legs (`:80`–`:83`) are unchanged; the collapsed leg asserts the strip (and therefore the `+`) is hidden |

**Extended (additions to existing suites).**

| Suite | What is added |
|---|---|
| `tests/test_dock_layout.py` | The collapsed pure cases (`plan_watchlist_width(..., collapsed=True) == 30`; `plan_dock_widths(..., left_collapsed=True)` fixes the left at 30, keeps `chart_area_w - left - right >= CHART_MIN_WIDTH` where feasible, keeps the right within its own cap/min, returns `(30, RIGHT_DOCK_MIN_WIDTH)` on an infeasible window, and never raises / stays int-stable over the T52 grid with `left_collapsed=True`); the constants test gains `WATCHLIST_COLLAPSED_WIDTH == 30`; the cross-module agreement test gains the new constant (the `CHART_MIN_WIDTH` invariant's sibling). The **expanded** cases stay **exactly** as they are |
| `tests/test_watchlist.py` | The collapsed delegate case (`clamp_watchlist_width` remains the **expanded** rule; the panel aliases `WATCHLIST_COLLAPSED_WIDTH` from `dock_layout`) |

**Added (new suites).** `tests/test_dock_widths_collapsed_d44.py` (`AC-D44.5`'s pinning guard, `AC-D44.2`'s
previous-width restore, `AC-D44.7`'s no-key assertion, `AC-D44.1`'s width measurable) and
`tests/test_watchlist_collapsed_bar_d44.py` (`AC-D44.1`/`.3`/`.4`/`.6`). Both use the repo's offscreen harness
conventions: `IBApiClient.connect` monkeypatched to a no-op, a throwaway SQLite DB, and a **per-test
`QSettings` ini** (the D22 harness pattern) so no width/collapse state leaks between tests.

**Verified unchanged — enumerated by call site of the changed entry points (the `ESC-050` rule; `ESC-055`'s
ownership remedy).** The changed production entry points are
`ui/dock_layout.py::plan_dock_widths` / `::clamp_watchlist_width`,
`ui/main_window.py::MainWindow._apply_dock_widths` / `::_plan_dock_widths` / `::_dock_widths_consistent`, and
`ui/watchlist_panel.py::WatchlistPanel._on_header_toggled` / `::set_collapsed` / `::is_collapsed`. Every test
file that reaches any of them was found by grep and classified:

| Suite | How it reaches the change | Why it is unchanged |
|---|---|---|
| `tests/test_dock_layout.py` (21 tests) | `plan_dock_widths` (3 positional args), the constants | The new parameter defaults to the expanded rule; the expanded branch (incl. the infeasible `(150, 200)` result) is preserved bit-for-bit; the constants' **values** are unchanged (`WATCHLIST_COLLAPSED_WIDTH` is purely additive) |
| `tests/test_watchlist.py` | `watchlist_max_width`, `clamp_watchlist_width` | The delegation preserves the expanded formula exactly |
| `tests/test_dock_widths_d17.py` | `_apply_dock_widths`, the drag hook, `resizeEvent`, the persistence re-clamp | Drives it with the watchlist **expanded**; the 150px minimum, the drag enforcement and the persistence legs are the **expanded** state |
| `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py` | `_plan_dock_widths` / `plan_dock_widths`, `_apply_dock_widths` | Expanded; the B3 cross-clamp arithmetic is unchanged for a non-collapsed left |
| `tests/test_right_dock_d21.py` | `plan_dock_widths`, `_apply_dock_widths`, `watchlist_dock.width() >= WATCHLIST_MIN_WIDTH` | Expanded; the right dock's own model is untouched |
| `tests/test_dock_d18_region.py` | the **right** region's collapse (`portfolio_panel.is_collapsed`) | The right dock, not the watchlist |
| `tests/test_d10_d13_integration.py` | `_apply_dock_widths`, `clamp_watchlist_width`, `watchlist_max_width`, `WATCHLIST_MIN_WIDTH` | Expanded; the persistence clamp is expanded-only by definition |
| `tests/test_toolbar_scroll_d19.py` | the `CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH` sum | A constants sum used for D19 harness sizing; **no constant's value changes** |
| `tests/test_watchlist_columns_d21.py::test_D21_10_T01` | the panel's title-bar/label assertions | Boots **expanded** — exactly the state those assertions describe |
| `tests/test_d41_portfolio_dock.py`, `tests/test_d41_removal.py` | `dock_layout` constants, the right dock | Untouched surfaces |
| `tests/test_d24_popouts.py`, `tests/test_phase3_fixpass.py`, `tests/test_d24_alarm_full_chain.py`, `tests/test_d24_smoke_gate.py`, `tests/test_d24_9_popout_persistence.py`, `tests/test_d28_tick_burst_baseline.py` | boot a `MainWindow` (so `resizeEvent` → `_apply_dock_widths`, expanded) and drive the **load path** | D44 does not touch the load path, so the `ESC-050` fixed-size-stub defect class is **not** re-triggered |
| `tests/test_watchlist_d14_midrag.py`, `tests/test_d39_*`, `tests/test_d22*` (other cases) | the panel's data/search APIs | No D44 path changes them |

**RED→GREEN evidence Phase 1 must produce (runnable offscreen, no live TWS).**

- **The guard (`tests/test_dock_widths_collapsed_d44.py`) is RED at `0c4d478` for the right reason.** The
  guard drives the **existing** `set_collapsed(True)` API and asserts the **observable outcome**, referencing
  the new constant defensively (so an `ImportError` can never be mistaken for a behavioural RED). Pre-fix the
  collapsed dock stays at its expanded width (~220px, and ≥150 after the clamp) and the assertions fail on the
  **width** — the repo's own credibility rule (`docs/memory.md` 2026-10-05: "a regression guard is only
  credible if it fails on the pre-fix tree and passes post-fix").
- **GREEN after Phase 1:** collapse at a known `W` → `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`;
  after `win.resize(...)` + `qapp.processEvents()` → still the collapsed width; after
  `win._on_dock_drag_event()` + `qapp.processEvents()` → still the collapsed width; expand →
  `dock.width() == clamp(W)`; collapse-from-150 → expand restores 150; collapse-from-cap → expand restores the
  cap; `QSettings` holds **no** collapse key; `chart_area_w >= CHART_MIN_WIDTH` in both states; the dock is
  still `DockWidgetMovable | DockWidgetFloatable` while collapsed.
- **The bar suite:** the bar and its rotated-label widget exist and are visible while collapsed; the strip,
  the `+` and the column-header row are not; the bar's stylesheet carries the app palette; hovering/pressing
  flips the `active` property (via `set_button_active`) and the `[active="true"]` style differs from the idle
  style; clicking the bar expands.
- **Commands:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_dock_widths_collapsed_d44.py
  tests/test_watchlist_collapsed_bar_d44.py -v` for the focused run, then the **full** offscreen suite
  (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`) — the whole-suite gate is what catches an
  assertion invalidated in a file outside a task's `touches_files` (`ESC-055`'s own lesson).

**The invariant (restated so the enumeration is checkable by rule, not by inspection).**

> **Enumerate by call site of the changed entry point — not by the suites the design names.** For every
> production symbol this increment changes (`plan_dock_widths`, `plan_watchlist_width`,
> `clamp_watchlist_width`, `MainWindow._apply_dock_widths` / `::_plan_dock_widths` / `::_dock_widths_consistent`,
> `WatchlistPanel._on_header_toggled` / `::set_collapsed` / `::is_collapsed`), find **every** test that reaches
> it — **including tests that only *drive* it** (boot a `MainWindow`, trigger a `resizeEvent`, drag a dock,
> click the header button) — and classify each as **corrected with its cause** or **verified unchanged**.
> Every corrected suite rides in the **same phase** as the production change that invalidates it, and any test
> file whose assertions a change can invalidate belongs to that change's `touches_files` (or to a sibling
> task's) — the `ESC-055` ownership remedy.

---

## Assumptions

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A78`).

- **AP-D44-1 (the collapsed width is enforced by relaxing the minimum + a collapsed-aware clamp — not by
  `setMaximumWidth`/`setFixedWidth`).** A left dock's reachable width is decided by its **widget minimums**,
  not by `resizeDocks` alone: a Plan-verified offscreen probe (2026-10-16) held a dock at 78px when asked for
  30 because the title-bar widget's minimum was 40 and the content label's was 78; with every visible widget at
  30 the same call yielded exactly 30. The collapsed state therefore relaxes the panel's **and** the dock's
  minimum to `WATCHLIST_COLLAPSED_WIDTH` and restores `WATCHLIST_MIN_WIDTH` on expand — the D21.13 pattern.
- **AP-D44-2 (`_watchlist_width` keeps meaning "the expanded/requested width").** It is never assigned while
  collapsed, so it *is* the "width held immediately before collapsing" that `AC-D44.2` restores, and
  `closeEvent`'s `save_watchlist_width(self._settings, self._watchlist_width, …)` is unchanged. **Consequence
  (recorded, since A76 is silent on it):** a session that ends **collapsed** still persists the user's
  **expanded** width, so the next launch starts expanded at that width — the only choice consistent with "the
  app starts expanded" (see `FI-D44-3`).
- **AP-D44-3 (`AC-D44.5`'s measurable is scoped to the docked watchlist).** Journey 37's own precondition is
  "the Watchlist dock is visible and expanded on the left", and Qt does not lay a **floating** dock out in the
  dock area, so `resizeDocks`/the clamp govern the docked state. While floating, the collapse still swaps the
  visual and the bar remains clickable to expand (D44's edge-case wording: "the bar must still be clickable to
  expand"); the 30px pin is best-effort there. This is a faithful reading of the criterion's scope, recorded
  rather than assumed silently.
- **AP-D44-4 (the ±1px tolerance convention applies to inner measurements; the dock equality is asserted
  exactly).** `_apply_dock_widths` re-issues `resizeDocks` only when the delta exceeds 1px, and the D17 suite
  records that "a residual of at most 1px is expected and asserted with `+1`"
  (`tests/test_dock_widths_d17.py:17`–`:21`). The probe shows `resizeDocks([dock], [30])` yields exactly 30
  offscreen, so the guard asserts the **dock** equality directly and keeps `+1` for derived/inner values.
- **AP-D44-5 (`WATCHLIST_COLLAPSED_WIDTH` lives in `ui/dock_layout.py` and is aliased in
  `ui/watchlist_panel.py`).** The D44 correction record names `ui/dock_layout.py`; the alias follows the
  existing pattern for `WATCHLIST_MIN_WIDTH`/`CHART_MIN_WIDTH`/`DEFAULT_WATCHLIST_WIDTH` (`:93`–`:95`), and the
  cross-module agreement test is extended to cover it — so the duplicated-constant invariant stays honest.
- **AP-D44-6 (no new dependency, no new Qt module, no rendering-stack change).** The only new Qt touch is a
  `QWidget.paintEvent` + `QPainter.rotate`; `QPainter` and a custom `paintEvent` are already in the repo
  (`ui/visual_conventions.py:190`, `ui/candlestick_item.py:121`) and `rotate` is a standard painter transform
  on the already-imported `QtGui` module. The pyqtgraph chart stack is a **locked** decision (`docs/memory.md`,
  2026-10-16) and D44 does not touch it.
- **AP-D44-7 (test invocation and isolation).** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the
  `pytest` entry point has a stale shebang); any **non-pytest** probe that can reach a DB-writing path exports
  `DB_PATH` to a temp file; the new suites use a **per-test `QSettings` ini** (the D22 harness pattern) so the
  persisted width and the collapse state cannot leak between tests.
- **AP-D44-8 (the enumeration rule is applied, and each corrected suite rides with its cause).** The changed
  entry points are enumerated by call site (the *Verified unchanged* table above), every correction names its
  cause, and no correction is left to the reconciliation phase alone — this is the `ESC-050` rule plus
  `ESC-055`'s ownership remedy, which stays TASK_MANAGER-owned and is **not** absorbed here.
- **AP-D44-9 (the suite total moves).** Two suites are added, two extended and three corrected (four sites +
  one docstring), so any doc figure quoting a suite total must be **re-measured** (the `DOC-1` follow-up) —
  the requirement is *green with every assertion exact or corrected intent-preserving*, not count parity.

---

## Flagged Issues

Requirements I could not satisfy with the architecture **as written**, or decisions a Task Manager could not
have made without inventing architecture. Each is surfaced here (not filed): the Validator turns these into the
official `docs/plan_notes.md` escalation.

- **FI-D44-1 — the exact-equality measurables vs the repo's ±1px tolerance convention (reading proposed; no
  escalation needed if ratified).** `AC-D44.1` and `AC-D44.5` both phrase the outcome as exact equality
  (`watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`), while the repo's established convention tolerates a
  1px residual because `_apply_dock_widths` only re-issues a resize when the delta exceeds 1px
  (`tests/test_dock_widths_d17.py:17`–`:21`; the D17/D18 suites assert `<= cap + 1`). **Reading proposed:**
  assert the **dock** width exactly (Plan's offscreen probe yields exactly 30 once the widget minimums allow
  it) and keep the `+1` tolerance only for inner/derived measurements (`AP-D44-4`). The alternative — a strict
  `==` on every measurement — risks a **false RED** from a platform's 1px dock separator, which would make the
  guard untrustworthy. **Disposition proposed:** ratified as a measurement convention; no Requirements change
  (the *outcome* — "the bar is 30px and stays 30px" — is unchanged).
- **FI-D44-2 — `A78`'s "the dock's title-bar widget presents the bar" cannot be literal for a *full-height*
  bar (decision + evidence, not a reinterpretation).** Qt lays a left dock's title-bar widget out at the
  **top** of the dock, at the dock's full width and the widget's own `sizeHint` height — even when the dock has
  no content widget (Plan-verified offscreen probe, 2026-10-16: a `QSize(30, 120)` title bar occupied
  `QRect(0, 0, 30, 120)` with the content at `QRect(0, 120, 30, 780)`). A full-height vertical bar is
  therefore impossible **in the title-bar slot**. D44 splits the affordance (`S25`): the full-height bar is the
  dock's **content** (`panel.collapsed_bar`) and the title-bar slot carries a 30×28 handle
  (`panel.collapsed_handle`) that keeps the dock movable (DG37) and clickable to expand. The **outcome** fixed
  by `AC-D44.1`/`AC-D44.6` (a thin, clickable, app-palette bar that reads as a panel) is unchanged, and A78
  itself delegates the mechanism ("the widget/title-bar mechanism is an implementation choice"). Recorded so
  the split is not read as a silent narrowing; the recorded **fallback** is the bar-as-title-bar variant if the
  handle proves problematic in build.
- **FI-D44-3 — A76 does not say what width is persisted when the app is closed *while collapsed*
  (decision, recorded).** A76 fixes "not persisted; the app starts expanded" but is silent on the persisted
  **width** in that case. **Decided (`S27`, `AP-D44-2`):** the tracked **expanded** width is persisted (the
  `watchlist/width` key is unchanged and `_watchlist_width` is never overwritten while collapsed), so a restart
  starts expanded at the user's last expanded width. Persisting the applied 30px instead would make the next
  launch's **expanded** dock clamp to the 150px minimum — a silent loss of the user's width. An owner override
  would revise A76 and `S27`; the requirement's own outcome ("no collapse key exists; the app starts
  expanded") is satisfied either way.

---

## Correction record — for Task Manager / Build / Code Reviewer

The supersessions and the artifacts that must change (mirrors `### D44`'s correction record, `:3914`–`:3925`):

1. **`AC-D21.11.2` / `AC-D21.11.3`** — their collapsed-appearance clause ("the collapsed state still shows the
   button", struck per `VIS-D21.1`) is **superseded for the collapsed watchlist state**: the collapsed form is
   the **thin bar with rotated text**. `VIS-D21.1` still applies to genuinely hidden/off **buttons** elsewhere
   (D21.12 volume, D21.13 portfolio) and to the header button whenever it is shown. **`AC-D21.11.1`** is
   unchanged (one "Watchlist" label; duplicate dock title deleted); the **title-bar widget identity** is
   `header_bar` while **expanded** and `collapsed_handle` while **collapsed** — the swap A78 authorises.
2. **`AC-D13.1` / `AC-D17.2`'s 150px minimum** — now applies to the **expanded** watchlist only; while
   collapsed the width is `WATCHLIST_COLLAPSED_WIDTH` (~30px). `AC-D13.2`/`.3` and `AC-D17.1`/`.3`–`.6` (cap,
   persistence, drag enforcement, re-clamp) are **unchanged for the expanded state**. `AC-D21.11`'s
   "collapsed-width geometry" edge case is **now specified** by `AC-D44.1`/`AC-D44.5`.
3. **The `## Non-Goals` restyling bullet** — revised by the owner (2026-10-16) to permit **only** the D44
   collapsed-bar styling, in the **app palette** (`#141822` / `#232938` / `#cbd5e1`). The mockup's white
   rounded pill is explicitly **not** the target.
4. **Task Manager:** write the Phase-1 work items against `AC-D44.1`–`AC-D44.8` and the revised
   `AC-D21.11.2`/`.3` + the revised 150px-minimum scope; the per-file map above **is** the `touches_files`
   partition, and the two shared files (`ui/main_window.py`, `tests/test_watchlist_columns_d21.py`) force the
   two file-group pairs into **different waves** (the apply path before the wiring; the width-leg correction
   before the appearance-leg correction). The pure rule (`ui/dock_layout.py`) must land **before** its
   consumers, and the bar widget **before** the `MainWindow` wiring. Each corrected suite must be owned by the
   file-group that changes the behaviour it asserts (the `ESC-055` remedy) — do **not** defer the corrections to
   the reconciliation phase. Phase 2 adds no production edit.
5. **Build:** add `WATCHLIST_COLLAPSED_WIDTH` to `ui/dock_layout.py` and keep `CHART_MIN_WIDTH` in lockstep
   with `ui/watchlist_panel.py` (the documented invariant); make the collapsed width honoured by the **single**
   apply entry point in **both** branches, with the minimum-width relaxation + deferred re-apply; add the
   rotated-text bar widget in the app palette (with the title-bar handle) and wire click-to-expand to restore
   the tracked previous width; hide the header strip / `+` / column-header row while collapsed. **Correct (do
   not merely weaken)** the four named sites + the docstring, and add the two new suites. **Demonstrate the
   guard is RED at `0c4d478`** — the collapsed dock staying at ~220px / the 150px minimum, **not** an
   `ImportError` — and GREEN after, with the **full** offscreen suite green.
6. **Code Reviewer:** independently verify (a) the collapsed width **survives** a real `resizeEvent` **and** a
   drag-event path (the R66 defect class, the batch's core claim); (b) the palette matches the app and is
   **not** a white pill; (c) the **expanded** D13/D17/D18/D21.13 criteria and their suites are unaffected
   (run them, don't read them); (d) the dock is still **movable/floatable** while collapsed (DG37) and
   click-to-expand restores the **previous** width, re-clamped; (e) **no** collapse-state key is written
   (A76); (f) no corrected assertion was weakened, skipped or xfailed. Re-check `R66`/`R67`.
7. **Every future increment:** the **enumeration rule** — enumerate the assertions a change invalidates **by
   call site of the changed entry point, not by the suites the design names**, including suites that merely
   *drive* the changed path, and give the invalidated test files a home in `touches_files` (the `ESC-050` rule
   + `ESC-055`'s ownership remedy; D42's two under-counts and `ESC-055`'s recurrence are the recorded
   precedents).

---

## Incidentally affected (noted, not absorbed)

- **`ESC-055`** (`routed_to: TASK_MANAGER`, open, `nice-to-have`) — the D42/ESC-050 enumeration rule's
  ownership remedy. D44 **applies** the rule (`AP-D44-8`) but does not absorb or close the escalation; it
  belongs to Task Manager.
- **`Q54`** (D44's owner-confirmation item) — **answered 2026-10-16** with recorded defaults A75–A77 and
  surfaced to the owner as a non-blocking confirmation; no blocking question exists, so this run proceeds. An
  owner override would revise `AC-D44.1`/`.4`/`.7` + `A75`–`A77` + `S23`/`S26`/`S27`.
- **`DOC-1`** (any doc figure quoting a suite total) goes stale again because two suites are added and two
  extended; the owner/Analyst follow-up, not a Build task (`AP-D44-9`).
- **Line-number drift:** `docs/requirements/requirements.md` and this pair cite line numbers that a
  `ui/main_window.py` edit invalidates (the file is edited often — `docs/memory.md`). Symbols are the primary
  pointer; every line reference in these proposals is **indicative only**.
- Nothing in D44 touches the chart renderer, the load path, the planner, the bar cache, the alarms, the
  drawings/studies, the orders machinery, the D41 removals, or the D42/D43 data paths.

Status: READY_FOR_VALIDATION
