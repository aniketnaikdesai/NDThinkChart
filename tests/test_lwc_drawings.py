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



# ── T11 · drawing parity (AC1) ──────────────────────────────────────────────


def _display(frac, xs, indices):
    return LV.display_from_fractional_index(frac, xs, indices)


class TestDrawingParity:

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





    def test_P6_T09_T11_body_drag_translates_the_whole_primitive(self, qapp):
        bars, ext, plotted, xs, indices = self._fixture_rows()
        drawing = _drawing("trendline", (plotted[2].ts, plotted[7].ts),
                           100.5, 102.25)

        view = _view(bars, ext)
        view.set_drawings([drawing])
        item = view.drawing_items[0]
        moved = LV.drag_drawing_item("trendline", item, -1, 1.0, -0.25,
                                     body=True)
        assert moved["points"][0][0] == pytest.approx(item["points"][0][0] + 1)
        assert moved["points"][1][0] == pytest.approx(item["points"][1][0] + 1)
        assert moved["points"][0][1] == pytest.approx(100.25)
        assert moved["points"][1][1] == pytest.approx(102.0)
        # The whole body moved one fractional index right and 0.25 down.
        assert _display(moved["points"][0][0], xs, indices) > _display(
            item["points"][0][0], xs, indices)
        assert _display(moved["points"][1][0], xs, indices) > _display(
            item["points"][1][0], xs, indices)

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
