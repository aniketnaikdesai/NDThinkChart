# NDThinkChart — Phase Changelog

A working record of what changed in each implementation phase, for the team
(and the next team) to understand the evolution of the codebase. Normative
requirements live in `docs/requirements/requirements.md`; the target design in
`docs/architecture.md`. This file is the *as-built* history.

**Documentation gate (owner-instituted 2026-10-13):** before the next phase starts,
ALL of the following must be updated for the completed phase — no exceptions:

1. **Requirements documents** — the phase's requirements finalized and committed
   (e.g. `docs/requirements/`); no dangling draft-only requirements.
2. **Plan document** — the implementation plan updated to as-built for the phase.
3. **Architecture document** — as-built changes synced (`docs/architecture.md`).
4. **Phase changelog** — full entry: commits, tests, review verdicts, drive-by fixes,
   decisions, follow-ups (`docs/phase-changelog.md`).
5. **Usage / readme** — `USAGE.txt` updated for any user-facing change; `README`
   likewise if one exists.

No phase's code is pushed to GitHub until its docs are complete, and the next phase
starts only after the gate is satisfied. Each changelog entry is written from the
coder's and reviewer's reports for that phase, verified against the branch.

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

- **Status:** Code complete and review-**APPROVED**; branch `phase3-sessions-popouts` (stacked on `d27-correctness` @ `69a2313`) **merged to `main`** and pushed — the Phase 4 AC-D28.4 performance gate later passed, which cleared it per the R52 reconciliation.
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

- **Status:** Code complete and review-**APPROVED**; branch `phase4-pacing-perf-teardown` (stacked on `phase3-sessions-popouts` @ `ba28c08`) **merged to `main`** and pushed. *(This was not the last phase: four further phases — D36–D40 — followed; see their entries below.)*
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

---

## Phase D39 — Volume-burst alerts + symbol search

- **Status:** Code complete and review-**APPROVED**; branch `feat/d39-burst-search` merged to `main` @ `83f792a` (feature commit `90b01e7`, post-review advisories `0b50fb7`), and pushed. Docs gate (this entry) on `docs/d24-d28-requirements-architecture`.
- **Review:** **APPROVED**, no blocking findings. B.6 mock-endpoint grep PASSED (production tree clean — no mock/fake/stubbed endpoint of any kind outside `tests/`).
- **Tests:** 1009 passing, 0 failing (offscreen): 970 pre-existing + 39 new `tests/test_d39_burst_search.py`; no test touches live TWS/network; mocked `ib_client` only. Two load flakes observed in reviewer runs (`test_attach_live_feed_defers_with_status_and_retries`, `test_smoke_gate_three_popouts`) — pass in isolation, not regressions.

### Commits
| SHA | Item | Change |
|---|---|---|
| `90b01e7` | 39.1 | **Symbol search** — new `services/symbol_search.py`: debounced `reqMatchingSymbols(pattern)` (**≤1 per 300ms** of typing), `symbolSamples` override verified **arg-for-arg against the 10.51.1 wheel** (`reqId, contractDescriptions`); ≤16 samples, 5s timeout, exactly-once correlation, disconnected/empty guards. Search box in the **watchlist header** (expanding, capped 180px, **zero minimum width** — a 110px minimum broke D17 dock tests). Results popup: symbol·secType·exchange; select → bounded contract resolution → `load_chart` |
| `90b01e7` | 39.2 | **Volume baseline service** — new `services/volume_baseline.py`: **robust median/MAD** (never mean/stddev) per (resolved-contract, time-of-day bucket), N=30, ET minute-of-day buckets, per-minute normalization. Three-tier source chain: (1) persisted `volume_baseline` table (**`samples` JSON column** for exact recomputation — the steady state after days of use); (2) one-time `BarCache` prime, **local only, zero IBKR requests**; (3) rolling-30 fallback. Guards (binding): **1.0/min volume floor** (no evaluation on dust), **5-bar warm-up** with explicit "warming up (n/5)" status, **5%-of-median MAD floor** (flat data scores z=0; real bursts on flat baselines fire finite — no infinity). Roll invalidation: baseline keyed on D36's `footprint_cache_key` (front month embedded); key change tombstones in-session — DB rows for the old contract **cannot resurrect** |
| `90b01e7` | 39.3 | **`volume_burst` alarm kind** — `data/models.py::Alarm`: `kind: str = "price"` + `params: dict` (additive DB migration; price rows untouched). New `evaluate_volume_burst()` in `services/alarm_service.py`: z-score semantics only (never K-multiple language — C39.1), threshold from `params["z_threshold"]` (default 4.0). Wired into `TickerSession._on_aggregated_bar`'s per-push evaluation **alongside** `evaluate_alarms` — forming bars evaluated (**conservative: partial volume ÷ full minutes can only understate**), completed bars recorded; identical persist/trigger/rearm semantics (`AlarmStore.mark_triggered`, `alarm_triggered` toast+sound exactly once, grouped emission); chart overlay skips non-price alarms; `evaluate_alarms` is kind-filtered — **a price=0.0 burst alarm can never fire as a price alarm** (genuine pre-fix bug, caught and fixed) |
| `90b01e7` | 39.4 | **Index proxy for burst** — burst alarms on indices carry `params.proxy`/`proxy_label` from D36's `INDEX_PROXY` (**reused, not duplicated**). `AlarmMonitor.reconcile` routes to the **proxy tape's session** (ensured headless); **no session is created for the index itself**. Toasts labelled proxy-derived, e.g. "Volume burst on ES tape (z=9.4)" |
| `0b50fb7` | Review | Post-review advisories: **A1** — z-threshold spinbox floor raised **0.5→1.0** in both alarm dialogs + tooltip caution (below 1.0 fires on normal variance); **A2** — tombstone symmetry guard: `record()` consults the in-session tombstone set |

