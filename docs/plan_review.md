# Plan Review — NDThinkChart D20 (toolbar scrollbar lane)

## Review Status
Status: APPROVED

## Validation Summary
This is validation **pass 2 (retry 1 of 3)** for the **D20 increment**. It validates the revised
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md`
against `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-06 with
D20 / Journey 21 / `AC-D20.1`–`AC-D20.6`, A39–A40, R35–R36, DG29–DG30, B7–B8 answered). No
`Status: ESCALATED_TO_PLAN` entry exists in `docs/code_review/escalations.md`, so this is a normal
forward validation cycle, not an escalation round.

**Scope.** D20 — the D19 toolbar wrapper pins **both** the toolbar widget and its `ToolbarScroll`
`QScrollArea` to `setFixedHeight(36)` (`ui/main_window.py:102`, `:233`), so the horizontal
scrollbar is laid out inside that same 36px and covers the label descenders. The increment is
planned on top of the **as-built, green D1–D19** baseline (commit `4d8952a`). D1–D19 are frozen
and are **not** re-planned. Existing-repo mode (the marker sentence and Current Tech Stack are
present in `requirements.md`).

**Verdict.** The revision **genuinely resolves RC-D20-1, RC-D20-2 and RC-D20-3**. The proposal
now picks **one** mechanism — the **derived** strip height
`TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` — and every height reference,
assertion, and rationale agrees on it (Phase 1 deliverable + exit condition, Phase 2 assertions,
PA-D20-1/3/5, the Tech Stack Decisions row, and the architecture's Summary/Components/
Non-Functional/Risks). There is no remaining internal contradiction, no new architectural decision
is required, and Task Manager can decompose the plan without inventing architecture. Details under
*Required Changes* (now all closed) and *Requirements Coverage*.

