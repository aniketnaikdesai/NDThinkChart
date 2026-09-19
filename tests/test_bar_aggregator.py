"""Tests for data/bar_aggregator.py — 5-second bars rolled into wider candles."""

import pytest

from data.bar_aggregator import BarAggregator, TIMEFRAME_SECONDS, _period_start


@pytest.fixture
def collected():
    """Capture (bar, is_new) tuples from an aggregator."""
    data = []

    def cb(bar, is_new):
        data.append((bar, is_new))

    return data, cb


class TestPeriodStart:
    def test_floors_to_boundary(self):
        assert _period_start(65, 60) == 60
        assert _period_start(300, 300) == 300
        assert _period_start(890, 300) == 600


class TestOneMinuteRollup:
    def test_boundary_bar_makes_two_candles(self, collected):
        data, cb = collected
        agg = BarAggregator("TEST", "1 min", on_bar_update=cb)
        for i in range(13):  # ts 0..60 → two one-minute periods
            agg.push(i * 5, o=float(i), h=float(i), l=float(i), c=float(i), vol=10.0)

        # first push opens candle 1 (is_new True), bar at ts=60 opens candle 2
        new_count = sum(1 for _bar, is_new in data if is_new)
        assert new_count == 2
        assert len(data) == 13  # one callback per push
        assert data[-1][0].ts == 60
        assert data[-1][1] is True

    def test_merge_semantics(self, collected):
        data, cb = collected
        agg = BarAggregator("TEST", "1 min", on_bar_update=cb)
        agg.push(0, o=5.0, h=6.0, l=4.0, c=5.0, vol=10.0)
        agg.push(5, o=5.0, h=7.0, l=3.0, c=6.0, vol=5.0)

        last_bar, _ = data[-1]
        assert last_bar.open == 5.0
        assert last_bar.high == 7.0
        assert last_bar.low == 3.0
        assert last_bar.close == 6.0
        assert last_bar.volume == 15.0
        assert last_bar.ts == 0

    def test_current_bar_partial(self):
        agg = BarAggregator("TEST", "1 min")
        assert agg.current_bar() is None
        agg.push(0, 1.0, 1.0, 1.0, 1.0, 10.0)
        cur = agg.current_bar()
        assert cur is not None
        assert cur.ts == 0
        assert cur.volume == 10.0


class TestFiveMinuteBoundary:
    def test_rollover_emits_new_candle(self, collected):
        data, cb = collected
        agg = BarAggregator("TEST", "5 mins", on_bar_update=cb)
        agg.push(0, 1, 1, 1, 1, 10)
        agg.push(295, 2, 2, 2, 2, 10)
        assert data[-1][1] is False
        agg.push(300, 3, 3, 3, 3, 10)
        assert data[-1][1] is True
        assert data[-1][0].ts == 300

    def test_bars_across_period_do_not_merge(self, collected):
        data, cb = collected
        agg = BarAggregator("TEST", "5 mins", on_bar_update=cb)
        agg.push(0, 1, 1, 1, 1, 10)
        agg.push(300, 2, 2, 2, 2, 10)
        assert data[-1][0].ts == 300
        assert data[-1][0].open == 2.0


class TestTimeframeConstants:
    def test_known_timeframes(self):
        assert TIMEFRAME_SECONDS["5 secs"] == 5
        assert TIMEFRAME_SECONDS["1 min"] == 60
        assert TIMEFRAME_SECONDS["5 mins"] == 300
        assert TIMEFRAME_SECONDS["15 mins"] == 900
        assert TIMEFRAME_SECONDS["1 hour"] == 3600
        assert TIMEFRAME_SECONDS["4 hours"] == 14400
        assert TIMEFRAME_SECONDS["1 day"] == 86400