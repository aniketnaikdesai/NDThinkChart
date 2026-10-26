"""tests/test_lwc_overlays.py — P6-T10 Phase 8 overlays + event markers (M).

The overlay-parity cases: identical bars/sessions/events must render identical
session bands, gap/VIX/ICT overlays and dividend/earnings/split markers on both
engines. Every reference below is the shipped default-engine renderer driven
on the same fixtures — ``ui/overlays/session_overlay.py``,
``ui/overlays/gap_overlay.py``, ``ui/overlays/vix_overlay.py``,
``ui/overlays/ict_overlay.py`` and ``ui/event_marker_overlay.py`` — and every
geometry value is compared in the **display-x** space both engines share:
``display_from_fractional_index`` on the LWC side is the inverse of the
reference overlays' ``_index_to_x`` / ``_ts_to_x``, so a region that lands on
the identical bar in both engines compares numerically equal.

The reference values themselves come from the unchanged services
(``session_bands``, ``calculate_rth_gaps``,
``calculate_vix_standard_deviation``, ``calculate_ict_concepts``), which this
suite also drives directly for the reference rendering — the parity is on the
render mapping, not on a second implementation of the numbers.

The residue scan closes the renderer-only boundary: no ``ibkr/``, store,
service-signature, watchlist/dock/persistence or order surface, no timestamps
or formatted labels on the wire, and the reference overlays/services untouched.

QApplication usage: the view is a ``QWidget`` and the reference overlays build
graphics items, so the render cases take the repo's session-scoped ``qapp``
fixture (a locally created application gets collected and aborts the process
at the next widget construction).
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt

from data.models import Bar
from services import chart_model
from services import gap_vix_service as GS
from services import ict_service as IS
from services import session_service as SS
from ui import event_marker_overlay as EO
from ui import lwc_view as LV
from ui.overlays import gap_overlay as GO
from ui.overlays import ict_overlay as IO
from ui.overlays import session_overlay as SO
from ui.overlays import vix_overlay as VO

REPO = Path(__file__).resolve().parent.parent
OVERLAYS_JS = REPO / "chart_assets" / "lwc" / "overlays.js"
MATRIX = REPO / "docs" / "lwc_parity_matrix.md"

_NODE = shutil.which("node")

SYMBOL = "AAPL"
TIMEFRAME = "15 mins"
DAYS = (24, 25)          # 2026-09-24 (Thu) and 2026-09-25 (Fri), both trading
TZ_OFFSET = 14400        # EDT

#: The three overlay studies the default engine renders through its overlays.
OVERLAY_STUDIES = [
    {"type": "rth_gaps", "enabled": True, "params": {}},
    {"type": "vix_sd", "enabled": True, "params": {}},
    {"type": "ict", "enabled": True, "params": {}},
]

_STYLE_NAMES = {
    Qt.PenStyle.SolidLine: "solid",
    Qt.PenStyle.DashLine: "dashed",
    Qt.PenStyle.DotLine: "dotted",
}


# ── fixtures ─────────────────────────────────────────────────────────────────


def _bars(days=DAYS, symbol=SYMBOL):
    """Two extended-hours sessions of 15-minute bars with an overnight gap."""
    out = []
    price = 200.0
    for day in days:
        start = datetime(2026, 9, day, 8, 0, tzinfo=timezone.utc)  # 04:00 ET
        for i in range(64):
            ts = int((start + timedelta(minutes=15 * i)).timestamp())
            open_ = price
            close = price + (1.5 if i % 7 else -2.0)
            out.append(Bar(symbol=symbol, timeframe=TIMEFRAME, ts=ts,
                           open=open_, high=max(open_, close) + 0.5,
                           low=min(open_, close) - 0.5, close=close,
                           volume=100.0 + i))
            price = close
        price += 4.0  # the overnight gap the rth_gaps study draws
    return out


def _view(bars=None, ext_hours=True, studies=True):
    view = LV.LwcChartView(tz_offset=TZ_OFFSET)
    view.set_symbol(SYMBOL)
    view.set_timeframe(TIMEFRAME)
    view.set_series("candles", _bars() if bars is None else bars)
    view.set_extended_hours(ext_hours)
    if studies:
        view.set_studies(OVERLAY_STUDIES)
    return view


def _axis(view):
    return view.drawing_axis()


def _display_of_frac(view, frac):
    """Display-x for a fractional logical index (the shared axis space)."""
    xs, indices, _cmap = _axis(view)
    return LV.display_from_fractional_index(frac, xs, indices)


def _display_of_ts(view, ts):
    _xs, _indices, cmap = _axis(view)
    return float(cmap.to_display(ts))


# ── reference (default engine) ──────────────────────────────────────────────


class _FakePlot:
    """Just enough PlotWidget for the reference overlays' item bookkeeping."""

    def __init__(self):
        self.items = []

    def addItem(self, item):  # noqa: N802 — pyqtgraph's own name
        self.items.append(item)

    def removeItem(self, item):  # noqa: N802
        if item in self.items:
            self.items.remove(item)


