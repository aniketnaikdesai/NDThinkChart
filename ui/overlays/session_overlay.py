"""Session shading overlay — pre/post market bands."""

import pyqtgraph as pg
from ui.overlays.base import StudyOverlay, parse_color

ORANGE = "#f59e0b"
BLUE = "#60a5fa"


class SessionOverlay(StudyOverlay):
    """Renders pre/post market vertical bands behind candles.

    ``bands`` carry ``start_ts``/``end_ts`` in the *ViewBox x-model*: after the
    D21.4 display-x collapse the caller (``ChartPanel._render_sessions``) passes
    already-mapped display-x values, so each band lands on the session actually
    shown and no band covers a collapsed non-trading gap (AC-D21.4.3).
    """

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
