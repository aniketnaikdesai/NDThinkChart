# P10 code review log — final pass (2026-10-28)

Tier: **FULL** (phase-final passes are always full; additionally `ui/lwc_view.py`
is shared by P10-T1 and P10-T3 per `precheck.json` overlaps).
Ground truth consumed, not re-derived: `precheck.json` (0 fail_fast; scope
P10-T1..T5, all `done`; per-task tests 3/3, 3/3, 3/3, 2/2, 3/3) and
`test_verification.json` (verdict `pass`, exit 0 — full offscreen suite green,
so the archived-results gate and every P10 suite are green on the live tree).
`docs/build/failures.json` is `{}` (no blocked tasks). `git diff` reviewed
scoped to each task's `files_changed`; full files read only where the diff was
ambiguous. No test was weakened, no code was edited.

## Per-task verdicts

- **P10-T1 (handle gating, `ui/lwc_view.py` + `tests/test_p10_handle_gating.py`)** —
  PASS, no finding. `drawing_op` delegates every item through `drawing_item`
  (`lwc_view.py:1008`), so the single gate at `:981`
  (`if bool(selected) and not item["locked"]`) covers both AC paths; `locked`
  is stamped at `:953` before the gate reads it. Locked keeps `selected`
  highlight with `handles == []`; deselect clears.
- **P10-T2 (page initiation, `chart_assets/lwc/gestures.js` + `.test.js`)** —
  PASS with one finding (ESC-088). Body whole-move for all five kinds plus
  per-kind anchor addressing verified in the diff (`hitTest`/`bodyHit`,
  `point_index`/`body` plumbed to the `drag_drawing` signature in
  `routeDragDelta`); locked never-starts; commit via existing
  `reportDrawingUpdate → drawingUpdated → updated` close-out, cancel emits
  nothing. Node 48/48 green per result + gate.
- **P10-T3 (Python close-out, `ui/lwc_view.py` + `tests/test_p10_drag_commit.py`)** —
  PASS with one edge noted (ESC-089). `drag_drawing` refusal returns
  `dict(item)` before geometry/op-log mutation and publishes nothing;
  `_drawing_locked` reads `DrawingGroup.locked` per attempt (AP-P10-3) with a
  render-time `locked` fallback; empty-color normalisation resolves to the
  rendered color so the store write is a no-op on color.
- **P10-T4 (lock completion, `ui/main_window.py` + `tests/test_p10_lock_recolor.py`)** —
  PASS with one gap (ESC-087). Page `deleted` path and Del-button path both
  refuse locked deletes (row + geometry intact); the Del fallback correctly
  resolves `chart_panel.selected_drawing` (exists on `LwcChartView`,
  `lwc_view.py:1989`; `chart_panel` is an `LwcChartView` via
  `build_main_chart_view`). Color/style bypass the guard per Q69.
- **P10-T5 (gate)** — PASS, no finding. Four suites green with zero skips/
  xfails; prod diff confined to D50 (gestures.js, lwc_view.py, main_window.py
  + tests); no order-code tokens introduced (grep over the diff for
  placeOrder/cancelOrder/reqGlobalCancel/order registry: 0 hits outside
  historical comments); frozen signal/store signatures byte-identical.
  `precheck`'s `unconfirmed_file` warning is the declared-but-unwritten
  `docs/build/results/P10-T5.json` (verification-only task; the record lives
  at `_archive/wave186_P10-T5.json`, `task_id` present) — noted, no action.

## Findings (all routed via `escalations.json`)

