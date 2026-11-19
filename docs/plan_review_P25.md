# Plan Review — Phase P25 (D67–D70) — final pass (retry_2_of_3)

**Status: APPROVED**

**Pass type:** targeted re-validation of the revised `docs/plan.md` § *Phase P25* and
`docs/architecture.md` § *Phase P25* against my `CHANGES_REQUIRED` review (six items, all `owner: PLAN`).
**All six are addressed against the live tree**, nothing regressed, and the phase is activated below.
This file supersedes the CHANGES_REQUIRED review of the same path; that cycle's Required Changes are
re-stated one by one under *RC verification* with the evidence I re-checked this pass.

**Phase gate:** **open** — `docs/code_review/review_log_P24.md` ends `Status: REVIEW_COMPLETE`
(`2026-11-18 16:39:46`), newer than `docs/build/build_log.md`'s terminal `Status: READY_FOR_REVIEW`
(`16:28:41`). Nothing earlier is in flight, so P25 finalises here (no provisional state).

**Lint:** `plan_lint.py --phase P25` → `LINT PASS: P25 (canonical sections); 0 failure(s), 1 warning(s)`
— the warning is the known `Frozen Interfaces module not found in codebase map: /` parse artefact
(same shape P23/P24 carried). Re-run after the status flip: still PASS, same single warning.

**Stamps (unavailable — tooling, not Plan):** `pipeline_state.py hash-section` fails on every phase in this
repo because `PHASE_HDR_RE = ^##\s+Phase\s+(P\d+)\s*$` requires a bare heading while each phase heading
carries a title after the id (verified in the script, `pipeline_state.py:221`). Same P23/P24 observation —
an Orchestrator-script limitation, not a Plan finding and not routed. Freshness therefore falls back to
mtime and points the right way: `requirements.md` **16:10:48** → `plan.md` / `architecture.md` revised
**16:33**, P25 section ends `READY_FOR_TASK_MANAGER` now that this review approves it.

**Requirements drift:** **none.** `docs/requirements/requirements.md` mtime is unchanged since the
previous pass (16:10:48), its P25 section still ends `Status: READY_FOR_PLAN`, and `git diff` shows
requirements changes only as additions (batch header, glossary, P25 record) — no P25 criterion moved.

**Escalations:** `docs/code_review/escalations.json` — **119 entries, 0 open** (nothing routed to PLAN).

**Baseline / delta:** HEAD `94d6119`; the working tree carries **docs only**. `git diff -U0` gives one
insertion hunk per doc at the P25 boundary (`plan.md` `+7033,364`; `architecture.md` `+10211,396`) and
additions-only in `requirements.md`, so **D1–P24 are untouched**. The delta is exactly **D67–D70**;
`P26`/`P27` appear only as ownership boundaries ("the wave is theirs"), no D71+ item is planned.

---

## RC verification (each re-checked in the tree, not taken on Plan's word)

