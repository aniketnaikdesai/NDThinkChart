# IBKR TWS API — Data Inventory (10.51.01)

> **API version:** 10.51.01. Client surface verified against the 10.51.1 Python client
> (`EClient`/`EWrapper` signatures grepped 2026-10-13).
> **Research date:** 13 October 2026. "Current" refers only to the documentation and
> client checked on that date.
> **WSH corporate-events API: verified present** in 10.51.1
> (`reqWshMetaData`, `reqWshEventData`, both cancels, `wshMetaData`/`wshEventData` callbacks).
> The older GitHub Pages mirror (interactivebrokers.github.io/tws-api) is deprecated but
> remains the preserved source for many field-level tables. Confidence per item is marked
> `verified live`, `client-verified` (10.51.1), `mirror` (docs mirror), or flagged as a
> conflict/caveat inline. Anything the terminal acts on should be re-verified at build time
> against the current API.

**Sources:** (1) Current Interactive Brokers TWS API documentation — live verification,
including the removal of the Fundamentals section (10.47). (2) Official deprecated mirror:
tick types; historical bars; historical limitations; historical Time & Sales; real-time bars;
tick-by-tick data; market-data types; market data; receiving market data; options; market
scanners; news; cryptocurrency. (3) IBKR 2026 API production release notes
(ibkrguides.com, 10.43–10.51). (4) 10.51.1 client source (`ibapi` package) — method/callback/
field existence verified directly.

## Executive summary

**The practical answer:** Interactive Brokers exposes enough data for a serious charting and
trading terminal: Level 1, 5-second bars, tick-by-tick, historical OHLCV, SMART depth, option
chains and Greeks, scanners, news, corporate events (WSH), portfolio/P&L, order state, and
executions.

**The major break:** `reqFundamentalData` and the fundamental-ratios tick were removed in
API 10.47 (methods, callbacks, and delivered tick 47 all gone — confirmed absent in the
10.51.1 client). Financial statements, estimates, and ratios must not be designed as IBKR API
features.

**The operating constraint:** entitlements, pacing, shared market-data lines, session resets,
and periodic human re-authentication are architectural inputs, not edge cases.

| 100 | 60 / 10 min | 32 | 15–20 min |
|---|---|---|---|
| default market-data lines | historical-request ceiling | API clients per TWS/Gateway | free delayed-data lag |

## 1. Streaming market data

Top-of-book prices, sizes, and 60+ specialist ticks arrive through one subscription surface.

**`reqMktData`** — streams a contract's bid, ask, last, sizes, open/high/low/close, day volume,
exchange/timestamp fields, generic statistics, option computations, EFP data, and news ticks.
Callbacks: `tickPrice`, `tickSize` (now `Decimal` — fractional sizes supported since 10.44),
`tickGeneric`, `tickString`, `tickOptionComputation`, `tickEFP`, `tickNews`. `snapshot=True`
gives a one-time snapshot; a regulatory NBBO snapshot costs $0.01 and requires the US
Securities Snapshot Bundle. Since TWS 985, US stock sizes are reported in shares, not
100-share lots. Cancel with `cancelMktData`.

**`reqMarketDataType(1|2|3|4)`** — call before `reqMktData`; effective type reported per
request via `marketDataType(reqId, type)`. 1 Live (subscriptions required); 2 Frozen (last
recorded quote after close; subscriptions still required; no generic ticks); 3 Delayed (free,
15–20 min late; delayed tick IDs 66–88); 4 Delayed-frozen (last delayed quote without
subscriptions).

**`reqRealTimeBars`** — one OHLC bar every 5 seconds (bar size fixed). `whatToShow=TRADES`
required for volume, WAP, and trade count. Consumes a market-data line AND counts against
historical pacing. Re-subscribe after server resets or session changes. `cancelRealTimeBars`.

**`reqHeadTimestamp`** — returns the earliest timestamp available for a contract and
`whatToShow`. The reliable way to discover actual history depth rather than assuming a fixed
lookback. `cancelHeadTimestamp`.

