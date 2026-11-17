# Plan Review — Phase P22 (Toolbar / timezone-toggle / crosshair / time-axis fixes, D61–D64)

**Status: APPROVED**

**Pass type:** final_pass (gate was already open at first invocation — no provisional
review exists for this phase — so the full Validation Method was run, then finalized).

**Decision:** APPROVED. `docs/plan.md` § *Phase P22* flipped to
`Status: READY_FOR_TASK_MANAGER`. Task Manager may proceed.

**Phase gate:** open — `docs/code_review/review_log_P21.md` carries
`Status: REVIEW_COMPLETE` (P21 batch gate green: full offscreen suite 1518
passed/3 skipped, node page-core 105 pass; the 2 history-guard reds are recorded
there as P22's gate concern, and P22's P22-4/`AC-D64.3` gate is the adjudication
point) newer than the build log's terminal `Status: READY_FOR_REVIEW` (waves 316–317
all done). P21's follow-offset/viewport contracts are read-only inputs to P22
(P22-2 exit condition keeps the P21 viewport suites green); D1–P21 are NOT reopened.

**Stamps:** `pipeline_state.py hash-section` cannot stamp this phase — the script
requires exactly `## Phase P<n>` while this repo's canonical headers carry trailing
text (`## Phase P22 — …`); `docs/plan_review_P21.md` likewise carries no stamps.
Freshness falls back to the mtime rule per the artifact rule.

**Lint backstop:** `plan_lint.py --phase P22` → PASS (0 failures, 4 warnings; the
warnings are `::symbol`-suffix parse noise on Frozen owner lines whose plain modules
— `ui/main_window.py`, `ui/lwc_view.py`, `chart_assets/lwc/`,
`docs/requirements/feature_suggestions.md` — all resolve).

- Coverage: every P22 expectation traced — `AC-D61.1`–`AC-D64.3`, Journeys 58–61,
  A181–A185, R134–R137, DG114–DG116 — via the plan traceability table; no
  expectation narrowed or reinterpreted; Q103–Q105 (all (a)) carried through as
  `AC-D62.3`/`AC-D63.1`/`AC-D64.1` FINAL.
- Completeness: constrained stack + zone-aware formatting home + test harness with
  rationale and rejected alternatives; components, data model (one QSettings scalar,
  no migration), integrations (none new, explicitly), frozen interfaces,
  AC-tied non-functional approach, risks AR-P22-1…AR-P22-5 — every S-P22 decision
  carries rationale.
- Consistency: `[extends D49.6]` (creation threading confirmed intact in the
  summary — `popout_view(tz_offset=…)`, `_popouts` registry, `_restore_popouts`
  seed; P22 adds only the live-update path) and `[extends P6]` (library-native
  crosshair confirmed — `CROSSHAIR_OPTIONS`/`applyCrosshair` in
  `chart_assets/lwc/interaction.js`) verified against source; all other inputs
  compose read-only; no contradictions.
- Plan quality: four ordered milestone phases (S/M/S/S) with goals, covers,
  dependencies, `touches_files`, and exit conditions; shared-file serialization
  noted (`ui/main_window.py`, `chart.js`); no task breakdown, no dependency graph,
  no per-task tests.
- Readiness: Task Manager can build a task graph without inventing architecture —
  the missing callee, bridge op semantics (AP-P22-1 fixes batching/replay; only
  envelope field names are Task Manager detail), formatter home, fan-out +
  persistence, free-tracking pin, and repro-first gates are all explicit.
- Existing-repo compliance: pass (5/5 — substantive Codebase Summary with
  file:line symbols re-verified by direct read; LWC-only stack respected; labels
  present; additive-only; summary consistent with the proposal).
- Frozen interfaces: pass — verbatim contracts re-verified against source
  (`_chart_call` dispatch, `format_tz_label` `local = t - offset`, `lwConfigure` +
  `axisProbe`, D19/D20 geometry, `_popouts` + D49.6 threading, UTC-second series
  basis, FS20 magnet); nothing under construction frozen (new work in the explicit
  NOT-frozen list); owners resolve; no duplicates.
- Map quality: pass — P22 note appended, no new module, entries index-sized;
  spot-checked key files (`ui/main_window.py`, `ui/lwc_view.py`,
  `ui/lwc_bridge.py`, `chart_assets/lwc/chart.js`, `interaction.js`,
  `ui/popout_window.py`) present.
- Doc sync: pass — `docs/pending_doc_sync.md` absent; no unapplied entries.
- Escalations: zero `open` PLAN-routed entries (104 entries, all addressed).

**Required Changes:** none. **Requirements Escalations:** none
(`Flagged Issues: None`; AP-P22-4/DG115/DG116 tripwires are decision rules with
in-phase handling, not gaps).

**Final decision:** `Status: APPROVED` — `docs/plan.md` carries
`Status: READY_FOR_TASK_MANAGER` for Phase P22.
