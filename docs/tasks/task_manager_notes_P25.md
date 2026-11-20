# Task Manager notes — Phase P25 (D67–D70: silent wrong chart data)

**Run:** fresh decomposition, 2026-11-19. **Baseline:** HEAD `08cade8` (the plan's baseline `94d6119` plus a
docs-only approval commit), tree clean. **Gate checked:** `docs/plan_review_P25.md` = `Status: APPROVED`;
`docs/plan.md` § *Phase P25* closes `Status: READY_FOR_TASK_MANAGER`. No `ESCALATED_TO_PLAN` open; no
`escalations.json` entry routed to `TASK_MANAGER`. Nothing was escalated to Plan and no requirements-ambiguity flag
was needed (Q119 is answered-by-default and the plan records the default).

## Decomposition — the plan's four waves → five tasks

| Plan wave | Task(s) | Size | Why this shape |
|---|---|---|---|
| P25-01 (D67) | **P25-T1** (page + bridge acceptance, marker rendering), **P25-T2** (base, covering rule, partial flag, prime suppression, view marker, suite) | M / M | Split for the context-pack budget, not for scope: P25-01's own file list is 13 files, and every touched file must also appear in the pack's `read_files` (≤ ~8). The split follows the plan's own ordering boundary — *the page must accept the op before anything emits it* (AP-P25-5 / AR-P25-3) — so the acceptance lands in T1 and the first emitter in T2. T1 and T2 are disjoint in files and coupled only by that ordering, recorded as a `DEPENDS_ON` edge (T2 ← T1) rather than left to file overlap. |
| P25-02 (D68) | **P25-T3** | S | As planned; touches no file T1/T2/T4 touches, so it runs in parallel with T1 and T2. |
| P25-03 (D69+D70) | **P25-T4** | M | As planned. Sized M rather than S because it spans five files (bridge, both page sources, both node test files) plus the parity suite, and the supersession rule is a real edit in `_stage`/`flush`. Depends on **T1 and T2**: it edits T1's two page sources and `ui/lwc_bridge.py`, and its directive ordering (`set_partial` last) is the op T2 emits. File overlap with T1 already forces sequencing; the logical edge is recorded too. |
| P25-04 (records) | **P25-T5** | S | As planned. Depends on all four, because it pins their constants and records the phase's whole diff. |

No task exceeds the ~20-step target; the ~32 exception cap and the size-exception note are not used. Sizes are S/M
only, as the plan requires.

**Wave picture:** W1 = P25-T1 + P25-T3 (parallel, disjoint files) · W2 = P25-T2 · W3 = P25-T4 · W4 = P25-T5.

## Facts carried into the packs (not re-derivable by a worker)

- **The measured `1 min` ceiling** — one `1 D` duration is accepted; `2 D` and `7 D` are rejected with error 321 —
  and **bars arrive oldest-first**. Both sit in P25-T2's `inputs` and back `AC-D67.3` and the replay-guard case; the
  wider wave windows (`30 D` / `1 min`) are *not* the priming path and belong to P26/P27 (AP-P25-4).
- **G1 (forming candle) and G2 (pop-out close with the main feed live) are owner-run gates**, named in P25-T5's
  delta-scope record and nowhere asserted as passed. Every other criterion in the phase is offscreen-assertable.
- **No new production module, dependency, migration or wire-version bump.** The one directive op rides the existing
  `{v: 1, ops}` envelope, and P25-T1 lands the page's acceptance before P25-T2 emits anything.
- **Frozen-then-changed sites are stated in each pack's `contracts`** (`push` keeps its observable contract and only
  records `first_ts`; `set_bars` keeps signature and emit contract and gains the adoption side effect; `detach`
  keeps its signature and changes only its release decision; `mergeRows` keeps signature and real-bar dispatch).

## Pack prose vs acceptance criteria