### Specialist tick map

Standard, option, and generic ticks exposed through the market-data subscription surface.
Delivered-tick IDs are positional in the client's `TickTypeEnum`.

- **0–9, 14** — bid/ask/last sizes and prices; high, low, volume, previous close, open.
- **10–13, 53** — bid/ask/last/model/custom option computation: IV, delta, option price,
  PV dividend, gamma, vega, theta, underlying price.
- **Generic 100 / 101** — call/put option volume (delivered 29/30) and open interest
  (delivered 27/28).
- **Generic 104 / 106 / 411** — 30-day historical volatility, IB 30-day implied volatility,
  real-time historical volatility.
- **105 / 588** — average option volume (generic 105 → delivered tick 87); futures open
  interest.
- **105–110 (delivered)** — **new in 10.46:** odd-lot bid/ask/bid-size/ask-size/bid-exchange/
  ask-exchange. Requested via **generic tick 787**. Namespace warning: generic tick 105
  (average option volume) is NOT delivered tick 105 (`ODD_LOT_BID`) — request and delivery
  IDs live in different namespaces.
- **165** — 13/26/52-week highs and lows plus 90-day average volume.
- **225** — auction volume, auction price, auction imbalance, regulatory imbalance.
- **232 vs 221** — Mark Price. Current table says generic 232; older references say 221.
  Treat as an unresolved documentation conflict — verify at build.
- **233 / 375** — RT Volume (price, size, time, total volume, VWAP, single-MM flag);
  RT Trade Volume excludes unreportable trades.
- **236** — shortable rating and Shortable Shares. Rating >2.5 means ≥1,000 shares;
  1.5–2.5 locatable; ≤1.5 not shortable.
- **292** — provider-specific news headlines (e.g. `292:BZ`).
- **293 / 294 / 295** — trade count, trade rate, volume rate.
- **318 / 456 / 460** — last RTH trade; IB dividends; bond factor multiplier.
- **576–578, 614, 623** — ETF NAV bid, ask, last, close, prior close, high, low, frozen last.
- **586 / 595 / 619** — estimated/final IPO price; 3/5/10-minute volume; Creditman slow mark.
- **258 / 47** — **removed in 10.47:** fundamental ratios (generic 258; delivered tick
  `FUNDAMENTAL_RATIOS = 47`). Both gone from the 10.51.1 client.
- Delayed variants 66–88 mirror the live ticks on delayed data.

## 2. History and tick-by-tick

Bar history is broad, but requests are paced and the feed is filtered. Tick history is precise
but capped per call.

**`reqHistoricalData`** — returns time, open, high, low, close, volume, trade count, and WAP
per bar, then `historicalDataEnd`. `useRTH` chooses regular-hours-only or all sessions.
Bar sizes: 1/5/10/15/30 sec; 1/2/3/5/10/15/20/30 min; 1/2/3/4/8 hour; 1 day/week/month.
`whatToShow`: TRADES, MIDPOINT, BID, ASK, BID_ASK, ADJUSTED_LAST, HISTORICAL_VOLATILITY,
OPTION_IMPLIED_VOLATILITY, FEE_RATE, bond YIELD variants, SCHEDULE, crypto AGGTRADES.
`keepUpToDate=True` streams updates of the unfinished bar (bar size ≥5 s, `endDateTime`
empty) via `historicalDataUpdate`. Cancel with `cancelHistoricalData`.

**Duration compatibility** (request duration → permitted bar sizes): 60 sec → 1 sec–1 min;
1 hour → 5 sec–1 hour; 1 day → 1 min–1 day; 1 week → 3 min–1 week; 1 month → 30 min–1 month;
1 year → 1 day–1 month. (Abridged — verify the full table at build.)

