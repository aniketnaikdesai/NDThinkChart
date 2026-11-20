# Task Manager notes — Phase P27 (D77–D83)

**Plan input:** `docs/plan.md` § *Phase P27* (`Status: READY_FOR_TASK_MANAGER`, committed `8fdc27f`),
`docs/architecture.md` § *Phase P27* (S-P27-1…S-P27-7, AR-P27-1…AR-P27-9), `docs/codebase-map.md`
P27 note (lines 205–226). **Baseline:** `623809e`. **Requirements:** `requirements.md` Phase P27,
Journeys 71–73, `AC-D77.1`–`AC-D83.2`, A230–A234, R170–R174, DG135.
**No escalation.** RG-P27-1 is `addressed`, so `AC-D77.1` is asserted literally (identity multiset,
before/after coverage identity, containment) exactly as the plan and AP-P27-2 state.

## Graph shape

| Task | Wave in plan | Size | Depends on | Touches |
|---|---|---|---|---|
| P27-T1 | P27-01 (D77+D82+D83) | M | — | `services/backfill_service.py`, `tests/test_d77_d82_d83_planner_identity.py` |
| P27-T2 | P27-02 (D78) | S | — | `ui/ticker_session.py`, `tests/test_d78_prime_retry_reachable.py` |
| P27-T3 | P27-03, D81 half | M | — | `ibkr/pacing.py`, `ibkr/market_data.py`, `ibkr/id_manager.py`, two pacing doubles, `tests/test_d79_d80_d81_budget_honesty.py` |
| P27-T4 | P27-03, D80+D79 half | M | P27-T2, P27-T3 | `ibkr/pacing.py`, `ui/ticker_session.py`, `data/bar_cache.py`, the two re-baselined cases, the same new suite |
| P27-T5 | P27-04 | S | P27-T1…T4 | `tests/test_p27_fence.py` |

Execution order produced by `check_tasks.py`: **{T1 ∥ T2 ∥ T3} → T4 → T5**. This preserves the plan's
`P27-01 ∥ P27-02 → P27-03 → P27-04` ordering: nothing depends on `ui/ticker_session.py` before P27-T2
writes it, and P27-T4 carries both edges (the shared file *and* the logical premise that a request that
never crossed the wire holds no slot).

## Sizing decisions (and one deviation from the plan's four waves)

1. **P27-03 was split into P27-T3 (D81) and P27-T4 (D80+D79).** Not a re-scope: every deliverable of the
   plan's P27-03 is assigned, in the plan's order, to one of the two tasks, and no file, AC or do-not is
   dropped. The reason is sizing, not parallelism: P27-03 as written touches **eleven** files (five
   production, four test files, two doubles) across five edited functions, eight deletion sites, two
   re-baselined cases and a six-case suite — over the ~20-step target and over the ~8-file pack budget.
   Split halves carry 6 files / 4 ACs each. The split is on the plan's own seam: D81 is *one rule*
   ("budget is stamped only by a send that crossed the wire"), and D80's refund retirement is a
   *consequence* of it (the plan says so: "D81 makes D80's refund vacuous"), while D79 is unrelated
   cache hygiene. D80+D79 share `ibkr/pacing.py` with D81 only for the one-line deletion of
   `refund_historical_slot`, so no invariant is quartered.
2. **The new suite is written by P27-T3 and extended by P27-T4.** Both edits are serialised by
   `touches_files` **and** by the dependency edge. P27-T4's description and pack instruct it to read
   P27-T3's cases (a),(b),(c),(f) first and not change them; its `test_command` runs the whole suite, so
   a P27-T4 regression in a P27-T3 case reddens P27-T4, not a later phase.
3. **P27-T5 is verification-only** (`touches_files` = the fence suite alone, matching the P26-T4
   precedent); the delta-scope record is a build artefact in the wave result, not a hash-pinned test, as
   the plan directs.

Every task is inside the step-fit target (~12–20 actions; no task above ~32). No `L` task, no `needs_graphify`.

