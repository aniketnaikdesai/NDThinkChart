# Code Review — Phase P21 (D60 follow-offset preservation)

Tier: FULL (8 full-suite failures; 2 size-M tasks; chart.js overlap T1/T2).
Scope (incremental, results newer than last marker — no P21 marker exists):
P21-T1 (done), P21-T2 (blocked). P21-T3 not started (gated).
Ground truth consumed: precheck.json (0 fail_fast; T1 4/4, T2 2/3;
chart.js overlap info-only), test_verification.json (FAIL exit 1, 8 failures),
build_log.md, failures.json, results/_archive/wave312_P21-T1.json +
wave314_P21-T2.json, task-graph.json, requirements (D60/AC-D60.1–7, Q100–Q102),
architecture + plan Phase P21 sections. 0 open escalations (entry C no-op).
Reproduced: T2 file 9/11 (same 2 fail), T1 pytest 4/4 + node 15/15 green,
chart.test.js 20/25 on tree vs 25/25 at HEAD worktree (P21-caused, see ESC-114).

## P21-T1 — done — ACCEPT (no findings)

What: envelope slot-delta shift replaces followLive edge-pin; goToRealtime/
fitAndFollow preserve per-instance rememberedGap (default 2, mirrors
ui/lwc_view.py:1685 FRESH_FRAME_RIGHT_PADDING); manual scroll/pinch only
zero-gap path; per-view state, no bridge field (verified: rememberedGap read
only for range math + lwRememberedGap probe; no report/emit payload change).
Checks: GxN shift math + exactly-once (AR-P21-1) sound; NaN/junk-range guards
present (isFinite, span>0, delta>0, slot>=0 fall back to fitToWidth);
rememberedGap can only be written while following (isFollowingSlot gates
slot<=to, so gap>=0 — no negative memory); away ranges never refresh;
refresh-on-following is pinned by T1's own static+runtime tests (red-first
13 node + 3 pytest pre-fix per result). T2's later single-application-point
restructure preserves the pin (T1 suites re-run green under it: 4/4 + 15/15).
Docs gate: no user-doc surface (usage.md/USAGE.txt never specify gap/snap
semantics; doc_required=false) — no finding. Mock-endpoint scan: prod diff
has no mock/fake/stub/simulat and no mock endpoint/client/service/server/api/
harness (only "offscreen harness" in comments) — PASS. T1's code is the
mandated Q100(b)/S-P21-2 revision, not the cause of the red suites below
(those pin the retired mechanics — see ESC-114).

## P21-T2 — blocked — 2 findings, both test-harness fidelity, route BUILD

Worker report is honest (no test edited per guardrails; 9/11 pass; P21-T1
suites + P19 T02-away control green). Both failures reproduced; each root
cause is in tests/test_d60_away_landing.py — inside T2's own touches_files —
with production (chart.js-only change) exonerated:

- Finding R1 (ESC-112, BUILD, blocking): test_p21_t2_ac1_legA_backfill_
  continuation auxiliary asserts lwRememberedGap()==2 after parkAway().
  parkAway seeds 60 bars with NO fresh frame (bare page fitToWidth lands
  {0,59}, gap 0, following → refresh rule S-P21-2/AP-P21-2, pinned by T1's
  tests, mandates rememberedGap=0). Production first loads always carry a
  Python fresh frame at gap 2 (set_series stamps continuity=False +
  appends frame whenever fresh requested), and the 5-slot keyboard pan
  exits follow on pan 1 (2-5<0) so no intermediate refresh can corrupt it —
  traced, so seeding parkAway through a frame-carrying envelope ({from,
  newest+2} following:true, i.e. driver-faithful first load) makes the
  unmodified assertion pass with all core bit-identical/disengaged
  assertions intact. Unfixable in production without breaking T1's pinned
  refresh. No assertion weakened by the remedy.
