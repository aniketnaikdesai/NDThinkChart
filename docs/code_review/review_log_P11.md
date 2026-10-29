# P11 code review log — terminal build pass (2026-10-29)

Tier: **FULL** (fail_fast P11-T2 in scope; T1/T2 overlap on
`chart_assets/lwc/chart.js`; size-M task in scope; and this closes the
terminal build per the preamble).
Ground truth consumed, not re-derived: `precheck.json` (scope
P11-T1/T2/T4/T5; T1/T4/T5 `done` clean, T2 `done`-with-footprint-flag;
fail_fast P11-T2 suppressed as duplicate of open PRE-008; doc candidates 3,
0 touched; unattributed changes = T2 in-flight edits + owner untracked
report `.txt` files, ignored per preamble) and `test_verification.json`
(verdict `pass`, exit 0 — full offscreen suite green). `docs/build/failures.json`
carries only the P11-T2 footprint record (worker self-check verdict fail on
footprint alone, tests pass). No test was weakened, no code was edited.

Scope note: the preamble states "T1/T4/T5/T6 done"; ground truth
(`task-graph.json` + `build_log.md` + results) shows T1/T4/T5 `done`, T2
`blocked`, T3/T6 `not_started` (no result files, no consolidation entries).
T6-done is not supported by any build record — reviewed as not_started.

## Per-task verdicts

- **P11-T1 (follow-state definition, `chart.js` + `chart.test.js` +
  `tests/test_p11_follow_state.py`)** — PASS, no finding. `isFollowingSlot`
  is pure, total (empty series / missing / non-finite range all report not
  following), and derivation-from-live-range satisfies AR-P11-1 by
  construction; probes (`lwIsFollowing`/`lwFollowProbe`/`lwVisibleRange`)
  are read-only. Spot run: 2/2 pytest + node surface green.
- **P11-T2 (no-yank live path, `chart.js` + `tests/test_p11_no_yank.py` +
  wave-mandated `chart.test.js` T12/T23 update)** — work PASS with one
  pack-level routing (ESC-093, see below). `followingBefore` is captured
  before upserts land (post-update check would misread every live edge);
  scrolled-back upserts leave the range untouched; resume only via
  `scrollToRealTime`/`setVisibleLogicalRange` with `fitToWidth` fallback;
  no auto-resume on bars alone — exactly S-P11-2. The wave-198 "separate
  known red" claim (`test_p11_follow_state.py` T12 failing by design) is
  stale on the live tree: my own spot run has all four P11 suites green
  (8 passed) and node 22/22. No code defect, no test weakened.
- **P11-T4 (per-symbol memory, `ui/lwc_view.py` + `ui/lwc_bridge.py` +
  `tests/test_p11_symbol_memory.py`)** — PASS, no finding. Store is
  in-memory upper-cased-keyed with copy-returning accessor (no persistence,
  no schema change); save-on-switch-away reads the freshest throttled
  report (AR-P11-2 last-write-wins), same-symbol `set_symbol` early-returns
  before any restore, restore publishes one `set_visible_range` op only
  when memory exists; `report_viewport` rejects non-finite ranges. Matches
  S-P11-5/AP-P11-2/AP-P11-3.
- **P11-T5 (same/new replacement, test-only change +
  `tests/test_p11_replace.py`)** — PASS, no finding. `replacePreservesViewport`
  requires an explicit `same_symbol === true` on a `set_bars`/`set_volume`
  op (a lone clear never preserves); `set_series` stamps the directive from
  the prior-series comparison with pending-viewport cover after a switch-back
  restore, first load fits; zero-bar Fit is a guarded no-op. T21/T22-style
  node assertions (22/22) pin the page side. Production code underpinning
  T5 rode in via the shared `chart.js`/`lwc_view.py` diffs owned by
  T1/T2/T4 waves — attribution is cross-wave but behaviour is pinned green
  by T5's own suites, so no action.
- **P11-T3 / P11-T6** — `not_started`, correctly dependency-gated
  (T3 on T1+T2 with T2 blocked; T6 on all). No separate escalation: the
  unblock chain is carried by ESC-093.

## Cross-cutting checks

- **Mock-endpoint containment:** grep of the P11 production diff for
  `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness`
  finds only the word "harness" in a code comment; `chart.test.js` fakes
  live in the test file only and no production module imports a fake.
  Clean, no finding.
- **Order-code / live-TWS surface:** no `placeOrder`/`cancelOrder`/`eConnect`/
  `reqHistoricalData`/`transmit` tokens in the P11 diff; independent
  `test_verification.json` suite green. Clean.
