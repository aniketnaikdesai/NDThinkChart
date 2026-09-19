"""
strategy_detection.py
Pure logic for detecting option strategies from position legs.

Ported from reference TypeScript implementation.
No I/O, no Qt, no IBKR dependencies.
"""

from typing import Literal
from dataclasses import dataclass

from data.models import Position

StrategyType = Literal["PCS", "PDS", "CCS", "CDS", "IC", "CUSTOM"]


@dataclass
class OptionLeg:
    """Normalized option leg for strategy detection."""
    right: str          # 'C' or 'P'
    strike: float
    qty: int            # signed: positive = long, negative = short
    expiry: str         # YYYYMMDD format
    local_symbol: str = ""
    con_id: int = 0


def _normalize_legs(positions: list[Position]) -> list[OptionLeg]:
    """Filter and normalize option positions to OptionLeg list."""
    legs = []
    for pos in positions:
        if pos.contract_type != "option":
            continue
        if pos.right not in ("C", "P"):
            continue
        if pos.strike is None or pos.expiry is None:
            continue
        legs.append(OptionLeg(
            right=pos.right,
            strike=pos.strike,
            qty=int(pos.qty),
            expiry=pos.expiry,
            local_symbol=pos.local_symbol or "",
            con_id=pos.con_id or 0,
        ))
    return legs


def _same_expiry(legs: list[OptionLeg]) -> bool:
    """Check if all legs share the same expiry."""
    if not legs:
        return False
    first = legs[0].expiry
    return all(leg.expiry == first for leg in legs)


def _detect_vertical_spread(legs: list[OptionLeg]) -> StrategyType | None:
    """Detect 2-leg vertical spreads: PCS, PDS, CCS, CDS."""
    if len(legs) != 2:
        return None
    if not _same_expiry(legs):
        return None

    l1, l2 = legs[0], legs[1]
    # Both legs must be same type (both calls or both puts)
    if l1.right != l2.right:
        return None

    # Vertical spread: long one strike, short the other
    if l1.qty * l2.qty >= 0:
        return None  # both long or both short

    # Sort by strike
    if l1.strike < l2.strike:
        lower, upper = l1, l2
    else:
        lower, upper = l2, l1

    right = l1.right  # 'C' or 'P'

    # Put Credit Spread (PCS): short higher put, long lower put
    if right == "P":
        if lower.qty > 0 and upper.qty < 0:
            return "PCS"   # long lower, short higher = credit put spread
        if lower.qty < 0 and upper.qty > 0:
            return "PDS"   # short lower, long higher = debit put spread
        return None

    # Call spreads
    if right == "C":
        if lower.qty > 0 and upper.qty < 0:
            return "CCS"   # long lower call, short higher call = credit call spread (bear call)
        if lower.qty < 0 and upper.qty > 0:
            return "CDS"   # short lower call, long higher call = debit call spread (bull call)
        return None

    return None


def _detect_iron_condor(legs: list[OptionLeg]) -> StrategyType | None:
    """Detect 4-leg Iron Condor: 2 puts + 2 calls, symmetric around center."""
    if len(legs) != 4:
        return None
    if not _same_expiry(legs):
        return None

    puts = [l for l in legs if l.right == "P"]
    calls = [l for l in legs if l.right == "C"]

    if len(puts) != 2 or len(calls) != 2:
        return None

    # Each side must have one long, one short
    put_qtys = sorted([l.qty for l in puts])
    call_qtys = sorted([l.qty for l in calls])
    if put_qtys != [-1, 1] or call_qtys != [-1, 1]:
        return None

    # Sort by strike
    puts.sort(key=lambda x: x.strike)
    calls.sort(key=lambda x: x.strike)

    # Iron condor: short put spread (higher put short) + short call spread (lower call short)
    # i.e., long lower put, short higher put, short lower call, long higher call
    # Strikes should be ordered: put_long < put_short < call_short < call_long
    put_long, put_short = puts[0], puts[1]
    call_short, call_long = calls[0], calls[1]

    if put_long.qty != 1 or put_short.qty != -1:
        return None
    if call_short.qty != -1 or call_long.qty != 1:
        return None

    # Strikes should be symmetric around center
    # For a proper IC, the wing widths should be equal
    put_width = put_short.strike - put_long.strike
    call_width = call_long.strike - call_short.strike

    if abs(put_width - call_width) > 0.01:  # allow small float diff
        return None

    return "IC"


def detect_option_strategy(positions: list[Position]) -> StrategyType:
    """
    Detect option strategy from a list of positions.

    Returns one of: PCS, PDS, CCS, CDS, IC, CUSTOM.
    """
    legs = _normalize_legs(positions)

    if not legs:
        return "CUSTOM"

    # Try specific detectors in order of specificity
    if strat := _detect_vertical_spread(legs):
        return strat

    if strat := _detect_iron_condor(legs):
        return strat

    return "CUSTOM"


def detect_and_group(
    positions: list[Position],
    group_name_prefix: str = "Auto"
) -> tuple[StrategyType, list[int]]:
    """
    Detect strategy and return (strategy_type, leg_indices).

    leg_indices are indices into the original positions list that form the strategy.
    """
    legs = _normalize_legs(positions)

    if not legs:
        return "CUSTOM", []

    # Map back to original positions indices
    leg_to_pos_idx = {}
    pos_idx = 0
    for i, pos in enumerate(positions):
        if pos.contract_type == "option" and pos.right in ("C", "P") \
                and pos.strike is not None and pos.expiry is not None:
            leg_to_pos_idx[pos_idx] = i
            pos_idx += 1

    # Try vertical spread (2 legs)
    if len(legs) == 2:
        if strat := _detect_vertical_spread(legs):
            return strat, [leg_to_pos_idx[0], leg_to_pos_idx[1]]

    # Try iron condor (4 legs)
    if len(legs) == 4:
        if strat := _detect_iron_condor(legs):
            return strat, [leg_to_pos_idx[i] for i in range(4)]

    return "CUSTOM", []