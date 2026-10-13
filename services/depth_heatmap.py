"""DepthHeatmapService: D37 microstructure data plane.

Consumes the depth op stream (insert/update/delete per side/price) and
maintains:

- a live book: ``price -> [bid_size, ask_size]`` (price-keyed; the DOM keeps
  its own positional OrderBook — this service is the heatmap's model)
- a bounded price x time matrix: the trailing ``bucket_count`` time buckets,
  each a snapshot ``{price: (bid_size, ask_size)}`` of resting size at roll
- imbalance over the top-5 and top-10 levels, recomputed on every op::

      imbalance = (bidVol - askVol) / (bidVol + askVol)

  over the N best bids + N best asks (0.0 when both sides are empty)

Pure logic — no Qt, no IBKR calls. The session drives ``roll_bucket()`` on
a timer; tests drive it directly. Rendering lives in
``ui/depth_heatmap_item.py``.
"""

from __future__ import annotations

SIDE_ASK = 0
SIDE_BID = 1

OP_INSERT = 0
OP_UPDATE = 1
OP_DELETE = 2

BUCKET_COUNT = 60
BUCKET_SECONDS = 30


class DepthHeatmapService:
    def __init__(self, symbol: str, bucket_count: int = BUCKET_COUNT):
        self.symbol = symbol.upper()
        self._book: dict[float, list[int]] = {}  # price -> [bid_size, ask_size]
        self._buckets: list[dict[float, tuple[int, int]]] = []
        self._bucket_count = bucket_count
        self._imbalance_5: float = 0.0
        self._imbalance_10: float = 0.0
        self._op_count: int = 0

    # ── Ingress ──────────────────────────────────────────────────────

    def on_depth_op(self, position: int, operation: int, side: int,
                    price: float, size: int,
                    is_smart_depth: bool = False) -> None:
        """Apply one depth op to the live book; recompute both imbalances.

        ``is_smart_depth`` records row provenance (SMART-aggregated vs
        exchange-direct L2 rows); the aggregated bookkeeping is identical.
        """
        if price <= 0:
            return
        entry = self._book.get(price)
        if entry is None:
            entry = [0, 0]
            self._book[price] = entry
        idx = 0 if side == SIDE_BID else 1  # entry is [bid_size, ask_size]
        if operation == OP_DELETE:
            entry[idx] = 0
        else:  # insert / update
            entry[idx] = size
        if entry[0] == 0 and entry[1] == 0:
            del self._book[price]
        self._op_count += 1
        self._recompute_imbalance()

    def roll_bucket(self) -> None:
        """Snapshot the current book as the newest time bucket (bounded)."""
        snap = {p: (b, a) for p, (b, a) in self._book.items() if b or a}
        self._buckets.append(snap)
        if len(self._buckets) > self._bucket_count:
            del self._buckets[:len(self._buckets) - self._bucket_count]

    # ── Reads ────────────────────────────────────────────────────────

    def matrix(self) -> list[dict[float, tuple[int, int]]]:
        """Time buckets oldest -> newest (each {price: (bid, ask)})."""
        return list(self._buckets)

    def book(self) -> dict[float, tuple[int, int]]:
        """Current live book {price: (bid_size, ask_size)}."""
        return {p: (b, a) for p, (b, a) in self._book.items()}

    def imbalance(self, n: int = 5) -> float:
        """Headline imbalance over the top-n levels (default top-5)."""
        return self._imbalance_5 if n <= 5 else self._imbalance_10

    @property
    def op_count(self) -> int:
        return self._op_count

    # ── Internals ────────────────────────────────────────────────────

    def _recompute_imbalance(self) -> None:
        self._imbalance_5 = self._imbalance_over(5)
        self._imbalance_10 = self._imbalance_over(10)

    def _imbalance_over(self, n: int) -> float:
        bids = sorted((p for p, (b, _a) in self._book.items() if b > 0),
                      reverse=True)[:n]
        asks = sorted((p for p, (_b, a) in self._book.items() if a > 0))[:n]
        bid_vol = sum(self._book[p][0] for p in bids)
        ask_vol = sum(self._book[p][1] for p in asks)
        total = bid_vol + ask_vol
        if total == 0:
            return 0.0
        return (bid_vol - ask_vol) / total