Each pack was checked against its own ACs (ESC-059/ESC-064 rule): no pack sentence tells the worker the opposite of
an AC, and every guarantee a pack states names the test that enforces it — e.g. the marker move/clear semantics are
T1-AC3, the "no prime when a base exists" claim is T2-AC4, the "one release per acquired hold" claim is T3-AC2 and
the "one replace per series" claim is T4-AC2. No guarantee lives only in a comment.

## Excluded by design (so they are not mistaken for gaps)

- `docs/requirements/**` is read-only for this phase; P25-T5 only *reads* `requirements.md` through its fence.
- `ui/main_window.py` is a one-line change (the clock wiring at session creation); every other main-window path is
  out of P25's scope.
- The base's *tail* coverage is deliberately not proved (FI-P25-1 / AP-P25-3): proving it needs a persisted capture
  time, i.e. a migration this phase forbids. Recorded in the plan; no task implies otherwise.

## P25-T1 test command correction (webengine abort)

P25-T1's `context.test_command` now runs the repo convention:

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_lwc_bridge.py -q -m "not webengine" && node --test chart_assets/lwc/
```

**Why:** `tests/test_lwc_bridge.py` contains one `@pytest.mark.webengine` test —
`test_host_loads_ndt_chart_offline` — which aborts the process (exit 134 / SIGABRT inside QtWebEngine) on this
macOS offscreen environment. The Orchestrator reproduced the abort on **both** the worker's tree and the committed
HEAD versions of `tests/test_lwc_bridge.py` and `ui/lwc_bridge.py`, so it is a pre-existing environment defect, not
a defect in P25-T1's code.

**Not a weakening of gated coverage:** `-m "not webengine"` is the repo's own convention (CI and every prior phase
use it; earlier results record these cases as pre-existing skips). The webengine test stays in the file unchanged
and still runs wherever WebEngine is functional. No acceptance criterion, test id, `touches_files` entry, dependency
or other task was changed; the graph is re-validated with `check_tasks.py`.

---

## Rework run — 2026-11-19 (ESC-126 / ESC-127 / ESC-128, owner-approved)

**Baseline:** the P25 build as recorded above (`P25-T1`…`P25-T5` all `done`, code review green, owner approved all
three findings on 2026-11-19). **Gate checked:** `docs/tasks/task-graph.json` still carries the five done tasks
unchanged; `docs/plan_review_P25.md` remains `APPROVED`; no phase structure was regenerated. Graph re-validated with
`check_tasks.py`: **8 tasks validated, `execution_graph.json` rewritten** for the new structural hash (the next
`advance` needs it).

### What was added — three S tasks, one wave

| Task | Escalation | Scope | Size | Depends on | Touches |
|---|---|---|---|---|---|
| **P25-T6** | **ESC-126** (should-fix, TASK_MANAGER) | Remove the dead import-time `QApplication` from `tests/test_p7_w4_streaming.py:39` and `tests/test_p7_w4_deferral.py:32`, give each a session-scoped autouse `_qt_app` fixture (Q-79's pattern), and add `tests/test_qt_app_import_invariant.py`: tree-wide module-scope AST scan + the escalated explicit collection order + a collected-case guard | S | none | the two suites + the new invariant suite |
| **P25-T7** | **ESC-127** (nice-to-have, BUILD) | One candle whitespace predicate — `open is None or close is None` — stated once per side, both Python branches, `chart.js` delegating to the exported `envelope.js` predicate; discriminating parity fixtures | S | **P25-T4** | `ui/lwc_bridge.py`, `chart_assets/lwc/{envelope,chart}.js`, `envelope.test.js`, `tests/test_d69_d70_bridge_contract.py` |
| **P25-T8** | **ESC-128** (nice-to-have, TASK_MANAGER) | One `usage.md` bullet for the amber partial marker on a forming week/month candle + a distinguishing half-sentence in the Event Markers note | S | **P25-T2** | `usage.md`, `tests/test_p25_usage_doc.py` |

No size exception was used (rule cap and ~32-step exception both unused; each task is ~5–10 steps: one or two file
edits, one test file, one verification run). No task exceeds the file count or the step target, so nothing was split
further; all three are disjoint in files and run in **one wave**.

**Edges, and why they are logical rather than file-level:**
- `P25-T7 → P25-T4` is recorded even though T4 is already `done`: T7 does not merely overlap T4's files, it *assumes
  T4's fold* (the skip-on-replace / delete-on-upsert behaviour and the AC4 parity harness). The edge documents the
  assumption for any later re-read of the graph.
- `P25-T8 → P25-T2` likewise: the doc bullet states T2's delivered marker semantics (AC-D67.1/2, the rollover
  clear). It touches no file T2 touched.
- `P25-T6` has no edge: it changes only test scaffolding and the import invariant; it assumes no phase contract. It
  is not ordered after T4/T2 even though it edits files those tasks' exit conditions run — that is regression
  coverage, not an assumed interface.

### ESC-127 — rule chosen: **the page's stricter reading** (`open is None OR close is None`)

Recorded here because the escalation left the direction to the implementer:

- A candle needs **both** endpoints to be a bar; Python's close-only test would reconstruct
  `(ts, None, 2.0, 0.5, 1.0)` — a malformed bar the page refuses to draw, i.e. exactly the "silently wrong data"
  class D70 exists to close.
- `AC-D70.2` makes **the page's merge the reference** the Python reconstruction must equal element-for-element; when
  they disagree, the page wins by construction of the criterion, and `AC-D70.1`'s "a None-close row" is a subset of
  the any-endpoint rule, not a competing rule.
- No emitted shape changes: `ui/lwc_view.py::build_series_ops` nulls all four value slots together, so the stricter
  predicate only rejects rows no producer can emit today (the escalation says the same).

`P25-T7`'s parity fixture therefore carries **both** the ESC-127 op `{open: 1, close: None, high: 2.0, low: 0.5}`
(the shape the prompt names) **and** its mirror `{open: None, close: 1.0, …}` — the mirror is the row that actually
separates the two sides today, and the escalation's own measurement is what establishes that. The task's AC1 makes
"one predicate per side" literal: `chart.js` may not keep a second copy, it delegates to
`LwEnvelope.isWhitespaceRow` (the file already uses `window.LwEnvelope`, and `chart.html` loads `envelope.js`
first).

### ESC-128 — route chosen: **an explicit one-file doc task**, not `pending_doc_sync.md`

`docs/pending_doc_sync.md` **does not exist** (Plan folded nothing this phase — the P25 review notes record it as
absent), and the ownership table gives that file to Plan (folds) and quick (appends); Task Manager is not an owner
and must not create an unowned coordination file. Handing the bullet to "the next Plan drafting pass" would leave a
user-visible affordance undocumented at phase close — the finding would simply re-open. A single S task editing
`usage.md` (plus one small content test) is the cheapest route that lands the wording **inside this phase**,
is verifiable by test rather than by promise, and implies no production change. `doc_required: true` is set so the
Code Reviewer's doc check applies.

### Invariants preserved

- `P25-T1`…`P25-T5`: substance, statuses, ACs, tests and `touches_files` untouched. `P25-T6` adds an invariant
  suite rather than editing `tests/test_p25_fence.py`, so T5's suite stays the frozen phase fence.
- `tests/test_lwc_render_smoke.py` is **not** in any `touches_files` (P28/R-07 territory); `P25-T6` reads it only
  to reproduce the escalated order and its pack says "do not change".
- No new production module, dependency, migration, wire version or op shape; no D67–D70 behaviour reopened. Sizes
  S only, as required.
- Pack prose vs ACs checked per task: every guarantee a pack states names its enforcing test — T6's invariant is
  AC2's AST scan and AC3's collection regression, T7's "one predicate" is AC1's source check and its behaviour is
  AC2/AC3, T8's wording requirements are AC1/AC2. No guarantee lives only in a comment.
- Each of the three escalations is left `open` in `docs/code_review/escalations.json` — that file is Code Reviewer's;
  the status flip is its call after verification.