- Finding R2 (ESC-113, BUILD, blocking): test_p21_t2_ac1_backfill_chunk_
  with_wave_in_flight asserts _on_viewport_settled issues 1 request; 0
  issued. Setup drops recent[0] (leading-edge gap, not an interior hole)
  and reports synthetic non-slot-mapped {5.0,15.0}; issuance lives in
  ui/main_window.py (outside touches, unchanged by T2 — chart.js-only
  diff — so the 0 is pre-existing for this setup, not a T2 regression).
  The identical-shape P19 helper (interior hole + slot-mapped settled
  report, following=False) issues 1 and passes on this tree (worker
  control re-confirmed). Remedy: mirror the P19 setup (seed full recent
  block, interior hole, slot-mapped report) so the AC-D60.7 "wave in
  flight" premise actually holds; no production change, no assertion
  weakened. Considered and rejected: treating leading-edge issuance as a
  product gap — backfill strategy is D16/P20 territory, out of D60 scope,
  and AC-D60.7 assumes the wave in flight. Caution attached: parkAway is
  shared by legs B–E/AC2/AC3 (all currently green) — re-run the whole
  11-test file on re-dispatch (legD/legE/freshWins/AC3 traced safe, but
  verify, don't assume).

## Full-suite 8 failures — 1 migration invariant, route TASK_MANAGER

All 8 are pre-P21 contracts asserting mechanics P21 deliberately retired
(Q100(b) preserve-override S-P21-2; S-P21-5 landing neutrality). 6 red +
2 latent (pass only via unfaithful seeds, will redden under faithful
seeds) — one invariant, one escalation (ESC-114, TASK_MANAGER, blocking):
pre-P21 suites need migration to preserve semantics + driver-faithful
envelopes; T3's touches_files (D60 files only) cannot legally touch them.
Adjudication per failure (each reproduced or log-anchored):
- T13 chevron_click_goes_realtime + T31-joint chevron_click_after_fresh_
  frame + T22 no_auto_resume + T32 affordance_visibility_and_invoke:
  assert _scrollCalls>0 (goToRealtime no longer calls scrollToRealTime —
  uses setVisibleLogicalRange + rememberedGap by owner decision) and/or
  post-action edge-pin (range.to==newest). Superseded outcome+mechanism;
  migrate to gap==remembered/follow-re-engaged/badge-consumed assertions.
  T2's own AC2 test already models the migrated form (drops the stale
  call-count, still green).
- T24b page_applies_fresh_frame_over_preserve: same_symbol:true + frame
  while away expects frame-wins [30,41], actual hold [2,20]. Directly
  contradicted by T2's PASSING legD (same combo → hold, the S-P21-5
  decision) and driver-impossible (set_series stamps continuity=False
  whenever a frame is requested — ui/lwc_view.py:2471-2474 — so
  same_symbol:true + frame is never emitted; new-symbol/timeframe loads
  always frame and still win, per passing freshWins + Python-half T21–T24).
- Geometry guard node_chart_suite_is_green: chart.test.js 20/25 (25/25 at
  HEAD). Single root for all 5 subtests: frameless re-seed over leftover
  away page state now holds (S-P21-5 bare-awayLanding leg) instead of
  refitting to {0,59} — seed expects {0,59}, gets held {-24.1,23.1},
  everything downstream (T11 zoom, T12 probe, T23 follow, P18-T1-T12
  probe) misfires. Production first/new-symbol loads always carry frames
  (above), so the idiom (frameless seed + shared page across its) is
  unfaithful; migrate (isolate page state per test and/or seed through
  frame-carrying envelopes as the driver does).
- T2 legA + wave_in_flight: own-file fidelity items, routed BUILD above
  (not part of the TM migration).
- Latent (currently green, will redden when seeds turn faithful):
  test_p11_t3_t31_fit_frames_all (asserts fit lands {0,newest}; passes
  only because bare-fit seeds leave rememberedGap=0 so fitAndFollow's
  +G extension no-ops) and the legA-adjacent gap-0 dependencies — the
  migration task must update these to to==newest+G rather than "fixing"
  them back to edge-pin.
No real regression found: the away core (bit-identical + disengaged) is
green everywhere it is faithfully set up (T2 legs B–E, AC2, AC3 9/11;
P19 T02 control); forming-tick/republish exactly-once green (T1 AC4).

## Entry C — nothing to close (0 open; precheck escalation_updates empty).

