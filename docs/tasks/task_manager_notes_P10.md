# Task Manager notes — Phase P10 (D50 drag-editing)

## Graph shape
- 5 tasks, S/M only (no L): P10-T1 (S, W1 handles) -> P10-T2 (M, W2 page initiation) -> P10-T3 (M, W2 python close-out) -> P10-T4 (S, W3 lock completion + recolor) -> P10-T5 (S, W4 gate).
- P10-T2 and P10-T3 are sequential (not parallel): T3's empty-color normalisation consumes the commit shape T2's page emits (AP-P10-2), so the DEPENDS_ON edge is logical, not just file overlap. T1/T3 share ui/lwc_view.py and are ordered T1 -> T3 for the same reason (wave order W1 -> W2).
- No overlapped-file parallelism anywhere: T1+T3 share lwc_view.py (ordered), T4 touches main_window.py alone among code tasks.

## Deliberate pack decisions
- No `new` contracts anywhere: the cross-boundary contracts (DrawingController signals, update_drawing None-contract, drag_drawing/drag_drawing_item/drawing_handle_points geometry) are all frozen existing; the page initiation entry point is intentionally unnamed (plan names no page function), so its shape is specified in T2's description/ACs rather than a fabricated signature.
- T4's delete guard is scoped to ui/main_window.py (_on_drawing_deleted / _delete_selected_drawing as present on the LWC-only tree); the worker locates the exact Del-button wiring via the _drawing_actions read-only pack entry.
- Gate task (P10-T5) mirrors the P9-T6 pattern: touches only its own result file.

## Repro-first honesty labels (per wave)
- W1 red: T11, T12 (handles always attached today). T13 is a labelled regression guard.
- W2 red: T21-T23 (no initiation path), T31 (no drag gate), T32 empty-color leg. T33 legs are labelled guards.
- W3 red: T41 delete leg. T42 color legs + T44 interplay are labelled allowed-behavior/interplay pins over T3's normalisation.

## No escalation
- No open TASK_MANAGER entries in escalations.json; plan P10 Status: READY_FOR_TASK_MANAGER confirmed. No architecture gap: all five waves decompose into the frozen surfaces plus the three existing-file edits the plan names.

## Code Reviewer follow-up round (ESC-087 + ESC-090 -> P10-T6, P10-T7)
- ESC-087 (should-fix, TASK_MANAGER) -> new P10-T6 (S, deps P10-T4): the groups-dialog Delete Selected path (ui/drawing_groups_dialog.py:228-232) bypasses the D50.3 lock P10-T4 scoped to the page-deleted and Del-button paths. Chose a new task over amending T4: T4 is done and the fix owns a file outside T4's touches_files. Gate reuses T4's policy verbatim (DrawingGroup.locked source of truth, fail-open, ungrouped/unknown unlocked, color/style untouched); main_window.py guards stay as-is. Single invariant AC (locked survive intact, unlocked still delete, all-locked selection is a no-op) with one repro-first integration test naming the uncovered dialog path. No shared files with any other pending task, so no new serialization.
- ESC-090 (should-fix docs, TASK_MANAGER) -> new P10-T7 (S, deps P10-T6, doc_required true, touches usage.md only): usage.md:180 "delete-only until D50 drag-editing lands" is stale and D50 behavior (handles, body/anchor drags, locked no-handle + drag/delete refusal with color allowed, cancel) is undocumented; no P10 task owned docs. USAGE.txt deliberately out of scope: its line-60 pointer already names drawings among usage.md-covered workflows and the file carries no per-batch sections to extend (so no ESC-058-style one-liner applies). Manual verification test; no code/test change. Deps P10-T6 so the docs describe the final all-paths locked-delete behavior. task_type "docs" (new value in this graph) accepted by check_tasks.py.
- Untouched per instruction: ESC-088/089 (BUILD round), P10-T1..T5 fields, escalations.json (Code Reviewer closes on re-verification). check_tasks.py: OK, 7 tasks validated (the P10-T6 new-test-file WARN matches the sanctioned T1/T3/T4 pure-output shape). Metadata status stays READY_FOR_BUILD.
