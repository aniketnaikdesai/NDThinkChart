# Task Manager notes — Phase P29 (D96–D100)

**Graph:** `docs/tasks/task-graph.json` (5 tasks) · `docs/tasks/execution_graph.json` (3 waves) ·
`check_tasks.py` PASS (only the expected "new suite not yet on disk" pure-output warnings).
**Baseline for the delta record:** `3b92ce6` (P28 close-out, pushed). Plan approved and activated at
`e7ac594`, wording amendment `RG-P29-1` at `2bb9a62`. No `ESCALATED_TO_PLAN` open.

## Waves

| Task | Wave | Size | Depends on |
|---|---|---|---|
| P29-T1 | P29-01 (D96 + D100) | M | — |
| P29-T2 | P29-02 (D97) | S | — |
| P29-T3 | P29-03 (D98) | M | P29-T2 |
| P29-T4 | P29-04 (D99) | M | — |
| P29-T5 | P29-05 (records/fence) | S | T1, T2, T3, T4 |

Wave frontier = **P29-T1 ∥ P29-T2 ∥ P29-T4**, then **P29-T3**, then **P29-T5** — the plan's
`01 ∥ 02 ∥ 04 → 03 → 05`. No two waves share a production file. `P29-T3` follows `P29-T2` because
`AC-D98.2`'s post-seed crossing case must be written against the phase's final crossing rule.

## Size notes

