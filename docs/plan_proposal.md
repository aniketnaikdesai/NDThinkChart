# Implementation Plan Proposal — NDThinkChart Batch 14 (D20: toolbar scrollbar lane)

> **Scope.** An *incremental* plan on top of the **already-built, green D1–D19** system
> (D1–D19 built at commit `4d8952a`; the D19 toolbar scroll/elide wrapper is in place and green).
> D1–D19 are **frozen** and are **not** re-planned. This is an **existing-repo** run:
> `requirements.md` contains the marker sentence `This is an existing repository.` and a Current
> Tech Stack; **PyQt6 + pyqtgraph is a hard constraint**. No stack change, no schema change, no new
> dependency, no new external integration, and no live-order-path change. Items are labelled
> `[existing]`, `[new]`, or `[new/changed]`.
>
> **Companion architecture:** `docs/architecture_proposal.md` (Codebase Summary, tech-stack rows,
> system components, data model, integration points, non-functional approach, risks).
> **Requirements:** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D20 / Journey 21 /
> `AC-D20.1`–`AC-D20.6`; A39–A40; R35–R36; B7–B8 answered 2026-10-06; DG29–DG30).
>
> **What D20 is.** The D19 wrapper pins both the toolbar widget and the `ToolbarScroll`
> `QScrollArea` to `setFixedHeight(36)` (`ui/main_window.py:102`, `:233`); the `QScrollArea` lays
> its horizontal scrollbar out inside that same 36px and shrinks the viewport, so the toolbar label
> descenders are clipped / covered. **B7 (user-confirmed):** keep the **content row at ~36px** and
> give the horizontal scrollbar its **own reserved lane below**, so the **total strip is ~50–52px**
> (not ~60px); this supersedes/relaxes `AC-D19.4`'s `<= ~40px` bound to a ~52px container bound.
> **B8 (user-confirmed):** **reserve the lane** and show the scrollbar **as-needed** (only on
> overflow), never overlapping the labels; the strip height stays stable in both states.
>
> **Chosen mechanism (RC-D20-1).** The strip height is **derived at construction**:
> `TOOLBAR_CONTENT_HEIGHT (36) + toolbar_scroll.horizontalScrollBar().sizeHint().height()`. Measured
> offscreen 2026-10-06: extent **18px → strip 54px, viewport 36px**, scrollbar mapped to y = 36
> (`>= toolbar.height()`); the requirement's `~50–52px` is the **macOS** figure (extent ~16px →
> 52px). This makes the viewport equal the content row whenever the scrollbar is shown, so the lane
> sits **entirely below** the content on every platform. The literal-52 variant is **not** used
> (offscreen it leaves a 34px viewport and a 2px lane overlap — RC-D20-1).

---

## Coverage Map

| Requirement / journey / AC | What it demands | Phase | Verdict |
|---|---|---|---|
| **D20** — toolbar label descenders clipped by the horizontal scrollbar | Increase the strip height so the scrollbar no longer overlaps the labels | 1 (implement) | Covered |
| `AC-D20.1` — labels fully readable; no descender clipped by the scrollbar | Every label's glyphs (incl. descenders) fully visible; no intersection with the scrollbar; single row, in both scrollbar states | 1 (implement) + 2 (assert) | Covered |
| `AC-D20.2` — height supersession (~52px total, content row ~36px) | Container = content row (36px) + reserved lane = the scrollbar's own extent (offscreen 54px; macOS ~52px, the `~50–52px` figure); content widget 36px; reserved lane below; `AC-D19.4`'s `<= ~40px` explicitly superseded | 1 (implement) + 2 (assert) | Covered (macOS figure; derived relation asserted) |
| `AC-D20.3` — scrollbar as-needed in its reserved lane (B8) | Wide → hidden but strip height unchanged; narrow → shown in the lane below, never overlapping | 1 (implement) + 2 (assert) | Covered |
| `AC-D20.4` — D19 behaviour preserved | Narrow → horizontal scroll range `> 0`, all controls reachable; wide → all directly visible | 2 (assert) / 1 (enable) | Covered |
| `AC-D20.5` — single row, no wrap; stays inside the central widget | Content stays one row; not moved to a `QMainWindow` toolbar area; only the scrollbar occupies the lane | 1 (implement) + 2 (assert) | Covered |
| `AC-D20.6` — D17/D18 unaffected; regression | D17/D18 hold in a toolbar-visible window; chart minimum preserved; suite green; the D19 height assertions updated in lockstep | 2 (lockstep) + 3 (regression) | Covered |
| Journey 21 — read the toolbar labels without the scrollbar covering them | End-to-end real-app behaviour (narrow/wide, scroll, labels readable) | 1 + 2 + 3 | Covered |
| A39 — D20 target (content ~36px + reserved lane, ~52px total; as-needed) | The confirmed target | 1 | Covered |
| A40 — D17/D18 unaffected (vertical-only change) | Horizontal dock model untouched | 1 + 3 | Covered |
| R35 (chart vertical space) | Minimal height change (~52px, not ~60px) | 1 | Covered |
| R36 (D19 height assertions left stale) | Update `tests/test_toolbar_scroll_d19.py` height assertions in lockstep | 2 | Covered |
| DG29 / DG30 | Wrapper height has no lane for the scrollbar; `AC-D19.4` bound must be explicitly superseded | 1 (DG29) / 2 (DG30 lockstep) | Covered |
| `AC-D19.4` (superseded clause) | The `<= ~40px` bound is relaxed to the derived container height (offscreen 54px; macOS ~52px); the D19 reachability intent is preserved | 1 (relax) + 2 (lockstep) | Covered (recorded supersession, not a silent reopen) |
| D1–D19 | Frozen, re-affirmed; not re-planned | — | Covered |

