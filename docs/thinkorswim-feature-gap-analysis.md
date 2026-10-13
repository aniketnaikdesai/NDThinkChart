# ThinkOrSwim → NDThinkChart: Feature Gap Analysis (IBKR-only data)

*2026-10-13. Source: deep web-index review of Schwab ThinkOrSwim desktop (16-section catalog;
nothing verified inside the running app — treat fine details as approximate). Constraint from
owner: **IBKR is the only data source; no other external software or vendors** (IBKR-sold
market-data subscriptions, e.g. Level II depth, count as IBKR).*

## 1. What NDThinkChart already has (D1–D28 baseline)

Candlestick charts with studies (SMA/EMA/VWAP/Bollinger/RSI/MACD/ICT/gap/VIX), drawing tools +
zones + persistent settings, watchlist, price alarms with **headless per-ticker monitoring**,
Active Trader + Portfolio docks, bracket/OCA orders with validation gate + kill switch,
detachable per-ticker pop-out chart windows (10 cap, read-only, restored across restarts),
pacing off the GUI thread, historical pacing, render-layer split with a 10-chart perf gate,
clean teardown, 898-test suite. This analysis measures ToS features against that baseline.

## 2. IBKR data inventory — the raw material

Available via the TWS API (all IBKR-native, no external vendor):

- **Market data:** 5-sec realtime bars; historical bars (1-sec → 1-month, duration-capped per
  bar size); tick-by-tick (Last, AllLast, BidAsk, MidPoint); Level I quotes; **Level II depth**
  (`reqMktDepth`, needs an IBKR depth subscription); extended-hours bars.
- **Options:** chains (`reqSecDefOptParams`); per-contract **Greeks + IV** via
  `tickOptionComputation`; volume / open interest on chains.
- **Scanner:** `reqScannerSubscription` with IBKR scan codes (top % gainers/losers, most
  active, high option volume, put/call ratios, hot contracts, etc.), filterable by
  instrument/region.
