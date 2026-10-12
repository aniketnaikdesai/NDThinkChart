"""VIX standard-deviation bands renderer.

D27.2: the label anchor is mapped to display-x via the D21.4 collapse map
(``StudyOverlay._index_to_x``) — a raw bar index would render off-screen.
"""

from PyQt6.QtCore import Qt

from ui.overlays.base import StudyOverlay

STYLE_MAP = {
    "solid": Qt.PenStyle.SolidLine,
    "dashed": Qt.PenStyle.DashLine,
    "dotted": Qt.PenStyle.DotLine,
}


class VixOverlay(StudyOverlay):
    """Draws price+sigma lines with right-edge labels, distinct per sigma."""

    def render(self, result: dict, bars: list) -> None:
        self.clear()
        bar_count = len(bars)
        # D27.2: label sits at the display-x of the last bar, not its index.
        label_x = self._index_to_x(bar_count - 1, bars) if bar_count else 0.0
        for level in result.get("levels", []):
            style = STYLE_MAP.get(level.get("lineStyle", "solid"), Qt.PenStyle.SolidLine)
            width = float(level.get("lineWidth", 1))
            price = level["price"]
            sigma = level.get("sigma", 0)
            label = f"0σ {price:.2f}" if sigma == 0 else f"{sigma:+.2g}σ {price:.2f}"
            self.add_hline(price, level["color"], style=style, width=width,
                           label=label, label_x=label_x)
