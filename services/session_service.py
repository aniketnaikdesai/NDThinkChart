"""Pure service for RTH/ETH session band computation.

Computes pre-market 04:00-09:30 ET and post-market 16:00-20:00 ET intervals
intersected with the loaded data range. DST-aware via ZoneInfo.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict

from services.time_collapse_service import is_daily_or_coarser

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")


def _et_date(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=_EASTERN)


def _et_midnight(date_obj) -> datetime:
    return datetime(date_obj.year, date_obj.month, date_obj.day, tzinfo=_EASTERN)


def _ts_at_et(date_obj, hour: int, minute: int = 0) -> int:
    dt = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, tzinfo=_EASTERN)
    return int(dt.timestamp())


def session_bands(bars, timeframe: str) -> List[Dict]:
    """Return session bands for the loaded bars.

    Args:
        bars: list of Bar with .ts
        timeframe: timeframe string (e.g. "5 mins", "1 day")

    Returns:
        list of dicts {kind: "pre"|"post", start_ts: int, end_ts: int}
        where pre is 04:00-09:30 ET and post is 16:00-20:00 ET, clipped to
        [t_min, t_max] of the bars.

        Returns [] for daily-and-coarser timeframes (S-P8-4) or bars empty.
    """
    if is_daily_or_coarser(timeframe):
        return []
    if not bars:
        return []
    # Determine range
    try:
        t_min = min(b.ts for b in bars)
        t_max = max(b.ts for b in bars)
    except Exception:
        return []

    start_date = _et_date(t_min).date()
    end_date = _et_date(t_max).date()

    bands: List[Dict] = []
    cur = start_date
    while cur <= end_date:
        pre_start = _ts_at_et(cur, 4, 0)
        pre_end = _ts_at_et(cur, 9, 30)
        post_start = _ts_at_et(cur, 16, 0)
        post_end = _ts_at_et(cur, 20, 0)

        # Pre band intersect [t_min, t_max]
        s = max(pre_start, t_min)
        e = min(pre_end, t_max)
        # Only include if interval has positive length (end > start)
        # If t_max exactly equals pre_end, interval length zero -> exclude? But spec says pre is [04:00,09:30) so 09:30 not included.
        # We keep strict >; test for clipping will check no band extends outside.
        if e > s:
            bands.append({"kind": "pre", "start_ts": s, "end_ts": e})
        s = max(post_start, t_min)
        e = min(post_end, t_max)
        if e > s:
            bands.append({"kind": "post", "start_ts": s, "end_ts": e})

        cur += timedelta(days=1)

    # Sort by start
    bands.sort(key=lambda b: b["start_ts"])
    return bands


def session_bands_for_range(t_min: int, t_max: int, timeframe: str) -> List[Dict]:
    """Helper taking explicit range."""
    if is_daily_or_coarser(timeframe):
        return []
    if t_max < t_min:
        return []
    # fake bars
    class _Fake:
        def __init__(self, ts):
            self.ts = ts
    return session_bands([_Fake(t_min), _Fake(t_max)], timeframe)