No requirement is narrowed, reinterpreted, or left unsatisfied. The one supersession
(`AC-D19.4`'s height bound) is **recorded on `AC-D19.4`** by the Requirements Analyst and is not a
silent change.

---

## Phases

Each phase is a milestone, coarser than Task Manager's per-task decomposition. Files touched are
listed so Task Manager can populate `touches_files` and Build can schedule waves without file
overlap.

### Phase 1 — Reserve the scrollbar lane in the D19 wrapper `[new/changed]`

- **Goal:** give the horizontal scrollbar its **own reserved lane entirely below** the ~36px toolbar
  content row so it never overlaps or clips the labels, keeping the content a single ~36px row and
  the D19 scroll/elide reachability intact (B7/B8).
- **Deliverables (`ui/main_window.py`):**
  - Keep `toolbar.setFixedHeight(36)` **unchanged** (the content row does not grow — B7); introduce
    `TOOLBAR_CONTENT_HEIGHT = 36` as the single named source of truth.
  - **Change the D19 wrapper height from the literal 36px to the derived strip height**
    `TOOLBAR_CONTENT_HEIGHT + toolbar_scroll.horizontalScrollBar().sizeHint().height()` (the 36px
    content row + the scrollbar's own reserved lane). Measured offscreen 2026-10-06:
    `sizeHint().height()` = 18px → strip **54px**, viewport **36px**; macOS extent ~16px → ~52px
    (the requirement's `~50–52px`). The literal `52` default is **not** used (RC-D20-1).
  - Keep the wrapper's `NoFrame`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, and
    vertical `ScrollBarAlwaysOff` **unchanged** (the lane is reserved by the wrapper's fixed height;
    the scrollbar is shown only on overflow — B8).
  - **Do not** grow the content row, move the toolbar to a `QMainWindow` toolbar area, or change any
    control/signal wiring. Keep `conn_badge` inside the scroll content.
  - **Optional cosmetic:** style the `ToolbarScroll` background to match the strip (`#101218`) so
    the reserved lane is not a differently-coloured band. Not required by any AC.
  - **Do not touch** `ui/dock_layout.py`, `_chart_area_width`, `_apply_dock_widths`, the cap
    constants, or the single right-dock region (A40/B6).
- **Requirements / journeys covered:** D20; `AC-D20.1`, `AC-D20.2`, `AC-D20.3`, `AC-D20.5`
  (implementation); enables `AC-D20.4`, `AC-D20.6`; Journey 21; A39/A40; DG29; R35; the recorded
  `AC-D19.4` supersession.
- **Dependencies on earlier phases:** none (a single self-contained change in
  `ui/main_window.py`).
- **Exit condition:** with the toolbar visible, `toolbar.height() == TOOLBAR_CONTENT_HEIGHT (36)`,
  `wrapper.height() == toolbar.height() + wrapper.horizontalScrollBar().sizeHint().height()`
  (offscreen 54px), and when the scrollbar is shown the viewport `>= toolbar.height()` (offscreen
  36px) with the scrollbar **mapped below** the content
  (`horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()`); and
  `centralWidget().minimumSizeHint().width() <= 750px` (the D19 benefit is unchanged — only the
  wrapper's height changed).

### Phase 2 — Update D19 height assertions + add D20 legibility/lane tests `[new/changed]`

- **Goal:** make the suite assert the D20 outcome (labels unclipped, reserved lane, as-needed
  scrollbar) and update the D19 height assertions in lockstep so D19 and D20 do not contradict
  (`AC-D20.6` / R36).
- **Deliverables (tests):**
  - `tests/test_toolbar_scroll_d19.py::T53-T04` (RC-D20-3 lockstep): replace the container-height
    assertions with the **derived relation** —
    `wrapper.height() == toolbar.height() + wrapper.horizontalScrollBar().sizeHint().height()`
    (offscreen 54px) — and replace `minimumHeight() == 36 and maximumHeight() == 36` with
    `wrapper.minimumHeight() == wrapper.height() and wrapper.maximumHeight() == wrapper.height()`
    (the fixed height is preserved); assert the **content widget** is
    `TOOLBAR_CONTENT_HEIGHT (36)` explicitly.
  - `tests/test_toolbar_scroll_d19.py::T53-T02`: keep the content-row bound but make it explicit
    that `toolbar.height() <= 40` bounds the **content row** (36px), not the container.
  - Add D20 assertions (in `tests/test_toolbar_scroll_d19.py` or a new disjoint
    `tests/test_toolbar_d20.py`):
    - `AC-D20.1`: for every toolbar `QLabel`/button text, the glyph bounding rect lies fully within
      the visible content area and does **not** intersect the horizontal scrollbar's lane —
      asserted in **both** the overflow (scrollbar shown) and non-overflow (scrollbar hidden)
      states. The lane/overlap form uses a **mapped** comparison (RC-D20-2): when the scrollbar is
      shown, `wrapper.viewport().height() >= toolbar.height()` **and**
      `wrapper.horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()`
      (measured **False** at the literal 52, **True** at the derived 54). Do **not** use
      `geometry()` — offscreen `geometry()` reports `QRect(0, 0, …, 18)` (top = 0), which would fail
      at every height.
    - `AC-D20.2`: container height equals
      `toolbar.height() + wrapper.horizontalScrollBar().sizeHint().height()` (the derived relation;
      offscreen 54px) and is `< 60px` (R35 budget); content widget height is `36`; the reserved lane
      equals the scrollbar's extent and sits below the content. **No hard `[50, 52]` bound** — the
      requirement's `~50–52px` is the macOS figure (RC-D20-1 direction a).
    - `AC-D20.3`: wide → `horizontalScrollBar().isVisible()` is `False` and the strip height is
      **unchanged** (still the derived height); narrow → it is `True` and its **mapped** lane sits
      below the content row (`mapTo(...).y() >= toolbar.height()`).
    - `AC-D20.4`: narrow → `wrapper.horizontalScrollBar().maximum() > 0` and every control remains a
      descendant of the scroll content; wide → every control is within the viewport.
    - `AC-D20.5`: the content stays a single row and inside the central widget (`addToolBar` is not
      used).
  - **Pre-fix evidence (R36 discriminator):** run the **corrected** assertions against the
    **pre-Phase-1 tree** (the D19 wrapper fixed at 36px, e.g. a temporary worktree/stash) and record
    that they **fail** there — `36 == 36 + 18` is False, `viewport 18 >= toolbar 36` is False,
    `mapTo(...).y() == 18 >= 36` is False — then record them **passing** after Phase 1 (54px).
- **Requirements / journeys covered:** `AC-D20.1`–`AC-D20.5` (assertions), `AC-D20.6` (D19 height
  assertions updated in lockstep); Journey 21; DG30; R36.
- **Dependencies on earlier phases:** Phase 1 (the new container height must exist for the
  pass-after assertions; the pre-fix red is captured against the pre-Phase-1 tree).
- **Exit condition:** `tests/test_toolbar_scroll_d19.py` no longer asserts a 36px container (it
  asserts the derived relation); the D20 assertions pass with the scrollbar both hidden and shown;
  the pre-fix red and post-fix green are both recorded.

### Phase 3 — Regression + real-app verification `[new/changed]`

- **Goal:** prove no D1–D19 regression and confirm the fix in the real dev build (R35 / R34-style).
- **Deliverables:** no production change expected. Re-run the full offscreen suite; re-confirm the
  D17/D18 criteria in a toolbar-visible window (only vertical space changed — A40); record a manual
  `python main.py` check that the toolbar labels read clearly with the scrollbar **hidden** (wide)
  and **shown** (narrow), with the strip height stable in both states (offscreen 54px; ~52px on
  macOS).
- **Requirements / journeys covered:** `AC-D20.6`; R35; global acceptance criteria (full suite
  green; no live-TWS test).
- **Dependencies on earlier phases:** Phases 1–2.
- **Exit condition:** `QT_QPA_PLATFORM=offscreen python -m pytest tests/` is green with no test
  connecting to live TWS or transmitting an order (Q9); the D17/D18 criteria hold in a
  toolbar-visible window; the manual dev-build check is recorded. Per project memory, confirm any
  intermittent failure with a clean full-suite run before treating it as a regression (shared
  test-DB / collection-order noise).

---

## Files Touched / `touches_files` Notes

The Task Manager must add a **`touches_files`** field to every task so Build's Lead can dispatch
non-conflicting tasks in parallel up to `max_parallel_tasks` (default 4; optional user-owned
`docs/build/build_config.json`). The Lead is the sole writer of task status.

| File | Phase | Consequence |
|---|---|---|
| `ui/main_window.py` | 1 | Single production change (wrapper height 36 → derived `36 + scrollbar extent`; content row stays 36px). One task; serial with any other `main_window.py` task (none in this batch) |
| `tests/test_toolbar_scroll_d19.py` | 2 | `T53-T04` container-height assertions updated to the derived relation; `T53-T02` content-row bound made explicit; D20 assertions may be added here. Serial per file |
| `tests/test_toolbar_d20.py` (optional, new) | 2 | D20 legibility / reserved-lane / as-needed assertions; disjoint from `test_toolbar_scroll_d19.py` and may parallelise |
| `ui/dock_layout.py`, `ui/watchlist_panel.py` | — | **Not touched** (A40/B6 keep the width model and cap) |
| D17/D18 harnesses (`tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`) | — | **Not touched** — they assert widths/visibility, not heights, so D20's vertical change does not affect them (A40) |

Practical rule: Phase 1's `ui/main_window.py` change is the only production edit and is
self-contained. Phase 2's test updates are disjoint files and **may parallelise**. Phase 3 adds no
file. The one ordering constraint is that Phase 2's pass-after assertions depend on Phase 1; the
pre-fix red evidence is captured against the pre-Phase-1 tree. If the D20 assertions are added to
`tests/test_toolbar_scroll_d19.py`, they must be in the **same** task as the `T53-T04` update
(same file — serial).

---

## Assumptions

Plan-level assumptions not already captured in `requirements.md`'s Assumptions Log (A39/A40 already
record the B7/B8 target and that D17/D18 are unaffected).

- **PA-D20-1 (mechanism — derived wrapper height, not a new widget).** The D19 `QScrollArea`
  wrapper's fixed height is changed from the literal 36px to the **derived** value
  `TOOLBAR_CONTENT_HEIGHT + toolbar_scroll.horizontalScrollBar().sizeHint().height()` (36px content
  row + the scrollbar's own reserved lane; measured offscreen 54px, macOS ~52px); the toolbar
  content widget stays at 36px; `setWidgetResizable(False)` and the scrollbar policies are
  unchanged. A separate lane widget was passed over because the scrollbar belongs to the
  `QScrollArea` and is laid out inside it (see `architecture_proposal.md`, tech-stack row
  “Scrollbar-lane height / wrapper height”).
- **PA-D20-2 (lane is reserved by the fixed container height).** The lane stays reserved in both
  scrollbar states because the wrapper's height is fixed; only the scrollbar widget's visibility
  changes with overflow (B8's recorded interpretation).
- **PA-D20-3 (named height constant + derived strip).** `TOOLBAR_CONTENT_HEIGHT = 36` is defined
  once in `ui/main_window.py`; the strip height is **derived** as
  `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` — not a second hard-coded
  constant, because the scrollbar extent is a runtime style property. The test asserts the same
  derived relation and the same 36px content target, so code and test cannot drift (R36).
- **PA-D20-4 (D19 benefit preserved).** The wrapper's **height** change does not affect
  `centralWidget().minimumSizeHint().width()` (still ≈ 88px offscreen; `<= 750px` budget); the
  toolbar's ~1716px width remains inside the scroll content. No change to `ui/dock_layout.py`,
  `_chart_area_width`, or `_apply_dock_widths`.
- **PA-D20-5 (high-DPI / platform — the derivation is the mechanism, not a contingency).** The
  wrapper height is derived from `horizontalScrollBar().sizeHint().height()` (`content + extent`) on
  **every** platform, so a taller scrollbar (high-DPI / font scaling) automatically widens the lane
  and `viewport().height() >= toolbar.height()` still holds when the scrollbar is shown. Measured
  offscreen extent 18px → 54px; the requirement's `~50–52px` is the macOS figure (extent ~16px).
- **PA-D20-6 (pre-fix evidence method).** R36's discriminator is evidenced by running the updated
  height/overlap assertions against the pre-Phase-1 tree (D19 wrapper at 36px, via a temporary
  worktree/stash) and recording the red, then re-running after Phase 1.
- **PA-D20-7 (manual real-app check is a user step).** The real-macOS-window verification is a
  manual `python main.py` check recorded in the build log (scrollbar hidden and shown); the
  automated guard is the offscreen D20 assertions.
- **PA-D20-8 (regression policy unchanged).** Every fix ships with an offscreen check that fails
  before and passes after (Q8), and no automated test touches live TWS (Q9).

---

## Flagged Issues

**None.** `AC-D20.1`–`AC-D20.6`, Journey 21, A39–A40, R35–R36 and DG29–DG30 are satisfiable as
written; B7–B8 are answered and no blocking question remains. The requirement leaves the exact
mechanism to Plan/Build (B7/B8 name the target height and the lane behaviour, not the widget), and
raising the D19 wrapper's fixed height to the content row plus a reserved scrollbar lane satisfies
`AC-D20.1`–`AC-D20.3` while preserving D19's scroll/elide reachability (`AC-D20.4`) and the D17/D18
horizontal model (`AC-D20.6`, A40). The one recorded supersession — `AC-D19.4`'s `<= ~40px` height
bound relaxed to the derived container height (offscreen 54px; macOS ~52px) — is already recorded by
the Requirements Analyst on `AC-D19.4` and is handled in lockstep in Phase 2 (R36/DG30); it is not a
silent reopen. The only non-blocking implementation nuance — how to assert “no label descender is
clipped” — is a test method (label bounding rects plus the **mapped** lane comparison
`mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()`, **not** `geometry()`), captured in Phase 2
and PA-D20-5, not a requirements gap. The offscreen scrollbar extent (18px → 54px strip) versus the
requirement's macOS `~50–52px` figure is a **platform fact the plan accommodates** by asserting the
derived relation (RC-D20-1 direction a); it is not a requirement defect and no
`ESCALATED_TO_REQUIREMENTS` entry is warranted.

---

## Revision — validation retry 1 (RC-D20-1/2/3)

`docs/plan_review.md` returned `CHANGES_REQUIRED` (retry 0 of 3). This revision picks **one**
mechanism and makes every height reference and assertion agree:

- **RC-D20-1 — resolved by direction (a):** the wrapper's fixed height is the **derived**
  `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` (offscreen 18px extent →
  **54px**, viewport **36px**; macOS ~16px → ~52px, the requirement's `~50–52px`). The literal 52
  default is dropped. Phase 1's deliverable and exit condition, the Tech Stack Decisions row,
  PA-D20-1 / PA-D20-3 / PA-D20-5, and the Phase 2 container assertion all now state the same derived
  relation.
- **RC-D20-2 — resolved:** the lane assertion uses the **mapped** form
  `horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()` (measured False at
  the literal 52, True at the derived 54) plus `viewport().height() >= toolbar.height()`;
  `geometry()` is explicitly disallowed (offscreen it reports `top == 0`).
- **RC-D20-3 — resolved:** Phase 2 carries **no** hard `[50, 52]` bound; `AC-D20.2` asserts the
  derived relation and `< 60px` (R35). The R36 discriminator is expressed against the corrected
  assertions (`36 == 36 + 18` False; `viewport 18 >= toolbar 36` False; mapped `18 >= 36` False
  pre-fix — all pass at the derived 54 post-fix). The D19 lockstep update of `T53-T04` (derived
  height; `min/max == height()`) and `T53-T02` (`<= 40`, content row) is retained.

D1–D19 are not re-planned; `AC-D20.1`–`AC-D20.6`, Journey 21, A39–A40, R35–R36 and DG29–DG30 are
unchanged and satisfied as written.

---

Status: READY_FOR_VALIDATION
