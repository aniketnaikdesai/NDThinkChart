"""D27.10 — drawing style edits (colour, label, group) persist via the store.

The settings path applied the new colour in-memory only: ``updated`` carried
just (drawing_id, payload), so ``DrawingStore.update_drawing`` never saw the
colour and a reload reverted it.

AC-D27.10: Given a drawing colour edit, Then reload shows the edited colour.
"""

from __future__ import annotations

from data.drawing_store import DrawingStore
from data.models import Drawing


def _drawing(symbol: str, color: str = "#38bdf8") -> Drawing:
    return Drawing(
        symbol=symbol,
        kind="horizontal",
        payload={"y": 100.0},
        color=color,
        label="",
        group_id=None,
    )


def test_d27_10_update_drawing_persists_colour_label_group():
    did = DrawingStore.create_drawing(_drawing("TEST_D2710_A"))
    DrawingStore.update_drawing(
        did,
        {"y": 101.5},
        color="#ff0000",
        label="resistance",
        group_id=7,
    )
    (reloaded,) = [
        d for d in DrawingStore.drawings_for_symbol("TEST_D2710_A")
        if d.id == did
    ]
    assert reloaded.payload == {"y": 101.5}
    assert reloaded.color == "#ff0000"
    assert reloaded.label == "resistance"
    assert reloaded.group_id == 7


def test_d27_10_update_drawing_omitted_fields_unchanged():
    """Omitted style fields must not be clobbered (None = unchanged)."""
    d = _drawing("TEST_D2710_B", color="#00ff00")
    d.label = "keep me"
    did = DrawingStore.create_drawing(d)
    DrawingStore.update_drawing(did, {"y": 102.0})
    (reloaded,) = [
        d for d in DrawingStore.drawings_for_symbol("TEST_D2710_B")
        if d.id == did
    ]
    assert reloaded.color == "#00ff00"
    assert reloaded.label == "keep me"


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)
    monkeypatch.setattr(
        pacing_mod.pacing_manager, "throttle_realtime", lambda: None
    )
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def test_d27_10_settings_path_persists_colour(monkeypatch, qapp):
    """Wiring: the settings path's update (id, payload, colour) reaches the
    store, so a reload shows the edited colour (AC-D27.10)."""
    win = _make_window(monkeypatch, qapp)
    did = DrawingStore.create_drawing(_drawing("TEST_D2710_C"))
    # What chart_panel._on_drawing_settings_requested emits after the dialog.
    win._on_drawing_updated(did, {"y": 103.0}, "#ff0000")
    (reloaded,) = [
        d for d in DrawingStore.drawings_for_symbol("TEST_D2710_C")
        if d.id == did
    ]
    assert reloaded.payload == {"y": 103.0}
    assert reloaded.color == "#ff0000"
    win.close()
