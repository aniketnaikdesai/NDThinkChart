# Code Review — Phase P25 (D67–D70: silent wrong data — forming week/month candle, stolen live feed, out-of-order flush, whitespace rows)

**Pass type:** phase-final → **full pass** (mandatory on the phase-final pass regardless of tier; the precheck's `files_verified: []` and its 23 fail_fast flags also ruled a light pass out).
**Scope (incremental):** P25-T1, P25-T2, P25-T3, P25-T4, P25-T5 — no `review_log_P25.md` existed before this pass, so all five are in scope (plus Q-79, committed as `7d93819`).
**Tree:** `76713af` (*P25 build: period base + forming-candle marker, pop-out hold latches, arrival-ordered flush, one whitespace rule*) + `7d93819` (*Q-79*); phase base `08cade8`, delta base `94d6119`.
**Inputs:** `precheck.json` (23 fail_fast entries — adjudicated in §4), `test_verification.json` (**verdict pass, exit 0, 211.77 s**, newer than `build_log.md`), `build_log.md` waves 388–393, the five archived results, `task-graph.json` P25 ACs, `requirements.md` D67–D70 / `AC-D67.1`–`AC-D70.3`, `plan.md` Phase P25 (P25-01…P25-04, AP-P25-1…11), `architecture.md` Phase P25.
**Result: 3 findings (ESC-126 should-fix, ESC-127 nice-to-have, ESC-128 nice-to-have). No blocking finding. PRE-022 closed (`addressed`). Owner gates G1/G2 NOT run — named, not claimed.**

---

## 1. Findings

| id | task | route | category | severity | one line |
|---|---|---|---|---|---|
| ESC-126 | P25-Q79 | TASK_MANAGER | quality | should-fix | Q-79 removed the import-time `QApplication` from one suite; two other suites still create one at import time and reproduce the exact Q-79 failure when collected first. |
| ESC-127 | P25-T4 | BUILD | consistency | nice-to-have | The "one whitespace rule" is not one predicate: Python treats a candle row as whitespace iff `close is None`; the page treats it as whitespace if `open` **or** `close` is null. Measured divergence on an op both validators accept. |
| ESC-128 | P25-T2 | TASK_MANAGER | gap | nice-to-have | D67 adds a user-visible amber marker on the forming week/month candle; no user-facing doc was touched and `usage.md` documents every user-visible phase addition. Nothing in `usage.md` is false — the affordance is undocumented. |

No `bug`, `security` or blocking finding. Detail in the escalations; context per task below.

---

## 2. Task-by-task (diff-first, `git show 76713af -- <files>`, plus `7d93819`)

Every claim below was checked against the diff, not against the worker's prose. The phase commit was also verified to be exactly the allowlist (§4).

### P25-T1 — `set_partial` transport (page + bridge), one guarded marker

- **`envelope.js`:** `validateOp` accepts `set_partial` only as a directive — integer `ts` (`isInteger`), boolean `partial`, and an explicit rejection if `series` or `cols` is present (`envelope.js:82-93`). An unknown `op` still falls through to "unknown op". Matches AC-D67.1 / P25-T1-AC1.
- **`chart.js`:** the directive is lifted before `describeOp` (`:1586-1596`); page-local `partialMarkedTs` + one plugin handle (`:357-368`); `applyPartialMarker` is guarded on `createSeriesMarkers` and re-applied after `applyRows` (for `series === "candles"`, `:1737-1745`), after `upsertRow`, and once per `applyOps` (`:1716-1719`) so a directive-only envelope also re-applies. A mark whose time is absent from `snapshot.candles` draws nothing (`partialMarkerEntries`). `PARTIAL_MARKER_COLOR = "#fbbf24"` (`:64`) differs from `LW_UP_COLOR` / `LW_DOWN_COLOR`.
- **`ui/lwc_bridge.py`:** `_check_op_shape` mirrors the page's checks and additionally rejects a `bool` `ts` (`:144-162`); `apply_ops_to_bars` skips `_DIRECTIVE_OPS` explicitly (`:270-273`) so the reconstruction is unchanged (asserted in `tests/test_lwc_bridge.py::TestPartialDirective`).
- **Tests:** JS test files are **pure additions** (`chart.test.js` +189/−0, `envelope.test.js` +129/−0 — `--numstat`), `tests/test_lwc_bridge.py` +34/−0. `node --test chart_assets/lwc/` → 124 pass, 0 fail (my run).

### P25-T2 — D67 part 2: period base, partial flag, skipped prime, marker leg

- **`data/models.py`:** `partial: bool = field(default=False, compare=False, repr=False)` — excluded from equality/repr so no fixture shifts meaning; `data/bar_cache.py::save_bars` enumerates nine columns and never passes `partial`, so it is genuinely transient (no read-back exists anywhere).
- **`data/bar_aggregator.py`:** `_AggState.first_ts` written at the single state-creation site in `push` (`:225-233`) and as `period_start` in `adopt_period_base` (`:172-198`); the adoption **replaces** the state (cannot double-count) and deliberately does **not** touch `_last_pushed_ts` (`:217-218` is the guard it relies on); `drop_period_base` only clears a base-derived state (`:200-209`); `covering_since` returns `first_ts` (`:156-170`). Confirmed against AC-D67.5 and the "redelivered tick not re-counted" requirement.
- **`services/market_calendar.py`:** `first_session_open` is holiday-aware (`trading_days`), mode-scoped (`_EXT_OPEN` 04:00 vs `_RTH_OPEN` 09:30 — the same constants `session_windows` uses), and `None` before the first open.
- **`ui/ticker_session.py`:** `set_bars` is the single replacement choke point and adopts/drops the base after the cap and before `bars_refreshed` (`:497-536`); `_stamp_partial` (`:628-655`) sets `partial` iff `covering_since > first_session_open(period_start(bar.ts), _wall_now(), _wave_extended_hours)` — a base-backed candle reports `first_ts == period_start` so it can never be partial, and non-calendar timeframes are forced `False`. `_wave_extended_hours` is assigned in `prepare_load` (`:1202`), so RTH/ETH are not mixed. The prime skip (`:1585-1588`) compares the base's period to `period_start(now)` and returns `False` on both the fresh and `retrying=True` entries.
- **`ui/main_window.py`:** exactly three lines — `session._wall_now = lambda: self._now_ts()` at session creation (`:1075-1080`), i.e. late-bound, before any `set_bars` path. `TickerSession._wall_now` defaults to `time.time` (`:196-204`).
- **`ui/lwc_view.py`:** `_advance_partial` (`:2692-2716`) emits only on a transition, and the op is appended **after** the rows in all three paths — `set_series` (`:2553-2556`, after the viewport op), the rollover branch (`:2660-2663`) and the tick path (`:2679-2682`).
- **Priming-skip starvation check (asked explicitly):** cannot starve the tail. A skipped prime returns `False`, which is the existing "attach the live feed" signal (documented in the docstring at `:1552-1557`); the base-backed state then merges live 5-second bars through `push`, and `test_ac5_replay_guard_survives_adoption` proves both halves — the redelivered ts (`TUE_1000`, vol 999) is rejected (volume stays 5000, high 210, close 205) while `TUE_1000+5` merges (5100 / 205.5). `test_ac5_rollover_*` drive the same merge via `ensure_rt_subscribed` + `on_realtime_bar`.
- **Tests:** `tests/test_d67_forming_candle.py` (573 lines, 12 tests incl. parametrisation) — `test_ac4_current_period_base_skips_the_prime` asserts zero requests on both entries; `test_ac4_no_base_issues_only_a_pair_inside_the_accepted_set` pins `1 min` / `86400 S` inside the accepted window; `test_ac1`/`ac2`/`ac3` cover the three head-coverage cases; `test_ac6_set_series_emits_one_marker_after_the_rows` asserts the marker is after both `set_bars` and `set_volume` and last in the envelope. `tests/test_d48_mode_parity.py` is a **docstring-only** change (+7/−5, no assertion touched) — AP-P25-9 kept.

### P25-T3 — D68 hold balance

- `_hold_acquired` is written **only** at the two places where `ensure_rt_subscribed()` returned (`popout_window.py:437`, `:548`), cleared **before** the release in attach's unwind (`:478-490`) and in `detach` (`:588-592`), so a failing release is not retried into a double release. `detach` sets `_closed = True` first (`:554`) and `_retry_rt_subscribe` consults it before the membership guard (`:517-523`), so a post-close retry acquires nothing.
- Each acquisition has exactly one matching release site; `git show 76713af -- ui/ticker_session.py` contains no hold-API change (`ensure_rt_subscribed` / `release_rt` / `_rt_holders` untouched), and `tests/test_p13_hold_fix.py` is not in the delta (P25-T3-AC6 satisfied by construction and by the green full suite).
- **Latent, no action:** `_closed` is never reset, so a hypothetical `attach()` on a previously detached window would acquire normally but never retry after a pacing rejection. `attach` is only called on freshly constructed pop-outs (`main_window.py:1185`, `:1551`), so there is no reachable path; recorded so a future re-attach feature does not inherit it silently.
- **Tests:** `tests/test_d68_hold_balance.py` (294 lines, 5 tests / 6 cases) uses a fake realtime manager at the IBKR boundary and a real `TickerSession`, both close orders parametrised; `test_deferred_popout_close_releases_nothing` asserts `fake.unsubscribed == []` and `_hold_acquired is False`, not merely a holder count.

### P25-T4 — D69 arrival-ordered flush + D70 one whitespace rule

- **Sequence stamping:** `_stage` stamps every accepted op (`lwc_bridge.py:412-428`); live `update_bar` coalescing keeps the *newest* op and its seq.
- **Supersession:** `flush` (`:446-495`) sorts by seq, computes `last_replace[series]` over `{set_bars, set_volume, clear}`, drops every op of that series with `seq < cutoff`, emits data ops ascending, then directives ascending.
- **"No series emitted twice" — true by construction:** all full replaces of a series share the `series` key, so the max-seq replace has `seq == cutoff` (kept) and every other replace has `seq < cutoff` (dropped) ⇒ at most one full replace per series per envelope; the emit loop visits each surviving tuple exactly once. A same-seq duplicate is impossible (the counter is monotonic). `clear` + `update_bar` keeps both because `clear`'s seq *is* the cutoff — `test_ac5_clear_then_update_yields_one_bar` asserts `["clear", "update_bar"]`, and the Python reconstruction therefore matches what the page sees (I specifically re-checked this case: dropping the clear would have diverged from `apply_ops_to_bars`).
- **Directives after rows:** `_DIRECTIVE_OPS` bypasses the cutoff branch and is appended last; `test_ac5_update_after_the_replace_applies_as_the_last_data_op` asserts `[set_bars, update_bar, set_partial]`.
- **`_op_log` / replay untouched:** `send_ops` extends the log at accept time (`:400`), `replay_log` copies it (`:659-661`); `test_ac2_one_replace_per_series_and_arrival_order_survive` asserts `replay_log() == arrival` and that no key is added.
- **Whitespace:** Python `set_bars` filters `c is not None` (`:286`), `update_bar` pops the ts on a None close (`:291-295`); the page skips/deletes via `isWhitespaceRow` in `mergeRows` (`envelope.js:159-200`) and sends `{time}` only from `upsertRow` (`chart.js:1745-1770`), including the derived line leg and the volume branch.
- **Parity is real, not a mirror:** `test_ac4_page_parity_for_whitespace_update_and_replace` runs the **real** `chart.js` + `envelope.js` in node against a stubbed document and a fake LWC tree, calls `window.lwApplyOps` and `window.lwSnapshot()`, and compares the page's candles to `apply_ops_to_bars` element-for-element for both fixtures (`test_d69_d70_bridge_contract.py:281-470`). That is the strongest evidence in the phase.
- **Residual asymmetry → ESC-127** (measured: `apply_ops_to_bars` keeps `(1, None, 2.0, 0.5, 1.0)` for an `open=None`/`close=1.0` row that `envelope.js::validateOp` accepts and `mergeRows` drops). Unreachable from any producer today (`build_series_ops` nulls all four value slots together), hence nice-to-have.
- **Counter note (adjudicated, not escalated):** `_counters["emitted"] += len(ops)` now counts survivors rather than staged ops. `emitted` still means "ops that crossed"; no test or code asserts `emitted == received`; `received` / `queued` / `coalesced` are untouched.

### P25-T5 — fence suite, delta record, owner gates

- `tests/test_p25_fence.py` (181 lines, 10 tests) reads the live artefacts: the marker sentence, presence-per-id for D41–D66 in a heading (not a literal `### D<n>`), the `#### D67-D70` and `Journey 65-67` headings, the AC endpoints + every AC-bearing defect, A1–A224, R1–R164, `**Current Tech Stack:**`; the three constants are read off `ui.lwc_bridge` (module, not `LwBridge`); the marker colour is parsed from `chart.js` and asserted different from both candle colours. No literal file/line/op counts — correct, and it does not re-pin the phase commit (P24 precedent).
- **Delta scope (AC3):** I re-derived it myself — `git diff --name-only 08cade8 76713af` is the ten production files below plus the four new suites (incl. the fence), `tests/test_d48_mode_parity.py`, `tests/test_lwc_bridge.py` and `docs/`. Nothing outside the allowlist; `7d93819` adds only `tests/test_d67_forming_candle.py` and the orchestrator's `escalations.json` entry.
- **Owner gates:** the result records `owner_gates.G1` / `G2` as "owner-run, not run" with `claimed: false` — correct, and I claim neither (§6).
- **Result-format observation (no escalation, see §5):** the archived `wave393_P25-T5.json` lacks `tests` and `files_changed` (the precheck's `malformed_result`), and its `delta_scope` records no file listing (a note only). The substance is verified by me independently.

### Q-79 (`7d93819`)

- The dead module-level `_APP = QApplication.instance() or QApplication([])` is gone (0 remaining `_APP` references in the file) and replaced by a session-scoped autouse `_qt_app` fixture created at test time with `QApplication(["pytest"])`; the AC6 seam test now drains deferred deletes before the app goes away. **No assertion changed** — the diff is the fixture + an import + a `finally` addition.
- Pair test green: `pytest -q -m 'not webengine' tests/test_d67_forming_candle.py tests/test_lwc_render_smoke.py` → **25 passed** (test_d67 imported first, the ordering that used to abort). But the *invariant* is not closed — two other suites still create a `QApplication` at import time and reproduce the identical failure when collected first → **ESC-126**.

---

## 3. Answers to the four plan-level questions

- **D67/R-02** — all seven clauses hold: adoption replaces (never adds) and preserves `_last_pushed_ts`; the prime is skipped when a current-period base exists, on the fresh and retrying entries; the partial flag is `covering_since > first_session_open(period_start)` and is unreachable for a base-backed state; `_wall_now` is late-bound at `get_or_create_session` before any `set_bars`; the marker op rides after the rows; the skipped prime cannot starve the tail because a skipped prime is the "attach live" signal and live 5-sec bars merge into the base; `Bar.partial` is transient/presentation-only (not persisted, `compare=False`).
- **D68/R-06** — detach releases at most the one hold it acquired, a post-close retry acquires nothing, no double-release (clear-before-release) and no leak (one acquisition site ↔ one release site); the session hold API is unchanged and its fence is untouched.
- **D69/R-19** — arrival-ordered emission with one replace per series is true by construction (proof in §2/P25-T4), directives still last, `_op_log`/replay keep plain arrival order with full fidelity.
- **D70/R-33** — both sides agree that a None-close row is not a bar, proved through the real `lwApplyOps`/`lwSnapshot` (not a mirror). One residual predicate asymmetry, unreachable from today's producers: ESC-127.

---

## 4. Precheck adjudication (23 fail_fast entries)

- The precheck produced **22 `unchanged_claimed_file`** flags (P25-T1 6, P25-T2 8, P25-T3 2, P25-T4 6) and **1 `malformed_result`** (P25-T5) — 23 entries, all listed in `precheck.json` `escalation_entries` PRE-023…PRE-045.
- **The 22 are INVALID — the orchestrator's judgement is confirmed.** `review_precheck.py` compares against the working tree/index, not against the phase base; the phase was committed at `76713af` at **22:04:54Z**, and the precheck ran at **22:26:43Z**. `git status --porcelain` is clean apart from `docs/tasks/task-graph.json` (build_wave status bookkeeping). Every claimed file is in `git diff --name-only 08cade8 76713af` — I checked the list by name, not just by commit time: `chart_assets/lwc/{envelope.js,chart.js,envelope.test.js,chart.test.js}`, `ui/lwc_bridge.py`, `tests/test_lwc_bridge.py`, `data/models.py`, `data/bar_aggregator.py`, `services/market_calendar.py`, `ui/ticker_session.py`, `ui/main_window.py`, `ui/lwc_view.py`, `tests/test_d48_mode_parity.py`, `tests/test_d67_forming_candle.py`, `ui/popout_window.py`, `tests/test_d68_hold_balance.py`, `tests/test_d69_d70_bridge_contract.py`. Consequence: `files_verified: []` for all five and no doc discovery beyond the candidates is a precheck artefact — I verified the footprint from the commit diff myself.
- **The 23rd (`malformed_result`, P25-T5) is factually true but benign.** The archived result genuinely lacks `tests` / `files_changed`: the worker exhausted its step budget before writing the result and the orchestrator recorded it from the worker's verbatim selfcheck stamp (selfcheck verdict pass, `tests/test_p25_fence.py` 10 passed) — `build_log.md` wave 393 says so. Re-running T5 would rebuild nothing and could only rewrite a record; I re-ran the fence suite instead (green) and verified the substance independently. No PRE entry was created for it (the orchestrator correctly withheld the invalid batch; this one is a record-format gap, not a code/test failure), and none is warranted.

---

## 5. Adjudicated, not escalated (measured, then cleared)

- **`docs/requirements/requirements.md` in the build commit is a pure block move.** `git show 76713af -- docs/requirements/requirements.md` = 8 added / 8 removed, same text: the Batch-38 "Current work in this run" note moved from inside the p14/p15-pinned span to just after the `## Existing Repository` heading (above the pinned marker sentence). The protected span is byte-identical again — `test_p14_cache_guard.py::test_t34_history_markers_intact` and `test_p15_surfacing.py::test_t33_history_markers_intact` pass in my own scoped run (the guard pins `2fe7b1ec…`). No D67–D70 criteria were added or changed by the build.
- **`docs/tasks/task-graph.json` (620/−285) + `execution_graph.json` + `task_manager_notes_P25.md` arrived in the build commit.** Docs-only, inside the allowlist's `docs/`; the P25 graph was Task-Manager-authored but committed with the phase instead of at plan time. Bookkeeping hygiene only — no scope breach, no action.
- **P25-T5's `delta_scope` records no file listing**, only a note about `tests/test_lwc_bridge.py` being P25-T1's authorised footprint rather than P25-T5's. AC3's substantive claim (subset of the allowlist) is true — I re-derived it — so the gap is in the record, inside an already-known-incomplete result.
- **`_counters["emitted"]` now counts surviving ops** (see §2/P25-T4). Semantics preserved; nothing asserts otherwise.
- **`_bars[-1]` (not `_plotted[-1]`) drives the `set_series` marker.** A trailing bar filtered out of the plotted view would name a ts absent from the page rows; the page's `partialMarkerEntries` guards it (draws nothing), so the worst case is a missing mark, never a wrong one.
- **Duplicate escalation id `PRE-022`** exists twice in `escalations.json` (P23-T26, addressed; P25-T5, closed this pass). Both were orchestrator-appended; ids are not unique. Harmless here, but a machine keying on id alone could misread it — noted for the orchestrator, not something I can renumber without rewriting history.

---

## 6. Standing duties

- **Mock-endpoint containment (B.6, blocking invariant):** the production diff (`data/models.py`, `data/bar_aggregator.py`, `services/market_calendar.py`, `ui/ticker_session.py`, `ui/lwc_view.py`, `ui/lwc_bridge.py`, `ui/popout_window.py`, `ui/main_window.py`, `chart_assets/lwc/envelope.js`, `chart_assets/lwc/chart.js`) grepped for `mock|fake|stub|simulat` crossed with `endpoint|client|service|server|api|harness|data` → **0 matches**. No production module imports a test fake; no endpoint/client/server was introduced. **Clean.**
- **Usage-doc judgment:** `precheck.json` `doc_candidates` = `USAGE.txt`, `docs/`, `usage.md`, all `touched: false`; `usage.md` is the canonical guide (its own header says so) and documents each user-visible addition by phase. The D67 partial marker is a new user-visible affordance and is undocumented — nothing in `usage.md` becomes false, so this is a gap, not staleness → **ESC-128** (nice-to-have, TASK_MANAGER, with the `pending_doc_sync` route named as the cheaper option). `USAGE.txt` is a pointer/quick-start and correctly untouched. The zoom cluster is P30's, not this phase's.
- **Pack-prose spot-check (sampled: P25-T1 = first task in the graph; P25-T4 and P25-T5 = the only packs containing a guarantee word, "never"):** no prose contradicts an AC, and each stated guarantee has an enforcing test — T1's "re-applies after every rows application" → the four marker cases in `chart.test.js`; T4's "never a hand-written JS mirror" → the node `lwApplyOps`/`lwSnapshot` parity test; T5's "never a literal `### D<n>` prefix" → `test_every_record_defect_id_is_present_in_a_heading`. T2's "leaving `push`'s observable contract, `_last_pushed_ts` and `TIMEFRAME_SECONDS` alone" also holds in the diff. **Clean.**
- **Owner gates:** **G1** (rendered forming week/month candle against the rendered current-period row) and **G2** (pop-out close with the main feed live) were **NOT run** in this review and are not claimed. They remain the owner's, per AP-P25-7; `AC-D67.2`/`AC-D68.1` are offscreen-asserted only.

---

## 7. Escalation close-out

- **PRE-022 (P25-T5, BUILD, blocking, `[orchestrator]`) → `addressed`.** Re-verified myself, not from the orchestrator's say-so. *Commit-state blocker:* the phase is committed at `76713af` and the tree is clean apart from `docs/tasks/task-graph.json`, so `test_d64_batch_gate.py::test_p22_t5_ac2_shared_seam_record` passes. *Span blocker:* the navigation note is outside the pinned span (block move only) and both history guards pass, with the span hashing back to the recorded `2fe7b1ec…`. *Full gate:* `test_verification.json` pass / exit 0 / 211.77 s, newer than `build_log.md`. T5's artefact is green (fence 10 passed). The entry's own consequence — T5 finalizing `done` — is already reflected in `build_log.md` and the archived result.
- No other open entries existed before this pass; ESC-126/127/128 are new.

---

## 8. Independent runs (mine, this pass)

| command | result |
|---|---|
| `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -m 'not webengine' tests/test_p14_cache_guard.py tests/test_p15_surfacing.py tests/test_d64_batch_gate.py tests/test_p25_fence.py tests/test_d68_hold_balance.py tests/test_d69_d70_bridge_contract.py tests/test_d67_forming_candle.py` | **64 passed** |
| `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -m 'not webengine' tests/test_d67_forming_candle.py tests/test_lwc_render_smoke.py` (Q-79 pair, former failing order) | **25 passed** |
| `node --test chart_assets/lwc/` | **124 pass, 0 fail** |
| `… pytest -q -m 'not webengine' tests/test_p7_w4_streaming.py tests/test_lwc_render_smoke.py` | **1 failed** — `ImportError` at `test_lwc_render_smoke.py:665` (ESC-126 repro) |
| `… pytest -q -m 'not webengine' tests/test_p7_w4_deferral.py tests/test_lwc_render_smoke.py` | **1 failed** — same error (ESC-126 repro) |
| `apply_ops_to_bars` vs `envelope.js::mergeRows` on `{open:null, close:1.0}` (both validators accept) | Python `[(1, None, 2.0, 0.5, 1.0)]` vs page `[]` (ESC-127 repro) |
| Orchestrator's full suite (`test_verification.json`) | pass, exit 0, **211.77 s** — ground truth for "the suite passed" |

---

Status: REVIEW_COMPLETE

---

# Re-review pass — P25 rework (`a22ecf6`)

**Pass type:** phase-final → **full pass** (mandatory on the phase-final pass regardless of tier; independently, the precheck's four cross-task overlaps on shared files — `envelope.js`, `envelope.test.js`, `tests/test_d69_d70_bridge_contract.py`, `ui/lwc_bridge.py` — rule a light pass out).
**Scope (incremental):** P25-T4 (rework, wave 398), P25-T6, P25-T7, P25-T8. T1/T2/T3/T5 are **confirmed unchanged** (§6) and not reopened.
**Tree:** `a22ecf6` (*P25 rework: single-sourced whitespace predicate, import-time QApplication invariant, partial-marker docs*) on top of `76713af` + `7d93819`; working tree clean.
**Inputs:** `precheck.json` (2026-11-19T23:56:43Z, `fail_fast: []`, no `PRE-*`), `test_verification.json` (**verdict pass, exit 0, 207.8 s**, newer than `build_log.md`), `build_log.md` waves 395–399, the four archived results, `task-graph.json` P25-T6/T7/T8 ACs, `usage.md`, `escalations.json`.
**Result: all three escalations closed (`addressed`). No new finding, no new escalation. Owner gates G1/G2 still NOT run — named, not claimed.**

---

## 1. Close-out summary

| id | task | route | what was claimed | verdict |
|---|---|---|---|---|
| ESC-126 | P25-Q79 | TASK_MANAGER → fixed by P25-T6 | both dead module-level `QApplication`s replaced by session-scoped autouse fixtures; tree-wide AST invariant + escalated-order regression | **addressed** — verified, including a challenge of the scanner |
| ESC-127 | P25-T4 | BUILD → fixed by T4 rework + P25-T7 | one predicate per side, both branches, no surviving duplicate; both discriminating shapes covered | **addressed** — verified by grep + structural fence + green parity runs |
| ESC-128 | P25-T2 | TASK_MANAGER → fixed by P25-T8 | `usage.md` documents the amber marker and distinguishes it from event markers | **addressed** — verified against the live document and the implementation |

---

## 2. ESC-126 — import-time `QApplication`, closed by P25-T6

- **Dead module-level apps are gone.** `grep -n '\bAPP\b|_APP'` over `tests/test_p7_w4_streaming.py` and `tests/test_p7_w4_deferral.py` → **0 matches**. Each module now declares `@pytest.fixture(scope="session", autouse=True) def _qt_app()` that calls `QApplication.instance()` and constructs `QApplication(["pytest"])` only **at test time** (`deferral.py:32-46`, `streaming.py:39-53`). The fixture docstrings name the smoke suite's raw `QtWebEngineWidgets` import and why a real `argv[0]` is used.
- **My own strict module-scope AST scan** (walks module-level statements, never descends into `FunctionDef`/`AsyncFunctionDef`/`ClassDef`/`Lambda`) over every `tests/*.py` → **0 application constructions**. `tests/conftest.py`'s app is inside its `qapp` fixture, so it is correctly not counted.
- **Scanner challenged, as asked:**
  - It **catches the original Q-79 shape**: `_APP = QApplication.instance() or QApplication([])` — the `or` operand is a `Call` reached by the expression-deep walk; the suite's own `test_scan_catches_boolop_ternary_and_module_level_if` pins exactly that line (expects `[1,2,4]` for direct-assignment / ternary / module-level-`if`). A plain `APP = QApplication([])` assignment is caught the same way.
  - It catches the attribute form (`QtWidgets.QApplication(...)`) because `_callee_name` reads `ast.Attribute.attr`, and it includes `QGuiApplication` alongside `QApplication`/`QCoreApplication`.
  - `QApplication.instance()` **alone** is correctly *not* a construction (it creates nothing when no instance exists) — only constructions break the `QtWebEngineWidgets` import.
  - **Nothing is exempted by name or path.** The scan is `TESTS_DIR.glob("*.py")`, i.e. every test module including `conftest.py`; there are no nested test packages (`find tests -type d` → `tests`, `tests/__pycache__`).
- **The escalated orders re-run as real runs, not `--collect-only`:** `pytest -q -m 'not webengine' tests/test_p7_w4_streaming.py tests/test_lwc_render_smoke.py` → **EXIT 0**; `... tests/test_p7_w4_deferral.py tests/test_lwc_render_smoke.py` → **EXIT 0**. These are the exact commands that produced the `ImportError` at `test_lwc_render_smoke.py:665` before the rework.
- `tests/test_qt_app_import_invariant.py` → **9 passed**. AC4's hard-coded 20 pre-rework ids are an intentional anti-weakening fence; both suites still collect them.

## 3. ESC-127 — one whitespace predicate per side, closed by the T4 rework + P25-T7

- **Python:** `ui/lwc_bridge.py` states `_candle_row_is_whitespace(o, c) -> bool` **once** (`:246-260`, `return o is None or c is None`), and `apply_ops_to_bars` has exactly **two** call sites — the `set_bars` loop (`:306`) and the `update_bar` branch (`:312`). The old close-only forms are gone: `cols["close"][0] is None` and `if c is not None` both grep to zero. No other candle null test survives in `ui/`, `data/` or `services/`.
- **Page:** `envelope.js::isWhitespaceRow` is stated once (`:160-167`), used by `mergeRows` in both branches, and exported (`:207-212`). `chart.js`'s helper of the same name (`:481-483`) is a **pure delegation** to `window.LwEnvelope.isWhitespaceRow`; its body contains none of `open`, `close`, `=== null`, `== null`. `test_p25_t7_ac1` asserts exactly that structurally (count fences + token absence), so a future re-inline fails the suite.
- **No test fixture re-implements the rule.** `tests/test_d69_d70_bridge_contract.py` builds rows through `_whitespace` / `_open_gap` / `_close_gap` and only *quotes* the rule inside assertions.
- **Both discriminating shapes are covered**, which was the substance of the finding: `open=None`/`close=2.0` (`_open_gap`) and the mirror `close=None`/`open=1.0` (`_close_gap`, the ESC-127 op `{open: 1, close: None, high: 2.0, low: 0.5}`) each run through **both** deliveries (`set_bars` row and `update_bar`) in `test_ac3_every_whitespace_shape_obeys_the_one_predicate` and `test_p25_t7_ac2`, and through the real `lwApplyOps`/`lwSnapshot()` in AC4's **six** fixtures (`upsert`, `replace`, `open_gap_upsert`, `open_gap_replace`, `close_gap_replace`, `close_gap_upsert`). The JS side adds the open-null case to `chart.test.js` (replace + update) and both shapes to `envelope.test.js`.
- **No production risk:** `apply_ops_to_bars` is a reconstruction helper used only by tests; the page's live `mergeRows` already used the open-or-close rule, so adopting it in Python changes no emitted shape (`build_series_ops` nulls all four slots together).

## 4. ESC-128 — `usage.md`, closed by P25-T8

- Verified in the **live document**, not from the test: the new bullet under `### Weekly & Monthly Timeframes (Phase D48)` says the forming `1 week`/`1 month` candle carries "a small amber dot above it whenever the loaded history cannot cover the whole period", that its OHLCV are "the aggregate of the bars actually available", and that "the dot disappears once the new period's data covers the period". That matches `_stamp_partial` (partial iff `covering_since > first_session_open(period_start)`), the `aboveBar` position and `PARTIAL_MARKER_COLOR = "#fbbf24"`.
- The `### Event Markers (removed — Q-34 …)` note keeps the D38 removal record and adds the distinction ("a data-completeness marker — not an event marker"). Diff is exactly those two spots (+2/−1).
- `tests/test_p25_usage_doc.py` reads the live file and scopes each assertion to its section, so a claim elsewhere cannot satisfy it — **2 passed**.

## 5. T4 generation and record

- `docs/build/results/_archive/wave398_P25-T4.json`: `status: done`, **`generation: 2`**, `footprint_flags: []`, `files_changed` = the six P25 files, `selfcheck.verdict: pass` with the verbatim tail (`# tests 127 / # pass 127 / # fail 0`), and **all five ACs `pass`**. The blocked wave-395 attempt and the stale wave-396 record are archived separately and are not the live result.
- **Record nit (no escalation):** AC4's note says "5 fixtures" while the parity set now holds **six** (`upsert`, `replace`, `open_gap_upsert`, `open_gap_replace`, `close_gap_replace`, `close_gap_upsert`). The note enumerates only three of them ("incl. …"), and the substance — every fixture compared through the real page — is true and green. A count typo in an archived note cannot be fixed without rewriting a record, and re-running T4 would rebuild nothing.
- T6/T7/T8 results: `done`, `selfcheck.verdict: pass`, `footprint_flags: []`, `files_changed` exactly the precheck's `files_verified`.

## 6. Standing duties

- **Mock-endpoint containment (B.6, blocking, not droppable):** the rework's production diff (`ui/lwc_bridge.py`, `chart_assets/lwc/envelope.js`, `chart_assets/lwc/chart.js`) grepped for `mock|fake|stub|simulat` crossed with `endpoint|client|service|server|api|harness` → **0 matches**. No production module imports a test fake; no endpoint/client/server was introduced. **Clean.** (The T6/T7 test files use no simulated endpoint either — `test_qt_app_import_invariant.py` uses a real subprocess pytest invocation.)
- **Usage-doc judgment:** the only user-facing change in the phase is D67's amber partial marker, and it is now documented (§4). `USAGE.txt` is a pointer to `usage.md` ("This is the short pointer. The canonical full guide is usage.md") and is correctly untouched; `docs/` needed nothing. **No user-facing doc is left stale.**
- **Owner gates:** T5's results still record **G1** (D67 forming week/month candle) and **G2** (D68 pop-out close with the live feed) as `status: "owner-run"`, `claimed: false`, "not run". I ran neither and claim neither. `AC-D67.2`/`AC-D68.1` remain offscreen-asserted only.
- **Delta scope:** the rework commit touches only P25 files plus the three findings' artefacts (`tests/test_p7_w4_{streaming,deferral}.py`, `tests/test_qt_app_import_invariant.py`, `tests/test_p25_usage_doc.py`, `usage.md`, `docs/`). **`docs/requirements/**` and `tests/test_lwc_render_smoke.py` are untouched by `a22ecf6`** (`git show --name-only a22ecf6` → no match for either). `docs/requirements/requirements.md` appears in the full phase delta `08cade8..a22ecf6` only via `76713af`'s pure block move, verified span-identical in the previous pass.
- **Unchanged tasks:** no file in T1/T2/T3/T5's footprints changed in the rework (`data/`, `services/`, `ui/ticker_session.py`, `ui/main_window.py`, `ui/lwc_view.py`, `ui/popout_window.py`, `tests/test_d67_forming_candle.py`, `tests/test_d68_hold_balance.py`, `tests/test_p25_fence.py` all absent from the commit). `chart.js`/`envelope.js`/`ui/lwc_bridge.py` are T1's shared files but the rework changes there are confined to the whitespace predicate — no `set_partial`/marker code was touched. No new evidence, not reopened.
- **Pack-prose spot-check (new packs sampled):** P25-T6/T7/T8 descriptions, plus P25-T1 (first task in the graph, unchanged). No prose contradicts an AC and no guarantee is stated without an enforcing test — T6's "do not edit `tests/test_lwc_render_smoke.py`" is honoured in the commit; T7's "chart.js … delegates … with no second open/close comparison" is exactly what `test_p25_t7_ac1` enforces; T8's two-spots constraint is the diff. **Clean.**

## 7. Adjudicated, not escalated

- **The AST invariant has one theoretical blind spot:** `_module_level_constructor_calls` skips the whole `FunctionDef` node, so a module-level `def f(app=QApplication([]))` default or a decorator expression constructing an app at import would not be seen. Neither shape exists in the tree, no AC requires it (P25-T6-AC2 names BoolOp / ternary / module-level `if`, all covered), and it is not a realistic third case — the realistic regression (`instance() or QApplication([])`) is caught and pinned. No action; recorded so a future widening of the scan is a known, cheap extension.
- **Three places create the test app:** `tests/conftest.py::qapp`, plus the two module-level `_qt_app` fixtures. The duplication is AC-mandated (a session-scoped **autouse** fixture per module; `conftest.qapp` is session-scoped but opt-in), and both fixtures go through `QApplication.instance()` first, so only one app ever exists.
- **T4's AC4 note count** (§5) and **`owner_gates` being absent from T6/T7/T8 results** (it is carried by T5's result, which is where the phase records G1/G2) are record-shape observations only.

## 8. Independent runs (mine, this pass)

| command | result |
|---|---|
| `pytest -q -m 'not webengine' tests/test_p7_w4_streaming.py tests/test_lwc_render_smoke.py` (ESC-126 order) | **EXIT 0** |
| `pytest -q -m 'not webengine' tests/test_p7_w4_deferral.py tests/test_lwc_render_smoke.py` (ESC-126 order) | **EXIT 0** |
| `pytest -q -m 'not webengine' tests/test_qt_app_import_invariant.py tests/test_d69_d70_bridge_contract.py tests/test_p25_usage_doc.py` | **EXIT 0, 25 passed** (9 invariant + 14 contract + 2 usage) |
| `node --test chart_assets/lwc/` | **128 pass, 0 fail** |
| my strict module-scope AST scan over `tests/*.py` | **0 constructions** |
| `grep '\bAPP\b\|_APP'` on both P7-W4 suites | **0 matches** |
| Orchestrator's full suite (`test_verification.json`) | pass, exit 0, **207.8 s** — ground truth for "the suite passed" |

## 9. Escalation close-out

- **ESC-126 → `addressed`** — re-verified on the live tree: source, my own scan, and the two formerly-failing orders green.
- **ESC-127 → `addressed`** — re-verified: one predicate per side, no surviving duplicate (including fixtures), both discriminating shapes covered in both deliveries and in the real-page parity fixtures.
- **ESC-128 → `addressed`** — re-verified: the document says what the implementation does, and the test asserts both sections.
- No other entry is open; no new entry was opened.

Status: REVIEW_COMPLETE