**`reqHistoricalTicks`** — highest-granularity historical Time & Sales, **max 1,000 ticks per
request**. TRADES returns time, price, size, exchange, conditions, attributes; BID_ASK
returns both prices and sizes; MIDPOINT returns time, price, size. Exactly one of start/end
time is set; a request does not cross multiple trading sessions (it may exceed 1,000 only to
complete a final second). No combos or AllLast-style block/combo trades. Cancel with
**`cancelHistoricalTicks`** (client-verified, 10.51.1).

**`reqTickByTickData`** — live ticks. `Last`: trade time, price, size, attributes, exchange,
conditions. `AllLast`: adds combo, derivative, and average-price trades. `BidAsk`: bid/ask
prices and sizes with bidPastLow/askPastHigh attributes. `MidPoint`: time and midpoint
(mainly FX). Options are historical-only; combos unsupported; indices limited to CME indices;
**one request per instrument per 15 seconds**. Cancel with `cancelTickByTickData`.

**`reqHistogramData`** — **confirmed present in 10.51.1** (was a build-time unknown in earlier
research). Returns histogram entries for a contract over a requested period, each entry
carrying **price and size only** — a server-produced volume-at-price distribution, not a
substitute for raw historical ticks (no bid/ask split). Regular-hours vs all-sessions
selectable. Availability and accepted period strings are contract-dependent; verify against
the current API build.

**`historicalSchedule`** — callback **confirmed present in 10.51.1**
(`reqId, startDateTime, endDateTime, timeZone, ...`). The earlier caveat about its absence is
dropped. Delivers session start/end/timezone for `whatToShow=SCHEDULE` (1-day bars only).

**`cancelContractData`** — cancels an in-flight `reqContractData` (client-verified, 10.51.1).

### Historical-data caveats that matter to chart correctness

- The historical feed is **filtered**: off-NBBO trades, combos, block trades, and derivative
  trades can be excluded, so volume can read lower than unfiltered feeds.
- Bars ≤30 seconds are unavailable beyond six months.
- Expired futures older than two years are unavailable; expired options, FOPs, warrants, and
  structured products have **no history or EOD data**.
- Daily futures closes may be settlement prices and can arrive hours after the session.
- No native combo history; legs must be requested separately.
- BID_ASK historical requests count as two pacing requests.

## 3. Options

IBKR supplies the chain skeleton and live computations; the application must validate
contracts and combine legs.

**`reqSecDefOptParams`** — per exchange: underlying conId, trading class, multiplier, a set
of expirations and a set of strikes. Expirations and strikes are independent lists — not every
combination is a valid contract. Preferred over `reqContractDetails` enumeration for large
chains (which are throttled). Futures options also require the futures-option exchange
parameter.

**`tickOptionComputation`** — from an option `reqMktData` subscription, bid/ask/last/model
ticks return implied volatility, delta, option price, present-value dividend, gamma, vega,
theta, and underlying price.

**`calculateOptionPrice` / `calculateImpliedVolatility`** — request IBKR's option-model
calculations for theoretical price or IV. Both have matching cancellation methods.

**Generic ticks 100 / 101** — on the underlying stock, aggregate call/put option volume and
open interest. Full per-contract quote/Greek coverage still needs option-contract market-data
lines.

## 4. Depth, scanners, and news

Discovery and context are available, but market-data and news entitlements determine what is
actually delivered.

**`reqMktDepth`** — Level 2 market depth, including SMART aggregated depth and
exchange-specific depth where subscribed. Depth subscriptions consume market-data lines and
have their own simultaneous-subscription formula (min 3, max 60, scaling with market-data
lines). The finished research confirmed the capability but did not preserve the complete
row-field schema — verify the current official method page before implementing the book
model. **`reqMktDepthExchanges`** lists venues offering deep-book data.

**`reqScannerParameters`** — returns XML describing available scan codes, instruments,
locations, and filters. Use it instead of hard-coding the server's scanner catalog.

