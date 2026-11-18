# Code Review — Phase P23 (D65 Option Spreads, Portfolio-stack removal)

**Pass:** phase-final, **full pass** (phase-final always full; the independent suite run is also red).
**Scope (incremental):** all 14 tasks with results newer than the P22 `REVIEW_COMPLETE` marker —
P23-T1..T14 (`docs/code_review/precheck.json`, `review_marker.log = review_log_P22.md`).
**Inputs consumed as ground truth:** `precheck.json` (0 fail_fast, 0 unattributed tree changes,
overlaps informational only), `test_verification.json` (verdict **fail**, exit 1, 85.31 s,
exactly two failing cases), `build_log.md` (P23 waves 330–349), every S/M task (no size L), and
the committed tree `82b82fd`.

**Verdict:** the phase's production work, deletions, residue gate and consistency claims hold.
Three findings are open: one breakdown gap (the two red contracts, ESC-116) and two code
findings (ESC-117 blocking, ESC-118 should-fix). `REVIEW_COMPLETE` is written with these open —
they are listed for the Orchestrator's pause/approval step, not waived.

---

## ESC-116 — `tests/test_d65_option_chain.py`: two wave-scoped contracts are false at phase end

- **Linked task:** P23-T6 (owns the file and its AC5). **Category:** consistency. **Severity:** blocking.
- **Root cause:** `bad_task_breakdown` — P23-T6-AC5 is worded "**Given this wave**, Then no
  production module outside `ibkr/` calls the new helpers **yet**, the four account/position
  EWrapper overrides and their four bridge signals **are still present** (they are P23-T11's
  deletions)". Both clauses were true at P23-T6's wave and are deliberately false at phase end:
  P23-T9's `ui/main_window.py` wiring is the **designed** first caller, and P23-T11 deleted the
  overrides/signals by owner decision. No task owned re-pointing the two cases: P23-T13's AC
  ("the full offscreen suite is green") had a `touches_files` (residue gate, `usage.md`,
  `option_ladder.py`) that cannot reach `test_d65_option_chain.py`, and its embedded gate record
  honestly logs `3 failed, 1682 passed` and defers them to "that contract's owner".
- **Adjudication:** these are **stale contracts, not regressions**. Neither is a Build defect in
  the code they fail on.
  - `test_no_production_caller_outside_ibkr` — reproduced: `assert offenders == []` with 7 hits,
    first `ui/main_window.py:get_option_contract`. The sweep (`_NEW_HELPERS` × `_production_modules`,
    skipping `.venv/.git/tests/docs/graphify-out/...`) only exempts `ibkr/`, so it forbids the
    wiring P23-T9-AC1..AC5 require. **Fix: re-point (allow `ibkr/` + the named live wiring in
    `ui/main_window.py`), never delete** — the caller-discipline guard is real.
  - `test_account_and_position_overrides_and_signals_remain` — reproduced: `account_summary` signal
    missing (`hasattr` False) because P23-T11-AC1 mandates absence. The case asserts the inverse of
    its own phase. **Fix: invert to the absence assertions** that `tests/test_ui_smoke.py:48-49`
    and `tests/test_d45_removal.py` block (d) already make.
- **Routing:** `TASK_MANAGER` (ESC-116) — rewrite P23-T6-AC5 (graph + suite docstring/banner) to the
  two phase-final invariants, extend the footprint, then re-dispatch Build for the test edit.
  Folding in the third red item P23-T13 recorded (`test_d64_batch_gate.py::test_p22_t5_ac2_shared_seam_record`):
  it is **already green on the committed tree** (an artefact of the uncommitted wave) — no action.

## ESC-117 — OFF → ON leaves the engine believing the pre-OFF legs are live (stale values shown as current)

- **Linked task:** P23-T9. **Category:** bug. **Severity:** blocking.
- **Reproduced** with the real `MainWindow` against the suite's fake TWS (`_make_window` /
  `_toggle_on` / `_deliver_chain` / `_settle`), offscreen, temp `DB_PATH`:

  | step | `_md_line_count()` | `_option_leg_req` | engine `live_legs()` | CCS row 0 |
  |---|---|---|---|---|
  | ON, settled | 16 | 16 | 16 | `SPX 20261117 7360/7380 −1.00 −1.20 −0.020 0.0004` |
  | OFF | 0 | 0 | 16 | cleared |
  | ON again (chain re-delivered, full settle) | **1 (spot only)** | **0** | **16** | **same pre-OFF values** |

  Zero option subscribes are issued on the second ON (`stale_legs()` empty), so the ladders render
  dead prices as live values with no line behind them.
- **Cause:** `SpreadEngine.toggle_off()` (`services/option_spread_engine.py:364-366`) clears only
  `_on`/`_seed_active`; `_subscribed`, `_leased`, `_window_legs`, `_anchors`, `_session_anchor`,
  `_seed_bounded`, `_quotes`, `_stale` survive, and `on_chain()` (:389-405) only resets on an expiry
  **change** — a same-session ON re-requests the same 0DTE expiry. `MainWindow._option_stop()`
  (`ui/main_window.py:2061-2085`) cancels the real lines but never tells the engine. Same stale set:
  `_option_subscribe_leg()` (:2276-2280) gates on `leg in live_legs()` and `_option_cutoff` but not
  `_option_active`, so a `PacingExceeded` `singleShot` retry (:2291-2296) firing after OFF opens a
  line while the panel is OFF (AC-D65.9's "zero reqIds" is then violated).
- **Why the suite missed it:** no case toggles ON twice in one window; the OFF case asserts only the
  off-state. Routed to `BUILD` (ESC-117) with the reset + guard + regression case.

## ESC-118 — the residue gate's sole allowlist entry excuses an unused alias via a document citation

- **Linked task:** P23-T13. **Category:** quality. **Severity:** should-fix.
- `services/option_spread_engine.py:1637` `OptionSpreadEngine = SpreadEngine` has **no production
  reader**; `tests/test_d65_residue.py:108-122` allowlists it citing
  "`docs/tasks/task-graph.json` P23-T7 signature `class OptionSpreadEngine`" — a document mention,
  not a registration site. `test_census_allowlist_cites_a_live_site` only checks the file exists.
  It is the **only** entry in `CENSUS_ALLOWLIST`, so the allowlist currently exists to keep this one
  dead symbol green: a narrow-looking carve-out that is convenient in substance, and it makes
  clause (i) passable by any symbol with a doc mention.
- **Checked and not a violation:** clause (iii)'s scoping to P23-authored files hides nothing today —
  I ran the gate's own `scan_unused_imports` / `scan_noqa_imports` / `scan_unreachable` over
  `ui/main_window.py`, `ui/watchlist_panel.py`, `ibkr/{bridge,client,contracts,market_data}.py`,
  `data/{db,models}.py`, `ui/ticker_session.py`, `tests/conftest.py`: all empty.
- Routed to `BUILD` (ESC-118): delete the alias + entry (or make the citation a real code site) and
  tighten the allowlist check.

---

## Verified clean (full pass duties)

**Escalation close-out.** `escalations.json` has **no open entries** (106 total, all addressed);
`precheck.json` `escalation_updates` is empty. Nothing to re-verify or close.

**Owner-confirmed deletions are complete.** No production module reads the dropped tables:
`positions` / `trade_groups` / `position_group_map` appear only in `data/db.py:164-179` (the guarded
child-first `DROP`, after `db_backup.backup_before_drop`) and in `data/db_backup.py` (copy
verification, read-only `mode=ro`, integrity + row counts, raises `BackupVerificationError` before
any drop). No `SELECT/INSERT/UPDATE` against them survives. `ibkr/account.py`,
`services/strategy_detection.py`, `ibkr/account` imports, `account_summary`/`position_update`
signals, `build_position_from_ib`, `data.models.Position`/`TradeGroup` appear only inside
absence assertions and forbidden-token tables. `ui/active_portfolio_panel.py` and its seven suites
are deleted; the surviving suites are re-pointed, not weakened (diff scan: no added
`skip`/`xfail`/`assert True`; every deleted test belongs to a deleted subject; 928 asserts added vs
283 removed, the removed ones tracking deleted subjects).

**S-P23-24 badge re-point is as recorded, not drift.** `conn_badge_text(monitoring_paused=False)`
returns `● Connected` / `#34d399`, paused keeps D40's amber wording, `_update_conn_badge` reads no
account state, no port-derived "Live" label invented; the port guard is untouched and the gate
record names it as the one phase-internal consequence (no requirements text edited).

**Numbers and formulas are identical everywhere.**
`display_bases` = `(long.ask − short.bid, long.bid − short.ask)`; `credit_bases` their exact
negatives with `credit_mid` the mean; credit spreads render negative by design (asserted).
`match_band = max(0.05, option_tick)` with the 0.05/0.10 break at 3.00. Target gate
`0.05 ≤ T ≤ 19.95` (`ui/option_spreads_panel.py:54-56,360`). Line accounting: `MAX_OPTION_LINES = 16`
in the engine lease pool + one spot line in `_md_line_count()` = 17. Canonical fixtures
`7425/7445`, `7340/7320`; `7425/7435` and `7315/7435` appear only as rejected examples, `7435/7455`
as the legal 20-wide non-banned pair. `docs/plan.md`, `docs/architecture.md`, the five phase suites,
`usage.md` and the T14 record state all of it identically.

**Residue gate is real.** `tests/test_d65_residue.py` 35 passed on the tree. It is proven red on its
seeded fixture by exercising the *same* scanner functions (`test_gate_is_red_on_a_seeded_dead_symbol`,
`test_gate_is_red_on_a_seeded_unconnected_signal`, and the red-then-green pair). Carve-outs: the
token carve-out is machine-checked (`test_every_carve_out_entry_is_earned`) and its stated rationale
matches its entries except `tests/test_d65_option_chain.py` — which is exactly ESC-116's residue, not
an independent hole. The single census-allowlist entry is ESC-118.

**Mock/fake/stub scan (B.6, blocking invariant).** Grepped the P23 diff's production files
(`ui/`, `services/`, `data/`, `ibkr/`, `config/`) for `mock|fake|stub|simulat` ×
`endpoint|client|service|server|api|harness`: three hits, all **comments** about test-host stubs
(`ui/main_window.py:273` describes the LWC factory seam; `ui/ticker_session.py:163,1054` note that
tests may pass a stub host). No mock/fake/stub/simulated endpoint, client, service or harness in
production code, and no production module imports a test fake. Clean.

**Usage docs.** The user-facing change (Portfolio panel → Option Spreads; account plane and strategy
auto-detection gone; three tables dropped after a verified backup) is documented in `usage.md`
(UI overview row, the "Option Spreads (view-only)" workflow, the tables section, the test command
list). `USAGE.txt` is a quick-start pointer with no panel inventory — correctly untouched. No
`doc_required_unmet` flags.

**P23-T14 record.** `docs/archive/probe_records/d65_paper_tws_acceptance.md`: all six AC-D65.19 items
unchecked with `Result: PENDING`, an empty evidence field each, header/line-count table, sign-off vs
explicit-waiver field; no fabricated result, and it states the six numbers identically. Docs-only
diff, as its AC requires.

**Pack-prose spot-check** (first task in the graph + tasks whose description carries a guarantee
word — P23-T1, P23-T8 "never", P23-T10 "never", P23-T12 "always"). No prose/AC contradiction and no
guarantee without an enforcing test in those four. P23-T6's prose "with none of it reachable from the
panel yet" *is* the stale phase-time guarantee behind ESC-116 and is covered there.

**Test re-baselines.** The twenty dock-lookup re-keys and the D18 suites are re-points (identity,
panel-fills, width) with no numeric tightening/loosening except the two owner-authorised A201
re-baselines; the `test_d65_option_panel.py` block T10 rewrote became a stricter absence test. No
case was weakened to make the build green.

---

## For the Orchestrator / owner

Open at handoff: **ESC-116** (TASK_MANAGER, blocking — the two red contracts), **ESC-117** (BUILD,
blocking — OFF→ON engine state), **ESC-118** (BUILD, should-fix — unused alias / gate allowlist).
The phase's other open gate is the **owner-run paper-TWS acceptance** (`AC-D65.19`, owned by
P23-T14): the checklist is created and every result pending — the phase cannot be called complete
until the owner runs it or records an explicit waiver. The repository documentation gate
(`docs/phase-changelog.md` has no D65/P23 entry yet; `plan.md`/`architecture.md` as-built sync) is
also owner-gated and outside this review.

