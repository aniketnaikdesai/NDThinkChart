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
