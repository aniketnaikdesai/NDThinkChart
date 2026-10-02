# Architecture Proposal — NDThinkChart D16 (historical-bar gap backfill)

> **Status: DRAFT for Plan Artifact Editor & Validator. Not canonical.**
> **Revision 2 (2026-10-02) — ESC-023 correction increment.** The D16 batch (T37–T41, all
> done) is now **built**; this revision folds in the corrected D16 trading-day calendar
> behaviour (`AC-D16.7`, A33, R27, DG22 — NYSE Rule 7.2 year-end accounting exception: Dec 31
> stays a trading day when the next Jan 1 is a Saturday) and marks the rest of D16 as
> `[existing]`/unchanged. It does **not** re-plan D1–D15 or any other part of D16.
> This is an **incremental** proposal on top of the **as-built** system described in
> `docs/architecture.md` (D1–D15 built, 383 passed, verified 2026-09-28; D16 T37–T41 built).
> Existing-repo mode: every item is labelled `[existing]`, `[new]`, or `[new/changed]`.

## Codebase Summary

> Factual inventory gathered with the **graphify** skill (`graphify-out/graph.json`,
> 1969 nodes) and then **validated against the current source files** (the repository is
> authoritative; the graph is dated 2026-09-28). Only the parts D16 touches are listed.
>
> **Graphify staleness (D16 increment).** Re-running `graphify query` for `market_calendar` /
> backfill returns only unrelated `calendar` / `_last_trading_day` nodes — the graph predates
> the D16 modules and contains **no `market_calendar` or `backfill_service` node**. Per the
> existing-repo rule, the D16 sections below were therefore inventoried by **direct source
> inspection** of the current tree, not from the graph.

### Existing bar-load path (the D16 surface)
`[existing] ui/main_window.py::MainWindow.load_chart` — the whole path:

1. `load_chart()` (lines 389–456) cancels the previous RT subscription, sets
   `_current_symbol`/`_current_tf`, calls `ChartPanel.set_symbol/set_timeframe/
   set_extended_hours`, reloads drawings/studies/alarms.
2. Step 1 (lines 421–428): `BarCache.get_bars(symbol, timeframe)` → show cached bars
   immediately via `chart_panel.update_chart(cached)`.
3. Step 2 (lines 430–444): `end_dt = ""` and **one** `MarketDataManager.req_historical_data(
   contract, timeframe, endDateTime="", whatToShow="TRADES", useRTH=1, extended_hours=…)`
   → stored as the single `self._current_req_id`.
4. Step 3 (line 447): start the RT bar stream.
5. `_on_historical_bar(reqId, bar)` (lines 566–579): filters `reqId != self._current_req_id`,
   parses `ainbr.utils.parse_ibkr_date`, appends a `Bar` to `self._pending_bars`.
6. `_on_historical_data_end(reqId)` (lines 581–592): filters the single reqId,
   `BarCache.save_bars(self._pending_bars)`, re-reads **all** cached bars with
   `BarCache.get_bars`, and calls `chart_panel.update_chart(all_bars)`.
7. `closeEvent` (lines 1132–1148): cancels `_current_req_id` only.

`[existing] ibkr/market_data.py` — `TIMEFRAME_CONFIG` (lines 7–14) is a fixed
`duration`/`bar_size` per timeframe: `1 min`→`1 D`, `5 mins`→`5 D`, `15 mins`→`5 D`,
`1 hour`→`10 D`, `4 hours`→`30 D`, `1 day`→`1 Y`. `req_historical_data()` (lines 20–54)
**already accepts an `endDateTime`** and already calls `id_manager.get_id()` +
`pacing_manager.throttle()` per request. It has **no** caller besides `load_chart`
(graphify degree 3).

`[existing] ibkr/client.py` — `historicalData` (line 160) emits `bridge.historical_bar`;
`historicalDataEnd` (line 164) emits `bridge.historical_data_end`.

`[existing] ibkr/bridge.py` — `historical_bar = pyqtSignal(int, object)`,
`historical_data_end = pyqtSignal(int)`, `error_msg = pyqtSignal(int, int, str)`.

`[existing] data/bar_cache.py` — `save_bars` (`INSERT OR REPLACE`, PK
`(symbol,timeframe,ts)`, lines 6–18), `get_bars` (all cached, ascending, lines 20–30),
`get_last_timestamp` (`MAX(ts)`, lines 32–41; **present but unused by `load_chart`** —
the DG21 observation).

