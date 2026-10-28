from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from data.models import Bar

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

# Seconds per timeframe
TIMEFRAME_SECONDS: Dict[str, int] = {
    "5 secs":  5,
    "1 min":   60,
    "5 mins":  300,
    "15 mins": 900,
    "1 hour":  3600,
    "4 hours": 14400,
    "1 day":   86400,
    # S-P8-2 nominal keys for fixed-seconds consumers only (A115). These are
    # never used for weekly/monthly bucketing — weeks anchor to Monday 00:00
    # ET and months to the calendar-month boundary (see below).
    "1 week":  604800,
    "1 month": 2592000,
}


@dataclass
class _AggState:
    """Accumulator for one open candle."""
    symbol: str
    timeframe: str
    period_start: int       # unix ts of the open of this candle
    open: float
    high: float
    low: float
    close: float
    volume: float


# D27.8: timeframes whose aggregation anchors to America/New_York wall time
# instead of the UTC-epoch grid. IBKR's historical daily series is ET
# session days, so the live forming bar must ts-match ET midnight (a UTC
# floor would split the ET session across two "daily" bars). The 4-hour
# grid is 00/04/08/12/16/20 ET.
#
# Spike note: IBKR's own 4h anchor could not be verified (no live TWS;
# docs inconclusive). Implemented per D27.8's ET prescription; revisit if
# live comparison shows a phase mismatch against IBKR's 4h history.
_ET_ANCHORED_TIMEFRAMES = frozenset({"1 day", "4 hours"})


def _et_period_start(ts: int, seconds: int) -> int:
    """Floor ts to the period grid anchored at America/New_York midnight."""
    et_midnight = int(
        datetime.fromtimestamp(ts, tz=_EASTERN)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    return et_midnight + ((ts - et_midnight) // seconds) * seconds


def _period_start(
    ts: int, seconds: int, timeframe: Optional[str] = None
) -> int:
    """Floor ts down to the nearest period boundary.

    ``timeframe`` selects the anchor: "1 day"/"4 hours" floor in
    America/New_York wall time (D27.8); everything else uses the
    UTC-epoch grid (unchanged).
    """
    if timeframe in _ET_ANCHORED_TIMEFRAMES:
        return _et_period_start(ts, seconds)
    return (ts // seconds) * seconds


# S-P8-2: calendar-anchored bucketing for the two coarse timeframes. Weeks
# and months are calendar concepts — a fixed-seconds grid would drift month
# ends (R94: 28–31-day months, February) — so these helpers sit BESIDE the
# existing fixed-seconds grid above, which is left byte-untouched.
def week_bucket_start(ts: int) -> int:
    """Start of the weekly bucket containing ``ts``: Monday 00:00 ET."""
    et = datetime.fromtimestamp(ts, tz=_EASTERN)
    monday = (et - timedelta(days=et.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int(monday.timestamp())


def month_bucket_start(ts: int) -> int:
    """Start of the monthly bucket containing ``ts``: month boundary ET."""
    et = datetime.fromtimestamp(ts, tz=_EASTERN)
    first = et.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(first.timestamp())


_CALENDAR_BUCKETED_TIMEFRAMES = frozenset({"1 week", "1 month"})


def _bucket_start(
    ts: int, seconds: int, timeframe: Optional[str] = None
) -> int:
    """Period start for any timeframe: calendar buckets for week/month,
    the existing fixed-seconds grid (``_period_start``) otherwise."""
    if timeframe in _CALENDAR_BUCKETED_TIMEFRAMES:
        if timeframe == "1 week":
            return week_bucket_start(ts)
        return month_bucket_start(ts)
    return _period_start(ts, seconds, timeframe)


class BarAggregator:
    """
    Rolls incoming IBKR 5-second real-time bars into any wider timeframe.

    Usage:
        agg = BarAggregator("AAPL", "5 mins", on_bar_update=my_callback)
        agg.push(ts, open, high, low, close, volume)

    Callbacks:
        on_bar_update(bar, is_new_candle)
            bar          – the current (possibly still open) Bar
            is_new_candle – True when the previous period just closed
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        on_bar_update: Optional[Callable[[Bar, bool], None]] = None,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self._period_seconds = TIMEFRAME_SECONDS.get(timeframe, 300)
        self._on_bar_update = on_bar_update
        self._state: Optional[_AggState] = None
        self._last_pushed_ts: Optional[int] = None

    def period_start(self, ts: int) -> int:
        """Start of the candle period containing ``ts`` (D27.9 priming)."""
        return _bucket_start(ts, self._period_seconds, self.timeframe)

    def push(self, ts: int, o: float, h: float, l: float, c: float, vol: float):
        """Feed one 5-second bar from IBKR into the aggregator.

        Deduplication guard: if the same timestamp has already been pushed
        (e.g. after a reconnect replay), the bar is skipped.
        """
        if self._last_pushed_ts is not None and ts <= self._last_pushed_ts:
            return  # skip duplicate / stale bar from replay
        ps = _bucket_start(ts, self._period_seconds, self.timeframe)
        is_new = False

        if self._state is None or ps != self._state.period_start:
            # New candle period — emit the previous candle first
            is_new = True
            self._state = _AggState(
                symbol=self.symbol,
                timeframe=self.timeframe,
                period_start=ps,
                open=o, high=h, low=l, close=c, volume=vol,
            )
        else:
            # Still within the same candle — merge
            self._state.high = max(self._state.high, h)
            self._state.low = min(self._state.low, l)
            self._state.close = c
            self._state.volume += vol

        if self._on_bar_update:
            bar = Bar(
                symbol=self._state.symbol,
                timeframe=self._state.timeframe,
                ts=self._state.period_start,
                open=self._state.open,
                high=self._state.high,
                low=self._state.low,
                close=self._state.close,
                volume=self._state.volume,
            )
            self._on_bar_update(bar, is_new)
        self._last_pushed_ts = ts

    def current_bar(self) -> Optional[Bar]:
        if self._state is None:
            return None
        return Bar(
            symbol=self._state.symbol,
            timeframe=self._state.timeframe,
            ts=self._state.period_start,
            open=self._state.open,
            high=self._state.high,
            low=self._state.low,
            close=self._state.close,
            volume=self._state.volume,
        )
