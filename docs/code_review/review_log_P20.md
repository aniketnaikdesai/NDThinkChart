# Code Review — Phase P20 (D59 index + futures contract support)

Tier: FULL pass (phase-final; CANNOT be light — `precheck.json` carries a fail_fast flag,
verification verdict is FAIL with SIGABRT, scoped tasks are size M sharing `ui/main_window.py`).
Scope: P20-T1, P20-T2, P20-T3 (no `review_log_P20.md` existed; all results newer than any marker).
Ground truth consumed: `docs/code_review/precheck.json` (+`.md`, 1 fail_fast: P20-T2),
`docs/code_review/test_verification.json` (FAIL, exit -6 SIGABRT at
`test_p19_prefetch_trigger.py::test_t01_trigger_matrix_intraday`, `_triple` MainWindow construction)
+ full `test_verification.log`, `docs/build/build_log.md` waves 293–298, per-task results
`wave293_P20-T1` / `wave298_P20-T2` / `wave296_P20-T3`, `task-graph.json` P20,
requirements `### Phase P20` (AC-D59.1–D59.6, Q96–Q99), architecture S-P20-1…S-P20-7,
plan § Phase P20, `docs/codebase-map.md`. No prior P20 review marker — this is the phase-final pass.

## Entry-C (escalation close-out)

Exactly one open entry: PRE-018 (P20-T2, precheck, blocking). Re-verified live:
`tests/test_p20_futures_scoping.py:403` still carries `@pytest.mark.skip(reason="owner-run
standalone live probe ...")` and the RESULTS block still reads PENDING for all five rows —
the TM-scoped skip→assert-waiver-record conversion was NOT performed (wave298 result still
reports `P20-T2-PROBE:skip`). Nothing changed → PRE-018 stays OPEN (still needs BUILD
re-dispatch; NOT duplicated below).

## Verification performed (beyond the suite verdict)

- P20 task suites isolated: `test_p20_resolution_probe` + `test_p20_futures_scoping` +
  `test_p20_proxy_guard` → **48 passed, 1 skipped** (the PROBE skip). Task-local claims hold.
- Full suite minus the aborting file: **33 FAILED** (log `/tmp/full_no_p19trig.log` analogue —
  exact list in the review record below). Clean-HEAD worktree (`/tmp/p20base` @ 65bc3e7,
  same venv) on the same subset: **3 FAILED**, all worktree artifacts that pass in-tree
  (`test_timeframe_config_untouched`, `test_archived_results_carry_task_id`,
  `test_t12_unapproved_durations_are_diff_clean` — verified green on the live tree).
  → ~30 failures are P20-caused, not pre-existing. Baseline/full lists diffed hunk-by-hunk.