# Code Review — P23 rework pass (ESC-116 / ESC-117 / ESC-118 closed)

**Pass:** phase-final, **full pass** (phase-final always full; and the verification artefact handed to this pass was stale, so nothing was tiered down).
**Scope (incremental):** P23-T9, P23-T13, P23-T15 — the three results newer than this log's previous `REVIEW_COMPLETE` marker (`precheck.json` scope, 0 `fail_fast`, 0 unattributed tree changes, one informational overlap: `tests/test_d65_residue.py` used by both T13 and T15).
**Tree:** `bb5d540`, clean; `git show --stat` = 2 production files + 3 test files + coordination docs. No footprint violation.
**Verdict:** all three reworks hold on the live tree; **ESC-116, ESC-117, ESC-118 flipped to `addressed`** after independent re-verification. Two **new, non-blocking** findings are opened: **ESC-119** (should-fix, TASK_MANAGER — the ESC-117 fix orphaned `SpreadEngine.toggle_off()`, and the standing gate cannot see dead methods) and **ESC-120** (nice-to-have, TASK_MANAGER — P23-T15-AC2 states a predicate that is unsatisfiable). The owner gates (AC-D65.19, phase changelog) are unchanged and still pending.

---

## 0. Verification provenance — the handed suite verdict was STALE (no action, but do not trust that file again)

`docs/code_review/test_verification.json` (mtime **18:29:59**) predates both the rework results (`19:01`–`19:10`) and commit `bb5d540` (**19:10:31**), and still reported `verdict: fail` on the two ESC-116 cases. It was older than `build_log.md` (19:10:26), so per the standalone fallback I re-ran the verifier myself:

```
verify_tests.py --command ".venv/bin/python -m pytest -q -m 'not webengine'"
-> VERIFY: pass  exit=0  85.0s   (rewrote docs/code_review/test_verification.json)
```

Ground truth: **the full suite is green on the committed tree.** The stage handed the reviewer a pre-rework verdict while asserting "precheck clean"; that combination is the one that could have closed a red phase as green, so it is recorded here as a process hazard. Per-task attribution, also run by me: `tests/test_d65_option_stream.py` → 27 passed; `tests/test_d65_option_chain.py tests/test_d65_residue.py` → 71 passed.

## 1. ESC-116 — CLOSED (`addressed`)

Both stale contracts were re-pointed by **P23-T15** (the task ESC-116 asked Task Manager to create), not softened:

- `test_no_unadmitted_production_caller` now scans through `_scan_callers`, admitting only `ibkr/` plus a **line-level** allowlist of seven named P23-T9 wiring sites in `ui/main_window.py` (3 helper imports, `req_sec_def_opt_params`, the `option_params` / `option_params_end` / `option_computation` connects). It additionally asserts `admitted == set(_ADMITTED_MAIN_WINDOW_LINES)`, so it cannot pass by finding nothing. Discrimination is proven twice in-tree: `test_seeded_non_ibkr_caller_is_still_reported` (`ui/rogue.py` offender reported) and `test_seeded_mention_outside_the_admitted_lines_is_still_reported` (a `main_window.py` mention outside the admitted lines reported).
- `test_account_and_position_overrides_and_signals_are_absent` asserts `name not in vars(IBApiClient)` + identity with the inherited `EWrapper` stub + `hasattr(IBBridge, signal) is False`, for all four pairs; `test_no_presence_assertion_for_the_dropped_account_names_survives` AST-walks the suite's own asserts so a presence assertion cannot creep back.
- The AC5 docstring bullet states the phase-final truth with no `yet` / `still present` / `deletes` wording, machine-enforced by `test_docstring_states_the_phase_final_ac5_invariants`; the residue carve-out rationale was corrected and is enforced by `test_residue_carve_out_entry_is_earned_or_gone`.

Framework fact checked by me: `class IBApiClient(EWrapper, EClient)` (`ibkr/client.py:46`) — `getattr(IBApiClient, name, None)` is **never** `None` for the four callbacks, which is why AC2 was reworded (see ESC-120). No test was deleted or weakened.

## 2. ESC-117 — CLOSED (`addressed`), with the reset's home tracked as ESC-119

Re-verified by reading the code and running the three new cases (all green):

| requirement | evidence |
|---|---|
| OFF → `live_legs()` empty, rows cleared, zero reqIds | `test_P23_T9_AC2_second_on_rebuilds_the_session_and_streams_fresh_values`: `live_legs()==set()`, `rows()=={}`, `_option_leg_req=={}`, `_option_req_ids=={}`, `_option_spot_req_id is None`, `entries_of_type(OPTION_LEGS)==[]`, fake counts `(0,0)`, `_md_line_count()==0`, every CCS/PCS cell cleared |
| deferred retry cannot open a line | `_option_subscribe_leg` now returns unless `_option_active and not _option_cutoff` (before the reqId/window gates); `test_P23_T9_AC2_deferred_leg_retry_after_off_opens_no_line`; `_option_ensure_spot` already carried the guard |
| 16:15 cutoff behaves like OFF | `_option_enter_cutoff` now also drops the chain lookup/reqId/params, drains messages and resets; `test_P23_T9_AC5_cutoff_discards_the_session_and_blocks_deferred_lines` |
| same-session ON re-seeds from fresh values, ≤16 + 1 | `>=16` fresh `OPT` subscribes with every live row's reqId in the post-OFF subscribe set, `max option <= 16`, `option+spot <= 17`, and a changed bid reaches the cell |

**Red-by-construction:** the second-ON case's first assertion after OFF is `live_legs()==set()` — the exact state ESC-117 measured as `16` pre-fix — so it discriminates; the deferred-retry case is red pre-fix for the same reason.

