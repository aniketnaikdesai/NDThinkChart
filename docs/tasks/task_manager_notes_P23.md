# Task Manager notes — Phase P23 (D65 Option Spreads panel)

**Status:** graph written, `check_tasks.py` green (14 tasks), `execution_graph.json` regenerated,
`task-graph.json` meta `status: READY_FOR_BUILD`.
Inputs: `docs/plan.md` § Phase P23 (ends `Status: READY_FOR_TASK_MANAGER`) and
`docs/plan_review_P23.md` (`Status: APPROVED`, no open PLAN/REQUIREMENTS/BUILD/TASK_MANAGER items).

## Wave → task mapping

The plan's ten waves map to fourteen tasks. Only wave **P23-01** exceeded the single-owner step
limit and was split; every other wave is one task, 1:1.

| Plan wave | Tasks | Build wave (by dependency) |
|---|---|---|
| P23-01 | **P23-T1, T2, T3, T4, T5** (split — see below) | waves 1–4 |
| P23-02 | P23-T6 | 2 |
| P23-03 | P23-T7 | 3 |
| P23-04 | P23-T8 | 4 |
| P23-05 | P23-T9 | 5 |
| P23-06 | P23-T10 | 6 |
| P23-07 | P23-T11 | 7 |
| P23-08 | P23-T12 | 8 |
| P23-09 | P23-T13 | 9 |
| P23-10 | P23-T14 | 10 |

Sizes: thirteen **M**, two **S** (P23-T11, P23-T14). **No task is L.**

## Why P23-01 is five tasks (the only wave over the step-fit limit)

Wave P23-01 carries two new modules, two new suites, one production swap, **eight** edited book
suites, **twenty** re-keyed dock-lookup modules, **seven** deletions and two re-baselines — an
honest action count well past the ~32 ceiling, so it cannot be one worker's task. It is split by
**member group** (never by file), and all five tasks stay inside the same wave boundary the plan
defines:

- **P23-T1 — ladder math module.** `services/option_ladder.py` + `tests/test_d65_option_ladder.py`.
  Pure, no Qt, no tree reads beyond conventions; the module P23-T2/T7/T9 consume.
- **P23-T2 — the panel widget.** `ui/option_spreads_panel.py` + the shell / Target-gate / toggle /
  elide / collapse groups of `tests/test_d65_option_panel.py`. Constructed standalone offscreen, so
  it needs no dock.
- **P23-T3 — the swap itself.** `ui/main_window.py` (dock block, rename, the ten deleted
  `ActivePortfolioPanel` call sites, three probe re-points with their docstrings, the launch-width
  request), the module + `test_d41_portfolio_dock.py` + six D27 suites deleted, the four
  panel-identity suites repaired, and the `AC-D65.9` launch/wide/narrow group appended to
  `tests/test_d65_option_panel.py`.
- **P23-T4 — the dock-lookup surface** (twenty modules). The plan forbids separating this from the
  rename *by wave*; the split keeps it in the same P23-01 wave and the dependency edge is a
  determinism choice, not a wave boundary: three of the twenty (the sentinels) hard-fail the moment
  the rename lands, so running this task before P23-T3 would be a race, while after it the edits are
  mechanical and its own greps are literally true when it fires.
- **P23-T5 — the width/probe/walkthrough surface.** The two owner-authorised A201 re-baselines, the
  D18 and D18-impl wide-content rebuilds, the D21.13/D22 probe and the `test_d45_removal.py`
  walkthrough rework. It depends on P23-T3 and runs parallel to P23-T4 (disjoint files).

Net effect: four build waves for wave P23-01 instead of one 60-step task, with no acceptance
criterion moved to a task that does not own its subject, and no file written by two tasks without a
dependency edge between them.

## Decisions recorded

1. **`LegKey` / `SpreadRow` live in `services/option_ladder.py`.** The plan's P23-02 dependency line
   says so ("the ladder module's `LegKey`/`SpreadRow` shapes"), while the architecture's Data Model
   bullet only names `SpreadRow` as ladder-built; P23-T1 owns both, so P23-T6/T7/T9 consume them by
   contract instead of re-deriving a shape.
2. **Pack read_files may not cite a file that does not exist yet.** `check_tasks.py` resolves every
   `read_files` path and `existing` contract ref at graph time, so the surfaces that P23-T1/T2/T7
   create and later tasks consume are carried as **`new` contracts with verbatim signatures**
   (P23-T3/T5/T7/T8/T9) rather than as forward references. A worker still reads the live file from
   its `touches_files`; the contract states the exact surface so it cannot be second-guessed.
3. **The user-doc carrier is `usage.md`, not `USAGE.txt`.** Plan P23-09 says the doc check is over
   `USAGE.txt`/`docs/README` and predicts "the right dock only as chrome". Verified: `USAGE.txt`
   says nothing about the dock, and **`usage.md:128` and `usage.md:189-196`** advertise the Portfolio
   dock ("account summary, positions and P&L") and the strategy auto-detection
   ("PCS, PDS, CCS, CDS, IC") that P23 deletes. P23-T13 owns that correction and is the graph's only
   `doc_required: true` task — this is P23-09's own "correct only if it claims a Portfolio view"
   authority applied to the file that actually makes the claim, not new scope.
4. **P23-T14 records the checklist and claims nothing.** Per the owner's instruction, the paper-TWS
   record is created with all six items **pending** and evidence fields empty; the task's acceptance
   is the record's structure and the canonical numbers, and P23-T13's gate record must state
   `AC-D65.19` open. No build task asserts `AC-D65.19` satisfied.
5. **P23-T12's token list excludes the three table names** (they are spelled by the migration and the
   absence assertions), and **P23-T10's exit excludes the four broker-boundary tokens** (P23-T11
   owns them) and the `data/db.py` comment (P23-T12 owns it) — each task's sweep is true when it
   fires, per the plan's exit-condition audit.

## Owner-decided facts encoded verbatim in the packs

No orders anywhere (D45/D46) and option data display-only; the unused-code rule with the residue
gate in P23-T13; **≤16 option lines + at most one spot line = 17** asserted in every relevant AC;
`ASK = long.ask − short.bid`, `BID = long.bid − short.ask`, `Δ/Γ = long − short` with credit spreads
negative by design; `h = max(0.05, one_tick)` with `option_tick` 0.05 below 3.00 and 0.10 at/above;
Target gate `0.05 ≤ T ≤ 19.95`; the spot chain **3a** chart SPX last price → **3b** exactly one
dedicated spot line → **3c** none; the **`OPTION_LEGS`** registration tag (never `MARKET_DATA`);
ON never survives a restart (launch OFF, Target 1.00); pre-drop SQLite backup with abort-on-failure
and the owner-confirmed drop of `positions`/`trade_groups`/`position_group_map`; the fixture
convention (width 20, `short/long`, CCS short below long, PCS short above, canonical `7425/7445`
and `7340/7320`, `7425/7435` and `7315/7435` rejected, `7435/7455` legal).

## Escalations

**None.** No undecided architectural choice was needed for any task: the three conflicts this phase
raised (FI-P23-1/-2/-3) were resolved in the canonical artifacts on 2026-11-17, and `S-P23-24`
decides the one consequence the review surfaced (the connection badge). No `ESC-PLAN-*` entry, and
no requirements-ambiguity flag was appended to `docs/requirements/open_questions.md`.

## Correction — 2026-11-17: P23-T3-AC4 re-stated to match D18's cross-clamp

**Source:** P23-T3's worker, verified by measurement (not a Code Reviewer escalation). No
`ESC-PLAN-*`; no architectural decision was involved — the canonical D18 clamp was always the
truth, the AC's arithmetic was not.

**Defect.** AC4 asserted that at a 900x700 window the 40 % cap yields a 272 px dock with an ~84 px
name column. That combination is unreachable. 272 = 0.40 x 680 assumed a 680 px chart area
(680 = 900 − 220), which ignores the right dock's own width: the settled window is left 150 /
right 200 / chart area 550, where `right_dock_max_width(550)` itself returns 200 (550 − 400 = 150
binds below the 220 cap) and `plan_dock_widths` returns the infeasible `(150, 200)`. Measured at
900x700: dock 200 px, name column 31 px. The AC's *intent* — the cap/cross-clamp wins, names elide
with real margin, tooltip intact — was satisfied; only its numbers were wrong. An AC that pins an
unreachable literal is a task-breakdown defect, so it was amended rather than re-baselined.

