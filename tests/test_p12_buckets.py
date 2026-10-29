"""P12-T2: 30-minute bucketing — TIMEFRAME_SECONDS 1800 key, DST-fold half-hour
boundaries, and live forming-bar parity (D52.2 / AC-D52.2).

Red-first design: every case resolves the period through the production path
(``TIMEFRAME_SECONDS["30 mins"]`` / ``BarAggregator("30 mins")``). Pre-fix the
unknown timeframe falls back to the 300 s grid (KeyError on the direct lookup),
so T21 fails on the key, T22 fails on off-half-hour samples, and T23 fails
because the forming tick lands in a 5-minute bucket.
"""

from datetime import datetime, timedelta

import pytest

from data.bar_aggregator import (
    TIMEFRAME_SECONDS,
    BarAggregator,
    _CALENDAR_BUCKETED_TIMEFRAMES,
    _ET_ANCHORED_TIMEFRAMES,
)

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

# Pre-existing contract: the nine keys (with values) plus both frozensets are
# byte-identical after P12-T2; only the 1800 key is added.
_EXPECTED_EXISTING = {
    "5 secs": 5,
    "1 min": 60,
    "5 mins": 300,
    "15 mins": 900,
    "1 hour": 3600,
    "4 hours": 14400,
    "1 day": 86400,
    "1 week": 604800,
    "1 month": 2592000,
}


def _et_ts(year: int, month: int, day: int, hour: int, minute: int) -> int:
    """Unix ts for an unambiguous ET wall time."""
    return int(datetime(year, month, day, hour, minute, tzinfo=_EASTERN).timestamp())


class TestThirtyMinsKey:
    """P12-T2-T21: TIMEFRAME_SECONDS maps 30 mins -> 1800; existing surface intact."""

    def test_30_mins_is_1800(self):
        assert TIMEFRAME_SECONDS["30 mins"] == 1800

    def test_nine_existing_keys_unchanged(self):
        for key, seconds in _EXPECTED_EXISTING.items():
            assert TIMEFRAME_SECONDS[key] == seconds
        assert len(TIMEFRAME_SECONDS) == 10

    def test_anchor_sets_unchanged(self):
        assert _ET_ANCHORED_TIMEFRAMES == frozenset({"1 day", "4 hours"})
        assert _CALENDAR_BUCKETED_TIMEFRAMES == frozenset({"1 week", "1 month"})


# Fall-back Sundays (DST ends 02:00 EDT -> 01:00 EST) parametrizing the fold.
_FOLD_SUNDAYS = [
    (2024, 11, 3),
    (2025, 11, 2),
    (2026, 11, 1),
]


class TestHalfHourBucketsAcrossFold:
    """P12-T2-T22: buckets open on ET clock half-hours across a DST fold."""

    @pytest.mark.parametrize("year,month,day", _FOLD_SUNDAYS)
    def test_every_bucket_starts_on_et_half_hour(self, year, month, day):
        agg = BarAggregator("TEST", "30 mins")
        sunday = datetime(year, month, day).date()
        saturday = sunday - timedelta(days=1)
        monday = sunday + timedelta(days=2)
        start = int(
            datetime(
                saturday.year, saturday.month, saturday.day, tzinfo=_EASTERN
            ).timestamp()
        )
        end = int(
            datetime(
                monday.year, monday.month, monday.day, tzinfo=_EASTERN
            ).timestamp()
        )
        # 5-minute sampling forces off-half-hour timestamps that a 300 s
        # fallback grid would leave on non-half-hour starts (red pre-fix).
        for ts in range(start, end, 300):
            bs = agg.period_start(ts)
            assert bs <= ts < bs + 1800
            et = datetime.fromtimestamp(bs, tz=_EASTERN)
            assert (et.minute, et.second, et.microsecond) in (
                (0, 0, 0),
                (30, 0, 0),
            ), f"bucket start {et.isoformat()} not on an ET half-hour"

    @pytest.mark.parametrize("year,month,day", _FOLD_SUNDAYS)
    def test_0930_rth_open_is_a_boundary(self, year, month, day):
        agg = BarAggregator("TEST", "30 mins")
        sunday = datetime(year, month, day).date()
        # Nearest trading days around the fold weekend: Friday before, Monday after.
        friday = sunday - timedelta(days=2)
        monday = sunday + timedelta(days=1)
        for session in (friday, monday):
            ts = _et_ts(session.year, session.month, session.day, 9, 30)
            assert agg.period_start(ts) == ts


class TestFormingBarJoinsCurrentHalfHour:
    """P12-T2-T23: the live forming bar aggregates into the current half-hour."""

    def test_forming_tick_joins_historical_half_hour(self):
        agg = BarAggregator("TEST", "30 mins")
        # Historical bars for the 09:30-10:00 ET half-hour (regular session day).
        day = (2025, 10, 15)
        historical = [_et_ts(*day, 9, 30) + k * 300 for k in range(6)]
        for ts in historical:
            agg.push(ts, o=100.0, h=101.0, l=99.0, c=100.5, vol=10.0)
        bucket = agg.period_start(historical[0])
        assert bucket == _et_ts(*day, 9, 30)
        # A live forming tick late in the same half-hour joins that bucket
        # (pre-fix it opens a 5-minute bucket at 09:55).
        forming_ts = _et_ts(*day, 9, 59) + 55
        assert agg.period_start(forming_ts) == bucket
        agg.push(forming_ts, o=100.5, h=102.0, l=100.0, c=101.5, vol=5.0)
        current = agg.current_bar()
        assert current is not None
        assert current.ts == bucket
