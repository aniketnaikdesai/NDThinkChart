"""Pure order-book model for Level I/II market depth.

IBKR delivers incremental BookMarks via updateMktDepth:
    reqId, position, operation, side, price, size
where operation is 0=insert, 1=update, 2=delete and side is 0=ask, 1=bid.
Each side keeps an ordered row list (position is dense and assigned by IBKR),
so operations can be applied positionally while prices remain row-attached.
"""

from dataclasses import dataclass
from typing import Optional

SIDE_ASK = 0
SIDE_BID = 1


@dataclass
class Level:
    position: int
    price: float
    size: int


def apply_operation(
    rows: list,
    operation: int,
    position: int,
    price: float,
    size: int,
) -> list:
    """Apply a single IBKR market-depth operation to a side's row list."""
    if operation == 0:  # insert
        rows.insert(position, Level(position=position, price=price, size=size))
        _renumber(rows)
    elif operation == 1:  # update
        if 0 <= position < len(rows):
            rows[position].price = price
            rows[position].size = size
    elif operation == 2:  # delete
        if 0 <= position < len(rows):
            del rows[position]
            _renumber(rows)
    return rows


def _renumber(rows: list) -> None:
    for idx, level in enumerate(rows):
        level.position = idx


class OrderBook:
    def __init__(self):
        self._rows = {SIDE_ASK: [], SIDE_BID: []}

    def apply(self, operation: int, side: int, position: int,
              price: float, size: int) -> None:
        rows = self._rows.get(side)
        if rows is not None:
            apply_operation(rows, operation, position, price, size)

    def levels(self, side: int) -> list:
        return list(self._rows.get(side, []))

    def ask_levels(self) -> list:
        return self.levels(SIDE_ASK)

    def bid_levels(self) -> list:
        return self.levels(SIDE_BID)

    def best_ask(self) -> Optional[Level]:
        rows = self._rows[SIDE_ASK]
        return rows[0] if rows else None

    def best_bid(self) -> Optional[Level]:
        rows = self._rows[SIDE_BID]
        return rows[0] if rows else None

    def top_of_book(self) -> dict:
        ask = self.best_ask()
        bid = self.best_bid()
        return {
            "bestAsk": ask.price if ask else None,
            "bestBid": bid.price if bid else None,
            "askSize": ask.size if ask else 0,
            "bidSize": bid.size if bid else 0,
        }

    def cumulative_sizes(self, side: int, num_levels: int | None = None) -> list:
        """Running total from the inside level outward."""
        rows = self._rows.get(side, [])
        if num_levels is not None:
            rows = rows[:num_levels]
        totals = []
        running = 0
        for level in rows:
            running += level.size
            totals.append(running)
        return totals