"""Session shading overlay — pre/post market bands."""

import pyqtgraph as pg
from ui.overlays.base import StudyOverlay, parse_color

ORANGE = "#f59e0b"
BLUE = "#60a5fa"


class SessionOverlay(StudyOverlay):
    """Renders pre/post market vertical bands behind candles."""

    def render(self, bands: list) -> None:
        self.clear()
        for band in bands:
            kind = band.get("kind")
            color = ORANGE if kind == "pre" else BLUE
            start = float(band["start_ts"])
            end = float(band["end_ts"])
            if end <= start:
                continue
            # LinearRegionItem spans full plot height vertically
            brush = parse_color(color, 0.10)
            region = pg.LinearRegionItem(
                values=(start, end),
                orientation="vertical",
                movable=False,
                brush=brush,
                pen=pg.mkPen(None),
            )
            region.setZValue(-10)
            # Prevent region lines from being hoverable/movable
            region.setMovable(False)
            self.add(region, zvalue=-10)