`[existing] data/bar_aggregator.py` — `TIMEFRAME_SECONDS` map (lines 6–14) already gives
the per-bar period in seconds for every timeframe.

`[existing] ui/main_window.py::_ibkr_end_date` (lines 69–76) — formats a unix ts as the
IBKR `yyyyMMdd-HH:mm:ss` **UTC hyphenated** `endDateTime`. It exists but currently has
**no caller**; it is exactly the chunk-anchor formatter D16 needs.

`[existing] services/session_service.py` — pure, Qt-free ET (`ZoneInfo("America/New_York")`)
session math (`session_bands`, `session_bands_for_range`). Before D16 there was no
trading-day/holiday logic anywhere in the repo; D16 then added the separate hidden-market
calendar module inventoried in the **D16 as-built modules** subsection below.

`[existing] ui/chart_panel.py` — `update_chart` sets `self._bars`; `_refresh_candles`
(lines 802+) builds **both** the candle data and the volume `BarGraphItem` from the same
`self._bars` list. So a continuous `_bars` list fixes candles **and** volume (AC-D16.2)
with no chart-panel change.

### D16 as-built modules (T37–T41 built) `[existing]`
`[existing] services/market_calendar.py` — pure, Qt-free ET trading-day/holiday calendar
(`is_trading_day`, `trading_days`, `session_windows`); holidays computed **by rule**.
**As-built behaviour:** `_observed(fixed)` (`:82–92`) shifts a Saturday fixed-date holiday to
the preceding Friday and a Sunday one to the following Monday, and `_holidays_for_year` (`:102`)
applies it to New Year's Day (`:112`) **without** the year-end exception — so
`is_trading_day(date(2021, 12, 31))` is currently `False` (and likewise `2027-12-31`,
`2032-12-31`, `2038-12-31`), while the 2022 holiday set contains `2021-12-31`. This is the
**ESC-023 / DG22 defect**; the correction is specified in the Tech Stack Decisions and System
Components below and in `AC-D16.7`.

`[existing] services/backfill_service.py` — pure, Qt-free planner
(`bar_period_seconds`, `find_missing_spans`, `plan_requests`), as recorded in
`docs/architecture.md`.

`[existing] ui/main_window.py` D16 orchestration (`_history_req_ids`, `_history_generation`,
finalise-on-empty, shortfall surface) — built under T39; **unchanged** by this correction.

`[existing] tests/test_market_calendar.py` — the D16 calendar test. **As-built:** T37-T03
asserts `is_trading_day(date(2021, 12, 31)) is False` (`:112–114`) and includes `2021-12-31` in
the "weekend legal dates are non-trading" loop (`:116`). Both encode the wrong convention and
are corrected under this increment.

### Data models / tables `[existing]`
`Bar` (symbol, timeframe, ts, open, high, low, close, volume). SQLite table `bars`
with `PRIMARY KEY (symbol, timeframe, ts)` (dev/single-process DB resolved by
`config/paths.get_db_path()`). No schema migration is needed.

### Major components & integrations `[existing]`
`config/`, `data/`, `services/` (pure), `ibkr/` (client/bridge/market_data/pacing/
id_manager/contracts/realtime_bars/utils), `ui/` (main_window, chart_panel, …). External
integrations in play: IBKR historical/RT data, SQLite, Qt signals, `pacing_manager`,
`id_manager`. **No new external integration is introduced by D16.**

### Relevant tests `[existing]`
`tests/test_watchlist_d14_midrag.py` already boots a real offscreen `MainWindow` with
`IBApiClient.connect` monkeypatched and `md_manager.req_historical_data`/
`rt_manager.subscribe` stubbed — the established pattern for a D16 integration test.
No test currently drives the historical load/backfill path.

---

## Summary
D16 is fixed by **planning and issuing a chunked set of historical requests** that cover
every cached trading day missing between the oldest cached bar and *now*, instead of one
request anchored to now with a fixed window. Two **new pure services** decide *what* to
fetch — a small ET trading calendar and a missing-span/backfill planner — and
`MainWindow` orchestrates multiple correlated requests (accumulating `_pending_bars`,
tracking a reqId set + generation, finalising with one save + re-read + render). The
chart-render path and the `bars` schema are **unchanged**: once `_bars` is continuous,
both the price and volume panels are correct (AC-D16.2). Genuine closures (weekend,
holiday, overnight) are non-trading intervals in the calendar, so they stay empty and are
never fabricated or compressed (AC-D16.3).

## Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI / broker / DB / tests | **Unchanged**: Python 3.11+, PyQt6, pyqtgraph, official `ibapi`, SQLite, pytest+pytest-qt offscreen | Existing-repo hard constraint; changing the stack is a stated non-goal | New deps (e.g. `pandas_market_calendars`) — rejected as a stack addition |
| Where backfill *planning* lives | **`[new] services/backfill_service.py`** — pure, Qt-free, importable | Matches the repo's pure-service pattern (`session_service`, `indicator_service`); unit-testable offscreen without Tk/TWS; keeps `MainWindow` as orchestration only | Inline in `load_chart` (untestable, duplicates logic); inside `MarketDataManager` (mixes transport with planning, needs `ibapi` Contract); inside `BarCache` (data layer must not know fetch windows) |
| Trading-day/holiday awareness | **`[existing] services/market_calendar.py`** — ET weekday + US equity holidays computed **by rule** (nth-weekday, Good Friday, fixed-date), no external dependency. `[new/changed]` for this increment: the New Year's observed-day shift carries the **NYSE Rule 7.2 year-end accounting exception** (`AC-D16.7`) — when Jan 1 is Saturday, **no New Year's closure is observed and Dec 31 stays a trading day** | Required by **AC-D16.3** (holidays are genuine closures), **AC-D16.1/16.5** (only *trading-session* bars required) and **AC-D16.7** (Dec 31 of a Jan-1-Saturday year is a trading day, never a closure); by-rule avoids a dead fixed year list | Weekday-only (flags every US holiday as a hole — violates AC-D16.3); no calendar + "empty response = closure" (cannot distinguish a real shortfall from a holiday without error codes; weaker AC-D16.4); `pandas_market_calendars` — **rejected** (new dependency, and `A7` already accepted a hand-rolled ET model); changing the **generic** `_observed` for all holidays instead of a New Year's-specific rule (would scramble the still-correct Independence Day/Christmas/Juneteenth shifts) — **rejected** |
| Missing-span detection granularity | **Session/day presence**: a trading day between `min(cached_ts)` and `now` with **zero** cached bars is missing; adjacent missing trading days merge into one span; the tail (`last cached day`→`now`) is the same rule | The reported defect is **whole missing sessions** (DG21, AC-D16.5); day presence avoids false positives from illiquid periods and from toggling Ext Hours (RTH-only cache still has bars that day). AC-D16.1's precondition is a closure **exceeding the fetch window**, i.e. a multi-session hole | Per-period cadence (illiquid symbols / empty pre-market periods would look like holes → churn + false shortfall); fetch-window threshold (fails for `1 day`, where the window is `1 Y`, so a 9-day hole would not be flagged); `MAX(ts)` tail-only anchor (**explicitly rejected by DG21** — leaves the reported internal hole) |
| Anchoring & chunking | **Reuse `MarketDataManager.req_historical_data(endDateTime=…)` unchanged**, stepping `endDateTime` back by the existing `TIMEFRAME_CONFIG[timeframe]["duration"]` until the span start is covered; format anchors with the existing `_ibkr_end_date(ts)` | The method already accepts `endDateTime` and already throttles + allocates a reqId; the configured duration is the natural chunk size; no new IBKR call shape and no signature change | Enlarging `duration` (may exceed IBKR's per-request limits and still be a single request; AC-D16.4 wants chunking); adding a `duration` parameter (unnecessary) |
| Multi-request correlation | **`[new/changed] ui/main_window.py`** keeps `_current_req_id` as the primary id and adds `_history_req_ids: set[int]` + a load-generation token; bars are accepted from any id in the set; finalisation (save + re-read + render) fires only when the set empties | Preserves the existing single-request behaviour as "set of one" (no D1–D15 regression); one write + one render per load avoids flicker; generation token + cancel prevents cross-contamination on symbol/timeframe switch (AC edge case) | Per-chunk save/render (multiple re-reads + flicker); a dedicated controller class (more surface for little gain; fewer async edges in `MainWindow`) |
| `now` reference | `now_ts = int(time.time())` at load time, passed **into** the pure planner as a parameter (a thin `_now_ts()` seam in `MainWindow`) | Pure planner stays deterministic and testable with a fixed `now`; matches the ACs which pin "now" | `datetime.now()` read inside the service (untestable) |
| Chart render path | **`[existing] ui/chart_panel.py` unchanged** | `_refresh_candles` already drives candles **and** volume from the same `_bars` (AC-D16.2); closures are empty x-intervals because plotting is timestamp-based (AC-D16.3) | Separate volume backfill (would duplicate the bar list — rejected) |
| Persistence | **No schema change**; chunk overlap deduped by `INSERT OR REPLACE` on the existing `(symbol,timeframe,ts)` PK | The `bars` table already keys by symbol/timeframe/ts, so overlapping chunks are idempotent | New `spans`/job table (unneeded) |
| Shortfall surfacing | Status-bar message + log line; trigger = an IBKR `error_msg` for a backfill reqId, or a trading day still empty after all requests complete | Required by **AC-D16.4** ("surfaced explicitly … never a silent hole"); never fabricates a bar | Silent acceptance of empty chunks (violates AC-D16.4) |

## System Components

### Existing layers (unchanged)
- `[existing] config/` — `settings`, `paths` (DB path), `theme.qss`.
- `[existing] data/` — `models`, `db`, `bar_cache`, `bar_aggregator`, `alarm_store`,
  `drawing_store`, `study_store`.
- `[existing] services/` — `session_service`, `indicator_service`, `gap_vix_service`,
  `ict_service`, `drawing_service`, `alarm_service`, `sound_service`,
  `strategy_detection`.
- `[existing] ibkr/` — `client`, `bridge`, `id_manager`, `pacing`, `contracts`,
  `market_data`, `realtime_bars`, `market_depth`, `order_book`, `orders`, `account`,
  `subscription_manager`, `utils`.
- `[existing] ui/` — `main_window`, `chart_panel`, `candlestick_item`,
  `chart_mouse_router`, `drawing_overlay`, `alarm_overlay`, `watchlist_panel`,
  `overlays/*`, dialogs.

### New / changed for D16
> **Increment note (ESC-023):** every D16 component below except the corrected
> `services/market_calendar.py` New Year's rule is **already built** (T37–T41) and is
> **unchanged** by this pass. `[new]` remains the original-D16 label; for this correction
> increment, `backfill_service` / `main_window` / `chart_panel` / `bar_cache` are `[existing]`.
- **`[existing] services/market_calendar.py`** (built T37) — pure, Qt-free ET calendar:
  `is_trading_day(date)`, `trading_days(start_ts, end_ts)`, and
  `session_windows(start_ts, end_ts, ext_hours)` (intraday `04:00–20:00 ET` on trading
  days; one window per trading day for `1 day`). Holidays computed by rule (fixed-date
  + nth-weekday + Good Friday) so future years need no data edit.
- **`[new/changed] services/market_calendar.py` — ESC-023 correction (`AC-D16.7`).** The
  New Year's observed shift gains an explicit **year-end accounting-period exception**: a
  New Year's-specific observed-day rule (applied only to the Jan 1 fixed date) returns **no
  closure** when Jan 1 is a Saturday — so no date is shifted onto Dec 31, Dec 31 stays a
  trading day, and **no substitute closure is created** (Jan 1 itself is a weekend and remains
  non-trading). Jan 1 on a Sunday still observes the following Monday; a weekday Jan 1 stays a
  closure; `_observed` for Juneteenth / Independence Day / Christmas is **unchanged**, and the
  remaining observed-shift assertions stay as regression guards. `_holidays_for_year`'s
  adjacent-year union is retained as a defensive guard, with its stale "New Year's observed on
  the preceding Dec 31" docstring/comment corrected.
- **`[new] services/backfill_service.py`** — pure, Qt-free planner:
  - `bar_period_seconds(timeframe)` (from `data.bar_aggregator.TIMEFRAME_SECONDS`).
  - `find_missing_spans(cached_ts, now_ts, timeframe) -> list[MissingSpan]` (trading-day
    presence → merged spans; empty cache → `[]` and the caller falls back to the
    configured window).
  - `plan_requests(missing_spans, timeframe) -> list[RequestPlan]` (each plan =
    `{endDateTime, bar_size, duration}` using `TIMEFRAME_CONFIG` + `_ibkr_end_date`
    formatting; ordered newest chunk first; chunk count bounded by the span).
  - In-memory dataclasses only (`MissingSpan`, `RequestPlan`); nothing persisted.
- **`[new/changed] ui/main_window.py`** —
  - `load_chart`: after showing cached bars, call the pure planner; if the plan is empty
    and the cache is current, skip redundant history requests (else issue the chunk set
    via `req_historical_data(endDateTime=…)`).
  - `_on_historical_bar` / `_on_historical_data_end`: accept any reqId in
    `_history_req_ids`; finalise (save + re-read + render) only when the set empties;
    drop stale generation.
  - `_on_error`: correlate a backfill reqId failure with its span for AC-D16.4.
  - `closeEvent` + symbol/timeframe switch: cancel every id in `_history_req_ids`.
  - New state: `_history_req_ids: set[int]`, `_history_generation: int`,
    `_backfill_missing_spans`, `_backfill_failed_req_ids`.
- **`[existing] ibkr/market_data.py` — no change required.** Chunking reuses
  `endDateTime` + the configured duration; `pacing_manager.throttle()` and
  `id_manager.get_id()` are already applied per request.
- **`[existing] data/bar_cache.py`** — reused as-is (`get_bars`/`save_bars`);
  `get_last_timestamp` remains available but is not required.
- **`[existing] ui/chart_panel.py`** — unchanged.

### Component relationships
`MainWindow.load_chart` calls `services.backfill_service.find_missing_spans` +
`plan_requests` (pure), then issues one `MarketDataManager.req_historical_data` per
`RequestPlan`. `IBBridge.historical_bar`/`historical_data_end` feed `MainWindow`, which
accumulates `Bar` objects, saves once via `BarCache.save_bars`, re-reads with
`BarCache.get_bars`, and calls `ChartPanel.update_chart`; `ChartPanel._refresh_candles`
drives both candles and volume. `services.market_calendar` is consumed only by
`backfill_service` (via `find_missing_spans`).

## Data Model
- **`[existing]`** `Bar` and the `bars` table (`symbol, timeframe, ts, open, high, low,
  close, volume`; PK `(symbol, timeframe, ts)`). **No new/changed entity or column.**
- **`[new]`** in-memory value types in `services/backfill_service.py`
  (`MissingSpan {start_ts, end_ts}`, `RequestPlan {endDateTime, duration, bar_size,
  span_start_ts, span_end_ts}`). Not persisted.
- **`[new/changed]`** ephemeral `MainWindow` runtime state: `_history_req_ids`,
  `_history_generation`, `_backfill_missing_spans`, `_backfill_failed_req_ids` (the
  existing `_pending_bars` retains its role, now shared across the chunk set).

## Integration Points
- **`[existing]` IBKR historical data** (`IBApiClient.historicalData` →
  `IBBridge.historical_bar`/`historical_data_end`) — now invoked **one request per chunk**
  instead of one per load. Same call shape and same `whatToShow`/`useRTH`; pacing via the
  existing `pacing_manager.throttle()`; reqIds via `id_manager`.
- **`[existing]` IBKR error stream** (`IBBridge.error_msg`) — correlated to backfill
  reqIds for AC-D16.4 shortfall surfacing.
- **`[existing]` SQLite `BarCache`** — `get_bars` / `save_bars` only; PK dedupes chunk
  overlap.
- **`[existing]` Qt signal bus / status bar** — one status-bar message on completion and
  on a surfaced shortfall.
- **`[new]` none.** No new external service, no new dependency, no new IBKR request type.

## Non-Functional Approach
- **Correctness (continuity, D16/AC-D16.1):** the planner's outcome is "every trading day
  between the oldest displayed bar and *now* has cached bars"; a tail gap is the special
  case where missing days run to the end. DG21's internal hole (newer block cached, older
  block separated by a hole) is healed because detection is on trading-day presence, not
  on `MAX(ts)`.
