# Code Review — "Do I have the permissions needed for the footprint chart?"

**Owner question (verbatim):** *"What about the footprint chart — do I have the permissions needed for it?"*
**Author:** Code Reviewer (subagent session)
**Date:** 2026-10-15
**Scope:** diagnosis only. **No code, requirements, plan, architecture, task, plan, or build files were edited.**
**Concurrency:** `escalations.json` / `review_log.md` are otherwise quiescent this pass (max existing id = ESC-039). I append **one** entry (ESC-040) for a distinct defect found in the footprint error path; see §7.

---

## 0. Bottom line

1. **The footprint does not need market *depth* (L2).** It never calls `reqMktDepth`; it is built entirely on `reqHistoricalTicks`, a different request family. **The owner's L2/depth gap does not affect the footprint at all** (§5).
2. **Historical ticks require a *Level 1 (Top Of Book)* market-data subscription** for the instrument — that is IBKR's documented rule for the "Historical Time & Sales" feature, which covers **both** `TRADES` and `BID_ASK` (§2). This is the **same class** of subscription your chart's ordinary *bars* already need, and it is **different from (and lighter than)** the L2 depth entitlement.
3. **I cannot verify your specific subscriptions from this machine.** Whether you hold the Level 1 subscription for the instruments the footprint taps (ES/NQ/YM/RTY futures for the index proxies; US equities for SPY/QQQ/other symbols) is an IBKR-account fact, not a repo fact. What to check is in §8.
4. **The app cannot tell you the answer.** Unlike depth (`354 → no_entitlement`, `ui/ticker_session.py:794-795`) and news (`reqNewsProviders` → "No API news subscription", `ibkr/news.py:50`, `ui/news_digest_dock.py:146-148`), the footprint has **no entitlement probe and no "not subscribed" state**. On an IBKR permission error the bars stay **"loading" forever** — reproduced (§4, §7). So if you *are* unsubscribed, the app will show a permanent "Footprint loading…", not a reason.
5. **One distinct code defect found** → **ESC-040** (`BUILD`, `should-fix`): the footprint error handler swallows/ignores the permission error and leaves an eternal "loading" state (§7).

---

## 1. Exactly what the footprint requests (verified from the repo)

All historical-tick traffic goes through one method: `TickHistoryManager.req_historical_ticks`
(`ibkr/tick_history.py:50-88`). Two call sites in the session.

