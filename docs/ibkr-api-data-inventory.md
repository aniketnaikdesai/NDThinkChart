# IBKR TWS API — Exhaustive Data Inventory (IBKR-only desktop trading terminal)

> Research date: 2026-10-13. Sources: official TWS API docs — current docs site verified live at https://www.interactivebrokers.com/docs/tws-api/doc/introduction, plus the (now deprecated) official docs mirror at interactivebrokers.github.io/tws-api, plus community sources flagged where used. Confidence per item is marked `verified live`, `index` (docs mirror), or `index/community`. Anything the terminal would act on should be re-verified at build time against the campus docs.

## Summary

The TWS API exposes: full L1 streaming quotes + 60+ tick types, 5-second real-time bars, tick-by-tick data (bid/ask, trades, midpoint), OHLCV historical bars (1 sec–1 month granularity), historical tick-by-tick (max 1000/request), L2 market depth (incl. SMART aggregated depth), news headlines/articles/bulletins, a market scanner, option chain skeletons + real-time Greeks/IV, full contract details, account/position/PnL data, open/completed orders and executions with commissions. Live L1/history requires paid per-exchange market-data subscriptions; free 15–20 min delayed data is available. **Critically: `reqFundamentalData` (ReportSnapshot/ReportRatios/financials/estimates) has been REMOVED from the current API** (verified live on the current docs site — no Fundamentals section exists; community pins removal to API 10.47). There is also no analyst-ratings, social-sentiment, economic-calendar, sector-constituent, tax-lot, or historical-Greeks feed. Up to 32 API clients per TWS/Gateway; default 100 market-data lines; historical pacing is a hard 60 requests/10 min.

## 1. Market data

### reqMktData
`reqMktData(tickerId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)` — streams one contract's quotes. Data arrives via: `tickPrice` (bid/ask/last/high/low/close/open...), `tickSize` (bid/ask/last size, volume...), `tickGeneric` (misc stats, IV, shortable...), `tickString` (RTVolume, last timestamp, news, dividends, exchanges), `tickOptionComputation` (Greeks, see §8), `tickEFP`, `tickNews`. `cancelMktData(tickerId)`. `snapshot=True` = one-time snapshot; `regulatorySnapshot=True` = one-time NBBO snapshot for holders of the "US Securities Snapshot Bundle" without full exchange subs — **$0.01 fee per snapshot**. Since TWS 985, US stock bid/ask/last sizes are reported in **shares** (not 100-share lots). Sources: tick_types.html, market_data.html, md_receive.html (index).