**Amendment to P23-T3-AC4 (and P23-T3-AC4's test).** Two claims, both true and both proving the
intent:

1. the cap's own contract as a pure unit fact — `right_dock_max_width(680) == 272` (40 % of 680;
   680 − CHART_MIN_WIDTH = 280 is not binding);
2. the real-window result at 900x700 — the cross-clamp settles left 150 / right 200 with a 550 px
   chart area, so the dock is exactly 200 px (160 px under the preferred 360 px width), the name
   column is at most two-thirds of the wide-fixture/360 px-layout column width, and the elide +
   tooltip path is taken (elided text != full name, full name in the tooltip).

The wide-fixture half of AC4 (dock ≥ 340 px, no name's text width over its column width) is
unchanged. The test description carries the required one-line code comment naming why the literal
272-at-900x700 is unreachable. No other acceptance criterion, test, dependency, `touches_files`, or
task was changed: **no D18 assertion was re-baselined** (owner authorisation covers only the two
sites in P23-T5, untouched here).

**Knock-on, pack-hygiene only.** `check_tasks.py` then failed on a pre-existing graph/repo drift:
P23-T2's context pack still listed `ui/active_portfolio_panel.py` as a read-only entry, but P23-T3's
worker has already deleted that file (verified: the path does not exist). The entry can never be
read again, so it was removed from P23-T2's `read_files` (4 → 3). P23-T2's ACs, tests, dependencies
and `touches_files` are untouched; it is `done` and the remaining three entries still carry the
sizing/toggle/test conventions.

**Verification.** `check_tasks.py`: `OK: 14 tasks validated, execution_graph.json written` (warnings
only: the usual "pure-output file" pack notes). Metadata left at `"status": "READY_FOR_BUILD"`.

## Correction — 2026-11-17 (rework): P23-T10's footprint omitted `tests/test_d65_option_panel.py`

**Source:** P23-T10 blocked after wave 6 for a footprint omission, not a work defect. No `ESC-PLAN-*`
and no Code Reviewer escalation entry: the work T10 did is correct, its `touches_files` under-declared.

**Why the file belongs to this wave.** `tests/test_d65_option_panel.py` carries the P23-T3-AC2 block
(`# P23-T3-AC2 — the rename, and the handlers that survive it`). That block asserted the very
account/position handlers wave 6 deletes and spelled tokens AC-D65.13 forbids tree-wide
(`_live_accounts`, `_positions_rendered`). Left untouched, it fails twice over: the block's own handler
assertions go red once T10's deletions land, and the tree-wide token sweep in T10-AC1 stays red because
a forbidden name survives in `tests/`. So the edit is required by T10's own AC1 and AC4 ("the test
book"), and the file must be listed in the task that is required to edit it. Verified after the edit:
the ten window-side tokens now appear in no source file under `ui/`, `ibkr/`, `services/`, `data/` or
`tests/` (only stale `tests/__pycache__/*.pyc` bytecode still carries two of them, which is not source).

**Change, P23-T10 only.** `tests/test_d65_option_panel.py` added to `touches_files` (11 → 12) and to
`context.read_files` with the range `386-414` and the why "the P23-T3-AC2 block, which must stop naming
the handlers this wave deletes and stop spelling the AC-D65.13 tokens" (9 → 10 entries, 6 distinct
files — the pack budget is counted in files, so the addition keeps it inside ~8). `status` reset
`blocked` → `not_started` so the corrected result can consolidate and re-run. **No other change:** no
acceptance criterion, test, dependency, `expected_artifacts`, `doc_required`, other task, or scope item
was touched; no dependency edge was added or removed, so the task order is identical. `check_tasks.py`
was re-run anyway, so `execution_graph.json` (and its `graph_struct_sha256`) reflects the current graph.

