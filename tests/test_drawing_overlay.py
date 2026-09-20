"""Tests for ui/drawing_overlay.py — mapping, rendering, creation, editing."""

import pytest
from PyQt6.QtCore import QPointF, Qt

from data.models import Drawing, DrawingGroup
from ui.drawing_overlay import TOOL_CURSOR


class FakeEvent:
    def __init__(self, scene_pos, button=Qt.MouseButton.LeftButton, finish=False):
        self._scene = scene_pos
        self._button = button
        self._finish = finish
        self.accepted = False

    def button(self):
        return self._button

    def scenePos(self):
        return self._scene

    def isFinish(self):
        return self._finish

    def accept(self):
        self.accepted = True


def event_at(overlay, x, y, finish=False):
    return FakeEvent(overlay._view.mapViewToScene(QPointF(x, y)), finish=finish)


def scene_at(overlay, x, y):
    return overlay._view.mapViewToScene(QPointF(x, y))


@pytest.fixture
def overlay(chart_panel, sample_bars):
    chart_panel.update_chart(sample_bars)
    ov = chart_panel.drawing_overlay
    ov.set_symbol("TEST")
    return ov


class TestCoordinateMapping:
    def test_ts_to_x(self, overlay, sample_bars):
        # x-space is timestamps since the DateAxisItem migration
        assert overlay._ts_to_x(sample_bars[0].ts) == float(sample_bars[0].ts)
        assert overlay._ts_to_x(sample_bars[7].ts) == float(sample_bars[7].ts)

    def test_x_to_ts(self, overlay, sample_bars):
        assert overlay._x_to_ts(float(sample_bars[3].ts) + 0.4) == sample_bars[3].ts

    def test_round_trip(self, overlay, sample_bars):
        for bar in sample_bars[:10]:
            assert overlay._x_to_ts(overlay._ts_to_x(bar.ts)) == bar.ts


class TestCreation:
    def test_click_click_trendline(self, overlay):
        created = []
        overlay.created.connect(created.append)
        overlay.set_tool("trendline")

        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[2], 100.0))
        assert overlay._draft is not None
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[10], 110.0))

        assert len(created) == 1
        drawing = created[0]
        assert drawing.kind == "trendline"
        assert drawing.payload["p1"] == {"x": overlay._bar_ts[2], "y": pytest.approx(100.0)}
        assert drawing.payload["p2"] == {"x": overlay._bar_ts[10], "y": pytest.approx(110.0)}
        assert overlay._draft is None

    def test_drag_release_commits(self, overlay):
        created = []
        overlay.created.connect(created.append)
        overlay.set_tool("horizontal")

        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[5], 120.0))
        overlay.view_mouse_drag(event_at(overlay, overlay._bar_ts[5], 130.0))
        overlay.view_mouse_drag(event_at(overlay, overlay._bar_ts[5], 125.0, finish=True))
        assert len(created) == 1
        assert created[0].payload["y"] == pytest.approx(125.0)

    def test_zone_commit_normalizes(self, overlay):
        created = []
        overlay.created.connect(created.append)
        overlay.set_tool("zone")
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[1], 130.0))
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[9], 110.0))
        payload = created[0].payload
        assert payload["y1"] < payload["y2"]
        assert payload["x1"] < payload["x2"]

    def test_tool_resets_to_cursor_on_bad_name(self, overlay):
        overlay.set_tool("trendline")
        overlay.set_tool("no-such-tool")
        assert overlay._tool == TOOL_CURSOR

    def test_assigns_active_group_and_color(self, overlay):
        group = DrawingGroup(id=42, symbol="TEST", name="DrawingSet_1",
                             seq_number=1, color="#f472b6")
        overlay.set_groups([group])
        overlay.set_active_group(42, "#f472b6")
        created = []
        overlay.created.connect(created.append)
        overlay.set_tool("horizontal")
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[1], 100.0))
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[1], 101.0))
        assert created[0].group_id == 42
        assert created[0].color == "#f472b6"


class TestRendering:
    def test_set_data_renders(self, overlay):
        drawings = [Drawing(id=1, symbol="TEST", kind="horizontal", payload={"y": 105.0})]
        overlay.set_data("TEST", drawings, [])
        assert 1 in overlay._items
        # D11: horizontal now renders the line plus an inner-right price label
        assert len(overlay._items[1]) == 2

    def test_hidden_group_not_rendered(self, overlay):
        group = DrawingGroup(id=7, symbol="TEST", name="G", seq_number=1, visible=False)
        drawings = [Drawing(id=1, symbol="TEST", kind="horizontal",
                            payload={"y": 105.0}, group_id=7)]
        overlay.set_data("TEST", drawings, [group])
        assert overlay._items.get(1) is None

    def test_toggle_visibility_rerenders(self, overlay):
        group = DrawingGroup(id=7, symbol="TEST", name="G", seq_number=1, visible=False)
        drawings = [Drawing(id=1, symbol="TEST", kind="horizontal",
                            payload={"y": 105.0}, group_id=7)]
        overlay.set_data("TEST", drawings, [group])
        group.visible = True
        overlay.set_groups([group])
        assert 1 in overlay._items