**`reqScannerSubscription`** — streams ranked `ContractDetails` results plus distance,
benchmark, projection, and combo legs. Examples: top % gainers/losers, most active, hot by
volume, high option-volume put/call ratio. **Max 50 results per scan; max 10 active API
scans.** Scanner rows contain no bid/ask/last/volume — subscribe separately. Scanner use
itself needs no market-data subscription, but filters generally do.

**`reqNewsProviders`** — returns subscribed provider codes and names. Most TWS news products
are not automatically available to the API; API-specific subscriptions and entitlements apply.

**`reqHistoricalNews`** — historical headlines: time, provider code, article ID, headline,
followed by a `hasMore` marker. **`reqNewsArticle`** retrieves the article body.

**Real-time headlines** — arrive through generic tick 292 and the `tickNews` callback.

**`reqNewsBulletins`** — exchange bulletins. `allMessages=True` includes existing bulletins
from the current day plus new ones; `False` delivers only new bulletins. `cancelNewsBulletins`.

## 5. Contract and market structure

Contract discovery resolves conIds and routing; auxiliary requests expose price increments,
venue mappings, volume-at-price distributions, and corporate events.

**`reqContractDetails`** — returns matching contract definitions and metadata. Can enumerate
option contracts from an incomplete option description, but large chains are throttled;
`reqSecDefOptParams` is preferred for chain discovery. New fields in the 10.51.1 client
(client-verified): size block (`minSize`, `sizeIncrement`, `suggestedSizeIncrement`,
`minAlgoSize`), precision block (`lastPricePrecision`, `lastSizePrecision`),
`settlementMethod`, a full **mutual-fund block** (`fundName`, `fundFamily`, `fundType`,
`fundFrontLoad`, `fundBackLoad`, `fundBackLoadTimeInterval`, `fundManagementFee`,
`fundClosed`, `fundClosedForNewInvestors`, `fundClosedForNewMoney`, `fundNotifyAmount`,
`fundMinimumInitialPurchase`, `fundSubsequentMinimumPurchase`, `fundBlueSkyStates`,
`fundBlueSkyTerritories`, `fundDistributionPolicyIndicator`, `fundAssetType`,
`ineligibilityReasonList`), and **event-derivative fields** (`eventContract1`,
`eventContractDescription1`, `eventContractDescription2`). **`mdSizeMultiplier` removed**
(confirmed absent in 10.51.1). Cancel in-flight requests with `cancelContractData`.

**`reqMarketRule`** — given a market-rule ID from contract details, returns the tick ladder:
price-increment bands, each defining the minimum price at which a particular increment
applies. Use to validate and round order/chart prices across tiered tick sizes.

**`reqSmartComponents`** — maps SMART bid/ask exchange component codes to exchange
identifiers (including the exchange letter used in market-data attribution). Reference
metadata, not a depth subscription.

### Wall Street Horizon corporate events (verified present, 10.51.1)

**`reqWshMetaData(reqId)`** → **`wshMetaData(reqId, dataJson: str)`** — describes available
corporate-event filters and fields. **`reqWshEventData(reqId, wshEventData)`** →
**`wshEventData(reqId, dataJson: str)`** — returns subscription-dependent company events as
JSON: event type, contract identifiers, and event-specific dates/status fields. Both have
matching cancels: `cancelWshMetaData`, `cancelWshEventData`. Protobuf variants exist for all
four.

The `WshEventData` request carries: `conId`, `filter` (JSON string), `fillWatchlist`,
`fillPortfolio`, `fillCompetitors`, `startDate`, `endDate`, `totalLimit`.

This is a **paid/entitled** Wall Street Horizon product — corporate events (earnings,
dividends, splits), not a broad macroeconomic calendar. Field sets vary by event type and API
version. It is the IBKR-native replacement path for the removed fundamentals feed's
*calendar* use case only (dates of events, not financials).

## 6. Account, positions, and P&L

Portfolio state is rich enough for a live terminal; tax-lot state is not.