### Drive-by fixes (found while implementing, verified real)
1. **`primary_session` reuse confirmed:** the D37-added property is properly backed — no regression from D39's heavier `TickerSession` traffic.
2. **`evaluate_alarms` kind-filtering:** pre-fix, a `volume_burst` alarm with `price=0.0` could have fired as a price alarm. Kind-filtered as part of 39.3.

### Decisions recorded
- **Burst threshold — robust z-score (median/MAD, never mean/stddev)**, **user-tunable threshold**, baseline **compared against same-time-of-day history**, **N = 30 bars** (owner, 2026-10-13).
- **Search box in the watchlist header** (owner, 2026-10-13).
- **Index-proxy rule:** SPX→ES front-month (NDX→NQ etc.) for burst alarms — indices have no tape (owner, 2026-10-13); D36's resolver reused.
- **Search results show symbol·secType·exchange** — 10.51.1's `ContractDescription` carries only `contract` + `derivativeSecTypes`; there is no company-name field. The requirement's "company name" was an API-docs oversell (reviewer-verified); details resolve on selection instead.
- **No generic rate ticks needed** — evaluation uses session bar volumes (the specified N=30-bars design); ticks 54/55/56/63/64/65 remain available but are not required.
- Pacing: D39 adds no new IBKR budget load — search requests are debounced user-initiated traffic; the baseline prime is local-only (zero IBKR requests); burst evaluation rides the per-aggregator-push path.

### Review findings of note
- **APPROVED**, no blocking findings.
- B.6 mock-endpoint invariant: PASSED on the full diff + new files.
- **`symbolSamples` verified arg-for-arg** against the 10.51.1 wheel — the D36 B1/B2 lesson is now a standing habit.
- **Pre-fix bug acknowledged by the Coder:** kind-unfiltered `evaluate_alarms` would have let a burst alarm fire as a price alarm; kind-filtered before merge.
- **Reviewer advisories:** A1 (z-threshold floor 0.5→1.0 + tooltip) and A2 (tombstone guard in `record()`) applied post-review in `0b50fb7`.
- **AC-D39.1–AC-D39.5 genuinely verified** (debounce cap; ≤16 samples → contract resolution → `load_chart`; synthetic skewed volume → median/MAD baseline → burst fires exactly once at z≥threshold; flat data never fires; fired → store shows triggered, re-arm works, headless monitored set includes it; full suite green).