**Dependency point raised by the worker — checked, nothing wrong.** P23-T11..T14 are `not_started`
because they sit behind T10 on a genuine logical chain, not because of a stale or circular edge:
T11 ← T10 (T10-AC1 asserts `account_summary` / `account_summary_end` / `position_update` /
`position_end` still survive in `ibkr/` — T11 is the wave that deletes them, so T11 must not run before
T10's sweep is satisfied; the two also share `tests/test_d45_removal.py`), T12 ← T11, T13 ←
(T1..T12, the residue gate needs T10's removals in place), T14 ← T13. No cycle, and no task waits on a
task that will not re-run: with T10 reset to `not_started` and no unmet dependencies of its own, T10 is
eligible on the next frontier, and each later task becomes eligible as its predecessor lands. This is
the intended "simply wait for it" shape, so the graph was left as-is.

**Verification.** `check_tasks.py`: `OK: 14 tasks validated, execution_graph.json written` (warnings
only — the usual "pure-output file" pack notes, unchanged in kind). Metadata left at
`"status": "READY_FOR_BUILD"`.

## Correction — 2026-11-17 (rework): P23-T13's footprint gains `services/option_ladder.py` for one residue line

**Source:** P23-T13's own residue gate, run against the finished tree, reported real P23 residue that
no earlier task's footprint covered: `services/option_ladder.py:52` still imports
`from datetime import date, datetime` and uses neither name. Verified: the only occurrences of the two
words elsewhere in the file are literal prose — the docstring at line 176 ("``Nov17`` from a
date/datetime …") and the `TypeError` f-string at line 183 ("expected a date/datetime or a string") —
so the import binds two names that are never referenced. `services/option_ladder.py` was written by
P23-T1, whose `touches_files` is exactly that module plus its suite, but T1 is `done` and cannot be
re-opened for a one-line cleanup, and the gate must not be narrowed to excuse the line it found.

**Change, P23-T13 only.** `services/option_ladder.py` added to `touches_files` (2 → 3) and to
`context.read_files` as the first entry, range `50-54`, why "edit: delete the one unused import … —
that single line is the whole change, leave the rest of the module untouched" (5 → 6 distinct files,
inside the ~8-file pack budget). This addition exists **solely** to let the wave delete that one import
line; it adds no scope to T13 and licenses no other edit to the module. The gate proved itself by
finding it — narrowing the gate (e.g. skipping `services/` or allowlisting the file) was rejected: the
whole point of AC1's "green on the real tree" clause is that the tree actually satisfies it.

**No other change.** No acceptance criterion, test, `expected_artifacts`, `doc_required`, dependency
edge, `status` (`in_progress`, unchanged — the task is mid-wave), or other task was touched; the
dependency order is identical. `check_tasks.py` re-run so `execution_graph.json` and its
`graph_struct_sha256` reflect the current graph.

**Verification.** `check_tasks.py`: `OK: 14 tasks validated, execution_graph.json written` (warnings
only — the usual "pure-output file" pack notes, unchanged in kind). Metadata left at
`"status": "READY_FOR_BUILD"`.

## ESC-116 — the two stale D65 option-chain contracts now have a phase-final owner

**Source:** `docs/code_review/escalations.json` ESC-116 (blocking, `routed_to: TASK_MANAGER`,
`task_id: P23-T6`). Full-suite verification (`docs/code_review/test_verification.json`, verdict fail,
exit 1) reddens exactly two cases in `tests/test_d65_option_chain.py`, and the reviewer's adjudication is
accepted as given — no re-diagnosis here: both are stale *wave-scoped* contracts, not regressions.
`test_no_production_caller_outside_ibkr` exempts only `ibkr/` in its sweep, so P23-T9's designed live
wiring in `ui/main_window.py` (7 hits: imports 37-41, the three signal connects 929-931, and the call
sites at 2153, 2180-2181, 2284, 2310) reads as an offender; `test_account_and_position_overrides_and_signals_remain`
asserts the presence of the four EWrapper overrides and four bridge signals that P23-T11-AC1 deleted by
owner decision. Root cause, accepted: P23-T6-AC5 was worded "Given this wave … yet / still present", true
at T6's wave and false at phase end, and no task owned the phase-final form — P23-T13's "full suite
green" AC has no footprint over that file and its gate record honestly deferred the two cases to "that
contract's owner".

**Changes — three, all in `docs/tasks/task-graph.json`.**

1. **P23-T6-AC5 is now explicitly the interim snapshot.** The AC (and its test's
   `linked_acceptance_criterion`, description and `expected_result`) states that it holds *at T6's wave
   only* and names P23-T15-AC1/AC2 as the phase-final owners of the polarity. No other T6 field changed:
   `touches_files`, `tests`, `status` (`done`) and its context pack (whose `ibkr/client.py` entry already
   said "this wave must leave present") are untouched. T6 was **not** reset: re-running it would re-do four
   production modules for a test-only re-point, and it is the dependency edge under T7/T9/T13.
2. **P23-T13-AC3 now names what it cannot reach.** "the full offscreen suite is green" becomes "green
   apart from exactly the two ESC-116 cases …, which are red at this wave only because no task in this
   phase can reach that file — P23-T15 owns and re-points them, and the gate record names those two cases
   and their owning task instead of claiming a green suite, while any other red case fails this AC". The
   AC's other clauses (marker grep, section presence, the three owner-authorised edits, S-P23-24,
   bookkeeping, AC-D65.19 open) are byte-intact. This closes the "gate that cannot see the file" hole
   without weakening the gate: any *other* red case still fails.
3. **New task P23-T15 — the BUILD rework, `status: not_started`.** "Re-point the D65 option-chain
   contract suite to the phase-final invariants (ESC-116)", `build_worker`, `size: M`, deps
   `[P23-T6, P23-T9, P23-T13]`, `touches_files` `[tests/test_d65_option_chain.py,
   tests/test_d65_residue.py]`, three ACs each with one test:
   - **AC1** — the caller sweep admits exactly two kinds of hit: modules under `ibkr/`, and the *named*
     designed P23-T9 wiring in `ui/main_window.py`. The AC is invariant-shaped and stays discriminating:
     a seeded offender in a temporary non-`ibkr`, non-`main_window` tree must still be reported, so the
     assertion cannot be satisfied by deleting or emptying the sweep.
   - **AC2** — the four overrides (`accountSummary`, `accountSummaryEnd`, `position`, `positionEnd`) and
     the four signals (`account_summary`, `account_summary_end`, `position_update`, `position_end`) are
     **absent** (`getattr(...) is None` / `hasattr(...) is False`), matching P23-T11-AC1 and
     `tests/test_ui_smoke.py`'s established absence block; no presence assertion survives in the suite.
   - **AC3** — the suite's docstring AC5 bullet states the phase-final invariants (no "yet"/"still
     present" wording, no "P23-T11 deletes them" future tense) and the `TOKEN_CARVE_OUT` entry for the
     file is dropped or re-justified against what the file now contains, with the residue suite's
     `carve-out-entries-spell-a-token` check green either way (that check forbids dropping the entry while
     the file still spells a token, which absence assertions do — hence "dropped *or* corrected").
   Pack: 8 `read_files` entries over 4 distinct files (the two suites, the three admitted
   `ui/main_window.py` slices, `tests/test_ui_smoke.py` read-only), 3 existing `contracts` refs, test
   command `… pytest tests/test_d65_option_chain.py tests/test_d65_residue.py -q`. Nothing in the pack
   contradicts the ACs: the `read_files` whys mark every `ui/main_window.py` slice read-only, and each
   stated guarantee names its enforcing test (AC1 → `P23-T15-AC1`'s seeded offender; AC2 → `P23-T15-AC2`;
   AC3 → `P23-T15-AC3` plus the residue suite's own check).

**ESC-117 / ESC-118 — cascade only, no substance here.** Both stay open and BUILD-routed to their own
tasks; their diagnosis, footprints and suggested fixes are untouched by this pass. This pass only had to
leave them *dispatchable*: P23-T9 (ESC-117) and P23-T13 (ESC-118) both remain `done` in the graph with
every one of their own dependencies `done`, so neither was reset or newly gated, and no dependency of
either points at `P23-T15`. P23-T15 sits *after* both (`P23-T15 ← P23-T9`, `P23-T15 ← P23-T13`), so the
two reworks land first and the contract suite is re-pointed against their finished state — including
against `tests/test_d65_residue.py` as ESC-118's rework leaves it.

**Verification.** `check_tasks.py`: `OK: 15 tasks validated, execution_graph.json written` (warnings are
the pre-existing "pure-output file" pack notes; P23-T15 raises none — all three of its `touches_files`
appear in its pack). Metadata left at `"status": "READY_FOR_BUILD"`.

## Footprint fix — P23-T13 / ESC-118 (post-rework consolidation)

ESC-118's rework deleted `OptionSpreadEngine = SpreadEngine` from
`services/option_spread_engine.py`, but that file was not in P23-T13's `touches_files`, so the worker's
self-check stamp reported `tests: pass, footprint_ok: false` and the result consolidated as `blocked` —
the edit is correct, only its declared footprint was short. Two-line graph fix, no AC/test/dependency
change:

- `touches_files` += `services/option_spread_engine.py` (the alias's deletion site; `SpreadEngine` itself
  is untouched at line 278). The file was already deleted from the tree at this point — this makes the
  footprint true, it does not widen scope: `tests/test_d65_residue.py` (allowlist entry +
  `test_census_allowlist_cites_a_live_site` tightening) and `usage.md` remain the task's other writes.
- `context.read_files` += `services/option_spread_engine.py` lines `1600-1633`, `why` naming the deleted
  alias and stating it is the only change in that file — so the write is pack-backed and the worker is
  told not to reintroduce the alias. Pack now 7 entries (budget ~8), no entry dropped.
- `status`: `blocked` → `not_started`, so the corrected result can consolidate on re-run.

**Dependency verdict (P23-T15 / ESC-116).** `P23-T15 ← {P23-T6 done, P23-T9 done, P23-T13 not_started}`.
T13's own dependencies `P23-T1..P23-T12` are all `done`, so T13 is the current frontier (dispatchable
now) and T15 becomes dispatchable the moment T13 re-consolidates as `done`. No cycle: T13's transitive
ancestors (13 nodes) never reach T15, and T15 is downstream of T13 by construction, so the wave order is
T13 → T15 with no deadlock and no new edge needed. T14 is already `done` despite depending on T13 (it
consolidated before the ESC-118 rework re-blocked T13); it gates nothing and is left as-is.

**Verification.** `check_tasks.py`: `OK: 15 tasks validated, execution_graph.json written` (exit 0,
`graph_struct_sha256` regenerated); the only P23-T13 warning is the pre-existing "pure-output file" note
for the new `tests/test_d65_residue.py`. Metadata left at `"status": "READY_FOR_BUILD"`.

## ESC-119 — engine-owned session reset, live `toggle_off()`, no constructor re-entry

**Source:** `docs/code_review/escalations.json` ESC-119 (should-fix, `routed_to: TASK_MANAGER`,
`task_id: P23-T9`). Diagnosis accepted as given — ESC-117's rework reset the engine from
`ui/main_window.py::_option_reset_engine` by re-running `SpreadEngine.__init__`, which orphaned
`SpreadEngine.toggle_off()` (zero tree-wide callers) and would silently drop the `clock=` seam on
re-entry. The root cause the escalation names is a breakdown omission, not a build defect:
`services/option_spread_engine.py` was never in the owning task's `touches_files`, so the engine half
of the reset had no home and the worker reached through the constructor. Owner-approved direction
("yes" and "fix it", 2026-11-18): `reset_session()` on the engine, `toggle_off()` delegating to it,
and the UI calling those instead of re-initialising.

**Scoping decision — a new task, not a T9 footprint patch.** The fix is production work in two
modules, and `P23-T9` is `done` and is the dependency edge under T10–T15; resetting it would re-run
an M task (chain discovery, registry replay, spot tiers, cadence) to add ~20 lines, and would make its
record claim writes it never made. So the owning task is **new `P23-T16`**, whose `touches_files`
**does** include `services/option_spread_engine.py` — that is the escalation's footprint point
resolved at the task that owns the fix, not retro-fitted onto a task whose work is finished and whose
rework already landed. `P23-T9` itself is unchanged (status stays `done`).

**New task `P23-T16` — "Engine-owned session reset … (ESC-119)", `build_worker`, `size: M`,
`status: not_started`, deps `[P23-T9]`.** Three ACs, one test each; `touches_files`
`[services/option_spread_engine.py, ui/main_window.py, tests/test_d65_spread_engine.py,
tests/test_d65_option_stream.py]`.

- **AC1 — `reset_session()` is the single owner of a session clear.** Built as
  `SpreadEngine(clock=<injected>, target=<t>)` and driven through a full session (ON, chain, quotes,
  spot, greeks, leased/subscribed legs, reqIds, window and both anchors, a seed, a latched message, a
  dropped pair, a stale leg, a frozen walk with a pending re-seat), every field `__init__` initialises
  is back at its `__init__` value **except the injected clock and the Target**; `_now()` still reads
  the same clock and `target` is unchanged (so the reset performs no `set_target` invalidation). Test
  `P23-T16-AC1` (unit, `tests/test_d65_spread_engine.py`) asserts that state set plus the clock/Target
  preservation via the suite's existing `Clock` helper.
- **AC2 — `toggle_off()` stays live and delegates.** It produces exactly AC1's clean state (not the
  old two-flag stub), `ui/main_window.py`'s OFF path calls it, `_option_reset_engine` is gone, no
  production module calls `SpreadEngine.__init__` on an existing engine, and the class docstring's
  public-API list names both `toggle_off()` and `reset_session()`. Test `P23-T16-AC2` (unit) asserts
  the identical clean state from `toggle_off()` **and** the discriminating source shape — this is the
  mechanical form of the escalation's "no dead symbol, methods included": a re-orphaned `toggle_off()`
  or a reintroduced `.__init__` reach-through fails it.
