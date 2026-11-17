# Archived plan reviews

Per-phase Plan Validator reviews for the completed phases P5–P22, plus the legacy unsuffixed
review (Batch 17). Files were moved here unchanged from `docs/`; each row's "Delivered" line is
taken from the review's own first heading. The current phase's review (`docs/plan_review_P23.md`)
stays in `docs/` — the build depends on it.

Each "Final status" cell quotes the last `Status:` token in the file, which is what
`pipeline_state.py` reads as a phase verdict (`last_status`). Where that token is
`Status: READY_FOR_TASK_MANAGER` the review's final paragraph is its Task Manager readiness note
quoting the plan-side activation; the review's own decision line in that file is `APPROVED`.

| Phase | Review | Final status | Delivered (from the review's title) |
|---|---|---|---|
| P5 | `plan_review_P5.md` | `Status: APPROVED` | D46 / Batch 21, revision 2 — scope EXPANDED |
| P6 | `plan_review_P6.md` | `Status: READY_FOR_TASK_MANAGER` | D47: chart stack migrates to Lightweight Charts |
| P7 | `plan_review_P7.md` | `Status: APPROVED` | data-path batch: historical backfill correct + fast, streaming correct |
| P8 | `plan_review_P8.md` | `Status: APPROVED` | D48 lite |
| P9 | `plan_review_P9.md` | `Status: READY_FOR_TASK_MANAGER` | alarm/drawing fix batch, Batch 25 |
| P10 | `plan_review_P10.md` | `Status: APPROVED` | D50 drag-editing for LWC drawings |
| P11 | `plan_review_P11.md` | `Status: APPROVED` | D51 follow-live viewport for the LWC main chart |
| P12 | `plan_review_P12.md` | `Status: APPROVED` | D52: `30 mins` interval, Batch 27 |
| P13 | `plan_review_P13.md` | `Status: APPROVED` | D49 pop-out robustness + D49.6 timezone handoff, Batch 24 |
| P14 | `plan_review_P14.md` | `Status: READY_FOR_TASK_MANAGER` | D53 persistent backfill-state indicator + cache-current guard |
| P15 | `plan_review_P15.md` | `Status: READY_FOR_TASK_MANAGER` | D54 10-second target on load chart |
| P16 | `plan_review_P16.md` | `Status: APPROVED` | D55 documentation consolidation, docs-only |
| P17 | `plan_review_P17.md` | `Status: READY_FOR_TASK_MANAGER` | D56 silence retry for historical chunks |
| P18 | `plan_review_P18.md` | `Status: APPROVED` | D57: viewport chevron + fresh per-timeframe framing |
| P19 | `plan_review_P19.md` | `Status: APPROVED` | D58 scroll-triggered backfill prefetch |
| P20 | `plan_review_P20.md` | `Status: READY_FOR_TASK_MANAGER` | Index + futures contract support, D59 |
| P21 | `plan_review_P21.md` | `Status: READY_FOR_TASK_MANAGER` | Follow-offset preservation on new-bar arrival, D60 |
| P22 | `plan_review_P22.md` | `Status: READY_FOR_TASK_MANAGER` | Toolbar / timezone-toggle / crosshair / time-axis fixes, D61–D64 |
| Legacy (Batch 17, read by `pipeline_state.py` as P1) | `plan_review.md` | `Status: APPROVED` | D23: two D22 post-build quality corrections |
