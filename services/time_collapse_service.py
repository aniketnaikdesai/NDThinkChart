"""Pure, Qt-free display-time collapse map for intraday charts (D21.4).

The D21.4 requirement is a **display-only** transform: on intraday timeframes the
empty space between trading sessions (overnight, weekend, holiday) must not be
plotted, while normal inter-bar spacing *within* a session is preserved and
genuine trading-session data holes stay visible (``AC-D21.4.1``/``AC-D21.4.4``).
``1 day`` is a no-op identity map (``AC-D21.4.2``). ``Bar.ts`` — the persisted
SQLite key — is never mutated.

The transform is a **piecewise-linear map from bar timestamp to a display-x**
coordinate. A gap between consecutive bars ``a < b`` is collapsed iff
``market_calendar.session_windows(a + bar_period, b, ext_hours)`` is empty.

Why the coverage adjustment (``a + bar_period`` rather than ``a``): bar
timestamps are period **starts** (``data/bar_aggregator.py``), so a bar at ``ts``
covers ``[ts, ts + bar_period)``. The last RTH bar of a session sits at 15:55 and
covers exactly to the 16:00 close (the last extended-hours bar at 19:55 covers to
20:00). Testing the raw ``[a, b]`` interval would let the closing session's own
window overlap the ordinary overnight/weekend/holiday gap and wrongly keep it.
Testing ``[a + bar_period, b]`` removes the last bar's own coverage, so the
ordinary between-session gap collapses while a within-session hole or a missing
trading session (session time strictly between ``a + bar_period`` and ``b``)
stays visible.

Public API:
    gap_is_non_trading(a, b, ext_hours, bar_period) -> bool
    build_collapse_map(bars, timeframe, ext_hours) -> TimeCollapseMap
    TimeCollapseMap.to_display(ts) -> int | float
    TimeCollapseMap.to_ts(x)      -> int | float
    TimeCollapseMap.x_values      -> list[int]
    TimeCollapseMap.is_identity   -> bool

No PyQt6/pyqtgraph/Qt import appears anywhere in this module; importing it needs
no ``QApplication``.
"""

from __future__ import annotations

from bisect import bisect_left
from typing import Dict, Iterable, List, Sequence, Tuple, Union

from data.bar_aggregator import TIMEFRAME_SECONDS
from services.market_calendar import session_windows

#: The only timeframe for which collapse is a no-op (one bar per trading day).
IDENTITY_TIMEFRAME = "1 day"

Number = Union[int, float]


def gap_is_non_trading(a: int, b: int, ext_hours: bool, bar_period: int) -> bool:
    """Return True iff the gap between consecutive bars ``a < b`` collapses.

    Collapse iff ``session_windows(a + bar_period, b, ext_hours)`` is empty, i.e.
    no trading-session window overlaps the span *after* accounting for the
    coverage of bar ``a`` (``[a, a + bar_period)``). Adjacent bars
    (``b == a + bar_period``) also return True but remove zero duration, so they
    are a no-op for :func:`build_collapse_map`.
    """
    if b <= a:
        # Not a forward gap; nothing to collapse.
        return False
    return not session_windows(a + bar_period, b, ext_hours)


def _bar_ts(bar) -> int:
    """Read a bar timestamp without copying or mutating the bar."""
    ts = getattr(bar, "ts", None)
    if ts is None:
        ts = bar
    return int(ts)


