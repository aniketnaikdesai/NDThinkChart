# Task Manager notes — Phase P30 (D101–D104)

**Decomposition run:** 2026-11-20. Plan `docs/plan.md` § Phase P30 ends `Status: READY_FOR_TASK_MANAGER`
(line 9567); architecture § Phase P30 approved; `docs/plan_review_P30.md` requires no further change.
No `ESCALATED_TO_PLAN` open, no open escalation routed to `TASK_MANAGER` (134 entries, all `addressed`).

## 1. Baseline — pinned to the run's actual tree, not the plan's older values

- **Recorded phase baseline: `956f9f8`** (P29 close-out: changelog, review log, ESC-138/139 addressed,
  memory correction). This is the commit every baseline-relative check in the graph names
  (`git diff --quiet 956f9f8 -- …`, `git diff --name-only 956f9f8`).
- The plan's "Baseline: HEAD `dcfdd60`" and its P30-04 record base `3b92ce6` are **P29's build commit and
  P29's own base**; they predate the P29 close-out commit that is actually checked out. The graph therefore
  supersedes both with `956f9f8`, and `P30-T4`'s record AC says so explicitly (pack-defect class 2 from the
  handoff brief: every recorded/baseline diff uses the run's actual baseline).
- `git diff` against `956f9f8` at the time of writing shows a clean tree, so the phase delta starts empty.

## 2. Tasks, sizes, frontier

| Task | Plan wave | Size | Deps | Frontier |
|---|---|---|---|---|
| `P30-T1` | P30-01 — D101 restore + D101.2 latch | M | — | wave 1 |
| `P30-T2` | P30-02 — D102 + D103 | S | — | wave 1 |
| `P30-T3` | P30-03 — D104 sweep | S | `P30-T1` | wave 2 |
| `P30-T4` | P30-04 — fence / records | S | `P30-T1`, `P30-T2`, `P30-T3` | wave 3 |

Frontier as approved: `P30-T1 ∥ P30-T2 → P30-T3 → P30-T4`. No task was added, merged or re-scoped.

**Size exception recorded — `P30-T1`.** It is declared `M`, but its honest action count is ~30 (8 read
sites, edits in 6 files, 3 new suites, 2 node runs, the join and the Python path). That is at the
**invariant-shaped ~32 cap**, deliberately: A246 forbids splitting the restore, and a language split would put
`AC-D101.2` (page latch) in one wave and its only production trigger (the `router_mode` op that exists only
once the press crosses) in the next — two halves of one criterion that cannot be asserted apart. The plan's
own § *Why this grouping, not one task per defect* says the same; it is recorded here because it is the one
task above the ~20-step target.

## 3. Pack-defect sweep (the three classes that cost P29 a round)

1. **`-m 'not webengine'` on any command naming a webengine-marked suite.** `tests/test_lwc_bridge.py` and
   `tests/test_lwc_e2e_data.py` carry `@pytest.mark.webengine` cases and both are in P30-01's exit condition,
   so `P30-T1`'s `test_command` passes `-m 'not webengine'`; `P30-T3`'s command passes it too (its popout
   suites import the same modules). `P30-T2` and `P30-T4` name no marked suite and carry no flag.
2. **Baseline.** Section 1 above; no pack or recorded check uses `dcfdd60` or `3b92ce6`.
3. **`touches_files` inside the agent allowlist — the map is Plan-owned.** The plan's P30-04 *Files* line names
   `docs/codebase-map.md`, and its deliverable 4 asks the wave to add a P30 note. A Build Worker is denied
   write access to the map, so `P30-T4`'s `touches_files` is **`tests/test_p30_fence.py` only**. The P30 note
   the plan asked for **already exists** in the map (written by Plan: `docs/codebase-map.md:670-706`, including
   the six new suites, the no-existing-suite-edited statement and the "G7 is owner-run and not claimed"
   sentence). `P30-T4` therefore **asserts the note read-only** (`AC-P30-04-MAP`, `read_files` entry marked
   read-only) and edits nothing in `docs/`. This is the mechanical fix the handoff brief required, not a scope
   change: every fact the plan wanted recorded is asserted; the only difference is who writes it (Plan already
   did).