- **Usage-doc coverage:** `doc_required` is false for all four scoped tasks
  and `precheck` raises no `doc_required_unmet`; the dirty `usage.md` in
  the tree documents P10 drag-editing, not P11, and the dirty
  `docs/requirements|architecture|plan` files are pipeline-owned phase
  artifacts. The follow-live behaviour change is user-visible in principle,
  but Task Manager already made the doc judgment (flag false) — per B.3 no
  finding filed. Considered and dismissed, recorded here.
- **Overlap T1/T2 on `chart.js`:** reviewed jointly — T1's probes plus T2's
  gating/preserve branches compose without conflict (probe surface stable
  across both waves; node count 21 → 22 is the additive T23 pin).

## Findings (routed via `escalations.json`)

- **RV-P11-1 → ESC-093 (TASK_MANAGER, consistency, blocking).**
  `bad_task_breakdown`: P11-T2's `touches_files` omits
  `chart_assets/lwc/chart.test.js` while the dispatched wave pack mandates
  editing exactly that file and the task's own `test_command` runs it, so
  two green BUILD waves are mechanically unconsolidatable and blind
  re-verify (wave 202) cannot unblock it. One-line pack amendment (add the
  file, re-consolidate T2 to done on the existing green results, no code
  change) unblocks T2 and thereby T3/T6. Per the repeat-invariant rule this
  goes to Task Manager as the single invariant fix — no third BUILD patch.

## Escalation close-out

