"""tests/test_chart_view_seam.py — the ChartView seam after P6-13.

The pyqtgraph engine was removed under an **owner-waived** gate
(``docs/build/gate_P6_T13.md``: deletion approved 2026-10-27, live-session
sign-off WAIVED, NOT SATISFIED, oracle RETIRE). The seam is now LWC-only.

T11: ``create_chart_view`` always returns the LWC driver; the old engine
env/settings values no longer select a renderer; ``tz_offset``/``editable``
propagate.
T12: the controllers keep the frozen pre-D47 signal surface.
T13: renderer-only boundary.
T14: the parity-matrix seam record stays truthful.
"""

import importlib
import os
import re

import pytest
from PyQt6.QtCore import QObject, QMetaMethod
from PyQt6.QtWidgets import QWidget

from ui.chart_view import (
    ENGINE_ENV_VAR,
    AlarmController,
    ChartView,
    DrawingController,
    create_chart_view,
)


# ── T11: factory selection (LWC only) ─────────────────────────────────────

class TestFactorySelection:
    def test_factory_returns_the_lwc_view(self, qapp):
        from ui.lwc_view import LwcChartView

        view = create_chart_view(0.0)
        assert isinstance(view, LwcChartView)
        assert isinstance(view, QWidget)
        assert isinstance(view, ChartView)
        assert view.ENGINE_NAME == "lwc"

    def test_former_engine_values_no_longer_select_a_renderer(
        self, qapp, monkeypatch
    ):
        from ui.lwc_view import LwcChartView

        for value in ("pyqtgraph", "bogus-engine", ""):
            if value:
                monkeypatch.setenv(ENGINE_ENV_VAR, value)
            else:
                monkeypatch.delenv(ENGINE_ENV_VAR, raising=False)
            view = create_chart_view(0.0)
            assert isinstance(view, LwcChartView), value

    def test_tz_offset_and_editable_propagate(self, qapp):
        view = create_chart_view(18000, editable=False)
        assert view.tz_offset == 18000
        assert view.editable is False

        default_view = create_chart_view()
        assert default_view.tz_offset == 0.0
        assert default_view.editable is True


# ── T12: signal surface ──────────────────────────────────────────────────

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
    def test_drawing_controller_keeps_the_frozen_surface(self, qapp):
        assert set(_own_signals(DrawingController())) == FROZEN_DRAWING_SIGNALS

    def test_alarm_controller_keeps_the_frozen_surface(self, qapp):
        assert set(_own_signals(AlarmController())) == FROZEN_ALARM_SIGNALS

    def test_lwc_view_exposes_the_same_controller_surface(self, qapp):
        view = create_chart_view(0.0)
        assert set(_own_signals(view.drawing_controller)) == \
            FROZEN_DRAWING_SIGNALS
        assert set(_own_signals(view.alarm_controller)) == FROZEN_ALARM_SIGNALS


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

    def test_pyqtgraph_engine_module_is_gone(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("ui.chart_panel")

    def test_view_accepts_bars_and_live_ticks(self, qapp, sample_bars):
        from data.models import Bar

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
    """The main chart is resolved through ``create_chart_view`` (LWC only)."""

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
        self, qapp, monkeypatch
    ):
        import ui.main_window as main_window
        from ui.lwc_view import LwcChartView as LwcDriverView

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
            assert isinstance(view, LwcDriverView)
        finally:
            win.close()
            qapp.processEvents()

    def test_main_window_rehosts_the_real_driver(self, qapp, monkeypatch):
        from ui.lwc_view import LwcChartView as LwcDriverView

        # DG88: no Chromium in offscreen CI. Record that MainWindow asks the
        # driver for its host, without depending on a WebEngine context.
        host_calls = []
        monkeypatch.setattr(
            LwcDriverView,
            "ensure_host",
            lambda self: host_calls.append(self) or None,
        )
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
