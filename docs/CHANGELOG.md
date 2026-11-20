# Changelog

> **Role (set 2026-10-28):** short index. The as-built history lives in `docs/phase-changelog.md` — this file
> points at it and carries no independent narrative. Per-entry detail (commits, tests, review verdicts) is
> added to `docs/phase-changelog.md`, never here.

## P6 (D47) — 2026-10-27

Chart migration to Lightweight Charts behind the `ChartView` seam, then pyqtgraph removal (P6-T13,
commit `6e35b27`, gate owner-waived (live-session sign-off waived, not satisfied) per `docs/build/gate_P6_T13.md`). Full record:
`docs/phase-changelog.md` § Phase P6 (D47). Parity: `docs/lwc_parity_matrix.md` (rows 1–18 accepted,
row 19 retired).

## P7 (data-path batch) — 2026-10-28

Per-load budget cap (a maximum, never a target) with oldest-first persist-and-resume backfill, same-chart
reload coalescing, window-relative watchdog, prime precedence, approved wide durations, streaming
close-out (feature commit `7cba534`; ESC-075…078 closed on evidence, ESC-079 open as Analyst debt).
Full record: `docs/phase-changelog.md` § Phase P7. Review: focused close-out 2026-10-28
(`docs/code_review/review_log_P8.md`, commit `4610c35`); full offscreen suite green (1204 passed / 3 skipped).

## P8 (D48 weekly/monthly timeframes) — 2026-10-28

`1 week` (2Y) and `1 month` (10Y) end to end: config rows, Monday-ET weekly + calendar-month bucketing,
shared full-session mode for daily-or-coarser, picker parity, probe record for both combos
(feature commit `09761fb`). Full record: `docs/phase-changelog.md` § Phase P8. Review:
phase-final **REVIEW_COMPLETE** (`docs/code_review/review_log_P8.md`, commit `f7d4e3c`); full suite green.

