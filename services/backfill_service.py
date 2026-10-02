"""Pure, Qt-free missing-span detection and chunked-request planner (D16).

This module is the decision layer behind historical-bar backfill. It answers two
questions without any UI, TWS or Qt dependency:

1. *Which trading sessions are missing?* — :func:`find_missing_spans` compares
   the cached bar timestamps against *now* at **trading-day presence** granularity
   (a trading day with zero cached bars is missing) and merges adjacent missing
   trading days into one :class:`MissingSpan`. Weekends and US-equity holidays
   are genuine closures and are never reported as missing. An empty cache returns
   ``[]`` so the caller falls back to the configured fetch window.

2. *How do we request them?* — :func:`plan_requests` turns each missing span into
   one or more :class:`RequestPlan` objects, chunking by the timeframe's
   ``TIMEFRAME_CONFIG`` duration, **newest chunk first**, with the ``endDateTime``
   anchor in the IBKR UTC-hyphenated ``yyyyMMdd-HH:mm:ss`` format.

Public API:
    bar_period_seconds(timeframe)                    -> int
    find_missing_spans(cached_ts, now_ts, timeframe) -> list[MissingSpan]
    plan_requests(missing_spans, timeframe)          -> list[RequestPlan]

No PyQt6/pyqtgraph/Qt import appears anywhere in this module; importing it needs
no ``QApplication`` and opens no IBKR connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, List

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.market_data import TIMEFRAME_CONFIG
from services.market_calendar import is_trading_day

_EASTERN = ZoneInfo("America/New_York")

# Fallback timeframe mirroring BarAggregator / req_historical_data defaults.
_FALLBACK_TIMEFRAME = "5 mins"

# IBKR durationStr unit -> seconds. Mirrors IBKR's duration vocabulary so a
# configured duration ("1 D", "5 D", "10 D", "30 D", "1 Y") can be used as the
# chunk step.
_DURATION_UNIT_SECONDS = {
    "S": 1,
    "D": 86_400,
    "W": 7 * 86_400,
    "M": 30 * 86_400,
    "Y": 365 * 86_400,
}

__all__ = [
    "MissingSpan",
    "RequestPlan",
    "bar_period_seconds",
    "find_missing_spans",
    "plan_requests",
]


@dataclass(frozen=True)
class MissingSpan:
    """An inclusive trading-session span that has no cached bars.

    ``start_ts`` is the ET midnight at the start of the first missing trading
    day; ``end_ts`` is the end of the last missing trading day (the following ET
    midnight, or ``now_ts`` when the tail reaches into *now*'s day).
    """

    start_ts: int
    end_ts: int


@dataclass(frozen=True)
class RequestPlan:
    """One historical request derived from a :class:`MissingSpan` chunk."""

    endDateTime: str
    duration: str
    bar_size: str
    span_start_ts: int
    span_end_ts: int


# ---------------------------------------------------------------------------
# Timeframe / duration helpers
# ---------------------------------------------------------------------------
def bar_period_seconds(timeframe: str) -> int:
    """Return the per-bar period in seconds for ``timeframe``.

    Source of truth is :data:`data.bar_aggregator.TIMEFRAME_SECONDS`; unknown
    timeframes fall back to the same ``5 mins`` default used elsewhere.
    """
    return TIMEFRAME_SECONDS.get(timeframe, TIMEFRAME_SECONDS[_FALLBACK_TIMEFRAME])


def _duration_to_seconds(duration: str) -> int:
    """Convert an IBKR ``durationStr`` (e.g. ``"5 D"``, ``"1 Y"``) to seconds."""
    token = (duration or "").strip().upper()
    if not token:
        raise ValueError("empty duration")
    if token[-1] in _DURATION_UNIT_SECONDS:
        magnitude = token[:-1].strip()
        if magnitude.isdigit():
            return int(magnitude) * _DURATION_UNIT_SECONDS[token[-1]]
    if token.isdigit():  # bare seconds
        return int(token)
    raise ValueError(f"unsupported duration: {duration!r}")


def _format_end_date(ts: int) -> str:
    """Format a unix ts as IBKR ``endDateTime`` ``yyyyMMdd-HH:mm:ss`` in UTC.

    Factored out of ``ui.main_window._ibkr_end_date`` so this module stays
    Qt-free while producing the identical anchor format.
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d-%H:%M:%S")


# ---------------------------------------------------------------------------
# ET calendar helpers
# ---------------------------------------------------------------------------
def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=_EASTERN).date()


