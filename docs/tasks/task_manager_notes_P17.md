# Task Manager Notes — Phase P17 (D56 silence retry)

## Decomposition (2026-11-05)
Plan P17 APPROVED (`docs/plan_review_P17.md`), `docs/plan.md` § Phase P17 `Status: READY_FOR_TASK_MANAGER`.
No open escalations routed to TASK_MANAGER; no `feature_suggestions.md` approved items in scope.
Q88–Q91 answered-owner-confirmed; proceeded on them per the approval (no invention).

Three plan phases → four tasks (P17-1's mechanism split into core + fencing so each
task has one independently verifiable AC cluster; same-file pairs serialize on
`touches_files`, costing no correctness):
- **P17-T1 (M)** — silence detection + cancel/re-issue core + shared `_retried_plans`
  allowance (AC-D56.1 zero-bar + trailing-silence, AC-D56.2 no-third-issue guard).
  Owns `ui/ticker_session.py` retry structures; no dependencies.
- **P17-T2 (S)** — generation fencing + identity-removal exactly-once (AC-D56.4,
  AC-D56.7-mechanism). Depends on P17-T1 (consumes its retry path/tags/lists).
- **P17-T3 (S)** — error taxonomy (any-code cancel-ack generalisation, the
  `ui/main_window.py::_on_error` edit per the Validator activation note) + pacing
  gate with queue-with-deadline fail-open (AC-D56.3, AC-D56.5). Depends on P17-T1.
- **P17-T4 (S)** — D53 retry marker + latch label with continuing elapsed (AC-D56.6),
  double-silent fall-through verification both variants (AC-D56.2-verify), batch
  gate incl. history-intact grep + full suite green (AC-D56.7-gate).
  Depends on P17-T1 + P17-T2 + P17-T3: T1/T3 per the plan wave note (P17-3 after
  P17-1 and P17-2, serialised on the shared `ui/main_window.py` — disjoint
  `_on_error` vs indicator regions), plus T2 because the gate asserts the whole
  phase green.

## Size note
No step-fit exception: T1 is M (new sweeper + retry path + 4 focused tests, fits
the ~20-step target / ~32 cap); T2–T4 are S (branch-level edits + 2–4 scoped tests).

## `check_tasks.py`
Pass: `OK: 4 tasks validated, execution_graph.json written.` Four WARNs only —
each new test module in `touches_files` but not in `read_files`, explicitly
`ok if pure-output file` (new files cannot be pre-read; they are named in
`touches_files` + `expected_artifacts`, and conventions come from the existing
suite reads in each pack).

## Flags for Requirements Analyst
None. No requirement or architecture ambiguity encountered; no escalation written.
`docs/requirements/requirements.md` untouched (Analyst-owned).

## Rework wave (2026-11-05) — owner-approved code-review rework, ESC-099 + ESC-100

Orchestrator-invoked, scope LIMITED to the two open TASK_MANAGER escalations;
P17 structure otherwise untouched (T1–T3 done, byte-identical), no D1–P16 or
P18 content touched, no requirements file claimed.

- **ESC-099 (blocking, ex P17-T4 gate):** history-guard pins
  (`test_t34_history_markers_intact`, `test_t33_history_markers_intact`) tripped
  by two P18/D57 glossary rows (Go-to-latest chevron, Initial framing) inside the
  hashed marker-through-D52 span. Verified in-tree: the live span diff vs the
  `b11d9da3` HEAD baseline is those two rows only, purely additive (no `-` lines).
  P18 has now SETTLED (Q92–Q95 answered, P18 READY_FOR_PLAN), so the coordinated
  re-pin proceeds per the reviewer's preferred direction (re-pin, never weaken —
  every protected assertion kept). **P17-T4** revised to explicit BUILD rework
  scope: re-verify landed retry-state work (AC1/AC2 unchanged), compute + verify
  + set the pin identically in both guard files (new T43), history grep + full
  suite gate (new T44); status reset `blocked` → `not_started`; `touches_files`
  gains the two guard test files (each also in `read_files`, 8 entries total,
  within pack budget). T1–T3 done, so T4's `DEPENDS_ON` edges cost no wait.
- **ESC-100 (should-fix, prime-path flake):** `test_p7_t07_t13_prime_retry_defers_then_issues`
  fails ~1.7% of runs — `_on_prime_retry` re-enters `prime_aggregator` with
  `int(time.time())`, so a run in the first 5 s of the 300 s period takes the
  `span_s<5` fail-open path (`_prime_req_id` None). P17 never touches the prime
  path (verified). **P17-T5 (S, no deps, disjoint files → parallel with T4)** —
  test-only hardening: freeze the retry clock at the existing `mid_period_ts()`
  instant in the existing test, plus a deterministic period-boundary case pinning
  the fail-open path; no production change, no weakened assertion.
- **Pack budget:** T4 6 files / 8 entries, T5 2 files / 4 entries; all `contracts`
  refs re-verified against the live tree (`set_backfill_state`,
  `clear_backfill_indicator`, `_refresh_backfill_indicator`,
  `_retry_silent_chunk`, `_on_prime_retry`, `prime_aggregator` all present).

## `check_tasks.py` (rework)
Pass: `OK: 5 tasks validated, execution_graph.json written.` Four WARNs only —
the pre-existing pure-output-file pattern (T1–T3 new suites + T4's
`test_d56_retry_indicator.py`); both guard files ARE in T4 `read_files`, and
T5's suite is a pre-existing file in `read_files`, so no new warnings.

## Rework (2026-11-05) — owner-directed P17-T4 pin-scope widening: 2xD57 + 2xD58

Orchestrator-invoked, scope LIMITED to P17-T4's AC3/T43 diff-content precondition.
No other task, scope, dep, or file changed (T1–T3 + T5 byte-identical, deps untouched).

- **Owner decision (verbatim direction: accept the D58 rows now):** the 2x D58
  prefetch glossary rows inside the history-guard hashed span
  (`| Prefetch (D58) |...|` and `| Buffer zone (D58) |...|`,
  `docs/requirements/requirements.md:643-644`, inside the marker-sentence(403)
  through `### D53`(5428) span) are accepted as correct ahead of the pipeline —
  verified additive-only by the P17-T4 worker, which correctly refused to pin
  them unapproved. P19's later validation still reviews them in full; this only
  stops the pin from lying in the meantime.
- **Lineage:** ESC-099 re-pin (2x approved D57: Go-to-latest chevron, Initial
  framing) -> P17-T4 first run verified the live span diff is purely additive
  but surfaced 2 further unapproved in-span rows (D58 Prefetch, Buffer zone) and
  correctly refused to pin them -> owner accepted the D58 rows now (2026-11-05)
  -> this rework widens the coordinated pin to all 4 additive rows.
- **Change:** AC3, T43 description, plus the same precondition restated in the
  task description and T44 (linked to AC3; its grep exception must admit the
  same 4 rows or it would fail against the live tree): "two approved D57 rows"
  becomes "four additive glossary rows (two approved D57 — Go-to-latest
  chevron, Initial framing — plus two D58 accepted-now per owner decision
  2026-11-05 — Prefetch, Buffer zone; purely additive)". Every other assertion
  byte-identical and never weakened (identical pin in both files, no other line
  changed, full offscreen suite green). P17-T4 reset `blocked` -> `not_started`
  for the re-run; T1–T3 done so its DEPENDS_ON edges cost no wait.
