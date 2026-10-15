# Investigation — "When RTH is selected, only the current date is populated in the chart"

**Author:** Code Reviewer (subagent session)
**Date:** 2026-10-15
**Scope:** diagnosis only — **no code, requirements, plan, architecture, tasks or build files were edited.**
**Concurrency:** I did **not** modify `docs/code_review/escalations.json` or `docs/code_review/review_log.md`
(another Code Reviewer session owns them this pass). My findings live only in this file.

---

## 0. TL;DR

* **What is wrong is not `useRTH`.** When RTH is selected the app sends `useRTH=1` correctly — proved.
* **Why only one date:** the app's *fetch window* is what fixes how many sessions are ever present, and for
  the `1 min` timeframe that window is `"1 D"` → exactly **one session**. The D16 backfill
  (`find_missing_spans`) **only heals holes between the earliest cached day and now** — it can never extend
  history *backwards*. So a `1 min` chart is stuck at one calendar day until the app is run on successive days.
* The on-disk cache is the proof: **`SPY` `1 min` holds exactly one day** (`2026-10-15 04:00 → 14:00`, 601 bars);
  every other `(symbol, timeframe)` holds several days.
* The status line in the screenshot (`…ed bars. Cache current.`) is *exactly* the message the app prints when
  it decides **no fetch is needed** (`ui/main_window.py:1838-1840`) — i.e. the app believes the one-day cache
  is complete.
* **Data is missing, not collapsed away.** The D21.4 collapse only removes *between-session* gaps; with a single
  session it is the identity map and cannot hide dates. The empty space either side is simply the absence of data.
* **Owner/route:** the concrete code defect I can prove (a silent RTH hole on a mode switch) → **BUILD**;
  the "how much history should a `1 min` chart show?" decision → **REQUIREMENTS** (no written requirement
  specifies a history depth beyond "the configured window").

---

## 1. What "RTH" actually toggles, and the request it produces

**Proved — `useRTH` is correct.** The chain:

1. `ui/main_window.py:259-267` — `ext_hours_btn` defaults **checked** ("Ext Hours" = extended hours ON).
   Unchecked means RTH (`_ext_hours_label`, `:2956-2962`).
2. `ui/main_window.py:2964-2971` — `_on_ext_hours_toggled` → `load_chart()`.
3. `ui/main_window.py:1720-1721` — `extended_hours = self.ext_hours_btn.isChecked()`.
4. `ui/main_window.py:1759` — `chart_panel.set_extended_hours(extended_hours)`.
5. `ui/ticker_session.py:1514-1544` — `queue_wave_plans(... extended_hours)` / `_issue_wave_chunks` call
   `req_historical_data(..., useRTH=1, extended_hours=self._wave_extended_hours, duration=plan.duration)`.
6. `ibkr/market_data.py:48-58` — `effective_useRTH = 0 if extended_hours else useRTH`.

⇒ **RTH selected (`extended_hours=False`) → `effective_useRTH = 1` (regular hours). ETH selected → `0`.** Proven
by direct run: every request captured with the RTH button off carried `useRTH=1, ext=False`; with it on,
`useRTH=1, ext=True` (see §5 evidence). **Hypothesis #1 is disproved.**

## 2. The request window (`TIMEFRAME_CONFIG`)

`ibkr/market_data.py:7-14`:

| timeframe | duration | bar_size |
|---|---|---|
| **`1 min`** | **`1 D`** | 1 min |
| `5 mins` | `5 D` | 5 mins |
| `15 mins` | `5 D` | 15 mins |
| `1 hour` | `10 D` | 1 hour |
| `4 hours` | `30 D` | 4 hours |
| `1 day` | `1 Y` | 1 day |

The window does **not** depend on `useRTH` — `plan_requests` always uses `TIMEFRAME_CONFIG[timeframe]["duration"]`
(`services/backfill_service.py:310-313`), and the empty-cache fallback uses the same
(`ui/main_window.py:1822-1832`). So under RTH a `5 mins` request is still `5 D`, which IBKR returns as ~5 RTH
sessions — and the on-disk cache confirms `5 mins` symbols do hold many sessions (§5). Only the **`1 min`** window
is a single day: `"1 D"`.