**`reqAccountUpdates`** — initial dump, then changes: account key/value/currency; portfolio
(contract, position, market price/value, average cost, unrealized and realized P&L); update
time and completion marker. One account at a time; a second subscription cancels the first.
Account-value updates are no more frequent than about every three minutes.

**`reqAccountSummary`** — account, tag, value, currency. Key tags: NetLiquidation,
TotalCashValue, SettledCash, BuyingPower, EquityWithLoanValue, GrossPositionValue,
initial/maintenance margin, AvailableFunds, ExcessLiquidity, Cushion, SMA, LookAhead values,
DayTradesRemaining, Leverage. ~3-minute cadence. The docs' `ReqTEquity`/`ReqTMargin` names
conflict with community-tested `regTEquity`/`regTMargin` — verify at build.

**`reqPositions`** — account, contract, position quantity, average cost for all accessible
accounts. (10.51 fix: the exchange field now returns accurate values for commodities/CFDs.)

**`reqPnL` / `reqPnLSingle`** — account/model P&L: daily, unrealized, realized; the single
variant adds position and market value for one conId.

**`reqAccountUpdatesMulti` / `reqPositionsMulti`** — account/model-scoped values and
positions for advisors and model portfolios.

## 7. Orders and executions

The API exposes live order state, completed orders, fills, and commissions — with client-ID
scope rules.

**`reqOpenOrders`** — current client's open orders: contract, order state, status fields
including filled/remaining, average fill, permId, parentId, last fill, clientId, held reason,
market-cap price. **Since 10.48 the response includes de-activated orders** — expect them and
handle explicitly. Client ID 0 can bind pre-existing TWS/manual orders. **`reqAllOpenOrders`**
gives a one-time view of all open orders across associated accounts. **`reqAutoOpenOrders`**
(client-ID-0 only) auto-binds future TWS orders to API-originated orders.

**`reqCompletedOrders`** — completed orders, with an `apiOnly` switch to restrict to
API-originated orders.

**`reqExecutions`** — filter by client ID, account, time, symbol, security type, exchange,
side. Each execution: execution ID, time, account, exchange, side, shares, price, permId,
client/order IDs, liquidation flag, cumulative quantity, average price, order reference,
model, liquidity, price-revision state. Default scope is since midnight; up to seven days
depends on the TWS Trade Log setting; IB Gateway is limited to the current day.

**Commission reports** — **`commissionAndFeesReport`** (replaces the old `commissionReport`,
removed): execution ID, **`commissionAndFees`** (commission **plus fees** — not commission
alone), currency, realized P&L, plus bond fields (`yield_`, `yieldRedemptionDate`).

**Order-object fields of note (10.51.1, client-verified):** `deactivate` (pairs with the
10.48 de-activated order state), `conditionsIncludeOvernight` (10.50 — conditional orders may
include overnight sessions when evaluating criteria), `hedgeMaxSize` (10.45),
`includeOvernight`, `postOnly`, and bracket-linkage fields `slOrderId`/`slOrderType` and
`ptOrderId`/`ptOrderType`. **Removed fields** (confirmed absent in 10.51.1): `eTradeOnly`,
`faProfile`, `firmQuoteOnly`, `nbboPriceCap` — do not reference them.

## 8. Crypto and fractional shares

Both are possible, but order semantics are narrower than standard whole-share equities.

**Crypto (PAXOS)** — `secType=CRYPTO`, exchange=PAXOS, currency=USD (from TWS/API 10.10+).
BTC and ETH are documented examples. L1, L2, and historical TRADES/MIDPOINT/BID/ASK/
BID_ASK/AGGTRADES supported. Crypto permission required, but no market-data subscription and
no data fee. Only MKT and LMT orders; market buys require `cashQty` and IOC; limits use IOC
or Minutes TIF and cancel after five unfilled minutes.

**Fractional shares** — with Fractional Shares permission, stock market buys can be expressed
via `order.cashQty`. Sells reject `cashQty`; reduce or close a dollar amount using the exact
fractional share quantity. Community testing reports directly submitted fractional sizes can
be rejected — re-verify this path against the account and current API before production use.
`tickSize` now delivers `Decimal` sizes (fractional last sizes, 10.44).