- **AC3 — OFF and cutoff are the same clean engine, with no re-`__init__`.** On a live window with 16
  streamed legs and a non-default Target, `_option_stop()` empties the session through `toggle_off()`
  and `_option_enter_cutoff()` through `reset_session()`, keeping the same engine instance, the Target
  and the injected clock object, with `SpreadEngine.__init__` executing zero further times
  (counter installed after the window is built). Test `P23-T16-AC3` (integration,
  `tests/test_d65_option_stream.py`) drives the real toggle and the real cutoff.
- **Pack** (7 `read_files` entries over 4 distinct files): the engine's `__init__` field list +
  lifecycle (`278-400`), its docstring public-API list (`76-92`), the UI edit sites (`2055-2140`), the
  engine's construction site read-only (`885-900`, showing `SpreadEngine()` takes no clock so the seam
  is on the instance), the `Clock`/`seed_engine` conventions (`40-150`), and the two stream-test
  groups this task extends or must keep green (`493-600`, `920-985`). Five contracts: three `new`
  (`reset_session(self) -> None`; `toggle_off(self) -> None  # body: self.reset_session()`;
  the two UI call shapes) and two `existing` refs (`_option_stop`, `_option_enter_cutoff`). No pack
  prose contradicts an AC: the reset's preservation rule is stated once in AC1 and restated as the
  pack's `why` for `278-400`, and each guarantee names its enforcing test (AC1 → `P23-T16-AC1`,
  AC2 → `P23-T16-AC2`, AC3 → `P23-T16-AC3`).
- `doc_required: false` — the OFF/cutoff states the user sees are unchanged; this removes a
  constructor reach-through and gives the reset an owner, it does not alter documented behaviour.
  `architecture.md:9462` already lists `toggle_on()`/`toggle_off()`; adding `reset_session()` does not
  contradict it (it is a public-surface list, not a closed set) and no Plan-owned doc is edited here.

