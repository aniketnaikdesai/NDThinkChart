# Task Manager Notes — P8 (D48: 1 week / 1 month)

## Decomposition
- 5 tasks, sizes M/S/S/M/S — no L; lane rule holds.
- P8-W1 -> P8-T01 (config + aggregator bucketing) + P8-T02 (planner verification, priming docstring, standalone probe). P8-T02 depends on P8-T01 (planner/probe cases read the new rows).
- P8-W2 -> P8-T03 (canonical daily+ mode in main_window + chart_model) + P8-T04 (predicate sweep, minutes, picker parity, visibility guard). Both depend on P8-T01 only; parallel-safe (disjoint touches_files).
- P8-W3 -> P8-T05 (gate: probe record, history intact, full suite). Depends on T02/T03/T04.
- No open TASK_MANAGER escalation applies (all such entries are addressed; ESC-075..078/079/PRE-001 are BUILD/PLAN-routed).

## Deliberate decisions
- A120 (visibility grid gains rows) vs S-P8-6 (no new rows): followed the canonical architecture/plan (S-P8-6, verified write-only grid, no consumer) — P8-T04 guards no-new-rows + default-checked + round-trip per DG97's "or equivalent" clause.
- Probe is a `manual` test in P8-T02 (live TWS required); P8-T05-T11 asserts the record's presence/content without re-probing.
- check_tasks.py WARNs on new-file touches (pure-output, created by the task) are the script-sanctioned shape; new test modules were removed from read_files because read_files paths must already exist. Workers: read the sibling test module for conventions instead.
- Contract refs use bare symbol substrings (the checker is substring-based; dotted `Class.method` forms do not resolve).

## Reviewer-escalation round (2026-10-28): ESC-080/081/082/085 -> P8-T06..T09

Four open TASK_MANAGER-routed escalations from review_log_P8.md (Status: REVIEW_COMPLETE);
handled in order. ESC-083/084 (BUILD-routed) and ESC-075..079 (prior-phase scope) untouched
per the invocation. No escalation status flipped here - the Code Reviewer closes them on
re-verification.

- ESC-080 (blocking) -> new P8-T06 (M, deps P8-T01): extend the T40 fixture
  `_session_bars` (tests/test_history_backfill.py:97-120) with a weekly/monthly bar model
  anchored on the canonical data/bar_aggregator.py week_bucket_start (:83) /
  month_bucket_start (:92) - Monday-00:00-ET weeks, calendar-month-boundary months,
  bucket-keyed against per-day-caller duplication. DECISION (the escalation's either/or):
  extend the fixture, do NOT scope TIMEFRAMES (keeps all-eight coverage) and do NOT move
  production bucketing (P8-T01 exonerated by independent probe). The t13 knock-on
  (test_p7_w1_cap.py subprocess rerun) clears with the same fix; no file of its own.
- ESC-081 (blocking) -> new P8-T07 (S, deps P8-T01): encode the S-P8-1 eight-row set in
  both exact-equality pins. Handshake map gains 1 week 2 Y / 1 month 10 Y; t12 approved
  AND chained dicts gain identical week/month entries (added-never-widened, so the
  changed-duration loop skips them with no approval record - no new record invented);
  the "(1 week/1 month are out of scope)" comment (t12:364-365) rewritten to match the
  assert. Fail-closed shape kept (no subset comparison); WIDEN_CANDIDATES + five P7
  records untouched. Settles toward the S-P8-1 rows per the escalation; baseline was
  green pre-P8 (fresh-worktree red is a missing-approvals artifact, recorded in T07).
- ESC-082 (blocking, pipeline hygiene) -> new P8-T08 (S, no deps): DECISION (the
  escalation's either/or): BOTH halves - re-scope
  test_archived_results_carry_task_id to latest-per-task (group ARCHIVE stems by task
  token, require task_id only on the newest per group; factored helper unit-tested on
  synthetic dicts) AND delete the five named superseded intermediates (each has a newer
  same-task stamped result). The task_id requirement itself is preserved (AC8_3),
  still fail-closed on a newest result missing it.
- ESC-085 (doc, nice-to-have) -> new P8-T09 (S, no deps, doc_required true): usage.md
  range 1 min - 1 day becomes 1 min - 1 month with the 1 week / 1 month entries named;
  plus a one-line D48 picker note in USAGE.txt after the D44 section per the ESC-058
  convention. Docs only.
- Amendment to an existing task: P8-T05 dependencies extended with P8-T06, P8-T07,
  P8-T08 (its AC3 suite-green gate needs all three blocking follow-ups). P8-T05 stays
  `blocked`; description/ACs/tests untouched. P8-T09 is independent of the gate (docs
  do not affect suite-green), so no T05 edge. No P8-T01..T04 field touched.
- check_tasks.py: OK, 9 tasks validated (only the six pre-existing new-file WARNs on
  T01..T05, sanctioned shape). No status flip to READY_FOR_BUILD needed - metadata
  already carries it; the Orchestrator re-dispatches T06..T09 then T05.
