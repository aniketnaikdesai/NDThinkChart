# Code Review Log — Phase P9 (alarm/drawing fixes + recolor both-semantics)

## Pass header
- **Tier: FULL** (phase-final pass is always full; also fails light conditions:
  two overlap pairs P9-T2/P9-T5 and P9-T3/P9-T4, three size-M tasks, one
  `unconfirmed_file` warning on P9-T6). Diff-first review of every P9 task's
  `files_changed`, plus the B.6 mock-endpoint scan and the usage-doc judgment.
- **Ground truth consumed, not re-derived:** `precheck.json` (fail_fast: none;
  scope P9-T1..T6; overlaps informational only), `test_verification.json`
  (verdict **pass**, exit 0, 73.88 s full offscreen suite).
- **Scope:** P9-T1..T6 incl. TM-round follow-ups
  (ESC-080/081/082/085/083/084, PRE-001..005).

## A. Failure diagnosis — none
`failures.json` is `{}`; build log ends `READY_FOR_REVIEW` with all six tasks
done. No blocked tasks to diagnose. (P9-T6's wave-176 BLOCKED was re-driven
in wave 178 and is done; the blocking cause is addressed under PRE-005 below.)

## B. Quality review (all done tasks)

### P9-T1 — alarm persistence isolation + retry queue — no finding
Diff (`ui/ticker_session.py`): both `mark_triggered` call sites
(`_on_aggregated_bar`, `_evaluate_burst_alarms`) now go through
`_persist_alarm_trigger` (try/except, symbol+alarm-ID error log, ID queued,
queue bounded by active-alarm count); `_flush_trigger_retries` runs on
subsequent bars and `reload_alarms` with no duplicate emits (flush only
writes the DB). Store signature frozen. Matches ACs; 4/4 tests pass and the
full suite is green. Error-per-bar while the DB is down is one line per
flush — acceptable, not a finding.

### P9-T2 — read-only group-name cell — no finding
One-line flag clear (`& ~ItemIsEditable`); Rename remains the sole path with
a regression guard. 2/2 pass.

### P9-T3 — active-group re-validation on reload — no finding
`_refresh_drawing_groups` re-validates against the current symbol's groups
(unknown/foreign → None → Ungrouped) and ends with
`_apply_active_draw_group()`, so the tool state is re-pushed as the ACs
require; ticker-change clear preserved. 3/3 pass.

### P9-T4 — group+color commit pipeline — no finding
Chain verified end to end on the live tree: `gestures.js::setActiveGroup`
(single writer, null/non-numeric → ungrouped+default) → `drawingItem` stamps
both → `LwcDrawingSurface.set_active_group` publishes the
`set_active_group` op (`_optional_int` exists at `ui/lwc_view.py:1587`) →
`_on_page_drawing_committed` forwards unchanged → `_on_drawing_created`
coerces foreign-symbol groups to None (AR-P9-1, no crash) →
`_apply_active_draw_group` re-pushes on reload (`:1953`) and symbol change
(`:1803`). Observation only (no action): a foreign-coerced commit keeps the
stamped color with group None — consistent with the stored-color rule, and
the ACs only pin the null group. 3 pytest + node suite pass.

### P9-T5 — recolor member-repaint + leave-group rule — no finding
`DrawingStore.repaint_group_members` (one UPDATE over current members;
leavers untouched) called from `_recolor_group`; ungroup/reassign/delete
paths preserve stored colors; D50 drag path untouched (composition only).
Static-method-on-module-`db` matches the file's convention; group IDs are
globally unique PKs so no symbol scoping is needed. 3/3 pass.

### P9-T6 — batch gate — no finding
Five suites 16/16, zero skips/xfails; diff confined to the five items;
frozen interfaces and order-code absence hold (independently re-grepped:
zero order tokens in the P9 production diff). Footprint flag on wave 178
(added `task_id` to its own stale wave-176 archive record) is the Q-56
precedent, git-ignored artifact, status/keys otherwise untouched — benign,
not a finding.

