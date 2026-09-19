"""ICT concept renderer for ui/overlays.

Renders every concept produced by services.ict_service.calculate_ict_concepts:
market structures (MSS/BOS), order blocks (incl. breakers), fair value gaps,
BPR overlap, liquidity pools, volume imbalances, opening gaps (NWOG/NDOG)
with midpoint lines, killzone vertical regions, and displacement markers.
"""

import pyqtgraph as pg
from PyQt6.QtCore import Qt

from ui.overlays.base import StudyOverlay, parse_color

VI_COLOR = "#e879f9"


class ICTStudyOverlay(StudyOverlay):
    def render(self, result: dict, bar_count: int) -> None:
        self.clear()
        last = float(max(bar_count - 1, 0))

        self._render_structures(result.get("marketStructures", []), last)
        self._render_order_blocks(result.get("orderBlocks", []), last)
        self._render_fvgs(result.get("fairValueGaps", []), last)
        self._render_pools(result.get("liquidityPools", []), last)
        self._render_volume_imbalances(result.get("volumeImbalances", []), last)
        self._render_opening_gaps(result.get("openingGaps", []), last)
        self._render_displacements(result.get("displacements", []))
        self._render_killzones(result.get("killzones", []))

    def _render_structures(self, structures: list, last: float) -> None:
        for structure in structures:
            x1 = float(structure["startIndex"])
            x2 = float(structure["endIndex"])
            self.add_segment(x1, x2, structure["price"], structure["color"],
                             style=Qt.PenStyle.DashLine, width=1.2,
                             label=structure["type"], zvalue=3)

    def _render_order_blocks(self, blocks: list, last: float) -> None:
        for block in blocks:
            x1 = float(block["barIndex"])
            x2 = last
            color = block.get("breakColor") if block.get("isBreaker") else block["color"]
            self.add_band(x1, x2, block["bottom"], block["top"], color,
                          border=color, alpha=0.18, zvalue=-3)

    def _render_fvgs(self, fvgs: list, last: float) -> None:
        for fvg in fvgs:
            color = fvg["color"]
            alpha = 0.06 if fvg.get("isMitigated") else 0.14
            border = color
            style = Qt.PenStyle.DotLine if fvg.get("isBroken") else Qt.PenStyle.SolidLine
            self.add_band(float(fvg["startIndex"]), float(fvg["endIndex"]),
                          fvg["bottom"], fvg["top"], color,
                          border=border, alpha=alpha, border_style=style, zvalue=-4)

    def _render_pools(self, pools: list, last: float) -> None:
        for pool in pools:
            color = pool["color"]
            x1 = float(pool["startIndex"])
            self.add_band(x1, last, pool["bottom"], pool["top"], color,
                          border=color, alpha=0.07, zvalue=-6)
            style = Qt.PenStyle.DashLine if not pool.get("isSwept") else Qt.PenStyle.DotLine
            self.add_segment(x1, last, pool["levelPrice"], color,
                             style=style, width=1.0, label=pool["type"], zvalue=-2)

    def _render_volume_imbalances(self, vis: list, last: float) -> None:
        for vi in vis:
            idx = float(vi["barIndex"])
            x1 = max(idx - 1.0, 0.0)
            x2 = min(idx + 1.0, last)
            color = vi["color"] or VI_COLOR
            self.add_band(x1, x2, vi["bottom"], vi["top"], color,
                          border=color, alpha=0.35, zvalue=-4)

    def _render_opening_gaps(self, gaps: list, last: float) -> None:
        for gap in gaps:
            x1 = float(gap["startIndex"])
            color = gap["color"]
            self.add_band(x1, last, gap["bottom"], gap["top"], color,
                          border=color, alpha=0.10, zvalue=-5)
            self.add_segment(x1, last, gap["midpoint"], color,
                             style=Qt.PenStyle.DotLine, width=1.0, zvalue=-2)

    def _render_displacements(self, displacements: list) -> None:
        if not displacements:
            return
        spots = []
        for item in displacements:
            up = item["direction"] in ("up", "bullish")
            color = item["color"] if item.get("color") else (
                "#34d399" if up else "#f87171")
            spots.append({
                "pos": (float(item["barIndex"]), item["price"]),
                "brush": parse_color(color),
                "symbol": "t" if up else "t1",
                "size": 10,
            })
        scatter = pg.ScatterPlotItem(spots, pxMode=True)
        self.add(scatter, zvalue=4)

    def _render_killzones(self, zones: list) -> None:
        for zone in zones:
            region = pg.LinearRegionItem(
                values=(zone["startIndex"], zone["endIndex"]),
                orientation="vertical",
                brush=parse_color(zone["color"]),
                pen=pg.mkPen(None),
                movable=False,
            )
            region.setZValue(-8)
            self.add(region)