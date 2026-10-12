"""Shared helpers for study renderers.

Each overlay owns a set of pyqtgraph items it added to the price plot, so a
restudy (or symbol change) can clear just that overlay's output. Color support
includes CSS-style rgba() strings used by the ICT service.
"""

import re

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

_RGBA_RE = re.compile(r"rgba\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)")


def parse_color(value: str, alpha: float | None = None) -> QColor:
    """Return a QColor for hex, named, or rgba() strings."""
    if value.startswith("rgba("):
        match = _RGBA_RE.match(value)
        if match:
            r, g, b, a = (float(part) for part in match.groups())
            color = QColor(int(r), int(g), int(b))
            color.setAlphaF(alpha if alpha is not None else a)
            return color
    color = QColor(value)
    if alpha is not None:
        color.setAlphaF(alpha)
    return color


class StudyOverlay:
    """Base class that tracks items it added to a plot for easy clearing."""

    def __init__(self, plot: pg.PlotWidget):
        self._plot = plot
        self._items: list = []
        # D27.2: D21.4 collapse map for bar-index -> display-x conversion.
        # Set via set_collapse_map; None means the identity (no map yet).
        self._collapse_map = None

    def set_collapse_map(self, collapse_map) -> None:
        """Set the D21.4 display-x map used by _index_to_x (D27.2)."""
        self._collapse_map = collapse_map

    def _index_to_x(self, index, bars) -> float:
        """Map a bar index to the ViewBox x-coordinate (D27.2).

        With a D21.4 collapse map active the x-model is display-x, so the
        index's timestamp is mapped through ``to_display`` (exactly what
        ``DrawingOverlay._ts_to_x`` does); otherwise the raw index is used.
        Out-of-range indices are clamped to the bar list.
        """
        try:
            i = int(index)
        except (TypeError, ValueError):
            return float(index)
        cmap = self._collapse_map
        if not bars:
            return float(i)
        i = min(max(i, 0), len(bars) - 1)
        if cmap is None:
            # Identity: the x-model is raw timestamps (as _ts_to_x does).
            return float(bars[i].ts)
        return float(cmap.to_display(bars[i].ts))

    @staticmethod
    def _pen(color: str, width: float = 1.0, style=Qt.PenStyle.SolidLine):
        return pg.mkPen(parse_color(color), width=width, style=style)

    def clear(self) -> None:
        for item in self._items:
            self._plot.removeItem(item)
        self._items.clear()

    def item_count(self) -> int:
        return len(self._items)

    def add(self, item, zvalue: float | None = None):
        if zvalue is not None:
            item.setZValue(zvalue)
        self._plot.addItem(item)
        self._items.append(item)
        return item

    def add_hline(self, price: float, color: str,
                  style=Qt.PenStyle.SolidLine, width: float = 1.0,
                  label: str | None = None, label_x: float | None = None):
        pen = self._pen(color, width, style)
        line = pg.InfiniteLine(pos=price, angle=0, pen=pen)
        line.setMovable(False)
        self.add(line)
        if label:
            text = pg.TextItem(label, color=color, anchor=(1, 0.5))
            text.setPos(float(label_x) if label_x is not None else float(self._last_index()), price)
            self.add(text)
        return line

    def add_band(self, x1: float, x2: float, bottom: float, top: float,
                 color: str, border: str | None = None, alpha: float = 0.12,
                 border_style=Qt.PenStyle.SolidLine, zvalue: float = -5):
        """A horizontal rectangle over bar range [x1, x2] and prices [b, t]."""
        if top <= bottom or x2 <= x1:
            return None
        x = [x1, x2, x2, x1, x1]
        y = [bottom, bottom, top, top, bottom]
        pen = self._pen(border or color, 0.8, border_style)
        curve = pg.PlotDataItem(x, y, pen=pen, fillLevel=bottom, fillBrush=parse_color(color, alpha))
        self.add(curve, zvalue=zvalue)
        return curve

    def add_segment(self, x1: float, x2: float, price: float, color: str,
                    style=Qt.PenStyle.DashLine, width: float = 1.2,
                    label: str | None = None, zvalue: float = 2):
        """A horizontal line segment (not infinite) from x1 to x2 at ``price``."""
        curve = pg.PlotDataItem([x1, x2], [price, price],
                                pen=self._pen(color, width, style))
        self.add(curve, zvalue=zvalue)
        if label:
            text = pg.TextItem(label, color=color, anchor=(0.5, 1.0))
            text.setPos(x2, price)
            self.add(text)
        return curve

    def _last_index(self) -> int:
        view_range = self._plot.getViewBox().viewRange()
        return int(view_range[0][1]) if view_range and view_range[0] else 0