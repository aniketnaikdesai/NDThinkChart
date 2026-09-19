"""Tests for services/indicator_service.py — pure numeric math."""

import math

import pytest

from services.indicator_service import (
    calculate_sma, calculate_ema, calculate_vwap,
    calculate_bollinger_bands, calculate_rsi, calculate_macd,
)


def closes_of(sample_bars):
    return [b.close for b in sample_bars]


class TestSMA:
    def test_length_and_warmup(self, sample_bars):
        closes = closes_of(sample_bars)
        sma = calculate_sma(closes, period=10)
        assert len(sma) == len(closes)
        assert sma[:9] == [None] * 9
        assert sma[9] == sum(closes[:10]) / 10

    def test_constant_series(self):
        closes = [5.0] * 20
        sma = calculate_sma(closes, 5)
        assert all(v == 5.0 for v in sma[4:])


class TestEMA:
    def test_constant_series_stays_constant(self, sample_bars):
        closes = [10.0] * 40
        ema = calculate_ema(closes, 10)
        assert ema[9] == 10.0
        assert all(v == 10.0 for v in ema[10:])

    def test_converges_to_sma(self):
        closes = list(range(1, 21))
        ema = calculate_ema(closes, 10)
        sma = calculate_sma(closes, 10)
        assert ema[9] == pytest.approx(sma[9])
        assert ema[-1] == pytest.approx(sma[-1], abs=0.05)


class TestVWAP:
    def test_no_timestamps_is_cumulative(self):
        hs = [100.0] * 6
        ls = [98.0] * 6
        cs = [102.0] * 6
        vs = [10.0] * 6
        vwap = calculate_vwap(hs, ls, cs, vs)
        assert vwap[0] == vwap[-1]  # single cumulative anchor

    def test_session_reset(self):
        hs = [100.0 + i for i in range(4)]
        ls = [98.0 + i for i in range(4)]
        cs = [102.0 + i for i in range(4)]
        vs = [10.0] * 4
        ts = [1_700_000_000 + i * 60 for i in range(4)]

        r = calculate_vwap(hs * 2, ls * 2, cs * 2, vs * 2,
                           timestamps=ts + [1_700_000_000 + 86_400 + i * 60
                                            for i in range(4)])
        assert r[3] > 100.001, r[3]   # accumulated across session 1
        assert abs(r[4] - 100.0) < 1e-6, r[4]  # reset at new session


class TestBollinger:
    def test_middle_equals_sma(self, sample_bars):
        closes = closes_of(sample_bars)
        upper, mid, lower = calculate_bollinger_bands(closes, 20, 2.0)
        sma = calculate_sma(closes, 20)
        assert mid == sma

    def test_ordering(self, sample_bars):
        closes = closes_of(sample_bars)
        upper, mid, lower = calculate_bollinger_bands(closes, 20, 2.0)
        for i in range(19, len(closes)):
            assert lower[i] <= mid[i] <= upper[i]

    def test_zero_vol_series(self):
        closes = [100.0] * 30
        upper, mid, lower = calculate_bollinger_bands(closes, 20, 2.0)
        assert upper[19] == 100.0
        assert lower[19] == 100.0


class TestRSI:
    def test_strictly_rising_is_100(self):
        prices = list(range(30))
        rsi = calculate_rsi(prices, 14)
        assert rsi[14] == 100.0
        assert all(rsi[i] == 100.0 for i in range(14, 30))

    def test_strictly_falling_is_0(self):
        prices = list(reversed(range(30)))
        rsi = calculate_rsi(prices, 14)
        assert rsi[14] == 0.0

    def test_bounds(self, sample_bars):
        closes = closes_of(sample_bars)
        rsi = calculate_rsi(closes, 14)
        for v in rsi[14:]:
            assert 0.0 <= v <= 100.0

    def test_warmup(self, sample_bars):
        closes = closes_of(sample_bars)
        rsi = calculate_rsi(closes, 14)
        assert rsi[:14] == [None] * 14


class TestMACD:
    def test_lengths(self, sample_bars):
        closes = closes_of(sample_bars)
        macd, signal, hist = calculate_macd(closes, 12, 26, 9)
        assert len(macd) == len(signal) == len(hist) == len(closes)

    def test_histogram_is_difference(self, sample_bars):
        closes = closes_of(sample_bars)
        macd, signal, hist = calculate_macd(closes, 12, 26, 9)
        for m, s, h in zip(macd, signal, hist):
            if m is not None and s is not None:
                assert h == pytest.approx(m - s)

    def test_histogram_zeros_before_signal_ready(self, sample_bars):
        closes = closes_of(sample_bars)
        macd, signal, hist = calculate_macd(closes, 12, 26, 9)
        assert hist[0] is None
        assert signal[0] is None