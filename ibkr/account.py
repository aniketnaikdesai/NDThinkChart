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
    trade_group_id: Optional[int] = None
    avg_cost: float = 0.0
    qty: float = 0.0  # signed: positive long, negative short
    market_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    # ESC-032 / P2-T27 (ESC-062): the `positions.id` DB row key. The panel
    # (`ActivePortfolioPanel._render_table`) dereferences `pos.id` to derive
    # strategy grouping, so the live path must carry the REAL row key — not a
    # defensive None. Without it the Strategy/Group columns render the '—'
    # missing-id placeholder.
    id: Optional[int] = None


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
        trade_group_id=trade_group_id,
        avg_cost=avg_cost,
        qty=qty,
    )