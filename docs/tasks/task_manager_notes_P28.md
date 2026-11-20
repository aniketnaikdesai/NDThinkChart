# Task Manager notes — Phase P28

Phase P28 (D84–D95, Journeys 74–77). Graph written against the approved plan
(`docs/plan.md` § *Phase P28*, `Status: READY_FOR_TASK_MANAGER`, line 8379) and
`docs/plan_review_P28.md` (`Status: APPROVED`), with `docs/architecture.md` § *Phase P28*
(S-P28-1…15, AR-P28-1…10) as the frozen-interface source.

Build baseline: **`ef04c5a`** (P27 close-out) — the plan's text names `0ff7964`, two commits
earlier; see *Baseline* below.

## Gates checked this run

- `docs/plan.md` § P28 ends `Status: READY_FOR_TASK_MANAGER`; `docs/plan_review_P28.md` ends
  `Status: APPROVED`. Neither is `CHANGES_REQUIRED` or `BLOCKED`.
- `docs/code_review/escalations.json`: 127 entries, **0 open** — nothing routed to Task Manager,
  so this is a fresh decomposition, not a rework.
- No `ESCALATED_TO_PLAN` open; `docs/plan.md` / `docs/architecture.md` settle every choice this
  graph needed (no plan escalation written, no task-graph blocker).
- `docs/requirements/requirements.md` § Phase P28 carries `AC-D84.1`–`AC-D95.3`, Journeys 74–77,
  A235–A240, R175–R180; every AC id used below was read from that file, not reconstructed.
- **Verification cache:** entries recorded for all three canonical files
  (`docs/plan.md` `exists:phase-p28-plan`, `docs/architecture.md` `exists:phase-p28-architecture`,
  `docs/codebase-map.md` `map-entry:p28`), but `verify_cache.py check --phase P28` still reported
  each as **`changed` / `phase mismatch`** even immediately after recording (the file holds several
  legacy P22–P27 entries per path; the checker appears to key on a different entry than the one just
  written). No `unchanged` report was therefore available to cite, so **every conclusion in this run
  was verified by direct read** of the file: the plan's eight waves and AP/FI blocks, the
  architecture's Components / Data Model / Frozen Interfaces / decisions, and the map's existing P28
  rows. A second, identical map claim was recorded as `map-entry:p28-v2` while probing the mismatch;
  it is a duplicate and can be ignored.

## Wave → task map

| Plan wave | Task(s) | Size | Dependencies |
|---|---|---|---|
| P28-01 (D87, D93) | **P28-T1** | S | — |
| P28-02 deliverables 1–5, 7, 8 (D84, D88) | **P28-T2** | M | — |
| P28-02 deliverable 6 (connection seam), split at its own seam | **P28-T3**, **P28-T4**, **P28-T5** | M each | P28-T2 |
| P28-03 (D89, D90) | **P28-T6** | M | P28-T2, T3, T4 |
| P28-04 (D85, D91) | **P28-T7** | M | P28-T6, T3, T5 |
| P28-05 (D86, D94) | **P28-T8** | M | — |
| P28-06 (D95) | **P28-T9** | M | P28-T8 |
| P28-07 (D92) | **P28-T10** | S | P28-T7, T8, T9 |
| P28-08 (records, fence) | **P28-T11** | S | all |

Wave frontier the graph produces: **1** {T1, T2, T8} → **2** {T3, T4, T5, T9} → **3** {T6} →
**4** {T7} → **5** {T10} → **6** {T11}. The two forced single-writer chains are preserved exactly:
`ui/main_window.py` runs **T2 → T6 → T7 → T10**, `main.py` runs **T8 → T9**. T1 (`ibkr/client.py`)
and T8 (`data/db.py`, `config/settings.py`, `main.py`) are file-disjoint from the window chain and
open with T2, as the plan states.

## Splits, and why

Only **one** plan wave was split: P28-02.

- **P28-T2** (deliverables 1–5, 7, 8) is the production half: `ibkr/error_codes.py`,
  `ibkr/market_data.py`, `ibkr/realtime_bars.py`, `ui/ticker_session.py`, `ui/main_window.py`, the
  two named re-baselines and the seven-case readiness suite. Honest action count ≈ 23 (five files,
  two test re-baselines, one new suite, three test runs) — inside the ~32 cap for a task whose
  invariants cannot be split without two owners for the same predicate.
