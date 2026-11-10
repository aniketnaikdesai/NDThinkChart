# Code Review — P22 (D61–D64 toolbar / timezone / crosshair / time-axis)

Tier: FULL (fail_fast PRE-020 present; test_verification verdict FAIL; file overlaps
main_window.py T1/T2 + chart.js T3/T4; phase-final pass — full duties regardless).
Scope: P22-T1..P22-T5 (all results newer than P21 REVIEW_COMPLETE marker).
Ground truth consumed, not re-derived: precheck.json + test_verification.json.
Full suite: FAIL exit 1 with exactly one failure
(tests/test_lwc_popouts.py::test_residue_scan_no_out_of_scope_surface); every other
suite — including P19 prefetch suites, P20/P21 history guards, and all P22 task suites —
green. P22 analyst additions are in and the history pins hold (T5-AC1 green).

## Entry 1 — ESC-115 (new) — blocking bug, routed BUILD, task P22-T2
- Category: bug. Severity: blocking.
- Observed: `ui/lwc_view.py:198`, inside `_live_eastern_offset`'s docstring, contains the
  literal token `ui.main_window` (``` ``ui.main_window._eastern_offset`` ```). The
  residue guard `tests/test_lwc_popouts.py:414` asserts that token absent from lwc_view
  source and fails (`AssertionError: ui.main_window`). Reproduced independently with the
  single-test run (same assertion, same line). Full-suite red is exactly this one test.
- Expected: lwc_view source contains no `ui.main_window` token; suite green. The
  docstring can keep the no-import-window contract without the dotted module path.
- Evidence: `git diff HEAD -- ui/lwc_view.py` (+45-line hunk, docstring at :198);
  test_verification.json output_tail; single-test repro exit 1.
- Root cause (code_bug): descriptive prose, not architecture — no import was added and
  the module boundary holds (window imports this module; verified: only the docstring
  matches `grep ui.main_window ui/lwc_view.py`). One-line reword inside P22-T2's own
  `touches_files`.
- Suggested direction: reword to e.g. "the main window `_eastern_offset` helper".
- Repeat-invariant check: first case of this invariant in P22; single BUILD route is correct.

## Entry 2 — PRE-020 (precheck, still OPEN) — P22-T5 missing result file
- Nothing relevant changed since it was opened: `docs/build/results/_archive/` still holds
  only `wave322_P22-T5.INVALID.json` (`attempted` is a list, must be a string); no valid
  P22-T5 result exists. Task-graph now shows P22-T5 `in_progress` (wave 324 re-dispatch
  in flight) vs `blocked` at precheck time — a status flip, not a fix. NOT verified
  resolved; leaving open. Next pass: flip to addressed only after a valid result file
  exists AND the suite is green.
- T5 work-product assessment (from the INVALID handoff + own re-verification): the gate
  file `tests/test_d64_batch_gate.py` is sound — ran it myself, 3/3 pass standalone
  (AC1 narrowed history pin, AC2 DG114-confirmed/DG115/DG116-closed record, AC3 guard
  adjudication re-pin + node core green). T5's AC3 block is entirely the ESC-115 residue
  failure, which lives outside T5's `touches_files` — correctly left untouched by the
  T5 worker. Decision: require both the ESC-115 reword (P22-T2) and a T5 re-run that
  writes a valid result file; the handoff evidence is accepted but does not substitute
  for the file.

## Entry 3 — P22-T1 quality review (done, no escalation)
- Diff (`ui/main_window.py` toolbar block): `_toolbar_caption` helper sets
  `QSizePolicy::Minimum` horizontal so full-text width is the floor; D19 scroll wrapper
  stays the overflow mechanism. Label-field-local per AP-P22-4; D19/D20 suites ran
  unmodified and green (16 passed incl. new D61 suite).
- Note: the SY clip did not reproduce pre-fix in this offscreen env (caption exactly its
  text advance, 42/42px — zero room, confirming the defect class); the fix adds
  structural room and holds under font drift. Acceptable.
- Observed-not-fixed (no escalation): dynamic `conn_badge` text can still squeeze when
  runtime text outgrows construction width — separate dynamic-sizing issue, deliberately
  untouched per the label-field-local rule. Logged for awareness only.

## Entry 4 — P22-T2 quality review (done, modulo ESC-115)
- `LwcChartView.set_timezone` publishes `{"op": "set_timezone", "mode"}` on the existing
  interaction channel; `_on_tz_changed` fans out to main (via `_chart_call`, verified to
  resolve: `LwcDriverView` is the `LwcChartView` alias) + every `self._popouts` entry
  (duck-typed getattr, safe) + persists `chart/timezone` with startup restore.
- Tests pin op shape both modes, replay survival, real-toggle fan-out to main + 2
  pop-outs, and restart restore incl. pop-out seed (D49.6 intact). 3/3 + 4 existing green.
- Minor plan variance (not a finding): `ui/lwc_bridge.py` untouched — the op rides the
  existing `send_channel`, so no new envelope shape was needed. Architecture called it a
  wire detail; the tests prove the wire works.

