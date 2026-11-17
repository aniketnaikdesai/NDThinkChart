# Code Review — Phase P18 (D57 viewport UX)

Tier: **FULL** (mechanical: VERIFY verdict FAIL exit 1 with 8 failures; P18-T2 blocked; shared/production files touched across tasks). Incremental scope: P18-T1, P18-T2 (results newer than any prior P18 marker; no P18 review log existed).

Ground truth consumed: `precheck.json` (scope P18-T1/P18-T2, no fail_fast, no overlaps, 4/4 + 5/6 per-task), `test_verification.json` + `.log` (FAIL, 8 failures), `build_log.md` (waves 277/278 read), both archived results JSON, `task-graph.json` (P18-T1/T2/T3), requirements AC-D57.1–D57.7 + Q92–Q95/A161–A165, architecture S-P18-1–S-P18-6 + AR-P18-1–AR-P18-6, `escalations.json` (88 entries, 0 open — no close-outs due). Diff-first: full `git diff HEAD` over every P18 file (production + tests); no graphify needed (diffs + results unambiguous). No full re-reads.

## Entry R1 — P18-T1 (chevron) — done, quality review: PASS with one nice-to-have

- Verified against S-P18-1/S-P18-2: `chevronVisible()` pure away-only (`!following`, newBars param intentionally ignored, documented), glyph-only `#goToLatest` button (aria-label, hidden default, bottom-right), click → unchanged `goToRealtime()`, toggling only on viewport-change paths (keyboard, goToRealtime, fitAndFollow, applyOps, landDeferred, init) — no polling. AC-D57.1/AC-D57.2/AC-D57.3 covered by T11/T13/T14 + T12 node matrix incl. the away-without-new-bars red cell. Own tests 4/4 pass; footprint verified, no overlaps.
- No security/maintainability concerns (static glyph textContent, no innerHTML; focusable button; probe side effects mirror existing affordance-probe pattern).
- Mock-endpoint scan over the reviewed diff: zero production mock/fake/stub/simulat × endpoint/client/service/server/api/harness hits (single "harness" hit is a comment about older test-harness button DOM, not an endpoint). Clear.
- Usage docs: `doc_candidates` (USAGE.txt, docs/, usage.md) untouched; both tasks carry `doc_required: false` (Task Manager's judgment stands) — chevron/framing are in-page behaviors pinned by offscreen suites. No doc finding; saying so explicitly per the docs gate.
- Finding: chevron visible on empty chart → ESC-105 (BUILD, quality, nice-to-have). `updateChevron()` reads `!isFollowing()`; empty snapshot (`newestBarSlot() == -1`) derives away, so init unhides the button before data lands. One-line page guard suggested; transient and AC-edge, hence nice-to-have.

## Entry R2 — P18-T2 (fresh framing) — blocked: failure reproduced, test-only root cause

- Reproduced with the task's own command (`... -q` single-test run): same node failure `[undefined, undefined]` vs `[2, 20]`.
- Root cause is in the TEST, not the implementation: T24b reads `page.lwVisibleRange().from/.to`, but the frozen probe returns `{newestSlot, range}` (chart.js:1323–1325); every frozen P11 consumer uses `.range` (test_p11_no_yank.py:222,264,270,284). Implementation verified correct from source shape (lone-frame and explicit-frame-wins paths lift `set_visible_range` out of the envelope and land/defer it; T21/T22/T23/T25/T26 pass).
- Routed: ESC-101 (BUILD, bug, blocking) — two-assertion `.range` fix in tests/test_d57_framing.py, inside T2's touches_files, no production change.

## Entry R3 — the 8 VERIFY failures, adjudicated per failure (orchestrator note answered)

Real regression vs fallout, each verified, not inferred:
- (a) T24b (`test_d57_framing`): test-only defect → ESC-101 (above).
- (b–e) 4× `TestRendererBoundary` (`alarms`/`drawings`/`overlays`/`studies` `..._never_ride_the_bar_transport`, KeyError `series`): FALLOUT, not a renderer regression. The frame directive (series-less `set_visible_range`) deliberately rides the bar envelope (same-envelope ordering per AR-P18-5; bridge + envelope validation landed and functional); the assertions encode the superseded series-only envelope assumption. Renderer channels untouched.
- (f–g) 2× `test_lwc_time_parity` (op-count 3≠2 at :172; unpack-2→3 at :201): FALLOUT, same envelope-membership cause.
- (b)–(g) share one owner gap: none of the 5 files is in T2's or T3's touches_files → ESC-102 (TASK_MANAGER, gap, blocking): one churn task (or widen P18-T3) to tolerate the series-less directive while keeping renderer-exclusion intent. Explicitly NOT a direction to move the frame off the envelope.
- (h) `test_p11_symbol_memory.py::test_p11_t4_t41` (0 vs 1 restore op): INTENDED behavior change (S-P18-4 retires range restore; AC-D57.5/A165 lineage) whose churn file has no owner (T3/T32 covers only `test_p11_fit_affordance.py`) → ESC-103 (TASK_MANAGER, gap, blocking).
- (i) `test_the_toolbar_trendline_draws_through_the_real_page` (anchors collapsed onto one bar): REAL REGRESSION, P18-caused. Proven by bisect: passes on the pre-P18 tree (P18 tracked edits stashed → 1 passed), fails consistently post-P18 including an isolated re-run. Suspect: framed load replacing fitToWidth on the `_channel_view` path collapses the drag's pixel→bar mapping. → ESC-104 (BUILD, bug, blocking) with repro + suspect sites (both inside T2 footprint).
- P18-T3 remains correctly gated on T2; T3 not started, nothing to review. Scope guard held: no D1–P17 phase reopened — the churn findings update P6/P11 *test files* only to accommodate a deliberate P18 wire decision, owned by P18.

## Entry R4 — unattributed working-tree changes (orchestrator note answered)

`ui/lwc_bridge.py` + `chart_assets/lwc/envelope.js` (accept `set_visible_range` on the bar envelope), the chart.js frame branch, and `tests/test_d57_framing.py` predate this worker but are P18's own (S-P18-3-citing comments; required for any framed load to validate — the worker's footprint flag is accurate), NOT another lane's leftovers. Verified correct as far as review goes (validation shapes finite; page lifts the directive out before series application). Hygiene note for Task Manager (no escalation): T2's result claims only `ui/lwc_view.py` while the phase's green depends on the unclaimed files — ensure the closing task claims or acknowledges them. Reviewed all of them via `git diff` regardless of attribution.