## Carry-forward constraints written into the packs

- **Plan purity.** `plan_requests` stays free of DB, clock and Qt (P27-T1's pack carries the isolated-
  interpreter purity case as a read-only pin; P27-T5 pins the import block).
- **Presence boundary (RC-1/AP-P27-3).** The half-open rule is confined to `_bar_level_missing_spans`;
  `present_days` keeps `window_start <= ts <= window_end`, its signature and its futures branch. P27-T1
  case (h) asserts **10 of 10** daily days present under both modes, `find_missing_spans` returning `[]`,
  and a **test-local** half-open variant returning **0 of 10**.
- **AP-P27-4 (no re-baselining).** P27-T1's description names
  `tests/test_history_backfill.py::test_t40_t04_chunked_multi_request_continuity` for both `1 day` params
  and its test command runs the D42 presence/granularity suites; a red D16/D42 assertion is an escalation.
  Only the two named D80 cases may be re-baselined, and only in P27-T4.
- **Q-80 / prime tests.** P27-T2 records that the two prime-retry tests in
  `tests/test_d28_3_historical_pacing.py` were made clock-hermetic at `623809e` and must stay green
  unchanged.
- **`n ≥ 1` batch semantics (P26 ESC-129 at `bda354f`).** P27-T3's AC-3 and pack state that the
  reservation is consumed per send and stamped once for `n ≥ 1`, while an empty `generic_batch(0)`
  reserves and stamps nothing.
- **No retuning, no new module/dependency/migration/settings key.** P27-T2 states no pacing constant is
  retuned; P27-T5 pins the five settings values, `per_load_historical_cap()`, the watchdog fractions and
  `TIMEFRAME_CONFIG`. D1–P26 stay unopened.

## Verification cache

`verify_cache.py check --phase P27 --files docs/plan.md docs/architecture.md docs/codebase-map.md`
reported `changed` for all three (`phase mismatch`), so every claim below was verified by reading the
files directly in this run; the conclusions are recorded back into the cache under phase P27.

## Pack fix — retiring-symbol contracts (P27-T4), post-build

**Trigger.** After all of P27-T1…T4 had built, `check_tasks.py` exited nonzero with exactly two errors —
`P27-T4: contract symbol 'refund_historical_slot' not found in ibkr/pacing.py` and
`P27-T4: contract symbol 'get_last_timestamp' not found in data/bar_cache.py` — so `build_wave.py advance`
refused to consolidate, holding T1's and T4's queued `done` results.

**Cause.** P27-T4's pack listed the two symbols it exists to delete as
`{"ref": …, "status": "existing"}`. `check_tasks.py` reads `existing` as "this symbol MUST resolve in the
source file", so the graph became unverifiable exactly when the task succeeded. The pack contradicted
itself: its `new` contract entry for `tests/test_d79_d80_d81_budget_honesty.py` already asserted the
*absence* of both symbols, via AC-D80.2 and AC-D79.1.

**Correction (nothing else changed).** Both entries were converted to legacy verbatim contract strings,
which the graph validator skips by design (its `isinstance(c, str): continue` branch):

- `ibkr/pacing.py:refund_historical_slot` → string stating the symbol is DELETED by this task and its
  absence is asserted by `AC-D80.2`. Do not re-add it.
- `data/bar_cache.py:get_last_timestamp` → string stating the symbol is DELETED by this task and its
  absence is asserted by `AC-D79.1`. Do not re-add it.

Each symbol appeared exactly once in the graph, so exactly two entries changed. T4's other nine contract
entries (including the `new` test-file contract) are untouched. No task's `status`,
`acceptance_criteria`, `tests`, `touches_files`, `expected_artifacts` or description changed; no task was
added, removed or re-scoped. T4 stays `in_progress` with its queued result so the build loop consolidates
it rather than re-dispatching, and `meta.status` stays `READY_FOR_BUILD`.

