"""ui/chart_view.py — the ChartView seam (P6-02 / Phase 1a, D47.1).

The chart stack migrates behind this strangler boundary: a ``ChartView``
protocol both engines satisfy, per-engine view classes, ``DrawingController``
/ ``AlarmController`` carrying the exact pre-D47 signal surface, and a
``create_chart_view`` factory that selects the engine.

Engine selection: ``NDT_CHART_ENGINE`` is read first; when it is unset or
blank the persisted ``QSettings`` value (``chart/engine``) is used; when both
are unset — or the resolved value is anything other than ``"lwc"`` — the
factory returns the pyqtgraph view. The LWC view is selected **only** for the
``"lwc"`` value. An unknown value never blanks the chart: it falls back to
pyqtgraph, which stays present and default through cutover.

Renderer-only boundary: this module imports nothing beyond Qt, the standard
library and the existing pyqtgraph panel. It creates no persistence, no
network surface and no windowing chrome of its own.

The LWC view here is a stub behind the factory: it owns the ``ChartView``
state and the controller signal surface so session wiring keeps working on
either engine, but render parity is later-phase work (P6-05+), not this task.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QWidget

from ui.chart_panel import ChartPanel

ENGINE_ENV_VAR = "NDT_CHART_ENGINE"
ENGINE_PYQTGRAPH = "pyqtgraph"
ENGINE_LWC = "lwc"

SETTINGS_ORGANIZATION = "NDThinkChart"
SETTINGS_APPLICATION = "NDThinkChart"
SETTINGS_ENGINE_KEY = "chart/engine"


@runtime_checkable
class ChartView(Protocol):
    """Engine-neutral chart surface both renderers satisfy."""

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

    Optionally wraps a pyqtgraph ``DrawingOverlay`` and forwards each of its
    signals; standalone (no overlay) on engines whose overlay lands later.
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
        """The wrapped overlay, or ``None`` when standalone."""
        return self._overlay


class AlarmController(QObject):
    """Signal surface for alarms — exactly the pre-D47 overlay surface.

    Optionally wraps a pyqtgraph ``AlarmOverlay`` and forwards each of its
    signals; standalone (no overlay) on engines whose overlay lands later.
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
        """The wrapped overlay, or ``None`` when standalone."""
        return self._overlay


class PyqtgraphChartView(ChartPanel):
    """The default engine view: the existing pyqtgraph panel behind the seam."""

    ENGINE_NAME = ENGINE_PYQTGRAPH

    def __init__(self, tz_offset: float = 0.0, editable: bool = True):
        super().__init__(tz_offset=tz_offset, editable=editable)
        self.drawing_controller = DrawingController(
            self.drawing_overlay, parent=self
        )
        self.alarm_controller = AlarmController(
            self.alarm_overlay, parent=self
        )

    @property
    def tz_offset(self) -> float:
        return self._tz_offset

    @property
    def editable(self) -> bool:
        return self._editable

    # ── ChartView protocol ──────────────────────────────────────────────
    # ``update_bars`` is the engine-neutral history replace; on the pyqtgraph
    # engine it maps onto ``ChartPanel.update_chart`` (signature unchanged).

    def update_bars(self, bars: list) -> None:
        self.update_chart(bars)


class LwcChartView(QWidget):
    """The LWC engine view — a stub behind the factory (P6-02).

    Owns the ``ChartView`` state and the controller signal surface so session
    wiring keeps working on either engine. Render parity lands in later
    phases; this stub never blanks: it always accepts bars and live ticks.
    """

    ENGINE_NAME = ENGINE_LWC

    def __init__(
        self,
        tz_offset: float = 0.0,
        editable: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._tz_offset = tz_offset
        self._editable = editable
        self._bars: list = []
        self._symbol: str = ""
        self._timeframe = None
        self.drawing_controller = DrawingController(parent=self)
        self.alarm_controller = AlarmController(parent=self)

    @property
    def tz_offset(self) -> float:
        return self._tz_offset

    @property
    def editable(self) -> bool:
        return self._editable

    # ── ChartView protocol ──────────────────────────────────────────────

    def update_bars(self, bars: list) -> None:
        self._bars = list(bars) if bars else []

    def update_last_bar(self, bar, is_new_candle: bool) -> None:
        if not self._bars:
            if is_new_candle:
                self.update_bars([bar])
            return
        if self._bars[-1].ts != bar.ts:
            self._bars.append(bar)
        else:
            self._bars[-1] = bar

    def set_symbol(self, symbol: str) -> None:
        self._symbol = symbol

    def set_timeframe(self, timeframe: str) -> None:
        self._timeframe = timeframe


def _read_persisted_engine() -> str:
    """Return the persisted ``QSettings`` engine value (``""`` when unset)."""
    try:
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        value = settings.value(SETTINGS_ENGINE_KEY, "", type=str)
    except Exception:
        return ""
    return value if isinstance(value, str) else ""


def _resolve_engine_name() -> str:
    """Resolve the engine name: env first, then the persisted override.

    Returns the normalized (stripped, lower-cased) value, or ``""`` when
    neither source names an engine. Callers treat anything other than
    ``"lwc"`` as pyqtgraph — unknown values fall back, never blank.
    """
    raw = os.getenv(ENGINE_ENV_VAR)
    if raw is None or not str(raw).strip():
        raw = _read_persisted_engine()
    return str(raw or "").strip().lower()


def create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView:
    """Create the chart view for the resolved engine.

    Returns the LWC view only for the ``"lwc"`` value; unset, blank, unknown
    and ``"pyqtgraph"`` values all return the pyqtgraph view (never blank).
    """
    if _resolve_engine_name() == ENGINE_LWC:
        return LwcChartView(tz_offset=tz_offset, editable=editable)
    return PyqtgraphChartView(tz_offset=tz_offset, editable=editable)