**Dependency verdict.** `P23-T16 ← P23-T9` (its edit sites, and the OFF/cutoff wiring whose reset it
replaces). It needs no edge to T7/T8 (`SpreadEngine`'s session fields) because T9 already depends on
both, and none to T13 (the residue gate enumerates module-level symbols only, so a live method is
invisible to it) or T15 (disjoint files, no shared contract). No cycle: T16 is a leaf.

## ESC-120 — `P23-T15-AC2` restated as the discriminating predicate

**Source:** `docs/code_review/escalations.json` ESC-120 (nice-to-have, `routed_to: TASK_MANAGER`,
`task_id: P23-T15`). `IBApiClient(EWrapper, EClient)` inherits `EWrapper`'s base stubs, so the AC's
`getattr(IBApiClient, name, None) is None` is unsatisfiable for the four deleted overrides — a green
tree cannot satisfy its own AC. Owner-approved: assert the class does not **override** them.

**Change, `P23-T15` only — AC2 wording (and the matching test's `linked_acceptance_criterion`,
`description` and `expected_result`).** AC2 now states: `name not in vars(IBApiClient)` and
`getattr(IBApiClient, name) is getattr(EWrapper, name)` for each of the four callbacks (the attribute
resolves only because `IBApiClient` inherits the base stub), `hasattr(IBBridge, signal_name) is False`
for each of the four signals, and the AC says in words that the `getattr(..., None) is None` form is
unsatisfiable here and is not used. Intent unchanged: "the app no longer supplies these callbacks".

**No re-dispatch, no status change.** `P23-T15` stays `done`: the delivered case
(`tests/test_d65_option_chain.py:595-607`, verified on the live tree) already asserts exactly this
discriminating form — `name not in vars(IBApiClient)`, identity with the `EWrapper` stub, and the
absent signals — so the tree needs no edit and the AC is being brought to what the test enforces, not
the other way round. No other T15 field changed (`touches_files`, `expected_artifacts`, contracts,
dependencies, `status` all untouched).

**Carry-forward note for future packs.** Do not phrase an "is absent" predicate as
`getattr(cls, name, None) is None` for any `EWrapper`/`EClient` callback: ibapi's base stubs make it
unsatisfiable. The discriminating form is "not in `vars(cls)` and identical to the base stub".

**Verification.** `check_tasks.py`: `OK: 16 tasks validated, execution_graph.json written` (exit 0;
warnings are only the pre-existing "pure-output file" pack notes — `P23-T16` raises none, as all four
of its `touches_files` appear in its pack). `graph_struct_sha256` regenerated. Metadata left at
`"status": "READY_FOR_BUILD"`; `P23-T16` is the only `not_started` task, so it is the next frontier.

## ESC-119 (second half) — the gate's clause (i) census extended to class methods

**Source:** `docs/code_review/escalations.json` ESC-119 (`should-fix`, `routed_to: TASK_MANAGER`,
`task_id: P23-T9`, `status: open`). The code half is closed: `P23-T16` landed
`SpreadEngine.reset_session()` + a live `toggle_off()` (both `done`, verified by the reviewer/`P23-T16`
result), so `toggle_off` is no longer orphaned. What remained is the enforcement gap ESC-119 named —
`tests/test_d65_residue.py` clause (i) enumerates **module-level** public names only
(`_defined_symbols` walks `ast.parse(text).body`), while `AC-D65.12(i)` requires "every module, class,
function, **method** …". A dead method passes the standing gate, which is the exact defect class
ESC-119 was raised for, and the suite docstring still claims "every P23 symbol".

**Owner decision (2026-11-18, verbatim):** "Extend the gate to class methods". Direction taken as
given: extend, never narrow `AC-D65.12`; the gate must carry clause-(v) exemptions for
framework-invoked callbacks (Qt slots/handlers, `EWrapper`/`EClient` overrides) cited at their
registration/override site (never a task-graph string); a seeded dead-method fixture must prove the
clause reddens; the docstring scope claim gets corrected; and a genuine dead method found by the
extended census is deleted, never allowlisted.

**Scoping decision — one new task, test-only.** The whole deliverable lives in
`tests/test_d65_residue.py` (the same file `P23-T13` authored and `P23-T15` re-pointed, both `done`):
the candidate builder, the reachability scanner, the exemption machinery and its docstrings are one
instrument, so splitting them would create two owners of one scanner. **New `P23-T17`**, `size: M`,
`status: not_started`, `task_type: test`, deps `[P23-T13, P23-T16]`, `touches_files`
`[tests/test_d65_residue.py]`, `doc_required: false`.

**No production file is in the footprint — verified, not assumed.** Before scoping I ran the extended
census over the tree with the very semantics the task specifies (all methods, public **and**
single-underscore, of every class in the four P23 new modules and of every class named in
`P23_ADDED_SYMBOLS`, reachability = load/attribute/string-constant/import mention in any scanned file
or any use beyond the definition in its own module): **zero dead methods**. `OptionSeries` is a plain
dataclass with no methods; `db_backup.VerifiedBackupPath` has only `__new__` (a dunder). So this run
expects no production edit; the task's description says a violation reported by the *implemented*
census means the scan is broader than `P23-T17-AC1` (fix the scan) or the tree changed since this
scoping (report, do not allowlist). If a later run does find one, the owning module joins
`touches_files` in that run and the method is **deleted**, per the owner's rule.

**Census scope decisions encoded in the ACs.**

1. **Dunders are the single exclusion** (names that both begin and end with `__`): Python/Qt machinery
   invokes them implicitly (`__new__`, `__init__`, `__eq__`), and exempting them by name shape is
   cheaper and more honest than a citation table for the data model. Single-underscore methods **are**
   censused — that is stricter than the module-level rule (which skips leading-underscore names, left
   untouched here), and it is what makes ESC-119's shape catchable: `toggle_off` had zero callers
   tree-wide, and an internal helper with zero callers is dead by the same rule.
2. **Keys are qualified**, `Module:Class.method` — a method name cannot be satisfied by a module-level
   symbol of the same spelling, and the violation string names the class.
3. **Reachability is the evidence the gate already accepts**, carried onto methods: load/attribute
   access in any scanned file, a use beyond the definition inside its own module (`self.x(...)`),
   a string constant equal to the name (`getattr(obj, "x")`, a name-keyed registry — added for the
   own-module direction, where today's scanner only reads loads), an import alias, and
   `.connect(...)`/registration sites. No new discovery machinery: `_load_names`/`_mention_names`
   stay the evidence.
4. **Clause (v) carried onto methods, scoped harder than today.** A framework-invoked method is exempt
   only through an entry naming the declaring class **and** the base class whose attribute registers
   the name, with the check verifying that base really declares it — so `sizeHint` on the delegate is
   exempt while the same name on a class with no such base is still censused. A document/task-graph
   string satisfies neither the base-class check nor the `citation_violation` cited-site form
   (`_REGISTRATION_RE` requires a `.py` path + line), keeping ESC-118's evidence rule intact.
5. **Nothing is weakened.** `P23-T17-AC1` states that clauses (ii)–(v), the seeded dead-symbol and
   unconnected-signal fixtures and the token/batch half keep their current strictness, with no
   assertion deleted or relaxed; the three pre-existing fixture cases are named as staying in place
   unmodified, and their test's `expected_result` says so in hygiene terms (no invented RED→GREEN).

**Why the dependency edges.** `P23-T17 ← P23-T13` (it edits the gate `P23-T13` authored — the
scanner, the citation checker and the clause-(v) tables) and `P23-T17 ← P23-T16` (its discriminating
assertions name the post-ESC-119 engine surface — `SpreadEngine.toggle_off` and `reset_session` — and
the census must be green on the state `P23-T16` leaves; before T16, `toggle_off` really was dead and
this task's green AC would be unsatisfiable). No edge to `P23-T15` (it re-pointed this file earlier
and is `done`; nothing it wrote is a contract this task consumes — including it would only remove
parallelism, which is moot now that it is complete). No edge to `P23-T3`/`T9` (file-disjoint from this
task, and their subjects are stable). `P23-T17` is a leaf.

**Size justification — `M`, ~18 steps.** Two scanners touched (`_defined_symbols` gains the method
walk; `_census_candidates` gains qualified keys), one exemption path (table + base check) reused from
clause (v), four new tests (candidate map, dead-method fixture + mutation, exemption fixture trio,
docstring scope) and the docstring correction — comfortably inside the ~20-step target, and one file,
so no split. Not `S`: the exemption scoping is a real design decision, not a mechanical edit.

**Pack.** 7 `read_files` entries over **one** file (the budget counts files), each with a range and a
`why` marking edit vs read-only; 5 contracts — two `new` (the `Class.method` candidate-key format and
the method exemption entry form, i.e. exactly what the tests assert) and three `existing` refs
(`scan_unreferenced_symbols`, `citation_violation`, `_defined_symbols`). No pack prose contradicts an
AC: the exclusion rule appears once (`AC1`) and is restated only as the docstring deliverable (`AC4`),
and each guarantee names its enforcing test (AC1 → `P23-T17-AC1`, AC2 → `P23-T17-AC2`, AC3 →
`P23-T17-AC3`, AC4 → `P23-T17-AC4`). `test_command` is the suite's own:
`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d65_residue.py -q`.

**Not done here.** `docs/code_review/escalations.json` is Code Reviewer's file — ESC-119 stays `open`
for the Reviewer's verification pass after this rework lands; this run did not edit it, nor
`requirements.md`, `plan.md` or `architecture.md` (`AC-D65.12` already requires methods; `S-P23-15`
already says "every symbol added by P23", so neither needed a change and neither is mine to make).

**Verification.** `check_tasks.py`: `OK: 17 tasks validated, execution_graph.json written` (exit 0;
warnings are only the pre-existing "pure-output file" pack notes — `P23-T17` raises none, as its one
`touches_files` entry is in its pack). `graph_struct_sha256` regenerated. Metadata left at
`"status": "READY_FOR_BUILD"`; `P23-T17` is the only `not_started` task, so it is the next frontier.

## ESC-121 + ESC-122 — production-only, class-bound residue evidence, and the dead members it exposes (owner-approved rework, 2026-11-18)

**Source:** `docs/code_review/escalations.json` ESC-121 (should-fix, `routed_to: TASK_MANAGER`,
`task_id: P23-T17`) and ESC-122 (nice-to-have, `routed_to: BUILD`, `task_id: P23-T17`). Owner
instruction: "fix everything". The reviewer's diagnosis is accepted as given; the 15-symbol list was
**re-verified against the tree**, not copied.

**What was measured here (not assumed).** Every clause-(i) candidate in the four P23 new modules and
every P23-added class was checked against the production tree (`ui/`, `services/`, `data/`, `ibkr/`,
`config/`, `main.py`) for an attribute access, a name load, an import alias and own-module use. The
current bare-name gate goes green on all 15; production has **no reader** for any of them. The
substitution in each case is a real production surface, not a plan string:

| Symbol | Production surface that actually carries the fact |
|---|---|
| `OptionSpreadsPanel.target_value` | `target_edit.text()` / `_last_valid_target`; production calls `set_target_value` only |
| `OptionSpreadsPanel.toggle_colour` | `toggle_button` palette colour + `spread_state` stylesheet (both already asserted) |
| `OptionSpreadsPanel.toggle_collapsed` | `header_button` click/`setChecked` + `is_collapsed()` (production path) |
| `OptionSpreadsPanel.preferred_width` | `OptionSpreadsPanel.PREFERRED_WIDTH` (main_window:691/4524/4686) and `sizeHint()` |
| `OptionSpreadsPanel.elided_name` | `_ElideNameDelegate.initStyleOption` + the table's `ElideRight` mode + tooltip |
| `option_ladder.validate_spread` | AC-D65.2's guard is a test-side convention; no production caller |
| `SpreadEngine.latched_causes` | `take_messages()` (the live drain) and `_latched` internally |
| `SpreadEngine.pair_score` / `pair_eligible` | `_score_pair_complete` / `_score_at` (the live scoring path) |
| `SpreadEngine.lease` / `release` | `_lease_pair` / `_release_pair` (the live lease path) |
| `SpreadEngine.pending_legs` | `evaluate()`'s inline `leg_state(leg) == "pending"` check |
| `SpreadEngine.window_step` | the live cadence is `evaluate()`; `main_window` never calls the walk API |
| `SpreadEngine.pair_dropped` / `reseat_count` | `_dropped` / `_reseat_counts` (live state) |
| `option_chain_strikes` | the engine reads `series.strikes_by_right` directly |

**Verdict on the 15: all fifteen are genuinely unused; none has a production caller the scan
mis-modelled.** No allowlist entry is added for any of them (ESC-121's explicit prohibition).

**Six additional members the bare-name gate was hiding (found by the class-bound rule, not in the
reviewer's 15).** These were reachable only through a same-named thing elsewhere or through another
dead member, so the reviewer's bare-name measurement could not see them; the strengthened gate will:

- `OptionSpreadsPanel.toggle_state` — its only caller is `toggle_colour`, itself dead; production sets
  `spread_state` but never reads the accessor. Deleted with `toggle_colour`.
- `OptionSpreadsPanel.set_collapsed` — its only caller is `toggle_collapsed`, itself dead; the live
  collapse path is the header button. Deleted with `toggle_collapsed`.
- `SpreadEngine.target` / `SpreadEngine.spot` — properties with no production reader; production reads
  `_target` / `_spot` and calls `set_target`.
- `SpreadEngine.release` — no caller anywhere (the engine uses `_release_pair`).
- `SpreadEngine.req_id` — no production reader; production uses `_req_ids` and `rebind_leg`.

**Scoping — seven new tasks (P23-T18..T24), grouped by member group, sizes S/M.**

| Task | Group | Size | Deps | Files |
|---|---|---|---|---|
| **P23-T19** | panel's 7 dead accessors (+ the 2 cascades, so one owner per pair) | M | — | `ui/option_spreads_panel.py`, 3 suites |
| **P23-T20** | `validate_spread` | S | — | `services/option_ladder.py`, its suite |
| **P23-T21** | `option_chain_strikes` | S | — | `ibkr/contracts.py`, its suite |
| **P23-T22** | engine's 11 scalar/observability accessors | M | — | engine + 2 suites |
| **P23-T23** | engine's `window_step` walk API (+ its 2 private helpers) | M | — | engine + spread suite |
| **P23-T18** | gate evidence: production-only pool + class-bound methods (ESC-121) | M | T19–T23 | `tests/test_d65_residue.py` |
| **P23-T24** | allowlist per-entry invariant (ESC-122) | S | T18 | `tests/test_d65_residue.py` |

No size exception is taken: the largest task (T18) is one instrument, one file, ~24 honest steps —
the scanner change plus five seeded cases; T22/T23 are member-group deletions, not whole-module
rewrites. The deletions are deliberately **not** in T18: a single task that strengthens the scanner and
deletes all 21 members would exceed the step budget and mix a test instrument with four production
modules.

**Scheduling facts.** T19–T23 have no dependencies (all prerequisites are `done`); Build serializes
T19/T22 on `tests/test_d65_option_stream.py` and T22/T23 on the engine + spread suite via
`touches_files`, so the first frontier runs them one at a time. T18 is the phase-final green: it
depends on every deletion, and T24 follows T18. The gate edits for deleted symbols live **only** in
T18 (drop `option_chain_strikes` from `P23_ADDED_SYMBOLS`, drop `SpreadEngine.target` from the
method-map key list, fix the stale `validate_spread` prose) so no deletion task has to edit the gate
file and there is exactly one owner of the census. Consequence: between a deletion task and T18 the
gate's own candidate/key lists are stale for `option_chain_strikes`/`target`; that is a transient in
the wave order, not a task-level red — no deletion task's `test_command` runs the residue suite, and
T18's AC4 is the phase-final green proof.

**The evidence design T18 encodes.** Clause (i)'s reachability pool is production-only (`ui/`,
`services/`, `data/`, `ibkr/`, `config/`, `main.py`); `tests/` remains in the tree for clause (ii)'s
helper-in-its-own-file rule and clause (iii)'s token/import sweeps. A `Class.method` reference must
resolve at both ends: the candidate key is `Module:Class.method`, and the evidence is an attribute
access whose base resolves to that class (a name bound by `Name = Class(...)`, a `self.<attr>` /
`other.<attr>` bound to `Class(...)`, an annotated parameter, the class name, or `self`/`cls` inside
the declaring class). Bare names, string constants, argument names and unrelated-object attributes do
not count. The framework-callback exemption keeps its `(module, declaring class, method, registering
base)` validation and is consulted independently of reachability — the third measured consequence
(the unrelated `sizeHint`/`paintEvent` green without an entry) is closed by the same rule.

**ESC-122.** The wave-local `assert CENSUS_ALLOWLIST == {}` is replaced by a per-entry invariant:
every entry's citation resolves through `citation_violation` and the symbol is one the scanner would
otherwise report (so empty passes trivially, a legitimate cited entry passes, an entry for a reachable
symbol fails). The phase's zero-exemption state survives only as a separate phase-scoped statement
whose message says "no P23 symbol needs an exemption today".

**Residual finding recorded for Code Reviewer (not resolved here).** `window_step` was the only
implementation of AC-D65.4's direction/`h` walk, and its dedicated cases (`test_P23_T8_AC1...` and the
walk legs of AC2/AC4/AC5) are removed with it. The live cadence path is `evaluate()` →
`_best_neighbour`, which selects among `anchor-5/anchor/anchor+5` by distance and does **not**
implement the `> h` stop or the all-three-bases direction veto that AC-D65.4 states. The live path does
have coverage (`tests/test_d65_option_stream.py`'s target-driven one-step cases and the `evaluate()`
cases in the spread suite). Deleting dead code does not create that gap — it exposes it. If the
reviewer judges AC-D65.4 under-covered, the follow-up is to point `evaluate()`'s walk at an AC-D65.4
implementation (a behaviour fix), not to resurrect `window_step` as dead API.

**Verification.** `check_tasks.py`: `OK: 24 tasks validated, execution_graph.json written` (exit 0;
warnings are the pre-existing "pure-output file" pack notes on earlier tasks — none on T18–T24).
`graph_struct_sha256` regenerated: `9a5472a34fb0643ed6603ebdbe46abfe7ef3d6582a6690ea37e9969cfa6c0ed4`.
Metadata left at `"status": "READY_FOR_BUILD"`; T19–T23 are the first frontier, T18 next, T24 last.

**Not done here.** `docs/code_review/escalations.json` is Code Reviewer's file — ESC-121/ESC-122 stay
`open` for the reviewer's verification pass; this run did not edit it. No edit to
`requirements.md`, `plan.md` or `architecture.md` (the deletions are code, and the architecture's API
list is Plan-owned sync material); no `docs/requirements/open_questions.md` flag was needed — the
requirements are not ambiguous here.

## Owner decision — wire `evaluate()` to AC-D65.4 (2026-11-18)

**Direction, verbatim:** "Wire evaluate() to AC-D65.4 (recommended)". This supersedes this file's
earlier "Residual finding recorded for Code Reviewer" entry (the one that kept `window_step` as dead
API and left AC-D65.4 to the live `_best_neighbour` walk). That entry is retained above as history;
it is no longer the plan.

**What was measured in the tree (not re-derived).** `evaluate()`'s unmatched branch
(`services/option_spread_engine.py:1213-1224`) called `_best_neighbour(side, anchor)` (`:602`), which
takes the best of `{anchor-5, anchor, anchor+5}` by `_rank` — no improvement threshold, no direction
rule, and unlisted rungs silently dropped (so no chain-edge message). The AC-D65.4 rule —
`> h` improvement, all-bases direction, once-only chain-edge latch, one rung — existed only in
`window_step`/`_walk_candidate` (`:1232-1330`), which no production code calls.

**The transposition, stated so the reviewer can check it.** `_walk_candidate` took its *direction*
from its `wanted` argument and used the three credit bases only as a veto on that direction. The
live path has no caller-supplied anchor — `evaluate()`'s only input is the cadence clock — so the
direction must come from AC-D65.4's own sentence: all three bases below `T` ⇒ the toward-the-money
rung (CCS strikes down, PCS strikes up), all three above ⇒ the away rung, otherwise no direction.
That is the one interpretive step in this change; everything after it is `_walk_candidate`'s code:
listed (else latch `CAUSE_WALK_CHAIN_EDGE` once, naming the current anchor as the best reachable
value), quoting, then `nxt.distance < cur.distance - band`. The veto's third state — bases that
straddle `T` — is the owner's explicit "refuse when the three bases disagree" case.

**Deletions this makes genuinely unreachable.** `window_step`, `_requested_targets`,
`_walk_candidate`, and `_best_neighbour` (its only caller was the branch being replaced). Kept, and
required by the live path: `_score_at`, `_score_pair_complete`, `_pair_listed`, `_anchor_matched`,
`_install_windows`, `_latch`, `band`, and `_rank`/`_best_of` (seeding). The class docstring's walk
bullet is rewritten to describe `evaluate()`'s decision.

**Cases that pinned the unapproved behaviour, and what happens to them.**

| Case | Was asserting | Now |
|---|---|---|
| T8 AC1 (`test_P23_T8_AC1_…`) | caller-directed `window_step` steps, including an up-step that the mid-curve allowed but the AC's strike direction does not | rewritten onto `evaluate()`: decided direction, one rung, exact-`h` stop, ask-only match, stationary feed, tie/no-oscillation |
| T8 AC2 (shared leg/reqId/budget) | `window_step` step | same facts through one `evaluate()` step (or `_install_windows`); legs, reqIds, peak/dip unchanged |
| T8 AC4 (freeze) | `window_step` no-op while frozen | second `evaluate()` no-op while frozen |
| T8 AC5 (error classes) | `window_step` after a dropped pair | `evaluate()` after the drop |
| T7 AC7 (vocabulary/budget) | re-anchored 7330→7335 by killing the anchor legs | **a dead anchor pair has no bases, so AC-D65.4 refuses** — the case now re-quotes the ladder to a compliant step and keeps its peak/dip assertions |
| T9 AC2 / AC6 (stream, owner of the live wiring) | a Target change to 1.20 moving CCS **7355** | moved to a separate task (P23-T25): the fixture cannot support that move (below) |

**Why the stream suite needed its own task.** The stream fixture's CCS credit curve *rises* 0.01 per
strike point (`_price`/`_credit` in `tests/test_d65_option_stream.py`), so one 5-point rung changes
`d` by exactly `h = 0.05` — under AC-D65.4's strict "more than `h`" rule the live ladder can never
step on that fixture at any target. Its two target-commit cases therefore pin a step the approved
rule does not permit, and no target value repairs that. P23-T25 makes the fixture economically
faithful (CCS mid falls, PCS mid rises, 0.02/point ⇒ 0.10 per rung) and re-points the two cases onto
the decided directions at `T = 1.20`: **CCS 7350→7345, PCS 7350→7355** — opposite strike directions,
which is exactly the case `window_step`'s dict-shaped `target_anchor` existed for.

**Task changes.** P23-T23 revised (behaviour + deletion + its cases). P23-T25 added (stream fixture
and the two target-commit cases, `dependencies: ["P23-T23"]`). P23-T18's dependencies extended to
`T19, T20, T21, T22, T23, T25` so both gates (T18, then T24) still see the final tree. T19, T20,
T21, T22 and T24 are unchanged: they are independent dead-symbol deletions. Build already serializes
T22/T23/T25 on the engine and the two suites; no new dependency was added for file overlap alone.

**AC → test mapping (which clause each test proves).**

| AC-D65.4 clause | Test |
|---|---|
| one 5-point step on both legs, toward the adjoining rung with the smaller `d` | P23-T23-AC1 (CCS 7330→7325, PCS 7330→7335 in one evaluation) |
| toward the money (all three bases below `T`; CCS down, PCS up) | P23-T23-AC1 |
| away from the money (all three above `T`; CCS up, PCS down) | P23-T23-AC1 (away leg) |
| stops when the pair is matched (incl. **matched on the ask basis only**) | P23-T23-AC2 (a) |
| stops when no neighbour improves `d` by more than `h` — exactly `h` included | P23-T23-AC1 (second evaluation) |
| stops when no neighbour improves `d` by more than `h` — strictly less than `h` | P23-T23-AC5 (red on the pre-change engine) |
| `h = max(0.05, one_tick)`: both levels pinned | P23-T23-AC3 (0.05 at `T<3.00`; 0.10 at `T≥3.00`; exact-`h` vs above-`h` in each) |
| stops when the improving rung is not a listed pair + **once-only chain-edge message naming the best reachable value** | P23-T23-AC2 (b) |
| equal-`d` neighbours break on the credit mid then stay; a stationary feed produces no further moves (no two-rung oscillation) | P23-T23-AC2 (d) + P23-T23-AC1 (second evaluation) |
| one step per evaluation (≤1 per A191 cadence, never a jump) | P23-T23-AC1 + re-pointed T7 AC7 (peak/dip 16→14→16) |
| the bases disagree about the direction ⇒ no step (owner's wording) | P23-T23-AC4 (red on the pre-change engine) |
| AC-D65.12(i): the parallel walk API is dead and removed | P23-T23-AC6 |
| AC-D65.6 shared leg keeps its line and reqId across a step | re-pointed T8 AC2 + P23-T25-AC2 |
| the live wiring carries the step (Target change, registry, ceiling) | P23-T25-AC2 |

**Red-first evidence.** P23-T23-AC4 and P23-T23-AC5 are written against the current engine first:
today's `evaluate()` steps to `0.05`-smaller `d` (AC5) and to a smaller-`d` rung regardless of where
the bases sit (AC4), so both fail before the change. Their `expected_result` says so; the worker is
instructed to run both before the engine edit and record the failure.

**Step-fit note (size exception, P23-T23).** T23 is the wave's largest task at an honest ~26–30
steps, above the ~20 target and inside the ~32 cap. It is taken because the change is one invariant
with one owner — the step decision — and because splitting the two red-first cases into a later task
would destroy the RED evidence the owner asked for (a test added after the behaviour exists can only
prove green). The production edit is one branch plus one helper plus four deletions.

**Transient red, by construction.** Between T23 and T25 the stream suite's two target-commit cases
are red (they assert the pre-change move). That is why T23's `test_command` is the spread suite
alone, T25 depends on T23, and T25's command runs both suites. This mirrors the phase's existing
"gate lists are stale between a deletion task and T18" transient, not a task-level red.

**Doc note for Plan (not edited here).** `docs/plan.md#P23-04` still lists
`window_step(target_anchor) → Actions` as the deliverable for this half of the engine. That line is
stale after T23 (the rule lives in `evaluate()`'s decision now); `docs/architecture.md` S-P23-4 never
named the API, so it stands. `plan.md` is Plan/Validator-owned — recorded for the doc-sync path, not
changed by this run.

**Verification.** `python3 ~/.config/opencode/scripts/check_tasks.py`: `OK: 25 tasks validated,
execution_graph.json written` (exit 0; no warning on T18, T23 or T25 — the remaining warnings are the
pre-existing "pure-output file" pack notes on earlier tasks). New
`graph_struct_sha256`: `099fc3cd185b5baf6ae41c281fbbbebbd95ee6c6284e91bca6eda428f536555f`.
Metadata left at `"status": "READY_FOR_BUILD"`; frontier is unchanged (T19–T23), then T25, then
T18, then T24.

**Not done here.** No edit to `services/option_spread_engine.py` or any test (this run only revises
the graph and its packs); no edit to `docs/code_review/escalations.json` (ESC-121 stays `open` for
the reviewer's verification pass); no edit to `requirements.md`, `plan.md` or `architecture.md`; no
`open_questions.md` flag — AC-D65.4 is unambiguous, and the owner supplied the one decision the
architecture did not (where the rule lives).

## Wave 8 (2026-11-18) — three owed items: T22's stale block, the census inventory entry, the paper-TWS record

### 1. P23-T22's `blocked` status — nothing invented, and the gate no longer waits on it

**What the graph says now, and why.**

- **T22's status is untouched** (`blocked`, exactly as its worker reported it). `build_wave.py reset`
  refuses blocked tasks ("those go through Code Reviewer"), so the graph cannot clear the block by
  flipping a string, and choosing a status for a blocked task is the reviewer's disposition, not
  mine. No status was invented and T22's criteria, tests and pack are unchanged.
- **P23-T18's dependencies changed** from `[T19, T20, T21, T22, T23, T25]` to
  `[T19, T20, T21, T23, T25, T26]` — the `T22` edge dropped, the new `T26` edge added (§3).
- **Why the drop is a factual correction, not a way round a blocked task.** The edge asserted "the
  gate cannot be green until T22 is `done`". T22's *subject* — the eleven `SpreadEngine` accessors
  deleted and both engine suites re-pointed at the production/internal surface they wrapped — is
  already in the tree: `services/option_spread_engine.py`, `tests/test_d65_spread_engine.py` and
  `tests/test_d65_option_stream.py` carry it uncommitted, and all eighteen deleted member names are
  absent from both modules. What the worker reported was two **pre-existing** stream-suite walk
  assertions (T9 AC2 registry :409, T9 AC6 rejected-target :1039, both 7350 vs 7355) red on P23-T23's
  new strict `> h` step rule — outside T22's subject. P23-T25 has since made the stream fixture
  faithful (0.10 per 5-point rung), and the four suites then reported **88 passed**
  (`tests/test_d65_option_panel.py tests/test_d65_option_stream.py tests/test_d45_removal.py
  tests/test_d65_spread_engine.py`). So the edge's premise is true and its only remaining effect was
  to hold the gate hostage to a status string.
- **What is kept.** T18 still depends on T19 (in progress — its seven panel-accessor deletions must
  land), T20, T21, T23 and T25: the landed deletions and the step rule whose tree the gate certifies.
  The list is "whose output the gate actually needs", not "every task that ever ran".
- **Consequence for the reviewer.** T22 now has **no dependents**, so it cannot stall the frontier; it
  stays visible in the graph and in the notes for the reviewer's pass, which may re-run it and reset
  it (subject landed → `done`) or open an escalation. Both are outside my remit.

### 2. The census inventory entry — folded into P23-T18 as an invariant, not one deleted string

**Facts.** `tests/test_d65_residue.py:93` still lists `option_chain_strikes` in
`P23_ADDED_SYMBOLS["ibkr/contracts.py"]`, although P23-T21 deleted that helper from `ibkr/contracts.py`.
Nothing fails: the census only asks whether a *candidate* has a caller, so a name that no longer exists
is simply never reported, and an inventory value that only mentions itself is invisible to it. The gate
therefore certifies an inventory of something that is gone.

**Change.** T18 gains **AC6** and **P23-T18-AC6**: every `P23_ADDED_SYMBOLS` name must resolve to a
symbol that still exists in the module it is filed under (a module-level definition or a class member
of that module), with a seeded phantom-entry fixture; `option_chain_strikes` must be absent from the
`ibkr/contracts.py` tuple. Invariant-shaped on purpose — the deleted symbol is the instance, "the
inventory describes what exists" is the rule — and it is **red on today's dict**, so removing the
entry is not the whole task. AC4's parenthetical was narrowed to `SpreadEngine.target` and
`validate_spread` so each AC keeps one subject; T18's pack gained the `80-100` read range for the
inventory block, an `outputs` line, and a `716-800` why naming where the new case lands.

### 3. P23-T26 — the acceptance record rewritten as a live-TWS, read-only checklist

**Facts.** `docs/archive/probe_records/d65_paper_tws_acceptance.md` instructs the reader to use a
**paper** port and says "never the live port". There is no paper TWS (owner, verbatim: *"there is no
paper-TWS"*), and AC-D65.19 was amended 2026-11-18 to an owner-run **live-TWS, read-only** acceptance
on `127.0.0.1:7496` (A211 revised). As written the record cannot be executed, and the phase gate it
belongs to is therefore unreachable.

**Task.** P23-T26 (`doc`, size M, no dependencies, `touches_files`: the record, `INDEX.md`,
`tests/test_d65_acceptance_record.py`, `tests/test_d65_residue.py`) rewrites the record as that
checklist: live `127.0.0.1:7496`, read-only by construction (zero order code; only
`reqSecDefOptParams` / `reqMktData` / `cancelMktData`), observation-only, no checklist item may ask the
owner to place, modify or cancel an order — the only cancel in the run is a market-data line. The same
six checks, the 16+1 = 17 line-count table, the fixed numbers (`h = max(0.05, one_tick)`, the sign
pair, the `7425/7445` and `7340/7320` fixtures), the screenshots/notes slots and the
ACCEPTED/REJECTED/WAIVED closers are carried over in the D48/D52 recorded-probe shape. **All six items
stay PENDING** — the owner has not run it, and the build records no result.

**Decisions recorded (each one deliberate).**

- **Filename retained** (`d65_paper_tws_acceptance.md`) even though "paper" is now false:
  `docs/architecture.md` (the acceptance-evidence row at :9415 and S-P23-22) and `docs/plan.md#P23-10`
  name that path, and both files are Plan/Validator-owned. A rename would leave canonical references
  dangling for a wave that may not edit them. The record's H1 states the live environment and its head
  block says the filename predates the 2026-11-18 amendment.
- **Plan-vs-requirements divergence, resolved by the requirement.** `docs/plan.md#P23-10`'s heading and
  goal still say "paper-TWS" (as does S-P23-22's sentence). AC-D65.19/A211 were amended on 2026-11-18
  and the owner's instruction for this run names the live run. I decomposed the *amended requirement* —
  a plan section cannot make an unsatisfiable environment executable — and record the divergence here
  rather than editing `plan.md`. **Doc note for Plan:** P23-10 and S-P23-22 need the paper→live
  correction on the doc-sync path.
- **The residue gate's own prose moves with it.** `tests/test_d65_residue.py`'s `GATE_RECORD` still
  says "the owner's paper-TWS acceptance run … owned by P23-T14" (:319-321) and
  `test_record_declares_ac_d65_19_open_and_owned` asserts "owned by P23-T14" (:1701), plus the module
  docstring's "still-open paper-TWS criterion" (:40). Left alone, the phase would ship a gate certifying
  the wrong environment and the wrong owner. T26 therefore declares that file and re-points those three
  sites at the live run and P23-T26.
- **T18 now depends on T26.** T18 turns the gate green and its AC4 certifies that file's prose, so it
  must see T26's wording. T24 already depends on T18, so the order is **T26 → T18 → T24**, serialised
  by the dependency, not merely by the file overlap.
- **A small dedicated suite** (`tests/test_d65_acceptance_record.py`, three doc assertions) rather than
  more cases in the residue gate: it keeps the gate's subject the census, and follows the existing
  `test_d48_gate.py` / `test_p12_gate.py` precedent of asserting a probe record's content.

Size note: T26 is M at ~14-18 steps (four file writes, two suite runs) — inside the ~20 target, no
size exception needed.

**Verification.** `python3 ~/.config/opencode/scripts/check_tasks.py`: `OK: 26 tasks validated,
execution_graph.json written` (exit 0). The only new warning is T26's `tests/test_d65_acceptance_record.py`
"not in read_files (ok if pure-output file)" — correct, it is created, not read. New
`graph_struct_sha256`: `a2f8e949cd3abd936ea45fab135a3f392464666249fc8f76dbc763c37e88eaa4`. Frontier
after this run: **T26 ready now**; T18 waits on T19 and T26; T24 after T18; T22 blocked with no
dependents. Metadata left at `"status": "READY_FOR_BUILD"`.

**Not done here.** No edit to P23-T19, T20, T21, T23, T25 or T17, and none to their packs; T22's status,
criteria, tests and pack untouched; no production or test code edited (this run revises the graph, its
packs and this file); `docs/code_review/escalations.json` untouched; `requirements.md`, `plan.md` and
`architecture.md` untouched; no new `open_questions.md` flag — AC-D65.19 is answered and unambiguous.

---

## Correction run — census-key fix moved into P23-T18; T18 unblocked from P23-T26

**Why.** P23-T26 reported blocked on one red outside its footprint:
`tests/test_d65_residue.py::test_method_census_covers_p23_classes_and_excludes_dunders` (:777) still expects
`SpreadEngine.target` in the method census. P23-T22 deleted that property (it is on T22's deletion list);
the engine defines `set_target` (`services/option_spread_engine.py:422`) and the `band` property (:432-433),
no `target`. The key list is the *gate's* inventory, not a fact T26 introduced — T18 already owns that file,
already has AC6 on inventory truth, and its AC4 named `SpreadEngine.target` as a deleted symbol the gate must
stop naming. So the correction is a defect in the gate, filed under T18.

**T18 AC4 amended (prose and test).** The case must still prove the census covers real P23 members, so the
stale key is replaced rather than deleted: `SpreadEngine.set_target` and `SpreadEngine.band` (both verified
in the tree above) now stand where `SpreadEngine.target` stood. To keep the case discriminating rather than
widened to whatever passes, AC4 and P23-T18-AC4 also require that `SpreadEngine.target`, the dunder
`SpreadEngine.__init__` and a synthetic non-member key (`SpreadEngine.not_a_method`) are *absent* from
services/option_spread_engine.py's census. The pack's `read_files` `why` for :716-800 states the same
(an edit instruction, not a contradiction). No footprint change: T18's `touches_files` is still just
`tests/test_d65_residue.py`.

**Dependency edge dropped.** T18's `dependencies` no longer include P23-T26 (now T19, T20, T21, T23, T25 —
all done). The edge existed only for T26's `GATE_RECORD` prose, and that prose is already in the tree
(T26 completed it); keeping the edge serialised the gate behind a task the gate itself unblocks. With the
edge gone T18 is dispatchable now; T24 stays dependent on T18, so the phase tail is T18 → T24.

**T26 untouched.** Its `status` field is left exactly as found (the file reads `in_progress`; the wave
reported it `blocked`) — Task Manager does not resolve a blocked task. T26's blocked status therefore stays
visible to the Code Reviewer, who owns resolving it; its four AC cases pass and its work is in the tree, so
the only thing outstanding is the gate red T18 now fixes.

**Verification.** `python3 ~/.config/opencode/scripts/check_tasks.py`: `OK: 26 tasks validated,
execution_graph.json written` (exit 0). New `graph_struct_sha256`:
`c5b7fcf47fadea644cb999108db514ff0b1368ad59ec3ffe9c9181ceb22562a8`. Metadata `"status":
"READY_FOR_BUILD"` (unchanged). No edit to T19/T20/T21/T23/T25/T26, no status change anywhere, no
production or test code edited.
