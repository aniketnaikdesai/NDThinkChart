"""P22-T2 (D62 apply leg): set_timezone op, fan-out, persistence round-trip.

T2-AC1 (unit): ``set_timezone`` publishes one ``{"op": "set_timezone",
"mode"}`` op on the existing interaction channel for both modes; the op
survives a page-ready replay; no ``runJavaScript`` path is added; the bar
``send_ops`` log is untouched.
T2-AC2 (integration): flipping the toggle reaches the main view plus every
pop-out view (red pre-fix: the toggle was a silent no-op — no
``set_timezone`` existed anywhere in ``ui/``).
T2-AC3 (integration): the flipped choice persists; a restarted window
restores it for the main view and seeds new pop-out creation (D49.6
threading intact).

Label-shift correctness is P22-T3's tests, not these.
"""

from __future__ import annotations

import inspect
import json

import pytest


@pytest.fixture()
def memory_settings(monkeypatch):
    """Isolate QSettings: one in-memory store shared by every window here."""
    import ui.main_window as mw_mod

    class _MemorySettings:
        store: dict = {}

        def __init__(self, *args, **kwargs):
            pass

        def value(self, key, default=None, **kwargs):
            val = type(self).store.get(key, default)
            coerce = kwargs.get("type")
            if coerce is not None and val is not None:
                try:
                    return coerce(val)
                except (TypeError, ValueError):
                    return val
            return val

        def setValue(self, key, val):
            type(self).store[key] = val

    _MemorySettings.store.clear()
    monkeypatch.setattr(mw_mod, "QSettings", _MemorySettings)
    return _MemorySettings.store


@pytest.fixture()
def make_window(monkeypatch, tmp_path, qapp, memory_settings):
    """Factory for offscreen MainWindows with no live TWS connection."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p22_t2_tz.db"))
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    from ui.main_window import MainWindow

    created: list = []

    def _make():
        win = MainWindow()
        created.append(win)
        return win

    yield _make

    for win in created:
        for popout in list(getattr(win, "_popouts", [])):
            try:
                popout.close()
            except Exception:
                pass
        try:
            win.close()
        except Exception:
            pass


def test_p22_t2_ac1_set_timezone_op_and_replay(qapp):
    """set_timezone emits the tz op on the interaction channel; replay kept."""
    from ui.lwc_view import LwcChartView

    view = LwcChartView(tz_offset=0.0)
    assert view.interaction_ops == []

    view.set_timezone("UTC")
    assert view.tz_offset == 0
    assert view.interaction_ops[-1] == {"op": "set_timezone", "mode": "UTC"}

    view.set_timezone("Eastern Time")
    assert view.tz_offset != 0
    assert view.interaction_ops[-1] == {
        "op": "set_timezone", "mode": "Eastern Time",
    }

    with pytest.raises(ValueError):
        view.set_timezone("Mars Time")

    # No runJavaScript call added — the op rides the existing bridge.
    assert "runJavaScript(" not in inspect.getsource(LwcChartView.set_timezone)

    # Bar send_ops path untouched: the bar replay log carries no tz op.
    assert all(
        op.get("op") != "set_timezone" for op in view.bridge.replay_log()
    )

    # Replay preserves the op after page-ready (existing channel replay).
    carried: list = []
    view.bridge.channelOpsJson.connect(carried.append)
    try:
        view.bridge.handle_page_ready()
    finally:
        view.bridge.channelOpsJson.disconnect(carried.append)
    seen: list = []
    for payload in carried:
        env = json.loads(payload)
        if env.get("channel") == "interaction":
            seen.extend(env["ops"])
    assert {"op": "set_timezone", "mode": "UTC"} in seen
    assert {"op": "set_timezone", "mode": "Eastern Time"} in seen


def test_p22_t2_ac2_flip_fans_out_to_main_and_popouts(make_window, qapp):
    """The toggle flip reaches the main view plus every pop-out view."""
    win = make_window()
    win._current_symbol = "AAPL"
    win._current_tf = "5 mins"
    win._open_popout()
    win._open_popout()
    assert len(win._popouts) == 2
    qapp.processEvents()

    # Real toggle path: the combo signal drives _on_tz_changed.
    win.tz_combo.setCurrentText("UTC")
    qapp.processEvents()

    assert win._tz_offset == 0
    assert win.chart_panel.interaction_ops[-1] == {
        "op": "set_timezone", "mode": "UTC",
    }
    for popout in win._popouts:
        assert popout.chart.interaction_ops[-1] == {
            "op": "set_timezone", "mode": "UTC",
        }
        assert popout.chart.tz_offset == 0

    win.tz_combo.setCurrentText("Eastern Time")
    qapp.processEvents()

    from ui.main_window import _eastern_offset

    assert win._tz_offset == _eastern_offset()
    assert win.chart_panel.interaction_ops[-1] == {
        "op": "set_timezone", "mode": "Eastern Time",
    }
    for popout in win._popouts:
        assert popout.chart.interaction_ops[-1] == {
            "op": "set_timezone", "mode": "Eastern Time",
        }
        assert popout.chart.tz_offset == win._tz_offset


def test_p22_t2_ac3_persisted_choice_restores(
    make_window, qapp, memory_settings
):
    """Flip, restart: the persisted mode restores and seeds pop-outs."""
    from ui.main_window import TIMEZONE_SETTING_KEY

    win = make_window()
    win.tz_combo.setCurrentText("UTC")
    qapp.processEvents()
    assert memory_settings.get(TIMEZONE_SETTING_KEY) == "UTC"

    # "Restart": a fresh window over the same persisted settings.
    restarted = make_window()
    qapp.processEvents()
    assert restarted.tz_combo.currentText() == "UTC"
    assert restarted._tz_offset == 0
    assert restarted.chart_panel.tz_offset == 0

    # New pop-outs are created with the persisted choice (D49.6 intact).
    restarted._current_symbol = "AAPL"
    restarted._current_tf = "5 mins"
    restarted._open_popout()
    qapp.processEvents()
    assert restarted._popouts
    assert restarted._popouts[-1].chart.tz_offset == 0