- **P29-T3 is sized at the invariant cap, not split.** It is one rule — *every outage has one interval, one
  baseline and one resume path* — whose two production files (the monitor and the window's drop/connect block)
  are the two halves of the same invariant. Splitting at the monitor/window seam would give two owners of the
  same baseline and make `AC-D98.1`'s cross-file assertions half-verifiable in each task. Honest step count
  (reads, 6 edits, 10 cases, 2 suite runs, report) is ~30, under the ~32 single-owner cap; recorded here as the
  required exception. `P29-T1` (~24), `P29-T2` (~12), `P29-T4` (~24) and `P29-T5` (~13) sit inside the ~20 target.

## Decisions carried verbatim into the packs

- **P29-T1:** serialize before touching the connection; `with db.conn:` around DELETE+executemany; unknown keys
  rejected before a cursor exists; one filtered pair list derives columns, placeholders and values; bool→int only
  for `visible`/`locked`; a bool for text rejected.
- **P29-T2:** `prev <= level < curr` / `prev >= level > curr`; previous side inclusive, current side exclusive;
  touch derived; **no new alarm field** (DG133).
- **P29-T3:** the gate is the **session** predicate, not `MainWindow._ibkr_connected`; `begin_outage()` returns
  immediately with no sessions; `_outage_active` has one setter (`begin_outage`) and one clearer (`resume_all`);
  `pause_all` no longer sets it; **`_go_live` is not edited**; the three residuals are accepted, not fixed.
- **P29-T4:** a page-ready transition delivers from `_op_log` only; staging buffers cleared, not drained;
  `set_ready` cannot emit.

## Recorded translation choices (no re-scope)

- **Delta-record base.** The plan's P29-05 deliverable 3 names `git diff --name-only ef04c5a`. `ef04c5a` predates
  the P28 build, so that diff would include all P28 files and fail the very allowlist it gates. The pack pins
  **`3b92ce6`** (the P29 baseline given for this run), which yields the P29-only delta the allowlist describes.
  Everything else in the deliverable is unchanged; `AC-P29-05-SCOPE` states the base explicitly.
- **G6.** Stated as owner-run and never claimed in P29-T3's exit condition, its suite docstring requirement and
  the pack; `AC-P29-05-G6` records it. No test asserts a live socket drop or a live alarm fire.
- **Declared re-baselines are gates.** P29-T2 carries the one alarm-service re-baseline; P29-T3 carries the D40
  re-baseline plus the four `_pause_start` renames and the `:445` value change; P29-T4 carries the bridge
  re-baseline. Each task's exit condition says any other red is a stop-and-escalate.
- **`_pause_start` travels as a legacy deletion string** (`status: new`, text `LEGACY - DELETED IN P29: ...`) plus
  `AC-P29-03-LEDGER`'s absence assertion — it is never an `existing` contract ref.

## P28 record drifts

The four non-blocking P28 record drifts the reviewer logged (`P28-T13`'s description, `P28-T14-05`'s
`expected_result`, `P28-T12`'s deleted `_in_phase` contract ref, `AC-P28-02-S8`'s stale `(b7914c3 ...)` note) lived
in the P28 graph. This run replaces `task-graph.json` wholesale with P29's tasks, so none of them carries forward
and none can mislead a later run; no separate edit was needed.

## Open items

- No requirements-ambiguity flag was needed (`docs/requirements/open_questions.md` untouched).
- No architectural decision was taken by Task Manager; every rule above is from the activated plan/architecture.

## Pack fix — P29-T4's test command (`-m 'not webengine'`)

**Trigger.** P29-T4 returned `blocked` with its implementation complete and green. Only the declared command
failed: `pytest tests/test_d99_page_ready_delivery.py tests/test_lwc_bridge.py -q` aborted with SIGABRT
(exit −6) inside `tests/test_lwc_bridge.py::test_host_loads_ndt_chart_offline` while constructing a
`QWebEnginePage`.

**Cause (pre-existing, environment-only).** `tests/test_lwc_bridge.py`'s gated host cases build
`QApplication.instance() or QApplication([])`; with an empty argv, QtWebEngine's Chromium `CommandLine` aborts
on this macOS box when a `QWebEnginePage` is constructed. Evidence supplied by the worker and re-checked here
against the file: the same abort reproduces with both changed files restored to `HEAD` (so it is not a D99
regression), and a minimal probe constructs the page fine under `QApplication(sys.argv)`. `docs/memory.md`
already carries this family as a Known Gotcha, and the pipeline's standard invocation is `-m 'not webengine'`.

**Change (T4 only; `status` stays `in_progress` for the finalize re-dispatch).**

- `context.test_command` now ends `-q -m 'not webengine'` — the same two files, nothing else.
- The task's exit-condition text (its `description`, the graph's own copy) now states that the gated
  `@pytest.mark.webengine` host cases are excluded **by marker** because the abort is a pre-existing
  environment limitation, not a D99 regression, and names the evidence (`HEAD` reproduction;
  `QApplication([])` vs `sys.argv`). It also says: no skip, no harness rewrite, and the gated cases are not
  touched — a harness fix, if the owner wants one, is a separate task.
- Unchanged: deliverables, acceptance criteria, tests, dependencies, `touches_files`, scope. The plan's
  P29-04 "Exit condition" bullet in `docs/plan.md` is Validator-owned and was **not** edited; the graph's
  task description carries the clarification into every dispatch instead.

**Scope check across P29.** Only P29-T4's `test_command` names a suite containing gated cases
(`tests/test_lwc_bridge.py`: three decorators — `test_interceptor_wired_blocks_non_ndt`,
`test_host_loads_ndt_chart_offline`, `test_render_terminated_recovery_wired`). P29-T1, P29-T2, P29-T3 and
P29-T5 name suites with **zero** `@pytest.mark.webengine` cases, so no other command needed the flag.
`tests/test_lwc_bridge_handshake.py` — named in P29-04's exit condition but not in the command — carries two
gated handshake cases (`test_page_bridge_handshake_reaches_window`,
`test_view_cycles_keep_page_loads_alive`); the description now tells the worker to run those nine companion
suites with the same marker exclusion, unchanged.

**Rule recorded.** A task's `test_command` must match the pipeline's invocation convention
(`-m 'not webengine'`) whenever it names a suite containing gated cases, or a healthy task reports `blocked`
on an environment artefact. Stating the exclusion in the task text (not just the command) keeps the exit
condition honest: the gate is the new suite plus every non-gated case.

