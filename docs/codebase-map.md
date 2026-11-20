# Codebase Map — NDThinkChart

> **Owner:** Plan agent (written/refreshed as the first step of every batch — `docs/orchestrator_state.json`
> `contract_change_2026_10_16`). **Read by:** Plan Artifact Editor & Validator, Task Manager, Build Worker,
> Code Reviewer. **Purpose:** a module index so downstream agents stop walking the repo tree. This is an
> **index, not documentation** — if an entry needs more than ~5 lines it is doing too much; follow the symbol,
> not this file.
>
> **This is an existing repository** (`requirements.md` carries the marker). **Current tree (2026-10-28):**
> PyQt6 + Lightweight Charts **only** — no pyqtgraph. P6-T13 executed the removal 2026-10-27 (commit
> `6e35b27`); `ui/chart_view.py`::create_chart_view is the LWC-only factory (`NDT_CHART_ENGINE` /
> chart/engine no longer select a renderer); live-session sign-off waived-not-satisfied per
> `docs/build/gate_P6_T13.md`. **P7 BUILT** (data-path batch, feature commit `7cba534`, 2026-10-28) and
> **P8 BUILT** (D48 weekly/monthly timeframes, feature commit `09761fb`, 2026-10-28). Detail lives in
> `docs/phase-changelog.md` (Phase P6/P7/P8) and `docs/lwc_parity_matrix.md`. Skeleton re-run 2026-11-19
> at P28 planning, HEAD `0ff7964`: **289 code files, 11 module rows, 23 test-impact rows**;
> `graphify-out/graph.json` used for discovery
> only — **the source is authoritative** where they disagree. P8 adds **no new module**, so every annotation
> below carries forward. All P6-planned paths have landed, so the 2026-10-26 skeleton-naming note below is
> spent (kept for lineage).
>
> **Status legend** (batch-relative P6 vocabulary, retained for the rows below): `[existing]` — present,
> **not** modified by P6 · `[new in P6]` — introduced by P6 · `[changed in P6]` — present and modified by
> P6. Post-P6 changes (P6-T13 removal, P7, P8) are recorded in the notes below and in
> `docs/phase-changelog.md`, never in the status cells.
>
> **Historical note — superseded 2026-10-26 plan-time wording (preserved as decision lineage, not current
> state).** P6 / Batch 22 (D47) was planned as a strangler migration: the chart stack would move to
> Lightweight Charts behind a `ChartView` seam with pyqtgraph retained and default until parity was accepted
> ("pyqtgraph stays default through Phase 10", "no pyqtgraph code is deleted before Phase 11", P6-T13
> separately gated); two new production modules would land (the ChartView seam + the shared chart model),
> plus one new web-asset tree + bridge, one throwaway spike directory (never imported), and two docs (parity
> matrix + spike results), with ui/chart_panel edited for delegation only. P6-T13 executed the removal
> instead (2026-10-27, commit `6e35b27`), so those sentences are superseded. Plan-time baseline was post-P5
> (D46 built — ibkr/orders + tests/test_order_builders + tests/test_stop_loss_target deleted; skeleton
> 2026-10-26: 205 code files, 24 test-impact rows; annotations carried forward from P5 and extended for P6).
> P5 end state for the record: five deleted production modules, `ibkr/error_codes.py` comment-only, **two**
> suites deleted, **thirteen** test files adjusted, **0** added; `USAGE.txt` / `usage.md` corrected and this
> map refreshed (full record: the D45 line below).
>
> **D45 record (delivered, not re-opened in P5).** Batch 20 removed the News Digest dock (+ the `View` menubar),
> the Trade Context Menu, the **Kill switch** and the **SL/TP dialog**: five deleted production modules
> (ui/news_digest_dock, ibkr/news, ui/trade_context_menu, ui/stop_loss_target_dialog, ibkr/validation),
> **three** edited production modules (`ui/main_window.py`, `ui/ticker_session.py`,
> ui/active_portfolio_panel.py), **five deleted** test files, **seven adjusted** test files and **one added**
> (`tests/test_d45_removal.py` — the static/behavioural removal guard), two docs cleaned. *(This line read
> "adjusts six" until 2026-10-25; corrected with the addition of the added suite per `ESC-063`.)*
>
> **P6 note (2026-10-26):** the skeleton is regenerated from the post-P5 tree, so it no longer lists the P5-deleted
> files — the stale-skeleton note from P5 is retired. Planned-but-not-yet-existing P6 paths (the ChartView seam
> module, the shared chart-model module, the spike directory, the parity-matrix and spike-results docs) are named
> **without backticks** in the annotations until they land, per the map lint rule; live files keep their real path.
>
> **P9 note (2026-10-28):** skeleton re-run for the alarm/drawing fix batch (Batch 25); only drift is
> five new test modules since P8. P9 adds **no new module** — every fix lands in existing files in
> place (`chart_assets/lwc/gestures.js`, `ui/lwc_view.py`, `ui/main_window.py`,
> `ui/drawing_groups_dialog.py`, `ui/ticker_session.py`, `data/drawing_store.py` for the recolor
> member-repaint + new/existing offscreen suites) — so every annotation above carries forward and the
> generated test-impact rows stand as regenerated (Plan-confirmed).
>
> **P10 note (2026-10-28):** skeleton re-run for the D50 drag-editing batch; only drift is
> five new test modules since P9. P10 adds **no new module** — every fix lands in existing
> files in place (`chart_assets/lwc/gestures.js`, `ui/lwc_view.py`, `ui/main_window.py` for
> the drag/handle/lock/commit work, plus new/existing offscreen + `node --test`
> suites) — so every annotation above carries forward and the generated test-impact rows
> stand as regenerated (Plan-confirmed). `data/drawing_store.py`, `ui/chart_view.py` and
> `ui/ticker_session.py` are touched by contract only (frozen signatures reused, not edited).
>
> **P12 note (2026-10-29):** skeleton re-run for the D52 `30 mins` batch (Batch 27); only drift is
> test modules since P10. P12 adds **no new module** — the row lands in `ibkr/market_data.py`,
> the 1800 key in `data/bar_aggregator.py`, config-order picker placement, docstring/inventory rows,
> plus new/existing offscreen suites and the standalone probe — so every annotation above carries
> forward and the generated test-impact rows stand as regenerated (Plan-confirmed).
>
> **P13 note (2026-10-29):** skeleton re-run for the D49 pop-out robustness batch (Batch 24 + D49.6);
> drift is 231 code files. P13 adds **no new module** — every fix lands in existing files in place
> (`ui/main_window.py` for restore/tz-handoff, `ui/popout_window.py` for transactional attach +
> error state + tz handoff, `ui/ticker_session.py` for data-path sync / single fan-out / hold
> verification, `data/popout_store.py` for the persisted offset, plus offscreen suites) — so every
> annotation above carries forward and the generated test-impact rows stand as regenerated
> (Plan-confirmed).
>
> **P14 note (2026-11-03):** skeleton re-run for the D53 persistent backfill-indicator batch (Batch 28);
> drift is 242 code files. P14 adds **no new module** — every change lands in existing files in place
> (`ui/main_window.py` for the permanent indicator widget + wave hooks + freshness predicate,
> `ui/ticker_session.py` for the one additive in-memory wave-start field, planner read-only, plus
> offscreen suites) — so every annotation above carries forward and the generated test-impact rows
> stand as regenerated (Plan-confirmed).
>
> **P15 note (2026-11-04):** skeleton re-run for the D54 10-second-target batch (Batch 29);
> drift is 246 code files. P15 adds **no new module** — every change lands in existing files in place
> (`ui/main_window.py` for the T0-anchored expiry hook + expiry render + D53-indicator interplay,
> `ui/ticker_session.py` read-only wave state, planner read-only, plus offscreen suites) — so every
> annotation above carries forward and the generated test-impact rows stand as regenerated
> (Plan-confirmed).
>
> **P16 note (2026-11-04):** docs-only consolidation batch (D55, Batch 30) — **no code, test,
> packaging, or schema change**, so the skeleton and all test-impact rows stand as regenerated
> (Plan-confirmed) and every annotation above carries forward. Pre-landed in the working tree:
> dev_docs/ deleted (Q86) and `services/sound_service.py` docstring self-contained (Q84);
> pending P16 disposition targets are `docs/code_review/review_log.md`,
> `docs/tasks/task_manager_notes.md`, `docs/code_review/precheck.json` +
> `docs/code_review/precheck.md` (Q87: delete, no archive — each has a suffixed successor).
>
> **P17 note (2026-11-05):** silence-retry batch (D56, Batch 31) — **no new module**; every
> change lands in existing files in place (`ui/ticker_session.py` for the last-activity
> stamps + sweeper + `_retry_silent_chunk` + shared `_retried_plans` allowance,
> `ui/main_window.py` for the D53 retry-state marker only, plus offscreen suites) — so every
> annotation above carries forward and the generated test-impact rows stand as regenerated
> (Plan-confirmed).
>
> **P18 note (2026-11-05):** viewport-UX batch (D57, Batch 32 — visible chevron + fresh
> framing) — **no new module**; every change lands in existing files in place
> (`chart_assets/lwc/chart.html` for the chevron button DOM, `chart_assets/lwc/chart.js`
> for chevron visibility/click + frame-range application, `ui/lwc_view.py` for the
> session-anchored frame computation + `set_symbol`/`set_timeframe` fresh-frame
> precedence, plus offscreen + `node --test` suites) — so every annotation above carries
> forward and the generated test-impact rows stand as regenerated (Plan-confirmed).
>
> **P19 note (2026-11-09):** scroll-triggered prefetch batch (D58, Batch 33 — settled-viewport
> trigger + ordinary-wave prefetch) — **no new module**; every change lands in existing files
> in place (`ui/lwc_view.py` for the settled-report trigger evaluation + slot-to-ts distance
> mapping, `ui/main_window.py` for the prefetch evaluator + ordinary-wave issuance,
> `ui/ticker_session.py` for the pending-prefetch re-evaluation state, plus offscreen suites) —
> so every annotation above carries forward and the generated test-impact rows stand as regenerated
> (Plan-confirmed).
>
> **P20 note (2026-11-09):** index + futures contract batch (D59, Batch 34 — IND table + rule-ordered
> resolution, probe-first unknown seam, futures canonical-mode + presence bypass, collapse/band
> scoping, proxy-never-for-price guard) — **no new module**; every change lands in existing files
> in place (`ibkr/contracts.py` for the IND table + predicates + fallthrough reorder,
> `services/contract_lookup_service.py` for first-details retention,
> `ui/main_window.py` + `ui/ticker_session.py` for the probe seam + error-200 gating + futures
> canonical mode, `services/backfill_service.py` for the defaulted `is_futures` flag,
> `services/time_collapse_service.py` + `ui/lwc_view.py` + `chart_assets/lwc/` for futures
> collapse/band scoping, plus offscreen suites) — so every annotation above carries forward and
> the generated test-impact rows stand as regenerated (Plan-confirmed).
>
> **P21 note (2026-11-09):** follow-offset preservation batch (D60, Batch 35 —
> envelope slot-delta shift + explicit-action preserve + per-view remembered gap +
> away-landing neutrality) — **no new module**; every change lands in existing files
> in place (`chart_assets/lwc/chart.js` for the shift + preserve actions + gap state,
> `ui/lwc_view.py` for the landing-continuity gate, plus offscreen + `node --test`
> suites) — so every annotation above carries forward and the generated test-impact
> rows stand as regenerated (Plan-confirmed).
>
> **P22 note (2026-11-10):** toolbar/timezone/crosshair/time-axis batch (D61–D64, Batch 36 —
> toolbar label-field room, live timezone apply path + per-view fan-out + persistence,
> zone-aware page formatting, library-crosshair free-tracking pin) — **no new module**;
> every change lands in existing files in place (`ui/main_window.py` for the toolbar label
> field + `_on_tz_changed` fan-out/persistence, `ui/lwc_view.py` for the new `set_timezone`
> view method, `ui/lwc_bridge.py` for the tz op channel, `chart_assets/lwc/chart.js` for
> the tz apply + zone-aware formatter + crosshair Normal re-assertion, plus offscreen +
> `node --test` suites) — so every annotation above carries forward and the generated
> test-impact rows stand as regenerated (Plan-confirmed).
>
> **P23 note (2026-11-17):** Option Spreads panel batch (D65, Batch 37 — right-dock panel replacement,
> SPX/SPXW 0DTE chain discovery, per-leg quote/greek streaming, the 16-option-line budget **plus at
> most one SPX spot line (17 total)**, a three-tier bounded seed, the D27.3 registry replay for
> option legs, the verified pre-drop backup, and the Portfolio/account-position stack deletion under
> the standing Unused-Code Rule). Skeleton re-run 2026-11-17 (273 code files, 24 test-impact rows).
> **New modules (named without backticks until they
> land, per the map lint rule):** ui/option_spreads_panel.py (dock panel: header collapse button, Target
> field with its `0.05 ≤ T ≤ 19.95` gate, ON/OFF toggle, two 4×5 tables, status label),
> services/option_ladder.py (pure ladder geometry, naming, the displayed/credit basis pair, the
> tick-derived band, quote validity, net greeks, rung snapping and the window leg set — no
> scan/step helper: the seed is the engine's bounded measurement and the walk is its window steps),
> services/option_spread_engine.py (pure Qt-free state machine: chain state, leg subscriptions,
> the three-tier seed with leases and the 10 s / 12-pair bound, pending legs, window steps,
> disconnect/reconnect states and the four per-line error classes), data/db_backup.py (the
> pre-drop verified copy).
> **Changed:** `ui/main_window.py` (dock swap + option wiring + `_replay_subscriptions`'s one added
> tag; the swap also **deletes the ten `ActivePortfolioPanel` call sites** — the panel's API, gone
> with it, so the rename and its dereferences land in the same wave (RC-16); the account path's
> **residue** is deleted in P23-06; and the connection badge's account read re-pointed — its paper/live
> derivation retires with the account path, S-P23-24), `ibkr/subscription_manager.py` (one added type tag), `ibkr/contracts.py`
> (OPT contract builder + SPXW/0DTE series selection), `ibkr/market_data.py`
> (reqSecDefOptParams), `ibkr/client.py` (tickOptionComputation + securityDefinitionOptionParameter
> overrides added; the four account/position overrides deleted), `ibkr/bridge.py` (option signals added;
> the four account/position signals deleted), `data/db.py` (positions/trade_groups/position_group_map
> dropped, behind the backup call), `data/models.py` (Position/TradeGroup deleted), `ui/watchlist_panel.py` +
> `ui/ticker_session.py` (the D27.5 price-sink chain deleted with `_symbol_last_prices`).
> **Deleted:** ui/active_portfolio_panel.py, ibkr/account.py, services/strategy_detection.py; the
> rows for those three and for the account/position data path read as **history** once P23 lands —
> nothing may re-plan them. `services/md_line_guard.py` becomes live (its guard
> `MainWindow._guard_md_lines` has had no production caller until this panel).
>
> **P26 note (2026-11-19):** reconnect-replay + backfill-wave lifecycle batch (D71–D76, Batch 38 slice 2);
> skeleton re-run for the phase: **280 code files, 23 test-impact rows** (test-module drift only — the
> phase adds **no new production module**). Every change lands in existing files in place:
> `ibkr/subscription_manager.py` (the replay becomes one transaction with a union budget and a per-type
> retire resolver), `ibkr/pacing.py` (one batch reservation beside the unchanged minimum-interval gate),
> `ui/ticker_session.py` (a parked wave state, the settle rule, the readiness episode, the shared
> chunk-surrender helper, generation-windowed cancel tags), `ui/main_window.py` (the epoch-guarded replay
> deferral, the retire resolvers, the coalesce-resume branch, the parked indicator marker, the bounded
> superseded window, the transport-named timeout reason) — plus three new suites and this note. Planned
> test modules (do not look for them yet, per the naming rule above): tests/test_d71_replay_transaction.py,
> tests/test_d72_d75_d76_parked_wave.py, tests/test_d73_d74_retry_ledger.py, tests/test_p26_fence.py.
> The phase's decisions are S-P26-1…S-P26-7 in `docs/architecture.md` § *Phase P26*; wave order is
> P26-01 → P26-02 → P26-03 → P26-04 in `docs/plan.md` § *Phase P26* (both files are edited by 01–03, so
> the chain is serialised). `ibkr/realtime_bars.py` is unchanged: its `unsubscribe` is what the RT
> retire step calls. *(Generator note: the 2026-11-19 skeleton run emits the root row as a
> slash-suffixed `(root)` token, which the map lint reads as a path and rejects; the row is kept in its
> previous slash-free form — `update_codebase_map.py` should emit it that way.)*
>
> **P27 note (2026-11-19):** planner + pacing hygiene batch (D77–D83, Batch 38 slice 3); the phase adds
> **no new production module** and no new dependency, migration or settings key, so the generated index
> is structurally unchanged (the skeleton is re-run at the phase's start as usual). Every change lands
> in existing files in place: `services/backfill_service.py` (one plan per request identity, no plan for
> an empty span, half-open *window membership* in the bar-level gap pass with the `now` cap inclusive —
> day presence (`present_days`) keeps its inclusive close, because `1 day` bars are stamped at the
> session close and a half-open presence test re-requests the whole daily history every load — and one
> 1.5-period gap threshold),
> `ui/ticker_session.py` (the prime's deferral backstop is derived from the retry's own deadline; the
> pre-issue refund branch and the `_history_req_issued` ledger are deleted), `ibkr/pacing.py` (the gate
> can be consulted without stamping; the inexact refund is deleted), `ibkr/market_data.py` (gate before
> the id, send, then stamp; a raising send rolls the id back), `ibkr/id_manager.py` (one new
> `release_id`), `data/bar_cache.py` (the mode-blind `get_last_timestamp` is deleted). Planned test
> modules (do not look for them yet, per the naming rule above): tests/test_d77_d82_d83_planner_identity.py,
> tests/test_d78_prime_retry_reachable.py, tests/test_d79_d80_d81_budget_honesty.py,
> tests/test_p27_fence.py; two existing cases are re-baselined (the D80 refund assertions in
> `tests/test_p7_w1_coalesce.py` and `tests/test_d56_taxonomy_pacing.py`) and two pacing doubles gain the new
> keyword-only parameter (tests/test_d65_option_chain.py, tests/test_ibkr_contract_details_d22.py).
> The phase's decisions are S-P27-1…S-P27-7 in `docs/architecture.md` § *Phase P27*; wave order is
> P27-01 ∥ P27-02 → P27-03 → P27-04 in `docs/plan.md` § *Phase P27* (02 and 03 share
> `ui/ticker_session.py`, so they serialise). `services/market_calendar.py` and `ui/main_window.py` are
> unchanged.
>
> **As-built P6-T13 note (2026-10-28):** the P6 plan-time sentences above ("pyqtgraph retained and default
> through Phase 10", "no pyqtgraph code is deleted before Phase 11") are **superseded history** — P6-T13 executed
> 2026-10-27 (removal commit `6e35b27`; gate owner-waived (live-session sign-off waived, not satisfied) per `docs/build/gate_P6_T13.md`). The tree is
> **LWC-only**: `ui/chart_view.py`::create_chart_view always returns the LWC view; `NDT_CHART_ENGINE` /
> chart/engine no longer select a renderer. Deleted: ui/chart_panel, ui/candlestick_item, the pyqtgraph
> overlay/control/router-companion modules, `ui/overlays/` contents (package marker only). Kept: the seam
> (`ui/chart_view.py`), the shared model (`services/chart_model.py`), the LWC host/view/bridge
> (`ui/lwc_host.py`, `ui/lwc_view.py`, `ui/lwc_bridge.py`), `chart_assets/lwc/`, `spikes/lwc/` (never imported).
> Row-level detail (parity vs deletion, retired suites) lives in `docs/lwc_parity_matrix.md`; gate disposition in
> `docs/build/gate_P6_T13.md`; the full outcome in `docs/architecture.md` § Phase P6 (as-built T13 outcome).
>
> **Status-cell reading rule for P6:** rows below that still carry a P5-era status (`[changed in P5]`,
> `deleted in P5`) describe the **delivered P5 end state**; under the P6 legend they read as `[existing]`
> (present, unmodified by P6) and deleted history respectively. Only the rows explicitly marked `[new in P6]` /
> `[changed in P6]` above change in P6.
>
> **Batch sequencing lives in `docs/plan.md` § *Phase P6*** (thirteen waves P6-01→P6-13, one commit per wave);
> the decisions (`S51`–`S60`, risks R86–R92) live in `docs/architecture.md` § *Phase P6*; the P5 record
> (`S39`–`S50`, `AR-D46-1`–`AR-D46-12`) lives in § *Phase P5*. *(Until 2026-10-25 these two pointers named the **superseded D45
> proposal drafts** `docs/plan_proposal.md` / `docs/architecture_proposal.md`. Do **not** read those for this batch:
> their `S29`/`AP-D45-1` decisions are superseded by P5, and a Build worker following them would preserve exactly
> what P5 deletes.)* This map carries the **module index**, not the rationale.

---

## Entry points

### `main.py` — `[existing]`
- **Responsibility:** the single app entry point: `QApplication` + `config/theme.qss`, `DB`, `IBApiClient`,
  `MainWindow`, exec loop. **Key symbol:** `main()`.
- **Test/dev use:** the dev build is the working target (`python main.py`); tests build `MainWindow` directly
  with `IBApiClient.connect` monkeypatched and `DB_PATH` exported to a temp file.

## `ui/` — widgets, layout and the chart

| Module | Responsibility (one line) | Status | Key entry points |
|---|---|---|---|
| `ui/main_window.py` (3,4xx L) | The window: docks, toolbar, load path, sessions, **error routing**, close teardown. | `[existing]` — P5 changed this file; P6 does not | Dock wiring `::__init__`, `::_apply_dock_widths` (the **single** dock-width apply point), `::_plan_dock_widths`, `::_chart_area_width`, `::eventFilter`, `::resizeEvent`, `::closeEvent`. P6 note: the load path keeps feeding the ChartView seam (renderer-only migration); no dock/toolbar/session change |
| `ui/watchlist_panel.py` (1,003 L) | The watchlist: header strip + table, tick cells, D21.5 columns, D22 add/remove, D39 search, D21.11/D44 collapse. | `[existing]` | `WatchlistPanel.header_bar`, `::header_button`, `::add_button`, `::search_box`, `::table` / `::body`, `::is_collapsed` / `::set_collapsed` / `::toggle_collapsed`, `::add_symbol` / `::remove_symbol` / `::clear`; pure helpers `watchlist_max_width`, `clamp_watchlist_width`, `load_watchlist_width`, `save_watchlist_width`, `should_load_on_double_click`, `normalise_symbol`, `symbol_in_list`, `ensure_symbol_present`, `sanitise_watchlist_columns`; constants aliased from `dock_layout`. **Unaffected by D45** — the D21.5 column popup and D22 add/remove are *not* the removed Portfolio menu |
| `ui/dock_layout.py` (139 L) | **Pure, Qt-free** single source of truth for dock widths (D17/D18/B3 cross-clamp, D44 collapsed width). | `[existing]` | `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `DEFAULT_WATCHLIST_WIDTH=220`, `RIGHT_DOCK_MIN_WIDTH=200`, `WATCHLIST_COLLAPSED_WIDTH=30`, `plan_watchlist_width`, `watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths`. **`CHART_MIN_WIDTH` must equal `ui/watchlist_panel.py` CHART_MIN_WIDTH** |
| `ui/visual_conventions.py` (203 L) | The shared VIS-D21 conventions: `DiagonalStrikeButton` (VIS-D21.1) + `set_button_active` / the active stylesheet (VIS-D21.2). | `[existing]` | `set_button_active(button, active)`, `ACTIVE_PROPERTY="active"`, `DiagonalStrikeButton.struck`, `VIS_D21_2_STYLESHEET` |
| ui/chart_panel (deleted by the P6 LWC build) | Was the pyqtgraph chart (panes, candles, volume, studies, overlays). | **deleted in P6** | Replaced by the ChartView seam (`ui/chart_view.py`) + LWC host (`ui/lwc_host.py`/`ui/lwc_view.py`); `services/chart_model.py` is the shared value source. Do not restore. |
| ui/candlestick_item (deleted by the P6 LWC build) | Was the candle `QPicture` renderer (+ the D42 `capped_body_half_width`). | **deleted in P6** | Rendering now lives in the LWC layer; the D42 density-cap wording is retired per D47/Q60 (`S56`). Do not restore. |
| `ui/ticker_session.py` (1,1xx L) | Per-symbol session: bars, waves, pacing, live bars, the S0 generic-tick substrate. | `[existing]` — **D45 changed this file; P5 does not** | `TickerSession.get_bars`, `::set_bars`, `::attach_view`, `::s0_register` / `::s0_register_many` / `::s0_deregister*`, `::on_s0_tick_string` (tick 59), `::dividend_info`, `::queue_wave_plans`; **D45 removes** the news `"292"` need registration, `::on_s0_tick_news`, `::add_news_push_listener` / `::remove_news_push_listener`, `::set_s0_headless`, the `_s0_headless` attribute **and the two `or self._s0_headless` clauses** in `::_s0_resync` / `::_s0_reissue`. **Retained verbatim:** the `"456"` dividend registration, tick 59, `_dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`/`events_unavailable` |
| ui/active_portfolio_panel.py (4xx L) | The right dock's Portfolio panel (D41/D21.13); **view-only after D45**; **deleted in P23** with the dock swap (`OptionSpreadsPanel` replaces it — nothing may import it after P23-01). | **`[deleted in P23]`** — historical record: **D45 changed this file; P5 did not** | `ActivePortfolioPanel.summary_label` (the right dock's title-bar toggle), `::is_collapsed`/`::set_collapsed`/`::toggle_collapsed`, `::refresh`, `::set_positions`/`::add_position`, the account-summary/positions render path, `::_group_and_render`/`::_render_table` (now **8 columns**); **D45 removes** the `TradeContextMenu` + `StopLossTargetDialog` imports/members, `::_show_context_menu`, `::_on_close_position`, `::_on_close_group`, `::_on_ungroup`, `::_on_flatten_all`, `::_on_set_sltp`, `::_on_sltp_confirmed`, `::update_position_sltp`, `::update_group_sltp`, `::_sltp_dialog`, the menu-only selection tracking (`_selected_row`/`_selected_position`/`::_on_selection_changed`), the `CustomContextMenu` policy, the five signals (`position_close_requested` / `group_close_requested` / `flatten_all_requested` / `position_sltp_changed` / `group_sltp_changed`), and the `Stop`/`Target` columns. **Storage note (D45 history, superseded):** D45 kept the `stop_loss`/`take_profit` model fields and DB columns (A87) — **P5 DROPS the columns and the fields by a guarded migration** (A99/`D46.12`, `S47`); this panel is not edited, and its 8 columns are unchanged |
| `ui/popout_window.py`, `ui/chart_mouse_router.py` | Pop-out charts, mouse-mode router. | `[existing]` | P6 re-hosts these surfaces per phase — the Python `RouterMode` TR-1…TR-17 contract is frozen. The pyqtgraph overlay companions (ui/drawing_overlay, ui/alarm_overlay, ui/event_marker_overlay, ui/zoom_overlay) were **deleted by the P6 LWC build** (drawings/alarms/markers now render through the LWC primitives/library layers); do not restore. |
| ChartView seam module (ui/chart_view.py — lands P6-02), shared chart-model module (services/chart_model.py — lands P6-03), LWC host + bridge assets (land P6-04), spike directory spikes/lwc (lands P6-01, never imported), parity-matrix doc docs/lwc_parity_matrix.md + spike-results doc docs/lwc_spike_results.md (land P6-01) | Strangler seam + single value source + offline host + throwaway evidence + gate record. **Named without backticks until they land.** | **`[new in P6]`** | Factory `create_chart_view(tz_offset, editable)`; `DrawingController`/`AlarmController` exact signal signatures; model value objects; `LwBridge` batched ops; matrix row dispositions |
| `ui/*_dialog.py`, `ui/toast.py`, `ui/chart_controls.py`, `ui/add_symbol_dialog.py` | Retained dialogs, toast, toolbar controls. | `[existing]` | `AddSymbolDialog` (D22), alarm/drawing/study dialogs — **none is an order or SL/TP surface** |
| **deleted in D45** — ui/news_digest_dock, ui/trade_context_menu, ui/stop_loss_target_dialog | The digest dock, the Portfolio context menu, the local-only SL/TP dialog. | **deleted** | not importable after D45; no replacement widget, menu or dialog exists (`AC-D45.1`/`.3`/`.6`) |
| `ui/overlays/` (`__init__.py` only) | Was the pyqtgraph overlay package. | **gutted in P6** | `base.py`, `session_overlay.py`, `gap_overlay.py`, `ict_overlay.py`, `vix_overlay.py` were **deleted by the P6 LWC build** (overlays now render on LWC); only the package marker remains. Do not restore. |

## `services/` — pure services (Qt-free unless noted)

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `services/market_calendar.py` | ET trading calendar + RTH/ETH session windows + the ESC-023 New-Year exception. | `[existing]` | `is_trading_day`, `trading_days`, `session_windows(start_ts, end_ts, ext_hours)` |
| `services/backfill_service.py` | The missing-span planner (D16/D42 depth floor). | `[existing]` | `find_missing_spans`, `plan_requests`, `floor_bar_budget`, `bar_period_seconds`, `MissingSpan`, `RequestPlan` |
| `services/time_collapse_service.py` | D21.4 display-only x-remap for collapsed non-trading gaps. | `[existing]` | `TimeCollapseMap._to_display` |
| `services/alarm_monitor.py`, `alarm_service.py`, `sound_service.py` | Alarm monitoring/state/sound. | `[existing]` | `AlarmMonitor` |
| `services/contract_lookup_service.py`, `symbol_search.py` | Symbol/contract resolution (D22 add, D39 search). | `[existing]` | `ContractLookupService.lookup`, `SymbolSearchService` |
| `services/drawing_service.py`, `indicator_service.py`, `ict_service.py`, `gap_vix_service.py`, `volume_baseline.py` (`strategy_detection.py` **deleted in P23**) | Drawings/studies/ICT/VWAP/D39 burst baseline. | `[existing]`; `strategy_detection.py` **`[deleted in P23]`** (`AC-D65.13`/A194 — its `Position.id` reader died with the account plane) | — |
| `services/session_service.py` | Equity RTH/ETH session shading bands. | `[existing]` | `session_bands` |
| `services/md_line_guard.py` | Market-data line budget guard. | `[existing]` | — |

## `data/` — persistence and models

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `data/db.py` (318 L) | SQLite schema + migrations (`bars`, `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline`). | **`[changed in P5]`** | `DB._init_schema`, `::_migrate_schema`, `::_table_columns`. **P5 wave 7** removes `stop_loss`/`take_profit` from both `CREATE TABLE` blocks and adds one guarded block to `_migrate_schema()` **after** the `idx_positions_symbol_con_id` statement: `_table_columns(table)` once, then `ALTER TABLE … DROP COLUMN` per column when present. Idempotent on a fresh DB (nothing to drop) and on every later open; each `DROP` is one atomic statement, so an interrupted open is completed by the next. Every row, the unique index, the FK and `sqlite_sequence` survive (measured 2026-10-25). No other table, index or migration touched. |
| `data/models.py` | `Bar` and the other row dataclasses (`Alarm`, `Study`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`). | **`[changed in P5]`** | `Bar`; **P5 wave 3 deletes the unused `UserOrder` dataclass** (zero consumers; its only reference was `tests/test_ui_smoke.py`:48), and **wave 7 deletes `Position.stop_loss`/`take_profit` and `TradeGroup.stop_loss`/`take_profit`** — the storage is dropped (`A99`, reversing A87). `dataclass`/`field` stay (used by `Study`); every other dataclass and field untouched. |
| `data/bar_cache.py` | Bar persistence + retention (`RETENTION_BARS`), D42 mode-aware key. | `[existing]` | `BarCache.save_bars` / `::get_bars` / `::prune` |
| `data/bar_aggregator.py` | Tick → bar aggregation. | `[existing]` | `BarAggregator` |
| `data/alarm_store.py`, `drawing_store.py`, `study_store.py`, `popout_store.py` | Per-feature stores. | `[existing]` | — |
| data/db_backup.py (**new in P23** — named without backticks until it lands, per the map lint rule) | The pre-drop SQLite backup: file copy into `config.paths`' app-support backups directory under a timestamped `charting_app_pre-D65_*.sqlite3` name, then a **read-only** verification of the copy (`PRAGMA integrity_check` + the three tables' row counts). | **`[new in P23]`** | `backup_before_drop`; its only production caller is `DB._migrate_schema` (P23-08), which aborts the drop if it raises. Never opens the app DB, so the ESC-043 opt-in gate is irrelevant to it. |
| data/events/ (**deleted** — directory absent from the tree) | Was the `EventProvider` ABC + the D38 event source. | **deleted** (removal landed before P7; recorded here so nothing re-plans it) | data/events/provider no longer exists; the D38 dividend/marker surface it fed is gone with the P6 render migration. Do not restore without a new requirement. |

## `ibkr/` — the broker boundary

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `ibkr/client.py` | `IBApiClient(EWrapper, EClient)`: the `ibapi` wrapper + reader thread + reconnect/teardown. | **`[changed in P5]`** | `IBApiClient.connect`, `::connected`, `::_on_disconnected`/`::_do_reconnect`; the fail-fast live-port check lives in `config/settings.py`::check_live_port. **P5 wave 2 deletes the `orderStatus` / `openOrder` / `execDetails` overrides** (the chain's only emitters) — the inherited `EWrapper` no-ops are what TWS then reaches. **Frozen and unchanged (`S46`):** `::error` — the `classify_error` severity gate, the D40.1 `502` backoff suppression and the `error_msg` emit — plus the lifecycle/account/position callbacks, and the news-boundary overrides (D45 `S35`). **Order transmit/cancel remain inherited from `EClient`** (`placeOrder`/`cancelOrder`/`reqGlobalCancel` are **not** defined here; D45's zero-call invariant stands, now enforced from the guard's forbidden set). **No `placeOrder` definition may be added.** |
| `ibkr/market_data.py` | Historical/RT market-data requests + `TIMEFRAME_CONFIG`. | `[existing]` | `MarketDataManager.req_historical_data`, `req_mkt_data(contract, generic_ticks=…)`, `TIMEFRAME_CONFIG` |
| `ibkr/contracts.py` (ibkr/account.py **deleted in P23**) | Contract helpers. | `contracts.py` **`[existing]`**, untouched by P23; `account.py` **`[deleted in P23]`** (`AC-D65.13`/A194 — the account/position plane) | `get_contract_for_symbol`. **P5 wave 7** deleted `ibkr.account.Position.stop_loss`/`take_profit` and `build_position_from_ib`'s two parameters and reworded the `Position.id` comment (`ESC-062`); P23 then removed the module with its only readers. |
| **deleted in P5** — ibkr/orders (`UserOrder`, `Orders` + the four builders, the registry, the `orders` singleton) | The order builders and the in-memory open-order registry. | **deleted in P5** | not importable after P5 (`import ibkr.orders` raises `ModuleNotFoundError`); its only importer was `ui/main_window.py`:36 and its registry was never written, so every read returned `None`. **The D45 decision to keep this module is OVERTURNED (A91/`S39`): it is deleted, nothing may restore it, and a future order path needs a new requirement rather than an un-comment.** |
| `ibkr/bridge.py`, `realtime_bars.py`, `pacing.py`, `id_manager.py`, `subscription_manager.py`, `stream_health.py`, `error_codes.py`, `utils.py` | Qt-signal bridge, RT bars, pacing, reqId allocation, the D27.3 subscription registry, stream health, error codes. | **`[changed in P5]`** — `bridge.py` (signals) and `error_codes.py` (**comment only**); `realtime_bars.py`, `pacing.py`, `id_manager.py`, `subscription_manager.py`, `stream_health.py`, `utils.py` are **`[existing]`, untouched** | `pacing_manager`, `MARKET_DATA`; **P5 wave 2 deletes the `order_status` / `open_order` / `exec_details` bridge signals** (with their client emitters); **wave 4 deletes `pacing.OrderRateLimiter` + `order_limiter`** (and `config/settings.py`'s `MAX_ORDER_NOTIONAL`); **wave 6 deletes `id_manager.reserve`** while `IdManager`, `get_id` and `set_next_valid_id` **stay** (six `get_id()` callers, incl. `ui/main_window.py`). The news signals (`tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article`) stay as the ibapi boundary mirror (D45 `S35`). **Frozen and unchanged:** `error_msg`; `::classify_error` in `ibkr/error_codes.py` (it gates **every** TWS error — only its 202 **comment** is reworded in wave 9, no code line); `PacingManager`/`PacingExceeded`; `IBApiClient.nextValidId`. |
| `ibkr/subscription_manager.py` | The D27.3 subscription registry: type-tagged entries with `reissue`/`rebind` hooks and the reconnect replay. | **`[changed in P23]`** — **one added module-level type tag** (`OPTION_LEGS`, value `"option_legs"`) and nothing else; `subscribe`, `unsubscribe`, `unsubscribe_all_of_type`, `entries_of_type` and `replay_all` are unmodified | `SubscriptionManager.subscribe`, `::replay_all` (`:94` — selected by tag, filters `reissue is not None`, raises `PacingExceeded` up front per D28.1). Tags `RT_BARS` / `MARKET_DATA` / `S0_TICKS`. **P23-05** adds the panel's leg tag so `_replay_subscriptions` can replay option legs without replaying the watchlist's MARKET_DATA rows (which `_restore_watchlist`'s pinned clear+re-add already re-issues, AC-D22.7.2). No method may be changed here without re-checking both call sites. |
| **deleted in D45** — ibkr/news, ibkr/validation | The news API client (`NewsManager`) and the order-validation gate (`validate_order`). | **deleted** | not importable after D45; `"292"` is never requested, and nothing builds an order for the gate to judge (`AC-D45.7`/`D26.7` moot) |

## `config/`, `packaging/`, root

| Path | Responsibility | Status | Key entry points |
|---|---|---|---|
| `config/settings.py` | Tunables (`SESSION_BAR_CAP`, `MAX_HISTORICAL_PER_600S`, `MIN_INTRADAY_SESSIONS`, …). | **`[changed in P5]`** | **P5 wave 4 deletes `MAX_ORDER_NOTIONAL`** and its `validate_order()` comment (zero readers; the gate died in D45). `check_live_port` and every other constant are frozen and untouched. |
| `config/paths.py` | `get_db_path()` (honours `DB_PATH`). | `[existing]` | `get_db_path` |
| config/instance_lock.py (planned, lands in P28-06) | Single-instance guard: one process owns the user-space DB (D95/A240). | **`[new in P28]`** (planned — the generated index lists the file from the next skeleton refresh; it is deliberately not backticked here because this map may not name a path that is not yet on disk) | `lock_path_for(db_path)` (`<db path>.lock`), `acquire(db_path) -> (QLockFile \| None, message)` — `QLockFile` with `setStaleLockTime(0)`/`tryLock(0)`, message from `getLockInfo()`. Called only from `main()`; no test constructs it indirectly |
| `config/theme.qss` | The app-level stylesheet. | `[existing]` | — |
| `main.py`, `NDThinkChart.spec`, `packaging/`, `dist/`, `build/` | Entry point + PyInstaller bundle. | `[existing]` | P28: `main()` takes the instance lock and imports `ui.main_window` lazily (the DB singleton is built inside `main()`, after `check_live_port`), shows `data.db.startup_notices()`, and `unlock()`s in a `finally`. `_register_lwc_scheme_before_qapp()` stays at module scope above `QApplication` — do not move it. |
| `pytest.ini`, `requirements*.txt` | Test config + pinned deps (`PyQt6`, `pyqtgraph`, `numpy`, `ibapi-latest==10.51.1`). | `[existing]` | — |

## `tests/` — the offscreen suite (131 modules)

**Invocation:** QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest (the pytest entry point has a stale
shebang — use `-m pytest`). Any **non-pytest** probe that can reach a DB-writing path must export `DB_PATH` to a
temp file. No test connects to live TWS or transmits an order.

| Group | Suites | Status |
|---|---|---|
| **D45 removal book** — **deleted (5, whole files):** tests/test_d28_6_close_contracts, tests/test_d41_retained_order_path, tests/test_order_validation, tests/test_kill_switch, tests/test_sltp_honesty. **Adjusted (6 + 1 deleted):** `tests/test_dock_d18_region.py` (`:147` dock filter; the five-signal receiver loop **deleted** — no signal survives), `tests/test_order_rejections.py` (the disconnected-close case; the observer cases kept), `tests/test_d28_pacing.py` (the close-deferral case; historical pacing kept), tests/test_d27_position_id.py (the SL/TP row-addressing case removed **in wave 2**; `8`/`9` → `6`/`7` **in wave 3**), tests/test_d27_flat_rows.py (the AC3 `_selected_position` tail dropped with the selection tracker; the index-alignment assertions kept), tests/test_d27_position_prices.py (`8`/`9` → `6`/`7`). **Kept unchanged (verified):** tests/test_stop_loss_target (model fields only), `tests/test_d41_removal.py` (`queue_depth` is an allow-list string), tests/test_order_builders (the retained ibkr/orders unit coverage — *D45's decision; **P5 deletes both the module and this suite**, see the P5 row above*). **New:** `tests/test_d45_removal.py` (static token scan + mocked-client zero-transmit walkthrough) | `[existing]` — **the delivered D45 record; P5 supersedes its ibkr/orders half** (see the P5 row below) |
| **P5 removal book (D46, revision 2)** — **deleted (2, whole files):** tests/test_order_builders (17 cases; the builders/registry), tests/test_stop_loss_target (3 cases; the four model fields). **Adjusted (13):** `tests/test_order_rejections.py` (two registry cases + their helpers removed; the third repointed **and renamed** at the generic line; the two `classify_error` cases kept; **one parametrised 201/103/202 surfacing case added** — 3 of the original 5 survive), `tests/test_d45_removal.py` (wave 1: the walkthrough's `_on_order_error` call repointed at `_on_error`; wave 8: the **ten** names moved from `_SURVIVORS` to the forbidden set — `_FORBIDDEN` 53 → 80 with **`orders`/`Orders` exact-matched** — plus the two absence pools, the end-state test (chain, module, `UserOrder`, `reserve`, the utilities, the four fields, the schema + idempotence) and the guard's own prose), `tests/test_ui_smoke.py` (`UserOrder` `hasattr`), tests/test_account.py (4 kwargs + 2 asserts), tests/test_strategy_detection.py (`:30`–`:31`), tests/test_d27_position_id.py (seeder + **one new case** seeding a non-null `trade_group_id`), tests/test_d27_account_partial_window.py and tests/test_d27_account_scoping.py (seeders), `tests/conftest.py` (the two `order_limiter` resets), `tests/test_d28_pacing.py` (`OrderRateLimiter` case + import), `tests/test_sound_service.py` (`TestFillBlip` + `:57` + **`paths["fill"]` at `:76`**), `tests/test_id_manager.py` (4 deleted, **2 rewritten**), `tests/test_dock_d18_region.py` (`ESC-062` rename + two docstrings). **Kept unchanged (verified):** `tests/test_d40_tws_lifecycle.py`, `tests/test_port_guard.py`, `tests/test_d41_removal.py`, `tests/test_db_schema.py`, every other suite. **Added:** none (the guard is reused, not duplicated) | **`[changed in P5]`** |
| Dock layout / widths (D13/D17/D18/D19/D21.13/D44) | `test_dock_layout.py`, `test_dock_widths_d17.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_right_dock_d21.py`, `test_dock_d18_region.py`, `test_d10_d13_integration.py`, `test_watchlist.py`, `test_toolbar_scroll_d19.py`, `test_d41_portfolio_dock.py`, `test_d41_removal.py`, `test_dock_widths_collapsed_d44.py`, `test_watchlist_collapsed_bar_d44.py` | `[existing]` (untouched by P5) |
| Watchlist panel (D14/D21.5/D21.11/D22/D39) | `test_watchlist_columns_d21.py`, `test_watchlist_add_remove_d22.py`, `test_watchlist_nonregression_d22.py`, `test_watchlist_d14_midrag.py`, `test_watchlist.py` | `[existing]` |
| Chart / render (D1–D12, D28.4, D42 width — pyqtgraph suites deleted by the P6 LWC build) | `test_candle_spacing.py`, `test_volume_width.py`, `test_chart_dpi.py`, `test_d28_4a_render_layers.py`, `test_volume_*.py`, `test_drawing_*.py`, `test_time_collapse_d21.py`, `test_collapse_resync_fix.py` — **all deleted in P6**; LWC parity suites (`test_lwc_*.py`, `test_chart_model.py`, `test_chart_view_seam.py`) are the current render coverage | **deleted in P6** |
| Data / planner (D16, D27, D28, D39, D42) | `test_backfill_service.py`, `test_history_backfill*.py`, `test_d27_*`, `test_d28_*`, `test_d39_*`, `test_d42_*`, `test_db_schema.py`, `test_market_calendar.py` | `[existing]` (the D38 event/news suite `test_d38_events_news.py` was deleted with data/events/; dividend/marker coverage now lives in the LWC overlay suites) |
| Alarm / account / orders / lifecycle (D25, D26, D40, D41) | `test_d25_*`, `test_d26_*`, `test_d27_account_scoping.py`, `test_d40_tws_lifecycle.py`, `test_d41_*`, `test_account.py` | `[existing]` — **after D45 there is no close/flatten/kill-switch/SL-TP coverage left, and after P5 no order-builder/registry coverage either** (both suites deleted); `test_order_rejections.py` keeps the **surfacing** proof (201/103/202 + `classify_error`), `test_d40_*`/`test_port_guard` keep the connection/error half (badge, port guard, 502 suppression) |
| Smoke / lifecycle harnesses | `test_d24_popouts.py`, `test_phase3_fixpass.py`, `test_d24_alarm_full_chain.py`, `test_d24_smoke_gate.py`, `test_d24_9_popout_persistence.py`, `test_d28_tick_burst_baseline.py`, `test_port_guard.py` | `[existing]` (these **drive** `MainWindow` — the `ESC-050` class; D45 does not touch the load path, and every one of them must stay green after the three window waves) |

## `docs/` — pipeline artifacts (ownership)

| Path | Owner | Note |
|---|---|---|
| `docs/requirements/requirements.md`, `design_gaps.md`, `open_questions.md`, `feature_suggestions.md` | Requirements Analyst | Requirements of record (`Status: READY_FOR_PLAN`, no blocking question); **D46 register, scope EXPANDED**, `AC-D46.1`–`AC-D46.13`, Journey 39, A91–A104, R76–R85, `design_gaps.md` DG78–DG87, `open_questions.md` Q56–Q59 (owner-answered, non-blocking) |
| `docs/architecture.md` § *Phase P5*, `docs/plan.md` § *Phase P5* | **Plan** (draft) / Validator (activation) | The P5 decisions (`S39`–`S50`), risks (`AR-D46-1`–`AR-D46-12`), the **three phases / ten waves**, the migration mechanism and the test book. **These are the authoritative pointers for this batch.** |
| `docs/architecture_proposal.md`, `docs/plan_proposal.md` | Plan (superseded) | **The D45 proposal pair — SUPERSEDED, not authoritative.** Their `S29`/`AP-D45-1` are superseded by P5; do **not** follow them for this batch. |
| `docs/codebase-map.md` | **Plan** | This map — refreshed per batch (memory 2026-10-23), refreshed for P5 |
| `docs/plan_notes.md`, `docs/plan_review_P5.md` | Validator | Escalation register and the P5 Plan review (`ESC-063`'s disposition lives in `plan_notes.md`) |
| `docs/tasks/`, `docs/build/`, `docs/code_review/` | Task Manager / `build_wave.py` / Code Reviewer | — |
| `docs/memory.md` | User (Orchestrator may append) | Locked decisions incl. the 2026-10-16 pyqtgraph lock, the 2026-10-15 delete-only worker lesson, and the `load_chart` symbol-uppercasing trap |
| `docs/phase-changelog.md`, `docs/ibkr-api-data-inventory.md`, `docs/thinkorswim-feature-gap-analysis.md` | historical reference | Surviving record of Phases 1–10 |
| `graphify-out/` | graphify tooling | `graph.json` (4,947 nodes) + `GRAPH_REPORT.md`; **discovery, not truth** — it still describes the pre-D45 tree |

---

## D45 delivery summary (reference only — delivered before P5; not this batch's work)

**Wave order (details in `docs/plan.md` § *D45 — Batch 20*, `Status: READY_FOR_TASK_MANAGER`, already built):**
`D45-01` Group A → `D45-02` Group B-main → `D45-03` Group B-panel → `D45-04` Group C → `D45-05` docs →
`D45-06` the new guard + batch gate. The three group tables below are the delivered record; **the retained order
surfaces they name are removed by P5** (see § *P5 touch summary*).

**Group A — News Digest + `View` menubar + `"292"` (`AC-D45.1`/`.2`, A79, A86, R68).**

| Module | What D45 changes |
|---|---|
| `ui/main_window.py` | Digest dock block + `menuBar()`/`View`/`_on_news_digest_visibility` + the `NewsManager` use + `b.tick_news.connect` + `_on_s0_tick_news`. The window then creates **no `QMenuBar`** |
| `ui/ticker_session.py` | The `"292"` need, `on_s0_tick_news`, the listener API, `set_s0_headless`/`_s0_headless` **and the two `or self._s0_headless` clauses**. **`"456"`/tick 59/`_dividend_info`/`dividend_updated`/`_merge_events` stay** |
| tests/test_d38_events_news | NewsManager + digest sections removed; **event-marker/dividend cases kept**; module docstring + the md-line docstring's `"292"` reference corrected |
| `tests/test_dock_d18_region.py` | `:147` `objectName() != "NewsDigest"` filter dropped |
| deleted | ui/news_digest_dock, ibkr/news |

**Group B — Trade Context Menu + the whole order path + the SL/TP dialog (`AC-D45.3`/`.4`/`.5`/`.10`, A80/A87/A89/A90, R69/R70/R75).**

| Module | What D45 changes |
|---|---|
| `ui/main_window.py` | The 5 Portfolio `.connect` lines, `_on_portfolio_close_position` / `_on_portfolio_close_group` / `_on_portfolio_flatten_all`, `_on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed` (with their row-`UPDATE`s), `_close_position_by_id`, `_ref_price_for`, the `validate_order` import, and the now-unused `order_limiter`/`UserOrder` import names. *(D45 kept the inbound observers + `order_registry`, `_symbol_last_prices`, `PacingExceeded` and the account/position render path — **P5 removes the observers and the registry import**.)* |
| ui/active_portfolio_panel.py | The menu member/import and policy, `_show_context_menu`, the close/close-group/ungroup/flatten handlers, the SL/TP chain (`_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`), the five signals, the menu-only selection tracking, and the **Stop/Target columns (10 → 8)**. **Retained:** the account-summary/positions render path, the D21.13 header, `_unrealized_pnl`, and the SL/TP **model fields/DB columns** (A87 — **SUPERSEDED by P5: dropped, A99/`D46.12`**) |
| `tests/test_dock_d18_region.py` | The five-signal receiver loop deleted; the wiring comment restated |
| `tests/*` | `test_d28_6_close_contracts`, `test_d41_retained_order_path`, `test_order_validation`, `test_sltp_honesty` deleted; `test_order_rejections`, `test_d28_pacing`, `test_d27_position_id` (AC3 case, **wave 2**), `test_d27_flat_rows` (**wave 3**), `test_d27_position_prices` adjusted; `test_stop_loss_target`, `test_d41_removal`, `test_order_builders` kept unchanged *(D45's decision — **P5 deletes `test_order_builders`**, because its subject is deleted too)* |
| deleted | ui/trade_context_menu, ui/stop_loss_target_dialog, ibkr/validation |

**Group C — Kill switch / the cancel path (`AC-D45.6`, A88, R73/R74).**

| Module | What D45 changes |
|---|---|
| `ui/main_window.py` | `kill_btn` + its preceding `QLabel("|")` separator + tooltip/style/connect, `_on_kill_switch_clicked`, `_kill_switch` (the `reqGlobalCancel()` call, the per-ID `cancelOrder()` loop, the pre/post counts, the `Cancelled` marking). The toolbar keeps its remaining widgets and its trailing `addStretch()`. **No replacement control; no teardown/disconnect cancel** |
| `tests/*` | `test_kill_switch` deleted |
| docs | `USAGE.txt` (kill-switch bullet, the "orders cannot be placed while disconnected" claim), `usage.md` |

**Retained by decision after D45** (do **not** "clean up"): the bridge's news signals and the client's ibapi news
overrides (the ibapi boundary mirror, D45 `S35`), `MainWindow._symbol_last_prices` (feeds the Portfolio P/L), and
`tests/test_d41_removal.py` verbatim. **Overturned by P5:** the old "ibkr/orders retained + inert observers" row —
both are **deleted**; the three leftovers D45 named as out of scope — config/settings.MAX_ORDER_NOTIONAL,
`ibkr/pacing.py` order_limiter and `ibkr/id_manager.py`'s `reserve` — are **tasks** in P5 (waves 4 and 6), with the module
and `get_id` retained; and **A87's `stop_loss`/`take_profit` storage is DROPPED** (A99, wave 7) — the D45 sentence
"columns and fields stay" is history, not the end state (see the P5 groups below).

---

## P5 touch summary (D46) — three member groups, one forced wave order

**Wave order (details in `docs/plan.md` § *Phase P5*):** `P5-T01` window consumers → `P5-T02` broker boundary →
`P5-T03` module + `data.models.UserOrder` → `P5-T04` pacing + notional cap → `P5-T05` order-fill sound →
`P5-T06` `IdManager.reserve` → `P5-T07` **stop/target storage (schema + every reader)** → `P5-T08` the instrument →
`P5-T09` surviving prose → `P5-T10` the batch gate.
`ui/main_window.py` is edited **twice** (waves 1 and 7); `data/models.py` twice (3 and 7);
`tests/test_d45_removal.py` twice (waves 1 and 8, different lines).
**Ordering is forced, not stylistic:** the consumer half goes first, each signal dies **with** its only emitters, the
module dies after its importers, and the schema lands **with** its readers — a signal deleted one wave before its
emitter raises `AttributeError` only on a live TWS order callback, and a skipped index shift silently puts a stop
value in the **Group** column, so the suite would stay green while the app broke. **The guard's token set lands
last** among the removals, because a token may only name code that is already gone.

**Group 1 — window consumers (`AC-D46.2`, wave 1).**

| Module | What P5 changes |
|---|---|
| `ui/main_window.py` | The `from ibkr.orders import orders as order_registry` import, the three `open_order`/`exec_details`/`order_status` connects, `_on_open_order` / `_on_order_status` / `_on_exec_details` / `_update_order_status` / `_on_order_error`, and the `order_registry.get(reqId)` branch + D26.9 comment inside `_on_error`. **Kept verbatim:** `_on_error`'s `_closing` guard, its session routing and its `Error [<code>]: <string>` 8000 ms line |
| `tests/test_order_rejections.py` | the two registry cases + helpers + the `ibkr.orders` import removed; `test_non_order_error_untouched` repointed/renamed at the generic line; the two `classify_error` cases kept; **one parametrised 201/103/202 surfacing case added** |
| `tests/test_d45_removal.py` | the walkthrough's `_on_order_error` call + docstring bullet repointed at `_on_error` |

**Group 2 — broker boundary (`AC-D46.2`, wave 2; one task, emitter + signal together).**

| Module | What P5 changes |
|---|---|
| `ibkr/client.py` | the `orderStatus` / `openOrder` / `execDetails` overrides **deleted whole** (no stubs). `error` (gate + D40.1 `502`) untouched |
| `ibkr/bridge.py` | the `order_status` / `open_order` / `exec_details` signals **deleted**; `error_msg` and the news-boundary signals stay |

**Group 3 — the module and its data-model twin (`AC-D46.1`/`.8`, wave 3).**

| Module | What P5 changes |
|---|---|
| ibkr/orders | **deleted** (whole file). No replacement, no dormant helper |
| `data/models.py` | the unused `UserOrder` dataclass **deleted** (wave 3); the four stop/target fields go in **wave 7** |
| tests/test_order_builders | **deleted** (17 cases, all for the deleted builders/registry) |
| `tests/test_ui_smoke.py` | the `UserOrder` `hasattr` dropped; `Position`/`Drawing` kept |

**Group 4 — pacing + notional cap (`D46.11`, wave 4).** `ibkr/pacing.py` loses `OrderRateLimiter` + `order_limiter`
(`PacingManager`/`PacingExceeded`/`pacing_manager` stay); `config/settings.py` loses `MAX_ORDER_NOTIONAL` and its
`validate_order()` comment; `tests/conftest.py` loses its two `order_limiter` resets; `tests/test_d28_pacing.py` loses
the import and its one `OrderRateLimiter` case.

**Group 5 — order-fill sound (`D46.11`, wave 5).** `services/sound_service.py` loses `render_fill_blip`,
`BLIP_DURATION`, `_fill_effect`, `play_fill`, the `"fill"` key and `order_fill.wav`, and **`_effect` collapses to
alarm-only** (its ternary names `"_fill_effect"` in a string constant the AST scan sees); `play_alarm`,
`render_alarm_chime` and the `"alarm"` key stay. `tests/test_sound_service.py` loses `TestFillBlip` (2), the
`render_fill_blip` use and the `paths["fill"]` assertion → **9 → 7 cases** (executed: 9 collected today).

**Group 6 — `IdManager.reserve` (`D46.10`, wave 6).** `ibkr/id_manager.py` loses `reserve` and its D26.2 docstring;
**the module and `get_id` stay** (six callers). `tests/test_id_manager.py` loses four cases and **rewrites two** →
**8 → 4 cases**.

**Group 7 — the stop/target storage (`D46.12`, wave 7, one task).** `data/db.py` (DDL + the guarded migration),
`data/models.py` (four fields), ibkr/account.py (two fields + two factory parameters), `ui/main_window.py` (the two
`_persist_position` kwargs, the `columns` tuple, the **name-keyed** bulk read with `trade_group_id` 14 → 12, the
upsert's columns/placeholders/`DO UPDATE`/values) — plus the whole test book (`test_stop_loss_target` **deleted**;
`test_account`, `test_strategy_detection`, the three seeders adjusted; **one new case** seeds a non-null
`trade_group_id`).

**Group 8 — the instrument (`D46.9`, wave 8).** `tests/test_d45_removal.py`: `_SURVIVORS` 26 → 16, `_FORBIDDEN`
53 → 80 (`orders`/`Orders` exact-matched, the other 25 new tokens substring; **`reserve` is not a token**), two
`_DELETED_*` entries, the end-state test (chain, module, `UserOrder`, `reserve`, the utilities, the four fields in all
three classes, the schema + a no-op second open), and the guard's own prose.

**Prose (wave 9, `AC-D46.6`/`D46.13`).** `ibkr/error_codes.py` — reword only `classify_error`'s 202 comment (no code,
no threshold); `usage.md` — drop tests/test_order_builders from the pytest example **and** rewrite the Database
bullet (the SL/TP columns are **dropped by a one-time migration**); `USAGE.txt` — rewrite the stop/target bullet the
same way, **keeping** its status-bar sentence verbatim; `tests/test_dock_d18_region.py` — the `ESC-062` rename and two
docstrings.

**Removed by P5 (nothing replaces them):** ibkr/orders (`UserOrder`, `Orders`, four builders, registry,
singleton) · the three `orderStatus`/`openOrder`/`execDetails` overrides · the three `order_status`/`open_order`/
`exec_details` bridge signals · `MainWindow._on_open_order` / `::_on_order_status` / `::_on_exec_details` /
`::_update_order_status` / `::_on_order_error` + the `_on_error` registry branch + the `order_registry` import ·
`data.models.UserOrder` · `pacing.OrderRateLimiter` + `order_limiter` · `settings.MAX_ORDER_NOTIONAL` ·
`sound_service`'s order-fill path · `IdManager.reserve` · **the `positions`/`trade_groups` `stop_loss`/`take_profit`
columns and the four model fields** · tests/test_order_builders · tests/test_stop_loss_target.

**Survivors after P5 (must NOT be reported as residue, and must NOT be "tidied"):** `classify_error` · `_on_error` ·
`error_msg` · `IBApiClient.error` (gate + D40.1 `502`) · `check_live_port` · the connection badge ·
**`IdManager` / `get_id` / `set_next_valid_id` / `id_manager`** (six `get_id()` callers — `reserve` alone goes) ·
**`nextValidId`** (the CONNECTED transition) · `PacingManager` / `PacingExceeded` / `pacing_manager` ·
`_symbol_last_prices` · the dividend path (`"456"`, tick 59) · the ibapi news boundary · **ICT
`order_blocks`/`orderBlocks`/`_render_order_blocks`** · **`sort_order`** · **`Position`/`positions`/the Portfolio view (8 columns)** and the strategy grouping
(`strategy_detection` over `Position.id`) · **`TradeGroup`/`trade_groups`/`position_group_map` — dead storage (zero
readers, zero writers) retained only to avoid widening the batch** (audit R10 correction; not a display consumer) · **`play_alarm`/`render_alarm_chime`/the
`"alarm"` key** · **`advancedOrderRejectJson`**.

**Removed from the revision-1 survivor list because they are now tasks:** `order_limiter` and `MAX_ORDER_NOTIONAL`
(wave 4, **forbidden** tokens), the order-fill sound (wave 5), `IdManager.reserve` (wave 6, measured by `hasattr`),
and the `stop_loss`/`take_profit` **storage** — the columns are **dropped** by the wave-7 migration and the four
model fields with them (`A99`, reversing A87). Nothing in this file may claim those columns or values survive, and
nothing may claim they are "kept".

**P5 test-impact (Plan-confirmed, outside the generated rows below)** — `select_tests.py` should treat these as
the modules whose changes can affect the named suites:

| Changed module | Test modules to select |
|---|---|
| `ui/main_window.py` | `test_order_rejections`, `test_d45_removal`, `test_d40_tws_lifecycle`, `test_port_guard`, `test_d41_removal`, `test_d27_position_id`, `test_d27_account_scoping`, `test_d24_smoke_gate`, `test_phase3_fixpass`, `test_dock_d18_region` |
| `ibkr/client.py` | `test_d40_tws_lifecycle`, `test_port_guard`, `test_d45_removal`, `test_d41_removal`, `test_d27_stream_health` |
| `ibkr/bridge.py` | `test_d45_removal`, `test_d24_smoke_gate`, `test_d27_stream_health`, `test_d28_2_sessions` |
| `data/models.py` | `test_ui_smoke`, `test_account`, `test_strategy_detection`, `test_d27_account_subs`, `test_d27_flat_rows` |
| `ibkr/error_codes.py` (comment only) | `test_order_rejections`, `test_d45_removal` |
| ibkr/account.py | `test_account`, `test_d27_position_id`, `test_d27_account_scoping` |
| `data/db.py` (schema + migration) | `test_d27_position_id`, `test_d27_account_partial_window`, `test_d27_account_scoping`, `test_db_schema`, `test_d45_removal` |
| `ibkr/pacing.py`, `config/settings.py` | `test_d28_pacing`, `test_d45_removal` (conftest's pacing fixture runs everywhere) |
| `services/sound_service.py` | `test_sound_service`, `test_d24_alarm_full_chain` |
| `ibkr/id_manager.py` | `test_id_manager`, `test_d45_removal` |
| ibkr/orders (deleted), tests/test_order_builders, tests/test_stop_loss_target (deleted) | `test_d45_removal` (the guard asserts the absence) |

**P6 test-impact (Plan-confirmed):** the generated rows above stand. P6 adds: the chart-model module → the
chart/render suites (candles, volume, collapse, bands, crosshair, drawings, alarms, overlays) + a delegation probe;
the ChartView seam module → new factory/signal-signature suites; the LWC host/bridge → batch-shape, replay-identity,
offline/interceptor suites + `node --test` JS suites; webengine-gated suites report `@pytest.mark.webengine`
(skip-never-red) with named manual-checklist counterparts. `select_tests.py` should treat ui/chart_panel
delegation as affecting every chart/render suite (they must stay green unmodified per `AC-D47.2`).


**P23 test-impact (Plan-confirmed, outside the generated rows)** — `select_tests.py` should treat these as
the modules whose changes can affect the named suites:

| Changed module | Test modules to select |
|---|---|
| `ui/main_window.py` (dock swap + launch width + option wiring + account path + badge) | `test_d65_option_panel`, `test_d65_option_stream`, `test_d65_residue`, `test_d41_removal`, `test_right_dock_d21`, `test_dock_d18_region`, `test_dock_widths_d18`, `test_dock_widths_d18_impl`, `test_dock_widths_collapsed_d44`, `test_watchlist_nonregression_d22`, `test_p13_gate`, `test_port_guard`, `test_d45_removal`, `test_d24_smoke_gate`, `test_phase3_fixpass`, `test_ui_smoke`, `test_db_schema` |
| `ibkr/client.py`, `ibkr/bridge.py` | `test_d65_option_chain`, `test_d65_option_stream`, `test_d65_residue`, `test_d40_tws_lifecycle`, `test_d45_removal`, `test_d27_stream_health` |
| `ibkr/contracts.py`, `ibkr/market_data.py` | `test_d65_option_chain`, `test_d65_spread_engine`, `test_contract_lookup_d22`, `test_p20_futures_scoping`, `test_d28_pacing` |
| `data/db.py`, `data/models.py` | `test_db_schema`, `test_d45_removal`, `test_d65_residue`, `test_ui_smoke` |
| `ui/watchlist_panel.py`, `ui/ticker_session.py` | `test_watchlist`, `test_watchlist_columns_d21`, `test_watchlist_add_remove_d22`, `test_d28_2_sessions`, `test_p13_fanout`, `test_d17_d18_*` (dock widths) |
| `ui/option_spreads_panel.py`, `services/option_ladder.py`, `services/option_spread_engine.py` | `test_d65_option_panel`, `test_d65_option_ladder`, `test_d65_spread_engine`, `test_d65_option_stream`, `test_d65_residue`, test_d66_delta_fence (from P24) |
| deleted (ui/active_portfolio_panel.py, ibkr/account.py, services/strategy_detection.py) | `test_d65_residue` (absence), `test_d41_removal`, `test_right_dock_d21`, `test_dock_d18_region` (re-pointed) |

P23's **`tests/conftest.py`** edit (dropping the three dropped tables from the autouse teardown wipe list) affects **every** suite at teardown, so `select_tests.py` should treat that file as suite-wide rather than mapping it to a list. `tests/test_db_schema.py` and `tests/test_ui_smoke.py` are reached through the `data/` and `main_window` rows above; `tests/test_dock_widths_collapsed_d44.py` is selected only for regression (it exercises the **left** watchlist dock and takes no P23 edit).

**P23-01 deletes six suites, so drop them from selection once that wave lands** — `test_d27_account_subs`, `test_d27_account_scoping`, `test_d27_account_partial_window`, `test_d27_flat_rows`, `test_d27_position_id`, `test_d27_position_prices`. Each one reads `win.portfolio_panel` (its `positions_table`, `account_detail` or `_positions`) or imports `ui.active_portfolio_panel`, so its subject is the **panel** P23-01 swaps out, not the window account path P23-06 removes; they cannot outlive wave 1. `tests/test_d45_removal.py` survives and is edited in four waves (P23-01, -06, -07, -08) — `select_tests.py` should select it for every P23 wave.

**P23-01 also re-points twenty surviving dock-lookup harnesses** — `test_history_backfill`, `test_history_backfill_disconnect`, `test_history_backfill_loadpath`, `test_d42_depth_floor`, `test_d27_phantom_alarms`, `test_d27_reconnect`, `test_d27_stream_health`, `test_p7_w1_persist`, `test_p7_w2_prime`, `test_p7_w2_watchdog`, `test_p14_indicator`, `test_p14_cache_guard`, `test_p14_lifecycle`, `test_p15_surfacing`, `test_p15_expiry`, `test_p15_continue`, `test_p20_resolution_probe`, `test_d10_d13_integration`, `test_watchlist_columns_d21`, `test_dock_widths_d17`. Each hides the right dock by its `Portfolio` title today (three assert the lookup resolved and hard-fail at the rename; the rest silently stop hiding), and all twenty are edited to `objectName()` in the rename's own wave — select them for P23-01, and for no other P23 wave.

**P24 note (2026-11-18) — D66: the PCS ordering delta on the green P23 tree.** **No new module and no
new production file**, so the generated skeleton below is unchanged (273 code files, 24 test-impact
rows). **One production change:** `services/option_ladder.py` `[changed in P24]` — `RUNG_OFFSETS`
becomes a **per-side, row-ordered** table (CCS `(1,+10) (2,+5) (3,0) (4,−5)`; PCS `(4,+5) (3,0)
(2,−5) (1,−10)`), `ladder_pairs` reads it in row order, the "one table on both sides" docstring and
comments are rewritten (DG127), and the `SpreadRow` docstring gains the display-row vs label
distinction (S-P24-3). Everything else in that module is unchanged. **`[existing]` unchanged:**
`services/option_spread_engine.py` (anchor = the offset-0 pair; `rows()` enumerates row order, so PCS
rows simply arrive in the new order; `SpreadRow.rung` stays the 1-based display row), `ui/option_spreads_panel.py`
(renderer only; Target row 3 on CCS / 2 on PCS falls out of the row list), `ui/main_window.py`,
`ibkr/*`. **Tests:** five suites `[changed in P24]` — `tests/test_d65_option_ladder.py` (per-side
offsets, corrected canonical PCS 7330/7310, 7325/7305, 7320/7300, 7315/7295), 
`tests/test_d65_spread_engine.py` (`mirror_table` re-centred + a window-coverage assertion),
`tests/test_d65_option_stream.py` (`EXPECTED_SHORTS` split per side; PCS row indices shift one up),
`tests/test_d65_option_panel.py` (PCS snapshot fixture pinned to the anchor pair 7325/7305) and
`tests/test_d65_residue.py` (`CANONICAL_FIXTURES`' PCS entry re-pointed 7340/7320 → 7325/7305; the
gate body, its holder list and the ban lists untouched) — plus **one new fence suite**
(tests/test_d66_delta_fence.py, named without backticks until it lands). `tests/test_d65_option_chain.py`
and `tests/test_d65_acceptance_record.py` are untouched. **Selection:** add
the fence suite (and `test_d65_option_panel`) to the option-modules row below so a future change to
`services/option_ladder.py` selects the whole D65/D66 set.

**P25 note (2026-11-19) — D67–D70: four silent-wrong-data defects, no new module.** Skeleton re-run
2026-11-19 for HEAD `94d6119` (**274 code files, 23 test-impact rows** — drift since P24 is test modules
only). **No new production module, no dependency, no migration, no wire-version bump.** `[changed in P25]`
edits land in place: `data/bar_aggregator.py` (period base adoption, `_AggState.first_ts`, `covering_since`
— `push`'s observable contract unchanged, it records `first_ts` at state creation;
`period_start`/`current_bar` byte-identical; the replay guard survives adoption), `data/models.py` (one
transient `Bar.partial` field, `compare=False`, never persisted), `services/market_calendar.py` (added
`first_session_open` beside `session_windows`), `ui/ticker_session.py` (base adoption in `set_bars`,
week/month prime suppressed when a base exists, `partial` stamped on the forming bar, a `_wall_now` clock
seam), `ui/lwc_view.py` (marker leg: driven toward the forming bar's `(ts, partial)`, moved on a rollover),
`ui/lwc_bridge.py` (sequence-stamped staging → arrival-ordered emission, `set_partial` accepted, one
whitespace rule in `apply_ops_to_bars`), `ui/popout_window.py` (pop-out-local RT-hold latch + closed latch —
`TickerSession` hold API untouched, per `tests/test_p13_hold_fix.py`), and the two page assets
`chart_assets/lwc/envelope.js` / `chart.js` (the `set_partial` directive + one `createSeriesMarkers` marker,
and D70's whitespace rule in the page's fold — `mergeRows` skips/deletes a whitespace row, `upsertRow`
sends `{time}` only). `ui/main_window.py` changes by **one line** (wiring
`session._wall_now = lambda: self._now_ts()` at session creation, before any `set_bars`). **`[existing]`
unchanged:** `services/backfill_service.py`, `ibkr/**`, `data/bar_cache.py`, `data/db.py`,
`services/chart_model.py`, `ui/lwc_host.py`, `ui/chart_view.py`, the option stack. **Tests:**
`[changed in P25]` — `tests/test_d48_mode_parity.py` (one docstring sentence: a week/month load with a
current-period bar now primes nothing); **new** — tests/test_d67_forming_candle.py,
tests/test_d68_hold_balance.py, tests/test_d69_d70_bridge_contract.py, tests/test_p25_fence.py, plus
node cases in `chart_assets/lwc/chart.test.js` / `envelope.test.js`. **Selection:** a change to
`ui/lwc_bridge.py` should select the whole envelope set (`test_lwc_bridge`, `test_lwc_time_parity`,
`test_lwc_page_wiring`, `test_lwc_drawings`, `test_lwc_alarms`, `test_p7_w1_coalesce`, `test_d57_*`,
`test_d60_*`, `test_d63_crosshair_free`, and the three new P25 suites); a change to
`data/bar_aggregator.py` or `ui/ticker_session.py` should select `test_bar_aggregator`,
`test_d27_aggregator_priming`, `test_d48_data_plane`, `test_d48_gate`, `test_d48_mode_parity`,
`test_p7_w4_streaming`, `test_p13_hold_fix`, `test_p13_attach`, `test_d24_popouts`, `test_lwc_popouts` as
well as their generated rows.

**P28 note (2026-11-19) — D84–D95: connection, startup and window lifecycle; one new module (not yet on
disk).** Skeleton re-run 2026-11-19 at **HEAD `0ff7964`** (P27 build): **289 code files, 11 module rows,
23 test-impact rows** — the drift since the P25 note is test modules only. **P28 adds exactly one
production module — the instance lock, config/instance_lock.py** (`[new in P28]`, planned; it gets its
annotation row below now and its generated index entry from the next skeleton refresh, because the file
does not exist yet and this map may not name a path that is not on disk). No dependency, no migration, no
settings key. **Rows whose P5-era status cell is stale for P28** (the cell says
`[changed in P5]`/`[existing]`; see the row's note for the current contract): `main.py`,
`config/settings.py`, `ibkr/client.py`, `ibkr/realtime_bars.py`, `ibkr/stream_health.py`,
`ui/main_window.py`, `ui/ticker_session.py`. **P28 read set (all `[existing]` unless its row says
otherwise):** `ibkr/error_codes.py`, `ibkr/market_data.py`, `ibkr/realtime_bars.py`, `ibkr/client.py`,
`ibkr/stream_health.py`, `ibkr/pacing.py`, `ibkr/id_manager.py`, `ibkr/subscription_manager.py`,
`ui/ticker_session.py`, `ui/main_window.py`, `ui/popout_window.py`, `data/db.py`, `data/db_backup.py`,
`data/popout_store.py`, `data/bar_cache.py`, `config/settings.py`, `config/paths.py`, `main.py`,
`services/market_calendar.py`, `services/backfill_service.py`. **Untouched by P28:** `ui/popout_window.py`
(P25's transactional `attach`/`detach`/`closeEvent` are the close path P28 orchestrates), `data/db_backup.py`,
`data/popout_store.py`, `config/paths.py`, and the three `ibkr/pacing.py` / `ibkr/id_manager.py` /
`ibkr/subscription_manager.py` contracts.
The per-file deltas (what each site encodes today → what P28 changes) live in `docs/architecture.md`
§ *Phase P28* § *Codebase Summary*; this note only points. **Selection:** a change to
`ui/main_window.py`'s RT/close paths should select `test_d27_stream_health`, `test_d28_5_teardown`,
`test_d24_popouts`, `test_lwc_popouts`, `test_d68_hold_balance` plus the P28 suites; a change to
`ibkr/realtime_bars.py` or `ibkr/stream_health.py` should select `test_ibkr_handshake_gate`,
`test_d27_stream_health`, `test_p7_w4_streaming`, `test_d71_replay_transaction`; a change to `main.py` or
`data/db.py` should select `test_port_guard`, `test_lwc_host_bootstrap`, the D65 backup suites and
`test_d86_d94_startup`.

**P29 note (2026-11-20) — D96–D100: persisted state and alarm evaluation; no new module, and the four suites have landed.** Skeleton
re-run against the **P29 build tree** (working tree on `3b92ce6`, P29 build uncommitted; phase baseline
`1404877`, base `ef04c5a`): **303 code files, 23 test-impact rows**. **P29 adds no production module and no
dependency, migration, settings key or wire-protocol change**, so the index shape is unchanged. The drift
since P28's 298-file figure is one P28-rework suite (`tests/test_p28_seam_diff_shape.py`, committed with the
P28 close-out) plus P29's four new test modules, which are now on disk and green.

| Row moved by P29 | What the row now means | Status |
|---|---|---|
| `data/study_store.py` | `save` serializes every row before touching the connection and replaces the set inside one `with db.conn:` transaction; `load` / `sanitize_study_params` unchanged | `[changed in P29]` |
| `data/drawing_store.py` | `update_group` rejects unknown keys **before** any SQL and derives columns, placeholders and values from one filtered pair list; bool → int keyed on `visible` / `locked`; every other method unchanged | `[changed in P29]` |
| `services/alarm_service.py` | `evaluate_alarms` is `prev <= level < curr` / `prev >= level > curr` (arrival at the level is a touch, not a crossing); `evaluate_volume_burst` / `_resolve_z_threshold` unchanged | `[changed in P29]` |
| `services/alarm_monitor.py` | `begin_outage()` added (no session → no outage, so a failed launch cannot wipe the cache seed) + `_outage_active`; `_pause_start` renamed `_outage_start`; `resume_all` re-seeds only a resume that follows a recorded outage; `format_gap_report` / `reconcile` unchanged | `[changed in P29]` |
| `ui/main_window.py` | `_on_disconnected` records the outage interval before classification; `_on_connected` has one resume path (`reconcile()` → `resume_all()`), the `_resuming_from_pause` branch is gone | `[changed in P29]` |
| `ui/lwc_bridge.py` | a page-ready transition clears `_queued` / `_outbox` / `_live_buf` and replays `_op_log` once; `set_ready` cannot emit; `ENVELOPE_VERSION`, the op set and the channel path unchanged | `[changed in P29]` |
| `ui/lwc_host.py` | one `loadFinished` comment word ("drain + replay" → "replay"); the ordering contract is untouched | `[changed in P29]` |

**Stale status cells (this note is the authority):** the `data/` combined store row, the `services/` alarm
row, `ui/main_window.py`, and the P6 LWC row that carries `ui/lwc_bridge.py` / `ui/lwc_host.py` still show
their P5/P6 status; P29 changed those seven files in place, as the table above records.

**Test rows, all on disk and green.** `[new in P29]` — tests/test_d96_d100_store_atomicity.py,
tests/test_d98_outage_baseline.py, tests/test_d99_page_ready_delivery.py, tests/test_p29_fence.py (the fence
is 13 tests: it pins the requirements record plus the phase's live decisions). `[changed in P29]` — the three
**named re-baselines**: tests/test_alarm_service.py::TestBoundaryAndState::test_exactly_on_alert_price_above_counts,
tests/test_d40_tws_lifecycle.py::test_d40_4_transient_drop_no_pause_ui and
tests/test_lwc_bridge.py::TestBatchShape::test_queue_until_ready_holds_pre_ready_ops, plus **five**
`_pause_start` reads in four D40 cases — four renames (`:199`, `:364`, `:375`, `:402`) and one assertion
whose value changes (`:445`, inside the re-baselined transient case). The per-file deltas live in
`docs/architecture.md` § *Phase P29* § *Codebase Summary*; the decisions are S-P29-1…S-P29-5; the wave
order was P29-01 ∥ P29-02 ∥ P29-04 → P29-03 → P29-05. **Selection:** a change to
`data/study_store.py`/`data/drawing_store.py` should select `test_drawing_store`, `test_p9_recolor`,
`test_p10_drag_commit`, `test_p10_lock_recolor`, `test_p9_group_dialog`, `test_p9_group_payload`,
`test_p9_active_group`, `test_p10_groups_dialog_lock`, `test_lwc_studies`, `test_studies_dialog`,
`test_db_schema` and `test_d96_d100_store_atomicity`; a change to `services/alarm_service.py` or
`services/alarm_monitor.py` / `ui/main_window.py`'s drop/connect block should select `test_alarm_service`,
`test_alarm_d21`, `test_d24_alarm_full_chain`, `test_d25_alarm_monitor`, `test_d27_phantom_alarms`,
`test_p9_alarm_persistence`, `test_d27_reconnect`, `test_d40_tws_lifecycle` and
`test_d98_outage_baseline`; a change to `ui/lwc_bridge.py` should select the whole envelope set
(`test_lwc_bridge`, `test_lwc_bridge_handshake`, `test_d69_d70_bridge_contract`, `test_lwc_page_wiring`,
`test_lwc_time_parity`, `test_p7_w1_coalesce`, the LWC overlay/alarm/drawing/study suites) and
`test_d99_page_ready_delivery`. **Generator note (standing):** the 2026-11-20 skeleton run still emits the
root row as a slash-suffixed (root) token, which the map lint reads as a path and rejects; the row is kept in
its slash-free form below — `update_codebase_map.py` should emit it that way.


<!-- MAP-SKELETON:BEGIN -->
## Module index (generated — do not hand-edit inside the skeleton markers)

- (root) — main.py, probe_D53_4phase.py, probe_deep.py, probe_live_backfill.py
- `chart_assets/lwc/` — alarms.js, all.js, chart.js, chart.test.js, envelope.js, envelope.test.js, follow_offset.test.js, gestures.js, gestures.test.js, interaction.js, lightweight-charts.standalone.production.js, overlays.js, primitives.js, studies.js, tz_format.test.js, volume_scale.test.js
- `config/` — __init__.py, instance_lock.py, paths.py, settings.py
- `data/` — __init__.py, alarm_store.py, bar_aggregator.py, bar_cache.py, db.py, db_backup.py, drawing_store.py, models.py, popout_store.py, study_store.py
- `ibkr/` — __init__.py, bridge.py, client.py, contracts.py, error_codes.py, id_manager.py, market_data.py, pacing.py, realtime_bars.py, stream_health.py, subscription_manager.py, utils.py
- `packaging/` — __init__.py
- `services/` — __init__.py, alarm_monitor.py, alarm_service.py, backfill_service.py, chart_model.py, contract_lookup_service.py, drawing_service.py, gap_vix_service.py, ict_service.py, indicator_service.py, market_calendar.py, md_line_guard.py, option_ladder.py, option_spread_engine.py, session_service.py, sound_service.py, symbol_search.py, time_collapse_service.py, volume_baseline.py
- `spikes/lwc/` — spike_probe.py
- `tests/` — conftest.py, test_add_symbol_dialog_d22.py, test_alarm_d21.py, test_alarm_service.py, test_alarm_store.py, test_backfill_progress.py, test_backfill_service.py, test_bar_aggregator.py, test_chart_model.py, test_chart_mouse_router.py, test_chart_view_seam.py, test_contract_lookup_d22.py, test_d10_d13_integration.py, test_d21_flash_lifetime.py, test_d23_nonregression.py, test_d24_9_popout_persistence.py, test_d24_alarm_full_chain.py, test_d24_popouts.py, test_d24_smoke_gate.py, test_d25_alarm_monitor.py, test_d27_aggregator_priming.py, test_d27_backfill_granularity.py, test_d27_et_anchoring.py, test_d27_phantom_alarms.py, test_d27_reconnect.py … (+186 more)
- `ui/` — __init__.py, add_symbol_dialog.py, alarm_dialog.py, alarm_edit_dialog.py, chart_controls.py, chart_mouse_router.py, chart_view.py, dock_layout.py, drawing_groups_dialog.py, drawing_settings_common.py, drawing_tools.py, horizontal_line_settings_dialog.py, lwc_bridge.py, lwc_host.py, lwc_view.py, main_window.py, option_spreads_panel.py, popout_window.py, studies_dialog.py, ticker_session.py, toast.py, visual_conventions.py, watchlist_panel.py, zone_settings_dialog.py
- `ui/overlays/` — __init__.py

## Test impact (generated draft — Plan confirms or corrects)

- `chart_assets/lwc/chart.js` -> `chart_assets/lwc/chart.test.js`
- `chart_assets/lwc/envelope.js` -> `chart_assets/lwc/envelope.test.js`
- `chart_assets/lwc/gestures.js` -> `chart_assets/lwc/gestures.test.js`
- `data/alarm_store.py` -> `tests/test_alarm_store.py`
- `data/bar_aggregator.py` -> `tests/test_bar_aggregator.py`
- `data/db_backup.py` -> `tests/test_db_backup.py`
- `data/drawing_store.py` -> `tests/test_drawing_store.py`
- `ibkr/id_manager.py` -> `tests/test_id_manager.py`
- `services/alarm_service.py` -> `tests/test_alarm_service.py`
- `services/backfill_service.py` -> `tests/test_backfill_service.py`
- `services/chart_model.py` -> `tests/test_chart_model.py`
- `services/drawing_service.py` -> `tests/test_drawing_service.py`
- `services/gap_vix_service.py` -> `tests/test_gap_vix_service.py`
- `services/ict_service.py` -> `tests/test_ict_service.py`
- `services/indicator_service.py` -> `tests/test_indicator_service.py`
- `services/market_calendar.py` -> `tests/test_market_calendar.py`
- `services/session_service.py` -> `tests/test_session_service.py`
- `services/sound_service.py` -> `tests/test_sound_service.py`
- `ui/chart_mouse_router.py` -> `tests/test_chart_mouse_router.py`
- `ui/dock_layout.py` -> `tests/test_dock_layout.py`
- `ui/lwc_bridge.py` -> `tests/test_lwc_bridge.py`
- `ui/studies_dialog.py` -> `tests/test_studies_dialog.py`
- `ui/visual_conventions.py` -> `tests/test_visual_conventions.py`

## Graph summary (generated)

- graphify-out/graph.json: 9033 nodes, 19477 edges
<!-- MAP-SKELETON:END -->