- **Deliverable 6 alone** (the seventeen audited suites) is over the ~20-step target and close to
  the 32 ceiling: ~17 edit sites plus three suite runs. It also cannot be one task under the
  edit-site pinning rule — every `touches_files` file must appear in `read_files`, and the pack
  budget is ~8 files, while this deliverable has 17 edit sites. So it is split **at the plan's own
  seam** (deliverable 6 = "harness only, no assertion change") and then into three file-disjoint
  groups so each pack fits:
  - **T3** (6 files): the two `SimpleNamespace` stub suites + `test_d24_alarm_full_chain`,
    `test_d24_popouts`, `test_d24_smoke_gate`, `test_d27_aggregator_priming`;
  - **T4** (6): `test_d27_phantom_alarms`, `test_d27_reconnect`, `test_d27_stream_health`,
    `test_d28_2_sessions`, `test_d28_4_gate`, `test_d28_pacing`;
  - **T5** (5): `test_d28_tick_burst_baseline`, `test_d68_hold_balance`, `test_p13_hold_fix`,
    `test_p13_restore`, `test_phase3_fixpass`.
  That is all **17** files from the plan, no more and no less. The three groups are
  file-disjoint, so they run in one wave; each group's exit is its own suites green with only the
  seam line added.
- No other wave was split. T6 ≈ 22 actions, T7 ≈ 20, T8 ≈ 24, T9 ≈ 18, T10 and T11 are S and need
  no exception record.
- Two suites are deliberately given **no** seam (the plan says so and both are recorded in T3's
  scope): `test_p7_w1_coalesce` (it patches `TickerSession.ensure_rt_subscribed`, so a refusing
  gate simply means the patch is never reached) and `test_d67_forming_candle` (session-level, never
  reaches the window gate). Verify them at case level; do not add a seam line to either.

## Decisions carried into the packs verbatim

Each of these is reproduced in the task that owns it, not summarised away:

1. **The drop owes the attach** (T2, AC-P28-02-1 + description + case (d)) — `_rt_attach_pending`
   has exactly **two** setters: the readiness refusal and the drop. Before `_clear_prime_state()` in
   `_on_disconnected`, mark a session when **all three** hold: `_rt_req_id is None`,
   `symbol == self._current_symbol`, and an in-flight load (`_prime_timer.isActive() or
   _prime_req_id is not None or _prime_retry_pending`). Neither a background session nor an
   already-live line may be flagged; `_attach_deferred_rt_feeds()` consumes the flag in
   `_on_connected` after `_replay_subscriptions()`.
2. **`_clear_prime_state()` has four call sites** (T2, AC-P28-02-2) — `teardown`, `prepare_load`,
   `_fail_open_prime`, `_on_disconnected`; the three-statement request transitions in
   `on_historical_data_end` / `on_historical_error` are exempt, and no other *full* copy may remain.
3. **The harness seam is the predicate** (T3/T4/T5 descriptions and ACs; T2's case (b) is written as
   load-bearing) — `win._transport_ready = lambda: True`, plus `_transport_ready=lambda: True` on the
   two `SimpleNamespace` stubs, **not** `_ibkr_connected`, because the gate reads
   `ib_client.api_ready`. `tests/test_d84_d88_readiness.py` case (b) is what keeps the override a
   seam rather than a hole, and the packs say so.
4. **AC-D90.3's reload** (T6) — in `ensure_rt_subscribed`, when `_rt_req_id is not None` and
   `state == EXHAUSTED`, unsubscribe then `_subscribe_rt(reset_backoff=True)` **before** the holders
   bump; the predicate is the terminal **state**, not `retry_budget_spent`; `prepare_load` and
   `resubscribe_rt()` are explicitly not touched (see T6's AC-P28-03-1, which pins the
   "not-terminal" half).
5. **`_discard_popout(popout, exc)` tolerates `None`** (T7, AC-P28-04-1) — both open sites bind
   `popout = None` before their `try` (construction in `_open_popout`; `_ensure_restore_data_path`
   inside `_restore_popouts`' `try`).
6. **Two validator build notes** — T2's case (d) scopes "a second `_on_connected()` adds nothing" to
   the **deferred pass** only (`_replay_subscriptions` re-issues the now-registered line), and the
   prime-clear sites are located **by site name**, not by the plan's line ranges (the cited ranges
   stop one line short and include `_prime_reserved`).
7. **Standing constraints** — appended to every task description: `config/instance_lock.py` is the
   only new module; no new dependency (QLockFile ships with PyQt6); no migration (no `popouts`
   UNIQUE — FI-P28-3); no settings key; no reconnect-policy change; D1–P27 unopened apart from the
   declared `[revises P4/P7/P13/P16]` labels; sizes S/M only; **G5 is owner-run and never claimed**.
