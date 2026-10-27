"""tests/test_lwc_alarms.py — P6-T08 Phase 6 alarm lines/overlays (M).

The alarm-parity cases: identical alarm state must render identically on both
engines. The reference is the shipped ``ui/alarm_overlay.py`` — its own colour
precedence and label composition are driven with a fake plot and compared,
value for value, against what ``chart_assets/lwc/alarms.js`` produces from the
wire columns. The preview line is compared against ``ui/chart_panel.py``'s
D21.10 reference. The residue scan closes the renderer-only boundary: no
``ibkr/``, store, service, order or persistence surface, no alarm data on the
bar transport, and the Qt alarm dialogs/overlays untouched.

QApplication usage: the view is a ``QWidget`` and the reference overlay builds
graphics items, so the render cases take the repo's session-scoped ``qapp``
fixture (a locally created application gets collected and aborts the process
at the next widget construction).
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from data.models import Alarm
from ui import alarm_overlay as AO
from ui import lwc_view as LV
from ui.chart_panel import ALARM_PREVIEW_COLOR
from ui.chart_mouse_router import RouterMode

REPO = Path(__file__).resolve().parent.parent
ALARMS_JS = REPO / "chart_assets" / "lwc" / "alarms.js"
MATRIX = REPO / "docs" / "lwc_parity_matrix.md"

_NODE = shutil.which("node")

SYMBOL = "LWC-ALARM"

#: The five visual states, named as the wave describes them. ``rearmed`` is
#: an alarm that fired and was re-armed: triggered=False, active=True — the
#: same visual as ``armed``, which this fixture pins (a regression that left
#: the (hit) suffix or the red colour behind would fail).
STATES = ("armed", "triggered", "rearmed", "muted", "inactive")


def _alarm(alarm_id, price, direction="cross_above", **kw):
    return Alarm(id=alarm_id, symbol=SYMBOL, price=price, direction=direction,
                 **kw)


def _state_alarms():
    """One alarm per visual state, in ``STATES`` order."""
    return [
        _alarm(1, 101.25),
        _alarm(2, 99.5, "cross_below", triggered=True, triggered_at=1790000000),
        _alarm(3, 103.0, "cross_either", note="trim half"),
        _alarm(4, 97.75, "cross_above", sound=False),
        _alarm(5, 105.0, "cross_above", active=False),
    ]


def _alarms():
    """The state fixture plus the two records that must draw no line.

    ``id is None`` is an unsaved alarm; ``kind="volume_burst"`` has no price
    level (D39). The reference overlay skips both, so the LWC engine must too.
    """
    return _state_alarms() + [
        _alarm(None, 100.0),
        _alarm(6, 0.0, kind="volume_burst"),
    ]


# ── reference (default engine) ───────────────────────────────────────────────


class _FakePlot:
    """Just enough PlotWidget for ``AlarmOverlay``'s item bookkeeping."""

    def __init__(self):
        self.items = []

    def getViewBox(self):  # noqa: N802 — pyqtgraph's own name
        return None

    def addItem(self, item):  # noqa: N802
        self.items.append(item)

    def removeItem(self, item):  # noqa: N802
        if item in self.items:
            self.items.remove(item)


def _reference_items(alarms):
    """What ``AlarmOverlay`` actually draws, keyed by alarm id."""
    overlay = AO.AlarmOverlay(_FakePlot())
    overlay.set_data(alarms)
    expected = [alarm.id for alarm in alarms if alarm.id is not None
                and getattr(alarm, "kind", "price") == "price"]
    assert sorted(overlay._items) == expected
    out = {}
    for alarm_id, (line, label) in overlay._items.items():
        text_item = getattr(label, "textItem", label)
        out[alarm_id] = {
            "price": float(line.value()),
            "color": line.pen.color().name(),
            "pen_width": float(line.pen.widthF()),
            "text": text_item.toPlainText(),
            "label_price": float(label.pos().y()),
            "label_x": float(label.pos().x()),
            "line_z": float(line.zValue()),
            "label_z": float(label.zValue()),
        }
    return out


# ── JS harness ───────────────────────────────────────────────────────────────


