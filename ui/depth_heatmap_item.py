"""depth_heatmap_item.py — D37 depth heatmap render layer.

A pyqtgraph GraphicsObject that draws the depth heatmap as a price-aligned
overlay strip at the right edge of the price plot (Bookmap-style):

- rows    = price levels (data coordinates → exactly price-aligned)
- columns = trailing time buckets, oldest left, newest right
- cell    = resting size at that level when the bucket rolled; left half
  bid (blue), right half ask (red), alpha by size

D28 render discipline: ``set_matrix()`` stores data only and never
repaints; ``refresh()`` rebuilds the picture (``regen_count`` mirrors
``FootprintItem`` so tests can assert depth op bursts cause zero
regenerations). The strip tracks the visible x-range, so the chart panel
also refreshes on view-range change.
"""

from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtGui import QPicture, QPainter, QColor, QBrush
from PyQt6.QtCore import QRectF, Qt

_BID_RGB = (96, 165, 250)    # blue-400
_ASK_RGB = (251, 146, 60)    # orange-400

STRIP_FRACTION = 0.18  # strip width as a fraction of the visible x-range


class DepthHeatmapItem(pg.GraphicsObject):
    def __init__(self):
        super().__init__()
        self._buckets: list[dict[float, tuple[int, int]]] = []
        self._half_tick: float = 0.01
        self._picture = QPicture()
        # D28 discipline: render-call counter — depth op bursts must not
        # regenerate; only explicit refresh() (timer / range change) does.
        self.regen_count: int = 0

    # ── Public API ─────────────────────────────────────────────────────

    def set_matrix(self, buckets: list[dict[float, tuple[int, int]]],
                   half_tick: float) -> None:
        """Store data only — never repaints."""
        self._buckets = list(buckets)
        self._half_tick = half_tick if half_tick > 0 else 0.01

    def refresh(self) -> None:
        """Rebuild the picture from the current matrix + view range."""
        self._generate()
        self.update()

    def clear(self) -> None:
        self._buckets = []
        self._picture = QPicture()
        self.update()

    # ── Internals ────────────────────────────────────────────────────

    def layout(self, view_right: float, view_width: float
               ) -> list[tuple[float, float, float, tuple[int, int]]]:
        """Pure layout: (x0, col_w, price, (bid, ask)) per cell.

        Testable without Qt: rows are price-centred by construction.
        """
        n = len(self._buckets)
        if n == 0 or view_width <= 0:
            return []
        col_w = (view_width * STRIP_FRACTION) / n
        cells = []
        for i, bucket in enumerate(self._buckets):
            x0 = view_right - (n - i) * col_w
            for price, sizes in bucket.items():
                cells.append((x0, col_w, price, sizes))
        return cells

    def _generate(self):
        self.regen_count += 1
        self._picture = QPicture()
        vb = self.getViewBox()
        if vb is None:
            return
        view = vb.viewRect()
        cells = self.layout(view.right(), view.width())
        if not cells:
            return
        peak = 0
        for _x0, _cw, _p, (bid, ask) in cells:
            peak = max(peak, bid, ask)
        peak = peak or 1
        p = QPainter(self._picture)
        p.setPen(Qt.PenStyle.NoPen)
        for x0, col_w, price, (bid, ask) in cells:
            y0 = price - self._half_tick / 2
            h = self._half_tick
            # Left half = bid, right half = ask; alpha scales with size.
            if bid > 0:
                a = int(40 + 215 * min(bid / peak, 1.0))
                p.setBrush(QBrush(QColor(*_BID_RGB, a)))
                p.drawRect(QRectF(x0, y0, col_w / 2, h))
            if ask > 0:
                a = int(40 + 215 * min(ask / peak, 1.0))
                p.setBrush(QBrush(QColor(*_ASK_RGB, a)))
                p.drawRect(QRectF(x0 + col_w / 2, y0, col_w / 2, h))
        p.end()

    # ── pyqtgraph overrides ────────────────────────────────────────────

    def paint(self, painter, option, widget):
        painter.drawPicture(0, 0, self._picture)

    def boundingRect(self):
        return QRectF(self._picture.boundingRect())
