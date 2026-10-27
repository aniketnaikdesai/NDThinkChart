# Investigation — the 1-min chart stops at 10/15 and the console fills with error 162

**Reported (owner):** "1 min chart won't plot beyond 10/15 and error message. I don't know if they are limited."

Verbatim log lines reported:

```
Aggregator priming pacing-limited; retrying once in 1.0s
ERROR 66 1793072477098 162 Historical Market Data Service error message:API historical data query cancelled: 66
ERROR 68 1793072477098 162 ... cancelled: 68
ERROR 70 ... cancelled: 70        ERROR 75 ... cancelled: 75
ERROR 77 ... cancelled: 77        ERROR 79 ... cancelled: 79
ERROR 81 ... cancelled: 81        ERROR 89 ... cancelled: 89
ERROR 91 ... cancelled: 91        (9 lines, ~100 ms apart)
Aggregator priming pacing-limited; retrying once in 1.0s
ResizeObserver loop completed with undelivered notifications. (ndt://lwc/chart.html:0)
```

**Verdict: not a data-permission limit.** It is a self-inflicted starvation of the app's own
`reqHistoricalData` budget by the 1-min backfill wave, combined with "persist only when the whole wave
finishes" + "a reload cancels the wave and throws its bars away". The 162 lines are the notation for
*our own* mass cancel on reload, not IBKR refusing an entitlement.

---

## 1. The state the app is actually in (production DB, read-only)

`~/Library/Application Support/NDThinkChart/charting_app.sqlite3`:

| symbol | timeframe | ext_hours | bars | first bar (ET) | last bar (ET) |
|---|---|---|---|---|---|
| SPY | **1 min** | 1 | **601** | 2026-10-15 04:00 | **2026-10-15 14:00** |
| SPY | 5 mins | 1 | 5952 | 2026-09-14 04:00 | 2026-10-26 19:55 |
| AAPL | 5 mins | 1 | 5952 | 2026-09-14 04:00 | 2026-10-26 19:55 |

Two facts fall straight out of that table:

* the 1-min series is real SPY data (values, volumes sane) and it **stops mid-session on 10/15**, so
  the chart's right edge *is* 10/15 — it is not a rendering problem;
* the 5-min series for the **same symbol** is current through today, so historical data, permissions
  and the transport all work. The failure is specific to the 1-minute timeframe.

The 601 bars are contiguous, 04:00→14:00 ET, i.e. **one** 1-D request's worth of extended-hours
1-min bars. Nothing before it and nothing after it was ever written, which tells us the last wave that
reached completion was that single chunk on 10/15 — every attempt since then has died before its
completion, which is the only thing that writes bars (see §3).

## 2. How much work ONE 1-min load asks for (measured, not estimated)

`MainWindow.load_chart` asks the planner for the D42 depth floor
(`settings.MIN_INTRADAY_SESSIONS = 30`) plus the 10/16→now hole, and `plan_requests` chunks each span at
`TIMEFRAME_CONFIG[timeframe]["duration"]`. For `1 min` that duration is `1 D` — the IBKR per-request
maximum for 1-min bars — so the floor needs one request **per calendar day**:

```
1 min    empty cache ->  43 requests   ~45 s to issue   86 % of the 50/600 s budget
1 min    cache as-is  ->  42 requests   ~44 s to issue   84 % of the 50/600 s budget
5 mins   empty cache  ->   9 requests   ~ 9 s            18 %
15 mins  empty cache  ->   9 requests   ~ 9 s            18 %
1 hour   empty cache  ->   5 requests   ~ 5 s            10 %
4 hours  empty cache  ->   2 requests   ~ 2 s             4 %
```

Driven through the real `TickerSession` + real `PacingManager` (`config/settings.HISTORICAL_MIN_INTERVAL_S = 1.0`)
with a fake transport, one SPY 1-min load behaves exactly like this:

```
plans for ONE 1-min load: 42
first issue t+0.00s, last issue t+43.14s      (issue gaps 1.04–1.10 s)
wave complete at t+44.7s
budget used: 42/50 per 600 s
```

So **the 1-minute timeframe is the only one whose cold catch-up nearly exhausts the app's entire
rolling budget** (`MAX_HISTORICAL_PER_600S = 50`). The app can afford exactly **one** such load per ten
minutes, and it shows the user nothing until the 45th second (§3).

## 3. Why a reload loses everything (and cannot catch up)

Three properties compose into a trap:

1. **Bars are only persisted and rendered when the whole wave finishes.** `_pending_bars` accumulates
   in `TickerSession` (`ui/ticker_session.py:987`); the only `BarCache.save_bars` + `set_bars` is
   `MainWindow._finalize_history_wave` (`ui/main_window.py:2039-2073`), reached only from
   `_on_session_wave_complete` when `_history_req_ids` and `_wave_plan_queue` are both empty
   (`ui/ticker_session.py:953-956`). During the 44 s the chart shows the cache, i.e. 10/15.
2. **Every `load_chart` cancels the in-flight wave and deletes what it has already fetched.**
   `ui/main_window.py:1705-1712` calls `new_session._cancel_history_requests()`, which (a) calls
   `cancelHistoricalData` on **every** tracked reqId and (b) sets `self._pending_bars = []`
   (`ui/ticker_session.py:833-842`). So a reload is not "resume" — it is "start over, and forget".
3. **A cancelled request still counts against the rolling budget.**
   `record_historical_slot()` is applied at issue (`ibkr/market_data.py:63-64`) and nothing refunds it on
   cancel. Measured: with 9 requests already spent, a fresh 42-chunk load is **one short** of the
   budget, so its last chunk has to wait for the oldest slot to expire — **≈590 s (10 minutes)**.

