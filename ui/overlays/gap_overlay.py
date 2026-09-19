"""RTH gap staircase renderer."""

from PyQt6.QtCore import Qt

from ui.overlays.base import StudyOverlay, parse_color

UP_COLOR = "#089981"
UP_BRUSH = "#064e3b"
DOWN_COLOR = "#f23645"
DOWN_BRUSH = "#7f1d1d"


class RthGapOverlay(StudyOverlay):
    """Draws each gap step as its own horizontal band over its bar range."""

    def render(self, gaps: list, bar_count: int) -> None:
        self.clear()
        for gap in gaps:
            steps = gap.get("steps") or []
            for step in steps:
                bottom = step.get("bottom", gap.get("currentBottom", gap.get("initialBottom")))
                top = step.get("top", gap.get("currentTop", gap.get("initialTop")))
                x1 = float(step.get("startBarIndex", gap.get("startBarIndex", 0)))
                x2 = float(min(step.get("endBarIndex", bar_count - 1), bar_count - 1))
                if top <= bottom:
                    continue
                if gap.get("isUp"):
                    color, border = UP_COLOR, UP_COLOR
                    brush = parse_color(UP_BRUSH, 0.32 if gap.get("isFullyFilled") else 0.55)
                else:
                    color, border = DOWN_COLOR, DOWN_COLOR
                    brush = parse_color(DOWN_BRUSH, 0.32 if gap.get("isFullyFilled") else 0.55)
                self.add_band(x1, x2, bottom, top, color, border, alpha=0.0,
                              border_style=Qt.PenStyle.DotLine if gap.get("isFullyFilled") else Qt.PenStyle.SolidLine)
                if self._items:
                    self._items[-1].setFillBrush(brush)