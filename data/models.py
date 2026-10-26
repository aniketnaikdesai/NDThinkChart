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
    # D39.3: alarm kind. "price" alarms behave exactly as before;
    # "volume_burst" alarms fire on unusual volume (robust z-score vs the
    # volume baseline) and carry their tuning in params. Price/chart code
    # must ignore non-"price" kinds (they have no price level).
    kind: str = "price"
    # D39.3: JSON-serializable params. Burst params: {"z_threshold": float,
    # "n": int, "proxy": str|None, "proxy_label": str}. Transient
    # (never persisted): trigger_z — the z-score at fire time, set by
    # evaluate_volume_burst for the toast.
    params: dict = field(default_factory=dict)
    trigger_z: Optional[float] = field(default=None, repr=False, compare=False)


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
    trade_group_id: Optional[int] = None
    id: Optional[int] = None


@dataclass
class TradeGroup:
    name: str
    strategy_type: str  # 'PCS' | 'PDS' | 'CCS' | 'CDS' | 'IC' | 'CUSTOM'
    underlying: str
    id: Optional[int] = None
    collapsed: bool = False
    created_at: Optional[int] = None