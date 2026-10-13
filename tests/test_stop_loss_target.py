"""Position/TradeGroup stop-loss/take-profit model fields.

D28.6: the phantom ``validate_sltp`` helper + ``TestValidateSLTP`` class
were deleted — they tested a validation function defined in this test
file itself, with no production counterpart. Only the real model-field
tests remain.
"""

from data.models import Position, TradeGroup


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
