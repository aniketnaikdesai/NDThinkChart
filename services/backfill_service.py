"""Pure, Qt-free missing-span detection and chunked-request planner (D16).

This module is the decision layer behind historical-bar backfill. It answers two
questions without any UI, TWS or Qt dependency:

1. *Which trading sessions are missing?* — :func:`find_missing_spans` compares
   the cached bar timestamps against *now* at **trading-day presence** granularity
   (a trading day with zero cached bars is missing) **plus bar-period
   granularity for the trailing ``TRAILING_BAR_GRANULARITY_DAYS`` trading days**
   (D27.7): a day with *some* bars but an intraday hole (e.g. a stranded wave's
   partial day) yields spans covering the hole, so a later load repairs it.
   Adjacent missing trading days merge into one :class:`MissingSpan`. Weekends
   and US-equity holidays are genuine closures and are never reported as
   missing. An empty cache returns ``[]`` so the caller falls back to the
   configured fetch window.

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
from services.market_calendar import is_trading_day, session_windows

_EASTERN = ZoneInfo("America/New_York")

# Fallback timeframe mirroring BarAggregator / req_historical_data defaults.
_FALLBACK_TIMEFRAME = "5 mins"

# D27.7: how many trailing trading days get bar-period-granularity gap
# detection (vs day-presence). A stranded wave's partial day is always
# recent; older days keep the cheaper day-presence check. Configurable via
# the ``trailing_days`` parameter of :func:`find_missing_spans`.
TRAILING_BAR_GRANULARITY_DAYS = 5

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
    trailing_days: int = TRAILING_BAR_GRANULARITY_DAYS,
    ext_hours: bool = False,
) -> List[MissingSpan]:
    """Return the trading sessions missing between the cached series and *now*.

    Detection is **trading-day presence** — any trading day from the earliest
    cached day through *now*'s ET day with no cached bar is missing, and adjacent
    missing trading days merge into a single span (a weekend or holiday between
    two missing trading days does not split the span) — **plus bar-period
    granularity for the trailing ``trailing_days`` trading days** (D27.7): a
    day with *some* cached bars but an intraday hole (a stranded wave's partial
    day) yields spans covering the hole, so a later load repairs it. Genuine
    closures are never reported. An empty cache returns ``[]``.

    Bar-level detection is gap-based (it uses the cached timestamps, never
    assumed slot positions, so it is agnostic to bar anchoring): within each
    trailing day's session window, a gap of more than 1.5 bar periods between
    consecutive cached bars — or between a session edge and the nearest bar —
    is a missing span, capped at *now* so today's open session is never
    over-fetched. Days with zero cached bars are left to the day-presence
    pass. ``ext_hours`` selects the session window, matching the load's
    toggle. Daily (and larger) timeframes skip the bar-level pass: day
    presence is already bar granularity there.

    Choice note (D27.7): bar-period detection for trailing N days was picked
    over per-chunk completion records — it is stateless (no new table) and
    repairs any partial day regardless of how the wave stranded. Limitation:
    a gap IBKR genuinely has no bars for (trading halt, IPO morning) is
    re-probed on each load; the probe is one planner chunk and the cache
    dedups whatever returns.
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

    # Merge runs of consecutive *trading* days (holidays/weekends between them do
    # not break a run because they are absent from ``trading``).
    index = {day: i for i, day in enumerate(trading)}
    spans: List[MissingSpan] = []
    if missing:
        run_start = run_end = missing[0]
        for day in missing[1:]:
            if index[day] == index[run_end] + 1:
                run_end = day
            else:
                spans.append(_build_span(run_start, run_end, now_ts))
                run_start = run_end = day
        spans.append(_build_span(run_start, run_end, now_ts))

    spans.extend(
        _bar_level_missing_spans(
            ts_values, now_ts, timeframe, trailing_days, ext_hours
        )
    )
    return spans


def _bar_level_missing_spans(
    ts_values: List[int],
    now_ts: int,
    timeframe: str,
    trailing_days: int,
    ext_hours: bool,
) -> List[MissingSpan]:
    """D27.7: intraday holes in the trailing ``trailing_days`` trading days.

    Gap-based: for each trailing day with cached bars, a gap of more than 1.5
    bar periods between consecutive cached bars (or a session edge and the
    nearest bar) becomes a MissingSpan. See :func:`find_missing_spans`.
    """
    period = bar_period_seconds(timeframe)
    if period >= 86_400 or trailing_days <= 0:
        return []
    gap_threshold = period * 1.5

    now_day = _et_date(now_ts)
    days: List[date] = []
    day = now_day
    while len(days) < trailing_days:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)

    by_day: dict[date, List[int]] = {}
    for ts in ts_values:
        by_day.setdefault(_et_date(ts), []).append(ts)

    spans: List[MissingSpan] = []
    for day in days:
        day_ts = sorted(by_day.get(day, ()))
        if not day_ts:
            continue  # owned by the day-presence pass
        day_start = _et_day_start_ts(day)
        day_end = _et_day_start_ts(day + timedelta(days=1))
        for window in session_windows(day_start, day_end, ext_hours):
            ws, we = window["start_ts"], window["end_ts"]
            bound = min(we, now_ts)
            in_window = sorted(t for t in day_ts if ws <= t <= bound)
            if not in_window:
                continue
            # Leading edge: session start -> first bar.
            if in_window[0] - ws > gap_threshold:
                spans.append(MissingSpan(start_ts=ws, end_ts=in_window[0]))
            # Internal gaps between consecutive cached bars.
            for prev, cur in zip(in_window, in_window[1:]):
                if cur - prev > gap_threshold:
                    spans.append(MissingSpan(start_ts=prev, end_ts=cur))
            # Trailing edge: last bar -> session bound (capped at now).
            last = in_window[-1]
            if bound - (last + period) >= period:
                spans.append(MissingSpan(start_ts=last, end_ts=bound))
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