**`useRTH=1` counts RTH sessions, so `1 D` = one RTH session**, i.e. `09:30–16:00` of one day (the screenshot's
`09:30 → 14:00` is that session still in progress). `5 D` would be five sessions — the app never asks for it on `1 min`.

## 3. The backfill path (D16) — why one day never grows

`ui/main_window.py:1795-1805` runs the planner on load:

```python
missing_spans = find_missing_spans(cached_ts, now_ts, timeframe, ext_hours=extended_hours) if cached else []
plans = plan_requests(missing_spans, timeframe)
```

`services/backfill_service.py:204-215` is the crux:

```python
present_days = {_et_date(ts) for ts in ts_values}
first_day = min(present_days)              # <-- the anchor
now_day = _et_date(now_ts)
trading = _trading_days(first_day, now_day)
missing = [day for day in trading if day not in present_days]
```

Detection is bounded **below by the earliest cached day**. It only ever *heals holes inside* `[first_cached_day, now]`;
it **cannot extend history backwards**. For a `1 min` cache whose only day is *today*, `first_day == now_day`,
`trading == [today]`, `missing == []` → `plans == []` → the branch at `ui/main_window.py:1836-1840` prints
`"{symbol} — {n} cached bars. Cache current."` and **issues no request at all**.

There is **no `useRTH`-dependent change to which spans are missing** beyond the session window used by the
bar-level pass (`services/backfill_service.py:276`), which is correct in the ordinary case.

### 3a. Latent mode-switch defect (provable)

The **day-presence pass is mode-blind** (any bar marks a day present) while the **bar-level pass is RTH-windowed**
and *skips the whole day when the RTH window is empty*:

```python
# services/backfill_service.py:276-281
for window in session_windows(day_start, day_end, ext_hours):
    ws, we = window["start_ts"], window["end_ts"]
    bound = min(we, now_ts)
    in_window = sorted(t for t in day_ts if ws <= t <= bound)
    if not in_window:
        continue          # <-- day has ETH bars but zero RTH bars => hole invisible
```

Reproduced (direct run, §5): a day holding **only pre/post bars** and **zero RTH bars** yields
`find_missing_spans(..., ext_hours=False) == []` — the RTH hole is **silently never requested** — while
`ext_hours=True` reports the whole span. This is the "believes the gap is already filled" case named in the
brief, and it contradicts the D16 edge case *"Ext Hours OFF vs ON changes `useRTH`; the backfill must respect
the current setting and not leave a hole because of a mode switch"* (`requirements.md:1819-1820`).

(Secondary: `BarCache` is keyed `(symbol, timeframe, ts)` only — `data/bar_cache.py:27-36`,
`data/db.py:16-22` — so RTH and ETH **share rows** with no session flag. This is a mode-bleed correctness issue,
but it would show *more* bars, not fewer, so it is **not** the cause of the reported one-day symptom.)

## 4. Time collapse (D21.4) — is the axis hiding the dates?

**No.** `services/time_collapse_service.py:51-63` collapses a gap `a < b` **iff
`session_windows(a + bar_period, b, ext_hours)` is empty** — strictly *between-session* gaps
(overnight/weekend/holiday). With a **single** session there is no such gap, so the map is the **identity**
(`build_collapse_map`, `:200-250`), the labels are true wall-clock, and the collapse cannot create the empty space;
if anything it would *remove* empty space. The RTH display filter (`ui/chart_panel.py:1162-1180`) is likewise a
pure *display* filter over `self._bars` and drops nothing from the cache.

⇒ The empty region around the one session is **absent data**, not a collapsed axis. (See §6 for the one caveat:
the ~1-day axis width implies the view range was wider than the single session — a range/fit question, not a
collapse question.)

## 5. Evidence I actually gathered

