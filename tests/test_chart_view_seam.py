"""tests/test_chart_view_seam.py — P6-T02 seam tests (AC-D47.1, AC3, AC4).

T11 (AC1): factory selection over ``NDT_CHART_ENGINE`` / the ``QSettings``
equivalent — unset/unknown/pyqtgraph select pyqtgraph, only ``lwc`` selects
the LWC view, never blank; ``tz_offset``/``editable`` propagate.
T12 (AC2): per-controller signal-signature assertions against the frozen
pre-D47 surface captured from the pyqtgraph overlays, on both engines.
T13 (AC3): renderer-only boundary — the seam module stays clear of the
broker boundary, persistence, chrome and order-code surfaces; pyqtgraph
stays present and default.
T14 (AC4): the parity-matrix seam record reflects this wave with no Done
row regressed.
"""

import importlib
import os

import pytest
from PyQt6.QtCore import QObject, QMetaMethod, QSettings
from PyQt6.QtWidgets import QWidget

from ui.chart_panel import ChartPanel
from ui.alarm_overlay import AlarmOverlay
from ui.drawing_overlay import DrawingOverlay
from ui.chart_view import (
    ENGINE_ENV_VAR,
    SETTINGS_APPLICATION,
    SETTINGS_ENGINE_KEY,
    SETTINGS_ORGANIZATION,
    AlarmController,
    ChartView,
    DrawingController,
    LwcChartView,
    PyqtgraphChartView,
    create_chart_view,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def clean_env(monkeypatch):
    """Run with ``NDT_CHART_ENGINE`` unset."""
    monkeypatch.delenv(ENGINE_ENV_VAR, raising=False)
    return monkeypatch


@pytest.fixture
def clean_settings():
    """Run with the persisted engine key cleared; restore afterwards."""
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    previous = settings.value(SETTINGS_ENGINE_KEY)
    settings.remove(SETTINGS_ENGINE_KEY)
    settings.sync()
    yield settings
    if previous is None:
        settings.remove(SETTINGS_ENGINE_KEY)
    else:
        settings.setValue(SETTINGS_ENGINE_KEY, previous)
    settings.sync()


# ── T11: factory selection (AC1) ──────────────────────────────────────────

class TestFactorySelection:
    def test_unset_env_returns_pyqtgraph(self, qapp, clean_env, clean_settings):
        view = create_chart_view(0.0)
        assert view is not None
        assert isinstance(view, PyqtgraphChartView)
        assert isinstance(view, ChartPanel)
        assert isinstance(view, ChartView)

    def test_unknown_value_returns_pyqtgraph(self, qapp, clean_settings, monkeypatch):
        monkeypatch.setenv(ENGINE_ENV_VAR, "bogus-engine")
        view = create_chart_view(0.0)
        assert isinstance(view, PyqtgraphChartView)
        assert not isinstance(view, LwcChartView)

    def test_pyqtgraph_value_returns_pyqtgraph(
        self, qapp, clean_settings, monkeypatch
    ):
        monkeypatch.setenv(ENGINE_ENV_VAR, "pyqtgraph")
        view = create_chart_view(0.0)
        assert isinstance(view, PyqtgraphChartView)

    def test_lwc_value_returns_lwc_view(self, qapp, clean_settings, monkeypatch):
        monkeypatch.setenv(ENGINE_ENV_VAR, "lwc")
        view = create_chart_view(0.0)
        assert view is not None
        assert isinstance(view, LwcChartView)
        assert isinstance(view, QWidget)
        assert not isinstance(view, ChartPanel)
        assert isinstance(view, ChartView)

    def test_qsettings_override_mirrors_env(self, qapp, clean_env, clean_settings):
        clean_settings.setValue(SETTINGS_ENGINE_KEY, "lwc")
        clean_settings.sync()
        assert isinstance(create_chart_view(0.0), LwcChartView)

        clean_settings.setValue(SETTINGS_ENGINE_KEY, "pyqtgraph")
        clean_settings.sync()
        assert isinstance(create_chart_view(0.0), PyqtgraphChartView)

        clean_settings.setValue(SETTINGS_ENGINE_KEY, "bogus-engine")
        clean_settings.sync()
        assert isinstance(create_chart_view(0.0), PyqtgraphChartView)

        clean_settings.remove(SETTINGS_ENGINE_KEY)
        clean_settings.sync()
        assert isinstance(create_chart_view(0.0), PyqtgraphChartView)

    @pytest.mark.parametrize("engine", ["pyqtgraph", "lwc"])
    def test_tz_offset_and_editable_propagate(
        self, qapp, clean_settings, monkeypatch, engine
    ):
        monkeypatch.setenv(ENGINE_ENV_VAR, engine)
        view = create_chart_view(18000, editable=False)
        assert view.tz_offset == 18000
        assert view.editable is False

        default_view = create_chart_view()
        assert default_view.tz_offset == 0.0
        assert default_view.editable is True


# ── T12: signal signatures (AC2) ──────────────────────────────────────────

def _text(value) -> str:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode()
    data = getattr(value, "data", None)
    if callable(data):
        try:
            return data().decode()
        except Exception:
            pass
    return str(value)


def _own_signals(obj_or_meta) -> dict:
    """Map signal name -> normalized signature, excluding QObject's own."""
    meta = (
        obj_or_meta
        if hasattr(obj_or_meta, "methodCount")
        else obj_or_meta.metaObject()
    )
    signals = {}
    for index in range(meta.methodCount()):
        method = meta.method(index)
        if method.methodType() != QMetaMethod.MethodType.Signal:
            continue
        signals[_text(method.name())] = _text(method.methodSignature())
    base = QObject().metaObject()
    base_names = set()
    for index in range(base.methodCount()):
        method = base.method(index)
        if method.methodType() == QMetaMethod.MethodType.Signal:
            base_names.add(_text(method.name()))
    return {
        name: sig for name, sig in signals.items() if name not in base_names
    }


FROZEN_DRAWING_SIGNALS = {
    "created",
    "updated",
    "deleted",
    "selection_changed",
    "mode_changed",
    "settings_requested",
}

FROZEN_ALARM_SIGNALS = {
    "create_requested",
    "moved",
    "mute_toggled",
    "rearm_requested",
    "delete_requested",
}


class TestSignalSignatures:
    def test_drawing_controller_matches_pyqtgraph_surface(self, qapp):
        controller = DrawingController()
        frozen = _own_signals(DrawingOverlay.staticMetaObject)
        assert set(frozen) == FROZEN_DRAWING_SIGNALS
        assert _own_signals(controller) == frozen

    def test_alarm_controller_matches_pyqtgraph_surface(self, qapp):
        controller = AlarmController()
        frozen = _own_signals(AlarmOverlay.staticMetaObject)
        assert set(frozen) == FROZEN_ALARM_SIGNALS
        assert _own_signals(controller) == frozen

    @pytest.mark.parametrize("engine", ["pyqtgraph", "lwc"])
    def test_both_engines_expose_same_surface(
        self, qapp, clean_settings, monkeypatch, engine
    ):
        monkeypatch.setenv(ENGINE_ENV_VAR, engine)
        view = create_chart_view(0.0)
        assert _own_signals(view.drawing_controller) == _own_signals(
            DrawingOverlay.staticMetaObject
        )
        assert _own_signals(view.alarm_controller) == _own_signals(
            AlarmOverlay.staticMetaObject
        )

    def test_controller_forwards_overlay_signals(self, qapp, chart_panel):
        drawing = DrawingController(chart_panel.drawing_overlay)
        received = []
        drawing.mode_changed.connect(received.append)
        chart_panel.drawing_overlay.mode_changed.emit("trendline")
        qapp.processEvents()
        assert received == ["trendline"]

        alarm = AlarmController(chart_panel.alarm_overlay)
        prices = []
        alarm.create_requested.connect(prices.append)
        chart_panel.alarm_overlay.create_requested.emit(123.45)
        qapp.processEvents()
        assert prices == [123.45]


# ── T13: renderer-only boundary (AC3) ─────────────────────────────────────

class TestRendererOnlyBoundary:
    def test_seam_module_imports_stay_renderer_only(self):
        path = os.path.join("ui", "chart_view.py")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        forbidden = [
            "from ibkr",
            "import ibkr",
            "from data",
            "import data",
            "from services",
            "import services",
            "placeOrder",
            "openOrder",
            "Orders(",
            "watchlist",
            "dock",
            "sqlite",
            "stop_loss",
            "take_profit",
            "QWebEngine",
        ]
        hits = [token for token in forbidden if token in source]
        assert hits == [], f"renderer-only breach in ui/chart_view.py: {hits}"

    def test_no_order_surface_reintroduced(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("ibkr.orders")

    def test_pyqtgraph_present_and_default(
        self, qapp, clean_env, clean_settings
    ):
        assert ChartPanel(tz_offset=0) is not None
        view = create_chart_view(0.0)
        assert isinstance(view, ChartPanel)

    @pytest.mark.parametrize("engine", ["pyqtgraph", "lwc"])
    def test_both_views_accept_bars_and_live_ticks(
        self, qapp, clean_settings, monkeypatch, engine, sample_bars
    ):
        from data.models import Bar

        monkeypatch.setenv(ENGINE_ENV_VAR, engine)
        view = create_chart_view(0.0)
        view.set_symbol("SPY")
        view.set_timeframe("5 mins")
        view.update_bars(sample_bars)
        last = sample_bars[-1]
        tick = Bar(
            symbol=last.symbol,
            timeframe=last.timeframe,
            ts=last.ts,
            open=last.open,
            high=last.high + 1.0,
            low=last.low,
            close=last.close + 0.5,
            volume=last.volume + 10.0,
        )
        view.update_last_bar(tick, False)
        assert view is not None


# ── T14: parity-matrix seam record (AC4) ──────────────────────────────────

class TestParityMatrixSeamRecord:
    def test_seam_rows_reflect_this_wave_without_regression(self):
        path = os.path.join("docs", "lwc_parity_matrix.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        assert "P6-02" in text
        assert text.count("| Open / pending |") == 19