- **RV-P10-1 → ESC-086 (PLAN, consistency, should-fix).** S-P10-2 says
  "per-move deltas flow through the existing `drag_drawing` validation" and the
  Tech-Stack table says "Python re-validates through `drag_drawing_item` before
  persist" (rejecting "page-computed payload persisted directly"). The shipped
  production path is the rejected shape: `chart.js::bindModules` binds
  `LwGestures` with 3 args (no `options.drag`), so `routeDragDelta` always
  returns false in production, and `commitDrag → reportDrawingUpdate →
  _on_page_drawing_updated → update_drawing` persists page-computed geometry
  with no Python `drag_drawing_item` pass. Behavior is correct (page
  `dragItem` in `primitives.js:494` mirrors the Python math incl. fib/measure
  recompute; suite green), so this is doc-vs-code drift, not a functional bug —
  but the decision record explicitly forbids the shipped shape, which invites a
  future latency-heavy "fix" or a false audit hit.
- **RV-P10-2 → ESC-087 (TASK_MANAGER, gap, should-fix).** D50.3 forbids locked
  delete unconditionally, but `DrawingGroupsDialog._delete_selected_drawings`
  (`ui/drawing_groups_dialog.py:228`) calls `DrawingStore.delete_drawings`
  directly with no lock check — a locked drawing is deletable from the groups
  dialog. P10-T4 met its ACs (scoped to page + Del-button paths) and cannot
  own `drawing_groups_dialog.py` within its footprint, so this needs a
  follow-up task (one invariant: every delete path refuses locked rows).
- **RV-P10-3 → ESC-088 (BUILD, bug, should-fix).** Orphaned in-flight drag in
  `gestures.js`: no pointer capture, and the move branch does not check
  `ev.buttons`, so a pointer-up outside the container leaves `drag` set with
  `moved=true`; subsequent hover keeps mutating the draft ghost button-free
  (`onPointerMove` drag branch), and the next pan-like press-travel commits the
  stale session via `commitDrag` (spurious persist + fan-out). `onPointerLeave`
  only acts in alarm mode; only a route change clears the drag.
- **RV-P10-4 → ESC-089 (BUILD, quality, nice-to-have).** `_on_page_drawing_updated`
  (`lwc_view.py:2498`) falls back to `""` when the drawing id is not in
  `_drawing_items`; `update_drawing(color="")` then writes `""` (only `None`
  means unchanged, `drawing_store.py:164`), clobbering the stored color —
  falsifying the "commit can never clobber" comment on the one path
  (delete-mid-drag race) the normalisation does not cover.
- **RV-P10-5 → ESC-090 (TASK_MANAGER, consistency, should-fix).** `usage.md:180`
  now asserts false behavior: "Right-click drawing → **Delete** (drawings are
  delete-only until D50 drag-editing lands)" — D50 has landed and no P10 task
  owned docs (`doc_required: false` throughout). Small docs follow-up owning
  `usage.md` (and `USAGE.txt` if per-batch coverage is wanted per the ESC-058
  convention): selection-gated handles, body/anchor drags, locked semantics.

## Standing checks

- **B.6 mock-endpoint scan: PASS.** `mock|fake|stub|simulat` hits in the
  reviewed diff exist only in `chart_assets/lwc/gestures.test.js` (test fakes
  at the boundary — allowed). No mocked/faked endpoint, client, service,
  server, API, or harness in production code; no production module imports a
  test double. The `options.drag` seam is unbound in production (DI for tests
  only), not a mock endpoint.
- **Escalation close-out: PRE-006 → addressed.** Re-verified, not taken on the
  worker's word: `task-graph.json` P10-T5 `status` is `done`; newest result
  `_archive/wave186_P10-T5.json` carries `task_id: "P10-T5"` (direct read);
  the corrupt `wave184_P10-T5.INVALID.json` is absent from disk; full suite
  green (covers `test_archived_results_carry_task_id`). The Q-58-style
  archive-key repair (task_id-carrying result + INVALID prune) is confirmed on
  the live tree. No other escalation is open (grep `"status": "open"` → only
  PRE-006 pre-flip).
- **Unattributed working-tree changes** (`ALARM_AND_DRAWING_CODE_REVIEW.txt`,
  `POPOUT_CHART_CODE_TRACE_REPORT.txt`): pre-existing owner-provided reports
  (D49/D50 inputs), untouched by P10 — noted, no action.
