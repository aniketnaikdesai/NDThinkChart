# Task Manager Notes — P21 (D60 follow-offset preservation)

## Graph
- 3 tasks: P21-T1 (M, live shift + preserve + per-view) → P21-T2 (M, away gate + session reset) → P21-T3 (S, batch gate).
- P21-T2 depends on P21-T1 (consumes the shift helper + remembered-gap state; also serialises on `chart_assets/lwc/chart.js`). P21-T3 depends on both.
- `check_tasks.py`: OK, 3 tasks validated, `execution_graph.json` generated. Remaining WARNs are pure-output new suite files only — no action.

## Sizing
- No size exceptions: T1/T2 are M (each ~4-6 distinct actions: focused page edits + 1 offscreen suite + 1 node suite + runs), T3 is S (gate only, no production edits).

## Lineage / non-decisions
- Q100(b) preserve-override with lineage in A178; per-view gaps never shared (Q102(b)); no new module, no Python store, no migration, no live-TWS step — all per plan/architecture, nothing invented.
- No ESCALATED_TO_PLAN items. No requirements ambiguity flagged.

## ESC-114 rework scoping (2026-11-10, owner-approved rework path)
- **ESC-114 (TASK_MANAGER, blocking):** 6 red pre-P21 suites pin mechanics P21 deliberately retired under Q100(b) (T13 chevron-click, T31 joint, T22 no-auto-resume, T32 affordance scroll-path/edge-pin, T24b frame-wins expectation, 5 chart.test.js geometry subtests via frameless re-seed) + 1 latent green-only-via-gap-0 suite (T31 fit_frames_all). None of the 6 files is in any P21 touches_files. Test-only migration direction: re-pin to preserve semantics, never weaken to green.
- **Fit judgment: dedicated tasks, not T3 expansion.** T3 is an S gate (no production edits, runs the joint suites + history-intact check). Folding a 7-file migration into it would conflate migration with gate verification, break the S sizing/step-fit (~20 steps: 7 suites x diagnose + migrate + run), and serialize migration behind T2's BUILD fixes. Instead:
  - **P21-T4 (M, deps [P21-T1]):** test-only migration of tests/test_d57_chevron.py, tests/test_d57_joint.py, tests/test_p11_no_yank.py, tests/test_p11_fit_affordance.py (covers T13/T31/T22/T32 + latent T31 -> {0, newest+G}). Parallel with T2.
  - **P21-T5 (M, deps [P21-T1]):** test-only migration of tests/test_d57_framing.py (T24b page half hold) + chart_assets/lwc/chart.test.js page isolation, with tests/test_lwc_time_parity.py as the geometry guard. Parallel with T2 and T4 (disjoint touches).
  - **P21-T3** unchanged except deps + inputs now include P21-T4/P21-T5 (gate verifies the migrated suites green). P21-T1 untouched (done, as instructed).
- **No production edits** in T4/T5 (AC3 diff-scope guards in each); no normative/D1-P20 content touched; no weakening (follow/badge/chevron/frame outcomes restated, none dropped).
- **ESC-112/113 (BUILD, blocking, both in T2's touches):** forward cascade only — P21-T2 status `blocked` -> `not_started` so BUILD can re-dispatch it (legA parkAway frame-carrying seed; backfill-chunk interior-hole setup). No T2 AC/touches/dependency change; T1 (done) already satisfies its dispatch deps.
- `check_tasks.py`: OK, 5 tasks validated, execution_graph.json written. Remaining WARNs are the pre-existing pure-output class only.