_NODE_SCRIPT = r"""
const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8"));
const mod = require(req.module);

const out = {
  colors: mod.ALARM_COLORS,
  previewColor: mod.PREVIEW_COLOR,
  lineWidth: mod.LINE_WIDTH_PX,
  z: { line: mod.ALARM_LINE_Z, label: mod.ALARM_LABEL_Z,
       preview: mod.PREVIEW_LINE_Z },
  labelAnchor: mod.LABEL_ANCHOR,
  specs: (req.alarms || []).map(function (alarm) { return mod.lineSpec(alarm); }),
  check: req.envelope ? mod.validateEnvelope(req.envelope) : null,
};

if (req.selftest) {
  const created = [];
  const removed = [];
  let open = [];
  const series = {
    createPriceLine: function (opts) {
      created.push(opts);
      const handle = { opts: opts };
      open.push(handle);
      return handle;
    },
    removePriceLine: function (handle) {
      removed.push(handle);
      const at = open.indexOf(handle);
      if (at >= 0) open.splice(at, 1);
    },
  };
  mod.bind({ applyOptions: function () {} }, series);
  out.results = req.envelopes.map(function (env) {
    const result = mod.applyAlarmOps(env);
    result.openLines = open.length;
    return result;
  });
  out.snapshot = mod.snapshot();
  out.created = created;
  out.removedCount = removed.length;
  out.openLines = open.length;
  if (req.replay && req.envelopes.length) {
    const last = req.envelopes[req.envelopes.length - 1];
    const before = JSON.stringify(mod.snapshot());
    mod.applyAlarmOps(last);
    mod.applyAlarmOps(last);
    out.replaySame = JSON.stringify(mod.snapshot()) === before;
    out.openLinesAfterReplay = open.length;
  }
}

process.stdout.write(JSON.stringify(out));
"""


