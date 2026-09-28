# Plan Review — NDThinkChart Stabilization revision (ESC-002 / ESC-003 / ESC-006 / ESC-007)

## Review Status
Status: APPROVED

## Validation Summary
Validated **revision 2** of `docs/plan_proposal.md` + `docs/architecture_proposal.md`
(`Status: READY_FOR_VALIDATION`) against `docs/requirements/requirements.md`
(`Status: READY_FOR_PLAN`, settled 2026-09-27), reading the source under question
directly (`ui/chart_mouse_router.py`, `tests/test_chart_mouse_router.py`,
`ui/chart_panel.py`, `tests/test_volume_linear.py`,
`docs/code_review/escalations.md` ESC-002/003/006/007, `docs/requirements` D2/D3/D8/D10/D11,
the Assumptions Log A22–A26). This is **validation pass 2** (`plan_validator_retries: 1`
of 3); pass 1 returned `CHANGES_REQUIRED` with RC-1…RC-4.

Revision 2 addresses **every** item from pass 1, and the two requirements-rooted
problems (RG-002, RG-003) are now **resolved in `requirements.md`** and consumed as
settled text rather than flagged assumptions. The canonical `docs/architecture.md` and
`docs/plan.md` have been rewritten with the validated content and marked
`READY_FOR_TASK_MANAGER`.

## Verdict on the previously-required changes
| RC | Item | Verdict |
|---|---|---|
| **RC-1** | Nice-number section single, self-consistent, reproduces confirmed set + examples, old list fixture-only, `(0) == 10_000 → 100` noted | **Resolved** |
| **RC-2** | Revised D2/Q33 carried: Y-axis lane, grey pill/white text, tick overlap permitted; inside-plot wording superseded; dock-open visibility retained as required AC + independent CR verification; `AC-D11.4` re-scoped to label-vs-label | **Resolved** |
| **RC-3** | `_active_mode` derivation/synchronisation explicit and sufficient for the five preserved router tests | **Resolved** |
| **RC-4** | D10 affordance corrected to checkable text label `Volume`; `view_mouse_click` in `DRAWING` documented | **Resolved** |