## Entry R5 — escalation close-out

`escalations.json` holds 88 entries, 0 with `status: open`; `precheck.json` `escalation_updates` is empty. Nothing to re-verify or flip. No `PRE-*` entries outstanding.

## Summary of routes

- ESC-101 → BUILD (blocking): T2 re-run fixes its own T24b accessor.
- ESC-102 → TASK_MANAGER (blocking): churn task for the 6 envelope-membership assertions (5 files, no current owner).
- ESC-103 → TASK_MANAGER (blocking): owner for the symbol-memory switch-back churn (widen T3 or new task).
- ESC-104 → BUILD (blocking): trendline drag-mapping regression (bisected to P18).
- ESC-105 → BUILD (nice-to-have): empty-chart chevron guard.
- T3 stays gated until ESC-101–104 clear; T1 needs no rework (ESC-105 non-blocking).

---

# Pass 2 — P18 rework final (2026-11-05)

Tier: **FULL** (phase-final pass is always full). Incremental scope: P18-T1, P18-T2, P18-T3 (results newer than the pass-1 marker). Ground truth consumed: `precheck.json` (scope 3 tasks, 0 fail_fast, overlap info T1↔T2 on chart.js), `test_verification.json` (PASS exit 0 — the suite is actually green), `build_log.md`, all three archived results JSON, `task-graph.json`, requirements/architecture P18 sections via the pass-1 read, `escalations.json` (ESC-101–105 open). Diff-first over every P18 file; targeted re-runs only (full suite ground truth already PASS — no re-run to check).

## Entry R1 — close-outs: ESC-101, ESC-104, ESC-105, ESC-102, ESC-103 → all addressed

- ESC-101 (T2 T24b probe shape): fix present at tests/test_d57_framing.py:432/450 (`.range` shape); T24b passes in my targeted re-run. → addressed.
- ESC-104 (trendline drag collapse): chart.js ResizeObserver re-asserts the current logical range on resize (isFinite-guarded, try/catch, slots unchanged → viewport-preserving) with landDeferred ordering; trendline e2e passes in my targeted re-run, 105/105 node per T2 selfcheck. → addressed. T2's owner-exception provenance audited (orchestrator_state.json owner_exception_2026_11_05_p18t2): edits confined to the two listed files; substance independently verified above — exception grant not re-litigated.
- ESC-105 (empty-chart chevron): updateChevron() hides when newestBarSlot() < 0, pure matrix untouched; new test_p18_t1_t14_empty_chart_chevron_hidden passes in my re-run. → addressed.
- ESC-102 (six envelope-membership re-pins): diff-reviewed all six — frames excluded by op=='set_visible_range' with 'series' absence asserted; renderer-exclusion intent intact (bar ops still must be candles/volume; alarm/drawing/overlay/study series still fail); time-parity selects by series key. Executed through widened P18-T3 as scoped. → addressed.
- ESC-103 (symbol-memory fresh-frame-wins): diff-reviewed — zero restore ops asserted, one fresh frame op (≠ remembered range) with tracking, S-P18-4 lineage recorded, follow-state assertions kept. → addressed.

## Entry R2 — quality review (pass tasks): no new findings

- ESC-104/105 hunks: ResizeObserver early-return when unlaid-out; re-assert is a same-value write (no yank, no gesture fight); chevron wiring is glyph-only textContent (no innerHTML), focusable, aria-labelled. No security/maintainability concerns.
- Mock-endpoint scan over the reviewed diff (mock/fake/stub/simulat × endpoint/client/service/server/api/harness): zero production hits (single "harness" hit is a comment about older test-harness button DOM). Clear.
- Usage docs: doc_candidates (USAGE.txt, docs/, usage.md) untouched; both in-scope tasks carry doc_required false — chevron/framing are in-page behaviors pinned by offscreen suites. No doc finding; saying so explicitly per the docs gate. D57 viewport only; P19 prefetch explicitly out; D1–P17 not reopened.
- Record-keeping note (no escalation): P18-T3's result lists files_changed=[] while the widened-T3 re-pin edits to the five churn files live in the tree — same attribution class as the pass-1 R4 hygiene note (T2's result likewise lists only chart.js + framing test while the S-P18-3 wire files ride along). Substance verified green; graph touches_files already cover all of them. No action.

## Summary of routes

- No new escalations. ESC-101/102/103/104/105 → addressed (all re-verified on the live tree above).
- Open escalations remaining: none.

Status: REVIEW_COMPLETE
