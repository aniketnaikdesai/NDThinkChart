"""Tests for P9-T5 — recolor semantics (3.3): stored colors, member repaint,
leave-group rule, D50 drag-path composition.

Red pre-fix (members unchanged on recolor), green post-fix.
"""

import pytest

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QColorDialog

from data.db import db
from data.drawing_store import DrawingStore
from data.models import Drawing
from ui import drawing_groups_dialog as dlg_module
from ui.drawing_groups_dialog import DrawingGroupsDialog
from ui.lwc_view import drag_drawing_item, drawing_item

SYMBOL = "TESTP9RECOLOR"
OLD_COLOR = "#38bdf8"
NEW_COLOR = "#f472b6"


@pytest.fixture(autouse=True)
def clean():
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM drawings WHERE symbol=?", (SYMBOL,))
    cursor.execute("DELETE FROM drawing_groups WHERE symbol=?", (SYMBOL,))
    db.conn.commit()
    yield
    cursor.execute("DELETE FROM drawings WHERE symbol=?", (SYMBOL,))
    cursor.execute("DELETE FROM drawing_groups WHERE symbol=?", (SYMBOL,))
    db.conn.commit()


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_group_with_members(n=2, color=OLD_COLOR):
    gid = DrawingStore.create_group(SYMBOL, "DrawingSet_1", 1, color)
    ids = [
        DrawingStore.create_drawing(Drawing(
            symbol=SYMBOL, kind="horizontal",
            payload={"y": float(i + 1)},
            color=color, group_id=gid,
        ))
        for i in range(n)
    ]
    return gid, ids


def _recolor_via_dialog(qapp, monkeypatch, gid, new_color):
    dlg = DrawingGroupsDialog(SYMBOL)
    dlg.groups_table.selectRow(0)
    monkeypatch.setattr(
        QColorDialog, "getColor",
        staticmethod(lambda *a, **k: QColor(new_color)),
    )
    dlg._recolor_group()
    dlg.close()
    return dlg


class TestRecolorRepaintsMembers:
    def test_recolor_repaints_all_current_members(self, qapp, monkeypatch):
        """P9-T5-T51: recolor repaints every current member's stored color."""
        gid, ids = _make_group_with_members()
        _recolor_via_dialog(qapp, monkeypatch, gid, NEW_COLOR)
        groups = DrawingStore.groups_for_symbol(SYMBOL)
        assert len(groups) == 1
        assert groups[0].color == NEW_COLOR
        stored = {d.id: d.color for d in DrawingStore.drawings_for_symbol(SYMBOL)}
        assert len(stored) == 2
        for did in ids:
            assert stored[did] == NEW_COLOR


class TestLeaveGroupRule:
    def test_ungroup_and_reassign_preserve_color(self, qapp, monkeypatch):
        """P9-T5-T52: stored colors survive ungroup, reassign, later recolors."""
        gid, ids = _make_group_with_members()
        # One drawing leaves the group before the recolor.
        DrawingStore.assign_groups([ids[0]], None)
        _recolor_via_dialog(qapp, monkeypatch, gid, NEW_COLOR)
        stored = {d.id: d for d in DrawingStore.drawings_for_symbol(SYMBOL)}
        # The leaver keeps the color it had; the stayer is repainted.
        assert stored[ids[0]].color == OLD_COLOR
        assert stored[ids[0]].group_id is None
        assert stored[ids[1]].color == NEW_COLOR
        # Reassign the leaver to a second group: color still preserved.
        gid2 = DrawingStore.create_group(SYMBOL, "DrawingSet_2", 2, "#a78bfa")
        DrawingStore.assign_groups([ids[0]], gid2)
        stored = {d.id: d for d in DrawingStore.drawings_for_symbol(SYMBOL)}
        assert stored[ids[0]].color == OLD_COLOR
        assert stored[ids[0]].group_id == gid2
        # Ungroup the repainted member: keeps its repainted color, never default.
        DrawingStore.assign_groups([ids[1]], None)
        stored = {d.id: d for d in DrawingStore.drawings_for_symbol(SYMBOL)}
        assert stored[ids[1]].color == NEW_COLOR
        assert stored[ids[1]].group_id is None

    def test_delete_group_preserves_member_colors(self):
        """P9-T5-T52 (delete path): delete_group NULLs membership, keeps color."""
        gid, ids = _make_group_with_members(color=NEW_COLOR)
        DrawingStore.delete_group(gid)
        drawings = DrawingStore.drawings_for_symbol(SYMBOL)
        assert len(drawings) == 2
        for drawing in drawings:
            assert drawing.group_id is None
            assert drawing.color == NEW_COLOR


class TestDragPreservesColor:
    def test_drag_item_preserves_color(self):
        """P9-T5-T53: geometry drags never touch the stored color."""
        gid = DrawingStore.create_group(SYMBOL, "DrawingSet_1", 1, OLD_COLOR)
        did = DrawingStore.create_drawing(Drawing(
            symbol=SYMBOL, kind="trendline",
            payload={"p1": {"x": 1, "y": 2.0}, "p2": {"x": 3, "y": 4.0}},
            color=OLD_COLOR, group_id=gid,
        ))
        drawing = next(
            d for d in DrawingStore.drawings_for_symbol(SYMBOL) if d.id == did
        )
        item = drawing_item(drawing, xs=[1.0, 3.0], indices=[0, 1])
        assert item["color"] == OLD_COLOR
        moved = drag_drawing_item("trendline", item, 1, 0.5, 1.0)
        assert moved["color"] == OLD_COLOR
        assert moved["points"] != item["points"]
        # The D50 persist path: a payload-only update keeps the stored color.
        DrawingStore.update_drawing(did, {"p1": {"x": 1, "y": 2.5},
                                          "p2": {"x": 3, "y": 5.0}})
        assert DrawingStore.drawings_for_symbol(SYMBOL)[0].color == OLD_COLOR
