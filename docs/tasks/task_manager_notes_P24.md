# Task Manager notes — Phase P24 (D66: PCS ordering delta)

**Graph:** `docs/tasks/task-graph.json` — three tasks, matching the approved plan's three waves.
**Status:** `READY_FOR_BUILD`. No `ESCALATED_TO_PLAN`, no requirements-ambiguity flag (the plan answers every
question this decomposition needed: the table shape, the canonical PCS pair, the gate-move ordering, the
`SpreadRow` docstring deliverable, and the fence's artefact list).

## Task split

| Task | Plan wave | Size | Production edit | Files |
|---|---|---|---|---|
| `P24-T1` | P24-01 | S | **yes** — `services/option_ladder.py` | ladder module + its suite |
| `P24-T2` | P24-02 | M | no | engine suite + stream suite |
| `P24-T3` | P24-03 | S | no | panel suite + residue suite + new fence suite |

Sizes follow the plan (S/M/S). The only production change in the phase is `P24-T1`, which keeps `AC-D66.8`'s
fence meaningful: every other task's `Do not` clause is carried into its acceptance criteria ("git diff lists no
production file").

## Dependency deviation from the plan's stated shape (deliberate, recorded)

The plan states `P24-01 → P24-02` and `P24-01 → P24-03` with 02 and 03 independent of each other. The graph keeps
both edges **and adds `P24-T2 → P24-T3`**, so the build order is `T1 → T2 → T3` (three waves).

Reason: `P24-T3`'s exit condition (plan wording: *all seven `tests/test_d65_*` suites plus the fence suite green
in one run*) is not satisfiable independently of `P24-T2`. The residue gate `test_canonical_fixtures_survive_and_
the_typos_do_not` scans `CONSISTENCY_FILES`, which includes `tests/test_d65_spread_engine.py` and
`tests/test_d65_option_stream.py` **as text** (for non-20-wide named pairs and banned examples) — so `P24-T3`
asserts a property of `P24-T2`'s two files. With no edge, Build would dispatch them in the same wave (their
`touches_files` are disjoint), and `P24-T3` would run the residue gate against a file another worker is mid-edit —
a semantic race no file-conflict check catches. The two tasks' *edits* remain logically independent (as the plan
says); the edge carries the verification dependency the plan itself requires. Cost: one extra wave on a 3-task
phase.

`P24-T3` is also the reason `AP-P24-9`'s ordering is safe: the panel fixture (deliverable 1) and the residue
constant (deliverable 2) are one task, panel first, and `P24-T1`/`P24-T2` are instructed to leave the ladder
suite's `7340/7320` legality examples in place, so no wave exits with the residue suite red.

## Sizing notes

- `P24-T3` carries four deliverables (panel fixture, residue re-point, the fence suite, the diff-scope record) and
  stays a single task. Reasons recorded per the sizing rules: (a) two of the four are one-line constant edits whose
  ordering `AP-P24-9` pins to a single wave (`tests/test_d65_residue.py` is the fifth re-baselined suite only
  because `RC-P24-1` put it there); (b) the fence suite is the same wave's exit instrument (one assertion per named
  artefact, `S-P24-5`), not a separate deliverable with its own acceptance criteria; (c) splitting would create a
  second writer of the residue suite's expectations in the same wave. Honest step count is ~24–26 (two constant
  edits + one new ~9-assertion suite + the diff record), above the ~20 target and well under the ~32 exception cap;
  the pack is written to keep the worker from re-deriving the marker sites or the regex.
- `P24-T2` is sized M for two 1,400–1,700-line suites: the re-derivation is fixture work (mirror profile, coverage
  assertion, per-side constants, row indices, re-anchor leg sets), each site named in the plan's deliverable 1–3.

## Carried constraints (encoded in the tasks, not just here)

- **Zero panel production lines change** — `P24-T3` may not edit `ui/option_spreads_panel.py`; its `read_files`
  entries for that module are marked read-only.
- **Prohibition is on positive fixture use only** — `P24-T3-AC9` requires the shipped negative guards
  (`BANNED_EXAMPLES`, its ban-list self-guard, `_fixture_guard`'s docstring) to keep naming the banned pairs; no
  task deletes them.
- **Anchor semantics untouched** — anchor = offset 0 = label 3 both sides; `rows()`'s `rung` = display row. Both
  are stated in `P24-T1`'s ACs and frozen contract refs.
- **Frozen interfaces** are carried as `existing` refs (`format_instrument`, `window_legs`, `ladder_pairs`,
  `SpreadRow`, `apply_snapshot`, `set_toggle_state`, `DEFAULT_TARGET`, `rows`, `anchor`), never as copies.
- **Real test commands**: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest … -q` per task (conftest pins
  `DB_PATH` to a temp file and `QT_QPA_PLATFORM=offscreen`; the env prefix is kept explicit per the plan).
- **No user-doc task** — `AP-P24-8`: `USAGE.md`'s Option Spreads section states no rung offset or row ordering, so
  `doc_required` is `false` on all three tasks.

## Test-to-AC linkage

Every acceptance criterion has exactly one linked test (6 / 8 / 9). No criterion is covered by a test that depends
on another task's not-yet-landed output: `P24-T3-AC9` (all eight suites green) and `P24-T3-AC2` (the residue gate)
are the only cross-file assertions, and both sit behind the `P24-T2` edge for that reason.
