# Task Manager Notes — P22 (D61–D64 toolbar/timezone/crosshair/time-axis)

## Decomposition (2026-11-10)
- 5 tasks from 4 plan phases: P22-T1 (S, toolbar label field, P22-1), P22-T2 (M, tz apply path + fan-out + persistence, P22-2 Python leg), P22-T3 (S, page tz apply + zone-aware formatter + DST, P22-2 page leg), P22-T4 (S, crosshair free-tracking pin, P22-3), P22-T5 (S, batch gate + history guard + P21-deferred guard adjudication, P22-4).
- P22-2 split into T2/T3 because the honest step count (3 prod files + bridge + fan-out + persistence + matrices on one task) exceeds the ~20-step target; T3 depends on T2 for the tz op/channel shape T2 defines (interface dependency, not just chart.js overlap).
- No size exceptions above M; no ~32-step invariant exception used.
- No escalations to Plan: every D61–D64 item is satisfiable as written; tripwires (AP-P22-4 fixture re-baseline, DG115 vertical line) are recorded as stop-and-escalate instructions inside T1/T4, not assumptions.
- No open TASK_MANAGER escalations in docs/code_review/escalations.json (104 entries, none open/routed here). No requirements-ambiguity flags (Q103–Q105 answered 2026-11-10).

## Check run
- `check_tasks.py`: OK, 5 tasks validated, execution_graph.json written (6 pure-output-file WARNs, expected for new suites).