Full tick-type list (id — name — generic tick required in `genericTickList` — callback):
- Auto-delivered (no generic tick): 0 Bid Size, 1 Bid Price, 2 Ask Price, 3 Ask Size, 4 Last Price, 5 Last Size, 6 High, 7 Low, 8 Volume (day; US stocks ×100 multiplier noted in docs), 9 Close (previous day; US equities adjusted for splits/dividends), 14 Open, 32/33 Bid/Ask Exchange, 45 Last Timestamp, 49 Halted, 50/51/52 Bid/Ask/Last Yield (bonds), 84 Last Exchange, 85 Last Regulatory Time (regulatory snapshots), 88 Delayed Last Timestamp.
- Option Greeks (auto for options): 10/11/12/13/53 → `tickOptionComputation` (impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice).
- Generic-tick-gated: 100 → 29/30 Option Call/Put Volume (day); 101 → 27/28 Option Call/Put Open Interest; 104 → 23 30-day Historical Volatility; 105 → 87 Average Option Volume; 106 → 24 IB 30-day Implied Volatility; 162 → 31 Index Future Premium; 165 → 15–20 13/26/52-week high/low + 21 90-day Avg Volume; 221/232 → 37 Mark Price (**conflict**: current tick-types page says generic 232; older references say 221 — verify at build); 225 → 34 Auction Volume, 35 Auction Price, 36 Auction Imbalance, 61 Regulatory Imbalance; 233 → 48 RT Volume (price;size;time;totalVol;VWAP;singleMM flag); 236 → 46 Shortable (difficulty rating) + 89 Shortable Shares (share count, TWS 974+); **258 → Fundamental Ratios — REMOVED/desupported (API 9.81.01)**; 375 → 77 RT Trade Volume (excludes unreportable trades); 411 → 58 RT Historical Volatility (30d); 456 → 59 IB Dividends ("past12m,next12m,nextDate,nextAmt"); 460 → 60 Bond Factor Multiplier; 292 → 62 News (provider-specific, e.g. `292:BZ`); 293/294/295 → 54 Trade Count / 55 Trade Rate / 56 Volume Rate; 318 → 57 Last RTH Trade; 576 → 94/95 ETF NAV Bid/Ask; 577 → 96 ETF NAV Last; 578 → 92/93 ETF NAV Close/Prior Close; 614 → 98/99 ETF NAV High/Low; 623 → 97 ETF NAV Frozen Last; 586 → 101 Estimated IPO Midpoint / 102 Final IPO Price; 588 → 86 Futures Open Interest; 595 → 63/64/65 Short-Term Volume (3/5/10 min, stocks); 619 → 79 Creditman Slow Mark Price. Delayed variants auto-appear: 66–88 (Delayed Bid/Ask/Last/High/Low/Volume/Close..., 80–83 delayed option greeks). Source: https://interactivebrokers.github.io/tws-api/tick_types.html (index).
- Notable: Shortable tick 46 = rating (>2.5 → ≥1000 shares shortable; 1.5–2.5 → locatable; ≤1.5 → not shortable); tick 89 = actual share count.

### reqRealTimeBars
`reqRealTimeBars(tickerId, contract, barSize, whatToShow, useRTH, realTimeBarsOptions)` — **bar size is fixed at 5 seconds only**; one OHLC bar every 5 s via `realTimeBar`. `whatToShow=TRADES` required to get volume/VWAP/trade count. Counts as BOTH a market-data line and against historical pacing (≤60 new requests/10 min). `cancelRealTimeBars`. Must be re-subscribed after server resets/session changes. Source: realtime_bars.html (index).

### reqMarketDataType
`reqMarketDataType(1|2|3|4)` — call **before** `reqMktData`; effective type reported per request via `marketDataType(reqId, type)` callback.
- 1 Live — real-time; requires market-data subscriptions.
- 2 Frozen — last recorded quote (for closed markets); requires the same subscriptions as live; **generic tick types not available on frozen**.
- 3 Delayed — **free**, 15–20 min delayed; auto-applies when the user lacks live subs (ignored if live available); returned on delayed tick ids 66–88.
- 4 Delayed-frozen — delayed "frozen" for users with no subscriptions.
TWS v970+: `marketDataType(…,1)` fires automatically after reqMktData when live permissions exist. Source: market_data_type.html (index).

### reqHeadTimestamp / cancelMktData
- `reqHeadTimestamp(tickerId, contract, whatToShow, useRTH, formatDate)` → `headTimestamp(reqId, headTimestamp)`: the earliest date for which that `whatToShow` has data — use it to discover true history depth. `cancelHeadTimestamp`.
- `cancelMktData(tickerId)` stops a streaming subscription (frees a market-data line).