### RC-1 — ESC-003 nice-number section (resolved)
`architecture_proposal.md` §3 now defines **one** candidate family
**`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`AC-D8.1`, A24) and **one** formula
`nice_max = min { v in family, v >= 100 : v >= max_vol * 1.1 }`, with `max_vol == 0 → 100`.
Every worked example agrees with the formula, including the previously contradictory
cases: `1_050_000 → 1_500_000` (the `1.5` mantissa is now in the family) and
`10_500_000 → 15_000_000`; the `50_000_000 → 75_000_000` case is valid precisely because
the family keeps the `7.5` mantissa (a strict `{1,2,2.5,5}` set would overshoot to
`100M`, which `AC-D8.5` rejects). The original fixed list is retained **only as a test
fixture** and every member is a family member, so no retained fixture contradicts the
formula. §3.4 correctly flags that of `tests/test_volume_linear.py:57–61` **only**
`_nice_volume_max(0) == 10_000` is stale and becomes **`100`**; the `8_000`, `80_000`,
`2_200_000`, `1_050_000` assertions stay valid. The coverage bound is correct: worst
case is the `2.5 → 5` step, ratio `≈ 5/(1.1×2.5) ≈ 1.82 <= 2`, asserted only above the
`100` floor (PA-R8). **RC-1 closed.**

### RC-2 — D2/Q33 and `AC-D11.4` (resolved)
§5.1–§5.3 carry the re-opened D2: chip in the **Y-axis lane outside the plot**, right of
the plot’s vertical axis line (`x >= view_rect.right()`), **grey pill with white text**,
left-anchored `anchor=(0,0.5)`, **axis-tick-label overlap permitted** (no deconfliction
offset). The superseded Batch-1 inside-plot wording is explicitly retired (§5.5 rewrites
the canonical `architecture.md` row; the canonical file now reads it). **Dock-open
visibility** is retained as the required `AC-D2.1` + edge case with **independent Code
Reviewer verification after Build** (A25 carve-out) — the Batch-1 fix is *not* assumed to
still hold. `AC-D11.4` is re-scoped to **label-vs-label stacking inside the plot only**
(§5.4), with the chip lane-separated and `_update_inner_labels` unchanged. Phase **R2**
owns the work and names `test_crosshair_chip_renders_in_axis_lane`. **RC-2 closed.**

### RC-3 — `_active_mode` derivation (resolved)
§2.5 pins the mechanism: `drawing`/`alarm`/`zoom` become **properties** whose setters
call `_reconcile_mode_from_overlays()`, deriving `_active_mode` with precedence
**`DRAWING > ZOOMING > ALARM_PLACING > IDLE`** using defensive `getattr` probes (the test
`FakeOverlay` implements only `tool_active()`). Hot handlers dispatch only on
`_active_mode`; the `IDLE` dispatch keeps the existing `not drawing.tool_active()` guard
as a defensive tie-break. Walked through against `tests/test_chart_mouse_router.py:28–68`:
`router.drawing = FakeOverlay(tool_active=True)` derives `DRAWING`; the subsequent
`router.alarm = …` re-derives to `DRAWING`; `view_mouse_press` dispatches **drawing only**,
so `test_drawing_tool_blocks_alarm_press` passes **verbatim**; `test_alarm_press_wins_in_cursor_mode`
(tool inactive → `IDLE` → alarm first), `test_alarm_miss_falls_through_to_drawing`,
`test_click_prefers_alarm_then_drawing`, and `test_missing_overlays_are_safe` all pass.
The mechanism is explicit, complete, and adds `test_reconcile_mode_from_wired_overlays`.
**RC-3 closed.**

### RC-4 — D10 affordance + `view_mouse_click` in `DRAWING` (resolved)
§5.5 corrects the canonical D10 row to the checkable **text label `Volume`**
(Q31/A22/`AC-D10.1`), at the top left of the volume panel (bottom left of the price
chart, A23), **not** an eye icon; it notes the built control is `👁 Volume`
(`ui/chart_panel.py:250`) but that its user-facing affordance is the `Volume` label.
Phase 3 and the coverage matrix carry the correction. §2.3 documents the
`view_mouse_click`-in-`DRAWING` behaviour change (drawing only) with the rationale
(alarm mode is force-cleared whenever a drawing tool is armed, so alarm click is
unreachable in production wiring) and pins it with
`test_click_in_drawing_reaches_only_drawing`; `IDLE` click keeps
`test_click_prefers_alarm_then_drawing` intact. **RC-4 closed.**

## `AC-D3.7` / `AC-D3.8` / `AC-D3.9` — transition table totality
The transition table (`architecture_proposal.md` §2.4, carried verbatim into canonical
`docs/architecture.md`) covers all three:
- **`AC-D3.7` forward** — TR-4: magnifier during `DRAWING` cancels the drawing, discards
  the draft, enters `ZOOMING`; `test_zoom_during_draw_cancels_draw`.
- **`AC-D3.7` reverse** — TR-5: drawing tool during `ZOOMING` exits `ZOOMING` and
  activates the tool; `test_draw_blocked_during_zoom` (name retained per PA-R3, asserting
  the confirmed reverse rule).
- **`AC-D3.8`** — TR-6: alarm placement during `ZOOMING` exits `ZOOMING` and enters
  `ALARM_PLACING`; `test_alarm_placement_blocks_zoom`.
- **`AC-D3.9`** — **TR-9**: magnifier during `ALARM_PLACING` is **REFUSED** (mode
  unchanged, pending placement intact, status-bar hint, control left unchecked);
  `test_magnifier_refused_during_alarm_placement`. This is the cell that makes the table
  **total** for every `(mode, trigger)` pair the router exposes — including
  `ALARM_PLACING + magnifier → ALARM_PLACING`. TR-14/TR-15 keep `AC-D3.3`/`AC-D3.4`
  as sub-state resets rather than mode changes.
The table is declared total in §2.4 and no `(mode, trigger)` pair is left unspecified.

## Requirements Coverage
| Requirement / AC | Proposal treatment | Verdict |
|---|---|---|
| `AC-D3.7` forward (Q35 (a)) | TR-4 cancels/discards the draft, enters `ZOOMING` | Covered |
| `AC-D3.7` reverse (A26) | TR-5 exits zoom, activates tool | Covered |
| `AC-D3.8` | TR-6 exits zoom, enters `ALARM_PLACING` | Covered |
| `AC-D3.9` (Q36 (b)) | TR-9 refusal + status hint; `test_magnifier_refused_during_alarm_placement` | Covered |
| `AC-D3.3` / `AC-D3.4` | TR-14/TR-15 sub-state reset, mode retained | Covered |
| `AC-D8.1`–`AC-D8.5` (ESC-003/008, RG-002) | §3 pinned family, floor `100`, old list = fixture; `(0)→100` only stale edit | Covered |
| `AC-D8.6` / `AC-D8.7` (ESC-007) | §4 O(1) cached running max, only-widen; `auto_range=False` re-apply | Covered |
| D2 / `AC-D2.1`–`AC-D2.3` (Q33/A25) | R2: Y-axis lane, grey pill/white text, overlap permitted; independent CR dock-open verification | Covered |
| `AC-D11.4` (ESC-006) | §5.4 label-vs-label only; chip lane-separated | Covered |
| `AC-D10.1` (Q31/A22) | §5.5 canonical affordance = text label `Volume` | Covered |
| `AC-D14.4` (ESC-010) | TR-17 + Phase 4: symbol change also resets router mode to `IDLE` | Covered |
| `AC-D7.*`, `AC-D8.1`–`AC-D8.3`, `AC-D9.*`, D12, D13, D15 | Unchanged, re-affirmed | Covered |
| Global AC | Phase 5 offscreen suite green, no live-TWS traffic (Q8/Q9) | Covered |

## Parallel-build consequences
Adequately reflected and carried into the canonical `docs/architecture.md` and
`docs/plan.md`. The file map names `ui/chart_panel.py` as the serial hot file shared by
R1/R2/Phase 1/Phase 3, `ui/main_window.py` as serial between R1 and Phase 4, states R1
must be its own wave, and requires per-test-file serialisation. `touches_files` and
`docs/build/build_config.json` (`max_parallel_tasks`, default 4) are cited as the Task
Manager’s input and Build’s wave rule; the Lead is the sole writer of task status.
This is sufficient for a valid task graph. Code Reviewer writes no `task-graph.json`
field in any case.

## Plan-level assumptions (PA-R2…PA-R8)
All are implementation-detail assumptions; **none** requires a Requirements Analyst
decision or a Plan change:
- **PA-R2** (DRAWING ≡ tool_active) — reasonable, preserves widget-state sync.
- **PA-R3** (test name retained while asserting the confirmed reverse) — naming note.
- **PA-R4** (only-widen satisfies `AC-D8.6`) — explicitly permitted by the requirement’s
  “or the bound is explicitly documented” clause.
- **PA-R5** (old list fixture-only; only `(0)` changes) — requirement-backed
  (`AC-D8.4`/A24).
- **PA-R6** (chip pixel geometry) — the lane/style/overlap are requirements; the pad is
  detail.
- **PA-R7** (`zoom_refused` wiring + hint string) — the requirement mandates *a* hint,
  not the wiring/text.
- **PA-R8** (`<= 2` bound asserted only above the `100` floor) — resolves the literal
  tension between `AC-D8.4`’s tightness bound and its own required floor; transparent and
  consistent with A24.
- **PA-R1** is **RETIRED** (superseded by `AC-D3.9`).

## Requirements Escalations
None open. `docs/plan_notes.md` records:
- **RG-002** — **RESOLVED 2026-09-27** (family pinned to `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`,
  no `10K` floor, smallest value `100`; old list = fixture only).
- **RG-003** — **RESOLVED 2026-09-27** (Q36 option (b) → new `AC-D3.9`; TR-9 rewritten
  as a refusal; PA-R1 retired).
- **RG-001** — previously addressed 2026-09-20 (D13/D14 register restored); no action.

## Task Manager Readiness
**Yes.** `docs/plan.md` ends with `Status: READY_FOR_TASK_MANAGER`. The canonical
`docs/architecture.md` and `docs/plan.md` carry the validated router state machine +
transition table, the pinned nice-number family and live-ceiling statement, the D2/Q33
chip relocation, the `AC-D11.4` re-scope, the D10 affordance correction, and the
`touches_files`/`build_config.json` sequencing constraint. The Task Manager can produce
a valid task graph with per-task `touches_files`.

## Final Decision
Status: APPROVED