**Independently verified against the live repository and the real offscreen `MainWindow`**
(2026-10-06; the repository is authoritative — the Validator re-ran the probe rather than trusting
the proposal's numbers):

- `ui/main_window.py:100–102` — `toolbar = QWidget(); toolbar.setObjectName("MainToolbar");
  toolbar.setFixedHeight(36)`; `:223–234` — `toolbar_scroll = QScrollArea()` (`objectName
  "ToolbarScroll"`, `NoFrame`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`,
  vertical `ScrollBarAlwaysOff`, `setFixedHeight(36)`), `toolbar_scroll.setWidget(toolbar)`;
  `:236–242` — the wrapper (not the bare toolbar) is `central`'s `layout.itemAt(0).widget()`.
  Exactly as the proposal states.
- `tests/test_toolbar_scroll_d19.py` — `T53-T02` asserts `toolbar.height() <= 40` (`:130`, `:156`);
  `T53-T04` asserts `wrapper.height() == 36` (`:199`) and `wrapper.minimumHeight() == 36 and
  wrapper.maximumHeight() == 36` (`:200`); `T53-T01` asserts `central.minimumSizeHint().width() <=
  750` and `itemAt(0)` is the `"ToolbarScroll"` `QScrollArea`. Exactly as the proposal states.
- **"Only one test asserts toolbar/chart height" — RE-CONFIRMED (2026-10-06).** A repo-wide sweep
  of `tests/**/*.py` for `.height()` / `minimumHeight` / `maximumHeight` finds toolbar/wrapper-height
  assertions **only** in `tests/test_toolbar_scroll_d19.py` (`:130`, `:156`, `:199`, `:200`). The
  other `.height()` hits are unrelated (`test_drawing_labels.py` label bboxes;
  `test_volume_toggle.py` `price_plot.height()`; `test_chart_dpi.py` `QImage`/viewport height). The
  D17/D18 harnesses (`test_dock_widths_d17/d18/d18_impl`, `test_dock_d18_region`, `test_dock_layout`)
  locate the toolbar/wrapper by objectName but assert **widths/visibility**, not heights. The
  baseline file is green (`4 passed`).
- **Graphify.** `graphify-out/graph.json` exists (refreshed 2026-10-06); the D19 wrapper node and
  the `ui/main_window.py` / `tests/test_toolbar_scroll_d19.py` symbols resolve. The proposal's
  Codebase Summary claims were re-confirmed against the current source.

**Validator offscreen probe (the real `MainWindow`, `QT_QPA_PLATFORM=offscreen`,
`IBApiClient.connect` monkeypatched; measured 2026-10-06):**

| Wrapper height | `hbar.sizeHint().height()` | `viewport().height()` shown | `viewport().height()` hidden | `mapTo(wrapper,0,0).y()` shown | `geometry().top()` | `centralWidget().minimumSizeHint().width()` |
|---|---|---|---|---|---|---|
| 36 (as-built) | 18 | **18** | 36 | 18 | 0 | 88 |
| 52 (literal-52 — **not adopted**) | 18 | **34** | 52 | 34 | 0 | 88 |
| **54 (`36 + extent`, adopted)** | 18 | **36** | 54 | **36** | 0 | **88** |

This confirms the proposal's revised arithmetic exactly: the offscreen scrollbar extent is **18px**
(not ~16px), so a literal 52px wrapper leaves a 34px viewport (2px short of the 36px content row)
and both `viewport().height() >= toolbar.height()` and `mapTo(...).y() >= toolbar.height()` are
**False**; the derived 54px makes both **True**. `geometry()` reports `top == 0` and is unusable,
as RC-D20-2 stated. `hbar.sizeHint().height()` is **18px already at construction** (verified
pre-show), so deriving the height at construction time is feasible. The D19 benefit is preserved:
`centralWidget().minimumSizeHint().width()` is **88** at both wrapper 36 and wrapper 54 (height does
not affect the horizontal minimum), and the narrow-size scroll range is `maximum() = 966 > 0`.

## Requirements Coverage
| Requirement / journey / AC | Proposal treatment | Verdict |
|---|---|---|
| D20 — descenders clipped by the horizontal scrollbar | Phase 1; architecture summary + components | Covered |
| `AC-D20.1` — labels fully readable; no descender clipped, both scrollbar states | Phase 2 assertion (glyph bbox + **mapped** lane; `viewport >= content` when shown) | Covered (assertion form corrected — RC-D20-2) |
| `AC-D20.2` — ~50–52px total, content row ~36px, lane below, `AC-D19.4` superseded | Phase 1 (derived height) + Phase 2 (derived relation + `< 60px`) | Covered (derived relation; `~50–52px` documented as the macOS figure — RC-D20-1 direction a) |
| `AC-D20.3` — scrollbar as-needed in its reserved lane (B8) | Phase 1 (policies kept) + Phase 2 assertion | Covered |
| `AC-D20.4` — D19 reachability preserved | Phase 1 enables; Phase 2 assertion | Covered |
| `AC-D20.5` — single row, no wrap, inside central widget | Phase 1 + Phase 2 assertion | Covered |
| `AC-D20.6` — D17/D18 unaffected; D19 height assertions updated in lockstep | Phase 2 (`T53-T02`/`T53-T04`) + Phase 3 | Covered |
| Journey 21 — read labels without the scrollbar covering them | Phases 1–3 | Covered |
| A39/A40 — confirmed target; D17/D18 unaffected | Phase 1; architecture | Covered |
| R35 (chart vertical space) / R36 (stale D19 height assertions) | Phase 1 / Phase 2 | Covered |
| DG29/DG30 — no lane; supersede `AC-D19.4` bound | Phase 1 / Phase 2 | Covered |
| `AC-D19.4` (superseded height clause) | Phase 1 relax + Phase 2 lockstep; recorded on `AC-D19.4` | Covered |
| D1–D19 | Frozen, re-affirmed; not re-planned | Covered |

No requirement is narrowed, reinterpreted, or removed. The one supersession (`AC-D19.4`'s
`<= ~40px` bound) is recorded on `AC-D19.4` by the Requirements Analyst and is not a silent change.

**Note on `AC-D20.2`'s literal measurable (`<= ~52px`).** The offscreen derived strip is 54px, 2px
above the `~52px` figure. This was the Validator-sanctioned **direction (a)** in the previous
review, and it is the user-confirmed intent (B7: "Content row 36px + scrollbar lane (~52px
total)"): the strip is the content row plus the scrollbar's own extent, and `~52px` is the macOS
figure (extent ~16px). The requirement writes the bound with `~` (approximate) and forbids only
"~60px"; the plan asserts the derived relation plus `< 60px` (R35) rather than a hard `[50, 52]`.
This is an accepted platform accommodation, not a requirements defect — no
`ESCALATED_TO_REQUIREMENTS` entry is warranted.

## Architecture Findings
- **Complete.** The proposal addresses tech stack (unchanged, with `[new]`/`[new/changed]`
  additions labelled), the component and its responsibility, relationships, data model,
  integrations, interfaces/boundaries, security (live-order path untouched; Q9), performance
  (O(1) layout change), high-DPI, operational constraints and risks — each with an explicit
  rationale in the Tech Stack Decisions table.
- **Internally consistent (RC-D20-1 resolved).** The Tech Stack Decisions row "Scrollbar-lane height
  / wrapper height" now states the wrapper is `TOOLBAR_CONTENT_HEIGHT +
  horizontalScrollBar().sizeHint().height()` (36px + extent; offscreen 54px, macOS ~52px), and that
  this makes the viewport `>= 36px` when shown — which the probe confirms (`viewport 36`,
  `mapTo 36`). PA-D20-5 no longer presents the derivation as a contradictory fallback; it is the
  chosen mechanism. The literal-52 variant appears only as an explicitly rejected alternative.
- **Consistent with the proposal (RC-D20-3 resolved).** Phase 2 carries **no** hard `[50, 52]`
  bound; it asserts the derived relation and `< 60px`. The R36 pre-fix-red/post-fix-green
  discriminator is expressed against the corrected assertions and matches the probe exactly
  (pre-fix wrapper 36: `36 == 36 + 18` False, `viewport 18 >= 36` False, `mapTo 18 >= 36` False;
  post-fix 54: all True). The D19 lockstep update of `T53-T04` (derived relation;
  `min/max == height()`) and `T53-T02` (`<= 40`, content row) is retained.
- **Mechanism preserves the prior decisions.** Keeping `toolbar.setFixedHeight(36)`, raising only
  the wrapper, keeping `NoFrame` / `setWidgetResizable(False)` / horizontal `ScrollBarAsNeeded` /
  vertical `ScrollBarAlwaysOff`, and not touching `ui/dock_layout.py` / `_apply_dock_widths` / the
  cap all agree. The D19 `widgetResizable(False)` central-minimum benefit is preserved (probe:
  `minimumSizeHint().width() == 88` at wrapper 54), and the D17/D18 dock behaviour is untouched
  (the change is vertical-only — A40).
- **Task-manager-completable — YES.** Every decision Task Manager needs is fixed: the wrapper
  class, the derived height formula and named constant, the policies, the insertion point, the
  objectNames, the content-row height, the assertion form (mapped, not `geometry()`), the pre-fix
  evidence method, and the recorded `AC-D19.4` supersession.

## Plan Findings
- **Phases are correctly structured.** Three ordered milestone phases (Phase 1 wrapper height;
  Phase 2 lockstep D19-height updates + D20 assertions; Phase 3 regression + real-app check), each
  with a goal, covered requirements/journeys, explicit dependencies, and an exit condition.
- **Coarse enough for decomposition.** Phases describe meaningful bodies of work, not individual
  tasks. No task-level dependency graph; no per-task test specification beyond naming the test
  files a verification phase naturally names.
- **Ordering is logical.** Phase 1 is a single self-contained production change; Phase 2's
  pass-after assertions depend on Phase 1 and capture the pre-fix red against the pre-Phase-1 tree;
  Phase 3 verifies. The one ordering constraint is stated.
- **`touches_files` sequencing is derivable.** Phase 1 touches only `ui/main_window.py`; Phase 2
  touches `tests/test_toolbar_scroll_d19.py` plus an optional disjoint `tests/test_toolbar_d20.py`;
  Phase 3 adds no file. If the D20 assertions live in `test_toolbar_scroll_d19.py`, they must share
  a task with the `T53-T04` update (same file — serial).
- **Assumptions are plan-level implementation details.** PA-D20-1…PA-D20-8 are implementation
  details, not requirements decisions; PA-D20-5 now states the derivation as the mechanism and is
  consistent with the measured 18px offscreen extent.
- **No Task Manager-level task breakdown** is present.
- **No scope drift.** D20 is the new clarified defect; D1–D19 are frozen. Nothing is added or
  removed.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + `ibapi` terminal; `requirements.md` contains the
literal marker sentence `This is an existing repository.` and a Current Tech Stack. Checks:

- **Codebase Summary present and substantive — PASS.** `architecture_proposal.md` carries a
  *Codebase Summary (existing repository — D20 surface)* that inventories the toolbar construction
  (`:100–211`), the D19 wrapper (`:223–234`), the central-widget composition (`:236–242`), the
  D17/D18 width model (`_chart_area_width`, `_apply_dock_widths`, `ui/dock_layout.py`), the affected
  test (`tests/test_toolbar_scroll_d19.py`, with line ranges), the D17/D18 harnesses, the existing
  data models/tables, and integrations. It is detailed, source-verified, and not a placeholder.
- **Existing stack respected — PASS.** Tech Stack Decisions keeps Python 3.11+ / PyQt6 / pyqtgraph /
  `ibapi` / SQLite / pytest-qt as **unchanged** (`[existing]`), listed before the D20
  `[new]`/`[new/changed]` rows; "Changing the tech stack" is a Non-Goal. Nothing existing is
  replaced or deprecated. No new dependency.
- **Labels present — PASS.** System Components, Data Model, and Integration Points each mark every
  item `[existing]`, `[new]`, or `[new/changed]`.
- **Additive-only — PASS.** Existing components (`ui/dock_layout.py`, `_apply_dock_widths`, the width
  model, D1–D19 modules, the live-order path) are untouched; the only production change is the
  wrapper's height.
- **Codebase Summary consistent with the proposal — PASS.** Every component the proposal treats as
  `[existing]` (toolbar, wrapper, central widget, `dock_layout`, the harnesses, `QSettings`) appears
  in the Codebase Summary.
- **Graphify-based, stated, and validated — PASS.** The summary states graphify was used and every
  claim validated against source; the graph exists and the claims check out.

## Required Changes
**None.** All three required changes from the previous review are resolved:

- **RC-D20-1 — RESOLVED (direction a).** The wrapper's fixed height is the **derived**
  `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` (offscreen 18px extent →
  **54px**, viewport **36px**; macOS ~16px → ~52px). The literal 52 default is dropped. Phase 1's
  deliverable and exit condition, Phase 2's container assertion, PA-D20-1 / PA-D20-3 / PA-D20-5, the
  Tech Stack Decisions row, and the architecture sections all state the same derived relation. The
  probe confirms `viewport().height() >= toolbar.height()` holds at 54 and fails at 52.
- **RC-D20-2 — RESOLVED.** The lane assertion uses the **mapped** form
  `horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()` (probe: `False` at 52,
  `True` at 54) plus `viewport().height() >= toolbar.height()`; `geometry()` is explicitly
  disallowed (offscreen it reports `top == 0`).
- **RC-D20-3 — RESOLVED.** Phase 2 carries **no** hard `[50, 52]` bound; `AC-D20.2` asserts the
  derived relation and `< 60px` (R35). The R36 discriminator is expressed against the corrected
  assertions (probe-confirmed pre-fix red / post-fix green). The D19 lockstep update of `T53-T04`
  and `T53-T02` is retained.

No new required changes were introduced by the revision.

## Requirements Escalations
None. `AC-D20.1`–`AC-D20.6`, Journey 21, A39–A40, R35–R36 and DG29–DG30 are settled (B7–B8 answered
2026-10-06) and satisfiable as written; the offscreen scrollbar extent (18px) versus the macOS
`~50–52px` figure is a platform fact the **plan** accommodates by asserting the derived relation,
not a requirement defect. No `ESCALATED_TO_REQUIREMENTS` entry was added to `docs/plan_notes.md`.
(The historical `plan_notes.md` entries RG-001/RG-002/RG-003 and FI-D16-1/FI-D16-2 remain
resolved/addressed and are not reopened.)

## Task Manager Readiness
**Yes.** Task Manager can produce a valid task graph from the canonical artifacts without making a
new architectural decision: the wrapper-height formula and named constant, the scrollbar policies,
the insertion point, the objectNames, the content-row height, the mapped assertion form, the pre-fix
evidence method, and the `AC-D19.4` supersession are all fixed. The production change is a single
self-contained edit in `ui/main_window.py` (Phase 1); the test updates are disjoint files (Phase 2);
Phase 3 is regression + a manual real-app check.

The canonical artifacts are written: `docs/architecture.md` (D20 increment folded in) and
`docs/plan.md` (D20 phases, coverage map, `touches_files` sequencing, assumptions). `docs/plan.md`
carries the terminal `Status: READY_FOR_TASK_MANAGER` marker (written after this review).

## Final Decision
Status: APPROVED
