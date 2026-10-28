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
