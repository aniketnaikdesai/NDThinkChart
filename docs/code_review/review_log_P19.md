# Code Review — Phase P19 (D58 scroll-triggered prefetch)

Tier: FULL pass (phase-final; scoped tasks are size M, share `ui/main_window.py`, and carry overlap/info + warning flags — light-pass conditions not met).
Scope: P19-T1, P19-T2, P19-T3, P19-T4 (all results newer than any prior marker; no `review_log_P19.md` existed).
Ground truth consumed: `docs/code_review/precheck.json` (+`.md`, 0 fail_fast), `docs/code_review/test_verification.json` (PASS, exit 0), `docs/build/build_log.md` waves 284–291, per-task results in `docs/build/results/_archive/wave28x/29x_*.json`, task-graph P19, requirements `### Phase P19` + trigger table, architecture S-P19-1…S-P19-7, plan § Phase P19, `docs/orchestrator_state.json` (`owner_exception_2026_11_09_p19t2`), `docs/codebase-map.md` (P19 note). No open entries in `escalations.json` — entry-C close-out has nothing to process (`precheck.escalation_updates` empty, confirmed).

## Diff reviewed (working tree vs HEAD `b39fdf2`)

- `ui/lwc_view.py` (+54): `viewport_settled` signal + emit in `_on_page_viewport_report` + `oldest_visible_ts()` resolving the stored `from` slot through `series_times`/`_logical`/`_plotted` with whitespace-placeholder skip and clamping. Matches S-P19-1/S-P19-2 and the ESC-104 placeholder contract cited in the docstring.
- `ui/main_window.py` (+278/-6): settled fan-out wiring (guarded `getattr` connect), `_on_viewport_settled`, `maybe_prefetch` (fire/silent only), `maybe_issue_prefetch_wave` (single-step ordinary wave, DG111 coalesce-never-cancel, triple re-validation, empty-cache defers to load path), `_consume_pending_prefetch` (current-triple only, marker cleared before re-evaluation), terminal-wins `_on_error` ordering, marker consumption after `_finalize_history_wave` in `_on_session_wave_complete`.
- `ui/ticker_session.py` (+12): `_pending_prefetch` field + clearing in the cancel path. In T2's declared `touches_files`; see observation O-1 below.
- `tests/test_d56_taxonomy_pacing.py` (+5/-2): t32 now asserts the terminal failed-requests message stands and the transient `162` line does not overwrite it on wave-terminating errors.
- New suites: `test_p19_prefetch_trigger.py`, `test_p19_prefetch_wave.py`, `test_p19_prefetch_depth.py`, `test_p19_prefetch_honesty.py`, `test_p19_prefetch_viewport.py` (all untracked working-tree files, expected pre-commit).

## Verification performed (beyond the suite verdict)

- Spot re-ran all five P19 suites offscreen: all dots, 0 failures — consistent with per-task claims and the full-suite PASS.
- Mock-endpoint scan (standing invariant): `mock|fake|stub|simulat` across the production diff — zero hits. No mock endpoint in production code; no production import of a test fake. PASS.
- Attribute/case audit on the new seams: `session._pending_prefetch`, `_wave_timeframe`, `_wave_extended_hours` all initialized (`ticker_session.py:192`, `:220`); session symbols uppercased at both creation (`ticker_session.py:128`) and registry (`main_window.py:880`), so the `_consume_pending_prefetch` triple guard compares like with like. `build_main_chart_view` returns the real `LwcChartView` on the LWC engine, which owns `viewport_settled`; the `getattr` guard degrades silently on any other engine. PASS.
- `_on_error` terminal-wins ordering: on wave-terminating errors the transient line is skipped so the finalization surfacing (shortfall / failed-requests) stands; while the wave is alive the error line still shows. Either arrival order ends on the terminal message. Coherent with AC-D53.3/AC-D16.4 honesty; the t32 update enshrines the corrected semantic (TM extended `touches_files` for it — footprint legitimate).
- Scope guard: diff touches only the P19 seam files + P19/D56 tests. No P20 (IND/futures), no D1–P18 criteria files, no planner/pacing/watchdog tuning. PASS.
- Usage-doc judgment: `doc_candidates` are `USAGE.txt`, `docs/`, `usage.md` (0 touched). D58 adds no user-facing surface — no new control, command, config, or workflow; prefetch is background behavior inside existing waves. No doc update required. Explicitly: docs gate satisfied by absence.
- Architecture/requirements consistency: T1→S-P19-1/S-P19-2 + AC-D58.1; T2→S-P19-3/S-P19-4 + AC-D58.2 (one step, one in flight, pacing/watchdog/D53/D56/generation, coalesce seam, terminal clearing, abandonment via generation-bump/cancel); T3→AC-D58.5 (chaining falls out of completion→consume→re-evaluate; no new production code needed, tests pin 3-link chains + honest stops); T4→AC-D58.3/AC-D58.4/AC-D58.6 (honesty, viewport-slot stability, batch gate green + history intact). No deviations found.
- T2 owner-exception audit (do-not-relitigate-grant scope): the exception record lists exactly `ui/main_window.py` (`_on_error` terminal-wins), the two test files, and the TM footprint extension for `test_d56_taxonomy_pacing.py`. All verified live above; ACs hold; full suite green. The exception work is substantive and sound.
- T3 "no production change" claim: accepted — chaining reuses the T2 marker loop; the depth suite (4 green here) exercises completion-driven re-evaluation, closure silence, single shortfall, and pacing fall-through. No missing hunk.

## Observations (no action — not escalated)

- O-1: `ui/ticker_session.py` carries a real P19 edit (the `_pending_prefetch` marker, code-commented `P19-T2`) that is inside T2's declared `touches_files` but absent from T2's result `files_changed`, hence precheck's "unattributed working-tree change" note. No footprint violation (touches cover it) and no behavior impact; the result manifest is simply under-listed. Recording here so a future pass does not re-diagnose it; not escalated because no code, test, or task-breakdown action exists to route.
- O-2: T2's result cites test ids `T21+T22` (precheck `unknown_test_ids` warning) while the task spec names `P19-T2-T01/T02` and the file holds `t01_*`/`t02_*` families (9 tests collected, all green). Cosmetic label sloppiness in the orchestrator-written result only; the underlying coverage maps to both ACs. Not escalated.

## Findings

None. No `BUILD` / `TASK_MANAGER` / `PLAN` / `REQUIREMENTS` routings. No `escalations.json` changes (nothing open, nothing new).

Status: REVIEW_COMPLETE