def _run_node(payload: dict) -> dict:
    """Run ``alarms.js`` under node and return its JSON answer."""
    if _NODE is None:  # pragma: no cover — the wave's test command needs node
        pytest.fail("node is required for the alarm-parity suites")
    data = dict(payload)
    data["module"] = str(ALARMS_JS)
    proc = subprocess.run(
        [_NODE, "-e", _NODE_SCRIPT],
        input=json.dumps(data), capture_output=True, text=True,
        cwd=str(REPO), timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def _wire(alarm):
    """The raw alarm row the engine sees (columns converted to JSON)."""
    return {
        "id": alarm.id,
        "price": alarm.price,
        "direction": alarm.direction,
        "active": alarm.active,
        "triggered": alarm.triggered,
        "sound": alarm.sound,
        "note": alarm.note,
    }


def _view(alarms=None, editable=True):
    view = LV.LwcChartView(tz_offset=14400, editable=editable)
    view.set_symbol(SYMBOL)
    view.set_timeframe("5 mins")
    view.set_alarm_lines(_alarms() if alarms is None else alarms)
    return view


def _alarm_envelopes(view):
    return [env for env in view.alarm_envelopes]


# ── T11 · alarm parity (AC1) ────────────────────────────────────────────────


class TestAlarmParity:
    def test_P6_T08_T11_constants_match_the_reference_overlay(self):
        assert LV.ALARM_TRIGGERED_COLOR == AO.TRIGGERED_COLOR
        assert LV.ALARM_ARMED_COLOR == AO.ARMED_COLOR
        assert LV.ALARM_MUTED_COLOR == AO.MUTED_COLOR
        assert LV.ALARM_INACTIVE_COLOR == AO.INACTIVE_COLOR
        assert LV.ALARM_DIRECTION_GLYPH == AO.DIRECTION_GLYPH
        assert LV.ALARM_PREVIEW_COLOR == ALARM_PREVIEW_COLOR
        assert (LV.ALARM_LINE_WIDTH, LV.ALARM_LINE_Z, LV.ALARM_LABEL_Z,
                LV.ALARM_PREVIEW_Z) == (1.4, 6, 7, 5)

        decoded = _run_node({"alarms": [_wire(alarm) for alarm in _alarms()]})
        assert decoded["colors"] == {
            "triggered": AO.TRIGGERED_COLOR,
            "armed": AO.ARMED_COLOR,
            "muted": AO.MUTED_COLOR,
            "inactive": AO.INACTIVE_COLOR,
        }
        assert decoded["previewColor"] == ALARM_PREVIEW_COLOR
        assert decoded["lineWidth"] == LV.ALARM_LINE_WIDTH
        assert decoded["z"] == {
            "line": LV.ALARM_LINE_Z, "label": LV.ALARM_LABEL_Z,
            "preview": LV.ALARM_PREVIEW_Z,
        }
        assert decoded["labelAnchor"] == "right"

    def test_P6_T08_T11_color_and_label_match_all_five_states(self, qapp):
        alarms = _state_alarms()
        reference = _reference_items(alarms)
        colors = {alarm.id: LV.alarm_color(alarm) for alarm in alarms}
        labels = {alarm.id: LV.alarm_label(alarm) for alarm in alarms}

        # The Python mirror agrees with the shipped overlay's own functions.
        for alarm in alarms:
            assert LV.alarm_color(alarm) == AO.AlarmOverlay._color_for(None, alarm)
            assert LV.alarm_label(alarm) == AO.AlarmOverlay._label_text(None, alarm)

        decoded = _run_node({"alarms": [_wire(alarm) for alarm in alarms]})
        specs = {spec["id"]: spec for spec in decoded["specs"]}
        assert list(specs) == [alarm.id for alarm in alarms]
        assert set(colors.values()) == {
            AO.ARMED_COLOR, AO.TRIGGERED_COLOR, AO.MUTED_COLOR,
            AO.INACTIVE_COLOR,
        }
        for alarm in alarms:
            spec = specs[alarm.id]
            ref = reference[alarm.id]
            assert spec["color"] == ref["color"] == colors[alarm.id]
            assert spec["title"] == ref["text"] == labels[alarm.id]
            assert spec["price"] == ref["price"] == alarm.price
            assert spec["price"] == ref["label_price"]
            assert spec["width"] == ref["pen_width"] == 1.4
            assert spec["z"] == ref["line_z"] == 6
            assert spec["labelZ"] == ref["label_z"] == 7
            assert spec["labelAnchor"] == "right"

        # Re-armed looks exactly like armed: no (hit) suffix, amber again.
        armed = specs[1]
        rearmed = specs[3]
        assert rearmed["color"] == armed["color"] == AO.ARMED_COLOR
        assert "(hit)" not in rearmed["title"]
        assert rearmed["title"].endswith("103.0000 \u00b7 trim half")
        assert specs[2]["title"].endswith("(hit)")
        assert specs[4]["title"].endswith("(muted)")
        assert specs[5]["title"].endswith("(off)")

    def test_P6_T08_T11_only_price_alarms_with_ids_draw(self, qapp):
        view = _view()
        cols = view.alarm_ops[0]["cols"]
        assert cols["id"] == [1, 2, 3, 4, 5]
        assert 6 not in cols["id"], "volume_burst has no price level (D39)"
        assert None not in cols["id"], "an unsaved alarm has no line yet"
        assert [alarm.id for alarm in view.alarms] == [1, 2, 3, 4, 5]

    def test_P6_T08_T11_engine_lines_match_the_reference_items(self, qapp):
        view = _view()
        reference = _reference_items(_alarms())
        envelopes = _alarm_envelopes(view)
        decoded = _run_node({"envelope": envelopes[0], "envelopes": envelopes,
                             "selftest": True})

        assert decoded["check"]["ok"] is True, decoded["check"]
        assert all(result["error"] is None for result in decoded["results"])
        assert decoded["results"][0]["applied"] == 1
        assert decoded["openLines"] == 5

        lines = decoded["snapshot"]["lines"]
        assert [line["id"] for line in lines] == [1, 2, 3, 4, 5]
        for line in lines:
            ref = reference[line["id"]]
            assert line["color"] == ref["color"]
            assert line["title"] == ref["text"]
            assert line["price"] == ref["price"]

        # The library call carries the same values. LWC price lines accept an
        # integer width only (1..4): the reference 1.4 crosses unchanged in
        # the spec and the call takes the nearest supported width.
        assert len(decoded["created"]) == 5
        for opts, line in zip(decoded["created"], lines):
            assert opts["price"] == line["price"]
            assert opts["color"] == line["color"]
            assert opts["title"] == line["title"]
            assert opts["axisLabelVisible"] is True
            assert opts["lineWidth"] == 1  # nearest integer to 1.4
            assert opts["lineStyle"] == 0  # solid, as the default pen

    def test_P6_T08_T11_replay_is_idempotent_and_empty_clears(self, qapp):
        view = _view()
        envs = _alarm_envelopes(view)
        decoded = _run_node({"envelopes": envs, "selftest": True,
                             "replay": True})
        assert decoded["replaySame"] is True
        assert decoded["openLinesAfterReplay"] == 5

        view.set_alarm_lines([])
        assert view.alarm_ops[-1] == LV.clear_alarms_op()
        assert view.alarms == []
        cleared = _run_node({"envelopes": _alarm_envelopes(view),
                             "selftest": True})
        assert cleared["results"][-1]["applied"] == 1
        assert cleared["snapshot"]["lines"] == []
        assert cleared["openLines"] == 0
        assert cleared["removedCount"] == 5

    def test_P6_T08_T11_identical_state_republishes_identical_values(self, qapp):
        first = _view()
        second = LV.LwcChartView(tz_offset=14400, editable=True)
        second.set_symbol(SYMBOL)
        second.set_alarm_lines(_alarms())
        assert first.alarm_ops == second.alarm_ops
        assert first.alarm_envelopes == second.alarm_envelopes

    # ── preview line (D21.10) ──────────────────────────────────────────

    def test_P6_T08_T11_preview_line_matches_the_panel(self, qapp):
        view = _view()
        assert view.alarm_preview_price is None

        view.show_alarm_preview(101.5)
        assert view.alarm_preview_price == 101.5
        assert view.alarm_ops[-1] == {
            "op": "set_alarm_preview", "series": "alarms", "price": 101.5}
        view.update_alarm_preview(102.25)
        assert view.alarm_preview_price == 102.25

        decoded = _run_node({"envelopes": _alarm_envelopes(view)[-2:],
                             "selftest": True})
        preview = decoded["snapshot"]["preview"]
        assert preview["price"] == 102.25
        assert preview["color"] == ALARM_PREVIEW_COLOR
        assert preview["width"] == 1.4
        assert preview["lineStyle"] == "dashed"
        assert preview["z"] == 5 and preview["z"] < LV.ALARM_LINE_Z
        assert preview["axisLabelVisible"] is False
        # Dashed in the library call; still below the alarm lines.
        opts = decoded["created"][-1]
        assert opts["lineStyle"] == 2
        assert opts["color"] == ALARM_PREVIEW_COLOR

        count = len(view.alarm_envelopes)
        view.update_alarm_preview(99.0)  # live move, still one line
        assert len(view.alarm_envelopes) == count + 1
        view.hide_alarm_preview()
        assert view.alarm_preview_price is None
        assert view.alarm_ops[-1] == LV.clear_alarm_preview_op()
        hidden = len(view.alarm_envelopes)
        view.hide_alarm_preview()  # idempotent, like the panel
        assert len(view.alarm_envelopes) == hidden

        cleared = _run_node({"envelopes": _alarm_envelopes(view)[-1:],
                             "selftest": True})
        assert cleared["snapshot"]["preview"] is None

    def test_P6_T08_T11_preview_update_while_hidden_is_a_noop(self, qapp):
        view = _view()
        before = len(view.alarm_envelopes)
        view.update_alarm_preview(123.0)
        assert len(view.alarm_envelopes) == before
        assert view.alarm_preview_price is None

    # ── placement mode (the Qt dialogs stay) ───────────────────────────

    def test_P6_T08_T11_placement_mode_routes_through_the_frozen_router(self,
                                                                        qapp):
        view = _view()
        assert view.router.active_mode == RouterMode.IDLE

        assert view.set_alarm_mode(True) == "ALARM_PLACING"
        assert view.router.active_mode == RouterMode.ALARM_PLACING
        assert view.interaction_ops[-1] == {
            "op": "router_mode", "mode": "ALARM_PLACING",
            "intent": "enter_alarm_placing", "refused": False}

        # TR-9: the magnifier is still refused while placing.
        result = view.handle_control("magnifier", True)
        assert result["refused"] is True
        assert result["mode"] == "ALARM_PLACING"

        assert view.set_alarm_mode(False) == "IDLE"
        assert view.router.active_mode == RouterMode.IDLE
        assert view.interaction_ops[-1]["intent"] == "exit_to_idle"

    def test_P6_T08_T11_non_editable_view_never_arms_placement(self, qapp):
        view = _view(editable=False)
        before = len(view.interaction_envelopes)
        assert view.set_alarm_mode(True) == "IDLE"
        assert view.router.active_mode == RouterMode.IDLE
        assert len(view.interaction_envelopes) == before

    def test_P6_T08_T11_parity_row_12_moves_to_done(self):
        text = MATRIX.read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("| 12 |")]
        assert len(rows) == 1, rows
        assert "P6-08" in rows[0]
        assert rows[0].rstrip().endswith("Done / accepted |"), rows[0]
        assert "alarms.js" in text, "the wave note names the JS module"
        for row in text.splitlines():
            if row.startswith("|") and "Done / accepted" in row:
                assert "Open / pending" not in row