## 9. Practical limits and operations

These are architectural constraints, not tuning suggestions.

**Pacing:** 60 historical requests / 10 min (BID_ASK counts twice); max 50 simultaneous
historical requests; no identical historical request within 15 s; one tick-by-tick request
per instrument per 15 s.

**Capacity:** 100 market-data lines default, shared across TWS, API, real-time bars, and
depth; max 10 active scanner subscriptions × 50 rows each.

**Entitlements:** live L1/history generally requires exchange subscriptions, trading
permission, and a funded account (FX and bonds excepted). Subscriptions are per TWS username
and billed for the full month. Paper trading can share live subscriptions when enabled;
activation may take up to 24 hours.

**2FA / headless:** TWS/Gateway login uses username, password, and 2FA. Daily auto-restart
can preserve a session, but full re-authentication is forced roughly weekly and needs a
person. Headless operation is not officially supported — design monitoring around the daily
login lifecycle.

**Release hygiene (10.45):** TWS/Gateway 10.45 one-time clears "Enable ActiveX and Socket
Clients" and "Allow connections from localhost only." After upgrading, re-enable API access
or nothing connects.

**Cancellation methods** — use the matching cancels to free resources and prevent stale
callbacks: `cancelMktData`, `cancelRealTimeBars`, `cancelHistoricalData`,
`cancelHistoricalTicks`, `cancelContractData`, `cancelTickByTickData`,
`cancelScannerSubscription`, `cancelNewsBulletins`, P&L/account-summary cancellations.

**Utility requests (short notes):** get/update-config request/response exists as a
**protobuf-based** API (`updateConfigProtoBuf` / `updateConfigResponseProtoBuf`).
**`reqUserInfo(reqId)`** → `userInfo(reqId, whiteBrandingId)`. **`reqCurrentTimeInMillis()`**
→ `currentTimeInMillis(timeInMillis)` — server clock in milliseconds.

## 10. Explicitly not available

These cannot be sourced through the current TWS API under an IBKR-only constraint.

- **Fundamentals & ratios** — `reqFundamentalData`, historic report types, and generic tick
  258 / delivered tick 47 are removed/desupported (10.47). No replacement API exists.
- **Analyst ratings** — no general analyst-ratings feed.
- **Social sentiment** — no social-sentiment feed.
- **General macroeconomic calendar** — no broad native macro calendar. Subscription-dependent
  Wall Street Horizon *corporate*-event data is available separately (§5).
- **Sector constituents** — no general sector-index constituent feed.
- **Tax lots** — positions expose average cost only; lots require statements/Flex, not the
  TWS API.
- **Historical Greeks** — no historical option-Greeks feed; Greeks are live computations only.
- **Full tick archive** — historical Time & Sales is capped at 1,000 ticks per call and
  constrained to one session.

## Sources and confidence

Research date: 13 October 2026. "Current" refers only to the live documentation and the
10.51.1 client checked on that date. The older GitHub Pages mirror is deprecated but remains
the preserved source for many field-level tables; implementation-critical conflicts are
called out above (mark-price 232 vs 221; `ReqTEquity`/`ReqTMargin` vs `regTEquity`/
`regTMargin`).

1. Current Interactive Brokers TWS API documentation — live verification, including the
   removal of the Fundamentals section (10.47).
2. Official deprecated mirror: tick types.
3. Historical bars, historical limitations, historical Time & Sales, real-time bars,
   tick-by-tick data.
4. Market-data types, market data, receiving market data.
5. Options; market scanners; news; cryptocurrency.
6. IBKR 2026 API production release notes (10.43–10.51).
7. 10.51.1 client source — method/callback/field existence verified directly
   (`EClient`/`EWrapper`/`Order`/`ContractDetails`/`TickTypeEnum`).