class _Signal:
    def connect(self, slot):  # noqa: ARG002 — the reference only connects
        return None


class _FakeViewBox:
    """A view box the reference renderers can query and add items to."""

    sigYRangeChanged = _Signal()
    sigXRangeChanged = _Signal()

    def __init__(self):
        self.items = []
        self.range = [[0.0, 10.0], [0.0, 100.0]]

    def addItem(self, item):  # noqa: N802
        self.items.append(item)

    def removeItem(self, item):  # noqa: N802
        if item in self.items:
            self.items.remove(item)

    def viewRange(self):  # noqa: N802
        return self.range


class _MarkerPlot:
    def __init__(self):
        self.view = _FakeViewBox()

    def getViewBox(self):  # noqa: N802
        return self.view


def _reference_overlay(cls, view):
    overlay = cls(_FakePlot())
    overlay.set_collapse_map(_axis(view)[2])
    return overlay


def _reference_session(view):
    overlay = SO.SessionOverlay(_FakePlot())
    overlay.set_collapse_map(_axis(view)[2])
    bands = [
        {"kind": band["kind"],
         "start_ts": _display_of_ts(view, band["start_ts"]),
         "end_ts": _display_of_ts(view, band["end_ts"])}
        for band in SS.session_bands(list(view.plotted_bars), TIMEFRAME)
    ]
    overlay.render(bands)
    return overlay


def _reference_gaps(view):
    overlay = _reference_overlay(GO.RthGapOverlay, view)
    bars = list(view.plotted_bars)
    gaps = GS.calculate_rth_gaps(
        bars, GS.infer_ticker_context(SYMBOL, bars), {})
    overlay.render(gaps, bars)
    return overlay


def _reference_vix(view):
    overlay = _reference_overlay(VO.VixOverlay, view)
    bars = list(view.plotted_bars)
    result = GS.calculate_vix_standard_deviation(
        GS.infer_ticker_context(SYMBOL, bars), bars, {})
    overlay.render(result, bars)
    return overlay, result


def _reference_ict(view):
    overlay = _reference_overlay(IO.ICTStudyOverlay, view)
    bars = list(view.plotted_bars)
    window = chart_model.trailing_bars(bars, LV.ICT_TRAILING_BARS)
    result = IS.calculate_ict_concepts(
        window, GS.infer_ticker_context(SYMBOL, bars), {})
    overlay.render(result, window)
    return overlay, result, window


def _pen_of(item):
    pen = item.opts.get("pen")
    return {
        "color": pen.color().name() if pen is not None else None,
        "width": round(float(pen.widthF()), 4) if pen is not None else None,
        "style": _STYLE_NAMES.get(pen.style(), "solid") if pen is not None else None,
    }


def _spot_rows(item):
    """Normalise a ``ScatterPlotItem``'s spots across pyqtgraph versions."""
    rows = []
    for entry in getattr(item, "data", []) or []:
        if isinstance(entry, dict):
            pos = entry.get("pos") or (0.0, 0.0)
            brush = entry.get("brush")
            rows.append({
                "x": float(pos[0]), "price": float(pos[1]),
                "size": float(entry.get("size", 0)),
                "symbol": entry.get("symbol"),
                "color": brush.color().name() if brush is not None else None,
            })
            continue
        brush = entry[5]
        rows.append({
            "x": float(entry[0]), "price": float(entry[1]),
            "size": float(entry[2]), "symbol": entry[3],
            "color": brush.color().name() if brush is not None else None,
        })
    return rows