Read-only inspection of the live user cache
`~/Library/Application Support/NDThinkChart/charting_app.sqlite3` (same file `config/paths.py:68-81` resolves):

```
symbol timeframe  days  newest-day window
SPY    1 min       1    2026-10-15 04:00 → 14:00   <-- ONE day only
SPY    5 mins     24    2026-10-15 04:00 → 13:40
AAPL   5 mins      5    2026-09-14 → 09-18
QQQ    5 mins      5    2026-09-30 → 10-06
TSLA   5 mins      5    2026-09-30 → 10-06
```

Per-day RTH coverage: **every non-`1 min` day has RTH bars** (e.g. 79 RTH bars/day at 5 mins), so the RTH
*display* filter drops no day. Only `SPY 1 min` is a single day → only `1 min` can exhibit this.

End-to-end reproductions (offscreen `MainWindow`, stubbed managers, fixed `now = 2026-10-15 14:00 ET`):

* `SPY 1 min`, **RTH** → `plotted = 271` bars, all `09:30–14:00` **today**; collapse `is_identity=True`;
  **no request issued**; status = `"SPY — 601 cached bars. Cache current."`
  *(matches the screenshot text)*.
* `SPY 1 min`, ETH → same single day, `04:00–14:00`.
* `SPY 5 mins`, RTH → `plotted = 1845` bars over **24 sessions**; fetch `5 D`; correct.
* Empty cache, every timeframe, RTH → the emitted request duration is exactly the table in §2
  (`1 min` → **`1 D`**, `5 mins` → `5 D`, …), each with `useRTH=1`.
* Mode-mismatch probe: a day with ETH bars but **zero RTH bars** → `ext_hours=False` returns **no span**
  (silent hole); `ext_hours=True` returns the span.

## 6. Ranked root causes

| # | Rank | Cause | Status |
|---|---|---|---|
| 1 | **Most likely** | **`1 min` fetches `"1 D"` = one session, and the D16 backfill cannot extend history backwards (`find_missing_spans` anchors at `min(present_days)`).** `ibkr/market_data.py:8` + `services/backfill_service.py:208-215` + `ui/main_window.py:1795-1805,1836-1840`. | **Proved** (cache + code + status line) |
| 2 | Secondary / latent | **Mode-blind day-presence + RTH-windowed bar-level pass**: a day with ETH bars and no RTH bars is silently skipped (`services/backfill_service.py:280-281`); plus a `useRTH`-blind cache key (`data/bar_cache.py:27`, `data/db.py:16-22`). | **Proved** by unit-level reproduction; a real mode-switch path exists but is an edge case, not the reported symptom |
| 3 | Unverifiable | IBKR returned fewer than `5 D` sessions for a `5 mins` RTH request (entitlement / `useRTH`+`durationStr` semantics). | **Not supported** — the on-disk cache shows every `5 mins` symbol has multiple days |

**Not causes (disproved):** wrong `useRTH` (it is `1` under RTH — §1); the D21.4 collapse (§4); a `useRTH`-blind
cache *serving a narrower set* (the cache holds more, not fewer — §3a).

## 7. Axis: collapsed vs data missing — **data missing**

Evidence:
1. The status line `…ed bars. Cache current.` is emitted only in the no-fetch branch
   (`ui/main_window.py:1836-1840`) → the app issued **no request**, so the older dates were never fetched.
2. The on-disk cache physically contains one day for `1 min`.
3. The collapse is between-session-only and identity for one session (`services/time_collapse_service.py:51-63`),
   so it cannot manufacture the empty space.

One honest caveat: my `1 min` RTH reproduction fits the axis **tightly** (~5 h, no large margins), so the
screenshot's wider (~1-day) axis implies the **view range was wider than the single session** at capture time
(user zoom / an un-refit range, e.g. `ChartPanel.set_extended_hours` refreshes with `auto_range=False`,
`ui/chart_panel.py:1409-1416`, though a full `load_chart` re-fits via `update_chart`). Either way this is a
*range* effect layered on top of missing data — **it is not the axis collapsing real data away.**

