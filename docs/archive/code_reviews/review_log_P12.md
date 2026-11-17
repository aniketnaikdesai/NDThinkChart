# Code Review Log — Phase P12 (D52: 30-min timeframe)

Tier: **full pass** (phase-final; T1/T2 touch shared config surfaces, so the
light lane is not taken even though all mechanical gates are clean).
Scope: P12-T1…P12-T6 (all `done`; build_log ends READY_FOR_REVIEW).
Ground truth consumed, not re-derived: `precheck.json` (0 fail_fast, 0 overlaps,
coherent results), `test_verification.json` (verdict **pass**, exit 0, full
offscreen suite green). No task is `blocked`, so entry point A does not apply.
73 prior escalations, **0 open** — entry point C has nothing to act on.

## Finding P12-R1 — T1 config row: verified, no finding
- Implementation (`ibkr/market_data.py`, commit 817ca2b): exactly one added row
  `"30 mins":{"duration": "30 D", "bar_size": "30 mins"}` between `15 mins` and
  `1 hour`; the eight pre-existing rows byte-identical. Matches AC-D52.1,
  plan P12-W1, architecture §P12 (insertion ordered so the picker needs no
  code change).
- Tests `tests/test_p12_config.py` (T11/T12) assert exact mapping, slot index,
  full key order, and row count 9. Re-ran on live tree: pass.

## Finding P12-R2 — T2 1800s bucketing: verified, no finding
- Implementation (`data/bar_aggregator.py`): one added key `"30 mins": 1800`;
  bucketing rides the existing UTC-epoch `_period_start` grid, no anchor-set
  change. Correct per S-P12-2: ET offset is always whole hours, so the
  UTC-epoch 1800 grid coincides with ET half-hours in both EST and EDT, and
  09:30 ET (34200 s past an ET midnight) is always grid-aligned.
- Tests `tests/test_p12_buckets.py` (10 cases: key pin, DST-fold Sundays
  2024/2025/2026 half-hour starts at 5-minute sampling, 09:30 boundary
  Fri/Mon, forming-tick joins current half-hour) are genuinely red-first
  (pre-fix 300 s fallback fails each). Re-ran on live tree: pass.

## Finding P12-R3 — T3 planner/priming/probe: verified, no finding
- Production delta is docstring-only (`ui/ticker_session.py` per-span table
  gains the `'30 mins'` row in the `5 secs` group); planner/backfill logic
  correctly unchanged per AC-D52.3. Priming branch (`span <= 3600 → 5 secs`,
  `[60 S, 3600 S]`) covers the 1800 s elapsed span with no new bar size —
  consistent with D43/AC-D52.9 and the ESC-036 ceiling.
- Probe record `docs/d52_probe_record.md`: live TWS read-only probe,
  control + `(30 D, 30 mins)` both completed, 389 bars (~13 RTH half-hour
  bars/day × 30 d), no 321-class rejection, pass conclusion. AC-D52.7 met;
  no R104 escalation triggered.
- Tests `tests/test_p12_planner_probe.py` (T31 chunking/floor/hole,
  T32 priming shape + table assertion, T33 record shape): pass on live tree.

## Finding P12-R4 — T4 presentation inventory: verified, no finding
- Test-only task (`tests/test_p12_presentation.py`): picker order/parity from
  config order, visibility-dialog default-on round-trip with unchanged Minutes
  row, `minutes_for_timeframe('30 mins') == 30.0` via secs/60 fallback with
  an assertion that no explicit mapping line exists. No production change was
  needed and none was made — correct per S-P12-6/DG99. Pass on live tree.

## Finding P12-R5 — T5 mode parity: verified, no finding
- Test-only task (`tests/test_p12_mode_parity.py`): RTH/ETH distinct bar sets
  under mode-aware keys, bands + D21.4 collapse apply as intraday,
  `is_daily_or_coarser('30 mins') is False` with 15-min region parity.
  Pass on live tree.

## Finding P12-R6 — T6 gate + Q-61 pins: verified, no finding
- `tests/test_p12_gate.py` (committed in 817ca2b): probe-record assertions,
  history-intact checks (marker sentence, `### D41`–`### D51`, Current Tech
  Stack, AC-D16.1 nine-enumeration with stale-wording guard, AC-D16.8 six
  intraday, AC-D27.9 table row), no-skip/xfail scan that correctly excludes
  its own indirect marker definitions. Pass on live tree.
- Q-61 pin updates (commit 968dfdf: `test_d48_data_plane.py`,
  `test_ibkr_handshake_gate.py`, `test_p7_w3_wide.py`) consistently extend the
  expected config/order/seconds and duration pins to the approved 9-row set;
  `30 mins` is treated as added-never-widened (no approval record required),
  matching the D48 precedent. Re-ran all P12 + pin files together on the live
  tree: **79 passed**.
- Bookkeeping note (not a finding, no action): T6's result carries
  `files_changed: []` and the precheck `unknown_test_ids` warning because the
  gate suite ran as the full offscreen suite rather than per-test-id cases.
  The gate file exists in the tree, passes, and the independent
  `test_verification.json` full-suite run is green — nothing to route.

## Cross-cutting checks
- **Mock-endpoint scan (standing invariant):** grepped the reviewed diff for
  mock/fake/stub/simulat × endpoint/client/service/server/api/harness. One
  hit: a pre-existing code comment in `ui/ticker_session.py:156`
  ("tests / stub hosts") describing the volume-baseline fallback owner — not
  a mock endpoint in production, no production module imports a fake. **Pass.**
- **Usage-doc coverage:** `doc_candidates` = USAGE.txt, docs/, usage.md
  (recall scan; `docs/` touched = the D52 probe record, not a user doc).
  `usage.md:133` describes the picker range as "1 min – 1 month", which still
  covers the new entry, and the D48 section enumerates only the
  weekly/monthly precedent. No user doc names a timeframe enumeration that is
  now stale; all tasks have `doc_required: false`. **No doc finding.**
- **Consistency vs requirements/plan/architecture:** implementation matches
  D52.1–D52.8/AC-D52.1–AC-D52.8, plan P12-W1–W3, and architecture §P12
  (config row, 1800 grid, intraday planner/floor treatment, picker slot,
  5-secs priming row, probe gate, history intact). **No deviation.**
- **Unattributed working-tree changes** (`ALARM_AND_DRAWING_CODE_REVIEW.txt`,
  `POPOUT_AND_CHART_REVIEW.txt`, `POPOUT_CHART_CODE_TRACE_REPORT.txt`):
  pre-existing review artifacts, untouched by and unrelated to P12. No action.
- **Escalation close-out:** 0 open entries in `escalations.json`; nothing to
  re-verify or flip. `escalations.json` left unmodified.

## Verdict
P12 clean: 6/6 tasks verified against the live tree, full suite green per
independent verification, probe gate passed, no new findings to route.

Status: REVIEW_COMPLETE
