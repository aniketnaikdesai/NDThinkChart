"""Pure, Qt-free ET trading-day / US-equity holiday calendar.

This module owns the definition of when the US equity market is *open*. It is a
leaf dependency for the D16 backfill planner: it decides which calendar days are
trading sessions so that weekends and genuine market holidays stay empty while
missing trading days are backfilled.

Holidays are computed **by rule** (fixed-date, nth-weekday and Good Friday) for
the requested year on the fly, in ``America/New_York``. There is deliberately no
per-year data table, so any future year is handled without a code edit.

Public API:
    is_trading_day(value)                  -> bool
    trading_days(start_ts, end_ts)         -> list[datetime.date]
    session_windows(start_ts, end_ts, ext_hours) -> list[dict]

No PyQt6/pyqtgraph/Qt import appears anywhere in this module; importing it needs
no ``QApplication``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Dict, List

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

# ET session boundaries (local clock time). The extended-hours session is the
# union of pre-market (04:00-09:30), regular hours (09:30-16:00) and post-market
# (16:00-20:00).
_EXT_OPEN = (4, 0)
_EXT_CLOSE = (20, 0)
_RTH_OPEN = (9, 30)
_RTH_CLOSE = (16, 0)


# ---------------------------------------------------------------------------
# Calendar primitives
# ---------------------------------------------------------------------------
def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the ``n``-th ``weekday`` (0=Monday) of ``month`` in ``year``."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last ``weekday`` (0=Monday) of ``month`` in ``year``."""
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    offset = (last.weekday() - weekday) % 7
    return last - timedelta(days=offset)


def _easter_sunday(year: int) -> date:
    """Gregorian Easter Sunday (Meeus/Jones/Butcher anonymous algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 - algorithm notation
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _observed(fixed: date) -> date:
    """Apply the US equity observed-day convention to a fixed-date holiday.

    A Saturday holiday is observed on the preceding Friday and a Sunday holiday
    on the following Monday; a weekday holiday is observed on the day itself.
    """
    if fixed.weekday() == 5:  # Saturday
        return fixed - timedelta(days=1)
    if fixed.weekday() == 6:  # Sunday
        return fixed + timedelta(days=1)
    return fixed


# Juneteenth National Independence Day became a US equity market holiday in
# 2022 (NYSE/Nasdaq first observed Monday 2022-06-20). It is a fixed-date
# holiday from that year onward; this is a start year, not a per-year date list.
_JUNETEENTH_FIRST_YEAR = 2022


@lru_cache(maxsize=None)
def _holidays_for_year(year: int) -> set[date]:
    """Return the observed ET market-closure dates belonging to ``year``.

    New Year's Day carries the NYSE Rule 7.2 year-end accounting-period
    exception (ESC-023 / AC-D16.7): the usual Saturday->preceding-Friday
    observed shift does **not** apply when that Friday is the last trading day
    of the year, so a Saturday Jan 1 produces no closure at all (Dec 31 stays a
    trading day) and no substitute closure is created. Every other fixed-date
    holiday keeps the ordinary observed shift. As a result this set never
    contains a date outside ``year``.
    """
    closures: set[date] = set()

    # --- fixed-date holidays (observed-day shifts applied) ---
    new_year = date(year, 1, 1)
    # NYSE Rule 7.2 year-end exception: a Saturday New Year's Day is not pulled
    # back onto the preceding Friday (Dec 31), which remains an open session.
    # A Sunday New Year's Day is still observed on the following Monday.
    if new_year.weekday() != 5:  # not Saturday
        closures.add(_observed(new_year))
    if year >= _JUNETEENTH_FIRST_YEAR:
        closures.add(_observed(date(year, 6, 19)))  # Juneteenth
    closures.add(_observed(date(year, 7, 4)))   # Independence Day
    closures.add(_observed(date(year, 12, 25)))  # Christmas Day

    # --- nth-weekday holidays (always weekdays, no observed shift) ---
    closures.add(_nth_weekday(year, 1, 0, 3))   # MLK Jr. Day - 3rd Mon Jan
    closures.add(_nth_weekday(year, 2, 0, 3))   # Presidents' Day - 3rd Mon Feb
    closures.add(_last_weekday(year, 5, 0))     # Memorial Day - last Mon May
    closures.add(_nth_weekday(year, 9, 0, 1))   # Labor Day - 1st Mon Sep
    closures.add(_nth_weekday(year, 11, 3, 4))  # Thanksgiving - 4th Thu Nov

    # --- Good Friday (Friday before Easter Sunday) ---
    closures.add(_easter_sunday(year) - timedelta(days=2))

    return closures


def _as_date(value) -> date:
    """Normalise a ``date``/``datetime`` to a plain ``date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"expected date or datetime, got {type(value)!r}")


def is_trading_day(value) -> bool:
    """Return True if ``value`` is a US equity trading day in ET.

    ``value`` may be a ``datetime.date`` or ``datetime.datetime`` (the tz-aware
    or naive wall date is used as-is; callers passing timestamps should convert
    to the ET date first, as ``trading_days`` does).
    """
    d = _as_date(value)
    if d.weekday() >= 5:  # Saturday / Sunday
        return False
    # Holiday closures are keyed by year; union adjacent years defensively so a
    # rule change that ever lands a closure across a year boundary still counts.
    for year in (d.year - 1, d.year, d.year + 1):
        if d in _holidays_for_year(year):
            return False
    return True


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=_EASTERN).date()


def _ts_at_et(day: date, hour: int, minute: int) -> int:
    return int(datetime(day.year, day.month, day.day, hour, minute, tzinfo=_EASTERN).timestamp())


def trading_days(start_ts: int, end_ts: int) -> List[date]:
    """Return the ET trading days in the inclusive range, ascending.

    Both endpoints are interpreted as instants and mapped to their ET calendar
    date; the returned list contains plain ``datetime.date`` objects. Weekends
    and US-equity holidays are excluded. Returns ``[]`` when ``end_ts < start_ts``.
    """
    if end_ts < start_ts:
        return []
    start = _et_date(start_ts)
    end = _et_date(end_ts)
    days: List[date] = []
    current = start
    while current <= end:
        if is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def session_windows(start_ts: int, end_ts: int, ext_hours: bool) -> List[Dict[str, int]]:
    """Return one intraday window per ET trading day, clipped to the range.

    Each window is ``{"start_ts": int, "end_ts": int}`` with unix seconds. The
    window is 04:00-20:00 ET when ``ext_hours`` is True, otherwise 09:30-16:00
    ET. Windows with no positive overlap with ``[start_ts, end_ts]`` are omitted,
    and non-trading days (weekend/holiday) produce no window.
    """
    if end_ts < start_ts:
        return []
    open_h, open_m = _EXT_OPEN if ext_hours else _RTH_OPEN
    close_h, close_m = _EXT_CLOSE if ext_hours else _RTH_CLOSE

    windows: List[Dict[str, int]] = []
    for day in trading_days(start_ts, end_ts):
        day_open = _ts_at_et(day, open_h, open_m)
        day_close = _ts_at_et(day, close_h, close_m)
        clipped_start = max(day_open, start_ts)
        clipped_end = min(day_close, end_ts)
        if clipped_end > clipped_start:
            windows.append({"start_ts": clipped_start, "end_ts": clipped_end})
    return windows
