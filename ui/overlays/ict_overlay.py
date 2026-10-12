"""ICT concept renderer for ui/overlays.

Renders every concept produced by services.ict_service.calculate_ict_concepts:
market structures (MSS/BOS), order blocks (incl. breakers), fair value gaps,
BPR overlap, liquidity pools, volume imbalances, opening gaps (NWOG/NDOG)
with midpoint lines, killzone vertical regions, and displacement markers.

D27.2: every bar index is mapped to display-x via the D21.4 collapse map
(``StudyOverlay._index_to_x``) — raw indices would render off-screen.
"""

import pyqtgraph as pg
from PyQt6.QtCore import Qt

from ui.overlays.base import StudyOverlay, parse_color

VI_COLOR = "#e879f9"


class ICTStudyOverlay(StudyOverlay):
    def render(self, result: dict, bars: list) -> None:
        self.clear()
        bar_count = len(bars)
        last = self._index_to_x(bar_count - 1, bars) if bar_count else 0.0

        self._render_structures(result.get("marketStructures", []), bars)
        self._render_order_blocks(result.get("orderBlocks", []), last, bars)
        self._render_fvgs(result.get("fairValueGaps", []), bars)
        self._render_pools(result.get("liquidityPools", []), last, bars)
        self._render_volume_imbalances(result.get("volumeImbalances", []), last,
                                       bars)
        self._render_opening_gaps(result.get("openingGaps", []), last, bars)
        self._render_displacements(result.get("displacements", []), bars)
        self._render_killzones(result.get("killzones", []), bars)

    def _render_structures(self, structures: list, bars: list) -> None:
        for structure in structures:
            x1 = self._index_to_x(structure["startIndex"], bars)
            x2 = self._index_to_x(structure["endIndex"], bars)
            self.add_segment(x1, x2, structure["price"], structure["color"],
                             style=Qt.PenStyle.DashLine, width=1.2,
                             label=structure["type"], zvalue=3)

    def _render_order_blocks(self, blocks: list, last: float,
                             bars: list) -> None:
        for block in blocks:
            x1 = self._index_to_x(block["barIndex"], bars)
            x2 = last
            color = block.get("breakColor") if block.get("isBreaker") else block["color"]
            self.add_band(x1, x2, block["bottom"], block["top"], color,
                          border=color, alpha=0.18, zvalue=-3)

    def _render_fvgs(self, fvgs: list, bars: list) -> None:
        for fvg in fvgs:
            color = fvg["color"]
            alpha = 0.06 if fvg.get("isMitigated") else 0.14
            border = color
            style = Qt.PenStyle.DotLine if fvg.get("isBroken") else Qt.PenStyle.SolidLine
            self.add_band(self._index_to_x(fvg["startIndex"], bars),
                          self._index_to_x(fvg["endIndex"], bars),
                          fvg["bottom"], fvg["top"], color,
                          border=border, alpha=alpha, border_style=style, zvalue=-4)

    def _render_pools(self, pools: list, last: float, bars: list) -> None:
        for pool in pools:
            color = pool["color"]
            x1 = self._index_to_x(pool["startIndex"], bars)
            self.add_band(x1, last, pool["bottom"], pool["top"], color,
                          border=color, alpha=0.07, zvalue=-6)
            style = Qt.PenStyle.DashLine if not pool.get("isSwept") else Qt.PenStyle.DotLine
            self.add_segment(x1, last, pool["levelPrice"], color,
                             style=style, width=1.0, label=pool["type"], zvalue=-2)

    def _render_volume_imbalances(self, vis: list, last: float,
                                  bars: list) -> None:
        for vi in vis:
            # D27.2: the ±1 bar window is applied in *index* space, then both
            # ends are mapped to display-x (window width in display-x is not
            # constant when time is collapsed).
            try:
                raw = int(vi["barIndex"])
            except (TypeError, ValueError):
                raw = 0
            x1 = self._index_to_x(max(raw - 1, 0), bars)
            x2 = self._index_to_x(raw + 1, bars)
            if x1 > x2:
                x1, x2 = x2, x1
            color = vi["color"] or VI_COLOR
            self.add_band(x1, x2, vi["bottom"], vi["top"], color,
                          border=color, alpha=0.35, zvalue=-4)

    def _render_opening_gaps(self, gaps: list, last: float,
                             bars: list) -> None:
        for gap in gaps:
            x1 = self._index_to_x(gap["startIndex"], bars)
            color = gap["color"]
            self.add_band(x1, last, gap["bottom"], gap["top"], color,
                          border=color, alpha=0.10, zvalue=-5)
            self.add_segment(x1, last, gap["midpoint"], color,
                             style=Qt.PenStyle.DotLine, width=1.0, zvalue=-2)

    def _render_displacements(self, displacements: list, bars: list) -> None:
        if not displacements:
            return
        spots = []
        for item in displacements:
            up = item["direction"] in ("up", "bullish")
            color = item["color"] if item.get("color") else (
                "#34d399" if up else "#f87171")
            spots.append({
                "pos": (self._index_to_x(item["barIndex"], bars), item["price"]),
                "brush": parse_color(color),
                "symbol": "t" if up else "t1",
                "size": 10,
            })
        scatter = pg.ScatterPlotItem(spots, pxMode=True)
        self.add(scatter, zvalue=4)

    def _render_killzones(self, zones: list, bars: list) -> None:
        for zone in zones:
            region = pg.LinearRegionItem(
                values=(self._index_to_x(zone["startIndex"], bars),
                        self._index_to_x(zone["endIndex"], bars)),
                orientation="vertical",
                brush=parse_color(zone["color"]),
                pen=pg.mkPen(None),
                movable=False,
            )
            region.setZValue(-8)
            self.add(region)
