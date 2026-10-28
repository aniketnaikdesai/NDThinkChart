# Code Review — P8 (D48: weekly/monthly timeframes), phase-final — 2026-10-28

**Reviewer:** Code Reviewer agent. **Phase:** P8 (D48, Batch 23, lite lane).
**Scope (incremental):** `P8-T01`…`P8-T05` — every P8 task is newer than the last
`REVIEW_COMPLETE` (`docs/code_review/review_log.md:3986`, D44 follow-up); this is the
first P8 pass, so the whole phase is in scope. No checkpoint split (phase-final).
**Entry:** `docs/build/build_log.md` ends `Status: NEEDS_CODE_REVIEW`; T01–T04 `done`,
T05 `blocked`.
**Tier: FULL pass** — required unconditionally for a phase-final pass, and independently
forced: a blocked task is present, `test_verification.json` is red, and size-M tasks
touched shared files (`ui/main_window.py`, `data/bar_aggregator.py`).
**Verification inputs (ground truth, consumed not re-derived):**
- `docs/code_review/precheck.json` (gen. 2026-10-28T05:30:29Z) — scope `[P8-T01..P8-T05]`,
  `fail_fast: []`, no overlaps, `doc_candidates` 3 (1 touched). Consumed as ground truth;
  no git-diff / doc-scan / footprint re-derivation performed.
- `docs/code_review/test_verification.json` — `verdict: fail`, exit 1, 73.54 s,
  8 failed (4× `test_t40_t04_chunked_multi_request_continuity[1 week|1 month …]`,
  `test_timeframe_config_untouched`, `test_archived_results_carry_task_id`,
  `test_t13_planner_contracts_and_scoped_suites` knock-on, `test_t12_…_diff_clean`).
  The suite is genuinely red; not re-run (one read-only baseline probe excepted, §A).
- `docs/build/build_log.md` (waves 155–164), `docs/build/failures.json` (P8-T05 entry),
  `docs/build/results/_archive/wave{155,156,159,160,161,163,164}_P8-*.json`,
  `docs/tasks/task-graph.json` (P8 graph), `requirements.md` (D48/AC-D48.1–7, A113–A120),
  `architecture.md` (Phase P8, S-P8-1–7), `docs/code_review/escalations.json` (prior output).
  Each read once; `build_log`/`escalations.json` references below are to those reads.
**Method:** diff-first over every task's `files_changed` (`git diff HEAD` for the 10
production files; the 6 test/probe/doc files are new/untracked and were read directly);
one offscreen probe of the shipped bucketing anchors (read-only, no repo write);
one clean-HEAD worktree run of the two pin tests to settle baseline attribution
(worktree removed afterwards); mock-endpoint grep over the reviewed diff.

## A. Failure diagnosis — P8-T05 `blocked` (all 8 suite failures attributed: 4+1+2+1)

P8-T05's own gate file is green (8/8 per the worker; the file read in full — 79 lines —
asserts the probe record, the D41–D47/marker/stack presence, the eight-timeframe
enumeration with a stale-wording guard, and the two priming-table rows; the worker's
over-broad-assertion fix is intent-preserving, no weakening). What blocks T05 is the
full-suite gate (AC-D48.7). Root causes:

| id | failures | class → route | severity | one-line |
|---|---|---|---|---|
| ESC-080 | 4× T40-T04 `[1 week\|1 month]` + t13 knock-on | `bad_task_breakdown` → TASK_MANAGER | **blocking** | T40 fixture has no weekly/monthly bar model; P8-T01 bucketing meets AC-D48.2 |
| ESC-081 | handshake `test_timeframe_config_untouched` + t12 `…_diff_clean` | `bad_task_breakdown` → TASK_MANAGER | **blocking** | exact-6-row pins vs mandated S-P8-1 rows; no P8 task owns the files |
| ESC-082 | `test_archived_results_carry_task_id` (5 files) | `bad_task_breakdown` → TASK_MANAGER | **blocking** | gate globs superseded intermediates; newest results all carry `task_id` |