- **Correctness (both panels, AC-D16.2):** no change to `ChartPanel`; continuity of
  `_bars` is the single fix for candles and volume (they share the list).
- **Correctness (closures, AC-D16.3 / AC-D16.7):** weekend/holiday/overnight are
  non-trading windows in `market_calendar`, so they are never requested-filled, never
  fabricated, and never compressed (timestamps are plotted as-is). **Dec 31 of a year whose
  next Jan 1 is a Saturday is explicitly *not* a closure** (`AC-D16.7`): under the NYSE Rule
  7.2 year-end accounting exception it is a trading day, so a genuine hole there is
  backfilled (`AC-D16.1`) or its shortfall surfaced (`AC-D16.4`) — never left as a silent
  hole (the ESC-023 defect).
- **Correctness (bounded, AC-D16.4):** chunking walks `endDateTime` back by the
  configured duration until the span start; `pacing_manager.throttle()` spaces requests;
  residual empty trading days + IBKR errors produce an explicit status-bar/log shortfall,
  and no bar is fabricated.
- **Correctness (switch safety, edge case):** a generation token plus cancellation of
  every id in `_history_req_ids` on symbol/timeframe change guarantees no
  cross-contamination; the existing `reqId` filter is generalised to the set.
- **Performance:** detection is O(trading days in `[min(ts), now]`) + O(N) over cached
  bars; chunk count is bounded by span/duration; chart render cost is unchanged; no
  per-frame allocation added.
