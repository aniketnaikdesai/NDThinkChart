# Architecture Proposal — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

> **Status of this document:** a **proposal** by the Plan agent. It is not canonical.
> `docs/architecture.md` / `docs/plan.md` are written by Plan Artifact Editor & Validator
> after validation. This is an **existing-repo run**: `docs/requirements/requirements.md`
> contains the marker sentence `This is an existing repository.` and a Current Tech Stack,
> which are treated as **hard constraints**. Every item is labelled `[existing]`, `[new]`,
> or `[new/changed]`.
>
> **Increment scope.** D23 is a **small, purely corrective increment on top of the already-built
> D1–D22 system** (D1–D21 at commit `286341e`, 673 tests; D22 built and green at **712 tests**,
> uncommitted). **D1–D22 are frozen and are NOT re-planned.** D23 fixes two *nice-to-have* Code
> Reviewer findings on the D22 work — **D23.1 = ESC-030** (a capability-guarded, documented
> contract-details cancel) and **D23.2 = ESC-031** (the `_row_data` row-key invariant in
> `remove_symbol`) — both approved by the user for a full-pipeline fix. **No stack change, no
> schema change, no new dependency, and no live-order-path change.** D23 does **not** reopen D22's
> feature criteria (`AC-D22.1`–`AC-D22.9` stand).
>
> **Baseline reference.** The as-built baseline is `docs/architecture.md` (D1–D21 validated through
> 2026-10-06; `## D22 increment` validated 2026-10-07). D23 supersedes nothing except the
> **task-level** `AC-D22.2.3` wire-cancel mandate, which it **corrects**, and it **reconciles D22
> architecture row `S3`**.

---

## Codebase Summary (existing repository — D23 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, **2851 nodes**,
> refreshed 2026-10-06 21:47) and then **validated against the current source files** (the
> repository is authoritative). The D23 surface is two functions and their tests: the
> contract-details cancel in `ibkr/market_data.py`, the row re-index in
> `ui/watchlist_panel.py::remove_symbol`, and the two D22 test modules that cover them.

### Data models / schema
- `[existing]` **SQLite `watchlist` table** — `data/db.py:23–27`:
  `watchlist(symbol TEXT PRIMARY KEY, category TEXT NOT NULL, sort_order INTEGER NOT NULL)`.
  D22 added access helpers (`add_watchlist_symbol` / `remove_watchlist_symbol`); D23 needs **no**
  schema or access-path change.
- `[existing]` All other persisted tables (`bars`, `alarms`, `zones`, `drawings`, …) — **unchanged**.
- `[existing]` **`WatchlistPanel` in-memory row-keyed state** (not persisted):
  `_req_to_row: dict[int, int]` (reqId → row), `_row_data: dict[int, dict]` (row → cached field
  values, FieldKey-bound), `_prev_close: dict[int, float]` and `_last_price: dict[int, float]`
  (keyed by **reqId**, not row), and `_flash_timers: dict[tuple[int, str], QTimer]` (keyed by
  `(row, field)`). This is the state D23.2's invariant applies to.
- `[existing]` **`ContractLookupService._pending: dict[int, PendingLookup]`** — the in-flight
  contract-details correlation map (`services/contract_lookup_service.py:85`), ephemeral, never
  persisted. D23.1 does not change it.
- `[existing]` **QSettings `("NDThinkChart","NDThinkChart")`** — keys `watchlist/width`,
  `watchlist/columns` (D21.5), `watchlist/configured` (D22 seed sentinel). D23 adds none.

### Major components and responsibilities
- `[existing]` **`ibkr/market_data.py::MarketDataManager`** (~92 lines) — `req_historical_data`
  (`:20`), `req_mkt_data`/`cancel_mkt_data` (`:56`/`:63`), **`req_contract_details(contract) -> int`**
  (`:71–76`, D22), **`cancel_contract_details(req_id)`** (`:78–84`, D22 — *the D23.1 target*),
  `cancel_historical_data` (`:86`). `cancel_contract_details` currently does:
  `if req_id is None: return` then `try: self.client.cancelContractDetails(req_id) except Exception: pass`.
