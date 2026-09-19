"""VIX standard-deviation bands renderer."""

from PyQt6.QtCore import Qt

from ui.overlays.base import StudyOverlay

STYLE_MAP = {
    "solid": Qt.PenStyle.SolidLine,
    "dashed": Qt.PenStyle.DashLine,
    "dotted": Qt.PenStyle.DotLine,
}


class VixOverlay(StudyOverlay):
    """Draws price+sigma lines with right-edge labels, distinct per sigma."""

    def render(self, result: dict, bar_count: int) -> None:
        self.clear()
        for level in result.get("levels", []):
            style = STYLE_MAP.get(level.get("lineStyle", "solid"), Qt.PenStyle.SolidLine)
            width = float(level.get("lineWidth", 1))
            price = level["price"]
            sigma = level.get("sigma", 0)
            label = f"0σ {price:.2f}" if sigma == 0 else f"{sigma:+.2g}σ {price:.2f}"
            self.add_hline(price, level["color"], style=style, width=width,
                           label=label, label_x=float(max(bar_count - 1, 0)))