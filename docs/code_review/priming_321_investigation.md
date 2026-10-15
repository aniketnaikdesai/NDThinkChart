# Investigation — TWS error 321 on the "Aggregator priming" request (reqId 144)

**Reviewer:** Code Reviewer agent (identity/role: diagnose from source, never fix code).
**Scope:** read-only investigation. **This file is the only artifact written.**
`docs/code_review/escalations.json` and `docs/code_review/review_log.md` were **NOT** modified —
a parallel Code Reviewer session is writing `docs/code_review/rth_single_day_investigation.md`
concurrently, so both are left untouched by me.

**Verbatim report:**

```
ERROR 144 1792087208364 321 Error validating request.-'ReqHistoricalData(20)' : cause - Historical data requested duration is invalid.
Aggregator priming request 144 failed [321]: Error validating request.-'ReqHistoricalData(20)' : cause - Historical data requested duration is invalid.
```

---

## 1. Verdict (one line)

The D27.9 aggregator-priming request fetches **`"5 secs"` bars** and builds its duration as
`f"{prime_s} S"` with `prime_s` capped at **7200** (`ui/ticker_session.py:56,1702,1711-1712`).
IBKR caps the duration for `"5 secs"` bars at **3600 S (1 hour)**. On the **4-hour and 1-day
timeframes** the code therefore emits **`duration="7200 S"`** with **`bar_size="5 secs"`**, which TWS
rejects with error **321 — "Historical data requested duration is invalid."** The request is the
*priming* request and nothing else in the codebase requests 5-second bars.

---

## 2. The priming request — exact arguments (proved)

Path: `ui/main_window.py:1853 load_chart` → `ui/ticker_session.py:1684 prime_aggregator` →
`ibkr/market_data.py:20 req_historical_data` → `client.reqHistoricalData(...)`.

Constructed at `ui/ticker_session.py:1703-1713`:

| Argument | Value | Where |
|---|---|---|
| `contract` | the charted contract | `:1704` |
| `timeframe` | the **chart** timeframe (used only to look up the aggregator/period) | `:1705` |
| `endDateTime` | `""` (up to now) | `:1707` |
| `whatToShow` | `"TRADES"` | `:1708` |
| `useRTH` | `1` | `:1709` |
| `extended_hours` | the chart's ext-hours toggle (→ `useRTH=0` when on) | `:1710`; `ibkr/market_data.py:50` |
| **`bar_size`** | **`"5 secs"`** (hardcoded override) | **`:1711`** |
| **`duration`** | **`f"{prime_s} S"`** where `prime_s = min(span_s, 7200)` | **`:1702,1712`** |
| `formatDate` | `2` (unix ts) | `ibkr/market_data.py:59` |

`span_s = now_ts - agg.period_start(now_ts)` (`:1699`), i.e. **seconds elapsed into the chart
timeframe's current candle period**.

**`now_ts` is an int** — `ui/main_window.py:1902-1904 _now_ts()` returns `int(time.time())` — and
`period_start` floors to an int grid (`data/bar_aggregator.py:60-71,101-103`). So the constructed
duration is **always a clean integer seconds string** (never a float, never `None`). I proved this by
exercising the path offscreen (see §4).

---

## 3. Why IBKR rejects it (proved against IBKR's own documentation)

IBKR's "Historical Data Limitations → **Step Sizes**" table (the rule that produces 321) is:

| Duration | Allowed Bar Sizes |
|---|---|
| 60 S | 1 sec – 1 min |
| 120 S | 1 sec – 2 mins |
| 1800 S (30 mins) | 1 sec – 30 mins |
| **3600 S (1 hr)** | **5 secs – 1 hr** |
| 14400 S (4 hr) | 10 secs – 3 hrs |
| 28800 S (8 hr) | 30 secs – 8 hrs |
| 1 D | 1 min – 1 day |
| … | … |

The binding practical rule (operation-tested in the wild — see corroboration below) is: **the longer
the requested duration, the coarser the minimum bar size — and conversely each bar size has a maximum
duration.** The finest bars have the tightest ceiling: **`1 secs` → max 1800 S, `5 secs` → max
3600 S, `10/15 secs` → max 14400 S, `30 secs` → max 28800 S.** `"5 secs"` appears in the table **only**
in the 3600 S row; rows below it (60/120/1800 S) top out at 30-min bars, so 5-sec bars are invalid for
durations *below* 60 S and, decisively, **any duration > 3600 S with `bar_size="5 secs"` is rejected
as an invalid duration (321)**.