- **PRE-008 (P11-T2 footprint, BUILD, blocking) → addressed.** Re-verified
  on the live tree per entry-C: work green by my own spot runs (not the
  worker's word), edit mandated by the dispatched pack
  (`docs/build/wave/P11-T2.md` read_files + `test_command`), reverting
  would break the mandated suite, full offscreen suite green. Accepted as
  a pack deviation rather than a code defect; the residual pack amendment
  is tracked open in ESC-093. Verified text appended in place; no other
  field touched.

Status: REVIEW_COMPLETE

# P11 focused close-out (2026-10-29, terminal build COMPLETE with P11-T2 blocked)

Tier: **FULL** (phase-final pass by rule; scoped slice carries the P11-T2 footprint history).
Ground truth consumed, not re-derived: `precheck.json` + `test_verification.json`
(verdict `pass`, exit 0 — full offscreen suite green). No code edited, no tests
re-run, no git/diff/doc-scan re-derivation.

## Decisions

- **ESC-093 (TASK_MANAGER, open) → addressed.** Re-verified per entry-C:
  the pack amendment is in the graph — P11-T2 `touches_files` is now
  `['chart_assets/lwc/chart.js', 'chart_assets/lwc/chart.test.js',
  'tests/test_p11_no_yank.py']` (confirmed from live `task-graph.json`);
  green work holds per wave202 result selfcheck (tests verdict `pass`,
  exit 0: pytest 2/2, node 22/22) and `test_verification.json` (verdict
  `pass`, exit 0). Pack defect resolved. `verified` appended in place.
- **PRE-008** already `addressed`; left untouched.
- **New: ESC-094 (BUILD, blocking) for P11-T2.** Graph status is still
  `blocked` on the wave-202 footprint flag; only a fresh BUILD re-dispatch
  re-stamps the gate on the amended pack (re-run scope: confirm the task
  `test_command` green, consolidate to `done`; no code change expected),
  so the next `build_wave` advance picks it up. This is the sole new
  finding — nothing else filed.

## Per-task standing (unchanged, recorded)

- P11-T1 / P11-T4 / P11-T5 `done`, green, no findings (prior pass verdicts stand).
- P11-T2 `blocked` on footprint technicality only; work green, pack amended.
- P11-T3 / P11-T6 `not_started`, correctly dependency-gated behind T2.

Status: REVIEW_COMPLETE

# P11 final close-out (2026-10-29, all 6 tasks done, build READY_FOR_REVIEW)

Tier: **FULL** (phase-final pass by rule; scoped slice P11-T2/T3/T6 carries
a size-M task and a T2/T3 `chart.js` overlap, so light is unavailable).
Ground truth consumed, not re-derived: `precheck.json` (scope P11-T2/T3/T6,
all `done`, tests 2/2 each; fail_fast empty; only flags are the T2/T3 overlap
info and the P11-T6 `unconfirmed_file` warning) and `test_verification.json`
(verdict `pass`, exit 0 — full offscreen suite green). No code edited. One
targeted node spot-run (part of T2/T3's own test_command) to support the
ESC-094 entry-C close-out; no pytest re-run (ground truth already green).

## Per-task verdicts (scoped slice)

- **P11-T2 (no-yank live path)** — PASS, no finding. Live-tree read of
  `chart_assets/lwc/chart.js`: `followingBefore` captured before upserts land
  (`applyOps` :995), unconditional post-applyOps refit gone (:1037-1042 —
  replace re-applies preserved range or fits fresh; upserts `followLive()`
  only while `followingBefore`), `followLive()` goes through
  `scrollToRealTime` with `setVisibleLogicalRange` fallback (:751-770), no
  auto-resume on bars alone (badge reconcile :1049-1053). Archived
  wave207 result: `done`, `footprint_flags: []`, pytest 2/2 + node 22/22;
  my own live-tree node run 22/22. Graph status `done`, `touches_files`
  holds the ESC-093 amendment.
- **P11-T3 (Fit/reset + go-to-realtime affordance)** — PASS, no finding.
  Live tree: `fitAndFollow()` frames via the existing `fitToWidth` framer
  and re-engages follow by derivation, consuming the badge on a landed fit
  (:787-793); `affordanceVisible()` is exactly (away AND new-bars-since-away)
  with reconcile-on-query so following disarms a stale badge (:798-802,
  AR-P11-4); `goToRealtime()` shares the one realtime-scroll path and
  consumes the badge (:777-781). Archived wave208 result: `done`,
  footprint clean, pytest 2/2 + node 22/22.
- **P11-T6 (batch gate)** — PASS, no finding. Archived wave209 result:
  `done`, full offscreen suite 1258 passed with only 3 pre-existing
  webengine skips, no skip/xfail added, production diff confined to the
  viewport path. The `unconfirmed_file` warning (live
  `docs/build/results/P11-T6.json` absent) is confirmed benign: T6 is a
  verification-only gate whose record lives in the archive; the gate's
  substance (full-suite green) is independently confirmed by
  `test_verification.json`. No action.

## Cross-cutting checks

- **Preamble-directed re-verification on the live tree** (all hold, no
  regressions under the dirty tree): T2-equivalent pointer guard —
  `gestures.js` move branch gated on `dragButtonHeld(ev)` (`buttons & 1`,
  :502-505/:810-812) with `pointercancel`/`pointerleave` abandon handlers
  (:927-993, ESC-091 comments intact); empty-color guard —
  `_on_page_drawing_updated` (:2628-2664) drops unknown-id commits when the
  id is in `_stored_drawing_colors`, else emits pre-P10 `""` (ESC-089/092
  fix intact).
- **Mock-endpoint containment:** grep of the scoped `chart.js` diff for
  `mock|fake|stub|simulat` × endpoint/client/service/server/api/harness —
  zero hits; `chart.test.js` fakes live in the test file only. Clean.
- **Order-code / live-TWS surface:** no new tokens in the P11 viewport path
  (page-side probes + gating only); full suite green. Clean.
- **Usage-doc coverage:** `doc_required` is false for P11-T2/T3/T6 in
  `task-graph.json` (Task Manager's judgment, respected per B.3). The
  precheck `docs/` touched flag is T6's own result file under `docs/`, not
  a user doc. The T3 affordance adds no DOM UI (page-side
  `lwAffordanceVisible` probe flag only — no Python/UX-surface change in
  scope), so no doc gap is filed. Considered and dismissed, recorded here.
- **Overlap T2/T3 on `chart.js`:** reviewed jointly — T2's gating/preserve
  branches and T3's badge/fit entries compose without conflict (single
  `newBarsSinceAway` flag, one realtime-scroll path shared by
  follow/resume/Fit/affordance).
- **Unattributed working-tree changes (16):** `chart.js`/`chart.test.js`
  and the scoped P11 test files are not among them; the remainder (P10
  gesture/bridge/view files, owner `.txt` reports, `usage.md`) sit outside
  this scope and carry no P11 finding. Noted, not reviewed.

## Findings

None new. This is a clean close-out: zero entries appended to
`escalations.json` besides the in-place close-out below.

## Escalation close-out

- **ESC-094 (P11-T2, BUILD, blocking) → addressed.** Entry-C re-verified
  on the live tree (see `verified` text appended in place): graph `done`
  on the amended pack, two clean gate re-stamps (wave206/wave207,
  footprint empty, tests green), own node run 22/22, full suite green,
  and the predicted unblock chain delivered (T3 done wave208, T6 done
  wave209). Nothing else was open: precheck `escalation_updates` lists
  only ESC-094 as changed.
- **ESC-088, ESC-089, ESC-091, ESC-092, PRE-007, PRE-008** — all already
  `addressed` from prior passes and unchanged since (absent from
  precheck `escalation_updates`); per entry-C rule 2 left untouched, not
  re-diagnosed. Their fixes' live-tree survival is additionally confirmed
  above (guards intact), but no `verified` field was rewritten since
  their closure already stands.
- **ESC-093, PRE-008** — already `addressed`; untouched.

Status: REVIEW_COMPLETE
