# Task Manager notes — Phase P26 (D71–D76)

**Run:** 2026-11-19 · fresh_graph · baseline `629be4a`, docs committed at `4975efa`
**Inputs read:** `docs/plan.md` § *Phase P26* (`Status: READY_FOR_TASK_MANAGER`), `docs/architecture.md`
§ *Phase P26* (`S-P26-1`…`S-P26-7`, *Frozen Interfaces*, AR-P26-1…AR-P26-8),
`docs/requirements/requirements.md` § *Phase P26* (`AC-D71.1`–`AC-D76.3`, A225–A229, R165–R169, G3/G4),
`docs/codebase-map.md` (the P26 note), `docs/code-review` escalations (no open `TASK_MANAGER` entry),
`docs/memory.md`.
**Outputs:** `docs/tasks/task-graph.json`, `docs/tasks/execution_graph.json` (`check_tasks.py`: *OK — 4 tasks
validated*), this file, and one requirements flag in `docs/requirements/open_questions.md` (see below).

## Graph

| Task | Size | Depends on | Scope |
|---|---|---|---|
| **P26-T1** | M | — | D71: union pre-check + one replay transaction + per-type retire resolver + epoch-guarded deferral (`ibkr/pacing.py`, `ibkr/subscription_manager.py`, `ui/main_window.py`) |
| **P26-T2** | M | P26-T1 | D72 + D75 + D76 as ONE lifecycle: parked state and settle rule, coalesce-resume, bounded readiness episode (`ui/ticker_session.py`, `ui/main_window.py`) |
| **P26-T3** | S | P26-T2 | D73 + D74: one chunk-surrender helper for both retry paths, generation-windowed cancel tags, per-wave failure set (`ui/ticker_session.py`, `ui/main_window.py`) |
| **P26-T4** | S | P26-T1, P26-T2, P26-T3 | Fence suite, delta-scope record, G3/G4 named (`tests/test_p26_fence.py`) |

**Strictly sequential.** The plan's AP-P26-8 is followed exactly: `ui/ticker_session.py` and
`ui/main_window.py` carry waves 01–03, so `touches_files` overlap serialises them in that order and there is
no parallel branch to widen. P26-T4 depends on all three (it records their combined diff) and writes no
production file.

## Sizing

- **P26-T1 (M, 5 AC / 5 tests / 3 production files).** Deliberate bundle: the plan's four deliverables are one
  contract — a union budget is useless without the transaction, and the transaction needs the retire resolvers
  to unwind. Splitting it would make a task whose own AC cannot be satisfied (memory, D44: an AC that depends
  on a later task is a graph defect). Honest step count ≈ 14 (three file edit clusters + one new suite of six
  cases + the named regression run) — inside the ~20 target.
- **P26-T2 (M, 8 AC / 8 tests / 2 production files).** **Bundle-of-record:** D72/D75/D76 are one state
  machine — the park is what the coalesce gate must see, and the readiness episode is the same watchdog-arming
  rule. Splitting would break the single-owner property of `_wave_parked` (two tasks editing the same flag in
  the same file, serialised anyway, paying startup twice). Step count ≈ 18–20 (four session seams + four window
  seams, seven suite cases, two regression runs) — at but not over the ~20 target, so **no size exception is
  claimed**; recorded here so a later reviewer does not read M + 8 ACs as an over-size.
- **P26-T3 (S):** mechanical extraction + bookkeeping, 4 AC / 4 tests, two files.
- **P26-T4 (S):** one new test file plus a record; no production file.

## Facts carried into the packs (do not re-derive)

1. **The 20 ms generic gate** is `1 / settings.MAX_REQ_PER_SEC` with `MAX_REQ_PER_SEC = 50`. **RT sends never
   touch it**, so `generic_n = len(pending) − rt_n` is exact — no per-type enumeration is needed.
2. **`S0_TICKS` is declared and included in the window's `include_types` but nothing in production registers
   under it**, so it contributes nothing to the union and the arithmetic stays correct if a hook is ever added.
3. **`SubscriptionManager.subscribe`'s signature is frozen** (P26-T1 pack, contract) and **four test doubles**
   carry the five-argument shape — this is why retirement is a per-type resolver, never a `subscribe(cancel=…)`
   keyword.
4. **The deferral keeps its `QTimer.singleShot(int(e.wait_seconds * 1000), …)` shape** — pinned by
   `test_p7_t07_t13_replay_all_defers_via_singleshot` (P26-T1 read_files, read-only).
5. **`_finalize_stranded_history_wave` is not changed.** The parked guard lives in
   `_on_session_history_wave_timeout` ONLY, so a disconnect still strands the wave and drops the parked queue
   (Journey 69's edge; P26-T2-AC8).
6. Hard constraints restated per wave in each description: **sizes S/M only, no new module/dependency/migration
   /settings constant, D1–P25 read-only.**

## Requirements flag (not an escalation)

- **`docs/requirements/open_questions.md` Q120** — appended (append-only, that file's single Task-Manager
  exception) for `AC-D75.1` vs `AC-D72.3`: the two clauses cannot both hold literally. Plan recorded the
  reconciliation as `AP-P26-5` / `FI-P26-1`; the graph implements that reading (the identical-triple reload
  **resumes** the queue, no cancel, no re-plan, no duplicate). The flag is **non-blocking** — every P26 test is
  satisfiable under the adopted reading — and it is logged there, not here, because Requirements Analyst reads
  that file and not this one.
- **`FI-P26-2` and `FI-P26-3` are carried as scope boundaries, not open items.** A parked wave still receives the
  D54 T0+10 s verdict (P26 does not touch `AC-D54.*`), and the parked queue does not survive a session teardown
  (the planner re-derives the remainder from the persisted cache). Neither is a Task-Manager decision; both are
  stated in the plan and must not be re-litigated in a pack.

## No escalation to Plan

No architectural choice was missing: `S-P26-1`…`S-P26-7` settle the union-budget model, the batch reservation
shape, the retire-resolver mechanism, the parked-state surface, the watchdog arming rule, the ledger window and
the coalesce-resume. `ESCALATED_TO_PLAN` is **not** set; the graph is `READY_FOR_BUILD`.