Corroboration (external, not authoritative repo evidence — treat as supporting, not proof):
- IBKR "Historical Data Limitations" (Step Sizes) — the table above.
- An independently maintained IBKR client documents the same ceilings verbatim: *"bars of 30 seconds
  or less … allow short durations only (1 secs up to 1800 S, **5 secs up to 3600 S**, 10/15 secs up
  to 14400 S, 30 secs up to 28800 S)"* (ib-gateway-mcp tool docs).
- A third-party TWS client maps `5 secs` → a **`60 S`** seed duration and documents the
  `keepUpToDate` floor at "5 seconds or greater" (stoqey/ib PR #270).

**Exactly which part is invalid:** the **number** (`7200`), not the unit or format — the unit `S` is
valid for 5-sec bars and `"7200 S"` is a well-formed integer-seconds duration. `7200 > 3600` = the
per-bar-size maximum. So the duration **exceeds the per-bar-size maximum** (it is not `None`, not a
float, not a bad unit).

---

## 4. Reproduction of the constructed string (proved, offscreen)

Exercising `BarAggregator.period_start` + the priming cap with `now_ts = int(...)` for a representative
RTH load (2026-10-13 10:30 ET) gives exactly the strings the code would send:

```
now_ts (int): 1791901800 | ET: 2026-10-13T10:30:00-04:00
   1 min   period=    60s  span=     0s  -> duration=      '0 S'
  5 mins   period=   300s  span=     0s  -> duration=      '0 S'
 15 mins   period=   900s  span=     0s  -> duration=      '0 S'
  1 hour   period=  3600s  span=  1800s  -> duration=   '1800 S'   (<= 3600: OK)
 4 hours   period= 14400s  span=  9000s  -> duration=   '7200 S'   (> 3600: INVALID -> 321)
   1 day   period= 86400s  span= 37800s  -> duration=   '7200 S'   (> 3600: INVALID -> 321)
```

(`span=0` rows return `False` at `:1700` — a period boundary needs no priming, so no request is sent.
Intraday timeframes never exceed 3599 s and are unaffected.)

---

## 5. The arithmetic trace (proved)

- `period_s = TIMEFRAME_SECONDS.get(timeframe, 300)` (`:1696`; table at `data/bar_aggregator.py:14-22`).
- `span_s = now_ts - agg.period_start(now_ts)` (`:1699`).
- `prime_s = min(span_s, 7200)` (`:1702`) — **this is the bug's locus**: the cap is set to 2 hours,
  but the request uses a 5-second bar size whose IBKR ceiling is 1 hour.
- `duration = f"{prime_s} S"` (`:1712`) with `bar_size="5 secs"` (`:1711`).

The mismatch is **bar size vs duration bound**: `7200 S` is combined with a bar size (`5 secs`) whose
maximum duration is `3600 S`. The `4 hours` and `1 day` timeframes are the only ones whose period
(14400 s / 86400 s) exceeds the cap, so they are the only ones that reach `7200`. (For `4 hours`, the
failure also fires for spans in `(3600, 7200]`, i.e. any load more than 1 hour into the 4-hour ET
bucket; for `1 day`, any load more than 1 hour into the ET day — i.e. most of RTH.)

---

## 6. What happens on failure (proved)

`ui/main_window.py:_on_error` (`:1650`) routes the error by reqId; the priming reqId is registered on
the session (`ui/ticker_session.py:1724`), so control reaches
`ui/ticker_session.py:1626 on_historical_error`, whose **priming branch** (`:1636-1645`) runs:

1. `_LOG.warning("Aggregator priming request %s failed [%s]: %s", …)` — this produces the second
   reported log line verbatim.
2. `self._prime_req_id = None`; `self._prime_timer.stop()`.
3. **Fail-open**: `self._host._on_session_prime_complete(self)` → `ui/main_window.py:2112-2115` →
   `_attach_live_feed_if_current` → attaches the live feed with an **unprimed** aggregator.

So the failure is **not retried** and does **not** strand the chart — but it **leaves the aggregator
unprimed**, which is precisely the state AC-D27.9 exists to prevent. Visible consequence on the
affected timeframes: the current **forming 4-hour/daily candle's open / high / low / volume reflect
only the live ticks since attach**, not the period's true start. Every 4h/1d load (re)emits the
warning + a status-bar `Error [321]` message, and the D27.9 guarantee is silently unmet for those two
timeframes.

---

## 7. Is 321 classified / routed? (proved)

- `ibkr/error_codes.py:1-22 classify_error(321)` returns **`'warning'`** (321 is in none of the
  info/fatal tuples; verified by running it: `321 -> warning`, `162 -> fatal`). It is consumed in
  `ibkr/client.py:228` only to gate the status-bar/severity log — it does not special-case 321.
- Routing is by **reqId**, not by code: `ui/main_window.py:_on_error` (`:1655-1672`) finds the owning
  session and calls `session.on_historical_error(...)`, which handles the priming reqId specially
  (§6). So 321 here *is* surfaced (warning log + status bar) and *is* actioned (fail-open), but the
  error code itself is unclassified — a generic `warning`, no dedicated handling.

---

## 8. Correct behaviour vs requirements/architecture (gap found)

- **Requirement D27.9** (`docs/requirements/requirements.md:2867-2868`): *"on chart load the
  aggregator **SHALL** be primed with trailing 5-second history before the live feed attaches, so the
  forming candle's OHLCV is not fabricated."* **AC-D27.9** (`:2888-2889`): *"Given a fresh chart load
  mid-period, Then the forming candle's open/volume reflect the primed 5-sec history…"*
- **Architecture** (`docs/architecture.md:2704`): *"D27.9: aggregator priming — trailing 5-sec
  history (**bounded 7200s**) …"*.
- Neither document specifies the **duration policy** for the 5-sec request, nor the IBKR per-bar-size
  ceiling, nor what to do for timeframes whose period exceeds the 5-sec ceiling. The `7200` bound is
  recorded as a **coder judgment** (`docs/phase-changelog.md:96`, commit `69a2313`).

So: **the code does not match IBKR's constraint (code bug), and the requirements are silent on the
duration policy (requirements gap).** Note also that even at a legal `3600 S`, 5-second bars can only
reach back 1 hour — they **cannot** reconstruct the full forming candle for the 4h (14400 s) or daily
(86400 s) periods. The priming *strategy* for 4h/1d is therefore unsound as specified (the
`docs/phase-changelog.md:100` follow-up "4h/daily forming-candle exactness under the 2h priming bound:
seed from the historical partial bar instead" already anticipated the intent problem, but did not
anticipate the outright 321 rejection).

---

## 9. Root cause — proved vs inferred

**Proved (from repo source + IBKR docs + offscreen reproduction):**
- The failing request is the D27.9 priming request: `bar_size="5 secs"`, `duration=f"{min(span_s,7200)} S"`
  (`ui/ticker_session.py:1702,1711-1712`; `ibkr/market_data.py:20-65`).
- `now_ts`/`prime_s` are ints, so the string is a clean integer like `"7200 S"` — not a float/`None`.
- For the `4 hours` and `1 day` timeframes the string is exactly `"7200 S"`; `7200 > 3600`, and IBKR's
  step-size rule caps `"5 secs"` durations at `3600 S` → error 321.
- On failure the handler fails open and leaves the aggregator unprimed, logging the reported line at
  `ui/ticker_session.py:1637-1639`.
- Only the priming path uses 5-sec bars (grep: `ui/ticker_session.py:1711` is the sole production
  `"5 secs"` request; `ibkr/market_data.py:38` is the docstring). Nothing else can produce this 321.

**Inferred (high confidence, not directly observed on live TWS by me):**
- The specific live session was on the **4-hour or 1-day** timeframe (consistent with "the chart showed
  only the current day"). `"7200 S"` with 5-sec bars is the only combination in the tree that yields
  a 321 on a priming request.
- IBKR's exact ceiling is `3600 S` for 5-sec bars per the step-size table; I did not have live TWS to
  observe the boundary, but the table, the two independent client implementations, and the app's own
  rejection all agree.

---

## 10. Regression? severity

- **Regression:** **No** — it is a *latent defect in the D27.9 feature since it was introduced*
  (Phase 2.9, commits `96de327` + `69a2313`; the `7200` bound is `69a2313` "bound the trailing priming
  fetch at 7200s"; moved into `TickerSession` by `1a27afd6`/3b-2). Before D27.9 no priming request
  existed, so nothing previously worked and broke. It has simply never been valid for 4h/1d.
- **Severity:** **should-fix** (I'd argue *blocking for the priming feature on 4h/1d specifically*,
  but not blocking for the pipeline/app). The app stays usable and no historical data is lost — the
  backfill wave is untouched and priming is fail-open — but AC-D27.9 is silently unmet on the two
  coarsest timeframes and every such load emits a 321 warning.

---

## 11. Does this explain the parallel "only current session populates under RTH" symptom?

**No — not directly, and I could not link them.** Reasons:

- The 321 is confined to the **priming** request (5-sec bars). The priming failure is **fail-open**
  (`ui/ticker_session.py:1643-1644`) and does **not** touch `_history_req_ids`/`_wave_plan_queue`, so
  the historical backfill wave is unaffected by it.
- The backfill planner (`services/backfill_service.py:299-333 plan_requests`) builds every request
  from `TIMEFRAME_CONFIG` (`ibkr/market_data.py:7-14`), whose bar sizes are `1 min … 1 day` — **never
  `5 secs`** and **never a seconds duration** — so the backfill cannot produce a 321.
- Therefore a priming 321 cannot, by itself, hide prior sessions/days.

**But** the two symptoms share the *same suspect surface* — **a history request whose
duration/bar-size combination is not validated against IBKR's step-size rules** — and both are in the
history-request path. Concrete leads for the RTH investigation (mine to hand over, theirs to prove):
`services/backfill_service.py:113-124 _duration_to_seconds` / `_format_end_date:127-133`, the
empty-cache single-plan path (`ui/main_window.py:1820-1835`, which fetches only the *configured*
window — for a 1-min chart that is `"1 D"` = essentially "today only"), and the RTH session-window
handling in `find_missing_spans` (`services/backfill_service.py:169-209`, `ext_hours`). **If the RTH
symptom also turns out to be a duration that doesn't fit its bar size, these are the same class of
defect; if it is the `"1 D"` empty-cache plan, it is a different one.** I state this explicitly rather
than claim a shared root cause.

---

## 12. Owner / route and proposed escalation id

- **Primary finding → `BUILD`** — pure code bug: the priming duration bound (`7200`) exceeds IBKR's
  per-bar-size maximum (`3600 S`) for the hardcoded `"5 secs"` bar size. Fix is inside the priming
  code (change the bound and/or the bar size), no architectural change required.
- **Secondary finding → `REQUIREMENTS`** — the duration policy for D27.9 is unspecified, and the
  requirement's intent (prime the forming candle) is **unachievable with 5-sec bars for the 4h/1d
  periods** (5-sec bars reach back only 1 hour; a 4h/1d period is 14400/86400 s). Whether 4h/1d should
  prime with a coarser bar size (e.g. `1 min`, valid up to `1 D`) or seed from the historical partial
  bar is a requirements decision, not a code one.

**Proposed id: `ESC-036`.** ⚠️ **Possible collision:** the concurrently-running RTH review is likely to
claim the next free id, `ESC-035` (current maximum in `escalations.json` is `ESC-034`). There is a race
on **both** `ESC-035` and `ESC-036`. I did not write the entry, so the Orchestrator/user must reconcile:
reserve `ESC-035` for the RTH review and `ESC-036` for this one, or renumber whichever lands second.
The proposed entry (for a writer to merge — **not** written by me):

```json
{
  "id": "ESC-036",
  "task_id": "D27-09",
  "routed_to": "BUILD",
  "category": "bug",
  "severity": "should-fix",
  "observed": "D27.9 aggregator priming (ui/ticker_session.py:1684-1728) hardcodes bar_size='5 secs' (:1711) and builds duration=f'{prime_s} S' with prime_s=min(span_s, _PRIME_MAX_SPAN_S) where _PRIME_MAX_SPAN_S=7200 (:56,1702). IBKR caps the duration for '5 secs' bars at 3600 S (Historical Data Limitations -> Step Sizes; '5 secs' appears only in the 3600 S row; two independent clients document '5 secs up to 3600 S'). For the '4 hours' and '1 day' timeframes span_s exceeds 7200, so the request is exactly duration='7200 S', bar_size='5 secs' -> TWS error 321 'Historical data requested duration is invalid' (verbatim log: 'Aggregator priming request 144 failed [321]'). Reproduced offscreen with now_ts=int(time.time()): 4h/1d -> '7200 S'; 1h -> '1800 S'; all 5-sec requests this loudest on 4h/1d. On failure on_historical_error (:1636-1645) fails open, leaving the aggregator UNPRIMED -> the forming 4h/daily candle's OHLCV is built only from live ticks (AC-D27.9 unmet on those timeframes) and every load emits the warning.",
  "expected": "The priming request must be a (durationStr, barSizeSetting) combination IBKR accepts: for bar_size='5 secs' the duration must be <= 3600 S (and >= 60 S). Equivalently, AC-D27.9 ('forming candle reflect primed history') must be met on every timeframe the user can select, including 4h/1d.",
  "suggested_direction": "Immediate (within the priming code): clamp the 5-sec priming span to IBKR's 3600 S ceiling, e.g. _PRIME_MAX_SPAN_S hard-capped at 3600 for bar_size='5 secs' (and note the >=60 S floor). But note the deeper mismatch: 5-sec bars cannot cover a 4h (14400 s) or daily (86400 s) forming period at all, so for those timeframes consider priming with a coarser bar size (e.g. '1 min', valid up to '1 D') or seeding from the historical partial bar — that choice is a requirements decision (see the separate REQUIREMENTS finding). Update tests/test_d27_aggregator_priming.py:177 which currently ASSERTS duration == '7200 S' (it enshrines the bug; correct, do not merely weaken).",
  "status": "open",
  "opened": "<UTC ISO8601 at write time>"
}
```

(And the companion requirements gap, for a writer to merge as its own entry: `routed_to:
"REQUIREMENTS"`, `task_id: "D27-09"`, `category: "gap"`, `severity: "should-fix"` — D27.9/AC-D27.9
specify the duration policy only as 'trailing 5-second history' with no ceiling and no rule for periods
longer than a 5-sec request can reach, so the 4h/1d priming intent is unspecified.)

---

## 13. Warranted regression test, and why the suite misses it

**Test (I write none — this is what a fix should assert):**
- Drive the priming path on a **`"1 day"`** (and `"4 hours"`) timeframe mid-period (extend
  `tests/test_d27_aggregator_priming.py::test_d27_9_prime_span_bounded`), and assert the issued
  priming request's duration **parses to ≤ 3600** when `bar_size == "5 secs"`. Prefer asserting the
  **invariant** — *for every 5-sec priming request, `duration_seconds <= 3600`* — rather than the
  literal `"7200 S"` the current test pins.
- Ideally add a small pure helper (e.g. `max_prime_span_s(bar_size)`) and unit-test the mapping
  `{"5 secs": 3600, …}` so the fix is guarded at the rule level, and assert the constructed
  `(duration, bar_size)` pair is in IBKR's allowed set for `1 min`/`5 mins`/`1 hour`/`4 hours`/`1 day`.
- Because the priming failure is fail-open, the test must assert on the **request arguments**
  (`duration`, `bar_size` recorded by the mocked `md_manager`), not on chart state.

**Why the suite misses it today:**
- Every priming test monkeypatches `md_manager.req_historical_data` with `fake_req_hist` that just
  records kwargs and returns an id (`tests/test_d27_aggregator_priming.py:46-50,130-134,158-162`). No
  test enforces IBKR's step-size rules, and there is no live TWS in the suite — a green suite says
  nothing about whether TWS will accept the arguments.
- Worse, `test_d27_9_prime_span_bounded` (`:151-177`) explicitly asserts `duration == "7200 S"`, i.e.
  **the test encodes the invalid value as expected** — so the suite is not merely blind, it *locks in*
  the bug and must be corrected with the fix.

**Broader test-hardening note:** all three currently-open escalations (ESC-032/033/034) and this one
are defects on paths the large offscreen suite never exercises against reality (live TWS validation,
real signal wiring, real C++ lifetimes). Candidate memory note for the Orchestrator: *"a green
offscreen suite does not validate request arguments against IBKR's server-side rules or real signal/
lifetime behaviour."*

---

## 14. Confirmation

- I wrote **only** `docs/code_review/priming_321_investigation.md`.
- I did **not** touch `docs/code_review/escalations.json` or `docs/code_review/review_log.md` (nor any
  code, requirements, plan, architecture, task, or build file), per the concurrency rule — the parallel
  RTH review owns `.json`/`.md` writes for this pass.
- No test was written; the warranted test is specified in §13 for the owning agent.
