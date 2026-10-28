# Task Manager Notes — P9 (Batch 25, alarm/drawing fix batch)

## Scope
Decomposed `docs/plan.md` Phase P9 only (waves P9-W1..W4) + `docs/architecture.md` S-P9-1..S-P9-4.
Task IDs P9-T<m>; `docs/tasks/task-graph.json` holds this phase only. `check_tasks.py`: OK, 6 tasks, execution_graph.json written (warnings only: new-file touches not in read_files, expected for pure-output files).

## Wave/task map
- P9-W1 (S) -> P9-T1 (sized M, see below): 1.4 persistence isolation, fault-injection repro first.
- P9-W2 (S) -> P9-T2 (3.2 read-only name cell) + P9-T3 (3.4 active-ID re-validation). Disjoint files (dialog vs main_window); both depend on T1 per the plan's wave ordering.
- P9-W3 (M) -> P9-T4 (3.1 payload + validation) + P9-T5 (3.3 recolor + leave-group + D50 composition). T5 depends on T4 (creation stamping precedes recolor semantics; shared files serialize anyway).
- P9-W4 (S) -> P9-T6 verification-only gate (task_type verification; touches only its own result file per the worker_selfcheck rule).

## Size exceptions (all within the S/M-only instruction; no L)
- P9-T1 = M: two call sites + in-memory retry queue with flush rules + fault-injection repro exceeds S single-file scope.
- P9-T4 = M: spans JS + bridge + main window + node and pytest suites.
- P9-T5 = M: two production files (dialog + store) plus renderer-read-only coupling and three test clusters.

## RG-P9-1 (flag for Requirements Analyst, NOT resolved here)
Requirements entries are outstanding for 3.1/3.2/3.4/1.4. Per instruction, no requirements were invented:
`requirement_ids` carry finding labels (P9-1.4, P9-3.1, P9-3.2, P9-3.4, P9-3.3, P9-W4) and every
measurable is taken verbatim from the plan waves + S-P9-1..S-P9-4.

## Escalations
None open routed to TASK_MANAGER at decomposition time; no pack-fix requested. No changes to other phases.
