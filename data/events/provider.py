"""D38 event-provider layer (38b.1): shared types + the EventProvider interface.

Corporate events only — earnings, dividends, splits. No economic calendar
(owner decision; AC-D38.4). Exactly one external source beyond IBKR is
approved: yfinance (owner decision 2026-10-13). No other external API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

# Event types. The corporate-events-only guard lives here: anything not in
# this tuple is rejected at the provider boundary (AC-D38.4).
EVENT_TYPES = ("earnings", "dividend", "split")


@dataclass
class Event:
    """One corporate event for chart markers + countdowns."""

    id: str                      # stable key for marker diffing (not the date)
    type: str                    # "earnings" | "dividend" | "split"
    symbol: str
    date: date                   # event date (ex-div for dividends)
    source: str                  # "ibkr" | "yfinance"
    details: dict = field(default_factory=dict)  # amount, estimate, surprise…

    def __post_init__(self):
        if self.type not in EVENT_TYPES:
            raise ValueError(f"non-corporate event type rejected: {self.type!r}")


class EventProvider(ABC):
    """One interface for all event sources — IBKR-first, yfinance-second."""

    @abstractmethod
    def get_events(self, symbol: str, start: date, end: date) -> list[Event]:
        """Return cached events for ``symbol`` in [start, end].

        Never raises to the UI: on source failure returns whatever the cache
        holds (possibly empty); the caller distinguishes "no events" from
        "source unavailable" via :meth:`unavailable`.
        """

    @abstractmethod
    def unavailable(self, symbol: str) -> bool:
        """True when the source cannot serve this symbol right now
        (outage/rate-limit with no fresh cache) — the UI shows the explicit
        "event data unavailable" state instead of an empty chart."""


def parse_ib_dividend_string(value: str) -> dict[str, Any]:
    """Defensively parse a tick-59 "IB Dividends" tickString.

    Documented shape is ``past12m,next12m,nextDate,nextAmt`` where nextDate
    is YYYYMMDD, but separators/fields vary by server — so: split on comma
    or semicolon, take fields positionally, and never raise. Returns a dict
    with any of ``past12m``, ``next12m``, ``next_date`` (a ``date`` or None),
    ``next_amt`` (float or None) that could be extracted.
    """
    out: dict[str, Any] = {
        "past12m": None, "next12m": None, "next_date": None, "next_amt": None,
    }
    if not value or not isinstance(value, str):
        return out
    sep = ";" if ";" in value else ","
    parts = [p.strip() for p in value.split(sep)]

    def _f(i):
        try:
            return float(parts[i]) if i < len(parts) and parts[i] else None
        except (ValueError, TypeError):
            return None

    out["past12m"] = _f(0)
    out["next12m"] = _f(1)
    if len(parts) > 2 and parts[2]:
        raw = parts[2].strip()
        try:
            out["next_date"] = date(int(raw[0:4]), int(raw[4:6]), int(raw[6:8]))
        except (ValueError, IndexError):
            out["next_date"] = None
    out["next_amt"] = _f(3)
    return out