8. **Deletion-shaped deliverables** — `RealtimeBarsManager.replay_all` (T2) and the fence's
   absence assertion (T11) are expressed as a **legacy verbatim contract string** naming the symbol
   DELETED plus the AC that asserts its absence (`AC-D88.1`). Neither is an `existing` ref: an
   `existing` ref asserts the symbol is there, which would make the graph unverifiable exactly when
   the task succeeds.

## Test-command scoping (important for the reviewer)

Task `test_command`s are scoped to the files the task controls. P28-T2's gate reddens window
suites that attach a live feed until the seam lands, so T2's command is the readiness suite plus the
two suites that are genuinely unaffected (`test_ibkr_handshake_gate`, `test_qt_app_import_invariant`)
rather than the plan's cumulative exit list, which spans four tasks. The plan's fuller exit lists are
satisfied cumulatively at T6's and T7's exits (which name the audited window suites and depend on the
seam groups), and by the orchestrator's full-suite run at the end of the build. No assertion in any
audited suite is re-baselined; the only test deletions are the two the plan names.

## Baseline

`meta.baseline_commit` is **`ef04c5a`** (P27 close-out), the tree this build starts from. The plan's
delta-scope text anchors on `0ff7964` (the P27 build commit); the two commits between them are P27's
rework (`5096b78`) and close-out (`ef04c5a`), and `0ff7964..ef04c5a` touches
`tests/test_p27_throttle_double_signature.py` — a P27 file that is not in P28's allowlist. T11
therefore records `git diff --name-only ef04c5a`, so a P27 rework file is not misreported as a P28
scope breach. This is a deliberate, minimal deviation from the plan's anchor, not a change of scope.

## Two deliverables handled outside a task's `touches_files`

- **`docs/codebase-map.md`'s P28 note** (plan P28-08 deliverable 4) is **not** in T11's
  `touches_files`: the ownership table gives the map to Plan, and the P28 annotation rows already
  exist in the map from drafting (including the planned `config/instance_lock.py` row noted as
  landing in P28-06). Prior phase precedent is the same (P27's fence task touched only its suite).
  A reviewer finding no map edit in the P28 diff should read it as Plan-owned work, not as a
  missed deliverable.
- **G5** appears in T7's description and AC context as owner-run and never asserted, and T11 records
  it in the build result. No suite claims a process exit or a dock icon.

## Requirements ambiguity

None found: every AC this graph decomposes is stated in `requirements.md`, and the two places where
a literal reading would over-reach are already resolved in the approved artifacts (FI-P28-2 scopes
`AC-D92.1`'s grep to six live files; FI-P28-3 takes `AC-D95.2`'s lock branch). No entry was appended
to `docs/requirements/open_questions.md`.

## P28-T8 — pack fix and authorized re-baseline (post-dispatch)

**Trigger.** T8's implementation is complete and its own new suite
(`tests/test_d86_d94_startup.py`, 10 tests) is green, but the task returned `blocked` on its
contract check. `tests/test_db_backup.py::test_migrate_schema_aborts_drop_when_backup_fails`
(line 245) does `with pytest.raises(BackupVerificationError): DB()`, pinning the D65 **fatality**
that `AC-D86.1` / D86 / S-P28-5 explicitly revise to "the drop is skipped and the app **starts**".
The assertion encodes the superseded contract; it is not a regression, and the D86 path is behaving
as specified.

**Change (P28-T8 only, nothing else touched).**

- `tests/test_db_backup.py` added to `P28-T8.touches_files`; its `read_files` entry re-labelled from
  "read-only, stay green unmodified" to an edit site (lines `20-60`, `240-272`).
- T8's description gains item 4: exactly **one** case is re-baselined. The `pytest.raises` is
  replaced by construction-completes + `startup_notices()` holding exactly one entry naming the
  backup path and the cause. Every other assertion in that case is kept verbatim (`_RETIRED_TABLES`
  all present, `idx_positions_symbol_con_id` present, `positions` = 2, `trade_groups` = 1,
  `position_group_map` = 1), so the case still fails if a DROP runs or a row disappears.
- `AC-D86.2` narrowed from "the shipped D65 backup suite is green unmodified" to "green with the
  single declared re-baseline … every other case unmodified". New task AC **`AC-P28-05-4`** states
  the re-baselined case's pinned shape, with test **`P28-T8-09`** linked to it; `P28-T8-04` (the
  contract check) now names the one permitted delta.
