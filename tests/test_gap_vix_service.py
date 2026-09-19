"""Tests for services/gap_vix_service.py."""

import pytest

from services.gap_vix_service import (
    calculate_rth_gaps,
    calculate_vix_standard_deviation,
    get_auto_volatility_index,
    infer_ticker_context,
    TickerContext,
)


def make_ticker(bars, symbol="SPY") -> TickerContext:
    return infer_ticker_context(symbol, bars)


class TestInferContext:
    def test_futures_tick_size(self, sample_bars):
        ctx = infer_ticker_context("/ES", sample_bars)
        assert ctx.tick_size == 0.25

    def test_stock_tick_size(self, sample_bars):
        ctx = infer_ticker_context("AAPL", sample_bars)
        assert ctx.tick_size == 0.01


class TestRTHGaps:
    def test_gap_detected(self, gap_bars):
        ticker = make_ticker(gap_bars, "SPY")
        gaps = calculate_rth_gaps(gap_bars, ticker, {"minTicks": 1, "maxGaps": 10})
        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["isUp"] is True
        assert gap["initialTop"] == 110.0
        assert gap["initialBottom"] == gap_bars[7].close == 103.5

    def test_gap_fills(self, gap_bars):
        ticker = make_ticker(gap_bars, "SPY")
        gaps = calculate_rth_gaps(gap_bars, ticker, {"minTicks": 1, "maxGaps": 10})
        gap = gaps[0]
        assert gap["isFullyFilled"] is True
        assert gap["currentTop"] == gap["initialBottom"] == 103.5

    def test_no_gap_without_boundary(self, sample_bars):
        ticker = make_ticker(sample_bars)
        assert calculate_rth_gaps(sample_bars, ticker) == []

    def test_min_gap_size_respects_ticks(self, gap_bars):
        ticker = make_ticker(gap_bars, "SPY")
        # minTicks large enough that a 10.0 gap is below the threshold
        gaps = calculate_rth_gaps(gap_bars, ticker, {"minTicks": 5000, "maxGaps": 10})
        assert gaps == []


class TestAutoVolatilityIndex:
    def test_mapping(self):
        assert get_auto_volatility_index("NQ")["name"] == "VXN"
        assert get_auto_volatility_index("RTY")["name"] == "RVX"
        assert get_auto_volatility_index("YM")["name"] == "VXD"
        assert get_auto_volatility_index("SPY")["name"] == "VIX"


class TestVixStandardDeviation:
    def test_levels_and_anchor(self, sample_bars):
        ticker = TickerContext(symbol="SPY", tick_size=0.01, digits=2, prev_close=100.0, open=100.0)
        result = calculate_vix_standard_deviation(ticker, sample_bars, {
            "sdDivisor": 15.87,
            "showAnchor": True,
            "showSd05": True,
            "showSd1": True,
            "showSd2": True,
            "showSd3": True,
        })
        assert result["anchorPrice"] == 100.0
        assert result["anchorName"] == "Prev RTH Close"
        assert len(result["levels"]) == 1 + 2 + 2 + 2 + 2  # anchor + 4 pairs

    def test_one_sigma_value(self, sample_bars):
        ticker = TickerContext(symbol="SPY", tick_size=0.01, digits=2, prev_close=100.0, open=100.0)
        result = calculate_vix_standard_deviation(ticker, sample_bars, {"sdDivisor": 15.87})
        # (100 * 15.40) / 15.87 / 100
        expected = (100.0 * 15.40) / 15.87 / 100.0
        assert result["oneSigmaMove"] == pytest.approx(expected, abs=0.01)

    def test_session_open_anchor(self, sample_bars):
        ticker = TickerContext(symbol="SPY", tick_size=0.01, digits=2, prev_close=100.0, open=110.0)
        result = calculate_vix_standard_deviation(ticker, sample_bars, {"anchorSource": "session_open"})
        assert result["anchorPrice"] == 110.0
        assert result["anchorName"] == "Session Open"

    def test_symmetric_sigma_around_anchor(self, sample_bars):
        ticker = TickerContext(symbol="SPY", tick_size=0.01, digits=2, prev_close=100.0, open=100.0)
        result = calculate_vix_standard_deviation(ticker, sample_bars, {"showSd1": True})
        by_sigma = {lvl["sigma"]: lvl["price"] for lvl in result["levels"]}
        one = result["oneSigmaMove"]
        assert by_sigma[1.0] == pytest.approx(100 + one, abs=0.01)
        assert by_sigma[-1.0] == pytest.approx(100 - one, abs=0.01)