# ── T12 · residue scan (AC2, renderer-only boundary) ────────────────────────


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
    SOURCES = ["ui/lwc_view.py", "chart_assets/lwc/alarms.js"]

    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings", "AlarmStore", "alarm_store",
        "placeOrder", "cancelOrder", "UserOrder", "OrderRateLimiter",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdn.", "http://", "https://",
        "orders", "BarCache", "get_bars", "save_bars",
    ]

    def test_P6_T08_T12_no_out_of_scope_surface(self):
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

    def test_P6_T08_T12_view_imports_stay_renderer_only(self):
        tree = ast.parse((REPO / "ui/lwc_view.py").read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module or "")
        forbidden = {
            "ibkr", "data.db", "data.alarm_store", "data.models",
            "services.alarm_service", "services.sound_service",
            "ui.alarm_overlay", "PyQt6.QtNetwork", "requests", "urllib",
            "urllib.request",
        }
        assert not {name for name in names
                    if name in forbidden or name.startswith("ibkr.")}

    def test_P6_T08_T12_stores_overlays_and_dialogs_are_untouched(self):
        tokens = ("set_alarm_lines", "alarmOpsEmitted", "alarms.js",
                  "LwcChartView", "LWC", "lwc")
        for rel in ("data/alarm_store.py", "ui/alarm_overlay.py",
                    "ui/chart_panel.py"):
            src = (REPO / rel).read_text(encoding="utf-8")
            hits = [token for token in tokens if token in src]
            assert hits == [], f"{rel} picked up LWC vocabulary: {hits}"

    def test_P6_T08_T12_alarm_ops_carry_prices_and_state_only(self, qapp):
        view = _view()
        assert view.alarm_ops
        for op in view.alarm_ops:
            json.dumps(op)  # primitives only, no objects
            assert op["series"] == "alarms"
            if op["op"] == "set_alarms":
                assert set(op["cols"]) == set(LV.ALARM_COLS)
                assert set(LV.ALARM_BOOL_COLS) <= set(op["cols"])
                for name in LV.ALARM_BOOL_COLS:
                    assert all(isinstance(v, bool) for v in op["cols"][name])
                assert all(isinstance(t, int) for t in op["cols"]["id"])
                assert all(isinstance(p, (int, float))
                           for p in op["cols"]["price"])

    def test_P6_T08_T12_alarms_never_ride_the_bar_transport(self, qapp):
        from datetime import datetime, timezone

        from data.models import Bar

        bar = Bar(symbol=SYMBOL, timeframe="5 mins",
                  ts=int(datetime(2026, 9, 25, 13, 30,
                                  tzinfo=timezone.utc).timestamp()),
                  open=100.0, high=101.0, low=99.0, close=100.5, volume=10.0)
        view = _view()
        view.set_series("candles", [bar])
        log = view.bridge.replay_log()
        assert log, "the bar transport carries the candles/volume ops"
        assert all(op["series"] in {"candles", "volume"} for op in log)
        assert [op for op in log if op["series"] == "alarms"] == []
        # And the alarm channel carries no bar op.
        assert all(op["series"] == "alarms" for op in view.alarm_ops)
