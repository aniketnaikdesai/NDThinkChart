"""P10-T1 (W1/D50.2): selection-gated handles, locked highlight-only.

Repro-first: T11/T12 fail on the pre-fix tree (handles always attached);
T13 pins the frozen visibility rule (green pre- and post-fix).
"""

from types import SimpleNamespace

import pytest

from ui.lwc_view import drawing_handle_points, drawing_item, drawing_op

XS = [1000, 2000, 3000, 4000, 5000]
INDICES = [0, 1, 2, 3, 4]

KINDS = ("trendline", "horizontal", "zone", "fibonacci", "measure")


def _payload(kind):
    if kind in ("trendline", "measure"):
        return {"p1": {"x": 1000, "y": 10.0}, "p2": {"x": 3000, "y": 12.0}}
    if kind == "fibonacci":
        return {"p1": {"x": 1000, "y": 10.0}, "p2": {"x": 3000, "y": 12.0},
                "type": "retr"}
    if kind == "horizontal":
        return {"y": 11.0}
    if kind == "zone":
        return {"x1": 1000, "x2": 3000, "y1": 10.0, "y2": 12.0}
    raise AssertionError(f"unknown kind {kind!r}")


def _drawing(kind, did, group_id=None):
    return SimpleNamespace(id=did, kind=kind, payload=_payload(kind),
                           color="#ff0000", group_id=group_id)


def _group(gid, locked=False, visible=True):
    return SimpleNamespace(id=gid, locked=locked, visible=visible)


def _by_id(op, did):
    return next(i for i in op["items"] if i["id"] == did)


@pytest.mark.parametrize("kind", KINDS)
def test_selected_attaches_handles_deselected_clears_item(kind):
    """P10-T1-T11 (drawing_item half)."""
    drawing = _drawing(kind, 7)
    selected = drawing_item(drawing, XS, INDICES, selected=True)
    assert selected["selected"] is True
    assert selected["handles"] == drawing_handle_points(kind, selected)
    assert len(selected["handles"]) > 0
    deselected = drawing_item(drawing, XS, INDICES, selected=False)
    assert deselected["selected"] is False
    assert deselected["handles"] == []


@pytest.mark.parametrize("kind", KINDS)
def test_selected_attaches_handles_deselected_clears_op(kind):
    """P10-T1-T11 (drawing_op half)."""
    drawing = _drawing(kind, 7)
    op = drawing_op([drawing], [], XS, INDICES, selected_id=7)
    assert _by_id(op, 7)["handles"] == drawing_handle_points(
        kind, _by_id(op, 7))
    assert len(_by_id(op, 7)["handles"]) > 0
    cleared = drawing_op([drawing], [], XS, INDICES, selected_id=None)
    assert _by_id(cleared, 7)["handles"] == []
    other = drawing_op([drawing], [], XS, INDICES, selected_id=999)
    assert _by_id(other, 7)["handles"] == []


def test_locked_selected_keeps_highlight_without_handles():
    """P10-T1-T12: locked drawing offers no draggable handle."""
    group = _group(3, locked=True)
    drawing = _drawing("trendline", 7, group_id=3)
    item = drawing_item(drawing, XS, INDICES, group=group, selected=True)
    assert item["selected"] is True
    assert item["locked"] is True
    assert item["handles"] == []
    op = drawing_op([drawing], [group], XS, INDICES, selected_id=7)
    wire = _by_id(op, 7)
    assert wire["selected"] is True
    assert wire["locked"] is True
    assert wire["handles"] == []


def test_visibility_rule_unchanged():
    """P10-T1-T13: groupless visible; hidden-group member omitted."""
    groupless = _drawing("trendline", 1)
    hidden_group = _group(9, visible=False)
    hidden = _drawing("horizontal", 2, group_id=9)
    op = drawing_op([groupless, hidden], [hidden_group], XS, INDICES)
    ids = [i["id"] for i in op["items"]]
    assert 1 in ids
    assert 2 not in ids