| RC | Disposition | Evidence from this pass |
|---|---|---|
| **RC-P25-1** — D70's page premise | **Accepted** | Premise re-confirmed: `chart.js:1672-1689` (`upsertRow` → `mergeRows` for candles), `envelope.js:142-163` with the unconditional `byTime[one.time] = one` at `:156`, `chart.js:1780` (`lwSnapshot()` unfiltered). The revision now **changes the fold**, which is *stronger* than the filter-only-upsertRow option I suggested: `mergeRows` applies the rule in both branches (`set_bars`/`set_volume` skip, `update_bar` deletes), `upsertRow` sends `{time}` only for a whitespace row, and the parity runs `lwApplyOps`/`lwSnapshot()` over **both** fixtures. This matches `AC-D70.1`'s second clause ("equals the page's merge") and the glossary (`requirements.md:6803`: a whitespace row "is not a bar") — coherent, and restating the criterion was correctly refused. File set is now complete: `envelope.js`, `chart.js`, `envelope.test.js` added to **P25-03** alongside `chart.test.js`, and all four are in P25-04's delta allowlist. Codebase Summary agrees: the two page rows describe today's behaviour (`mergeRows` unconditional; `upsertRow` unfiltered) and name the change in the disposition column; the `docs/codebase-map.md` P25 note was updated the same way. `AP-P25-11` records the justification, and "`mergeRows` is not the display fold" is true (`applyRows` → `seriesRows`/`barRows`, `chart.js:1658-1670`, `:467-491`), so AC-D21.4.4 gap slots survive. No rejected answer. |
| **RC-P25-2** — `_wall_now` position | **Accepted** | `TickerSession(key, self)` is at `ui/main_window.py:1077` (the **only** construction in the repo) inside `get_or_create_session`; the late-bound `lambda: self._now_ts()` therefore lands before every `set_bars`. Both load paths verified line-exact: cold restore `prepare_load` `:1218` → `set_bars` `:1220` (through `get_or_create_session` at `:1217`), primary load `prepare_load` `:3162` → `set_bars` `:3173`. `_now_ts` is the existing seam at `:3302-3304`, and `tests/test_d48_mode_parity.py:171` patches it (`win._now_ts = lambda: NOW`, `NOW = 2026-11-02 12:00 ET` at `:57`), so the restated docstring sentence is now true under test. |
| **RC-P25-3** — `push` contract | **Accepted** | The contradiction is gone and uses `prime_aggregator`'s form in all four places (P25-01 item 3, System Components, Frozen Interfaces bullet, Codebase Summary row): `push` is the only place `_AggState` is created (`data/bar_aggregator.py:158-168`, state created in `push` after the `ts <= _last_pushed_ts` skip), so it records `first_ts = ts` there while its observable contract (dedup, rollover `is_new_candle=True`, merge, callback) is unchanged. `AC-D67.2`'s partial fixture now says it drives `on_historical_bar` → `BarAggregator.push` (suite case (b)), and `on_historical_bar` does call `agg.push(...)` (`ui/ticker_session.py:1277-1299`), so the fixture reaches the real write path. |
| **RC-P25-4** — replay guard | **Accepted** | `adopt_period_base` now **preserves** `_last_pushed_ts` in every place that states the mechanism (P25-01 item 3, S-P25-1, System Components, Data Model *Period base*, Non-Functional, AR-P25-1) with the safety argument ("a base's data is older than the next live tick; arrival is oldest-first, so the guard only rejects a bar the base or the replaced state already counted"). Suite case **(h)** exists and asserts both halves (a re-pushed ts does not re-count into the base-derived volume; a newer ts still merges). This is the only answer consistent with R161/AR-P25-1, and nothing in the plan needed the reset. Residual non-blocking note: a tick landing between the base row's coverage end and `_last_pushed_ts` is dropped rather than merged — inside the boundary already recorded as **FI-P25-1** (a stale-but-present base covers the head; the tail is live-only), so no new criterion is needed and nothing is routed. |
| **RC-P25-5** — marker rollover | **Accepted** | One rule replaces the ambiguous sentence: `target = bar.ts if bar.partial else None`, emitted only when `target != _partial_ts`, driven on every emitting tick — explicitly including `update_live_bar`'s `new_period` branch (the rollover edge, `ui/lwc_view.py:2578-2599`) — and in `set_series` against `rows[-1]`. `update_bars` and `update_last_bar` delegate to those two methods (`ui/lwc_view.py:2250-2261`), so there is no third emitting path left unruled. Page semantics are stated (one marked time; `partial: true` moves; `partial: false` clears only on a match; a time absent from the rows is not applied), the node case asserts the **move**, and suite case **(g)** asserts both rollover directions — including the completed candle losing its mark, which is `AC-D67.2`'s negative arm at the edge Journey 65 names. |
| **RC-P25-6** — fence literals | **Accepted** | (a) `TIMEFRAME_SECONDS` = **ten** keys, cited as ten and listed ten (`data/bar_aggregator.py:13-28`); no "nine" survives anywhere in the P25 sections. (b) The three bridge constants are cited as **module-level** `ui.lwc_bridge.ENVELOPE_VERSION` / `.COALESCE_MS` / `.LIVE_OPS` at `:82-88` (verified: `:82`, `:85`, `:88`), with the `LB.` alias note (`ui/lwc_view.py:2807`) and the explicit "not `LwBridge` class attributes". (c) P25's defect headings are `#### D67`–`#### D70` (`requirements.md:6807/6815/6822/6828`), and the record's real shape was correctly re-derived: `### D41`–`### D53` are defect entries, `D54`–`D66` sit in `## Phase P<n>` headers and `#### Journey` titles (verified per id) — so P25-04 item 1 asserts **presence per id in a heading** instead of the `### D41`–`### D66` shorthand, and no longer claims a literal prefix for every id. (d) The `set_bars` frozen bullet now reads "signature and emit contract frozen … the base-adoption side effect inside it is this phase's change (NOT frozen)", mirroring `prime_aggregator`. Every other frozen entry spot-checked this pass (`push`, `period_start`, `current_bar`, `week_bucket_start`, `month_bucket_start`, `Bar` field list/order, `session_windows`, `ensure_rt_subscribed`, `release_rt`, `get_bars`, `on_realtime_bar`, `attach_view`/`detach_view`, pop-out `attach`/`detach`/`closeEvent`, `send_ops`/`flush`/`apply_ops_to_bars`/`replay_log`/`handle_page_ready`/`counters`, the four `LwChartView` methods, `KNOWN_SERIES`/`CHANNELS`, `lwApplyOps`/`lwSnapshot`) — still verbatim; the missing `first_session_open` is correctly `[new]`, not frozen. |

