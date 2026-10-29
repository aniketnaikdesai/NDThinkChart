# Task Manager Notes — Phase P11 (D51 follow-live viewport)

## Decomposition (2026-10-29)

Plan `docs/plan.md` § Phase P11 defines 4 ordered waves (S/M/S/S) + architecture
S-P11-1…S-P11-5. Decomposed into 6 tasks (S/M/S/S/S/S):

| Task | Wave | AC | Size | Why this split |
|---|---|---|---|---|
| P11-T1 | W1 | AC-D51.1 | S | Follow-state definition + repro probes (S-P11-1); foundation every later task assumes |
| P11-T2 | W2a | AC-D51.2 | M | No-yank live path (S-P11-2); multi-file behaviour change, kept whole per step budget |
| P11-T3 | W2b | AC-D51.3 | S | Fit/reset + affordance (S-P11-4); separate AC cluster from T2, depends on T2 (affordance needs no-yank semantics) |
| P11-T4 | W3a | AC-D51.4 | S | Per-symbol store (S-P11-5); separate AC cluster, Python-side |
| P11-T5 | W3b | AC-D51.5 | S | Same/new directive (S-P11-3) + zero-bar Fit edge; separate AC cluster, depends on T4 (store + report channel) |
| P11-T6 | W4 | all | S | Batch gate (verification-only; touches only its result file per worker_selfcheck rule) |

W2 and W3 were each split because "done" for the wave required two distinct AC
clusters (sizing rule: one cluster per task). No step-fit exception needed —
all tasks target ~20 steps; the single M (T2) is the bounded live-path gating.

## Dependency notes

- DEPENDS_ON edges are logical (assumed contracts), not file overlap: T2/T3/T5
  all touch `chart_assets/lwc/chart.js` and serialize on it, but T3→T2 exists
  because the affordance's show condition assumes no-yank behaviour, and
  T5→T4 because the continuity directive assumes the store + report channel.
- T4→T1 only (range probes); it does not assume T2/T3 behaviour.
- No open TASK_MANAGER escalations at graph time (ESC-087/090 addressed).

## Flags

- None. No architecture gap (S-P11-1…S-P11-5 decided; plan Flagged Issues: none).
  Noskips/xfails permitted — stated in T6 AC2.
- `doc_required: false` on all tasks: no user-facing doc change (usage docs
  untouched per P11 scope; affordance reuses the D3 control idiom, AP-P11-4).
- New test files appear in `touches_files` but not `read_files` (they do not
  exist at graph time) — the six check_tasks.py WARNs are the tolerated
  pure-output case, same as the P10 precedent.

## ESC-093 rework (2026-10-29; status: open — Code Reviewer closes on re-verification)

- Root cause (per escalation): P11-T2's `touches_files` omitted
  `chart_assets/lwc/chart.test.js`, but the dispatched pack required the worker
  to edit exactly that file (T12 post-fix assertion + T23 fallback pin), and the
  task's own `test_command` runs it. Green results from waves 198/202 were
  unconsolidatable on the footprint mismatch.
- Change (P11-T2 only; every other task byte-identical):
  1. `touches_files` += `chart_assets/lwc/chart.test.js` — covers the edit the
     pack already required; pack-only change, no code edit, no BUILD rework.
  2. Context pack `read_files` 338-373 `why` flipped from
     `read-only: ... do not duplicate its fixtures` to an explicit edit site
     (`T2 owns this hunk: T12 replacement + T23 pin`) — a file in
     `touches_files` must not be marked read-only (edit-site pinning rule).
- Note on invocation wording: the dispatch said "context pack ... (read-only
  reference + why)", but a read-only marking is exactly what caused the
  mismatch — the escalation's suggested direction (cover the edited file in
  `touches_files`) is what unblocks re-consolidation, so that was applied.
- `check_tasks.py`: OK (6 tasks validated; only the six pre-existing
  pure-output WARNs). Metadata stays `READY_FOR_BUILD`; P11-T2 `status` left
  `blocked` for `build_wave.py`/Orchestrator to advance.
- ESC-093 NOT marked addressed here — left `open` for Code Reviewer to close.