**Rule for future phase graphs.** A task whose job is to *delete* a symbol must express that as a legacy
verbatim contract string naming the symbol as DELETED plus the AC that asserts its absence — never as
`{"status": "existing"}`, which asserts the opposite. `existing` refs are for symbols a task consumes and
must keep resolving; a "contract" that the right answer destroys is a pack defect that only surfaces once
the build succeeds.

**Verification.** `python3 ~/.config/opencode/scripts/check_tasks.py` →
`OK: 5 tasks validated, execution_graph.json written.` (0 errors; the five `touches_files … not in context
read_files` lines are pre-existing benign warnings for pure-output test files) — `graph_struct_sha256`
`1a2ad3c6d0123ee2a6106e7791b46ed42ceb2a01ef3b634f58a04b65e469bbb7`.

## Rework — P27-RW1: the `throttle` signature change's test-double sweep (P27-T6), post-T5-fence

**Trigger.** T5 attempted and returned `blocked` with a **skeleton** result: `tests/test_p27_fence.py` is
written and green (12 passed), but the phase's own change reddened three pre-existing tests. Nothing is
committed (HEAD is still `8fdc27f`, the approved plan).

**Root cause (proven, not inferred).** P27-T3 made `PacingManager.throttle` keyword-only
`throttle(*, stamp: bool = True)` (`ibkr/pacing.py:135`) and `ibkr/market_data.py` now calls
`throttle(stamp=False)` at three request sites (`:111` `req_mkt_data`, `:142` `req_contract_details`,
`:177` `req_sec_def_opt_params`). Three tests install a **zero-argument** double, so the keyword call
raises `TypeError: … got an unexpected keyword argument 'stamp'` — inside a Qt slot in the option-stream
case, which turns the exception into PyQt6 `qFatal` → SIGABRT (exit 134):

| File:line | Broken case |
|---|---|
| `tests/test_d65_option_stream.py:191` | `test_P23_T9_AC1_on_populates_both_ladders_negative_and_partial_legs` (exit 134) |
| `tests/test_d27_reconnect.py:148` | `test_d27_3_drop_reconnect_reissues_with_rebound_reqids` (FAILED) |
| `tests/test_d45_removal.py:516` | `test_zero_transmit_walkthrough` fixture (ERROR) |

The other five `lambda: None` sites (`test_d27_aggregator_priming:26`, `test_d48_mode_parity:118`,
`test_d67_forming_candle:569`, `test_d27_stream_health:56`, `test_d41_removal:252`) pass only because
their paths stub the generic request seam (`win.md_manager.req_historical_data`,
`win.rt_manager.subscribe`) or drive RT-bar/historical paths, so no `req_mkt_data` /
`req_contract_details` / `req_sec_def_opt_params` call reaches the double. They are **not** exempted from
the fix: the guard sweeps all ten.

**Task added.** `P27-T6` (size `S`, `dependencies: [P27-T3]`) — the three doubles become
`lambda *, stamp=True: None` (assertions untouched, one line per file), plus
`tests/test_p27_throttle_double_signature.py`: a run-time AST discovery of every `throttle` double under
`tests/` (8 `monkeypatch.setattr(…, "throttle", …)` sites + 2 class `def throttle` methods) with a
keyword-`stamp` predicate, a pin on the real keyword-only signature, and a negative control proving a
zero-argument double reddens the guard. `touches_files` = exactly those three files + the guard.

