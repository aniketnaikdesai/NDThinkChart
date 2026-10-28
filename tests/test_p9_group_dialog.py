"""P9-T2: group-name cell read-only; Rename button stays the sole rename path.

Offscreen probes (run with QT_QPA_PLATFORM=offscreen):
- T21: the name cell carries no ItemIsEditable flag (inline editing impossible).
- T22: _rename_group still renames the row and persists via the store.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QInputDialog

from data.drawing_store import DrawingStore
from ui.drawing_groups_dialog import DrawingGroupsDialog

SYMBOL = "P9T2"


def _make_dialog():
    DrawingStore.create_group(SYMBOL, "Alpha", 1, "#38bdf8")
    return DrawingGroupsDialog(SYMBOL)


def test_name_cell_not_editable(qapp):
    dlg = _make_dialog()
    try:
        item = dlg.groups_table.item(0, 0)
        assert item is not None
        assert not (item.flags() & Qt.ItemFlag.ItemIsEditable)
    finally:
        dlg.close()


def test_rename_path_still_persists(qapp, monkeypatch):
    dlg = _make_dialog()
    try:
        dlg.groups_table.selectRow(0)
        monkeypatch.setattr(
            QInputDialog, "getText", lambda *args, **kwargs: ("Renamed", True)
        )
        dlg._rename_group()
        groups = DrawingStore.groups_for_symbol(SYMBOL)
        assert [g.name for g in groups] == ["Renamed"]
        assert dlg.groups_table.item(0, 0).text() == "Renamed"
    finally:
        dlg.close()