## Escalations opened this pass: ESC-112 (BUILD, blocking), ESC-113 (BUILD,
blocking), ESC-114 (TASK_MANAGER, blocking). No code touched (reviewer
writes: this log + escalations.json only); /tmp worktree removed.

Status: REVIEW_COMPLETE

---

# Code Review — Phase P21 rework (D60 follow-offset + away-hold)

Tier: FULL (phase-final pass is always full). Scope (incremental, results
newer than the last marker): P21-T2, P21-T3, P21-T4, P21-T5 (all done).
P21-T1 accepted last pass — re-confirmed still held (see below), not reopened.
Ground truth consumed: precheck.json (0 fail_fast; T2 11/11, T3 2/2, T4 3/3,
T5 3/3; no overlaps; doc_candidates 3, 0 touched), test_verification.json
(PASS exit 0, ground truth — no suite re-run to check it), build_log.md,
results/_archive/wave316_P21-T2/T4/T5 + wave317_P21-T3, task-graph.json
(P21-T1..T5, TM migration tasks as ESC-114 directed), requirements
(D60/AC-D60.1–7, Q100–Q102) + architecture/plan Phase P21 sections.
Reproduced (spot, flagged tasks only — never the whole phase): T2 file 11/11,
T4 4-suite 12/12, T5 framing+parity 30/30 + node chart.test.js 25/25, T1
follow_offset 5/5 + node follow_offset 15/15.

## P21-T2 — done — rework VERIFIED, no new findings

Both ESC-112/113 remedies landed exactly as routed, inside the task's own
touches_files, with no production edit and no weakened assertion:
- ESC-112: parkAway seeds through a frame-carrying envelope
  ({from:0, to:n-1+2}, following:true — test_d60_away_landing.py:215-216),
  so lwRememberedGap()==2 holds per the S-P21-2 refresh rule; all core
  bit-identical/disengaged assertions intact.
- ESC-113: wave-in-flight setup seeds a genuine one-day interior hole
  (_prev_trading_day(recent[0]) excluded, 3-day older block behind it,
  :581-597) with a slot-mapped settled report; issuance premise holds.
T2 diff is test-only (files_changed: tests/test_d60_away_landing.py only;
chart.js/lwc_view.py untouched). 11/11 green on re-run.

## P21-T4 — done — ACCEPT (no findings)

Test-only preserve migration of the 4 ESC-114 suites + latent T31. Each
migrated case establishes the remembered gap via a frame-carrying tracking
frame (G=2), then asserts post-action gap==G with span preserved, follow
re-engaged, badge consumed/chevron hidden; retired scrollToRealTime
call-count pins removed, follow/badge/chevron outcomes restated not dropped.
T31-fit re-pinned to {0, newest+G}; no_yank T22 keeps both the entry-resume
and the ArrowRight-derivation legs. Diff touches only the 4 test files
(precheck files_verified match). 12/12 green on re-run. Consistent with
AC-D60.1/2/4/5 and S-P21-2. No production change, as tasked.

## P21-T5 — done — ACCEPT (no findings)

T24b page half restated to hold ([2,20], follow disengaged) with an added
fresh-load-wins leg ([30,41]) that keeps the new-symbol frame-wins contract
green — matches passing legD and the driver-impossible note (continuity
stamping), so no contradiction. chart.test.js: per-suite beforeEach +
frame-carrying seeds (production-faithful idiom); geometry guard green via
parity suite (30/30 pytest + 25/25 node on re-run). Diff touches only the 2
test/js files named (tests/test_lwc_time_parity.py listed in touches but
correctly unchanged — guard-only). Consistent with S-P21-5/AC-D60.7.
No production change, as tasked.

## P21-T3 — done — ACCEPT (no findings)

Gate: full-suite evidence (task ran the whole offscreen suite green; ground
truth test_verification.json PASS exit 0 confirms) + AC-D60.6 history-intact
assertions present in-file (test_p21_t3_ac2_history_intact: marker sentence,
tech stack, D41–D60 sections). 2/2 green. No production edits per gate role.

## P21-T1 — still held (confirm, not reopen)