- `[existing]` **`ibkr/client.py::IBApiClient(EWrapper, EClient)`** (~223 lines) — forwards
  EWrapper callbacks to `IBBridge`; D22 added `contractDetails` / `contractDetailsEnd` overrides
  mirroring the existing callback pattern. `error()` (`:114–141`) forwards non-`info` severities to
  `bridge.error_msg` (error `200` is `fatal`, `ibkr/error_codes.py:12`).
- `[existing]` **`ibkr/bridge.py::IBBridge(QObject)`** — typed signal bus; D22 added
  `contract_details(int, object)` and `contract_details_end(int)`.
- `[existing]` **`services/contract_lookup_service.py::ContractLookupService(QObject)`** (~176
  lines) — owns the reqId-keyed pending map, arms a single-shot `QTimer(CONTRACT_LOOKUP_TIMEOUT_MS
  = 5000)` per request, resolves **exactly once** via `lookup_finished(req_id, symbol, ok, reason)`.
  `cancel(req_id)` (`:114–120`) / `cancel_all()` (`:122–125`) **drop the pending entry and stop the
  timer** — they do **not** call `md_manager.cancel_contract_details`. `_on_disconnected` in
  `MainWindow` calls `cancel_all()`. This is the **real safety net** D23.1 must document.
- `[existing]` **`ui/watchlist_panel.py::WatchlistPanel`** (816 lines) — `QTableWidget`, header
  strip (`self.header_bar`, `:282–289`) + D21.11 collapse toggle, D21.5 column model/menu (`:605`),
  tick handlers, D14 double-click, width/column persistence. `add_symbol(symbol, contract)`
  (`:664`) inserts a row, renders cells, subscribes via `req_mkt_data`, records `_req_to_row`.
  **`remove_symbol(symbol) -> bool`**
  (`:682–728`) — *the D23.2 target*: finds the row case-insensitively, cancels that row's
  `req_mkt_data` and pops its `_req_to_row`/`_prev_close`/`_last_price`, stops the removed row's
  flash timers, `table.removeRow(row)`, then re-indexes `_row_data` (`:716–719`),
  `_req_to_row` (`:720–723`) and `_flash_timers` (`:724–727`). `clear()` (`:730+`) empties all
  row-keyed state.
- `[existing]` **`ui/main_window.py::MainWindow`** (~2113+ lines, D22-modified) —
  `DEFAULT_WATCHLIST`, watchlist dock + title-bar wiring, `_on_connected` / `_restore_watchlist` /
  `_on_disconnected` (→ `self._contract_lookup.cancel_all()`), `ContractLookupService` construction
  and `lookup_finished` wiring, the add/remove slots, the connection gate. Not touched by D23.
- `[existing]` **`data/db.py`** — `get_watchlist` / `set_watchlist` + the D22
  `add_watchlist_symbol` / `remove_watchlist_symbol` helpers. Not touched by D23.

### Key entry points
- **Watchlist add** — `+` button / header-strip "Add symbol…" → `MainWindow` gate + duplicate check
  → `ContractLookupService.request` → `reqContractDetails` → bridge callbacks (queued) →
  `lookup_finished` → `WatchlistPanel.add_symbol` + `db.add_watchlist_symbol`.
- **Watchlist remove** — table-body "Remove symbol" → `MainWindow` →
  `WatchlistPanel.remove_symbol` + `db.remove_watchlist_symbol`.
- **Contract-lookup cancellation** — `ContractLookupService.cancel` / `cancel_all` (local
  invalidation). `MarketDataManager.cancel_contract_details` has **no production caller** (grep
  across the tree: only its definition at `ibkr/market_data.py:78` and
  `tests/test_ibkr_contract_details_d22.py`).

### External integrations already in use
- `[existing]` **IBKR via the official `ibapi` (pinned `9.81.1.post1`), live TWS port 7496 only**:
  `reqMktData`/`cancelMktData` (watchlist ticks), `reqHistoricalData`/`cancelHistoricalData`
  (chart + D16 backfill), `reqMktDepth` (DOM), realtime bars, account/position/order callbacks, and
  (new in D22) `reqContractDetails` / `contractDetails` / `contractDetailsEnd`.
