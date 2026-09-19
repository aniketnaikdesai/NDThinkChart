from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from data.models import Bar

# Seconds per timeframe
TIMEFRAME_SECONDS: Dict[str, int] = {
    "5 secs":  5,
    "1 min":   60,
    "5 mins":  300,
    "15 mins": 900,
    "1 hour":  3600,
    "4 hours": 14400,
    "1 day":   86400,
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


def _period_start(ts: int, seconds: int) -> int:
    """Floor ts down to the nearest period boundary."""
    return (ts // seconds) * seconds


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

    def push(self, ts: int, o: float, h: float, l: float, c: float, vol: float):
        """Feed one 5-second bar from IBKR into the aggregator.

        Deduplication guard: if the same timestamp has already been pushed
        (e.g. after a reconnect replay), the bar is skipped.
        """
        if self._last_pushed_ts is not None and ts <= self._last_pushed_ts:
            return  # skip duplicate / stale bar from replay
        ps = _period_start(ts, self._period_seconds)
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