- **Observation, not escalated:** `build_main_chart_view`'s docstring
  (`main_window.py:182-188`) still describes pyqtgraph as the default engine,
  stale since P6-T13 (LWC-only baseline). Pre-existing prose outside every
  P10 hunk; suggest folding into a future prose sweep (ESC-067 pattern), not a
  P10 finding.

Status: REVIEW_COMPLETE

---

# P10 TM-round review (2026-10-28, 22:55 UTC) — T6, T7 + T2/T3 re-verify

Tier: **FULL** (phase-final passes are always full; the scoped slice also
contains size-M P10-T2, so the light-pass conditions fail regardless).
Ground truth consumed, not re-derived: `precheck.json` (0 fail_fast; scope
P10-T2, P10-T3, P10-T6, P10-T7, all `done`, no overlaps, no flags) and
`test_verification.json` (verdict `pass`, exit 0 — full offscreen suite
green). `docs/build/failures.json` is `{}` (no blocked tasks). `git diff`
and targeted greps reviewed scoped to each task's `files_changed`; full
files read only where the diff was ambiguous. No test was weakened, no code
was edited.

## Per-task verdicts

- **P10-T6 (dialog locked-delete refusal, `ui/drawing_groups_dialog.py` + `tests/test_p10_groups_dialog_lock.py`)** —
  PASS, no finding. `_delete_selected_drawings` now filters through
  `_locked_drawing_ids` (`:228-260`): `DrawingGroup.locked` read at the
  operation surface, ungrouped/unknown ids unlocked, lookup failure fails
  open, color/style paths bypass per Q69. Locked members survive with row +
  geometry intact; all-locked selection is a no-op (no delete, no reload,
  no fan-out). Mirrors `MainWindow._drawing_group_locked` exactly.
- **P10-T7 (D50 usage docs, `usage.md`)** — PASS, no finding. Drawing Tools
  section rewritten to shipped D50 behavior (select shows per-kind handles,
  deselect hides; body/handle drags with fib/measure recompute; locked
  no-handle + drag/delete refusal with color allowed; Esc cancel). The
  stale delete-only line is gone (grep 0 hits). `USAGE.txt` correctly
  untouched (pointer only, no per-batch section).
- **P10-T2 re-verify (verify-only per dispatch)** — PASS (48/48 node green
  per result + gate). No production change attempted or expected.
- **P10-T3 re-verify (verify-only per dispatch)** — PASS (3/3 green per
  result + gate). Worker's own result notes the ESC-089 guard is not in
  the tree — as dispatched.

## Escalation close-out (entry C)

- **ESC-087 → addressed.** Task graph gained P10-T6 (deps P10-T4); T6
  `done`; gate re-verified on the live tree (see T6 verdict above).
- **ESC-090 → addressed.** Task graph gained P10-T7 (deps P10-T6); T7
  `done`; docs re-verified on the live tree (see T7 verdict above).
- **ESC-086 → addressed.** `architecture.md`/`plan.md` changed since the
  final pass (commit `de01dfa`, record only) and the change is exactly
  what ESC-086 asked for: S-P10-2 restated (`architecture.md:6339,6425`;
  same restatement in `plan.md` D50.1 row) to record the shipped shape —
  page-side `primitives.js::dragItem` mirror (header at
  `primitives.js:484`, equivalence-pinned to the frozen
  `drag_drawing_item` plus per-kind suites) with the
  `page_geometry_payload` commit-time shape/bounds check as the recorded
  validation, `drag_drawing` as the lock-enforcing surface bound in
  tests/direct calls, and production `bindModules` passing no
  `options.drag`. Behavior unchanged, as the escalation prescribed.