### Follow-ups filed (not Phase D39 scope)
- D40 not started.
- (Carried) delayed-depth labeling if ever observed; pop-out panels to adopt footprint later; `contract.class_` never populated; `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests (plus the two D39 reviewer-run load flakes); 4h/daily forming-candle exactness; stale reqId accumulation.

### USAGE.txt
- New "Volume-burst alerts & symbol search (Phase D39)" section: creating a burst alarm, z-threshold, warm-up note, search box location, proxy labels.

---

## Phase D40 — TWS daily-lifecycle pause/resume

- **Status:** Code complete and review-**APPROVED**; branch `feat/d40-tws-lifecycle` merged to `main` @ `b366b19` (feature `4ac2453`; the reviewer's findings were applied **in the merge commit `b366b19` itself** — an earlier draft of this entry cited a review-fix SHA `d6f38e8`, which **does not exist** in the repository), and pushed. Docs gate (this entry) on `docs/d24-d28-requirements-architecture`.
- **Review:** **CHANGES REQUIRED → rework → APPROVED.** First pass found 1 blocking (B1, below); the Coder fixed it plus 2 advisories, added a B1 regression test (verified to **fail on the old call order** with the stale 99.0 seed and **pass on the fix**), and the re-check verified APPROVED. B.6 mock-endpoint re-grep PASSED (production tree clean — no mock/fake/stubbed endpoint of any kind outside `tests/`).
- **Tests:** 1020 passing, 0 failing (offscreen): 1009 pre-existing + 11 new `tests/test_d40_tws_lifecycle.py`; no test touches live TWS/network; mocked `ib_client` only. One load flake in the reviewer's run (`test_place_order_defers_when_limiter_empty` — wall-clock timing; the order path is untouched — passes in isolation, not a regression).

### Commits
| SHA | Item | Change |
|---|---|---|
| `c24f4f3` | 40.1 | **Disconnect classification** — new `ibkr/client.py::DisconnectClass` (`TRANSIENT` / `TWS_GONE`); `connectionClosed()` classifies TWS-gone per ibapi's own docstring ("fires when TWS closes the sockets connection … or when TWS is shut down"), records the classification before emitting `disconnected`, and **restarts the backoff reconnect loop** — a genuine drive-by bug fix: the old code stopped polling after `connectionClosed` and scheduled nothing, so the app could **never notice a morning TWS login without a restart**. Backoff base 2s capped 16s (~1 gentle attempt per 16s overnight). Error 502 during paused backoff downgraded to a debug log (no all-night status-bar spam); a 502 at startup with no prior connection still surfaces. `_last_disconnect_class` reset on connect |
| `c24f4f3` | 40.2 | **Pause** — new `AlarmMonitor.pause_all()`: records per-symbol pause-start, sets `monitoring_paused` on every alarmed session; both evaluation entry points (price-alarm and burst-alarm in `_on_aggregated_bar`) gate on the flag — headless uses the same path. `conn_badge_text(..., monitoring_paused=...)` shows the owner-approved **"Monitoring paused — TWS disconnected"** in amber `#fbbf24`, never green. Proxy burst alarms pause with their tape |
| `c24f4f3` | 40.3 | **Resume** — on `connected`, the as-built D27 replay re-issues subscriptions, then `reconcile()` FIRST, then `resume_all()`: every session's `prev_price` re-seeded to None (**AC-D25.3 first-tick-no-eval guard** — no phantom triggers), staged subscribes finished, gap intervals returned. Per-symbol gap report surfaced in the status bar, e.g. "ES, NQ unmonitored 22:14–09:40". Alarms created while TWS is down are **staged** (`_monitor_subscribe_pending`) and covered on resume. Backfill waves in flight keep the existing generation fencing |
| `c24f4f3` | 40.4 | **Transient path unchanged** — poll-driven drops and 1100/1101/1102 stay transient: fast D27 reconnect, no pause UI, no gap accounting, `prev_price` untouched |
| `b366b19` | Review | **B1 fix (blocking):** call order swapped to reconcile-then-resume — reconcile-created sessions now take the staged path (`monitoring_paused=True`, `last_chart_price=None`, subscribe deferred) instead of the normal path with a stale cache seed (phantom-trigger hole). Regression test `test_d40_2_resume_session_recreated_mid_pause_no_phantom`. **A1:** `_last_disconnect_class` reset on connect (a stale TWS_GONE would otherwise downgrade a later transient drop to the paused path). **A2:** cancel-then-arm reconnect timer (no double-arm) |

### Drive-by fixes (found while implementing, verified real)
1. **Reconnect loop never restarted on `connectionClosed`:** the old code stopped polling and scheduled nothing — the app could never detect a morning TWS login without a restart. Fixed as part of 40.1 (reviewer-verified real).

### Decisions recorded
- **TWS only — never Gateway** (owner, 2026-10-13). Aniket closes TWS nightly and logs in manually each morning; there is no 24/7 headless scenario to protect — D40 is pause/resume around TWS's daily lifecycle.
- **Badge wording/placement** — "Monitoring paused — TWS disconnected" in the connection-badge area, amber `#fbbf24`, never a green "connected" appearance while paused (owner-approved, 2026-10-13).
- **No phantom alarm triggers after the gap** — resume re-seeds `prev_price` to None per session (AC-D25.3 first-tick-no-eval guard); gap accounting is per-symbol and surfaced, never silent ("ES, NQ unmonitored 22:14–09:40").
- **Transient drops keep the fast D27 path** — classification boundary: `connectionClosed` → TWS_GONE only if a live session existed; TWS daily auto-restart classifies as TWS-gone per the plan's edge cases.