**Rejected:** none. Every RC answer was accepted; RC-1's answer is the stronger of the two coherent
options and is preferred for that reason.

**Editorial corrections I made at activation (no new decision):** (1) `docs/plan.md` P25-01 item 3 pointed
at "item 4 says why" for the guard's rationale — item 4 is session wiring and says no such thing; the
pointer now names `S-P25-1` / AR-P25-1, which carry it. (2) the section's closing status flip.

---

## Validation steps (targeted scope: the six RCs plus the consistency ripple each touches)

- **Requirements coverage — PASS.** Every P25 id, Journey 65–67, A220–A224 and R160–R164 still maps to a
  wave through the Traceability table; the two coverage gaps this cycle closed (`AC-D70.1`/`AC-D70.2` page
  half; `AC-D67.2`'s rollover negative arm) now have implementation paths and fixtures inside their waves.
- **Architecture completeness — PASS** (unchanged from the full pass; revision touched only S-P25-1/2/6,
  the summary rows, the D70 tech-stack row, the frozen/NOT-frozen split and one assumption).
- **Consistency — PASS.** Revision notes, plan and architecture now agree on D70's symmetry (fold + display
  branch), on the `_wall_now` seam position, on `push`, on the preserved guard, on the marker rule and on
  the fence literals; no "byte-identical" claim survives against `push`; no stale "nine keys" or
  `LwBridge.<const>` literal survives.
- **Plan quality — PASS.** Four waves, dependency shape `01 → 03 → 04`, `02` parallel; sizes M/S/S/S; each
  wave carries goal, covered criteria, files, ordered deliverables, exit condition, do-not list. No
  task-level breakdown, no task graph, no per-task test spec.
- **Task Manager readiness — PASS.** No architectural decision is left open: the fold's rule, the seam's
  position, `push`'s edit permission, the guard's fate, the marker's rollover rule and every fence literal
  are stated as decisions a worker executes.
- **Existing-repo compliance — PASS** (re-checked on the touched rows). Codebase Summary remains
  substantive and now disagrees with nothing: the `envelope.js` / `chart.js` rows describe today's
  behaviour correctly and name the P25 change in the disposition column; the map note matches; labels
  `[existing]` / `[new/changed]` / `[new in P25]` are present on every changed item; nothing existing is
  replaced and no `[new]` production module appears.
- **Frozen Interfaces — PASS** (all four checks; evidence in RC-6). Nothing under construction is frozen
  whole, nothing consumed-but-unmodified is missing, every owner module resolves, no duplicates.
- **Codebase map — PASS.** Sections resolve, spot-checked key files exist, the P25 note now names the
  page fold change and labels every edited file `[changed in P25]`, the skeleton is the 2026-11-19
  regeneration (274 code files, 23 test-impact rows), no deleted-module entry.
- **Pending doc sync — PASS.** `docs/pending_doc_sync.md` is absent (folded into architecture § *Quick-lane
  folds*, verified again: `USAGE.md` carries neither the expiry rendering nor a retry bound).

**Findings owned outside Plan:** none.

---

## Final Decision

**Status: APPROVED**

Activated: `docs/plan.md` § *Phase P25* now closes `Status: READY_FOR_TASK_MANAGER`. Architecture stays
as drafted (the phase's cumulative updates already sit under its own heading, with the relationship labels
and the frozen/NOT-frozen split Plan authored). Task Manager may proceed.
