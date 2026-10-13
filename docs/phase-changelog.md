# NDThinkChart — Phase Changelog

A working record of what changed in each implementation phase, for the team
(and the next team) to understand the evolution of the codebase. Normative
requirements live in `docs/requirements/requirements.md`; the target design in
`docs/architecture.md`. This file is the *as-built* history.

**Gate rule:** this document is updated with a phase's full details **before**
that phase's code is committed/pushed to GitHub. The next phase starts only
after the changelog entry is complete. Each entry is written from the coder's
and reviewer's reports for that phase, verified against the branch.

---

## Phase 1 — D26 P0 real-money safety (order path)

- **Status:** MERGED to `main` and pushed 2026-10-12 (`031ea99..5d4daf4`).
- **Branch:** `d26-p0-safety` (10 commits).
- **Review:** Code Reviewer verdict **APPROVE** (all 9 items + both drive-bys verified).
- **Tests:** 779 passing, 0 failing (offscreen). 69 order-path tests; no test transmits an order or touches TWS (mocked `ib_client` only).

### Commits
| SHA | Item | Change |
|---|---|---|
| `a46d17d` | 1.1 | Bracket children placed on the **opposite** side of the parent (`ibkr/orders.py::bracket_order`); rewrote `tests/test_order_builders.py:83-104` which had asserted the buggy same-side behaviour (red-first: 2 failures pre-fix) |
| `f7b5e69` | 1.2 | New `IdManager.reserve(n)` — thread-safe contiguous block; bracket branch reserves 3 IDs. Audited all other `get_id()` callers (all single-ID, no collision) |
| `5e11722` | 1.3 | MKT buttons fixed: `_on_buy_mkt/_on_sell_mkt` route through `_send_mkt(action)`; qty from spinbox; qty≤0 refused (was a 5-vs-6-arg `TypeError` crash) |
| `db28c84` | 1.4 | Port guard: `config/settings.py::LIVE_PORT = 7496` + `check_live_port()` fail-fast in `main()` (fatal dialog, exit 1); connection badge derived from verified port + `AccountType` |
| `1148050` | 1.5 | Explicit Buy/Sell side selector drives `_on_place` (was hardcoded `"BUY"`); dead `_pending_ladder` path deleted |
| `9f6d2ed` | 1.6 | New `ibkr/validation.py::validate_order()` pure gate (symbol, side, type, qty>0, price>0 per type, bracket geometry, notional ≤ cap); wired at the top of `_place_order`; rejections surface in UI, never traceback, never transmit |
| `ed0a174` | 1.7 | `_on_error` routes registry-matching reqIds to order status (201/103→Rejected, 202→Cancelled + TWS message in ticket); 201/103/1100/502/503/509 promoted to fatal in `ibkr/error_codes.py`; order entry blocked while disconnected |
| `1645cea` | 1.8 | Set Stop-Loss/Take-Profit dialog honestly labelled: saves targets locally only, **does not place orders** (real-leg transmission scoped as follow-up batch) |
| `a4ed306` | 1.9 | Kill switch: `reqGlobalCancel()` + per-ID `cancelOrder` for every tracked open order; **all three bracket legs registered at transmit time** (validator requirement); wired into `_on_portfolio_flatten_all`; (open_before, cancels_sent) surfaced in UI; red toolbar button, no confirm dialog (panic control by design) |
| `5d4daf4` | 1.6 | Regression test pinning `MAX_ORDER_NOTIONAL == 25000` (plan §7.2 gate requirement; added post-review) |

### Drive-by fixes (found while implementing, verified real by reviewer)
1. `_place_order` built `order_registry.UserOrder(...)` but `UserOrder` is a module-level dataclass — **no order could ever transmit** via that path (`AttributeError`, previously masked by the MKT crash). Fixed by direct import.
2. SL/TP dialog used `QHBoxLayout` without importing it — the dialog **could never open** (`NameError`). Import added.

### Decisions recorded
- `MAX_ORDER_NOTIONAL = 25000` USD (owner, 2026-10-12).
- D26.3: labelling-only now; real STP/LMT leg transmission for existing positions → follow-up batch (proposed D29; candidate inclusion: partial-fills display fix).
- Kill switch: no confirm dialog (reviewer agreed: panic controls stay immediate).

### Follow-ups filed (not Phase 1 scope)
- `_close_position_by_id` transmits close-MKT `placeOrder` outside `_place_order` (bypasses validation/disconnect guards, unregistered).
- Kill switch marks orders "Cancelled" even when `cancelOrder(oid)` raised (failed cancel invisible to retry).
- Two flaky UI-timing tests under full-suite load (`test_history_backfill_loadpath`, `test_watchlist_d14_midrag`) — pass in isolation.

---

## Phase 2 — D27 correctness (charts, studies, alarms, reconnect)

