# Architecture Proposal — NDThinkChart Batch 20 (**D45**): the News Digest dock (+ the `View` menubar), the Trade Context Menu, the **Kill switch** and the **SL/TP dialog** are removed — the app has **zero order interaction** afterwards

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical architecture —
> `docs/architecture.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/plan_proposal.md` (phases, waves, per-file map, test book, residue verification, assumptions,
> correction record). Module index: `docs/codebase-map.md` (refreshed for this batch,
> `update_codebase_map.py` re-run 2026-10-25).
>
> **Run shape:** **legacy single-scope** — the invocation preamble carries **no `phase: P<n>`**, so these are
> the unsuffixed proposal files and the D45 increment merges into the cumulative canonical
> `docs/architecture.md` / `docs/plan.md` as a `## D45 increment` section (the D16–D44 precedent).
>
> **This file replaces the stale D44 draft WHOLESALE** (the previous contents of
> `docs/architecture_proposal.md` were the D44 proposal). **D44 is delivered** — committed at `c702be9`, suite
> green, review complete. A previous D45 Plan run was cancelled **after** refreshing `docs/codebase-map.md`;
> its never-activated draft is **superseded whole** by this document, so **every identifier it minted is
> re-minted here**: this document owns `S29`–`S38` (D44 owned `S14`–`S28`), and the cancelled draft's
> `FI-D45-1`, `S32` and `AP-D45-*` numbers **carry no authority** — in particular `FI-D45-1` ("`StopLossTargetDialog`
> has no in-app entry point") is **moot**: the dialog itself is now **deleted** (`AC-D45.6`). This is
> **Revision 2** (round 2 of 3) — revised against the Validator's `CHANGES_REQUIRED` on R1–R4; the revision
> notes are at the top of `docs/plan_proposal.md`. R1/R2 change test-book **wave membership** only, R3 makes
> the residue instrument's claim true, R4 reconciles this document's `tests/test_dock_d18_region.py` row with
> the plan (the loop is **deleted**, not shrunk to three — `RG-D45-1`). **No architectural decision changed**;
> `S29`–`S38` stand as validated.
>
> **Scope: D45 only** (Batch 20, owner-requested 2026-10-25 **and its later extension the same day**). The
> requirements were **substantively** revised by the extension (kill switch + SL/TP dialog move from *retained*
> to *removed*, `AC-D45.6` inverted, `AC-D45.10` added, A82/A83 reversed) — so the standing
> `plan_proposal` staleness flag is **not** benign here (memory 2026-10-23); both proposals are rewritten, not
> amended.
>
> **Sources of record** (`docs/requirements/requirements.md`, `Status: READY_FOR_PLAN`, 0 open questions):
> **`### D45`** `:4100`–`:4481` (three removal groups, "Scope — KEEP", six owner-accepted consequences,
> requirements D45.1–D45.6, `AC-D45.1`–`AC-D45.10` `:4282`–`:4370`, the supersession/revision record
> `:4371`–`:4416`, assumptions A79–A90 `:4417`–`:4460`, correction record `:4461`–`:4481`);
> **Journey 38** `:1086`–`:1119`; **R68–R75** `:4699`–`:4706`; `design_gaps.md` **DG75** `:1189`–`:1212`,
> **DG76** `:1214`–`:1229`, **DG77** `:1231`–`:1260`.
> **Baseline:** `main` @ **`c702be9`** (2026-10-23, "Stop tracking orchestrator runtime state"); the tree carries
> only the requirements/design-gaps/codebase-map edits of this batch.
>
> **Escalation state at planning time.** **No `PLAN`-routed escalation is open** — `docs/code_review/escalations.json`
> currently holds **no `status: "open"` entry at all** (re-verified 2026-10-25). `docs/plan_review.md` is the
> **APPROVED** D44 cycle, so this is a normal forward increment. `docs/tasks/task_manager_notes.md` carries no
> `ESCALATED_TO_PLAN` item. **DG76 is the one open Plan-level question and this document decides it (§ `S29`,
> DG76 resolution below); DG77 is resolved by the named adjustments in `docs/plan_proposal.md`.**

**The one workstream — subtractive, three groups, one invariant.** D45 removes **all** order *interaction* from a
read-only observation terminal: the news half of D38 (Group A), the whole in-app close/order path plus the
SL/TP setter chain (Group B), and the cancel path (Group C, the owner's later extension). The invariant that
binds them is **reachability, not file count** (`D45.2`, `AC-D45.4`, `AC-D45.6`): after D45 **no `ui/` module
can call `placeOrder`, `cancelOrder` or `reqGlobalCancel`**, and no `ui/` module imports the three deleted
feature modules or the deleted validation module. Two owner decisions must survive the deletion and are the
main risk in the change: the **dividend S0 `"456"` substrate** (R68 — it shares the `s0_register` mechanism
with the news `"292"` line) and the **stop/target storage** (A87 — the DB columns, model fields and the
position upsert are **not** touched; only the two display columns and every setter go). Nothing is added: no
replacement close UI, no replacement cancel control, no read-only SL/TP fallback, no schema migration.

---

## Relationship to prior increments

Every decision below carries exactly one relationship label. `[revises …]` names the earlier decision it
changes; an unlabelled decision would be read as new.

| # | Decision | Relationship |
|---|---|---|
| **S29** | **`ibkr/orders.py` is retained, unreferenced by any transmit path, with a module-docstring note.** The `AC-D45.4` measure is **reachability and zero transmits**, not file existence; and the module is **not** in fact orphaned (see § Codebase Summary) — `ui/main_window.py` imports its `orders` singleton as `order_registry` for the **retained, inert inbound observers** (`A90`). Deleting it would force those observers to be rewritten (registry-safe) for **zero** reachability gain and would delete the only unit coverage the builders keep (`tests/test_order_builders.py`). | **`[new in D45]`** — settles DG76 option (a). Supersedes the D41 "Scope — KEEP / retained order machinery" bullet's *intent* (the machinery is no longer retained **for a purpose**) without reversing A80's default. |
| **S30** | **Sever the transmit path at its single call site.** `MainWindow._close_position_by_id` is the **only** `placeOrder` call site in the tree; it goes with `_on_portfolio_close_position`, `_on_portfolio_close_group`, `_on_portfolio_flatten_all`, `_ref_price_for` and the `validate_order` import, and `ibkr/validation.py` is deleted. `placeOrder` itself is **ibapi's inherited `EClient.placeOrder`** — it is not defined in this repo at all, so "removing the transmit" means *removing every written caller*, never editing `ibkr/client.py`. | **`[revises D41: the retained close/flatten order path]`** — D41 kept this path (`validate_order` gate, order-path pacing token, `ref_price`, the D28.6 contract rebuild) for Portfolio closes; D45 deletes it whole. `ref_price`/`_ref_price_for` become source-less and go (`AC-D41.4`'s `ref_price` clause is **moot**). |
| **S31** | **Delete the cancel capability completely, and add none back.** `kill_btn` (+ the `QLabel("|")` separator before it), `_on_kill_switch_clicked`, `_kill_switch` (the `reqGlobalCancel()` call, the per-ID `cancelOrder()` loop, the pre/post status-bar counts and the local `order_registry.update_status(…, "Cancelled")` marking) are deleted. `reqGlobalCancel`/`cancelOrder` then have **no call site anywhere in the app**, and **no** teardown / `closeEvent` / disconnect / reconnect path may acquire one. Cancel surface after D45 = **TWS**. | **`[revises D26.8: the kill switch / AC-D26.8]`** — superseded in full (A88). Reverses A82 (recorded as a reversal, not silently dropped). |
| **S32** | **Delete the SL/TP setter chain end-to-end.** The dialog module, its `confirmed` signal, the panel's `position_sltp_changed`/`group_sltp_changed`, `_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`, and `MainWindow._on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed` (with their `UPDATE positions SET stop_loss=…` / `UPDATE trade_groups SET stop_loss=…` statements) are deleted. **No** read-only fallback dialog (the owner declined replacement UI twice). | **`[revises D26.3: the SL/TP dialog]`** — `AC-D26.3`'s labelling branch has no dialog, so it is **moot** (A89). Reverses A83. |
| **S33** | **Portfolio becomes a view-only 8-column render.** `Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`; the `Stop`/`Target` header, value and alignment slots go; the right-aligned index set becomes `(1, 2, 4, 5)`; the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording is corrected. Storage is **untouched**: the `positions`/`trade_groups` `stop_loss`/`take_profit` columns, the `Position`/`TradeGroup` fields and the `_upsert_position` round-trip stay; **no migration, no data deletion**; legacy values are simply not settable and not displayed. | **`[revises D41: the Portfolio section's close/flatten/SL-TP controls]`** — `AC-D41.1`'s Portfolio clause becomes "renders view-only"; the D18 width model (`AC-D18.6`, `RIGHT_DOCK_MIN_WIDTH = 200`) is **re-derived, not superseded** — the table only demands *less* width. Storage retention is `[extends D27: position/trade-group SL/TP persistence]` unchanged. |
| **S34** | **Remove the digest half of D38 and nothing more.** Delete `ui/news_digest_dock`, `ibkr/news`, the `View` menubar (`menuBar()`/`view_menu`/`_on_news_digest_visibility`/`self.news_digest_dock`/the `Ctrl+Shift+N` action), the `NewsManager` use, the `b.tick_news` connection and `_on_s0_tick_news`, and the digest-only session plumbing: the news `"292"` S0 registration, `on_s0_tick_news`, `add_news_push_listener` / `remove_news_push_listener`, and the digest-only `set_s0_headless` / `_s0_headless` flag **including the two `or self._s0_headless` clauses in the S0 line-build paths**. **No menubar replaces the `View` menu** (A86). The dividend substrate (`"456"`, tick 59, `_dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, the marker overlay, the yfinance provider) is **untouched**. | **`[revises D38: the news digest]`** — `AC-D38.2`/`AC-D38.3` **superseded**, `AC-D38.6` revised to the surviving half (A79). `[extends D38]` for the dividend half, which stays byte-for-byte. A86's "no menubar" is new and follows from the section (the app returns to no menubar). |
| **S35** | **Keep the broker-boundary plumbing inert rather than deleting it.** In `ui/main_window.py` the inbound observers (`_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`) and the `order_registry` import stay wired; the registry is never populated by the app any more, so they observe and surface TWS state only. In `ibkr/bridge.py` / `ibkr/client.py` the news signals (`tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article`) and the ibapi callback overrides stay as API-boundary mirrors — they are now **unconnected** (`NewsManager`, their only consumer, is gone). The fail-fast port check, the connection badge and the global no-test-transmits rule are retained. | **`[extends D26: the connection/error path]`** — `AC-D26.5` (badge + port check) is unchanged and depends on this path; `[extends D38: the ibapi news boundary]` retained unconnected. A90 records the inertness so it is not mistaken for a leftover (R74). |
| **S36** | **The acceptance instrument is a source-scan invariant plus a mocked-client walkthrough, not a convention.** A new `tests/test_d45_removal` asserts: deleted modules are unresolvable and deleted files absent; the removed tokens listed in the plan's residue-verification step appear nowhere in the scanned tree — the **AST** pass reads identifiers **and** string constants over `ui/ services/ data/ ibkr/ config/` (comments are invisible to it, which is why `config/settings.py`'s `validate_order()` *comment* is out of scope in a file no task may edit), and a **`ui/`-only grep** is the prose net — both under an explicit survivor allow-list; `tests/` is covered by neither, so `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in the module; `ibkr/validation` and `ibkr/news` do not exist; and driving a real offscreen `MainWindow` through every remaining affordance issues **zero** `placeOrder`, **zero** `cancelOrder`, **zero** `reqGlobalCancel`. It replaces the **intent** of the five deleted suites (`AC-D45.4`, R70) with a static + behavioural invariant and must be **proven discriminating** against the pre-D45 tree. | **`[new in D45]`** — the mechanism exists (`tests/test_d41_removal.py` is its precedent: AST token scan + allow-list + real offscreen window); the D45 variant is new. Supersedes the *coverage claim* of the deleted order-safety suites (consequence 5 of D45 states the loss plainly). |
| **S37** | **Ordering is forced by two shared files, not chosen for taste.** `ui/main_window.py` is touched by three groups (A, B-main, C) and `ui/active_portfolio_panel.py` by one (B-panel); `tests/test_dock_d18_region.py` by two (A `:147`, B `:174`–`:179`); `USAGE.txt`/`usage.md` by all three. Therefore: **one task per wave on `ui/main_window.py`** (waves 1, 2, 4), **Group B's window half lands before its panel half** (panel-first would leave `MainWindow.__init__` connecting signals that no longer exist → `AttributeError` in every window test, i.e. a wave that cannot pass its own tests), and **all three docs go in one terminal task** (wave 5) instead of three conflicting edits. | **`[new in D45]`** — the sequencing constraint, recorded in `docs/plan_proposal.md` § Sequencing. (The `ESC-055` rule — enumerate assertions invalidated **outside** the edited files — is applied, not restated.) |
| **S38** | **Docs are one batch-scoped step, and the map's skeleton is not hand-edited.** `USAGE.txt`, `usage.md` are cleaned in one task with the three owner-named items removed (`A85`); `docs/codebase-map.md` is refreshed by Plan (this batch) — the generated skeleton is rebuilt from the tree by `update_codebase_map.py`, so it keeps listing the deleted files until the **next** refresh, and the annotation tables describe the **post-D45 target state** (stated in the map's header). | **`[new in D45]`** — `AC-D45.7` makes doc freshness checkable; A85 scopes the files. `[extends the per-batch map convention: memory 2026-10-23 item 5]`. |

---

## Codebase Summary (existing repository — the D45 surface, source-validated 2026-10-25 @ `c702be9`)

**This is the pointer to `docs/codebase-map.md`, not a second inventory.** The map carries the module index,
the status legend and the test-impact rows; this section records only what D45's decisions rest on, and every
fact below was re-derived from source in this run (graphify `graph.json` (4,947 nodes) used for discovery;
**the source is authoritative** where they disagree).

### Facts D45's decisions rest on (all re-verified in this run)

| Fact | Verified evidence | Consequence |
|---|---|---|
| `placeOrder` has **exactly one** production call site | `ui/main_window.py:3476` inside `_close_position_by_id`; **no `placeOrder` definition exists in `ibkr/`** — it is ibapi's inherited `EClient.placeOrder` (`ibkr/client.py:39 class IBApiClient(EWrapper, EClient)`) | `S30`: deleting that one method makes `placeOrder` uncalled tree-wide. The map's earlier "`IBApiClient.placeOrder` (the only transmit)" was **wrong** and is corrected this batch. |
| `reqGlobalCancel`/`cancelOrder` have **exactly one** call site pair | `ui/main_window.py:3042`, `:3048`, inside `_kill_switch`; no `ibkr/` wrapper; no `closeEvent`/disconnect caller (`closeEvent` teardown order re-read 2026-10-25) | `S31`: the cancel capability is removed outright; nothing needs re-homing. |
| `_kill_switch` has exactly **two** callers | the toolbar button (`:3061`) and `_on_portfolio_flatten_all` (`:3385`, deleted by `S30`) | Both callers go inside one batch; neither survives. |
| `_ref_price_for` has **exactly one** caller | definition `:2154`; caller `:3435` (inside `_close_position_by_id`); the `_symbol_last_prices` map it reads **stays** (the Portfolio P/L path reads it directly at `:3207`) | `S30`: delete the accessor, keep the map. R74 names a leftover `_ref_price_for` as residue — this is the removal that prevents it. |
| The SL/TP dialog's **only** entry point is the context menu | `ui/active_portfolio_panel.py:156 self._context_menu.set_sltp_action.triggered.connect(self._on_set_sltp)`; `_on_set_sltp` is the only constructor call of `StopLossTargetDialog` | A89: Groups B and the extension agree — the setter was already unreachable once the menu went; the extension completes the removal. |
| `order_registry` is **not** orphaned by the removal | `ui/main_window.py:36` imports it; consumers: `_update_order_status` (`:3335`), `_on_order_error` (`:1598`), and `_close_position_by_id` (`:3400`, deleted) | `S29`/`S35`: keep the module; the registry stays read/written by the **inert** observers, so it is neither unreferenced code nor a transmit path. |
| `ibkr/orders.py` keeps **real** unit coverage | `tests/test_order_builders.py` covers `market_order`/`limit_order`/`stop_order`/`bracket_order` (structure, OCA groups, `transmit` flags) and the registry (`register`/`get`/`update_status`/`clear_filled`/`all`) | DG77's "left with **no tests at all**" is **wrong for this module**; what the five deleted suites took was the *integration* driver (`_kill_switch` reading the registry, `_close_position_by_id` transmitting), not the builders' unit coverage. Recorded so it is not "discovered" later. |
| `tests/test_d41_removal.py` stays green after `ibkr/news` is deleted | its only news reference is `_ALLOWED_ANYWHERE` = `{"footprint_cache_key", "queue_depth"}` (a frozenset **string**, `:105`); its token scan reads `ui/ services/ data/ ibkr/ config/` only and `queue_depth` lives in the allow-list, so no assertion reads `NewsManager` behaviour | `AC-D45.8`: **keep unchanged** (verified, not assumed). |
| `tests/test_stop_loss_target.py` survives on its own merits | 3 cases, imports only `data.models.Position`/`TradeGroup`, asserts the four model fields (defaults + explicit values) and no UI | A87: the fields stay → the file stays **unchanged** and still means something. |
| The digest test block is contiguous and separable | `tests/test_d38_events_news.py`: NewsManager block `:145`–`:201`; digest block `:419`–`:549` (`_StubNewsManager`, `_StubHost`, `_make_dock`, `test_ac_d38_2_digest_groups_headlines`, `test_ac_d38_3_no_entitlement_state`, `test_ac_d38_2_click_fetches_article`); surviving blocks `:83`–`:143` (tick 59), `:202`–`:417` (yfinance, markers, AC-D38.5), `:551`–`:593` (no-mock-endpoint, md-line guard) | Group A trims by symbol: two whole sections go, the file stays. The md-line guard docstring's `"292"` reference is the "one docstring" the correction record names. |
| The 8-column shift invalidates **exactly two** external files | `tests/test_d27_position_id.py:164-165` and `tests/test_d27_position_prices.py:290-291` address Strategy/Group as `8`/`9`; a scan of `tests/` for `positions_table` shows no other column-index assertion (`test_d27_account_subs.py:102` uses column `0`; the D18 width suites iterate `range(table.columnCount())` and are index-agnostic) | R75/DG77: `6`/`7`, named in the plan's test book. No third file needs touching. |
| `_s0_headless` is digest-only but is read in **two** S0 line-build paths | set only by `ui/news_digest_dock.py:209/:221`; read at `ui/ticker_session.py:437` and `:483` (`want = self._s0_union_str() if (self.view_count > 0 or self._s0_headless) else ""`) | `S34`: deleting the flag is a **three-site** edit, not one — the residue risk a worker would miss. |

### Data models / persisted state `[existing]`

- **`positions`** — `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier,
  expiry, strike, right, stop_loss, take_profit, trade_group_id, updated_at` (`data/db.py:117`–`:124`).
  **Unchanged by D45** (A87) — no DDL edit, no migration.
- **`trade_groups`** — `id, name, strategy_type, underlying, stop_loss, take_profit, collapsed, created_at`
  (`data/db.py:127`–`:134`). **Unchanged.**
- **`data/models.py`** — `Position.stop_loss/take_profit: Optional[float] = None`, `TradeGroup.stop_loss/
  take_profit: Optional[float] = None`. **Unchanged.**
- **Not persisted:** dock layout / toolbar state are `QSettings`-free for the right region (A36) and the
  digest dock relies on Qt's restored dock state — a saved state naming a removed dock must be **ignored**
  (Journey 38 edge case), which Qt does when the objectName no longer exists. **No new key, no migration.**

### Major components and responsibilities (post-D45 target; deltas in the next table)

`ui/main_window.py` (window, docks, toolbar, load path, sessions, teardown) · `ui/ticker_session.py`
(per-symbol session: bars, waves, pacing, live bars, S0 generic-tick substrate) · `ui/active_portfolio_panel.py`
(the right dock's Portfolio panel, **view-only**) · `ui/chart_panel.py` + `ui/candlestick_item.py` +
`ui/overlays/*` + `ui/event_marker_overlay.py` (render stack, **untouched**) · `ui/watchlist_panel.py` +
`ui/dock_layout.py` (**untouched**) · `services/*` (calendar, backfill, collapse, alarms, search, drawings,
studies, md-line guard — **untouched**) · `data/*` (SQLite, cache, aggregator, stores, event provider —
**untouched**) · `ibkr/*` (client wrapper, bridge, market data, RT bars, pacing, id managers, subscriptions,
stream health, account, contracts, **orders (kept, no transmit caller)**, **news (deleted)**,
**validation (deleted)**).

### Key entry points / data flow (unchanged shape)

`main.py` → `MainWindow()` → `IBApiClient.connect` (fail-fast port check) → bridge signals → sessions/chart;
account-summary + position callbacks → `_upsert_position` → `ActivePortfolioPanel.set_positions/add_position` →
`_group_and_render` → `_render_table`. **D45 removes three inbound UI paths that branched off this flow** —
the digest dock (news callbacks), the Portfolio context menu/close handlers, and the toolbar kill switch — and
changes nothing on the retained path.

### External integrations already in use `[existing]`

IBKR TWS via the official `ibapi` (`10.51.1`): historical + realtime bars, market data with S0 generic ticks,
account summary/positions, news API + tick `"292"` (**removed**), dividends tick `"456"`/59 (**retained**),
order transmit (`placeOrder`, inherited `EClient`) + cancel (`cancelOrder`, `reqGlobalCancel`) — **no longer
reachable**; yfinance as the sole approved secondary event source (**retained**); SQLite (**retained**).

### What D45 changes, in one line

Four modules deleted (`ui/news_digest_dock`, `ibkr/news`, `ui/trade_context_menu`,
`ui/stop_loss_target_dialog`), plus `ibkr/validation`; **three** production modules edited (`ui/main_window.py`,
`ui/ticker_session.py`, `ui/active_portfolio_panel.py`); five test files deleted and seven adjusted; two docs
cleaned; **no file added** to production (one new test module, `S36`).

---

## Summary

D45 is a **subtractive** increment whose requirement is **unreachability**: after it, no UI path in NDThinkChart
can place, cancel or close an order, and no UI path can set a stop/target — the app observes TWS and renders.
The architecture therefore does not add a component or a seam; it **severs three inbound UI branches at their
single call sites** (`_close_position_by_id` for the transmit; `_kill_switch` for the cancel; the panel's
SL/TP chain for the setter), deletes the four feature modules plus the now-unused validation module, and
leaves the broker boundary, the dividend substrate, and the stop/target storage untouched and inert. The
guarantee is then **structural, not conventional**: a static source-scan invariant over `ui/` plus a
mocked-client zero-transmit walkthrough, both proven discriminating against the pre-D45 tree.

---

## Tech Stack Decisions

**Constrained choices first** — these are the existing stack; D45 changes none of them (no requirement asks
for a stack change, and the pyqtgraph decision is **locked**, `docs/memory.md` 2026-10-16).

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| UI toolkit `[existing]` | **PyQt6** (widgets, signals, docks, QSettings) | Entire app is PyQt6; D45 only deletes widgets | — (no change proposed) |
| Chart renderer `[existing]` | **pyqtgraph**, locked | Locked decision (2026-10-16); D45 does not touch the render stack | `QWebEngineView` + Lightweight Charts — **declined by the owner**, do not re-propose |
| Broker client `[existing]` | official **`ibapi`** (`10.51.1.post1`) via `IBApiClient(EWrapper, EClient)` | Order/cancel methods are **inherited** from `EClient`; removing callers needs no client edit | Writing an in-repo transmit wrapper — rejected: adds surface for a path that must not exist |
| Persistence `[existing]` | **SQLite** (`data/db.py`), additive migrations only | A87 keeps the SL/TP columns → **no migration at all** in this batch | Dropping the two column pairs (rejected by the owner: destructive, zero user-visible gain) |
| Removal mechanism `[new in D45]` | **Delete** the modules + **sever** the three call sites; keep the broker boundary inert | `AC-D45.4`/`.6` measure absence + zero calls; deletion is what makes a future re-wire impossible by accident | Keep modules + runtime guards (rejected: reachability by convention; a stray `.connect` would resurrect the path unnoticed) |
| Verification mechanism `[new in D45]` | **AST/token source scan over `ui/`** + **mocked-client offscreen walkthrough** in one new test module | Precedent exists and works (`tests/test_d41_removal.py`); no new dependency; catches string-constant leftovers, not just live lookups | Grep-only in CI (rejected: prose false positives, no behavioural half); mypy/type-level «unreachable» (rejected: new dependency, and `placeOrder` is inherited/duck-typed) |
| `ibkr/orders.py` `[new in D45]` | **Retain**, add a module-docstring note that it is unreachable after D45; keep `tests/test_order_builders.py` | DG76(a) + A80/A90: the registry is *used* by the retained observers; deleting it forces registry-safe rewrites of the error path for zero reachability gain | Delete it (DG76(b)) — rejected: outside the owner's named inventory, breaks `A90`'s retained observers, and discards real unit coverage |
| Test runner `[existing]` | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` | Repo convention (the `pytest` entry point has a stale shebang) | — |
| New dependencies `[new in D45]` | **None** | Constraint; nothing in D45 needs one | — |

---

## System Components

Status is relative to the codebase (`[existing]` = present and **unmodified** by this batch;
`[new/changed]` = present and modified).

### Changed by this batch

| Component | Status | What changes |
|---|---|---|
| `ui/main_window.py` | **`[new/changed]`** | **Group A:** the digest dock block (`:479`–`:493`), `_on_news_digest_visibility` (`:2757`–`:2763`), the `NewsManager` construction (`:529`–`:530`), `b.tick_news.connect` (`:628`), `_on_s0_tick_news` (`:1968`–`:1976`). **Group B:** the two SL/TP + three close `.connect` lines (`:647`–`:651`), `_on_portfolio_close_position` / `_on_portfolio_close_group` / `_on_portfolio_flatten_all` / `_on_portfolio_sltp_changed` / `_on_portfolio_group_sltp_changed`, `_close_position_by_id`, `_ref_price_for`, the `validate_order` import, and the `order_limiter` (and now-unused `pacing_manager`) names in the `ibkr.pacing` import — `PacingExceeded` stays. **Group C:** `kill_btn` + its `QLabel("|")` separator + tooltip/style/connect (`:319`–`:330`), `_kill_switch` (`:3028`–`:3057`), `_on_kill_switch_clicked` (`:3059`–`:3061`). **Retained in the same file (A90):** `order_registry`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `_symbol_last_prices`, the fail-fast connect path, the badges, `closeEvent` teardown. |
| `ui/ticker_session.py` | **`[new/changed]`** | The news `"292"` register line + its comments, `on_s0_tick_news`, `add_news_push_listener`, `remove_news_push_listener`, `set_s0_headless`, `_s0_headless` (`:175`) **and the two `or self._s0_headless` clauses** (`:437`, `:483`). **Retained verbatim:** `_needs["dividends"] = {"456"}` (`:232`), `on_s0_tick_string` tick-59 branch, `_dividend_info`, `dividend_updated`, `dividend_info()`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`, the S0 union/resync/cancel machinery. |
| `ui/active_portfolio_panel.py` | **`[new/changed]`** | The `TradeContextMenu` + `StopLossTargetDialog` imports and members, the `CustomContextMenu` policy and its connection, `_show_context_menu`, `_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`, `_sltp_dialog`, the five signals, the now-dead selection tracking (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection and the two stale comments that name it), and the `Stop`/`Target` columns (**10 → 8**; values list and alignment set `(1,2,4,5)`; the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording). **Retained:** `summary_label`/`_on_header_toggled`/`is_collapsed`/`set_collapsed`/`toggle_collapsed`, `set_account_summary`/`set_account_id`/`set_account_unavailable`, `set_positions`/`add_position`, `refresh`/`_render_summary`/`_group_and_render`, `account_summary_changed`, `positions_changed`, `_unrealized_pnl`. |
| `tests/test_d38_events_news.py` | **`[new/changed]`** | Two sections removed (NewsManager `:145`–`:201`, digest `:419`–`:549`); module docstring trimmed; the md-line-guard docstring's `"292"` reference corrected to the surviving `"456"` line. **Event-marker/dividend blocks kept byte-for-byte** (R68's regression guard). |
| `tests/test_dock_d18_region.py` | **`[new/changed]`** | `:147` drops the `objectName() != "NewsDigest"` filter (Group A); `:174`–`:179` **deletes the five-signal receiver loop outright** (Group B-main). All five signals go, so **no signal survives** — the loop is removed, not narrowed; the surrounding assertions stay (the panel is still the dock's widget, `account_summary_changed` / `positions_changed` are still present, and the `positions_changed` zero-receiver probe still proves the probe is not vacuous), and the wiring comment is restated as the post-D45 truth. This is a **deviation from the register's suggested "three-signal loop"** (`requirements.md:4178`–`:4179`, `DG77` item 4) — recorded in `docs/plan_notes.md` `RG-D45-1` and in the plan's § Exactness note; the deviation **does not weaken `AC-D45.8`**, which requires the file to be *adjusted*. |
| `tests/test_d27_position_id.py` | **`[new/changed]`** | `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row` removed **in wave 2** — its subject is deleted in two halves and its passing path is the window's `position_sltp_changed` connection, removed there; `:164`–`:165` `8`/`9` → `6`/`7` **in wave 3** (the columns shift there). **Kept:** the AC1 live-update case, the AC2 bulk-id case (the D27.1 id-correctness property survives there), and `EXPECTED_COLUMNS`-style fixtures if any (Build checks). |
| `tests/test_d27_flat_rows.py` | **`[new/changed]`** | The AC3 tail only: `:108`–`:111` (the `selectRow` drive plus the two `panel._selected_position` assertions) go with the deleted selection tracker; `:104`–`:106` (**the index-alignment assertions — the property AC3 exists for**) stay verbatim, and the AC3 docstring sentence is restated without naming the removed members. AC1/AC2 untouched. `S37`'s wave-membership rule puts this edit in **wave 3**, the wave that deletes the tracker. |
| `tests/test_d27_position_prices.py` | **`[new/changed]`** | `:290`–`:291` Strategy/Group `8`/`9` → `6`/`7`. Nothing else. |
| `tests/test_order_rejections.py` | **`[new/changed]`** | `test_close_blocked_while_disconnected` deleted (its subject, `_close_position_by_id`, is gone — `AC-D26.9`'s disconnected branch has no order path left to block); the `_fresh_registry`/`_register` helpers and the `_on_order_error`/`classify_error` cases **stay** (they cover the retained observer path, A90). |
| `tests/test_d28_pacing.py` | **`[new/changed]`** | `test_close_position_defers_when_limiter_empty` deleted whole (it drives `_close_position_by_id` and pins the gate-before-pacing order). The historical-pacing cases **stay** — they are D28.3, unrelated to the order bucket. |
| `tests/test_d45_removal` (new) | **`[new]`** | The `S36` instrument — the one file this batch adds. |
| `USAGE.txt`, `usage.md` | **`[new/changed]`** (**docs**) | The digest/`View` section, the close/close-group/close-all text, the kill-switch bullet, the SL/TP bullet, the "orders cannot be placed while disconnected" claim; `usage.md`'s `### Portfolio & SL/TP` heading/steps and its Portfolio table row; a Database-section note that SL/TP stay **stored** but are no longer settable. Must state plainly that **closes and cancels happen in TWS**. |
| `docs/codebase-map.md` | **`[new/changed]`** (**Plan-owned**) | Refreshed this batch: the three removed modules and `ibkr/validation` no longer listed as live; `_kill_switch`/`StopLossTargetDialog` no longer named as retained; the `placeOrder` ownership error corrected; the D45 test book updated. |

### Deleted by this batch (nothing replaces them)

| Module | Status | Reason |
|---|---|---|
| `ui/news_digest_dock` (`NewsDigestDock`) | **deleted** | `S34`/`AC-D45.1`; owner: its only consumer is the digest |
| `ibkr/news` (`NewsManager`) | **deleted** | `S34`/A79; only consumer was the dock + its tests |
| `ui/trade_context_menu` (`TradeContextMenu`) | **deleted** | `S30`/`AC-D45.3`; the only close/group/flatten/SL-TP entry point |
| `ui/stop_loss_target_dialog` (`StopLossTargetDialog`) | **deleted** | `S32`/A89; local-only setter, unreachable after the menu goes |
| `ibkr/validation` (`validate_order`) | **deleted** | `S30`; gates an order nothing builds (`AC-D26.7` moot) |
| `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py`, `tests/test_kill_switch.py`, `tests/test_sltp_honesty.py` | **deleted** | Their subjects no longer exist (A81/`AC-D45.8`, five named whole-file deletions) |

### Retained and deliberately **inert** (not leftovers — A90)

- `ibkr/orders.py` — builders + `Orders` registry + the `orders` singleton; **no transmit caller**, still the
  registry the observers read (`S29`). One permitted edit: a module-docstring note.
- `MainWindow._on_open_order` / `_on_order_status` / `_on_exec_details` / `_on_order_error` /
  `_update_order_status` + the `order_registry` import — observe TWS, place/cancel nothing, registry never
  populated by the app.
- `ibkr/bridge.py` news signals + `ibkr/client.py`'s `tickNews`/`newsProviders`/`historicalNews`/
  `historicalNewsEnd`/`newsArticle` overrides — the ibapi boundary mirrors; unconnected, harmless (`S35`).
- `config/settings.py::MAX_ORDER_NOTIONAL` — see *Incidentally affected* in the plan; **not** deleted.
- `ibkr/pacing.py::order_limiter` — the order-path token bucket; no consumer after D45, but `pacing.py` is a
  shared, tested module — **not** edited by this batch.

---

## Data Model

No schema change, no migration, no data deletion (A87/`D45.6`). Every entity below is `[existing]`.

| Entity | Status | Key fields | D45 effect |
|---|---|---|---|
| `positions` (SQLite) | `[existing]` | `id, symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, multiplier, expiry, strike, right, stop_loss, take_profit, trade_group_id, updated_at` | **none** — `stop_loss`/`take_profit` stay, written by the unchanged upsert |
| `trade_groups` (SQLite) | `[existing]` | `id, name, strategy_type, underlying, stop_loss, take_profit, collapsed, created_at` | **none** — the `UPDATE trade_groups SET stop_loss=…` statement is deleted, the columns are not |
| `data.models.Position` | `[existing]` | `symbol, qty, avg_cost, contract_type, con_id, account, local_symbol, multiplier, expiry, strike, right, stop_loss, take_profit, trade_group_id, id` | **none** — `stop_loss`/`take_profit` retained (A87); `tests/test_stop_loss_target.py` keeps asserting them |
| `data.models.TradeGroup` | `[existing]` | `name, strategy_type, underlying, id, stop_loss, take_profit, collapsed, created_at` | **none** |
| `MainWindow._upsert_position` (`:3283`) | `[existing]` | `INSERT INTO positions (… stop_loss, take_profit …) … ON CONFLICT(symbol, con_id) DO UPDATE SET … stop_loss=excluded.stop_loss, take_profit=excluded.take_profit … RETURNING id` | **none** — the position upsert still writes both fields. *(The requirements call this `_persist_position`; the tree names it `_upsert_position` — a naming drift only, recorded in the plan.)* |
| `MainWindow._on_position_end` bulk load (`:3250`–`:3282`) | `[existing]` | SELECTs the 15 columns incl. `stop_loss`/`take_profit`, builds `Position(...)` with `id` | **none** — legacy values keep round-tripping; they are simply not displayed |
| **Positions table view model** | `[new/changed]` (**view only — no storage**) | 8 columns, in order: `0 Symbol`, `1 Qty`, `2 Avg Price`, `3 Type`, `4 Multiplier`, `5 P/L`, `6 Strategy`, `7 Group`; right-aligned set `(1, 2, 4, 5)` | `S33`: the `Stop`(6)/`Target`(7) slots go; `Strategy`/`Group` move `8/9 → 6/7` (`AC-D45.10`). This is a render mapping, **not** a persisted entity |

Relationships: `positions.trade_group_id → trade_groups.id` (FK, unchanged); `position_group_map` unchanged;
strategy/group cell derivation (`services.strategy_detection.detect_and_group`) unchanged.

---

## Integration Points

| Integration | Status | Why it is needed / what changes |
|---|---|---|
| **IBKR TWS** — historical + realtime bars, market data, account summary/positions (`ibapi` over the local socket, `7496` live / fail-fast port check) | `[existing]` | The app's whole data plane; **unchanged**. `AC-D26.5`'s port check + badge retained. |
| **IBKR S0 generic tick `"456"`** (+ tick 59 string) → `_dividend_info` → `dividend_updated` → dividend marker | `[existing]` | Retained **verbatim** (`S34`, R68, `AC-D45.2`): it is the only live dividend source for the chart's event markers. |
| **IBKR S0 generic tick `"292"`** (live news push) | **removed** | `AC-D45.1`/`.2`: never requested; the digest that consumed it is gone. **The `s0_register` mechanism stays** — only the news need disappears. |
| **IBKR news API** (`reqNewsProviders`, `reqHistoricalNews`, `reqNewsArticle`) + the bridge's news signals | `[existing]` (inert) | The client/bridge overrides stay (`S35`) — deleting them would touch the connection-callback file for no reachability gain; nothing constructs `NewsManager` any more, so they are never requested. |
| **IBKR order transmit** (`EClient.placeOrder`, inherited) / **cancel** (`cancelOrder`, `reqGlobalCancel`) | `[existing]`, **unreachable** | `S30`/`S31`: zero call sites in the tree after D45. `ibapi` still exposes the methods (deleting them is impossible/unwise); the **app never calls them** — proven by `S36`. |
| **IBKR inbound order/execution callbacks** (`openOrder`, `orderStatus`, `execDetails`, `error`) | `[existing]` (inert) | Retained observers (A90): they surface TWS state and order errors on the status bar; registry never populated by the app. |
| **yfinance** corporate-events provider (`data/events/yfinance_source`, cache in SQLite) | `[existing]` | Sole approved secondary source; drives earnings/split markers when IBKR has none; **untouched** (`AC-D38.4`, `AC-D38.5` stand). |
| **SQLite** (`data/db.py`, `bar_cache`, stores) | `[existing]` | **No migration** this batch; a pre-D45 DB opens unchanged with its legacy stop/target values. |
| **Qt `QSettings`** (watchlist width/columns) | `[existing]` | Untouched; a stale entry naming the removed dock/toolbar button must be ignored (Journey 38 edge case) — Qt ignores restored state whose objectName no longer exists. |
| *New integrations* | — | **None.** D45 adds no service, no dependency, no endpoint. |

---

## Frozen Interfaces

Interfaces this batch treats as **read-only**: settled, and modified by **no** D45 task. Contracts are
**verbatim** from the tree at `c702be9` (never paraphrased), with the owning module, so Task Manager can hand
a worker the contract instead of the implementation. **Nothing under construction this batch is listed** —
the digest/kill-switch/SL-TP/close surfaces (being deleted) and the 8-column render (being changed) are
deliberately absent, and `ibkr/orders.py` is frozen **at its API** with one permitted docstring note (`S29`).

| Interface | Verbatim contract | Owning module |
|---|---|---|
| Dividend signal `[existing]` | `dividend_updated = Signal()` | `ui/ticker_session.py` |
| Tick-59 ingress `[existing]` | `def on_s0_tick_string(self, req_id: int, tick_type: int,`<br>`                          value: str) -> None:` — tick-59 branch parses defensively, sets `_dividend_info`, emits `dividend_updated`, calls `_merge_ibkr_dividend_event` | `ui/ticker_session.py` |
| Dividend reader `[existing]` | `def dividend_info(self) -> dict:` | `ui/ticker_session.py` |
| S0 registration API `[existing]` | `def s0_register(self, feature: str, ticks: set[str]) -> None:` · `def s0_deregister(self, feature: str) -> None:` · `def s0_register_many(self, needs: dict[str, set[str]]) -> None:` · `def s0_deregister_many(self, features) -> None:` | `ui/ticker_session.py` |
| Event merge / read `[existing]` | `def _merge_ibkr_dividend_event(self) -> None:` · `def _merge_events(self, new_events: list, source: str) -> None:` · `def events(self) -> list:` · `def events_unavailable(self) -> bool:` | `ui/ticker_session.py` |
| Dividend string parser `[existing]` | `def parse_ib_dividend_string(value: str) -> dict[str, Any]:` | `data/events/provider.py` |
| Marker overlay API `[existing]` | `class EventMarkerOverlay(QObject):`<br>`    def __init__(self, plot: pg.PlotWidget):`<br>`    def set_bars(self, bars) -> None:`<br>`    def set_collapse_map(self, collapse_map) -> None:`<br>`    def set_events(self, events, unavailable: bool = False) -> None:`<br>`    def event_count(self) -> int:`<br>`    def clear(self) -> None:`<br>`    def countdown_text(self) -> str:` | `ui/event_marker_overlay.py` |
| MD-line guard `[existing]` | `def assess(projected_count: int, symbol: str, purpose: str`<br>`           ) -> tuple[str, str]:` — level ∈ `{"ok", "approaching", "exceeded"}` | `services/md_line_guard.py` |
| `Position` SL/TP fields `[existing]` | `stop_loss: Optional[float] = None` · `take_profit: Optional[float] = None` (on both `Position` and `TradeGroup`) | `data/models.py` |
| Position upsert `[existing]` | `def _upsert_position(self, position: Position) -> int:` — `INSERT INTO positions (… stop_loss, take_profit …) … ON CONFLICT(symbol, con_id) DO UPDATE SET … stop_loss=excluded.stop_loss, take_profit=excluded.take_profit … ` + `RETURNING id` | `ui/main_window.py` |
| Position bulk load `[existing]` | `def _on_position_end(self):` — SELECTs the 15 columns incl. `stop_loss`, `take_profit`, stamps `id` | `ui/main_window.py` |
| Order registry API `[existing]` | `class Orders:` with `def market_order(self, action: str, qty: float) -> Order:` · `def limit_order(self, action: str, qty: float, price: float) -> Order:` · `def stop_order(self, action: str, qty: float, price: float) -> Order:` · `def bracket_order(`<br>`        self,`<br>`        parent_id: int,`<br>`        action: str,`<br>`        qty: float,`<br>`        entry_price: float,`<br>`        stop_price: float,`<br>`        limit_price: float,`<br>`    ) -> tuple[Order, Order, Order]:` · `def register(self, order: UserOrder) -> None:` · `def get(self, order_id: int) -> Optional[UserOrder]:` · `def update_status(self, order_id: int, status: str) -> None:` · `def clear_filled(self, order_id: int) -> None:` · `def all(self) -> Dict[int, UserOrder]:` · singleton `orders = Orders()` — **API frozen; the only permitted edit is a module-docstring note; no signature and no behaviour change** | `ibkr/orders.py` |
| Inert inbound observers `[existing]` | `def _on_open_order(self, orderId: int, contract, order, orderState):` · `def _on_order_status(self, orderId: int, status: str, filled: float,`<br>`                           remaining: float, avgFillPrice: float,`<br>`                           permId: int, parentId: int, lastFillPrice: float,`<br>`                           clientId: int, whyHeld: str, mktCapPrice):` · `def _on_exec_details(self, reqId: int, contract, execution):` · `def _on_order_error(self, order_id: int, error_code: int, error_string: str):` · `def _update_order_status(self, orderId: int, status: str):` | `ui/main_window.py` |
| Portfolio render API `[existing]` | `account_summary_changed = pyqtSignal(dict)` · `positions_changed = pyqtSignal(list)` · `def set_account_summary(self, summary: dict[str, str]) -> None:` · `def set_account_id(self, account_id: str \| None) -> None:` · `def set_account_unavailable(self, unavailable: bool) -> None:` · `def set_positions(self, positions: list[Position]) -> None:` · `def add_position(self, position: Position) -> None:` · `def refresh(self) -> None:` | `ui/active_portfolio_panel.py` |
| Portfolio collapse header `[existing]` | `def is_collapsed(self) -> bool:` · `def set_collapsed(self, collapsed: bool) -> None:` · `def toggle_collapsed(self) -> None:` · `self.summary_label` (the right dock's title-bar toggle, D21.13) | `ui/active_portfolio_panel.py` |
| Right-dock minimum `[existing]` | `RIGHT_DOCK_MIN_WIDTH = dock_layout.RIGHT_DOCK_MIN_WIDTH` (= 200, `ui/dock_layout.py`) — the **value** is frozen; only the module docstring's "10-column" wording is corrected | `ui/active_portfolio_panel.py`, `ui/dock_layout.py` |
| Broker boundary `[existing]` | `class IBApiClient(EWrapper, EClient):` — `EClient.__init__(self, self)`, remembered connect params for the D27.3 reconnect (`_do_reconnect` re-issues the real `EClient.connect`), `def connected(self)`, the bridge instance. **No `placeOrder`/`cancelOrder`/`reqGlobalCancel` definition exists here** (all inherited from `EClient`) — this batch must not add one | `ibkr/client.py` |
| Fail-fast port check `[existing]` | `def check_live_port() -> None:` | `config/settings.py` |
| Error classification `[existing]` | `def classify_error(error_code: int) -> str:` — returns `'info' \| 'warning' \| 'fatal'`; drives the retained `_on_order_error` / connection-alert path | `ibkr/error_codes.py` |

---

## Non-Functional Approach

- **Reachability / zero-transmit (from `D45.2`, `AC-D45.4`, `AC-D45.6`, R70).** The guarantee is delivered by
  **structure** (three call sites severed, four modules deleted) and **verified twice**: a static AST/string
  scan over `ui/` (no `placeOrder`, `cancelOrder`, `reqGlobalCancel`, `validate_order`, the deleted module
  names, or any of the removed member tokens) and a behavioural walkthrough over a real offscreen
  `MainWindow` with a mocked client exercising every surviving affordance, asserting
  `placeOrder.call_count == cancelOrder.call_count == reqGlobalCancel.call_count == 0`. Requirement
  `D45.5`/`AC-D45.5` (Portfolio still renders and live-updates, view-only, reflecting a TWS-side close on the
  next position update) is asserted on the same walkthrough so "removed" cannot quietly mean "stopped
  rendering".
- **Dividend preservation (from `AC-D45.2`, `D45.3`, R68 — the batch's highest-risk deletion).** Both halves
  share one `s0_register` mechanism and one file (`ui/ticker_session.py`). Mitigation is procedural **and**
  structural: the S0 union is built from `_s0_needs`, so removing the `"news"` need leaves `"dividends"`
  registering `"456"` unchanged; the surviving event-marker/dividend cases in `tests/test_d38_events_news.py`
  are the regression guard; and the residue list explicitly **forbids** deleting `"456"`, tick 59,
  `_dividend_info`, `dividend_updated`, `_merge_events` (they are the survivor allow-list, not residue).
- **Data safety / no migration (from A87, `D45.6`, `AC-D45.10`).** The DB and the ORM fields are untouched, so
  the migration surface is zero: a pre-D45 database opens unchanged, legacy `stop_loss`/`take_profit` values
  survive, and the upsert keeps writing them. The only data-adjacent change is **presentational** (two columns
  not rendered). Verification includes opening a pre-D45 file and confirming the values are still there.
- **Worker safety on delete-only work (from memory 2026-10-15, R69).** D41 lost three workers to large
  delete-only tasks. D45 is **split by member group and by file, one wave per `ui/main_window.py` touch**, and
  every wave task ends with an import/syntax check plus its own group's residue grep — so a worker death is
  detected at the file, not at the suite.
- **Importability between waves (from S37).** The window half of Group B lands **before** the panel half,
  because removing the panel's signals first would make `MainWindow.__init__` connect attributes that no
  longer exist — every window test would fail for a reason unrelated to the work in flight. Each wave leaves
  the app importable and its own tests green.
- **Doc freshness (from `D45.5`, `AC-D45.7`, R71).** Two owner-facing docs plus the Plan-owned map; the
  assertion is **grep-checkable** (`News Digest`, `Ctrl+Shift+N`, `Close All Positions`, `Close Group`,
  `Close Position`, `Kill switch`, `Stop-Loss` absent except where the text says the app does not place/cancel
  and that closes/cancels happen in **TWS**), so the Code Reviewer verifies it independently rather than
  trusting the task.
- **Performance / scalability.** No measurable change and none required: the positions table renders two
  fewer cells per row, three scheduled paths disappear (the digest's article fetches, the kill switch's
  per-ID cancel loop, the close path's pacing-deferred retry), and no new request is issued on any path. The
  S0 line for a charted symbol becomes *shorter* (`"456"` only), not longer.
- **Security / blast radius (the point of the batch).** The app's authority over the account **shrinks to
  zero**: it cannot place, cancel or close, so the notional cap, the order pacing bucket and the
  disconnected-order guard stop gating anything (`AC-D26.7`/`D26.9` moot). Accepted and recorded (owner,
  R73): **TWS is the cancel surface**, and the app cannot create the order it would need to cancel. No new
  credential, no new endpoint, no new persistence.
- **Platform side effect (A86).** Removing `menuBar()` means the app creates **no `QMenuBar`** at all — on
  macOS it contributes **no** application-menu items, and no orphan `Ctrl+Shift+N` `QAction` can survive
  because the action object lived on the deleted dock's `toggleViewAction()`.

---

## Architecture Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| **AR-D45-1** | Removing the news `"292"` line takes the **dividend `"456"`** path (and the markers) with it — one `s0_register` mechanism, one file (R68) | **H** | `AC-D45.2` pins both sides; the surviving event-marker/dividend cases are the guard; the residue list marks `"456"`/tick 59/`_dividend_info`/`dividend_updated` as **survivors**; Build greps `"292"` after each file in the group |
| **AR-D45-2** | A half-finished deletion leaves the app non-importable (dangling import, a signal connected to a deleted handler, a call into the deleted validation module) — the D41 worker-death pattern (R69) | **H** | One wave per `ui/main_window.py` touch; per-file syntax/import check + residue grep; the per-wave test command covers every suite that builds a window |
| **AR-D45-3** | The **suite stays green while proving less** — five order-safety suites deleted (R70) | **H** | `S36`'s static invariant + zero-transmit walkthrough replace the *intent*; the loss is stated in D45 consequence 5 and the plan's test book, never presented as "no change"; the new guard is proven **RED** on the pre-D45 tree |
| **AR-D45-4** | Column shift (`10 → 8`) makes a Strategy/Group assertion read the wrong cell and pass (R75, DG77) | **M** | `AC-D45.10` fixes the shape; the two named files are adjusted `8/9 → 6/7` in the **same wave** as the panel edit; a `tests/`-wide scan confirmed no third column-index assertion exists |
| **AR-D45-5** | A **half-removed** cancel/protection/context-menu path survives (an `order_registry` read in `_on_order_error`, a leftover `_ref_price_for`, an orphan `set_sltp` string, a panel member whose menu is gone) and a later worker "restores" it (R74) | **M** | The residue list is extended beyond D45's own list and **verified live**, and it now names the **nine panel members wave 3 deletes** (`_show_context_menu`, `_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_selected_row`, `_selected_position`, `_on_selection_changed`, `set_sltp_action`) alongside `_ref_price_for`, `_s0_headless`, `_on_s0_tick_news`, `NewsDigest`, `menuBar`. Its **scope is stated** so the claim is checkable: AST over `ui/ services/ data/ ibkr/ config/` (comments invisible ⇒ `config/settings.py`'s `validate_order()` comment is out of scope) plus a `ui/`-only grep; `tests/` is covered by neither, which is why `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in `tests/test_d45_removal.py`. `S29`/`S35` record the **intentional** survivors so inertness is not mistaken for a leftover |
| **AR-D45-6** | A wave-2/3 ordering mistake makes the panel's removed signals still connected (or the reverse), producing `AttributeError` at window construction | **M** | `S37`: window-first ordering is mandatory and stated; the panel's signals are removed only after the window stops connecting them |
| **AR-D45-7** | Docs drift — the three files keep advertising the digest, the `View` menu, app-placed closes, an in-app cancel or settable SL/TP (R71) | **M** | `AC-D45.7` is grep-checkable; one doc task owns all three; the Code Reviewer greps independently |
| **AR-D45-8** | An **unlisted** test/assertion depends on a removed surface and turns red or silently stops testing (R72) | **M** | The plan's test book enumerates **assertions**, not files; the full offscreen suite runs in the final wave; the two "kept by decision" files are justified individually (`test_d41_removal`, `test_stop_loss_target`) |
| **AR-D45-9** | **No in-app panic cancel** afterwards — a runaway TWS order cannot be stopped from the app (R73) | **H** *(accepted)* | Owner-accepted and recorded; **TWS is the cancel surface**; `AC-D45.6` forbids re-adding a cancel path without a new requirement; docs say so plainly |
| **AR-D45-10** | `ibkr/orders.py` retained-but-unused invites a future reconnection and contradicts "the app places no orders" (DG76) | **L** | `S29`: retained with a docstring note stating unreachability; `ibkr/orders.py`'s builders keep unit coverage (`tests/test_order_builders.py`); `AC-D45.4`'s scan makes a new caller fail a test, not just a review |

---

## Requirements → architecture traceability

| Requirement / journey | Architecture section | Phase (plan) |
|---|---|---|
| **`AC-D45.1`** (no digest dock; no menubar; no `Ctrl+Shift+N`) | `S34`; System Components (`ui/main_window.py`, `ui/ticker_session.py`, deleted `ui/news_digest_dock`); AR-D45-1/2 | Phase 1 · **Wave 1** |
| **`AC-D45.2`** (news `"292"` never requested; `"456"` retained, tick 59 + markers still work) | `S34` + Frozen *Dividend signal / tick-59 ingress / dividend reader / S0 registration / event merge / parser / marker overlay*; Integration Points; AR-D45-1 | Phase 1 · **Wave 1** |
| **`AC-D45.3`** (no context menu; no close/close-group/flatten affordance) | `S30` + `S32`; System Components (`ui/active_portfolio_panel.py`, deleted `ui/trade_context_menu`); AR-D45-2/5/6 — the `hasattr(...) is False` measurables are asserted **directly** in the wave-6 module (the token list is a net, not a substitute) | Phase 1 · **Waves 2–3**; Phase 2 · **Wave 6** |
| **`AC-D45.4`** (zero order interaction; `placeOrder`/`cancelOrder`/`reqGlobalCancel` unreachable) | `S30` + `S31` + `S36`; Frozen *Order registry API* / *Broker boundary*; Non-Functional (reachability); AR-D45-3/5 | Phase 1 · **Waves 2, 4** + Phase 2 · **Wave 6** |
| **`AC-D45.5`** (Portfolio view-only; data path retained; TWS-side close reflected) | `S33`; Frozen *Portfolio render API*; Data Model (`_on_position_end`); AR-D45-4 | Phase 1 · **Wave 3**; Phase 2 · **Wave 6** |
| **`AC-D45.6`** (INVERTED — kill switch and SL/TP dialog are GONE; no cancel path) | `S31` + `S32`; System Components; AR-D45-5/9 | Phase 1 · **Waves 3 (dialog), 4 (kill switch)** |
| **`AC-D45.7`** (docs cleaned in the same batch) | `S38`; System Components (docs rows); Non-Functional (doc freshness); AR-D45-7 | Phase 2 · **Wave 5** |
| **`AC-D45.8`** (no dangling references; suite green; recorded test book) | `S36` + `S37` (**including the wave-membership rule: an assertion's subject and its removal live in the same wave**); the plan's test book (5 deleted / **7** adjusted / 1 added); AR-D45-2/3/8 | Phase 1 · **Waves 1–4** + Phase 2 · **Wave 6** |
| **`AC-D45.9`** (history preserved; marker + tech stack intact) | `S29`–`S38` relationship table; *Supersessions* below | — (recorded; no production edit) |
| **`AC-D45.10`** (Stop/Target columns gone; storage + no-migration guarantee) | `S33`; Data Model (view model + `positions`/`trade_groups` unchanged); AR-D45-4 | Phase 1 · **Wave 3**; Phase 2 · **Wave 6** |
| **`D45.1`–`D45.6`** (the six requirements) | `S29`–`S33`, `S36`, `S38` | Phases 1–2 |
| **Journey 38** (steps 1–9; postconditions; the edge cases: stale dock state, orphan shortcut, TWS–cancel, legacy stop/target rows, pre-D45 DB, disconnected) | `S31`, `S33`, `S34`, `S35`, `S38`; Non-Functional (data safety, platform side effect); Data Model | Phase 1 · **Waves 1–4** + Phase 2 · **Waves 5–6** |
| **A79 / A86 / A87 / A88 / A89 / A90** (owner-decided defaults) | `S34` / `S34` / `S33` / `S31` / `S32` / `S35`; Frozen interfaces | Phases 1–2 |
| **A80 + DG76** (`ibkr/orders.py`: delete or retain) | `S29` — **retained**, with the docstring note; DG76 resolved | Phase 1 · **Waves 2–4** (no task touches the module's API) |
| **A81 / A85** (test-book and doc scope) | `S36`, `S38`; the plan's test book | Phases 1–2 |
| **R68 / R69 / R70 / R71 / R72 / R73 / R74 / R75** | AR-D45-1 / 2 / 3 / 7 / 8 / 9 / 5 / 4 | Phases 1–2 |
| **DG75** (the "fourth deleted file" count) | Resolved by supersession — the book is now **five named** whole-file deletions (`AC-D45.8`); no deletion rests on a count | Phase 1 · **Waves 2–4** |
| **DG77** (assertions invalidated in files that stay) | `S37` + AR-D45-4/5; the plan's test book names every adjusted assertion | Phase 1 · **Waves 1–4** |
| **D1–D44** | `[no relationship]` — **not reopened**; only the clauses D45 names are superseded/revised | — |

---

## Supersessions and non-changes (recorded, never silent)

1. **`AC-D38.2` / `AC-D38.3` — SUPERSEDED BY D45.** The digest's grouping and its no-entitlement state have no
   surface left (`S34`); `AC-D38.6`'s green-suite rule stands for the surviving half (markers + dividend merge:
   `AC-D38.1`, `.4`, `.5`).
2. **`AC-D41.1`'s Portfolio clause — REVISED.** "Portfolio section (Close / Close Group / Flatten All + the
   SL/TP dialog) still renders" → "renders **view-only** (no close/flatten control, no SL/TP dialog, no
   Stop/Target columns)" (`S30`, `S32`, `S33`).
3. **`AC-D41.4` (retained-order-path / `ref_price`) — REVISED and MOOT in part.** No order-related surface is
   retained: the SL/TP dialog goes too, nothing builds or transmits an order (`S30`), and `ref_price` has no
   consumer — `_ref_price_for` is deleted while its `_symbol_last_prices` source stays for the P/L path.
   D41's "Scope — KEEP: order machinery" bullet is **superseded**: `ibkr/validation` deleted; `ibkr/orders`
   retained **without a caller** (`S29`, A80/A90); only the fail-fast port check and the inert inbound
   observers remain.
4. **D26 order-entry clauses — MOOT / SUPERSEDED.** `AC-D26.3` (SL/TP labelling branch) is **moot** (`S32`);
   `AC-D26.8` (kill switch: `reqGlobalCancel` + per-ID cancels + pre/post counts) is **superseded in full**
   (`S31`); `AC-D26.7` (validate-order gate) and `AC-D26.9`'s order-entry/registry clauses have **no control to
   exercise**; `AC-D26.4`/`AC-D26.6` were already control-less after D41. **Retained:** the fail-fast port
   check + connection badge (`AC-D26.5`) and the connection half of the error alerts (`S35`).
5. **`D21.13` — reviewed, NOT superseded.** It governs the right dock's title-bar toggle and the Portfolio
   panel, which **stays** (view-only). No `AC-D21.13.*` clause names a close/flatten, kill-switch or SL/TP
   control; the frozen *Portfolio collapse header* contract is unchanged.
6. **`AC-D18.6` / D18 width model — NOT superseded, re-derived.** The table drops 10 → 8 columns, which only
   **reduces** its width demand; `RIGHT_DOCK_MIN_WIDTH` keeps its value; the D18 cap/visibility criteria stand.
7. **Glossary.** "Live-order path" **revised** (no live-order path exists); **new** rows "Kill switch" and
   "SL/TP dialog" record both as **removed**. Recorded by Requirements; no production consequence.
8. **The cancelled-draft numbers (`S29`–`S32`, `FI-D45-1`, `AP-D45-*` of the previous, never-activated D45
   draft) carry no authority**; `FI-D45-1` in particular is **moot** — the SL/TP dialog it described as
   "retained with no entry point" is now **deleted** (A89/`S32`). The refreshed `docs/codebase-map.md` no
   longer names `_kill_switch` or `StopLossTargetDialog` as retained (it did in the previous draft's
   annotations — DG77 item 1).
9. **Explicit non-changes (recorded so they are not read as omissions):** the chart render stack, `ui/dock_layout.py`
   constants (values), `ui/watchlist_panel.py`, the chart load/backfill path, alarms, drawings, studies,
   pop-outs, D39/D40/D42/D43/D44 behaviour, `data/db.py`'s schema and migrations, `data/models.py`'s fields,
   the `_upsert_position` upsert, `ibkr/orders.py`'s API, `ibkr/pacing.py`, `config/settings.py` (the now-dead
   `MAX_ORDER_NOTIONAL` constant is **not** deleted — outside the owner's inventory; noted in the plan), and
   the pinned dependency set (**no new dependency**).
10. **The D45 register's suggested "three-signal loop" is recorded as a DEVIATION, not as pending work.** The
    register's correction record (`requirements.md:4178`–`:4179`) and `DG77` item 4 describe the
    `tests/test_dock_d18_region.py` edit as the five-signal loop "shrinking to three". D45 removes **all
    five** signals, so no signal survives and a three-signal loop cannot exist in any wave. The loop is
    **deleted** (wave 2) and the file's remaining assertions stay; `AC-D45.8` requires the file to be
    *adjusted* and is satisfied. Recorded here, in the plan's § Exactness note, and in `docs/plan_notes.md`
    `RG-D45-1` so no later worker "restores" the three close signals.