### Review findings of note
- **B1 (blocking, fixed):** `resume_all`-before-`reconcile` let reconcile-created sessions take the normal path with a stale cache seed — phantom-fire hole. Fixed by the call-order swap + staged path for reconcile-created sessions; regression test verified fails-on-old-order / passes-on-fix.
- **A1** (`_last_disconnect_class` reset on connect) and **A2** (cancel-then-arm reconnect timer) applied post-review.
- **AC-D40.1–AC-D40.5 genuinely verified:** pause on TWS close (badge text + all symbols paused); resume with no phantoms (price through an alarm level fires exactly once; resume alone fires nothing); gap report names symbols + durations; transient drop → fast reconnect, no paused state; full suite green.
- B.6 mock-endpoint invariant: PASSED on the re-grep of the full D40 diff.

### Follow-ups filed (not Phase D40 scope)
- (Carried) delayed-depth labeling if ever observed; pop-out panels to adopt footprint later; `contract.class_` never populated; `_close_position_by_id` bypass; kill-switch failed-cancel marking; flaky UI-timing tests under load; 4h/daily forming-candle exactness; stale reqId accumulation.
- **No further phases (D41+) without Aniket's explicit go-ahead** (owner, 2026-10-13).

### USAGE.txt
- New "TWS daily lifecycle (Phase D40)" section: what the paused badge means, what happens on morning login, gap report, transient vs TWS-gone.

---

## Phase D38 — Events & news (event markers + news-for-holdings digest)

- **Status:** Code complete and review-**APPROVED**; branch `feat/d38-events-news` merged to `main` @ `8599ce4` (feature commit `b893911`), and pushed. Docs gate (this entry) on `docs/d24-d28-requirements-architecture`.
- **Review:** **APPROVED**, no blocking findings. B.6 mock-endpoint grep PASSED (production tree clean — no mock/fake/stubbed endpoint of any kind outside `tests/`). Single-secondary-source rule PASSED (no other external API anywhere in the tree).
- **Tests:** 970 passing, 0 failing (offscreen): 947 pre-existing + 23 new `tests/test_d38_events_news.py`; no test touches live TWS/network; mocked `ib_client` only. yfinance calls are mocked at the boundary; a B.6-style no-mock-endpoint test follows the D36/D37 pattern.