- **Status:** Code complete and review-**APPROVED**; branch `d27-correctness` NOT yet merged/pushed (stacked on `d26-p0-safety` @ `5d4daf4`).
- **Branch:** `d27-correctness` (16 commits: 8 Phase-2 + 8 fix-pass).
- **Review:** first verdict **REQUEST-CHANGES** (2 issues + 2 missed plan items); fix pass done; re-review verdict **Phase 2 PASSES gate**.
- **Tests:** 819 passing, 0 failing (offscreen). 30 new `tests/test_d27_*.py` + fix-pass tests; no test touches live TWS/network.

### Commits (Phase 2)
| SHA | Item | Change |
|---|---|---|
| `11f8362` | 2.1 | Phantom alarms: `_finalize_history_wave` no longer rewinds `_last_chart_price` to stale historical close (`_rt_seen` flag); live forming bar re-applied after finalize |
| `0109a5c` | 2.2 | Invisible overlays: MACD histogram `xs[i]` fix; ICT/gap/VIX overlays map bar indices → display-x via collapse map |
| `cb142c9` | 2.3 | Reconnect: `connect()` stores params and is re-issuable (was dead code); `SubscriptionManager` rewritten with reqId-keyed registry + rebind; chart/DOM/watchlist subs registered; `_replay_subscriptions` replays RT_BARS+DEPTH |
| `b972f90` | 2.4 | New `ibkr/stream_health.py` (owned by `MainWindow` this phase; designed to migrate into `TickerSession` in Phase 3b); persistent toolbar badge; RT errors → red badge + backoff retry |
| `d7e2dc2` | 2.5 | Central `_symbol_last_prices` map (chart + watchlist feeds); positions use their own symbol's price, 0.0 = unknown (no fabricated P&L) |
| `2bfd097` | 2.6 | `_on_connected` issues `reqPositions` + `reqAccountSummary`; "Account data unavailable — not subscribed" panel state |
| `2f2d976` | 2.7 | Gap-based bar-level backfill detection for trailing 5 trading days (configurable); `load_chart` passes ext-hours toggle. Three pre-existing test files re-seeded (day-granularity → 1-min days; assertions unchanged — legitimate contract change) |
| `68a8b69` | 2.8 | "1 day"/"4 hours" floors anchored in America/New_York; VWAP resets on ET date. **Caveat:** IBKR's own 4h anchor unverifiable without live TWS — implemented per ET prescription, flagged in code (`data/bar_aggregator.py`) |

### Commits (fix pass — review issues + missed items)
| SHA | Item | Change |
|---|---|---|
| `f191500` | A | Reviewer issue A (stale collapse map) did **NOT reproduce** — `_rebuild_collapse_map()` already calls `_sync_collapsed_consumers()`; committed as regression test only, no code change (re-reviewer confirmed false positive) |
| `5c24ab4` | B | Backoff fix: `StreamHealth.mark_subscribed(reset_backoff=True)`; `_retry_rt_subscribe` passes `False` → delays 5→10→20→40→60s (was stuck at 5s) |
| `96de327` / `69a2313` | 2.9 | Aggregator priming: `load_chart` replays trailing 5-sec history (bounded at 7200s) through the fresh `BarAggregator` before live attach; fail-open on error; 15s QTimer backstop |
| `b9874d0` | 2.10 | Drawing colours: `DrawingStore.update_drawing` accepts optional color/label/group_id (`None` = unchanged); `updated` signal carries `(id, payload, color)` from all three emitters; settings path persists |
| `fd9e308` / `f35876f` / `d0e4412` | — | Test-compat for the new priming behaviour (purposes preserved, no weakened assertions) |

### Drive-by fixes (found while implementing, verified real by reviewer)
1. `_on_position_update` was missing required `stop_loss`/`take_profit` args — `TypeError` on every position update.
2. `positions` table lacked the `UNIQUE(symbol, con_id)` its own upsert needs — added via additive `_migrate_schema`.

### Decisions recorded
- 2.9 priming fetch bounded at 7200s (coder judgment; re-reviewer: reasonable — sub-2h intraday timeframes covered exactly; follow-up filed for 4h/daily forming-candle exactness: seed from the historical partial bar instead).
- Reviewer issue A closed as false positive with regression test kept (no code change).

### Follow-ups filed (not Phase 2 scope)
- 4h/daily forming-candle exactness under the 2h priming bound.
- Backoff docstring nit ("5s -> 10s -> 20s -> 60s" skips 40).
- Transient duplicate-ts append on first aggregator push (cosmetic; wiped by backfill finalize refresh).
- Stale reqId accumulation in `SubscriptionManager.replay_all`; dead `RealtimeBarsManager.replay_all`; write-only `_account_subscribed`.
- (Carried) `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests.

---

## Phase 3 — Session keystone + pop-outs + alarm monitor (3a→3b→3c→3d)

- **Status:** IN PROGRESS (coder on `phase3-sessions-popouts`, stacked on `d27-correctness`).
- Entry to be written when Phase 3 passes review, before its branch is pushed.
