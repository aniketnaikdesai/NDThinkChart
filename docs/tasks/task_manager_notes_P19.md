# Task Manager Notes — Phase P19 (D58 scroll-triggered backfill prefetch)

## Decomposition (2026-11-09)
- Plan's 3 milestone phases → 4 tasks. P19-2 (size M) split into **P19-T2** (ordinary-wave issuance + DG111 coalesce seam + pending-marker lifecycle, `AC-D58.2`) and **P19-T3** (fetch-while-fetchable chaining + honest stops, `AC-D58.5`): a single task covering one-step issuance, marker lifecycle, abandonment, chaining, closure stop, single shortfall, and pacing fall-through would exceed the ~20-step sizing target; the split keeps each task independently verifiable (issuance lifecycle vs depth behaviour) with T3 depending on T2.
- **P19-T1** proves only the fire/silent decision (no wave issuance by its code paths) so its matrix tests cannot pass spuriously via issuance side effects; **P19-T4** is production-edit-free (honesty + viewport stability + gate), depending on T2+T3.
- No size exceptions: all tasks S/M per the scope guard; no task approaches the ~32-step exception cap.
- No `ESCALATED_TO_PLAN`: every D58 item was satisfiable as written; the DG111 seam was already decided by S-P19-4 (coalesce, never cancel) — tasks only cover the marker lifecycle under `AC-D58.2`, no architecture invented.
- No flags for Requirements Analyst: trigger table is analyst-decided per owner delegation; owner corrections land as in-place refinements.

## Validation
- `check_tasks.py`: 4 tasks validated, `execution_graph.json` written (only WARNs: new `tests/test_p19_*` files in `touches_files` but not `read_files` — pure-output files, explicitly ok).
- Handoff: `task-graph.json` metadata `status: READY_FOR_BUILD`.

## Footprint fix — P19-T2 (2026-11-09)
- P19-T2 completed under owner exception (dispatch failures; provenance in `orchestrator_state.json` `owner_exception_2026_11_09_p19t2`); full suite green, but consolidation blocked on worker_selfcheck footprint violation: `tests/test_d56_taxonomy_pacing.py` was missing from T2's `touches_files`.
- Fix (task-graph only, no scope change): added `tests/test_d56_taxonomy_pacing.py` to P19-T2 `touches_files` and to `context.read_files` (lines 182-209, t32 terminal-expectation). The one-assertion update (t32 terminal-message expectation: terminal state wins over transient error lines on wave-terminating errors) is required by T2's own `_on_error` ordering fix — test-only, no production scope change, AC-D56.3-relevant.
- No other task, dep, test, or scope touched. Pack stays within budget (7/8 read_files). P19-T2 reset to `not_started` so the corrected result (content already verified green) can consolidate.
