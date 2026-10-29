# Plan Review — Phase P13 (D49 pop-out robustness + D49.6 timezone handoff, Batch 24)

**Review Status:** initial_validation (full pass)
**Phase:** P13 — `docs/plan.md` § *Phase P13*, `docs/architecture.md` § *Phase P13 — D49 pop-out robustness*
**Pass type:** initial_validation (full Validation Method, steps 1–10)
**Date:** 2026-10-29

## Decision

`Status: APPROVED` — the P13 material passes; the phase gate is open (P12 `REVIEW_COMPLETE`) and the section is activated.

## Validation (one line per step)

- **Coverage:** every D49 expectation is traced — D49.1–D49.7 / `AC-D49.1`–`AC-D49.7` / Journey 42 / A121–A126+A133/A134 / R96–R98/R102 each map to an architecture section and a wave (P13-W1…W8); nothing narrowed or reinterpreted; D49.5's conditional wave is the requirements-specified gated outcome (A126/Q66), not a gap.
- **Completeness:** stack, components + responsibilities + relationships, data model, integrations, interfaces, non-functional (perf/correctness/observability/stability gate), risks AR-P13-1…AR-P13-4 with severity + mitigation, and a substantive Codebase Summary are all present; every S-P13 decision carries rationale + rejected alternative.
- **Consistency:** no contradictions — restore reuses the `AC-D16.8`/`AC-D16.9` machinery (no second fetch path), cleanup ordering answers R97, the probe-record gate answers R98, the A134 fallback answers R102; waves depend only on architecture defined in the same section.
- **Plan quality:** 8 ordered waves (S/M only), each with goal, covered inputs, acceptance criteria and validation method; one commit per wave in order; repro-first with the W4 pin-first documented exception; no task-level breakdown, no dependency graph, no per-task tests.
- **Readiness:** Task Manager can build the graph without inventing architecture — the only deferred detail (AP-P13-3 key type) is explicitly implementation-level against a fixed owner set + idempotence property; AP-P13-1 visual gate is owner-confirmed (Q64).
- **Existing-repo compliance:** pass — Codebase Summary inventories the D49 surface with `[existing]` labels against source; stack stays PyQt6 + LWC-only (hard constraint, no replacement); all System/Data/Integration items labelled; additive-only (sole schema touch is one additive `popouts.tz_offset` column); `[existing]` items consumed match the Summary.
- **Frozen interfaces:** pass — 6 entries with verbatim contracts (`create_chart_view` signature, `chart_engine_failure_message` signature + return shape, `detach_view` comprehension, `BarCache` read/write API, planner contracts, order-code absence); all `[existing]` and unmodified this phase (the `[new]` tz column is correctly absent); owning modules resolve in `docs/codebase-map.md`; no duplicates.
- **Map quality:** pass — P13 note present (skeleton re-run, 231 files, no new module, annotations carry forward); named modules (`ui/main_window.py`, `ui/popout_window.py`, `ui/ticker_session.py`, `data/popout_store.py`) exist in the skeleton; no stale entries; index-sized.
- **Doc sync:** pass — `docs/pending_doc_sync.md` absent, nothing to fold.
- **Gate/escalations:** P12 `REVIEW_COMPLETE` (`docs/code_review/review_log_P12.md`) is newer than the build terminal `Status: READY_FOR_REVIEW`; zero `open` escalations (none routed to PLAN); requirements still carry `Status: READY_FOR_PLAN` with D49 unchanged.

## Activation

- `docs/plan.md` § *Phase P13* status flipped `READY_FOR_VALIDATION` → `Status: READY_FOR_TASK_MANAGER` (line 3836). Canonical files otherwise untouched (`architecture.md` § *Phase P13* already carries the labelled `[new in P13]` decisions; no `[revises]`/`[extends]` to reconcile; `plan_notes.md` unmodified — Flagged Issues: None, no requirements gap).

## Final Decision

`Status: APPROVED`