## P4 — 2026-10-26

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P4-T01 — Deleted ui/news_digest_dock.py and ibkr/news.py; removed the digest dock, whole View menubar, NewsManager use, tick_news wiring and both news handlers from ui/main_window.py and the news "292" need/headless/push-listener API plus both `or self._s0_headless` clauses from ui/ticker_session.py; trimmed the digest/NewsManager test sections while keeping the dividend substrate.
- P4-T02 — Severed the window's order path (5 Portfolio connections, 5 close/SL-TP handlers, _close_position_by_id, _ref_price_for, validate_order + unused imports), deleted ibkr/validation.py and three close-path suites, trimmed the two suites' close cases and the D27.1 AC-3 case, and restated test_dock_d18_region's wiring comment to the view-only end state; all seven wave suites pass.
- P4-T03 — Removed the Portfolio context menu, its five signals, the SL/TP setter chain and the menu-only selection tracker from ui/active_portfolio_panel.py, shrank the table to 8 columns (Strategy 6 / Group 7, right-aligned (1,2,4,5)), and deleted ui/trade_context_menu.py, ui/stop_loss_target_dialog.py and tests/test_sltp_honesty.py; the three D27 test files adjusted (one 8/9 -> 6/7 edit each, flat-rows AC-3 tail dropped) and all ten wave suites pass.
- P4-T04 — Removed the Kill switch toolbar cluster (button, objectName, tooltip, style, connect, and the preceding QLabel("|") separator), deleted _kill_switch and _on_kill_switch_clicked so no cancel call site remains anywhere, and deleted tests/test_kill_switch.py; wave's five suites pass.
- P4-T05 — Cleaned USAGE.txt and usage.md for D45: dropped the close/cancel/kill-switch/SL-TP/disconnected-order prose and the news-digest section, added the plain 'app places, cancels and closes nothing - TWS is the surface, Portfolio is view-only, legacy SL/TP stay stored but are not settable or shown' statement, reworked the Portfolio section and Database note, and removed usage.md's stale in-app close/flatten confirm-dialog bullets in Safety.
- P4-T06 — Created tests/test_d45_removal.py — 8 guards (five modules/suites gone; AST identifier+string-constant token scan over ui/ services/ data/ ibkr/ config/ with the plan's survivor allow-list; ui/-only raw-text grep twin; no placeOrder/cancelOrder/reqGlobalCancel definition or call site; mocked-connect offscreen MainWindow walkthrough over every remaining affordance recording zero transmit/cancel calls with the Portfolio render/TWS-close path intact; 8-column table; dividend path alive; direct AC-D45.3 hasattr/policy probes) — green on the batch tree, RED on pristine c702be9.

### Recent commits
- c702be9 Stop tracking orchestrator runtime state
- 72bc152 memory: migrate the durable items out of orchestrator_state.json
- e244451 state: record the freshness flag as benign (owner decision)
- 1b7aff6 graphifyignore: exclude the live escalation ledger and the orchestrator state
- 10e5a91 D44: sync the canonical plan artifacts with the restated AC-D44.2
- 4376dca state: fix duplicated working_on/last_status keys and stale values
- 432c671 memory: the D44 task-graph decomposition lesson
- a78fbfc D44 follow-ups: the usage docs, the AC-D44.2 restatement, the graph footprint fix
- bb903a1 D44: the collapsed watchlist becomes a thin vertical bar (Batch 19)
- 0c4d478 memory: record the declined web-chart migration as a locked decision
- c9a7966 docs(requirements): drop references to the deleted GUI test-plan documents
- b10395e docs: delete the two GUI test-plan documents (never implemented)
- b8e81b8 docs: correct the usage guides after D41 removed the trading UI
- 3fd8f1c gitignore the Code Review's transient inputs
- 42d067c Add .graphifyignore: index the application, not the build process
- 7b98bb9 Stage C: fix the seven owner-reported live-run defects (+ the review follow-ups)
- 5d518ad D42: density-aware candle/volume width + RTH/ETH intraday depth floor
- b48133d D41: remove D36 footprint, D37 depth/IMB/AUC, and the whole Active Trader panel
- 29067af docs: delete PENDING_IMPLEMENTATION_PLAN.md and retire its references
- b09a89f docs(gaps): close the nine remaining D1-D15 specification-ambiguity gaps
## P5 — 2026-10-26

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 1.

### Done
- P5-T01 — Wave 1: removed the window-side order consumers from ui/main_window.py (order_registry import, three connects, three slots, _update_order_status, _on_order_error, _on_error registry branch), repointed the rejection book at the generic status line, and updated the D45 guard's walkthrough and docstring.
- P5-T02 — Deleted the three order-lifecycle EWrapper overrides (orderStatus/openOrder/execDetails) from ibkr/client.py and the three matching bridge signals in the same task; both order-status halves are gone, no placeOrder/cancel definitions exist, and the order/error/news boundaries still pass their suites.
- P5-T03 — Deleted ibkr/orders.py (builders + Orders registry + singleton) and tests/test_order_builders.py; removed data.models.UserOrder and its smoke assertion; all absence, residue and import gates green.
- P5-T04 — Deleted OrderRateLimiter/order_limiter from ibkr/pacing.py (comment now "# Global singleton"), MAX_ORDER_NOTIONAL and its validate_order comment from config/settings.py, the two order_limiter fixture resets and the order-bucket docstring clause from tests/conftest.py, and the OrderRateLimiter import/case/docstring sentence from tests/test_d28_pacing.py; residue grep empty, imports OK, pacing suite green (6 cases).
- P5-T05 — Deleted the order-fill sound from services/sound_service.py and collapsed _effect to alarm-only (`def _effect(self)` creating/returning self._alarm_effect from _paths_or_create()["alarm"]); ensure_sound_files returns only {"alarm"}; tests/test_sound_service.py now collects 7 green cases.
- P5-T06 — Deleted IdManager.reserve and its D26.2 docstring; rewrote tests/test_id_manager.py to 4 cases (monotonic case renamed/rewritten without reserve, concurrent case without reserve(3) and asserting 8 * 200) and corrected the docstring's bracket-order sentence.
- P5-T07 — Dropped stop_loss/take_profit everywhere: DDL + guarded D46/A99 migration (four ALTER TABLE DROP COLUMN, index/FK/rows/sqlite_sequence preserved), four model fields, the factory's two params/kwargs, the window's persist/load/upsert sites (bulk read now name-keyed via sqlite3.Row with the 13-name frozen column order), ESC-062 comment rewrites, three seeders 11->9, the new seeded-trade_group_id case, and tests/test_stop_loss_target.py deleted
- P5-T08 — Guard instrument finalised: _SURVIVORS 16, _FORBIDDEN 80 (two exact-matched), three absence pools, the P5 end-state test, and the authorised file-scoped stop_loss/take_profit exemption for data/db.py (_ALLOWED_IN_FILE + _allowed_in at the scan call site).
- P5-T09 — Prose-only: classify_error's 202 comment now states warning-not-info for status-bar emission; usage.md drops test_order_builders and says SL/TP columns are dropped by a one-time migration on first open (rows survive, only those values lost); USAGE.txt says the columns are dropped on first open and nothing is stored; test_dock_d18_region renames T48_T03 to summary_signals_exposed, states zero receivers and fixes the >= 1 docstring. classify_error code untouched.
- P5-T10 — Gate green. Full suite exit 0 (1022 tests). Guard green: 9 passed, 0 AST offences, 0 twin hits, only the permitted stop_loss/take_profit in data/db.py. 201/103/202 surface per code through the generic 8000 ms line. Launch probe green; ibkr.orders unimportable. Legacy-fixture migration preserves rows, ids/sqlite_sequence, unique index and FK. Zero transmit/cancel call sites. Pre-P5 discrimination 41/40 vs 0/0.
- P5-T08 — Rework ESC-064: the _ALLOWED_IN_FILE exemption's named-not-used half is now a persisted assertion — test_allowed_in_file_is_narrow_and_named_not_used checks its exact two-token/one-file shape, its call-site scope, and parses data/db.py to require both tokens to be elements of the DROP COLUMN loop's subject tuple and never an ast.Name/Attribute/arg/keyword (or def/class/alias) or any other string constant; the exemption comment and module docstring now name that test instead of claiming an assertion that did not exist. Full guard green (10 passed).
- P5-T11 — ESC-065: factored the nested node into _inner_pytest_args/_run_inner_suite over a stable non-timing subset (three wall-clock gates + three Qt-teardown modules, incl. test_watchlist_addflow_d22.py added after the three-run AC2 check caught a real SIGSEGV at test_D22_07_T03_seed_guard), added durable argv/seam and red-child discrimination tests, and rewrote both docstrings with exclusion reasons plus the named whole-suite-green owners (verify_tests.py -> docs/code_review/test_verification.json; P5-T10).

### Blocked
None in the final state. Two transient blocks were both resolved inside the phase:
- **P5-T08** — blocked on ESC-064 (the guard forbade the two column tokens its own migration must name). The Task Manager authorised a file-scoped exemption, the pack was re-dispatched, and the task completed — see the "Rework ESC-064" entry above.
- **P5-T10** — the worker reached its step limit *after* completing every gate check but before writing the result; the Orchestrator ran `worker_selfcheck.py` (`violations: []`, suite pass) and finalised the result under the owner-death policy.

### Recent commits
- c702be9 Stop tracking orchestrator runtime state
- 72bc152 memory: migrate the durable items out of orchestrator_state.json
- e244451 state: record the freshness flag as benign (owner decision)
- 1b7aff6 graphifyignore: exclude the live escalation ledger and the orchestrator state
- 10e5a91 D44: sync the canonical plan artifacts with the restated AC-D44.2
- 4376dca state: fix duplicated working_on/last_status keys and stale values
- 432c671 memory: the D44 task-graph decomposition lesson
- a78fbfc D44 follow-ups: the usage docs, the AC-D44.2 restatement, the graph footprint fix
- bb903a1 D44: the collapsed watchlist becomes a thin vertical bar (Batch 19)
- 0c4d478 memory: record the declined web-chart migration as a locked decision
- c9a7966 docs(requirements): drop references to the deleted GUI test-plan documents
- b10395e docs: delete the two GUI test-plan documents (never implemented)
- b8e81b8 docs: correct the usage guides after D41 removed the trading UI
- 3fd8f1c gitignore the Code Review's transient inputs
- 42d067c Add .graphifyignore: index the application, not the build process
- 7b98bb9 Stage C: fix the seven owner-reported live-run defects (+ the review follow-ups)
- 5d518ad D42: density-aware candle/volume width + RTH/ETH intraday depth floor
- b48133d D41: remove D36 footprint, D37 depth/IMB/AUC, and the whole Active Trader panel
- 29067af docs: delete PENDING_IMPLEMENTATION_PLAN.md and retire its references
- b09a89f docs(gaps): close the nine remaining D1-D15 specification-ambiguity gaps
## P10 — 2026-10-28

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 3.

### Done
- P10-T1 — drawing_item attaches per-kind handles only while selected and unlocked; locked keeps highlight with empty handles, deselect clears; visibility rule pinned
- P10-T2 — P10-T2 done: drag initiation verified (body whole-move + per-kind anchor drags for all five kinds, locked never-start, commit/cancel); added T21-T23 node suites (48/48 green, exit 0)
- P10-T3 — P10-T3 done: locked drags refused at LwcDrawingSurface/LwcChartView.drag_drawing (geometry/store/op-log unchanged), empty commit color normalises to unchanged, persist-reload-exactly-once-fan-out and cancel/zero-view close-out pinned; 3/3 tests pass
- P10-T4 — P10-T4 done: locked deletes refused on page + Del-button paths (row/geometry intact), color/recolour allowed, geometry-only commits and mid-drag/leave-group interplay pinned; 2 passed, exit 0
- P10-T5 — P10-T5 gate green: four suites pass (pytest 17/17 exit 0, node 48/48 exit 0), zero skips/xfails added, prod diff confined to D50 with frozen contracts and order-code absence holding, full offscreen suite 1243 passed with only 3 pre-existing display-gated skips
- P10-T2 — P10-T2 re-verified green: page drag initiation (body whole-move + per-kind anchor drags, locked never-start, commit/cancel) with node suite 48/48 pass
- P10-T6 — Gate groups-dialog Delete Selected on DrawingGroup.locked; locked members survive with row and geometry intact, all-locked selection is a no-op
- P10-T3 — Re-verified P10-T3 landed work: all 3 drag-commit tests green (exit 0); note ESC-089 unknown-item empty-color guard not present in tree (ui/lwc_view.py _on_page_drawing_updated still emits '' when id absent from _drawing_items; no re-implementation per dispatch).
- P10-T7 — Rewrote usage.md Drawing Tools section to describe shipped D50 drag-editing (select/deselect handles, body/handle drags, locked no-handle with drag/delete refusal and color allowed, cancel semantics)
- P10-T2 — ESC-091 fixed: drag moves require the button held, pointerleave/pointercancel abandon orphaned drags, non-hit press clears stale sessions; 52/52 node tests pass (exit 0)
- P10-T3 — ESC-092 fixed: unknown-item empty-color commit dropped in _on_page_drawing_updated, stored color preserved; 4/4 tests green
- P10-T3 — P10-T3 done: lock refusal + geometry-only commit + cancel/zero-view close-out green (5/5); archive wave193 task_id restored so archived-results gate green (11/11); e2e edit case + full e2e file green (19 passed, 1 skipped) — reported #chart 0x0 did not reproduce, load-dependent flake

### User-facing / documented-behavior changes (doc_required)
- P10-T7

### Recent commits
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
- a04fbd9 Q64-66 answered by owner (accept defaults); D50 Q70 settled to (c)
- 281d4e8 ESC-079 addressed: AC-D16.8 restatement verified, zero open escalations
- 61f8dff CI: restore workflow_dispatch colon (fuzzy edit ate it)
- abd036e CI: fix workflow syntax (stray colon)
- 73b27be CI: cancel superseded LWC parity runs on new pushes
- 82ccf1a RG-P7-1: AC-D16.8 successive-loads restatement (additive annotation, history preserved)
- 42c6474 Remove worked-through review snapshots (findings all landed)
- 3b3d190 Q-55: gates accept the retired row-19 disposition, fail closed elsewhere
- d4aa352 Quality report follow-ups: status sync docs + reconnect/session/map error visibility
- 0b19f7f Doc consolidation changesets 5-6: navigation baselines, historical labels, final audit
- c9e2b77 Doc consolidation changesets 3-4: P7 cap semantics, LWC-only user guides
- 3345161 Doc consolidation changesets 1-2: authority index + P6 reconciliation as-built
- 4610c35 Close ESC-075-078: verified resolved on live tree, full suite green
- f7d4e3c P8 close-out review: REVIEW_COMPLETE, 10 escalations verified addressed
## P12 — 2026-10-29

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 6.

### Done
- P12-T1 — Added 30 mins -> 30 D / 30 mins row to TIMEFRAME_CONFIG between 15 mins and 1 hour, plus tests/test_p12_config.py config/order assertions
- P12-T2 — P12-T2 done: TIMEFRAME_SECONDS gains 30 mins -> 1800 on the existing UTC-epoch grid; 10/10 new bucket tests green (exit 0)
- P12-T3 — P12-T3 done: 30 mins planner verified (1-chunk plan, newest-first chunking, mode-aware 30-session floor, bar-granular hole), priming docstring row added (5 secs group), live probe of 30 D/30 mins passed with no 321 (389 bars, record written)
- P12-T4 — P12-T4 done: new tests/test_p12_presentation.py pins picker order/parity for 30 mins, visibility default-on round-trip with unchanged Minutes row, and minutes_for_timeframe fallback 30.0; suite green (3 passed, exit 0)
- P12-T5 — P12-T5 done: 30-min intraday parity suite green — RTH/ETH loads return mode-distinct bar sets under separate cache keys, bands+collapse apply as intraday with 15-min regions parity
- P12-T6 — P12 batch gate: probe record + history intact + no skips + full offscreen suite green. Verified by Orchestrator: Q-61 fallouts fixed, full suite exit 0, worker_selfcheck verdict pass with clean footprint.

### Recent commits
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
- a04fbd9 Q64-66 answered by owner (accept defaults); D50 Q70 settled to (c)
- 281d4e8 ESC-079 addressed: AC-D16.8 restatement verified, zero open escalations
- 61f8dff CI: restore workflow_dispatch colon (fuzzy edit ate it)
- abd036e CI: fix workflow syntax (stray colon)
- 73b27be CI: cancel superseded LWC parity runs on new pushes
- 82ccf1a RG-P7-1: AC-D16.8 successive-loads restatement (additive annotation, history preserved)
- 42c6474 Remove worked-through review snapshots (findings all landed)
- 3b3d190 Q-55: gates accept the retired row-19 disposition, fail closed elsewhere
## P13 — 2026-10-29

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P13-T1 — Cold restore routes through cached bars + aggregator + realtime/backfill; disconnected stays a no-op
- P13-T2 — Rewrote PopoutChartWindow.attach as a transaction with per-step acquired flags (signals/view/hold-only-where-ensure_rt-returned/registration/resources) and disconnect-first reverse unwind; T21 per-injection and T22 survivor tests green (4 passed, exit 0)
- P13-T3 — P13-T3 done: pop-out shows ESC-070 error state (message area + status text, verbatim wording) when the chart host raises at startup; diagnostic debug log retained
- P13-T4 — P13-T4 done: drawing fan-out pinned then deduped to exactly one all-view sync per change with baseline-equal end state, signal and per-pop-out wiring kept
- P13-T5 — P13-T5 probe green: hold count tracked owners at every lifecycle step (reload coalesced into running wave); record committed with verdict 'no lasting effect'; no prod change
- P13-T6 — P13-T6 verified-close: probe verdict is no lasting effect, so no production change; added verdict-gated hold test, full hold suites green (exit 0)
- P13-T7 — Threaded main-chart tz offset into pop-out creation; removed hardcoded 0.0
- P13-T8 — D49.6 persist/restore: PopoutStore persists tz_offset (additive nullable column, offset-preserving saves) and _restore_popouts applies it with main-chart fallback for pre-change saves
- P13-T9 — P13-T9 gate re-stamped done: gate file 13/13 green (T91 checklist, T92 history, T93 no-skip/no-order) and full offscreen suite 1329 passed / 3 pre-existing webengine skips, exit 0; no code change, ESC-095 resolved at source

### Blocked
- P13-T9 — Output:

### Recent commits
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
- a04fbd9 Q64-66 answered by owner (accept defaults); D50 Q70 settled to (c)
- 281d4e8 ESC-079 addressed: AC-D16.8 restatement verified, zero open escalations
- 61f8dff CI: restore workflow_dispatch colon (fuzzy edit ate it)
- abd036e CI: fix workflow syntax (stray colon)
- 73b27be CI: cancel superseded LWC parity runs on new pushes
- 82ccf1a RG-P7-1: AC-D16.8 successive-loads restatement (additive annotation, history preserved)
## P14 — 2026-11-03

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 1.

### Done
- P14-T1 — P14-T1 done: permanent QStatusBar indicator (addPermanentWidget) raised on wave issue incl. queue-only, refreshed on wave events, cleared on finalize/cancel; all showMessage texts/timings unchanged; 3/3 new tests pass
- P14-T2 — P14-T2 done: session wave-start baseline (set-once/cleared-on-termination) with exactly-once indicator clearing on normal, stranded, cancel/teardown, and disconnect paths; Branch-A keeps baseline unreset; mode-switch clears-and-reraises
- P14-T3 — P14-T3 done: _is_cache_current predicate gates the no-plans branch and finalize path so no freshness claim shows while a wave is in flight or spans are missing; stranded waves keep the verbatim AC-D16.4 shortfall and history markers stay intact (8/8 guard tests green, self-check pass).
- P14-T1 — P14-T1 done: permanent backfill indicator as addPermanentWidget child with in-flight/queue/elapsed/reqIds state, raised on wave issue incl. queue-only; elapsed baseline is MainWindow-local so no ticker_session.py change by this task (the session _wave_start_ts field belongs to the sibling lifecycle task); all showMessage texts/timings untouched; 3/3 tests pass
- P14-T2 — P14-T2 rework: verified prior worker's zero-arg clear spies in tests/test_p14_lifecycle.py match the clear_backfill_indicator() contract; T21 (4 terminal paths, exactly-once clear), T22 (coalesced keep), T23 (mode-switch clear-and-reraise) all pass and exit cleanly, full offscreen suite green (1346 passed, 3 skipped).

### Blocked
- P14-T1 — Output:
- P14-T2 — Output:

### Recent commits
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
- a04fbd9 Q64-66 answered by owner (accept defaults); D50 Q70 settled to (c)
- 281d4e8 ESC-079 addressed: AC-D16.8 restatement verified, zero open escalations
- 61f8dff CI: restore workflow_dispatch colon (fuzzy edit ate it)
## P15 — 2026-11-04

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 1.

### Done
- P15-T1 — P15-T1 done: per-wave single-shot T0+10s expiry verdict in MainWindow (armed at raise, disarmed on every terminal path, acts only when incomplete with arrived bars + verbatim AC-D16.4 shortfall); all 6 tests pass, P14 neighbor suites green
- P15-T2 — P15-T2 done: expiry stays a pure verdict past T0+10 s (wave continues, indicator runs, normal/strand finalize unchanged); disconnect wins over pending expiry incl. queue-only waves; mode-switch/new-triple re-anchor T0, coalesced keep holds T0
- P15-T3 — P15-T3 done: missed T0+10s expiry latches the D53 indicator to 'Backfill (partial): ...' with verbatim shortfall and no current-cache claim; complete-by-bound waves keep the unchanged idle/completion path; 6/6 new tests plus P15-W1/W2 and P14 guard/lifecycle suites green.
- P15-T1 — P15-T1 done: single-shot T0+10s expiry verdict renders arrived bars plus verbatim AC-D16.4 shortfall on incomplete waves; all 4 task tests pass
- P15-T2 — P15-T2 background-continue seams verified: wave continues past T0+10s expiry under unchanged D53 lifecycle, disconnect wins over pending expiry, seam loads re-anchor T0 while coalesced reload keeps it (5/5 cases pass). Rework note: no code edits needed, implementation already present; fixed the malformed/missing result file with a well-formed stamped result.

### Recent commits
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
- a04fbd9 Q64-66 answered by owner (accept defaults); D50 Q70 settled to (c)
- 281d4e8 ESC-079 addressed: AC-D16.8 restatement verified, zero open escalations
## P16 — 2026-11-04

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 3.

### Done
- P16-T2 — Created docs/D55_fact_sheet.md: 13 cited fact rows (LWC-only, live-only, P7 cap maximum, spike labelling, P7/P8 dating) plus 50-vs-100 explicitly open with decider named
- P16-T1 — D55 inventory produced (docs/D55_inventory.md): preserved-state note, 79 tracked doc files each in exactly one of six buckets, filename/heading cross-reference map with reader source locations; zero deletions
- P16-T5 — Six-file P6 reconciliation complete: CHANGELOG P6 entry and codebase-map as-built note now carry waived-not-satisfied; architecture/parity-matrix/review-log/phase-changelog already compliant (plan-vs-delivered separated, parity-vs-cutover structural, original review text untouched). NOTE: an optional repeat of the waiver phrase in the architecture.md header was denied by tool permissions (file rejects worker edits); the file already carries waived-not-satisfied at the as-built T13 outcome and frozen-interfaces entries, so no AC is affected.
- P16-T3 — P16-T3 done: README carries status/authority/current-work/historical/ownership blocks with Role metadata and all 7 authority targets exist; map live header states LWC-only with stale engine claims confined to superseded/as-built banners and historical prose otherwise byte-identical (P16 note appended, A152 waived-not-satisfied clarification adopted in footprint)
- P16-T6 — P7 cap-as-maximum coordinated addendum (D55.6) appended to plan, architecture, P7 review and P7 notes; cap reads maximum-never-target with examples, per-load definition, 50-vs-100 reconciled to 100 per config/settings.py (DG102/A154), AC-D16.8 by reference only
- P16-T7 — P16-T7 done: baseline blocks (architecture, active phase, unresolved reqs, as-built changelog link) + recorded link audit atop architecture.md/plan.md, uniform Status/Commit/Evidence/Supersession metadata on P16 increments; archive candidates listed with pre-move pass, zero moves (P16-T8); requirements/ untouched by this task (tree-wide T7_FAIL flag pre-dates this worker)
- P16-T1 — D55 inventory present with 1:1 bucketed coverage of all 79 tracked doc files, cross-reference map with zero dangling code refs, zero deletions
- P16-T3 — P16-T3 done: README carries status/authority/current-work/historical/ownership blocks with Role metadata; map live header states LWC-only with stale engine claims confined to superseded/as-built banners and historical prose otherwise byte-identical (P16 note appended, A152 waived-not-satisfied clarification); rework fix: result now carries task_id per schema
- P16-T4 — P16-T4 done: USAGE.txt paper-(DU) sentence replaced with live-only pointer; usage.md canonical live-only with one LWC engine, as-of date and status links; zero paper-mode instructions and zero parity-complete claims in either file
- P16-T8 — P16-T8 done: D55 disposition ledger placed every in-scope file in one bucket with evidence; dev_docs/ held deleted with reference check re-verified and four Q87 targets deleted without archive after successors verified live
- P16-T9 — D55 final docs-only review certified in docs/D55_final_review.md (checklist 1:1, stale-claim greps clean, history span byte-identical); narrowed history guards pass with all protected assertions intact
- P16-T9 — P16-T9 docs-only final review certified (docs/D55_final_review.md) and both history-markers-intact guards pass on the narrowed protected span; T9_FAIL_NON_DOCS echo is the recorded pre-landed Q84 comment-only exception, exit 0
- P16-T4 — usage.md is the canonical live-only full guide (one LWC engine, 7496-only, as-of date, troubleshooting/status links) and USAGE.txt its agreeing short pointer; zero paper-mode instructions, zero parity-complete claims; test_command prints T4_OK

### Blocked
- P16-T4 — Output:
- P16-T4 — Output:

### Recent commits
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
- 8226aef P9 alarm/drawing fixes: persistence isolation, dialog fixes, group-color pipeline with (c) Both recolor; gate green, REVIEW_COMPLETE
## P17 — 2026-11-05

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P17-T1 — Silence sweeper + cancel/re-issue core with shared once-only allowance in TickerSession; 5 offscreen clock-controlled tests green
- P17-T2 — P17-T2 done: production fencing + identity-removal already present via P17-T1 (_retry_silent_chunk pop + identity-removal, unchanged _history_event_accepted fence, PK-idempotent persist) verified intact; added tests/test_d56_fencing.py with T21 (late bars+END on superseded reqId change nothing vs control) and T22 (partial-chunk retry counts each bar exactly once, PK-unique cache, clean re-read); suite 2/2 pass, self-check pass.
- P17-T3 — P17-T3 done: any inventoried code (162/321/200/399/504) on a cancel-tagged superseded reqId is debug-only with no status-bar/shortfall/pacing effect; fresh-reqId errors keep semantics with the shared _retried_plans allowance checked first; silence re-issue is paced with watchdog-bounded continuation (8/8 tests pass).
- P17-T5 — P17-T5 test-only: froze retry clock in prime-retry defers-then-issues test and added deterministic period-boundary fail-open case; module green, 20/20 loop pass
- P17-T4 — P17-T4 done: D53 retry state re-verified (distinguishable retry label, continuing elapsed, terminal-only clear); history pin re-pinned to live span hash 2fe7b1ec in both guard files (span diff vs b11d9da3 is exactly the four additive D57/D58 glossary rows); full offscreen suite green (1383 passed, 3 skipped)

### Blocked
- P17-T4 — Output:
- P17-T4 — Output:
- P17-T4 — Output:
- P17-T4 — Output:

### Recent commits
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
- 4438068 P9 tracking: plan/architecture activation, TM graph, reviewer close-out
## P18 — 2026-11-05

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P18-T1 — P18-T1 done: glyph-only go-to-latest chevron in chart.html (hidden, aria-labelled, bottom-right) driven by chart.js away-only chevronVisible with goToRealtime click; T11/T13/T14 offscreen green, T12 node cases green (25/25), P11 suite unregressed
- P18-T2 — P18-T2 done by orchestrator under owner exception (dispatch repeatedly failed). ESC-104 trendline collapse fixed in chart.js ResizeObserver (re-assert current range on resize; verified 0..81 @10.9px post-resize, anchors distinct). ESC-101 T24b fixed (probe .range shape + True->true). 15/15 framing, trendline e2e, 105/105 node green.
- P18-T1 — ESC-105 fixed: updateChevron() hides the chevron when newestBarSlot() < 0 (empty chart never reads as away); pure chevronVisible matrix untouched; new empty-chart case in test_d57_chevron.py. All task tests pass (4 pytest + 25 node).
- P18-T3 — P18-T3 verified green with no edits needed: joint chevron x framing cases hold, declared P11/LWC churn already in place and passing, full offscreen suite green (1415 tests, exit 0), node core 25/25, requirements history intact.

### Blocked
- P18-T2 — Output:

### Recent commits
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
- 9282e5a Q-57: fix 6 validated usage-doc defects (D38 removal, drag-edit, pop-out cap, test times)
## P19 — 2026-11-09

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 1.

### Done
- P19-T1 — P19-T1 done: settled-viewport trigger evaluation (oldest_visible_ts slot-to-ts mapping + maybe_prefetch fire/silent decision per S-P19-2 table) green across all 27 offscreen cases; no wave issuance in this phase's paths
- P19-T2 — P19-T2 done by orchestrator under owner exception (dispatch tool_choice failures; state preserved via reset). Implementation (prior worker) verified: pending-prefetch marker, coalesce seam, terminal clearing, abandonment fencing. Fixed to green: chain-drive used 30D window for 60D plan (now CHAIN_TF); fixtures reshaped to the AC-D58.1 fire shape (edge 4 back <= T=5); HA switch leg wires primary+view so teardown path is exercised; G2 idle assert replaced with new-triple assertions; T24b probe .range shape + True->true; terminal message now wins over transient Error line on wave-terminating errors (t01_162 + t32 expectations updated to the corrected semantic). Full offscreen suite green.
- P19-T3 — P19-T3 done: new tests/test_p19_prefetch_depth.py proves 3-link fetch-while-fetchable chaining (one in flight, no depth cap, window-by-window coverage) and honest stops (closure silence, single retention shortfall with no D56 retry, pacing-exhaustion watchdog fall-through); 4/4 green, no production change needed
- P19-T4 — P19-T4 verified: per-chunk incremental render with D53 in-flight honesty, verbatim AC-D16.4 shortfall and empty closures; viewport slots identical across landings in both follow states with no prefetch frame/range op; batch gate green (full offscreen suite 1451 passed/3 skipped, requirements history intact append-only)

### Blocked
- P19-T2 — Output:
- P19-T2 — Output:
- P19-T4 — Output:

### Recent commits
- b39fdf2 P18: go-to-latest chevron + fresh per-timeframe framing (D57, Q92-95 answered)
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
- de01dfa ESC-086: reconcile S-P10-2 decision record with as-built drag flow (record only)
## P20 — 2026-11-10

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 2.

### Done
- P20-T1 — P20-T1 done: probe-first seam (unknown symbols issue exactly one probe before any leg; adopt-on-ok, honest refuse otherwise) + error-200 realtime gate with AC-D16.4 shortfall; 21/21 new tests pass, neighbors green
- P20-T2 — P20-T2 done: futures roots run canonical full-session mode (one shared cache, toggle is pure cache hit), planner is_futures flag with Saturday-only closure, collapse/band suppression for futures; 13 pass + 1 skipped (owner-run live probe, still PENDING). Note: corrected one unsatisfiable equity-collapse control in the in-flight test (contiguous overnight feed cannot fold under the frozen gap-based collapse contract; equity folding still pinned via the weekend-gap control). chart.js needed no change (read-only scope confirmed).
- P20-T3 — P20-T3 proxy-never-for-price guard green: IND provenance + INDEX_PROXY-free chart path pinned, burst suite green, history intact
- P20-T2 — P20-T2 futures session scoping verified green: canonical full-session mode for futures roots, planner is_futures flag, collapse/band suppression; PROBE owner-waived 2026-11-09 ('Waive it', P6 precedent), never claimed as run; IND venue risk stays open.
- P20-T1 — ESC-108 fixed: adopted probe contract survives restore and prefetch waves via session._wave_contract fallback, and a None contract is never queued (wave skipped instead); two regression tests added, all 23 pass
- P20-T2 — P20-T2 rework done: dropped the ibkr import from ui/lwc_view.py (renderer-local futures root set + bool passthrough, futures visual scoping intact); task suite 13 passed + PROBE skipped-as-waived, boundary AST-clean, chart_model suite green
- P20-T5 — P7 planner pin now names full find_missing_spans signature incl. is_futures; deferral scan allowlists exactly _start_probe_load refuse site, all other pacing paths still defer-with-wait
- P20-T4 — P20-T4 done: synthetic symbols charset-conforming, doubles carry T1/T2 attrs, streaming scan migrated to probe-refuse allowlist; 52 passed, test-only
- P20-T2 — P20-T2 rework: empty-symbol guard moved above futures canonical-mode hunk (IndexError fixed, verified); PROBE skip converted to passing assert-waiver (owner Waive it 2026-11-09, P6 precedent, IND risk open); 14/14 green
- P20-T3 — P20 proxy-never-for-price guard: index chart-series provenance + INDEX_PROXY-free chart path pinned, burst-proxy tape use preserved
- P20-T6 — Migrated 10 P19 prefetch synthetic symbols to STK-charset names (P19DCHN/P19DCLS/P19DRET/P19DPACE, P19HA–P19HD, P19VA/P19VB); all 9 prefetch cases green, change set test-only
- P20-T3 — P20 proxy-never-for-price guard green (14 guard cases + burst suite: 54 passed); history intact; batch gate NOT green: 8 failures confined to out-of-scope tests/test_p19_prefetch_{depth,honesty,viewport}.py in a tree dirty with sibling in-flight edits — left untouched per out-of-scope rule

### Blocked
- P20-T4 — Output:
- P20-T3 — Output:

### Recent commits
- 65bc3e7 P19: scroll-triggered backfill prefetch (D58, owner-accepted trigger table)
- b39fdf2 P18: go-to-latest chevron + fresh per-timeframe framing (D57, Q92-95 answered)
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
- 550ba8a Q-59: renderer-owned color index replaces data.db read in LWC view
## P21 — 2026-11-10

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P21-T1 — Follow-offset live path in chart.js: envelope slot-delta shift replaces the followLive edge-pin, goToRealtime/fitAndFollow preserve the per-view remembered gap (default 2), manual scroll/pinch stays the only zero-gap path; 4 pytest + 15 node tests green, red-first verified (13 node + 3 pytest fail pre-fix).
- P21-T2 — P21-T2 rework: wave setup seeds a genuine one-day interior hole with a slot-mapped settled report so _on_viewport_settled issues 1 wave (P19 shape), and the page seed carries a fresh frame so the remembered gap holds its default; all 11 away-landing suites pass
- P21-T4 — P21-T4 test-only preserve migration green: T13/T31-click/T22/T32 assert post-action gap==remembered gap (G=2 via frame-carrying envelope) with span preserved, follow re-engaged, badge consumed/chevron hidden, no scrollToRealTime pins; T31 fit re-pinned to {0, newest+G} in both cases; diff touches only the four test files
- P21-T5 — P21-T5 done: T24b page half restated to hold (same_symbol+frame while away keeps [2,20], follow off; fresh new-symbol frame still wins [30,41]); chart.test.js seeds carry production-style frames + beforeEach isolation (25/25 node green, pytest framing + parity guard green); diff touches only the two test files
- P21-T3 — P21 batch gate green: full offscreen suite 1518 passed/3 skipped, node page-core 105 pass, D51/P18/P19 suites 78 pass, D60 follow-offset/away suites green incl. new AC-D60.6 history-intact test; requirements marker, tech stack, D41-D60 sections and reversals intact, requirements.md byte-identical to HEAD

### Blocked
- P21-T2 — Output:
- P21-T2 — Output:

### Recent commits
- 5a8307b P20: index + futures contract support (D59, Q96-99 answered)
- 65bc3e7 P19: scroll-triggered backfill prefetch (D58, owner-accepted trigger table)
- b39fdf2 P18: go-to-latest chevron + fresh per-timeframe framing (D57, Q92-95 answered)
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
- d65b52f Q-60: gates track approved behavior (nine timeframes, same_symbol key, follow gating present)
- bc6d84a P10 rework close-out: ESC-088/089/091/092 + PRE-007 verified addressed, zero open
## P22 — 2026-11-10

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P22-T2 — P22-T2 rework done: docstring no longer names ui.main_window; task suite (7 tests) and the residue guard both green
- P22-T3 — P22-T3 done: live tz apply (applyTz sets tzMode/tzOffset, re-applies shared tick/time formatters, forces tick re-render) plus zone-aware ET formatting (etLabel via America/New_York, UTC stays plain math); pytest 4 passed, node 14 passed
- P22-T1 — P22-T1 done: static toolbar captions (Symbol:/TF/Mode/Draw/separators) given Minimum-policy room via _toolbar_caption helper so full-text width is the floor and overflow stays with the D19 scroll wrapper; new D61 suite plus untouched D19/D20 suites green (16 passed). NOTE: the SY clip did not reproduce pre-fix in this offscreen env — the Symbol: caption is allocated exactly its text advance (42/42px with theme.qss, 48/47 without), i.e. zero room, confirming the defect class; the fix adds structural room and holds full width under font-drift pressure. Noticed-not-fixed (out of scope): the dynamic conn_badge ("Connecting" etc.) can still squeeze when its runtime text outgrows its construction width — separate dynamic-sizing issue, badges left untouched per AP-P22-4 label-field-local rule.
- P22-T4 — P22-T4 done: Normal crosshair pinned at creation + tz re-apply (snap source was the unapplied Magnet default); 4/4 d63 tests pass, incl. red-first AC1
- P22-T5 — P22-T5 batch gate green: history-intact narrowed pins hold, DG114 confirmed one shared tz-apply seam with DG115/DG116 closed, guards re-pinned and full offscreen plus node suites pass

### Recent commits (unscoped)
- 6ea3293 P21: follow-offset preservation + away-hold viewport (D60, Q100-102 answered)
- 5b3ec66 P21: follow-offset preservation + away-hold viewport (D60, Q100-102 answered)
- 5a8307b P20: index + futures contract support (D59, Q96-99 answered)
- 65bc3e7 P19: scroll-triggered backfill prefetch (D58, owner-accepted trigger table)
- b39fdf2 P18: go-to-latest chevron + fresh per-timeframe framing (D57, Q92-95 answered)
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
- 2223786 P16: doc consolidation D55 batch 1 (inventory, fact sheet, navigation, live-only guides, P6/P7 reconciliation, disposition ledger + Q87 deletions, final review)
- 945a2b2 Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports
- e9e5912 P15: 10-second load-chart target + graceful degradation (D54, target reading A148)
- 2d8fabd P14: persistent backfill-state indicator + cache-current guard (D53, Finding 2)
- e93fa47 P12 final review record (REVIEW_COMPLETE)
- 5fd5416 Q-62: popouts residue scan expects tz_offset column
- e6288ff Changelog: P13 as-built entry
- 19fd7cd P13 tracking: plan/architecture activation, validator + reviewer records, task graph
- 95f593b P13 popout robustness + timezone handoff (T01-T09, gate green, REVIEW_COMPLETE)
- 4f888aa P12 tracking: plan activation, validator approval, task graph
- 968dfdf Q-61: recompute pinned counts for the approved 9-row 30-min config
- 817ca2b P12 30-min timeframe: config row, 1800s buckets, priming table row, probe record
- 7a9a06f P10/P11 + D50/D51/D52 requirements, plans, reviews, task graphs, usage docs
- 0abd1fc P10 drag-editing + P11 follow-live implementation (interleaved in chart.js/gestures.js/lwc_view.py; green suite, both REVIEW_COMPLETE)
## P23 — 2026-11-18

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P23-T1 — Added services/option_ladder.py (20-wide ladder from one offset table on both sides, short-first naming plus fixture-convention guard, display/credit sign pair as the single sign source, tick band, quote-validity screen, credit-base distance, net greeks, snap_rung, four-rung window legs, cell formatters) with tests/test_d65_option_ladder.py covering AC1-AC7.
- P23-T6 — Added D65 chain-discovery/option-contract helpers (get_option_contract, today_expiry_yyyymmdd, select_zero_dte_series, option_chain_strikes, OptionSeries), req_sec_def_opt_params, three option bridge signals plus tickOptionComputation/securityDefinitionOptionParameter(+End) overrides that pass sentinels through unmodified, and tests/test_d65_option_chain.py (30 tests, green).
- P23-T2 — Created ui/option_spreads_panel.py (shell, CCS/PCS 4x5 tables, Target gate 0.05-19.95, red/green ON/OFF toggle, 360px preferred width, tooltip+ellipsis names, collapse contract) with tests/test_d65_option_panel.py; all 13 tests pass
- P23-T7 — Added services/option_spread_engine.py (three-tier seed ladder, 12-pair/10 s bound on an injected clock, pending/sentinel quote validity, credit-basis anchor with ordered tie-breaks, match_band gating, 16-line lease pool with re-anchor dip) and tests/test_d65_spread_engine.py (8 tests, AC1-AC7 plus Qt/ibapi isolation); suite green.
- P23-T3 — Option Spreads dock swap complete: new title/objectName + header_button title bar, ten Portfolio call sites deleted, 360 px launch derived once through plan_dock_widths (wide 360, narrow 200 per the AC4 ruling), panel module + seven suites deleted, five suites re-pointed; declared suite green (47 passed); test_d45_removal.py red only at its three planned later-wave sites.
- P23-T8 — Spread engine B: window_step (one 5-point step per side in the AC-D65.4 direction, cancels before subscribes, reqId-preserving re-anchor), greek source precedence with the never-mixed rule, disconnect/reconnect lifecycle (STALE, frozen walk, same-anchor resume, one re-seed) and the four per-line error classes, with the P23-T8-AC1..AC5 suite green
- P23-T4 — Re-keyed the twenty surviving right-dock lookups to dock.objectName() in ("Option Spreads",): 15 uniform hide loops, 3 module-constant forms (_RIGHT_DOCK_TITLES -> _RIGHT_DOCK_NAMES) and the 3 sentinel assertions; all twenty suites green (158 passed); the tests/-wide grep is clean within the footprint (residual 'Portfolio' lookups remain only in test_dock_widths_d18.py and test_watchlist_nonregression_d22.py, outside this task's touches_files).
- P23-T5 — Re-pointed both D18 width suites to the Option Spreads panel (identity, panel-fills, wide content on ccs_table/pcs_table, the two owner-authorised A201 re-baselines with no other numeric move), re-pointed the D21.13/D22 probe to header_button/is_collapsed/body/'Option Spreads', and reworked the D45 walkthrough onto the new panel (deleting the eight-column and removed-member tests); all four suites green.
- P23-T9 — ESC-117: OFF and the 16:15 cutoff now discard the session engine so a same-session ON re-seeds and re-subscribes from the wire, and _option_subscribe_leg refuses while the panel is OFF; three regression tests fail on the pre-fix tree and pass now.
- P23-T10 — Removed the account/position window residue and re-pointed the connection badge: conn_badge_text(monitoring_paused=False) now takes no account parameter and returns the connection-only text '● Connected' / #34d399 with D40's unchanged amber paused wording, and _update_conn_badge reads no account state (D26.5's paper/live derivation retired by design — no port-derived Live label invented, the fail-fast port guard untouched); deleted the whole price-sink chain across its three AC-D65.18 homes (ui/main_window.py::_symbol_last_prices/_record_symbol_price plus the D27.5 comment, ui/watchlist_panel.py::set_price_sink/_price_sink and their call site, ui/ticker_session.py's host call), along with the five handlers and helpers, the bulk DB read, the six state fields, the disconnect clears, the status line and the dead imports; test book updated (_stub_account_calls and its call site, the four badge cases replaced by the connected/paused pair, five inert fake-host stubs, the two stream-suite recorders), tests/test_d65_option_panel.py's P23-T3-AC2 block rewritten and that file is now inside the footprint by Task Manager correction (the only reason the prior run blocked), and tests/test_p7_w4_streaming.py's replay expectation was updated to include OPTION_LEGS (pre-existing red from P23-05's S-P23-17 tag, not this task's regression).
- P23-T11 — Deleted the four client overrides, four bridge signals, ibkr/account.py, services/strategy_detection.py, data.models.Position/TradeGroup and the two retired suites, and rewrote test_ui_smoke.py:48-49 and test_d45_removal.py block (d) to absence assertions; NOTE for review, outside this task's footprint: tests/test_d65_option_chain.py::test_account_and_position_overrides_and_signals_remain (P23-T6's suite) still asserts the four overrides/signals are PRESENT and now fails - it needs inverting by whoever owns that file (its sibling test_no_production_caller_outside_ibkr was already failing before this task).
- P23-T12 — Pre-drop backup verified: backup_before_drop copies via shutil.copy2 to backups/charting_app_pre-D65_<stamp>.sqlite3, opens only the COPY read-only (mode=ro), requires integrity_check == ok plus positions/trade_groups/position_group_map row counts, and raises BackupVerificationError on any failure; _migrate_schema calls it only when one of the three tables survives and aborts before the drop on failure (proven by the failure-injection test). The three tables are dropped child-first (position_group_map, positions, trade_groups) idempotently; the D46 stop/target drop loop and its now-subjectless carve-out (_ALLOWED_IN_FILE, _allowed_in, _drop_column_subject_nodes, _EXEMPT_TOKENS and its test) are deleted; conftest's wipe list and test_db_schema/instrument token lists re-baselined. Three out-of-scope full-suite failures recorded as NOT this task's: test_d64_batch_gate's shared-seam record on a dirty tree, and test_d65_option_chain's two stale expectations about P23-06/07 removals.
- P23-T13 — ESC-118 closed: deleted the unused ˋOptionSpreadEngine = SpreadEngineˋ alias from services/option_spread_engine.py and emptied CENSUS_ALLOWLIST; the allowlist check now demands a ˋ<repo-relative .py>:<line> — <how it is invoked>ˋ citation and AST-verifies the cited line really invokes/registers the symbol, with a seeded-red case rejecting the exact task-graph document mention from ESC-118 (gate green on the tree at 36 passed, still red on its seeded dead-symbol/unconnected-signal fixtures); usage.md rewritten to describe the display-only Option Spreads panel (Target 0.05-19.95, ON/OFF, no order entry) with no Portfolio/Account Summary claim and no strategy auto-detection, and services/option_ladder.py's unused datetime import removed (both already committed on the tree, no current diff); AC-D65.19 (owner's paper-TWS acceptance) remains OPEN and owned by P23-T14, declared in the gate record.
- P23-T14 — Added docs/archive/probe_records/d65_paper_tws_acceptance.md: the owner-run paper-TWS checklist with the six AC-D65.19 items all PENDING, empty evidence fields, the 16+1 (17) line-count table, screenshots/notes slots and a sign-off-or-waiver field; no code touched and the gate left open
- P23-T15 — Re-pointed the D65 option-chain suite to the phase-final invariants: the caller sweep admits only ibkr/ plus the named P23-T9 ui/main_window.py wiring sites (line-level admission, seeded non-ibkr and stray-mention offenders still reported), the account/position presence case is inverted to absence (asserted via vars(IBApiClient) because IBApiClient inherits EWrapper's base stubs, so getattr is never None), and the docstring plus the residue carve-out rationale restate the phase-final truth.

### User-facing / documented-behavior changes (doc_required)
- P23-T13

### Recent commits (unscoped)
- bb5d540 P23 rework: ESC-116 contract re-point, ESC-117 OFF/cutoff session reset, ESC-118 dead alias + allowlist tighten
- 82b82fd P23 build: Option Spreads panel, chain/greeks, engine, live wiring, Portfolio stack removal, schema drop (10 waves)
- 4bb01e9 P23: plan approved after owner review (10 waves, RC-1..RC-16)
- e27c03b D65 amended for owner review; plan revised to 10 waves (FI-P23-2/3 resolved)
- 337221e Q-72: CI parity gate reads the archived matrix path
- 153c317 Archive reference docs; D65 amended per owner review (Q-71)
- 99bd362 Archive review logs, plan reviews and probe records (Q-68..Q-70)
- 697d940 Q-69: archive probe records and re-point their gate tests
- d572047 P23: option spreads plan approved; implementation plan for owner review
- 4d8f628 Q-67: hide the collapsed-watchlist handle while expanded (covered 'Sy' header text)
- 015e77d Q-66: toolbar scroll opens at its left edge (startup offset fix)
- 1953386 Q-65: style the horizontal toolbar scrollbar to match the dark theme
- 4ea1482 Q-64: derive toolbar row height from content sizeHint (36px floor)
- c2289c8 P22: toolbar label room, live timezone toggle, free crosshair, time-axis labels (D61-64)
- 6ea3293 P21: follow-offset preservation + away-hold viewport (D60, Q100-102 answered)
- 5b3ec66 P21: follow-offset preservation + away-hold viewport (D60, Q100-102 answered)
- 5a8307b P20: index + futures contract support (D59, Q96-99 answered)
- 65bc3e7 P19: scroll-triggered backfill prefetch (D58, owner-accepted trigger table)
- b39fdf2 P18: go-to-latest chevron + fresh per-timeframe framing (D57, Q92-95 answered)
- e50a759 P17: silence retry for historical chunks (D56, Q88-91 answered)
## P24 — 2026-11-18

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P24-T1 — Per-side row-ordered RUNG_OFFSETS with ladder_pairs reading tuple order (never sorted); retired the shared dict {1:10,2:5,3:0,4:-5}, sorted(RUNG_OFFSETS)==[1,2,3,4], the 'both sides' prose, the PCS [10,5,0,-5] expectation, test_P23_T1_AC1_one_offset_table_on_both_sides (replaced by a per-side no-second-table test), PCS canonical 7340/7320 (now 7330/7310, 7325/7305, 7320/7300, 7315/7295 at anchor 7325) and PCS window_legs anchor 7340 (now 7325); ladder suite 89 tests green.
- P24-T2 — Re-derived both PCS fixture suites to the per-side +5/0/-5/-10 table (per-fixture quote-coverage and both-anchor assertions, split EXPECTED_SHORTS_CCS/PCS, PCS row indices up one, re-anchor sets leave P7320/arrive P7360 keeping P7340); no PCS anchor moved -- every re-derived value equals the strike-based P23 anchor; two suites and all seven tests/test_d65_* suites green; this wave's diff is the two test files (the working-tree diff also carries P24-01's services/option_ladder.py)
- P24-T3 — Panel PCS fixture re-baselined to SPX Nov17 7325/7305, residue CANONICAL_FIXTURES PCS entry re-pointed to 7325/7305 (constant+comment only; gate body/holders/ban lists byte-identical), and tests/test_d66_delta_fence.py green with all five [revises P23, 2026-11-18 markers asserted by site; delta scope recorded.

### Recent commits (unscoped)
- 246e5df P24: PCS per-side offsets + reversed row order (D66); fixtures re-derived, delta fence
- f9bb73c P24: requirements + plan approved (D66 PCS ordering delta); ESC-123/124/125 closed; acceptance record names db21672
- db21672 P23 rework: restore the install guard (ESC-124); surface the IB chain error code and stop claiming no-0DTE on failure (Q-74)
- 39856b0 P23 cleanup: delete 18 test-only symbols, wire AC-D65.4 into evaluate(), harden the residue gate (ESC-121/122), live-TWS acceptance record
- c04cc03 Q-73: usage docs cover the D65 badge, STALE/freeze and no-0DTE empty state
- a6800b2 P23 T17: residue gate censuses class methods with cited framework exemptions
- c2fc2af P23 T16: engine-owned reset_session, live toggle_off, no constructor re-entry
- bb5d540 P23 rework: ESC-116 contract re-point, ESC-117 OFF/cutoff session reset, ESC-118 dead alias + allowlist tighten
- 82b82fd P23 build: Option Spreads panel, chain/greeks, engine, live wiring, Portfolio stack removal, schema drop (10 waves)
- 4bb01e9 P23: plan approved after owner review (10 waves, RC-1..RC-16)
- e27c03b D65 amended for owner review; plan revised to 10 waves (FI-P23-2/3 resolved)
- 337221e Q-72: CI parity gate reads the archived matrix path
- 153c317 Archive reference docs; D65 amended per owner review (Q-71)
- 99bd362 Archive review logs, plan reviews and probe records (Q-68..Q-70)
- 697d940 Q-69: archive probe records and re-point their gate tests
- d572047 P23: option spreads plan approved; implementation plan for owner review
- 4d8f628 Q-67: hide the collapsed-watchlist handle while expanded (covered 'Sy' header text)
- 015e77d Q-66: toolbar scroll opens at its left edge (startup offset fix)
- 1953386 Q-65: style the horizontal toolbar scrollbar to match the dark theme
- 4ea1482 Q-64: derive toolbar row height from content sizeHint (36px floor)
## P25 — 2026-11-20

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P25-T3 — D68: PopoutChartWindow now records the one RT hold it acquired in _hold_acquired and latches _closed in detach(); detach releases at most that hold, attach's unwind reads the instance latch, and a post-close retry acquires nothing. New tests/test_d68_hold_balance.py (5 tests / 6 cases, both close orders) green, P13 hold fence untouched and green.
- P25-T1 — P25-T1 done: envelope.js and ui/lwc_bridge.py accept the set_partial directive (int ts, bool partial, no series/cols) and chart.js lifts it before describeOp and re-applies one guarded createSeriesMarkers marker after every rows application; suite green (117 node, 19 pytest) with the @pytest.mark.webengine case excluded by repo convention (it aborts on macOS offscreen even on unmodified HEAD — pre-existing environment defect, not this task's code).
- P25-T2 — D67 part 2: week/month forming candle adopts the rendered current-period row as the aggregator base, skips the prime when based, stamps Bar.partial from covering_since vs the first session open, and drives one set_partial marker from the view; new suite green.
- P25-T4 — Re-verified the existing D69/D70 implementation (arrival-ordered flush with one replace per series; one whitespace predicate ˋopen is None or close is Noneˋ shared by both Python reconstruction branches and the single exported envelope.js::isWhitespaceRow that chart.js reuses): 12 Python tests + 127 node tests pass; re-submitted with generation 2 (the prior result was archived only for a wrong generation value).
- P25-T5 — worker completed the fence suite and self-check but exhausted its step budget before writing the result; orchestrator records it from the worker's verbatim stamp, with the gate re-run green after Q-79
- P25-T6 — ESC-126: both P7-W4 suites no longer build a QApplication at import (the dead module-level _APP/APP is replaced by a session-scoped autouse _qt_app fixture creating the app at test time), and new tests/test_qt_app_import_invariant.py pins the tree-wide module-scope AST invariant, the two escalated collection orders, and all 20 pre-rework test ids; note AC3's pre-fix red is not reproducible here because ui/lwc_host.py guards its QtWebEngineWidgets import (HAS_WEBENGINE just goes false), so the red/green signal lives in the AC1/AC2 static cases.
- P25-T8 — ESC-128: usage.md now documents the amber partial marker on a forming 1 week/1 month candle (bullet under Weekly & Monthly Timeframes) and distinguishes it as a data-completeness cue in the Event Markers note; new tests/test_p25_usage_doc.py.
- P25-T7 — Single-sourced the candle whitespace predicate per side: Python now has one module-level _candle_row_is_whitespace called by both apply_ops_to_bars branches (no close-only test left), envelope.js exports the one isWhitespaceRow used by mergeRows and delegated to by chart.js; added the AC1 source-structure fence, the AC2 both-shapes/both-deliveries case, the ESC-127 close-null update parity fixture, and the fold's mirror case.

### User-facing / documented-behavior changes (doc_required)
- P25-T8

### Recent commits (unscoped)
- a22ecf6 P25 rework: single-sourced whitespace predicate, import-time QApplication invariant, partial-marker docs (ESC-126/127/128)
- 7d93819 Q-79: drop the dead module-level QApplication in the forming-candle suite (import-order fix)
- 76713af P25 build: period base + forming-candle marker, pop-out hold latches, arrival-ordered flush, one whitespace rule
- 08cade8 P25: plan approved (D67-D70 silent-wrong-data); Batch-38 requirements recorded as phases P25-P30
- 94d6119 Q-76/77/78: expiry renders Nov19, silence bound scales with chunk shape, ResizeObserver work coalesced
- 9418a54 P24 close-out: changelog, review log, PRE-021 addressed
- 246e5df P24: PCS per-side offsets + reversed row order (D66); fixtures re-derived, delta fence
- f9bb73c P24: requirements + plan approved (D66 PCS ordering delta); ESC-123/124/125 closed; acceptance record names db21672
- db21672 P23 rework: restore the install guard (ESC-124); surface the IB chain error code and stop claiming no-0DTE on failure (Q-74)
- 39856b0 P23 cleanup: delete 18 test-only symbols, wire AC-D65.4 into evaluate(), harden the residue gate (ESC-121/122), live-TWS acceptance record
- c04cc03 Q-73: usage docs cover the D65 badge, STALE/freeze and no-0DTE empty state
- a6800b2 P23 T17: residue gate censuses class methods with cited framework exemptions
- c2fc2af P23 T16: engine-owned reset_session, live toggle_off, no constructor re-entry
- bb5d540 P23 rework: ESC-116 contract re-point, ESC-117 OFF/cutoff session reset, ESC-118 dead alias + allowlist tighten
- 82b82fd P23 build: Option Spreads panel, chain/greeks, engine, live wiring, Portfolio stack removal, schema drop (10 waves)
- 4bb01e9 P23: plan approved after owner review (10 waves, RC-1..RC-16)
- e27c03b D65 amended for owner review; plan revised to 10 waves (FI-P23-2/3 resolved)
- 337221e Q-72: CI parity gate reads the archived matrix path
- 153c317 Archive reference docs; D65 amended per owner review (Q-71)
- 99bd362 Archive review logs, plan reviews and probe records (Q-68..Q-70)
## P26 — 2026-11-20

Build: Status: READY_FOR_REVIEW; review: REVIEW_COMPLETE; findings logged: 0.

### Done
- P26-T1 — ESC-129 rework: generic_batch with count <= 0 is now a no-op body that reserves nothing and skips the interval stamp, so an empty reservation is not spendable and an RT-only replay no longer defers the next send; the count <= 1 docstrings now state that a batch of one admits its single send by design (AC-D71.5's n-of-n contract unchanged). New regression tests pin both behaviours; all 5 P26-T1 tests and the seven named pre-existing suites pass unchanged.
- P26-T2 — D72/D75/D76: the cap yield parks the wave (bound settled once nothing is in flight, queue survives an identical reload and resumes oldest-first, a stalled member or a disconnect still strands exactly once); a readiness episode arms the bound once, announces once and ends through a bounded finalise naming the transport.
- P26-T3 — D73/D74: one _surrender_chunk_bars helper now serves both retry paths (162 branch surrenders before re-queue), the cancel ledger is generation-tagged and pruned to the current+previous generation at each wave start, _backfill_failed_req_ids resets per wave, and MainWindow's superseded tags live in a two-batch window; new suite tests/test_d73_d74_retry_ledger.py covers all four criteria.
- P26-T4 — P26 fence suite added (11 tests): presence-per-id requirements markers (D41-D70 headings, D71-D76 entries, Journeys 68-70, AC/A/R ranges, existing-repo marker, Current Tech Stack) and the six module-read pins; delta diff vs 629be4a is inside the phase allowlist; full offscreen suite green; G3/G4 listed as owner-run, not claimed.

### Recent commits (unscoped)
- bda354f P26 rework: empty batch reservation reserves nothing; batch-of-one contract documented (ESC-129)
- 70b16f2 P26 build: transactional reconnect replay, cap-parked wave lifecycle, retry surrender, generation-scoped ledgers (D71-D76)
- 4975efa P26: plan approved (D71-D76 reconnect replay + wave lifecycle)
- 629be4a P25 close-out: changelog, review log, escalations addressed
- a22ecf6 P25 rework: single-sourced whitespace predicate, import-time QApplication invariant, partial-marker docs (ESC-126/127/128)
- 7d93819 Q-79: drop the dead module-level QApplication in the forming-candle suite (import-order fix)
- 76713af P25 build: period base + forming-candle marker, pop-out hold latches, arrival-ordered flush, one whitespace rule
- 08cade8 P25: plan approved (D67-D70 silent-wrong-data); Batch-38 requirements recorded as phases P25-P30
- 94d6119 Q-76/77/78: expiry renders Nov19, silence bound scales with chunk shape, ResizeObserver work coalesced
- 9418a54 P24 close-out: changelog, review log, PRE-021 addressed
- 246e5df P24: PCS per-side offsets + reversed row order (D66); fixtures re-derived, delta fence
- f9bb73c P24: requirements + plan approved (D66 PCS ordering delta); ESC-123/124/125 closed; acceptance record names db21672
- db21672 P23 rework: restore the install guard (ESC-124); surface the IB chain error code and stop claiming no-0DTE on failure (Q-74)
- 39856b0 P23 cleanup: delete 18 test-only symbols, wire AC-D65.4 into evaluate(), harden the residue gate (ESC-121/122), live-TWS acceptance record
- c04cc03 Q-73: usage docs cover the D65 badge, STALE/freeze and no-0DTE empty state
- a6800b2 P23 T17: residue gate censuses class methods with cited framework exemptions
- c2fc2af P23 T16: engine-owned reset_session, live toggle_off, no constructor re-entry
- bb5d540 P23 rework: ESC-116 contract re-point, ESC-117 OFF/cutoff session reset, ESC-118 dead alias + allowlist tighten
- 82b82fd P23 build: Option Spreads panel, chain/greeks, engine, live wiring, Portfolio stack removal, schema drop (10 waves)
- 4bb01e9 P23: plan approved after owner review (10 waves, RC-1..RC-16)
