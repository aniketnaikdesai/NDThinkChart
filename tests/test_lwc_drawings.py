"""tests/test_lwc_drawings.py — P6-T09 Phase 7 drawing primitives (L).

The drawing-parity cases: identical drawings must render identically on both
engines. The reference is the shipped ``ui/drawing_overlay.py`` driven with a
fake plot, and ``chart_assets/lwc/primitives.js`` driven from the same wire
envelope. Every case is parametrized over the five drawing kinds × the four
DG93 timestamp edge fixtures:

* ``dst_fold`` — the 2024-11-03 EDT→EST fold (repeated wall-clock hour);
* ``dst_spring`` — the 2025-03-09 EST→EDT gap;
* ``session_boundary`` — RTH edges plus the overnight non-trading collapse
  and a within-session continuation;
* ``index_collision`` — two pairs of bars sharing one display-x.

The asserted identity is the mapping pair, not an eyeball: a drawing anchor's
timestamp maps to one fractional logical index, and the inverse of that index
is the reference overlay's own ``_ts_to_x(ts)`` — value-for-value, on every
fixture. Labels are composed on the JS side from the numbers that cross; the
suite compares those strings to the reference ``TextItem`` text.

QApplication usage: the view is a ``QWidget`` and the reference overlay builds
graphics items, so the render cases take the repo's session-scoped ``qapp``
fixture.
"""

from __future__ import annotations

import ast
import copy
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from data.models import Bar, Drawing, DrawingGroup
from services import chart_model
from services.drawing_service import (
    FIB_EXTENSION_LEVELS,
    FIB_LEVELS,
    fib_levels,
)
from ui import drawing_overlay as DO
from ui import lwc_view as LV

REPO = Path(__file__).resolve().parent.parent
PRIMITIVES_JS = REPO / "chart_assets" / "lwc" / "primitives.js"
MATRIX = REPO / "docs" / "lwc_parity_matrix.md"

_NODE = shutil.which("node")

SYMBOL = "LWC-DRAW"
TIMEFRAME = "5 mins"
PERIOD = 300

KINDS = ("trendline", "horizontal", "zone", "fibonacci", "measure")
FIXTURE_NAMES = ("dst_fold", "dst_spring", "session_boundary", "index_collision")


def _ts(y, m, d, hour, minute):
    return int(datetime(y, m, d, hour, minute, tzinfo=timezone.utc).timestamp())


# ── DG93 fixtures ────────────────────────────────────────────────────────────


def _fixture(name: str):
    """``(bars, ext_hours)`` for one DG93 edge fixture."""
    if name == "dst_fold":
        # 2024-11-03: 01:00 EDT -> 01:00 EST at 06:00 UTC.
        tss = [_ts(2024, 11, 3, 5, 0) + i * PERIOD for i in range(30)]
        ext = True
    elif name == "dst_spring":
        # 2025-03-09: 02:00 EST -> 03:00 EDT at 07:00 UTC.
        tss = [_ts(2025, 3, 9, 6, 30) + i * PERIOD for i in range(24)]
        ext = True
    elif name == "session_boundary":
        # 2024-10-03 (EDT): RTH morning, the 16:00 ET close, then the next
        # day's opening bar — the overnight collapse plus a same-day tail.
        tss = ([_ts(2024, 10, 3, 13, 30) + i * PERIOD for i in range(20)]
               + [_ts(2024, 10, 3, 19, 55) + i * PERIOD for i in range(3)]
               + [_ts(2024, 10, 4, 13, 30) + i * PERIOD for i in range(5)])
        ext = False
    elif name == "index_collision":
        # Two pairs of bars share one timestamp (hence one display-x).
        base = _ts(2024, 9, 25, 13, 30)
        tss = [base, base, base + PERIOD, base + PERIOD, base + 2 * PERIOD]
        ext = True
    else:  # pragma: no cover — parametrization guard
        raise AssertionError(f"unknown fixture: {name}")
    bars = [
        Bar(symbol=SYMBOL, timeframe=TIMEFRAME, ts=ts,
            open=100.0 + i * 0.05, high=101.0 + i * 0.05,
            low=99.0 + i * 0.05, close=100.5 + i * 0.05, volume=10.0 + i)
        for i, ts in enumerate(tss)
    ]
    return bars, ext


def _plotted(bars, ext):
    return [bars[i] for i in chart_model.plotted_index_rows(
        bars, TIMEFRAME, ext)]


def _axis(bars, ext):
    plotted = _plotted(bars, ext)
    xs, indices, cmap = LV.drawing_axis(plotted, TIMEFRAME, ext)
    return plotted, xs, indices, cmap


# ── reference engine (ui/drawing_overlay.py) ─────────────────────────────────


class _Signal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)


class _FakeScene:
    def __init__(self):
        self.sigMouseMoved = _Signal()


class _FakePlot:
    """Just enough PlotWidget for ``DrawingOverlay``'s item bookkeeping."""

    def __init__(self):
        self.items = []
        self._scene = _FakeScene()

    def scene(self):
        return self._scene

    def getViewBox(self):  # noqa: N802 — pyqtgraph's own name
        return None

    def addItem(self, item):  # noqa: N802
        self.items.append(item)

    def removeItem(self, item):  # noqa: N802
        if item in self.items:
            self.items.remove(item)


def _reference(bars, ext, drawings, groups=()):
    """The shipped overlay's own rendering of the same records."""
    plotted = _plotted(bars, ext)
    cmap = chart_model.collapse_for_bars(plotted, TIMEFRAME, ext)
    overlay = DO.DrawingOverlay(_FakePlot())
    overlay.set_symbol(SYMBOL)
    overlay.set_bars(plotted)
    overlay.set_collapse_map(cmap)
    overlay.set_data(SYMBOL, list(drawings), list(groups))
    return overlay