## 4. Translation notes (decisions carried verbatim into the packs)

- **Q118 = RESTORE is final.** `P30-T1`'s description and Do-not keep the cluster mounted and live; the delete
  arm (deleting `ChartControls`, the page factory or the mirror) is recorded as **declined**, never built.
- **The press seam.** Packed verbatim: the click applies the viewport action **locally** (`zoom(range, factor)` /
  `fitAndFollow()` — the keyboard path's functions) and only durable state (`router_mode`) returns; the
  published `zoom`/`reset_view` ops keep **no** page consumer, because `_replay_channels` re-sends the whole
  interaction log and a replayed viewport step would re-apply after every recovery. `handle_control`'s body and
  frozen return shape stay; `ENVELOPE_VERSION`, `CHANNELS` and the envelope are untouched.
- **`AC-D101.2` is in scope, both starting states plus the refusal path.** Both are driven in
  `interaction.controls.test.js` (`P30-T1-04`), and the production refusal report is the Python side
  (`P30-T1-07`).
  *One reading resolved explicitly, because the plan's own case text and its handler disagree:* the plan's
  refusal branch restores the pre-click value (`value ? "false" : "true"`), so with `aria-pressed="true"`
  pre-set (the constructed on→refused state, AP-P30-3) the attribute ends `"true"`; plan case (d) says
  "afterwards not `"true"`". The test asserts the invariant both readings satisfy and the AC actually states —
  **the attribute never equals the state the refused click requested** (off→refused: `"false"`, not `"true"`;
  on→refused: not `"false"`) — plus one report per refusal, and `P30-T1-05` asserts `syncControlState` drives
  the truthful mode state. A revert implementation and a drive-from-return implementation both pass; the
  pre-fix optimistic write fails both directions. No behaviour is added or removed by this translation.
- **`FI-P30-1` — no data-limit refusal is invented.** The no-visible-range press changes **no viewport**, emits
  **no** `zoomRefused`, reports **once**, and the shim's zoom return carries `refused: false`
  (`P30-T1-03`, `P30-T1-07`). TR-9 (`enter_zoom` from `ALARM_PLACING`) is the only refusal any P30 case drives.
- **The testability split / G7.** Four offscreen layers are packed as four evidence groups (DOM suite, real
  page-glue suite with its own stub — `chart.test.js` is never edited, the pytest bridge path, the four-way
  join with a negative case). **G7 is owner-run and not claimed:** it is named in `P30-T1`'s scope AC and
  Do-not, and in `P30-T4`'s `AC-P30-04-G7`; no suite asserts a painted page, a real `QWebEngineView` render, a
  click inside Chromium or a screenshot. This box cannot rasterise the page offscreen (measured, exit 134), so
  the graph never asks for it.
- **D104's per-site split.** Six sites are "words wrong, code right" → the words are fixed and the code is not
  touched (the dead re-host branch stays). `LwcChartView.release_resources` is the reverse: **the docstring is
  the contract**, so the body clears `bridge._channel_logs` (every bucket) and `_channel_queue`;
  `memory_bytes` is **untouched** and recorded as AR-P30-6's residual inside the release docstring and the test.
  The sweep's enumeration is **20 hits / 12 files = 12 allow-listed + 8 eliminated**, keyed by
  `(path, distinctive fragment)`, never by line number; `services/chart_model.py:273` is **not** allow-listed —
  it is a docstring rewrite with a positive assertion that the fragment is gone. `services/chart_model.py` is in
  `P30-T3`'s `touches_files` and in `P30-T4`'s recorded diff.
- **Records are build artefacts, not pytest.** `P30-T4` records `git diff --name-only 956f9f8` in
  `docs/build/results/P30-T4.json` (the P29 fence precedent: a git diff pinned inside a suite reddens every
  later phase). `P30-T1`/`P30-T3` assert only their own footprints and the named suites' identity, because
  `P30-T1` and `P30-T2` run in the same parallel wave and a phase-wide diff would see each other's edits.

## 5. Standing constraints carried

No new module, dependency, migration, settings key, wire-version bump or order path; D1–P29 unopened away from
the declared labels; sizes S/M only; `memory_bytes`' bucket set unchanged; `ChartControls` stays unconstructed
by design (Q118 restored the *page* surface); no live-TWS surface is touched by this phase.

## 6. Escalation run 2026-11-20 — two gate repairs (`task_manager_escalation`)

**State on entry:** `P30-T1`–`P30-T4` `done`, committed `9425555`; build `READY_FOR_REVIEW`; full suite
red on exactly one test. Zero open escalations routed to `TASK_MANAGER` (134 entries, all `addressed`);
no `ESCALATED_TO_PLAN`. Two size-S tasks added; **no phase deliverable re-scoped, no T1–T4 status or
footprint touched** (verified after the write: T1–T4 still `done`, byte-identical `touches_files`).

| Task | Purpose | Size | Deps | Frontier |
|---|---|---|---|---|
| `P30-T5` | Task A — the red test: restate the D101 docstring without the fence literal | S | `P30-T1` (done) | wave 1 |
| `P30-T6` | Task B — the DG116 clause compares to the phase base, not `HEAD` | S | — | wave 1 |

File-disjoint (`ui/lwc_view.py` vs `tests/test_d64_batch_gate.py`); they may open together.

### `P30-T5` — fix the wording, not the fence

- **The residue:** `tests/test_lwc_overlays.py::TestRendererBoundary::test_P6_T10_T12_no_out_of_scope_surface`
  failed with `out-of-scope residue: ["ui/lwc_view.py: 'QWebChannel'"]` — the only occurrence in the file
  is P30-T1's docstring at `ui/lwc_view.py:3109`.
- **The fence has no exception for this token.** `FORBIDDEN` is a plain substring list; only `pyqtgraph`
  gets the ESC-072 property-based path (`_uses_pyqtgraph`). So the literal is reworded, and the fence file
  is never edited (a stated AC + test).
- **Decided replacement (verbatim in the task description):** "The page cannot see the shim's answer — a
  bridge call returns before the page can read it — so the refusal is reported here — once — and the router
  op the shim publishes is what drives the page's pressed state." Both shipped facts survive: the page
  cannot read the shim's return value, and the refusal is reported in Python exactly once while the
  published router op drives the pressed state.
- **Footprint `ui/lwc_view.py` only**, so no new test file is written: the existing fence node is the
  RED→GREEN test, and the two remaining ACs are checked by reading the docstring and by two git diffs
  (docstring-only change; `tests/` untouched). `tests/test_p30_fence.py` is run read-only as a
  no-pinned-value-moved guard.

### `P30-T6` — the batch gate: phase base + declared allowlist

- **The defect, both directions.** The DG116 tail asserted `git status --porcelain -- tests/` was clean.
  That reddens on *any* uncommitted phase work (four verification runs in this session; every phase build
  hits it — P23, P25, P27, P29 all recorded it) and it is **blind to a committed** re-baseline, which is
  the breach DG116 actually forbids.
- **Derivation used, and why it is reliable.** The base is read from `docs/tasks/task-graph.json`
  `meta.baseline_commit` — a standing convention, verified in history: P28 `ef04c5a`, P29 `3b92ce6`,
  P30 `956f9f8`. The allowlist is the `tests/` subset of every task's `touches_files`. No hardcoded base
  and no hardcoded path list, so the clause keeps working in P31+ without edits; the base is additionally
  resolved with `rev-parse --verify <base>^{commit}` and required to be an ancestor of `HEAD`. If the key
  is ever absent the test fails naming it — it never falls back to `HEAD`.
- **Self-reference trap, caught before writing.** The gate file itself joins the phase delta once edited
  and once committed, so it must be in its own allowlist or the clause reddens on this very repair. It is,
  via `P30-T6`'s `touches_files` — which is the concrete reason the allowlist is *derived* and not a literal
  list.
- **Untracked files stay ignored**, as the old `??` filter did: a worker's in-progress new suite must not
  redden the gate mid-wave. `git diff` never shows untracked paths.
- **Kept byte-for-byte:** AC1's requirements pin, the whole DG114 block (seven source assertions + the two
  suite checks), the DG115 CROSSHAIR/Magnet block, and AC3's guard re-pin. Two new tests exercise the
  helpers in a throwaway `git init` repo (allowlisted edit admitted uncommitted **and** committed; an
  unlisted edit reported by name) and the derivation (equals an independent read of the graph; disjoint
  from the D19/D20 fixtures; phase-agnostic, so P31 does not edit the test).

