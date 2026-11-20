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
