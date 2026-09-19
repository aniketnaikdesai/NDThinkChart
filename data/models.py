from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Bar:
    symbol: str
    timeframe: str
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Alarm:
    id: Optional[int]
    symbol: str
    price: float
    direction: str
    active: bool = True
    triggered: bool = False
    triggered_at: Optional[int] = None
    sound: bool = True
    note: str = ""
    created_at: Optional[int] = None


@dataclass
class Drawing:
    """A user drawing on a chart. Payload is a JSON-serializable dict.

    Payload shapes per kind:
      trendline   -> {"p1": {"x": ts, "y": price}, "p2": {"x": ts, "y": price}}
      horizontal  -> {"y": price}
      zone        -> {"x1": ts, "x2": ts, "y1": price, "y2": price}
      fibonacci   -> {"p1": {"x": ts, "y": price}, "p2": {"x": ts, "y": price}, "type": "retr"}
      measure     -> {"p1": {"x": ts, "y": price}, "p2": {"x": ts, "y": price}}
    """
    symbol: str
    kind: str  # 'trendline' | 'horizontal' | 'zone' | 'fibonacci' | 'measure'
    payload: dict
    id: Optional[int] = None
    color: str = "#38bdf8"
    label: str = ""
    group_id: Optional[int] = None


@dataclass
class DrawingGroup:
    symbol: str
    name: str
    seq_number: int
    id: Optional[int] = None
    color: Optional[str] = None
    visible: bool = True
    locked: bool = False
    created_at: Optional[int] = None


@dataclass
class Position:
    symbol: str
    qty: float  # signed: positive long, negative short
    avg_cost: float
    contract_type: str  # 'stock' | 'future' | 'option'
    con_id: Optional[int] = None
    account: str = ""
    local_symbol: str = ""
    multiplier: float = 1.0
    expiry: Optional[str] = None
    strike: Optional[float] = None
    right: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trade_group_id: Optional[int] = None
    id: Optional[int] = None


@dataclass
class TradeGroup:
    name: str
    strategy_type: str  # 'PCS' | 'PDS' | 'CCS' | 'CDS' | 'IC' | 'CUSTOM'
    underlying: str
    id: Optional[int] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    collapsed: bool = False
    created_at: Optional[int] = None


@dataclass
class OrderBookLevel:
    position: int      # level index from IBKR
    side: str          # 'bid' | 'ask'
    price: float
    size: int
    market_maker: str = ""


@dataclass
class UserOrder:
    order_id: int
    symbol: str
    action: str        # 'BUY' | 'SELL'
    total_qty: float
    order_type: str    # 'MKT' | 'LMT' | 'STP'
    lmt_price: Optional[float] = None
    aux_price: Optional[float] = None
    status: str = ""
    parent_id: int = 0
    oca_group: str = ""
    transmit: bool = True