- **ESC-088 → NOT resolved, left open.** T2 re-ran (`done`, wave188) but
  verify-only, so the fix was never attempted. Re-verified on the live
  tree: `onPointerMove` drag branch (`gestures.js:482`) still has no
  `ev.buttons`/pressure check, no `pointercancel` handler exists, and
  `onPointerLeave` (`:878`) still acts only in alarm-placing mode. The
  stale-commit hazard stands. Fresh rework routed as **ESC-091** (new
  `opened` timestamp re-arms `build_wave.py` dispatch, which only
  re-runs a task once per escalation opening; ESC-088 stays open as the
  original record).
- **ESC-089 → NOT resolved, left open.** T3 re-ran (`done`, wave189) but
  verify-only. Re-verified on the live tree: `_on_page_drawing_updated`
  (`lwc_view.py:2501-2513`) still emits `""` when the id is absent from
  `_drawing_items`, which `update_drawing` persists (only `None` means
  unchanged). The worker's own result confirms the guard is absent.
  Fresh rework routed as **ESC-092** (same dispatch rationale; ESC-089
  stays open as the original record).

## Findings routed this pass

- **RV-P10-6 → ESC-091 (BUILD, bug, should-fix).** Fresh dispatch vehicle
  for the ESC-088 orphaned in-flight drag: follow-up task owning
  `chart_assets/lwc/gestures.js` + `chart_assets/lwc/gestures.test.js`
  (buttons-held check in the move branch + leave/cancel abandon + node
  orphan-guard; T21/T23 suites must not weaken).
- **RV-P10-7 → ESC-092 (BUILD, quality, nice-to-have).** Fresh dispatch
  vehicle for the ESC-089 unknown-item color guard: follow-up task
  owning `ui/lwc_view.py` + `tests/test_p10_drag_commit.py` (early
  return / None-color on the unknown-item path + stored-color-untouched
  guard).

## Standing checks

- **B.6 mock-endpoint scan: PASS.** `mock|fake|stub|simulat` (case-insensitive)
  across the scoped diff: two hits, both benign prose — `gestures.js:36`
  comment naming "the node fake" (test boundary), `lwc_view.py:134`
  pre-existing "stub" comment. No mocked/faked endpoint, client, service,
  server, API, or harness in production code; no production module imports
  a test double.
- **Usage-doc gate: PASS.** The one user-facing behavior change in scope
  (locked-delete refusal reaching the groups dialog) is covered by T7's
  `usage.md` rewrite ("refuses drag and delete"); P10-T6 itself needed no
  separate doc (internal gate, `doc_required: false`).
- **Unattributed working-tree changes** (`precheck.json`): the two owner
  report `.txt` files (pre-existing D49/D50 inputs, noted in the final
  pass) plus `tests/test_p10_handle_gating.py`,
  `tests/test_p10_lock_recolor.py`, `ui/main_window.py` — the latter three
  are P10-T1/T4 files unchanged since the final review (clean per
  `git status`; attributed to their archived results, outside this
  incremental scope). No action.
- **Repeat-invariant rule:** no new per-case BUILD patch duplicates an
  existing invariant escalation; ESC-091/092 are fresh dispatch vehicles
  for two distinct, still-open defects, cross-referenced to ESC-088/089
  — not third patches on one rule.

# P10 rework close-out (2026-10-28)

Tier: **FULL** (phase-final close-out; reworked production paths re-read on
the live tree). Ground truth consumed, not re-derived: `precheck.json`
(0 fail_fast; scope P10-T2) and `test_verification.json` (verdict `pass`,
exit 0, full offscreen suite green). `docs/build/failures.json` is `{}`.
Scope per dispatch: the ESC-091/T2 pointer-capture guard in `gestures.js`,
the ESC-092/T3 unknown-item empty-color guard via the renderer-owned index
(no `data.db` import), and the Q-59 boundary restoration. No code edited.

## Verdicts (all re-verified on the live tree, not the workers' word)

