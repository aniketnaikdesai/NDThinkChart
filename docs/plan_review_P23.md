# Plan Review — Phase P23 (Option Spreads panel in the right dock, D65)

**Status: APPROVED**

**Pass type:** targeted re-validation of `RC-11`–`RC-13` (revision 3, `retry_3_of_3`) + full
Validation Method. **Lint backstop:** `plan_lint.py --phase P23` → `LINT PASS: P23 (canonical
sections); 0 failure(s), 0 warning(s)` — carried in the preamble and re-run after this pass's
editorial corrections, still PASS.

**Decision:** APPROVED. `docs/plan.md` § *Phase P23* is flipped to
`Status: READY_FOR_TASK_MANAGER`; `docs/architecture.md` § *Phase P23* is activated as written.
Four editorial line-anchor/statement corrections were applied at activation (listed below) —
no architectural decision was made, removed or re-interpreted by this review.

**Phase gate:** open — `docs/code_review/review_log_P22.md` ends `Status: REVIEW_COMPLETE`,
newer than `docs/build/build_log.md`'s last `Status: READY_FOR_REVIEW` (line 7222). This is
therefore a finalizing pass, not a provisional one.

**Stamps:** `pipeline_state.py hash-section --file docs/plan.md --phase P23` and the
`architecture.md` twin both still return `ERROR: no '## Phase P23' section` (the script's
`PHASE_HDR_RE` does not match this repo's `## Phase P23 — …` headings). Re-confirmed this
pass; freshness falls back to the mtime rule (`plan.md` and `architecture.md` are now newer
than every input: `requirements.md` 14:30, this review-cycle start 15:00). Tooling defect, not
a P23 defect.

---

## Retry scope — pass-4 (`retry 2`) Required Changes, item by item

| Item | Verdict | Independent evidence in the tree (re-checked this pass, not accepted from the plan) |
|---|---|---|
| **RC-11** — the whole title-keyed lookup surface scheduled; predicate re-keyed to `objectName` | **ADDRESSED** | Grep of `tests/` returns **22** modules carrying `windowTitle() in ("Portfolio",)`. Six of them are D27 suites P23-01 **deletes** (account_subs, account_scoping, account_partial_window, position_id, position_prices — 5 — plus flat_rows elsewhere), leaving exactly **17** surviving loop modules = the plan's rows 1–15 + rows 16–17. With the three module-constant forms (rows 18–20) that is **20**, and the plan's 20-row table matches file-for-file and line-for-line. `"Portfolio"` appears in **34** test files: 20 lookups + 7 book files that hold it + 7 deletions = 34, so the exit's "cover every file that holds the old identity" holds. All 15 uniform-loop files import `QDockWidget` exactly twice (import + the loop), so "the predicate only" is the correct edit and creates no unused import. Rows 18/19 line anchors verified (`:42`/`:60`, `:309`/`:323`). |
| **RC-11's contested third hard-fail site** | **HOLDS** — my previous count of 19 was wrong | `tests/test_dock_widths_d17.py`: `:40` `_RIGHT_DOCKS = ("Portfolio",)`, `:77` the predicate, and `assert hidden == 1` — this suite hard-fails at P23-01, it is not a silent no-op. Plan's count (three hard-fail: `test_history_backfill_loadpath.py:177`, `test_d42_depth_floor.py:189`, `test_dock_widths_d17.py:83`) is correct. **Correction recorded below.** |
| **RC-12** — `test_dock_d18_region.py` re-anchored incl. `T48-T03` | **ADDRESSED, and the plan's anchors beat my review's** | Tree: `:32` module import; `test_T48_T01` at `:77`; `test_T48_T02` at `:106`; the collapsed-width floor `assert region.width() <= win._right_dock_collapsed_min_width + 2` is at **`:133`, inside `T48-T02`**; `test_T48_T03_panel_present_and_summary_signals_exposed` at **`:154`** through `:181` (`:158` isinstance, `:172-173` the two `hasattr` probes, `:177` the `_receiver_count` call); `_receiver_count` at `:184-194`. Exactly as the plan now states — so **my previous "`:150-172` is the head of T48-T03" anchor was right about T48-T03 but wrong about the floor's anchor**; the plan's version is the accurate one. |
| **RC-13** — five `_record_symbol_price` stubs scheduled | **ADDRESSED** | Tree has exactly five test-side carriers, at the plan's lines: `test_p7_w4_streaming.py:141`, `test_d39_burst_search.py:334`, `test_lwc_popouts.py:129`, `test_p13_fanout.py:104`, `test_p9_alarm_persistence.py:39`. Only caller is `ui/ticker_session.py:562`; `ui/main_window.py:767`/`:3382` hold the sink. Plan's "no other reader" claims verified: `host.prices` only at `:140-141`; `_StubHost.recorded` only at `:332`/`:335`; p9's `_stub_host()` namespace really does become empty. Same-wave deletion means no `AttributeError` window. |
| **Root-cause finds folded in** | **CORRECT** | `tests/test_ui_smoke.py:48` is `assert hasattr(data.models, "Position")` (hard failure the moment P23-06 lands; `:49` `Drawing` untouched). P23-04's fake-client account recorders are real (the window still calls `reqPositions`/`reqAccountSummary` on connect until P23-05) and P23-05 names their removal. |

## Independent sample of the new exit-condition audit table

Two rows picked without reference to what the plan emphasises, verified against the tree:

**P23-05 row (sampled 1).** The eleven-token tree-wide exit is now literally true: `_upsert_position`,
`_positions_rendered`, `_symbol_last_prices`, `set_price_sink` and `_price_sink` occur in **no**
`tests/` file today; `_record_symbol_price` occurs only in the five stubs this wave deletes;
`account_summary` occurs in the four D27 suites P23-01 deletes plus `test_dock_d18_region.py`'s
`T48-T03` probes (P23-01); `position_update` only in the four D27 suites P23-01 deletes plus
`test_d45_removal.py:605,617` (P23-01's walkthrough rework). Production carriers are exactly the
sinks the wave deletes (`ui/main_window.py`, `ui/watchlist_panel.py`, `ui/ticker_session.py`).
The row's verdict is right because every subject it reads is owned in that wave or gone earlier.

**P23-07 row (sampled 2).** `tests/conftest.py:105-124`'s autouse `_isolate_test_db` really does
`DELETE FROM position_group_map/positions/trade_groups` after every test (the "whole suite
errors at teardown" claim is exact, not rhetorical); `EXPECTED_TABLES` at `test_db_schema.py:15-26`
really names all three; block (g) is `:939-1001` over `_PRE_P5_DDL` (`:803`) /
`_write_pre_p5_db` (`:837`); `_ALLOWED_IN_FILE` `:220`, `_allowed_in` **`:271`**, `_EXEMPT_TOKENS`
`:1010`, `_drop_column_subject_nodes` `:1013`, the narrowness test `:1047` — and every
`_EXEMPT_TOKENS`/`_drop_column_subject_nodes` use is inside the region the plan deletes. Readers
of the three tables are the six D27 suites (P23-01) + `test_d45_removal.py` (this wave) +
`conftest.py`/`test_db_schema.py` (this wave) + the `ui/main_window.py` handlers (P23-05): no
surviving suite is left reading a dropped table. Row verdict correct.

*(Also re-sampled, less fully: P23-01's row — the 20/8/7 coverage arithmetic above; P23-02's —
the four account `EWrapper` overrides really are still present at `ibkr/client.py:453-466` and are
P23-06's; P23-06's — `test_account.py`/`test_strategy_detection.py` exist and carry
`build_position_from_ib`/`detect_and_group`/`OptionLeg`, and the exit's emptiness is reachable
once they and `test_d45_removal.py`'s block (d) go in that wave.)*

## The deliberate carve-out (verified narrow)

P23-01's exit and P23-08's re-run exclude the **forbidden-token tables only**:
`tests/test_d45_removal.py`'s `_FORBIDDEN` (`:90`, a tuple of string literals) and `_SURVIVORS`
(`:187`, a frozenset), plus `tests/test_d65_residue.py`'s displaced-token list created in P23-08.
Checked for leakage:

- Those are the only places the retired spellings survive **after** P23-01: the file's live
  uses (`:502`, `:610-613`, `:671`, `:712-719`) are all scheduled in P23-01, and its prose is
  re-pointed with the code.
- At P23-01's own exit the carve-out is not even needed yet (the tables do not spell the exit's
  tokens today); it exists so P23-07's additions cannot make P23-08's re-run redden on itself.
- The carve-out covers literal data structures, never an import, attribute access or assertion
  subject; the plan says so and the tree agrees — `_FORBIDDEN`/`_SURVIVORS` are data, and the
  existing instrument scans **production** source (`_source_files()` over `_SOURCE_DIRS`), so a
  test-side literal cannot legitimise a live use.
- It does not excuse P23-07's `_PRE_P5_DDL` (which spells `positions`/`trade_groups`): none of
  the exit's five greps or three symbols match those strings, and bare `positions` is not in
  `S-P23-15`'s displaced list.

## Validation Method — step results

| Step | Verdict |
|---|---|
| **1 Requirements coverage** | **PASS** — `AC-D65.1`–`AC-D65.13`, Journeys 62–63, A186–A201, R138–R149 and DG117–DG123 each trace to an `S-P23-*` decision and at least one wave; DG122 stays unplanned on the requirements' instruction. `AC-D65.9` measurable end to end (tracked launch value, rebuilt window, 1600×900 legibility, 900×700 elide). No criterion narrowed. |
| **2 Architecture completeness** | **PASS** — stack, components, responsibilities, relationships, data model, integrations, frozen boundaries, non-functional approach (cadence/streaming/threading/16-line accounting), risks `AR-P23-1…15`, each decision with rationale and alternatives. |
| **3 Consistency** | **PASS** — window-step primitive / monotone sweep / shared-leg / 16-line accounting agree across S-P23-5, AP-P23-6/11/12 and *Non-Functional*; no `probe`/`scan_anchor`/`next_step`/`O(log n)` survives as live design. |
| **4 Plan quality** | **PASS** — eight milestone waves, S/M only, ordering forced and justified (panel live before the account path dies; each signal with its only emitter; each test with its subject; token set last). No task-level graph, no per-task test spec. |
| **5 Task Manager readiness** | **PASS** — a valid task graph is derivable without a new architectural decision (see below). |
| **6 Scope integrity** | **PASS** — no scope added or removed; the one behaviour change (D18 launch width) is owner-authorised (`A201`) with exactly two re-baselined sites; `FI-P23-1`/`RG-P23-1` closed. |
| **7 Existing-repo compliance** | **PASS** — Codebase Summary substantive and line-anchored (the `data/db.py` "no upsert/read helper" correction stands); existing stack first, nothing replaced; labels complete; additive-only apart from Q110(a)'s flagged removal; summary consistent with the proposal. |
| **8 Frozen Interfaces** | **PASS** — 14 entries, all `[existing]`, each verbatim and re-verified this pass: `req_mkt_data`/`cancel_mkt_data` (`ibkr/market_data.py:93,112`), `assess` (`md_line_guard.py:20`), `classify_error` (`error_codes.py:10`, returns `'info'`/`'warning'`/`'fatal'`), `IBApiClient.error(self, *args, **kwargs)` (`client.py:269`), `PacingManager.throttle` + `PacingExceeded` (`pacing.py:68,7,15`), `is_trading_day` (`market_calendar.py:149`), `right_dock_max_width`/`plan_dock_widths` + the three constants (`dock_layout.py:21,34,40,56,92`), `DiagonalStrikeButton`/`set_button_active`/`ACTIVE_PROPERTY`, `ContractLookupService.request` (`:101`), `get_index_contract`/`get_contract_for_symbol` (`contracts.py:166,262`), `get_bars` (`ticker_session.py:429`), the three bridge signals (`bridge.py:6-8`). NOT-frozen list covers everything created/changed; no duplicate; every owning module exists. |
| **9 Codebase map** | **PASS** — P23 note matches the material (new modules un-backticked, three deleted modules read as history, `md_line_guard` becoming live), the twenty-lookup selection note lists all twenty by file, the six deleted suites are named, and the `test_d45_removal.py` four-wave split is recorded. No stale or pre-deleted entries; index-sized. |
| **10 Pending doc sync** | **PASS** — `docs/pending_doc_sync.md` absent; the four quick-lane changes are folded into the architecture summary. |

**Inputs:** `requirements.md` § P23 ends `READY_FOR_PLAN`; no open escalation routed to `PLAN`
(106 entries scanned, none open); `plan_notes.md` `RG-P23-1` is `addressed` (A201,
2026-11-17); requirements not modified since the prior review.

## Corrections to my own earlier reviews (recorded, not re-failed against Plan)

1. **Lookup-surface count: 20, not 19.** My retry-2 review missed
   `tests/test_dock_widths_d17.py`, a third hard-fail site. The plan's figure stands.
2. **`test_dock_d18_region.py` anchors.** My retry-2 finding named `:150-172` for the
   collapsed-floor assertion; the floor is `:133` inside `T48-T02`, and `T48-T03` is `:154-181`.
   The revised plan states both correctly.
3. **`test_dock_widths_d17.py:82` → `:83`.** The `assert hidden == 1` statement begins at `:83`
   (`:82` is the preceding comment). Corrected in both documents at activation.

## Editorial corrections applied at activation

No architectural content changed; each is a line-anchor or an arithmetic/wording correction to
evidence text, verified against the tree this pass:

1. `docs/plan.md` lookup table row 20 and the "three hard-fail" paragraph: `:82` → `:83`
   (`test_dock_widths_d17.py`); same in `docs/architecture.md` (three occurrences).
2. `docs/plan.md` P23-07: `_allowed_in` helper `:276` → `:271` (the definition line; `:276` is
   inside its docstring).
3. `docs/plan.md` P23-06 exit: the parenthetical "the two deleted suites are the only carriers"
   replaced with the accurate carrier list for today's tree — `tests/test_account.py` and
   `tests/test_strategy_detection.py` (deleted here), `tests/test_d27_position_id.py` (deleted
   in P23-01), `tests/test_d45_removal.py` (imports + block (d) here). The exit's claim itself is
   unchanged and was already true at P23-06.
4. `docs/architecture.md` Codebase Summary: "**fifteen** test modules assert
   `self.portfolio_panel` — the eight P23-01 edits, `test_d45_removal.py`, and the six D27
   suites" double-counted `test_d45_removal.py` (it is one of the eight) and included
   `test_p13_gate.py`, which references `active_portfolio_panel.py` by filename only.
   Corrected to **fourteen** = the seven P23-01 edits that read the attribute +
   `test_d41_portfolio_dock.py` (deleted) + the six D27 suites.

## Task Manager Readiness

**Ready.** Architecture, data model, integrations, the frozen set, the 16-line budget, the fault
model, the deletion inventory, the per-wave file scope and the four-wave `test_d45_removal.py`
split are all explicit; the exit-condition audit now lets a worker verify each wave's stop rule
instead of re-deriving it. Nothing in the material requires a decision only Plan may make.

**Owner-process note (not a readiness defect):** the phase section records that, after approval,
the Orchestrator produces the human-reviewable implementation plan for the owner instead of
invoking Task Manager (`docs/memory.md`, 2026-11-17). That is the Orchestrator's routing choice;
this review's handoff status is the standard `READY_FOR_TASK_MANAGER`.

## Final Decision

**Status: APPROVED**

- `RC-11`, `RC-12`, `RC-13` verified addressed — revision 3 is a real fix, and two of its claims
  corrected this review's own earlier counts.
- The exit-condition audit was sampled independently at P23-05 and P23-07 (plus P23-01/02/06) and
  is correct; the forbidden-token carve-out is narrow and cannot legitimise live residue.
- No open requirements escalation; no `PLAN`-routed Code Reviewer escalation open.
- `docs/plan.md` § *Phase P23*: `Status: READY_FOR_TASK_MANAGER`.
- No further Plan revision required.
