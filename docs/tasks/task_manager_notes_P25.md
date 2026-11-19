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
