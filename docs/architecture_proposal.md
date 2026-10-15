# Architecture Proposal — NDThinkChart Batch 18 (**D41**: remove D36 footprint + D37 depth/imbalance/auction + the **entire Active Trader panel**, and make the right dock Portfolio-only)

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical
> architecture — `docs/architecture.md` is written by Plan Artifact Editor & Validator after
> validation. Companion: `docs/plan_proposal.md` (phases, per-file `touches_files` map,
> sequencing, test surface, assumptions, flagged issues).
>
> Requirements of record: `docs/requirements/requirements.md` (**`Status: READY_FOR_PLAN`**),
> `### D41` (`:3263`–`:3426`, `AC-D41.1`–`AC-D41.7`), Journey 36 (`:855`–`:882`), assumptions
> `A68`–`A71` (`:3499`–`:3502`), gaps `DG66`–`DG71` (`design_gaps.md:1012`–`:1153`).
>
> Relationship to prior decisions: every decision below carries `[existing]` / `[new]` /
> `[new/changed]`, and where it **changes or supersedes** an earlier decision the superseded
> item is named in the row (D18/**B2**, `AC-D18.3`, D21.13, D26's order-entry surface, D36, D37).
> Unlabelled = `[new]`.
>
> **Revision 2 (2026-10-15) — round-1 `CHANGES_REQUIRED` response.** The Validator **verified all
> three architecture decisions (`S4` `ref_price` source, `S6` Portfolio-only dock, `S7`
> `footprint_cache` drop) and the order-path finding (verified fact 1 / `FI-1`) against source**;
> **none of them is changed by this revision.** What changed: the dock-title consumer count and its
> full enumeration (verified fact 4), the `S19`→`S5` cross-reference, the FI/severity attributions
> (`OrderBookLevel` = **FI-2**; the wide-candle defect = **FI-3**; ESC-041 = **blocking**), a
> softened `S4` rationale sentence, the two KEEP-coverage re-homes for `footprint_cache_key` and
> `md_line_guard.assess` (plan proposal **R2**), and the phase-1 file list in the sequencing
> summary. The per-file/test maps and the R1–R6 record live in `docs/plan_proposal.md`.

---

## Codebase Summary (existing repository — the D41 removal surface)

Factual inventory, source-validated 2026-10-15 (graphify discovery, then verified against the
working tree). The repo is **not** greenfield: it is a PyQt6 + pyqtgraph desktop charting/order
terminal with ~4,900 graph nodes and a 1,028-test offscreen suite at `29067af`.

### Data models / schema

- **`data/db.py::DB`** — SQLite, one connection, `_init_schema()` (DDL script) + `_migrate_schema()`
  (additive `ALTER TABLE`, `CREATE UNIQUE INDEX`, idempotent). Tables: `bars`, `watchlist`,
  `alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `popouts`, `positions`,
  `trade_groups`, `position_group_map`, **`footprint_cache`** (`:121`–`:127`, D36: one compressed
  JSON blob per `(resolved_contract, date, timeframe)`), `yfinance_events_cache` (D38, `:132`),
  `volume_baseline` (D39, `:144`). `config/paths.py::get_db_path()` returns the **user-space
  production DB** when `DB_PATH` is unset (`tests/conftest.py` sets it to a temp file).
- **`data/models.py`** — dataclasses `Bar`, `Position`, `TradeGroup`, `UserOrder`,
  **`OrderBookLevel`** (`:105`–`:110`; verified referenced by **nothing** in the tree), drawing/study models.
- **`data/footprint_cache.py`** — `FootprintCache` + `is_cacheable` (D36 persistence).
- **In-memory models that matter to D41:** `MainWindow._symbol_last_prices: dict[str, float]`
  (D27.5 central `symbol → last_price` map, `main_window.py:727`), `TickerSession._s0_needs`
  (refcounted generic-tick need registry), `SubscriptionManager` entries keyed by `req_type`.
- **DB access:** `data/footprint_cache.py` takes `_app_db.conn`; `positions` rows are the
  Portfolio panel's source (`_on_position_end` selects the whole table).

### Major components and responsibilities

| Component | Responsibility (as-built) |
|---|---|
| `ui/main_window.py` (~3,700 lines) | toolbar, watchlist + **single right dock region**, session lifecycle, historical/backfill orchestration, RT/DOM/depth wiring, `_md_line_count`/`_guard_md_lines`/`_guard_depth_budget`, order placement + portfolio close/flatten, dock-width clamp |
| `ui/chart_panel.py` (~1,800 lines) | candle + volume plots, crosshair, drawing overlay, **D36 footprint render layers + floating control cluster**, **D37 depth/IMB/AUC controls + 500 ms depth repaint timer**, D38 event markers |
| `ui/ticker_session.py` (~1,800 lines) | per-symbol session: RT bar subscription, BarAggregator, alarms, **S0 generic-tick substrate (D37 substrate, reused by D38)**, **D36 footprint service/wave/cache**, **D37 depth refcount + auction**, historical backfill waves |
| `ui/active_trader_panel.py` (658 lines) | `LadderTable`, `BookTable`, **`OrderEntryWidget`** (Buy/Sell MKT/LMT/STP/Bracket + confirm + status), `ActiveTraderPanel` shell + `header_bar`/`header_button` |
| `ui/active_portfolio_panel.py` | `ActivePortfolioPanel`: `summary_label` (`DiagonalStrikeButton("Account Summary")`, its hide/show toggle), `body`, `is_collapsed()`, positions table + Close/Close Group/Flatten All + SL/TP dialogs |
| `ui/dock_layout.py` | **pure, Qt-free** single source of truth for dock widths: `CHART_MIN_WIDTH=400`, `WATCHLIST_MIN_WIDTH=150`, `RIGHT_DOCK_MIN_WIDTH=200`, `WATCHLIST_CAP_FRACTION=0.50`, `RIGHT_DOCK_CAP_FRACTION=0.40`, `watchlist_max_width`, `right_dock_max_width`, `plan_dock_widths` (B3 cross-clamp) |
| `ibkr/market_depth.py` | `MarketDepthManager`: DOM `subscribe/cancel/cancel_all/on_update/snapshot` **and** the D37 refcounted `subscribe_shared/release_shared/resubscribe_shared` |
| `ibkr/order_book.py` | `Level`, `OrderBook`, `apply_operation`, `SIDE_ASK/SIDE_BID` |
| `ibkr/tick_history.py` | `TickHistoryManager.req_historical_ticks` (D36); never uses `reqTickByTickData` |
| `ibkr/bridge.py` / `ibkr/client.py` | Qt signals ↔ `ibapi.EClient` overrides (`historicalTicksBidAsk/Last`, `updateMktDepth`, `updateMktDepthL2`, `tickGeneric/tickString/tickNews`) |
| `ibkr/subscription_manager.py` | replay/rebind registry; tags `RT_BARS`, `MARKET_DATA`, **`DEPTH`**, **`DEPTH_HEATMAP`**, `S0_TICKS` |
| `services/` | `footprint_service.py`, `depth_heatmap.py` (features being removed); `md_line_guard.py::assess`, `volume_baseline.py`, `market_calendar.py`, `backfill_service.py`, `alarm_monitor.py` (kept) |
| `ibkr/orders.py`, `ibkr/validation.py`, `ibkr/id_manager.py`, `ibkr/pacing.py`, `config/settings.py::check_live_port` | **retained** order machinery (builders incl. `bracket_order`, `validate_order()`, id reservation, token buckets, fail-fast live-port check) |

### Key entry points

`main.py` (imports pyqtgraph **before** `QApplication`, installs a non-abort `sys.excepthook`) →
`MainWindow.__init__` → `load_chart(symbol, timeframe, extended_hours)`; toolbar controls
(`dom_btn` → `_on_dom_toggled` → `_subscribe_dom`; `load_btn` → `load_chart`); the right dock
(`self.right_dock`, `QDockWidget("Active Trader", self)` + `setObjectName("Active Trader")`,
`setTitleBarWidget(self.active_trader.header_bar)`); order entry via
`active_trader.order_place_requested` → `MainWindow._on_order_place_requested` → `_place_order`;
portfolio closes via `portfolio_panel.group_close_requested`/`flatten_all_requested` →
`_on_portfolio_close_group`/`_on_portfolio_flatten_all` → `_close_position_by_id`.

### External integrations already in use

IBKR TWS via official `ibapi` (pinned `9.81.1.post1`), **live port 7496 only** (fail-fast):
`reqRealTimeBars`, `reqMktData` (incl. S0 generic ticks `"292"` news / `"456"` dividends / **`"225"` auction**),
`reqHistoricalData`, **`reqMktDepth`/`cancelMktDepth`**, **`reqHistoricalTicks`**,
`reqPositions`/`reqAccountSummary`, `reqMatchingSymbols` (D39), `reqNewsProviders`/article fetch (D38),
`placeOrder`/`cancelOrder`/`reqGlobalCancel`, `reqContractDetails`. Secondary approved source:
yfinance (D38 corporate events, cached). Persistence: SQLite via `config/paths.get_db_path()`.
Packaging: PyInstaller `.app` (not exercised here). Tests: pytest + pytest-qt, offscreen only.

### Verified facts that shape D41 (source-validated 2026-10-15)

1. **The retained order paths never call `validate_order()`.** `validate_order(...)` has exactly
   **one** production call site — `ui/main_window.py:3112`, inside `_place_order` — and
   `_place_order`'s only caller is `_on_order_place_requested` (`:3092`), which exists only for
   the **`OrderEntryWidget` ticket** (`active_trader.order_place_requested`, `:693`).
   `_close_position_by_id` (`:3446`) builds the order itself and calls `placeOrder` directly, with
   **no** validation and **no** connection guard; the D26.9 "never transmit while disconnected"
   guard also lives only in `_place_order` (`:3105`). `ui/stop_loss_target_dialog.py` places **no**
   orders at all (`tests/test_sltp_honesty.py` asserts non-transmission). ⇒ After D41 the
   in-app ticket is gone, so both the validate gate and the disconnected guard would go with it
   unless they are **re-homed onto the surviving emitter** (decision `S5`).
2. **`ref_price`'s only consumer is the ticket path.** `ref_price=self.active_trader.last_price`
   (`:3116`); `last_price` was populated from the DOM depth feed (`_on_mkt_depth` →
   `active_trader.set_last_price`, `:3033`). Both ends are being removed.
3. **A retained, symbol-keyed price source already exists and is fed twice.** `_symbol_last_prices`
   (D27.5) is written by `_record_symbol_price` from (a) the watchlist price sink
   (`watchlist_panel.set_price_sink`, `:609`) and (b) **every aggregated chart bar**
   (`ticker_session.py:863 → _host._record_symbol_price(self.symbol, bar.close)`), and is already
   the D27.5-mandated source for position market prices (`:3313`).
4. **The right dock is one `QDockWidget` titled *and* `objectName`d `"Active Trader"`** containing
   a `RightDockContainer` with `ActiveTraderPanel` stacked over `ActivePortfolioPanel`; its
   **title bar is the Active Trader header**, and the "both panels collapsed" state
   (`_sync_right_dock_collapse`, `:2494`) is the D21.13 region-collapse. **Title/`objectName`-keyed
   lookups exist in 15 test files** — `test_dock_widths_d17.py:37`/`:73`,
   `test_watchlist_d14_midrag.py:35`/`:82`, `test_crosshair_axis_lane.py:101`–`:106`/`:123`,
   `test_d27_position_prices.py:30`, `test_history_backfill.py:199`,
   `test_history_backfill_disconnect.py:136`, `test_dock_widths_d18.py:177`,
   `test_d10_d13_integration.py:35`/`:53`, `test_d27_account_subs.py:27`,
   `test_watchlist_columns_d21.py:308`/`:322`, `test_d27_phantom_alarms.py:56`,
   `test_d27_stream_health.py:67`, `test_history_backfill_loadpath.py:165`,
   `test_dock_d18_region.py:107`/`:110`, `test_d27_reconnect.py:163` — **plus 2 files asserting the
   dock's title-bar *text*** (`test_right_dock_d21.py:64`, `test_watchlist_nonregression_d22.py:142`)
   — **17 files total**, every one of them enumerated in the plan's Phase-2 map with the edit it
   needs. This is the repo's known "stable title/`objectName`" trap (the D19 masking trap), and the
   under-count of it was one of the round-1 blockers: a title-keyed consumer left out of the map
   silently stops hiding/renaming anything, so its suite passes while exercising a window the app no
   longer has.
5. **Dock-width guards are pure and reusable unchanged:** `ui/dock_layout.py` imports no Qt symbol;
   `plan_dock_widths` owns the per-dock caps, the combined chart-minimum cross-clamp, and the
   never-below-dock-minimum guarantee (ESC-026 corrected). D41 changes **how many sections** the
   right dock hosts, not the geometry rules.
6. **`_md_line_count` (`:790`) sums RT + S0 + `depth_manager.active_feed_count()` + watchlist rows**;
   `_guard_depth_budget`/`DEPTH_FEED_CAP = 60` gate depth feeds only. `md_line_guard.assess` +
   `_guard_md_lines` are shared with **D38's S0 lines** (`ticker_session.py:485`).
7. **The S0 substrate is shared:** `s0_register_many`/`_s0_needs`/`S0_TICKS`/`tick_generic`/
   `tick_string`/`tick_news` serve D38's `"292"`/`"456"`; only `attach_view`'s `{"auction": {"225"}}`
   registration and the auction ingress (`on_tick_price`/`on_tick_size`, `_auction`,
   `auction_state`) are D37.
8. **`ibkr/contracts.py::footprint_cache_key` + `INDEX_PROXY` are D39 load-bearing**
   (`ticker_session.py:35`, `:922`; `services/alarm_monitor.py`, `ui/alarm_dialog.py`) — only
   `resolve_footprint_contract` is D36-exclusive.
9. **Toolbar geometry fixtures pin the control set** (`dom_btn` in `_CONTROL_NAMES` of
   `test_toolbar_scroll_d19.py:42` / `test_toolbar_d20.py:44`, and in `_CHECKABLE_TOGGLES` of
   `test_toolbar_d21.py:152`), and the toolbar's intrinsic width is font-dependent
   (1965 px @9 pt vs 1921 px with Inter 11 px) — the D19/D20 hidden-toolbar **masking** trap applies.
10. **`tests/test_db_schema.py` subset-asserts** `EXPECTED_TABLES` (never listed `footprint_cache`),
    so removing the DDL alone is silent — an explicit absence/drop assertion is needed.

---

## Summary

D41 is a **removal**, not a feature. Three coupled changes: (1) delete the D36 footprint and D37
depth/imbalance/auction feature trees (modules, bridge/client surface, subscription tags,
chart controls, session state, DB table); (2) delete the **entire** Active Trader panel — DOM
ladder *and* the in-app order-entry ticket — together with the market-depth machinery and the
`DOM` toolbar button, and re-shape the single right dock into a **Portfolio-only** section
reusing D21.13's header/collapse mechanism and the unchanged pure `ui/dock_layout.py` clamp;
(3) **re-home** the D26 safety gates that the deleted ticket was their only caller of
(the disconnected guard and the `validate_order()` gate, now fed by a retained `ref_price`
source) onto the one surviving order emitter, Portfolio's close/flatten path. Everything else —
D1–D35, D38 news/events, D39 bursts/search, D27/D28 correctness/pacing, the chart, the kill
switch, the fail-fast port check — is untouched and is the non-regression contract.

---

## Tech Stack Decisions

Constrained (existing) choices first, then the D41 additions/changes.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Existing-repo hard constraint; changing the stack is an explicit non-goal | Any new UI/charting framework — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` (`9.81.1.post1`), **live TWS 7496 only** (`check_live_port` fail-fast), numpy, SQLite via `config/paths.get_db_path()`, PyInstaller `.app`, pytest + pytest-qt offscreen (no live TWS, no order transmission) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB / new test framework — rejected |
| S3 | **Removal mechanism** `[new]` | **Whole-file deletion** for the 9 feature-exclusive production modules (`ui/footprint_item.py`, `ui/depth_heatmap_item.py`, `ui/active_trader_panel.py`, `services/footprint_service.py`, `services/depth_heatmap.py`, `data/footprint_cache.py`, `ibkr/tick_history.py`, `ibkr/market_depth.py`, `ibkr/order_book.py`) and the 5 feature/widget-scoped test suites (S11); **surgical in-file deletion** for the shared files (bridge/client/subscription/contracts/db/chart_panel/ticker_session/main_window/watchlist_panel/models). **No shim modules, no deprecation stubs, no commented-out code, no `# removed` placeholders** | `AC-D41.3` requires those paths to **no longer exist** and nothing to import or reference them; feature-exclusive modules have a zero-consumer blast radius once the call sites go. Stubs/comments would violate the "no dangling reference" clause and re-invite accidental re-wiring | (i) keep modules, drop call sites — fails `AC-D41.3`; (ii) keep modules with deprecation warnings — same, plus dead code; (iii) leave commented-out blocks as a record — reviewable-history belongs to git/docs (DOC-4), not source |
| S4 | **`ref_price` retained source** `[new]` — closes **DG71(1)** | `ref_price` comes from the **D27.5 central `symbol → last_price` map** (`MainWindow._symbol_last_prices`, `:727`), read through one small accessor `MainWindow._ref_price_for(symbol) -> float | None` (normalises to upper-case; returns `None` when a symbol has no recorded price). No other source is consulted. Rationale: the map is **already the D27.5-mandated price source for position market prices** and is fed by **both** the watchlist tick sink and **every aggregated chart bar** (`ticker_session.py:863`), so it resolves for any symbol that is on the **watchlist** or has a **live chart session** — the map is symbol-keyed, not reqId-keyed or session-scoped, which is what the retained close path needs. `None` on an unknown symbol (one that is in neither) is safe: `validate_order` already skips the notional check when no positive price basis exists, so an unknown price can never fabricate a rejection | (i) session `last_chart_price` — single-symbol, primary-chart-only, and semantically "the chart's price", not the position's own symbol (this is precisely why D27.5 introduced the map) — rejected; (ii) `WatchlistPanel._last_price` — keyed by `reqId` inside panel internals, not symbol-keyed — rejected; (iii) re-derive from the removed DOM feed — impossible; (iv) `positions.market_price` from the DB — a stale persisted value, not a live reference — rejected |
| S5 | **Retained order path carries the surviving D26 gates** `[new/changed]` — **revises the D26/`_place_order`-scoped arrangement** (its ticket surface is removed by D41) | `MainWindow._close_position_by_id` (the **only** production order emitter after D41) becomes, in order: (1) the **D26.9 disconnected guard** (refuse + status-bar message, never transmit), (2) `validate_order(action=…, order_type="MKT", qty=close_qty, symbol=symbol, ref_price=self._ref_price_for(symbol), risk_reducing=True)`, (3) the existing `order_limiter` pacing/deferral, (4) `placeOrder`. `ibkr/validation.py::validate_order` gains one **additive** keyword `risk_reducing: bool = False`; when `True` the **notional-cap check is skipped** and **every structural check still applies**. `_place_order` and `_on_order_place_requested` (ticket-only) are deleted with the ticket, and `ibkr/validation.py`'s **module docstring `:5`** (which today says the gate is "Wired at the top of `MainWindow._place_order`") is **re-pointed at the retained emitter** `MainWindow._close_position_by_id` — the symbol it names must still exist after D41 (R6) | `AC-D41.4` requires the retained machinery to be "exercised" and the retained paths to "build and validate orders with a **resolving `ref_price`**", and D41's KEEP list says **D26's safety requirements stand**. Today the gate and the disconnected guard are reachable *only* from the deleted ticket, so leaving them in place would make `validate_order`/`ref_price` dead on the retained path while the app's only order emitter ran ungated — the D26.9 defect class (order "Submitted" against a dead socket) reopened. The `risk_reducing` carve-out is required because the cap exists to bound **new** exposure: without it, a position above USD 25,000 could never be flattened from the UI (a real availability regression, not a hypothetical) | (i) **no gate** — `validate_order` becomes production-dead, `ref_price` consumerless, `AC-D41.4`'s ref_price clause unmet — rejected; (ii) **gate without the carve-out** — blocks legitimate >25 k flattens — rejected; (iii) **gate with `ref_price=None`** — the notional check is skipped only *incidentally*, `ref_price` stays meaningless, and a future cap change would silently start blocking closes — rejected; (iv) a separate `validate_close_order()` — duplicates the gate (two divergent implementations; the ESC-026 anti-pattern) — rejected; (v) keep `_place_order` alive as a helper — it is ticket-only by construction (`AC-D41.3` forbids the ticket) — rejected |
| S6 | **Portfolio-only right dock** `[new/changed]` — **supersedes D18/B2's two-section region**, `AC-D18.3`, and D21.13's Active-Trader-title-bar clauses | **One** `QDockWidget`, `windowTitle()` **and** `objectName()` = **`"Portfolio"`**, whose widget is the existing `ActivePortfolioPanel` **directly** (the `RightDockContainer`, `_right_dock_layout` and the two-panel stretch juggling are deleted). Its **title-bar widget IS the Portfolio panel's `summary_label`** (`DiagonalStrikeButton("Account Summary")`) — so there is still exactly one visible label and it is the hide/show toggle — native title hidden (`Movable`/`Floatable` features unchanged). Collapse = that single section's body hidden; the collapsed state is the region-collapse state. `RIGHT_DOCK_MIN_WIDTH` stays **200**; the collapsed floor stays `max(RIGHT_DOCK_COLLAPSED_MIN_WIDTH=150, summary_label.sizeHint().width() + 2×RIGHT_DOCK_COLLAPSED_MARGIN)` (the existing formula, now over **one** button); **`RIGHT_DOCK_CAP_FRACTION` stays 0.40** and **`ui/dock_layout.py` + `plan_dock_widths` are unchanged** | `AC-D41.7` fixes the *outcome* (single Portfolio section, non-zero width, fully visible in full screen, clamped against the chart minimum) and leaves the *mechanism* to Plan (DG71). Reusing D21.13's affordance + the untouched pure clamp means the surviving D18 guarantees (incl. the original D17/D18 full-screen symptom and the ESC-026 floor fix) hold **by construction** rather than by re-derivation. The 40 % cap is an **upper bound** — keeping it removes no user capability, is DG71's explicitly blessed default, and is the only non-regressive choice; the 200 px minimum is what `plan_dock_widths` already enforces. The **rename** is deliberate: a Portfolio-only dock titled/`objectName`d `"Active Trader"` would keep a live "Active Trader" identifier in the UI and code after `AC-D41.1` forbids every Active-Trader affordance; the repo's title-keyed-lookup trap is handled by enumerating **all 17** title/`objectName`/title-bar-text consumer files, one by one, with the edit each needs (see S11, the plan's Phase-2 map, and AR-D41-3) | (i) **keep title/`objectName` `"Active Trader"`** to avoid touching the 17 consumer files — rejected: dishonest identifier, and it keeps the removed feature's name as a live UI/server string (a naming lie of exactly the kind DG67 already flags for `footprint_cache_key`); (ii) a **new bespoke title-bar widget** — rejected: duplicates D21.13's tested affordance and splits one convention into two; (iii) **narrow the cap to ~0.30** — rejected: removes user capability with no requirement behind it (DG71 blesses 0.40 as the safe default); (iv) **keep the container widget with one child** — rejected: dead structure, and `_right_dock_layout`/stretch factors exist only for two sections; (v) **merge Portfolio into the watchlist dock** — rejected: changes the left dock's D13/D17 model for no reason |
| S7 | **`footprint_cache` deletion** `[new/changed]` — closes **DG70** / A69 (Q49 = "delete") | Remove the `footprint_cache` **DDL** from `data/db.py::_init_schema` (fresh DBs never create it) **and** add an idempotent **`DROP TABLE IF EXISTS footprint_cache`** to `data/db.py::_migrate_schema()` (which already runs on every `DB()` open, alongside the existing additive `ALTER TABLE`s and the `idx_positions_symbol_con_id` index). Delete `data/footprint_cache.py`. Net effect on an existing user DB: table + rows gone at the next app start | The requirement asks for a "small migration" (A69/Q49 "delete"), and `_migrate_schema()` **is** this repo's migration mechanism: it already runs unconditionally at open, needs no version table, and `IF EXISTS` makes it a one-time, idempotent, crash-safe no-op afterwards. `DROP TABLE` (not `DELETE FROM`) is the recorded default (DG70 (b)) since the owning feature is removed | (i) **delete rows, keep the empty table** — DG70 (a); rejected per A69/DG70's recorded default (orphan schema for a removed feature); (ii) **standalone one-off script / manual `sqlite3` step** — rejected: there is no migration runner in this repo and an owner-run step would simply never happen for existing installs; (iii) **a versioned migration framework** — over-engineering for one drop — rejected; (iv) **keep the DDL, empty the table** — fresh DBs would recreate dead schema, contradicting A69's DDL-removal clause — rejected |
| S8 | **Subscription/registry surface** `[new/changed]` | Delete `DEPTH` and `DEPTH_HEATMAP` from `ibkr/subscription_manager.py`; keep `RT_BARS`, `MARKET_DATA`, `S0_TICKS`. Delete `MainWindow._guard_depth_budget` and `DEPTH_FEED_CAP`; **remove only the `depth` term** from `_md_line_count` (RT + S0 + watchlist terms stay). `services/md_line_guard.py::assess` and `MainWindow._guard_md_lines` are **unchanged** (D38's S0 lines use them) | Nothing subscribes with those tags once the depth feed and the ladder are gone; `S0_TICKS` is D38's (`"292"`/`"456"`). Keeping unused tags/caps would leave dead constants that invite a future mis-subscribe, and the depth term in the line count would reserve budget for a feed that cannot exist | (i) keep the tags/constants — dead surface, no benefit — rejected; (ii) keep the `depth` term in `_md_line_count` — inflates the count against no consumer — rejected; (iii) also drop `md_line_guard` — breaks D38 — rejected |
| S9 | **Bridge / client surface** `[new/changed]` | Delete exactly: `Bridge.historical_ticks_bid_ask`, `Bridge.historical_ticks_last`, `Bridge.update_mkt_depth`, and the overrides `IBApiClient.historicalTicksBidAsk`, `historicalTicksLast`, `updateMktDepth`, `updateMktDepthL2`. **Keep** the S0 overrides (`tickGeneric`, `tickString`, `tickNews`) and their signals (D38) | `AC-D41.2` demands **zero** `reqMktDepth`/`cancelMktDepth` of any kind and zero historical-ticks requests. Removing the overrides also makes a stray `updateMktDepth` callback from `ibapi` a **no-op** at the client boundary instead of a routed DOM update — the removal is enforced at the integration edge, not only at the call sites | (i) keep the overrides but ignore their payloads — silent dead path, still routes nothing but keeps the D37 signal surface — rejected; (ii) keep the signals for symmetry — dead signal — rejected |
| S10 | **Contract resolver surface** `[new/changed]` | Delete `ibkr/contracts.py::resolve_footprint_contract` (D36-only). **Keep `footprint_cache_key` and `INDEX_PROXY`** verbatim — D39's burst baseline key (`ui/ticker_session.py:922`) and D39's `alarm_monitor`/`alarm_dialog` proxy resolution depend on them | `AC-D41.4` names both as required survivors. The D36-derived **name** of `footprint_cache_key` is a recorded naming smell (DG67 → FS17) and a **non-requested refactor**: renaming it is out of D41's scope | (i) rename `footprint_cache_key` to a neutral name as part of D41 — rejected (unrequested refactor, touches D39's tested surface); (ii) inline the key rule into `ticker_session` and delete it — rejected (breaks `AC-D41.4`, duplicates the rule) |
| S11 | **Test surface** `[new/changed]` | **Delete** `tests/test_d36_footprint.py`, `tests/test_d37_microstructure.py`, `tests/test_market_depth.py`, `tests/test_order_entry_mkt.py`, `tests/test_order_entry_side.py` (all five are feature/widget-scoped). **Re-point** (not delete): `test_order_validation.py` (drop the two `_place_order` wiring tests, keep the pure gate tables), `test_order_rejections.py` (keep the registry assertions; re-point the surfaced message from the removed ticket to `status_bar`), `test_dock_d18_region.py`, `test_right_dock_d21.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_dock_widths_d17.py`, `test_watchlist_nonregression_d22.py` (title-bar/collapse assertions → the Portfolio header), `test_d27_reconnect.py` (Phase 1: drop the D37 session-depth assertions and re-derive the replayed `mkt_data` count, keep RT/S0/watchlist replay **and** the DOM-depth assertions; Phase 2: the dock-title tuple → `"Portfolio"` only), **the 15 title/`objectName`-keyed dock consumers** (`test_dock_widths_d17.py`, `test_watchlist_d14_midrag.py`, `test_crosshair_axis_lane.py`, `test_d27_position_prices.py`, `test_history_backfill.py`, `test_history_backfill_disconnect.py`, `test_dock_widths_d18.py`, `test_d10_d13_integration.py`, `test_d27_account_subs.py`, `test_watchlist_columns_d21.py`, `test_d27_phantom_alarms.py`, `test_d27_stream_health.py`, `test_history_backfill_loadpath.py`, `test_dock_d18_region.py`, `test_d27_reconnect.py` → `"Portfolio"`), **`test_d28_pacing.py`** (the D28.1 order-path deferral re-pointed at the retained close emitter), **`test_kill_switch.py`** (D26.8's all-three-bracket-legs assertion re-pointed at the retained builders — never deleted), and the toolbar control lists (`test_toolbar_scroll_d19.py`, `test_toolbar_d20.py`, `test_toolbar_d21.py` → drop `dom_btn`). **Add** `tests/test_d41_removal.py`, `tests/test_d41_portfolio_dock.py`, `tests/test_d41_retained_order_path.py`; **extend** `tests/test_db_schema.py`; and **re-home the two KEEP symbols' only tests** (R2) — `footprint_cache_key`'s roll-over rule into `tests/test_d39_burst_search.py` and `md_line_guard.assess`'s thresholds into `tests/test_d38_events_news.py` — so that `AC-D41.4`'s "remain and remain exercised by their tests" holds for every KEEP-listed symbol | `AC-D41.3`/`4`/`5` cannot be evidenced by suites that test the removed widgets, and the requirements explicitly require the order-entry tests to be "re-pointed at the retained machinery or removed with the widget" and the toolbar geometry fixtures to be "re-checked". The dock/toolbar suites are **re-pointed rather than deleted** because their surviving assertions are `AC-D41.7`'s acceptance evidence. The title-keyed tuples must be updated in lockstep with the rename or those helpers silently stop hiding the right dock — the D19 "hidden widget masks the real constraint" trap (memory 2026-10-05) | (i) delete the D18/D21.13/dock-width suites wholesale — rejected: loses `AC-D41.7`'s evidence; (ii) keep `"Active Trader"` as the dock title to avoid the churn — rejected (see S6); (iii) leave the toolbar `_CONTROL_NAMES` unchanged — they would assert a control that no longer exists — rejected |
| S12 | Testing `[existing]` | pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), **no live TWS, no transmitted orders**; run as `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale shebang); any non-pytest probe that can reach a DB-writing path **must** export `DB_PATH` to a temp file (ESC-043: an unset `DB_PATH` writes the owner's production DB) | Repo standard (Q8/Q9) + the repo's own recorded gotchas | Manual-only / live-TWS verification — rejected (`AC-G` and Q9) |

---

## System Components

### Removed `[existing → deleted]`

| Component | Files | Notes |
|---|---|---|
| Footprint render layer + controls | `ui/footprint_item.py`; the `Footprint`/`Classic`/`Tick count` cluster + `footprint_static`/`footprint_live`/`_fp_*`/`refresh_footprint`/`_fp_status_text` and the `footprint_toggled`/`footprint_viewport_changed` signals in `ui/chart_panel.py` | `AC-D41.1` |
| Footprint service / cache / tick history | `services/footprint_service.py`, `data/footprint_cache.py`, `ibkr/tick_history.py`; the `filename`/wave/forming/cache state in `ui/ticker_session.py`; the `historical_ticks_*` signals in `ibkr/bridge.py` + the `historicalTicks*` overrides in `ibkr/client.py`; `resolve_footprint_contract` | `AC-D41.3` |
| Depth heatmap / IMB / AUC | `ui/depth_heatmap_item.py`, `services/depth_heatmap.py`; the `Depth`/`IMB —`/`AUC —` cluster, heatmap strip, state text, 500 ms repaint timer and `bind_d37_session`/`unbind_d37_session`/`set_depth_state`/`update_auction_chip` in `ui/chart_panel.py`; `_depth`/`_depth_req_id`/`_depth_holders`/`_depth_state`/`ensure_depth_subscribed`/`release_depth`/`_cancel_depth`/`_reissue_depth`/`_rebind_depth_req_id`/`on_depth_update`/`on_depth_error`/`_set_depth_state`/`depth_imbalance`/`_depth_roll_timer` and the `depth_state_changed`/`auction_updated` signals in `ui/ticker_session.py`; the `"225"` auction need + auction ingress; `subscription_manager.DEPTH_HEATMAP` | `AC-D41.1`/`AC-D41.2` |
| Active Trader panel (whole) + DOM ladder | `ui/active_trader_panel.py` (ladder/book **and** `OrderEntryWidget` ticket **and** the panel shell/`header_bar`); `ibkr/market_depth.py`; `ibkr/order_book.py`; the `DOM` toolbar button + `_on_dom_toggled`/`_subscribe_dom`/`_on_mkt_depth`/`_depth_req_id`/`_rebind_depth_req_id`/the depth error branch/`closeEvent`'s depth cancels in `ui/main_window.py`; `ui/watchlist_panel.py::set_depth_manager`/`on_depth_update`/`_depth_manager`; `subscription_manager.DEPTH`; `Bridge.update_mkt_depth` + the `updateMktDepth*` overrides | `AC-D41.1`/`AC-D41.3`; makes ESC-039/ESC-035 moot (DG66) |
| Depth feature's model | `data/models.py::OrderBookLevel` (`:105`–`:110`) | **Dead today** — zero references in the tree (verified); it is the depth feature's model, so D41 takes it (`AC-D41.3`'s no-dangling intent). Inert removal; **FI-2, accepted by the Validator as within "all associated code"** and recorded here as an **explicit scope close-out** (a deliberate, named inclusion — not an undeclared extra), machine-checked by the removal guard's token set |
| Persisted footprint data | `footprint_cache` DDL in `data/db.py` + `DROP TABLE IF EXISTS` in `_migrate_schema()` (S7) | Q49/A69/DG70 |

### Retained, unchanged `[existing]`

`ibkr/orders.py` (incl. `bracket_order`), `ibkr/validation.py` (**function body unchanged** — one additive keyword, S5), `ibkr/id_manager.py`, the kill switch (`reqGlobalCancel` + per-ID cancels), the order registry / order-error routing, `config/settings.py::check_live_port` + `MAX_ORDER_NOTIONAL`; the D38 S0 substrate (`s0_register_many`/`S0_TICKS`/`tick_generic`/`tick_string`/`tick_news` + overrides), `services/volume_baseline.py` + the `volume_baseline` table, `ibkr/contracts.py::footprint_cache_key`/`INDEX_PROXY`, `services/md_line_guard.py`, `data/db.py`'s other tables, and the yfinance event source (D38) — i.e. **nothing D1–D35 or D38–D40 depends on is redesigned**.

**KEEP-list coverage is preserved, not just the symbols (R2).** Every `AC-D41.4` survivor keeps a
test in the post-D41 tree: `footprint_cache_key` (its only test, `tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape`, moves to `tests/test_d39_burst_search.py`) and
`md_line_guard.assess` (its only test, `tests/test_d37_microstructure.py::test_md_line_guard_thresholds`, moves to `tests/test_d38_events_news.py`) — both re-homed in the same phase that deletes the
suite they lived in. `INDEX_PROXY`/`S0_TICKS`/`volume_baseline` keep their existing D38/D39 suites;
`bracket_order` keeps `tests/test_order_builders.py`; the kill switch keeps `tests/test_kill_switch.py`
with its all-three-legs assertion re-pointed at the retained builders.

### New / changed `[new/changed]`

| Component | Change |
|---|---|
| `MainWindow._ref_price_for(symbol)` | New tiny accessor over `_symbol_last_prices` (S4) |
| `MainWindow._close_position_by_id` | Gains the disconnected guard + `validate_order(..., risk_reducing=True, ref_price=…)` before the existing pacing + `placeOrder` (S5) |
| `ibkr/validation.py::validate_order` | One additive keyword `risk_reducing: bool = False` (default preserves all existing behaviour and tests) (S5) |
| `MainWindow` right dock | Portfolio-only single-section dock (S6); `_compute_right_dock_collapsed_min_width` now reads one button; `_sync_right_dock_collapse` loses the two-panel stretch juggling |
| `data/db.py::_migrate_schema` | Adds `DROP TABLE IF EXISTS footprint_cache` (S7) |
| `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`, `ibkr/contracts.py`, `ui/watchlist_panel.py` | Deletions only (no new behaviour) |
| `ui/active_portfolio_panel.py` | **Not modified.** Its `summary_label`/`body`/`is_collapsed()` are reused as-is by the new dock. (Deliberate: ESC-043/ESC-045 live in this file's render path and are **not** D41's to fix.) |

---

## Data Model

| Entity | Status | Key fields / notes |
|---|---|---|
| `footprint_cache` (SQLite) | `[existing → removed]` | `resolved_contract`, `date`, `timeframe`, `blob` (PK on the first three). DDL leaves `data/db.py`; an existing DB's table is dropped by the idempotent `_migrate_schema()` step (S7) |
| `data/models.py::OrderBookLevel` | `[existing → removed]` | `position`, `side`, `price`, `size`, `market_maker`; zero references (S3; **FI-2**, accepted scope close-out) |
| `data/footprint_cache.py::FootprintCache` / `is_cacheable` | `[existing → removed]` | Module deleted with the DDL |
| `volume_baseline` (SQLite) | `[existing]` | D39; untouched — `AC-D41.4` |
| `yfinance_events_cache` (SQLite) | `[existing]` | D38; untouched |
| `positions`, `trade_groups`, `position_group_map` | `[existing]` | Untouched (D27.5/Phase 7). `positions.id` remains the SL/TP + close key |
| `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `popouts` | `[existing]` | Untouched |
| `MainWindow._symbol_last_prices` (in-memory) | `[existing]`, **newly consumed** `[new/changed]` | Becomes the retained `ref_price` source (S4); already fed by the watchlist sink and every aggregated chart bar |
| `MarketDepthManager._feeds` / `_shared` (in-memory) | `[existing → removed]` | Whole manager deleted |
| `OrderBook` / `Level` (in-memory) | `[existing → removed]` | `ibkr/order_book.py` deleted |
| `levels`/state dicts in `ui/active_trader_panel.py` | `[existing → removed]` | Module deleted |

**No new entity, no new column, no field-level change.** The only schema delta is a **drop**.

---

## Integration Points

| Integration | Status | Why |
|---|---|---|
| IBKR `reqMktDepth` / `cancelMktDepth` | `[existing → removed]` | Both the heatmap's refcounted SMART feed and the ladder's direct feed go; `AC-D41.2` requires **zero** of any kind |
| IBKR `reqHistoricalTicks` | `[existing → removed]` | D36 footprint pages |
| IBKR `reqTickByTickData` | `[existing]` — **never used** (asserted by the D36 docs/tests) and still not used | `AC-D41.2` requires zero; removal makes it structurally impossible |
| IBKR generic ticks `"225"` (auction) via `reqMktData` | `[existing → removed]` | `AC-D41.2` |
| IBKR S0 generic ticks `"292"` (news) / `"456"` (dividends) via `reqMktData` | `[existing]` | D38 still needs them (`AC-D41.4`); the S0 substrate stays |
| IBKR `reqRealTimeBars`, `reqHistoricalData`, `reqContractDetails`, `reqPositions`, `reqAccountSummary`, `reqMatchingSymbols` (D39), `reqNewsProviders` (D38) | `[existing]` | Untouched |
| IBKR `placeOrder` / `cancelOrder` / `reqGlobalCancel` | `[existing]` | Retained; after D41 the **only** emitter is Portfolio Close / Close Group / Flatten All (+ the kill switch). `bracket_order` survives as retained machinery, exercised by its own tests |
| yfinance (D38 corporate events) | `[existing]` | Untouched |
| SQLite (`config/paths.get_db_path()`) | `[existing]` | One fewer table; `DB_PATH` hermeticity rules apply to every new test (S12) |
| **New integrations** | — | **None.** D41 adds no external dependency |

---

## Non-Functional Approach

- **Performance / work per tick (driven by `AC-D41.1`/`AC-D41.2`).** Removing the 500 ms
  `_depth_refresh_timer` repaint, the depth-op ingress, the two `FootprintItem` render layers and
  the footprint backfill wave removes per-tick and per-op work from the chart and the session.
  The §7 market-data line count loses its `depth` term and `DEPTH_FEED_CAP` disappears, so a
  removed feed can no longer consume budget. **No** change to the candle/volume rendering math
  (`ui/candlestick_item.py`, the volume width path) — deliberately, because ESC-041/ESC-042 own
  that defect (FI-3).
- **Pacing (D28.3/D28.4 guarantees preserved).** The footprint wave's `reqHistoricalTicks` pages
  and the depth subscriptions leave the historical/market-data budget; `ibkr/pacing.py`, the
  order token bucket (`order_limiter`) and the RT-bar budget are untouched. The retained close
  path keeps using `order_limiter` and its `singleShot` deferral (S5 step 3).
- **Safety / security (driven by D26 standing + `AC-D41.4`).** The in-app order ticket goes, so
  no UI path can compose an arbitrary order; the surviving close/flatten path is *gated* rather
  than ungated (S5): disconnected ⇒ refuse; structural validation always; notional cap for
  risk-increasing orders only. The kill switch, order-ID reservation, order-error routing and the
  fail-fast live-port check are untouched. No test transmits an order or connects to TWS (S12).
- **Scalability / session hygiene.** Depth refcounting per symbol disappears, so
  `SubscriptionManager` carries fewer entries per session and the post-reconnect replay set shrinks
  (`test_d27_reconnect.py` counts are re-derived, not weakened — AR-D41-5). Session teardown loses
  the depth/footprint branches, shrinking the teardown surface.
- **Observability.** The removed user-visible states (`Footprint loading…`, `No tick data for …`,
  `Depth unavailable`/`Depth subscription required`, the ladder/book tabs) disappear with their
  features. The **retained** path's feedback is the status bar (rejections, pacing deferral,
  close confirmations) — `_on_order_error`/`_update_order_status` keep the registry update and
  drop their ticket line (AR-D41-1).
- **Maintainability / docs.** 9 production modules and 5 suites leave the tree. AC-D41.6's markdown-history
  markers (`SUPERSEDED BY D41` on `### D36`/`### D37` + the D18/D21.13 notes) are already present in
  `requirements.md` and are **Requirements-owned** — Build must not edit that file (AP-5). The
  `footprint_cache_key` naming smell stays recorded as FS17 (S10).

---

## Architecture Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D41-1 | A **retained** path silently depends on something deleted — e.g. `_update_order_status`/`_on_order_error` calling `active_trader.set_order_status`, `closeEvent`'s depth cancels, `_rebind_depth_req_id` in the reconnect replay, or the `depth` term in `_md_line_count` | **H** | Every `active_trader.*`/`depth_manager.*`/`_depth_req_id` reference is enumerated by file in the plan's `touches_files` map; the ticket-line calls become status-bar-only; the new `tests/test_d41_removal.py` scans the whole production+test tree for the removed identifiers and the reconnect suite re-verifies replay after the edits |
| AR-D41-2 | **Dead imports** left in `ui/main_window.py` (`TickHistoryManager`, `FootprintCache`, `MarketDepthManager`, `DEPTH`/`DEPTH_HEATMAP`, `ActiveTraderPanel`, `on_depth_callback`, `FootprintItem`, `DepthHeatmapItem`, `resolve_footprint_contract`) — the tree imports fine today and would fail only at run time for some, at import for others | **H** | The import guard asserts `importlib.util.find_spec(...) is None` for each deleted module **and** greps `ui/`, `ibkr/`, `services/`, `data/`, `config/`, `tests/`, `main.py` for the identifiers; the UI smoke path (`MainWindow()` construction) runs in the same suite |
| AR-D41-3 | The dock **rename** quietly defuses the title-keyed dock-hiding helpers, so geometry tests keep passing while exercising a window the app does not have (exactly the D19 masking trap) | **M** | The plan enumerates **all 17** consumer files — 15 `windowTitle()`/`objectName()` lookups + 2 title-bar-text assertions — one by one with the edit each needs (S11; `docs/plan_proposal.md` Phase 2). The round-1 proposal under-counted these as "8"/"9" and omitted five of them, three of which fail **deterministically**; the corrected list is the mitigation. The new dock suite asserts **exactly one** right dock, titled/`objectName`d `"Portfolio"`, that it is the Portfolio panel, and that **no** dock/widget titled `"Active Trader"` exists anywhere — a stale tuple is then detectable, not silent |
| AR-D41-4 | Toolbar geometry fixtures pin `dom_btn` **and** a font-dependent intrinsic width (1965 px @9 pt vs 1921 px with Inter 11 px); removing the button changes the fixture baseline | **M** | Drop `dom_btn` from `_CONTROL_NAMES`/`_CHECKABLE_TOGGLES`; re-run the D19/D20/D21 geometry suites; the toolbar only gets **narrower**, so overflow assertions stay satisfiable — never lower an assertion below a measured width |
| AR-D41-5 | `tests/test_d27_reconnect.py` asserts replayed subscription **counts** (`len(fake.mkt_depth)`, `len(fake.mkt_data) == 4`, per-reqId rebinding) that the removal changes | **H** | The D37 session-depth assertions are dropped **and** the replayed `mkt_data` count re-derived from the surviving watchlist row + S0 line **in Phase 1** (where their subjects go); the DOM-depth assertions (`:200`–`:203`, `:228`–`:229`) are kept until **Phase 2** (where `_subscribe_dom`/`_depth_req_id` go) and its one dock-title line (`:163`) moves in Phase 2 with the rename; the RT/S0/watchlist replay + rebinding assertions (the real D27.3 guarantee) are preserved verbatim throughout as a deliberate **two-phase, disjoint-line** edit (AP-11) |
| AR-D41-6 | Deleting `_place_order` takes the D26.9 disconnected guard and the validate gate with it, leaving the surviving close/flatten path ungated (**reopens the defect class the ticket path had fixed**) | **H** | S5 re-homes both gates onto `_close_position_by_id`, with new tests: disconnected close refuses + no `placeOrder`; invalid close refuses; valid close transmits exactly once with a resolved `ref_price`. The two existing suites that drove the **deleted** `_place_order` are **re-pointed at the retained path**, not left red (R1): the D28.1 order-path deferral (`tests/test_d28_pacing.py`) and D26.8's all-three-bracket-legs transmit-time registration (`tests/test_kill_switch.py`, the only test of that property) |
| AR-D41-7 | The notional cap blocking a legitimate large flatten if the `risk_reducing` carve-out is implemented wrong (or applied where it should not be) | **M** | Carve-out is a single new keyword **defaulting to False** (no existing caller's behaviour changes); asserted both ways: a >USD 25 000 close transmits, and a risk-increasing `validate_order` call above the cap is still rejected (`test_order_validation.py`'s existing notional tests stay untouched) |
| AR-D41-8 | `AC-D41.1`'s ban on any `footprint_*`/`depth_*`/`auction_*` signal or attribute is a **broad** surface — a stray leftover (`_fp_queue_viewport_sync`, `_depth_state_text`, `depth_enabled`, `bind_d37_session`, `auction_state`, `_auction`, `set_depth_state`) fails it | **M** | The guard enumerates the token set (including `hasattr` probes on a real `ChartPanel`/`MainWindow`) and is **red before** the change; the removal tasks are scoped per file so nothing is half-removed |
| AR-D41-9 | D41 is credited with fixing the wide-candle / volume-overlap defect (DG68 still **open**), while the concluded investigation proves the cause is the D6 4-px floor vs inter-bar pitch in `ui/candlestick_item.py:122`–`:138` + the chart volume width path (`ui/chart_panel.py:1688`–`:1690`) and rules the footprint overlay **out** | **M** | Explicitly out of D41's blast radius: `ui/candlestick_item.py` and the volume-width math are **untouched**; **ESC-041 stays open and BUILD-owned and is `blocking` in `escalations.json`** (not "should-fix" — corrected); DG68 is flagged (FI-3) so the removal is not sold as a fix. Evidence: `docs/code_review/candle_overlap_investigation.md` §1/§2 (lead 3)/§4 |
| AR-D41-10 | A removal pass touches shared files three times (chart_panel / ticker_session / main_window / bridge / client / subscription_manager), and `main_window.py` line numbers are cited across the docs — churn invalidates citations and invites merge conflicts | **M** | Phases are **strictly ordered** (one phase's wave consolidated before the next opens) and each phase's `touches_files` is **disjoint**, so no two workers edit the same file in a wave; the file map is published per phase; docs citations in `architecture.md`/`plan.md` are the Validator's/Code Reviewer's to re-anchor, not Build's to chase |
| AR-D41-11 | Junk/foreign rows or a non-hermetic probe DB (ESC-043) surfacing as false failures while validating the dock/portfolio geometry | **M** | Every new test constructs its window like the existing suites (monkeypatched `connect`, `tests/conftest.py` sets `DB_PATH` to a temp file); no probe writes to the user-space DB (S12) |
| AR-D41-12 | Orphaned `__pycache__` for the deleted modules (the DOC-3/ESC-001 precedent) making an import guard pass or fail confusingly | **L** | The guard asserts on `find_spec`/source paths, not on cached artefacts; the verification phase runs from a clean tree |

---

## Implementation sequencing (summary — the authoritative phase/per-file map is in `docs/plan_proposal.md`)

Three phases, strictly ordered, each partitioned by file so concurrent tasks never share a
`touches_file`:

1. **Phase 1 — remove the D36 footprint *and* D37 depth/heatmap/imbalance/auction feature trees.**
   **20 file entries.** Deletes 6 production modules + 2 suites; surgical deletions in
   `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`, `ibkr/bridge.py`,
   `ibkr/client.py`, `ibkr/subscription_manager.py`, `ibkr/contracts.py`, `data/db.py`; one
   docstring de-reference (`services/md_line_guard.py`); the `footprint_cache` drop; three test
   edits — `tests/test_d27_reconnect.py` (the D37 session-depth assertions + the replayed-count
   re-derivation) and the **two KEEP-coverage re-homes** (`tests/test_d39_burst_search.py`,
   `tests/test_d38_events_news.py`). Depends on: nothing.
2. **Phase 2 — remove the Active Trader panel + DOM ladder + market-depth machinery, re-shape the
   right dock Portfolio-only, and re-home the retained order gates.** **39 file entries.** Deletes 3
   production modules + 3 suites; edits `ui/main_window.py`, `ui/watchlist_panel.py`, `data/models.py`,
   `ui/dock_layout.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`,
   `ibkr/validation.py`; re-points the dock/toolbar/order suites **and all 17 title/title-bar
   consumers**, plus `tests/test_d28_pacing.py`, `tests/test_kill_switch.py`,
   `tests/test_crosshair_axis_lane.py`, the four dock-hide helpers, and the one dock-title line in
   `tests/test_d27_reconnect.py` (S11; plan-proposal R1). Depends on: Phase 1 (shared files).
3. **Phase 3 — non-regression verification.** **4 file entries.** Adds `tests/test_d41_removal.py`
   (with the widened token set + documented allow-list), `tests/test_d41_portfolio_dock.py`,
   `tests/test_d41_retained_order_path.py`; extends `tests/test_db_schema.py`; full offscreen suite
   green (`AC-D41.5`); D38/D39/D26 spot checks (`AC-D41.4`). Depends on: Phases 1–2.

**Not in D41 (must not be touched):** `ibkr/orders.py`, `ibkr/id_manager.py`,
`ibkr/error_codes.py` (outside the S5 keyword), `config/settings.py`'s `check_live_port`/
`MAX_ORDER_NOTIONAL`/pacing constants, `services/volume_baseline.py`, `services/md_line_guard.py`
(function), `data/events/*`, `ibkr/news.py`, `ui/news_digest_dock.py`, the D39 search path,
`ui/candlestick_item.py`, `services/backfill_service.py`, `services/market_calendar.py`,
`ui/active_portfolio_panel.py`, and **every** escalation that D41 does not moot
(ESC-032/033/034/036/037/**038**/041/042/043/044/045 — **11** `open` entries; ESC-035/039/040 are
mooted by the removal per DG66 and are the **Code Reviewer's** to close after re-verification, not
Build's — AP-7).