### Commits
| SHA | Item | Change |
|---|---|---|
| `b893911` | 38a.1 | `ibkr/news.py::NewsManager` — `reqNewsProviders()` → the user's actual entitlement list (API news requires API-specific subscriptions — most TWS news services are NOT available via the API); per-holding `reqHistoricalNews(conId, providerCodes, startDateTime, endDateTime, totalResults)` issued **sequentially via a FIFO queue** (no headline-fetch storm on digest open), pacing-aware; `reqNewsArticle(providerCode, articleId)` on headline click. Bridge: 4 signals — `news_providers` / `historical_news` / `historical_news_end` / `news_article`; `ibkr/client.py`: 4 new overrides (10.51.1 arg-for-arg verified) |
| `b893911` | 38a.2 | `ui/news_digest_dock.py` — **repositionable, closable digest dock**, reopenable from a minimal View-only menubar (`View → News Digest`, `Ctrl+Shift+N`; the app had no menubar — added, drive-by). Refresh = **backfill on open** (38a.1) + **live push primary** (generic tick `"292"` on holdings' S0 subscriptions → `tickNews` → headline prepended) + **15-min periodic re-query backstop** (QTimer, only while the digest is open). Non-charted holdings get lightweight headless `TickerSession`s while the digest is open (D24 headless semantics), torn down on close; their S0 lines are counted in the MD-line budget. Honest states — "No API news subscription" (entitlement honesty), "No holdings", "Headlines unavailable" — never silently empty |
| `b893911` | 38b.1 | **Event-provider layer** — new `data/events/` package: `provider.py` (`Event` dataclass with id/type/symbol/date/source/details, corporate-events-only guard **rejecting non-corporate types at the provider boundary** — AC-D38.4; `EventProvider` ABC; defensive tick-59 dividend parser `parse_ib_dividend_string` that **never raises**), `ibkr_source.py` (dividends from session tick-59 state, **skips futures contracts** — no dividend stream there), `yfinance_source.py` (SQLite per-symbol cache: 24h TTL, **6h revalidation for events within 7 days** so corrections propagate; single `QThread` worker, **≥1s between calls**, own connections — never on the IBKR pacing budget; lazy import; `failed_at` distinguishes outage from loading). `requirements.txt`: **`yfinance==1.7.0`** with a re-pin policy comment (re-pin quarterly or whenever Yahoo breaks the library; every re-pin re-runs the full offscreen suite). **yfinance is the sole secondary source — no other external API** (owner-mandated 2026-10-13; WSH removed entirely) |
| `b893911` | 38b.2 | `ui/event_marker_overlay.py` — time-axis markers with **distinct icon/color per type**: earnings gold ◆E, dividend green ●D, split blue ▲S; countdown label ("Earnings in 3d") for the next upcoming event. Source priority **IBKR tick-59 dividends first → yfinance** (earnings/splits + dividend fallback); IBKR-first merge **drops same-date yfinance dividends**. **No-data rule (owner):** both sources empty → explicit "no event data" state, logged for the owner (owner decides on feature removal). Markers are **id-keyed, not date-keyed** — date corrections move the marker |
| `b893911` | S0 | Generic-tick union extended to `"225,292,456"` (auction, news push, IB Dividends); new `s0_register_many`/`s0_deregister_many` batch helpers (single resync — fixes double re-subscribe churn); one-subscription-per-symbol preserved |

### Drive-by fixes (found while implementing, verified real)
1. **Self-fixed:** duplicated `_on_auction_tick` body tail — dead code removed.
2. **Digest dock init-order fix:** signal wiring deferred to first dock open (the digest's sessions don't exist at construction).
3. **Minimal View-only menubar added** (the app had none) — just `View → News Digest` (`Ctrl+Shift+N`), no other menu surface.

### Decisions recorded
- **yfinance is the sole secondary data source** (owner, 2026-10-13) — no other external API, ever. If neither IBKR nor yfinance yields a feature's data, the UI shows an explicit no-data state and the owner is informed — the owner then decides whether the feature is removed. Never a silently empty chart, never a third source added silently.
- Source priority: **IBKR tick-59 dividends first** (live, free), yfinance for earnings/splits and as dividend fallback.
- Marker styling — **distinct icon/color per event type** (owner, 2026-10-13): earnings gold ◆E, dividend green ●D, split blue ▲S.
- Digest placement — **repositionable, closable dock**, reopenable from the menubar (owner, 2026-10-13).
- Digest refresh — **backfill on open + live push primary + periodic re-query backstop** (owner-confirmed, 2026-10-13).
- **No-data rule (owner):** both sources empty → explicit "no event data" state + logged for the owner.

### Review findings of note
- **APPROVED**, no blocking findings.
- B.6 mock-endpoint invariant: PASSED on the full diff + new files.
- **Single-source rule PASSED:** tree-wide check — no Alpha Vantage, Massive, FMP, Finnhub, Twelve Data, or any other external API; yfinance is the only non-IBKR network dependency.
- **4 new news overrides verified arg-for-arg** against the 10.51.1 wheel (the D36 B1/B2 lesson applied proactively).
- **Existing-test edits signed off as genuine:** D37 S0-union assertion updates (the union string grew) and digest-dock region changes — neither weakens the D1–D37 guarantees.
- **Reviewer advisories:** A1 applied post-review (two merge tests re-pointed at the real `TickerSession._merge_events` — they had been asserting on a helper); A2 harmless double `events_updated` emit noted as benign; A3 `get_earnings_dates(limit=12)` validated as correct usage.
- **AC-D38.1–AC-D38.6 genuinely verified** (synthetic provider events → three distinctly-styled markers + countdown; 2 holdings + synthetic headlines → grouped digest + article fetch; no entitlement → explicit state; economic-calendar payload → filtered out; mocked yfinance outage → unavailable state, chart unaffected; full suite green).

### Follow-ups filed (not Phase D38 scope)
- D39–D40 not started.
- Re-pin `yfinance` quarterly or whenever Yahoo breaks the library — every re-pin re-runs the full offscreen suite (policy recorded in `requirements.txt`).
- (Carried) delayed-depth labeling if ever observed; pop-out panels to adopt footprint later; `contract.class_` never populated; `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests; 4h/daily forming-candle exactness; stale reqId accumulation.

### USAGE.txt
- New "Event markers & news digest (Phase D38)" section: marker icons, countdown, digest open/close, no-entitlement messages, yfinance note.

---

## Phase D37 — Microstructure (depth heatmap + auction imbalance)

- **Status:** Code complete and review-**APPROVED**; branch `feat/d37-microstructure` merged to `main` @ `9958891` (feature commit `69c2d66`), and pushed. Docs gate (this entry) on `docs/d24-d28-requirements-architecture`.
- **Review:** **APPROVED**, no blocking findings. B.6 mock-endpoint grep PASSED (production tree clean — no mock/fake/stubbed endpoint of any kind outside `tests/`).
- **Tests:** 947 passing, 0 failing (offscreen): 927 pre-existing + 20 new `tests/test_d37_microstructure.py`; no test touches live TWS/network; mocked `ib_client` only. One load flake observed in `test_smoke_gate_three_popouts` (wall-clock timing gate; passes in isolation and on re-runs — not a regression).

### Commits
| SHA | Item | Change |
|---|---|---|
| `69c2d66` | 37.0 | **Substrate S0 — generic-tick plumbing (shared by D37/D38).** `ibkr/client.py`: `tickGeneric`/`tickString`/`tickNews` overrides (10.51.1-verified — `tickNews` is 6-arg incl. `extraData`); `ibkr/bridge.py`: 3 new signals; `ibkr/market_data.py`: `req_mkt_data(contract, generic_ticks="")`; per-symbol generic-tick union (`"225"` auction, `"292"` news push, `"456"` IB Dividends — D38 use) merged into the single per-symbol subscription; features register/deregister, session re-subscribes only when the union changes |
| `69c2d66` | 37.1 | `services/depth_heatmap.py` — price-keyed live book from the depth op stream (insert/update/delete + L2 MPID/exchange rows); 60×30s price×time matrix; imbalance `(bidVol−askVol)/(bidVol+askVol)` computed over **top-5 AND top-10** on every op; refcounted per symbol (feed lives only while `views > 0`); depth replays on reconnect via the D27 path; `isSmartDepth` (D36 B2 fix) carried as row provenance for SMART-row disambiguation |
| `69c2d66` | 37.2 | `ui/depth_heatmap_item.py` — price-aligned overlay strip at the chart's right edge (live layer, Bookmap-style); 100-op burst → **0 static regens** (D28 discipline holds) |
| `69c2d66` | 37.3 | Auction **header chip**: imbalance side + paired shares + indicative price from ticks **34** (auction volume) / **35** (auction price) / **36** (auction imbalance) via the S0 `"225"` generic list, tick **61** (regulatory imbalance) when present; chip **highlights during 9:25–9:35 / 15:55–16:05 ET**; click expands a popover with raw values; absent ticks → explicit "no auction data" state |
| `69c2d66` | 37.4 | Degradation: IBKR error **354** on `reqMktDepth` → explicit `no_entitlement` state, feed cancelled, panel shows "Depth subscription required" + status bar `Depth [354]: <server message>` — never silently empty. Depth feeds refcounted 3–60 with separate sub-manager tags `DEPTH_HEATMAP`/`S0_TICKS` (the DOM's `unsubscribe_all_of_type(DEPTH)` would otherwise wipe session feeds) |
| `69c2d66` | 37.5 | `services/md_line_guard.py` — owns the §7 market-data-line accounting: `ok` <90, `approaching` 90–99 (warns **naming the symbol**), `exceeded` ≥100 (refuses **naming the symbol**); S0's per-symbol reqMktData lines counted explicitly |

### Drive-by fixes (found while implementing, verified real)
1. **Latent main-branch bug:** `primary_session` was referenced **26×** but never defined — any footprint/depth toggle would have raised `AttributeError`. Fixed: properly backed property added (`ui/main_window.py`).

### Decisions recorded
- Depth heatmap **default ON — CONFIRMED by the owner 2026-10-14 (Q44 / assumption A67)**. The reviewer had recommended **OFF** for consistency with D36's OFF default and to avoid burning depth budget by default; the owner chose ON. Code defaults ON (unchanged).
- Heatmap placement — **chart overlay** (price-aligned, live render layer), not a dock panel (owner, 2026-10-13).
- Auction presentation — **expandable header chip**, not a panel (owner, 2026-10-13).
- Imbalance — **compute both, headline top-5, top-10 as a click toggle** on the headline label (owner, 2026-10-13).
- Known limitation (recorded in code): if TWS delivers **delayed depth instead of** the 354 error, it would render unlabeled — the 354 path is handled; delayed-depth labeling is a follow-up if the behavior is ever observed.

### Review findings of note
- **10.51.1 signatures verified arg-for-arg** against the installed wheel (no drift beyond what D36's 38a.0 already fixed).
- **D27 reconnect test edit explicitly signed off:** replay assertions extended for S0/depth feeds — the D27 reconnect guarantee is not weakened.
- **AC-D37.1–AC-D37.5 genuinely verified** (heatmap matrix from op stream, imbalance sign-correct for N=5 and N=10, auction chip from synthetic 34/35/36, 354 → explicit state, full suite green).
- B.6 mock-endpoint invariant: PASSED on the full diff + new files.

### Follow-ups filed (not Phase D37 scope)
- D38–D40 not started.
- Delayed-depth labeling, if the behavior is ever observed.
- (Carried) pop-out panels to adopt footprint later; `contract.class_` never populated; `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests; 4h/daily forming-candle exactness; stale reqId accumulation.

### USAGE.txt
- New "Depth heatmap & auction chip (Phase D37)" section: overlay toggle, top-5/top-10 headline click, chip expand, auction-window highlight, no-entitlement message.

---

## Phase D36 — Footprint charts

- **Status:** Code complete and review-**APPROVED**; branch `feat/d36-footprint` @ `89fe152` (single squashed commit), later **merged to `main` @ `efffc51`** and pushed. Docs gate (this entry) on `docs/d24-d28-requirements-architecture`.
- **Review:** first verdict **CHANGES REQUIRED** (3 blocking + 5 advisories + 1 cosmetic); rework done; re-review verdict **APPROVED** (every finding verified, not trusted).
- **Tests:** 927 passing, 0 failing (offscreen). 29 new `tests/test_d36_footprint.py`; no test touches live TWS/network; mocked `ib_client` only. Includes `test_ac_d36_3_production_tree_has_no_mock_endpoint` — scans `ibkr/`, `services/`, `ui/`, `data/` for fake/mock/stub/simulated clients/servers/endpoints (owner rule: mocks exist only in tests).

### Commits
| SHA | Item | Change |
|---|---|---|
| `89fe152` | 36.1 | `ibkr/tick_history.py::TickHistoryManager` — backward-paging `reqHistoricalTicks` client (1000-tick windows, BID_ASK + TRADES), pacing-counted via `pacing_manager` (never sleeps), zero `reqTickByTickData` (AC-D36.3 asserted on the request registry + source call-site scan). Bridge: 2 new signals; `ibkr/client.py`: 2 overrides (a third pair — the histogram path — was removed under this phase's deviation 1) |
| `89fe152` | 36.2 | `services/footprint_service.py` — per-level `{bidVol, askVol, delta}` buckets from BID_ASK ticks, per-level trade volume + trade count from TRADES ticks; bounded waves (≤60 requests/wave), viewport-newest-first, lazy-fill on scroll/timeframe change, structural per-bar loading/unavailable states, forming-bar incremental refresh following the selected metric |
| `89fe152` | 36.3 | `ibkr/contracts.py`: `INDEX_PROXY` (SPX→ES, NDX→NQ, DJI→YM, RUT→RTY), `resolve_footprint_contract()` (front-month via existing `_front_month()` schedule), `footprint_cache_key()` — all cache/state keys use the RESOLVED contract (e.g. `ESZ6`), never the continuous symbol |
| `89fe152` | 36.4 | `data/footprint_cache.py` + additive `footprint_cache` table (`data/db.py`) — one compressed JSON blob per (resolved contract, date, timeframe); read before backfill, write on completion; **only** for SPX/SPY/QQQ/ES-front/NQ-front (owner decision), all other symbols re-fetch per session (in-memory only) |
| `89fe152` | 36.5 | `ui/footprint_item.py` renderer + `ui/chart_panel.py`/`ui/main_window.py`/`ui/ticker_session.py` wiring — **display-style toggle** (classic bid×ask bars vs heatmap-shaded candles) **× metric selector in heatmap mode** (per-level volume vs per-level trade count); classic is volume-only; intraday + daily; completed bars static (0 static-layer regens on 100-tick burst, AC-D36.4); forming bar incremental |
| `89fe152` | 38a.0 | `requirements.txt`: `ibapi>=9.81` → `ibapi-latest==10.51.1` (plain `ibapi==10.51.01` is not on PyPI — verified). Full suite re-run green on the aligned version before any D36 code. **Drive-by 10.51.1 breakage fixed:** `EWrapper.error` is now 5-arg `(reqId, errorTime, errorCode, errorString, advancedOrderRejectJson)` |

### Drive-by fixes (found while implementing/reviewing, verified real by reviewer)
1. `orderStatus` override was missing 10.51.1's 11th param (`mktCapPrice`) — **TypeError on every order-status callback** in the reader thread, which would have broken the D26 safety layer. Fixed: 11th param added, `order_status` signal → 11 args (11th typed `object`, None-safe), `_on_order_status` updated. (Reviewer B1 — the 38a.0 gate caught `error()` but missed this.)
2. `updateMktDepthL2` override was missing 10.51.1's 8th param (`isSmartDepth`) — **TypeError on every L2 depth update**, breaking existing DOM depth and making D37 DOA. Fixed: param added, `update_mkt_depth` signal → 7 args, `_on_mkt_depth` accepts `is_smart_depth` (carried for D37's SMART-row disambiguation). (Reviewer B2.)
3. Infinite loop in `_fp_pump` on unexpected request failure — the generic `except` returned `True`, re-queuing the same spec forever → **main-thread hang**. Fixed: return `False` (bounded defer via the continue timer). (Reviewer B3.)

### Decisions recorded
- Footprint default **OFF** behind a chart toggle (owner, 2026-10-13) — pacing-expensive feature as opt-in; reviewer agreed.
- Heatmap metric selector (owner, 2026-10-13): per-level **volume** vs per-level **trade count** in heatmap mode; classic mode is volume-only (trade count has no bid/ask split to render as bars).
- **As-built deviation (reviewer-confirmed):** `reqHistogramData(tickerId, contract, useRTH, timePeriod)` takes **no date parameter** — per-bar histograms are impossible, so the planned histogram path was REMOVED from code and docs. Tick-count metric now comes from the same TRADES tick pages as volume: **one dataset, two metrics, zero new requests** (strictly better than plan; the owner's original "same per-level data" decision is now literally true). Dead histogram plumbing deleted (reviewer A1); §7 histogram budget entry deleted.
- yfinance as sole secondary data source + WSH removal are D38 decisions (recorded in the D36–D40 drafts); no D36 code depends on them.
- Owner rule (binding, 2026-10-13): mocked/fake IBKR client — generalized to **any mock endpoint** — exists **only in tests, never in production code**. Standing Code Reviewer duty (pipeline-v3 `code_reviewer.md` step B.6): every review greps for mock endpoints in production code as a blocking check. D36's B.6 grep PASSED.

### Review findings of note
- **Rework advisories (all fixed, reviewer-verified):** A1 dead histogram plumbing removed; A2 forming-spec reqId leak in `on_fp_error` (now unregisters + forgets); A3 dataless completed bars stuck on "loading" (now move to `_unavailable_bars`); A4 disconnect-mid-wave zombie (new `on_fp_disconnect()`/`on_fp_reconnect()` + `_ibkr_connected` guards, wired into connect/disconnect); A5 forming-bar initial state UNAVAILABLE→LOADING (required changing one existing test's expectation — reviewer signed off: the old assertion had been passing on the bug).
- **AC-D36.1–AC-D36.5 genuinely verified** — reviewer read every test (bucket sums, 1000-tick page contiguity, registry assertion for AC-D36.3, zero footprint refs in the per-tick path for AC-D36.4).
- **10.51.1 lesson (architecture-relevant):** the 38a.0 "re-verify signatures" gate caught `error()` but missed `orderStatus`/`updateMktDepthL2` — on future API upgrades, re-verify **ALL** `EWrapper` overrides against the wheel, not just the ones the plan names.

### Follow-ups filed (not Phase D36 scope)
- Pop-out panels to adopt footprint later (the `TickerSession` footprint service is shared; only the main chart is wired this phase).
- D37–D40 not started.
- (Carried) `contract.class_` never populated; `_close_position_by_id` bypass; kill-switch failed-cancel marking; two flaky UI-timing tests; 4h/daily forming-candle exactness; stale reqId accumulation.

### USAGE.txt
- New "Footprint charts (Phase D36)" section: toggle location, style toggle, metric selector, OFF default, cache scope, loading states.

---

## Phase P6 (D47) — chart migration to Lightweight Charts + P6-T13 removal (as-built, appended 2026-10-28)

- **Status:** Built 2026-10-26 (waves `P6-T01`…`P6-T12` + hotfix trail `Q-1`…`Q-17`); **P6-T13 executed 2026-10-27
  as removal commit `6e35b27`** (owner-approved). The tree is LWC-only: `ui/chart_view.py::create_chart_view`
  always returns the LWC view; `NDT_CHART_ENGINE` / `QSettings chart/engine` no longer select a renderer.
- **Review:** Code Reviewer pass over `P6-T01`…`P6-T12` + `Q-1`…`Q-17` verdict **REVIEW_COMPLETE** 2026-10-27
  (`docs/code_review/review_log_P6.md` — no blocking code defect; 1 should-fix ESC-070 silent engine start,
  3 nice-to-have, 1 Task Manager note). Post-review ad-hoc investigation of the owner's 1-min backfill
  starvation filed ESC-075 (blocking) + ESC-076/077/078 + ESC-079 (budget invariant gap), all open into P7.
- **Gate:** `docs/build/gate_P6_T13.md` — owner approval SATISFIED 2026-10-27; the one-clean-live-session
  sign-off (AC-D47.8 / S59) **WAIVED, NOT SATISFIED** (no live session run); oracle decision RETIRE (34
  engine-specific + 30 oracle-comparison suites went with the engine; lost coverage ledgered in
  `docs/lwc_parity_matrix.md` "Retired coverage (P6-T13, 2026-10-27)").
- **Parity:** feature-parity rows 1–18 Done/accepted (Q-8 + Q-9 reconciliations, each on a named passing test);
  row 19 (pyqtgraph retained/default) Retired — retention is moot post-removal. Parity and deletion are
  recorded separately; no row claims live-session validation.
- **Tests:** wave gate suites per `docs/build/results/P6-T*.json` + `Q-*.json`; full offscreen suite green at
  each landing (see `docs/build/test_verification.json`).
- **Follow-ups (not P6 scope):** ESC-070 (surface engine-start failure) still owed; the one clean live session
  is still owed as live validation of the LWC-only tree; ESC-075…ESC-079 feed P7 (per-load cap S-P7-1) with
  the `AC-D16.8` restatement open as Analyst debt.
