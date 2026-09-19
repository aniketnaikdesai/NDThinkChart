"""Pure order builders and open-order tracking for Phase 5 Order Entry."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from ibapi.order import Order
from ibapi.contract import Contract
from ibkr.id_manager import id_manager


@dataclass
class UserOrder:
    """In-memory tracking of an order placed via the client."""
    order_id: int
    symbol: str
    action: str  # 'BUY' | 'SELL'
    total_qty: float
    order_type: str  # 'MKT' | 'LMT' | 'STP'
    lmt_price: Optional[float] = None
    aux_price: Optional[float] = None
    status: str = ""
    parent_id: int = 0
    oca_group: str = ""
    transmit: bool = True
    contract: Contract = field(default_factory=Contract)


class Orders:
    """Order builders + in-memory open-order registry."""

    def __init__(self):
        self._orders: Dict[int, UserOrder] = {}

    # ── Builders ─────────────────────────────────────────────────────────────
    def market_order(self, action: str, qty: float) -> Order:
        """Create a market order."""
        order = Order()
        order.action = action  # BUY/SELL
        order.orderType = "MKT"
        order.totalQuantity = qty
        return order

    def limit_order(self, action: str, qty: float, price: float) -> Order:
        """Create a limit order."""
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.totalQuantity = qty
        order.lmtPrice = price
        return order

    def stop_order(self, action: str, qty: float, price: float) -> Order:
        """Create a stop order."""
        order = Order()
        order.action = action
        order.orderType = "STP"
        order.totalQuantity = qty
        order.auxPrice = price
        return order

    def bracket_order(
        self,
        parent_id: int,
        action: str,
        qty: float,
        entry_price: float,
        stop_price: float,
        limit_price: float,
    ) -> tuple[Order, Order, Order]:
        """
        Create a bracket (entry + stop + target) as three Order objects.
        Returns (parent, stop, limit).

        - Parent: entry order (LMT) with transmit=False
        - Stop: stop order (STP) with parentId, ocaGroup, transmit=False
        - Limit: limit order (LMT) with parentId, ocaGroup, transmit=True (last)
        """
        # Parent order (entry)
        parent = Order()
        parent.orderId = parent_id
        parent.action = action
        parent.orderType = "LMT"
        parent.totalQuantity = qty
        parent.lmtPrice = entry_price
        parent.transmit = False  # Hold until children are submitted

        # OCA group for the bracket
        oca_group = f"bracket-{parent_id}"
        oca_type = 1  # Cancel all remaining on fill

        # Stop-loss child
        stop = Order()
        stop.action = action
        stop.orderType = "STP"
        stop.totalQuantity = qty
        stop.auxPrice = stop_price
        stop.parentId = parent_id
        stop.ocaGroup = oca_group
        stop.ocaType = oca_type
        stop.transmit = False

        # Take-profit child
        limit = Order()
        limit.action = action
        limit.orderType = "LMT"
        limit.totalQuantity = qty
        limit.lmtPrice = limit_price
        limit.parentId = parent_id
        limit.ocaGroup = oca_group
        limit.ocaType = oca_type
        limit.transmit = True  # Last child transmits the whole group

        return parent, stop, limit

    # ── Registry ─────────────────────────────────────────────────────────────
    def register(self, order: UserOrder) -> None:
        """Track an order after it's been placed."""
        self._orders[order.order_id] = order

    def get(self, order_id: int) -> Optional[UserOrder]:
        """Retrieve a tracked order by ID."""
        return self._orders.get(order_id)

    def update_status(self, order_id: int, status: str) -> None:
        """Update the status of a tracked order."""
        if order_id in self._orders:
            self._orders[order_id].status = status

    def clear_filled(self, order_id: int) -> None:
        """Remove an order from tracking when it's filled/cancelled."""
        self._orders.pop(order_id, None)

    def all(self) -> Dict[int, UserOrder]:
        """Return a copy of all tracked orders."""
        return self._orders.copy()


# Global singleton
orders = Orders()