def _describe_reference_items(overlay):
    """Paint-order records for what a reference overlay actually drew.

    ``LinearRegionItem`` -> a full-height region; ``ScatterPlotItem`` -> point
    rows; a filled ``PlotDataItem`` -> a band (its brush alpha is the fill
    alpha); an unfilled one -> a segment. Text items are returned separately
    (they are the labels a segment already carries on the LWC side).
    """
    shapes, labels = [], []
    for item in overlay._items:
        name = type(item).__name__
        if name == "LinearRegionItem":
            region = item.getRegion()
            brush = item.brush.color()
            shapes.append({
                "shape": "region",
                "from": min(region), "to": max(region),
                "color": brush.name(), "alpha": round(brush.alphaF(), 4),
                "z": float(item.zValue()),
            })
        elif name == "InfiniteLine":
            pen = item.pen
            shapes.append({
                "shape": "hline",
                "price": float(item.value()),
                "color": pen.color().name(),
                "width": round(float(pen.widthF()), 4),
                "style": _STYLE_NAMES.get(pen.style(), "solid"),
                "z": float(item.zValue()),
            })
        elif name == "ScatterPlotItem":
            for spot in _spot_rows(item):
                shapes.append({
                    "shape": "point", "from": spot["x"],
                    "to": spot["x"], "price": spot["price"],
                    "color": spot["color"], "size": spot["size"],
                    "symbol": spot["symbol"], "z": float(item.zValue()),
                })
        elif name == "TextItem":
            labels.append({
                "text": item.toPlainText(),
                "x": float(item.pos().x()),
                "price": float(item.pos().y()),
                "color": item.color.name() if item.color is not None else None,
            })
        elif name == "PlotDataItem":
            xs, ys = item.getData()
            pen = _pen_of(item)
            fill = item.opts.get("fillBrush")
            if fill is not None:
                brush = fill.color() if hasattr(fill, "color") else fill
                shapes.append({
                    "shape": "band",
                    "from": float(min(xs)), "to": float(max(xs)),
                    "bottom": float(min(ys)), "top": float(max(ys)),
                    "color": pen["color"],
                    "alpha": round(brush.alphaF(), 4),
                    "fill": brush.name(),
                    "borderWidth": pen["width"],
                    "borderStyle": pen["style"],
                    "z": float(item.zValue()),
                })
            else:
                shapes.append({
                    "shape": "segment",
                    "from": float(min(xs)), "to": float(max(xs)),
                    "price": float(ys[0]), "color": pen["color"],
                    "width": pen["width"], "style": pen["style"],
                    "z": float(item.zValue()),
                })
    return shapes, labels


def _lwc_shapes(view, name):
    """The LWC overlay's regions, converted into the shared display-x space."""
    rows = []
    for region in view.overlays.get(name, []):
        row = dict(region)
        if "from" in row:
            row["from"] = _display_of_frac(view, row["from"])
        if "to" in row:
            row["to"] = _display_of_frac(view, row["to"])
        row["borderWidth"] = row.get("borderWidth", 0.8)
        rows.append(row)
    return rows


# ── JS harness ──────────────────────────────────────────────────────────────


_NODE_SCRIPT = r"""
const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8"));
const mod = require(req.module);

const out = {
  colors: mod.SESSION_COLORS,
  sessionAlpha: mod.SESSION_ALPHA,
  sessionZ: mod.SESSION_Z,
  gap: mod.GAP_STYLE,
  vix: mod.VIX_STYLE,
  ict: mod.ICT_STYLE,
  event: mod.EVENT_STYLE,
  markerZ: mod.MARKER_Z,
  markerAnchor: mod.MARKER_ANCHOR,
  countdown: {
    anchor: mod.COUNTDOWN_ANCHOR,
    z: mod.COUNTDOWN_Z,
    color: mod.COUNTDOWN_COLOR,
    unavailableColor: mod.COUNTDOWN_UNAVAILABLE_COLOR,
    unavailableText: mod.COUNTDOWN_UNAVAILABLE_TEXT,
  },
  overlayNames: mod.OVERLAY_NAMES,
  envelope: req.envelope ? mod.validateEnvelope(req.envelope) : null,
  envelopes: (req.envelopes || []).map(function (env) {
    return mod.validateEnvelope(env);
  }),
  vixLabels: (req.vixLevels || []).map(function (level) {
    return mod.vixLabel(level.sigma, level.price);
  }),
  countdownText: ("countdownState" in req)
    ? mod.countdownText(req.countdownState) : null,
  countdownColor: ("countdownState" in req)
    ? mod.countdownColor(req.countdownState) : null,
  markerSpecs: (req.markerItems || []).map(function (item) {
    return mod.markerSpec(item);
  }),
};

if (req.selftest) {
  const attached = [];
  const series = {
    attachPrimitive: function (primitive) { attached.push(primitive); },
    priceToCoordinate: function () { return null; },
  };
  const chart = {
    timeScale: function () {
      return { timeToCoordinate: function () { return null; } };
    },
  };
  mod.bind(chart, series);
  out.results = req.envelopes.map(function (env) {
    return mod.applyOverlayOps(env);
  });
  out.plan = mod.snapshot().plan;
  out.planCounts = {
    regions: out.plan.regions.length,
    bands: out.plan.bands.length,
    hlines: out.plan.hlines.length,
    segments: out.plan.segments.length,
    points: out.plan.points.length,
    markers: out.plan.markers.length,
  };
  out.countdownTextNow = out.plan.countdownText;
  out.attached = attached.length;
  if (req.replay && req.envelopes.length) {
    const last = req.envelopes[req.envelopes.length - 1];
    const before = JSON.stringify(mod.snapshot());
    mod.applyOverlayOps(last);
    mod.applyOverlayOps(last);
    out.replaySame = JSON.stringify(mod.snapshot()) === before;
  }
  if (req.clearLast) {
    const cleared = mod.applyOverlayOps(req.clearLast);
    out.clearResult = cleared;
    out.clearedPlan = mod.snapshot().plan;
  }
}

process.stdout.write(JSON.stringify(out));
"""


