"""
event_marker_overlay.py — D38 (38b.2).

Renders corporate-event markers (earnings / dividend / split) on the price
plot's time axis with distinct icon/color per event type, plus a countdown
label ("Earnings in 3d") for the next upcoming event.

Markers are keyed by event id (not date) so date corrections move the marker
instead of duplicating it. Positioning follows the AlarmOverlay pattern:
event dates map to bars, bars map through the collapse map to display-x.
"""

from datetime import date, datetime, timezone

import pyqtgraph as pg
from PyQt6.QtCore import QObject

# Distinct icon + color per event type (owner decision 2026-10-13).
EVENT_STYLE = {
    "earnings": {"glyph": "◆ E", "color": "#fbbf24", "label": "Earnings"},
    "dividend": {"glyph": "● D", "color": "#4ade80", "label": "Dividend"},
    "split": {"glyph": "▲ S", "color": "#60a5fa", "label": "Split"},
}


def _date_to_ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day,
                        tzinfo=timezone.utc).timestamp())


class EventMarkerOverlay(QObject):
    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self._plot = plot
        self._view = plot.getViewBox()
        self._events: list = []
        self._items: dict[str, pg.TextItem] = {}
        self._bars: list = []
        self._collapse_map = None
        self._unavailable: bool = False

        self._countdown = pg.TextItem(anchor=(0, 0))
        self._countdown.setZValue(10)
        self._view.addItem(self._countdown)
        self._countdown.hide()

        self._view.sigYRangeChanged.connect(self._reposition_all)
        self._view.sigXRangeChanged.connect(self._reposition_all)

    # ── Public API ───────────────────────────────────────────────────

    def set_bars(self, bars) -> None:
        self._bars = list(bars) if bars else []
        self._reposition_all()

    def set_collapse_map(self, collapse_map) -> None:
        self._collapse_map = collapse_map
        self._reposition_all()

    def set_events(self, events, unavailable: bool = False) -> None:
        """Replace the event set; diff by id so corrections move markers."""
        self._unavailable = bool(unavailable)
        self._events = list(events) if events else []
        self._reposition_all()

    def event_count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        for item in self._items.values():
            self._view.removeItem(item)
        self._items.clear()
        self._events = []
        self._countdown.hide()

    # ── Positioning ──────────────────────────────────────────────────

    def _display_x(self, ts: int) -> float | None:
        cmap = self._collapse_map
        if cmap is None:
            return None
        try:
            return float(cmap.to_display(ts))
        except Exception:
            return None

    def _x_for_event(self, ev) -> float | None:
        """Display-x for an event: first bar on/after the event date; future
        events sit one bar-width past the last bar."""
        if not self._bars:
            return None
        day_ts = _date_to_ts(ev.date)
        for bar in self._bars:
            try:
                if int(bar.ts) >= day_ts:
                    return self._display_x(int(bar.ts))
            except (AttributeError, TypeError, ValueError):
                continue
        # Future event (or beyond data): one step past the last bar.
        try:
            last_x = self._display_x(int(self._bars[-1].ts))
        except (AttributeError, TypeError, ValueError, IndexError):
            return None
        return None if last_x is None else last_x + 1.0

    def _reposition_all(self) -> None:
        # Drop stale markers (diff by id).
        live_ids = {e.id for e in self._events}
        for eid in [k for k in self._items if k not in live_ids]:
            self._view.removeItem(self._items.pop(eid))
        # (Re)build + position.
        try:
            _yrange = self._view.viewRange()[1]
            top = _yrange[1]
            x_range = self._view.viewRange()[0]
        except Exception:
            return
        for ev in self._events:
            style = EVENT_STYLE.get(ev.type)
            if style is None:
                continue
            item = self._items.get(ev.id)
            if item is None:
                item = pg.TextItem(text=style["glyph"], color=style["color"],
                                   anchor=(0.5, 1.0))
                item.setZValue(10)
                self._items[ev.id] = item
                self._view.addItem(item)
            x = self._x_for_event(ev)
            if x is None:
                item.hide()
                continue
            item.setPos(x, top)
            item.show()
            item.setToolTip(self._tooltip_for(ev, style))
        self._update_countdown(x_range[0], top)

    def _tooltip_for(self, ev, style: dict) -> str:
        lines = [f"{style['label']} — {ev.date.isoformat()}",
                 f"Source: {ev.source}"]
        details = getattr(ev, "details", {}) or {}
        if ev.type == "dividend" and details.get("amount") is not None:
            lines.append(f"Amount: {details['amount']}")
        if ev.type == "earnings":
            if details.get("estimate") is not None:
                lines.append(f"EPS est: {details['estimate']}")
            if details.get("reported") is not None:
                lines.append(f"Reported: {details['reported']}")
        if ev.type == "split" and details.get("ratio") is not None:
            lines.append(f"Ratio: {details['ratio']}")
        return "\n".join(lines)

    def _update_countdown(self, left_x: float, top: float) -> None:
        """Countdown label for the next upcoming event ("Earnings in 3d").
        Hidden when there is no upcoming event (edge case)."""
        today = date.today()
        upcoming = [e for e in self._events if e.date >= today]
        if self._unavailable and not self._events:
            self._countdown.setText("Event data unavailable",
                                    color="#f87171")
            self._countdown.setPos(left_x, top)
            self._countdown.show()
            return
        if not upcoming:
            self._countdown.hide()
            return
        nxt = min(upcoming, key=lambda e: e.date)
        days = (nxt.date - today).days
        style = EVENT_STYLE.get(nxt.type, {})
        label = style.get("label", nxt.type)
        when = "today" if days == 0 else f"in {days}d"
        self._countdown.setText(f"{label} {when}",
                                color=style.get("color", "#e5e7eb"))
        self._countdown.setPos(left_x, top)
        self._countdown.show()

    def countdown_text(self) -> str:
        """Current countdown label text (for tests)."""
        try:
            return self._countdown.toPlainText()
        except Exception:
            return ""