### Companion assertions named, none duplicated

- **No second `status --porcelain -- tests/`** anywhere in `tests/` (repo-wide grep). `tests/test_d64_batch_gate.py:117`
  was the only site.
- **`tests/test_d65_residue.py:289-310` `GATE_RECORD`** mentions the old semantics in prose. It is a
  *historical, past-tense record of the P23 run*, and no test asserts its mechanism sentences (only
  `AC-D65.19`, "still OPEN", "live-TWS", "owned by P23-T26", "NOT claimed"). Left as the historical record
  — not a live pin, and rewriting it would falsify that run's log.
- **`tests/test_p20_proxy_guard.py:222`** and **`tests/test_d60_follow_offset.py:177`** pin
  `git diff HEAD -- docs/requirements/requirements.md` — the frozen *requirements input*, a different
  property, and one AC3 of the gate file deliberately asserts they keep it. Not copies of the `tests/`
  rule; neither is edited.

### Consequences recorded

- P30-T4's recorded delta (`AC-P30-04-RECORD`, a subset of the phase allowlist) grows by exactly
  `tests/test_d64_batch_gate.py` — the repair is a declared P30 task, so the listing stays a subset of the
  allowlist; the T4 result remains a historical artefact and is not rewritten.
- **Maintenance contract for future Task Managers:** keep `meta.baseline_commit` in the per-phase task
  graph (`check_tasks.py` does not enforce it; `tests/test_d64_batch_gate.py` now consumes it).