- **ESC-091 / P10-T2 (gestures.js orphan-drag guard)** — FIXED. Move branch
  gated on `dragButtonHeld` (`buttons & 1` / `pressure`, `:504-505`, defined
  `:810-818`; synthetic node events without either field still move, so
  T21/T23 are intact); `pointerleave` abandons past `LEAVE_GRACE_MS` via
  `leaveDragTimer` (`:925-941`, separate from the alarm `leaveTimer`);
  `pointercancel` abandons immediately (`:946-963`, wired `:992`);
  non-hit `pointerdown` clears a stale session (`:471`); route change
  cancels (`:423`). My own run: `node --test
  chart_assets/lwc/gestures.test.js` → 52 passed / 0 failed (incl. the
  additive ESC-091 orphan suite: buttons-0 ignored, leave abandon, cancel
  abandon, stale-press clear).
- **ESC-092 / P10-T3 (unknown-item empty-color guard)** — FIXED.
  `_on_page_drawing_updated` (`lwc_view.py:2502-2531`): empty page color
  resolves to the rendered color when `current` is found; when `current`
  is None, the commit is dropped iff the id is in the renderer-owned
  `_stored_drawing_colors` (deleted-mid-drag / hidden-group race), else
  emitted with `""` (Q-20 pin: no stored row exists, `update_drawing`
  touches zero rows). My own run: `QT_QPA_PLATFORM=offscreen pytest
  tests/test_p10_drag_commit.py` → 5 passed (T31, T32 close-out,
  unknown-item-dropped, unknown-id-no-store-row-emits, T33).
- **Q-59 boundary restoration** — HOLDS. Commit `550ba8a` builds
  `_stored_drawing_colors` in `set_drawings` from delivered records
  (`:2692-2702`); `grep` over `ui/lwc_view.py` → 0 `data.db` / drawing-store
  references. The view never reads the DB; the color index is renderer-owned.
- **PRE-007 (malformed P10-T3 result)** — RESOLVED. Live
  `docs/build/results/P10-T3.json` carries `task_id: P10-T3` (ran
  23:24:17, 5 passed); archive `wave193_P10-T3.json` carries `task_id`
  (worker restored the key in its own prior archive scratch — git-ignored,
  self-disclosed via `footprint_flags`, same precedent as P10-T5/Q-56).

## Escalation close-out (entry C)

- **ESC-088 → addressed.** Original orphan-drag record; fix landed via
  ESC-091 (wave192 done) and re-verified above.
- **ESC-089 → addressed.** Original unknown-item record; fix landed via
  ESC-092 (wave193 done) and re-verified above.
- **ESC-091 → addressed.** Rework verified above (guards + 52/52 node).
- **ESC-092 → addressed.** Rework verified above (guard + 5/5 pytest,
  boundary holds).
- **PRE-007 → addressed.** Result shape verified above (task_id present
  live + archive; suite green).

## Findings routed this pass

None. No new defect, consistency, security, or gap issue found; nothing
filed.

## Standing checks

- **B.6 mock-endpoint scan: PASS.** `mock|fake|stub|simulat` over the
  reviewed live diff: production hits are the two pre-existing benign prose
  comments (`gestures.js:36` "node fake", `lwc_view.py:134` "stub"); all
  other hits are `gestures.test.js` fakes at the test boundary (allowed).
  No mocked endpoint/client/service/server/API/harness in production; no
  production import of a test double.
- **Usage-doc gate: PASS.** Both fixes are internal hardening (abandon
  semantics, drop-vs-emit on an unrendered race); no user-facing behavior
  change beyond what T7's `usage.md` rewrite already documents.
- **Repeat-invariant rule:** no new BUILD patch; the two closes are the
  original + vehicle pairs for two distinct defects, both now verified.

Note (no action, for the Orchestrator): `task-graph.json` still shows
P10-T3 `in_progress` with `wave.json` at `DISPATCH_PENDING` (wave195,
published 23:03) while live `docs/build/results/P10-T3.json` is `done`
(ran 23:24) — a consolidation lag, not a code finding; `build_log.md`
terminal remains `READY_FOR_REVIEW` and `failures.json` is `{}`.

Status: REVIEW_COMPLETE