- T8 reset from `blocked` to `in_progress` so the loop re-dispatches it as a finalize pass.
  `check_tasks.py` run: 0 errors, `execution_graph.json` regenerated (warnings are the pre-existing
  "new output file" notices only).

**Plan / exit-condition correction for the reviewer to confirm.** P28-05's exit condition says the
D65 backup suites stay green **"unchanged"**, and its diff allowlist is
`data/db.py`, `config/settings.py`, `main.py`, the new suite. Both are wrong by exactly one file and
one case: D86 revises the very behaviour that case pins, so that case is legitimately inside
P28-05's scope. The reviewer should correct the P28-05 exit condition to name this single
re-baseline. This is **not** a licence to re-baseline anything else — the verified-backup path
(`test_migrate_schema_drops_child_first_and_only_once`, `AC-D86.2`) and all `backup_before_drop`
cases must stay byte-identical, and no other task's scope changes.

**Lesson (carry forward).** When a phase revises a *safety* behaviour — here "a failed pre-drop
backup is fatal" becoming "skip and start" — the test that pins the old fatality is in scope of
that phase by construction. An exit condition demanding that suite stay "unchanged" is itself the
defect to correct: writing "suite unchanged" alongside an AC that revises the suite's subject
guarantees a blocked worker and a re-baseline request. Decompose such a phase with the pinning case
named explicitly as an edit site from the start.

## P28-T7 — pack fix: the eighteenth seam suite (post-dispatch, `task_manager_escalation`)

**Trigger.** T7's implementation is complete and its own seven-case suite
(`tests/test_d85_d91_popout_ownership.py`) is green, but `worker_selfcheck` returned `fail` on four
tests in **`tests/test_p13_attach.py`**: `test_attach_failure_unwinds_acquired_steps[sync]`,
`[registration]`, `[save]` and `test_failed_second_attach_leaves_survivor_undisturbed`. That file was
never in P28-02's seam enumeration, so it is still in wave P28-02's *pre-seam* shape.

**Diagnosis (the worker proved it; not re-derived here).** `_make_window` (lines 36–51) constructs
`win = MainWindow()` and never overrides the readiness seam, so `load_chart()` reaches
`_attach_live_feed`, the real `_transport_ready()` refuses (no live transport in an offscreen
harness), no hold is acquired, and `session._rt_holders` is `0` where the case asserts `>= 1`. Patching
only `MainWindow._transport_ready = lambda self: True` from outside the repo makes the unmodified file
pass 4/4. Every sibling suite already carries the line — `tests/test_p13_hold_fix.py:67` and
`tests/test_p13_restore.py:55` both read `win._transport_ready = lambda: True` directly after
`MainWindow()`.

**Change (P28-T7 only; T1–T6, T8–T11 untouched).**

- `tests/test_p13_attach.py` added to `P28-T7.touches_files` and to the pack's `read_files` as an edit
  site (lines `36-52`); pack is 5 files, inside the ~8 budget.
- Exactly **one** edit authorized there: in `_make_window`, immediately after `win = MainWindow()` and
  before `ids = iter(range(9001, 9200))`, add `win._transport_ready = lambda: True`. Same line, same
  position as the two sibling suites. No assertion, fixture value, monkeypatch target or other case
  changes.
- Description item 5 states it is a **harness seam only**: the window now intends a live attach, so a
  hold is acquired — the four cases pass because `_attach_live_feed` really runs, not because the gate
  was weakened. `MainWindow._transport_ready` is unchanged, and `tests/test_d84_d88_readiness.py` keeps
  the override a seam rather than a hole.
- New task AC **`AC-P28-04-4`** pins the invariant (one added line, four cases green with a real hold,
  gate and assertions untouched); test **`P28-T7-08`** enforces it by re-running the shipped suite plus
  the readiness suite and checking the file's diff is the one hunk.
- T7 left **`in_progress`** with its skeleton so the loop re-dispatches it as a finalize pass.
  `check_tasks.py`: 0 errors, `execution_graph.json` regenerated.