**Soundness of resetting by re-initialising the same instance** (asked explicitly; `services/option_spread_engine.py` was outside T9's footprint):

- **Identity:** preserved trivially — `_option_engine` has exactly one holder (`ui/main_window.py:893`); `ui/option_spreads_panel.py` holds no engine reference. The test asserts object identity.
- **Target:** survives explicitly (`__init__(target=self._option_engine.target)`); `_target` is the only owner setting on the engine.
- **No orphaned Qt timer/signal:** `SpreadEngine` is a plain Python class (`:278`, no `QObject`, no `pyqtSignal`, no `QTimer`), and all its session state is assigned in `__init__`, so re-running `__init__` creates nothing to leak or double-connect.
- **Nothing else dropped today:** production builds `SpreadEngine()` with no clock, and no test injects a clock through `MainWindow`.
- **Post-OFF pollution:** the two engine lifecycle hooks are gated (`_on_disconnected` on `_option_active and not _option_cutoff`; `on_reconnected` on `_option_active`), so the fresh post-reset engine cannot be re-polluted while OFF.

**Judgement, as requested: an engine-level `reset_session()` is the better home and should be the follow-up.** The UI-side `__init__` re-entry is a private-API reach-through, would silently drop the `clock=` seam if one were ever injected, and — concretely — left `SpreadEngine.toggle_off()` with **zero callers**. That is ESC-119.

## 3. ESC-118 — CLOSED (`addressed`)

- `OptionSpreadEngine` has **0** occurrences in any `.py`; remaining mentions are planning records only (`task-graph.json` P23-T7 signature / P23-T13 pack text, build log, wave packs, this log) — no definition, no importer.
- `CENSUS_ALLOWLIST == {}` (`tests/test_d65_residue.py:127`); the carve-out no longer exists to excuse anything, and its comment states the standard (a code registration site, never a document mention).
- The check is now evidence-based: `citation_violation()` requires `<repo-relative .py>:<line> — <how it is invoked>` (a `.json`/`.md` path cannot match), the path must be gate-scanned, the line must be in range, and `_invokes_by_name()` AST-verifies a call argument/keyword value, a class base, or a name-keyed string constant at that line.
- Seeded-red proof runs in-tree: `test_census_allowlist_rejects_a_document_mention` feeds the **exact** task-graph string from the escalation plus a `docs/plan.md` citation plus a bare definition line and rejects all three while accepting a real `signal.connect(handler)` site; the dead-symbol, unconnected-signal and red-then-green fixture cases still assert RED. Count: 36 passed (was 35).
- Scope note (not a re-open): clause (i) enumerates **module-level** public names only (`_defined_symbols` walks `ast.parse(text).body`), so dead methods are invisible to it — folded into ESC-119.

## 4. New finding — ESC-119 (should-fix, TASK_MANAGER): the ESC-117 fix orphaned a documented public method

`SpreadEngine.toggle_off()` (`services/option_spread_engine.py:364`) now has **zero callers** (tree-wide grep: the def, the class docstring `:83`, and `docs/architecture.md:9462` / `docs/plan.md:6070`, which still document it as the engine's OFF entry point). Pre-rework both `_option_stop` and `_option_enter_cutoff` called it, so `bb5d540` created the dead symbol.

**Root cause is the breakdown, not the worker.** ESC-117's own `suggested_direction` said "Add an explicit engine session reset … call it from `_option_stop` and `_option_enter_cutoff`" and warned that the engine file sat outside P23-T9's `touches_files`. T9's footprint was **not** extended, and the P23-T13 rework pack scoped `services/option_spread_engine.py` to "that single deletion and nothing else", so the worker had no footprint for the engine-side reset and reached through `__init__` from the UI.

**Why TASK_MANAGER and not BUILD:** this is a second case of the invariant ESC-118 was opened for ("no unused code; the gate must mechanically catch it") — one invariant, one task-definition fix, not a third BUILD patch. The gate as built cannot see it: `_defined_symbols` walks only top-level nodes. ESC-119 asks Task Manager to either make `toggle_off()` the engine-side reset (preferred: restores the documented caller, removes the `__init__` reach-through, keeps the clock seam) or delete it with the Plan-owned surfaces synced, **and** to state whether clause (i) is meant to cover class methods.

## 5. New finding — ESC-120 (nice-to-have, TASK_MANAGER): P23-T15-AC2 asserts an impossible predicate

AC2 says the overrides are absent when "`getattr(IBApiClient, name, None) is None`". `IBApiClient(EWrapper, EClient)` inherits ibapi's base stubs, so that is never `None`. Measured on the tree: `getattr(...) is None` → **False ×4**, `name in vars(IBApiClient)` → **False ×4**, `getattr(...) is getattr(EWrapper, ...)` → **True ×4**, signals absent → **False ×4**. The delivered case asserts the truthful, stronger form and documents the deviation; only the AC wording needs correcting so a later reader cannot mistake a green case for one that fails its own AC. No rework required.

## 6. Full-pass duties

- **Mock/fake/stub scan (B.6, blocking invariant).** Grepped the rework diff (`bb5d540`) for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness`: all hits are in `docs/` prose, in `tests/` fixtures (`_make_window`, `fake`), and one test comment explaining the `EWrapper` base stub. Production files changed are exactly `ui/main_window.py` and `services/option_spread_engine.py`; no mock endpoint, fake client/service, or harness in production, and no production module imports a test fake. **Clean.**
- **Usage docs (ruling for T13's `doc_required_unmet`).** `usage.md` **is** the project's user doc and it documents the phase's user-facing change: UI-overview row at `:128` ("Option Spreads (Right Dock) … Target credit field (0.05–19.95) and an ON/OFF switch … no order entry, close or cancel controls") and the workflow section at `:189`. This rework changed **no** user-facing behaviour (a dead alias deletion, a UI-side session reset, test re-points), so no doc update was required in this diff. **Ruling: met — nothing to do.** `USAGE.txt` correctly untouched (quick-start pointer, no panel inventory).
- **Pack-prose spot-check.** P23-T15's pack prose vs its ACs surfaced ESC-120 (an AC whose stated predicate contradicts the framework, not a prose/AC disagreement and not a guarantee without a test — every T15 guarantee names its enforcing case). The first-task and guarantee-word sample (T1, T8, T10, T12) was checked last pass with no contradiction; T13's "state that AC-D65.19 is open rather than claiming it" is honoured in the delivered summary/gate record.
- **Residue gate on the tree.** `tests/test_d65_residue.py` 36 passed as part of my run; its own seeded fixtures still assert RED (a green suite is the pair's required second half).
- **AC-D65.19 owner gate.** `docs/archive/probe_records/d65_paper_tws_acceptance.md`: **6** `Result: PENDING`, **0** checked boxes, every evidence field empty, sign-off blank, and the file states in prose that nothing on the page may be read as a pass. **Nothing was fabricated.** Still owner-gated.
- **`docs/phase-changelog.md`.** No `D65` / `P23` / "Option Spread" entry (grep: 0 hits; last modified Oct 28). Unchanged and correctly owner-gated — this review did not touch it.
- **Escalation close-out.** The three open entries (`ESC-116/117/118`) were the only open items; each is now `addressed` in place with its re-verification evidence. `precheck.json`'s `escalation_updates` (all three `changed_since_last_review: true`) matched reality.

## 7. For the Orchestrator / owner

The three reworks are **closed and verified**; the phase's production behaviour is sound and the suite is green on `bb5d540`. Two new items remain open, both TASK_MANAGER-owned and **neither blocking**: **ESC-119** (should-fix — decide `toggle_off()`'s fate / clause (i)'s method scope; this is also the answer to "should `reset_session()` be an engine-side follow-up": yes) and **ESC-120** (nice-to-have — one AC's wording). Unchanged owner gates: the **paper-TWS acceptance** (`AC-D65.19`, P23-T14, all six items PENDING) and the repository documentation gate (`docs/phase-changelog.md` has no D65 entry; `plan.md`/`architecture.md` as-built sync).

# Code Review — P23 close-out pass (ESC-119 / ESC-120, P23-T16)

**Pass:** phase-final, **full pass** (phase-final always full).
**Scope (incremental):** **P23-T16** only — the single result newer than this log's previous `REVIEW_COMPLETE` marker (`precheck.json` `scope: ["P23-T16"]`, `fail_fast: []`, `overlaps: []`, 0 unattributed tree changes, `flags: []`).
**Inputs consumed as ground truth:** `precheck.json` (fresh, 01:39), `test_verification.json` (**fresh — 01:40:31, i.e. newer than `build_log.md` (01:39:00) and than the commit; verdict `pass`, exit 0, 85.57 s**), `build_log.md` wave 357, `docs/build/results/_archive/wave357_P23-T16.json` (`done`, 3/3 pass, `footprint_flags: []`), the task graph (`P23-T16`, `P23-T15`), `requirements.md` AC-D65.12, and the committed tree **`c2fc2af`** (clean).
**Verdict:** **P23-T16 delivers all three of its own ACs on the live tree, and ESC-120 is closed.** **ESC-119 is only *half* resolved and stays open** (§3): the code half — the orphaned method and the constructor reach-through — is fixed and mechanically guarded, but the escalation's gate-scope half (decide/record whether clause (i) covers class **methods**, per `AC-D65.12(i)`, which does name methods) was not delivered in either permitted form. That is not a P23-T16 defect (T16 met its ACs verbatim); it is an undecided question the escalation exists to force. Details, evidence and the exact residual are below.

---

## 1. P23-T16 — verified clean (AC1 / AC2 / AC3)

Diff reviewed: `services/option_spread_engine.py` (+56/−1), `ui/main_window.py` (+6/−18), and two test files (246 added lines, **0 deleted** — `git show c2fc2af -- tests/ | grep '^-'` is empty, so nothing was weakened to make it green).

| the point I was asked to verify | how I verified it | result |
|---|---|---|
| `reset_session()` restores **every** `__init__` field except the clock and the Target | AST over the live file: `__init__` stores **36** fields on `self`; `reset_session` stores **34**; the difference is exactly `{_clock, _target}`; `reset_session`-only fields: none. A second AST pass over every method in the class shows **no field is assigned only outside `__init__`** (`fields assigned only outside __init__: []`), so there is no lazily-created state the reset can miss. | **pass** |
| clock **object identity** survives; Target unchanged; **no `set_target` side effect** | `_clock` is assigned in exactly one place (the `__init__` body, line 287); `_target` in exactly two (`__init__:289`, `set_target:429`). `reset_session` writes neither, so the injected callable stays the same object (`engine._clock is clock` asserted by both AC1 and AC3) and the Target cannot be re-validated/re-based — `set_target`'s own invalidation (`_session_anchor.clear()`, `_seed_bounded = None`) is deliberately **not** run, and the reset clears both fields anyway. | **pass** |
| `toggle_off()` has a real caller on the OFF path | `toggle_off` tree-wide: the `def` (:369), the delegation body (:371), the module/class docstrings, the tests, and **`ui/main_window.py:2082` inside `_option_stop()`** — the panel's OFF handler. No zero-caller public method remains. | **pass** |
| `ui/main_window.py` no longer constructs a second engine | `SpreadEngine(` occurs exactly once in production (`ui/main_window.py:893`, the one construction site); `ui/option_spreads_panel.py` holds no engine. `_option_reset_engine` appears **nowhere** in any `.py` (was `.__init__(target=…)`). The only `.__init__(` calls left in `ui/`/`services/` are `super().__init__(…)`. | **pass** |
| the 16:15 cutoff uses `reset_session()`; OFF is equivalent; same instance | `_option_enter_cutoff` calls `self._option_engine.reset_session()` (`:2120`); `_option_stop` calls `toggle_off()` (`:2082`), which *is* `reset_session()`. Both are preceded by the same `take_messages()` drain and followed by the same UI-state assignments as before, so the user-visible OFF/cutoff states are unchanged (pack statement "no behaviour change to the user-visible OFF/cutoff states" is true). The instances are the window's single engine (`win._option_engine is engine` asserted). | **pass** |
| the new tests fail on the **previous** commit and pass now | Ran P23-T16's own command on the live tree: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d65_spread_engine.py tests/test_d65_option_stream.py -q` → green (exit 0). Then a `git worktree` at **`bb5d540`** (the parent commit) with only the two new test files copied in: **all three fail** — `test_P23_T16_AC1…` and `…AC2…` (no `reset_session`), and `…AC3…` at `assert calls == []` with `Left contains one more item: <SpreadEngine object>` — i.e. AC3 is red **for the exact reason the escalation named** (one constructor re-entry from the UI), not incidentally. Red-by-construction is real. | **pass** |

Behavioural note (not asked, checked because it is the one way this fix could have gone wrong): resetting `_seed_sides`, `_greeks`, `_req_ids`, `_pending_reseat`, `_reseat_counts`, `_latched` and `_pending_messages` is what makes the next ON re-seed and re-subscribe from scratch, and `_stale`/`_stale_after`/`_no_value`/`_dropped` are cleared so no pre-OFF cell state can leak into the new session — consistent with what ESC-117's fix achieved by re-running `__init__`, which is the whole point of the change.

## 2. ESC-120 — CLOSED (`addressed`), re-verified

`precheck.json` says `task-graph.json` changed since the last review; it did, exactly where it should. `P23-T15` AC2 (and `tests[P23-T15-AC2].linked_acceptance_criterion` / `description` / `expected_result`) now state `name not in vars(IBApiClient)` **and** `getattr(IBApiClient, name) is getattr(EWrapper, name)`, plus the four absent bridge signals, and say in words that `getattr(..., None) is None` is unsatisfiable here **because** `IBApiClient` inherits `EWrapper` — so the wording can no longer be mistaken for a predicate the tree fails. Measured on the live interpreter (ibapi 9.81.1.post1), for all four callbacks: `getattr(...) is None` → **False ×4**, `name not in vars(IBApiClient)` → **True ×4**, identity with the `EWrapper` stub → **True ×4**, `hasattr(IBBridge, signal) is False` → **True ×4**. The enforcing case (`tests/test_d65_option_chain.py:595-607`) already asserted that form and is unchanged; `tests/test_d65_option_chain.py` + `tests/test_d65_residue.py` → **71 passed**, exit 0. No code or test edit was required, which is what a wording-only AC defect should look like. **Flip recorded in place.**

## 3. ESC-119 — code half fixed and verified, gate half NOT delivered → stays `open`

**What landed (verified, and it is what the escalation asked for first):** `SpreadEngine.reset_session()` is now the single owner of a session clear, `toggle_off()` delegates to it and is the live OFF entry point again, `_option_reset_engine` is deleted, and `P23-T16-AC2` parses `ui/main_window.py` to prove `"_option_engine.toggle_off()" in _option_stop` and the absence of both `_option_reset_engine` and any `._option_engine.__init__(`. The clock seam is preserved structurally (a reset that cannot drop `clock=`), the Target survives, and the residue-gate blind spot is now covered **for this symbol** by a case rather than by a reviewer. Footprint was correct (`services/option_spread_engine.py` is in `touches_files`), and the regression cases the escalation demanded (clean engine after OFF **and** after the cutoff, Target preserved) exist and discriminate. **No new dead code was introduced by the rework** (`reset_session` has a production caller, `toggle_off` has one, the two new test helpers are used in their own file).

**What did not land — the escalation's own second deliverable, verbatim:** *"Either way record whether clause (i) is meant to cover class methods: if yes, extend `_defined_symbols`/`scan_unreferenced_symbols` with an explicit exemption list for Qt/EWrapper name-invoked and duck-typed public surfaces; if no, state the module-level scope in the gate docstring so the owner's rule is not silently narrower than it reads."*

Neither branch was taken:

- **Not extended.** `tests/test_d65_residue.py:317-328` `_defined_symbols` iterates `ast.parse(text).body` only ("Public top-level names a module *offers*: defs, classes, constants") and `_census_candidates` (:603-609) feeds clause (i) from it plus `P23_ADDED_SYMBOLS`; **class methods are not candidates**, so a future dead method is still invisible. Nothing in `tests/test_d65_residue.py` changed in `c2fc2af` (the commit's 10 files do not include it).
- **Not recorded in the gate.** The gate docstring still claims clause (i) is "every P23 symbol has a production caller or a cited **code** registration site", with no statement that the implemented scope is module-level only. The task manager's notes do say, once, "the residue gate enumerates module-level symbols only, so a live method is invisible to it" (`task_manager_notes_P23.md:370`) — but that sentence exists to justify a *dependency edge*, is not a decision about what the rule should be, and lives in a file nobody reads when they read the gate.
- **And the "no" answer is not available without a requirements change.** `requirements.md` **AC-D65.12(i)** is unambiguous: *"every module, class, function, **method**, constant and signal added by P23 has a production caller…"*. The owner's ratified rule already covers methods, so the honest reading is "yes, extend the gate" — or amend the AC, which only Requirements may do. As it stands the owner's rule is still *silently narrower in the implementation than in the requirement*, which is precisely the risk ESC-119 was opened to eliminate.

**Why this is not a P23-T16 finding.** `P23-T16` did exactly what its three ACs demanded, and its `notes` claim that AC2 is "the mechanical form of 'no dead symbol, methods included'" is true only for `toggle_off`; it is a per-symbol source assertion, not clause (i) coverage of class methods. So the residual is the one invariant ESC-119 already carries (**one invariant, one escalation**) — I am not opening a third BUILD patch or a duplicate entry, and I am not closing the escalation on a partial delivery.

**Disposition:** `status` stays `"open"`, routed `TASK_MANAGER` (a new/scoped task owning `tests/test_d65_residue.py` to extend clause (i) to methods with the `EWrapper`/Qt/duck-typed exemption list clause (v) already establishes, plus a seeded dead-method fixture asserting RED — or a Requirements amendment to AC-D65.12(i) if the owner wants module-level scope after all). No owner decision on this exists in `orchestrator_state.json` (only ESC-055 is recorded there), so it needs one.

## 4. Full-pass duties

- **Mock/fake/stub scan (B.6, blocking invariant).** Grepped the `c2fc2af` production diff and the two changed production files whole for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness`: **no hits at all**. No mock endpoint, fake client/service, stub or harness in production, and no production module imports a test fake. **Clean.**
- **Usage docs.** `precheck.json` `doc_candidates` = `USAGE.txt`, `docs/`, `usage.md`, **all `touched: false`**; `P23-T16` carries `doc_required: false` and that is right — the rework changes no user-facing behaviour (the OFF/cutoff states, labels and line counts are identical; only *who* performs the engine clear changed), so `usage.md` correctly needed no edit. Ruling: **met — nothing to do.**
- **Pack-prose spot-check** (first task in the graph + guarantee-word tasks; `P23-T16` is new and its prose says "never re-initialises", "preserving"): its description does not contradict AC1–AC3 (both reset paths, both preserved values and the no-re-init claim are exactly what the ACs and tests pin), and each stated guarantee names its enforcing case (AC1→AC1, AC2→AC2, AC3→AC3). No prose/AC contradiction and no unenforced guarantee. The task manager's stronger claim at notes `:345` (AC2 as the mechanical form of "methods included") is folded into ESC-119 above rather than treated as a prose defect.
- **Full suite.** `test_verification.json` is **fresh and green** (pass, exit 0, 85.57 s, newer than both `build_log.md` and `c2fc2af`) — no independent re-run needed and none performed. Targeted re-runs: the four D65 suites together **114 passed** (`test_d65_spread_engine` + `test_d65_option_stream` + `test_d65_residue` **36** + `test_d65_option_chain`), exit 0.
- **Residue gate.** `tests/test_d65_residue.py` **36 passed** on the tree, with its seeded-red fixtures unchanged (the green tree is still paired with a proven-red fixture; the gate has not been emptied).
- **AC-D65.19 owner gate.** `docs/archive/probe_records/d65_paper_tws_acceptance.md`: **6** `Result: PENDING`, **0** checked boxes, 0 `Result: PASS`, header still "No result recorded yet". **Nothing fabricated. Still owner-gated.**
- **`docs/phase-changelog.md`.** Grep for `D65` / `P23` / "Option Spread": **0 hits** — still no phase entry, unchanged and correctly owner-gated (`docs/CHANGELOG.md` was auto-generated by `gen_changelog.py`, which is not that gate).
- **Escalation close-out.** Two open entries came in. **ESC-120** → `addressed` in place with fresh evidence (§2). **ESC-119** → left `open` (§3), with the reason recorded here rather than silently flipped; its `observed`/`expected` are unchanged so the owner can read the original ask. No `PRE-*` entries were open.

## 5. For the Orchestrator / owner

**One escalation is open and it needs a decision, not more code from Build:** **ESC-119** — `SpreadEngine`'s reset is delivered and verified, so the *defect* is gone; what is missing is the answer to "does the standing no-unused-code gate cover class **methods**?" `AC-D65.12(i)` says it does; the gate implements module-level only; the answer is either "extend the gate (+ a seeded dead-method fixture)" — a small task owning `tests/test_d65_residue.py` — or an explicit requirements amendment narrowing `AC-D65.12(i)`. Everything else in this pass closed.

**Owner gates unchanged and outside this review:** the **paper-TWS acceptance** (`AC-D65.19`, `P23-T14`: all six items `PENDING`, no evidence, no signature) and the repository documentation gate (`docs/phase-changelog.md` has no D65/P23 entry; `plan.md`/`architecture.md` as-built sync). The phase's production behaviour is sound and its suite is green on `c2fc2af`; the phase cannot be called *done* until those two owner actions are recorded.

# Code Review — P23 pass 4 (P23-T17, ESC-119 answered)

**Pass:** phase-final, **full pass** (phase-final always full).
**Scope (incremental):** **P23-T17** only — the single result newer than this log's previous `REVIEW_COMPLETE` marker (`precheck.json` `scope: ["P23-T17"]`, `fail_fast: []`, `overlaps: []`, 0 unattributed tree changes, `flags: []`, `doc_candidates` all `touched: false`).
**Inputs consumed:** `precheck.json` (fresh, 02:18:02), `build_log.md` wave 359, `docs/build/results/_archive/wave359_P23-T17.json` (`done`, 4/4 pass, `footprint_flags: []`, `files_changed: ["tests/test_d65_residue.py"]` — matches git), the task graph (`P23-T17` AC1–AC4), `requirements.md` AC-D65.12(i), and the committed tree **`a6800b2`** (clean).
**Verdict:** **P23-T17 delivers all four of its ACs on the live tree, and ESC-119's enumerated ask is closed.** ESC-119 flipped to `addressed` after independent re-verification (§2). Two **new, non-blocking** findings are opened with measurements: **ESC-121** (should-fix, TASK_MANAGER — clause (i)'s *evidence* standard is weaker than the requirement it enforces: test-file references count as "production callers", and method keys are probed by bare name) and **ESC-122** (nice-to-have, BUILD — a wave-local `CENSUS_ALLOWLIST == {}` literal). Neither is a P23-T17 defect; both were found by trying to falsify the extension rather than by reading it.

---

## 0. Verification provenance — the handed suite verdict was STALE, second pass in a row

`docs/code_review/test_verification.json` had mtime **01:40:31** — older than `build_log.md` (02:18:02), older than commit `a6800b2` (02:18:02) and older than the P23-T17 result (02:17:45). It was the *previous* pass's run and could not speak for this tree. Per the standalone fallback I ran the verifier myself:

```
verify_tests.py --command ".venv/bin/python -m pytest -q -m 'not webengine'"
-> VERIFY: pass  exit=0  88.9 s   (rewrote docs/code_review/test_verification.json)
```

Ground truth: **the full suite is green on `a6800b2`.** This is the second consecutive pass handed a verification artifact that predates the commit it is supposed to cover (see §0 of the previous entry); the freshly written file now post-dates `a6800b2`, so this pass is not resting on it. Task-attribution run by me: `tests/test_d65_residue.py` → **41 passed** (was 36).

## 1. P23-T17 — the five things I was asked to verify

| # | claim | how I verified it | result |
|---|---|---|---|
| 1 | the census enumerates class methods, keyed so a message names the class | Read `_class_methods` / `_census_candidates` and ran them over the live tree: **102** method candidates; `SpreadEngine.target` (`@property`) and `OptionSpreadsPanel._cells_for` (`@staticmethod`) are candidates; no key ends in a dunder; `VerifiedBackupPath.__new__` absent. `ast.walk` finds `ClassDef` nodes (not just module body), each body's `FunctionDef`/`AsyncFunctionDef` children are taken, key is `Class.method`, and a violation renders `module:Class.method`. | **pass** |
| 2 | the seeded dead-method fixture is discriminating | Ran the fixture through the gate's own `scan_unreferenced_symbols`: exactly `['fixture_module.py:Owner.orphan_method']`. Removed the caller's `owner.used_method()` → exactly `[orphan, used]`. Also ran the **reverse** mutation the suite does not: adding `owner.orphan_method()` to the caller → `[]`. Not flag-everything, not flag-nothing. | **pass** |
| 3 | the clause-(v) exemption needs a cited declaring class **and** a verified registering base | `FRAMEWORK_CALLBACKS` is keyed `(module, declaring class, method) -> base class`; `_framework_callback_exempt` requires `isinstance(base, type)`, `hasattr(base, method)`, the declaring class to really inherit that base (name check over `ClassDef.bases`), and the class body to define the method. Measured on the tree: `QStyledItemDelegate.initStyleOption` → `True`, `QWidget.sizeHint` → `True`, both entries resolve, and the two declaring classes do inherit those bases. A document/task-graph string is not a `type`, so it exempts nothing — asserted twice (allowlist value and framework value). | **pass** |
| 4 | the real tree and the full suite are green, and no clause was weakened | Residue suite **41 passed**; full suite `pass`, exit 0, 88.9 s on `a6800b2`. Deleted lines in the diff: 19, each replaced by a strictly wider or equivalent form (`QT_CALLBACKS` → `FRAMEWORK_CALLBACKS` gains the declaring class; `symbol not in tree[module]` → `_defines_symbol`; the old bare allowlist skip → a verified citation). `_defined_symbols` byte-identical; the seeded dead-symbol, unconnected-signal and red-then-green cases untouched. | **pass** |
| 5 | the docstring/scope claim matches the implementation | Module docstring's clause-(i) bullet now names class methods, the dunder exclusion and the clause-(v) cited-site exemption, and the module-level-only claim is gone; `test_docstring_states_the_implemented_census_scope` checks each sentence against the same candidate map (a real method key present, the dunder key absent) rather than asserting prose alone. I re-read the bullet against `_class_methods`/`_census_candidates`: "every method of every P23 class" is accurate — the four new modules are wholly P23, and `OptionSeries` is the only P23 class added to a pre-existing module (the other three extended modules' classes are pre-P23, verified). | **pass** |

Digits: method candidates **102**; new suite cases **5** (method-census, docstring-scope, dead-method fixture, framework-exemption, real-tree framework callbacks); suite **36 → 41**.

## 2. ESC-119 — CLOSED (`addressed`)

The escalation's own `expected` had five parts; all are delivered, and I re-verified each against the tree rather than the worker's summary:

- **"record whether clause (i) is meant to cover class methods"** — recorded by doing it: `AC-D65.12(i)` names *method*, the gate now censuses methods, and the docstring states the scope. No "no" branch was needed.
- **"extend `_defined_symbols`/`scan_unreferenced_symbols` with an explicit exemption list for Qt/EWrapper name-invoked and duck-typed public surfaces"** — `FRAMEWORK_CALLBACKS` is that list, and it is verified against the base class rather than trusted.
- **"no dead symbol, methods included"** — a method with no reference anywhere is now reported: measured by stripping *every* `toggle_off` mention outside the engine (production + tests) → `services/option_spread_engine.py:SpreadEngine.toggle_off` appears. The exact symbol ESC-119 named is caught when it is actually orphaned.
- **footprint** — `touches_files: ["tests/test_d65_residue.py"]`, and the diff is that file plus coordination docs; no production edit.
- **engine reset / regression case** — inherited from P23-T16 and still green (§1 row 4).

**Why closing is not a waiver:** while trying to break the extension I measured two ways the gate is still weaker than the requirement reads. They are a *different claim* from this entry's enumeration scope — they apply to module-level names too and pre-date P23-T17 — so they are carried by **ESC-121**, and the wave-local literal by **ESC-122**. The `verified` field on ESC-119 says exactly that.

## 3. New finding — ESC-121 (should-fix, TASK_MANAGER): clause (i)'s evidence is weaker than AC-D65.12(i)

`AC-D65.12(i)` says *every module, class, function, **method**, constant and signal added by P23 has a **production** caller*. The gate's reference pool is `sources()`, which includes `tests/`, so a test call satisfies it. Measured on the live tree by re-running every clause-(i) candidate against production files only:

- **15 P23 symbols have no production reference at all** while the census reports `[]`: `OptionSpreadsPanel.{target_value, toggle_colour, toggle_collapsed, preferred_width, elided_name}`, `validate_spread`, `SpreadEngine.{latched_causes, pair_score, pair_eligible, lease, pending_legs, window_step, pair_dropped, reseat_count}`, `option_chain_strikes`.
- `elided_name` is the clean example: production elides through `_ElideNameDelegate.initStyleOption` setting `option.textElideMode` (`ui/option_spreads_panel.py:103-105`) and never calls the panel helper (`:448`) — only tests do. `preferred_width` duplicates the `PREFERRED_WIDTH` constant that `sizeHint` (`:442-444`) actually reads. `validate_spread` is imported by no production module.

Second, measured: for a method key the probe is `probe = method` — the **bare method name** — so any `Name`/`Attribute`/`Constant`/`arg` occurrence anywhere counts. Seeding one dead method at a time into a copy of `services/option_spread_engine.py` and running the gate's own scanner: **caught** `_zzz_orphan_marker`, `refresh`; **not caught** `close`, `update`, `run`, `start`, `stop`, `size`, `target`, `reset`, `clear`, `handle`, `name`, `value`, `items`, `set`, `get`, `emit`, `connect`, `_out`, `_drain`, `paintEvent`, `sizeHint` — **19 of 23 sampled**. Consequence for the exact ESC-119 scenario: deleting `ui/main_window.py:2082` (`self._option_engine.toggle_off()`) leaves the gate green because `tests/test_d65_spread_engine.py:1216` still calls it.

Third, a consequence for AC3: "a same-named method on a class with no such base is still censused" is true in the isolated two-class fixture but not on a real tree, because the reachability check returns before the exemption is consulted — a seeded unrelated class defining `sizeHint`/`paintEvent` is green with no exemption entry. The AC wording and the AC1-mandated evidence standard are in tension; that is a Task Manager decision, not a Build patch (repeat-invariant rule: one invariant, one escalation).

## 4. New finding — ESC-122 (nice-to-have, BUILD): a wave-local literal in a standing gate

`test_method_census_covers_p23_classes_and_excludes_dunders` ends with `assert CENSUS_ALLOWLIST == {}` ("no exemption may stand in for a symbol that has a call site"). That forbids *every* entry, including a legitimate one — e.g. the duck-typed public surface ESC-119 itself contemplated, which `FRAMEWORK_CALLBACKS` cannot express because that path needs a base class declaring the name (ESC-121's 15 symbols are exactly that shape). `docs/memory.md` records this defect shape from D47/P6 ("assert the invariant … rather than the current instance count or a literal list" — five wave-local expectations broke in one batch). Green today, so hygiene only.

## 5. Full-pass duties

- **Mock/fake/stub scan (B.6, blocking invariant).** The `a6800b2` diff touches one test file plus coordination docs; no production file changed (`git show --stat`). Grep of the diff for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness`: **no hits**. No production module imports a test fake; no mock endpoint, client or harness anywhere outside tests. **Clean.**
- **Usage docs.** `precheck.json` `doc_candidates` = `USAGE.txt`, `docs/`, `usage.md`, all **`touched: false`**; `P23-T17` carries `doc_required: false`, which is right — this is a test-only change to the residue instrument, with no user-facing behaviour. Ruling: **met — nothing to do.**
- **Pack-prose spot-check.** Sampled task P23-T17 (new; its description carries "never allowlist it"). Its prose does not contradict AC1–AC4: "no production symbol is expected to change … if the implemented census reports one, report it, never allowlist it" matches AC1's green-with-no-exemption clause and AC3's cited-site rule, and every stated guarantee names its enforcing case (AC1→the candidate-map case, AC2→the fixture + mutation, AC3→the three-shape fixture, AC4→the docstring case). No prose/AC contradiction, no unenforced guarantee. (The earlier passes' sample — T1, T8, T10, T12 — is unchanged.)
- **Residue gate on the tree.** 41 passed, and its seeded fixtures still assert RED (the green tree remains paired with a proven-red fixture; the gate was not emptied).
- **AC-D65.19 owner gate.** `docs/archive/probe_records/d65_paper_tws_acceptance.md`: **6** `**Result:** PENDING`, **0** `Result: PASS`, every item unchecked, evidence fields empty, sign-off blank, header still "No result recorded yet". **Nothing fabricated. Still owner-gated.**
- **`docs/phase-changelog.md`.** Grep for `D65` / `P23` / "Option Spread": **0 hits** — unchanged and correctly owner-gated (`docs/CHANGELOG.md` is `gen_changelog.py`'s output, not that gate).
- **Escalation close-out.** One open entry came in (**ESC-119**); re-verified and flipped to `addressed` with fresh evidence (§2). No `PRE-*` entries were open. Two entries added (**ESC-121**, **ESC-122**) with their measurements.

## 6. For the Orchestrator / owner

**Closed this pass:** ESC-119 — the gate now enumerates class methods, its Qt/EWrapper exemptions resolve against a declaring class *and* a registering base, a dead method with no reference anywhere is caught, and the docstring states the implemented scope.

**Open, non-blocking:** **ESC-121** (should-fix, TASK_MANAGER) — decide whether a test reference is a "production caller" and whether a method's evidence must name its class; the 15 symbols it lists are the immediate decision set. **ESC-122** (nice-to-have, BUILD) — make the allowlist's safety a per-entry invariant. Neither blocks the phase's functional ACs; both are about the standing instrument the next phases inherit.

**Outside this review, unchanged:** the **owner-run paper-TWS acceptance** (`AC-D65.19`, P23-T14: six items `PENDING`, no evidence, no signature) and the owner-gated **`docs/phase-changelog.md` D65 entry** (absent; `plan.md`/`architecture.md` as-built sync rides with it). The phase's production behaviour is sound and its suite is green on `a6800b2`; those two owner actions are what remain before the phase can be called done.

Status: REVIEW_COMPLETE

---

# Code Review — P23 pass 5 (the ESC-121/ESC-122 fix round: deletions, AC-D65.4 wiring, gate hardening, live-TWS record)

**Pass:** phase-final, **full pass** (phase-final is always full; the scope also carries shared-file overlaps — `services/option_spread_engine.py` by T22+T23 and three shared test files — which forbids a light tier).
**Scope (incremental):** the ten results newer than this log's `REVIEW_COMPLETE` marker — **P23-T17 … P23-T26** (`precheck.json` scope; `fail_fast: []`; `escalation_entries: []`; 0 unattributed tree changes; all flags informational overlap leads). Tree: commit **`39856b0`**, clean; `build_log.md` terminal `Status: READY_FOR_REVIEW`.
**Inputs consumed:** `precheck.json` (17:01:43), `test_verification.json` (**pass, exit 0, 239.38 s — mtime 17:09:52, i.e. AFTER the 17:05:52 commit; the two stale-verification passes this log records do not repeat here**), `build_log.md`, the ten archived results, `task-graph.json` (P23-T17..T26 ACs), `requirements.md` AC-D65.4/AC-D65.12(i)/AC-D65.19, `plan.md`/`architecture.md`, and `escalations.json`.
**Verdict:** **The round does what it was asked to do.** ESC-121 is closed by a genuinely production-only, class-bound clause (i) plus the removal of every symbol it listed; ESC-122 is closed by a per-entry invariant with a separate phase snapshot; AC-D65.4 is now implemented **in the live path** and the two red-first cases really are red on the pre-change engine and green on this one; the acceptance record is the live-TWS read-only checklist, six items `PENDING`, with nothing fabricated. I opened **one should-fix** (the acceptance record names a build commit that predates AC-D65.4 — ESC-123), **one nice-to-have** latent guard loss in `evaluate()` (ESC-124), and **one should-fix PLAN doc-sync** (ESC-125: plan/architecture still say paper-TWS and still describe `window_step`). No blocking finding.

---

## 0. What I re-derived rather than trusted

- **The deletions are real and dead.** 24 function definitions removed (commit message says 18; measured with `git show --numstat` + a def-by-def count: **2 module-level**, **15 engine** — 11 accessors + `window_step`/`_requested_targets`/`_walk_candidate`/`_best_neighbour` — and **7 panel**). Production grep (ui/, services/, data/, ibkr/, config/, main.py) returns **0** hits for every one of them. The only bare-name residues are unrelated members on other classes (`WatchlistPanel.set_collapsed`/`toggle_collapsed`) and the `Action("release")` kind string / `release_rt` / `release_resources` — none is a reader of a deleted member.
- **The red-first evidence is real.** I loaded `services/option_spread_engine.py` **as of `39856b0^`** into a probe module, swapped it in for the current class in `tests/test_d65_spread_engine.py`, and ran the two cases the owner's rule is supposed to make red:
  - `test_P23_T23_AC4_disagreeing_bases_decide_no_direction` — **OLD: AssertionError** (`acts.actions == []`; the old `_best_neighbour` path stepped on a mixed-base anchor) / **NEW: pass**.
  - `test_P23_T23_AC5_improvement_below_the_band_never_moves_the_ladder` — **OLD: AssertionError** (`d` improved by 0.03, below `h`, and the old path stepped) / **NEW: pass**.
  Neither passes for a loosened reason: AC4 asserts the deciding bases and both `d` values (`0.60/1.40/1.00`, `d = 0.10` vs neighbour `0.05`) and only then that nothing moved; AC5 asserts the exact 0.03 improvement and that the anchor is unchanged.
- **The gate discriminates.** My own probes against `tests/test_d65_residue.py`'s scanner (not its test cases) are listed in §1.
- **The full P23 surface passes.** `pytest` over the eight touched suites (spread 27, stream 29, panel 23, residue 47, ladder 77, chain 34, acceptance 5, d45-removal 9 = **251 cases**) → **exit 0** on `39856b0`.

## 1. ESC-121 — CLOSED (`addressed`): production-only, class-bound, and the 15 symbols are gone

| claim | my probe | result |
|---|---|---|
| clause (i)'s pool is production-only | added `zzz_probe_helper` to a copy of `services/option_ladder.py`, referenced it **only** from `tests/test_d65_residue.py` → `['services/option_ladder.py:zzz_probe_helper']`; added one production reference → gone. `scan_unreferenced_symbols` defaults to `_production_subset(tree)`; the only override of `reachability_tree` in the whole file is the fixture case that proves the parameter is honoured verbatim (line 1977) — nothing widens the real-tree check. | **pass** |
| a method key is class-bound at both ends | appended `def close(self)` to `SpreadEngine` in a tree copy → `services/option_spread_engine.py:SpreadEngine.close` reported **even though `close` occurs in production elsewhere** (`data/db_backup.py`: `conn.close()`) — exactly the hole ESC-121 measured (19 of 23 sampled names were invisible before); adding `self.close()` inside the class cleared it. A seeded `class ZzzUnrelated: def sizeHint` in a production module → reported, with no exemption entry, because the clause-(v) check is now consulted *after* a failed reachability test instead of returning early. | **pass** |
| the seeded fixtures still separate red from green | two-module fixture reports exactly `fixture_module.py:Owner.orphan_method`; removing the caller's `owner.used_method()` adds `Owner.used_method`; the real tree is `[]` in the same run. With `FRAMEWORK_CALLBACKS` passed, my seeded tree's only violation was the symbol I seeded — the two real Qt callbacks are still rescued through their cited `(declaring class, registering base)` entries. | **pass** |
| the 15 listed symbols are resolved, not exempted | 0 production hits for `target_value`, `toggle_colour`, `toggle_state`, `preferred_width`, `elided_name`, `latched_causes`, `pair_score`, `pair_eligible`, `pending_legs`, `pair_dropped`, `reseat_count`, `window_step`, `_requested_targets`, `_walk_candidate`, `_best_neighbour`, `validate_spread`, `option_chain_strikes`; `set_collapsed`/`toggle_collapsed` survive only as unrelated **`WatchlistPanel`** members (`ui/watchlist_panel.py:628`/`:636`, a different class, never imported here); no `.lease(`/`.release(` production call (the bare-name hits are `Action("release")` and `release_rt`/`release_resources`). `CENSUS_ALLOWLIST` is `{}` on the finished tree. | **pass** |
| the requirement and the gate now agree | the docstring/AC language is production-only + class-bound, and the tree is green under that stricter rule — so the gate is not weaker than `AC-D65.12(i)` any more; nothing needed amending in `requirements.md`. | **pass** |

## 2. The deletions — re-pointed, not softened

Read every removed assertion in `tests/test_d65_spread_engine.py`, `tests/test_d65_option_stream.py`, `tests/test_d65_option_panel.py`, `tests/test_d65_option_ladder.py`, `tests/test_d65_option_chain.py`, `tests/test_d45_removal.py`:

- `pair_eligible(...) is False` → `_score_pair_complete(...) is None` — the helper *was* `is not None`, so this is identical, not weaker. `pair_score` → `_score_pair_complete`; `pending_legs()` → `{leg for leg in _subscribed if leg_state(leg) == "pending"}` (a verbatim copy of the deleted body, hoisted to a test helper); `target`/`spot`/`req_id`/`latched_causes`/`pair_dropped`/`reseat_count` → `_target`/`_spot`/`_req_ids`/`sorted(_latched)`/`LegKey in _dropped`/`_reseat_counts.get(side, 0)`.
- Panel: `target_value()` → `target_edit.text()` + `_last_valid_target`; `toggle_state()`/`toggle_colour()` → `isChecked()` + the `spread_state` property + the button palette colour read directly (strictly *stronger* than the constant-returning helper); `toggle_collapsed()` → `header_button.click()`; `set_collapsed()` → `header_button.setChecked()`; `preferred_width()` → `PREFERRED_WIDTH` + `sizeHint().width() == 360`; `elided_name()` → a test-local `QFontMetrics.elidedText(...ElideRight...)` against the table's own metrics. The D45 zero-transmit walkthrough now collapses through `header_button.click()` and keeps both collapsed/restored assertions.
- `validate_spread` → a **verbatim** `_fixture_guard` in `tests/test_d65_option_ladder.py` (rejects 10-wide and both inverted PCSs, accepts 7435/7455, 7425/7445, 7340/7320 and every canonical `ladder_pairs()` pair). `option_chain_strikes`'s dedicated case goes with its subject as the AC permits, and `select_zero_dte_series` still returns sorted per-right strikes (retained assertion from an unsorted payload).
- **Nothing was deleted to make something pass.** The one case whose *concept* disappeared (`window_step({"CCS": target})` alternating-target oscillation) has a live analogue that survived the refactor: the equal-`d` three-rung table evaluated six times in `test_P23_T8_AC1` asserts **0 actions and an unchanged anchor**, and the exactly-`h` refusal is asserted twice (T23-AC1's second evaluation, T23-AC3's parametrized `(1.00, 0.05, False)` / `(3.00, 0.10, False)`).

## 3. AC-D65.4 in `evaluate()` — the rule, not a proxy

`_step_candidate(side, live)` (services/option_spread_engine.py:1133) against the AC text:

- **one rung, decided direction** — `candidate = live ± STRIKE_STEP`; below-`T` bases → CCS down / PCS up, above-`T` → CCS up / PCS down, mixed → `None`. Matches AC-D65.4's "toward-the-money (CCS: both strikes down; PCS: both strikes up) … away (CCS: up; PCS: down)".
- **all-bases veto** — `all(< T)` / `all(> T)` with a bare `else: return None`; verified red on the old engine (§0).
- **strict `> h`** — installs only when `nxt.distance < current.distance - band - 1e-9`; `band = match_band(target) = max(0.05, option_tick(target))` (services/option_ladder.py:219) — exactly `h = max(0.05, one_tick)`. The 1e-9 tightens, never loosens, so "exactly `h`" cannot install.
- **matched pair never moves** — `current.distance <= band + 1e-9` (the same predicate as `_anchor_matched`, which survives for the `_seed_bounded` branch). The ask-basis-only case (`d = 0`) is asserted.
- **listed / quoting / chain edge** — unlisted decided rung latches `CAUSE_WALK_CHAIN_EDGE` naming the current anchor (via `_latch`, which is per-cause once-only, so later evaluations cannot repeat it — asserted); unquoted arriving rung returns `None`.
- **monotonicity** — each installed step strictly lowers `d` by `> h`, and `d` is a function of the quotes, so a two-rung oscillation is structurally impossible (the AC's own measurable list asks for that case; the equal-`d`/exactly-`h` refusals are what pin it).
- **fixture faithfulness (P23-T25)** — the stream fixture's CCS mid now falls `0.02`/point and PCS rises `0.02`/point (`f(x)-f(x+20) = 1.00 - 0.02x`; verified algebraically against the new `_price` polynomials), so one 5-point rung moves `d` by **0.10** at `T < 3.00`, with bases at `mid ∓ 0.10`. That is the economically faithful shape, and it is the *data* that moved — `band`, the strict comparison and the veto are untouched. The re-pointed target-commit cases now step CCS **down** to 7345 and PCS **up** to 7355 at `T = 1.20`, keep the reqId/one-out-one-in/≤16-line registry assertions, and add a second evaluation that moves nothing.

## 4. ESC-122 — CLOSED (`addressed`): per-entry invariant, phase snapshot separate

`assert CENSUS_ALLOWLIST == {}` is gone. `scan_census_allowlist` holds each entry to three halves simultaneously — citation resolves to a live `<.py>:<line>` registration site, the key is a clause-(i) candidate, the key is one the scanner would otherwise report, and `_has_python_call_site` finds no production call — and the phase's zero-exemption state survives as one separate `assert not CENSUS_ALLOWLIST` whose message says "phase-scoped, not the standing rule … no P23 symbol needs a census exemption today". My probes: legitimate connect-site entry → `[]`; the same citation for a genuinely-called method → *"has a Python call site"*; a document citation → *"a document mention registers nothing"*; a non-candidate → rejected; empty → `[]` over both a fixture and the real tree. `test_census_allowlist_state_is_phase_scoped_not_a_blanket_rule` reads the suite's own AST and self-tests its detector on both forms, so the absence claim is not a grep of prose.

## 5. P23-T26 — the acceptance record is honest

Read in full. Live TWS on **`127.0.0.1:7496`**, read-only by construction (zero order code; `reqSecDefOptParams` / `reqMktData` / `cancelMktData` only), observation-only, the D48/D52 precedent cited; no "paper port", no paper-account field, no "never the live port"; the six AC-D65.19 checks appear in order, each with **`**Result:** PENDING`** (count = 6), an empty evidence placeholder, and no `Result: PASS` anywhere; the sign-off block is blank; the no-order rule is stated twice and no item asks the owner to place/modify/cancel an order (the only cancel is a market-data line). `INDEX.md` carries the matching three-column row naming AC-D65.19 / A211, P23-T26, and **PENDING**. The residue gate's `GATE_RECORD` paragraph now describes the live-TWS run owned by P23-T26 and keeps "still OPEN / NOT claimed". One defect found — the header's build commit (§7, ESC-123).

## 6. Full-pass duties (whole phase, not just the slice)

- **Mock-endpoint containment (B.6, blocking invariant).** Production diff = `ibkr/contracts.py`, `services/option_ladder.py`, `services/option_spread_engine.py`, `ui/option_spreads_panel.py`; grep of that diff for `mock|fake|stub|simulat` → **no hits**; no production module imports anything from `tests/`. The only fakes are the stream suite's recorder client, which lives in `tests/`. **Clean.**
- **Usage docs.** `doc_required: false` on all ten tasks, and rightly so: nothing here changes the user-facing contract. In fact the docs are now *more* correct than before — `usage.md:197-198` already promised "the ladder steps toward the listed 20-wide credit spread in 5-point moves, one step per evaluation, and stops when the credit is inside one tick's band of the Target", which is what the code now does for the first time. `USAGE.txt` is a feature index and needs nothing. Ruling: **met, no doc change**.
- **Pack-prose spot-check.** Phase-first task P23-T1 was sampled in pass 2 and is unchanged; this pass sampled the tasks whose packs carry guarantee words — **T18** ("never a bare name"), **T25** ("never exceeds 16"), **T26** ("all six items stay PENDING"). No prose contradicts an AC, and every guarantee names its enforcing case (T18-AC2's fixture + the `SpreadEngine.close` appended-method case; T25-AC2's `max(option…) <= 16` + second-evaluation stop; T26-AC2's six-PENDING parse). **No TASK_MANAGER routing needed.**
- **Residue gate on the tree.** 47 cases (was 41), green, with its seeded dead-symbol / dead-method / unconnected-signal fixtures still proven red.

## 7. New findings (none blocking)

- **ESC-123 (BUILD, consistency, should-fix)** — `d65_paper_tws_acceptance.md` names `Build commit: c04cc03`, which **predates** the AC-D65.4 wiring: `git show c04cc03:services/option_spread_engine.py` has **0** `_step_candidate` and **1** `def window_step`; the phase tree is `39856b0` (2 / 0). Checklist item (3) exercises exactly the step decision that changed, so the owner's evidence would be attributed to a tree without the behaviour being accepted. One-line header fix; the existing test accepts any well-formed sha.
- **ESC-124 (BUILD, quality, nice-to-have)** — `evaluate()` dropped the deleted `window_step`'s guard: the old code advanced `_session_anchor` only `if … self._install_windows(acts, steps)` returned True; the new code advances unconditionally after the call. On the `_install_windows` budget-refusal branch (returns False *before* setting `_anchors`, after already cancelling the leaving legs) the remembered session anchor would disagree with the live one. **Not reachable today** — a one-rung step swaps 1 leg per side (stale 2, added 2, free `16-14 = 2`), so I am labelling it latent, not paging. The partial-teardown-on-refusal behaviour itself predates this commit and is *not* part of the finding.
- **ESC-125 (PLAN, consistency, should-fix)** — canonical docs still describe the superseded phase shape: `plan.md` 5388 / 5619 / 6497 / 6545 / 6547 and `architecture.md` 8968 / 9389 / 9885 all call AC-D65.19 a **paper-TWS** run (requirements.md amended it on 2026-11-18 to the owner's **live** TWS, read-only, on 7496 — the owner stated "there is no paper-TWS"), and `plan.md:6116` still lists `window_step(target_anchor)` as the engine's walk API. Docs-only; the Orchestrator is holding this sync until the review lands, so the escalation is its trigger.

**Not a finding, for the record:** the commit message says "18 test-only symbols"; the measured count is **24** function removals (26 `def`/`@property` lines). The code is right; the message undercounts.

## 8. Escalation close-out

- **ESC-121 → `addressed`.** Re-verified the invariant myself (§1), not from the task-graph edit: production-only pool, class-bound method evidence, exemption consulted independently of reachability, and all 15 named symbols deleted with their facts re-pointed to production surfaces.
- **ESC-122 → `addressed`.** Per-entry invariant with three halves, a discriminating detector self-test, and a separate phase-scoped snapshot (§4); my probes redden a bad citation and an entry for a called symbol.
- **PRE-021 (P23-T22) → `addressed`.** The residue was a missing selfcheck stamp; the archived result now carries `selfcheck.verdict = pass`, `footprint_ok: true`, `violations: []` for this task id, its three manifest tests pass, and the post-commit full suite (plus my 251-case scoped run) is green.
- **PRE-022 (P23-T26) → `addressed`.** Same residue; `selfcheck.verdict = pass` at 16:59:17Z with its own two-suite run exit 0, four manifest tests pass, footprint clean, and this round's precheck reports no fail-fast/mechanical entries.
- **Opened:** ESC-123 (BUILD), ESC-124 (BUILD), ESC-125 (PLAN).

## 9. For the Orchestrator / owner

**The phase's code is sound and its instrument is now honest.** AC-D65.4 exists in the live path with red-first proof; the no-dead-code rule has a gate strong enough to enforce it and no exemptions; the acceptance record is a real live-TWS checklist.

**Two actions stay outside this review and the phase cannot close without them:**
1. **The owner-run live-TWS acceptance** — `AC-D65.19`, still **6/6 PENDING**, no evidence, no signature. The build records no result and marks nothing satisfied; only the owner's run fills it (and ESC-123 should land first so the evidence names the tree it was collected on).
2. **The owner-gated `docs/phase-changelog.md` D65 entry** — still absent (grep for `D65`/`P23`/`Option Spread`: 0 hits).

**Third gate, routed not owner-run:** **ESC-125** — the `plan.md`/`architecture.md` doc sync (paper-TWS → live-TWS, and `window_step` → `evaluate()`'s step decision). I agree with the hold and have made it a PLAN escalation so it cannot be lost.

Status: REVIEW_COMPLETE

---

# Pass 6 — escalation close-out (P23 @ `db21672`)

**Pass:** phase-final, escalation close-out. **Tier:** full (phase-final). **Scope:** the three open entries only — ESC-123 (BUILD, P23-T26), ESC-124 (BUILD, P23-T23), ESC-125 (PLAN, P23-T26). No task is re-reviewed: nothing in `docs/build/results/` is newer than the last marker, and no result was re-consolidated after `db21672`.

**Verification state — read before the verdict.** `precheck.json` (12:01 local) and the previous `test_verification.json` (12:09 local) both **predate** HEAD `db21672` (14:58 local), so I re-ran the suite myself (`verify_tests.py`, `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q`). **The working tree is not the committed tree:** another session is writing the P24/D66 docs into it while this pass runs (`docs/requirements/{requirements,design_gaps,open_questions}.md`, `docs/plan.md`, `docs/architecture.md`, `docs/codebase-map.md` are modified; one residue violation moved `plan.md:6893 → :6897 → clear` between two of my own runs). Measured separately:

| tree | run | result |
|---|---|---|
| clean worktree at `db21672` | seven `tests/test_d65_*` + `test_d45_removal` + both requirements guards | **257 passed, 0 failed** |
| clean worktree at `db21672` | full `tests/` | 1737 tests, 3 failed — all three **missing-untracked-artifact** failures (`docs/build/approvals/P7-T06-1min.md` and `docs/build/results/_archive/` are untracked, so a pristine checkout lacks them); in the real tree those modules are **21 passed, 0 failed** |
| working tree (P24 docs uncommitted) | full `tests/` (`test_verification.json`) | **fail, exit 1** — exactly `test_d60_follow_offset::test_p21_t3_ac2_history_intact` and `test_p20_proxy_guard::test_p20_t3_ac2_history_intact`, both `docs/requirements/requirements.md differs from HEAD`; re-checked at close: 2 failures, the same two |

**Ruling:** the committed phase tree `db21672` **is green**. The working tree's two failures are HEAD-baseline freeze guards reddened by uncommitted P24 amendments to `requirements.md`; they clear when that doc is committed. No P23 code is implicated and no task reopens. Heads-up for P24 (not a P23 finding, no escalation opened): while the P24 plan section was mid-write, `tests/test_d65_residue.py::test_canonical_fixtures_survive_and_the_typos_do_not` flagged `docs/plan.md: banned example 7315/7435 presented live` — the P24 exit-condition sentence that names `7315/7435` falls inside the gate's 3-line claim window. It cleared as the doc changed; if the committed P24 text keeps that sentence in a claim context, the P23 fixture gate will be red at P24 build (rephrase the sentence, or widen the gate's "named as forbidden" exemption).

**Mock-endpoint scan (full-pass duty; `db21672` production diff = `services/option_spread_engine.py`, `ui/main_window.py`):** `mock|fake|stub|simulat` → no hits; no production module imports from `tests/`. **Clean.**

## ESC-124 → `addressed` (BUILD, P23-T23)

- **Both named sites are guarded on the live tree.** `services/option_spread_engine.py:1203-1206` (200 re-seat branch) reads `if self._install_windows(acts, targets):` and only then advances `_session_anchor[side]` / `_session_anchor_expiry`; `:1226-1229` (step branch) reads `if targets and self._install_windows(acts, targets):` with the identical guarded body.
- **A third site the entry did not name is fixed too:** the seed commit path `:996-998` now wraps `_install_window(acts, side, anchor)` before advancing the anchor. `_finish_bound`'s `:1026` call is unguarded but advances no session anchor, so it cannot desync.
- **Source proof it was the fix:** `git show db21672 -- services/option_spread_engine.py` shows the unconditional `self._install_windows(acts, targets)` + unguarded assignment (and the reseat branch's assignment-above-the-call form) replaced by exactly these guards.
- **Behavioural probe (monkeypatched mutant — no file edited):** forcing `SpreadEngine._install_windows` to return False leaves the step path at `_session_anchor == {CCS: 7330.0, PCS: 7330.0}` with `_anchors` unchanged and 0 actions, and leaves the 200 re-seat path (pending reseat `{CCS: 7335.0}`) also at `{CCS: 7330, PCS: 7330}`. Pre-guard both would have advanced.
- **Guard case:** `tests/test_d65_spread_engine.py:1281::test_P23_T23_ESC124_a_refused_install_leaves_the_session_anchor_with_the_live_one` drives the real capacity refusal (`subscribes == []`, `live_legs == MAX_OPTION_LINES - 2`, both anchors stay at 7330), then frees the lines and asserts both anchors move to 7325/7335, then repeats under the re-seat path. Passes; 257/257 with the phase suites in a clean `db21672` checkout.

## ESC-125 → `addressed` (PLAN, P23-T26)

- **Grep:** `paper-TWS`, `paper TWS`, `window_step` → **0 hits in `docs/plan.md`** and **0 hits in `docs/architecture.md`**.
- **AC-D65.19 now reads as the live-TWS run, owned by P23-T26:** `plan.md:5388` "(9) live-TWS, read-only acceptance → new P23-10 … against `127.0.0.1:7496`"; `:5619-5620` the AC-D65.19 matrix row ("owner-run live-TWS, **read-only** acceptance on `127.0.0.1:7496` … P23-10 (built as P23-T26)"); `:6502-6503` "the owner's recorded live-TWS, **read-only** run and P23-10 (built as P23-T26) owns it"; `:6551` heading "P23-10 — Owner-run live-TWS, read-only acceptance (built as P23-T26)"; `:6554` "live-TWS, **read-only** … on `127.0.0.1:7496` (there is no paper account — A211)". `architecture.md:8968-8969` "(I) the live-TWS, read-only acceptance run … against `127.0.0.1:7496`"; `:9390-9391` "owner-run live-TWS, **read-only** acceptance record (live `127.0.0.1:7496`, observation-only)"; `:9887` AR-P23-22 "The live-TWS, read-only acceptance run (`127.0.0.1:7496`, observation-only)".
- **Step decision is `evaluate()`'s own:** `plan.md:6104-6121` (P23-04) now says "`evaluate()` decides and installs the step itself: `_step_candidate(side, live)` … `_install_windows(acts, targets)`" — the `window_step(target_anchor)` entry is gone.
- **Residual, deliberate, not a violation:** the record's **filename** `d65_paper_tws_acceptance.md` is still referenced (`plan.md:6564/6575/6699`, `architecture.md:9417/9918`). `plan.md:6564-6566` and the record's own head note (lines 12-14) state the name is retained so existing references resolve and that its content describes the live-TWS run — a recorded naming decision, not a paper-TWS description of the criterion.
- `requirements.md` AC-D65.19/A211 at HEAD already read the live-TWS, read-only acceptance, so all three canonical documents now agree.

## ESC-123 → stays `open` (BUILD, P23-T26)

- **The defect is still on the tree:** `docs/archive/probe_records/d65_paper_tws_acceptance.md:4` still reads ``Build commit: `c04cc03` (`c04cc03c0a12e60a4c10a34dab44810efbc960a4`) — the build tree this checklist describes.``
- **Measured:** `c04cc03` is HEAD~2 (`git rev-list --count c04cc03..HEAD` = 2). At `c04cc03`: `_step_candidate` **0** hits, `def window_step` **1**. At HEAD `db21672`: **2** and **0**. The record was added at `39856b0` already naming `c04cc03`, so it was stale when authored and is two commits stale now.
- **Why it is not acceptable as-is:** the header's own words attribute the checklist to a build tree, and the acceptance will be run against the shipped tree. `db21672` additionally changes `ui/main_window.py`'s chain-failure behaviour (surfaces the IB chain error code and stops claiming no-0DTE on failure) — precisely what item (1) (eight rows populate) and the no-0DTE empty state observe — so evidence attributed to `c04cc03` comes from a tree that neither steps the ladder (item 3) nor reports chain failure the way the shipped app does.
- **Exact fix (one line, BUILD, `P23-T26`):** replace line 4 with
  ``Build commit: `db21672` (`db216721b7f45f42cfb92d3f968de58093e238e9`) — the build tree this checklist describes.``
  Verified compatible with `tests/test_d65_acceptance_record.py::test_header_names_the_build_commit_and_the_d48_d52_precedent`: the regex matches and the short-is-long-prefix invariant holds (I ran the test's own regex over the exact replacement line). **No test change needed.**

## Escalation close-out

- **ESC-124 → `addressed`** (verified above, not from the commit message).
- **ESC-125 → `addressed`** (verified above).
- **ESC-123 → left `open`**, with the exact one-line change above. No other entry is open: ESC-121/122 and PRE-021/022 were closed in pass 5 and are not reopened.

## For the Orchestrator

1. **ESC-123 first, then the owner's run** — the acceptance record must name `db21672` before it collects evidence, or the phase's only live-gate evidence is attributed to a tree without AC-D65.4.
2. **The working tree's red suite is P24 doc state, not P23** — `docs/requirements/requirements.md` (plus `design_gaps`/`open_questions`) is uncommitted, so the two `*_history_intact` freeze guards compare against a stale HEAD. Commit (or stash) the doc sync and the suite is green again; the committed `db21672` tree measured 257/257 on the phase suites and 1737 tests with only the three untracked-artifact failures in a pristine checkout.
3. **P24 warning (no escalation opened):** the P24 plan sentence naming `7315/7435` trips `test_d65_residue`'s fixture ban while it sits in a claim window — fix the wording or the gate's exemption before P24's build gate.

Status: REVIEW_COMPLETE

---

# Pass 7 — single-escalation close-out (ESC-123, P23-T26 @ `db21672` + Q-75)

**Pass:** phase-final, single-escalation re-verify. **Tier:** light (one documentation line, no scoped task changed, phase suites unchanged since pass 6).

Q-75 applied the pass-6 required change to `docs/archive/probe_records/d65_paper_tws_acceptance.md`. Verified on the live tree, not from Q-75's word:

1. **The line is exact.** Line 4 is ``Build commit: `db21672` (`db216721b7f45f42cfb92d3f968de58093e238e9`) — the build tree this checklist describes.`` — byte-identical to the required replacement; short sha is the long sha's prefix, the long sha is 40 hex and equals `git rev-parse HEAD`.
2. **It is the only change.** `git diff -- docs/archive/probe_records/d65_paper_tws_acceptance.md` is one hunk with exactly one removed (`c04cc03` / `c04cc03c0a12e60a4c10a34dab44810efbc960a4`) and one added line. No other line of the record differs, so no meaning was altered.
3. **The record is still an open gate.** Status line unchanged ("PENDING — owner-run gate. No result recorded yet; every item below is unchecked."), `**AC-D65.19 is OPEN.**` present, **9 unchecked / 0 checked** boxes, `**Result:** PENDING` ×6, **zero** PASS results, sign-off date line still blank.
4. **The header invariant holds.** `tests/test_d65_acceptance_record.py` — **5 passed, 0 failed**, including `test_header_names_the_build_commit_and_the_d48_d52_precedent` (regex + short=long-prefix); no test change was needed.

**ESC-123 → `addressed`.** The evidence header now names the shipped code tree, so the owner's run will be attributable to the tree that contains AC-D65.4 and the `db21672` chain-failure behaviour. The edit is still uncommitted in the working tree, which is harmless: the header names the code tree, not the doc's own commit.

No other entry is open. No production code or other docs were touched.

Status: REVIEW_COMPLETE
