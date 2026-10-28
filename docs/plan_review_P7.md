# Plan Review — Phase P7 (data-path batch: historical backfill correct + fast, streaming correct)

> Pass type: final (delta check only vs the provisional review of 2026-10-27).
> Proposal: `docs/plan.md` § *Phase P7* + `docs/architecture.md` § *Phase P7 — data-path batch*.
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, unchanged since the provisional pass).

**Status: APPROVED**

**Decision:** APPROVED — the delta check is clean on both axes, so the provisional validation stands and the
phase is activated. `docs/plan.md` § *Phase P7* now ends `Status: READY_FOR_TASK_MANAGER`.

- **Coverage:** no change — ESC-075…079 all still `open`; the traceability table still addresses every one; nothing narrowed. Pass.
- **Completeness:** no change — stack, components, data model, integrations, interfaces, NFR, risks, Codebase Summary all intact. Pass.
- **Consistency:** no change — no new contradictions; P7 still references none of the P6-deleted renderer modules. Pass.
- **Plan quality:** no change — 4 ordered waves (M/S/S/M), coarse milestones, no task breakdown. Pass.
- **Readiness:** Task Manager can build a task graph without inventing architecture; generate P7 packs from the post-T13 tree. Pass.
- **Existing-repo compliance:** P6-T13's removal is committed as `6e35b27` (owner-approved, owner-waived, oracle retired per `docs/build/gate_P6_T13.md`); `ui/ticker_session.py` + `ui/main_window.py` wave internals verified present post-removal (`_pending_bars`, `_finalize_history_wave`, `_wave_plan_queue`, `_prime_req_id`); P7's Codebase Summary matches the post-T13 tree; frozen seam resolves LWC-only. Pass.
- **Frozen interfaces:** no change — all rows still `[existing]` and unmodified by every P7 wave; editorial only: the seam row now carries the verbatim `create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView` signature (verified in `ui/chart_view.py:121`). Pass.
- **Map quality:** P7 adds no modules so no map change is required; carried nit (not a finding): `docs/codebase-map.md` is Plan-owned and outside Validator writables, so its header pointer still reads post-P6/pre-P7 — Plan refreshes it next draft. Pass.
- **Doc sync:** `docs/pending_doc_sync.md` absent. Pass.

**Delta check detail (final pass only):**
1. **Requirements drift:** none. `requirements.md` last modified 2026-10-26 (`1df6668`), before the provisional review (2026-10-27); `Status: READY_FOR_PLAN` intact; no criterion touched.
2. **Review invalidations:** none. No `routed_to: PLAN` escalation was addressed since the provisional pass (ESC-079 still `open`; ESC-075…078 still `open` BUILD). P6-T13's addressed outcome (deletion `6e35b27`) was conflict-checked against P7's edit surface: P7 waves touch `ui/ticker_session.py` + `ui/main_window.py` data-path internals (all present) and freeze — never edit — the renderer seam; no `[revises]`/`[extends]` label depends on the old renderer. Clean.

**Activation performed:** flipped `docs/plan.md` § *Phase P7* to `Status: READY_FOR_TASK_MANAGER`; appended RG-P7-1 (`AC-D16.8` restatement → `ESCALATED_TO_REQUIREMENTS`) and RG-P7-2 (stack-doc staleness → analyst-owned, non-blocking) to `docs/plan_notes.md`; added the verbatim seam signature to `docs/architecture.md` (editorial, no new decision).

**Requirements Escalations:** RG-P7-1 filed in `docs/plan_notes.md` (`ESCALATED_TO_REQUIREMENTS`) — non-blocking for the build: P7 plans the satisfiable multi-load reading (S-P7-1) and Flagged Issue 1 records the restatement request. RG-P7-2 recorded `open`, non-blocking.

**Task Manager Readiness:** ready — proceed; build P7 packs from the post-T13 tree.

## Delta note 2026-10-28 (Q-51 doc-consolidation — approval preserved)

This section is appended; the approval record above is untouched and `Status: APPROVED` stands.
`AC-D16.8` stays open Requirements Analyst debt (RG-P7-1); nothing here restates requirements.

- **Per-load cap = maximum, never target (S-P7-1 / P7-W1 reading, clarified):** a single chart load issues
  at most `min(requests needed, floor(B/4))` historical requests (`B` = current `MAX_HISTORICAL_PER_600S`);
  the cap never creates work to fill itself. Worked examples at `floor(B/4) = 25`: need **1** -> issue **1**;
  need **10** -> issue at most **10**; need **40** -> issue at most **25** this load, persist completed chunks,
  resume the rest on later loads (persist-and-resume / oldest-first, S-P7-2). No forced chunking, no
  automatic spend of reserved slots, no promise of immediate full history.
- **Per-load defined:** one chart-load wave for one symbol + timeframe + ext-hours mode. A same-chart reload
  coalesces into the running wave and shares its allocation (AP-P7-2); a cancelled slot is refunded only
  when its request never reached TWS (AP-P7-3 / AR-P7-4).
- **Budget-number reconciliation (plan Flagged Issue 3):** the tree carries `MAX_HISTORICAL_PER_600S = 100`
  (`config/settings.py`, owner-set per the source comment); ESC-075's "50-slot" text is stale prose. The
  operative value is **100 per the source**, and the invariant is fraction-based so it holds under either
  value — both figures are named here, none silently chosen.
- **User guides (changeset 4, same task):** `usage.md` is the canonical full guide (LWC-only engine, no
  `NDT_CHART_ENGINE` opt-in, port/paper-live reconciliation, as-of dated); `USAGE.txt` is a short
  pointer/quick-start. Packaging/`NDThinkChart.spec` bundle no plain-text consumer (checked 2026-10-28),
  so the pointer form is safe. No source/test file changed.