def _drawing(kind, anchors, y1, y2, drawing_id=1, color=None):
    ts1, ts2 = anchors
    if kind == "trendline":
        payload = {"p1": {"x": ts1, "y": y1}, "p2": {"x": ts2, "y": y2}}
    elif kind == "measure":
        payload = {"p1": {"x": ts1, "y": y1}, "p2": {"x": ts2, "y": y2}}
    elif kind == "horizontal":
        payload = {"y": y1}
    elif kind == "zone":
        payload = {"x1": ts1, "x2": ts2, "y1": y1, "y2": y2}
    elif kind == "fibonacci":
        payload = {"p1": {"x": ts1, "y": y1},
                   "p2": {"x": ts2, "y": y2}, "type": "retr"}
    else:  # pragma: no cover
        raise AssertionError(kind)
    kwargs = {}
    if color is not None:
        kwargs["color"] = color
    return Drawing(symbol=SYMBOL, kind=kind, payload=payload, id=drawing_id,
                   **kwargs)


def _view(bars, ext):
    view = LV.LwcChartView(tz_offset=14400)
    view.set_symbol(SYMBOL)
    view.set_timeframe(TIMEFRAME)
    view.set_extended_hours(ext)
    view.set_series("candles", bars)
    return view


# ── JS harness ───────────────────────────────────────────────────────────────


_NODE_SCRIPT = r"""
const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8"));
const mod = require(req.module);

const out = {
  channel: mod.DRAWING_CHANNEL,
  kinds: mod.DRAWING_KINDS,
  widths: mod.LINE_WIDTHS,
  z: mod.DRAWING_Z,
  alpha: mod.ZONE_ALPHA,
  inset: mod.LABEL_INSET_PX,
  minHeight: mod.LABEL_MIN_HEIGHT_PX,
  handle: {
    size: mod.HANDLE_SIZE, pen: mod.HANDLE_PEN,
    brush: mod.HANDLE_BRUSH, width: mod.HANDLE_PEN_WIDTH,
  },
  selected: { color: mod.SELECTED_COLOR, width: mod.SELECTED_WIDTH },
  check: req.envelope ? mod.validateEnvelope(req.envelope) : null,
};

if (req.items) {
  out.plan = mod.renderPlan(req.items, req.groups || [],
                            req.selectedId === undefined ? null : req.selectedId);
}
if (req.anchors) {
  out.mapped = req.anchors.map(function (x) {
    const f = mod.displayToFrac(x, req.xs, req.indices);
    return { frac: f, back: mod.fracToDisplay(f, req.xs, req.indices) };
  });
}
if (req.drag) {
  out.drag = mod.dragItem(req.drag.item, req.drag.pointIndex,
                          req.drag.dFrac, req.drag.dPrice, req.drag.body);
}
if (req.fibs) {
  out.fibs = req.fibs.map(function (f) {
    return mod.fibLevels(f.y1, f.y2, f.type);
  });
}
if (req.labelsFor) {
  out.labels = req.labelsFor.map(function (item) { return mod.labelsFor(item); });
}
if (req.visible) {
  out.visible = mod.visibleItems(req.items, req.groups || [])
    .map(function (item) { return item.id; });
}
if (req.selftest) {
  const attached = [];
  const series = {
    attachPrimitive: function (primitive) { attached.push(primitive); },
    priceToCoordinate: function () { return 0; },
  };
  const chart = {
    timeScale: function () {
      return { timeToCoordinate: function () { return 0; } };
    },
  };
  mod.bind(chart, series);
  out.results = req.envelopes.map(function (env) { return mod.applyDrawOps(env); });
  out.snapshot = mod.snapshot();
  out.attached = attached.length;
  if (req.replay && req.envelopes.length) {
    const last = req.envelopes[req.envelopes.length - 1];
    const before = JSON.stringify(mod.snapshot());
    mod.applyDrawOps(last);
    mod.applyDrawOps(last);
    out.replaySame = JSON.stringify(mod.snapshot()) === before;
  }
}

process.stdout.write(JSON.stringify(out));
"""


