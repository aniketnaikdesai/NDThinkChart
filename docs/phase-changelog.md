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

- **Status:** Code complete and review-**APPROVED**; branch `phase3-sessions-popouts` NOT pushed and NOT merged (stacked on `d27-correctness` @ `69a2313`; stays unmerged until the Phase 4 AC-D28.4 performance gate passes, per the R52 reconciliation).
- **Review:** first verdict **REQUEST-CHANGES** (5 wiring items); fix pass done; re-review verdict **Phase 3 PASSES gate**.
- **Tests:** 855 passing, 0 failing (offscreen). 36 new tests (27 Phase-3 + 9 fix-pass); no test touches live TWS/network.

### Commits (Phase 3)
| SHA | Item | Change |
|---|---|---|
| `4f2a804` | 3a | D28.1: `throttle_realtime()` (could sleep 10 min on the GUI thread) replaced by pure `realtime_wait_seconds()` / `realtime_wait_for_slots()` + `record_realtime_slot()`; `PacingExceeded(wait_seconds)` raised instead of sleeping; all callers defer via `QTimer.singleShot` with persistent "pacing-limited, retrying in Ns" status. Orders removed from the realtime throttle — new `OrderRateLimiter` token bucket (5/s, burst 5); both order paths defer via singleShot with validation re-run |
| `692bb61` / `1a27afd` / `bc2a147` | 3b | D28.2: new `ui/ticker_session.py::TickerSession(QObject)` keyed by uppercase symbol; `MainWindow` holds `_sessions` registry + `_req_to_session` routing table. Four clusters, suite green between each: (1) data plane — per-timeframe `BarAggregator`s, per-timeframe bars with `SESSION_BAR_CAP=5000` (front-loaded D28.4), refcounted RT lifecycle, `_last_chart_price` (D27.1), per-session alarm evaluation (DEC-1), `StreamHealth` migrated in; (2) history wave — req-id registry, watchdog, generation fencing; (3) studies config + fan-out; (4) drawings/groups. `load_chart(symbol, timeframe, extended_hours)` parameterised (no toolbar reads); `alarm_triggered` carries firing symbol. Deleted dead `_pending_brackets`, `_current_req_id`. Tick-burst baseline: 0.35ms/tick |
| `3e81f66` | 3c | D24 + D24.9: new `ui/popout_window.py::PopoutChartWindow` (28px header `SYMBOL · timeframe · mode` + close; `ChartPanel(editable=False)` — drawing/alarm/studies/timeframe/mode blocked, overlays render, crosshair/zoom/pan work). Toolbar "Pop out" + Ctrl/Cmd+P; `MAX_POPOUTS=10` with status message at cap. One IBKR subscription per symbol (refcounted: first holder subscribes, last releases). Always-on-top default OFF with per-window header context-menu toggle. D24.9: additive `popouts` table + `data/popout_store.py`; save on open/close and 500ms-debounced move/resize; lazy cache-first restore after connect. Smoke gate: 3 pop-outs → 1.27ms/tick, 0 full QPicture regenerations per tick |
| `ce1ef41` | 3d | D25: new `services/alarm_monitor.py::AlarmMonitor` + `AlarmStore.symbols_with_active_alarms()`. Headless sessions are ordinary `TickerSession`s (`views==0`, `monitored=True`): one 5-sec RT sub, `BarAggregator("1m")`, evaluation on every push (DEC-2). `prev_price` seeded from 1m cache, else first-tick seed with NO evaluation (no phantom). Zero history requests. Reconcile on connect / alarm CRUD / rearm / trigger / attach / detach; pacing guardrail (most-recently-active first + warning naming unmonitored symbols) |

### Commits (fix pass — review issues)
| SHA | Issue | Change |
|---|---|---|
| `8383d49` | HIGH | Deleted shadowing second `detach_view` in `ui/ticker_session.py` (:162) — it had killed the `alarm_monitor.on_session_detached` notification, so navigating away from an alarmed symbol tore the session down instead of promoting it to headless monitoring |
| `8ef0342` | MODERATE | Overlay-level `editable` flag on `AlarmOverlay`/`DrawingOverlay` (plumbed from `ChartPanel(editable=…)`); all IDLE mouse handlers inert when not editable; Delete gated. Also fixed an extra hole the reviewer missed: `DrawingOverlay.view_mouse_drag` mutating shared payload + double-click opening settings in read-only pop-outs |
| `282aae5` | MODERATE | `_restore_popouts` skips records whose (symbol, timeframe, mode) is already open; 10-cap enforced against open+new count (no duplicate windows on reconnect) |
| `448b3b0` | MOD-LOW | Pop-out attach catches `PacingExceeded` → status message + `singleShot` retry (skips if closed) |
| `97acc51` | MODERATE | `AlarmMonitor._start_monitoring` schedules `singleShot` retry on pacing exhaustion (skips if no longer headless+monitored); warning still names the symbol |
| `ba28c08` | — | Smoke-gate deviation recorded (see below); stale "≤2x" docstrings fixed |