- SIGABRT adjudication (real P20 interaction, NOT full-suite flake):
  `test_t01_trigger_matrix_intraday` (12 params: 6×ETH then 6×RTH) aborts deterministically
  on the P20 tree (6 dots, then abort at the FIRST RTH param's `_triple` setChecked) and
  passes 12/12 on clean HEAD; the aborting param passes ALONE on the P20 tree (ETH no-op).
  Parameter order (collected: ETH-1min…ETH-4h, RTH-1min…) proves the 6 dots never entered
  the toggle slot and the abort fires on first slot entry with an empty symbol widget —
  the B1 IndexError chain below. Scratch repro (`/tmp/mw_leak.py`, fresh MainWindows +
  `setChecked`) raises the identical `IndexError` through the identical slot chain.
- Mock-endpoint scan (standing invariant): crossed grep `mock|fake|stub|simulat` ×
  `endpoint|client|service|server|api|harness` over all 7 P20 production files → only
  comment/docstring mentions of test stub-hosts and fake bridges. No mock endpoint in
  production, no production import of a test fake. PASS.
- Wiring audit: production LWC path threads `self._symbol` through `_collapse_for_view`,
  `logical_indices`, `drawing_axis`, `session_regions` (view methods + module ops) —
  T2 visual scoping is live, not dead code. `session._wave_contract` initialized
  (`ticker_session.py:211`), reset per wave (`queue_wave_plans`), `_contract_rejected_200`
  reset in `prepare_load`. Probe adopt/refuse, exactly-once `take_details`, bounded
  `_resolved` (64), honest-refuse on pacing — all match AC-D59.2 as written.
- Overlap/unattributed: `ui/main_window.py` overlap (T1+T2) reviewed jointly — hunks are in
  disjoint regions with compatible semantics (probe seam + canonical forcing). The 3
  precheck-unattributed files (`ibkr/contracts.py`, `services/contract_lookup_service.py`,
  `ui/ticker_session.py`) are all inside P20-T1's declared `touches_files`; T1's result
  under-listed `files_changed` (manifest clerical gap, no footprint violation, no action).
- Usage-doc judgment: `doc_candidates` are `USAGE.txt` (quick start) + `usage.md` (canonical
  guide) + `docs/`, 0 touched. P20 is backend plumbing (contract tables, probe seam, planner
  flags, collapse/band suppression) reusing existing status-message patterns; no new control,
  command, config, or workflow a user doc would describe. Docs gate satisfied by absence.
- Architecture/requirements consistency: IND table (SPX/CBOE, NDX/NASDAQ, DJI/CME, RUT/CME),
  STK-charset→probe→adopt/refuse with no persistence, Saturday-only futures week with
  fetch-not-assumed holidays, proxy-tape-only guard, history markers — all match S-P20-1…S-P20-7
  and AC-D59.1–D59.5 as written. The failures below are regression/breakdown conflicts, not
  AC deviations — EXCEPT the task text's deliberate overrides (probe refuse vs P7 deferral),
  which belong to Task Manager (TM2).

## Findings (5 new: 3 BUILD, 2 TASK_MANAGER; plus PRE-018 carried open)

- F-1 (BUILD, blocking, P20-T2) — ESC-106. Empty-symbol crash before the guard:
  `load_chart` calls `is_futures_root(symbol)` (main_window ~2152) BEFORE the
  `if not symbol` guard; `is_futures_root("")` → `_base_symbol("")` → `"".split()[0]` →
  IndexError (contracts.py:152-163). Kills the supported empty-toolbar path
  (`test_toolbar_click_empty_symbol_shows_message` fails with the slot IndexError; passes
  on HEAD) AND is the SIGABRT trigger (first RTH toggle → `load_chart("")` → IndexError in
  the Qt slot → abort). Fix direction (not a decision): move the `if not symbol` guard above
  the canonical-forcing hunk and/or harden `_base_symbol` for empty/whitespace; re-run the
  aborting trigger file to confirm the abort closes with it.
- F-2 (BUILD, blocking, P20-T2) — ESC-107. Renderer-boundary violation: `ui/lwc_view.py`
  gained `from ibkr.contracts import is_futures_root`, tripping 12 pinned P6 boundary tests
  (`lwc_view reached into the backend/network: ibkr.contracts` + `test_no_out_of_scope_residue`).
  Fix direction: compute futures-ness outside the renderer (caller/main_window/chart_model)
  and pass a plain bool down the already-threaded `symbol=` params; drop the ibkr import.
- F-3 (BUILD, should-fix, P20-T1) — ESC-108. Latent None-contract sinks for adopted probes:
  `_ensure_restore_data_path` (:1044) and `maybe_issue_prefetch_wave` (:1151) queue
  `get_contract_for_symbol(symbol)` (None for probe-unknown symbols) instead of the adopted
  `session._wave_contract`, discarding the probe adoption on restore/prefetch. No current test
  covers the combo (hence should-fix). Fix direction: use the established
  `session._wave_contract or get_contract_for_symbol(...)` fallback already used at :2486.
- F-4 (TASK_MANAGER, blocking) — ESC-109. Systematic probe-diversion vs synthetic symbols:
  the STK-charset rule diverts every underscore/long test symbol into the probe path (no
  session, no wave, pending probe), failing 16 tests whose files are outside P20 touches and
  whose criteria the phase was forbidden to redesign (scope guard D1–P19): p10 lock/recolor
  KeyError ×2 (`P10T4_*` underscore), p19 wave marker-not-cleared ×2 (`P19W_G2` underscore —
  explicit `load_chart` parks in `_pending_probes` instead of the synchronous cancel),
  d42 depth-floor 0-sessions ×8 + no-wave-eth ×1 (9-char `P22…` symbols), d42 shortfall
  `session.symbol` AttributeError ×1, p7 attach `_contract_rejected_200` AttributeError ×2
  (doubles predate the new attrs). Decision needed (not mine): (a) scoped follow-up migrating
  affected tests to conforming symbols/doubles, or (b) revise the STK/probe trigger. Also
  re-sequence the now-stale T3-AC2 full-suite gate after fixes.
- F-5 (TASK_MANAGER, blocking) — ESC-110. Pinned-contract conflicts the breakdown didn't scope:
  p7 signature pin (`find_missing_spans` exact params vs the mandated `is_futures` param) ×1
  and P7 deferral scans ×2 (`_start_probe_load` refuses-by-design per the T1 task text, which
  deliberately overrides the defer-everywhere invariant). Decision needed: allowlist the
  task-mandated deviations via scoped test updates. (The deviations themselves are
  task-faithful; this is test-scope debt, not code bugs.)

PRE-018 (open, carried): T2 PROBE still `@pytest.mark.skip` with PENDING results —
needs BUILD re-dispatch for the TM-scoped skip→assert-waiver-record conversion.

## Per-task verdicts

- P20-T1: own tests green; implementation AC-faithful; ships 2 routings (F-3 should-fix;
  F-4/F-5 breakdown debt owned by TM). NOT accepted while F-1/F-2 keep the suite red.
- P20-T2: own tests green except the waived PROBE (PRE-018 open); ships F-1 + F-2 blocking.
- P20-T3: own tests green; proxy guard holds; its AC2 full-suite gate is STALE (suite red) —
  must re-run post-fix (covered by F-4 direction).

Status: REVIEW_COMPLETE

---
# Rework review pass — 2026-11-10T00:05Z (incremental over waves 300–303)

Tier: FULL pass (verification FAIL SIGABRT + blocked P20-T4 in scope; CANNOT be light).
Scope: P20-T1, P20-T2, P20-T4, P20-T5 (results wave300–303 newer than the
prior REVIEW_COMPLETE). P20-T3 has no new result — out of scope. Ground truth
consumed: `docs/code_review/precheck.json` (0 fail_fast, overlaps/T4-T5 shared
`test_p7_w4_deferral.py` informational, unattributed-tree-changes informational),
`docs/code_review/test_verification.json` (FAIL exit -6 SIGABRT), results
wave300–303, task-graph P20 touches, requirements AC-D59.x, architecture S-P20-x.
Unattributed-files note: every precheck-unattributed path sits inside P20-T1/T2/T3
`touches_files` (contracts.py, contract_lookup_service, ticker_session, probe/scoping
tests in T1; backfill/time_collapse services in T2) — manifest `files_changed`
under-listing only (same clerical gap as last pass), no footprint violation.

## Entry-C (escalation close-out)

- PRE-018 (P20-T2, precheck, BLOCKING) — STAYS OPEN. Nothing changed:
  `tests/test_p20_futures_scoping.py:403` still `@pytest.mark.skip`, RESULTS block
  still all PENDING. Wave301 reports `P20-T2-PROBE:pass` in its results JSON while the
  runtime tail shows `.............s` (13 passed, 1 skipped) — the skip→pass
  reporting gap (result claims pass, test skips) persists; the TM-scoped
  skip→assert-waiver-record conversion was NOT performed. Precheck no longer flags it
  (T2 reads 4/4), but the underlying condition is unchanged per rule C2.
- ESC-106 (P20-T2, BUILD, blocking) — STAYS OPEN, fix did NOT land. Re-verified live:
  `is_futures_root('')` still raises `IndexError` (`_base_symbol('')` → `"".split()[0]`,
  ibkr/contracts.py:152); `load_chart` still calls `is_futures_root(symbol)` (:2169)
  BEFORE the `if not symbol` guard (:2171). Same crash, not a new one:
  `test_d28_2_load_chart_button.py::test_toolbar_click_empty_symbol_shows_message`
  fails with the identical unhandled-slot `IndexError('list index out of range')`;
  `tests/test_p19_prefetch_trigger.py` run standalone still aborts (faulthandler tail,
  same MainWindow-construction/toggle site as the suite-wide SIGABRT). Note: the
  rework claiming the guard fix touched only `ui/lwc_view.py` (T2) — the guard lives in
  `ui/main_window.py`/`ibkr/contracts.py` (T1 territory). Still routed BUILD.
- ESC-107 (P20-T2, BUILD, blocking) — ADDRESSED (verified, flipped in place).
  `grep ibkr ui/lwc_view.py` shows no import (only a historical comment); futures-ness
  now via renderer-local `_FUTURES_ROOTS` + `_is_futures_symbol` (bool passthrough or
  local-root resolve) and `_collapse_for_view`. Green: test_chart_model.py +
  test_p20_resolution_probe.py (30 passed), test_lwc_router_mirror.py +
  test_p20_proxy_guard.py + test_p20_futures_scoping.py (74 passed, 1 PROBE skip),
  test_lwc_alarms.py + test_chart_view_seam.py + test_chart_mouse_router.py (34 passed).
- ESC-108 (P20-T1, BUILD, should-fix) — ADDRESSED (verified, flipped in place). Both
  sites now use `session._wave_contract or get_contract_for_symbol(symbol)` with a
  None-contract early-out (restore ~:1050, prefetch ~:1164). The two new regression
  tests are genuine and discriminating by construction (pre-fix they fail: prefetch
  asserts `hist_calls[0]['contract'] is adopted` where pre-fix queued None; restore
  asserts `hist_calls == []` with non-empty spans where pre-fix queued a None wave).
- ESC-109 (TASK_MANAGER, blocking) — ADDRESSED (verified, flipped in place). TM executed
  option (a) via P20-T4: all 16 originally-diverted named cases green in the six-file
  suite (p10 renames `P10T{pid%1000}`+A/B charset-valid ≤8 chars; p19 `P19W_G2`→`P19WG2`
  restoring the synchronous cancel; d42 `_TF_ABBR` symbols; `_FakeSession.symbol` +
  `_contract_rejected_200` doubles). No weakened assertions in the diff. Residual T4 red
  is ESC-110 scope (tracked there), not a diversion.
- ESC-110 (TASK_MANAGER, blocking) — STAYS OPEN, partially executed. T5 (wave303, done)
  resolved 2 of 3: signature pin now names the full `find_missing_spans` signature incl.
  `is_futures`, and the deferral scan allowlists exactly `ui/main_window.py:_start_probe_load`
  (narrow, positively pins honest-refuse `"load refused"`, exact-allowlist-match asserted,
  no-blocking-tokens kept absolute — high-quality edit, no finding). Remaining: the
  streaming twin `test_p7_t07_t13_every_pacing_handler_defers_without_blocking` still fails
  on the same approved refuse site. Same TM ruling needed (extend the T5 allowlist pattern
  to the streaming scan, or rule production must defer). T4's AC3 red is exactly this item.

## Quality review (done tasks: T1, T2, T5)

- T1: own tests green (probe module incl. 2 ESC-108 guards); AC-faithful; services/session
  hunks reviewed (probe `take_details` exactly-once + 64-cap, error-200 latch + per-load
  reset, futures identity map with default-False byte-identical callers). No new findings
  (guard ordering stays under ESC-106, not duplicated).
- T2: boundary fix verified; `_is_futures_symbol` bool-passthrough keeps the threaded
  `symbol=` params working. Maintenance note (no escalation): `_FUTURES_ROOTS` duplicates
  the broker `FUTURES_SCHEDULE` keys by boundary necessity — a future new root must be
  added in both places or visual scoping silently misses it. Worth a one-line comment
  cross-ref; not routing (mandated by the renderer-only boundary + TM scope).
- T5: no findings (see ESC-110 note above for edit quality).
- T4 (blocked): worker correctly refused both prohibited fixes (no assertion rewrite, no
  out-of-footprint production edit) and reported precisely. T4's result is now stale vs
  T5's deferral edit (cites 2 residual failures; live tree shows 1) — build_wave will
  re-run it after ESC-110 clears; no reviewer action.
- Usage docs: `USAGE.txt`/`usage.md`/`docs/` untouched; P20 remains backend plumbing (probe
  seam, planner flags, collapse/band suppression reusing existing status patterns) with no
  new control/command/config/workflow — docs gate satisfied by absence.
- Mock-endpoint scan: cross grep `mock|fake|stub|simulat` over all 7 P20 production files'
  diff → zero hits. PASS.

## Per-task verdicts

- P20-T1: done holds (own tests green, ESC-108 closed). NOT suite-green while ESC-106 open.
- P20-T2: done holds (boundary closed). PRE-018 + ESC-106 open items remain.
- P20-T4: blocked holds — correctly, on exactly 1 residual scan (ESC-110 streaming twin).
- P20-T5: done holds, no findings.
- Full suite: still FAIL (SIGABRT) — adjudicated SAME crash as ESC-106 (empty-symbol
  IndexError in the slot), not a new failure. No new escalations opened this pass.

Status: REVIEW_COMPLETE

---
# Rework review pass — 2026-11-10T00:20Z (incremental over wave305–308)

Tier: FULL pass (CANNOT be light — scoped tasks P20-T2/T4 are size M; verification
verdict is FAIL with 8 failures). Scope: P20-T2, P20-T3, P20-T4 (results
wave306/wave307-308/wave305 newer than the prior REVIEW_COMPLETE). P20-T1/T5 have
no newer result — out of scope; their substance was verified last pass and no new
evidence against it surfaced (probe seam, `_pending_probes`, `_wave_contract`
fallbacks and honest-refuse wording all observed intact in the live-tree diff).
Ground truth consumed: `docs/code_review/precheck.json` (+`.md`, 0 fail_fast,
overlaps none, doc_candidates 3 with 0 touched, 8 unattributed-tree-changes),
`docs/code_review/test_verification.json` (FAIL, exit 1, 8 failures — all in P19
prefetch suites) + full `test_verification.log`, per-task results
wave306_P20-T2 / wave307-308_P20-T3 / wave305_P20-T4, task-graph P20 touches,
requirements AC-D59.x, architecture S-P20-x. No full re-reads beyond the single
initial pass; later steps consulted the already-read artifacts.

## Adjudication of the 8 failures (real fallout, NOT a T2 regression)

- The 8 failures are `assert 0 == 1` on wave issue (`stub.calls == []` /
  `_wave_plan_queue == []` immediately after `_on_viewport_settled`) in
  tests/test_p19_prefetch_depth.py x3 (T01 deep_scroll_chains, T02
  retention_edge, T02 pacing_exhaustion), tests/test_p19_prefetch_honesty.py x3
  (T01 per_chunk_incremental, T01 strand_finalization, T01 genuine_closures),
  tests/test_p19_prefetch_viewport.py x2 (T02 away + following landings).
- Reproduced with the tasks' own commands: the pacing case fails standalone with
  the byte-identical assertion (`_wave_plan_queue == []`); `get_contract_for_symbol`
  returns None for P19D_CHAIN/P19V_A/P19H_A (STK for SPY) — every failing symbol
  carries an underscore, failing the STK-charset pattern, so the approved T1
  probe-first seam parks the load in `_pending_probes` before any prime/wave leg.
- T2 futures scoping is exonerated: `is_futures_root` is False for all four P19
  families (True only for ES), so the canonical-mode hunk is a no-op here; the
  prefetch `_wave_contract or get_contract_for_symbol(...)` fallback (ESC-108
  fix) correctly yields None with no wave. Same invariant as ESC-109 (16 cases,
  addressed via P20-T4), now in 3 files T4 never scoped — per the repeat-invariant
  rule this routes to TASK_MANAGER as one new escalation, never a BUILD patch.
- Prior-pass SIGABRT is gone from this verdict (exit 1, no abort): consistent
  with the ESC-106 guard fix closing the empty-symbol slot crash.

## Entry-C (escalation close-out — all four re-verified live, flipped in place)

- PRE-018 (P20-T2, precheck, BLOCKING) — ADDRESSED. The skip-to-assert-waiver
  conversion LANDED: no `@pytest.mark.skip`/PENDING remains in
  tests/test_p20_futures_scoping.py; P20-T2-PROBE is now
  test_p20_t2_probe_waiver_recorded (owner verbatim, P6 precedent, probe
  explicitly not claimed, IND risk open). Module re-run: 14 passed, 0 skipped.
- PRE-019 (P20-T2, orchestrator, BLOCKING) — ADDRESSED. Both conditions hold:
  guard above the hunk (main_window.py:2155 before :2174) + waiver test passing.
- ESC-106 (P20-T2, BUILD, blocking) — ADDRESSED. Guard order confirmed in source
  with owning comment; exact repro tests/test_d28_2_load_chart_button.py: 3 passed.
- ESC-110 (TASK_MANAGER, blocking) — ADDRESSED. All three pins reconciled (cap
  pin names is_futures; BOTH deferral + streaming scans carry the exact-match
  refuse allowlist for `ui/main_window.py::_start_probe_load`, other-sites-defer
  and no-blocking-tokens absolute). Re-ran T2+T3+both scans+cap pin: 51 passed;
  T4's six-file set green (32 on the four non-scan files, scans inside the 51).

## Quality review (scoped done tasks: T2, T3, T4)

- T2: guard hunk reviewed at main_window.py:2155-2189 (early-return before any
  futures/probe work; comment owns the IndexError edge). Scoping module 14/14.
  No new findings. Maintenance note (no escalation, carried): renderer-local
  `_FUTURES_ROOTS` duplicates broker FUTURES_SCHEDULE keys by boundary necessity.
- T3: proxy-guard module green; no INDEX_PROXY in the chart load/history path;
  burst-proxy tape use preserved. No findings.
- T4: test-only diff across the six files (charset renames + doubles carrying
  `symbol`/`_contract_rejected_200` + streaming-twin allowlist mirroring the
  landed deferral shape). No weakened assertions observed. No findings.
- Mock-endpoint scan (standing invariant): crossed grep over the
  ui/main_window.py reviewed diff for mock/fake/stub/simulat x
  endpoint/client/service/server/api/harness → zero hits. PASS. (Only production
  file in incremental scope; test files out of the invariant's reach by definition.)
- Usage-doc judgment: candidates USAGE.txt/usage.md/docs/, 0 touched. The rework
  is a guard move, a waiver-record test, and test-only migrations — no new
  control, command, config, or workflow a user doc would describe. The only
  user-doc-like files in this project are the quick-start/guide candidates above.
  Docs gate satisfied by absence.
- Unattributed-tree-changes note (8 files): every path sits inside P20-T1/T5
  touches (contracts, lookup, ticker_session, backfill/time_collapse services,
  probe/scoping tests, p7 cap pin) — same manifest `files_changed` under-listing
  adjudicated the last two passes (clerical gap, no footprint violation). The
  sampled hunks are all P20-seam related; no out-of-scope edit observed. No action.

## Findings (1 new: TASK_MANAGER; plus 4 close-outs above)

- F-6 (TASK_MANAGER, blocking) — ESC-111. P20-T1 probe-diversion residual in 3
  unscanned P19 suites: 8 prefetch failures (depth x3, honesty x3, viewport x2),
  all underscore-symbol loads parking in `_pending_probes` with zero waves.
  Same invariant as ESC-109 (addressed) — one invariant, one TM escalation, no
  BUILD patch per the repeat-invariant rule. Direction (not a decision): scoped
  test-only migration of the depth/viewport/honesty symbols to charset-conforming
  names preserving chaining/honesty/stability intent, or revise the STK/probe
  trigger. D1–P19 stay unreopened for criteria; the fix touches tests only.

## Per-task verdicts

- P20-T2: done holds (14/14 incl. waiver record; guard fix verified). No open items.
- P20-T3: done holds (3/3; gate re-runs after ESC-111 lands).
- P20-T4: done holds (6/6 green; substance verified, no new evidence).
- Full suite: FAIL exit 1 with exactly the 8 ESC-111 cases; everything else green.
  T3-AC2 batch gate stays sequenced after the ESC-111 migration.

Status: REVIEW_COMPLETE
---
# Rework review pass — 2026-11-10T03:45Z (incremental over wave310)

Tier: LIGHT pass (all light conditions hold: test_verification PASS exit 0; precheck
0 fail_fast, 0 overlaps, results coherent with no flags; scoped tasks P20-T3/T6 are
size S; files_changed are tests-only, no shared/core file). Phase history already
carries three FULL passes; this slice needs no line-by-line production read-through
(no production file in scope). Full-pass standing duties executed for the slice:
mock-endpoint scan (blocking) + usage-doc judgment (below).

Scope: P20-T3, P20-T6 (results wave310 newer than the prior REVIEW_COMPLETE).
P20-T1/T2/T4/T5 have no newer result — out of scope; ESC-106/107/108/109/110 and
PRE-018/PRE-019 stay addressed (nothing relevant changed since, per rule C2 — not
re-diagnosed). Ground truth consumed: precheck.json (+.md), test_verification.json
(PASS exit 0, ground truth for suite-green), build_log waves (tail), results
wave310_P20-T3 / wave310_P20-T6, task-graph P20 (T6 done), prior review passes above.

## Entry-C (escalation close-out)

- ESC-111 (TASK_MANAGER, blocking) — ADDRESSED (verified, flipped in place). TM
  executed option (a) via P20-T6: 10 one-line renames (P19D_* -> P19DCHN/P19DCLS/
  P19DRET/P19DPACE; P19H_* -> P19HA-D; P19V_* -> P19VA/B), all charset-valid
  (uppercase letters only, <=8 chars). Reviewer re-ran the three suites: 9 passed
  (covers all 8 named ESC-111 cases); probed get_contract_for_symbol -> STK
  non-None and is_futures_root False for all 10; diff is test-only (exactly the 3
  listed files, zero production). Full suite green per test_verification.json.

## Quality review (scoped done tasks: T3, T6)

- T3: proxy-guard module + burst suite re-run: 54 passed. No INDEX_PROXY in the
  chart load/history path (prior FULL-pass finding, unchanged). T3-AC2 batch gate
  now holds on the clean re-run: full suite PASS exit 0 (test_verification.json).
- T6: test-only charset migration, no weakened assertions (pure renames), no new
  findings. Repeat-invariant rule respected: one TM escalation for the invariant,
  no BUILD patch.
- Mock-endpoint scan (standing invariant): scoped files are tests-only; crossed
  grep mock/fake/stub/simulat x endpoint/client/service/server/api/harness over
  the 4 scoped test files shows no production mock endpoint. PASS.
- Usage-doc judgment: candidates USAGE.txt/usage.md/docs/, 0 touched. The slice
  is a test-only guard re-run + test-only renames — no new control, command,
  config, or workflow a user doc would describe. Docs gate satisfied by absence.
- Unattributed-tree-changes note (16 files): every path sits inside P20-T1/T2/T4
  touches or the T4/T5/T6 test migrations (contracts, lookup, backfill/collapse
  services, main_window/ticker_session/lwc seams, p10/p19/d42/p7 suites) — same
  manifest files_changed under-listing adjudicated in prior passes (clerical gap,
  no footprint violation). Sampled hunks are all P20-seam related. No action.

## Per-task verdicts

- P20-T3: done holds (guard + gate green).
- P20-T6: done holds (migration green, test-only).
- Full suite: PASS exit 0. Zero open escalations.

Status: REVIEW_COMPLETE
