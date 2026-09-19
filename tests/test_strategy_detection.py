"""Tests for services/strategy_detection.py — pure option strategy detection."""

import pytest

from data.models import Position
from services.strategy_detection import (
    detect_option_strategy,
    detect_and_group,
    OptionLeg,
    StrategyType,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _pos(**kwargs) -> Position:
    """Convenience factory for a Position with sensible defaults."""
    return Position(
        symbol="TEST",
        qty=kwargs.get("qty", 1),
        avg_cost=kwargs.get("avg_cost", 100.0),
        contract_type=kwargs.get("contract_type", "option"),
        con_id=kwargs.get("con_id", 1),
        account=kwargs.get("account", "DU12345"),
        local_symbol=kwargs.get("local_symbol", ""),
        multiplier=kwargs.get("multiplier", 1.0),
        expiry=kwargs.get("expiry", "20240119"),
        strike=kwargs.get("strike", 100.0),
        right=kwargs.get("right", "C"),
        stop_loss=kwargs.get("stop_loss"),
        take_profit=kwargs.get("take_profit"),
        trade_group_id=kwargs.get("trade_group_id"),
    )


def _leg(**kwargs) -> OptionLeg:
    """Convenience factory for an OptionLeg."""
    from services.strategy_detection import OptionLeg
    return OptionLeg(
        right=kwargs.get("right", "C"),
        strike=kwargs.get("strike", 100.0),
        qty=kwargs.get("qty", 1),
        expiry=kwargs.get("expiry", "20240119"),
        local_symbol=kwargs.get("local_symbol", ""),
        con_id=kwargs.get("con_id", 1),
    )


# ── Detection fixture data ──────────────────────────────────────────

# PCS: Put Credit Spread — long 1 lower put, short 1 higher put
_PCS_POSITIONS = [
    _pos(right="P", strike=95.0, qty=1),   # long lower put
    _pos(right="P", strike=105.0, qty=-1),  # short higher put
]

# PDS: Put Debit Spread — short 1 lower put, long 1 higher put
_PDS_POSITIONS = [
    _pos(right="P", strike=95.0, qty=-1),  # short lower put
    _pos(right="P", strike=105.0, qty=1),  # long higher put
]

# CCS: Credit Call Spread (bear call) — long lower call, short higher call
_CCS_POSITIONS = [
    _pos(right="C", strike=95.0, qty=1),   # long lower call
    _pos(right="C", strike=105.0, qty=-1),  # short higher call
]

# CDS: Debit Call Spread (bull call) — short lower call, long higher call
_CDS_POSITIONS = [
    _pos(right="C", strike=95.0, qty=-1),  # short lower call
    _pos(right="C", strike=105.0, qty=1),  # long higher call
]

# IC: Iron Condor — 4 legs (long lower put, short higher put, short lower call, long higher call)
_IC_POSITIONS = [
    _pos(right="P", strike=95.0, qty=1),     # long lower put
    _pos(right="P", strike=105.0, qty=-1),   # short higher put
    _pos(right="C", strike=115.0, qty=-1),   # short lower call
    _pos(right="C", strike=125.0, qty=1),    # long higher call
]

# CUSTOM: Anything else
_CUSTOM_POSITIONS = [
    _pos(right="C", strike=100.0, qty=1),
    _pos(right="P", strike=100.0, qty=1),
]


# ── Tests ────────────────────────────────────────────────────────────

class TestDetectOptionStrategy:
    """detect_option_strategy() returns the correct StrategyType."""

    @pytest.mark.parametrize(
        "positions, expected",
        [
            (_PCS_POSITIONS, "PCS"),
            (_PDS_POSITIONS, "PDS"),
            (_CCS_POSITIONS, "CCS"),
            (_CDS_POSITIONS, "CDS"),
            (_IC_POSITIONS, "IC"),
            (_CUSTOM_POSITIONS, "CUSTOM"),
        ],
    )
    def test_detects_correct_strategy(self, positions, expected):
        result = detect_option_strategy(positions)
        assert result == expected

    def test_no_option_legs(self):
        result = detect_option_strategy([])
        assert result == "CUSTOM"

    def test_mixed_rights_returns_custom(self):
        pos1 = _pos(right="C", strike=95.0, qty=1)
        pos2 = _pos(right="P", strike=105.0, qty=-1)
        result = detect_option_strategy([pos1, pos2])
        assert result == "CUSTOM"

    def test_different_expiry_returns_custom(self):
        pos1 = _pos(right="C", strike=95.0, expiry="20240119", qty=1)
        pos2 = _pos(right="C", strike=105.0, expiry="20240126", qty=-1)
        result = detect_option_strategy([pos1, pos2])
        assert result == "CUSTOM"


class TestDetectAndGroup:
    """detect_and_group() returns (StrategyType, leg_indices)."""

    def test_vertical_spread_returns_indices(self):
        strat, indices = detect_and_group(_PCS_POSITIONS)
        assert strat == "PCS"
        assert len(indices) == 2

    def test_iron_condor_returns_indices(self):
        strat, indices = detect_and_group(_IC_POSITIONS)
        assert strat == "IC"
        assert len(indices) == 4

    def test_no_legs(self):
        strat, indices = detect_and_group([])
        assert strat == "CUSTOM"
        assert indices == []

    def test_vertical_spread_with_extra_non_option(self):
        pos = _PCS_POSITIONS[0]
        pos.contract_type = "stock"  # type: ignore
        extra = _pos(right="C", strike=100.0, qty=1, contract_type="stock")  # type: ignore
        strat, indices = detect_and_group([pos, extra])
        assert strat == "CUSTOM"
        assert indices == []

    def test_ic_with_extra_leg(self):
        strat, indices = detect_and_group(_IC_POSITIONS + [_pos(right="C", strike=130.0, qty=1)])
        assert strat == "CUSTOM"
        assert indices == []


class TestOptionLeg:
    """OptionLeg normalization helpers."""

    def test_normalize_creates_leg(self):
        leg = _leg(right="P", strike=95.0, qty=-1, expiry="20240119")
        assert leg.right == "P"
        assert leg.strike == 95.0
        assert leg.qty == -1
        assert leg.expiry == "20240119"

    def test_same_expiry_returns_true(self):
        from services.strategy_detection import _same_expiry
        legs = [_leg(right="C", strike=95.0, expiry="20240119", qty=1),
                _leg(right="C", strike=105.0, expiry="20240119", qty=-1)]
        assert _same_expiry(legs) is True

    def test_same_expiry_different_returns_false(self):
        from services.strategy_detection import _same_expiry
        legs = [_leg(right="C", strike=95.0, expiry="20240119", qty=1),
                _leg(right="C", strike=105.0, expiry="20240126", qty=-1)]
        assert _same_expiry(legs) is False


class TestVerticalSpread:
    """Vertical spread detection logic."""

    def test_pcs_identified(self):
        from services.strategy_detection import _detect_vertical_spread
        legs = [_leg(right="P", strike=95.0, qty=1),
                _leg(right="P", strike=105.0, qty=-1)]
        assert _detect_vertical_spread(legs) == "PCS"

    def test_pds_identified(self):
        from services.strategy_detection import _detect_vertical_spread
        legs = [_leg(right="P", strike=95.0, qty=-1),
                _leg(right="P", strike=105.0, qty=1)]
        assert _detect_vertical_spread(legs) == "PDS"

    def test_ccs_identified(self):
        from services.strategy_detection import _detect_vertical_spread
        legs = [_leg(right="C", strike=95.0, qty=1),
                _leg(right="C", strike=105.0, qty=-1)]
        assert _detect_vertical_spread(legs) == "CCS"

    def test_cds_identified(self):
        from services.strategy_detection import _detect_vertical_spread
        legs = [_leg(right="C", strike=95.0, qty=-1),
                _leg(right="C", strike=105.0, qty=1)]
        assert _detect_vertical_spread(legs) == "CDS"

    def test_non_vertical_returns_none(self):
        from services.strategy_detection import _detect_vertical_spread
        # both long
        legs = [_leg(right="P", strike=95.0, qty=1),
                _leg(right="P", strike=105.0, qty=1)]
        assert _detect_vertical_spread(legs) is None


class TestIronCondor:
    """Iron condor detection logic."""

    def test_ic_identified(self):
        from services.strategy_detection import _detect_iron_condor
        legs = [
            _leg(right="P", strike=95.0, qty=1),
            _leg(right="P", strike=105.0, qty=-1),
            _leg(right="C", strike=115.0, qty=-1),
            _leg(right="C", strike=125.0, qty=1),
        ]
        assert _detect_iron_condor(legs) == "IC"

    def test_non_ic_returns_none(self):
        from services.strategy_detection import _detect_iron_condor
        # 4 calls/puts, not symmetric
        legs = [
            _leg(right="P", strike=95.0, qty=1),
            _leg(right="P", strike=105.0, qty=-1),
            _leg(right="C", strike=115.0, qty=1),
            _leg(right="C", strike=125.0, qty=-1),
        ]
        assert _detect_iron_condor(legs) is None