### Deviation recorded (reviewer-accepted)
- **Smoke gate 2× → 5× baseline** (`[DEVIATION RECORD 2026-10-12]` in plan-draft.md §1): 4 independent pyqtgraph panels scale linearly by construction (measured 3.6×); Gate 2 (zero full QPicture regenerations per tick) is the real anti-R52 guard and holds; absolute budget 1.27ms vs 5000ms tick interval. Phase 4 (AC-D28.4) owns the 10-chart optimization.

### Decisions recorded
- Always-on-top: default OFF, per-pop-out header context-menu toggle (owner, 2026-10-12 — implemented in 3c).
- D24.9: additive `popouts` SQLite table (owner-confirmed; implemented, not QSettings).
- Per-session alarm evaluation (DEC-1) and event-driven headless evaluation on 5-sec pushes (DEC-2): implemented in 3b/3d.
- Restore dedup strategy: per-record skip on (symbol, timeframe, mode) already open (chosen over "restore only when empty" — precise on reconnect, still retries failed records).

### Follow-ups filed (not Phase 3 scope)
- Per-tick cost at the 5k bar cap untested with long series (Phase 4's problem).
- Historical/mkt-data path ≤20ms sleeps remain (pre-existing, bounded).
- Fix-4 nit: non-`PacingExceeded` exceptions in pop-out attach swallowed without logging.
- (Carried) `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests; 4h/daily forming-candle exactness; stale reqId accumulation.

---

## Phase 4 — Historical pacing, performance, teardown, test hardening

- **Status:** Code complete and review-**APPROVED**; branch `phase4-pacing-perf-teardown` (stacked on `phase3-sessions-popouts` @ `ba28c08`) NOT pushed and NOT merged. This is the last phase of the plan.
- **Review:** first verdict **REQUEST-CHANGES** (2 items); fix pass done; re-review verdict **Phase 4 PASSES gate** — and per the R52 reconciliation, **Phase 3 is cleared to merge to `main`**.
- **Tests:** 898 passing, 0 failing (offscreen). 43 new tests across the phase; no test touches live TWS/network.

### Commits (Phase 4)
| SHA | Item | Change |
|---|---|---|
| `2eb9206` | 4a | D28.3: rolling 600s non-blocking window for `reqHistoricalData` (expiry at oldest-slot + 600s, `PacingExceeded` instead of sleep, slot recorded only after issue); ~60 chunks/wave with singleShot continuation + watchdog re-arm; IBKR error 162 retried exactly once before finalising short; non-162 errors fail fast. `prime_aggregator` fails open. 11 new tests (monkeypatched-time pacing math; rapid symbol-switch → no 162 storm) |
| `28c4e69` | 4b-1 | D28.4: static-history + live-bar render layers — forming ticks refresh only the 1-bar live layer; static QPicture regen skipped unless bar-count/spacing changes. `regen_count` counters on both layers |
| `cfc6afc` | 4b-2 | Study cache wired for real: exact-match incremental `sma/ema/vwap/bollinger/rsi/macd_update` fns, tail-verified against batch (incl. RSI's seed quirk); `calculate_*` no longer runs per candle; ICT capped to trailing 500 bars |
| `1e47b63` | 4b-3 | Bisection over cached `_plot_xs`/`_plot_vols` for crosshair, volume ceiling, and the pan/zoom frame path. Caught a real regression: ceiling recompute ran before `_plot_vols[-1]` refreshed — fixed by reordering in `770bba4` |
| `4b55093` | 4b-4 | `TimeCollapseMap.extend(ts)` — tail step instead of full rebuild on new candles; verified extend ≡ fresh build incl. the identity→collapsed weekend flip |
| `463d51b` | 4b-5 | `BarCache.prune(symbol, timeframe, keep=5000)` hooked into wave finalize. Caught spec drift: two backfill tests had enshrined the unbounded cache (9600 seeded 1-min bars) — updated to assert the retention invariant (`770bba4`) |
| `860e8ec` | 4b-6 | **Binding 10-chart gate** (main + 9 pop-outs, 500 bars each): **4.45ms/tick (bound ≤50ms), 0 static full regens across 99 forming ticks, 990/990 live-layer refreshes, exactly 10 static regens on the trailing new-candle commit, all panels within `SESSION_BAR_CAP` with consistent cached arrays.** Supersedes the Phase 3 ≤5×/4-panel smoke gate for R52 |
| `5167875` | 4c | D28.5: `_closing` flag (data slots early-return; `closeEvent` idempotent); explicit order — persist prefs → cancel contract lookups → disarm timers (incl. wave-continue timer, added to `session.teardown()`) → cancel depth/RT subs → disconnect → **join `ibkr-reader` with 5s timeout** → clear UI. 3 tests (close mid-backfill; slots no-op when closing; double-close safe) |
| `3363422` / `c1a2ba2` | 4d | D28.6: T-1 alarm E2E verified-not-duplicated (the four assertions already live in `test_d24_alarm_full_chain.py`); T-2 close-path contract reconstruction for stock/option/future — **caught a real bug: `contract_type.upper()` produced invalid IBKR secTypes `OPTION`/`FUTURE`, now mapped to `OPT`/`FUT`**; T-4 drawing store→overlay round-trip per kind (all 5 kinds, payload byte-identical); T-5 `id_manager` behavioural + 8-thread concurrency tests. Deleted 3 doc-asserting tests + phantom `validate_sltp` (kept behavioural guards). Autouse `_isolate_test_db` fixture for DB hermeticity |

### Commits (fix pass — review issues)
| SHA | Issue | Change |
|---|---|---|
| `61aedd0` | MODERATE | Panel bar cap: `ChartPanel.update_last_bar` new-candle path now head-prunes at `SESSION_BAR_CAP` (same `config.settings` attribute as the session); prune path calls `_rebuild_collapse_map()` (not `extend`) and invalidates the study cache; non-prune path keeps incremental behaviour. Gate 3 tightened to `<= SESSION_BAR_CAP` |
| `3d12821` | MODERATE-LOW | `update_chart` now invalidates the study cache — makes the `indicator_service.py:137` claim ("a wholesale bar replacement invalidates the cache") actually true. Per-new-candle incremental path (`update_last_bar`) untouched |

### Review findings of note
- **Gate methodology judged SOUND:** Gate 1 (deterministic counters — 0 static regens / exactly 10 on new-candle commits) directly guards the R52 pathology; Gate 2 (≤50ms, measured ~4.8ms) is a generously-documented secondary backstop. Methodology honest (warm-up, synchronous tick-dispatch path measured, `processEvents` after). Coverage gaps filed as follow-ups: 500 not 5000 bars in the gate (O(1) forming ticks fine; O(n) new-candle regen untested at cap); no studies enabled in the gate; single-symbol layout only.
- **`contract.class_` gap: FOLLOW-UP, not blocking** (reviewer call): `_on_position_update` always stores `contract_type="stock"` (ibapi's `Contract` has no `class_`), so the corrected OPT/FUT close reconstruction is unreachable via the real position path. Pre-existing since the D22/D23 era; Phase 4's T-2 logic is correct and tested; with `conId` set the likely outcome is an IBKR rejection, not a silent wrong-instrument trade. Proper fix (derive from `contract.secType` + position-pipeline test) deserves its own commit.

### Follow-ups filed (not Phase 4 scope)
- `contract.class_` → derive contract type from `contract.secType` in the position path (safety-adjacent; shouldn't linger long).
- Full scroll-back paging (defined follow-up per plan §10.3 — out of scope).
- Pacing-deferred singleShot retries can fire post-teardown (degrade to harmless dead subscribe on disconnected client; `monitored` never cleared on teardown).
- Gate coverage: 5000-bar runs, studies under 10-chart load, 10-symbol × 1-panel layout.
- (Carried) `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests; 4h/daily forming-candle exactness; stale reqId accumulation; post-teardown `monitored` flag.

### USAGE.txt
- No user-facing changes in Phase 4 (pacing, rendering internals, teardown, tests are invisible). No USAGE.txt update needed.
