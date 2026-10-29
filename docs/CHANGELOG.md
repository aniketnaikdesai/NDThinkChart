# Changelog

> **Role (set 2026-10-28):** short index. The as-built history lives in `docs/phase-changelog.md` — this file
> points at it and carries no independent narrative. Per-entry detail (commits, tests, review verdicts) is
> added to `docs/phase-changelog.md`, never here.

## P6 (D47) — 2026-10-27

Chart migration to Lightweight Charts behind the `ChartView` seam, then pyqtgraph removal (P6-T13,
commit `6e35b27`, gate owner-waived per `docs/build/gate_P6_T13.md`). Full record:
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