### A1. ESC-080 — backfill T40-T04 vs the new anchors (4 params + 1 knock-on, one invariant)
`TIMEFRAMES = list(TIMEFRAME_CONFIG.keys())` (`test_history_backfill.py:418`) newly
pulls in the two S-P8-1 rows, but `_session_bars` (`:97–120`) models **every** timeframe
as per-trading-day 04:00-ET bars stepped by nominal fixed `TIMEFRAME_SECONDS` — for
week/month that yields one 04:00 bar/day, which cannot represent Monday-00:00-ET weeks
or month-boundary months. Observed: index-0 shift of exactly 86400 plus 2 extra
in-span bars in all 4 params; `delivered == expected` still holds upstream, so the
divergence is in span/filter semantics under the new bucketing, not in transport.
P8-T01's bucketing is exonerated: its own DST-fold / February / cross-year cases pass,
and my probe of the shipped helpers gives `week_bucket_start(Thu 2026-04-30)` =
`Mon 2026-04-27 00:00 ET`, `month_bucket_start` = `2026-04-01 00:00 ET` — exactly
AC-D48.2. `test_p7_w1_cap.py::test_t13_…` fails only as a subprocess re-run of this
same suite (tail: same 4 failures) → knock-on, same escalation, no separate entry
(repeat-invariant rule: one invariant, one escalation). Suggested direction: follow-up
task owning `tests/test_history_backfill.py` extends the fixture with an AC-D48.2
weekly/monthly bar model (or scopes `TIMEFRAMES`); production bucketing must not move.

### A2. ESC-081 — duration pins contradict the approved addition
Both pins assert exact 6-row equality (`handshake:154`, `t12:352`) and fail on the two
mandated rows. `t12` is internally contradictory: its comment (`:364–365`,
"`1 week/1 month` are out of scope") scopes P8 out while `:352` forbids any added row.
No P8 task owns either file → TASK_MANAGER (extend the approved dicts + approval-record
loop; keep the fail-closed shape). Baseline note: the worker's "red on baseline" is a
clean-worktree artifact — a fresh worktree lacks the untracked
`docs/build/approvals/*` files, so both tests fail earlier at `os.path.exists`
(`t12:357/370`, `handshake:165`); in the real pre-P8 tree the equality asserts pass.
These two pins are **newly reddened by P8**, not pre-existing red.

### A3. ESC-082 — archived-results gate vs superseded waves
All 5 offending files are superseded intermediates (`wave156_*` → stamped by `wave163_*`,
`wave159_P8-T03` → `wave163`, `wave160_P8-T05` skeleton → `wave161`; plus
`wave154_P7-T08.PRIOR_PHASE`). Newest results all carry `task_id` + passing selfcheck
(precheck `files_verified` confirms). The gate globs the whole git-ignored archive dir;
the files are written by `build_wave.py`, outside every worker footprint → TASK_MANAGER
(prune superseded files or scope the gate to latest-per-task; keep the `task_id`
requirement — it caught real PRE-001…004 gaps). PRE-002…004's substance is delivered;
only stale intermediates keep this leg red (see §C).

## B. Quality review — T01–T04 `done` (all diffs read; anchored to arch/requirements)

| id | task | category | class → route | severity | one-line |
|---|---|---|---|---|---|
| — | P8-T01 | — | — | — | Anchors correct (probe §A1); nominal keys beside (not inside) the grid. One nit → ESC-084 |
| ESC-084 | P8-T01 | quality | code → BUILD | nice-to-have | `_CALENDAR_BUCKETED_TIMEFRAMES` defined (`bar_aggregator.py:99`), never used |
| — | P8-T02 | — | — | — | Planner-verified (8/8), docstring rows documentation-only per S-P8-5, probe record names both combos with no 321 and plausible counts (105 weekly / 121 monthly). No finding; the "out-of-footprint" note resolves: final `files_changed` == `touches_files` exactly |
| ESC-083 | P8-T03 | consistency | code → BUILD | nice-to-have | `is_daily_or_coarser` triplicated (time_collapse canonical + chart_model + main_window copies) vs S-P8-4 "one shared predicate"; equivalent today, cycle-free to consolidate |
| — | P8-T04 | — | — | — | Six gates + 1950.0/8190.0 minutes + picker parity + visibility guard all match S-P8-4/6/7; `None`/unknown-timeframe behaviour unchanged (still `False` down every branch). No finding |
| ESC-085 | P8-T04 | consistency | doc → TASK_MANAGER | nice-to-have | `usage.md:134` "Select timeframe (1 min – 1 day)" now stale (range is 1 min – 1 month); no P8 task owns user docs |

