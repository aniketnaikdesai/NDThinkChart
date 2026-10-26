# Order-code audit — independent inventory (pre-D46)

**Scope:** audit only. No code, test, plan or requirement was modified. This file is the only
artifact of the run.
**Method:** produced from the source tree first (grep over `ui/ services/ data/ ibkr/ config/ main.py`,
`tests/`, the SQLite schema, config defaults, assets, packaging, docs and build residue), then
diffed against the requirements' `D46.9` / `AC-D46.9` inventory. Section 2 was written after
section 1 and does not feed back into it.
**Disclosure:** `docs/codebase-map.md` is the mandated first read for this agent, and it already describes the
P5/D46 *target* (the narrow 17-name scope, as it turns out — § 2.5). I treated it as hypotheses and re-derived
every row below from source; I did **not** open `requirements.md`'s D46 section, `plan.md` § P5 or
`architecture.md` § P5 until § 1 was written.
**Baseline:** working tree at `main` + the delivered-but-uncommitted D45 removal (`git status`:
`ibkr/news.py`, `ibkr/validation.py`, `ui/news_digest_dock.py`, `ui/trade_context_menu.py`,
`ui/stop_loss_target_dialog.py` and five suites already deleted).

---

## Verdict

**The inventory is close but not complete: it misses 3 order-related items, leaves 1 order-named comment and 3
residue/judgement items unnamed; it over-includes none; 2 adjacent statements (R10, A99) need correcting; and the
plan/architecture/map it will be built from are a previous revision of it.**

- **25 DELETE / 12 RETAIN is the right shape.** Rows 1–10 reproduce my live-chain findings one-for-one (module,
  builders, registry, overrides, signals, connects, slots, `_on_order_error`, import, `data.models.UserOrder`).
  Rows 11–18 reproduce, unprompted, the three dead utilities I flagged (`OrderRateLimiter`, `MAX_ORDER_NOTIONAL`,
  the order-fill blip) and the stop/target storage. **I found no DELETE row that should be retained.**
- **Misses (3 genuine, all small):** the stale SL/TP-dialog comment in `ibkr/account.py:39-42`; the
  `_on_order_error` call inside the retained D45 removal guard (`tests/test_d45_removal.py:523`), which D46.5's
  test book does not name; and `usage.md:167`, which still runs `tests/test_order_builders.py`. Detail in § 2.3.