- Graph: 6 tasks; `check_tasks.py` **OK — 6 tasks validated**; `execution_graph.json` regenerated
  (`graph_struct_sha256 dd69188f1b9c305c2a76d990096816aac287d19d7baf2a1023b4ad925b6991f9`); metadata
  `"status": "READY_FOR_BUILD"`.

### Concurrent tree change observed mid-run — `docs/requirements/requirements.md`

- At run start (15:18) `git status --short` was **empty**. At 15:25, while this run was writing the graph,
  `docs/requirements/requirements.md` was modified **by another agent** (mtime 15:25; the edit closes
  RG-P7-1/RG-P7-2 and rewrites the Problem Statement / Current Tech Stack wording — 4 removed lines). It is
  **not this run's write** and was not reverted.
- **Consequence, recorded not worked around:** `tests/test_d64_batch_gate.py::test_p22_t5_ac1_history_intact`
  pins an additive-only `git diff HEAD` on that file, so it reds for exactly as long as that edit is
  uncommitted — a *different* clause from DG116 and outside this invocation's scope. Verified from the diff
  (4 removed lines), not by running pytest.
- **Hardening applied to both packs:** `P30-T5` and `P30-T6` assert "the only path **this task** writes",
  naming `requirements.md` as another agent's concurrent write that is neither reverted nor counted.
  `P30-T6`'s `test_command` names the DG116 node plus its two new tests, and its preservation AC asserts the
  other assertions are *present verbatim* and that AC3 passes — AC1's **runtime** status is recorded in the
  result, not asserted. AC1's assertion itself stays in the file unweakened and goes green once the
  requirements edit commits.
- If `requirements.md` is still uncommitted at review time, the full suite carries a second red — the same
  defect class as DG116 — and that would need its own (third) task. **Flagged, not silently fixed.**

## 7. Escalation run 2026-11-20 — protected-span hash re-pin (`task_manager_escalation`)

**State on entry:** `P30-T1`–`P30-T5` `done`, `P30-T6` in flight (batch-gate repair); one size-S task added
(`P30-T7`), **no existing task's status, footprint, AC or dependency touched** (verified after the write:
T1–T6 byte-identical, statuses as found). Zero open `TASK_MANAGER` escalations; no `ESCALATED_TO_PLAN`.