**Guard placement — its own file, not the phase fence.** `tests/test_p27_fence.py` is P27-T5's artefact,
already written, and T5 will be re-dispatched as a finalize worker; a second task writing it would either
serialize against an in-flight task or silently lose the guard when the fence is regenerated. The guard
therefore lives in `tests/test_p27_throttle_double_signature.py`, is discovered dynamically (so a later
phase's double is covered without editing it), and is reached by T5's full-suite pass anyway.

**Sequencing (explicit).** T5 is `in_progress` holding a skeleton result. `build_wave.py` resets a first
skeleton to `not_started` (with a generation bump) and only re-admits it when every dependency is `done`,
so **P27-T6 was added to P27-T5's `dependencies`**: T1–T4 → T6 → T5-finalize. The fix therefore lands
before T5's finalize pass, which verifies the green suite and records the delta. T5's
`acceptance_criteria`, `tests`, `touches_files` and fence content are unchanged.

**The one edit to T5 (allowlist amendment, recorded openly).** The plan's P27-04 delta allowlist names
"the two pacing doubles"; that count is wrong (there are ten, and six are signature-bearing in effect).
Left as written, T5's finalize would classify four legitimately changed files as a scope breach. Its
description now states that the phase delta also carries the three doubles plus the guard file and that
they are in scope. No other T5 text, and no T1–T4 text, changed.

**Exit condition.** The full offscreen suite (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -m
'not webengine' -q`) green. **Recorded exception:** `tests/test_d64_batch_gate.py::test_p22_t5_ac2_shared_seam_record`
asserts a clean `tests/` working tree and can only pass once the phase is committed — it has bitten four
runs and is **not** a code defect, so it is recorded, not "fixed" here. **Recommended future task (not
done now):** make that gate compare against the phase base (`git diff --name-only <baseline> -- tests/`
restricted to paths outside the phase's own allowlist) instead of demanding an empty working tree; a
pre-commit build can never satisfy a clean-tree assertion, and unbounded phase scope is the real
property worth pinning.

**Lesson for future phase graphs.** *A signature change must enumerate every test double, not trust a
doc's count.* The architecture's "two pacing doubles" list was the only inventory consulted, so the sweep
stopped at two while the tree held ten (`grep -rn '"throttle"' tests/` + `grep -rn 'def throttle' tests/`).
Two defences are now in the graph: every task that changes a callable's signature carries a
discovery-based guard over its doubles (not a list), and the AC is written as the invariant "every double
accepts the keyword form", never as the enumeration "these two doubles are fixed".

**Verification.** `python3 ~/.config/opencode/scripts/check_tasks.py` →
`OK: 6 tasks validated, execution_graph.json written.` (0 errors; the six `touches_files … not in context
read_files` lines are the benign pure-output-test-file warnings). `meta.status` stays `READY_FOR_BUILD`.

## Pack fix — P27-T6 (static-guard footprint)

**Trigger.** P27-T6's worker completed the work (its task command green, 61 passed) but exhausted its steps
before writing a result, and `worker_selfcheck.py`'s footprint check would have failed against the pack as
scoped. The Orchestrator invoked a **pack fix**, not a re-scope: T1–T5, the task set and the guard file are
unchanged.

**Defect (pack-side, mine).** T6's description said "change exactly the three" and called the other five
`lambda: None` sites safe "because their paths never reach the double". That is behaviourally true and was
still the wrong scoping: `AC-P27-06-2` is a **static, zero-exemption AST guard** which scans `tests/**/*.py`
and rejects every zero-argument `throttle` double, reachable or not. With three files in `touches_files`
the AC was unsatisfiable inside the declared footprint.

**Changes (P27-T6 only; T1–T5 untouched).**

- `touches_files` gained the five missing files: `tests/test_d27_aggregator_priming.py`,
  `tests/test_d48_mode_parity.py`, `tests/test_d67_forming_candle.py`, `tests/test_d27_stream_health.py`,
  `tests/test_d41_removal.py`. All eight zero-argument sites are now edited to `lambda *, stamp=True: None`.
- Description: "change exactly the three" and "the other five are safe" replaced with the correct statement
  — the guard is a static AST scan with zero exemptions, all eight sites install the zero-argument shape, and
  the five already-passing files are changed for signature conformance alone with every assertion untouched.
- `AC-P27-06-3`: the "only edit in each file is the installed double's signature" clause now also permits
  the second in-footprint change in `tests/test_d65_option_stream.py` — `_make_window`'s
  `monkeypatch.setattr(pacing_mod.pacing_manager, "record_request_slot", lambda: None)` pacing-seam stub,
  the same class of harness double. The AC records why: D81 moved the interval stamp out of `throttle()`
  into `record_request_slot()`; without the stub the 16 leg sends stamp the generic interval,
  `generic_wait_for_batch(16)` returns 0.3 s, and P26's all-or-nothing `replay_all` defers the reconnect
  replay via a `QTimer.singleShot` that never fires under pytest, yielding 0 new `reqMktData`. It is
  scheduling-only: no production line changes, and the asserted `reqMktData` counts are unchanged.
  `AC-P27-06-2` is left exactly as written — its zero-exemption invariant is the correct one.
- `expected_artifacts`, `P27-T6-02` and `P27-T6-04` wording aligned with the eight-file reality (the
  test command and the discovered-set assertion now name all eight, and -04 names the permitted stub).
- Pack trimmed to 9 `read_files` entries to hold the ~8-file budget: dropped `ibkr/pacing.py`,
  `ibkr/market_data.py` and `tests/test_d65_option_chain.py`. Their interfaces are inlined verbatim at
  dispatch through the existing `contracts` refs and no task edits them.

**State.** `P27-T6` stays `in_progress` with **no** result file, so the build loop re-dispatches it as a
finalize pass (run the suite, write the result) rather than redoing the work. `check_tasks.py` →
`OK: 6 tasks validated` (0 errors; the same six benign pure-output-file warnings). `execution_graph.json`
was regenerated and `meta.status` stays `READY_FOR_BUILD`.

**Lesson.** *A static invariant AC puts every matching site in the footprint.* When the assertion scans
source (AST, grep, schema walk) rather than exercising behaviour, "behaviourally unreachable" is not
"out of scope" — the `touches_files` set must be the same set the scan discovers. This sharpens the
earlier lesson ("a signature change must enumerate every double") with its scoping corollary: the AC's
form decides how wide the footprint has to be, so write the footprint **after** the AC, not before.

---

## Rework wave — 2026-11-20 (ESC-130 / ESC-131 / ESC-132, owner-approved 2026-11-20)

**Baseline.** The P27 build is committed at **`0ff7964`** (phase baseline `623809e`); `P27-T1`…`P27-T6` are
`done`; the phase review is `REVIEW_COMPLETE` with exactly three open entries in
`docs/code_review/escalations.json`. **The diff base for this wave is `0ff7964`, not `623809e`** — any delta
list this wave records is `git diff --name-only 0ff7964`. `623809e`'s phase allowlist (`docs/plan.md`
P27-04 deliverable 3) is not the base here.

**Gate checked.** `docs/plan.md` § *Phase P27* still ends `Status: READY_FOR_TASK_MANAGER` (`:8144`);
`docs/plan_review_P27.md` is `Status: APPROVED`; no phase section was regenerated and no decided P27
behaviour is reopened. `check_tasks.py` → **`OK: 8 tasks validated, execution_graph.json written`** (the same
benign pure-output-file warnings as before, plus one for `P27-T7`'s new suite).

### What was added — two S tasks, one wave

| Task | Escalation | Scope | Size | Depends on | Touches |
|---|---|---|---|---|---|
| **P27-T7** | **ESC-130** (nice-to-have, BUILD, `task_id: P27-T4`) | Restate `_register_history_request`'s comment at `ui/ticker_session.py:990-991`: the live sites are the registration stamp and the accepted-bar re-stamp in `on_historical_bar`; record that P27-T4 deleted the issue-time re-stamp. Comment text only. Guard: a new source/AST suite. | S | **P27-T4** | `ui/ticker_session.py`, `tests/test_p27_stamp_sites_documented.py` |
| **P27-T8** | **ESC-131** (nice-to-have, BUILD, `task_id: P27-T6`) | Extend `FIXED_SETATTR_FILES` from three to **eight** files (all the `setattr` doubles P27-T6 swept) and add the discriminating per-required-pair presence test. Discovery, predicate, `KEYWORD_DEF_FILES`, negative control untouched. | S | **P27-T6** | `tests/test_p27_throttle_double_signature.py` |
| — | **ESC-132** (nice-to-have, TASK_MANAGER, `task_id: P27-T3`) | **No task.** The criterion is qualified to the four generic paths; the edit belongs to the Requirements Analyst (see below). | — | — | none |

No size exception is used (the ~32-step holistic exception is not invoked): T7 is a two-line comment plus one
source suite (~6 steps), T8 is one constant block, one comment and one parametrized test (~7 steps). Both sit
far inside the ~20-step target. Neither is split — each is a single cluster. The three fixes are
file-disjoint, so they are **one wave**: the execution graph's frontier is `{P27-T7 ∥ P27-T8}` (the third fix
writes no file).

### Edge rationale (logical, not file-level)

- `P27-T7 ← P27-T4` (already `done`): T7's comment states T4's deletion of `mark_history_request_issued`
  as a fact and its regression pin asserts that absence. The relation is not file overlap alone — the
  comment's subject is the post-T4 state of the stamp.
- `P27-T8 ← P27-T6` (already `done`): T8 edits the guard T6 wrote and its required list *is* T6's swept file
  set (`P27-T6.touches_files`). Both the file and the premise are T6's.

### ESC-130 — one comment; the "optional" second site is already correct

The escalation offers an optional matching note at the D80 rule in `_cancel_history_requests`. It is
**already there**: `ui/ticker_session.py:1033` reads *"The slot was recorded after the send; a wave never
refunds."* (P27-T4's restatement), and `_retry_silent_chunk:1210-1211` states the same rule for the retry
path. T7 therefore edits **one** comment and its pack marks `:1019-1045` read-only with an explicit "do not
restate" — otherwise a worker would duplicate the rule a third time, which is the drift class this escalation
exists to stop.

The replacement wording is stated verbatim in T7's `new` contract, so the comment cannot drift from the test:
stamped at registration and on each accepted bar (`on_historical_bar`); P27-T4 deleted the issue-time
re-stamp; this registration stamp is the only issue-side one. The discriminating assertion is the absence of
the retired string `re-stamped at issue` (verified: **one** occurrence in the tree, at `:990`), which is RED
before the edit and GREEN after.

### ESC-131 — the presence set becomes the swept set

Measured on the live tree: **eight** `monkeypatch.setattr(..., "throttle", ...)` doubles
(`test_d65_option_stream.py`, `test_d27_reconnect.py`, `test_d41_removal.py`, `test_d27_stream_health.py`,
`test_d48_mode_parity.py`, `test_d67_forming_candle.py`, `test_d45_removal.py`,
`test_d27_aggregator_priming.py`) plus **two** class-based `def throttle` doubles
(`test_d65_option_chain.py:109`, `test_ibkr_contract_details_d22.py:115`) — the ten the escalation names.
T8's required tuples therefore become all ten.

The new test is the point, not the constant: parametrized over the ten pairs, it removes one pair from
`_DISCOVERED` and asserts `_assert_required_files_present` raises. On the pre-change three-file list **five**
of those ten cases fail (the helper never looks at those five paths), so the test is genuinely RED→GREEN and
pins the escalation's actual complaint — a double that stops being discoverable must fail, not silently
drop its case. The discovery/predicate/negative control are explicitly out of scope and read-only in the
pack; `KEYWORD_DEF_FILES` (the two class doubles) already covers its pair.

### ESC-132 — decision: **(a) qualify the criterion**; the edit is the Requirements Analyst's

`AC-D81.2` is unqualified, while the shipped rollback covers only the four generic `MarketDataManager` paths
(`req_mkt_data`, `req_contract_details`, `req_sec_def_opt_params`, `req_matching_symbols`). `req_historical_data`
still allocates an id at `:76` before an unwrapped send at `:79`, so a raising send there leaves an id gap.

**Route (b) — a follow-up BUILD task carrying the historical rollback — is rejected**, for four reasons:

1. **It re-scopes a decided deliverable.** `docs/plan.md` P27-03 deliverable 2 says, for
   `req_historical_data`, *"move the gate in front of `get_id`; the send and `record_historical_slot()` stay
   where they are"* — the absence of a rollback there is the approved plan, not an oversight. Wrapping that
   send is new behaviour the plan explicitly did not schedule; the brief for this wave forbids re-opening
   decided P27 behaviour.
2. **There is no defect to fix.** `AC-D81.1` holds on that path (`record_historical_slot()` runs after the
   send, so a raise charges nothing), and the id gap costs nothing: `IdManager.release_id` only rolls back
   the newest allocation and `set_next_valid_id` is forward-only, so ids stay increasing — the property the
   wire actually needs.
3. **The AC already has the branch.** `AC-D81.2` reads *"either no id is consumed by the failed attempt **or
   the phase records why an allocated id is acceptable**"*. Qualifying the criterion is not a weakening: it
   names the branch the phase chose and the scope in which it chose it.
4. **Churn on a closed, reviewed data path for zero user-visible gain.** The phase is committed and reviewed;
   editing `ibkr/market_data.py` to close a harmless gap buys nothing and puts a reviewed send path at risk.

**The edit is not mine to make** — `docs/requirements/requirements.md` is the Requirements Analyst's file, and
Task Manager never edits it. Delivered instead as a flag: `docs/requirements/open_questions.md` **Q121**
(append-only, non-blocking) with the exact replacement wording below.

**Recommended replacement (Analyst's edit; keep the `**AC-D81.2` label — see the fence note):**

> - **AC-D81.2 (ids are not burned on a failed generic send)** Given the same failing send on one of the four
>   generic market-data request paths (`req_mkt_data`, `req_contract_details`, `req_sec_def_opt_params`,
>   `req_matching_symbols`), When the client call raises, Then the id that attempt took is released before the
>   exception propagates, so the id sequence has no gap caused by a failed generic send. On
>   `req_historical_data` the send is not wrapped and an allocated id may be left unused: no pacing budget is
>   charged there (the slot is recorded only after the send, `AC-D81.1`), the counter has already moved past
>   the id so it is never reissued, and ids remain increasing, which is what the wire requires — this is the
>   criterion's "records why an allocated id is acceptable" branch, recorded rather than fixed. (Measurable:
>   `id_manager` sequence assertion across the four generic paths; the historical path's send stays
>   unwrapped by design.)

**Minimum edit, if the Analyst prefers not to restate the paragraph** — append to the existing sentence:
"… the id sequence has no gap caused by a failed **generic** send (`req_mkt_data`, `req_contract_details`,
`req_sec_def_opt_params`, `req_matching_symbols`); on `req_historical_data` an allocated id may be left
unused, since the budget is unchanged and ids only need to increase."

### Fence check — `tests/test_p27_fence.py` stays valid

Read at `:1-296`. It pins **only**: the requirements markers (existing-repository sentence, `D41`–`D83`
headings, Journeys 71–73, the AC ranges, A/R ranges, Current Tech Stack), the five pacing settings,
`per_load_historical_cap()`, the two watchdog fractions, `_PRIME_BACKSTOP_MS` / `_prime_backstop_ms`,
`TIMEFRAME_CONFIG`'s nine rows, and the planner's Qt/DB/clock-free import block.

- It does **not** pin the `_register_history_request` comment or any comment text → **ESC-130's edit leaves it
  valid**. Neither does it pin `tests/test_p27_throttle_double_signature.py`'s file lists → **ESC-131's edit
  leaves it valid** (the fence's *docstring* mentions the eight swept files, and that prose stays true).
- It is in **no** task's `touches_files`; both new tasks read it read-only, and their packs say "never edit".
- The one constraint it does impose on ESC-132: `test_acceptance_criteria_ranges_are_present` matches
  `\*\*AC-D81\.2\b`, so the reworded criterion must keep the `**AC-D81.2` prefix (it asserts presence, never
  the body). Recorded in Q121 as well.

### Wave shape, and the one interaction worth recording

`P27-T7` and `P27-T8` are file-disjoint (`ui/ticker_session.py` + a new suite vs the guard module) and run in
one wave. T8's guard enumerates `tests/**/*.py` at import time and therefore *reads* T7's new module; **no
edge is added** because T7's module contains no `throttle` double (it is a source-text/AST test over
`ui/ticker_session.py`), and `doubles_in_source` returns `[]` on a `SyntaxError`, so even a partially written
file cannot redden T8. Recorded so the missing edge is not later read as an omission.

### Invariants preserved

- `P27-T1`…`P27-T6`: statuses, ACs, tests, footprints and descriptions untouched; the graph keeps them so the
  phase record stays readable.
- No production behaviour reopened, no pacing constant, no settings key, no module, dependency or migration;
  the only production file in either footprint is `ui/ticker_session.py`, and only a comment line in it.
- `doc_required: false` on both — neither changes user-facing behaviour or a documented default (a source
  comment and a test guard), so the Reviewer's doc check does not apply.
- No guarantee lives only in a comment: T7's restated claim is enforced by P27-T7-01's source assertion; T8's
  "all ten are enforced" is enforced by P27-T8-01's per-pair removal cases.
- `docs/code_review/escalations.json` untouched (Code Reviewer's file) — all three entries stay `open` for its
  verification pass. Nothing under `docs/requirements/` was edited except the single permitted **Q121**
  append, which is a flag, not a criterion change.

## Graph correction — 2026-11-20: `P27-T7` / `P27-T8` deleted (redundant with the build loop's own reset+rework)

**Trigger.** Orchestrator: `build_wave.py advance` reset the two escalated tasks themselves — **P27-T4**
(ESC-130) and **P27-T6** (ESC-131) — both rework workers completed and self-checked green, and the same
`advance` then published `P27-T7` / `P27-T8` `in_progress` with no worker and no result file.

**Why deleting them is the correct fix, not a workaround.** Each new task's *entire* deliverable had already
landed in the escalated task's own rework:

- **`P27-T7`** carried only the `_register_history_request` comment restatement, and **T4's rework already
  wrote it** (registration + accepted-bar, no issue-time re-stamp). Running T7 would have re-edited the same
  lines for zero behavioural change.
- **`P27-T8`** carried only widening the throttle-double guard's required set to the eight `setattr` files
  plus both class doubles, and **T6's rework already did it** (61 tests green). Running T8 would have
  re-edited the same constant and test for zero change.

Both were leaves (nothing depended on them); the removal is two task objects and no other field. T1–T6 are
untouched: `P27-T1`…`P27-T5` and **`P27-T6` `done`** — T6's rework result was consolidated on the previous
advance; no status was reset, no AC, test, footprint or description reopened. `tests/test_p27_fence.py` was not
read or written by this correction, and `docs/code_review/escalations.json` was not touched — all three
entries stay `open` until the reviewer re-verifies them.

`check_tasks.py` → **`OK: 6 tasks validated, execution_graph.json written`** (0 errors; the same benign
pure-output-file warnings for T1–T6 as before). `execution_graph.json` was regenerated in that same run, so the
structural hash matches the corrected graph.

**Lesson (the reusable part).** An escalation entry that is already routed to a task keeps a live *owner*:
`build_wave.py` resets **that** task and reworks it directly. Scoping a *new* task for the same fix does not
close that route — so the wave publisher sees two items for one change and queues both, duplicating the work
and producing two misleading `done` results. There are only two coherent moves when an open escalation is
routed to a task that is still in the loop:

1. **Leave it to the build loop** — reset and rework the routed task (what happened here), and scope nothing
   new; or
2. **Deliberately take it away from the build loop** — scope the new task *and* close the escalation route so
   the routed task is not also queued.

Doing both at once is the defect. When the reviewer escalates with `task_id` naming a task that will be reset,
the default answer is (1): decide whether the existing task can absorb the fix before writing a task at all —
if it can, the correct graph diff is empty.
