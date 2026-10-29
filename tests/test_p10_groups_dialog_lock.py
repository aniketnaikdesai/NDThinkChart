"""P10-T6 (ESC-087): groups-dialog locked-delete refusal.

Repro-first: seed one drawing in a locked group and one in an unlocked
group, select both in an offscreen DrawingGroupsDialog and invoke
_delete_selected_drawings. Pre-fix the locked row is removed; post-fix the
locked row and geometry survive, the unlocked row is deleted, and an
all-locked selection is a no-op.
"""

import pytest
from PyQt6.QtCore import Qt

from data.drawing_store import DrawingStore
from data.models import Drawing
from ui.drawing_groups_dialog import DrawingGroupsDialog

SYMBOL = "P10T6-LOCK"

LOCKED_PAYLOAD = {"p1": {"x": 1_700_000_000, "y": 100.0},
                  "p2": {"x": 1_700_000_060, "y": 101.0}}
FREE_PAYLOAD = {"p1": {"x": 1_700_000_000, "y": 200.0},
                "p2": {"x": 1_700_000_060, "y": 202.5}}


@pytest.fixture
def seeded_ids():
    locked_gid = DrawingStore.create_group(SYMBOL, "Locked set", 1, "#38bdf8")
    DrawingStore.update_group(locked_gid, locked=True)
    free_gid = DrawingStore.create_group(SYMBOL, "Free set", 2, "#f472b6")
    locked_id = DrawingStore.create_drawing(Drawing(
        symbol=SYMBOL, kind="trendline", payload=dict(LOCKED_PAYLOAD),
        group_id=locked_gid))
    free_id = DrawingStore.create_drawing(Drawing(
        symbol=SYMBOL, kind="trendline", payload=dict(FREE_PAYLOAD),
        group_id=free_gid))
    return locked_id, free_id


def _select_dialog_drawings(dialog, wanted_ids):
    for row in range(dialog.drawings_list.count()):
        item = dialog.drawings_list.item(row)
        if item.data(Qt.ItemDataRole.UserRole) in wanted_ids:
            item.setSelected(True)


def test_P10_T6_T61_mixed_selection_keeps_locked(qapp, seeded_ids):
    locked_id, free_id = seeded_ids
    dialog = DrawingGroupsDialog(SYMBOL)
    _select_dialog_drawings(dialog, {locked_id, free_id})
    assert set(dialog._selected_drawing_ids()) == {locked_id, free_id}

    dialog._delete_selected_drawings()

    rows = {d.id: d for d in DrawingStore.drawings_for_symbol(SYMBOL)}
    assert locked_id in rows, "locked-group member must survive Delete Selected"
    assert rows[locked_id].payload == LOCKED_PAYLOAD, \
        "locked member geometry must be intact"
    assert free_id not in rows, "unlocked member must still be deleted"


def test_P10_T6_T61_all_locked_selection_is_noop(qapp, seeded_ids):
    locked_id, _free_id = seeded_ids
    dialog = DrawingGroupsDialog(SYMBOL)
    _select_dialog_drawings(dialog, {locked_id})

    dialog._delete_selected_drawings()

    rows = {d.id: d for d in DrawingStore.drawings_for_symbol(SYMBOL)}
    assert locked_id in rows, "all-locked selection must delete nothing"
    assert rows[locked_id].payload == LOCKED_PAYLOAD