- **Residue/judgement (3 items):** stale bytecode (`orders.cpython-311.pyc`, `order_book.cpython-311.pyc`, the
  deleted test suites' `.pyc`s); the Sep-18 `dist/` bundle plus the dev `charting_app.sqlite3`; and the order-named
  tokens inside `tests/test_d41_removal.py`'s old guard. DG87 covers the `__pycache__` but dispositions it
  "ignore", not "delete".
- **Two adjacent statements need correcting, not removing.** **R10's evidence is false**: `TradeGroup`, the `trade_groups` table
  and `position_group_map` have **zero** production consumers; the display grouping R10 describes is
  `services/strategy_detection.py` + `Position.id`, not those entities. **A99's "could only ever hold NULL" is
  overstated**: a pre-D45 row that never receives another live update keeps its old stop/target bytes; they are
  invisible and unsettable, so the drop is still defensible — but the sentence is not true as written (§ 2.4).
- **The headline risk is not the table — it is the documents that will drive the build.** `docs/plan.md` § P5,
  `docs/architecture.md` § P5 and `docs/codebase-map.md` were last written **18:52 / 18:52 / 18:46**, the requirements'
  expansion landed **18:57**, and the approved plan review is stamped **18:53**. All three still encode the
  **pre-expansion** 17-name scope and explicitly **forbid** the D46.10–D46.12 deletions (`IdManager.reserve`,
  `order_limiter`, `MAX_ORDER_NOTIONAL`, "no schema change, no migration", `tests/test_stop_loss_target.py`
  unchanged). Built from the activated plan as it stands, the 25-row inventory would **not** be executed.
  § 2.5 lists every contradicting line. `docs/tasks/task-graph.json` still holds only P4 tasks, so fixing the
  documents now costs nothing.
- **Retain rows R1–R9, R11, R12 verify.** `IdManager` is load-bearing (`get_id()` at
  `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`, `ui/main_window.py:1095`), `nextValidId` is the
  CONNECTED transition (`ibkr/client.py:182-193`), and `classify_error`/`error_msg` gate every TWS error. The
  per-row evidence check is § 2.6. Nothing innocent was over-cut.

---

## 1. Blind inventory (produced from source before reading `D46.9`)

**Two framing facts, verified by grep over `ui/ services/ data/ ibkr/ config/ main.py`:**

- **The chain is live-loaded but behaviourally inert.** `ibkr.orders.orders` is constructed at import
  (`ui/main_window.py:36`); the only production write to it is `order_registry.update_status(...)` inside
  `_on_order_error` (`:1559`), which is itself only reachable through a registry lookup that can never be non-empty
  because `Orders.register()` has **no production caller**. Every `get()` returns `None`.
- **`placeOrder` / `cancelOrder` / `reqGlobalCancel` have zero definitions and zero call sites** in production
  (they are inherited `EClient` methods). That absence is an invariant to preserve, not an item to delete.

Legend — **Substance:** `order` = order wiring in substance; `general` = general code that merely
touches orders and must be retained; `name-only` = the token is a coincidental substring or a
historical comment. **Reach:** who calls/reads it in production.

### A. `ibkr/orders.py` — the module (141 lines)

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| A1 | `ibkr/orders.py:1` | Module docstring: "Pure order builders and open-order tracking for Phase 5 Order Entry." | imported by `ui/main_window.py:36` | order | delete |
| A2 | `ibkr/orders.py:10-24` | `UserOrder` dataclass — `order_id, symbol, action('BUY'/'SELL'), total_qty, order_type('MKT'/'LMT'/'STP'), lmt_price, aux_price, status, parent_id, oca_group, transmit=True, contract: ibapi.Contract` | only `Orders.register/get/update_status`; no production reader of any field | order | delete |
| A3 | `ibkr/orders.py:34-40` | `Orders.market_order(action, qty)` → `ibapi.Order` MKT | no production caller | order | delete |
| A4 | `ibkr/orders.py:42-49` | `Orders.limit_order(action, qty, price)` → LMT | no production caller | order | delete |
| A5 | `ibkr/orders.py:51-58` | `Orders.stop_order(action, qty, price)` → STP (`auxPrice`) | no production caller | order | delete |
| A6 | `ibkr/orders.py:60-115` | `Orders.bracket_order(...)` — parent LMT `transmit=False`; STOP child + LMT child with `parentId`, shared `ocaGroup=f"bracket-{id}"`, `ocaType=1`, children trade opposite the entry side, last child `transmit=True` | no production caller (tests only) | order | delete |
| A7 | `ibkr/orders.py:118-137` | Registry: `register`, `get`, `update_status`, `clear_filled`, `all` (in-memory `Dict[int, UserOrder]`) | `register`/`clear_filled`/`all`: no production caller. `get` ← `ui/main_window.py:1546` and `:3227`; `update_status` ← `ui/main_window.py:1559` | order | delete |
| A8 | `ibkr/orders.py:141` | Module-level singleton `orders = Orders()` | constructed at import via `ui/main_window.py:36`; never written | order | delete |

### B. `ui/main_window.py` — consumers

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| B1 | `ui/main_window.py:36` | `from ibkr.orders import orders as order_registry` | top-level import, always executed | order | delete |
| B2 | `ui/main_window.py:595` | `b.open_order.connect(self._on_open_order)` | always wired | order | delete |
| B3 | `ui/main_window.py:596` | `b.exec_details.connect(self._on_exec_details)` | always wired | order | delete |
| B4 | `ui/main_window.py:597` | `b.order_status.connect(self._on_order_status)` | always wired | order | delete |
| B5 | `ui/main_window.py:1543-1549` | `_on_error`'s D26.9 branch: `if order_registry.get(reqId) is not None: self._on_order_error(...); return` + its 5-line comment | `_on_error` ← `b.error_msg` (`:585`); the branch is unreachable in practice because the registry is never populated | order | delete branch + comment; **keep the rest of `_on_error`** |
| B6 | `ui/main_window.py:1551-1561` | `_on_order_error(order_id, error_code, error_string)` — maps 201/103→"Rejected", 202→"Cancelled", else `Error <code>`; writes registry; 12 000 ms `Order #<id> <status>: <msg>` | only B5 (and tests) | order | delete |
| B7 | `ui/main_window.py:2951-2952` | `_on_open_order(orderId, contract, order, orderState)` → `_update_order_status(orderState.status)` | ← `b.open_order` | order | delete |
| B8 | `ui/main_window.py:2954-2957` | `_on_exec_details(reqId, contract, execution)` → `execution.orderId` → `"Filled"` | ← `b.exec_details` | order | delete |
| B9 | `ui/main_window.py:2959-2965` | `_on_order_status(...)` 11-arg slot → `_update_order_status(orderId, status)` | ← `b.order_status` | order | delete |
| B10 | `ui/main_window.py:3226-3229` | `_update_order_status(orderId, status)` → `order_registry.get(...).status = status` | ← B7/B8/B9 | order | delete |
| B11 | `ui/main_window.py:442-443` | Comment: "The Active Trader panel (DOM ladder + order-entry ticket) … are removed" | n/a (comment) | name-only / historical | **judgement:** not code; retaining history is defensible, reword if the batch is scrubbing order vocabulary. Do not sweep into a code deletion. |
| B12 | `ui/main_window.py:1713` | `_attach_live_feed` docstring: "Start the real-time bar stream (+ DOM)." | n/a (docstring) | name-only / stale | **judgement:** reword (DOM no longer exists); not code. |
| B13 | `ui/main_window.py:3065` | Comment: "… the exact mirror of the D28.6 inverse on the close-order path (see below)" — no close-order path exists below | n/a (comment) | name-only / stale | **judgement:** reword. |
| B14 | `ui/main_window.py:572` | `self.sound_service.warm()` | always executed at startup | general (indirect) | retain the call; it is the reachability path for the fill-blip rows (L2–L3) |

### C. `ibkr/bridge.py` — signals

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| C1 | `ibkr/bridge.py:47-49` | `order_status = pyqtSignal(int, str, float, float, float, int, int, float, int, str, object)` + arg comment | emitted only by `ibkr/client.py:405`; connected at `ui/main_window.py:597` | order | delete (with emitter) |
| C2 | `ibkr/bridge.py:51-52` | `open_order = pyqtSignal(int, object, object, object)` (`orderId, Contract, Order, OrderState`) | `ibkr/client.py:412`; `ui/main_window.py:595` | order | delete |
| C3 | `ibkr/bridge.py:54-55` | `exec_details = pyqtSignal(int, object, object)` | `ibkr/client.py:416`; `ui/main_window.py:596` | order | delete |
| C4 | `ibkr/bridge.py:42` | Section comment "# Account & Orders" | n/a | name-only | reword to "# Account" |

### D. `ibkr/client.py` — `EWrapper` overrides

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| D1 | `ibkr/client.py:394-408` | `orderStatus(...)` override — 11 args incl. `whyHeld`/`mktCapPrice`, calls `super()` then emits `bridge.order_status` | TWS callback; emission only on a live order for this clientId (none exist) | order | delete whole override (inherited `EWrapper` no-op remains) |
| D2 | `ibkr/client.py:410-412` | `openOrder(...)` override → `bridge.open_order` | TWS callback | order | delete |
| D3 | `ibkr/client.py:414-416` | `execDetails(...)` override → `bridge.exec_details` | TWS callback | order | delete |
| D4 | `ibkr/client.py:182-193` | `nextValidId(orderId)` override — `super()`, `id_manager.set_next_valid_id(orderId)`, then flips `_connected`/`ConnectionState.CONNECTED`, clears `_last_disconnect_class`, `_set_state(CONNECTED)` | called by TWS on every connect/reconnect (`_do_reconnect` → `start_polling` relies on it, `:178-181`) | **general** | **retain** — this IS the CONNECTED transition (D40), not an order callback. `orderId` is only the seed. |
| D5 | `ibkr/client.py:195-221` | `error(*args, **kwargs)` — signature negotiation incl. `advancedOrderRejectJson` (the ibapi `EWrapper.error` 5th arg) | every TWS error (`b.error_msg` at `:245`) | **general** | **retain** — gates every TWS error. `advancedOrderRejectJson` is field-name-only; dropping it breaks the `super()` call chain. |
| D6 | `ibkr/client.py:228-245` | `classify_error(errorCode)` severity gate + D40.1 502 suppression + `error_msg` emit | every TWS error | **general** | **retain** — see G1 for the comment |
| D7 | inherited `EClient.placeOrder/cancelOrder/reqGlobalCancel` | **not defined anywhere in the repo**; no call sites (`grep` over `ui/ services/ data/ ibkr/ config/ main.py` = 0) | n/a | general (ibapi surface) | retain by absence — nothing to delete; a guard may keep asserting the absence |

### E. `ibkr/id_manager.py` — ID allocation

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| E1 | `ibkr/id_manager.py:8-11` | `set_next_valid_id(order_id)` — monotonic seed | `ibkr/client.py:184` | **general** | **retain** |
| E2 | `ibkr/id_manager.py:13-17` | `get_id()` — the reqId allocator | `ibkr/market_data.py:42,74,90,103`; `ibkr/realtime_bars.py:31`; `ui/main_window.py:1095` | **general** | **retain** |
| E3 | `ibkr/id_manager.py:19-30` | `reserve(n)` — contiguous block reserve | **no production caller** (only `tests/test_id_manager.py`) | order-by-purpose (bracket IDs) | **judgement:** deleting it is safe at runtime; retaining it is also safe. Its docstring is order-only. A wrong "delete the whole module" is the damaging move, not this method. |
| E4 | `ibkr/id_manager.py:22-23` | `reserve` docstring "D26.2: multi-leg orders (brackets) … live order ID" | n/a | name-only (comment) | reword if E3 is retained |

### F. `ibkr/pacing.py` — rate limiting

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| F1 | `ibkr/pacing.py:128-167` | `OrderRateLimiter` token bucket (`try_acquire`, `retry_delay_s`, `reset_for_tests`) | **no production caller** | order | delete (or retain as dead — it is the only order-named class left in the module) |
| F2 | `ibkr/pacing.py:172` | Global `order_limiter = OrderRateLimiter()` | no production caller; reset in `tests/conftest.py:143,146` | order | delete with F1 |
| F3 | `ibkr/pacing.py:131-134` | Docstring "Orders were throttled by the realtime-bar budget…" | n/a | name-only | remove with F1 |
| F4 | `ibkr/pacing.py:7-19, 22-126, 171` | `PacingExceeded`, `PacingManager`, `pacing_manager` | `ibkr/market_data.py`, `ui/main_window.py`, `ibkr/subscription_manager.py` | general | **retain** |

### G. `ibkr/error_codes.py`

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| G1 | `ibkr/error_codes.py:1-22` | `classify_error` — the severity gate for every TWS error; contains `201`/`103` as `fatal`; `:14-18` comment says order errors route "to the registry as Cancelled" | `ibkr/client.py:228` | **general** | **retain**; reword only the `:14-18` comment (the `202`/registry sentence is now false). No code change. |

### H. `config/settings.py`

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| H1 | `config/settings.py:8-24` | `LIVE_PORT`, `check_live_port()` — fail-fast unless port 7496; message "NDThinkChart trades live only" | `main.py:36` | general (connection/port guard) | **retain**; wording is trading-flavoured, semantics are not order code |
| H2 | `config/settings.py:37-39` | `MAX_ORDER_NOTIONAL = 25000` + D26.7 `validate_order()` comment | **no reader** (`grep` = 0 outside tests/allow-lists) | order (dead) | delete (with its comment) |
| H3 | `config/settings.py:3-6,26-35,41-53` | host/port/client-id, pacing budgets, `MAX_POPOUTS`, `SESSION_BAR_CAP`, `MIN_INTRADAY_SESSIONS` | used throughout | general | retain |

### I. `data/models.py`

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| I1 | `data/models.py:104-116` | `UserOrder` dataclass — duplicate of A2 (no `contract` field) | **no production consumer**; only `tests/test_ui_smoke.py:48` | order | delete |
| I2 | `data/models.py:86-87` | `Position.stop_loss`, `Position.take_profit` | read/written only by persistence (`ui/main_window.py:3093-3094,3132-3165,3184-3218`) | order-intent (vestigial) | **judgement:** no setter or display remains; the values are never populated (live path writes `None`). Deleting them is a schema change; keep-or-delete is the owner's call. |
| I3 | `data/models.py:98-99` | `TradeGroup.stop_loss`, `TradeGroup.take_profit` | `TradeGroup` itself has **no production consumer at all** | order-intent (vestigial) | **judgement** (see K2) |

### J. `ibkr/account.py`

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| J1 | `ibkr/account.py:32-34` | `Position.stop_loss/take_profit/trade_group_id` (a second Position model) | `ui/main_window.py:3036` imports `build_position_from_ib` | order-intent (vestigial) | **judgement** with I2 |
| J2 | `ibkr/account.py:57-66,78-81` | `build_position_from_ib(..., stop_loss, take_profit, trade_group_id)` — constructs J1 | `ui/main_window.py:3036` | order-intent | **judgement** with I2 |
| J3 | `ibkr/account.py:39-42` | Comment: "the SL/TP dialog keys `UPDATE positions … WHERE id=?` on it" | n/a | name-only / stale | reword (the dialog is deleted in D45) |

### K. SQLite schema / persistence — `data/db.py`

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| K1 | `data/db.py:107-124` | `positions` table — incl. `stop_loss REAL`, `take_profit REAL`, `trade_group_id INTEGER REFERENCES trade_groups(id)` | `ui/main_window.py:3132-3220` (read/upsert) | order-intent for the two SL/TP columns; `trade_group_id` is grouping metadata | **judgement:** the SL/TP columns are vestigial order parameters; `trade_group_id` is display grouping (currently always NULL). Migration/`ALTER` would be needed — not a one-line delete. |
| K2 | `data/db.py:125-133` | `trade_groups` table (`name, strategy_type, underlying, stop_loss, take_profit, collapsed, created_at`) | **no reader and no writer anywhere** (`grep trade_groups` = schema + one `REFERENCES` only) | order-intent / dead | **judgement:** would be a clean delete (table + `TradeGroup` + `positions.trade_group_id` + `position_group_map`), but it is schema, not code. |
| K3 | `data/db.py:135-139` | `position_group_map(ibkr_position_id, trade_group_id)` | **no reader and no writer anywhere** | order-intent / dead | **judgement** with K2 |
| K4 | `data/db.py:264-292` | `watchlist.sort_order` / `reorder` loop (`new_order`) | watchlist writes | **name-only** | **false positive — do not touch** |

### L. Services

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| L1 | `services/sound_service.py:9` | Module docstring: "*Order-fill blip* …" | n/a | order | delete the bullet with L2 |
| L2 | `services/sound_service.py:75-86` | `render_fill_blip()` — the order-fill tone (987.77→1318.51 Hz sweep) | **no production caller**; `tests/test_sound_service.py:14,46,51,57` only | **order** | **delete** (owner asked for order code gone; this is order-fill audio) |
| L3 | `services/sound_service.py:114-123` | `ensure_sound_files()` writes `order_fill.wav` and returns `{"alarm":…, "fill":…}` | **reachable**: `ui/main_window.py:572` → `warm()` → `ensure_sound_files()` writes the file at every startup | order | delete the fill path, keep the alarm path |
| L4 | `services/sound_service.py:170-175` | `SoundService.play_fill()` | **no production caller** | order | delete |
| L5 | `services/sound_service.py:127-175` | `SoundService` alarm path (`play_alarm`, `warm`) | `ui/main_window.py:572`; alarm triggers | general | retain |
| L6 | `services/ict_service.py:114,139,258` | ICT **order blocks** (`order_blocks`, `_order_blocks`) | studies/ICT overlay | **name-only** | **false positive — do not touch** |
| L7 | `ui/overlays/ict_overlay.py:44-62` | `_render_order_blocks` (draws ICT order blocks) | `ui/overlays/ict_overlay.py:34` | **name-only** | **false positive — do not touch** |
| L8 | `services/ict_service.py:128-150,515-547`, `ui/overlays/ict_overlay.py:119` | ICT **killzones** (`show_killzones`, `_killzones`, `_close_killzone`, `_render_killzones`) | ICT study | **name-only** ("kill" substring) | **false positive — do not touch** |
| L9 | `services/alarm_monitor.py:87-88,139` | `_order_by_recency` | alarm monitor | **name-only** | **false positive** |
| L10 | `services/strategy_detection.py:1-198` | Option-strategy grouping (PCS/PDS/CCS/CDS/IC) for the Portfolio display; consumes `Position.qty/strike/right` | `ui/active_portfolio_panel.py:23` → `:247` | **not order code** (display grouping) | **retain** — deleting it removes the Strategy/Group columns |
| L11 | `ibkr/subscription_manager.py:23-26` | `RT_BARS`, `MARKET_DATA`, `S0_TICKS` type tags | live | general | retain |
| L12 | `ibkr/contracts.py`, `ibkr/utils.py` | Contract construction (`secType`), date parsing | chart load | general | retain |

### M. Tests

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| M1 | `tests/test_order_builders.py` (1-200) | 17 cases: MKT/LMT/STP builders, bracket structure/OCA/transmit, `UserOrder` fields, registry | tests only | order | delete whole file |
| M2 | `tests/test_order_rejections.py:15,30-37,41-75` | `_fresh_registry`, `_register`, `test_rejected_order_updates_registry_and_status`, `test_cancelled_order_updates_registry`, `test_non_order_error_untouched` | tests | order | delete the registry cases; **keep** the `classify_error` cases (`:79-92`) and add/keep a 201/103/202 surfacing case |
| M3 | `tests/test_order_rejections.py:5-9` | Docstring naming `_on_order_error` | n/a | name-only | update |
| M4 | `tests/test_ui_smoke.py:48` | `assert hasattr(data.models, "UserOrder")` | tests | order | delete line |
| M5 | `tests/test_d28_pacing.py:14,97-101` | `OrderRateLimiter` import + `test_order_limiter_allows_burst_then_denies` | tests | order | delete if F1 goes |
| M6 | `tests/conftest.py:143,146` | `order_limiter.reset_for_tests()` (autouse fixture) | every test | order | delete lines if F1 goes |
| M7 | `tests/test_id_manager.py:3` + `reserve` cases (`:8,18,28,34,79`) | Docstring "bracket orders consume three order IDs" + `reserve` coverage | tests | order-by-purpose | **judgement** with E3 |
| M8 | `tests/test_d45_removal.py` | The D45 static/behavioural guard: `_FORBIDDEN` list, `_SURVIVORS` allow-list (currently contains all eight order names at `:145-149`), transmit recorders, walkthrough calling `win._on_order_error(1, 201, …)` at `:523` | test harness | guard, not order code | **retain + update** (move the names to forbidden, repoint the walkthrough); never delete the guard |
| M9 | `tests/test_d41_removal.py:97` | Token list containing `_on_order_place_requested`, `_place_order`, `dom_btn` | test harness | guard | retain |
| M10 | `tests/test_stop_loss_target.py` (whole) | `Position`/`TradeGroup` SL/TP model fields | tests | order-intent | **judgement** with I2/I3 |
| M11 | `tests/test_account.py:36-37,62-63,85-86,103-109` | `build_position_from_ib(..., stop_loss=None, take_profit=None)` + assertions | tests | order-intent | **judgement** with J1 |
| M12 | `tests/test_d27_account_partial_window.py:68`, `test_d27_account_scoping.py:68`, `test_d27_position_id.py:99` | Raw `INSERT INTO positions (…, stop_loss, take_profit, …)` | tests | order-intent (schema) | **judgement** with K1 |
| M13 | `tests/test_strategy_detection.py:30-31` | Fake `Position` accepts `stop_loss/take_profit` kwargs | tests | incidental | **judgement** with J1 |
| M14 | `tests/test_sound_service.py:14,46,51,57` | `render_fill_blip` tests | tests | order | delete with L2/L4 |

### N. Build artifacts / shipped state

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| N1 | `ibkr/__pycache__/orders.cpython-311.pyc` | Compiled copy of A1–A8 | not importable from `__pycache__` without source | order (residue) | delete with the source (leave no stale bytecode) |
| N2 | `ibkr/__pycache__/order_book.cpython-311.pyc` | Compiled `ibkr/order_book.py` — **the source file no longer exists**; a Level-I/II market-depth book model ("Pure order-book model for Level I/II market depth", `updateMktDepth`). Market depth, not order transmission, but order-named and already orphaned | none | order-adjacent (dead) | **judgement:** delete as residue; it is not a live module to audit |
| N3 | `ibkr/__pycache__/tick_history.cpython-311.pyc` | Compiled `ibkr/tick_history.py` — source deleted (D41 footprint) | none | not order | delete as general residue (not this batch's subject) |
| N4 | `dist/NDThinkChart/` (built 2026-09-18) + `dist/NDThinkChart/NDThinkChart` (93 MB binary) | PyInstaller bundle predating D45/D46. `strings` finds none of `ibkr.orders`/`order_book`/`placeOrder` (the PYZ is compressed), so its contents cannot be asserted from the outside | user-launchable bundle | order-adjacent (unverifiable) | **judgement:** rebuild after D46 rather than edit the binary; a stale bundle is a distribution problem, not a source delete |
| N5 | `charting_app.sqlite3` (61 KB dev DB) | Contains `positions`, `trade_groups`, `position_group_map` tables; all three are **empty** (0 rows) | dev DB; `config/paths.py` points production elsewhere | order-intent (schema only) | **judgement** with K2/K3 |
| N6 | `NDThinkChart.spec`, `packaging/`, `build/` | PyInstaller spec — `datas` only `config/theme.qss`, `hiddenimports=[]` | packaging | general | retain (no order references) |

### O. Config / theme / assets

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| O1 | `config/theme.qss` | App stylesheet — only `border`/`fill` cosmetics; no order/ticket/DOM selector | app-wide | **name-only** | **false positive** |
| O2 | `config/paths.py` | DB path resolution | `data/db.py` | general | retain |
| O3 | Shipped audio assets (`.wav/.mp3/.ogg`) | **none in the repo** — the order-fill tone is synthesised at runtime (L2/L3) | n/a | — | nothing to delete; the runtime-generated `order_fill.wav` lives in the temp dir (`services/sound_service.py:110-123`) |

### P. User-facing docs

| # | Location | What it is | Reach | Substance | Disposition |
|---|---|---|---|---|---|
| P1 | `USAGE.txt:84-90` | "Orders: the app places, cancels and closes nothing…"; "Stop and target values … can no longer be set or displayed"; "IBKR rejections and cancellations appear in the status bar…" | shipped doc | order-topic prose; the **order** half is already post-D46-accurate | **retain**; `:88`'s "the database columns are kept" is false under D46.12 and must become "dropped" (DG84/D46.13) |
| P2 | `usage.md:102,136-139,154,206` | "View-only: … no order entry, close or cancel controls"; SL/TP columns kept/no migration; "the app places, cancels and closes nothing" | shipped doc | order-topic prose | **retain** except `:154` ("columns are kept (no migration)") which D46.12 reverses — update in this batch |
| P3 | `usage.md:160-168` | pytest example still lists `tests/test_order_builders.py` | shipped doc | order | update after M1 is deleted |
| P4 | `docs/*`, `dev_docs/*` | See § 4 — historical/planning docs, not code | n/a | mixed | **judgement**, listed separately |

---

## 2. Requirements diff (`D46.9` / `AC-D46.9`)

The requirements carry **25 numbered DELETE rows** and **12 RETAIN rows (R1–R12)**. Two counting notes: DELETE
row **24 is dispositioned RETAIN** (the historical comments at `ui/main_window.py:442-443, 612`), and DELETE row 3
(`from ibapi.order import Order`) is a line inside row 1's file — so "25" is a table-row count, not 25 distinct
deletions. Neither changes the substance.

### 2.1 Where the two inventories agree

| Requirements row | My row(s) | Agreement |
|---|---|---|
| 1, 2, 3 (module, builders/registry/singleton, `ibapi.order` import) | A1–A8 | exact |
| 4 (`orderStatus`/`openOrder`/`execDetails` overrides) | D1–D3 | exact |
| 5 (`order_status`/`open_order`/`exec_details` signals) | C1–C3 | exact |
| 6 (three connects) | B2–B4 | exact |
| 7 (four slots) | B7–B10 | exact |
| 8 (`_on_order_error` + `_on_error` branch + comment) | B5, B6 | exact (incl. "unreachable") |
| 9 (`order_registry` import) | B1 | exact |
| 10 (`data.models.UserOrder`) | I1 | exact |
| 11 (`OrderRateLimiter`, `order_limiter`, docstring) | F1–F3 | exact — a genuine expansion beyond the live chain |
| 12 (`MAX_ORDER_NOTIONAL` + comment) | H2 | exact |
| 13 (fill blip: `render_fill_blip`, `BLIP_DURATION`, `_fill_effect`, `play_fill`, `"fill"` key, `order_fill.wav`, docstring) | L1–L4 | exact |
| 14 (`IdManager.reserve` + D26.2 docstring) | E3, E4 | exact |
| 15, 16 (`positions` / `trade_groups` stop/target columns) | K1, K2 | exact |
| 17 (`Position`/`TradeGroup` model fields) | I2, I3 | exact |
| 18 (`ibkr.account.Position` fields + factory params) | J1, J2 | exact |
| 19–21 (live path `stop_loss=None`, SQL columns/placeholders, row-index shift) | I2/K1 `Reach` (I folded these into the persistence rows rather than itemising; row 21's **index shift** is the sharpest detail in the requirements and I had not spelled it out — it is correct: `trade_group_id` moves `row[14]` → `row[12]`) | covered |
| 22 (`:3065`, `:3096`, `:3123` comments) | B13 covered `:3065`; the other two are real and I had folded them into J3/K1 rather than listing them — **theirs is better** | covered |
| 23 (`classify_error` comment) | G1 | exact |
| 24 (historical comments `:442-443`, `:612`) | B11 covered `:442-443`; `:612` I missed — **theirs is better** | covered |
| 25 (test book) | M1–M14 | exact on the named files; the `:523` repoint is the one omission — § 2.3 M-2 |
| R1–R9, R11, R12 | B5-tail, D5/D6, G1, D5, D4/E1, E2, F4, L6/L7, K4, (implicit), L5 | evidence independently verified — § 2.6 |
| R10 | I3, L10 | **rationale false for `TradeGroup`/`trade_groups`/`position_group_map` — § 2.4 C-1** |

### 2.2 Where the requirements have a row I did not itemise

These are not defects in their inventory; they are places my table folded a detail or missed a comment:

- `ui/main_window.py:612` — "the order path is gone" (I had only `:442-443`).
- `ui/main_window.py:3096` / `:3123` — the SL/TP-dialog comments on the persistence path (I folded into K1).
- The `row[12]/row[13]` → `row[12]` **index shift** (DG85). I named the risk ("indices shift") but did not pin the
  exact silent-failure mode; theirs does.
- `services/sound_service.py:22` `BLIP_DURATION` and `:151`'s `_fill_effect` mapping (I listed the behaviour, not the
  line).
- `tests/test_stop_loss_target.py` as a **whole-file deletion** (I had it as "judgement" under I2/I3; now that
  D46.12 drops the fields, whole-file deletion is the only coherent disposition).

### 2.3 What the requirements' inventory misses

| # | Location | What it is | Reach | Substance | Why it matters |
|---|---|---|---|---|---|
| **M-1** | `ibkr/account.py:39-42` | Comment: *"the SL/TP dialog keys `UPDATE positions … WHERE id=?` on it"* | n/a (comment on the live `Position.id` field) | **order** (stale order prose) | D46.6's comment sweep is scoped to the `ui/main_window.py` persistence comments and `sound_service`; this additional stale "SL/TP dialog" reference is in neither the DELETE table's row 22 nor AC-D46.6's grep. It names a deleted dialog on a live field. Rewrite (one line). |
| **M-2** | `tests/test_d45_removal.py:22` (docstring bullet), `:523` (`win._on_order_error(1, 201, "Order rejected (walkthrough)")`) | The retained removal guard calls the method wave 1 deletes | test harness | **order** (guard call) | D46.5's book says only "survivor allow-list shrunk, forbidden set extended". Architecture `S44` and the map both say the `:523` call **must be repointed in wave 1**, or the guard raises `AttributeError` and the suite goes red. D46.5 must name it; as written, the requirements' own AC-D46.5 ("suite green") is unsatisfiable by the book it lists. |
| **M-3** | `usage.md:167` | The "Phase 10 core logic tests" pytest command still includes `tests/test_order_builders.py` | shipped doc | **order** (doc line) | `architecture.md` AP-D46-9 catches it; requirements D46.6/AC-D46.6's list and grep terms (`ibkr/orders.py`, `order registry`, `NOT be deleted`, `routes it to the registry`, `Order-fill`, `SL/TP dialog`) do not, so the measurement passes while the command is broken. Add `test_order_builders` to the grep terms. |
| **M-4** | `ibkr/bridge.py:42` | Section comment `# Account & Orders` | n/a | name-only | Their own S44 counts this line as one of the four `Orders` occurrences and notes it is invisible to both nets, but no row dispositions it. After D46 the bridge has no order signals and the comment is wrong. Reword (one line); harmless if left. |
| **M-5** | `tests/test_d41_removal.py:97` | Forbidden-token list containing `_on_order_place_requested`, `_place_order`, `dom_btn` | test harness | name-only | D46.5 says "no other test file changes", so this file keeps order-named symbols. Harmless (a historical guard list), but it falsifies D46.9's "no order-named symbol exists outside those two sets". Either add the file to the inventory as a retain-with-reason or scope AC-D46.9 to *live* symbols. |
| **M-6** | `ibkr/__pycache__/orders.cpython-311.pyc`; `ibkr/__pycache__/order_book.cpython-311.pyc`; `tests/__pycache__/{test_order_builders,test_order_entry_mkt,test_order_entry_side,test_order_validation,test_d41_retained_order_path,test_kill_switch}.cpython-311-pytest-9.1.1.pyc` | Stale bytecode, incl. a compiled copy of the module D46 deletes and an orphan from the earlier-deleted `ibkr/order_book.py` | none (CPython 3.11 does not import `__pycache__`-only modules; the `ModuleNotFoundError` measurable is unaffected) | order (residue) / order-adjacent (`order_book` is a market-depth model, not order transmission) | **Covered only by DG87**, whose resolution is "scope the scan to tracked source and treat `__pycache__` as untracked residue". That is defensible for a scan, but the owner asked for the code **deleted**; deleting stale bytecode is free and removes the exact "looks like a surviving module" trap DG87 describes. Recommend a cleanup step in the batch (low risk, not a requirement). |
| **M-7** | `dist/NDThinkChart/` (built 2026-09-18), `charting_app.sqlite3` | Pre-D45 PyInstaller bundle; dev DB carrying the `positions`/`trade_groups`/`position_group_map` schema (all three empty) | user-launchable bundle; dev only | order-adjacent (judgement) | A stale bundle embeds whatever the Sep-18 tree held; `strings` cannot prove its PYZ contents, so this is **unverifiable from outside**. The correct disposition is "rebuild after D46", not a source delete. The dev DB is a schema sample, superseded by the D46.12 migration test. Named for completeness; neither is order code. |

**Count:** 3 genuinely order-related misses (**M-1**, **M-2**, **M-3**), 1 name-only comment (**M-4**), 3
residue/judgement items (**M-5**–**M-7**). None of them is a live order path the app can execute.

### 2.4 What it includes that should not be cut — and the two rows that need correcting

**No DELETE row should be retained.** I checked each one against production reachability:

- Rows 1–10: the chain is inert (no `register()` caller) and `ibkr.orders`' only importer is
  `ui/main_window.py:36`. Safe.
- Row 11 (`OrderRateLimiter`/`order_limiter`): **zero** production readers (`grep` finds only `tests/conftest.py:143,146`
  and `tests/test_d28_pacing.py:14,97`). Safe; deleting requires the two conftest lines and the one test.
- Row 12 (`MAX_ORDER_NOTIONAL`): **zero** readers. Safe.
- Row 13 (order-fill blip): `play_fill` has **zero** callers; the only runtime touch is `ensure_sound_files()` writing
  `order_fill.wav` to the temp dir via `warm()` at `ui/main_window.py:572`. Removing it changes a temp-file side
  effect only. Safe.
- Row 14 (`reserve`): **zero** production callers (`tests/test_id_manager.py` only). Safe; the module itself must
  stay.
- Rows 15–21 (stop/target storage): safe at runtime, with the caveat in **C-2** below.

**C-1 — R10's evidence is false.** R10 says `TradeGroup`, `trade_group_id` and "strategy grouping" are
"display-only strategy grouping". Verified:

- `TradeGroup` (the dataclass) has **no production consumer** — `grep -rn "TradeGroup" ui/ services/ data/ ibkr/`
  returns only its own definition in `data/models.py:93`.
- The `trade_groups` table has **no reader and no writer** — no `INSERT INTO trade_groups`, no `SELECT … FROM
  trade_groups` anywhere in production.
- `position_group_map` has **no reader and no writer** either.
- The Strategy/Group columns come from `ui/active_portfolio_panel.py:247` → `services/strategy_detection.py` →
  `Position.id`, **not** from `trade_groups`.
- `positions.trade_group_id` is written on every upsert from a `Position` whose `trade_group_id` is the dataclass
  default `None` (`data/models.py:88`; `_on_position_update` never sets it, and `_upsert_position` writes
  `excluded.trade_group_id` at `ui/main_window.py:3186,3200`), so the column is always `NULL` in practice.

So R10 is **right to keep `Position`/`positions`/the Portfolio view (R11)** but wrong about `TradeGroup`,
`trade_groups` and `position_group_map`: they are dead storage, and AC-D46.9's "each RETAIN entry still has its
named consumer" fails for them. Keeping them is harmless (and `tests/test_db_schema.py:22-23` asserts the two tables
exist, so deleting them would widen the test book) — but the **rationale** should say "dead, retained to avoid
widening the batch", not "display-only strategy grouping". This is a documentation correction, not an over-cut.
It is also the one place where an honest "unclear" beats a confident "retain for display".

**C-2 — A99's justification overstates, and the destructive step is the one place to be careful.** A99 says the
columns "could only ever hold `NULL`". Trace:

- `_on_position_update` (`ui/main_window.py:3032`) builds `Position(..., stop_loss=None, take_profit=None)`
  (`:3093-3094`) and `_upsert_position`'s `DO UPDATE SET stop_loss=excluded.stop_loss, take_profit=excluded.take_profit`
  (`:3198-3199`) writes `NULL` — so **the next live update of a row clears it**, exactly as ESC-060 says.
- `_on_position_end` (`:3108`) only **SELECTs** (`:3132-3165`) and renders; it does not re-persist, so it neither
  clears nor restores.
- Therefore a row from a pre-D45 database that **never receives another live position update** (a symbol no longer
  held / not streamed, or the account not subscribed) keeps its old stop/target values in the file.

Those values are invisible (8-column panel), unsettable (no dialog/menu since D45) and unsupported — so the drop is
still defensible. But the claim "could only ever hold `NULL`" is false for an inherited DB, and "the drop destroys
nothing that survived" should read "destroys nothing the app can reach". D46.12 already requires every **row** to be
preserved; recommend it also state the byte-level truth, so the destructive step is not sold on a false premise.
This is the only DELETE in the batch that destroys bytes; everything else is code with no data.

**C-3 — D46.5 and architecture `S44` disagree about `tests/test_d45_removal.py`.** S44 says `:523` is repointed in
wave 1; D46.5's book does not name the call. Same issue as **M-2**.

**C-4 — The plan/architecture's exact-match guard rationale is void after D46.** Plan `AP-D46-7` / architecture
`S44` justify exact-matching `orders` and `Orders` precisely because `ibkr/id_manager.py:22` (reserve docstring) and
`ibkr/pacing.py:131` (`OrderRateLimiter` docstring) sit in files "no task may edit". D46 rows 11 and 14 **delete both
docstrings**. Keeping exact matching is harmless, but the written rationale is now wrong and the guard must be
re-derived against the post-D46 tree (the plan says the scan must be re-run, so this is a documentation trap, not a
code blocker).

**C-5 — Cosmetic errors and one phantom symbol** (not findings, noted so nobody chases them): DELETE row 10 cites
`data/models.py:105-120` (file ends at 116); R3 cites `error_codes.py:1-27` (file ends at 22); and D46.6/D46.12/DG85
name `_persist_position`, which **does not exist** in the tree — the live path is `MainWindow._on_position_update`
(`ui/main_window.py:3032`) → `_upsert_position` (`:3170`). A task that greps for `_persist_position` finds nothing
and may conclude the work is done.

### 2.5 The activated plan, architecture and map are a revision behind the requirements

This is the most consequential result of the audit. The requirements' expansion (`D46.1`–`D46.13`, A99–A104,
DG82–DG87) landed at **2026-10-25 18:57**. The plan, architecture and codebase map were last written at
**18:52 / 18:52 / 18:46**, and the plan review is stamped **18:53 — "requirements drift was checked (none:
`requirements.md` unchanged since the round-1 review)"**. That statement is no longer true. The documents still
encode the **narrow, 17-name** scope and, worse, **forbid** the expanded deletions:

| Document:line | What it says | Contradicts |
|---|---|---|
| `docs/plan.md:2468` | Phase P5 title: "delete `ibkr/orders.py` and the inert order-observation chain" | D46.11–D46.12 (utilities + storage) are absent from the title/scope |
| `docs/plan.md:2549-2552` | "The **kept** surface is frozen … `IdManager` (incl. `reserve`), and the `positions`/`trade_groups` stop/target **storage**" | D46.10 deletes `reserve`; D46.12 deletes the storage |
| `docs/plan.md:2554-2556` | "Out of scope — do NOT plan these … `data/db.py`'s schema; … `ibkr/id_manager.py` (A97/DG80); `ibkr/pacing.py`; `config/settings.py`; … `tests/test_stop_loss_target.py`" | DELETE rows 11, 12, 14, 15–18, 25 |
| `docs/plan.md:2879` | `AP-D46-12`: "**No new test module, no new dependency, no schema change, no migration.**" | D46.12 requires the project's first **destructive** migration |
| `docs/plan.md:2797-2805` | Forbidden list: 17 names only (`ibkr.orders` … `exec_details`) | missing `order_limiter`, `MAX_ORDER_NOTIONAL`, `render_fill_blip`, `play_fill`, `reserve`, `stop_loss`/`take_profit` |
| `docs/architecture.md:5099` | `S46`: "`IdManager` **whole** (incl. `reserve` …) … the `positions`/`trade_groups` stop_loss/take_profit **storage** … are **not touched** by any P5 task" | D46.10, D46.12 |
| `docs/architecture.md:5130, 5135, 5239, 5333` | "no DDL, no migration" (×4); "a pre-P5 database opens unchanged" | D46.12, D46.13 |
| `docs/architecture.md:5428` | Explicit non-changes: "`ibkr/pacing.py` (incl. the now-dead `order_limiter`), `ibkr/id_manager.py` (incl. `reserve`), `config/settings.py` (incl. the now-dead `MAX_ORDER_NOTIONAL`)" | DELETE rows 11, 12, 14 |
| `docs/codebase-map.md:110-111, 194-197, 246-251` | `ibkr/orders` deleted, but `pacing.order_limiter` and `id_manager.reserve` "have no production caller and are **left in place** (A97/DG80 — not this batch's scope)"; "Retained by decision after D45 … `MAX_ORDER_NOTIONAL` and `ibkr/pacing.order_limiter` (**dead but out of scope**)"; survivors list still includes `order_limiter`/`MAX_ORDER_NOTIONAL`/S-L-T-P storage | DELETE rows 11, 12, 14, 15–18 |

