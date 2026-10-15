# Implementation Plan Proposal — NDThinkChart Batch 18 (**D41**)

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical plan —
> `docs/plan.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/architecture_proposal.md` (Codebase Summary, decisions `S1`–`S12`, components, data model,
> integrations, non-functional approach, risks `AR-D41-1`–`AR-D41-12`).
>
> **Revision 2 (2026-10-15)** — this is the **round-1 `CHANGES_REQUIRED` response**. The three
> architecture decisions (`S4` `ref_price` source, `S6` Portfolio-only dock, `S7` footprint_cache
> drop) and the order-path finding (`FI-1`'s load-bearing claim) were **verified against source by
> the Validator and are unchanged**; what changed is the **file/test map** (both `touches_files` maps
> completed), the **KEEP-list coverage re-home**, the **removal guard's token set**, and the
> **evidence/severity + internal cross-reference corrections**. R1–R6 are addressed item by item in
> § *Review-response record (R1–R6)* at the end of this file.
>
> **Scope: D41 only** — a **removal** work item, owner-requested 2026-10-15, scope finalised
> 2026-10-15 (Q48/Q49/Q50). `requirements.md` carries `Status: READY_FOR_PLAN`, `### D41`
> (`:3263`–`:3426`, `AC-D41.1`–`AC-D41.7`), Journey 36 (`:855`–`:882`), `A68`–`A71`,
> gaps `DG66`–`DG71`. `AC-D36.*`/`AC-D37.*` are **SUPERSEDED BY D41** (history, DOC-4), and the
> affected **D18**/**`AC-D18.3`**/**D21.13** clauses are **superseded by D41** with reasons.
> Built on the frozen baseline: `main` @ `29067af`, 1,028-test offscreen suite green.

**What D41 removes:** the D36 footprint feature tree; the D37 depth heatmap / imbalance / auction
feature tree; the **entire** Active Trader panel (DOM ladder **and** the in-app order-entry
ticket) with `ibkr/market_depth.py`, `ibkr/order_book.py`, the `DOM` toolbar button, the watchlist
depth wiring and the depth terms of the MD-line accounting; the persisted `footprint_cache` table
(+ rows) — and the right dock becomes **Portfolio-only**.

**What D41 must not break:** the retained order machinery (`ibkr/orders.py` incl. `bracket_order`,
`ibkr/validation.py` + `validate_order()`, order-ID reservation, the kill switch, order registry /
error handling, the fail-fast port check) for Portfolio's Close / Close Group / Flatten All and the
SL/TP dialogs; D38 (news/dividends: `footprint_cache_key`, `INDEX_PROXY`, `md_line_guard.assess`,
`_guard_md_lines`, S0 `"292"`/`"456"`, the S0 substrate); D39 (`volume_baseline` + burst/search);
D27/D28 correctness/pacing/perf and the chart. **11 escalations stay open and untouched**
(ESC-032/033/034/036/037/**038**/041/042/043/044/045 — `escalations.json` holds **14** `open`
entries today, of which ESC-038 is `open`/routed REQUIREMENTS and D41-neutral); ESC-035/039/040 go
**moot** by removal only (DG66) and are flipped to `addressed` by the **Code Reviewer** after
re-verification, not by Build (AP-7).

---

## Phases

Three phases, **strictly ordered**. Each phase's wave must be fully consolidated before the next
phase opens, because `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`,
`ibkr/bridge.py`, `ibkr/client.py` and `ibkr/subscription_manager.py` each receive edits in more
than one phase (see the sequencing constraint below).

### Phase 1 — Remove the D36 footprint *and* D37 depth / imbalance / auction feature trees

- **Goal:** after this phase the app has no footprint render layer, no footprint service/cache/tick
  history, no depth heatmap, no IMB/AUC controls, no session depth refcount, no `"225"` auction
  need, and no `footprint_cache` table — while the chart, the watchlist, D38's S0 lines, D39's
  burst/search substrate and the retained order machinery are unchanged.
- **Covers:** `AC-D41.1` (the footprint/depth/IMB/AUC half), `AC-D41.2` (the
  `reqHistoricalTicks`/`reqTickByTickData`/`reqMktDepth`-heatmap/`"225"` half), `AC-D41.3` (the
  D36/D37 modules + the two suites), `AC-D41.4` (the D38/D39 half), and the Q49/A69/DG70
  persisted-data drop.
- **Requirement/journey coverage:** Journey 36 steps 1–5 (postconditions 1 and 2, and the
  `footprint_cache` edge case); `### D41` "Scope — REMOVE" bullets 1–2 and "Persisted footprint
  data".
- **Depends on:** nothing (first phase of the batch).
- **Why these two features are one phase:** their chart-side removal is **one contiguous edit** in
  `ui/chart_panel.py` (a single floating cluster whose D37 row is positioned "below the footprint
  row", plus one adjacent handler block) and one contiguous session edit in
  `ui/ticker_session.py`; splitting them would edit the same files twice for no verification gain,
  and D41's own scope presents them as one removal item. It also keeps `main_window.py` to **one**
  edit in this phase (the docs cite `main_window.py` line numbers — churn is a real cost, AR-D41-10).

**`touches_files` map — Phase 1** *(20 file entries; one task per file; within a wave these sets
are disjoint)*

| File | Action | Content |
|---|---|---|
| `ui/footprint_item.py` | **delete** | `FootprintItem` |
| `services/footprint_service.py` | **delete** | `FootprintService`, `mark_no_tick_data` (dead), page/wave bookkeeping |
| `data/footprint_cache.py` | **delete** | `FootprintCache`, `is_cacheable` |
| `ibkr/tick_history.py` | **delete** | `TickHistoryManager.req_historical_ticks` |
| `ui/depth_heatmap_item.py` | **delete** | `DepthHeatmapItem` |
| `services/depth_heatmap.py` | **delete** | `DepthHeatmapService`, `BUCKET_SECONDS` |
| `tests/test_d36_footprint.py` | **delete** | D36 suite (551 lines) |
| `tests/test_d37_microstructure.py` | **delete** | D37 suite (421 lines) |
| `ui/chart_panel.py` | edit (delete-only) | imports `:15`–`:16`; signals `:249`–`:254` (`footprint_toggled`/`footprint_viewport_changed`/`depth_toggled`); render layers `:351`–`:376` (`footprint_static`/`footprint_live`/`depth_heatmap_item`/`_depth_enabled_ui`); the whole floating cluster (footprint row + D37 row) `:500`–`:565`; `_position_fp_controls`/`_on_fp_*`/`refresh_footprint`/`_fp_status_text`/`_fp_queue_viewport_sync`/`_fp_emit_viewport` `:651`–`:750`; D37 `:757`–`:971` (`depth_enabled`, `_position_d37_controls`, `_on_depth_toggled`, `_on_imb_clicked`, `_on_auction_clicked`, `_on_depth_refresh`, `bind_d37_session`/`unbind_d37_session`, `_on_auction_tick`, `update_auction_chip`, `_in_auction_window`, `set_depth_state`, `_depth_refresh_timer`); the `resizeEvent`/scroll back-references `:988`–`:992`, `:1790`–`:1797`. **Keep** the zoom cluster, the `Volume` toggle, D38 `bind_d38_session`/`_on_events_updated`, and the D6/D9 width math (`ui/chart_panel.py::ChartPanel._clamp_half_width`, `:1688`–`:1690` — ESC-041's subject, AR-D41-9) |
| `ui/ticker_session.py` | edit (delete-only) | imports `:41`, `:46`; signals `:76`–`:80`; `_footprint`/`_fp_*` state `:163`–`:179`; auction state + depth state/timer `:203`–`:217`; `attach_view`'s `{"auction": {"225"}}` registration `:260`–`:269`; `detach_view`'s auction dereg `:281`; `teardown` `:332`–`:345`; `_append_bar`'s footprint resync `:829`–`:838`; the whole `_fp_host_managers`/`footprint_enable`/`footprint_resync`/`footprint_disable`/wave/forming/`_fp_*` block `:958`–`:1420`; the depth block `:708`–`:830` (`ensure_depth_subscribed`, `release_depth`, `_cancel_depth`, `_reissue_depth`, `_rebind_depth_req_id`, `on_depth_update`, `on_depth_error`, `_set_depth_state`, `depth_imbalance`, `depth_req_id`, `_on_depth_roll_timeout`); auction ingress in `on_tick_price`/`on_tick_size` `:539`–`:556`. **Keep** `footprint_cache_key`'s D39 use `:922`, the S0 substrate + `on_s0_tick_generic`/`on_s0_tick_string`/`on_s0_tick_news`, the RT path |
| `ui/main_window.py` | edit (delete-only) | imports `:32`–`:33`, `:41`; `self.tick_history_manager`/`self.footprint_cache` `:556`–`:558`; `b.historical_ticks_*` connects `:654`–`:655`; `chart_panel.footprint_toggled`/`footprint_viewport_changed`/`depth_toggled` connects `:350`–`:355`; `footprint_updated` connect/disconnect `:935`–`:954`; `_on_depth_toggled`/`_on_fp_toggled`/`_on_fp_viewport`/`_on_primary_footprint_updated` `:965`–`:1015`; the footprint restart on reconnect `:1178`; the D36/D37 error branches `:1664`–`:1671`; `_on_fp_ticks_*` slots; the `depth` term of `_md_line_count` `:800`–`:801` and `_guard_depth_budget`/`DEPTH_FEED_CAP` `:99`, `:817`–`:824` (its only caller is `ui/ticker_session.py::TickerSession.ensure_depth_subscribed` `:720`, removed here). **Keep** `self.depth_manager` creation `:560` (its last consumers are Phase 2's DOM path) and `_guard_md_lines` `:805` |
| `ibkr/bridge.py` | edit (delete-only) | `historical_ticks_bid_ask` `:15`, `historical_ticks_last` `:17` |
| `ibkr/client.py` | edit (delete-only) | `historicalTicksBidAsk` `:314`–`:316`, `historicalTicksLast` `:318`–`:320` |
| `ibkr/subscription_manager.py` | edit (delete-only) | `DEPTH_HEATMAP` `:38` (**keep** `S0_TICKS`, and the retained `SubscriptionManager.has_subscription` `:81`) |
| `ibkr/contracts.py` | edit (delete-only) | `resolve_footprint_contract` `:160`+ (**keep** `footprint_cache_key` `:144` verbatim, `INDEX_PROXY` `:133`) |
| `data/db.py` | edit | remove the `footprint_cache` DDL `:118`–`:127`; add `DROP TABLE IF EXISTS footprint_cache` to `_migrate_schema` (S7). **Keep** `yfinance_events_cache` + `volume_baseline` |
| `services/md_line_guard.py` | edit (comment only) | module docstring `:13` de-references "depth feeds" (only the S0 lines gate on the verdict after D41); thresholds + `assess()` body unchanged (S8) |
| `tests/test_d27_reconnect.py` | edit | drop **the D37 session-depth assertions** (`:204`–`:208`, `:230`–`:232`) and the replayed-`mkt_data` count `:221`–`:223`, re-derived from the surviving watchlist row + S0 line (the `"225"` auction need is gone above); **keep** `:200`–`:203`/`:228`–`:229` (the DOM-depth assertions) **until Phase 2**, and **keep** the RT/S0/watchlist replay + rebinding assertions verbatim (`:220`, `:224`–`:227`, `:233`–`:236`). The `"Active Trader"` dock-title tuple `:163` is **left untouched here** — the rename lands in Phase 2, and the file is re-pointed again there for that one line *(the two-phase edit is deliberate: the depth drops must land with the code they assert, the title split cannot precede the rename)* |
| `tests/test_d39_burst_search.py` | edit (**R2 re-home**) | gains `test_footprint_cache_key_rollover_isolates_tape` — the assertions moved **verbatim** from `tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape` (`:389`–`:395`): `footprint_cache_key("SPX", now=…)` startswith `"ES"` for two dates on either side of the front-month roll, and `key1 != key2`. D39 is the surviving consumer of the key (`ui/ticker_session.py::TickerSession` burst baseline), so this is its natural home; without it the deleted D36 suite takes the symbol's **only** test (R2) |
| `tests/test_d38_events_news.py` | edit (**R2 re-home**; previously "no change") | gains `test_md_line_guard_thresholds` — the assertions moved from `tests/test_d37_microstructure.py::test_md_line_guard_thresholds` (`:336`–`:344`), re-purposed to the **surviving** purpose: `assess(50, "SPX", "S0 ticks") == ("ok", "")`, `assess(90, …)` → `"approaching"` with `"90/100"` in the message, `assess(100, …)` → `"exceeded"` naming the symbol and refusing. The D38 S0 lines are what `_guard_md_lines` still gates, so the thresholds get their retained suite; without it the deleted D37 suite takes `assess`'s **only** test (R2). Its existing `queue_depth` assertions (`:158`, `:165`) and its comment-only D36 references are untouched |

### Phase 2 — Remove the Active Trader panel (DOM ladder + order-entry ticket) and the market-depth machinery; make the right dock Portfolio-only; re-home the retained order gates

- **Goal:** `ui/active_trader_panel.py`, `ibkr/market_depth.py` and `ibkr/order_book.py` are gone;
  the `DOM` button and every DOM/depth signal path is gone; the right dock hosts the Portfolio
  section only and still satisfies the surviving D18 visibility/clamp outcomes in full screen; and
  the app's only surviving order emitter (Portfolio Close / Close Group / Flatten All) is gated by
  the retained D26 machinery with a resolving `ref_price`.
- **Covers:** `AC-D41.1` (no DOM button, no Active Trader panel/ladder/ticket/title-bar button, no
  `active_trader` attribute), `AC-D41.2` (the `reqMktDepth`/`cancelMktDepth` and
  `updateMktDepth*` half), `AC-D41.3` (the three modules + `tests/test_market_depth.py`), the
  order-path half of `AC-D41.4`, and `AC-D41.7`.
- **Requirement/journey coverage:** Journey 36 steps 3 and 6 (postconditions 3 and 5);
  `### D41` DOM-ladder bullet, "Active Trader panel — whole" bullet, and the `ref_price` /
  D18 / D21.13 KEEP bullets (closing **DG71(1)** and **DG71(2)**, and **DG69**).
- **Depends on:** Phase 1 (it edits `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py` and
  `ibkr/subscription_manager.py`, all already touched there; phases are strictly ordered).
- **Decisions consumed:** `S5` (`ref_price` source + re-homed gates), `S6` (Portfolio-only dock
  model), `S9` (remaining bridge/client deletions), `S11` (test re-pointing).

**`touches_files` map — Phase 2** *(37 rows / 39 file entries; one task per file; within a wave
these sets are disjoint)*

| File | Action | Content |
|---|---|---|
| `ui/active_trader_panel.py` | **delete** | whole file (ladder, book, `OrderEntryWidget`, panel shell/header) |
| `ibkr/market_depth.py` | **delete** | whole file (DOM + D37 shared halves) |
| `ibkr/order_book.py` | **delete** | whole file (`OrderBook`, `Level`, `apply_operation`, `SIDE_*`) |
| `tests/test_market_depth.py` | **delete** | 182 lines, depth-only |
| `tests/test_order_entry_mkt.py`, `tests/test_order_entry_side.py` | **delete** | widget-scoped only (verified: they import only `ui.active_trader_panel` and guard no retained order path — FI-6) |
| `ui/main_window.py` | edit | `ActiveTraderPanel`/`on_depth_callback` import `:76`; `dom_btn` (`:249`–`:254`, `:321`, `:1883`–`:1884`); `self.active_trader` construction + container `:471`–`:483`; dock creation/title-bar/minimum/objectName `:485`–`:502` (**rename to `"Portfolio"`**); collapse wiring `:524`–`:533`; `watchlist_panel.set_depth_manager` `:610`; `b.update_mkt_depth` connect `:668`; `order_place_requested` connect `:693`; `_depth_req_id` + `_rebind_depth_req_id` `:714`, `:1437`–`:1439`; `_on_mkt_depth` + `_on_dom_toggled` + `_subscribe_dom` `:2984`–`:3040`; the DOM depth error branch `:1677`–`:1683`; `closeEvent`'s depth cancels `:3550`–`:3555`; `_on_order_place_requested`/`_place_order` `:3092`–`:3246` and every `active_trader.*` call (`:1705`, `:3033`, `:3108`, `:3121`, `:3132`, `:3152`, `:3164`, `:3176`, `:3207`, `:3243`, `:3388`); **every** remaining `"Active Trader"` literal/comment in the file (`:249`, `:253`, `:464`–`:468`, `:2459`, `:2982`, `:2985`–`:2986`); **new** `_ref_price_for`; **new** gates in `_close_position_by_id` `:3446`–`:3508`; dock re-shape per `S6` (`_compute_right_dock_collapsed_min_width` `:2455`, `_right_region_is_collapsed` `:2477`, `_sync_right_dock_collapse` `:2494`, `_on_right_panel_toggled` `:2487`, `RightDockContainer`/`_right_dock_layout` `:473`–`:487`, `:2510`) |
| `ibkr/bridge.py` | edit (delete-only) | `update_mkt_depth` `:52` |
| `ibkr/client.py` | edit (delete-only) | `updateMktDepth` `:391`–`:394`, `updateMktDepthL2` `:397`–`:406` |
| `ibkr/subscription_manager.py` | edit (delete-only) | `DEPTH` `:37` (**keep** `SubscriptionManager.has_subscription` `:81` — untagged, retained, and *not* D41's) |
| `ibkr/validation.py` | edit (**additive**) | one keyword `risk_reducing: bool = False`; skip the notional check when `True`; every structural check unchanged; the **module docstring `:5` is re-pointed** from "Wired at the top of `MainWindow._place_order`" to the retained emitter `MainWindow._close_position_by_id` (R6) |
| `ui/watchlist_panel.py` | edit (delete-only) | `_depth_manager` `:273`, `set_depth_manager` `:767`–`:769`, `on_depth_update` `:789`–`:793` |
| `data/models.py` | edit (delete-only) | `OrderBookLevel` `:105`–`:110` (zero references — inert; **FI-2**, accepted as an explicit scope close-out) |
| `ui/dock_layout.py` | edit (comments only) | module docstring `:4` and the constant comment `:29` "right (Active Trader) dock" → Portfolio-only; constants + `plan_dock_widths` **unchanged** (S6). *(Moved here from Phase 1: its only Active-Trader references belong to this phase's rename.)* |
| `tests/test_dock_d18_region.py` | edit (re-point) | `findChild(QDockWidget, "Active Trader")` `:107` + `objectName() == "Active Trader"` `:110` → `"Portfolio"`; `win.active_trader.width()` `:86`/`:140`/`:145`/`:163` → the Portfolio panel / the dock's widget; `win.right_dock_container` `:88`/`:173` → `win.right_dock.widget()`; docstring `:1`–`:13`; **keep** every surviving D18 visibility/clamp/equal-width assertion |
| `tests/test_right_dock_d21.py` | edit (re-point) | `from ui.active_trader_panel import ActiveTraderPanel` `:29` and every `win.active_trader.*` (`:64`, `:65`, `:69`, `:82`, `:83`, `:86`, `:87`, `:107`, `:159`, `:170`, `:189`, `:203`, `:234`, `:237`, `:249`, `:279`) → the single Portfolio section; the title-bar-text assertions `:57`/`:62`/`:67` (`at_btn.text() == "Active Trader"`) → the retained `summary_label` ("Account Summary") + the D21.13 strike-through on it; docstrings `:6`–`:7` |
| `tests/test_watchlist_nonregression_d22.py` | edit (re-point) | `window.active_trader.header_button` `:137` → the Portfolio `summary_label`; title-bar-text assertion `:142` (`== "Active Trader"`) → `"Account Summary"`; collapse/restore assertions `:148`–`:159` → the retained Portfolio header |
| `tests/test_dock_widths_d18.py` | edit (re-point) | `objectName() == "Active Trader"` `:177` → `"Portfolio"`; `win.active_trader.width()` `:277` and `win.active_trader.ladder.*` `:362`–`:363` → a wide widget inside the Portfolio section (AC-D18.6's "wide content cannot push the dock off-screen" probe survives); `win.right_dock_container.width()` `:279` → the dock's widget; `_RIGHT_PERSISTENCE_HINTS` `:72` drops the now-stale `"active_trader"` entry; docstring `:13`/`:17`; comment `:111`; **keep** every cap/min/chart-minimum assertion |
| `tests/test_dock_widths_d18_impl.py` | edit (re-point) | `win.active_trader.ladder.*` `:267`–`:268` → a wide widget inside the Portfolio section; `_RIGHT_PERSISTENCE_HINTS` `:48` drops `"active_trader"`; docstring `:9`; **keep** every `plan_dock_widths` invariant + the geometry assertions |
| `tests/test_dock_widths_d17.py` | edit (re-point) | `_RIGHT_DOCKS = ("Active Trader", "Portfolio")` `:37` (used `:73`) → `("Portfolio",)`; **keep** every ADR-17 clamp assertion |
| `tests/test_d10_d13_integration.py` | edit (1-line) | `_RIGHT_DOCKS` `:33`–`:35` (used `:53`) → `("Portfolio",)`; docstring `:17` (AR-D41-3) |
| `tests/test_watchlist_columns_d21.py` | edit (1-line) | `_RIGHT_DOCK_TITLES = ("Active Trader",)` `:308` (used `:322`) → `("Portfolio",)` |
| `tests/test_history_backfill_loadpath.py` | edit (1-line) | title-keyed hide `:165` → `("Portfolio",)` |
| `tests/test_d27_account_subs.py` | edit (1-line) | title-keyed hide `:27` → `("Portfolio",)` |
| `tests/test_d27_phantom_alarms.py` | edit (1-line) | title-keyed hide `:56` → `("Portfolio",)` |
| `tests/test_d27_stream_health.py` | edit (1-line) | title-keyed hide `:67` → `("Portfolio",)` |
| `tests/test_watchlist_d14_midrag.py` | edit (**R1.4**) | `_RIGHT_DOCKS = ("Active Trader",)` `:35` (used `:82`) + the comment `:33`–`:34` → `("Portfolio",)`. Without this the D14 gesture harness silently stops hiding the dock and runs against a different chart width |
| `tests/test_d27_position_prices.py` | edit (**R1.5**) | the title-keyed hide in `_make_window` `:29`–`:31` → `("Portfolio",)` |
| `tests/test_history_backfill.py` | edit (**R1.6**) | the title-keyed hide in the window factory `:198`–`:200` → `("Portfolio",)` |
| `tests/test_history_backfill_disconnect.py` | edit (**R1.7**) | the title-keyed hide in the window factory `:135`–`:137` → `("Portfolio",)` |
| `tests/test_crosshair_axis_lane.py` | edit (**R1.3**) | `region = docks["Active Trader"]` `:105` → `region = docks["Portfolio"]`; the now-**inverted** `assert "Portfolio" not in docks` `:106` → a positive assertion (`"Portfolio" in docks` **and** `"Active Trader" not in docks`), which is what D18 Phase 3's comment `:102`–`:104` was asserting in the old two-section world; docstring `:7` and the f-string at `:123` follow the rename. Without this the module fails with a deterministically red `KeyError` |
| `tests/test_d28_pacing.py` | edit (**R1.1**) | `test_place_order_defers_when_limiter_empty` `:117`–`:140` calls the **deleted** `win._place_order(...)` `:130` → re-point at the retained emitter: seed one `positions` row, keep `win._ibkr_connected = True` and the stubbed `placeOrder`, drive `win._close_position_by_id(<seeded id>)`, and keep the four D28.1 order-path guarantees (no immediate transmit, no GUI-thread sleep, a `pacing-limited` status message, exactly one deferred transmit after the bucket refills at `:137`). This is also the live proof of `S5`'s step-3 ordering (pacing after the gate, before `placeOrder`) |
| `tests/test_kill_switch.py` | edit (**R1.2**) | `test_bracket_place_registers_all_three_legs` `:77`–`:100` calls the **deleted** `win._place_order(order_type="BRACKET", …)` `:90` → re-point at the retained builders (`ibkr/orders.py::bracket_order` + `order_registry.register`), keeping the `IdManager` patch `:87`–`:89` so the legs are the reserved `1/2/3`, and keeping every assertion: all three legs registered at transmit time, ids `[1, 2, 3]`, parent `BUY`, both children `SELL` (`:93`–`:98`), and `_kill_switch` seeing the counts (the neighbouring `:63`–`:74`). This is **D26.8's only all-three-legs-at-transmit test** — it must not be deleted (`AC-D41.4`'s "retained machinery … exercised") |
| `tests/test_order_validation.py` | edit (re-point) | drop the two `_place_order` wiring tests (`:91`–`:107` refuses-invalid, `:109`–`?` transmits-valid); **keep** every pure-gate test incl. the notional-cap pair (`:128`); module docstring `:1` de-references `_place_order` |
| `tests/test_order_rejections.py` | edit (re-point) | keep the registry assertions; re-point the surfaced message from the removed ticket (`win.active_trader.order_entry.status_label.text()` `:46`) to `status_bar`; re-point `win._place_order(...)` `:85` at the retained close path |
| `tests/test_toolbar_scroll_d19.py`, `tests/test_toolbar_d20.py` | edit | drop `dom_btn` from `_CONTROL_NAMES` (`:42` / `:44`); re-check the geometry fixtures (AR-D41-4) |
| `tests/test_toolbar_d21.py` | edit | drop `dom_btn` from `_CHECKABLE_TOGGLES` `:152` |
| `tests/test_d27_reconnect.py` | edit (1 line) | the dock-title tuple `:163` → `("Portfolio",)`. **Only this line changes in this phase** — the depth-assertion drops are Phase 1's (see that row); the split is forced by the rename landing here |

**Phase-2 files explicitly checked and *not* changed** (listed so no worker "fixes" them):
`tests/test_order_builders.py` (`bracket_order` side-correctness — `AC-D41.4`'s retained-builder
evidence, untouched), `tests/test_sltp_honesty.py` (the SL/TP dialog discloses non-transmission;
the dialog itself is untouched), `tests/test_sltp_honesty.py`'s subject
`ui/stop_loss_target_dialog.py` (no `placeOrder` anywhere — verified), `tests/test_port_guard.py`,
`tests/test_id_manager.py`, `tests/test_d38_events_news.py` (Phase 1's only change is the R2
re-home), `tests/test_d39_burst_search.py` (same), `tests/test_db_schema.py` (Phase 3's).

### Phase 3 — Non-regression verification and the D41 guards

- **Goal:** the removals are **evidenced**, not asserted: automated guards prove the modules,
  identifiers, controls and requests are gone, the retained substrate/order machinery still works,
  and the whole offscreen suite is green.
- **Covers:** `AC-D41.3` (the scan half), `AC-D41.4` (substrate + retained machinery + resolving
  `ref_price`), `AC-D41.5`, `AC-D41.7` (measurable half), plus the Q49 drop verification.
- **Requirement/journey coverage:** Journey 36 steps 2, 4, 5.
- **Depends on:** Phases 1–2 (the guards cannot be green before both are complete).

**`touches_files` map — Phase 3** *(4 file entries)*

| File | Action | Content |
|---|---|---|
| `tests/test_d41_removal.py` | **new** | `AC-D41.1`/`AC-D41.3`/`AC-D41.5`: module-absence (`importlib.util.find_spec` `None` + source-path existence) for all 9 deleted modules and the 5 deleted suites; a **token scan** over `ui/`, `ibkr/`, `services/`, `data/`, `config/`, `tests/`, `main.py` (excluding `docs/`, `graphify-out/`, `__pycache__`) for the **complete** token set below; a **render probe** on a real offscreen `MainWindow` (no `Footprint`/`Classic`/`Tick count`/`Depth`/`IMB —`/`AUC —` button anywhere, no `DOM` button in the toolbar, `hasattr(win, "active_trader") is False`, no `footprint_*`/`depth_*`/`auction_*` attribute or signal on `ChartPanel`/`MainWindow`, while the zoom cluster, the `Volume` toggle and the Portfolio controls still render); a **request probe** (fake client records every call; drive `load_chart` + every remaining control + `_on_connected()` + a symbol switch ⇒ zero `reqMktDepth`/`cancelMktDepth`/`reqHistoricalTicks`/`reqTickByTickData` and no `reqMktData` generic-ticks string containing `"225"`, while the D38 S0 line and the watchlist market-data/RT lines still issue); and an app-start/chart smoke (`MainWindow()` → `load_chart` → bars render candles + volume) |
| `tests/test_d41_portfolio_dock.py` | **new** | `AC-D41.7`: exactly one right dock; `windowTitle()`/`objectName()` == `"Portfolio"`; its widget **is** `win.portfolio_panel`; no dock/widget titled `"Active Trader"` exists; **full-screen** visibility (non-zero width, on screen, not pushed past the window edge — the original D17/D18 symptom); `width <= right_dock_max_width(chart_area_after) + 1` and `>= RIGHT_DOCK_MIN_WIDTH`; the watchlist/chart minimums still hold (pure `plan_dock_widths` invariants re-asserted); clicking `portfolio_panel.summary_label` collapses to the single-button strip (`_right_dock_collapsed_min_width`) and the chart reclaims the width, clicking again restores; no **new** `QSettings` key is written for the right dock. Its `"Active Trader"` occurrences are **negative assertions only** (allow-listed in the token scan, see below) |
| `tests/test_d41_retained_order_path.py` | **new** | `AC-D41.4`: `_ref_price_for` resolves from `_symbol_last_prices` (fed by the watchlist sink **and** by a session's aggregated bar) and returns `None` for an unknown symbol; a **disconnected** close refuses and never calls `placeOrder`; an **invalid** close (empty symbol / zero qty) refuses; a **valid** close with a >USD 25,000 notional transmits **exactly once** (the risk-reducing carve-out) while `validate_order` on the equivalent risk-increasing call is still rejected; the kill-switch/order-ID/port-check modules import and their existing suites stay untouched |
| `tests/test_db_schema.py` | edit (**add**) | a fresh `DB()` has **no** `footprint_cache` table, and a legacy DB pre-seeded with the old DDL + a row has it **dropped** after `DB()` init, while `volume_baseline` + `yfinance_events_cache` survive (Q49/A69/DG70); the existing `EXPECTED_TABLES`/`_init_schema`-once assertions stay |

**The removal guard's token set (widened per R3).** `tests/test_d41_removal.py` scans for **all** of:

- *Deleted modules/classes:* `FootprintItem`, `FootprintService`, `FootprintCache`, `TickHistoryManager`,
  `DepthHeatmapItem`, `DepthHeatmapService`, `MarketDepthManager`, `OrderBook`, `OrderBookLevel`,
  `LadderTable`, `BookTable`, `ActiveTraderPanel`, `OrderEntryWidget`, `RightDockContainer`.
- *Deleted members:* `is_cacheable`, `apply_operation`, `active_feed_count`, `resolve_footprint_contract`,
  `refresh_footprint`, `_fp_` , `_fp_host_managers`, `_on_fp_`, `bind_d37_session`, `unbind_d37_session`,
  `set_depth_state`, `update_auction_chip`, `depth_enabled`, `depth_state_changed`, `ensure_depth_subscribed`,
  `release_depth`, `cancel_depth`, `reissue_depth`, `rebind_depth_req_id`, `on_depth_update`, `on_depth_error`,
  `depth_imbalance`, `_depth_state`, `_depth_refresh_timer`, `depth_req_id`, `_depth_req_id`, `_depth_manager`,
  `set_depth_manager`, `footprint_enable`, `footprint_resync`, `footprint_disable`, `auction_state`,
  `_auction`, `_guard_depth_budget`, `DEPTH_FEED_CAP`, `active_trader`, `dom_btn`,
  `_subscribe_dom`, `_on_dom_toggled`, `_on_mkt_depth`, `_place_order`, `_on_order_place_requested`,
  `right_dock_container`, `_right_dock_layout`.
- *Deleted integration surface:* `historical_ticks_`, `historicalTicks`, `update_mkt_depth`,
  `updateMktDepth`, `reqMktDepth`, `cancelMktDepth`, `reqHistoricalTicks`, `reqTickByTickData`,
  `DEPTH_HEATMAP`, `DEPTH`, and the generic-tick literal `"225"`.
- *The removed dock identifier:* the **quoted literal** `"Active Trader"`.

**Documented allow-list** (each with the reason recorded in the guard's docstring, so a reader can
tell an intentional survivor from a miss):
1. `footprint_cache_key` — **kept verbatim** by `AC-D41.4`/DG67 (D39's burst-baseline key; S10, FI-5).
2. `queue_depth` — `NewsManager`'s retained queue depth (`tests/test_d38_events_news.py:158`).
3. `has_subscription` — **scoped, not bare**: `MarketDepthManager.has_subscription`
   (`ibkr/market_depth.py:45`, deleted) is covered by the `MarketDepthManager` module-absence check,
   while `SubscriptionManager.has_subscription` (`ibkr/subscription_manager.py:81`) is **retained**
   and is not D41's to remove. The guard therefore scans the **qualified** forms
   (`depth_manager.has_subscription`, `active_trader…`) rather than the bare token, and the bare
   token is allowed **only** in `ibkr/subscription_manager.py`.
4. `"Active Trader"` — allowed **only** in the guard files themselves
   (`tests/test_d41_removal.py`, `tests/test_d41_portfolio_dock.py`) where it appears in negative
   assertions; the guard excludes itself from the scan and allow-lists the dock suite's literal.
   Every other token above **is** scanned in both files.
5. `DEPTH`/`depth` as **substrings of retained names** are matched by whole-token boundaries only
   (`depth_state_changed`, `DEPTH_FEED_CAP`, …), so `NewsManager.queue_depth` and `md_line_guard`'s
   own `depth`-free code are not false positives.

**The guard must be red before the change.** The Phase-3 task's own acceptance includes running it
against the pre-removal tree (or against a stash of the removals) to prove every token it claims
actually fires; a token that never matches pre-D41 is struck rather than left as decoration.

**Consumer count for the dock rename (R1).** Verified in the tree: **15** test files key on the
right dock's `windowTitle()`/`objectName()` **plus 2** files assert its title-bar **text** = **17**
files total; the Validator's enumeration of 14 keyed consumers is complete except for
`tests/test_dock_widths_d18.py:177` (an `objectName()` assertion), which was already inside the
Phase-2 map — hence 15. All 17 are enumerated with their line reads and required change in the
two Phase-2 rows above and in the two adjacent rows (`test_dock_d18_region.py`,
`test_crosshair_axis_lane.py`). No title-keyed consumer is left unlisted, so AR-D41-3's "a stale
tuple is then detectable, not silent" is now actually true.

---

## Sequencing constraint and wave shape

- **Within a phase:** one task per file. Two tasks with overlapping `touches_files` must never be
  `in_progress` in the same wave — so the partition above *is* the parallelism plan.
  With `max_parallel_tasks` default **6**, Phase 1 (**20** file entries) and Phase 2 (**39** file
  entries) each run in a few rolling waves; the long pole is `ui/main_window.py`, which is therefore
  **one task per phase** (never split across workers in the same wave). The two-phase entries for
  `tests/test_d27_reconnect.py` are in **different** phases and therefore never share a wave.
- **Across phases:** strictly sequential — Phase 2 opens only after Phase 1's wave is consolidated,
  Phase 3 only after Phase 2's. The shared files are `ui/chart_panel.py`, `ui/ticker_session.py`,
  `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`
  (Phases 1 and 2) and `tests/test_d27_reconnect.py` (Phases 1 and 2, disjoint lines); this is the
  only ordering constraint that matters.
- **Deletions are safe to pair** with any edit task: deleting a module whose last importer is
  removed in the same wave is fine because the *edit* task owns the importer's file, and no other
  task imports the deleted module. Where a deletion and the edit that removes its last reference
  land in the same wave, the edit must land (`build_wave.py` re-runs the wave until the frontier
  drains; a `ModuleNotFoundError` from a partially-applied wave is expected and resolves on the
  next pass — run the phase's own test selection once the wave is consolidated, not per task).
- **Per-task verification:** each task carries its own focused check (the Task Manager's call).
  The **phase-level** acceptance evidence is: Phase 1 — `test_d27_reconnect` + the D38/D39 suites
  **including the two R2 re-homes** green; Phase 2 — the re-pointed dock/toolbar/order suites
  **plus `test_d28_pacing`, `test_kill_switch`, `test_crosshair_axis_lane` and the four
  dock-hide-helper suites** green; Phase 3 — the three new suites + the extended
  `test_db_schema` + the full offscreen run.

---

## Requirements → architecture → phase traceability

| Requirement / journey | Architecture section (proposal) | Phase |
|---|---|---|
| `AC-D41.1` — no D36/D37/DOM-ladder/Active-Trader/order-entry control renders | S3, S6, S9, S11; Components "Removed" (rows 1–4); AR-D41-8 | 1 (footprint/depth controls) + 2 (DOM/Active Trader/Portfolio-only) |
| `AC-D41.2` — no D36/D37/DOM-ladder request is ever issued (`reqHistoricalTicks`, `reqTickByTickData`, `reqMktDepth`/`cancelMktDepth`, generic `"225"`) | S8, S9; Integration Points (rows 1–5) | 1 (ticks/heatmap/`"225"`) + 2 (depth/ladder) |
| `AC-D41.3` — the 9 modules + 3 suites are gone, no dangling import/reference | S3, S10, S11; AR-D41-2, AR-D41-8, AR-D41-12 | 1 (D36/D37 modules) + 2 (Active Trader/depth modules) + 3 (scan guard, **token set widened per R3**) |
| `AC-D41.4` — D38/D39/D27–D28 substrate intact **and** the retained order machinery + resolving `ref_price` | S4, S5, S8, S10; Components "Retained unchanged"; AR-D41-6, AR-D41-7 | 1 (substrate preserved + **the two KEEP-coverage re-homes**: `footprint_cache_key` → `tests/test_d39_burst_search.py`, `md_line_guard.assess` → `tests/test_d38_events_news.py`, **R2**) + 2 (re-homed gates; `bracket_order` all-three-legs kept via `tests/test_kill_switch.py`, **R1.2**; the retained close-path deferral kept via `tests/test_d28_pacing.py`, **R1.1**) + 3 (evidence) |
| `AC-D41.5` — app starts and charts; full offscreen suite green | S12; AR-D41-10..12 | 3 (with 1–2 as prerequisites; the three deterministically-red suites of R1 are re-pointed in 1–2 rather than left to fail here) |
| `AC-D41.6` — `### D36`/`### D37` + `AC-D36.*`/`AC-D37.*` carry `SUPERSEDED BY D41`, D18/D21.13 notes, tech-stack sentence intact | Requirements-owned (already present at `requirements.md:69`, `:83`, `:2074`, `:2088`, `:3075`, `:3116`) — **no code work**, see AP-5 / FI-3 | — (Requirements) |
| `AC-D41.7` — right dock is Portfolio-only, visible in full screen, non-zero width, clamped; re-derived cap/header | S6; Integration Points (none new); AR-D41-3 | 2 (implementation + **all 17 title/title-bar consumers**, R1) + 3 (evidence) |
| Journey 36 (all 6 steps + edge cases) | Summary; Components; Non-Functional Approach | 1, 2, 3 as above |
| **D1–D35 and D38–D40 are not reopened** — every one of their criteria is unchanged-by-construction and re-verified as the non-regression contract | Components "Retained unchanged"/"Not in D41"; Non-Functional Approach; AR-D41-1/2/9 | 1, 2 (preservation) + 3 (full-suite evidence) |
| Q49 / A69 / DG70 — persisted footprint data deleted | S7; Data Model row 1 | 1 |
| Q48 / DG69 / DG66 — ladder + whole panel removed; ESC-035/039/040 moot | S3, S9; Components "Removed" row 3 | 2 |
| DG71(1) — retained `ref_price` source | S4 | 2 |
| DG71(2) — Portfolio-only dock cap/header re-derived | S6 | 2 |
| DG67 — surgical removal (KEEP list) | S8, S10, Components "Retained unchanged" | 1, 2 |
| D26 safety standing; D18/`AC-D18.3`/D21.13 superseded-but-surviving outcomes | S5, S6 | 2 |

---

## Assumptions

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A71`).

- **AP-1 (phase ordering).** Phases 1–3 are strictly sequential: Phase 2 opens only after Phase 1's
  wave is consolidated and Phase 3 only after Phase 2's. Reason: six shared files receive edits in
  more than one phase, and `build_wave.py`'s non-overlap rule is per *wave*, not per batch.
- **AP-2 (wave shape).** Build runs `build_wave.py` with `max_parallel_tasks` default 6; the
  per-phase file partition above is the `touches_files` map, one task per file, and the long-pole
  `ui/main_window.py` stays a single task per phase.
- **AP-3 (test invocation).** The suite is run as
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale
  shebang); any non-pytest probe that can reach a DB-writing path exports `DB_PATH` to a temp file
  first (ESC-043; `tests/conftest.py` already does this for pytest).
- **AP-4 (no persisted-state migration beyond the table drop).** The right dock's width and collapse
  state are in-memory only (A36 — no `QSettings` key), and the DOM/depth/footprint toggles were
  never persisted. The **only** persisted artefact that changes is the `footprint_cache` table (S7).
  Consequently no settings-key cleanup task exists, and the new dock suite asserts no new key is
  written (the existing `_RIGHT_PERSISTENCE_HINTS` scan stays, minus its stale `"active_trader"`
  hint).
- **AP-5 (documentation ownership).** `AC-D41.6`'s markdown-history markers are **Requirements-owned**
  and already applied; Build must not edit `requirements.md`, `docs/architecture.md`, `docs/plan.md`
  or `docs/plan_notes.md`. `usage.md`'s test-count sentence (DOC-1) will need a docs-only refresh
  after the suite size drops — owner/Analyst follow-up, not a Build task.
- **AP-6 (test count moves down).** Three suites are deleted and two more shrink, so the suite total
  **falls**; `AC-D41.5` requires green, not parity of counts. Any docs figure quoting a total must be
  re-measured rather than assumed (DOC-1).
- **AP-7 (escalations are not D41's work).** **14** entries are `open` today; ESC-035/039/040 (all
  `should-fix`) go moot by removal (DG66), leaving **11** open and untouched —
  ESC-032/033/034/036/037/038/041/042/043/044/045, all BUILD/REQUIREMENTS-owned (ESC-038 is
  REQUIREMENTS-routed and D41-neutral). Flipping the three moot ones to `addressed` is the **Code
  Reviewer's** action after re-verification (DG66) — not Build's, and not a task in these phases.
- **AP-8 (clean tree for verification).** Phase 3 runs from a clean tree so orphaned `__pycache__`
  for deleted modules cannot confuse the module-absence guards (AR-D41-12; DOC-3/ESC-001 precedent).
- **AP-9 (`OrderBookLevel` removal is inert).** `data/models.py::OrderBookLevel` has **zero**
  references in the tree today, so removing it cannot change behaviour; it is included because it is
  the depth feature's model (see FI-2).
- **AP-10 (KEEP coverage is re-homed, not dropped).** `footprint_cache_key` and
  `md_line_guard.assess` each have exactly **one** test today and both live in suites D41 deletes, so
  their assertions are **moved** in the same phase as the deletion (R2): the key rule into
  `tests/test_d39_burst_search.py` (D39 is the surviving consumer), the guard thresholds into
  `tests/test_d38_events_news.py` (the D38 S0 lines are the surviving caller). `AC-D41.4`'s "remain
  and remain exercised by their tests" is then literally true.
- **AP-11 (per-phase green).** Each phase's consolidated state is green on its own suite selection,
  not merely at the end of Phase 3. This is why the depth assertions leave `tests/test_d27_reconnect.py`
  in Phase 1 (their subjects go there) while its one dock-title line leaves in Phase 2 (the rename
  lands there), and why R1's three deterministically-red suites are re-pointed inside Phases 1–2.

---

## Flagged Issues

Surfaced for the Validator's ruling (which turns them into `plan_notes.md` if they stand). The
Validator's round-1 dispositions are **folded in** below and the proposals are revised to match; FIs
1–6 are recorded here in their post-ruling form so the canonical files can be written from this text
without re-litigating anything.

- **FI-1 — `AC-D41.4`'s "the retained order paths … still build and **validate** orders with a
  resolving `ref_price`" is not what the code does, and satisfying it verbatim needs a decision
  inside a removal.** Verified 2026-10-15: `validate_order()` has exactly one production call site
  (`ui/main_window.py:3112`, inside the ticket-only `_place_order`), while the retained
  Close / Close Group / Flatten All path (`_close_position_by_id`, `:3446`) builds its MKT order and
  calls `placeOrder` with **no** validation and **no** disconnected guard; the SL/TP dialogs place
  **no** orders at all — evidenced by `ui/stop_loss_target_dialog.py` containing **no** `placeOrder`
  anywhere (verified repo-wide), with `tests/test_sltp_honesty.py` asserting only the dialog's
  **disclosure label text** (`:16`, `:24`), not non-transmission. So if D41 is a pure removal, the
  D26 gate and the D26.9 disconnected guard become production-dead, `ref_price` loses its only
  consumer, and `AC-D41.4`'s `ref_price` clause is unmet. **Plan's resolution (S4 + S5):** re-home
  both gates onto `_close_position_by_id`, with one additive keyword
  `validate_order(..., risk_reducing=False)` that skips the notional cap for closes so a >USD 25,000
  position can still be flattened. **Disposition (Validator, round 1): RATIFIED as reading (a), and
  NON-BLOCKING** — the re-homing is exactly what `AC-D41.4` and the KEEP list demand, it is not
  scope addition and not an invention, the AC's wording is ambiguous and its "SL/TP dialogs" limb is
  **vacuous**, and `DG71`/`A71` bless both the source and the mechanism. Recorded as **`RG-D41-1`**
  in `docs/plan_notes.md` (`Status: open`, **`Escalation: none`**) — **not** escalated to
  Requirements and no Analyst action is required. The proposal keeps S4+S5 unchanged.
- **FI-2 — `OrderBookLevel` is not in D41's named tokens but is the removed feature's model.**
  `data/models.py::OrderBookLevel` (`:105`–`:110`) is referenced by **nothing** in the tree today
  (verified repo-wide). D41's scope text ("remove … and all associated code") covers it, but
  `AC-D41.3`'s token list does not name it, so a strict reader could call its removal out of scope.
  **Disposition (Validator, round 1): ACCEPTED** — within "all associated code", and inert. **Plan's
  resolution:** remove it in Phase 2, recorded as an **explicit scope close-out** (a deliberate,
  named inclusion under `### D41`'s "all associated code" — not an undeclared extra), and the removal
  guard's token set names `OrderBookLevel` so the closure is machine-checked.
- **FI-3 — D41 must not be credited with the wide-candle / volume-overlap defect (DG68 is still
  open; the investigation proves a different cause).** ESC-041 (`escalations.json`, **`blocking`**,
  routed BUILD; corroborated by `docs/orchestrator_state.json.blocking_bugs`) measures the overlap as
  the D6 4-device-pixel floor exceeding the inter-bar pitch in `ui/candlestick_item.py:122`–`:138`
  (the `min_w = 2.0 / px_per_sec` floor) plus the chart's volume width path
  (`ui/chart_panel.py:1688`–`:1690`, `w_vol = self._clamp_half_width(...)`). `docs/code_review/
  candle_overlap_investigation.md` is **concluded** and **rules the footprint overlay OUT**
  (§1, §2 lead 3, §4): reproducing with **no** footprint active still merges the price and volume
  panes. DG68 records the in-flight investigation as unresolved. **Disposition (Validator, round 1):
  ACCEPTED** with this labelling/severity correction. **Plan's resolution:** D41's phases **do not
  touch** `ui/candlestick_item.py` or the volume-width math, and no task may claim the symptom as
  fixed; ESC-041 stays **blocking** and BUILD-owned; the canonical `AC-D41.1`/`AC-D41.5` treatment
  records that D41 removes the footprint render layers but resolves **no** width defect, and DG68 is
  closed as "not resolved by D41".
- **FI-4 — the requirements do not say whether the right dock's stable title/`objectName` (used by
  title-keyed lookups in the test tree) may change.** `AC-D41.1` bans every Active-Trader
  *affordance*; `AC-D41.7` requires the header to be re-derived; neither addresses the dock's
  identifier, and the repo carries a recorded trap that dock lookups are `windowTitle()`/
  `objectName`-keyed. **Plan's resolution (S6):** rename the single dock to `"Portfolio"` (honest
  name; leaving `"Active Trader"` as a live identifier contradicts the removal) **and** update every
  title/title-bar consumer in the same phase — **15** `windowTitle()`/`objectName()` consumers +
  **2** title-bar-text assertion files, all enumerated in the Phase-2 map with their line reads — with
  a new guard asserting exactly one right dock titled `"Portfolio"` and no `"Active Trader"`
  dock/widget (neutralising the D19 masking risk). The alternative — keep the old title to avoid
  touching those files — is recorded and rejected. **Disposition (Validator, round 1): RATIFIED,
  conditional on R1's complete consumer list** — which this revision now supplies (the round-1 list
  said "8"/"9"; the verified count is 15 + 2, and
  `tests/test_dock_widths_d18.py:177` was missing from the round-1 enumeration).
- **FI-5 — `footprint_cache_key`'s name survives D41 and will read as a leftover.**
  `AC-D41.4`/DG67 require keeping `ibkr/contracts.py::footprint_cache_key` (D39's burst-baseline key),
  so a footprint-named symbol remains after the footprint is gone. Renaming is recorded as FS17 and
  is **not** part of D41. **Disposition (Validator, round 1): ACCEPTED** — the symbol is kept
  **verbatim**, the rename stays **FS17**, out of D41. **Plan's resolution:** the smell + the
  deliberate non-rename are recorded (so a later reader does not "clean it up" during D41), the
  removal guard **allow-lists** the token as an intentional survivor, and **R2** re-homes its only
  test into `tests/test_d39_burst_search.py` so "kept" also means "still exercised".
- **FI-6 — the removal of `test_order_entry_mkt.py` / `test_order_entry_side.py` deletes D26.4/D26.6
  coverage outright.** The requirements say the order-entry tests "must not be deleted wholesale
  **if** they also guard the retained order paths" — verified 2026-10-15: both files import **only**
  `ui.active_trader_panel` (`OrderEntryWidget`/`ActiveTraderPanel`) and touch no `MainWindow` and no
  retained machinery, so deletion is the correct reading; their *intent* (a side is explicit; qty
  comes from the input; nothing transmits on a bad qty) is carried over to the retained path by
  `tests/test_d41_retained_order_path.py`, and the retained builders keep their own coverage in
  `tests/test_order_builders.py` + the re-pointed `tests/test_kill_switch.py`. **Disposition
  (Validator, round 1): ACCEPTED** — both widgets' suites import only `ui.active_trader_panel`, so
  deletion is right and `AC-D41.4`'s "exercised" clause is met by the re-pointed suites + the new
  ones.

---

## Review-response record (R1–R6) — round 1 of 3, `Status: CHANGES_REQUIRED`

| # | Required change | Where it is addressed |
|---|---|---|
| **R1.1** | `tests/test_d28_pacing.py` (`:130` calls the deleted `_place_order`) | Phase 2 row — re-pointed at the retained emitter with a seeded `positions` row; D28.1's deferral guarantee kept |
| **R1.2** | `tests/test_kill_switch.py` (`:90`, D26.8's only all-three-legs test) | Phase 2 row — re-pointed at `order_registry.bracket_order` + `register`; the assertion is kept, not deleted |
| **R1.3** | `tests/test_crosshair_axis_lane.py` (`:105` `KeyError`, `:106` inverted assertion) | Phase 2 row — `docks["Portfolio"]`, inversion replaced by a positive assertion |
| **R1.4–R1.7** | Four silently-masked dock-hide helpers: `test_watchlist_d14_midrag.py:35`, `test_d27_position_prices.py:30`, `test_history_backfill.py:199`, `test_history_backfill_disconnect.py:136` | Four Phase-2 rows, each → `("Portfolio",)` |
| **R1 (count)** | "8/9" consumers → the verified number | 15 `windowTitle()`/`objectName()` consumers + 2 title-bar-text files = **17** test files, all enumerated with line reads + required change (the Validator's 14 is complete except `test_dock_widths_d18.py:177`, already inside the map) |
| **R2** | `footprint_cache_key` and `md_line_guard.assess` lose their only tests | New Phase-1 rows: `tests/test_d39_burst_search.py` (key rollover, moved verbatim from `test_d36_footprint.py:389`–`:395`) and `tests/test_d38_events_news.py` (guard thresholds, moved from `test_d37_microstructure.py:336`–`:344`, re-purposed to the S0 purpose); both recorded in the `AC-D41.4` traceability row and AP-10 |
| **R3** | Widen `tests/test_d41_removal.py`'s token scan | The full widened set (incl. `_place_order`, `_on_order_place_requested`, `_on_dom_toggled`, `_on_mkt_depth`, `_rebind_depth_req_id`, `active_feed_count`, `has_subscription` (scoped), `apply_operation`, `is_cacheable`, `LadderTable`, `BookTable`, `right_dock_container`, `_right_dock_layout`, `RightDockContainer`, and the literal `"Active Trader"`) with a five-item documented allow-list, plus the pre-change red-proof requirement |
| **R4** | FI-1/FI-3 evidence + ESC-041 severity | FI-1 now cites `ui/stop_loss_target_dialog.py` (no `placeOrder`) and `tests/test_sltp_honesty.py`'s label-only assertion; FI-3 cites `docs/code_review/candle_overlap_investigation.md` + `ui/candlestick_item.py:122`–`:138` / `ui/chart_panel.py:1688`–`:1690` and records ESC-041 as **blocking** |
| **R5** | Internal cross-reference corrections | `S19` → **`S5`** (`architecture_proposal.md:93`); `OrderBookLevel` attributed to **FI-2** (not FI-1) in Components and Data Model; AR-D41-9's wide-candle pointer → **FI-3**; ESC-041 severity → **blocking**; "14 escalations stay open" → **11** (AP-7 and the header); file counts → **20** (Phase 1) / **39** (Phase 2); `ui/dock_layout.py` moved from Phase 1 to Phase 2; the maps pair each line range with its symbol (DG56 convention) |
| **R6** | `ibkr/validation.py:5`'s `_place_order` docstring reference | Phase 2 `ibkr/validation.py` row — the module docstring is re-pointed to `MainWindow._close_position_by_id`; S5's decision text names the docstring sentence explicitly |

---

## Handoff

Phase order: **Phase 1 → Phase 2 → Phase 3**, strictly sequential, then Code Reviewer verification
(which also re-verifies and closes ESC-035/039/040 as moot per DG66).

Status: READY_FOR_VALIDATION