class TestHitTesting:
    def test_hit_trendline_midpoint(self, overlay):
        drawing = Drawing(
            id=1, symbol="TEST", kind="trendline",
            payload={"p1": {"x": overlay._bar_ts[0], "y": 100.0},
                     "p2": {"x": overlay._bar_ts[20], "y": 120.0}},
        )
        overlay.set_data("TEST", [drawing], [])
        mid = scene_at(overlay, overlay._bar_ts[10], 110.0)
        assert overlay._hit_drawing(mid).id == 1

    def test_miss_returns_none(self, overlay):
        drawing = Drawing(
            id=1, symbol="TEST", kind="trendline",
            payload={"p1": {"x": overlay._bar_ts[0], "y": 100.0},
                     "p2": {"x": overlay._bar_ts[20], "y": 120.0}},
        )
        overlay.set_data("TEST", [drawing], [])
        far = scene_at(overlay, overlay._bar_ts[10], 105.0)
        assert overlay._hit_drawing(far) is None

    def test_hit_horizontal(self, overlay):
        drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                          payload={"y": 108.0})
        overlay.set_data("TEST", [drawing], [])
        pos = scene_at(overlay, overlay._bar_ts[5], 108.0)
        assert overlay._hit_drawing(pos).id == 1

    def test_hidden_group_not_hittable(self, overlay):
        group = DrawingGroup(id=7, symbol="TEST", name="G", seq_number=1, visible=False)
        drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                          payload={"y": 108.0}, group_id=7)
        overlay.set_data("TEST", [drawing], [group])
        pos = scene_at(overlay, overlay._bar_ts[5], 108.0)
        assert overlay._hit_drawing(pos) is None


class TestSelectionAndEdit:
    def _trendline(self, overlay):
        return Drawing(
            id=1, symbol="TEST", kind="trendline",
            payload={"p1": {"x": overlay._bar_ts[2], "y": 100.0},
                     "p2": {"x": overlay._bar_ts[12], "y": 120.0}},
        )

    def test_select_by_click(self, overlay):
        overlay.set_data("TEST", [self._trendline(overlay)], [])
        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[7], 110.0))
        assert overlay._selected_id == 1

    def test_drag_handle_updates_payload(self, overlay):
        drawing = self._trendline(overlay)
        overlay.set_data("TEST", [drawing], [])
        updated = []
        overlay.updated.connect(lambda did, payload: updated.append((did, payload)))
        overlay._select(1)

        p1_scene = scene_at(overlay, overlay._bar_ts[2], 100.0)
        overlay.view_mouse_press(FakeEvent(p1_scene))
        assert overlay._drag is not None
        assert overlay._drag["point_index"] == 0

        overlay.view_mouse_drag(event_at(overlay, overlay._bar_ts[2], 90.0, finish=True))
        assert updated
        assert updated[-1][1]["p1"]["y"] == pytest.approx(90.0)
        assert overlay._drag is None

    def test_locked_group_blocks_drag(self, overlay):
        group = DrawingGroup(id=7, symbol="TEST", name="G", seq_number=1, locked=True)
        drawing = self._trendline(overlay)
        drawing.group_id = 7
        overlay.set_data("TEST", [drawing], [group])
        updated = []
        overlay.updated.connect(lambda did, payload: updated.append((did, payload)))

        overlay.view_mouse_press(event_at(overlay, overlay._bar_ts[7], 110.0))
        assert overlay._selected_id == 1
        overlay.view_mouse_drag(event_at(overlay, overlay._bar_ts[7], 100.0, finish=True))
        assert updated == []

    def test_delete_selected(self, overlay):
        overlay.set_data("TEST", [self._trendline(overlay)], [])
        deleted = []
        overlay.deleted.connect(deleted.append)
        overlay._select(1)
        overlay.delete_selected()
        assert deleted == [1]
        assert overlay._find_drawing(1) is None

    def test_locked_group_blocks_delete(self, overlay):
        group = DrawingGroup(id=7, symbol="TEST", name="G", seq_number=1, locked=True)
        drawing = self._trendline(overlay)
        drawing.group_id = 7
        overlay.set_data("TEST", [drawing], [group])
        deleted = []
        overlay.deleted.connect(deleted.append)
        overlay._select(1)
        overlay.delete_selected()
        assert deleted == []
        assert overlay._find_drawing(1) is not None

    def test_clear_selection(self, overlay):
        overlay.set_data("TEST", [self._trendline(overlay)], [])
        overlay._select(1)
        overlay.clear_selection()
        assert overlay.has_selection() is False