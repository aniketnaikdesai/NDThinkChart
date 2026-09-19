"""Tests for data/drawing_store.py — group + drawing CRUD."""

import pytest

from data.db import db
from data.drawing_store import DrawingStore
from data.models import Drawing

SYMBOL = "TESTDRAW"


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


class TestGroups:
    def test_create_and_list(self):
        gid = DrawingStore.create_group(SYMBOL, "DrawingSet_1", 1, "#38bdf8")
        groups = DrawingStore.groups_for_symbol(SYMBOL)
        assert len(groups) == 1
        g = groups[0]
        assert g.id == gid
        assert g.name == "DrawingSet_1"
        assert g.seq_number == 1
        assert g.color == "#38bdf8"
        assert g.visible is True
        assert g.locked is False

    def test_next_seq(self):
        assert DrawingStore.next_group_seq(SYMBOL) == 1
        DrawingStore.create_group(SYMBOL, "DrawingSet_1", 1)
        DrawingStore.create_group(SYMBOL, "DrawingSet_2", 2)
        assert DrawingStore.next_group_seq(SYMBOL) == 3

    def test_update_flags(self):
        gid = DrawingStore.create_group(SYMBOL, "G", 1)
        DrawingStore.update_group(gid, visible=False, locked=True, name="Renamed")
        g = DrawingStore.groups_for_symbol(SYMBOL)[0]
        assert g.visible is False
        assert g.locked is True
        assert g.name == "Renamed"

    def test_delete_group_unassigns_drawings(self):
        gid = DrawingStore.create_group(SYMBOL, "G", 1)
        did = DrawingStore.create_drawing(Drawing(
            symbol=SYMBOL, kind="horizontal", payload={"y": 5.0}, group_id=gid,
        ))
        DrawingStore.delete_group(gid)
        assert DrawingStore.groups_for_symbol(SYMBOL) == []
        remaining = DrawingStore.drawings_for_symbol(SYMBOL)
        assert len(remaining) == 1
        assert remaining[0].id == did
        assert remaining[0].group_id is None


class TestDrawings:
    def test_create_and_roundtrip(self):
        did = DrawingStore.create_drawing(Drawing(
            symbol=SYMBOL, kind="trendline",
            payload={"p1": {"x": 1, "y": 2.0}, "p2": {"x": 3, "y": 4.0}},
            color="#f472b6", label="note", group_id=None,
        ))
        drawings = DrawingStore.drawings_for_symbol(SYMBOL)
        assert len(drawings) == 1
        d = drawings[0]
        assert d.id == did
        assert d.kind == "trendline"
        assert d.payload["p1"] == {"x": 1, "y": 2.0}
        assert d.color == "#f472b6"
        assert d.label == "note"

    def test_update_payload(self):
        did = DrawingStore.create_drawing(Drawing(
            symbol=SYMBOL, kind="horizontal", payload={"y": 5.0},
        ))
        DrawingStore.update_drawing(did, {"y": 9.5})
        assert DrawingStore.drawings_for_symbol(SYMBOL)[0].payload == {"y": 9.5}

    def test_assign_and_ungroup(self):
        gid = DrawingStore.create_group(SYMBOL, "G", 1)
        ids = [
            DrawingStore.create_drawing(Drawing(symbol=SYMBOL, kind="horizontal", payload={"y": 1.0})),
            DrawingStore.create_drawing(Drawing(symbol=SYMBOL, kind="horizontal", payload={"y": 2.0})),
        ]
        DrawingStore.assign_groups(ids, gid)
        assert all(d.group_id == gid for d in DrawingStore.drawings_for_symbol(SYMBOL))
        DrawingStore.assign_groups(ids, None)
        assert all(d.group_id is None for d in DrawingStore.drawings_for_symbol(SYMBOL))

    def test_delete_one_and_many(self):
        ids = [
            DrawingStore.create_drawing(Drawing(symbol=SYMBOL, kind="horizontal", payload={"y": float(i)}))
            for i in range(3)
        ]
        DrawingStore.delete_drawing(ids[0])
        assert len(DrawingStore.drawings_for_symbol(SYMBOL)) == 2
        DrawingStore.delete_drawings(ids[1:])
        assert DrawingStore.drawings_for_symbol(SYMBOL) == []