"""ui/chart_view.py — the ChartView seam (P6-02 / Phase 1a, D47.1; P6-13).

The chart stack lives behind this strangler boundary: a ``ChartView``
protocol, ``DrawingController`` / ``AlarmController`` carrying the exact
pre-D47 signal surface, and a ``create_chart_view`` factory that now resolves
to the LWC engine only.

P6-13 / Phase 11 removed the pyqtgraph engine. **The removal gate is
owner-waived, not satisfied**: ``docs/build/gate_P6_T13.md`` records the
2026-10-27 owner approval of the deletion, the live-session sign-off as
WAIVED, NOT SATISFIED, and the oracle decision RETIRE. There is no runtime
engine switch left — returning to pyqtgraph is a ``git revert`` of the removal
commit.

Engine selection: ``NDT_CHART_ENGINE`` and the persisted ``chart/engine``
value are still read by deployment tooling, but they no longer select a
renderer: this module always returns the LWC view, which is the only engine.

Renderer-only boundary: this module imports nothing beyond Qt and the standard
library at module scope. The LWC driver is imported inside the factory so a
process that never builds a chart never touches the WebEngine host.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PyQt6.QtCore import QObject, pyqtSignal

ENGINE_ENV_VAR = "NDT_CHART_ENGINE"
ENGINE_LWC = "lwc"

SETTINGS_ORGANIZATION = "NDThinkChart"
SETTINGS_APPLICATION = "NDThinkChart"
SETTINGS_ENGINE_KEY = "chart/engine"


@runtime_checkable
class ChartView(Protocol):
    """Engine-neutral chart surface the LWC renderer satisfies."""

    def update_bars(self, bars: list) -> None:
        """Full history replace."""
        ...  # noqa: E704

    def update_last_bar(self, bar, is_new_candle: bool) -> None:
        """Intra-bar live update (replace forming bar or append new period)."""
        ...  # noqa: E704

    def set_symbol(self, symbol: str) -> None:
        """Bind the view to a symbol."""
        ...  # noqa: E704

    def set_timeframe(self, timeframe: str) -> None:
        """Bind the view to a timeframe."""
        ...  # noqa: E704


class DrawingController(QObject):
    """Signal surface for drawings — exactly the pre-D47 overlay surface.

    Optionally wraps a drawing surface and forwards each of its signals;
    standalone (no surface) when the view publishes drawings through its own
    envelope.
    """

    created = pyqtSignal(object)          # Drawing (no id yet)
    updated = pyqtSignal(int, dict, str)  # drawing_id, new payload, color
    deleted = pyqtSignal(int)             # drawing_id
    selection_changed = pyqtSignal(int)   # drawing id or -1
    mode_changed = pyqtSignal(str)        # active tool name
    settings_requested = pyqtSignal(object)  # Drawing opened for editing

    def __init__(self, overlay=None, parent=None):
        super().__init__(parent)
        self._overlay = overlay
        if overlay is not None:
            overlay.created.connect(self.created.emit)
            overlay.updated.connect(self.updated.emit)
            overlay.deleted.connect(self.deleted.emit)
            overlay.selection_changed.connect(self.selection_changed.emit)
            overlay.mode_changed.connect(self.mode_changed.emit)
            overlay.settings_requested.connect(self.settings_requested.emit)

    @property
    def overlay(self):
        """The wrapped surface, or ``None`` when standalone."""
        return self._overlay


class AlarmController(QObject):
    """Signal surface for alarms — exactly the pre-D47 overlay surface.

    Optionally wraps an alarm surface and forwards each of its signals;
    standalone (no surface) when the view publishes alarms through its own
    envelope.
    """

    create_requested = pyqtSignal(float)  # price for a new alarm
    moved = pyqtSignal(int, float)        # alarm_id, new price
    mute_toggled = pyqtSignal(int, bool)  # alarm_id, sound
    rearm_requested = pyqtSignal(int)     # alarm_id
    delete_requested = pyqtSignal(int)    # alarm_id

    def __init__(self, overlay=None, parent=None):
        super().__init__(parent)
        self._overlay = overlay
        if overlay is not None:
            overlay.create_requested.connect(self.create_requested.emit)
            overlay.moved.connect(self.moved.emit)
            overlay.mute_toggled.connect(self.mute_toggled.emit)
            overlay.rearm_requested.connect(self.rearm_requested.emit)
            overlay.delete_requested.connect(self.delete_requested.emit)

    @property
    def overlay(self):
        """The wrapped surface, or ``None`` when standalone."""
        return self._overlay


def create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView:
    """Create the chart view: the LWC engine, the only engine since P6-13."""
    from ui.lwc_view import LwcChartView

    return LwcChartView(tz_offset=tz_offset, editable=editable)
