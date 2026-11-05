# Plan Review — Phase P17 (D56 silence retry for historical chunks)

**Status: APPROVED**

**Pass type:** final_pass (full Validation Method; gate was open on first invocation —
P16 `REVIEW_COMPLETE` in `docs/code_review/review_log_P16.md`, no provisional existed,
0 open escalations). LINT PASS carried in the preamble.

**Decision:** Task Manager may proceed. `docs/plan.md` § *Phase P17* now ends
`Status: READY_FOR_TASK_MANAGER`.

- **Coverage:** AC-D56.1–D56.7, Journey 51, A156–A160, R114–R118, Q88–Q91, DG106–DG108
  all traced (plan § Traceability); zero-bar + trailing-silence triggers, per-chunk
  budget, explicit retry state with continuing elapsed, fencing, pacing, exactly-once
  counting each land in a phase. No requirement narrowed; D1–P16 untouched.
- **Completeness:** stack (constrained + 2 new), components, data model, integrations,
  NFR (timing/concurrency/budget/honesty/testability), 6 risks with mitigations,
  6 rationale-backed decisions S-P17-1…S-P17-6. DG106 arithmetic (≤65 s vs 120 s),
  DG107 seam (queue-with-deadline), DG108 inventory (162/321/200/399/504) all stated.
- **Consistency:** shared allowance S-P17-4 caps every chunk at two issues with error
  semantics unchanged for never-retried chunks; watchdog/pacing/PK/finalization
  contracts read-only. No internal contradiction.
- **Plan quality:** P17-1 (M) → P17-2 (S) → P17-3 (S), ordered, goals/covers/deps/
  touches_files/exit conditions present; phase-sized, no task graph, no per-task tests.
- **Readiness:** yes — every mechanism (stamps, sweeper, cancel path, fencing, pacing
  gate, latch label) is decided; Task Manager decomposes without inventing architecture.
  Editorial fix applied at activation (no new decision): P17-2's `_on_error` cancel-ack
  generalisation correctly attributed to `ui/main_window.py` (the `errorCode == 162`
  literal lives there) and the wave note serialises P17-3 after P17-2 on the shared file.
- **Existing-repo compliance:** pass — Codebase Summary substantive and source-verified;
  stack intact and listed first; every item labelled `[existing]`/`[new]`/`[new/changed]`;
  additive-only (no `[revises]`); proposal consistent with its summary.
- **Frozen interfaces:** pass — 8 entries, all `[existing]` with verbatim contracts,
  spot-verified against the tree (`cancel_historical_data`, `_history_event_accepted`,
  watchdog derivation, `mark_history_request_issued`, PK idempotency, terminal funnel,
  pacing constants); owning modules exist; nothing under construction frozen; no
  duplicates.
- **Map quality:** pass — P17 note appended, no new module, annotations carried
  forward, index-sized; `ui/ticker_session.py` + `ui/main_window.py` resolve.
- **Doc sync:** pass — `docs/pending_doc_sync.md` absent; no drift.

**Scope guard held:** go-to-latest-bar floating button absent from the plan (correctly
excluded); TWS cause, chunk resize, watchdog retune, D1–P16 reopen all explicitly out.

**Required changes:** none. **Requirements escalations:** none.