**Lesson — inventory by discovery, never by count (second occurrence in this phase family).**
P28-02's seam enumeration counted **seventeen** suites; the tree had **eighteen**. The missing one was
found only by a red team of four cases, after three seam tasks had already reported `done`. The correct
discovery rule is a *predicate over the tree*: every suite whose window factory reaches
`_attach_live_feed` — grep `_ibkr_connected`, `load_chart`, `MainWindow(` across `tests/`, and check each
hit's window factory by hand — never a list assembled from the plan's prose, and never a count taken on
trust. This is the **second inventory-by-count failure in the phase family**: P27 recorded "the two
pacing doubles" in its architecture, and the real inventory was ten doubles, six of them
signature-bearing (`task_manager_notes_P27.md:159`), which cost P27 a rework task and a discovery-based
guard. Both failures share one shape: a prose count was accepted as an inventory. Where a phase's
deliverable is "fix every X", the task must either (a) enumerate X by a grep/AST predicate at build
time and assert the *set* (as P27's `test_p27_throttle_double_signature.py` does), or (b) be written as
an invariant over the population ("every suite whose window factory reaches `_attach_live_feed` carries
the seam"), so a missed member is a red test rather than a silent gap. A count in a plan is a claim to
verify, not a scope boundary.

## P28-T10 — pack fix: the sibling suite that pinned the retired phrase (post-dispatch, `task_manager_escalation`)

**Trigger.** T10's implementation is complete — title, guard message, port comments and all three
guides now say read-only market data / places no orders / configuration check, and its own D92 suite
(`tests/test_d92_honest_description.py`) is green — but the task flagged one out-of-footprint red:
`tests/test_d86_d94_startup.py::test_paper_port_still_refused_through_the_same_dialog` (line 420)
asserts at line 433 `assert "trades live only" in message` — precisely the phrase D92 retires. That
suite was written by **P28-T8**, a sibling task in the same phase, and it encodes the old contract.

**Change (P28-T10 only; T1–T9 and T11 untouched).**

- `tests/test_d86_d94_startup.py` added to `P28-T10.touches_files` and to its pack's `read_files` as
  a single-assertion edit site (lines `415-445`). The pack is 8 files, at the ~8-file budget.
- Exactly **one** edit authorized there: line 433's `"trades live only"` assertion becomes an
  assertion of the new honest wording — the message states the app is a read-only market-data client,
  places no orders, and that the guard is a configuration check on the configured port
  (`'read-only market-data client'`, `'places no orders'`, `'configured port'`). Everything else in the
  case stays byte-identical: `settings.LIVE_PORT == 7496`, the `IBKR_PORT=7497` harness run, the
  non-zero exit, the message naming the offending port (7497 **and** 7496), and
  `payload["ui_main_window_imported"] is False` — so the case still reddens if the guard stops
  refusing 7497. Behaviour is unchanged; only the phrase is superseded.
- New task AC **`AC-P28-07-3`** states that this is the task's only out-of-footprint edit and why;
  test **`P28-T10-06`** enforces it by re-running the shipped T8 case and checking the file's diff is
  that one line. T10's description gains item 6 saying the same; its `test_command` now includes
  `tests/test_d86_d94_startup.py`.
- T10 left **`in_progress`** so the loop re-dispatches it as a finalize pass.
  `check_tasks.py`: **0 errors**, `execution_graph.json` regenerated (only the pre-existing
  pure-output-file warnings).

**Lesson — a retired string's blast radius is the whole tree, not the task's allowlist.** This is the
third variant of the same phase-family failure and it belongs next to the inventory lesson above: a
string retirement is also an *inventory* problem. P28-07 retired "trades live only" and enumerated the
six **live** files it owns (FI-P28-2) — but the phrase is also quoted by an *assertion*, and that
assertion lives in a suite a **sibling task wrote earlier in the same phase**. The plan's writing was
correct and the six-file live scope was the right scope for the product text; what was missing is that
the test tree is a consumer of the string too. The rule to carry forward: when a phase retires or
rewrites a user-visible string, the inventory of edit sites is every **occurrence** of that string —
product text *and* test assertions, including assertions written by a sibling task in the same phase
(at build time, grep the retired literal across `tests/` as well as the source tree) — and the task
that retires the string owns re-pointing each pinning assertion at the new wording while leaving the
behavioural assertions around it byte-identical. Writing "the suite is green unmodified" next to an AC
that retires the suite's quoted wording is the same defect class as the P28-T8 fatality re-baseline
recorded above: the exit condition and the AC disagree, and the worker discovers it as a red.

## P28-T10 — status flip only: `blocked` → `in_progress` (mechanical, `task_manager_escalation`)

**Trigger.** T10's work was already complete and verified — the repair pass described in the section
above re-baselined the one retired-phrase assertion at `tests/test_d86_d94_startup.py:433`, the
five-file suite is green, `worker_selfcheck` reports `verdict: pass`, `footprint_ok: true`,
`violations: []`, and `docs/build/results/P28-T10.json` exists with `status: done`,
`generation: 0`. But the graph still carried T10 at `blocked`, and `build_wave.py` consolidates a
result only for a task in `in_progress` — a `blocked` task's result is left in place while the loop
declares `WAVE: COMPLETE` with the task blocked and its dependent T11 unreachable.

**Change.** Exactly one field: `P28-T10.status` `blocked` → `in_progress`. Nothing else in the graph
was touched — no acceptance criterion, test, `touches_files` entry, description, dependency,
`context`, or size; T1–T9 and T11, `docs/build/results/**` and `docs/build/wave*` untouched
(`diff` against a pre-edit copy shows the single line). `check_tasks.py`: **0 errors**,
`execution_graph.json` regenerated (only the pre-existing pure-output-file warnings).

**The mechanical rule (carry forward).** A task that goes `blocked` for a *pack or contract* reason,
and whose work is then finished by a repair pass on the same task, **cannot be consolidated until its
status is `in_progress` again**. Neither of the loop's other levers covers it: consolidation refuses a
non-`in_progress` task, and `build_wave.py reset` accepts only `in_progress` (so it cannot lift a
`blocked` task either). The Task Manager's status flip is the only lever that re-opens consolidation
without editing the result — and it is a **bookkeeping** act, not a verdict: it must never be used to
skip a real block. The test this flip must pass before it is written is that the block's *cause* has
already been removed and independently verified (here: `selfcheck` pass + a green suite + a `done`
result on disk). If the cause is still present, the correct action is a graph change that removes it
(as in the T7/T8/T10 pack-fix sections above) or an escalation — never a bare status flip, which would
hand the loop a `done` claim for a defect nobody fixed.

**Generation.** The flip does not bump `generation` — `reset` and `packfix` do, this does not — and
T10's graph `generation` is absent (normalized to 0). The result's `generation: 0` therefore matches
exactly, so the next `advance` consolidates it as fresh with no re-record. If any later command resets
or packfixes T10 first (either bumps to `generation: 1`), the on-disk result becomes stale and needs a
one-line re-record at the new generation before it will consolidate.

## P28-T10 — second status flip: `in_progress` → `not_started` (orchestrator-requested)

**Why the first flip was insufficient.** Setting T10 to `in_progress` (previous section) did not
re-open consolidation; it made `advance` treat T10 as a task *in flight with no wave manifest*, so
`docs/build/wave.json` settled at `{"wave": 440, "status": "WAITING", "tasks": []}` and the on-disk
`done` result was never consolidated, leaving T11 (whose only dependency is T10) unreleased.
`build_wave.py` offers no standalone `consolidate`, and `reset` refuses T10 precisely because its
result is pending ("will consolidate normally") — so the graph's `status` is the loop's only lever.

**What changed.** One line: `docs/tasks/task-graph.json` line 1951, P28-T10 `"status":
"in_progress"` → `"not_started"`. Verified by `diff` against a pre-edit copy: exactly that one line,
nothing else. No change to ACs, tests, `touches_files`, description, `dependencies`, `generation`,
T1–T9, T11, or anything under `docs/build/results/`.

**Check.** `check_tasks.py`: **0 errors** (`OK: 11 tasks validated, execution_graph.json written.`),
only the pre-existing pure-output-file warnings. `graph_struct_sha256` is unaffected by a status flip
(status and `generation` are excluded from the structural hash), so `advance` will not refuse.

**Generation.** No bump. Publishing a wave copies the task's current generation verbatim
(`build_wave.py` ~L2030: absent/non-int → 0), and T10 has no `generation` key → the wave manifest
stamps `generation: 0`. Consolidation compares `_r_gen = 0` against `_g_gen = 0` (L1440-1450) → equal
→ fresh, so the existing result consolidates as-is with no re-record. Only `reset`, `packfix` and the
blocked skeleton/selfcheck fast-path bump (L1845, L2247, L2316) — none of which is in play here.
**Do not** run `reset` or `packfix` on T10 before it consolidates: either would bump it to
`generation: 1` and stale the on-disk result.

## P28 review rework — ESC-133…ESC-136 (2026-11-20, owner-approved)

**Trigger.** The review ended `REVIEW_COMPLETE` on commit `1404877` with exactly four open entries;
the owner approved all four on 2026-11-20. Routed: ESC-133 → BUILD **P28-T2**, ESC-135 → BUILD
**P28-T6**, ESC-134 + ESC-136 → Task Manager. Graph change: **the two escalated tasks re-scoped and
reset, plus one new task (P28-T12)**. No other task's ACs, tests, files, dependencies or status was
touched — T1, T3–T5, T7–T11 remain `done`, asserted one by one against a pre-edit copy of the graph.

### P28-T2 — ESC-133 (blocking): the dead-replay scan must detect USAGE, not prose

- `AC-D88.1`, case `P28-T2-05` and description item (e) rewritten: the scan is a **code-only AST
  walk** over every `.py` under `ui/`, `ibkr/`, `tests/`, flagging `ast.Attribute(attr='replay_all')`,
  `ast.Name(id='replay_all')` and `ast.FunctionDef`/`AsyncFunctionDef` with that name — string
  constants and comments excluded. The old text scan's single hit was
  `tests/test_p28_fence.py`'s **module docstring**, which merely names the symbol as absent.
- The fence stays unedited: a Do-not clause now names it (its docstring and its `not hasattr`
  assertion are the phase's negative assertion), and the case gains a two-sided self-check — a
  `mgr.replay_all()` snippet must be flagged, a docstring-only / `not hasattr` snippet must not — so a
  genuine reintroduction still reddens.
- Pack retargeted to the rework: `tests/test_d84_d88_readiness.py` is now a read/edit site (it was a
  create-only file), the fence is a read-only entry, and the implementation files' `why`s read
  "already landed — unchanged by this rework". Pack = 9 entries (8 `touches_files` + the fence); one
  over the ~8 budget is deliberate, because the pinning rule is hard and the fence entry is the only
  context for the false positive.

### P28-T6 — ESC-135 (nice-to-have): no attempt is spent while the transport is not ready

- New **`AC-P28-03-4`** and case **`P28-T6-10`**: the terminal state is structurally unreachable
  while the transport is not ready.
- Decided shape, two edits, no policy change: (i) `_on_rt_stream_error`'s first statement *after* the
  EXHAUSTED guard is `if not self._transport_ready(): return` — a post-drop echo no longer marks the
  health, emits a line or schedules a retry, so it can neither spend an attempt nor reach the terminal
  branch; (ii) `_retry_rt_subscribe`'s early return **splits**: not-ready → the timer starts
  `_RT_RECHECK_MS` (a transport-gated re-arm is not an attempt, because `next_retry_delay_s()`
  counts), while the separate no-symbol branch keeps `self._schedule_rt_retry()`. New module constant
  `_RT_RECHECK_MS = 5_000`.
- Explicitly untouched: `next_retry_delay_s`'s arithmetic, the `5/10/20/40/60/60 s` progression, the
  connected-path behaviour pinned by T6-01/02/08, and the `except IBKRNotReady` belt branch.
- Pack updated: `ui/main_window.py` read ranges now cover the constant block and both handlers
  (`134-140`, `1810-1835`, `2843-2900`, `2903-2925`); `tests/test_d89_d90_stream_budget.py` added as
  an edit site (it was missing from `read_files` entirely).

### P28-T12 (new, size S) — ESC-134 (blocking) and ESC-136 (nice-to-have)

- **ESC-134 — the last three seams.** `tests/test_p13_hold_probe.py:48`,
  `tests/test_d41_removal.py:256` and `tests/test_p7_w2_prime.py:38` each gain one line in
  `_make_window`, immediately after `win = MainWindow()`: `win._transport_ready = lambda: True` — the
  shipped shape and position of `tests/test_p13_hold_fix.py:67`. No assertion, expected value, case
  name, fixture or monkeypatch target changes; the 10 cases go green. Pins the difference from a
  product fix: the reviewer injected the seam into the *unmodified* files (10 passed) and traced
  `_fail_open_prime → _clear_prime_state → _on_session_prime_complete` (six prime markers cleared,
  `_rt_req_id` never touched). No production file is in T12's footprint; T2's case (b) keeps the
  override a harness stub rather than a hole.
- **Why a new task, not a widened T2/T6** (owner's scoping instruction): both escalated tasks are
  already reset for their own fixes, and the three suites were in **no** task's `touches_files`, so no
  re-dispatch could repair them without a footprint violation — widening would have duplicated work
  exactly as P27's T7/T8 did.
- **No dependency edge**, deliberately. T12's prerequisite — the readiness gate itself — landed in
  `1404877`; T2's rework touches only `tests/test_d84_d88_readiness.py`, T6's only `ui/main_window.py`
  and its own suite, so nothing T12 assumes is changed by either rework. All three file sets are
  disjoint, so the three fixes can run in one wave. (An edge would only add a wave, not correctness.)
- **ESC-136 — the diff-shape guarantee gets a test.** New suite
  `tests/test_p28_seam_diff_shape.py`: one parametrized case over the **21-file** audited seam set
  asserting, per file, that `git diff ef04c5a -- <file>` adds exactly one line, that it matches the
  seam assignment (`win._transport_ready = lambda: True`, optional trailing comment, or the
  `_transport_ready=lambda: True` stub keyword), and that it removes nothing. Single exemption:
  `tests/test_p7_w4_streaming.py`, whose 20 removed lines are P28-T2's retired `replay_all` case and
  whose added line is still exactly one seam. Two self-checks keep the detector honest (a synthetic
  `- assert`/`+ assert` patch must be flagged; a docstring-only addition is still an added line), and
  the case **skips with a named reason** once a commit outside the P28 family exists in
  `ef04c5a..HEAD`.
  - Why phase-bounded: the repo's own precedent (S-P24-5; `tests/test_p28_fence.py`'s docstring) is
    that a git diff pinned against the phase base reddens every later phase. Inside P28 the guarantee
    now enforces; after P28 the phase diff is closed and a later phase's edits to those files are its
    own. Only the **base** `ef04c5a` is pinned — no phase commit hash, no file/line count.

### The measured seam inventory (as instructed, recorded here)

- **42** suites reach `MainWindow._attach_live_feed` at runtime; **21** need the readiness seam —
  **18 present** at review (`test_p7_w4_deferral`, `test_p7_w4_streaming`, `test_d24_alarm_full_chain`,
  `test_d24_popouts`, `test_d24_smoke_gate`, `test_d27_aggregator_priming`, `test_d27_phantom_alarms`,
  `test_d27_reconnect`, `test_d27_stream_health`, `test_d28_2_sessions`, `test_d28_4_gate`,
  `test_d28_pacing`, `test_d28_tick_burst_baseline`, `test_d68_hold_balance`, `test_p13_hold_fix`,
  `test_p13_restore`, `test_phase3_fixpass`, `test_p13_attach`) and **3 missing**
  (`test_p13_hold_probe`, `test_d41_removal`, `test_p7_w2_prime`).
- **18 further suites** get at least one refusal but assert nothing about the live RT line
  (`test_d24_9_popout_persistence`, `test_d28_2_load_chart_button`, `test_d42_depth_floor`,
  `test_d45_removal`, `test_d48_mode_parity`, `test_history_backfill`,
  `test_history_backfill_disconnect`, `test_history_backfill_loadpath`, `test_p13_host_error`,
  `test_p14_cache_guard`, `test_p14_indicator`, `test_p14_lifecycle`, `test_p15_continue`,
  `test_p15_expiry`, `test_p15_surfacing`, `test_p19_prefetch_wave`, `test_p7_w1_persist`,
  `test_p7_w3_wide`) — they can never redden on this gate, and T12 seams none of them.
- **1** refusal is by design: `tests/test_d84_d88_readiness.py` case (b) exercises the real predicate
  refusing.
- Provenance: the reviewer's instrumented full-suite run, `docs/code_review/review_log_P28.md`
  section 3. T12 records the four counts in its build result (AC-P28-02-S6, manual) instead of
  rebuilding the instrumented harness inside the suite.

### Statuses, generations, loop mechanics

- `P28-T2`, `P28-T6` and `P28-T12` are `not_started`; every other task keeps `done`.
  `meta.status` = `READY_FOR_BUILD`.
- `generation` bumped so a pre-rework `done` result can never consolidate as the fixed one: T2
  absent → `1`, T6 `2` → `3` (status and `generation` are both excluded from `graph_struct_sha256`,
  so `advance` will not refuse). Both on-disk results predate the escalations' `opened` timestamps
  (2026-11-20T05:15/05:16), so the rework dispatch is not skipped by the freshness rule.
- `check_tasks.py`: **OK — 12 tasks validated, `execution_graph.json` written**, 0 errors. The
  warnings are the pre-existing pure-output-file notices (the new suite files their tasks create,
  plus T12's new suite).

**Lesson — the inventory, not the diff shape, was the failure; both are now closed.** This is the
third inventory-by-count miss in the phase family (P28-02 counted 17 suites, the tree had 18; the
review instrumented the population and found 3 more). ESC-136 is right that a diff-shape assertion
alone would have caught none of it — but it is also right that "each changed file differs only by its
seam assignment(s)" was prose nothing checked. Both are now in place: the **enforcement** is a
diff-shape case enumerating all 21 (so a suite that later loses its seam line, or gains a second
edited line, reddens), and the **population** is a recorded, provenance-carrying count. The rule to
carry: an inventory AC must name the *set* (enumerated in the AC, asserted by a test), and any
"nothing else changed" clause beside it needs a test or must be labelled a review-time check — never
left as prose in an AC.