## 2. Tick-by-tick — reqTickByTickData
`reqTickByTickData(requestId, contract, tickType, numberOfTicks, ignoreSize)`; `tickType` is case-sensitive: `BidAsk`, `Last`, `AllLast`, `MidPoint`. `cancelTickByTickData`.
- `Last` → `tickByTickAllLast(tickType=1, …)`; `AllLast` → same callback with tickType=2 and **additionally includes combos, derivatives, average-price trades** not in `Last`. Fields: time, price, size, tickAttribLast (pastLimit, unreported bits), exchange, specialConditions.
- `BidAsk` → `tickByTickBidAsk`: time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk (bidPastLow, askPastHigh bits). `ignoreSize=True` suppresses size-only updates.
- `MidPoint` → `tickByTickMidPoint`: time, midPoint (mainly FX).
- If `numberOfTicks != 0`, recent historical ticks are first replayed through `historicalTicksLast`/`historicalTicksBidAsk`/`historicalTicks`.
- Limits: options = historical only (no real-time tick-by-tick); indices = CME indices only; combos not supported; **≤1 request per instrument per 15 s**; simultaneous subscriptions follow the market-depth formula (min 3, max 60, scaling with market-data lines). TWS 10.15+/API 10.15+: `pastLimit` attribute with zero price/size marks halted/unhalted ticks. Source: tick_data.html (index).

## 3. Historical data — reqHistoricalData / reqHistoricalTicks
`reqHistoricalData(tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate, keepUpToDate, chartOptions)` → `historicalData(reqId, bar)` per bar (time, open, high, low, close, volume, count/tradeCount, WAP) then `historicalDataEnd`. Bar timezone = TWS login timezone.
- `endDateTime`: `"yyyyMMdd-HH:mm:ss"` (+ optional TMZ); empty = now.
- `useRTH`: 1 = regular-hours only, 0 = all sessions.
- `formatDate`: 1 = `"yyyyMMdd HH:mm:ss"`, 2 = epoch seconds (day bars: yyyyMMdd only).
- `keepUpToDate=True` (API 973.03+/TWS 965+): streaming updates of the unfinished bar via `historicalDataUpdate`; bar size must be ≥5 s; `endDateTime` must be empty. `cancelHistoricalData`.
- Valid bar sizes: `1 secs, 5 secs, 10 secs, 15 secs, 30 secs | 1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, 30 mins | 1 hour, 2 hours, 3 hours, 4 hours, 8 hours | 1 day | 1 week | 1 month`. Smallest = 1 s.
- Duration↔bar-size compatibility (must fit one of these): 60 S → 1 s…1 min; 120 S → 1 s…2 min; 1800 S → 1 s…30 min; 3600 S → 5 s…1 h; 14400 S (4 h) → 10 s…3 h; 28800 S (8 h) → 30 s…8 h; 1 D → 1 min…1 day; 2 D → 2 min…1 day; 1 W → 3 min…1 week; 1 M → 30 min…1 month; 1 Y → 1 day…1 month. Source: historical_bars.html, historical_limitations.html (index).
- "whatToShow" values: TRADES (splits-adjusted, not dividends), MIDPOINT, BID, ASK, BID_ASK (time-avg bid/ask; open=avg bid, close=avg ask), ADJUSTED_LAST (splits+dividends, TWS 967+), HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY, FEE_RATE, YIELD_BID / YIELD_ASK / YIELD_BID_ASK / YIELD_LAST (corporate bonds only), SCHEDULE (TWS API 10.12+, 1-day bars only, delivered via `historicalSchedule` with session start/end/timezone — no OHLCV), AGGTRADES (**crypto only**). Per-product table: stocks/ETFs support TRADES/MIDPOINT/BID/ASK/BID_ASK/HV/OIV/SCHEDULE; FX & CFDs have no TRADES (use MIDPOINT); indices only TRADES/HV/OIV/SCHEDULE; options only TRADES/MIDPOINT/BID/ASK/BID_ASK; bonds add all four YIELD_*; crypto TRADES/MIDPOINT/BID/ASK/BID_ASK/SCHEDULE/AGGTRADES. Source: historical_bars.html (index).
- Caveats: feed is **filtered** — excludes trades away from NBBO (combos, block, derivatives) so volume < unfiltered feeds; no native history for combos (sum of legs); futures daily close may be the **settlement price** (lands hours after close); ≤30 s bars older than 6 months unavailable; **no history at all for expired options/FOPs/warrants/structured products or their EOD**; expired futures >2 y
...[truncated 17093 chars]