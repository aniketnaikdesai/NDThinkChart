# Task Manager Notes — Phase P18 (D57 viewport chevron + fresh framing)

## Decomposition (2026-11-05)
Plan P18 APPROVED (`docs/plan_review_P18.md`), `docs/plan.md` § Phase P18 `Status: READY_FOR_TASK_MANAGER`,
architecture Phase P18 in place. No open escalations routed to TASK_MANAGER; no
`feature_suggestions.md` approved items in scope. Q92–Q95 answered-owner-confirmed;
proceeded on them per the approval (no invention). Q95 override lineage (Q75
follow-memory stands, range-restore retired) is recorded in P18-T2's description
and requirement_ids so it survives in task context; P19 prefetch explicitly out.

Three plan phases → three tasks (phases map 1:1; no split needed — each phase is
already one independently verifiable AC cluster; sizes S/M/S per plan):
- **P18-T1 (S)** — chevron DOM + away-only visibility + goToRealtime click (D57.1;
  AC-D57.1/AC-D57.2/AC-D57.3). Owns `chart.html` + the chart.js
  visibility/click hunks. No dependencies.
- **P18-T2 (M)** — session/calendar-anchored fresh-frame computation + precedence
  + frame-application branch + y-coverage (D57.2;
  AC-D57.4/AC-D57.5/AC-D57.6). Owns `ui/lwc_view.py` + the chart.js frame
  branch. No dependencies (disjoint from T1's hunks; the shared `chart.js`
  in `touches_files` serializes the two waves — no logical edge added per the
  Dependency Mapping Rules, since neither task's correctness assumes the
  other's output).
- **P18-T3 (S)** — joint chevron×framing states + declared P11 churn
  (`tests/test_p11_fit_affordance.py` away-alone-hidden → away-only, per
  S-P18-1/AR-P18-4) + batch gate incl. history-intact grep + full suite green
  (D57.7). Test files only, no production edits. Depends on P18-T1 + P18-T2.

## Size note
No step-fit exception: T1 is S (one DOM element + predicate + click wiring + 4
scoped tests); T2 is M (cutoff computation over nine timeframes + precedence +
one page branch + 6 parametrized/scoped tests, fits the ~20-step target);
T3 is S (joint cases + churn rewrite + gate).

## `check_tasks.py`
Pass: `OK: 3 tasks validated, execution_graph.json written.` Three WARNs only —
each new test module in `touches_files` but not in `read_files`, explicitly
`ok if pure-output file` (new files cannot be pre-read; conventions come from
the existing suite reads in each pack).

## Flags for Requirements Analyst
None. No requirement or architecture ambiguity encountered; no escalation written.
`docs/requirements/requirements.md` untouched (Analyst-owned). D1–P17 not reopened
(the two P11 revisions are recorded with lineage, per plan/architecture).

## Rework scoping — ESC-102 / ESC-103 (2026-11-05, TASK_MANAGER escalations)

Both entries were read in full (observed vs expected vs suggested direction);
translation only, no re-diagnosis. No repo-wide exploration; one batched read of
the six assertion sites to pin `touches_files`/`read_files` line ranges.

- **P18-T1 kept as-is (done, chevron clean). P18-T2 substance untouched** — its own
  T24b probe-shape fix (`.from`/`.to` → frozen `.range`) and the BUILD-routed
  ESC-104 (trendline regression) / ESC-105 (chevron empty-chart guard) ride the
  forward cascade on the owning tasks. No AC/test/touches change on T1 or T2.
- **P18-T3 widened to own all 6 orphaned files** (the suggested-direction
  "widen P18-T3" branch; no new task id, phase structure unchanged):
  `tests/test_lwc_alarms.py` (L428), `tests/test_lwc_drawings.py` (L600),
  `tests/test_lwc_overlays.py` (L540), `tests/test_lwc_studies.py` (L362),
  `tests/test_lwc_time_parity.py` (L172 count + L210 unpack),
  `tests/test_p11_symbol_memory.py` (L77 restore block). No production file
  added — test-only rework, `touches_files` 2 → 8, each with a `read_files`
  range + one-clause why. `chart.js` follow-core read dropped (contracts carry
  it) to hold the ~8-file pack budget.
- **AC4/T34 (ESC-102):** the 4 renderer-boundary + 2 time-parity assertions are
  adjudicated fallout of the intended series-less frame directive riding the bar
  envelope (AR-P18-5 same-envelope ordering stands — the frame is NOT moved off
  the envelope). Re-pin excludes ops with `op == 'set_visible_range'` from the
  series-membership check and selects candles/volume ops by series; the
  renderer-exclusion intent is kept (any series-carrying foreign op still fails).
- **AC5/T35 (ESC-103):** the symbol-memory switch-back case is declared churn
  under S-P18-4 (range-restore retired, AC-D57.5/A165 lineage) — rewritten to
  fresh-frame-wins with the following encoding kept. The range-restore path is
  NOT restored (that would violate AC-D57.5/Q95(b)).
- **Size S → M** on P18-T3 (8 test files, two churn clusters + re-pin cluster +
  joint + gate; still fits the ~20-step target, no step-fit exception).
- **Dependencies unchanged** (`P18-T1`, `P18-T2`): T3 still gates on T2, so the
  BUILD-routed T2 fixes land first and the rework dispatches after — the forward
  cascade the preamble requires. No dispatch dep was blocking beyond that order.
- Honest linkage: T34/T35 state RED pre-exists as fallout/churn (mirroring the
  T32 phrasing) — no RED→GREEN language where no RED exists.

## `check_tasks.py` (re-run after rework)
Pass: `OK: 3 tasks validated, execution_graph.json written.` Three WARNs only —
the pre-existing pure-output new-file notes (T1 chevron, T2 framing, T3 joint);
all six newly-owned existing files are in `read_files`, so no new WARNs.
`docs/tasks/task-graph.json` metadata status `READY_FOR_BUILD` (rework scope).