- `[existing]` **SQLite** via `data/db.py` (module singleton `db`), path from
  `config/paths.get_db_path()`.
- `[existing]` **QSettings**, the **Qt signal bus** (`IBBridge`), and the **pyqtgraph** chart scene.

### Verified facts that shape D23 (source-validated 2026-10-07)
1. **The pinned `ibapi` has no cancel.** `.venv` `ibapi 9.81.1.post1`;
   `hasattr(EClient, 'cancelContractDetails') is False` while `hasattr(EClient, 'reqContractDetails')
   is True`. Therefore `ibkr/market_data.py:82`'s `self.client.cancelContractDetails(req_id)` raises
   `AttributeError`, which the enclosing `except Exception: pass` (`:83–84`) silently swallows → the
   cancel is a **no-op on the wire**. Requirement **D23.1** fixes this as a **capability-guarded,
   documented** call.
2. **The wire cancel is dead code today.** No production path calls
   `MarketDataManager.cancel_contract_details`; `ContractLookupService.cancel`/`cancel_all` only
   drop the pending entry and stop the bounded timer; `_on_disconnected` calls `cancel_all()`.
   TWS ends a `reqContractDetails` request itself (`contractDetailsEnd` / an `error`). Hence the
   behaviour change is **forward-correctness**, verifiable in isolation, with **no D22 observable
   behaviour change** (`AC-D23.1.4` / A53 / A54).
3. **The D22 test's fake hides the gap.** `tests/test_ibkr_contract_details_d22.py::_FakeClient`
   (`:118–130`) **defines** `cancelContractDetails` (`:127`); `TestD22_02_T03`
   (`:133`) covers "delegates + None-safe" (`:151`) and "swallows client exception" (`:163`) but
   has **no** case for a client that *lacks* the method. D23.1 adds that case and pairs the
   method-defining fake with a fake that does not define it (`AC-D23.1.1`).
4. **`remove_symbol` leaves a stale `_row_data` key only on the last row.**
   `ui/watchlist_panel.py:716–719` re-indexes `_row_data` with `{(r-1 if r > row else r): values…}`
   but **never drops the removed row's own key**. Reproduced: a 3-row panel
   (AAPL/MSFT/TSLA), `remove_symbol('TSLA')` → `rowCount() == 2` but
   `sorted(_row_data.keys()) == [0, 1, 2]` (stale key 2). A middle-row removal leaves `[0, 1]`
   because the shifted-up row overwrites the removed key. `_req_to_row`, `_prev_close`/`_last_price`
   and `_flash_timers` are already handled explicitly, so **only `_row_data`** carries the stale
   key (`AC-D23.2.1`–`AC-D23.2.2` / A55).
5. **The existing remove coverage cannot catch it.**
   `tests/test_watchlist_add_remove_d22.py::test_D22_05_T02` (`:281`) removes the **middle** row and
   asserts `_row_data.keys() == {0, 1}` — it passes pre-fix. There is **no** last/first/only-row
   assertion; `test_D22_05_T03` (`:324`) covers the absent/blank no-op (`AC-D23.2.3`/`AC-D23.2.4`).

---

## Summary

D23 is a targeted, two-item correctness increment on the built D22 watchlist work.
**(D23.1)** `MarketDataManager.cancel_contract_details` becomes a **capability-guarded best-effort
cancel** (`getattr(self.client, 'cancelContractDetails', None)`, called only if present) with an
in-code note that the pinned `ibapi` lacks the method, that TWS's own `contractDetailsEnd`/error
ends the wire request, and that `ContractLookupService`'s local invalidation (bounded QTimer +
`cancel_all` on disconnect) is the real safety net — no raised and no silently-swallowed
`AttributeError`. **(D23.2)** `WatchlistPanel.remove_symbol` drops the removed row's own
`_row_data` key, so `set(_row_data.keys()) == set(range(table.rowCount()))` after **any** removal
(first / middle / last / only), and the missing last-row (and/or first/only-row) coverage is added.
Both are additive, behaviour-preserving corrections: no stack change, no schema change, no new
dependency, no live-order-path change, and no reopening of `AC-D22.1`–`AC-D22.9`.