- **Fundamentals:** ⚠️ `reqFundamentalData` was **removed** from the TWS API (v10.47;
  verified 2026-10-13 against IBKR's current API docs — no replacement). Ratios, financial
  statements, and estimates are **not** obtainable via the API. Corporate events
  (earnings/dividends/splits) are available via WSH event data
  (`reqWshMetaData` / `reqWshEventData`).
- **News:** news providers, bulletins, historical headlines
  (`reqNewsProviders` / `reqNewsBulletins` / `reqHistoricalNews`).
- **Account:** positions, PnL, orders, executions.
- **Orders:** MKT/LMT/STP/STP-LMT/TRAIL; bracket (parent + children); OCA groups; IBKR **algo
  orders** (VWAP, TWAP, ArrivalPx, DarkIce, etc.); **conditional orders** (price / time /
  margin / execution / volume / percent-change conditions); **combo (BAG) multi-leg** orders;
  fractional shares (US stocks).
- **Pacing reality:** ~60 historical requests per 10 min (already handled in 4a); scanner and
  chain-heavy features must be designed around it.

**Not obtainable from IBKR:** analyst ratings, social sentiment, economic calendars, licensed
video/news, server-side execution while the app is closed, full historical tick archives
(duration caps apply).

## 3. Feature-by-feature verdicts

Legend: ✅ Have · 🟢 Feasible (IBKR-only) · 🟡 Partial · 🔴 Not feasible (IBKR-only).
Effort uses the plan's S/M/L scale.

### 3.1 Charts

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Heikin-Ashi / Equivolume styles | 🟢 | S | Pure computation from OHLCV |
| Renko / tick / range / volume aggregations | 🟢 | M | Build locally from tick-by-tick |
| 400+ built-in studies | 🟢 | S each / M program | Any study is computable from OHLCV; recommend curated "study pack" batches rather than 400 at once |
| 20 drawing tools (8 Fibonacci) | 🟡 | M | Core set exists; add Fib extensions/channels, pitchfork |
| Candlestick pattern recognition | 🟢 | S–M | Algorithmic from OHLCV |
| Chart-pattern (H&S, wedges, triangles) auto-detect | 🟢 | M | Feasible but noisy; lower value than it looks |
| Alerts set from drawings | 🟢 | S–M | Alarm engine exists; extend triggers to drawings |
| Flexible Grid + symbol/timeframe linking | 🟢 | M | Client-side layout manager; pop-outs already exist |
| Detachable windows | ✅ | — | Pop-outs (D24) |
| Saved/shared chart styles | 🟢 | S | SQLite + export file |

### 3.2 thinkScript → custom indicator engine

The single highest-leverage feature in ToS: one engine powering custom studies, scan filters,
watchlist columns, and alert conditions. Cloning thinkScript syntax verbatim is L effort and
buys compatibility with a language the owner doesn't need. Recommended instead:

- **Python-based indicator API (M):** sandboxed functions receiving OHLCV + indicator
  library, hot-reload, shared as files. Fits a PyQt app; more powerful than thinkScript
  (no thinkScript limits: real loops, arrays, multi-timeframe).
- One engine, four surfaces: chart studies, scanner filters, custom watchlist columns,
  alert conditions. This multiplies the value of every other P0 item.

### 3.3 Scanner (Stock / Option / Spread Hacker)

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Scan UI on IBKR scan codes + dynamic watchlists | 🟢 | M | The closest IBKR-native equivalent of Stock Hacker |
| Client-side study scans over watchlist | 🟢 | M | Pacing-aware design required (60 req/10 min shapes it) |
| Option Hacker (Greeks/IV/OI filters) | 🟢 | M–L | Chain fetch per symbol is heavy; scope to watchlist |
| Spread Hacker | 🟡 | L | Client-side spread-construction scan; defer |
| Server-side always-on scan alerts | 🔴 | — | No server; best available = client-side + headless monitor while app runs (pattern exists from D25) |

### 3.4 Trade tab / orders

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Conditional orders (incl. cross-symbol / study triggers) | 🟢 | M | IBKR `OrderConditions` cover price/time/margin/execution/volume/percent-change; study triggers via local engine |
| OCO / 1st-triggers-OCO | 🟢 | S–M | Bracket exists (D26); add OCA templates |
| Saved order templates | 🟢 | S | SQLite; shareable as files |
| Big Buttons / program buttons | 🟢 | S | Client-side presets |
| Drag-drop working orders on chart/ladder | 🟢 | M | — |
| Forex / futures traders | 🟢 | M each | IBKR supports; scoping question (equities-first?) |
| Pairs trader | 🟡 | — | Two coordinated orders; low value, defer |

### 3.5 Analyze tab — the #1 differentiator

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Risk Profile P&L graphs | 🟢 | M–L | Needs chains + IV (IBKR) + a local Black-Scholes pricer. **Highest-priority single build.** |
| Probability ITM / OTM / Touching | 🟢 | S–M | From IV once the pricer exists |
| Market Maker Move (expected move) | 🟢 | S | ~IV-implied expected move; compute locally, no license needed |
| What-if (price/vol/time shifts) | 🟢 | M | Rides on the pricer |
| Per-expiry expected move on chain | 🟢 | S | — |
| thinkBack options backtesting | 🟡 | — | IBKR lacks historical IV chains; limited to underlying replay |

### 3.6 Options tools

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Chains with Greeks / IV / OI / Sizzle | 🟢 | M | `tickOptionComputation`; Sizzle = volume vs 5-day avg from chain history |
| Multi-leg single orders | 🟢 | M | IBKR BAG combos |
| Strategy Roller (auto-roll covered calls) | 🟢 | M | Rule engine + orders; note this is automation — confirm it's in scope |
| Probability of Expiring cone study | 🟢 | S | Rides on the pricer |

### 3.7 Active Trader / DOM

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| DOM ladder (have basic D18) | ✅/🟢 | — | Extend: Level II depth columns (needs IBKR depth sub) — M; Time & Sales via tick-by-tick — S–M |
| Drag working orders on ladder | 🟢 | M | — |
| Options on DOM | 🟢 | M | Later |

### 3.8 Monitor

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Position grouping / Greeks columns | 🟢 | S–M | Have positions; add columns |
| Beta weighting | 🟢 | S–M | Historical data → beta vs index, computed locally |
| Tax lots | 🟡 | — | IBKR API doesn't expose lots directly; verify before promising |
| Account statements in-app | 🔴 | — | IBKR Flex is web-only; link out |

### 3.9 News / research

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| News headlines feed | 🟢 | S–M | IBKR news providers |
| Fundamentals panel (ratios/statements/estimates) | 🔴 | — | `reqFundamentalData` was removed from the TWS API (v10.47); no API replacement. Not feasible IBKR-only. |
| Earnings/dividend/split calendar | 🟡 | S | Via WSH event data (`reqWshMetaData`/`reqWshEventData`) — corporate events only, not full economic calendar |
| Heatmap | 🟡 | M | Build from IBKR scanner results (gainers/losers, most active) |
| Economic calendar | 🔴 | — | Not in IBKR |
| Analyst ratings / social sentiment | 🔴 | — | Not in IBKR |
| Licensed video (CNBC et al.) | 🔴 | — | Licensed; no |

### 3.10 Paper trading

Technically feasible (IBKR paper/DU account), but the repo's standing decision is **live-only**.
Flagged as an owner decision, not a technical gap.

### 3.11 Replay (thinkOnDemand)

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Tick archive back to 2009 | 🔴 | — | IBKR duration caps forbid it |
| Record-and-replay going forward | 🟢 | M | App records ticks/bars locally; replay mode with simulated orders. Recommended shape. |

### 3.12 Alerts

| ToS feature | Verdict | Effort | Notes |
|---|---|---|---|
| Price alerts | ✅ | — | Have (D25) |
| Study-condition alerts | 🟢 | S–M | Evaluate per tick; alarm engine exists |
| News alerts | 🟢 | M | Rides on news feed |
| Scan-change alerts (while running) | 🟢 | M | Client-side; no logged-out firing |
| Email via user's own SMTP | 🟢 | S | — |
| SMS / push | 🔴 | — | Needs external gateway |

### 3.13 Misc

- **Fractional shares:** 🟢, S (IBKR supports).
- **Extended-hours display:** ✅ have.
- **Multi-asset (futures/forex):** 🟢, scoping question.
- **Education / chat rooms / tos.mx sharing:** out of scope for a solo-dev terminal; file-sharing
  of studies/scans covers the useful part of sharing.

## 4. Priority roadmap

### P0 — build first (top differentiators, all IBKR-feasible)
1. **Options Analyze tab** — Risk Profile + ITM/OTM/Touching probabilities + MMM + what-if
   (needs option chains first; the pricer is the keystone).
2. **Option chains with Greeks/IV/OI/Sizzle.**
3. **Custom indicator engine (Python API)** — unlocks studies, scan filters, watchlist columns,
   alert conditions in one build.
4. **Scanner** on IBKR scan codes + dynamic watchlists (+ client study scans).
5. **Conditional orders + OCO/bracket templates.**
6. **DOM ladder depth**: Level II + Time & Sales + drag-drop order management.
7. **Study-condition alerts.**
8. **Footprint charts** — bid×ask volume-at-price from historical ticks; a pro day-trader
   staple ToS lacks natively (see §6).

### P1 — high value, moderate effort
Study-pack expansion · Renko/tick/range/Heikin-Ashi aggregations · Flexible Grid + symbol
linking · multi-leg option orders (BAG) · news integration · Fib/pitchfork
drawing expansion · saved order templates + Big Buttons · scanner heatmap · beta weighting ·
**auction imbalance panel** · **unusual-volume burst alerts** · **WSH event markers +
countdowns** · **depth heatmap / book imbalance** · **symbol search autocomplete** ·
**news-for-holdings digest** (see §6).

### P2 — later / needs scope decisions
Strategy Roller (automation — confirm in scope) · Spread Hacker · record-and-replay ·
pairs · futures/forex depth · email alerts · fractional shares.

### Out of scope under the IBKR-only constraint
Analyst ratings · social sentiment · economic calendar · licensed media · server-side
always-on alerts · full historical tick archive · in-app account statements.

## 5. Suggested requirement batches (D29+ candidates)

- **D29:** Real SL/TP leg transmission (already planned).
- **D30:** Options chains + Greeks data layer.
- **D31:** Analyze tab (Risk Profile, probabilities, MMM, what-if).
- **D32:** Custom indicator engine (Python API).
- **D33:** Scanner (IBKR codes + dynamic watchlists + study scans).
- **D34:** Conditional orders + order templates.
- **D35:** DOM ladder (Level II + T&S + drag-drop).
- **D36:** Footprint charts (bid×ask volume-at-price via historical ticks / histogram).
- **D37:** Microstructure (depth heatmap + book imbalance; auction imbalance panel).
- **D38:** Events & news (WSH earnings/dividend/split markers + countdowns on charts;
  news-for-holdings digest).
- **D39:** Discovery & alert expansion (symbol search autocomplete; unusual-volume burst alerts).
- Order adjustable per owner priority; D30 should precede D31 (pricer needs chains).
- API constraints shaping design: D33 scanner — max 10 concurrent scans, 50 results each,
  results carry no market-data fields (separate quote request per hit); D35/D37 depth —
  per-exchange subscription required, 3–60 simultaneous feeds; D36 footprint — historical
  ticks only (live tick-by-tick ≤1 req/instrument/15s); backtest/replay scope bounded
  (no ≤30s bars past 6 months, no expired-option history).

## 6. IBKR-native additions (beyond ToS parity) — owner-requested 2026-10-13

These came from the IBKR API inventory (see `docs/ibkr-api-data-inventory.md`), not from
ToS. All are IBKR-feasible.

| Feature | Effort | IBKR path | Notes |
|---|---|---|---|
| Footprint charts (bid×ask volume-at-price) | M | `reqHistoricalTicks` (BID_ASK + TRADES, ≤1000/req) or `reqHistogramData` | Pro day-trader staple; ToS lacks it natively. Must use historical ticks — live tick-by-tick capped at 1 req/instrument/15s. → P0, D36 |
| Depth heatmap / book imbalance | M | `reqMktDepth` SMART aggregated | Rides on D35 depth work. Needs per-exchange depth subscription; 3–60 simultaneous feeds. → P1, D37 |
| Auction imbalance panel | S–M | Auction ticks 34/35/36/61 | Opening/closing auction display. → P1, D37 |
| Unusual-volume burst alerts | S | Trade count/rate (54/55/56), short-term volume 3/5/10-min (63/64/65) | Rides on the D25 alarm engine. → P1, D39 |
| Earnings/dividend/split markers + countdowns | S–M | WSH `reqWshMetaData` / `reqWshEventData` | Chart markers like ToS. → P1, D38 |
| Symbol search autocomplete | S | `reqMatchingSymbols` | Quick UX win. → P1, D39 |
| News-for-holdings digest | S–M | IBKR news providers (`reqNewsProviders`, `reqHistoricalNews`) | Rides on news integration. → P1, D38 |

### Operational caveat: weekly re-auth vs headless monitoring
IBKR requires a full re-authentication roughly weekly, which breaks the always-on assumption
behind headless alarm monitoring (D25). **Follow-up:** reconnect/re-auth story for the alarm
monitor (detect auth expiry, surface state, resume monitoring after re-login).

## 7. Caveats

- ToS research is web-index derived, not live-app verified; fine details (exact study counts,
  archive depths, limits) are approximate — the source catalog flags confidence per item.
- Verify with IBKR before building: depth subscription SKUs/cost, crypto coverage for your
  account, news provider entitlements on your account. (Note: `reqFundamentalData` was
  removed in API v10.47 — do not plan around it; corporate events come via WSH event data.)
- ToS's weaknesses are NDThinkChart's openings: the Java client is memory-hungry and laggy
  (your render-layer split already attacks this), the UI is widely called dated and hard to
  learn (your chrome-light pop-outs are the right instinct), and thinkScript can't place live
  orders — a Python engine with *optional* live-order hooks would leapfrog it, if the owner
  wants automation in scope.
