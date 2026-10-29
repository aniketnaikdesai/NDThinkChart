# Task Manager Notes — P13 (D49 pop-out robustness + D49.6 timezone handoff)

## Graph shape
- 9 tasks, strict chain T1→T2→…→T9 per `docs/plan.md` Phase P13 ("waves run in order; a later wave depends on all earlier ones").
- W1 (M, T1) and W2 (M, T2) touch disjoint prod files (`ui/main_window.py` vs `ui/popout_window.py`) but are still chained: the plan's wave order is a build-order fact, and T2's attach is exercised by T1's restored windows.
- W7 split into T7 (create threading) + T8 (persist/restore/fallback): one task covering 3 prod files plus migration plus 2 test files would exceed the ~20-step target; the split keeps each task independently verifiable (creation offset vs round-trip/fallback) with T8 depending on T7 (same `ui/main_window.py` footprint plus logical threading-before-persist).
- All sizes S/M (no L, no size exception needed). No `needs_graphify` (all relationships captured in packs).

## W6 conditional (record-gated, not a gap)
- P13-T6 branches deterministically on the P13-T5 record verdict: fix-and-prove vs verified-close. Both branches are fully specified in the ACs and T61 reads the verdict file rather than skipping, so the no-skips/xfails rule holds in either outcome. A T6 diff with no probe record fails review (R98) — recorded in the task description.

## Escalations / ambiguity
- No open `TASK_MANAGER` escalations in `docs/code_review/escalations.json` (all addressed); nothing to translate.
- No undecided architecture: S-P13-1…S-P13-6 settle every mechanism (ensure step, flag semantics with AP-P13-2's hold-acquired definition, ESC-070 wording reuse, pin-then-dedupe, verify-first gate, additive column + A134 fallback). No escalation to Plan; `requirements.md` ambiguity: none (D49.6 fully derivable per requirements).
- Frozen-interface compliance: `detach_view`, `create_chart_view`, `chart_engine_failure_message`, `BarCache`/planner APIs are called-not-modified (read-only in packs); `sync_drawings_to_views` call-site multiplicity is the S-P13-4 sanctioned change; no order-code tokens appear anywhere (`placeOrder`/`cancelOrder`/`reqGlobalCancel` absent; T9 scans for them).

## Qt-free boundary
- `data/` + `services/` appear in packs as read-only contracts only; no task modifies them except the additive `popouts.tz_offset` column in `data/popout_store.py` (schema, not logic — same additive-migration precedent as D24.9). No new module, no new dependency, no `touches_files` outside the P13 surface.
