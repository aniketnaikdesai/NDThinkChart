# Plan Review — Phase P15 (D54 10-second target on load chart)

Pass type: final_pass (gate was open at first invocation — P14 `REVIEW_COMPLETE` newer than
the build terminal status — so no provisional review exists; full Validation Method run once,
then finalized).

Status: APPROVED

Decision: Phase P15 is APPROVED for build. `docs/plan.md` § Phase P15 now carries
`Status: READY_FOR_TASK_MANAGER`.

- Coverage: every P15 input traced — D54.1→W1, D54.2→W2, D54.3/D54.4→W3; Journey 47
  (render / background / surfacing steps plus all six edges: 9.9 s, zero-bar,
  disconnect-wins, coalesced-T0, mode-switch-re-T0, exact-boundary) across W1–W3;
  A145→S-P15-1, A146→S-P15-4, A147→all waves, A148/Q81–Q83→W1/W2/W3 on defaults
  (a)/(a)/D53+AC-D16.4; R108→AR-P15-1, R109→AR-P15-2, DG101→all waves, Finding-1/TWS
  boundary→S-P15-4 read-only. No expectation narrowed or reinterpreted; A148 target
  (not cap) reading preserved.
- Completeness: stack (LWC-only + Qt single-shot expiry + offscreen clock-control harness,
  no new dependency/module/store), components (expiry hook / wave-hook interplay /
  expiry surfacing / read-only session, planner, cache, order-absence rows), data model
  (in-memory wave state, `bars` PK, additive tables), integrations (IBKR read-only, SQLite,
  Qt timer), non-functional (correctness / honesty / performance / suite-green gate),
  risks (AR-P15-1…AR-P15-4 with mitigations). Every `[new in P15]` decision carries
  rationale plus a rejected alternative.
- Consistency: expiry is hook-only — no cancel path, no lifecycle reshape, D53 referenced
  (contracts read, wording unrewritten), watchdog/pacing/request-shape/port/renderer/`bars`
  schema untouched, zero order interaction. Single-sided T0+10.0 s-complete bound and
  disconnect-wins / re-anchor / coalesced-keep seams agree across plan and architecture.
- Plan quality: three milestone waves (M/M/S), ordered W1→W3, one commit per wave,
  repro-first red→green cases, no fine-grained task breakdown, no task graph, no per-task
  tests. Scope guards explicit: Finding 1 / TWS-side causes and watchdog retuning out,
  D53 not reopened, D1–P14 not reopened.
- Readiness: Task Manager can decompose W1–W3 without inventing architecture — T0 anchor,
  single-shot mechanism (AP-P15-3), verdict semantics, lifecycle seams, and surfacing
  surface are all pinned with offscreen-measurable acceptance.
- Existing-repo compliance: pass — Codebase Summary substantive (load_chart T0/coalesced
  contract, D53 indicator ownership, session wave state, finalize paths with verbatim
  shortfall, planner/cache, LWC-only stack note, all validated against source); stack
  unchanged relative to the as-built LWC-only tree (P6-T13, owner-approved); every
  component/data-model/integration item labelled `[existing]` or `[new in P15]`;
  additive-only, no migration; proposal entities match the summary.
- Frozen interfaces: pass — all frozen entries `[existing]` and unmodified this phase
  (nothing under construction frozen); `load_chart`, `set_backfill_state`,
  `_is_cache_current` carry verbatim signatures verified against `ui/main_window.py`;
  shortfall wording and `"Backfill: idle"` quoted verbatim and verified in source;
  wave-lifecycle/planner/cache carry-forwards and order-absence match § Phase P14;
  owners (`ui/main_window.py`, `ui/ticker_session.py`) resolve in `docs/codebase-map.md`;
  no duplicates. Consumes-but-unmodified D53 contracts (`set_backfill_state` /
  `clear_backfill_indicator` / `_is_cache_current`) all present.
- Map quality: pass — P15 annotation present (no new module, files-in-place list),
  skeleton current (246 code files), touched modules resolve, no stale entries, status
  labels current, index-sized.
- Doc sync: pass — `docs/pending_doc_sync.md` absent (nothing unapplied).

Required changes: none. Requirements escalations: none (Q81–Q83 proceed on logged
defaults per A148; all `PLAN`-routed escalations `addressed`, none open).

Task Manager readiness: READY — Task Manager may proceed on § Phase P15.
