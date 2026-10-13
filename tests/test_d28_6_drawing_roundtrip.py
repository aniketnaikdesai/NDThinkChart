"""D28.6 T-4 — drawing store→overlay round-trip per kind.

One drawing of each kind (trendline, horizontal, zone, fibonacci,
measure) goes through DrawingStore.create_drawing → drawings_for_symbol
→ overlay.set_data; the payload must survive the store byte-for-byte
and the overlay must build items for every kind.
"""
import pytest

from data.drawing_store import DrawingStore
from data.models import Drawing

SYMBOL = "T4DRAW"
TS1, TS2 = 1_760_000_000, 1_760_000_300

PAYLOADS = {
    "trendline": {"p1": {"x": TS1, "y": 100.0}, "p2": {"x": TS2, "y": 101.0}},
    "horizontal": {"y": 100.5},
    "zone": {"x1": TS1, "x2": TS2, "y1": 99.0, "y2": 101.0},
    "fibonacci": {"p1": {"x": TS1, "y": 99.0}, "p2": {"x": TS2, "y": 102.0},
                  "type": "retr"},
    "measure": {"p1": {"x": TS1, "y": 100.0}, "p2": {"x": TS2, "y": 100.8}},
}


@pytest.fixture()
def overlay(chart_panel, sample_bars):
    chart_panel.update_chart(sample_bars)
    ov = chart_panel.drawing_overlay
    ov.set_symbol(SYMBOL)
    return ov


def test_store_overlay_round_trip_per_kind(overlay):
    ids = []
    try:
        for kind, payload in PAYLOADS.items():
            did = DrawingStore.create_drawing(
                Drawing(symbol=SYMBOL, kind=kind, payload=dict(payload),
                        color="#ff0000"))
            ids.append(did)

        stored = DrawingStore.drawings_for_symbol(SYMBOL)
        assert len(stored) == len(PAYLOADS)
        by_kind = {d.kind: d for d in stored}
        assert set(by_kind) == set(PAYLOADS)
        for kind, payload in PAYLOADS.items():
            assert by_kind[kind].payload == payload, (
                f"{kind}: payload did not survive the store round-trip")

        overlay.set_data(SYMBOL, stored, [])
        assert len(overlay._drawings) == len(PAYLOADS)
        for kind, drawing in by_kind.items():
            items = overlay._items.get(drawing.id)
            assert items, f"{kind}: overlay built no items"
    finally:
        if ids:
            DrawingStore.delete_drawings(ids)


def test_round_trip_update_and_delete(overlay):
    did = DrawingStore.create_drawing(
        Drawing(symbol=SYMBOL, kind="horizontal",
                payload={"y": 100.0}))
    try:
        DrawingStore.update_drawing(did, payload={"y": 101.5})
        stored = DrawingStore.drawings_for_symbol(SYMBOL)
        assert [d for d in stored if d.id == did][0].payload == {"y": 101.5}
    finally:
        DrawingStore.delete_drawing(did)
    assert did not in {d.id for d in DrawingStore.drawings_for_symbol(SYMBOL)}