- **Architecture/requirements consistency:** config rows match A113/A116 exactly, appended
  after `1 day` (S-P8-1); bucketing beside the fixed grid (S-P8-2); planner untouched with
  period-based floor exclusion (S-P8-3); canonical full-session mode forcing `extended_hours=True`
  for daily+ with one shared cache key (S-P8-4/A118); docstring-only priming rows (S-P8-5/DG98);
  no new visibility rows (S-P8-6/DG97); 1950.0/8190.0 RTH-session minutes (S-P8-7). No deviation.
- **Usage-doc coverage:** candidates `USAGE.txt` (untouched), `docs/` (touched — probe record,
  not user docs), `usage.md` (untouched). D48 is user-facing (new picker entries) → ESC-085.
- **Mock-endpoint containment (B.6, blocking scan):** `mock|fake|stub|simulat` ×
  `endpoint|client|service|server|api|harness` over the P8 production diff → only benign
  hits (`session_bands` docstring `_Fake` test helper, "Phase-1a seam stub" comments,
  engine-less stub that **raises**). No mock endpoint in production; no test fake imported
  by production code. Clean.
- **Test integrity:** precheck `flags: []`, no skips/xfails; no weakened assertions found in
  the reviewed test diffs (T05's enumeration fix constrains stale wording while asserting
  the positive eight + both new keys).
- **Footprint:** every task's verified files match its declared `touches_files`; no overlaps.

## C. Escalation close-out — nothing flipped (no statuses changed this pass)

- **ESC-075…078 (BUILD, open, no linked artifact):** nothing relevant changed. P8 adds
  daily+ timeframes only; ESC-075 (1-min starvation), ESC-076 (162-cancel storms),
  ESC-077 (watchdog vs continuation), ESC-078 (prime starvation) are all intraday
  wave/pacing-scope with no P8 interaction. Left open.
- **ESC-079 (PLAN, open):** the thing it was routed for now exists — `docs/architecture.md`
  carries **S-P7-1 "Budget invariant + per-load cap (answers ESC-079)"** (`:5936`: one
  quarter of `MAX_HISTORICAL_PER_600S` per load, floor satisfied monotonically across
  loads, bounds in budget-window terms), with the P7 machinery (per-load cap, oldest-first
  resume, window-relative watchdog, prime precedence) landed per the build log. Recorded
  for owner close-out; status untouched.
- **PRE-001 (P7-T01, open):** `changed_since_last_review: null`, out of P8 scope. Untouched.
- **PRE-002…004 (P8-T02/03/04):** substance verified — the newest results
  (`wave163_P8-T02`, `wave163_P8-T03`, `wave164_P8-T04`) all carry `task_id` with passing
  selfchecks and match their footprints. The gate's remaining complaint is stale
  intermediates only → folded into ESC-082. Statuses untouched.

## D. Pipeline state for the Orchestrator

- **Full-suite attribution is complete (8/8):** 4× backfill + 1 knock-on → ESC-080;
  2× duration pins → ESC-081; 1× archived-results gate → ESC-082. No unattributed red.
- **P8-T05 stays `blocked`** until ESC-080/081/082 land (all three are breakdown/pipeline
  follow-ups outside any current task footprint; no P8 code is at fault).
- **T01–T04 are sound:** anchor math independently probed, no arch/requirements deviation,
  no mock endpoint, footprints clean. Their only findings are nice-to-haves
  (ESC-083 dedup, ESC-084 dead set).
- **New findings this pass:** ESC-080, ESC-081, ESC-082 (TASK_MANAGER, blocking);
  ESC-083, ESC-084 (BUILD, nice-to-have); ESC-085 (TASK_MANAGER, nice-to-have).
  No finding duplicates an open entry (ESC-075…079, PRE-001…004 are distinct matters).
- **Docs written:** this file (`docs/code_review/review_log_P8.md`) + 6 appended entries
  in `docs/code_review/escalations.json`. No code or any other file touched.

Status: REVIEW_COMPLETE

---

# Code Review — P8 close-out pass (T06–T09 + Q follow-ups), phase-final — 2026-10-28

