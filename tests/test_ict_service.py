"""Tests for services/ict_service.py — structural invariants + determinism."""

import pytest

from services.gap_vix_service import TickerContext
from services.ict_service import calculate_ict_concepts


ALLOWED_KZ_NAMES = {"New York", "London Open", "London Close", "Asian"}
ALLOWED_VI_DIRS = {"bullish", "bearish"}


def _make_ticker(bars, symbol="SPY") -> TickerContext:
    prev_close = bars[-2].close if len(bars) > 1 else bars[0].close
    session_open = bars[0].open
    return TickerContext(symbol=symbol, tick_size=0.01, digits=2,
                        prev_close=prev_close, open=session_open)


class TestEdgeCases:
    def test_empty_bars_returns_empty(self):
        from data.models import Bar
        result = calculate_ict_concepts([], TickerContext("SPY"))
        assert result["marketStructures"] == []

    def test_few_bars_returns_empty(self):
        from data.models import Bar
        bars = [Bar("T", "5m", 1_700_000_000 + i*60, 100+i, 101, 99, 100, 100) for i in range(5)]
        ticker = _make_ticker(bars)
        result = calculate_ict_concepts(bars, ticker)
        assert result["marketStructures"] == []


class TestResultStructure:
    def test_all_keys_present(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        for key in ["marketStructures", "orderBlocks", "fairValueGaps",
                     "liquidityPools", "volumeImbalances", "openingGaps",
                     "displacements", "killzones", "currentBias", "summaryBadge"]:
            assert key in result, f"Missing key: {key}"

    def test_bias_is_one_of_three(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        assert result["currentBias"] in ("Bullish", "Bearish", "Neutral")

    def test_summary_mentions_fvg_and_ob(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        assert "FVG" in result["summaryBadge"]
        assert "OB" in result["summaryBadge"]


class TestOutputShapes:
    def test_market_structure_entry_shape(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        for ms in result["marketStructures"]:
            assert ms.keys() >= {"type", "price", "startIndex", "endIndex", "color"}
            assert ms["type"] in ("MSS", "BOS")
            assert ms["startIndex"] <= ms["endIndex"]

    def test_fvg_entry_shape(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        for fvg in result["fairValueGaps"]:
            assert fvg.keys() >= {"top", "bottom", "isBroken", "color", "startIndex", "endIndex"}
            assert fvg["top"] >= fvg["bottom"]

    def test_liquidity_pool_entry_shape(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        for pool in result["liquidityPools"]:
            assert pool.keys() >= {"type", "top", "bottom", "levelPrice", "startIndex", "isSwept", "color"}
            assert pool["type"] in ("buyside", "sellside")
            assert pool["top"] >= pool["bottom"]

    def test_killzone_windows(self, impulse_bars):
        result = calculate_ict_concepts(impulse_bars, _make_ticker(impulse_bars))
        for kz in result["killzones"]:
            assert kz["name"] in ALLOWED_KZ_NAMES
            assert kz["startIndex"] <= kz["endIndex"]


class TestDeterminism:
    def test_same_input_same_output(self, impulse_bars):
        t = _make_ticker(impulse_bars)
        r1 = calculate_ict_concepts(impulse_bars, t)
        r2 = calculate_ict_concepts(impulse_bars, t)
        assert len(r1["marketStructures"]) == len(r2["marketStructures"])
        assert len(r1["fairValueGaps"]) == len(r2["fairValueGaps"])
        assert r1["currentBias"] == r2["currentBias"]


class TestParamSensitivity:
    def test_disabling_ob_returns_empty_ob(self, impulse_bars):
        t = _make_ticker(impulse_bars)
        result = calculate_ict_concepts(impulse_bars, t, {"showOB": False})
        assert result["orderBlocks"] == []

    def test_disabling_fvg_returns_empty_fvg(self, impulse_bars):
        t = _make_ticker(impulse_bars)
        result = calculate_ict_concepts(impulse_bars, t, {"showFVG": False})
        assert result["fairValueGaps"] == []

    def test_disabling_structure_returns_empty_ms(self, impulse_bars):
        t = _make_ticker(impulse_bars)
        result = calculate_ict_concepts(impulse_bars, t, {"showMS": False})
        assert result["marketStructures"] == []