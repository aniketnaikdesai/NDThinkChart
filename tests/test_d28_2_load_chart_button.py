"""D28.2 / ESC-033 — the toolbar 'Load Chart' button wiring.

AC-D14.1 (Journey 21 toolbar path) / AC-D28.2: the toolbar button's
``clicked(bool checked=False)`` signal must drive ``load_chart``'s widget path
(symbol read from ``symbol_input``, upper-cased) — never bind the emitted bool
to ``load_chart``'s ``symbol`` parameter (which produced
``AttributeError: 'bool' object has no attribute 'strip'``).

``load_chart``'s D28.2 signature stays frozen for the explicit-value callers
(pop-outs, the alarm monitor, tests); only the toolbar wiring is decoupled.

Note (memory): pyqtgraph installs a non-abort ``sys.excepthook``, so a slot
exception is printed and SWALLOWED. These tests install a temporary recording
excepthook and assert observable state instead of relying on propagation.
"""

from __future__ import annotations

import inspect
import itertools
import sys

BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300  # 5-min period boundary -> priming is a no-op


class _RecordingHook:
    """Temporary ``sys.excepthook`` that records unhandled exceptions."""

    def __init__(self) -> None:
        self.errors: list[tuple] = []

    def __call__(self, etype, value, tb) -> None:
        self.errors.append((etype, value))


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    # Deterministic RT reqIds; never hit the network for historical requests.
    # The D42 depth floor issues many chunks from one load, so hand out ids
    # unbounded rather than exhausting a fixed list.
    rt_ids = itertools.count(7001)
    win.rt_manager.subscribe = lambda *a, **k: next(rt_ids)
    hids = itertools.count(8001)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win._now_ts = lambda: NOW_TS
    win.show()
    qapp.processEvents()
    return win


def test_toolbar_click_loads_widget_symbol(monkeypatch, qapp):
    """AC1: the real ``clicked(bool)`` fires the widget path and loads."""
    win = _make_window(monkeypatch, qapp)
    hook = _RecordingHook()
    old_hook = sys.excepthook
    sys.excepthook = hook
    try:
        win._on_connected()
        win.symbol_input.setText("AAPL")
        win.tf_combo.setCurrentText("5 mins")
        win.load_btn.click()
        qapp.processEvents()

        assert hook.errors == [], f"unhandled exception in slot: {hook.errors}"
        assert win._current_symbol == "AAPL"
        assert "AAPL" in win._sessions
    finally:
        sys.excepthook = old_hook
        win.close()


def test_toolbar_click_empty_symbol_shows_message(monkeypatch, qapp):
    """AC2: empty field -> widget path shows 'Enter a symbol first.'"""
    win = _make_window(monkeypatch, qapp)
    hook = _RecordingHook()
    old_hook = sys.excepthook
    sys.excepthook = hook
    try:
        win._on_connected()
        win.symbol_input.clear()
        win.load_btn.click()
        qapp.processEvents()

        assert hook.errors == [], f"unhandled exception in slot: {hook.errors}"
        assert "Enter a symbol first." in win.status_bar.currentMessage()
    finally:
        sys.excepthook = old_hook
        win.close()


def test_load_chart_signature_and_explicit_params(monkeypatch, qapp):
    """AC3: the D28.2 signature is unchanged and explicit callers win."""
    from ui.main_window import MainWindow

    sig = inspect.signature(MainWindow.load_chart)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == [
        "self", "symbol", "timeframe", "extended_hours",
    ]
    assert all(
        p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD for p in params
    )
    assert all(p.default is None for p in params[1:])

    win = _make_window(monkeypatch, qapp)
    try:
        # Toolbar widgets deliberately hold different values.
        win.symbol_input.setText("WRONG")
        win.tf_combo.setCurrentText("1 min")
        win.ext_hours_btn.setChecked(False)

        win.load_chart("EXPL", "15 mins")

        assert win._current_symbol == "EXPL"
        assert win._current_tf == "15 mins"
        # Explicit values win and the widgets are untouched.
        assert win.symbol_input.text() == "WRONG"
        assert win.tf_combo.currentText() == "1 min"
        assert win.ext_hours_btn.isChecked() is False
    finally:
        win.close()