- **Scalability:** chunk count is bounded by the missing span and IBKR retention; the
  cache is rebuilt once per load, not per chunk.
- **Security / live orders:** untouched. No automated test connects to live TWS or
  transmits an order (Q9); tests stub `IBApiClient.connect` and the managers.
- **Testability:** the two new services are pure and parameterised over all six
  timeframes and ≥2 symbols; one offscreen `MainWindow` integration test stubs the
  historical feed (pattern from `tests/test_watchlist_d14_midrag.py`).

## Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Holiday calendar drifts for future years | M | Holidays computed **by rule** (nth-weekday/fixed/Good Friday), not a fixed list; `tests/test_market_calendar.py` pins known holidays incl. Good Friday, Juneteenth, observed-day shifts |
| Observed-day shift misclassifies a genuine trading day (Dec 31) as a closure → silent hole (ESC-023 / R27) | M | `AC-D16.7` states the NYSE Rule 7.2 year-end accounting exception; the New Year's-specific rule never shifts a closure onto Dec 31; `tests/test_market_calendar.py` asserts `is_trading_day` is **True** for `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31`, and keeps every other observed shift (Independence Day/Christmas/Juneteenth/New Year's-Sunday) as a regression guard |
| IBKR long-ago data beyond retention returns nothing/errors → chart still has a hole | M | Chunk requests respect `pacing_manager`; residual missing trading days + `error_msg` on a backfill reqId are **surfaced** (status bar + log); never fabricate (AC-D16.4) |
| Many chunks hit IBKR's historical pacing limit | M | Chunk count bounded by span/configured duration; every request already goes through `pacing_manager.throttle()`; if a rate-limit `error_msg` arrives it is surfaced, not retried in a tight loop |
| Stale in-flight responses after a symbol/timeframe switch | H | `_history_generation` token + cancel every id in `_history_req_ids` on switch/close; `_on_historical_bar`/`_on_historical_data_end` drop non-current generation and non-member reqIds |
| Reusing `_pending_bars` for the chunk set regresses the single-request path | M | The set-of-one case is behaviourally identical; the existing `reqId` filter is preserved as membership; D1–D15 tests must stay green |
| Equity calendar mis-models futures (which trade some US holidays) | L | Consistent with the accepted `session_service`/DG1 default (equity sessions for all symbols); recorded as `PA-D16-3` and flagged (FI-D16-2) |
| Illiquid symbols have legitimately empty trading sessions → false "missing" | M | Day presence only needs **≥1** bar; a wholly empty day is the reported defect class; shortfall is surfaced (not fatal), and the per-day cadence assertion is applied only to the stubbed liquid scenarios |
| `endDateTime` formatting wrong (space vs hyphenated) triggers warning 2174 | L | Reuse the existing `_ibkr_end_date` (UTC hyphenated, already documented for this exact purpose) |
| Detection window grows unbounded if the cache is very old | L | Detection is bounded by `min(cached_ts)`; chunking is bounded by the span and by surfacing-on-shortfall when retention is exceeded |

## Flagged Issues (architecture-level)
The authoritative Flagged Issues list (with suggestions) lives in
`docs/plan_proposal.md` → **Flagged Issues**. In summary, the proposal surfaces:
`FI-D16-1` (AC-D16.1's per-bar cadence measurable assumes liquid data and cannot hold
for thinly traded symbols/empty periods) and `FI-D16-2` ("any symbol" vs an equity
holiday calendar for futures). Neither blocks the D16 fix; both need a Validator
decision on how the acceptance test is applied.

**ESC-023 correction pass:** no new Flagged Issues. `AC-D16.7` is satisfiable as written —
it is a self-contained holiday-rule correction with clear measurable assertions
(`is_trading_day(2021-12-31/2027-12-31/2032-12-31/2038-12-31) is True` plus an unchanged
observed-shift regression guard), so it requires no requirements escalation.