---

## Tech Stack Decisions (D23 increment)

Constrained (existing) choices first, then the D23 additions. **No new dependency.**

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Existing-repo hard constraint; "Changing the tech stack" is an explicit Non-Goal | Any new UI/charting framework — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` (pinned `9.81.1.post1`), live TWS port `7496` only; numpy (`>=1.26`); SQLite via `config/paths.get_db_path()`; PyInstaller `.app`; pytest + pytest-qt offscreen (no live TWS) | Existing-repo hard constraint; Q9 forbids automated TWS/order traffic | Paper mode / new broker / new DB / new test framework — rejected |
| S3 *(reconciled)* | **D23.1 — capability-guarded best-effort contract-details cancel** `[new/changed]` | Rewrite `[existing] ibkr/market_data.py::MarketDataManager.cancel_contract_details` to: keep `if req_id is None: return`; resolve `cancel = getattr(self.client, 'cancelContractDetails', None)`; **call it only if present**, inside the existing containment (`try/except Exception: pass`); carry a docstring/comment documenting that (a) pinned `ibapi 9.81.1.post1` exposes no `EClient.cancelContractDetails`, (b) TWS's own `contractDetailsEnd`/error ends the wire request, and (c) `ContractLookupService`'s local invalidation (bounded 5s QTimer + `cancel_all` on disconnect) is the real safety net. This **reconciles D22 architecture row `S3`** (the request path is unchanged; only the cancel is corrected) and **supersedes the task-level `AC-D22.2.3`** wire-cancel mandate (`AC-D23.1.1`–`AC-D23.1.4`) | `getattr`-guard makes the call **capability-detected**: correct on the pinned dep today (no-op, no exception) and forward-correct if a future `ibapi` adds the method (called once). Keeping the containment preserves the method's existing "never raises" contract (`AC-D23.1.3`), and the documentation makes the no-op **intentional and discoverable** rather than a swallowed `AttributeError`. It also matches the ESC-030 suggested direction exactly | (i) **Leave as-is** — silently swallowed `AttributeError`; dishonest and non-forward-correct (rejected). (ii) **Delete the call + the method** — removes a public-shaped method the D22 architecture names, loses forward-compat, and cannot be asserted (rejected). (iii) **Drop the `try/except` and let it raise** — breaks the established containment contract and could surface on a reader/UI path (rejected). (iv) **Attempt a real wire cancel some other way** — no such API exists on the pinned dep (rejected) |
| S15 | **D23.2 — `_row_data` row-key invariant in `remove_symbol`** `[new/changed]` | In `[existing] ui/watchlist_panel.py::remove_symbol`, drop the removed row's own entry while re-indexing — e.g. `self._row_data.pop(row, None)` alongside the existing `{(r-1 if r > row else r): values …}` re-map — so that after `remove_symbol` returns `True`, `set(self._row_data.keys()) == set(range(self.table.rowCount()))` (and, unchanged, the `_req_to_row` values and `_flash_timers` keys cover exactly the surviving rows). Update the `remove_symbol` docstring's re-index contract to state the invariant | The stale key is caused by the removed row's own index never being overwritten when it is the max index. Popping it first makes the invariant explicit and mirrors the **already-explicit** handling of `_req_to_row` (popped) and `_flash_timers` (removed-row timers stopped). The narrow fix keeps the shift expression and the FieldKey-bound `_row_data` values untouched (DG32), preserving `_rebuild_table`/`_set_cell` behaviour (`AC-D23.2.4`) | (i) **Rely on the shift alone** — leaves the stale last-row key (the defect; rejected). (ii) **Rebuild `_row_data` from the table contents** — discards cached field values and the FieldKey binding, and re-queries widgets (rejected: risks DG32/`_set_cell` regressions and is a larger change). (iii) **Filter with `{k: v for k, v in … if k < rowCount()}`** — works but is less direct than popping the removed key and obscures *why* the key is stale (rejected in favour of the explicit pop) |
| S16 | **D23 test surface** `[new/changed]` | Update two D22 test modules: `tests/test_ibkr_contract_details_d22.py` — (i) a **code-shape/source assertion** (the pre-fix-red evidence for `AC-D23.1.1`): `cancel_contract_details`'s own source contains **no** bare `self.client.cancelContractDetails(...)` attribute access and **does** contain the `getattr(self.client, "cancelContractDetails", None)` capability guard; (ii) a **missing-capability behavioural test** with a fake that does **not** define `cancelContractDetails` (e.g. `types.SimpleNamespace(reqContractDetails=…)`) asserting no exception (a **post-fix guard**, explicitly *not* pre-fix-red); (iii) the **present-method** case with the method-defining `_FakeClient` (invoked once with `req_id`); keep the existing "delegates"/"None-safe"/"raises" cases. `tests/test_watchlist_add_remove_d22.py` — add **last-row** (and/or **first-row** / **only-row**) removal assertions that fail pre-fix | Q8: every fix ships a check that fails before and passes after, runnable offscreen. For D23.2 the last-row assertion is genuinely red pre-fix. For D23.1 the fix retains `try/except Exception: pass` and changes **no externally observable behaviour** (the pre-fix code already returns normally for a client lacking the method — `AttributeError` raised inside the `try`, swallowed — and a `getattr(…, None)` guard still performs the attribute lookup), so **no behavioural or attribute-access-spy test can be red pre-fix**; the genuine pre-fix-red evidence is therefore the **code-shape/source assertion**, and the behavioural cases are honest **post-fix guards** (`AC-D23.1.1`). A method-defining fake no longer matches the pinned surface, so the no-op must also be exercised against a fake that omits the method. The existing middle-row test (`test_D22_05_T02`) passes pre-fix and cannot be the only guard (`AC-D23.2.3`) | Behavioural-only testing of the guard (cannot be red pre-fix — the retained containment makes pre/post behaviour indistinguishable); a live-TWS test (forbidden by Q9); asserting the private attribute's absence at import time (brittle) |
| S14 | Testing `[existing]` | pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS; run as `.venv/bin/python -m pytest` (stale `pytest` shebang is a known gotcha) | Repo standard (Q8/Q9) | Manual-only / live-TWS tests — rejected |

**D23 introduces no new dependency and replaces or deprecates no existing tech-stack item.** The
pinned `ibapi` version is **not** changed — D23 makes the code honest about its actual surface
instead.

---

## System Components (D23 increment)

**Existing components (responsibilities unchanged):**
- `[existing] services/contract_lookup_service.py` — `ContractLookupService` pending map, bounded
  QTimer, exactly-once resolution, `cancel`/`cancel_all` local invalidation. **Unchanged** — D23.1
  documents it as the safety net.
- `[existing] ibkr/client.py`, `[existing] ibkr/bridge.py` — the contract-details request/callback
  plumbing. **Unchanged** (the request path is untouched; only the cancel is corrected).
- `[existing] ibkr/contracts.py`, `[existing] ibkr/id_manager.py`, `[existing] ibkr/pacing.py`,
  `[existing] ibkr/error_codes.py`. **Unchanged.**
- `[existing] data/db.py`, `[existing] ui/main_window.py`, `[existing] ui/add_symbol_dialog.py`.
  **Unchanged by D23.**
- `[existing] ui/watchlist_panel.py::WatchlistPanel` — all behaviour except the `remove_symbol`
  re-index body. **Unchanged** otherwise (table, header strip, D21.5 column model/menu, D21.11
  toggle, `add_symbol`, `clear`, tick handlers, D14 double-click, persistence).

**Changed components:**
- `[new/changed] ibkr/market_data.py::MarketDataManager.cancel_contract_details` — capability-guard
  + documentation (S3/D23.1). Public signature `cancel_contract_details(req_id: int | None) -> None`
  unchanged; `req_contract_details` unchanged.
- `[new/changed] ui/watchlist_panel.py::WatchlistPanel.remove_symbol` — drop the removed row's
  `_row_data` key while re-indexing; docstring states the row-key invariant (S15/D23.2). Signature
  `remove_symbol(symbol: str) -> bool` unchanged.
- `[new/changed] tests/test_ibkr_contract_details_d22.py`,
  `[new/changed] tests/test_watchlist_add_remove_d22.py` — added/updated cases (S16).

**No new component, module, thread, or dependency is introduced.** The request/response path
(`ContractLookupService → MarketDataManager.req_contract_details → IBApiClient.reqContractDetails →
bridge signals → ContractLookupService`) and all component relationships are unchanged; only the
(uncalled) cancel is corrected and one panel method's internal state bookkeeping is tightened.

---

## Data Model (D23 increment)

- `[existing]` All persisted entities and tables (`Bar`, `Alarm`, `Drawing`, `Watchlist`, …; tables
  `bars`, `watchlist`, `alarms`, `zones`, `drawings`, …) — **unchanged; no migration, no schema
  change**.
- `[existing]` `ContractLookupService._pending` (reqId → `PendingLookup`) — **unchanged**.
- `[existing]` QSettings keys `watchlist/width`, `watchlist/columns`, `watchlist/configured` —
  **unchanged**.
- `[new/changed]` **Documented row-key invariant on `WatchlistPanel`'s in-memory state** (not
  persisted): after `remove_symbol` returns `True`,
  `set(_row_data.keys()) == set(range(table.rowCount()))`; the `_req_to_row` **values** and the
  `_flash_timers` **keys** likewise cover exactly the surviving rows (no key for a removed row
  survives). `_prev_close` / `_last_price` stay keyed by **reqId** with the removed row's reqIds
  dropped. This is a corrected invariant over existing structures, not a new store.

---

## Integration Points (D23 increment)

- `[existing]` **IBKR `reqContractDetails` / `contractDetails` / `contractDetailsEnd`** — the D22
  request path is **unchanged**. D23.1 records the externally-verified fact that the pinned
  `EClient` exposes **no** `cancelContractDetails`, so the wire request has no client-side cancel
  and is ended by TWS itself. No new IBKR call type is added.
- `[existing]` **ContractLookupService local invalidation** — the bounded QTimer + `cancel_all()` on
  disconnect remain the safety net for an unresolved lookup (`AC-D23.1.2`).
- `[existing]` **SQLite / QSettings / Qt signal bus / pyqtgraph** — unchanged.
- **No new external service, API, dependency, or persisted table is introduced by D23.**

---

## Non-Functional Approach (D23 increment)

- **Correctness — capability guard (D23.1).** The cancel performs `getattr(..., None)` and calls
  the method only when present, so on the pinned `ibapi` it is a **clean no-op** rather than a
  swallowed `AttributeError` (`AC-D23.1.1`). Containment is preserved: `req_id is None` is a no-op,
  and a client whose (present) cancel **raises** does not propagate (`AC-D23.1.3`). The
  documentation requirement (`AC-D23.1.2`) makes the pinned-dep absence, TWS's `contractDetailsEnd`
  termination, and the `ContractLookupService` safety net discoverable in-code.
- **Forward correctness (D23.1).** If a future `ibapi` adds `cancelContractDetails`, the guard calls
  it exactly once with `req_id` — the method becomes live with no further change; the D23.1.4
  correction record keeps the task/architecture records consistent with the pinned surface.
- **Correctness — row-key invariant (D23.2).** The re-index stays O(n) over the watchlist (a very
  small n) and now drops the removed row's own `_row_data` key, so reads (all of which go through
  `table.item(row, col)` for `row in range(rowCount())`) and the FieldKey-bound
  `_rebuild_table`/`_set_cell` path are unaffected; the invariant is asserted for first / middle /
  last / only-row removals (`AC-D23.2.1`–`AC-D23.2.4`).
- **Performance.** No change: no polling, no new request, no new thread; the cancel rarely/never
  runs (dead code today) and the re-index is unchanged in cost.
- **Security / safety (Q9).** No new dependency; the live-order path (`ibkr/orders.py`) is
  untouched; no automated test connects to live TWS or transmits an order. The contract lookup is a
  read-only query.
- **Test discipline (Q8).** Both fixes ship a **genuine** pre-fix-red / post-fix-green check,
  runnable offscreen; the pre-existing suite (712 tests) must stay green. D23.2's pre-fix-red
  evidence is the last-row assertion. D23.1's fix retains `try/except Exception: pass` and changes
  no externally observable behaviour, so its pre-fix-red evidence is a **code-shape/source
  assertion** (the bare `self.client.cancelContractDetails(...)` access is gone; the
  `getattr(self.client, "cancelContractDetails", None)` guard is present) rather than a behavioural
  test — the behavioural missing-capability (no exception) and present-method (called once with
  `req_id`) cases are **post-fix guards**, explicitly *not* pre-fix-red. The shared-test-DB and
  stale-`pytest`-shebang gotchas recorded in `docs/memory.md` apply — verify with a clean full-suite
  run as `.venv/bin/python -m pytest`.
- **Non-regression.** `AC-D22.1`–`AC-D22.9` stand; the add/remove flow, persistence, connection
  gate, D21.5 column menu, D21.11 toggle, D14 double-click and D21.13 dock behaviour are untouched.

---

## Architecture Risks (D23 increment)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D23-1 | The guarded cancel could still swallow a genuine error, or could stop containing one (raising to a caller) | M | Keep the `try/except Exception: pass` around the guarded call and add/keep explicit cases for `req_id is None`, missing attribute, and a raising client (`AC-D23.1.3`); assert `cancel_calls == [7]` only for the present-method case |
| AR-D23-2 | A test that only uses the method-defining `_FakeClient` cannot exercise the pinned (missing) surface, so the guard could regress unnoticed; and because the retained containment makes pre/post behaviour identical, a behavioural test cannot be pre-fix-red | M | Add the **code-shape/source assertion** (pre-fix-red: no bare `self.client.cancelContractDetails(...)` access; `getattr(self.client, "cancelContractDetails", None)` present) **and** pair the method-defining fake with a fake that does **not** define `cancelContractDetails` (`types.SimpleNamespace(reqContractDetails=…)`) as a post-fix no-exception guard (`AC-D23.1.1`) |
| AR-D23-3 | Correcting the task-level `AC-D22.2.3` and its test could conflict with the already-built D22 tests, leaving the suite red if not updated in lockstep (R49) | L | Update `AC-D22.2.3` (Task Manager, `docs/tasks/task-graph.json` task `D22-02`) and `tests/test_ibkr_contract_details_d22.py` **in lockstep** with the guard; keep the None/raises cases; confirm the full 712-test suite stays green |
| AR-D23-4 | Re-indexing `_row_data` incorrectly could shift a symbol's cached values onto the wrong row (R50) | L | Use the narrow fix (pop the removed key around the existing shift) and assert `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/last/only-row removals; leave `_rebuild_table`/`_set_cell` FieldKey binding (DG32) unchanged |
| AR-D23-5 | The `S3` reconciliation could remain doc-only/ambiguous, leaving architecture and the pinned surface inconsistent | L | Rewrite architecture `S3` to the capability-guarded best-effort cancel (Plan proposes; Validator records it in `docs/architecture.md`); record the reconciliation in `docs/plan_notes.md`; Code Reviewer re-verifies ESC-030 after Build |
| AR-D23-6 | Broadening the fix beyond the two findings (e.g. touching the request path or persistence) could regress D22 | L | Scope guard: D23 touches only `cancel_contract_details` + the test, and `remove_symbol`'s re-index + the test; the request path, DB, `MainWindow`, and the recipe flows are untouched; D1–D22 criteria are re-affirmed |

---

## Implementation sequencing (D23 increment)

At the architecture level the sequence is: **(1)** the D23.1 capability-guarded, documented cancel
plus its missing-capability test; **(2)** the D23.2 `remove_symbol` `_row_data` stale-key fix plus
the last/first/only-row coverage; **(3)** the record reconciliation (`S3` in
`docs/architecture.md`, `AC-D22.2.3` in `docs/tasks/task-graph.json`) and full-suite non-regression
verification. Phases 1 and 2 touch **fully disjoint** file sets and may run in the same wave;
Phase 3 follows both. D1–D22 are frozen throughout. Detailed phases, coverage and `touches_files`
notes are in `docs/plan_proposal.md`.
