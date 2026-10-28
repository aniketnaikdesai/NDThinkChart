# Codebase Map — NDThinkChart

> **Owner:** Plan agent (written/refreshed as the first step of every batch — `docs/orchestrator_state.json`
> `contract_change_2026_10_16`). **Read by:** Plan Artifact Editor & Validator, Task Manager, Build Worker,
> Code Reviewer. **Purpose:** a module index so downstream agents stop walking the repo tree. This is an
> **index, not documentation** — if an entry needs more than ~5 lines it is doing too much; follow the symbol,
> not this file.
>
> **This is an existing repository** (`requirements.md` carries the marker). It is a PyQt6 + pyqtgraph +
> official `ibapi` desktop trading terminal (live TWS 7496, SQLite, PyInstaller `.app`).
>
> **Baseline:** post-P5 (D46 built — ibkr/orders + tests/test_order_builders +
> tests/test_stop_loss_target deleted from the tree; skeleton regenerated 2026-10-26).
> **Map written:** 2026-10-26, **P6 / Batch 22 (D47)** — the chart stack migrates to Lightweight Charts behind a
> `ChartView` seam (strangler; pyqtgraph retained and default until parity accepted). Skeleton re-run 2026-10-26
> (205 code files, 24 test-impact rows); annotations carried forward from P5 and extended for P6 below;
> `graphify-out/graph.json` (4,625 nodes) used for discovery only — **the source is authoritative** where they
> disagree.
>
> **D45 record (delivered, not re-opened in P5).** Batch 20 removed the News Digest dock (+ the `View` menubar),
> the Trade Context Menu, the **Kill switch** and the **SL/TP dialog**: five deleted production modules
> (`ui/news_digest_dock`, `ibkr/news`, `ui/trade_context_menu`, `ui/stop_loss_target_dialog`, `ibkr/validation`),
> **three** edited production modules (`ui/main_window.py`, `ui/ticker_session.py`,
> `ui/active_portfolio_panel.py`), **five deleted** test files, **seven adjusted** test files and **one added**
> (`tests/test_d45_removal` — the static/behavioural removal guard), two docs cleaned. *(This line read
> "adjusts six" until 2026-10-25; corrected with the addition of the added suite per `ESC-063`.)*
>
> **Status legend** (batch-relative): `[existing]` — present, **not** modified by P6 · `[new in P6]` —
> introduced by P6 · `[changed in P6]` — present and modified by P6. A row may still **describe** an earlier batch's delivered change; that history belongs in the row's
> prose, never in the status cell — no `[… in D4x]` value is a status here. P6 is a **renderer-migration increment** (D47): two new production modules land (the ChartView seam + the shared chart model), one new web-asset tree + bridge land, one throwaway spike directory lands (never imported), and two docs land (parity matrix + spike results); `ui/chart_panel` is the one chart file edited (delegation only, no behaviour change); pyqtgraph stays default through Phase 10 and **no pyqtgraph code is deleted before Phase 11** (P6-13, separately gated). P5's removal record below is history. Every other entry below is `[existing]`.
> (`ibkr/error_codes.py`); **two** suites deleted, **thirteen** test files adjusted, **0** added; two user-facing docs
> corrected (`USAGE.txt`, `usage.md`) and this map refreshed. Every other entry below is `[existing]`.
>
> **P6 note (2026-10-26):** the skeleton is regenerated from the post-P5 tree, so it no longer lists the P5-deleted
> files — the stale-skeleton note from P5 is retired. Planned-but-not-yet-existing P6 paths (the ChartView seam
> module, the shared chart-model module, the spike directory, the parity-matrix and spike-results docs) are named
> **without backticks** in the annotations until they land, per the map lint rule; live files keep their real path.
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
| `ui/dock_layout.py` (139 L) | **Pure, Qt-free** single source of truth for dock widths (D17/D18/B3 cross-clamp, D44 collapsed width). | `[existing]` | `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `DEFAULT_WATCHLIST_WIDTH=220`, `RIGHT_DOCK_MIN_WIDTH=200`, `WATCHLIST_COLLAPSED_WIDTH=30`, `plan_watchlist_width`, `watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths`. **`CHART_MIN_WIDTH` must equal `ui/watchlist_panel.CHART_MIN_WIDTH`** |
| `ui/visual_conventions.py` (203 L) | The shared VIS-D21 conventions: `DiagonalStrikeButton` (VIS-D21.1) + `set_button_active` / the active stylesheet (VIS-D21.2). | `[existing]` | `set_button_active(button, active)`, `ACTIVE_PROPERTY="active"`, `DiagonalStrikeButton.struck`, `VIS_D21_2_STYLESHEET` |
| `ui/chart_panel` (deleted by the P6 LWC build) | Was the pyqtgraph chart (panes, candles, volume, studies, overlays). | **deleted in P6** | Replaced by the ChartView seam (`ui/chart_view.py`) + LWC host (`ui/lwc_host.py`/`ui/lwc_view.py`); `services/chart_model.py` is the shared value source. Do not restore. |
| `ui/candlestick_item` (deleted by the P6 LWC build) | Was the candle `QPicture` renderer (+ the D42 `capped_body_half_width`). | **deleted in P6** | Rendering now lives in the LWC layer; the D42 density-cap wording is retired per D47/Q60 (`S56`). Do not restore. |
| `ui/ticker_session.py` (1,1xx L) | Per-symbol session: bars, waves, pacing, live bars, the S0 generic-tick substrate. | `[existing]` — **D45 changed this file; P5 does not** | `TickerSession.get_bars`, `::set_bars`, `::attach_view`, `::s0_register` / `::s0_register_many` / `::s0_deregister*`, `::on_s0_tick_string` (tick 59), `::dividend_info`, `::queue_wave_plans`; **D45 removes** the news `"292"` need registration, `::on_s0_tick_news`, `::add_news_push_listener` / `::remove_news_push_listener`, `::set_s0_headless`, the `_s0_headless` attribute **and the two `or self._s0_headless` clauses** in `::_s0_resync` / `::_s0_reissue`. **Retained verbatim:** the `"456"` dividend registration, tick 59, `_dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`/`events_unavailable` |
| `ui/active_portfolio_panel.py` (4xx L) | The right dock's Portfolio panel (D41/D21.13); **view-only after D45**. | `[existing]` — **D45 changed this file; P5 does not** | `ActivePortfolioPanel.summary_label` (the right dock's title-bar toggle), `::is_collapsed`/`::set_collapsed`/`::toggle_collapsed`, `::refresh`, `::set_positions`/`::add_position`, the account-summary/positions render path, `::_group_and_render`/`::_render_table` (now **8 columns**); **D45 removes** the `TradeContextMenu` + `StopLossTargetDialog` imports/members, `::_show_context_menu`, `::_on_close_position`, `::_on_close_group`, `::_on_ungroup`, `::_on_flatten_all`, `::_on_set_sltp`, `::_on_sltp_confirmed`, `::update_position_sltp`, `::update_group_sltp`, `::_sltp_dialog`, the menu-only selection tracking (`_selected_row`/`_selected_position`/`::_on_selection_changed`), the `CustomContextMenu` policy, the five signals (`position_close_requested` / `group_close_requested` / `flatten_all_requested` / `position_sltp_changed` / `group_sltp_changed`), and the `Stop`/`Target` columns. **Storage note (D45 history, superseded):** D45 kept the `stop_loss`/`take_profit` model fields and DB columns (A87) — **P5 DROPS the columns and the fields by a guarded migration** (A99/`D46.12`, `S47`); this panel is not edited, and its 8 columns are unchanged |
| `ui/popout_window.py`, `ui/chart_mouse_router.py` | Pop-out charts, mouse-mode router. | `[existing]` | P6 re-hosts these surfaces per phase — the Python `RouterMode` TR-1…TR-17 contract is frozen. The pyqtgraph overlay companions (`ui/drawing_overlay`, `ui/alarm_overlay`, `ui/event_marker_overlay`, `ui/zoom_overlay`) were **deleted by the P6 LWC build** (drawings/alarms/markers now render through the LWC primitives/library layers); do not restore. |
| ChartView seam module (ui/chart_view.py — lands P6-02), shared chart-model module (services/chart_model.py — lands P6-03), LWC host + bridge assets (land P6-04), spike directory spikes/lwc (lands P6-01, never imported), parity-matrix doc docs/lwc_parity_matrix.md + spike-results doc docs/lwc_spike_results.md (land P6-01) | Strangler seam + single value source + offline host + throwaway evidence + gate record. **Named without backticks until they land.** | **`[new in P6]`** | Factory `create_chart_view(tz_offset, editable)`; `DrawingController`/`AlarmController` exact signal signatures; model value objects; `LwBridge` batched ops; matrix row dispositions |
| `ui/*_dialog.py`, `ui/toast.py`, `ui/chart_controls.py`, `ui/add_symbol_dialog.py` | Retained dialogs, toast, toolbar controls. | `[existing]` | `AddSymbolDialog` (D22), alarm/drawing/study dialogs — **none is an order or SL/TP surface** |
| **deleted in D45** — `ui/news_digest_dock`, `ui/trade_context_menu`, `ui/stop_loss_target_dialog` | The digest dock, the Portfolio context menu, the local-only SL/TP dialog. | **deleted** | not importable after D45; no replacement widget, menu or dialog exists (`AC-D45.1`/`.3`/`.6`) |
| `ui/overlays/` (`__init__.py` only) | Was the pyqtgraph overlay package. | **gutted in P6** | `base.py`, `session_overlay.py`, `gap_overlay.py`, `ict_overlay.py`, `vix_overlay.py` were **deleted by the P6 LWC build** (overlays now render on LWC); only the package marker remains. Do not restore. |

## `services/` — pure services (Qt-free unless noted)

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `services/market_calendar.py` | ET trading calendar + RTH/ETH session windows + the ESC-023 New-Year exception. | `[existing]` | `is_trading_day`, `trading_days`, `session_windows(start_ts, end_ts, ext_hours)` |
| `services/backfill_service.py` | The missing-span planner (D16/D42 depth floor). | `[existing]` | `find_missing_spans`, `plan_requests`, `floor_bar_budget`, `bar_period_seconds`, `MissingSpan`, `RequestPlan` |
| `services/time_collapse_service.py` | D21.4 display-only x-remap for collapsed non-trading gaps. | `[existing]` | `TimeCollapseMap._to_display` |
| `services/alarm_monitor.py`, `alarm_service.py`, `sound_service.py` | Alarm monitoring/state/sound. | `[existing]` | `AlarmMonitor` |
| `services/contract_lookup_service.py`, `symbol_search.py` | Symbol/contract resolution (D22 add, D39 search). | `[existing]` | `ContractLookupService.lookup`, `SymbolSearchService` |
| `services/drawing_service.py`, `indicator_service.py`, `ict_service.py`, `strategy_detection.py`, `gap_vix_service.py`, `volume_baseline.py` | Drawings/studies/ICT/VWAP/D39 burst baseline. | `[existing]` | — |
| `services/session_service.py` | Equity RTH/ETH session shading bands. | `[existing]` | `session_bands` |
| `services/md_line_guard.py` | Market-data line budget guard. | `[existing]` | — |

## `data/` — persistence and models

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `data/db.py` (318 L) | SQLite schema + migrations (`bars`, `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline`). | **`[changed in P5]`** | `DB._init_schema`, `::_migrate_schema`, `::_table_columns`. **P5 wave 7** removes `stop_loss`/`take_profit` from both `CREATE TABLE` blocks and adds one guarded block to `_migrate_schema()` **after** the `idx_positions_symbol_con_id` statement: `_table_columns(table)` once, then `ALTER TABLE … DROP COLUMN` per column when present. Idempotent on a fresh DB (nothing to drop) and on every later open; each `DROP` is one atomic statement, so an interrupted open is completed by the next. Every row, the unique index, the FK and `sqlite_sequence` survive (measured 2026-10-25). No other table, index or migration touched. |
| `data/models.py` | `Bar` and the other row dataclasses (`Alarm`, `Study`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`). | **`[changed in P5]`** | `Bar`; **P5 wave 3 deletes the unused `UserOrder` dataclass** (zero consumers; its only reference was `tests/test_ui_smoke.py:48`), and **wave 7 deletes `Position.stop_loss`/`take_profit` and `TradeGroup.stop_loss`/`take_profit`** — the storage is dropped (`A99`, reversing A87). `dataclass`/`field` stay (used by `Study`); every other dataclass and field untouched. |
| `data/bar_cache.py` | Bar persistence + retention (`RETENTION_BARS`), D42 mode-aware key. | `[existing]` | `BarCache.save_bars` / `::get_bars` / `::prune` |
| `data/bar_aggregator.py` | Tick → bar aggregation. | `[existing]` | `BarAggregator` |
| `data/alarm_store.py`, `drawing_store.py`, `study_store.py`, `popout_store.py` | Per-feature stores. | `[existing]` | — |
| `data/events/` (**deleted** — directory absent from the tree) | Was the `EventProvider` ABC + the D38 event source. | **deleted** (removal landed before P7; recorded here so nothing re-plans it) | `data/events/provider` no longer exists; the D38 dividend/marker surface it fed is gone with the P6 render migration. Do not restore without a new requirement. |

## `ibkr/` — the broker boundary

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `ibkr/client.py` | `IBApiClient(EWrapper, EClient)`: the `ibapi` wrapper + reader thread + reconnect/teardown. | **`[changed in P5]`** | `IBApiClient.connect`, `::connected`, `::_on_disconnected`/`::_do_reconnect`; the fail-fast live-port check lives in `config/settings.py::check_live_port`. **P5 wave 2 deletes the `orderStatus` / `openOrder` / `execDetails` overrides** (the chain's only emitters) — the inherited `EWrapper` no-ops are what TWS then reaches. **Frozen and unchanged (`S46`):** `::error` — the `classify_error` severity gate, the D40.1 `502` backoff suppression and the `error_msg` emit — plus the lifecycle/account/position callbacks, and the news-boundary overrides (D45 `S35`). **Order transmit/cancel remain inherited from `EClient`** (`placeOrder`/`cancelOrder`/`reqGlobalCancel` are **not** defined here; D45's zero-call invariant stands, now enforced from the guard's forbidden set). **No `placeOrder` definition may be added.** |
| `ibkr/market_data.py` | Historical/RT market-data requests + `TIMEFRAME_CONFIG`. | `[existing]` | `MarketDataManager.req_historical_data`, `req_mkt_data(contract, generic_ticks=…)`, `TIMEFRAME_CONFIG` |
| `ibkr/account.py`, `ibkr/contracts.py` | Account/position rows and contract helpers. | **`[changed in P5]`** — `account.py`; `contracts.py` `[existing]`, untouched | `Position` row build, `get_contract_for_symbol`. **P5 wave 7** deletes `ibkr.account.Position.stop_loss`/`take_profit` and `build_position_from_ib`'s two parameters, and rewords the `Position.id` comment to justify `id` by strategy grouping only (`ESC-062`). Nothing else in either module changes. |
| **deleted in P5** — ibkr/orders (`UserOrder`, `Orders` + the four builders, the registry, the `orders` singleton) | The order builders and the in-memory open-order registry. | **deleted in P5** | not importable after P5 (`import ibkr.orders` raises `ModuleNotFoundError`); its only importer was `ui/main_window.py:36` and its registry was never written, so every read returned `None`. **The D45 decision to keep this module is OVERTURNED (A91/`S39`): it is deleted, nothing may restore it, and a future order path needs a new requirement rather than an un-comment.** |
| `ibkr/bridge.py`, `realtime_bars.py`, `pacing.py`, `id_manager.py`, `subscription_manager.py`, `stream_health.py`, `error_codes.py`, `utils.py` | Qt-signal bridge, RT bars, pacing, reqId allocation, the D27.3 subscription registry, stream health, error codes. | **`[changed in P5]`** — `bridge.py` (signals) and `error_codes.py` (**comment only**); `realtime_bars.py`, `pacing.py`, `id_manager.py`, `subscription_manager.py`, `stream_health.py`, `utils.py` are **`[existing]`, untouched** | `pacing_manager`, `MARKET_DATA`; **P5 wave 2 deletes the `order_status` / `open_order` / `exec_details` bridge signals** (with their client emitters); **wave 4 deletes `pacing.OrderRateLimiter` + `order_limiter`** (and `config/settings.py`'s `MAX_ORDER_NOTIONAL`); **wave 6 deletes `id_manager.reserve`** while `IdManager`, `get_id` and `set_next_valid_id` **stay** (six `get_id()` callers, incl. `ui/main_window.py`). The news signals (`tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article`) stay as the ibapi boundary mirror (D45 `S35`). **Frozen and unchanged:** `error_msg`; `::classify_error` in `ibkr/error_codes.py` (it gates **every** TWS error — only its 202 **comment** is reworded in wave 9, no code line); `PacingManager`/`PacingExceeded`; `IBApiClient.nextValidId`. |
| **deleted in D45** — `ibkr/news`, `ibkr/validation` | The news API client (`NewsManager`) and the order-validation gate (`validate_order`). | **deleted** | not importable after D45; `"292"` is never requested, and nothing builds an order for the gate to judge (`AC-D45.7`/`D26.7` moot) |

## `config/`, `packaging/`, root

| Path | Responsibility | Status | Key entry points |
|---|---|---|---|
| `config/settings.py` | Tunables (`SESSION_BAR_CAP`, `MAX_HISTORICAL_PER_600S`, `MIN_INTRADAY_SESSIONS`, …). | **`[changed in P5]`** | **P5 wave 4 deletes `MAX_ORDER_NOTIONAL`** and its `validate_order()` comment (zero readers; the gate died in D45). `check_live_port` and every other constant are frozen and untouched. |
| `config/paths.py` | `get_db_path()` (honours `DB_PATH`). | `[existing]` | `get_db_path` |
| `config/theme.qss` | The app-level stylesheet. | `[existing]` | — |
| `main.py`, `NDThinkChart.spec`, `packaging/`, `dist/`, `build/` | Entry point + PyInstaller bundle. | `[existing]` | — |
| `pytest.ini`, `requirements*.txt` | Test config + pinned deps (`PyQt6`, `pyqtgraph`, `numpy`, `ibapi-latest==10.51.1`). | `[existing]` | — |

## `tests/` — the offscreen suite (131 modules)

**Invocation:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale
shebang — use `-m pytest`). Any **non-pytest** probe that can reach a DB-writing path must export `DB_PATH` to a
temp file. No test connects to live TWS or transmits an order.

| Group | Suites | Status |
|---|---|---|
| **D45 removal book** — **deleted (5, whole files):** `tests/test_d28_6_close_contracts`, `tests/test_d41_retained_order_path`, `tests/test_order_validation`, `tests/test_kill_switch`, `tests/test_sltp_honesty`. **Adjusted (6 + 1 deleted):** `tests/test_dock_d18_region.py` (`:147` dock filter; the five-signal receiver loop **deleted** — no signal survives), `tests/test_order_rejections.py` (the disconnected-close case; the observer cases kept), `tests/test_d28_pacing.py` (the close-deferral case; historical pacing kept), `tests/test_d27_position_id.py` (the SL/TP row-addressing case removed **in wave 2**; `8`/`9` → `6`/`7` **in wave 3**), `tests/test_d27_flat_rows.py` (the AC3 `_selected_position` tail dropped with the selection tracker; the index-alignment assertions kept), `tests/test_d27_position_prices.py` (`8`/`9` → `6`/`7`). **Kept unchanged (verified):** tests/test_stop_loss_target (model fields only), `tests/test_d41_removal.py` (`queue_depth` is an allow-list string), tests/test_order_builders (the retained ibkr/orders unit coverage — *D45's decision; **P5 deletes both the module and this suite**, see the P5 row above*). **New:** `tests/test_d45_removal` (static token scan + mocked-client zero-transmit walkthrough) | `[existing]` — **the delivered D45 record; P5 supersedes its `ibkr/orders` half** (see the P5 row below) |
| **P5 removal book (D46, revision 2)** — **deleted (2, whole files):** `tests/test_order_builders` (17 cases; the builders/registry), `tests/test_stop_loss_target` (3 cases; the four model fields). **Adjusted (13):** `tests/test_order_rejections` (two registry cases + their helpers removed; the third repointed **and renamed** at the generic line; the two `classify_error` cases kept; **one parametrised 201/103/202 surfacing case added** — 3 of the original 5 survive), `tests/test_d45_removal` (wave 1: the walkthrough's `_on_order_error` call repointed at `_on_error`; wave 8: the **ten** names moved from `_SURVIVORS` to the forbidden set — `_FORBIDDEN` 53 → 80 with **`orders`/`Orders` exact-matched** — plus the two absence pools, the end-state test (chain, module, `UserOrder`, `reserve`, the utilities, the four fields, the schema + idempotence) and the guard's own prose), `tests/test_ui_smoke` (`UserOrder` `hasattr`), `tests/test_account` (4 kwargs + 2 asserts), `tests/test_strategy_detection` (`:30`–`:31`), `tests/test_d27_position_id` (seeder + **one new case** seeding a non-null `trade_group_id`), `tests/test_d27_account_partial_window` and `tests/test_d27_account_scoping` (seeders), `tests/conftest` (the two `order_limiter` resets), `tests/test_d28_pacing` (`OrderRateLimiter` case + import), `tests/test_sound_service` (`TestFillBlip` + `:57` + **`paths["fill"]` at `:76`**), `tests/test_id_manager` (4 deleted, **2 rewritten**), `tests/test_dock_d18_region` (`ESC-062` rename + two docstrings). **Kept unchanged (verified):** `tests/test_d40_tws_lifecycle`, `tests/test_port_guard`, `tests/test_d41_removal`, `tests/test_db_schema`, every other suite. **Added:** none (the guard is reused, not duplicated) | **`[changed in P5]`** |
| Dock layout / widths (D13/D17/D18/D19/D21.13/D44) | `test_dock_layout.py`, `test_dock_widths_d17.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_right_dock_d21.py`, `test_dock_d18_region.py`, `test_d10_d13_integration.py`, `test_watchlist.py`, `test_toolbar_scroll_d19.py`, `test_d41_portfolio_dock.py`, `test_d41_removal.py`, `test_dock_widths_collapsed_d44.py`, `test_watchlist_collapsed_bar_d44.py` | `[existing]` (untouched by P5) |
| Watchlist panel (D14/D21.5/D21.11/D22/D39) | `test_watchlist_columns_d21.py`, `test_watchlist_add_remove_d22.py`, `test_watchlist_nonregression_d22.py`, `test_watchlist_d14_midrag.py`, `test_watchlist.py` | `[existing]` |
| Chart / render (D1–D12, D28.4, D42 width — pyqtgraph suites deleted by the P6 LWC build) | `test_candle_spacing.py`, `test_volume_width.py`, `test_chart_dpi.py`, `test_d28_4a_render_layers.py`, `test_volume_*.py`, `test_drawing_*.py`, `test_time_collapse_d21.py`, `test_collapse_resync_fix.py` — **all deleted in P6**; LWC parity suites (`test_lwc_*.py`, `test_chart_model.py`, `test_chart_view_seam.py`) are the current render coverage | **deleted in P6** |
| Data / planner (D16, D27, D28, D39, D42) | `test_backfill_service.py`, `test_history_backfill*.py`, `test_d27_*`, `test_d28_*`, `test_d39_*`, `test_d42_*`, `test_db_schema.py`, `test_market_calendar.py` | `[existing]` (the D38 event/news suite `test_d38_events_news.py` was deleted with `data/events/`; dividend/marker coverage now lives in the LWC overlay suites) |
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
| `tests/test_d38_events_news` | NewsManager + digest sections removed; **event-marker/dividend cases kept**; module docstring + the md-line docstring's `"292"` reference corrected |
| `tests/test_dock_d18_region.py` | `:147` `objectName() != "NewsDigest"` filter dropped |
| deleted | `ui/news_digest_dock`, `ibkr/news` |

**Group B — Trade Context Menu + the whole order path + the SL/TP dialog (`AC-D45.3`/`.4`/`.5`/`.10`, A80/A87/A89/A90, R69/R70/R75).**

| Module | What D45 changes |
|---|---|
| `ui/main_window.py` | The 5 Portfolio `.connect` lines, `_on_portfolio_close_position` / `_on_portfolio_close_group` / `_on_portfolio_flatten_all`, `_on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed` (with their row-`UPDATE`s), `_close_position_by_id`, `_ref_price_for`, the `validate_order` import, and the now-unused `order_limiter`/`UserOrder` import names. *(D45 kept the inbound observers + `order_registry`, `_symbol_last_prices`, `PacingExceeded` and the account/position render path — **P5 removes the observers and the registry import**.)* |
| `ui/active_portfolio_panel.py` | The menu member/import and policy, `_show_context_menu`, the close/close-group/ungroup/flatten handlers, the SL/TP chain (`_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`), the five signals, the menu-only selection tracking, and the **Stop/Target columns (10 → 8)**. **Retained:** the account-summary/positions render path, the D21.13 header, `_unrealized_pnl`, and the SL/TP **model fields/DB columns** (A87 — **SUPERSEDED by P5: dropped, A99/`D46.12`**) |
| `tests/test_dock_d18_region.py` | The five-signal receiver loop deleted; the wiring comment restated |
| `tests/*` | `test_d28_6_close_contracts`, `test_d41_retained_order_path`, `test_order_validation`, `test_sltp_honesty` deleted; `test_order_rejections`, `test_d28_pacing`, `test_d27_position_id` (AC3 case, **wave 2**), `test_d27_flat_rows` (**wave 3**), `test_d27_position_prices` adjusted; `test_stop_loss_target`, `test_d41_removal`, `test_order_builders` kept unchanged *(D45's decision — **P5 deletes `test_order_builders`**, because its subject is deleted too)* |
| deleted | `ui/trade_context_menu`, `ui/stop_loss_target_dialog`, `ibkr/validation` |

**Group C — Kill switch / the cancel path (`AC-D45.6`, A88, R73/R74).**

| Module | What D45 changes |
|---|---|
| `ui/main_window.py` | `kill_btn` + its preceding `QLabel("|")` separator + tooltip/style/connect, `_on_kill_switch_clicked`, `_kill_switch` (the `reqGlobalCancel()` call, the per-ID `cancelOrder()` loop, the pre/post counts, the `Cancelled` marking). The toolbar keeps its remaining widgets and its trailing `addStretch()`. **No replacement control; no teardown/disconnect cancel** |
| `tests/*` | `test_kill_switch` deleted |
| docs | `USAGE.txt` (kill-switch bullet, the "orders cannot be placed while disconnected" claim), `usage.md` |

**Retained by decision after D45** (do **not** "clean up"): the bridge's news signals and the client's ibapi news
overrides (the ibapi boundary mirror, D45 `S35`), `MainWindow._symbol_last_prices` (feeds the Portfolio P/L), and
`tests/test_d41_removal` verbatim. **Overturned by P5:** the old "ibkr/orders retained + inert observers" row —
both are **deleted**; the three leftovers D45 named as out of scope — `config/settings.MAX_ORDER_NOTIONAL`,
`ibkr/pacing.order_limiter` and `ibkr/id_manager`'s `reserve` — are **tasks** in P5 (waves 4 and 6), with the module
and `get_id` retained; and **A87's `stop_loss`/`take_profit` storage is DROPPED** (A99, wave 7) — the D45 sentence
"columns and fields stay" is history, not the end state (see the P5 groups below).

---

## P5 touch summary (D46) — three member groups, one forced wave order

**Wave order (details in `docs/plan.md` § *Phase P5*):** `P5-T01` window consumers → `P5-T02` broker boundary →
`P5-T03` module + `data.models.UserOrder` → `P5-T04` pacing + notional cap → `P5-T05` order-fill sound →
`P5-T06` `IdManager.reserve` → `P5-T07` **stop/target storage (schema + every reader)** → `P5-T08` the instrument →
`P5-T09` surviving prose → `P5-T10` the batch gate.
`ui/main_window.py` is edited **twice** (waves 1 and 7); `data/models.py` twice (3 and 7);
`tests/test_d45_removal` twice (waves 1 and 8, different lines).
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
| `ibkr/orders` | **deleted** (whole file). No replacement, no dormant helper |
| `data/models.py` | the unused `UserOrder` dataclass **deleted** (wave 3); the four stop/target fields go in **wave 7** |
| `tests/test_order_builders` | **deleted** (17 cases, all for the deleted builders/registry) |
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
`data/models.py` (four fields), `ibkr/account.py` (two fields + two factory parameters), `ui/main_window.py` (the two
`_persist_position` kwargs, the `columns` tuple, the **name-keyed** bulk read with `trade_group_id` 14 → 12, the
upsert's columns/placeholders/`DO UPDATE`/values) — plus the whole test book (`test_stop_loss_target` **deleted**;
`test_account`, `test_strategy_detection`, the three seeders adjusted; **one new case** seeds a non-null
`trade_group_id`).

**Group 8 — the instrument (`D46.9`, wave 8).** `tests/test_d45_removal.py`: `_SURVIVORS` 26 → 16, `_FORBIDDEN`
53 → 80 (`orders`/`Orders` exact-matched, the other 25 new tokens substring; **`reserve` is not a token**), two
`_DELETED_*` entries, the end-state test (chain, module, `UserOrder`, `reserve`, the utilities, the four fields in all
three classes, the schema + a no-op second open), and the guard's own prose.

**Prose (wave 9, `AC-D46.6`/`D46.13`).** `ibkr/error_codes.py` — reword only `classify_error`'s 202 comment (no code,
no threshold); `usage.md` — drop `tests/test_order_builders` from the pytest example **and** rewrite the Database
bullet (the SL/TP columns are **dropped by a one-time migration**); `USAGE.txt` — rewrite the stop/target bullet the
same way, **keeping** its status-bar sentence verbatim; `tests/test_dock_d18_region.py` — the `ESC-062` rename and two
docstrings.

**Removed by P5 (nothing replaces them):** `ibkr/orders` (`UserOrder`, `Orders`, four builders, registry,
singleton) · the three `orderStatus`/`openOrder`/`execDetails` overrides · the three `order_status`/`open_order`/
`exec_details` bridge signals · `MainWindow._on_open_order` / `::_on_order_status` / `::_on_exec_details` /
`::_update_order_status` / `::_on_order_error` + the `_on_error` registry branch + the `order_registry` import ·
`data.models.UserOrder` · `pacing.OrderRateLimiter` + `order_limiter` · `settings.MAX_ORDER_NOTIONAL` ·
`sound_service`'s order-fill path · `IdManager.reserve` · **the `positions`/`trade_groups` `stop_loss`/`take_profit`
columns and the four model fields** · `tests/test_order_builders` · `tests/test_stop_loss_target`.

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
| `ibkr/account.py` | `test_account`, `test_d27_position_id`, `test_d27_account_scoping` |
| `data/db.py` (schema + migration) | `test_d27_position_id`, `test_d27_account_partial_window`, `test_d27_account_scoping`, `test_db_schema`, `test_d45_removal` |
| `ibkr/pacing.py`, `config/settings.py` | `test_d28_pacing`, `test_d45_removal` (conftest's pacing fixture runs everywhere) |
| `services/sound_service.py` | `test_sound_service`, `test_d24_alarm_full_chain` |
| `ibkr/id_manager.py` | `test_id_manager`, `test_d45_removal` |
| `ibkr/orders` (deleted), `tests/test_order_builders`, `tests/test_stop_loss_target` (deleted) | `test_d45_removal` (the guard asserts the absence) |

**P6 test-impact (Plan-confirmed):** the generated rows above stand. P6 adds: the chart-model module → the
chart/render suites (candles, volume, collapse, bands, crosshair, drawings, alarms, overlays) + a delegation probe;
the ChartView seam module → new factory/signal-signature suites; the LWC host/bridge → batch-shape, replay-identity,
offline/interceptor suites + `node --test` JS suites; webengine-gated suites report `@pytest.mark.webengine`
(skip-never-red) with named manual-checklist counterparts. `select_tests.py` should treat `ui/chart_panel`
delegation as affecting every chart/render suite (they must stay green unmodified per `AC-D47.2`).


<!-- MAP-SKELETON:BEGIN -->
## Module index (generated — do not hand-edit inside the skeleton markers)

- `(root)/` — main.py, probe_1min_short.py
- `chart_assets/lwc/` — alarms.js, all.js, chart.js, chart.test.js, envelope.js, envelope.test.js, gestures.js, gestures.test.js, interaction.js, lightweight-charts.standalone.production.js, overlays.js, primitives.js, studies.js, volume_scale.test.js
- `config/` — __init__.py, paths.py, settings.py
- `data/` — __init__.py, alarm_store.py, bar_aggregator.py, bar_cache.py, db.py, drawing_store.py, models.py, popout_store.py, study_store.py
- `ibkr/` — __init__.py, account.py, bridge.py, client.py, contracts.py, error_codes.py, id_manager.py, market_data.py, pacing.py, realtime_bars.py, stream_health.py, subscription_manager.py, utils.py
- `packaging/` — __init__.py
- `services/` — __init__.py, alarm_monitor.py, alarm_service.py, backfill_service.py, chart_model.py, contract_lookup_service.py, drawing_service.py, gap_vix_service.py, ict_service.py, indicator_service.py, market_calendar.py, md_line_guard.py, session_service.py, sound_service.py, strategy_detection.py, symbol_search.py, time_collapse_service.py, volume_baseline.py
- `spikes/lwc/` — spike_probe.py
- `tests/` — conftest.py, test_account.py, test_add_symbol_dialog_d22.py, test_alarm_d21.py, test_alarm_service.py, test_alarm_store.py, test_backfill_progress.py, test_backfill_service.py, test_bar_aggregator.py, test_chart_model.py, test_chart_mouse_router.py, test_chart_view_seam.py, test_contract_lookup_d22.py, test_d10_d13_integration.py, test_d21_flash_lifetime.py, test_d23_nonregression.py, test_d24_9_popout_persistence.py, test_d24_alarm_full_chain.py, test_d24_popouts.py, test_d24_smoke_gate.py, test_d25_alarm_monitor.py, test_d27_account_partial_window.py, test_d27_account_scoping.py, test_d27_account_subs.py, test_d27_aggregator_priming.py … (+88 more)
- `ui/` — __init__.py, active_portfolio_panel.py, add_symbol_dialog.py, alarm_dialog.py, alarm_edit_dialog.py, chart_controls.py, chart_mouse_router.py, chart_view.py, dock_layout.py, drawing_groups_dialog.py, drawing_settings_common.py, drawing_tools.py, horizontal_line_settings_dialog.py, lwc_bridge.py, lwc_host.py, lwc_view.py, main_window.py, popout_window.py, studies_dialog.py, ticker_session.py, toast.py, visual_conventions.py, watchlist_panel.py, zone_settings_dialog.py
- `ui/overlays/` — __init__.py

## Test impact (generated draft — Plan confirms or corrects)

- `chart_assets/lwc/chart.js` -> `chart_assets/lwc/chart.test.js`
- `chart_assets/lwc/envelope.js` -> `chart_assets/lwc/envelope.test.js`
- `chart_assets/lwc/gestures.js` -> `chart_assets/lwc/gestures.test.js`
- `data/alarm_store.py` -> `tests/test_alarm_store.py`
- `data/bar_aggregator.py` -> `tests/test_bar_aggregator.py`
- `data/drawing_store.py` -> `tests/test_drawing_store.py`
- `ibkr/account.py` -> `tests/test_account.py`
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
- `services/strategy_detection.py` -> `tests/test_strategy_detection.py`
- `ui/chart_mouse_router.py` -> `tests/test_chart_mouse_router.py`
- `ui/dock_layout.py` -> `tests/test_dock_layout.py`
- `ui/lwc_bridge.py` -> `tests/test_lwc_bridge.py`
- `ui/studies_dialog.py` -> `tests/test_studies_dialog.py`
- `ui/visual_conventions.py` -> `tests/test_visual_conventions.py`

## Graph summary (generated)

- graphify-out/graph.json: 4625 nodes, 10249 edges
<!-- MAP-SKELETON:END -->