**Graph check.** `check_tasks.py` → `OK: 5 tasks validated`, exit 0; `execution_graph.json` regenerated. The
only output is the four pre-existing "new suite not yet on disk" pure-output warnings.

**Status note (same run).** During this pack fix the build loop consolidated the archived blocked result and
left T4 `blocked`; per the escalation it was set back to `in_progress` so the loop re-dispatches it as a
finalize pass (no other field touched).

## Pack fix — P29-T5's footprint vs agent permissions (`docs/codebase-map.md`)

**Trigger.** P29-T5 could not finalize: its `touches_files` listed `docs/codebase-map.md`, but the Build
Worker's permission block denies editing the map (it is Plan-owned per AGENTS.md). The worker correctly
refused to route around the permission and reverted its generator run, so the fence suite
`tests/test_p29_fence.py` is written and green (13 passed) and its delta-scope and G6 records are verified
clean, with nothing left to build except a write the task was never allowed to make.

**Change (T5 only; `status` stays `in_progress` for the finalize re-dispatch).**

- `touches_files` is now exactly `['tests/test_p29_fence.py']`; `docs/codebase-map.md` appears in no task's
  `touches_files`.
- `description` no longer instructs a map refresh or a `(root)/`-row repair; it states that the map is
  Plan-owned and refreshed by Plan under `map_repair`, that this task never writes it, and that the exit
  condition does not depend on the map changing in this task.
- `AC-P29-05-MAP` keeps the same assertions but is now explicitly read-only: the fence asserts the P29 note,
  the carried-forward annotations (P28 included), the absence of a `(root)/` row and the four suites on disk;
  refreshing the map is Plan's edit site.
- `expected_artifacts` / `outputs` drop "the refreshed map note" and name the fence's read-only map
  assertions instead. `inputs` labels the map read "read-only".
- The pack's `read_files` entry for the map is marked read-only ("never edit … Plan owns this map"),
  with an approximate range that says to locate the note/markers by heading because Plan is refreshing it
  concurrently.
- Unchanged: all five acceptance criteria's behaviour, all five tests and their links, dependencies, `size`,
  `doc_required`, `test_command`, and T1–T4 in every field. The fence's assertions were not touched.

**Rule recorded — `touches_files` must respect agent permission blocks.** A file the assigned agent cannot
edit does not belong in that task's `touches_files`; it belongs to the agent that owns it (the codebase map →
Plan). A task that needs to verify such a file may **assert** on it read-only, with the read marked as
read-only in the pack and with no acceptance criterion requiring the task to write it. Otherwise a healthy
task can only report `blocked`, and the correct worker behaviour (refusing to bypass permissions) reads as a
task failure.

**Three P29 pack-defect classes to check before handoff next phase.** This is the third defect of its class in
P29; each was a pack fact that the graph asserted falsely, not a build failure:

1. **Test command vs environment marker** (T4): a `test_command` naming a suite with `@pytest.mark.webengine`
   cases must carry the pipeline's `-m 'not webengine'` exclusion.
2. **Delta base** (T5/T3 record): the recorded `git diff` base must be the phase baseline the plan names, not
   the tree's current `HEAD` — verifiable by running the command's base against the phase baseline row in
   `docs/plan.md`.
3. **Footprint vs permissions** (this entry): no `touches_files` entry may name a file the task's agent is
   denied by its permission block.

Before setting `READY_FOR_BUILD` next phase, sweep every task for all three: (a) does each `test_command`'s
suite carry gated cases without the marker flag, (b) does each recorded-diff base match the plan's phase
baseline, (c) does each `touches_files` entry sit inside the assigned agent's permission allowlist.

**Graph check.** `check_tasks.py` → `OK: 5 tasks validated`, exit 0; `execution_graph.json` regenerated. The
only output is the four pre-existing "new suite not yet on disk" pure-output warnings.