class TimeCollapseMap:
    """A piecewise-linear ts <-> display-x map that removes non-trading gaps.

    ``x_values[i]`` is the display-x of the ``i``-th input bar (input order).
    ``to_display`` maps an original bar timestamp to display-x; ``to_ts`` is its
    inverse. Exact bar timestamps round-trip exactly.
    """

    __slots__ = (
        "timeframe",
        "bar_period",
        "ext_hours",
        "is_identity",
        "x_values",
        "_ts_sorted",
        "_display_sorted",
        "_ts_to_display",
        "_display_to_ts",
    )

    def __init__(
        self,
        *,
        timeframe: str,
        bar_period: int,
        ext_hours: bool,
        is_identity: bool,
        x_values: List[int],
        ts_to_display: Dict[int, int],
        ts_sorted: Sequence[int],
        display_sorted: Sequence[int],
    ) -> None:
        self.timeframe = timeframe
        self.bar_period = bar_period
        self.ext_hours = ext_hours
        self.is_identity = is_identity
        self.x_values = list(x_values)
        self._ts_sorted = list(ts_sorted)
        self._display_sorted = list(display_sorted)
        self._ts_to_display = dict(ts_to_display)
        self._display_to_ts = {d: t for t, d in self._ts_to_display.items()}

    # -- mapping -----------------------------------------------------------
    def to_display(self, ts: Number) -> Number:
        """Map an original timestamp to its display-x coordinate."""
        if self.is_identity:
            return ts
        mapped = self._ts_to_display.get(ts)
        if mapped is not None:
            return mapped
        return self._interp(ts, self._ts_sorted, self._display_sorted)

    def to_ts(self, x: Number) -> Number:
        """Map a display-x coordinate back to the original timestamp."""
        if self.is_identity:
            return x
        mapped = self._display_to_ts.get(x)
        if mapped is not None:
            return mapped
        return self._interp(x, self._display_sorted, self._ts_sorted)

    @staticmethod
    def _interp(value: Number, src: Sequence[int], dst: Sequence[int]) -> Number:
        """Piecewise-linear interpolation (extrapolating with the end segment)."""
        n = len(src)
        if n == 0:
            return value
        if n == 1:
            return value + (dst[0] - src[0])
        idx = bisect_left(src, value)
        if idx <= 0:
            i0, i1 = 0, 1
        elif idx >= n:
            i0, i1 = n - 2, n - 1
        else:
            i0, i1 = idx - 1, idx
        x0, x1 = src[i0], src[i1]
        y0, y1 = dst[i0], dst[i1]
        if x1 == x0:
            return y0
        return y0 + (y1 - y0) * (value - x0) / (x1 - x0)

    def extend(self, ts: int) -> bool:
        """Append one bar timestamp at the tail (D28.4).

        Replicates the tail step of :func:`build_collapse_map` without a
        rebuild: the gap between the previous last bar and ``ts`` collapses
        iff it is non-trading time. Returns False (leaving the map
        untouched) when ``ts`` is not a forward extension — the caller
        falls back to a full rebuild.
        """
        ts = int(ts)
        if not self._ts_sorted or ts <= self._ts_sorted[-1]:
            return False
        if self.timeframe == IDENTITY_TIMEFRAME:
            # "1 day" is an identity map by construction (build never
            # collapses it) — the tail step is a plain append.
            self.x_values.append(ts)
            self._ts_sorted.append(ts)
            self._display_sorted.append(ts)
            self._ts_to_display[ts] = ts
            self._display_to_ts[ts] = ts
            return True
        prev_ts = self._ts_sorted[-1]
        prev_dx = self._display_sorted[-1]
        offset = prev_ts - prev_dx  # current collapsed offset
        uncovered = ts - (prev_ts + self.bar_period)
        if uncovered > 0 and gap_is_non_trading(
                prev_ts, ts, self.ext_hours, self.bar_period):
            offset += uncovered
            self.is_identity = False
        dx = ts - offset
        self.x_values.append(dx)
        self._ts_sorted.append(ts)
        self._display_sorted.append(dx)
        self._ts_to_display[ts] = dx
        self._display_to_ts[dx] = ts
        return True

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"TimeCollapseMap(timeframe={self.timeframe!r}, "
            f"bars={len(self.x_values)}, is_identity={self.is_identity})"
        )


def build_collapse_map(bars: Iterable, timeframe: str, ext_hours: bool) -> TimeCollapseMap:
    """Build the display-x collapse map for ``bars`` on ``timeframe``.

    ``bars`` is an iterable of objects exposing ``.ts`` (or plain ints). The
    input objects are only read — never mutated — and no bar is dropped: the
    returned ``x_values`` has exactly one entry per input bar, in input order.
    ``1 day`` yields the identity map.
    """
    bar_period = TIMEFRAME_SECONDS[timeframe]
    ts_seq = [_bar_ts(bar) for bar in bars]

    if timeframe == IDENTITY_TIMEFRAME:
        return TimeCollapseMap(
            timeframe=timeframe,
            bar_period=bar_period,
            ext_hours=ext_hours,
            is_identity=True,
            x_values=list(ts_seq),
            ts_to_display={ts: ts for ts in ts_seq},
            ts_sorted=sorted(set(ts_seq)),
            display_sorted=sorted(set(ts_seq)),
        )

    ordered = sorted(set(ts_seq))
    display_by_ts: Dict[int, int] = {}
    offset = 0
    collapsed_any = False
    prev_ts = None
    for ts in ordered:
        if prev_ts is not None:
            uncovered = ts - (prev_ts + bar_period)
            if uncovered > 0 and gap_is_non_trading(prev_ts, ts, ext_hours, bar_period):
                offset += uncovered
                collapsed_any = True
        display_by_ts[ts] = ts - offset
        prev_ts = ts

    ts_sorted = sorted(display_by_ts)
    display_sorted = [display_by_ts[t] for t in ts_sorted]
    x_values = [display_by_ts[ts] for ts in ts_seq]

    return TimeCollapseMap(
        timeframe=timeframe,
        bar_period=bar_period,
        ext_hours=ext_hours,
        is_identity=not collapsed_any,
        x_values=x_values,
        ts_to_display=display_by_ts,
        ts_sorted=ts_sorted,
        display_sorted=display_sorted,
    )