## 8. Does it contradict a written requirement?

* **Yes, partly.** `requirements.md:1819-1820` requires the backfill to *"respect the current setting and not
  leave a hole because of a mode switch"* — the §3a silent-RTH-hole behaviour violates this (proved).
* **No** for the main symptom: the app *does* satisfy `AC-D16.1` (`:1739-1750`, continuity "from the oldest
  displayed bar through now") and the edge case *"Empty cache / brand-new symbol → fetch the configured window"*
  (`:1824`), because the window is `1 D` and it fetched exactly that. Nothing written specifies a **minimum
  history depth** or that RTH should show more than one session; D16's journey even assumes *"Ext Hours is ON"*
  (`:478`). So the one-day `1 min` result is **unfiled** — a requirements/design gap, not a code violation.
* D21.4 (`:2268-2274`) is satisfied — with RTH selected only RTH bars show and non-RTH time collapses.

## 9. Verdict, owner/route, and warranted test

**Verdict:** a **defect**, in two separable parts:

1. **`1 min` cannot show more than one session** (the owner's symptom). The fetch-window choice
   (`1 min` → `1 D`) is a design/config decision no requirement set a floor for, and `find_missing_spans`
   is by design a gap-healer, not a history extender. → **Route to `REQUIREMENTS`** (define the expected history
   depth per timeframe / a minimum session count under RTH). If the decision is instead "change the request
   window strategy", the follow-on is `PLAN`.
2. **Silent RTH hole on a mode switch** (mode-blind day-presence + empty-window skip). → **Route to `BUILD`**
   (`services/backfill_service.py` detection must treat a *present-but-RTH-empty* day as missing when
   `ext_hours=False`).

**Next free escalation id: `ESC-037`** (`ESC-036` is the current maximum). Suggested split:
`ESC-037` → `BUILD` (silent RTH hole, `should-fix`); `ESC-038` → `REQUIREMENTS` (intraday history depth, `should-fix`).

**Warranted regression tests** (assert the invariant, not a single case):

```python
# BUILD — must be RED pre-fix, GREEN post-fix
def test_d16_rth_reports_hole_when_day_has_eth_bars_only():
    # a trading day whose cached bars are all outside RTH (zero RTH bars)
    cached = pre_and_post_bars(today)                 # e.g. 04:00–09:25 + 16:05–19:55
    spans = find_missing_spans(cached, now, "5 mins", ext_hours=False)
    assert spans, "an RTH hole in a day that has ETH bars must be reported"

# REQUIREMENTS/BUILD — the owner's symptom
def test_intraday_chart_covers_more_than_one_session():
    # fresh cache -> load each intraday timeframe with RTH selected
    calls = load_fresh(symbol, "1 min", rth=True)
    # the issued historical request(s) must cover >= 2 trading sessions,
    # i.e. NOT a single "1 D" request for the intraday timeframes
    assert sessions_covered(calls) >= 2
```

(Invariant at play: **"RTH mode must still yield a usable multi-session intraday series, and must not silently
treat an RTH gap as filled."** If an AC is written case-by-case instead, the Task Manager should rewrite it to
this invariant — one `TASK_MANAGER`/`REQUIREMENTS` escalation rather than accumulating per-case `BUILD` patches.)

---

## 10. Housekeeping / confirmations

* **I did not modify `docs/code_review/escalations.json` or `docs/code_review/review_log.md`** (both are owned by
  the concurrent Code Reviewer session this pass). Nothing outside `docs/code_review/` was edited.
* During a reproduction run one throwaway symbol (`SYM`, 960 bars) was written to the user SQLite cache by the
  app's own `BarCache.save_bars`; **I removed it** (and the test-only `ZZTEST` symbol I used) — verified gone.
  The cache now contains exactly the symbols it did before: `AAPL, P1A, P1B, P1C, P2D, P2T, QQQ, SPY, TSLA`.
* This file (`rth_single_day_investigation.md`) is the only artifact I created.
