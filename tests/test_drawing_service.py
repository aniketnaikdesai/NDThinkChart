"""Tests for services/drawing_service.py — pure payload/group logic."""

import pytest

from data.models import Drawing, DrawingGroup
from services.drawing_service import (
    auto_group_name,
    drawing_summary,
    fib_levels,
    next_group_seq,
    normalize_payload,
    points_in_ts,
)


def test_auto_group_name():
    assert auto_group_name(1) == "DrawingSet_1"
    assert auto_group_name(7) == "DrawingSet_7"


def test_next_group_seq_empty():
    assert next_group_seq([]) == 1


def test_next_group_seq_uses_max():
    groups = [
        DrawingGroup(symbol="X", name="A", seq_number=2),
        DrawingGroup(symbol="X", name="B", seq_number=5),
        DrawingGroup(symbol="X", name="C", seq_number=1),
    ]
    assert next_group_seq(groups) == 6


class TestNormalizePayload:
    def test_trendline(self):
        p = normalize_payload("trendline", {
            "p1": {"x": 100, "y": 1.5}, "p2": {"x": 200, "y": 2.5},
        })
        assert p == {"p1": {"x": 100, "y": 1.5}, "p2": {"x": 200, "y": 2.5}}

    def test_trendline_p2_takes_precedence_over_missing_keys(self):
        with pytest.raises(ValueError):
            normalize_payload("trendline", {"p1": {"x": 1, "y": 1}})

    def test_bad_point_value(self):
        with pytest.raises(ValueError):
            normalize_payload("trendline", {"p1": "nope", "p2": {"x": 1, "y": 1}})

    def test_horizontal(self):
        assert normalize_payload("horizontal", {"y": 42}) == {"y": 42.0}

    def test_horizontal_bad(self):
        with pytest.raises(ValueError):
            normalize_payload("horizontal", {"y": "abc"})

    def test_zone_sorts_low_to_high(self):
        p = normalize_payload("zone", {"x1": 300, "x2": 100, "y1": 20, "y2": 10})
        assert p == {"x1": 100, "x2": 300, "y1": 10.0, "y2": 20.0}

    def test_zone_missing_field(self):
        with pytest.raises(ValueError):
            normalize_payload("zone", {"x1": 1, "y1": 1, "y2": 2})

    def test_fibonacci_defaults_retr(self):
        p = normalize_payload("fibonacci", {"p1": {"x": 1, "y": 1}, "p2": {"x": 2, "y": 2}})
        assert p["type"] == "retr"

    def test_fibonacci_rejects_bad_type(self):
        with pytest.raises(ValueError):
            normalize_payload("fibonacci", {
                "p1": {"x": 1, "y": 1}, "p2": {"x": 2, "y": 2}, "type": "bogus",
            })

    def test_unknown_kind(self):
        with pytest.raises(ValueError):
            normalize_payload("circle", {})

    def test_non_dict_payload(self):
        with pytest.raises(ValueError):
            normalize_payload("horizontal", None)


class TestFibLevels:
    def test_endpoints(self):
        levels = fib_levels(100.0, 200.0)
        assert levels[0] == (0.0, 100.0)
        assert levels[-1] == (1.0, 200.0)

    def test_midpoint(self):
        levels = dict(fib_levels(100.0, 200.0))
        assert levels[0.5] == 150.0
        assert levels[0.236] == pytest.approx(123.6)

    def test_descending(self):
        levels = dict(fib_levels(200.0, 100.0))
        assert levels[0.5] == pytest.approx(150.0)

    def test_extension_levels_project_beyond(self):
        levels = dict(fib_levels(100.0, 200.0, "ext"))
        assert levels[1.618] == pytest.approx(261.8)
        assert levels[1.0] == 200.0


class TestPointsInTs:
    def test_trendline(self):
        pts = points_in_ts("trendline", {"p1": {"x": 5, "y": 1}, "p2": {"x": 9, "y": 2}})
        assert pts == [(5, 1.0), (9, 2.0)]

    def test_horizontal(self):
        assert points_in_ts("horizontal", {"y": 7}) == [(0, 7.0)]

    def test_zone(self):
        pts = points_in_ts("zone", {"x1": 3, "x2": 8, "y1": 1, "y2": 2})
        assert pts == [(3, 1.0), (3, 2.0)]


class TestDrawingSummary:
    def test_trendline(self):
        d = Drawing(symbol="X", kind="trendline", payload={"p1": {"x": 1, "y": 1}, "p2": {"x": 2, "y": 2}})
        assert drawing_summary(d) == "Trendline"

    def test_horizontal(self):
        d = Drawing(symbol="X", kind="horizontal", payload={"y": 103.456})
        assert drawing_summary(d) == "H @ 103.46"

    def test_zone(self):
        d = Drawing(symbol="X", kind="zone", payload={"x1": 1, "x2": 2, "y1": 100, "y2": 110})
        assert drawing_summary(d) == "Zone 100.00–110.00"

    def test_bad_payload_falls_back(self):
        d = Drawing(symbol="X", kind="horizontal", payload={})
        assert drawing_summary(d) == "Horizontal"