def _et_day_start_ts(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=_EASTERN).timestamp())


def _trading_days(start_day: date, end_day: date) -> List[date]:
    """Return trading days in ``[start_day, end_day]`` ascending."""
    days: List[date] = []
    current = start_day
    while current <= end_day:
        if is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def _build_span(first_day: date, last_day: date, now_ts: int) -> MissingSpan:
    start_ts = _et_day_start_ts(first_day)
    end_ts = min(now_ts, _et_day_start_ts(last_day + timedelta(days=1)))
    if end_ts < start_ts:
        end_ts = start_ts
    return MissingSpan(start_ts=start_ts, end_ts=end_ts)


# ---------------------------------------------------------------------------
# Missing-span detection
# ---------------------------------------------------------------------------
def find_missing_spans(
    cached_ts: Iterable[int],
    now_ts: int,
    timeframe: str,
) -> List[MissingSpan]:
    """Return the trading sessions missing between the cached series and *now*.

    Detection is **trading-day presence**: any trading day from the earliest
    cached day through *now*'s ET day with no cached bar is missing, and adjacent
    missing trading days merge into a single span (a weekend or holiday between
    two missing trading days does not split the span). Genuine closures are never
    reported. An empty cache returns ``[]``.

    ``timeframe`` is accepted for API symmetry with the planner; detection is
    intentionally day granularity so it behaves identically for every timeframe.
    """
    ts_values = list(cached_ts)
    if not ts_values:
        return []

    present_days = {_et_date(ts) for ts in ts_values}
    first_day = min(present_days)
    now_day = _et_date(now_ts)
    if now_day < first_day:
        return []

    trading = _trading_days(first_day, now_day)
    missing = [day for day in trading if day not in present_days]
    if not missing:
        return []

    # Merge runs of consecutive *trading* days (holidays/weekends between them do
    # not break a run because they are absent from ``trading``).
    index = {day: i for i, day in enumerate(trading)}
    spans: List[MissingSpan] = []
    run_start = run_end = missing[0]
    for day in missing[1:]:
        if index[day] == index[run_end] + 1:
            run_end = day
        else:
            spans.append(_build_span(run_start, run_end, now_ts))
            run_start = run_end = day
    spans.append(_build_span(run_start, run_end, now_ts))
    return spans


# ---------------------------------------------------------------------------
# Request planning
# ---------------------------------------------------------------------------
def plan_requests(
    missing_spans: Iterable[MissingSpan],
    timeframe: str,
) -> List[RequestPlan]:
    """Chunk missing spans into newest-first historical requests.

    Each span is split into ``ceil(span_seconds / configured_duration)`` chunks;
    the newest chunk is anchored at the span end and each successive anchor steps
    back by exactly one configured duration. Every plan carries the timeframe's
    ``bar_size``/``duration`` and the span it was derived from.
    """
    cfg = TIMEFRAME_CONFIG.get(timeframe, TIMEFRAME_CONFIG[_FALLBACK_TIMEFRAME])
    duration = cfg["duration"]
    bar_size = cfg["bar_size"]
    chunk_seconds = _duration_to_seconds(duration)

    plans: List[RequestPlan] = []
    for span in sorted(missing_spans, key=lambda s: s.end_ts, reverse=True):
        span_seconds = span.end_ts - span.start_ts
        if span_seconds < 0:
            continue
        chunk_count = max(1, -(-span_seconds // chunk_seconds))
        anchor = span.end_ts
        for _ in range(chunk_count):
            plans.append(
                RequestPlan(
                    endDateTime=_format_end_date(anchor),
                    duration=duration,
                    bar_size=bar_size,
                    span_start_ts=span.start_ts,
                    span_end_ts=span.end_ts,
                )
            )
            anchor -= chunk_seconds
    return plans