## Entry 5 — P22-T3 quality review (done, no escalation)
- Page leg: `applyTz` sets tzMode/tzOffset, re-applies the shared `formatTick` path to
  both `tickMarkFormatter` and `localization.timeFormatter`, forces re-render via a
  viewport-preserving range re-assert; ET ticks format per-tick via `America/New_York`
  (`etLabel`, DST-correct) with scalar fallback; UTC stays plain math; stored bars
  untouched (A185). Crosshair/tooltip time shares the path, so AC-D62.2 follows AC-D62.1
  by construction — and AC3 tests enforce it. Pytest 4 + node 14 green.

## Entry 6 — P22-T4 quality review (done, no escalation)
- Repro-first diagnosis held: Magnet default governed the live chart because
  `applyCrosshair` never reached it. Normal pinned at creation + re-asserted on the tz
  re-render; `interaction.js` untouched (diagnosis cleared it — matches plan's
  "whichever file the diagnosis clears stays existing"); `freeLinePrice` clamps
  out-of-range to the pane edge per existing behaviour. 4/4 green.
- Cross-task coherence (chart.js T3+T4 overlap, serialized waves): the cumulative tree is
  coherent — T3's `applyTz` already carries the Normal re-assert, consistent with T4's
  pin. No conflict. Same for main_window.py T1/T2 (disjoint blocks).

## Standing scans (full-pass duties)
- B.6 mock-endpoint scan: grepped the reviewed diff for mock/fake/stub/simulat ×
  endpoint/client/service/server/api/harness — zero production hits (sole "harness" is a
  code comment). Clean.
- Usage-doc judgment: candidates `USAGE.txt` (pointer), `usage.md` (canonical guide),
  `docs/` untouched; all P22 tasks `doc_required: false`. Changes restore intended
  behavior (label room, toggle plumbing, crosshair mode, tick formatting); `usage.md`
  never documented the timezone toggle, so there is no doc section to update and no
  new user-facing surface needing one. No finding.
- Pack-prose spot-check (first task P22-T1 + guarantee-word tasks): T1's "never weaken
  an assertion" is enforced by AC2 (suites run unmodified); T3's "follows by
  construction" is enforced by AC3 tests; T4's "no snap anywhere" by AC1/AC2 tests. No
  contradictions.

Status: REVIEW_COMPLETE

## Pass 2 — P22 auto-redo close-out (2026-11-10)

Tier: FULL (phase-final pass — full duties regardless; light-pass conditions also
hold: VERIFY pass exit 0, 0 fail_fast, 0 overlaps, flags clean, sizes S/M, no
shared-file touches in scope).
Scope: P22-T2, P22-T5 (only results newer than the Pass-1 REVIEW_COMPLETE marker).
Ground truth consumed, not re-derived: precheck.json + test_verification.json
(verdict pass, exit 0, 77.56 s).

## Entry 7 — PRE-020 close-out (P22-T5 result file) — addressed
- Re-verified on the live tree: `docs/build/results/_archive/wave328_P22-T5.json`
  carries task_id='P22-T5', status=done, files_changed=['tests/test_d64_batch_gate.py'],
  tests 3/3 pass (AC1/AC2/AC3); task-graph P22-T5 status=done; full suite green.
  Flipped to addressed in place.

## Entry 8 — ESC-115 close-out (P22-T2 docstring token) — addressed
- Re-verified on the live tree, not the worker's word: `grep ui.main_window
  ui/lwc_view.py` = 0 hits (docstring now "the main-window ``_eastern_offset``
  helper"); the diff is prose-only (no import added, module boundary holds);
  targeted re-run (residue guard + d62 toggle + d64 gate) = 7 passed; full suite
  green. Flipped to addressed in place.

## Entry 9 — P22-T2/T5 quality (incremental, no new findings)
- T2 diff (ui/lwc_view.py): one-line docstring reword only; set_timezone op shape,
  fan-out, persistence unchanged from the accepted Pass-1 review. Minor plan
  variance (lwc_bridge untouched) stands as reviewed.
- T5: new result file only; gate file tests/test_d64_batch_gate.py unchanged and
  sound (3/3). T1/T3/T4 accepted Pass-1 — confirmed still held (full suite green,
  no new evidence; D1–P21 not reopened per scope guard).

## Standing scans (full-pass duties)
- B.6 mock-endpoint scan: no mock/fake/stub/simulat tokens in either scoped diff;
  no endpoint/harness cross. Clean.
- Usage-doc judgment: all P22 tasks doc_required=false; candidates USAGE.txt,
  usage.md, docs/ untouched. Restored-behavior batch, no new user-facing surface.
  No finding.
- Pack-prose spot-check (T1 first + guarantee-word tasks, restated): T1's
  "never weaken an assertion" enforced by AC2; T2's pin claims match its ACs;
  no contradictions.

No open P22 items. PRE-020 and ESC-115 verified and closed above.

Status: REVIEW_COMPLETE
