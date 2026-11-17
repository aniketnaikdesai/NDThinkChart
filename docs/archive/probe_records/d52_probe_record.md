# D52 standalone IBKR probe record (AC-D52.7, P12-T3)

Date (UTC): 2026-10-29. Operator: Build Worker P12-T3.

## Method (read-only, port-guard respected)

- `config.settings.check_live_port()` passed (live TWS port), then a
  throwaway ibapi client (clientId 913, `/tmp`, never committed) connected
  to `127.0.0.1:7496` and issued **historical requests only** — no orders,
  no `placeOrder`/`cancelOrder`, no real-time subscriptions.
- Contract for every request: `AAPL STK SMART USD`, `TRADES`, `useRTH=1`,
  open end (`""`). Requests spaced 15 s apart (pacing-safe).
- A known-good control combo ran first to separate endpoint health from
  combo acceptance.

## Outcomes

| # | duration | bar size | completed | bars | first bar | last bar | errors |
|---|---|---|---|---|---|---|---|
| control | `30 D` | `5 mins` | yes | 2329 | 20260918 09:30:00 US/Eastern | 20261029 15:00:00 US/Eastern | farm-OK notices only (2104/2106/2158) |
| 1 | `30 D` | `30 mins` | yes | 389 | 20260918 09:30:00 US/Eastern | 20261029 15:00:00 US/Eastern | farm-OK notices only (2104/2106/2158) |

The new combo completed with **no 321-class rejection** (no error 321
on any request; the only codes seen were the informational 2104/2106/2158
farm-connection notices on reqId -1). Bar count matches expectation
(~13 RTH half-hour bars/day × 30 days ≈ 389; control ~78 five-minute
bars/day × 30 days ≈ 2329).

## Conclusion

AC-D52.7 probe gate **passes**: the (30 D, 30 mins)
historical request is accepted by live TWS. No R104 escalation, no
duration change.