**The standing rule, recorded for future phases: a hash-pinned span re-pins whenever an owner-approved
requirements edit lands inside it.** `PROTECTED_SPAN_SHA256` (`tests/test_p14_cache_guard.py`,
`tests/test_p15_surfacing.py`) pins `requirements.md` from the `This is an existing repository.` marker to
`\n### D53 `; any owner-approved edit in that range moves the digest by construction, and the fence then
reddens on the digest assertion only while every marker/heading assertion still passes. That is the fence
working, not a defect — do not relax it. The rule is mechanical now: **the Requirements Analyst reports the
new digest with the edit** (this run: `4de9f5...`, previous `ffa6ff...`, boundaries unchanged, 531,306 →
532,623 bytes), so the Task Manager scopes a literal move and never re-derives the span.

| Task | Purpose | Size | Deps | Frontier |
|---|---|---|---|---|
| `P30-T7` | Re-pin the three digest literals + extend the audit comments | S | — | wave 1 |

File-disjoint from `P30-T6` (`tests/test_d64_batch_gate.py`), so they may run together.

### `P30-T7` — re-pin only, no structural change

- **Three literals, nothing else:** `tests/test_p14_cache_guard.py:84` (`PROTECTED_SPAN_SHA256`),
  `tests/test_p14_cache_guard.py:454` (`expected` inside `test_p28_t14_pin_matches_live_span`),
  `tests/test_p15_surfacing.py:77` (`PROTECTED_SPAN_SHA256`). The second literal exists so the live-digest
  guard cannot silently agree with a stale `PROTECTED_SPAN_SHA256` in the same file; all three move together.
- **Live digest independently re-verified this run** against the working tree
  (`sha256(span).hexdigest()` = `4de9f5...`, 532,623 bytes) rather than taken on trust, and the in-span
  diff was read (`@@ -416`, `@@ -561`, `@@ -582` in `requirements.md`) so the audit comments describe what
  actually moved: the marker sentence restated, the Current Tech Stack and Constraints rows rewritten to the
  shipped LWC-only end state (pyqtgraph removed), plus the D23.1 reconciliation. Note for the next reader:
  `pyqtgraph` still occurs elsewhere in the span — as preserved decision lineage, not as a stack claim — so
  no AC asserts its absence from the span.
- **Audit trail is a runtime requirement, not prose.** `test_p28_t14_repin_is_pin_only` reads the contiguous
  `#` block above the pin and requires `RG-P29-1`, `Q120`, `AC-D75.1`, `2026-11-20`, plus the "outside the
  pin" marker. So the new authorising-record paragraph is **appended** and the P28-T14 record is kept as
  history, never overwritten; blank separator lines stay `#`-prefixed or the block scan stops early. The
  comment must also never quote a `PROTECTED_SPAN_SHA256 = (` assignment, or the guard's regex would match
  the comment instead of the constant.
- **Pin-only is asserted two ways:** `test_p28_t14_repin_is_pin_only` proves the anchors and the
  exact-equality comparison survive and no containment/`startswith` form appears; a `manual` AC reads
  `git diff -U0 956f9f8 -- <the two files>` and requires every changed line to be a comment line or a digest
  literal. No new test was added to either fence file — that would itself be an assertion change.
- **`requirements.md` is another agent's concurrent write** (already modified at run start; `plan_notes.md`
  too). Neither is reverted or counted; `P30-T7`'s diff AC says so explicitly, and its test command names only
  the four guard nodes, so the unrelated `test_d64_batch_gate.py` AC1 red stays outside this task.
- **Result contract:** RED-before / GREEN-after for the four nodes recorded in
  `docs/build/results/P30-T7.json`; the three digest-only failures before, `4 passed` after.

### Graph state after this run

`check_tasks.py`: **OK — 7 tasks validated**, `execution_graph.json` regenerated
(`graph_struct_sha256 47f03a9f75b5970ea4a077ce6742818bfa356dd532ed7487c1b35cf7a7e5dadb`); metadata
`"status": "READY_FOR_BUILD"`, `meta.baseline_commit` still `956f9f8`. (`P30-T6` flipped to `done` while
this run was writing — `build_wave.py` advancing it, not this run's write.)