**Reviewer:** Code Reviewer agent (subagent close-out). **Phase:** P8 (D48, Batch 23).
**Scope:** `P8-T06`…`P8-T09` (follow-ups to ESC-080/081/082/085), the Q-46/Q-48
follow-ups, ESC-083/084 nice-to-haves, PRE-001…004 + PRE-005…009 adjudication,
and close-out of ESC-080/081/082/083/084/085. ESC-075…079 explicitly out of scope
(prior phase — left untouched). Entry: committed tree @ `8f72f42`, clean.
**Tier: FULL pass** — phase-final, required unconditionally.
**Ground truth consumed, not re-derived:** `docs/code_review/precheck.json`
(gen. 2026-10-28T14:09Z — scope `[P8-T01, P8-T03, P8-T06…P8-T09]`,
`fail_fast: [P8-T08]` via PRE-005…009, `doc_candidates` 3 with both user docs
touched); task-graph P8 (T01–T04, T06–T09 `done`, T05 `blocked` — gate evidence
is the suite itself). `test_verification.json` on disk was stale (red on the
superseded gate), so per the brief I ran the suite fresh rather than trusting it.

## A. Fresh verification (mine, this pass)

- **Full offscreen suite:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
  -q -o addopts=""` → **1204 passed, 3 skipped, exit 0, ~70 s.** Suite is green;
  P8-T05's AC-D48.7 gate evidence holds.
- **Targeted re-run:** `test_lwc_failure_visibility.py` +
  `test_history_backfill.py` + `test_ibkr_handshake_gate.py` + `test_p7_w3_wide.py`
  → all green (no failures).
- **PRE-005…009 adjudication — CONFIRMED INVALID, not appended:** the 5 flagged
  paths (`wave154_P7-T08.PRIOR_PHASE`, `wave156_P8-T02`, `wave156_P8-T04`,
  `wave159_P8-T03`, `wave160_P8-T05`) are byte-for-byte the 5 files P8-T08's
  TM-approved task description orders deleted (AC2 lists each path verbatim);
  all 5 confirmed absent on disk (`GONE` × 5); P8-T08's verified files are
  `tests/test_lwc_failure_visibility.py` only — no worker edit outside footprint.
  The precheck "violation" is the sanctioned prune observed as a diff, the same
  class as the `PRIOR_PHASE` consolidation rename. No `BUILD` escalation exists
  or is filed; the Orchestrator's invalidation stands on this evidence.

## B. Follow-up verification (each re-verified on the live tree, not on report)

| id | landed work | how confirmed |
|---|---|---|
| ESC-080 (T06) | `_session_bars` weekly/monthly AC-D48.2 branch | `test_history_backfill.py` green incl. all 4 week/month T40-T04 params; production `bar_aggregator.py` bucketing untouched |
| ESC-081 (T07) | eight-row duration pins, exact-equality kept | both pin files green in direct re-run; approval loop still P7-five-only |
| ESC-082 (T08) | latest-per-task gate + 5-file prune | gate file green; 5 paths absent; `task_id` requirement intact (newest results all carry it) |
| ESC-085 (T09) | docs-only | `usage.md:134` reads "1 min – 1 month, including 1 week and 1 month"; `USAGE.txt:217` D48 section present |
| ESC-083 | predicate consolidation | single `def` at `time_collapse_service.py:53`; `chart_model.py:36` + `main_window.py:86` import it; repo grep finds no other def |
| ESC-084 | dead set wired up | `_bucket_start` (`bar_aggregator.py:107`) dispatches via `in _CALENDAR_BUCKETED_TIMEFRAMES` |
| PRE-001…004 | newest results well-formed | direct reads: `wave147_P7-T01`, `wave163_P8-T02`, `wave167_P8-T03`, `wave164_P8-T04` all carry `task_id` + `done`; gate green |
| Q-46 / Q-48 | test-book alignment / pinned chunk math | commits `8e74373` / `d941e54` in history; suite green over them |
| Q-49 | — | no Q-49 artifact exists anywhere (history, notes, build log all searched): nothing outstanding, no finding filed |

- **Usage-doc judgment:** candidates `USAGE.txt` + `usage.md` both `touched: true`,
  both verified above with D48-correct content. Gate met, no finding.
- **Mock-endpoint containment (B.6):** scoped production files show zero
  mock/fake/stub/simulat × endpoint/client/service/server/api/harness hits; no
  production module imports `tests.*` (repo grep, 0 hits). Clean, non-downgraded.
- **Test integrity:** no skips/xfails added in the P8 test diffs; no weakened
  assertion found (T06 adds a branch, T07 extends dicts keeping exact equality,
  T08 keeps the fail-closed newest-missing check plus a synthetic proving case).

## C. Escalation close-out

- **Flipped to `addressed` with per-entry `verified` (10):**
  ESC-080, ESC-081, ESC-082, ESC-083, ESC-084, ESC-085,
  PRE-001, PRE-002, PRE-003, PRE-004. Each re-verified above by direct
  file reads and test runs, never on the owning agent's say-so.
- **PRE-005…009:** never entered `escalations.json` (correctly); confirmed
  invalid here with evidence (§A). Nothing to flip.
- **ESC-075…079: left `open`, untouched** — prior-phase scope per the brief; no
  P8 interaction re-diagnosed this pass.

## D. Findings this pass

**None.** No new code, quality, consistency, security, or gap findings. The P8
batch (weekly/monthly timeframes + widened durations, T01–T04 + T06–T09, Q-46 /
Q-48) is fully landed with a green 1204-test suite on the committed tree, both
user docs correct, and every P8-routed escalation closed on verified evidence.

Status: REVIEW_COMPLETE

## Focused close-out pass — ESC-075/076/077/078 (P7 1-min-chart defects) — 2026-10-28

**Tier:** full (phase-final duty for the in-scope slice: four pre-existing BUILD
escalations from a prior phase; precheck clean, 0 fail-fast). **Entry:** full
offscreen suite green on the committed tree (re-measured this pass: 1204 passed /
3 skipped / exit 0 in 73 s, superseding the stale `test_verification.json`
fail which names a `wave167_P8-T03.json` state that no longer holds — that file
now carries `task_id` and `test_lwc_failure_visibility.py` is 11/11 green).
**Scope note:** ESC-079 (PLAN) and ESC-083/084 leftovers untouched per the brief;
this pass owns only the four BUILD close-outs. No code or task-graph edits made;
only `escalations.json` (four status flips) and this log were modified.

**Method:** for each ESC, read the P7 implementation diff (commit `7cba534`: per-load
cap, per-chunk persist, coalescing, refund, superseded-162, window-relative
watchdog, strand clearing, prime precedence) against the live files, confirmed
the guards drive real `MainWindow`/`TickerSession` paths (recording fake
transport + in-memory bar cache only), ran all 8 P7 test modules green
(37 passed), ran one neutralising mutation per fix (restored byte-identical via
`git checkout`, tree verified clean after), and re-ran the full suite green.

- **ESC-075 (blocking, 1-min stuck + storm) → addressed.** Cap
  `floor(MAX_HISTORICAL_PER_600S/4)` as a tunable fraction; cap-exhaustion yields
  with remainder queued and no continuation timer; per-chunk persist+render with
  flush-before-cancel and finaliser owing only never-completed members; T12 proves
  monotonic oldest-first convergence to the 30-session floor. Mutations:
  cap-to-huge fails cap-T11; persist neutered fails persist-T11.
- **ESC-076 (should-fix, nine 162s) → addressed.** Identical-triple reload
  coalesces (cancels empty, generation and reqIds unchanged, wave completes);
  triple change still cancels and fences; pre-issue-only refund (empty-budget
  no-op, interval clock untouched); superseded-162 at debug with no status-bar
  error, genuine 162 keeps warning, status and single-retry. Mutation:
  superseded branch neutralised fails coalesce-T14.
- **ESC-077 (should-fix, fixed 120 s watchdog) → addressed.** Bound
  `max(window/5, wait+window/20)` from `pacing_manager._hist_window`; re-armed on
  every scheduled continuation including the 162-retry path; strand stops the
  timer, clears the queue, fences the generation, finalises exactly once (timeout
  and disconnect strands both proven; late end-markers and continuation ticks
  no-op). Mutation: fixed 120000 bound fails watchdog-T11.
- **ESC-078 (nice-to-have, prime starvation) → addressed.** Deferred prime holds
  `_prime_reserved` and slips a queued wave by exactly one
  `HISTORICAL_MIN_INTERVAL_S`; reservation released on issue, fail-open, backstop,
  teardown and reload; a skipped prime warns (naming symbol and timeframe) and
  counts `_prime_skipped_count`, while a merely deferred prime is never counted.
  Mutation: slip removed fails prime-T11.

**Escalation close-out:** flipped ESC-075/076/077/078 to `addressed` with per-entry
`verified` (code sites, guard names, mutation evidence, suite result), each
re-verified on the live tree, never on the worker's word. ESC-079 left `open`
untouched. No new findings; no follow-ups opened — every sub-claim the four
reports named is implemented and guarded by a discriminating test.

Status: REVIEW_COMPLETE