The 1-minute chart is therefore in a stable bad state: one attempt costs 86 % of the budget and 45 s of
silence; the natural reaction (press **Load** again, or flip Ext Hours / timeframe) discards the
attempt *and* leaves the budget short, so the next attempt cannot finish inside the window either
(§7 of the numbers above). That is exactly what the reported log is a snapshot of.

## 4. What the 162 lines are

`ERROR <reqId> <ts> 162 Historical Market Data Service error message:API historical data query
cancelled: <reqId>` is IBKR's acknowledgement that a request was **cancelled through the API**, one line
per cancelled reqId. In this app the cancel sites are:

* `MainWindow.load_chart` → `TickerSession._cancel_history_requests()` — every symbol/timeframe/
  extended-hours load, and the same symbol re-loaded (`ui/main_window.py:1709`);
* `_finalize_stranded_history_wave` — a transport drop (`ui/main_window.py:1581`) or the wave watchdog
  (`:1645`).

Evidence that the reported nine lines are the reload path: the warning immediately **before** them
(`Aggregator priming pacing-limited…`, logged only from `prime_aggregator`, i.e. from `load_chart`) shows
a load was in flight, and `_cancel_history_requests` iterates `_history_req_ids`, so the storm's length
equals the number of requests outstanding at that instant — nine here, which is what a 1/s wave looks
like when each 1-D request takes several seconds to answer. They arrive ~100 ms apart because TWS
answers the cancels in sequence.

This is also why the app looks like it is being "limited": the log is loudest precisely at the moment the
user retries. It is not an entitlement error; IBKR's permission denials read differently
(`No market data permissions for …`, error 10197/354), and the same symbol's 5-min history is current.

**IBKR's real limits** (`interactivebrokers.github.io/tws-api/historical_limitations.html`, fetched
2026-10-27) are worth stating because they bound any fix:

* **max 50 simultaneous open historical requests** — "it will probably be more efficient to have a much
  smaller number of requests pending at a time";
* the pacing caps (identical requests within 15 s; 6+ for the same contract/exchange/tick type within
  2 s; 60 per 10 min) apply to bars of **30 s or less**; for `1 min` and larger they are *lifted*, with a
  **soft throttle** that leads to "throttling and eventual disconnect" if you ask for too much too fast.

So a 42-request 1-min burst is legal on paper and still exactly the shape that gets throttled — and the
app piles a second wave on top of it on every retry.

## 5. The "Aggregator priming pacing-limited" warning is a real, separate race

The wave and the aggregator prime share one global 1-second interval gate
(`HISTORICAL_MIN_INTERVAL_S`, `ibkr/pacing.py:106-146`). `load_chart` issues the wave's first chunk
(`ui/main_window.py:1791`) and then primes (`:1815`), so the prime is *guaranteed* to find the gate
closed while a 42-chunk wave is being spaced one per second. The one allowed retry fires at ≈1.05 s,
racing the wave's own continuation timer at ≈1.05 s; if the wave wins, the retry takes the
`retrying=True` branch, returns False and `_fail_open_prime()` attaches the live feed unprimed
(`ui/ticker_session.py:1131-1136`, `1167-1206`). Consequence: on a cold 1-min load the forming candle is
built from ticks only (D27.9 not met), and the user sees the warning on every load.

## 6. A latent second defect: the wave watchdog is shorter than a legitimate deferral

`_schedule_wave_continuation` re-arms the watchdog at a fixed 120 s
(`ui/ticker_session.py:144`, `933-948`) while the continuation timer may legitimately be scheduled for
up to `MAX_HISTORICAL_PER_600S`'s window — up to ~600 s when the budget gate binds. When that happens
the watchdog fires first, `_finalize_stranded_history_wave` cancels every in-flight request (another 162
storm) and finalises a wave that was merely waiting, while `_wave_plan_queue` and the pending
continuation timer survive — so the wave both strands and later resurrects into a second finalise.

---

## Root-cause classification

| what | classification | owner |
|---|---|---|
| 1-min catch-up cannot complete → cache frozen at 10/15 | `code_bug` (incremental persistence absent; reload discards progress) | BUILD |
| 162 storm = our own mass cancel + budget not refunded | `code_bug` | BUILD |
| watchdog 120 s < max continuation wait | `code_bug` | BUILD |
| prime races the wave for the single interval gate | `code_bug` | BUILD |
| "one load may consume ≤N% of the budget; the depth floor is filled across loads" is not stated anywhere | `bad_architecture_decision` (the 30-session floor × 1-D chunks cannot fit the 50/600 s budget for 1-min bars) | PLAN |

## Reproduction (no TWS needed)

* plan counts: `find_missing_spans(<cached ts>, now, "1 min", ext_hours=True, min_sessions=30)` →
  `plan_requests(...)` against the production cache copy;
* wave cadence: `TickerSession.queue_wave_plans(plans, contract, "1 min", True)` with a fake
  `md_manager` that enforces `pacing_manager.historical_wait_seconds()` and records the wall clock —
  42 issues in 43.1 s, completion at 44.7 s, `42/50` slots spent;
* budget cliff: seed 9 slots, then compute the free count — 41 free vs 42 needed, oldest slot expires
  in 590 s.

No test asserts any of this: `tests/test_backfill_progress.py` pins "N plans issue N requests" but not
*how many* plans a 1-min load produces, and nothing pins "an interrupted wave must not lose fetched
bars" or "a reload must not spend the budget twice".
