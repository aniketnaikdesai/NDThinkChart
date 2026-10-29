"""P12-T5 / D52.4 — intraday mode parity for ``30 mins``.

Verifies ``30 mins`` keeps the intraday contract (the D48 weekly/monthly
precedent with the intraday polarity inverted):

* T51 — RTH and ETH loads of ``30 mins`` return their mode's own bars
  (not identical sets) under distinct mode-aware cache keys.
* T52 — session bands and the D21.4 collapse map apply to ``30 mins``
  exactly as for the other intraday timeframes (1800 s stays intraday
  under the shared daily-or-coarser predicate), with ``session_regions``
  parity against ``15 mins``.
"""

from __future__ import annotations

from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.models import Bar
from services.chart_model import plotted_index_rows
from services.session_service import session_bands
from services.time_collapse_service import (
    build_collapse_map,
    is_daily_or_coarser,
)
from ui.lwc_view import session_regions

EASTERN = ZoneInfo("America/New_York")

#: Monday 2026-11-02 (a trading day per the D48 precedent).
DAY_ONE = datetime(2026, 11, 2, tzinfo=EASTERN).date()
#: Friday 2026-10-30 — with DAY_ONE (Mon 2026-11-02) spans a weekend,
#: so the D21.4 collapse map has a genuine non-trading gap under both modes.
DAY_FRI = datetime(2026, 10, 30, tzinfo=EASTERN).date()

TIMEFRAME = "30 mins"


def _ts(day, hour: int, minute: int = 0) -> int:
    return int(datetime(day.year, day.month, day.day,
                        hour, minute, tzinfo=EASTERN).timestamp())


def _bar(symbol: str, timeframe: str, ts: int, price: float = 100.0) -> Bar:
    return Bar(
        symbol=symbol, timeframe=timeframe, ts=ts,
        open=price, high=price + 0.5, low=price - 0.5,
        close=price, volume=1000,
    )


def _ts_set(bars) -> set:
    return {int(b.ts) for b in bars}


# ---------------------------------------------------------------------------
# P12-T5-T51 — mode-split: RTH/ETH loads return their mode's own bars
# ---------------------------------------------------------------------------
def test_p12_t5_t51_intraday_mode_split():
    """RTH and ETH ``30 mins`` loads return mode-distinct bar sets."""
    symbol = "P12T5MODE30M"
    # Pre-market 08:00 ET bar: inside the ETH session, outside RTH.
    pre_ts = _ts(DAY_ONE, 8, 0)
    rth_ts = [_ts(DAY_ONE, 9, 30), _ts(DAY_ONE, 10, 0), _ts(DAY_ONE, 10, 30)]

    rth_bars = [_bar(symbol, TIMEFRAME, ts, 100.0 + i)
                for i, ts in enumerate(rth_ts)]
    eth_bars = ([_bar(symbol, TIMEFRAME, pre_ts, 99.0)]
                + [_bar(symbol, TIMEFRAME, ts, 100.0 + i)
                    for i, ts in enumerate(rth_ts)])

    BarCache.save_bars(rth_bars, ext_hours=False)
    BarCache.save_bars(eth_bars, ext_hours=True)

    loaded_rth = BarCache.get_bars(symbol, TIMEFRAME, ext_hours=False)
    loaded_eth = BarCache.get_bars(symbol, TIMEFRAME, ext_hours=True)

    # Each mode reads back its own bars under its own key.
    assert _ts_set(loaded_rth) == set(rth_ts)
    assert _ts_set(loaded_eth) == {pre_ts} | set(rth_ts)
    # The sets are mode-distinct — not identical, not a shared key.
    assert _ts_set(loaded_rth) != _ts_set(loaded_eth)
    assert len(loaded_eth) == len(loaded_rth) + 1

    # The plotted filter honors the mode split: the pre-market bar plots
    # under ETH and is filtered under RTH.
    assert plotted_index_rows(loaded_eth, TIMEFRAME, True) == list(
        range(len(loaded_eth)))
    rth_plotted = plotted_index_rows(loaded_eth, TIMEFRAME, False)
    assert len(rth_plotted) == len(loaded_eth) - 1
    assert pre_ts not in {int(loaded_eth[i].ts) for i in rth_plotted}


# ---------------------------------------------------------------------------
# P12-T5-T52 — bands + collapse apply; predicate + regions parity
# ---------------------------------------------------------------------------
def test_p12_t5_t52_bands_collapse_parity():
    """Bands and collapse apply to ``30 mins`` as intraday; predicate holds."""
    # 1800 s stays intraday under the shared predicate.
    assert is_daily_or_coarser(TIMEFRAME) is False
    assert is_daily_or_coarser("15 mins") is False
    # Contrast: daily-and-coarser stays canonical.
    assert is_daily_or_coarser("1 day") is True

    # Span covering pre-market Friday through post-market Monday (across
    # a weekend). The last Friday bar covers exactly to the 20:00 ET ETH
    # close and the first Monday bar opens at 04:00 ET, so the weekend gap
    # is non-trading time under both modes and the D21.4 map collapses it.
    span_ts = [
        _ts(DAY_FRI, 8, 0), _ts(DAY_FRI, 8, 30),
        _ts(DAY_FRI, 9, 30), _ts(DAY_FRI, 10, 0),
        _ts(DAY_FRI, 15, 0), _ts(DAY_FRI, 15, 30),
        _ts(DAY_FRI, 19, 0), _ts(DAY_FRI, 19, 30),
        _ts(DAY_ONE, 4, 0), _ts(DAY_ONE, 4, 30),
        _ts(DAY_ONE, 9, 30),
        _ts(DAY_ONE, 16, 0), _ts(DAY_ONE, 16, 30),
    ]
    bars = [_bar("P12T5BANDS", TIMEFRAME, ts, 100.0 + i)
            for i, ts in enumerate(span_ts)]

    # Bands apply (non-empty, both session kinds present).
    bands = session_bands(bars, TIMEFRAME)
    assert bands, f"{TIMEFRAME}: expected session bands, got none"
    assert {b["kind"] for b in bands} == {"pre", "post"}
    # Daily-and-coarser stays band-free under the same span.
    assert session_bands(bars, "1 day") == []

    # The D21.4 collapse map applies: the overnight gap collapses, so the
    # map is not the identity, and no bar is dropped.
    cmap = build_collapse_map(bars, TIMEFRAME, ext_hours=False)
    assert cmap.is_identity is False
    assert len(cmap.x_values) == len(bars)
    cmap_eth = build_collapse_map(bars, TIMEFRAME, ext_hours=True)
    assert cmap_eth.is_identity is False
    assert len(cmap_eth.x_values) == len(bars)

    # session_regions parity with 15 mins over the same span: identical
    # kind sequence, non-empty under extended hours, empty without.
    bars_15 = [_bar("P12T5BANDS15", "15 mins", ts, 100.0 + i)
               for i, ts in enumerate(span_ts)]
    regions_30 = session_regions(bars, bars, TIMEFRAME, True)
    regions_15 = session_regions(bars_15, bars_15, "15 mins", True)
    assert regions_30, "30 mins: expected session regions under ETH"
    assert regions_15, "15 mins: expected session regions under ETH"
    assert [r["kind"] for r in regions_30] == [r["kind"] for r in regions_15]
    assert session_regions(bars, bars, TIMEFRAME, False) == []