`docs/tasks/task-graph.json` holds **only P4 tasks** (6), so no work has been broken down against the stale plan yet.
The cheap fix is a Plan revision (revision 2) that (a) adopts the 25/12 inventory, (b) replaces `AP-D46-12`'s "no
schema change" with the D46.12 migration, (c) flips the `S46`/survivor rows for `reserve`/`order_limiter`/
`MAX_ORDER_NOTIONAL`/storage, (d) refreshes the map's survivors list, and (e) re-derives the guard's exact-match
rationale (**C-4**). Until that happens, a worker following the activated plan will **not** execute rows 11–18.

### 2.6 Retain-row evidence, checked one by one

"Each RETAIN entry still has its named consumer" is the requirement's own test. I re-verified rather than accepted
the rationale:

| Row | Claim | Verified consumer | Verdict |
|---|---|---|---|
| R1 | `_on_error`'s final `showMessage(..., 8000)` | `b.error_msg` → `_on_error` (`ui/main_window.py:585`); fall-through after the session branch | **correct** |
| R2 | `IBApiClient.error` + `error_msg` | every TWS error; `classify_error` gate at `ibkr/client.py:228`, emit at `:245` | **correct** |
| R3 | `classify_error` | `ibkr/client.py:228`; gates all errors, 201/103 `fatal`, 202 `warning` | **correct** |
| R4 | `advancedOrderRejectJson` | `ibkr/client.py:195-221` — the 5-arg `EWrapper.error` signature negotiation | **correct** |
| R5 | `nextValidId` + `set_next_valid_id` | `ibkr/client.py:182-193` sets `_connected`/`CONNECTED`, resets backoff, clears disconnect class; D40/D25 tests drive it (`test_d40_tws_lifecycle.py:239,311,368,407,450`, `test_d25_alarm_monitor.py:397`) | **correct** |
| R6 | `IdManager`, `get_id`, singleton | `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`, `ui/main_window.py:1095` | **correct** |
| R7 | `PacingManager`, `PacingExceeded`, `pacing_manager` | `ibkr/market_data.py:44,57`, `ibkr/subscription_manager.py:32,117,119`, `ui/main_window.py` | **correct** |
| R8 | ICT order blocks | `services/ict_service.py:114` → `:144` `"orderBlocks"` → `ui/overlays/ict_overlay.py:27,44` | **correct — false positive, do not touch** |
| R9 | `sort_order` | `data/db.py:48,249-295`, `ui/watchlist_panel.py` persistence | **correct — false positive** |
| R10 | `TradeGroup`, `trade_group_id`, strategy grouping | **`TradeGroup`/`trade_groups`/`position_group_map`: no consumer at all.** Grouping is `strategy_detection` + `Position.id` | **evidence false — C-1** |
| R11 | `Position`, `positions`, Portfolio view | `ui/main_window.py:3032-3218` persistence/render; `ui/active_portfolio_panel.py` | **correct** (note: loses two columns in the same batch) |
| R12 | `render_alarm_chime`, `play_alarm`, `"alarm"` key | `ui/main_window.py:2114` `sound_service.play_alarm()`; `tests/test_d24_alarm_full_chain.py:88` | **correct** |

