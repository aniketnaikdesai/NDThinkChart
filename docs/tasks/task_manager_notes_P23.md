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
