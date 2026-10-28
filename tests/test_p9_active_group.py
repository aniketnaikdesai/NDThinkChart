"""P9-T3 (S-P9-2 / finding 3.4): active draw-group re-validated on every reload.

_red pre-fix_: deleting the selected group (or seeding a foreign ID) leaves a
stale ``_active_draw_group_id`` behind after ``_refresh_drawing_groups``.
_green post-fix_: every reload coerces an unknown ID to ``None``, resets the
combo to Ungrouped, and re-pushes the tool state; the ticker-change clear in
``load_chart`` behaves exactly as today.
"""
import pytest

from data.drawing_store import DrawingStore
from ibkr.client import IBApiClient
from ui.main_window import MainWindow

SYMBOL = "P9T3"
OTHER = "P9T3B"
UNGROUPED_LABEL = "— Ungrouped —"


@pytest.fixture()
def window(qapp, tmp_path, monkeypatch):
    """Offscreen MainWindow: no live TWS, DB scoped to a temp file."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p9t3.db"))
    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    w = MainWindow()
    w._current_symbol = SYMBOL
    yield w
    w.close()


def _recorder(window, monkeypatch):
    """Stand in for the drawing tool surface; records set_active_group pushes."""

    class _Rec:
        def __init__(self):
            self.calls = []

        def set_active_group(self, group_id, color):
            self.calls.append((group_id, color))

    rec = _Rec()
    monkeypatch.setattr(window, "_drawing_actions", lambda: rec)
    return rec


def _combo_selection(window):
    return window.draw_set_combo.currentText(), window.draw_set_combo.currentData()


def test_t31_deleted_selected_group_clears(window, monkeypatch):
    """T31: select a group, delete it via the store, reload -> cleared."""
    gid = DrawingStore.create_group(SYMBOL, "sel", 1)
    try:
        window._active_draw_group_id = gid
        window._refresh_drawing_groups(SYMBOL)
        assert window._active_draw_group_id == gid
        assert _combo_selection(window) != (UNGROUPED_LABEL, None)

        rec = _recorder(window, monkeypatch)
        DrawingStore.delete_group(gid)
        gid = None
        window._refresh_drawing_groups(SYMBOL)

        assert window._active_draw_group_id is None
        assert _combo_selection(window) == (UNGROUPED_LABEL, None)
        assert rec.calls, "tool state must be re-pushed on reload"
        assert rec.calls[-1][0] is None
    finally:
        if gid is not None:
            DrawingStore.delete_group(gid)


def test_t32_stale_foreign_id_coerces_to_none(window, monkeypatch):
    """T32: a stale foreign active ID coerces to None on reload."""
    rec = _recorder(window, monkeypatch)
    window._active_draw_group_id = 2**31 - 1  # never a real group id
    window._refresh_drawing_groups(SYMBOL)
    assert window._active_draw_group_id is None
    assert _combo_selection(window) == (UNGROUPED_LABEL, None)
    assert rec.calls, "tool state must be re-pushed on reload"
    assert rec.calls[-1][0] is None


def test_t33_ticker_change_clear_preserved(window):
    """T33: load_chart with a symbol change clears the active group as today."""
    window._active_draw_group_id = 2**31 - 1  # stale before the switch
    window.load_chart(OTHER)
    assert window._active_draw_group_id is None
    assert window.draw_set_combo.currentData() is None
