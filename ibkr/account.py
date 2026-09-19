"""
account.py
Account model and helpers for IBKR account summary / positions.
No Qt, no I/O beyond DB — keep it pure and testable.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Account:
    """Represents an IBKR account snapshot."""
    account: str
    tag: str
    value: str
    currency: str = ""


@dataclass
class Position:
    """Normalized position from IBKR."""
    symbol: str
    account: str
    con_id: Optional[int]
    contract_type: str  # 'stock' | 'future' | 'option'
    local_symbol: str = ""
    multiplier: float = 1.0
    expiry: Optional[str] = None
    strike: Optional[float] = None
    right: Optional[str] = None  # 'C' | 'P'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trade_group_id: Optional[int] = None
    avg_cost: float = 0.0
    qty: float = 0.0  # signed: positive long, negative short
    market_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


def _parse_contract_type(s: str) -> str:
    """Normalize IBKR contract type string."""
    return s.strip().lower()


def build_position_from_ib(
    symbol: str,
    account: str,
    con_id: Optional[int],
    contract_type: str,
    local_symbol: str,
    multiplier: float,
    expiry: Optional[str],
    strike: Optional[float],
    right: Optional[str],
    avg_cost: float,
    qty: float,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    trade_group_id: Optional[int] = None,
) -> Position:
    """Convenience helper to build a Position from IBKR callback data."""
    return Position(
        symbol=symbol,
        account=account,
        con_id=con_id,
        contract_type=_parse_contract_type(contract_type),
        local_symbol=local_symbol,
        multiplier=multiplier,
        expiry=expiry,
        strike=strike,
        right=right,
        stop_loss=stop_loss,
        take_profit=take_profit,
        trade_group_id=trade_group_id,
        avg_cost=avg_cost,
        qty=qty,
    )