| Property | Value | Evidence |
|---|---|---|
| IBKR call | `reqHistoricalTicks(req_id, contract, startDateTime, endDateTime, numberOfTicks, whatToShow, useRTH, ignoreSize, [])` | `ibkr/tick_history.py:76-86` |
| `whatToShow` | **`"BID_ASK"` then `"TRADES"`** — never `MIDPOINT` | `services/footprint_service.py:156-161` (`next_spec`: BID_ASK phase first, TRADES second, both always run); session passes `spec.what_to_show` at `ui/ticker_session.py:1207`; forming loop `for what in ("BID_ASK","TRADES")` at `ui/ticker_session.py:1379` |
| `numberOfTicks` | **1000** (IBKR's documented max per request) | `ibkr/tick_history.py:35` (`TICKS_PER_REQUEST = 1000`), `:55`; call sites `ui/ticker_session.py:1206` and `:1383` |
| `useRTH` | **`1`** always (regular trading hours) | `ui/ticker_session.py:1208`, `:1383` |
| `ignoreSize` | **`False`** (keeps size-only updates — required for volume-at-price) | `ibkr/tick_history.py:84` |
| `startDateTime` / `endDateTime` strategy | **Backfill:** `startDateTime=""`, `endDateTime=<page cursor>` — pages *backward* from the bar's end. **Forming refresh:** `startDateTime=<forming bar start>`, `endDateTime=""` — one trailing window. Exactly one of the two is set, as IBKR requires. | backfill `ui/ticker_session.py:1204-1205`; forming `ui/ticker_session.py:1382`; cursor formatting `services/footprint_service.py:69-71` |
| Contract | index proxies resolve to the **front-month futures tape** (SPX→ES, NDX→NQ, DJI→YM, RUT→RTY; label "ES tape"); everything else uses the stock contract at `SMART` | `ibkr/contracts.py:133-138, 160-178, 181-187` |

**How many requests a typical chart load issues (the cap):**

- **Per-wave cap = 60 requests.** `MAX_REQUESTS_PER_WAVE = 60` (`services/footprint_service.py:46`), enforced in the session pump `while self._fp_wave_issued < MAX_REQUESTS_PER_WAVE:` (`ui/ticker_session.py:1173-1175`, counter `:1224`). A first load of an N-completed-bar chart issues **one BID_ASK page per bar, newest-first, capped at 60** (`next_wave`, `services/footprint_service.py:265-292`), then the TRADES phase + any backward follow-up pages count against the *same* 60-request burst.
- **Shared pacing budget = 60 requests / 600 s.** Historical-tick requests are charged to the same rolling historical budget as bars: `pacing_manager.record_historical_slot()` (`ibkr/tick_history.py:87`, gate `:73-75`), with `MAX_HISTORICAL_PER_600S = 60` (`config/settings.py:35`). The manager never sleeps — it raises `PacingExceeded` and the session defers via `QTimer.singleShot` (`ui/ticker_session.py:1210-1214`, `1229-1231`).
- **Forming bar:** +2 requests (one `BID_ASK` + one `TRADES`) at most every 15 s, and only when no backfill is pending (`ui/ticker_session.py:1379-1394`; cadence `services/footprint_service.py:47, 433-440`).
- **Cache:** cached symbols (SPX/SPY/QQQ/ES-front/NQ-front) reload with **zero** requests (`ui/ticker_session.py:1118-1122`, `services/footprint_service.py:188-196`). Practical consequence: if your cache is already warm you may see a footprint and never observe a subscription problem.

No `reqTickByTickData` anywhere — enforced by AC-D36.3 and `tests/test_d36_footprint.py:180-205`.

---

## 2. What entitlement each request needs (IBKR-documented vs asserted)

**Verified from IBKR's documentation:**

- IBKR's *Historical Time & Sales* page (https://www.interactivebrokers.com/docs/tws-api/doc/md/historical-ticks) states, for `reqHistoricalTicks`: **"Time & Sales data requires a Level 1, Top Of Book market data subscription."** That feature returns *both* `TRADES` (→ `historicalTicksLast`) and `BID_ASK` (→ `historicalTicksBidAsk`); the same "Level 1, Top Of Book" statement appears on the *Tick-By-Tick* page (https://www.interactivebrokers.com/docs/tws-api/doc/md/live-ticks).
- The same page documents: **"Historical tick data is only available for the last 3 years"**, and **"Data will not be returned from multiple trading sessions in a single request; Multiple requests must be used."** (the app's backward pagination respects the latter).

**So, for a US equity:**

| Request | Subscription that gates it | Source |
|---|---|---|
| `reqHistoricalTicks` `whatToShow=TRADES` | **Level 1 / Top Of Book** for that instrument | IBKR doc (above) |
| `reqHistoricalTicks` `whatToShow=BID_ASK` | **Level 1 / Top Of Book** — top-of-book bid/ask quotes are Level 1 data; the doc has no separate BID_ASK-specific subscription | IBKR doc (above); the `BID_ASK` variant is the *same* `reqHistoricalTicks` call, only a different `whatToShow` |
| ordinary historical **bars** (`reqHistoricalData`) | **Level 1 / Top Of Book** as well (missing permission → error 162) | IBKR error-code docs / campus |

**How this differs from depth and from bars:**

- **vs depth (L2):** `reqMktDepth` needs the per-venue **Level 2 / market-depth** entitlement — the heavier one the earlier `.md` investigation covered (`docs/code_review/market_depth_permissions.md`). Historical ticks are **not** gated by it. The two are unrelated request families with unrelated entitlements.
- **vs bars:** same *class* of subscription (Level 1). The practical upshot: **if your candles load for a symbol, you almost certainly already hold the Level 1 the footprint needs for that symbol** — the footprint is not asking for anything extra beyond Level 1.

**Asserted / not locally verifiable (stated plainly):**

- That BID_ASK historical ticks need *nothing more than* Level 1. This follows from the doc's blanket "Time & Sales data requires a Level 1" statement and from BID_ASK being top-of-book; I found **no** documented separate "tick-by-tick historical" subscription *beyond* Level 1 for API historical ticks. (The *live* `reqTickByTickData` path has an extra 5%-of-market-data-lines cap, but the app does not use it.)
- That IBKR returns **error 162** specifically for a missing historical-market-data permission *on historical ticks*. I verified error 162's documented meaning ("Historical market data Service error message", with the canonical text `…No market data permissions for <EXCHANGE> <SECTYPE>`), but I could **not** observe the exact code IBKR emits for historical *ticks* on a real session from here. See §3.
- Which of the owner's instruments/venues are subscribed — **an IBKR account fact, unverifiable on this machine.**

---

## 3. What the app does if the owner is NOT entitled (verified from the repo)

**Error routing chain:**

1. `IBClient.error` classifies and emits — `ibkr/error_codes.py::classify_error`; `ibkr/client.py:228-245`. Only `'info'` is suppressed; `'fatal'` and `'warning'` both emit `error_msg`.
2. `MainWindow._on_error` routes by reqId to the owning session — `ui/main_window.py:1650-1676` (footprint reqIds go through `session.on_historical_error`, `:1672`).
3. `TickerSession.on_historical_error` gives the footprint first refusal — `ui/ticker_session.py:1626-1635` → `on_fp_error` (`:1631`).
4. `TickerSession.on_fp_error` — `ui/ticker_session.py:1299-1322`.

**Classification of the relevant codes** (my own run of `classify_error`):

| Code | Meaning (IBKR) | `classify_error` |
|---|---|---|
| **162** | "Historical market data Service error message: … **No market data permissions for X**" — **the historical/no-permission code** | `fatal` (`ibkr/error_codes.py:12`) |
| 354 | "Requested market data is not subscribed…" (streaming) | `warning` (default) |
| 10197 | "No market data during competing session" | `warning` |
| 10168 | "Requested market data is not subscribed…" (delayed variant) | `warning` |
| 200 | "No security definition" | `fatal` |

Classification only gates suppression — **all of these reach `on_fp_error`.**

**What `on_fp_error` actually does** (`ui/ticker_session.py:1299-1322`):

- Unregisters + forgets the reqId (`:1310-1311`).
- Forming refreshes: return (`:1312-1313`).
- Non-forming specs: **only if `code != 162`**, it nulls the in-flight phase's cursor (`:1315-1321`). **For code 162 it does nothing at all** to the bar's state.
- It never calls `mark_no_tick_data()` and never sets the affected bar/symbol to `unavailable`.

**Result (reproduced against the real code — see §4):** with the permission error, every completed bar reads **`loading`** in perpetuity. `FootprintService.state()` returns `LOADING` whenever `bar_ts in self._jobs` (`services/footprint_service.py:412-422`) — and the errored job is never removed from `_jobs` (the error path never runs `_on_page`'s completion/`_unavailable_bars` bookkeeping, `services/footprint_service.py:342-350`). `chart_panel` then renders **"Footprint loading… (N bars)"** forever (`ui/chart_panel.py:729-747`, `:742-745`). `no_tick_data` stays `False`, so the honest "No tick data" label (`:737-739`) never appears either.

**Existing tests cover only the *non-error* paths** — `tests/test_d36_footprint.py`:
- `test_loading_state_until_data_ready` (`:277-285`) — loading until a page arrives.
- `test_no_tick_data_after_consecutive_empty_first_pages` (`:288-308`) — **3 consecutive *empty* first pages** → `unavailable` "no tick data". This is the *only* route to an explicit unavailable state, and it is driven by empty responses, **not** by an IBKR error.
- AC-D36.2 tests (`:106-163`) — contiguity / phase completion.
- **No test drives an IBKR error into the footprint path**: `on_fp_error` appears in **no** test file (`grep -rln on_fp_error tests` → empty). The `mark_no_tick_data()` "explicit signal (e.g. IBKR error)" hook (`services/footprint_service.py:401-404`) is **never called** by any production code (verified: only the definition + the internal `_declare_no_tick_data` call site exist).

---

## 4. Reproduction (offscreen, real code)

Drove the real `TickerSession` with the existing fake client/host from `tests/test_d36_footprint.py`, enabled footprint on 4 bars, and fed an IBKR error for every footprint reqId while the event loop ran (so the session's own re-pump/continue-timer behaved normally):

```
CODE 162 : no_tick_data=False  pending=3  states=['loading']  jobs_left=3  queued=3
CODE 354 : no_tick_data=False  pending=0  states=['loading']  jobs_left=3  queued=0
CODE 10197/10168/200: same → states=['loading'], no_tick_data=False
```

- **Every** code leaves **all** bars `loading`, `no_tick_data False`, and the chart showing "Footprint loading… (N bars)" indefinitely.
- With **162** the bars are additionally **re-requested in a loop** (the phase cursor is untouched, so `next_wave` re-issues the same page on each pump — bounded only by the 600 s/60-request pacing budget), i.e. a repeating no-permission request with no user-visible reason.
- There is **no** code path from an IBKR error to an explicit footprint state.

---

## 5. Does the footprint need DEPTH (L2)? — **No.**

- The footprint issues **only** `reqHistoricalTicks` / `cancelHistoricalTicks` (`ibkr/tick_history.py`, whole file; `grep` confirms no `reqMktDepth` in the footprint path).
- `reqHistoricalTicks` is a **historical-data** request (the same family as the chart's bars), gated by **Level 1 / Top Of Book**, independent of the L2 book entitlement that `reqMktDepth` needs.
- Therefore **your L2 gap (BATS/NASDAQ/ARCA/BEX/NYSE depth) is irrelevant to the footprint.** If the footprint is blank while your candles load, the cause is *not* depth — look at §7 / §8 instead.

---

## 6. Can the app answer "am I subscribed for this?" itself? — **No, not for the footprint.**

The app has entitlement states elsewhere but **none** for the footprint:

| Feature | Probe / explicit state | Evidence |
|---|---|---|
| Depth (D37) | `354` → `depth_state = "no_entitlement"` | `ui/ticker_session.py:794-795` |
| News (D38) | `reqNewsProviders` (entitled provider list) → "No API news subscription" | `ibkr/news.py:50`, `ui/news_digest_dock.py:146-148` |
| **Footprint (D36)** | **none** — no probe, no "not subscribed" state; an error degrades to an eternal "loading" | §3, §4 |

So today the owner would have to **infer** a footprint subscription problem from a stuck "Footprint loading…" label (or a blank chart) — which, per §7, is exactly what the app shows on a permission error. That inference-only situation is itself the finding (ESC-040).

---

## 7. Distinct defect → ESC-040

**Category:** `bug` · **Severity:** `should-fix` · **Routed to:** `BUILD`

**Observed.** `TickerSession.on_fp_error` (`ui/ticker_session.py:1299-1322`) never resolves a footprint request error to an explicit state, and explicitly ignores the one code IBKR uses for "no historical market-data permission":

- `if job is not None and code != 162:` (`ui/ticker_session.py:1315`) — **162 is IBKR's "Historical Market Data Service error message: No market data permissions for X"** code, not pacing-only. On 162 the handler leaves the phase exactly as-is; because the reqId was also forgotten (`:1311`), the same page is **re-issued in a loop** (bounded only by pacing).
- For any other code it only nulls the phase cursor; it never marks the bar unavailable nor the symbol `no_tick_data`, and never resumes/terminates the wave deliberately.
- Net: `FootprintService.state()` returns `LOADING` forever (job never leaves `_jobs`, `services/footprint_service.py:412-422`); `chart_panel` shows "Footprint loading… (N bars)" forever (`ui/chart_panel.py:742-745`); `no_tick_data` stays `False` so the honest "No tick data" label never shows.
- Reproduced for codes 162/354/10197/10168/200 (§4). No test covers it (`on_fp_error` appears in no test).

**Expected.** An IBKR error on a footprint request must resolve to a **terminal, user-visible** state for the affected bar/symbol (mirroring depth's `no_entitlement` and news's "No API news subscription") rather than a permanent "loading", and **162 must not be assumed to be pacing-only**. The wave must either resume deliberately or stop — never spin re-issuing a failed page.

**Suggested direction (not a decision made for them).** Split entitlement errors from pacing in `on_fp_error`; on an entitlement error call `FootprintService.mark_no_tick_data()` (already present, `:401-404`, currently dead code) or add a distinct "not subscribed" state, and surface it on the panel; ensure 162 no longer silently loops. Regression test: drive `session.on_fp_error(req_id, 162)` on a real spec and assert the surfaced state/flag (currently asserted nowhere).

**Distinctness.** Not covered by ESC-035 (depth `2152` → `unavailable`, a `REQUIREMENTS` behaviour decision) or ESC-039 (DOM-ladder request shape). This is the footprint's own error/maintenance path.

*Note:* the *choice of label* ("not subscribed" vs "unavailable" vs "no tick data") is a small product call. The **stuck-forever loading state is a defect regardless of the label chosen**, so this is routed as `BUILD`; if the team prefers to settle the label as a requirement first, the REQUIREMENTS side is a one-line AC addition, not a blocker for fixing the stuck state.

---

## 8. What the owner should check in IBKR (Account Management)

If the footprint is blank/stuck, check for the **Level 1 / Top Of Book** subscription on the instruments you footprint — *not* depth:

1. **Client Portal → Settings → Market Data Subscriptions.** Confirm a **Level 1 (Top Of Book)** subscription covering the footprint's instruments:
   - **US equities** (SPY, QQQ, AAPL, …): typically the **"US Securities Snapshot and Futures Value Bundle"** (often waived/free with commissions) or per-exchange Level 1.
   - **Index proxies (SPX/NDX/DJI/RUT)** tap the **CME/CBOT front-month futures** tape (ES/NQ/YM/RTY), so you need the **futures Level 1** data (e.g. the CME Level 1 / US Futures bundle), not an equity feed.
2. Confirm the subscription is on the **same user / account** the API connects with (the "additional subscription for API" wording in IBKR's error). Restart TWS/Gateway after a subscription change (IBKR notes permissions can take effect only after a restart).
3. Ignore the depth/L2 packages for this purpose — they are **not** what the footprint uses.
4. Remember the footprint is **default OFF** (`ui/chart_panel.py:359`) and **cached symbols render with zero requests** (§1) — so an empty result on a fresh (uncached) symbol is the signal to look at.

---

## 9. Verified from the repo vs IBKR-side (unverified locally)

**Verified from the repo (`file:line`):**
- Request shape: `ibkr/tick_history.py:35, 50-88` (`whatToShow` BID_ASK/TRADES, `numberOfTicks=1000`, `useRTH=1`, `ignoreSize=False`, one-of start/end); call sites `ui/ticker_session.py:1202-1209` (backfill) and `:1379-1393` (forming); phase order `services/footprint_service.py:156-161`.
- Wave cap 60: `services/footprint_service.py:46`, `ui/ticker_session.py:1173-1175`; pacing `config/settings.py:35`, `ibkr/pacing.py:95-118`.
- Contracts/proxies: `ibkr/contracts.py:133-138, 160-178, 181-187`.
- Error routing & handling: `ibkr/error_codes.py:12`; `ibkr/client.py:228-245`; `ui/main_window.py:1650-1676`; `ui/ticker_session.py:1626-1635`, `1299-1322`, `794-795`.
- States & UI: `services/footprint_service.py:392-404, 412-422`; `ui/chart_panel.py:359, 737-745`; contrast `ibkr/news.py:50`, `ui/news_digest_dock.py:146-148`.
- Coverage: `tests/test_d36_footprint.py:277-308` (states from empty pages only; no error path).
- Repro outputs in §4.

**IBKR-side assertions (documentation — not verifiable in this repo):**
- "Time & Sales data requires a Level 1, Top Of Book market data subscription" (Historical Time & Sales and Tick-By-Tick pages); historical tick data available for the last 3 years; one session per request.
- `162` = "Historical market data Service error message" incl. "No market data permissions"; `354` = "Requested market data is not subscribed…".

**Unverified locally (flagged, not escalated):**
- The exact code IBKR emits for a missing permission on historical *ticks* (I expect 162; could also surface as 354 or, in some cases, empty pages — an empty-page response would instead trigger the existing "No tick data" state, which is honest-but-misleading, not a hang).
- **Observation (low priority, shared with the bars path — NOT escalated):** `reqHistoricalTicks` docs say the datetimes "use the TWS timezone specified at login", while the app formats them in **UTC** (`services/footprint_service.py:69-71`; the bars path does the same — `services/backfill_service.py:128-133`). If TWS's login timezone is not UTC this could shift a page window; since the bars path uses the same convention and works in practice, I could not substantiate a defect, so I record it as an observation only.

---

## 10. Plain-language answer

**Does the footprint need permissions? Yes — but *not* the depth ones you were just diagnosed on.** The footprint is built entirely from *historical ticks* (`reqHistoricalTicks`), which IBKR gates on a **Level 1 / Top-Of-Book** market-data subscription for the instrument — the **same kind of subscription your ordinary chart bars already need**, and a **different (lighter)** one than the L2 depth entitlement.

**Your L2/depth gap is irrelevant to the footprint.** It does not touch depth; a missing BATS/NASDAQ/ARCA/BEX/NYSE *depth* feed changes nothing here.

**Can I confirm from the repo whether you're subscribed? No.** That is an IBKR-account fact I cannot see from this machine. What I *can* tell you is how to check (§8): a **Level 1 / Top-Of-Book** subscription on the footprint's instruments (US-equity Level 1 for stocks; the **CME/CBOT futures** Level 1 for the SPX/NDX/DJI/RUT proxies, since those tap the ES/NQ/YM/RTY tape).

**Why you may not have noticed a problem:** the footprint is **OFF by default**, and for **cached** symbols (SPX/SPY/QQQ/ES/NQ front) it renders from cache with **zero** requests — so it can look fine while being unsubscribed.

**If you are *not* subscribed, the app will not tell you.** Unlike depth and news (which have explicit "no entitlement" states), the footprint has **no** subscription check and **no** "not subscribed" state. On an IBKR permission error the bars sit at **"Footprint loading…"** forever. That is a real defect, and I raised it as **ESC-040** (`BUILD`, `should-fix`): the handler ignores error **162** — which is IBKR's *"No market data permissions"* code for historical data, not just pacing — so a permission failure never resolves to a visible state.

**Defect found: ESC-040** (footprint error/permission path → permanent "loading", 162 mishandled). **No request-shape defect found** (the request combination is valid: one of start/end set, 1000 ticks, Level-1-gated `BID_ASK`/`TRADES`).