### B.6 mock-endpoint scan — CLEAN (blocking check, no finding)
Grep over the reviewed diff for `mock|fake|stub|simulat` ×
`endpoint|client|service|server|api|harness` returns one hit: a pre-existing
D39 comment at `ui/ticker_session.py:156` ("tests / stub hosts") describing
the fallback owner — no mock endpoint, client, service or harness in
production code, and no production import of a test fake.

### Usage-doc judgment — no finding (explicit)
Candidates: `USAGE.txt` (untouched), `docs/` (touched = build artifacts
only, not user docs), `usage.md` (untouched). P9 refines an
already-documented feature (`usage.md:181` "Sets… named groups with
color/lock/visibility") without contradicting any documented statement and
adds no new user surface (retry queue is invisible resilience; read-only
cell, re-validation, stamping and member-repaint are behavior refinements).
All six tasks carry `doc_required: false` (Task Manager decision) — concur.
No doc update routed.

### Overlaps / sequencing — no finding
Both overlap pairs ran serialized per dependencies (T2+T3 wave 173 →
T4 wave 174 → T5 wave 175); the merged tree is coherent
(`_refresh_drawing_groups` carries T3's validation and feeds T4's re-push).

### Unattributed working-tree changes — noted, not findings
`ALARM_AND_DRAWING_CODE_REVIEW.txt`, `POPOUT_CHART_CODE_TRACE_REPORT.txt`
are owner-dropped analysis inputs (tracked per 8f72f42), not build outputs.

## C. Escalation close-out

### PRE-005 (open → addressed this pass)
Re-verified myself: `docs/build/results/_archive/wave178_P9-T6.json` carries
top-level `task_id: "P9-T6"`, `status: done`, 3/3 pass, and the independent
full-suite run (`test_verification.json`, exit 0) includes the
`test_archived_results_carry_task_id` gate green — the PRE-005 substance
(malformed P9-T6 result) is delivered, same pattern as PRE-001..004.
Flipped to `addressed` in `escalations.json` with `verified` note. Nothing
else was open.

### TM-round follow-ups (already `addressed`; re-verified holding this pass)
- **ESC-080** (T40 fixture model): week/month T40-T04 params pass on the live
  tree (5 passed); `data/bar_aggregator.py` bucketing untouched. Holds.
- **ESC-081** (duration pins): `test_ibkr_handshake_gate.py` +
  `test_p7_w3_wide.py` green (10 passed), eight-row fail-closed shape kept.
  Holds.
- **ESC-082** (archive hygiene): `test_lwc_failure_visibility.py` green as
  part of the 27-test targeted run; latest-per-task gate intact. Holds.
- **ESC-085** (usage docs): intent holds — `usage.md:133` timeframe range
  plus `usage.md:163-164` D48 section (picker, 2Y/10Y, Ext-Hours note).
  Nuance for future passes: the `verified` line's `USAGE.txt:217` reference
  is stale because the owner-committed doc consolidation (`c9e2b77`,
  "LWC-only user guides") deliberately rewrote USAGE.txt (63 lines) into an
  index role pointing at `usage.md` for timeframe detail — the D48 content
  was moved, not lost. Not a regression; no action.
- **ESC-083** (predicate consolidation): single `def is_daily_or_coarser`
  in `services/time_collapse_service.py:53`; `chart_model.py:36` and
  `main_window.py:86` import it; no other def. Holds.
- **ESC-084** (dead set): `data/bar_aggregator.py:107` dispatches via
  `timeframe in _CALENDAR_BUCKETED_TIMEFRAMES`. Holds.
- **PRE-001..004**: already `addressed`; substance confirmed by analogy
  (every P9 newest result carries `task_id`, direct-read verified).

## Findings routed
None. No new `escalations.json` entries.

## Verdict
P9 is clean: six tasks done, full suite green, no open escalations, no new
findings. Nothing requires rework by any agent.

Status: REVIEW_COMPLETE
