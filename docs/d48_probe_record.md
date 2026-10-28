# D48 standalone IBKR probe record (AC-D48.6, P8-T02)

Date (UTC): 2026-10-28. Operator: Build Worker P8-T02.

## Method (read-only, port-guard respected)

- `config.settings.check_live_port()` passed (live TWS port), then a
  throwaway ibapi client (clientId 912, `/tmp`, never committed) connected
  to `127.0.0.1:7496` and issued **historical requests only** — no orders,
  no `placeOrder`/`cancelOrder`, no real-time subscriptions.
- Contract for every request: `AAPL STK SMART USD`, `TRADES`, `useRTH=1`,
  open end (`""`). Requests spaced 15 s apart (pacing-safe).
- A known-good control combo ran first to separate endpoint health from
  combo acceptance.

## Outcomes

| # | duration | bar size | completed | bars | first bar | last bar | errors |
|---|---|---|---|---|---|---|---|
| control | `30 D` | `5 mins` | yes | 2340 | 2026-09-16 09:30 US/Eastern | 2026-10-27 15:55 US/Eastern | farm-OK notices only (2104/2106/2158) |
| 1 | `2 Y` | `1 week` | yes | 105 | 20241101 | 20261027 | none |
| 2 | `10 Y` | `1 month` | yes | 121 | 20161031 | 20261027 | none |

Both new combos completed with **no 321-class rejection** (no error 321
on any request; the only codes seen were the informational 2104/2106/2158
farm-connection notices on the control). Bar counts match expectation
(~104 weekly bars in 2 Y, ~120 monthly bars in 10 Y).

## Conclusion

AC-D48.6 probe gate **passes**: both `(2 Y, 1 week)` and `(10 Y, 1 month)`
historical requests are accepted by live TWS. No R93 escalation, no
duration change. (First attempt with a wrong `error()` override signature
returned garbled codes and a spurious 504; fixed signature + control combo
on re-run — recorded here so the garbled first run is never mistaken for
a rejection.)