def _run_node(payload: dict) -> dict:
    """Run ``overlays.js`` under node and return its JSON answer."""
    if _NODE is None:  # pragma: no cover — the wave's test command needs node
        pytest.fail("node is required for the overlay-parity suites")
    data = dict(payload)
    data["module"] = str(OVERLAYS_JS)
    proc = subprocess.run(
        [_NODE, "-e", _NODE_SCRIPT],
        input=json.dumps(data), capture_output=True, text=True,
        cwd=str(REPO), timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def _all_envelopes(view):
    return view.overlay_envelopes + view.marker_envelopes


# ── T11 · overlay + marker parity (AC1) ─────────────────────────────────────


class TestOverlayParity:
    def test_P6_T10_T11_constants_match_the_reference_renderers(self, qapp):
        decoded = _run_node({})
        assert decoded["colors"] == {"pre": SO.ORANGE, "post": SO.BLUE}
        assert decoded["sessionAlpha"] == 0.10
        assert decoded["sessionZ"] == -10
        assert decoded["gap"] == {
            "up": {"color": GO.UP_COLOR, "brush": GO.UP_BRUSH},
            "down": {"color": GO.DOWN_COLOR, "brush": GO.DOWN_BRUSH},
            "openAlpha": 0.55,
            "filledAlpha": 0.32,
            "borderWidth": 0.8,
            "z": -5,
        }
        assert decoded["vix"]["labelAnchor"] == "right"
        assert decoded["vix"]["z"] == 0
        assert decoded["ict"]["structure"] == {
            "width": 1.2, "lineStyle": "dashed", "z": 3}
        assert decoded["ict"]["orderBlock"] == {"alpha": 0.18, "z": -3}
        assert decoded["ict"]["fvg"] == {
            "alpha": 0.14, "mitigatedAlpha": 0.06, "z": -4}
        assert decoded["ict"]["killzone"] == {"z": -8}
        assert decoded["event"] == EO.EVENT_STYLE
        assert decoded["markerZ"] == 10
        assert decoded["markerAnchor"] == [0.5, 1.0]
        assert decoded["countdown"]["anchor"] == [0.0, 0.0]
        assert decoded["countdown"]["z"] == 10
        assert decoded["countdown"]["color"] == "#e5e7eb"
        assert decoded["countdown"]["unavailableColor"] == "#f87171"
        assert (decoded["countdown"]["unavailableText"]
                == "Event data unavailable")
        assert decoded["overlayNames"] == list(LV.OVERLAY_NAMES)

        # The Python mirror carries the same reference constants.
        assert LV.SESSION_COLORS == {"pre": SO.ORANGE, "post": SO.BLUE}
        assert (LV.SESSION_ALPHA, LV.SESSION_Z) == (0.10, -10)
        assert LV.GAP_UP_COLOR == GO.UP_COLOR
        assert LV.GAP_UP_BRUSH == GO.UP_BRUSH
        assert LV.GAP_DOWN_COLOR == GO.DOWN_COLOR
        assert LV.GAP_DOWN_BRUSH == GO.DOWN_BRUSH
        assert (LV.GAP_OPEN_ALPHA, LV.GAP_FILLED_ALPHA,
                LV.GAP_BORDER_WIDTH, LV.GAP_Z) == (0.55, 0.32, 0.8, -5)
        assert LV.ICT_STRUCTURE_WIDTH == 1.2
        assert LV.ICT_ORDER_BLOCK_ALPHA == 0.18
        assert LV.ICT_FVG_ALPHA == 0.14
        assert LV.ICT_FVG_MITIGATED_ALPHA == 0.06
        assert LV.ICT_POOL_ALPHA == 0.07
        assert LV.ICT_VOLUME_IMBALANCE_ALPHA == 0.35
        assert LV.ICT_VOLUME_IMBALANCE_COLOR == IO.VI_COLOR
        assert LV.ICT_OPENING_GAP_ALPHA == 0.10
        assert LV.ICT_KILLZONE_Z == -8
        assert LV.EVENT_MARKERS == EO.EVENT_STYLE
        assert (LV.MARKER_Z, LV.MARKER_ANCHOR) == (10, (0.5, 1.0))

    def test_P6_T10_T11_session_bands_match_the_reference_overlay(self, qapp):
        view = _view()
        shapes, labels = _describe_reference_items(_reference_session(view))
        regions = _lwc_shapes(view, "session")

        assert labels == []
        assert len(regions) == len(shapes) > 0
        assert [row["kind"] for row in regions] == ["pre", "post", "pre", "post"]
        for region, reference in zip(regions, shapes):
            assert region["shape"] == "region" == reference["shape"]
            assert region["from"] == pytest.approx(reference["from"], abs=1e-6)
            assert region["to"] == pytest.approx(reference["to"], abs=1e-6)
            assert region["color"] == reference["color"]
            assert region["alpha"] == pytest.approx(reference["alpha"], abs=1e-6)
            assert region["z"] == reference["z"] == -10

    def test_P6_T10_T11_session_bands_follow_the_reference_gating(self, qapp):
        # No extended hours -> no bands (ChartPanel._render_sessions).
        no_ext = _view(ext_hours=False)
        assert no_ext.overlays["session"] == []

        # 1 day -> the service returns no bands.
        daily = LV.LwcChartView(tz_offset=TZ_OFFSET)
        daily.set_symbol(SYMBOL)
        daily.set_timeframe("1 day")
        daily.set_series("candles", _bars())
        assert daily.overlays["session"] == []
        # Nothing was ever drawn on this axis, so there is nothing to clear:
        # the empty state is recorded without traffic.
        assert daily.overlay_ops == []

    def test_P6_T10_T11_gap_staircase_matches_the_reference_overlay(self, qapp):
        view = _view()
        shapes, _labels = _describe_reference_items(_reference_gaps(view))
        bands = _lwc_shapes(view, "rth_gaps")

        assert bands, "the fixture must contain an RTH gap"
        assert len(bands) == len(shapes)
        for band, reference in zip(bands, shapes):
            assert reference["shape"] == "band"
            assert band["from"] == pytest.approx(reference["from"], abs=1e-6)
            assert band["to"] == pytest.approx(reference["to"], abs=1e-6)
            assert band["bottom"] == pytest.approx(reference["bottom"])
            assert band["top"] == pytest.approx(reference["top"])
            assert band["color"] == reference["color"]
            assert band["brush"] == reference["fill"]
            assert band["alpha"] == pytest.approx(reference["alpha"])
            assert band["borderWidth"] == pytest.approx(
                reference["borderWidth"])
            assert band["borderStyle"] == reference["borderStyle"]
            assert band["z"] == reference["z"] == -5

    def test_P6_T10_T11_vix_levels_match_the_reference_overlay(self, qapp):
        view = _view()
        overlay, result = _reference_vix(view)
        shapes, labels = _describe_reference_items(overlay)
        rows = _lwc_shapes(view, "vix_sd")

        lines = [row for row in shapes if row["shape"] == "hline"]
        assert len(rows) == len(lines) == len(result["levels"])
        assert len(labels) == len(rows)
        for row, reference, label in zip(rows, lines, labels):
            assert row["shape"] == "hline"
            assert row["price"] == pytest.approx(reference["price"])
            assert row["color"] == reference["color"]
            assert row["width"] == pytest.approx(reference["width"])
            assert row["lineStyle"] == reference["style"]
            assert row["z"] == reference["z"] == 0
            # The label is composed engine-side from sigma + price.
            assert LV.vix_label(row["sigma"], row["price"]) == label["text"]
            assert _display_of_frac(view, row["labelFrom"]) == pytest.approx(
                label["x"], abs=1e-6)
            assert row["labelAnchor"] == "right"

        # The JS composer produces the same strings from the same numbers.
        decoded = _run_node({"vixLevels": [
            {"sigma": row["sigma"], "price": row["price"]} for row in rows]})
        assert decoded["vixLabels"] == [label["text"] for label in labels]

    def test_P6_T10_T11_ict_concepts_match_the_reference_overlay(self, qapp):
        view = _view()
        overlay, _result, _window = _reference_ict(view)
        shapes, labels = _describe_reference_items(overlay)
        rows = _lwc_shapes(view, "ict")

        assert rows, "the fixture must produce ICT concepts"
        shapes = [row for row in shapes if row["shape"] != "segment"
                  or row.get("color") is not None]
        assert len(rows) == len(shapes), (rows, shapes)
        for row, reference in zip(rows, shapes):
            assert row["shape"] == reference["shape"]
            assert row["from"] == pytest.approx(reference["from"], abs=1e-6)
            assert row["to"] == pytest.approx(reference["to"], abs=1e-6)
            if row["shape"] in ("band", "region"):
                assert row.get("alpha", 1.0) == pytest.approx(
                    reference["alpha"])
                assert row["color"] == reference["color"]
                assert row["z"] == reference["z"]
            elif row["shape"] == "segment":
                assert row["price"] == pytest.approx(reference["price"])
                assert row["color"] == reference["color"]
                assert row["width"] == pytest.approx(reference["width"])
                assert row["lineStyle"] == reference["style"]
                assert row["z"] == reference["z"]
            else:  # point
                assert row["price"] == pytest.approx(reference["price"])
                assert row["color"] == reference["color"]
                assert row["size"] == pytest.approx(reference["size"])
                assert row["direction"] == (
                    "up" if reference["symbol"] == "t" else "down")
                assert row["z"] == reference["z"]

        # Segments that carry a reference label carry the same text.
        lwc_labels = [row.get("label") for row in rows
                      if row["shape"] == "segment" and row.get("label")]
        assert lwc_labels == [label["text"] for label in labels]

    def test_P6_T10_T11_event_markers_match_the_reference_overlay(self, qapp):
        view = _view()
        today = date.today()
        events = [
            EO_Event("ev-earn", "earnings", today - timedelta(days=1),
                     {"estimate": 1.25, "reported": 1.31}),
            EO_Event("ev-div", "dividend", today - timedelta(days=2),
                     {"amount": 0.25}),
            EO_Event("ev-split", "split", today + timedelta(days=3),
                     {"ratio": "4:1"}),
        ]
        reference = EO.EventMarkerOverlay(_MarkerPlot())
        reference.set_bars(list(view.plotted_bars))
        reference.set_collapse_map(_axis(view)[2])
        reference.set_events(events)
        view.set_event_markers(events)

        assert len(view.event_markers) == len(events)
        for item in view.event_markers:
            ref_item = reference._items[item["id"]]
            style = EO.EVENT_STYLE[item["type"]]
            spec = _run_node({"markerItems": [item]})["markerSpecs"][0]
            assert spec["glyph"] == style["glyph"]
            assert spec["color"] == style["color"]
            assert spec["label"] == style["label"]
            assert spec["z"] == ref_item.zValue() == 10
            assert spec["anchor"] == [0.5, 1.0]
            assert _display_of_frac(view, item["x"]) == pytest.approx(
                float(ref_item.pos().x()), abs=1e-6)
            assert float(ref_item.pos().y()) == pytest.approx(100.0)
            assert spec["tooltip"] == ref_item.toolTip()

        # Countdown: the next upcoming event, in the reference wording.
        assert reference.countdown_text() == "Split in 3d"
        decoded = _run_node({"countdownState": view.countdown})
        assert decoded["countdownText"] == reference.countdown_text()
        assert decoded["countdownColor"] == EO.EVENT_STYLE["split"]["color"]

    def test_P6_T10_T11_markers_diff_by_id_and_future_sits_past_last(self,
                                                                    qapp):
        view = _view()
        # The fixture's axes are 2026-09-24/25, so an in-window date moves the
        # marker when it is corrected (a future-only pair would both land on
        # the single "past the last bar" slot and never move).
        first = EO_Event("ev-x", "earnings", date(2026, 9, 24), {})
        view.set_event_markers([first])
        x_first = view.event_markers[0]["x"]
        assert len(view.event_markers) == 1

        # A date correction moves the marker instead of duplicating it.
        corrected = EO_Event("ev-x", "earnings", date(2026, 9, 25), {})
        view.set_event_markers([corrected])
        assert len(view.event_markers) == 1
        x_moved = view.event_markers[0]["x"]
        assert x_moved > x_first

        # A future event sits one display-x step past the last bar — the
        # reference rule is "+1.0 in the axis' own unit", not one bar width.
        future = EO_Event("ev-f", "split", date.today() + timedelta(days=5), {})
        view.set_event_markers([future])
        x_future = view.event_markers[0]["x"]
        last_display = _display_of_ts(view, int(view.plotted_bars[-1].ts))
        assert _display_of_frac(view, x_future) == pytest.approx(
            last_display + 1.0)
        assert _display_of_frac(view, x_future) < last_display + 15 * 60

    def test_P6_T10_T11_unavailable_state_and_empty_set(self, qapp):
        view = _view()
        view.set_event_markers([], unavailable=True)
        assert view.countdown == {"kind": "unavailable"}
        decoded = _run_node({"countdownState": view.countdown})
        assert decoded["countdownText"] == "Event data unavailable"
        assert decoded["countdownColor"] == LV.COUNTDOWN_UNAVAILABLE_COLOR

        view.set_event_markers([])
        assert view.countdown is None
        assert view.event_markers == []
        assert view.marker_ops[-1] == {
            "op": "clear_markers", "series": "markers"}

    def test_P6_T10_T11_identical_state_republishes_identical_values(self,
                                                                     qapp):
        first = _view()
        today = date.today()
        events = [EO_Event("ev-1", "dividend", today, {"amount": 0.5})]
        first.set_event_markers(events)

        second = _view()
        second.set_event_markers(events)

        assert first.overlays == second.overlays
        assert first.overlay_ops == second.overlay_ops
        assert first.overlay_envelopes == second.overlay_envelopes
        assert first.event_markers == second.event_markers
        assert first.marker_ops == second.marker_ops

    def test_P6_T10_T11_envelopes_validate_replay_and_clear(self, qapp):
        view = _view()
        events = [EO_Event("ev-1", "earnings", date.today(), {"estimate": 2.0})]
        view.set_event_markers(events)
        envelopes = _all_envelopes(view)
        assert envelopes

        decoded = _run_node({"envelopes": envelopes, "selftest": True,
                             "replay": True})
        assert all(check["ok"] for check in decoded["envelopes"]), decoded
        assert decoded["replaySame"] is True
        assert decoded["attached"] == 1
        counts = decoded["planCounts"]
        assert counts["regions"] == len(view.overlays["session"])
        assert counts["bands"] == len(view.overlays["rth_gaps"]) + len(
            [row for row in view.overlays["ict"] if row["shape"] == "band"])
        assert counts["hlines"] == len(view.overlays["vix_sd"])
        assert counts["markers"] == 1
        assert decoded["countdownTextNow"] == "Earnings today"

        # Clearing republishes clear ops and empties the engine.
        view.set_series("candles", [])
        assert view.overlays["session"] == []
        # The reference hides a marker it cannot place once the axis is empty
        # (the item stays, invisible); the wire mirrors that as visible=False
        # and the engine draws nothing.
        assert view.event_markers
        assert all(item["visible"] is False for item in view.event_markers)
        cleared = _run_node({
            "envelopes": _all_envelopes(view)[-1:], "selftest": True})
        assert cleared["plan"]["regions"] == []
        assert cleared["plan"]["bands"] == []
        assert cleared["plan"]["hlines"] == []
        assert cleared["plan"]["markers"] == []

    def test_P6_T10_T11_parity_rows_6_9_10_move_to_done(self):
        text = MATRIX.read_text(encoding="utf-8")
        for row_id in ("6", "9", "10"):
            rows = [line for line in text.splitlines()
                    if line.startswith(f"| {row_id} |")]
            assert len(rows) == 1, rows
            assert "P6-10" in rows[0]
            assert rows[0].rstrip().endswith("Done / accepted |"), rows[0]
        for row in text.splitlines():
            if row.startswith("|") and "Done / accepted" in row:
                assert "Open / pending" not in row
        assert "overlays.js" in text, "the wave note names the JS module"


class EO_Event:
    """The D38 event record shape (``data.events.provider.Event`` fields)."""

    def __init__(self, event_id, etype, event_date, details=None):
        self.id = event_id
        self.type = etype
        self.symbol = SYMBOL
        self.date = event_date
        self.source = "ibkr"
        self.details = dict(details or {})


# ── T12 · residue scan (AC2, renderer-only boundary) ────────────────────────


class TestRendererBoundary:
    SOURCES = ["ui/lwc_view.py", "chart_assets/lwc/overlays.js"]

    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings", "BarCache", "get_bars", "save_bars",
        "placeOrder", "cancelOrder", "UserOrder", "OrderRateLimiter",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdn.", "http://", "https://",
        "AlarmStore", "DrawingStore", "EventProvider", "yfinance",
        "QWebChannel",
    ]

    def test_P6_T10_T12_no_out_of_scope_surface(self):
        hits = []
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                if token in src:
                    hits.append(f"{rel}: {token!r}")
        assert hits == [], f"out-of-scope residue: {hits}"

    def test_P6_T10_T12_view_imports_stay_renderer_only(self):
        tree = ast.parse((REPO / "ui/lwc_view.py").read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module or "")
        forbidden = {
            "ibkr", "data.db", "data.bar_cache", "data.alarm_store",
            "data.drawing_store", "data.events.provider",
            "ui.chart_panel", "ui.event_marker_overlay", "ui.overlays",
            "ui.alarm_overlay", "PyQt6.QtNetwork",
            "requests", "urllib", "urllib.request",
        }
        assert not {name for name in names
                    if name in forbidden or name.startswith("ibkr.")}

    def test_P6_T10_T12_overlays_services_and_provider_are_untouched(self):
        tokens = ("set_overlay", "set_event_markers", "overlayOpsEmitted",
                  "markerOpsEmitted", "LwcChartView", "overlays.js", "lwc")
        for rel in ("ui/overlays/session_overlay.py",
                    "ui/overlays/gap_overlay.py",
                    "ui/overlays/vix_overlay.py",
                    "ui/overlays/ict_overlay.py",
                    "ui/event_marker_overlay.py",
                    "services/session_service.py",
                    "services/gap_vix_service.py",
                    "services/ict_service.py",
                    "data/events/provider.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            hits = [token for token in tokens if token in src]
            assert hits == [], f"{rel} picked up LWC vocabulary: {hits}"

    def test_P6_T10_T12_ops_carry_no_timestamp_and_no_formatted_string(self,
                                                                       qapp):
        view = _view()
        view.set_event_markers(
            [EO_Event("ev-1", "dividend", date.today(), {"amount": 0.1})])
        assert view.overlay_ops and view.marker_ops
        for op in view.overlay_ops + view.marker_ops:
            json.dumps(op)  # primitives only, no objects
            assert op["series"] in {"overlays", "markers"}
            for region in op.get("regions", []):
                keys = set(region)
                assert "ts" not in keys and "timestamp" not in keys
                for time_key in ("from", "to"):
                    if time_key not in region:
                        continue  # a full-width hline carries no x extent
                    assert isinstance(region[time_key], float)
                    assert abs(region[time_key]) <= len(view.plotted_bars) + 1
                # Labels are composed engine-side: no text on a region except
                # the service's own concept name (a display string, not a
                # formatted price/time value).
                assert "labelFull" not in keys and "labelShort" not in keys
            for item in op.get("items", []):
                if item["x"] is not None:
                    assert isinstance(item["x"], float)
                    assert abs(item["x"]) <= len(view.plotted_bars) + 1

    def test_P6_T10_T12_overlays_never_ride_the_bar_transport(self, qapp):
        view = _view()
        view.set_event_markers(
            [EO_Event("ev-1", "split", date.today(), {})])
        log = view.bridge.replay_log()
        assert log, "the bar transport carries the candles/volume ops"
        assert all(op["series"] in {"candles", "volume"} for op in log)
        assert all(op["series"] == "overlays" for op in view.overlay_ops)
        assert all(op["series"] == "markers" for op in view.marker_ops)
