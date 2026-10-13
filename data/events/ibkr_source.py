"""D38 IBKR event source (38b.1): dividends from generic tick 456.

The dividend data arrives back as tick type 59 via ``tickString`` on the
symbol's S0 reqMktData (the "456" generic is the *request* code — the plan's
B1 correction). This source reads the parsed tick-59 state off the owning
``TickerSession``; it issues no requests itself.

Futures contracts are skipped (plan A38.4): there is no dividend stream on
futures, so subscribing would be pointless.
"""

from datetime import date

from data.events.provider import Event, EventProvider, parse_ib_dividend_string


def _is_futures_symbol(symbol: str) -> bool:
    try:
        from ibkr.contracts import FUTURES_SCHEDULE
    except Exception:
        return False
    base = (symbol or "").split()[0].upper()
    return base in FUTURES_SCHEDULE


class IBKREventSource(EventProvider):
    """Dividend events from the session's tick-59 state (S0, generic 456)."""

    def __init__(self, session_lookup):
        """``session_lookup(symbol) -> TickerSession | None``."""
        self._lookup = session_lookup

    def get_events(self, symbol: str, start: date, end: date) -> list[Event]:
        if _is_futures_symbol(symbol):
            return []
        session = self._lookup(symbol)
        if session is None:
            return []
        info = session.dividend_info() or {}
        next_date = info.get("next_date")
        if not isinstance(next_date, date):
            return []
        if not (start <= next_date <= end):
            return []
        amount = info.get("next_amt")
        return [Event(
            id=f"ibkr:dividend:{symbol.upper()}:{next_date.isoformat()}",
            type="dividend",
            symbol=symbol.upper(),
            date=next_date,
            source="ibkr",
            details={"amount": amount} if amount is not None else {},
        )]

    def unavailable(self, symbol: str) -> bool:
        # IBKR dividends ride the live S0 subscription: if the session has no
        # tick-59 data yet the source simply has nothing — that is "no events",
        # not an outage (outages surface via the session/connection state).
        return False


def dividend_event_from_tick_string(symbol: str, value: str) -> Event | None:
    """Build the dividend Event from a raw tick-59 string (for tests)."""
    parsed = parse_ib_dividend_string(value)
    next_date = parsed.get("next_date")
    if not isinstance(next_date, date):
        return None
    return Event(
        id=f"ibkr:dividend:{symbol.upper()}:{next_date.isoformat()}",
        type="dividend",
        symbol=symbol.upper(),
        date=next_date,
        source="ibkr",
        details={"amount": parsed.get("next_amt")}
        if parsed.get("next_amt") is not None else {},
    )
