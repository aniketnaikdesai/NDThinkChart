"""Tests for Phase 7: Stop-Loss / Take-Profit validation logic."""

import pytest

from data.models import Position, TradeGroup


# ── Validation helpers ────────────────────────────────────────

def validate_sltp(
    position: Position,
    stop_price: float | None,
    target_price: float | None,
    market_price: float | None = None,
) -> bool:
    """
    Validate stop-loss and take-profit prices for a position.

    Returns True if valid, raises ValueError on failure.

    Rules:
      - long (qty > 0):  stop < market < target
      - short (qty < 0): stop > market > target
      - stop != market and target != market
    """
    if market_price is None:
        market_price = position.avg_cost

    if stop_price is None and target_price is None:
        raise ValueError("At least one of stop_price or target_price must be set.")

    if stop_price is not None and stop_price == market_price:
        raise ValueError(f"Stop price ({stop_price}) cannot equal market price ({market_price}).")

    if target_price is not None and target_price == market_price:
        raise ValueError(f"Target price ({target_price}) cannot equal market price ({market_price}).")

    if position.qty > 0:  # long
        if stop_price is not None and stop_price >= market_price:
            raise ValueError(
                f"Long stop ({stop_price}) must be below market ({market_price})."
            )
        if target_price is not None and target_price <= market_price:
            raise ValueError(
                f"Long target ({target_price}) must be above market ({market_price})."
            )
    elif position.qty < 0:  # short
        if stop_price is not None and stop_price <= market_price:
            raise ValueError(
                f"Short stop ({stop_price}) must be above market ({market_price})."
            )
        if target_price is not None and target_price >= market_price:
            raise ValueError(
                f"Short target ({target_price}) must be below market ({market_price})."
            )

    return True


class TestValidateSLTP:
    """validate_sltp() raises on invalid relationships."""

    def test_long_valid(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        assert validate_sltp(pos, stop_price=145.0, target_price=160.0) is True

    def test_short_valid(self):
        pos = Position(symbol="AAPL", qty=-10, avg_cost=150.0, contract_type="stock")
        assert validate_sltp(pos, stop_price=155.0, target_price=140.0) is True

    def test_long_stop_above_market_raises(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="must be below market"):
            validate_sltp(pos, stop_price=155.0, target_price=160.0)

    def test_long_target_below_market_raises(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="must be above market"):
            validate_sltp(pos, stop_price=145.0, target_price=140.0)

    def test_short_stop_below_market_raises(self):
        pos = Position(symbol="AAPL", qty=-10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="must be above market"):
            validate_sltp(pos, stop_price=145.0, target_price=140.0)

    def test_short_target_above_market_raises(self):
        pos = Position(symbol="AAPL", qty=-10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="must be below market"):
            validate_sltp(pos, stop_price=155.0, target_price=160.0)

    def test_stop_equals_market_raises(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="cannot equal market"):
            validate_sltp(pos, stop_price=150.0, target_price=160.0)

    def test_target_equals_market_raises(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="cannot equal market"):
            validate_sltp(pos, stop_price=145.0, target_price=150.0)

    def test_no_stop_no_target_raises(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        with pytest.raises(ValueError, match="At least one of stop_price"):
            validate_sltp(pos, stop_price=None, target_price=None)

    def test_stop_only(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        assert validate_sltp(pos, stop_price=145.0, target_price=None) is True

    def test_target_only(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        assert validate_sltp(pos, stop_price=None, target_price=160.0) is True

    def test_custom_market_price(self):
        """Allow validation against a custom market price (e.g., chart price)."""
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        assert validate_sltp(pos, stop_price=145.0, target_price=160.0, market_price=155.0) is True


class TestPositionModel:
    """Position model already has stop_loss/take_profit fields."""

    def test_position_defaults(self):
        pos = Position(symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock")
        assert pos.stop_loss is None
        assert pos.take_profit is None

    def test_position_with_sltp(self):
        pos = Position(
            symbol="AAPL", qty=10, avg_cost=150.0, contract_type="stock",
            stop_loss=145.0, take_profit=160.0,
        )
        assert pos.stop_loss == 145.0
        assert pos.take_profit == 160.0

    def test_trade_group_with_sltp(self):
        tg = TradeGroup(name="PCS Spread", strategy_type="PCS", underlying="AAPL")
        assert tg.stop_loss is None
        assert tg.take_profit is None