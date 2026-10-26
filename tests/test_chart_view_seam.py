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
import re

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

# Rows this project has completed so far. Later waves add to this set; a row
# regressing to Open/pending still fails because every other row must be Open.
DONE_PARITY_ROWS = {7, 8, 13, 14}

DONE_DISPOSITION = "Done / accepted"
OPEN_DISPOSITION = "Open / pending"


def _parity_rows(text: str) -> dict:
    """Map parity-row number -> disposition cell from the matrix table."""
    rows = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        rows[int(cells[0])] = cells[-1]
    return rows


class TestParityMatrixSeamRecord:
    def test_seam_rows_reflect_this_wave_without_regression(self):
        path = os.path.join("docs", "lwc_parity_matrix.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        assert "P6-02" in text

        rows = _parity_rows(text)
        # The matrix keeps the same 19 data rows no matter which waves landed.
        assert set(rows) == set(range(1, 20)), sorted(rows)

        done = {number for number, cell in rows.items() if cell == DONE_DISPOSITION}
        open_rows = {number for number, cell in rows.items() if cell == OPEN_DISPOSITION}
        # Every row carries one of the two dispositions, exactly.
        assert done | open_rows == set(rows)
        assert not done & open_rows
        # Completed rows stay Done (later waves may complete more) ...
        assert DONE_PARITY_ROWS <= done, sorted(DONE_PARITY_ROWS - done)
        # ... and every other row is still Open, so a regression fails.
        assert open_rows == set(rows) - done

        # The summary line is derived from the table, not pinned to a count.
        summary = re.search(
            r"Row count:\s*(\d+)\.\s*"
            r"Dispositioned Open/pending:\s*(\d+)\.\s*"
            r"Done/accepted:\s*(\d+)\.",
            text,
        )
        assert summary is not None, "parity matrix summary line missing"
        total, open_count, done_count = (int(group) for group in summary.groups())
        assert total == len(rows)
        assert open_count == len(open_rows)
        assert done_count == len(done)
        assert open_count + done_count == total


# ── Q-10: MainWindow goes through the factory (AC1) ───────────────────────

class TestMainWindowChartFactory:
    """The main chart is engine-selected through ``create_chart_view``.

    Before Q-10 ``MainWindow`` built ``ChartPanel`` directly, so the factory
    only ever reached pop-outs: ``NDT_CHART_ENGINE=lwc`` could not select the
    main chart and the live-session sign-off gate was unreachable. These
    cases pin the factory path, the pyqtgraph fallback for an unknown value,
    and the LWC driver re-host on the main-chart construction path.
    """

    @staticmethod
    def _make_window(monkeypatch):
        from ibkr.client import IBApiClient

        monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
        monkeypatch.setattr(IBApiClient, "run", lambda *a, **k: None)
        from ui.main_window import MainWindow

        win = MainWindow()
        win.show()
        return win

    def test_main_window_chart_comes_from_the_factory(
        self, qapp, clean_env, clean_settings, monkeypatch
    ):
        import ui.main_window as main_window

        calls = []
        real_create = main_window.create_chart_view

        def spy(*args, **kwargs):
            view = real_create(*args, **kwargs)
            calls.append((view, dict(kwargs)))
            return view

        monkeypatch.setattr(main_window, "create_chart_view", spy)
        win = self._make_window(monkeypatch)
        try:
            qapp.processEvents()
            assert calls, "MainWindow built its chart without the engine factory"
            view, kwargs = calls[0]
            assert kwargs.get("editable") is True
            assert kwargs.get("tz_offset") == win._tz_offset
            assert win.chart_panel is view
            assert isinstance(view, PyqtgraphChartView)
        finally:
            win.close()
            qapp.processEvents()

    def test_unknown_engine_value_falls_back_to_pyqtgraph(
        self, qapp, clean_settings, monkeypatch
    ):
        monkeypatch.setenv(ENGINE_ENV_VAR, "definitely-not-an-engine")
        win = self._make_window(monkeypatch)
        try:
            qapp.processEvents()
            assert isinstance(win.chart_panel, PyqtgraphChartView)
            assert win.chart_panel.ENGINE_NAME == "pyqtgraph"
        finally:
            win.close()
            qapp.processEvents()

    def test_lwc_engine_rehosts_the_real_driver(
        self, qapp, clean_settings, monkeypatch
    ):
        from ui.lwc_view import LwcChartView as LwcDriverView

        # DG88: no Chromium in offscreen CI. Record that MainWindow asks the
        # driver for its host (the pop-out path does the same in attach),
        # without depending on a WebEngine context existing here.
        host_calls = []
        monkeypatch.setattr(
            LwcDriverView,
            "ensure_host",
            lambda self: host_calls.append(self) or None,
        )
        monkeypatch.setenv(ENGINE_ENV_VAR, "lwc")
        win = self._make_window(monkeypatch)
        try:
            qapp.processEvents()
            assert isinstance(win.chart_panel, LwcDriverView)
            assert win.chart_panel.ENGINE_NAME == "lwc"
            assert win.chart_panel.editable is True
            # The session-facing surface the main-chart fan-out needs.
            assert hasattr(win.chart_panel, "drawing_overlay")
            assert host_calls == [win.chart_panel]
        finally:
            win.close()
            qapp.processEvents()