def _run_node(payload: dict) -> dict:
    """Run ``primitives.js`` under node and return its JSON answer."""
    if _NODE is None:  # pragma: no cover — the wave's test command needs node
        pytest.fail("node is required for the drawing-parity suites")
    data = dict(payload)
    data["module"] = str(PRIMITIVES_JS)
    proc = subprocess.run(
        [_NODE, "-e", _NODE_SCRIPT],
        input=json.dumps(data), capture_output=True, text=True,
        cwd=str(REPO), timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def _assert_close(actual, expected, path=""):
    """Recursive ``==`` with float tolerance (JSON round-trip safe)."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: {actual!r} is not a dict"
        assert set(actual) == set(expected), f"{path}: keys differ"
        for key in expected:
            _assert_close(actual[key], expected[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: {actual!r} is not a list"
        assert len(actual) == len(expected), f"{path}: lengths differ"
        for i, (a, e) in enumerate(zip(actual, expected)):
            _assert_close(a, e, f"{path}[{i}]")
        return
    if isinstance(expected, float) or isinstance(actual, float):
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-9), path
        return
    assert actual == expected, f"{path}: {actual!r} != {expected!r}"


def _texts(items):
    return [item.toPlainText() for item in items
            if hasattr(item, "toPlainText")]


def _all_keys(value):
    """Every dict key appearing anywhere in a JSON-shaped value."""
    keys = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys |= _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            keys |= _all_keys(item)
    return keys


def _pen(item):
    return item.pen


# ── T11 · fractional-index mapping (AC1 / DG93) ─────────────────────────────


class TestFractionalIndexMapping:
    def test_P6_T09_T11_constants_match_the_reference(self):
        assert LV.DRAWING_CHANNEL == "drawings"
        assert tuple(LV.DRAWING_KINDS) == KINDS
        assert LV.DRAWING_Z == 10
        assert LV.DRAWING_ZONE_ALPHA == 36
        assert LV.DRAWING_LINE_WIDTHS == {
            "trendline": 1.4, "horizontal": 1.2, "zone": 1.0,
            "fibonacci": 1.0, "measure": 1.4,
        }
        assert LV.DRAWING_LABEL_INSET_PX == 4.0
        assert LV.DRAWING_LABEL_MIN_HEIGHT_PX == 15.0
        assert (LV.DRAWING_HANDLE_SIZE, LV.DRAWING_HANDLE_PEN,
                LV.DRAWING_HANDLE_BRUSH, LV.DRAWING_HANDLE_PEN_WIDTH) == (
                    DO.HANDLE_SIZE, "#ffffff", "#0ea5e9", 1.5)

        decoded = _run_node({})
        assert decoded["channel"] == LV.DRAWING_CHANNEL
        assert decoded["kinds"] == list(LV.DRAWING_KINDS)
        assert decoded["widths"] == LV.DRAWING_LINE_WIDTHS
        assert decoded["z"] == LV.DRAWING_Z
        assert decoded["alpha"] == LV.DRAWING_ZONE_ALPHA
        assert decoded["inset"] == LV.DRAWING_LABEL_INSET_PX
        assert decoded["minHeight"] == LV.DRAWING_LABEL_MIN_HEIGHT_PX
        assert decoded["handle"] == {
            "size": LV.DRAWING_HANDLE_SIZE, "pen": LV.DRAWING_HANDLE_PEN,
            "brush": LV.DRAWING_HANDLE_BRUSH,
            "width": LV.DRAWING_HANDLE_PEN_WIDTH,
        }
        assert decoded["selected"] == {
            "color": LV.DRAWING_SELECTED_COLOR,
            "width": LV.DRAWING_SELECTED_WIDTH,
        }

    @pytest.mark.parametrize("name", FIXTURE_NAMES)
    def test_P6_T09_T11_mapping_round_trips_every_anchor(self, name, qapp):
        bars, ext = _fixture(name)
        plotted, xs, indices, cmap = _axis(bars, ext)
        assert plotted
        overlay = _reference(bars, ext, [])

        # Every bar, one off-grid point, and one anchor outside the window
        # (the reference overlay's collapse map clamps it).
        anchors = [bar.ts for bar in plotted]
        anchors.append(plotted[len(plotted) // 2].ts + 137)
        anchors.append(plotted[-1].ts + 7200)
        anchors.append(plotted[0].ts - 3600)
        reference_xs = [overlay._ts_to_x(ts) for ts in anchors]

        fracs = [LV.fractional_index_for_ts(ts, plotted, TIMEFRAME, ext)
                 for ts in anchors]
        for ts, x, frac in zip(anchors, reference_xs, fracs):
            back = LV.display_from_fractional_index(frac, xs, indices)
            assert back == pytest.approx(x, rel=1e-12, abs=1e-9), (
                f"{name}: ts={ts} reference x={x} back={back}")

        decoded = _run_node({
            "xs": xs, "indices": indices, "anchors": reference_xs,
        })
        assert len(decoded["mapped"]) == len(anchors)
        for mapped, x, frac in zip(decoded["mapped"], reference_xs, fracs):
            assert mapped["back"] == pytest.approx(x, rel=1e-12, abs=1e-9)
            assert mapped["frac"] == pytest.approx(frac, rel=1e-12, abs=1e-9)

    def test_P6_T09_T11_dst_fold_bars_keep_consecutive_indices(self, qapp):
        bars, ext = _fixture("dst_fold")
        plotted, xs, indices, _cmap = _axis(bars, ext)
        # The repeated wall-clock hour is still 5-minute UTC spacing: no bar
        # is lost and no stream of whitespace is invented.
        assert [indices[i + 1] - indices[i]
                for i in range(len(indices) - 1)] == [1] * (len(indices) - 1)
        assert [xs[i + 1] - xs[i]
                for i in range(len(xs) - 1)] == [PERIOD] * (len(xs) - 1)
        overlay = _reference(bars, ext, [])
        # Two bars one UTC hour apart across the fold render at their own x.
        left = plotted[6].ts
        right = plotted[18].ts
        assert overlay._ts_to_x(right) - overlay._ts_to_x(left) == 12 * PERIOD

    def test_P6_T09_T11_dst_spring_bars_keep_consecutive_indices(self, qapp):
        bars, ext = _fixture("dst_spring")
        _plotted_rows, xs, indices, _cmap = _axis(bars, ext)
        assert indices == list(range(len(indices)))
        assert [xs[i + 1] - xs[i]
                for i in range(len(xs) - 1)] == [PERIOD] * (len(xs) - 1)

    def test_P6_T09_T11_session_boundary_collapses_overnight(self, qapp):
        bars, ext = _fixture("session_boundary")
        plotted, xs, indices, _cmap = _axis(bars, ext)
        # 26 RTH bars after filtering; the overnight gap becomes whitespace
        # slots (logical indices keep the within-session step rule).
        assert len(plotted) < len(bars)
        assert indices[-1] > len(plotted) - 1
        steps = [indices[i + 1] - indices[i] for i in range(len(indices) - 1)]
        assert all(step >= 1 for step in steps)
        assert any(step > 1 for step in steps), "the overnight gap must show"

    def test_P6_T09_T11_display_x_collisions_resolve_identically(self, qapp):
        bars, ext = _fixture("index_collision")
        plotted, xs, indices, _cmap = _axis(bars, ext)
        overlay = _reference(bars, ext, [])
        # No bar is lost to a shared display-x: indices stay strictly rising.
        assert indices == list(range(len(plotted)))
        assert len(set(indices)) == len(indices)
        colliding = [i for i in range(len(xs) - 1) if xs[i] == xs[i + 1]]
        assert colliding, "the fixture must contain a display-x collision"
        for i in colliding:
            assert overlay._ts_to_x(plotted[i].ts) == xs[i]
            assert overlay._ts_to_x(plotted[i + 1].ts) == xs[i]
            # Both colliding indices inverse-map to the one shared x.
            for idx in (indices[i], indices[i + 1]):
                assert LV.display_from_fractional_index(
                    idx, xs, indices) == pytest.approx(xs[i])
            # The later index is the deterministic resolution.
            frac = LV.fractional_index_for_ts(
                plotted[i].ts, plotted, TIMEFRAME, ext)
            assert frac == pytest.approx(indices[i + 1])


# ── T11 · drawing parity (AC1) ──────────────────────────────────────────────


def _display(frac, xs, indices):
    return LV.display_from_fractional_index(frac, xs, indices)


class TestDrawingParity:
    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("name", FIXTURE_NAMES)
    def test_P6_T09_T11_each_kind_matches_the_reference(
            self, kind, name, qapp):
        bars, ext = _fixture(name)
        plotted, xs, indices, _cmap = _axis(bars, ext)
        anchors = (plotted[len(plotted) // 4].ts, plotted[-1].ts)
        drawing = _drawing(kind, anchors, 100.5, 102.25)

        overlay = _reference(bars, ext, [drawing])
        reference_items = overlay._items[1]

        view = _view(bars, ext)
        view.set_drawings([drawing])
        assert len(view.drawing_items) == 1
        item = view.drawing_items[0]
        envelope = view.drawing_envelopes[-1]
        decoded = _run_node({
            "envelope": envelope,
            "items": [item],
            "xs": xs,
            "indices": indices,
        })
        assert decoded["check"] == {"ok": True, "error": None}
        plan = decoded["plan"]
        assert plan["selectedId"] is None

        texts = _texts(reference_items)

        if kind == "trendline" or kind == "measure":
            line = reference_items[0]
            ref_x, ref_y = line.getData()
            ref_x = [float(v) for v in ref_x]
            ref_y = [float(v) for v in ref_y]
            assert ref_y == [p[1] for p in item["points"]]
            assert ref_x == [_display(p[0], xs, indices)
                             for p in item["points"]]
            assert LV.DRAWING_LINE_WIDTHS[kind] == pytest.approx(
                float(line.opts["pen"].widthF()))
            assert line.opts["pen"].color().name() == item["color"]

            assert len(plan["lines"]) == 1
            seg = plan["lines"][0]
            _assert_close(seg["x1"], item["points"][0][0])
            _assert_close(seg["y1"], item["points"][0][1])
            _assert_close(seg["x2"], item["points"][1][0])
            _assert_close(seg["y2"], item["points"][1][1])
            assert seg["width"] == pytest.approx(item["width"])
            assert seg["color"] == item["color"]
            assert seg["z"] == float(line.zValue()) == LV.DRAWING_Z

            if kind == "trendline":
                assert [label["text"] for label in plan["labels"]] == texts
                assert texts == [f"{p[1]:.2f}" for p in item["points"]]
                assert [label["anchor"] for label in plan["labels"]] == [
                    "inner-right", "inner-right"]
                for label in plan["labels"]:
                    json.dumps(label)  # primitives only
                    assert label["anchor"] == "inner-right"
                    assert "z" not in label
            else:
                assert len(plan["labels"]) == 1
                label = plan["labels"][0]
                assert label["anchor"] == "center"
                assert label["text"] == texts[0]
                assert label["text"] == (
                    f"\u0394 {item['delta']['dy']:+.2f}  "
                    f"({item['delta']['pct']:+.2f}%)")
                assert label["frac"] == pytest.approx(
                    (item["points"][0][0] + item["points"][1][0]) / 2)
                assert label["price"] == pytest.approx(
                    (item["points"][0][1] + item["points"][1][1]) / 2)
                assert float(reference_items[1].pos().y()) == pytest.approx(
                    label["price"])

        elif kind == "horizontal":
            line = reference_items[0]
            assert float(line.value()) == item["price"]
            assert float(line.pen.widthF()) == item["width"] == 1.2
            assert line.pen.color().name() == item["color"]
            assert len(plan["hlines"]) == 1
            assert plan["hlines"][0]["price"] == item["price"]
            assert plan["hlines"][0]["z"] == float(line.zValue()) == 10
            assert [label["text"] for label in plan["labels"]] == texts
            assert texts == [f"{item['price']:.2f}"]

        elif kind == "zone":
            region = reference_items[0]
            assert list(region.getRegion()) == pytest.approx(
                [item["y1"], item["y2"]])
            assert region.brush.color().alpha() == 36
            assert float(region.lines[0].pen.widthF()) == item["width"] == 1.0
            assert region.lines[0].pen.color().name() == item["color"]
            assert len(plan["rects"]) == 1
            rect = plan["rects"][0]
            assert rect["y1"] == item["y1"] and rect["y2"] == item["y2"]
            assert rect["fillAlpha"] == 36
            assert rect["x1"] is None and rect["x2"] is None
            assert rect["z"] == float(region.zValue()) == 10
            assert [label["text"] for label in plan["labels"]] == texts
            assert texts == [f"{item['y1']:.2f}", f"{item['y2']:.2f}"]
            # The zone's own x anchors survive as its two corner handles.
            assert [_display(p[0], xs, indices) for p in item["handles"]] == [
                overlay._ts_to_x(anchors[0]),
                overlay._ts_to_x(anchors[1]),
            ]

        elif kind == "fibonacci":
            lines = reference_items[0::2]
            labels = reference_items[1::2]
            assert len(lines) == len(FIB_LEVELS) == len(item["levels"])
            assert [float(line.value()) for line in lines] == pytest.approx(
                [price for _ratio, price in item["levels"]])
            assert [float(line.pen.widthF()) for line in lines] == [1.0] * 7
            assert all(float(line.zValue()) == 10 for line in lines)
            assert len(plan["hlines"]) == 7
            assert [level["price"] for level in plan["hlines"]] == [
                price for _ratio, price in item["levels"]]
            assert all(level["z"] == 10 for level in plan["hlines"])
            assert [label["text"] for label in plan["labels"]] == _texts(labels)
            for label, (ratio, price) in zip(plan["labels"], item["levels"]):
                assert label["text"] == f"{ratio * 100:.1f}%  {price:.2f}"
                assert label["price"] == price
            assert item["levels"] == [[float(r), float(p)] for r, p in
                                      fib_levels(100.5, 102.25, "retr")]

        else:  # pragma: no cover — KINDS is exhaustive
            raise AssertionError(kind)

    @pytest.mark.parametrize("fib_type", ("retr", "ext"))
    def test_P6_T09_T11_fib_levels_are_the_service_geometry(self, fib_type):
        y1, y2 = 100.5, 102.25
        drawing = Drawing(
            symbol=SYMBOL, kind="fibonacci", id=1,
            payload={"p1": {"x": 0, "y": y1}, "p2": {"x": 300, "y": y2},
                     "type": fib_type})
        item = LV.drawing_item(drawing, [0, 300], [0, 1])
        expected = [[float(ratio), float(price)]
                    for ratio, price in fib_levels(y1, y2, fib_type)]
        assert item["levels"] == expected
        assert [ratio for ratio, _price in item["levels"]] == list(
            FIB_EXTENSION_LEVELS if fib_type == "ext" else FIB_LEVELS)

        decoded = _run_node({"fibs": [{"y1": y1, "y2": y2,
                                       "type": fib_type}]})
        _assert_close(decoded["fibs"][0], expected)

    def test_P6_T09_T11_custom_colour_crosses_unchanged(self, qapp):
        bars, ext = _fixture("dst_fold")
        plotted, xs, indices, _cmap = _axis(bars, ext)
        drawing = _drawing("horizontal", (plotted[0].ts, plotted[1].ts),
                           101.0, 101.0, color="#ff8800")
        view = _view(bars, ext)
        view.set_drawings([drawing])
        item = view.drawing_items[0]
        assert item["color"] == "#ff8800"
        decoded = _run_node({"items": [item]})
        assert decoded["plan"]["hlines"][0]["color"] == "#ff8800"
        assert decoded["plan"]["labels"][0]["color"] == "#ff8800"

    @pytest.mark.parametrize("kind", KINDS)
    def test_P6_T09_T11_identical_state_republishes_identical_values(
            self, kind, qapp):
        bars, ext = _fixture("dst_spring")
        plotted, _xs, _indices, _cmap = _axis(bars, ext)
        drawing = _drawing(kind, (plotted[0].ts, plotted[-1].ts), 100.5, 102.25)
        first = _view(bars, ext)
        first.set_drawings([drawing])
        second = _view(bars, ext)
        second.set_drawings([drawing])
        assert first.drawing_ops == second.drawing_ops
        assert first.drawing_envelopes == second.drawing_envelopes

    def test_P6_T09_T11_replay_is_idempotent_and_empty_clears(self, qapp):
        bars, ext = _fixture("dst_fold")
        plotted, _xs, _indices, _cmap = _axis(bars, ext)
        drawings = [
            _drawing(kind, (plotted[2].ts, plotted[8].ts), 100.5, 102.25,
                     drawing_id=i + 1)
            for i, kind in enumerate(KINDS)
        ]
        view = _view(bars, ext)
        view.set_drawings(drawings)
        envelopes = view.drawing_envelopes
        decoded = _run_node({"envelopes": envelopes, "selftest": True,
                             "replay": True})
        assert all(result["error"] is None for result in decoded["results"])
        assert decoded["results"][0]["applied"] == 1
        assert decoded["attached"] == 1
        assert decoded["replaySame"] is True
        assert [item["id"] for item in decoded["snapshot"]["items"]] == [
            1, 2, 3, 4, 5]

        view.set_drawings([])
        assert view.drawing_ops[-1] == LV.clear_drawings_op()
        cleared = _run_node({"envelopes": view.drawing_envelopes, "selftest": True})
        assert cleared["snapshot"]["items"] == []
        assert cleared["snapshot"]["plan"]["lines"] == []

    def test_P6_T09_T11_set_drawing_primitive_validates_frac_points(self, qapp):
        bars, ext = _fixture("dst_fold")
        _plotted_rows, xs, indices, _cmap = _axis(bars, ext)
        view = _view(bars, ext)
        view.set_drawing_primitive("trendline", [[2.0, 100.5], [7.25, 102.0]])
        op = view.drawing_ops[-1]
        assert op == {
            "op": "set_drawing_primitive", "series": "drawings",
            "kind": "trendline", "points": [[2.0, 100.5], [7.25, 102.0]],
        }
        decoded = _run_node({"envelope": view.drawing_envelopes[-1]})
        assert decoded["check"] == {"ok": True, "error": None}

        view.set_drawing_primitive("horizontal", [[3.0, 101.5]])
        assert view.drawing_ops[-1]["points"] == [[3.0, 101.5]]

        with pytest.raises(ValueError):
            view.set_drawing_primitive("circle", [[0.0, 1.0]])
        with pytest.raises(ValueError):
            view.set_drawing_primitive("trendline", [[0.0, 1.0]])
        with pytest.raises(ValueError):
            view.set_drawing_primitive("trendline", [[0.0, "1.0"], [1.0, 2.0]])
        with pytest.raises(ValueError):
            view.set_drawing_primitive("horizontal", [])


# ── T11 · groups, handles, selection, drag-edit ─────────────────────────────


class TestGroupsHandlesAndDrag:
    def _fixture_rows(self):
        bars, ext = _fixture("dst_fold")
        plotted, xs, indices, _cmap = _axis(bars, ext)
        return bars, ext, plotted, xs, indices

    def test_P6_T09_T11_hidden_group_draws_nothing_on_either_engine(self,
                                                                    qapp):
        bars, ext, plotted, _xs, _indices = self._fixture_rows()
        drawing = _drawing("zone", (plotted[0].ts, plotted[-1].ts),
                           100.5, 102.25)
        drawing.group_id = 7
        hidden = DrawingGroup(symbol=SYMBOL, name="hidden", seq_number=1,
                              id=7, visible=False)
        overlay = _reference(bars, ext, [drawing], [hidden])
        assert 1 not in overlay._items

        view = _view(bars, ext)
        view.set_drawings([drawing], [hidden])
        assert view.drawing_items == []
        assert view.drawing_ops[-1]["items"] == []

        visible = DrawingGroup(symbol=SYMBOL, name="shown", seq_number=1,
                              id=7, visible=True)
        view.set_drawing_groups([visible])
        assert [item["id"] for item in view.drawing_items] == [1]
        decoded = _run_node({
            "items": view.drawing_items, "groups": [
                {"id": 7, "visible": False, "locked": False}],
            "visible": True,
        })
        assert decoded["visible"] == []
        assert decoded["plan"]["rects"] == []
        decoded = _run_node({
            "items": view.drawing_items,
            "groups": [{"id": 7, "visible": True, "locked": False}],
            "visible": True,
        })
        assert decoded["visible"] == [1]

    def test_P6_T09_T11_locked_group_suppresses_handles(self, qapp):
        bars, ext, plotted, _xs, _indices = self._fixture_rows()
        drawing = _drawing("trendline", (plotted[0].ts, plotted[5].ts),
                           100.5, 102.25)
        drawing.group_id = 3
        locked = DrawingGroup(symbol=SYMBOL, name="locked", seq_number=1,
                              id=3, locked=True)
        overlay = _reference(bars, ext, [drawing], [locked])
        overlay._select(1)
        assert len(overlay._handles.points()) == 0

        view = _view(bars, ext)
        view.set_drawings([drawing], [locked])
        item = view.drawing_items[0]
        assert item["locked"] is True
        view.select_drawing(1)
        decoded = _run_node({
            "items": view.drawing_items, "selectedId": 1,
            "groups": [{"id": 3, "visible": True, "locked": True}],
        })
        assert decoded["plan"]["handles"] == []

    def test_P6_T09_T11_selection_and_handles_match_the_reference(self, qapp):
        bars, ext, plotted, xs, indices = self._fixture_rows()
        drawing = _drawing("trendline", (plotted[1].ts, plotted[6].ts),
                           100.5, 102.25)
        overlay = _reference(bars, ext, [drawing])
        overlay._select(1)
        ref_pen = overlay._items[1][0].opts["pen"]
        assert ref_pen.color().name() == LV.DRAWING_SELECTED_COLOR
        assert float(ref_pen.widthF()) == LV.DRAWING_SELECTED_WIDTH
        ref_handles = [spot.pos() for spot in overlay._handles.points()]

        view = _view(bars, ext)
        view.set_drawings([drawing])
        view.select_drawing(1)
        assert view.selected_drawing == 1
        assert view.drawing_ops[-1] == {
            "op": "select_drawing", "series": "drawings", "id": 1}
        item = view.drawing_items[0]
        assert item["selected"] is True

        decoded = _run_node({"items": [item], "selectedId": 1})
        plan = decoded["plan"]
        assert plan["lines"][0]["color"] == LV.DRAWING_SELECTED_COLOR
        assert plan["lines"][0]["width"] == LV.DRAWING_SELECTED_WIDTH
        assert len(plan["handles"]) == len(ref_handles) == 2
        for handle, ref_pos in zip(plan["handles"], ref_handles):
            assert _display(handle["frac"], xs, indices) == pytest.approx(
                float(ref_pos.x()))
            assert handle["price"] == pytest.approx(float(ref_pos.y()))
            assert handle["size"] == DO.HANDLE_SIZE
            assert handle["brush"] == "#0ea5e9"

    @pytest.mark.parametrize("kind", ("trendline", "measure", "fibonacci",
                                      "zone", "horizontal"))
    def test_P6_T09_T11_drag_edit_matches_the_reference(self, kind, qapp):
        from PyQt6.QtCore import QPointF

        bars, ext, plotted, xs, indices = self._fixture_rows()
        drawing = _drawing(kind, (plotted[2].ts, plotted[7].ts),
                           100.5, 102.25)
        body = False
        point_index = 0
        d_price = 0.4
        d_frac = 1.0

        # Reference: a drag from the point's own anchor to one bar later.
        # The reference overlay mutates the Drawing in place (as the shipped
        # overlay does), so it gets its own copy — the wire item must be
        # built from the pristine record.
        reference_drawing = copy.deepcopy(drawing)
        overlay = _reference(bars, ext, [reference_drawing])
        if kind in ("trendline", "measure", "fibonacci", "zone"):
            grab_x = overlay._ts_to_x(plotted[2].ts)
            grab_y = 100.5 if kind != "zone" else reference_drawing.payload["y1"]
        else:
            grab_x = 0.0
            grab_y = 100.5
        overlay._drag = {
            "id": 1, "point_index": point_index, "body": body,
            "locked": False, "grab": (grab_x, grab_y),
        }
        overlay._apply_drag(QPointF(grab_x + PERIOD, grab_y + d_price))
        reference_payload = reference_drawing.payload

        # Move the wire item by the same one-bar / 0.40 delta.
        view = _view(bars, ext)
        view.set_drawings([drawing])
        item = view.drawing_items[0]
        moved = LV.drag_drawing_item(kind, item, point_index, d_frac, d_price,
                                     body=body)
        wire = view.drag_drawing(kind=kind, drawing_id=1,
                                 point_index=point_index, d_frac=d_frac,
                                 d_price=d_price, body=body)
        _assert_close(wire, moved)
        assert view.drawing_ops[-1]["op"] == "drag_drawing"

        decoded = _run_node({"drag": {
            "item": item, "pointIndex": point_index,
            "dFrac": d_frac, "dPrice": d_price, "body": body,
        }})
        _assert_close(decoded["drag"], moved)

        if kind in ("trendline", "measure", "fibonacci"):
            moved_x = [_display(p[0], xs, indices) for p in moved["points"]]
            assert moved_x[0] == pytest.approx(
                overlay._ts_to_x(reference_payload["p1"]["x"]),
                rel=1e-9, abs=1e-6)
            assert moved_x[1] == pytest.approx(
                overlay._ts_to_x(reference_payload["p2"]["x"]),
                rel=1e-9, abs=1e-6)
            assert moved["points"][0][1] == pytest.approx(
                reference_payload["p1"]["y"])
        elif kind == "zone":
            assert moved["y1"] == pytest.approx(
                reference_payload["y1"], rel=1e-12)
            assert moved["y2"] == pytest.approx(
                reference_payload["y2"], rel=1e-12)
        else:
            assert moved["price"] == pytest.approx(
                reference_payload["y"], rel=1e-12)

    def test_P6_T09_T11_body_drag_translates_the_whole_primitive(self, qapp):
        from PyQt6.QtCore import QPointF

        bars, ext, plotted, xs, indices = self._fixture_rows()
        drawing = _drawing("trendline", (plotted[2].ts, plotted[7].ts),
                           100.5, 102.25)
        reference_drawing = copy.deepcopy(drawing)
        overlay = _reference(bars, ext, [reference_drawing])
        grab_x = overlay._ts_to_x(plotted[2].ts)
        grab_y = 100.5
        overlay._drag = {
            "id": 1, "point_index": -1, "body": True,
            "locked": False, "grab": (grab_x, grab_y),
        }
        overlay._apply_drag(QPointF(grab_x + PERIOD, grab_y - 0.25))

        view = _view(bars, ext)
        view.set_drawings([drawing])
        item = view.drawing_items[0]
        moved = LV.drag_drawing_item("trendline", item, -1, 1.0, -0.25,
                                     body=True)
        assert moved["points"][0][0] == pytest.approx(item["points"][0][0] + 1)
        assert moved["points"][1][0] == pytest.approx(item["points"][1][0] + 1)
        assert moved["points"][0][1] == pytest.approx(100.25)
        assert moved["points"][1][1] == pytest.approx(102.0)
        ref_payload = reference_drawing.payload
        assert _display(moved["points"][0][0], xs, indices) == pytest.approx(
            overlay._ts_to_x(ref_payload["p1"]["x"]), abs=1e-6)
        assert _display(moved["points"][1][0], xs, indices) == pytest.approx(
            overlay._ts_to_x(ref_payload["p2"]["x"]), abs=1e-6)

        decoded = _run_node({"drag": {
            "item": item, "pointIndex": -1, "dFrac": 1.0,
            "dPrice": -0.25, "body": True,
        }})
        _assert_close(decoded["drag"], moved)


# ── T12/T13 · renderer-only boundary, Qt dialogs, parity matrix ─────────────


def _uses_pyqtgraph(src: str) -> bool:
    """True when source imports or instantiates pyqtgraph (ESC-072).

    The boundary is a property — the LWC engine must not import or use the
    default engine — not the literal word. A docstring that merely names the
    default engine passes; a real import/usage still fails.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:  # a JS asset: text is all there is
        return "pyqtgraph" in src
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "pyqtgraph"
                   for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "pyqtgraph":
                return True
        elif isinstance(node, ast.Name) and node.id == "pyqtgraph":
            return True
    return False


class TestRendererBoundary:
    SOURCES = ["ui/lwc_view.py", "chart_assets/lwc/primitives.js"]

    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings", "DrawingStore", "drawing_store",
        "placeOrder", "cancelOrder", "UserOrder", "OrderRateLimiter",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdn.", "http://", "https://",
        "orders", "BarCache", "get_bars", "save_bars",
    ]

    def test_P6_T09_T13_no_out_of_scope_surface(self):
        hits = []
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                if token == "pyqtgraph":
                    # ESC-072: assert the property, not the word.
                    if _uses_pyqtgraph(src):
                        hits.append(f"{rel}: 'pyqtgraph' imported/used")
                elif token in src:
                    hits.append(f"{rel}: {token!r}")
        assert hits == [], f"out-of-scope residue: {hits}"

    def test_P6_T09_T13_view_imports_stay_renderer_only(self):
        import ast

        tree = ast.parse((REPO / "ui/lwc_view.py").read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module or "")
        forbidden = {
            "ibkr", "data.db", "data.drawing_store", "data.models",
            "services.backfill_service",
            "PyQt6.QtNetwork", "requests", "urllib", "urllib.request",
        }
        assert not {name for name in names
                    if name in forbidden or name.startswith("ibkr.")}

    def test_P6_T09_T13_stores_services_and_overlays_are_untouched(self):
        tokens = ("set_drawings", "drawingOpsEmitted", "primitives.js",
                  "LwcChartView", "DRAWING_CHANNEL", "lwc")
        for rel in ("data/drawing_store.py", "services/drawing_service.py",
                    "ui/drawing_overlay.py",
                    "ui/zone_settings_dialog.py",
                    "ui/horizontal_line_settings_dialog.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            hits = [token for token in tokens if token in src]
            assert hits == [], f"{rel} picked up LWC vocabulary: {hits}"

    def test_P6_T09_T13_drawing_ops_carry_frac_indices_and_prices_only(
            self, qapp):
        bars, ext = _fixture("session_boundary")
        plotted, _xs, _indices, _cmap = _axis(bars, ext)
        drawings = [
            _drawing(kind, (plotted[2].ts, plotted[10].ts), 100.5, 102.25,
                     drawing_id=i + 1)
            for i, kind in enumerate(KINDS)
        ]
        view = _view(bars, ext)
        view.set_drawings(drawings)
        view.select_drawing(1)
        for op in view.drawing_ops:
            json.dumps(op)  # primitives only, no objects
            assert op["series"] == "drawings"
            # No timestamp key survives any drawing op: time crosses as a
            # fractional index, never as a raw ts.
            assert "ts" not in _all_keys(op)
        set_op = view.drawing_ops[0]
        assert set_op["op"] == "set_drawings"
        for item in set_op["items"]:
            assert isinstance(item["color"], str)
            assert isinstance(item["z"], int)
            assert isinstance(item["width"], float)
            for point in item.get("points", []):
                assert isinstance(point[0], float)
                assert isinstance(point[1], float)
            assert isinstance(item["kind"], str)

    def test_P6_T09_T13_drawings_never_ride_the_bar_transport(self, qapp):
        bars, ext = _fixture("dst_fold")
        plotted, _xs, _indices, _cmap = _axis(bars, ext)
        view = _view(bars, ext)
        view.set_drawings([
            _drawing("horizontal", (plotted[0].ts, plotted[1].ts), 100.5,
                     100.5)])
        log = view.bridge.replay_log()
        assert log, "the bar transport carries the candles/volume ops"
        assert all(op["series"] in {"candles", "volume"} for op in log)
        assert all(op["series"] == "drawings" for op in view.drawing_ops)

    def test_P6_T09_T12_no_html_dialog_is_rebuilt(self):
        hits = []
        for path in sorted((REPO / "chart_assets").rglob("*")):
            if path.suffix.lower() not in {".js", ".html", ".css"}:
                continue
            low = path.read_text(encoding="utf-8", errors="ignore").lower()
            for token in ("<dialog", "showmodal", "zone_settings_dialog",
                          "horizontal_line_settings_dialog"):
                if token in low:
                    hits.append(f"{path.relative_to(REPO)}: {token}")
        assert hits == [], f"HTML dialog rebuild found: {hits}"

        for rel in ("ui/zone_settings_dialog.py",
                    "ui/horizontal_line_settings_dialog.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            assert "QDialog" in src, f"{rel} is no longer a Qt dialog"
            assert "lwc" not in src.lower()

    def test_P6_T09_T12_qt_dialog_suites_green_unmodified(self):
        modules = [str(REPO / "tests" / name) for name in (
            "test_zone_dialog.py", "test_horizontal_line_dialog.py")]
        for module in modules:
            assert Path(module).exists(), module
        env = dict(os.environ)
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *modules, "-q"],
            cwd=str(REPO), capture_output=True, text=True, timeout=300,
            env=env,
        )
        assert proc.returncode == 0, (
            proc.stdout[-2000:] + proc.stderr[-2000:])

    def test_P6_T09_T11_parity_row_11_moves_to_done(self):
        text = MATRIX.read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("| 11 |")]
        assert len(rows) == 1, rows
        assert "P6-09" in rows[0]
        assert rows[0].rstrip().endswith("Done / accepted |"), rows[0]
        assert "primitives.js" in text, "the wave note names the JS module"
        for row in text.splitlines():
            if row.startswith("|") and "Done / accepted" in row:
                assert "Open / pending" not in row
