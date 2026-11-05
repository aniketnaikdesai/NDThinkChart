# Code Review Log — Phase P17 (D56 silence retry)

Tier: **FULL** (phase-final-style full pass: one task `blocked`, full-suite VERIFY verdict FAIL).
Scope (incremental — all four tasks newer than any prior review marker; no `review_log_P17.md` existed): P17-T1, P17-T2, P17-T3, P17-T4.
Ground truth consumed: `precheck.json` (0 fail_fast, footprints verified, no violations/overlaps beyond cross-task info flags), `test_verification.json` (FAIL exit 1, 3 failures), `build_log.md`, `failures.json`, results `_archive/wave265..271_P17-T*.json`, task-graph P17, requirements P17/D56, architecture/plan Phase P17.
Diff basis: `git diff HEAD` over each task's `files_changed` (production files); new test files read directly. P17 suites re-run by reviewer: 19/19 pass.

## F-P17-01 — P17-T4 batch gate blocked by external history-guard pins (no P17 defect)
- Task: P17-T4 (status `blocked`) — linked escalation ESC-099 (blocking, TASK_MANAGER).
- Category: gap. Root cause: `bad_task_breakdown` (pin-update work belongs to no P17 task; tripped by another batch's requirements edit).
- Observed: T4's own suite is green — reviewer re-ran `test_d56_retry_indicator.py` plus all P17 suites: 19/19 pass (T41 retry-state distinguishability/continuity/latch, T42 zero-bar + partial double-silent fall-through, T43 history grep). The AC3 full-suite gate fails only on `test_p14_cache_guard.py::test_t34_history_markers_intact` and `test_p15_surfacing.py::test_t33_history_markers_intact`, both asserting `sha256(marker→### D53 span) == b11d9da3…` (got `47306f78…`). Reviewer reproduced both failures on the live tree.
- Expected: gate green; T4 `done`.
- Evidence the trip is external to T4: `git diff HEAD -- docs/requirements/requirements.md` shows the only change inside the hashed span is two P18/D57 glossary rows (Go-to-latest chevron, Initial framing) inserted in the glossary table between the marker sentence and `### D53` — a front-stage overlap collision from in-tree P18 analyst work, not T4 (T4 touches no requirements file; its P17 appendix lands after D55, outside the span). T4's T43 grep (marker + `### D41`–`### D55` presence) passes because it does not pin the hash.
- Suggested direction: Task Manager to scope the pin update (recompute `PROTECTED_SPAN_SHA256` in both P14/P15 test files once P18's requirements edits settle — P18 owns the span change, so coordinate with that batch rather than re-pinning mid-edit); then re-run T4. No P17 code action.

## F-P17-02 — Full-suite third failure is a pre-existing P7 prime-retry wall-clock flake, not P17 fallout
- Task: none (full-suite gate noise) — linked escalation ESC-100 (should-fix, TASK_MANAGER).
- Category: gap (flaky test). Root cause: `bad_task_breakdown` (hardening belongs to a P7-scoped follow-up; D1–P16 are not reopened by P17).
- Observed: `test_p7_t07_t13_prime_retry_defers_then_issues` failed in the VERIFY full-suite run (`_prime_req_id is None` after `_on_prime_retry` with mode="issue" — fail-open path taken) but **passes in isolation** (reviewer re-ran: pass).
- Evidence of non-causation: the P17 diff never touches the prime path (`prime_aggregator`/`_on_prime_retry`/`_fail_open_prime` byte-identical to HEAD). The test defers with wall-clock-independent fake pacing, but `_on_prime_retry` re-enters `prime_aggregator(..., int(time.time()), ...)` with the REAL clock: when the run lands within the first 5 s of a 300 s period (`span_s < 5`, ~1.7% of runs), the retry returns False → fail-open → assertion fails. Only wall-clock input varies; the fake transport is per-test deterministic. Verdict: timing flake, will pass on re-run.
- Suggested direction: harden the test (e.g. inject/freeze the retry clock instead of `int(time.time())`), scoped as a P7 follow-up by Task Manager. No P17 code action; do not weaken the assertion.

## Quality review — P17-T1 (done): silence sweeper + cancel/re-issue core — PASS, no findings
- Matches arch S-P17-1/S-P17-2/S-P17-4 and plan P17-1. Per-reqId monotonic stamps (`_silence_now` seam, never wall-clock), 1 s sweeper armed only while reqIds are in flight, `_retry_silent_chunk` mirrors `_issue_wave_chunks` kwargs exactly (contract/timeframe/useRTH=1/extended_hours/plan bar_size+duration), shared `_retried_plans` recorded BEFORE re-issue (no third issue on any outcome), PacingExceeded path re-queues at head + waits via existing continuation bounded by the unchanged watchdog, identity-removal from `_pending_bars` with PK-idempotent cache re-read.
- Lifecycle verified: every wave-termination funnel (`_cancel_history_requests`, incl. watchdog/disconnect via `_finalize_stranded_history_wave`, plus per-chunk end/error paths) clears stamps and parks the sweeper; re-registration stamps fresh windows. Overlap with T3 on `ui/ticker_session.py` is sequential (T3 after T1), no conflict.
- Observation (non-actionable, no escalation): the superseded old reqId keeps its host routing-table entry until the next wave cancel — identical to the pre-existing 162-retry path, and fully fenced either way (`_history_event_accepted` drops late bars/ENDs; `_is_superseded_history_req` debug-only acks late errors; T21/T31 prove both). Symmetry-only cleanup if ever touched.

## Quality review — P17-T2 (done): fencing + exactly-once tests — PASS, no findings
- Production mechanism rides T1 (tag + drop + identity-removal, unchanged `_history_event_accepted` fence) as the plan allows; T2 contributes the two discriminating offscreen cases (late bars+END change nothing vs control; partial-chunk retry counts once with PK-unique cache). `files_changed` correctly lists only the test file.

## Quality review — P17-T3 (done): taxonomy generalisation + pacing gate — PASS, no findings
- Matches arch S-P17-3/S-P17-5 and plan P17-2. `_SUPERSEDED_HISTORICAL_ACK_CODES={162,321,200,399,504}` checked against `_is_superseded_history_req` BEFORE session routing, so fresh-reqId semantics (162-retry via shared allowance → finalize-short; 200/399/504 fatal via `classify_error`) are untouched; superseded echoes are ours-by-cancel for every inventoried code. T31 parametrizes all five codes; T32 pins no-third-issue on fresh 162; T33/T34 pin slot accounting + watchdog fall-through. Overlaps sequential, no conflicts.

## Quality review — P17-T4 substance (blocked only by F-P17-01): retry indicator + fall-through verify — PASS, no code findings
- Matches arch S-P17-6 and plan P17-3. Retry latch (`_backfill_retry_in_flight` + reqIds) set only while a live reqId's plan sits in the shared allowance (both retry axes covered), cleared only by the terminal funnel alongside the expiry latch; `elapsed` stays a pure `_backfill_wave_start` read (never reset by retry); label composes `(partial, retry)` markers; AC-D53.3 no-current-claim behavior asserted by T41. Own 4/4 green, re-verified by reviewer.

## Standing checks (full-pass duties)
- Mock-endpoint scan: `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness` over the reviewed diff — one hit, a pre-existing comment ("tests / stub hosts"), no mock endpoint in production. CLEAN.
- Usage-doc judgment: candidates `USAGE.txt`, `usage.md`, `docs/` untouched. D56 is internal wave-lifecycle logic; the only user-visible delta is the transient status-bar label `Backfill (retry)`, which neither `USAGE.txt` nor `usage.md` covers for the existing D53 indicator either (grep: no "Backfill" in either file). No doc update warranted — consistent with the D53 precedent. No finding.
- Requirements/architecture consistency: implementation follows S-P17-1…S-P17-6 and the plan's phase mapping (4-task split of the 3 dev phases covers every D56 expectation; no narrowing). AC-D56.1…D56.7 all exercised by the new suites. No deviation.
- Repeat-invariant rule: first P17 review; no prior P17 findings. No dup-escalation risk.

## Escalation close-out (entry point C)
- `escalations.json` has zero `open` entries (86 total, all `addressed`); `precheck.json` reports no `escalation_updates`. Nothing to re-verify or flip. (PRE-017 cited in the dispatch preamble belongs to P16-T4 and is already `addressed` — not P17 scope.)

## Handoff
- New escalations: ESC-099 (F-P17-01, blocking → TASK_MANAGER), ESC-100 (F-P17-02, should-fix → TASK_MANAGER). No BUILD/PLAN/REQUIREMENTS routes: P17 code is clean; the D57 glossary content is P18's answered-scope work, not a requirements defect.
- P17-T1/T2/T3: reviewed, no action. P17-T4: substance approved; re-run to `done` once ESC-099 lands (ESC-100 clears on re-run by mechanism, hardening tracked separately).

Status: REVIEW_COMPLETE

---

## Pass 2 — P17 rework verification (2026-11-05): T4 pin over owner-accepted 4 rows, T5 flake hardening

Tier: **FULL** (phase-final: all five P17 tasks `done`; full-suite VERIFY verdict `pass` exit 0).
Scope (incremental — only tasks with results newer than the pass-1 `REVIEW_COMPLETE` marker, per `precheck.json`): P17-T4 (`_archive/wave275_P17-T4.json`), P17-T5 (`_archive/wave273_P17-T5.json`). D1–P16 NOT reopened per scope guard.
Ground truth consumed: `precheck.json` (0 fail_fast, footprints verified, no violations/overlaps), `test_verification.json` (PASS exit 0, 77.23 s — full suite green, ground truth for "tests pass").

### Quality review — P17-T4 (done): history-pin re-pin + D53 retry re-verify — PASS, no findings
- `files_changed` (verified): `tests/test_p14_cache_guard.py`, `tests/test_p15_surfacing.py` only. Live `git diff HEAD` over both files is exactly one line each: the `PROTECTED_SPAN_SHA256` literal `b11d9da3…` → `2fe7b1ec…`. No other line in either file changed — every protected assertion byte-identical, per AC3/T43.
- Pin correctness re-verified by reviewer (not the worker's word): `sha256(marker-sentence-through-D52 span)` computed on the live `docs/requirements/requirements.md` == `2fe7b1ec62fa0e60…cee0c139` == the new literal in both files. T43 (span-diff-only-four-additive-rows mechanics) passes in the result selfcheck; the four rows (approved D57 Go-to-latest chevron + Initial framing, D58 accepted-now Prefetch + Buffer zone per 2026-11-05 owner decision) are present in the glossary (requirements.md:642-645). Requirements file itself untouched by T4 (outside its touches, Analyst-owned) — correct.
- Substance re-verified live: `tests/test_p14_cache_guard.py + tests/test_p15_surfacing.py + tests/test_d56_retry_indicator.py` → 18/18 pass, exit 0. Result selfcheck (T41–T44 incl. full-suite 1383 passed / 3 skipped) verdict pass exit 0, consistent with the independent VERIFY ground truth.
- No production change (test-only pin literals); D53 retry substance was approved in pass 1 and is untouched.

### Quality review — P17-T5 (done): prime-retry clock freeze + deterministic boundary case — PASS, no findings
- `files_changed` (verified): `tests/test_p7_w4_streaming.py` only. Live diff: `test_p7_t07_t13_prime_retry_defers_then_issues` gains a `monkeypatch` arg freezing `ticker_session_mod.time.time` at the mid-period instant (`span_s=90>=5`) across `_on_prime_retry()` plus a `len(requests)==2` issue-once assertion; new `test_p7_t07_t13_prime_retry_boundary_fail_open_deterministic` freezes at `period_start+1` (`span_s=1<5`) and asserts no-issue + skip-counted + live-feed-attached with transport open. No production file modified (the `_on_prime_retry` wall-clock call and `span_s<5` guard are read-only context) — exactly the ESC-100 suggested direction, no weakening (the defers-then-issues assertion is strictly strengthened).
- Determinism re-verified live: module 13/13 pass; the two clock-sensitive cases looped 3× green (the ~1.7% wall-clock flake this kills cannot be forced on demand, but zero wall-clock dependence follows from the freeze by construction).
- No P7 production-path touch; D1–P16 stay closed (test-only change to a P7 suite, no P7 AC touched).

### Standing checks (full-pass duties)
- Mock-endpoint scan: `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness` over the reviewed diff (both tasks) — zero hits. CLEAN.
- Usage-doc judgment: candidates `USAGE.txt`, `usage.md`, `docs/` all `touched: false`. Both tasks are test-only (pin literal + test hardening); no user-facing behavior changed. No doc update warranted. No finding.
- Requirements/architecture consistency: pin matches live span; every other guard assertion intact; no D56 production drift (T4/T5 touch no production file). No deviation.
- Repeat-invariant rule: no prior P17 BUILD findings; no per-case patch accumulation. No dup-escalation risk.

### Escalation close-out (entry point C)
- ESC-099 (P17-T4 pin, blocking → TASK_MANAGER): CHANGED (task-graph carries the rework task; T4 `done` wave275). Re-verified fix myself: live span hash == new pin (computed above), T43 mechanics pass, task suites 18/18 green, VERIFY full-suite pass. → flipped to `addressed` with `verified` note.
- ESC-100 (prime-retry flake, should-fix → TASK_MANAGER): CHANGED (P17-T5 landed). Re-verified fix myself: 13/13 module green, 3× loop deterministic, diff is test-only with no weakened assertion. → flipped to `addressed` with `verified` note.
- ESC-097/098: remain `addressed` — no new evidence (097's command fix holds via T4's green selfchecks; 098's narrowed-span mechanism is exactly what T4 just re-pinned, guards green).
- PRE-015 + PRE-017: remain `addressed` and HELD — newest T4 result wave275 carries top-level `task_id: P17-T4` (direct read), so the malformed-result condition does not recur.

### Handoff
- No new findings. No new escalations (no BUILD/TASK_MANAGER/PLAN/REQUIREMENTS routes — both reworks are correct and green).
- P17 complete: T1/T2/T3 approved pass 1; T4/T5 approved this pass. Full suite green per VERIFY ground truth.

Status: REVIEW_COMPLETE
