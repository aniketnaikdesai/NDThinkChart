"""
candlestick_item.py
Custom pyqtgraph GraphicsObject supporting 5 render modes:
  'candles'  — filled green/red bodies with wicks
  'hollow'   — outline-only bodies (TOS hollow candles)
  'heikin'   — Heikin-Ashi computed in the data layer
  'line'     — close-price line
  'area'     — close-price filled area
"""

from enum import Enum
from typing import List, Tuple, Optional
import pyqtgraph as pg
from PyQt6.QtGui import QPicture, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt6.QtCore import QRectF, QPointF

GREEN  = QColor('#34d399')  # emerald-400
RED    = QColor('#f87171')  # red-400
LINE_C = QColor('#60a5fa')  # blue-400 — used for line/area mode


class ChartMode(str, Enum):
    CANDLES = "candles"
    HOLLOW  = "hollow"
    HEIKIN  = "heikin"
    LINE    = "line"
    AREA    = "area"


def _compute_heikin(data: List[Tuple]) -> List[Tuple]:
    """
    data: list of (t, o, h, l, c)
    Returns transformed Heikin-Ashi (t, ha_o, ha_h, ha_l, ha_c).
    """
    result = []
    prev_ha_o, prev_ha_c = None, None
    for (t, o, h, l, c) in data:
        ha_c = (o + h + l + c) / 4
        ha_o = ((prev_ha_o + prev_ha_c) / 2) if prev_ha_o is not None else (o + c) / 2
        ha_h = max(h, ha_o, ha_c)
        ha_l = min(l, ha_o, ha_c)
        result.append((t, ha_o, ha_h, ha_l, ha_c))
        prev_ha_o, prev_ha_c = ha_o, ha_c
    return result


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data: List[Tuple], mode: ChartMode = ChartMode.CANDLES):
        super().__init__()
        self._raw_data: List[Tuple] = data
        self._mode = mode
        self._picture = QPicture()
        self._generate()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_data(self, data: List[Tuple], mode: Optional[ChartMode] = None):
        self._raw_data = data
        if mode is not None:
            self._mode = mode
        self._generate()
        self.update()

    def set_mode(self, mode: ChartMode):
        self._mode = mode
        self._generate()
        self.update()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _generate(self):
        self._picture = QPicture()
        if not self._raw_data:
            return

        p = QPainter(self._picture)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        if self._mode in (ChartMode.CANDLES, ChartMode.HOLLOW):
            self._draw_candles(p, hollow=(self._mode == ChartMode.HOLLOW))
        elif self._mode == ChartMode.HEIKIN:
            self._draw_candles(p, hollow=False, data=_compute_heikin(self._raw_data))
        elif self._mode == ChartMode.LINE:
            self._draw_line(p)
        elif self._mode == ChartMode.AREA:
            self._draw_area(p)

        p.end()

    def _draw_candles(self, p: QPainter, hollow: bool, data: Optional[List[Tuple]] = None):
        data = data or self._raw_data
        # Compute candle half-width as a fraction of typical bar spacing
        if len(data) > 1:
            # Use median time diff between bars to set width (e.g., 40% of spacing)
            time_diffs = [data[i][0] - data[i-1][0] for i in range(1, len(data))]
            time_diffs.sort()
            median_diff = time_diffs[len(time_diffs)//2]
            w = median_diff * 0.4  # half-width = 40% of spacing
        else:
            w = 0.25  # fallback for single bar

        # Body pens (slightly thicker for visible edges)
        green_pen   = QPen(GREEN); green_pen.setWidthF(1.0)
        red_pen     = QPen(RED);   red_pen.setWidthF(1.0)
        # Wick pen (thin, 0.5px - half the body width)
        wick_pen    = QPen(QColor('#9ca3af')); wick_pen.setWidthF(0.5)  # gray-400

        green_brush = QBrush(GREEN)
        red_brush   = QBrush(RED)
        no_brush    = QBrush(QColor(0, 0, 0, 0))

        for (t, o, h, l, c) in data:
            bull = c >= o
            body_pen   = green_pen if bull else red_pen
            body_brush = (no_brush if hollow else (green_brush if bull else red_brush))
            # Wick (thin, neutral color)
            p.setPen(wick_pen)
            p.drawLine(QPointF(t, l), QPointF(t, h))
            # Body
            body_top    = max(o, c)
            body_bottom = min(o, c)
            body_h = body_top - body_bottom
            p.setPen(body_pen)
            p.setBrush(body_brush)
            if body_h < 0.0001:
                p.drawLine(QPointF(t - w, o), QPointF(t + w, o))
            else:
                p.drawRect(QRectF(t - w, body_bottom, w * 2, body_h))

    def _draw_line(self, p: QPainter):
        pen = QPen(LINE_C)
        pen.setWidthF(1.2)
        p.setPen(pen)
        pts = [QPointF(t, c) for (t, o, h, l, c) in self._raw_data]
        for i in range(1, len(pts)):
            p.drawLine(pts[i - 1], pts[i])

    def _draw_area(self, p: QPainter):
        if len(self._raw_data) < 2:
            return
        path = QPainterPath()
        first_t, _, _, _, first_c = self._raw_data[0]
        path.moveTo(first_t, 0)
        path.lineTo(first_t, first_c)
        for (t, o, h, l, c) in self._raw_data:
            path.lineTo(t, c)
        last_t = self._raw_data[-1][0]
        path.lineTo(last_t, 0)
        path.closeSubpath()

        fill = QColor(LINE_C)
        fill.setAlpha(40)
        p.setBrush(QBrush(fill))
        pen = QPen(LINE_C)
        pen.setWidthF(1.2)
        p.setPen(pen)
        p.drawPath(path)

    # ── pyqtgraph overrides ────────────────────────────────────────────────────

    def paint(self, painter, option, widget):
        painter.drawPicture(0, 0, self._picture)

    def boundingRect(self):
        return QRectF(self._picture.boundingRect())