**Also verified as false positives (my L6–L9 / K4, the requirements' R8/R9):** ICT order blocks, `showKillzones` /
`killzones` in `services/ict_service.py` + `ui/overlays/ict_overlay.py`, `_order_by_recency` in
`services/alarm_monitor.py`, and `sort_order`. None is order code; none should be "tidied".

---

## 3. Ambiguous — listed, not guessed

These are the items where a confident delete or retain is not honest without an owner decision. None blocks the
live order deletion; they affect the **scope boundary** of D46.

1. **`TradeGroup` / `trade_groups` / `position_group_map` — dead storage, not order transmission.** Zero readers,
   zero writers, zero consumers (C-1). They are not order code, but they exist only because of the deleted
   grouping/SL-TP feature. Deleting them widens `tests/test_db_schema.py` (asserts both tables) and `tests/conftest.py`
   (drop order). I would **not** fold them into D46; record them as a cleanup candidate.
2. **The stop/target drop (D46.12) — destructive, justified but overstated.** Rows preserved, values unreachable,
   but a non-updated inherited row keeps bytes (C-2). If the owner wants zero data-destruction risk, a
   copy-the-DB-before-migration step (DG86 already suggests it) is the conservative addition.
3. **`ibkr/__pycache__/order_book.cpython-311.pyc`.** "Order book" here is a market-depth ladder, not an order
   ticket — it is D41/DOM residue, not D46 order code. Delete as general residue; do not count it as an order item.
4. **`dist/NDThinkChart/` (2026-09-18).** Contents unverifiable from outside; a rebuild is the only honest
   disposition. Whether the owner cares about a stale local bundle is a release question, not a code question.
5. **`charting_app.sqlite3`.** Empty group/position tables in a dev sample. Harmless; the migration test is the real
   coverage.
6. **`config/settings.py::check_live_port` / `LIVE_PORT`.** Trading-safety wording ("trades live only"), but the
   code guards the **connection**, not an order. Retain; do not let a vocabulary sweep take it.
7. **`ui/main_window.py:1713` "(+ DOM)" and `ui/watchlist_panel.py:950` "MarketDepth management".** Stale **DOM**
   comments from D41, not order code. Out of D46's scope; name them so nobody confuses them with order residue.
8. **`tests/test_d41_removal.py:97` order-named guard tokens (`M-5`).** Historical forbidden list; leaving it is
   correct, but it makes D46.9's absolute "no order-named symbol outside the two sets" literally false.
9. **`ibkr/error_codes.py`'s `201`/`103` → `fatal` classification.** Looks order-specific; is the general TWS error
   severity table (and the reason 201/103 surface at all). Retain — R3 is right.

---

## 4. Out-of-code surface (docs, history, build state)

Named for completeness; none is a code path. The owner said "all order-related coding", so these are
documentation/release decisions, not inventory rows:

| Path | What it contains | Recommendation |
|---|---|---|
| `USAGE.txt:84-90` | Accurate on the **order** half: "the app places, cancels and closes nothing"; "IBKR rejections and cancellations appear in the status bar…". But `:88` still says "The database columns are kept, but an update from TWS writes them empty". | `:88`'s "columns are kept" becomes false under D46.12 — exactly DG84/AC-D46.13's contradiction. Update to "dropped" in the same batch. |
| `usage.md:102,136-139,154,167,206` | Same, plus `:154` "columns are kept (no migration)" and `:167` the deleted builder suite | Update `:154` (dropped) and `:167` (M-3); the rest is accurate. |
| `docs/codebase-map.md` | Post-P5 **target** prose, but narrow scope; survivors still include `order_limiter`/`MAX_ORDER_NOTIONAL`/storage | Must be refreshed with the expanded inventory (§ 2.5). |
| `docs/phase-changelog.md`, `docs/ibkr-api-data-inventory.md`, `docs/thinkorswim-feature-gap-analysis.md` | Historical records that describe order entry as a planned/delivered feature | Leave as history, consistent with D46.7. |
| `dev_docs/delta.md`, `dev_docs/detailed_technical_spec.md`, `dev_docs/development_phases_tasks.md`, `dev_docs/ibkr_TOS_trading_terminal_implementation_plan.md`, `dev_docs/trading_app_architecture.txt` | Original design corpus: `orders.py` "single and OCA bracket", `placeOrder`, `orderStatus`/`execDetails`, "Flatten All", bracket SL/TP, the DOM ladder, `nextValidId` seeding | **Leave as history.** They are the provenance for what was built, and D46.7's history rule applies. If the owner wants no order prose anywhere, that is a separate documentation purge — flagging, not recommending. |
| `ibkr/__pycache__/*.pyc`, `tests/__pycache__/*.pyc`, `dist/`, `charting_app.sqlite3` | Build residue and a stale bundle (M-6, M-7) | Delete the project `__pycache__` as cleanup; rebuild `dist/` after D46. |

---

## 5. Bottom line for the pre-build check

- **Use the requirements' 25/12 table as the spec** — it is materially right, and its reachability judgements
  (inert chain, zero-consumer utilities, `IdManager`/`nextValidId` retain) match mine.
- **Amend it with** M-1, M-2, M-3 and the R10/A99 corrections before the build, or the batch will (a) leave one
  stale SL/TP comment and one stale doc line, (b) break the retained removal guard on wave 1, and (c) document a
  retain rationale that is not true.
- **Do not start the build from `plan.md` § P5 / `architecture.md` § P5 as they stand.** They are the pre-expansion
  scope and explicitly forbid rows 11–18. A Plan revision is required first; the task graph is still empty, so this
  is the cheapest possible moment to do it.