Production chart.js diff (rememberedGap/FRESH_FRAME_RIGHT_PADDING=2,
slot-delta shift, preserve entries, away-landing neutrality gate) is the
accepted T1+T2 shape; T1 suites re-run green (5/5 pytest + 15/15 node),
and the T4/T5 migrations pin the same semantics. No new evidence to reopen.

## Cross-cutting checks

- Mock-endpoint scan (standing invariant, blocking): grepped the reviewed
  diff for mock/fake/stub/simulat x endpoint/client/service/server/api/
  harness — zero production hits (only "stub document + fake 5.x tree" in
  test-file harness comments; chart.js prod diff clean). PASS.
- Usage-doc gate: doc_candidates are USAGE.txt, docs/, usage.md (0 touched).
  Correct to be untouched — D60 changes follow-offset/landing internals and
  the gap default; no user-facing CLI/API/workflow surface changes, and no
  doc_required flag on any scoped task. No finding.
- Requirements/architecture: migrated assertions match AC-D60.1/2/4/5/7 and
  S-P21-1/2/5 + AR-P21-1 exactly-once; T24b hold does not contradict legD.
- Hygiene note (no escalation, orchestrator-owned): precheck lists
  tmp_p21t2/ (+ copies) as unattributed untracked scratch — worker probe
  debris from the T2 diagnosis, not part of any delivery. Suggest deleting
  the directory; not routed (outside every task's touches_files, and a BUILD
  re-dispatch for `rm -rf` of scratch would be disproportionate). Also
  chart.js / follow_offset.test.js appear "unattributed" only because their
  owner (P21-T1) is out of this incremental scope — expected, not drift.

## Entry C — close-outs this pass

- ESC-112 (BUILD, P21-T2) → addressed (verified above, 11/11 + suite green).
- ESC-113 (BUILD, P21-T2) → addressed (verified above, 11/11 + suite green).
- ESC-114 (TASK_MANAGER) → addressed (verified above: P21-T4/P21-T5 diffs
  test-only, outcomes restated, 12 + 30 + 25 green, full suite PASS).
No open escalations remain.

## Escalations opened this pass: none.

Status: REVIEW_COMPLETE

---

# Code Review — Phase P21 re-confirmation pass (2026-11-10, post-P22 analyst edits)

Tier: LIGHT (incremental scope is empty — precheck.json scope 0 tasks, 0 fail_fast,
0 overlaps, 0 unattributed changes; every P21 result already consumed and archived
as wave312/313/314/316/317; nothing is newer than the last REVIEW_COMPLETE marker).
Entry A/B: no-op (no scoped tasks — nothing to diff, reproduce, or quality-review).
Entry C: no-op (escalations.json: 104 total, 0 open; precheck escalation_updates empty).

Verification note (no finding, no escalation — out-of-scope tree dirt, recorded so
the FAIL is not mistaken for a P21 regression): test_verification.json verdict FAIL
exit 1 is exactly 2 failures, both history-intact guards —
test_p21_t3_ac2_history_intact and test_p20_t3_ac2_history_intact — each asserting
docs/requirements/requirements.md is byte-identical to HEAD (commit 5b3ec66, the P21
feature commit). The working tree carries P22's uncommitted analyst additions
(+83 requirements lines incl. the R133 row, +228 architecture, +182 plan — D61–D64
per the P22 map note), so the byte-identity assertion fails by construction. Every
other suite passes (progress shows only those 2 F's across the full offscreen run).
This is P22 in-flight requirements work tripping P21/P20 guards that pin committed
prose — adjudication (re-pin vs narrow, never weaken) belongs to P22's own gate,
not to P21: scope guard holds (D60 only; P21 code untouched — git status shows
docs-only modifications, P21 production/test files identical to the reviewed
commit). failures.json carries no blocked tasks; build_log.md terminal state remains
READY_FOR_REVIEW with P21-T1..T5 all done. Prior findings stand closed: ESC-112,
ESC-113, ESC-114 all verified addressed in the preceding passes. Mock-endpoint and
usage-doc gates were discharged on the full passes; nothing in this empty scope
reopens them.

## Escalations opened this pass: none (the 2 history-guard reds are P22's gate
concern, not a P21 defect — no route from this review).

Status: REVIEW_COMPLETE
