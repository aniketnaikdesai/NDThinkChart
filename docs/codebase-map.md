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
> **Baseline:** `main` @ `0c4d478` (D43 + the D42/Stage-C follow-ups complete; full offscreen suite green).
> **Map written:** 2026-10-16, Batch 19 (**D44** — the collapsed watchlist thin bar), source-validated against
> the tree at `0c4d478`; `graphify-out/graph.json` (4,859 nodes, built at `7b98bb9`) used for the initial map —
> the **source is authoritative** where they disagree.
>
> **Status legend** (batch-relative, since this is a non-suffixed legacy run):
> `[existing]` — present, **not** modified by this batch · `[new in D44]` — introduced by this batch ·
> `[changed in D44]` — present and modified by this batch. D44 is a **UI-layout increment**: it changes three
> production modules and adds two test suites; every other entry below is `[existing]`.

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
| `ui/main_window.py` (3,399 L) | The window: docks, toolbar, load path, sessions, close teardown. | **`[changed in D44]`** | `MainWindow._apply_dock_widths` (the **single** dock-width apply point, wired to `resizeEvent` **and** the drag hook), `::_plan_dock_widths`, `::_chart_area_width`, `::_read_persisted_width`, `::_sync_right_dock_collapse` (**the D21.13 min-width-pin precedent D44 follows**), `::_deferred_dock_clamp`, `::_dock_widths_consistent`, `::eventFilter`, `::_on_dock_drag_event`, `::_schedule_dock_clamp`, `::resizeEvent`, `::closeEvent`; dock wiring `::__init__` (`watchlist_dock.setTitleBarWidget(panel.header_bar)`, `LeftDockWidgetArea`, `panel.setMinimumWidth(WATCHLIST_MIN_WIDTH)`) |
| `ui/watchlist_panel.py` (1,003 L) | The watchlist: header strip + table, tick cells, D21.5 columns, D22 add/remove, D39 search, D21.11 collapse. | **`[changed in D44]`** | `WatchlistPanel.header_bar` (28px, `#141822`, is the dock's **title bar**), `::header_button` (`DiagonalStrikeButton("Watchlist")`), `::add_button` (D22.1 `+`), `::search_box` (D39.1), `::table` / `::body`, `::_on_header_toggled`, `::is_collapsed` / `::set_collapsed` / `::toggle_collapsed` (**the public collapse API — preserved**), `::add_symbol` / `::remove_symbol` / `::clear`; pure helpers `watchlist_max_width`, `clamp_watchlist_width`, `load_watchlist_width`, `save_watchlist_width`, `should_load_on_double_click`, `normalise_symbol`, `symbol_in_list`, `ensure_symbol_present`, `sanitise_watchlist_columns`; constants aliased from `dock_layout` |
| `ui/dock_layout.py` (139 L) | **Pure, Qt-free** single source of truth for dock widths (D17/D18/B3 cross-clamp). | **`[changed in D44]`** | `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `DEFAULT_WATCHLIST_WIDTH=220`, `RIGHT_DOCK_MIN_WIDTH=200`, the cap fractions, `watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths`. **`CHART_MIN_WIDTH` must equal `ui/watchlist_panel.CHART_MIN_WIDTH`** (documented `:13`–`:14`) |
| `ui/visual_conventions.py` (203 L) | The shared VIS-D21 conventions: `DiagonalStrikeButton` (VIS-D21.1) + `set_button_active` / the active stylesheet (VIS-D21.2). | `[existing]` | `set_button_active(button, active)`, `ACTIVE_PROPERTY="active"`, `DiagonalStrikeButton.struck`, `VIS_D21_2_STYLESHEET`, `apply_toolbar_stylesheet` |
| `ui/chart_panel.py` (1,683 L) | The chart: pyqtgraph panes, candles, volume, studies, overlays. | `[existing]` | `ChartPanel.update_chart`, `::update_last_bar`, `::set_symbol`, `::set_timeframe`, `::_refresh_candles` |
| `ui/candlestick_item.py` (251 L) | The candle `QPicture` renderer (+ the D42 `capped_body_half_width`). | `[existing]` | `CandlestickItem.set_data`, `::_draw_candles`, `capped_body_half_width` |
| `ui/ticker_session.py` (1,106 L) | Per-symbol session: bars, waves, pacing, live bars. | `[existing]` | `TickerSession.get_bars`, `::set_bars`, `::_append_bar`, `::queue_wave_plans` |
| `ui/active_portfolio_panel.py` (423 L) | The right dock's Portfolio panel (D41/D21.13). | `[existing]` | `PortfolioPanel.summary_label` (the right dock's title-bar toggle), `::is_collapsed` |
| `ui/popout_window.py`, `ui/chart_mouse_router.py`, `ui/drawing_overlay.py`, `ui/alarm_overlay.py`, `ui/event_marker_overlay.py`, `ui/zoom_overlay.py` | Pop-out charts, mouse-mode router, drawings, alarms, event markers, zoom label. | `[existing]` | — (untouched by D44) |
| `ui/*_dialog.py`, `ui/toast.py`, `ui/news_digest_dock.py`, `ui/chart_controls.py`, `ui/trade_context_menu.py`, `ui/add_symbol_dialog.py` | Dialogs, toast, D38 news dock, toolbar controls. | `[existing]` | `AddSymbolDialog` (D22) |
| `ui/overlays/` (`base.py`, `session_overlay.py`, `gap_overlay.py`, `ict_overlay.py`, `vix_overlay.py`) | pyqtgraph overlays for the chart. | `[existing]` | `Overlay` base |

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
| `data/db.py` (318 L) | SQLite schema + additive migrations (`bars`, `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline`). | `[existing]` | `DB._init_schema`, `::_migrate_schema` |
| `data/models.py` | `Bar` and the other row dataclasses. | `[existing]` | `Bar` |
| `data/bar_cache.py` | Bar persistence + retention (`RETENTION_BARS`), D42 mode-aware key. | `[existing]` | `BarCache.save_bars` / `::get_bars` / `::prune` |
| `data/bar_aggregator.py` | Tick → bar aggregation. | `[existing]` | `BarAggregator` |
| `data/alarm_store.py`, `drawing_store.py`, `study_store.py`, `popout_store.py` | Per-feature stores. | `[existing]` | — |
| `data/events/` (`provider.py`, yfinance source) | The `EventProvider` ABC + the D38 event source. | `[existing]` | `EventProvider` |

## `ibkr/` — the broker boundary

| Module | Responsibility | Status | Key entry points |
|---|---|---|---|
| `ibkr/client.py` | `IBApiClient`: the `ibapi` wrapper + reader thread + fail-fast live-port check. | `[existing]` | `IBApiClient.connect`, `::connected`, `check_live_port` |
| `ibkr/market_data.py` | Historical/RT market-data requests + `TIMEFRAME_CONFIG`. | `[existing]` | `MarketDataManager.req_historical_data`, `TIMEFRAME_CONFIG` |
| `ibkr/orders.py`, `account.py`, `contracts.py`, `validation.py` | Order builders (retained machinery), account/position rows, contract helpers, order validation. | `[existing]` | — |
| `ibkr/bridge.py`, `realtime_bars.py`, `news.py`, `pacing.py`, `id_manager.py`, `subscription_manager.py`, `stream_health.py`, `error_codes.py`, `utils.py` | Qt-signal bridge, RT bars, D38 news, pacing, reqId allocation, the D27.3 subscription registry, stream health, error codes. | `[existing]` | `pacing_manager`, `MARKET_DATA` |

## `config/`, `packaging/`, root

| Path | Responsibility | Status | Key entry points |
|---|---|---|---|
| `config/settings.py` | Tunables (`SESSION_BAR_CAP`, `MAX_HISTORICAL_PER_600S`, `MIN_INTRADAY_SESSIONS`, …). | `[existing]` | — |
| `config/paths.py` | `get_db_path()` (honours `DB_PATH`). | `[existing]` | `get_db_path` |
| `config/theme.qss` | The app-level stylesheet. | `[existing]` | — |
| `main.py`, `NDThinkChart.spec`, `packaging/`, `dist/`, `build/` | Entry point + PyInstaller bundle. | `[existing]` | — |
| `pytest.ini`, `requirements*.txt` | Test config + pinned deps (`PyQt6`, `pyqtgraph`, `numpy`, `ibapi-latest==10.51.1`). | `[existing]` | — |

## `tests/` — the offscreen suite (128 files)

**Invocation:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale
shebang — use `-m pytest`). Any **non-pytest** probe that can reach a DB-writing path must export `DB_PATH` to a
temp file. No test connects to live TWS or transmits an order.

| Group | Suites | Status |
|---|---|---|
| **Dock layout / widths (the D44 blast radius)** | `test_dock_layout.py` (pure model, 21 tests), `test_dock_widths_d17.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_right_dock_d21.py`, `test_dock_d18_region.py`, `test_d10_d13_integration.py`, `test_watchlist.py`, `test_toolbar_scroll_d19.py`, `test_d41_portfolio_dock.py`, `test_d41_removal.py` | **`[changed in D44]`** — `test_dock_layout.py` + `test_watchlist.py` extended; the rest verified unchanged (expanded state) |
| **Watchlist panel (D14/D21.5/D21.11/D22/D39)** | `test_watchlist_columns_d21.py`, `test_watchlist_add_remove_d22.py`, `test_watchlist_nonregression_d22.py`, `test_watchlist_d14_midrag.py`, `test_watchlist.py` | **`[changed in D44]`** — the three collapse-appearance sites corrected |
| **New this batch** | `test_dock_widths_collapsed_d44.py`, `test_watchlist_collapsed_bar_d44.py` | **`[new in D44]`** |
| Chart / render (D1–D12, D28.4, D42 width) | `test_candle_spacing.py`, `test_volume_width.py`, `test_chart_dpi.py`, `test_d28_4a_render_layers.py`, `test_volume_*.py`, `test_drawing_*.py`, `test_time_collapse_d21.py`, `test_collapse_resync_fix.py` | `[existing]` |
| Data / planner (D16, D27, D28, D38, D39, D42) | `test_backfill_service.py`, `test_history_backfill*.py`, `test_d27_*`, `test_d28_*`, `test_d38_*`, `test_d39_*`, `test_d42_*`, `test_db_schema.py`, `test_market_calendar.py` | `[existing]` |
| Alarm / account / orders / lifecycle (D25, D26, D40, D41) | `test_d25_*`, `test_d26_*`, `test_d27_account_scoping.py`, `test_d40_tws_lifecycle.py`, `test_d41_*`, `test_order_builders.py`, `test_account.py` | `[existing]` |
| Smoke / lifecycle harnesses | `test_d24_popouts.py`, `test_phase3_fixpass.py`, `test_d24_alarm_full_chain.py`, `test_d24_smoke_gate.py`, `test_d24_9_popout_persistence.py`, `test_d28_tick_burst_baseline.py` | `[existing]` (these **drive** `MainWindow.load_chart` — the `ESC-050` class; D44 does not touch the load path) |

## `docs/` — pipeline artifacts (ownership)

| Path | Owner | Note |
|---|---|---|
| `docs/requirements/requirements.md`, `design_gaps.md`, `open_questions.md`, `feature_suggestions.md` | Requirements Analyst | Requirements of record (`Status: READY_FOR_PLAN`); D44 `:3782`–`:3925`, Journey 37 `:976`–`:989`, A75–A78 `:4005`–`:4008`, R66–R67 `:4129`–`:4130`, DG74, Q54 |
| `docs/architecture_proposal.md`, `docs/plan_proposal.md`, `docs/codebase-map.md` | **Plan** | This map + the D44 proposal pair |
| `docs/architecture.md`, `docs/plan.md`, `docs/plan_notes.md`, `docs/plan_review.md` | Validator | Cumulative canonical artifacts; the D44 increment merges as a `## D44 increment` section |
| `docs/tasks/`, `docs/build/`, `docs/code_review/` | Task Manager / `build_wave.py` / Code Reviewer | — |
| `docs/memory.md` | User (Orchestrator may append) | Locked decisions incl. the 2026-10-16 pyqtgraph lock |
| `docs/phase-changelog.md`, `docs/ibkr-api-data-inventory.md`, `docs/thinkorswim-feature-gap-analysis.md` | historical reference | Surviving record of Phases 1–10 |
| `graphify-out/` | graphify tooling | `graph.json` (4,859 nodes) + `GRAPH_REPORT.md`; **discovery, not truth** |

---

## D44 touch summary (the three production modules)

| Module | What D44 changes |
|---|---|
| `ui/dock_layout.py` | `+ WATCHLIST_COLLAPSED_WIDTH = 30`; a pure collapsed-width rule; `plan_dock_widths` gains a collapsed mode (the 150px minimum becomes **expanded-state only**) |
| `ui/main_window.py` | The collapsed-aware apply path (both branches), the min-width pin + deferred re-apply, the tracked previous width, the title-bar swap wiring |
| `ui/watchlist_panel.py` | The `CollapsedWatchlistBar` (rotated label, app palette), the collapsed title-bar handle, the hide/show of the header strip + table, the `collapsed_changed` signal |
