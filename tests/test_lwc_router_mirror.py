"""tests/test_lwc_router_mirror.py — P6-07 / Phase 5 interaction gate (D47.7).

Gate evidence for the three P6-07 acceptance criteria:

* **P6-T07-T11 (AC1)** — every row of the frozen Python TR-1…TR-17 table
  (``ui/chart_mouse_router.py``) is driven on *both* engines: the real Python
  router (with recording fake overlays) and the JS mirror
  (``chart_assets/lwc/interaction.js``, loaded under node). The JS mirror's
  table must be row-for-row identical to the Python transcription and every
  resolution must end in the same mode with the same effects — including the
  ALARM_PLACING + magnifier refusal (TR-9) and the mid-drag symbol-change
  reset (TR-17).
* **P6-T07-T12 (AC2)** — the crosshair is the library-native crosshair + axis
  labels (Q63 / A108 owner-confirmed accept-drift): configured through
  ``chart.applyOptions({crosshair: …})`` with both ``labelVisible`` flags on,
  and no custom crosshair-label primitive anywhere in the app's
  ``chart_assets/`` tree. The zone / horizontal-line / alarm dialogs stay the
  same Qt dialogs — the LWC interaction surface constructs none of its own,
  and their suites ride the same test command.
* **P6-T07-T13 (AC3)** — renderer-only residue scan: ``ui/chart_mouse_router.py``
  is untouched (no LWC / mirror vocabulary in it) and the interaction diff
  carries no ``ibkr/`` / DB / store / service / watchlist / dock / order
  surface, and no network call.

Runs offscreen; the JS half needs ``node`` (the same binary the wave's
``node --test chart_assets/lwc/`` step uses).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ui import lwc_view as LV
from ui.chart_controls import ChartControls
from ui.chart_mouse_router import ChartMouseRouter
from ui.drawing_tools import DRAWING_TOOLS, TOOL_CURSOR

ROOT = Path(__file__).resolve().parents[1]
INTERACTION_JS = ROOT / "chart_assets" / "lwc" / "interaction.js"

_NODE = shutil.which("node")

#: First real drawing tool (a member of ``DRAWING_TOOLS`` that is not the
#: cursor) — the frozen router coerces anything else to the cursor, so the
#: harness takes it from the contract rather than hard-coding a name.
REAL_TOOL = next((tool for tool in DRAWING_TOOLS if tool != TOOL_CURSOR), None)

TRANSITION_IDS = [row["id"] for row in LV.ROUTER_TRANSITIONS]

#: The JS->node driver: load the mirror, seed a mode by replaying the seed
#: triggers through the mirror's own resolver, then answer every row.
_NODE_SCRIPT = r"""
const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8"));
const mod = require(req.module);

const SEEDS = {
  IDLE: [],
  DRAWING: ["draw_tool"],
  ZOOMING: ["enter_zoom"],
  ALARM_PLACING: ["enter_alarm_placing"],
};

function seedState(mode) {
  var state = mod.initialState();
  var seeds = SEEDS[mode];
  if (!seeds) throw new Error("unknown seed mode: " + mode);
  for (var i = 0; i < seeds.length; i++) {
    state = mod.resolveTransition(state, seeds[i]).state;
  }
  return state;
}

const out = {
  version: mod.INTERACTION_VERSION,
  modes: mod.ROUTER_MODES,
  triggers: mod.ROUTER_TRIGGERS,
  gestures: mod.ROUTER_GESTURES,
  transitions: mod.ROUTER_TRANSITIONS,
  controls: mod.CONTROL_BUTTONS,
  zoomFactors: mod.ZOOM_FACTORS,
  crosshairModeId: mod.CROSSHAIR_MODE_ID,
  crosshairModeName: mod.CROSSHAIR_MODE_NAME,
  crosshairOptions: mod.crosshairOptions(),
  focusModel: mod.FOCUS_MODEL,
  functions: [
    "initialState", "resolveTransition", "routeGesture", "controlFor",
    "zoomBy", "crosshairOptions", "applyCrosshair", "releaseFocus",
    "mountControls"
  ].filter(function (name) { return typeof mod[name] === "function"; }),
  resolved: (req.resolve || []).map(function (row) {
    var result = mod.resolveTransition(seedState(row.from), row.trigger);
    result.id = row.id || null;
    return result;
  }),
  routed: (req.route || []).map(function (row) {
    var result = mod.routeGesture(seedState(row.from), row.gesture, row.hits || {});
    result.id = row.id || null;
    return result;
  }),
};

if (req.selftest) {
  var applied = null;
  var chart = { applyOptions: function (opts) { applied = opts; } };
  out.crosshairReturned = mod.applyCrosshair(chart);
  out.crosshairApplied = applied;

  var zoomed = null;
  var zoomChart = {
    timeScale: function () {
      return {
        getVisibleLogicalRange: function () { return { from: 0, to: 10 }; },
        setVisibleLogicalRange: function (range) { zoomed = range; },
      };
    },
  };
  out.zoomIn = mod.zoomBy(zoomChart, 1) ? zoomed : null;
  zoomed = null;
  out.zoomOut = mod.zoomBy(zoomChart, -1) ? zoomed : null;
}

process.stdout.write(JSON.stringify(out));
"""


# ── harness ──────────────────────────────────────────────────────────────────


def _run_node(payload: dict) -> dict:
    """Run the JS mirror under node and return its JSON answer."""
    if _NODE is None:  # pragma: no cover — the wave's test command needs node too
        pytest.fail("node is required for the router-mirror suites")
    proc = subprocess.run(
        [_NODE, "-e", _NODE_SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        pytest.fail(f"node mirror driver failed:\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)


class _Overlay:
    """Recording overlay: notes what was asked and whether it handled it."""

    name = "overlay"

    def __init__(self):
        self.hit = True
        self.received: list = []
        self.handled = False

    def _hit(self, kind: str) -> bool:
        self.received.append(kind)
        if self.hit:
            self.handled = True
        return self.hit

    def view_mouse_press(self, ev) -> bool:
        return self._hit("press")

    def view_mouse_drag(self, ev) -> bool:
        return self._hit("drag")

    def view_mouse_click(self, ev) -> bool:
        return self._hit("click")


class _FakeDrawing(_Overlay):
    name = "drawing"

    def __init__(self):
        super().__init__()
        self.tool = None

    def tool_active(self) -> bool:
        return self.tool is not None and self.tool != TOOL_CURSOR

    def set_tool(self, tool) -> None:
        self.tool = tool


class _FakeAlarm(_Overlay):
    name = "alarm"

    def __init__(self):
        super().__init__()
        self.mode = False

    def is_alarm_mode(self) -> bool:
        return self.mode

    def set_alarm_mode(self, enabled) -> None:
        self.mode = bool(enabled)


class _FakeZoom(_Overlay):
    name = "zoom"

    def __init__(self):
        super().__init__()
        self.active = False
        self.cancels = 0

    def is_active(self) -> bool:
        return self.active

    def set_active(self, active) -> None:
        self.active = bool(active)

    def cancel(self) -> None:
        self.cancels += 1


def _wired_router():
    """A frozen Python router with recording overlays on all three wires."""
    drawing, alarm, zoom = _FakeDrawing(), _FakeAlarm(), _FakeZoom()
    router = ChartMouseRouter()
    router.drawing = drawing
    router.alarm = alarm
    router.zoom = zoom
    return router, drawing, alarm, zoom


def _seed(router, mode: str) -> None:
    if mode == "IDLE":
        return
    if mode == "DRAWING":
        assert REAL_TOOL is not None, "DRAWING_TOOLS carries no real tool"
        router.enter_drawing(REAL_TOOL)
    elif mode == "ZOOMING":
        router.enter_zoom()
    elif mode == "ALARM_PLACING":
        router.enter_alarm_placing()
    else:  # pragma: no cover — table guard
        raise AssertionError(f"unknown seed mode: {mode!r}")
    assert router.active_mode.name == mode


def _apply(router, trigger: str) -> bool:
    """Apply one intent trigger; returns the TR-9 refusal flag."""
    if trigger == "draw_tool":
        router.enter_drawing(REAL_TOOL)
    elif trigger == "draw_cursor":
        router.enter_drawing(TOOL_CURSOR)
    elif trigger == "enter_zoom":
        return not router.enter_zoom()
    elif trigger == "enter_alarm_placing":
        router.enter_alarm_placing()
    elif trigger == "exit_to_idle":
        router.exit_to_idle()
    else:  # pragma: no cover — table guard
        raise AssertionError(f"unknown intent trigger: {trigger!r}")
    return False


def _state(router, drawing, alarm, zoom) -> dict:
    tool = drawing.tool
    if tool is None:
        normalized = "none"
    elif tool == TOOL_CURSOR:
        normalized = "cursor"
    else:
        normalized = "tool"
    return {
        "mode": router.active_mode.name,
        "tool": normalized,
        "zoomActive": bool(zoom.active),
        "alarmMode": bool(alarm.mode),
    }


def _python_transition(from_mode: str, trigger: str, hits: dict | None = None):
    """Drive the frozen Python router one row. Returns (state, refused, handledBy)."""
    router, drawing, alarm, zoom = _wired_router()
    for overlay in (drawing, alarm, zoom):
        overlay.hit = (hits or {}).get(overlay.name, True)
    _seed(router, from_mode)
    refused = False
    handled = "none"
    if trigger in LV.ROUTER_GESTURES:
        gesture = {
            "press": router.view_mouse_press,
            "drag": router.view_mouse_drag,
            "click": router.view_mouse_click,
        }[trigger]
        gesture(object())
        handled = next(
            (o.name for o in (zoom, alarm, drawing) if o.handled), "none")
    elif trigger == "symbol_change":
        LV.reset_router_for_symbol_change(router)
    else:
        refused = _apply(router, trigger)
    return _state(router, drawing, alarm, zoom), refused, handled


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def _qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture(scope="module")
def mirror() -> dict:
    """One node process: the JS mirror's contract + every TR row resolved."""
    return _run_node({
        "module": str(INTERACTION_JS),
        "selftest": True,
        "resolve": [{"id": row["id"], "from": row["from"],
                     "trigger": row["trigger"]}
                    for row in LV.ROUTER_TRANSITIONS],
        "route": [{"id": row["id"], "from": row["from"],
                   "gesture": row["trigger"]}
                  for row in LV.ROUTER_TRANSITIONS
                  if row["trigger"] in LV.ROUTER_GESTURES],
    })


@pytest.fixture(scope="module")
def resolved(mirror) -> dict:
    return {row["id"]: row for row in mirror["resolved"]}


@pytest.fixture(scope="module")
def routed(mirror) -> dict:
    return {row["id"]: row for row in mirror["routed"]}


# ── AC1: the JS mirror never reinterprets the frozen table ───────────────────


def test_p6_t07_t11_the_mirror_table_is_transcribed_not_reinterpreted(mirror):
    assert mirror["modes"] == list(LV.ROUTER_MODES)
    assert mirror["triggers"] == list(LV.ROUTER_TRIGGERS)
    assert mirror["gestures"] == list(LV.ROUTER_GESTURES)
    # Row-for-row: ids, from, trigger, to and the single refusal flag.
    assert mirror["transitions"] == [dict(row) for row in LV.ROUTER_TRANSITIONS]
    assert [row["id"] for row in mirror["transitions"]] == [
        f"TR-{i}" for i in range(1, 18)]
    assert len(mirror["transitions"]) == 17


@pytest.mark.parametrize(
    "index", range(len(LV.ROUTER_TRANSITIONS)), ids=TRANSITION_IDS)
def test_p6_t07_t11_every_tr_row_resolves_identically(resolved, routed, index):
    row = LV.ROUTER_TRANSITIONS[index]
    js = resolved[row["id"]]
    state, refused, handled = _python_transition(row["from"], row["trigger"])

    assert js["refused"] is refused, f'{row["id"]}: refusal diverges'
    assert js["state"] == state, f'{row["id"]}: mirror state diverges'
    assert state["mode"] == row["to"], f'{row["id"]}: row expectation drifted'
    if row["trigger"] in LV.ROUTER_GESTURES:
        assert routed[row["id"]]["handledBy"] == handled, (
            f'{row["id"]}: gesture dispatch diverges')


@pytest.mark.parametrize("mode", LV.ROUTER_MODES)
@pytest.mark.parametrize("gesture", LV.ROUTER_GESTURES)
def test_p6_t07_t11_gesture_dispatch_is_identical_on_both_engines(mode, gesture):
    cases = [{}]
    if mode == "IDLE":
        cases = [{}, {"alarm": False}, {"alarm": False, "drawing": False}]
    request = [{"id": f"{mode}/{gesture}/{i}", "from": mode,
                "gesture": gesture, "hits": hits}
               for i, hits in enumerate(cases)]
    js_rows = {row["id"]: row for row in _run_node(
        {"module": str(INTERACTION_JS), "route": request})["routed"]}
    for i, hits in enumerate(cases):
        state, _refused, handled = _python_transition(mode, gesture, hits)
        js = js_rows[f"{mode}/{gesture}/{i}"]
        assert js["handledBy"] == handled, f"{mode}/{gesture}/{hits}"
        assert state["mode"] == mode  # a gesture never changes the mode


def test_p6_t07_t11_tr9_refusal_is_explicit(resolved):
    """ALARM_PLACING + magnifier: refused, zoom untouched, alarm still armed."""
    row = next(r for r in LV.ROUTER_TRANSITIONS if r["id"] == "TR-9")
    assert row["from"] == "ALARM_PLACING" and row["trigger"] == "enter_zoom"
    assert row.get("refused") is True

    router, drawing, alarm, zoom = _wired_router()
    _seed(router, "ALARM_PLACING")
    assert router.enter_zoom() is False
    assert router.active_mode.name == "ALARM_PLACING"
    assert zoom.active is False and zoom.cancels == 0
    assert alarm.mode is True

    js = resolved["TR-9"]
    assert js["refused"] is True
    assert js["state"] == _state(router, drawing, alarm, zoom)


@pytest.mark.parametrize("mode", LV.ROUTER_MODES)
def test_p6_t07_t11_tr17_symbol_change_resets_every_mode(mode, resolved):
    """TR-17: a symbol change mid-gesture lands in IDLE from any mode."""
    router, drawing, alarm, zoom = _wired_router()
    _seed(router, mode)
    mode_after = LV.reset_router_for_symbol_change(router)
    assert mode_after is router.active_mode
    assert router.active_mode.name == "IDLE"
    assert drawing.tool_active() is False  # the draft is discarded
    assert zoom.active is False

    js = resolved["TR-17"] if mode == "DRAWING" else _run_node({
        "module": str(INTERACTION_JS),
        "resolve": [{"id": mode, "from": mode, "trigger": "symbol_change"}],
    })["resolved"][0]
    assert js["state"]["mode"] == "IDLE"


# ── AC1: in-HTML controls + the Python shim ─────────────────────────────────


def test_p6_t07_t11_control_ids_mirror_chart_controls(mirror):
    assert tuple(button["id"] for button in mirror["controls"]) == LV.CONTROL_IDS
    assert tuple(button["intent"] for button in mirror["controls"]) == (
        "zoom_out", "zoom_in", "magnify_toggle", "reset")
    # The Python side of the contract is ChartControls' signal surface.
    for signal_name in ("zoom_in", "zoom_out", "magnify_toggled", "reset"):
        assert hasattr(ChartControls, signal_name)
    assert mirror["zoomFactors"] == {
        "in": LV.ZOOM_FACTORS["in"], "out": LV.ZOOM_FACTORS["out"]}
    # The page's zoom math is the one chart.js already uses (0.8 / 1.25).
    # Zoom about the visible-range midpoint: 0.8 in, 1.25 out (range 0..10).
    assert mirror["zoomIn"] == {"from": 1, "to": 9}
    assert mirror["zoomOut"] == {"from": -1.25, "to": 11.25}


def test_p6_t07_t11_magnifier_control_goes_through_the_router(_qapp):
    view = LV.LwcChartView()
    entered = view.handle_control("magnifier")
    assert entered["refused"] is False
    assert entered["mode"] == "ZOOMING"
    assert view.router.active_mode.name == "ZOOMING"
    assert entered["op"] == {"op": "router_mode", "mode": "ZOOMING",
                             "intent": "enter_zoom", "refused": False}

    left = view.handle_control("magnifier")  # toggle off
    assert left["mode"] == "IDLE"
    assert left["op"]["intent"] == "exit_to_idle"

    ops = view.interaction_ops
    assert [op["op"] for op in ops] == ["router_mode", "router_mode"]
    envelopes = view.interaction_envelopes
    assert len(envelopes) == 2 and envelopes[0]["v"] == 1


def test_p6_t07_t11_alarm_placement_refuses_the_magnifier_control(_qapp):
    view = LV.LwcChartView()
    view.router.enter_alarm_placing()
    out = view.handle_control("magnifier", True)
    assert out["refused"] is True
    assert out["mode"] == "ALARM_PLACING"
    assert out["op"]["refused"] is True
    assert view.router.active_mode.name == "ALARM_PLACING"


def test_p6_t07_t11_zoom_and_reset_controls(_qapp):
    view = LV.LwcChartView()
    assert view.handle_control("zoom-in")["op"] == {"op": "zoom", "step": 1}
    assert view.handle_control("zoom-out")["op"] == {"op": "zoom", "step": -1}
    view.handle_control("magnifier")
    reset = view.handle_control("reset")
    assert reset["mode"] == "IDLE"
    assert reset["op"] == {"op": "reset_view", "mode": "IDLE"}
    with pytest.raises(ValueError):
        view.handle_control("no-such-control")


def test_p6_t07_t11_symbol_change_resets_the_view(_qapp, mirror):
    view = LV.LwcChartView()
    assert REAL_TOOL is not None
    view.router.enter_drawing(REAL_TOOL)
    assert view.router.active_mode.name == "DRAWING"
    view.set_symbol("MSFT")
    assert view.router.active_mode.name == "IDLE"
    assert view.interaction_ops[-1]["intent"] == "symbol_change"
    assert view.interaction_ops[-1]["mode"] == "IDLE"


def test_p6_t07_t11_focus_round_trip_is_recorded(_qapp, mirror):
    """DG92: the page's Esc blur hands focus back, and the round trip counts."""
    assert mirror["focusModel"] == "lwc-focus-forward-v1"
    view = LV.LwcChartView()
    seen: list = []
    view.focusRoundTrip.connect(lambda: seen.append(True))
    view.handle_focus_released()
    view.handle_focus_released()
    assert view.focus_releases == 2
    assert len(seen) == 2


# ── AC2: library-native crosshair; the dialogs stay Qt ──────────────────────

#: Tokens that would mark a hand-rolled crosshair label primitive.
_CUSTOM_CROSSHAIR_TOKENS = (
    "pill", "pricechip", "price-chip", "price_chip", "drawcrosshair",
    "draw_crosshair", "_update_crosshair", "crosshairlabel", "crosshair_label",
)


def test_p6_t07_t12_crosshair_is_the_library_native_crosshair(mirror):
    assert mirror["crosshairModeId"] == LV.CROSSHAIR_MODE_ID == 0
    assert mirror["crosshairModeName"] == LV.CROSSHAIR_MODE_NAME == "normal"
    options = mirror["crosshairOptions"]
    for line in ("vertLine", "horzLine"):
        assert options[line]["visible"] is True
        assert options[line]["labelVisible"] is True
    # It reaches the chart through the library's own applyOptions.
    assert mirror["crosshairApplied"] == {"crosshair": options}
    assert mirror["crosshairReturned"] == {"crosshair": options}


def test_p6_t07_t12_no_custom_crosshair_primitive_in_chart_assets():
    assets = ROOT / "chart_assets" / "lwc"
    files = sorted(path for path in assets.iterdir()
                   if path.is_file() and path.suffix in {".js", ".html", ".css"})
    assert files, "the LWC asset tree is missing its page assets"
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        for token in _CUSTOM_CROSSHAIR_TOKENS:
            assert token not in text, (
                f"{path.name} carries a custom crosshair primitive ({token!r})")


def test_p6_t07_t12_the_dialogs_stay_qt():
    for suite in ("test_zone_dialog.py", "test_horizontal_line_dialog.py"):
        assert (ROOT / "tests" / suite).is_file(), (
            f"the Qt dialog suite {suite} is missing")
    # The LWC interaction surface builds no dialog of its own.
    for path in (ROOT / "ui" / "lwc_view.py", INTERACTION_JS):
        text = path.read_text(encoding="utf-8")
        assert "QDialog" not in text
        assert "showModal" not in text


# ── AC3: renderer-only residue scan ─────────────────────────────────────────

#: Top-level names the renderer may import *beyond* the stdlib: its Qt host and
#: the project's own packages. Everything else is third-party or network — the
#: boundary is "stdlib + renderer", not a literal snapshot of today's imports.
#: A hardcoded list rots the moment a later wave legitimately adds a stdlib
#: module, which is exactly how P6-T09's ``bisect`` broke this gate.
_RENDERER_EXTRA_ALLOWED = frozenset({"PyQt6", "data", "services", "ui", "config"})

#: Backend / persistence / network surfaces the renderer must never reach into,
#: whatever the allowlist grows to. Checked before the allowlist, because some
#: of these (``sqlite3``, ``socket``, ``urllib``) are stdlib names.
_RENDERER_FORBIDDEN_IMPORTS = frozenset({
    "ibkr", "stores", "persistence",
    "sqlite3", "sqlalchemy", "psycopg2", "psycopg",
    "socket", "ssl", "socketserver", "http", "urllib", "urllib3", "requests",
    "httpx", "aiohttp", "websocket", "websockets", "ftplib", "smtplib",
    "telnetlib", "xmlrpc",
})

_FORBIDDEN_SURFACE = (
    "import ibkr", "from ibkr", "sqlite3", "qsettings", "watchlist", "popout",
    "place_order", "send_order", "order_id", "nextvalidid",
    "reqhistoricaldata", "market_data",
)


def test_p6_t07_t13_python_router_is_untouched():
    path = ROOT / "ui" / "chart_mouse_router.py"
    source = path.read_text(encoding="utf-8")
    assert "class RouterMode(Enum)" in source
    assert "class ChartMouseRouter" in source
    low = source.lower()
    for token in ("lwc", "interaction", "mirror", "chart_assets"):
        assert token not in low, f"the frozen router grew {token!r} vocabulary"


def test_p6_t07_t13_no_out_of_scope_surface_in_the_interaction_diff():
    for path in (ROOT / "ui" / "lwc_view.py", INTERACTION_JS):
        text = path.read_text(encoding="utf-8").lower()
        for token in _FORBIDDEN_SURFACE:
            assert token not in text, f"{path.name} carries {token!r}"
    js = INTERACTION_JS.read_text(encoding="utf-8")
    for token in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon"):
        assert token not in js, f"interaction.js grew a network call ({token})"


def test_p6_t07_t13_renderer_only_import_boundary():
    source = (ROOT / "ui" / "lwc_view.py").read_text(encoding="utf-8")
    modules = re.findall(r"^(?:from|import)\s+([A-Za-z_][\w.]*)", source, re.M)
    assert modules, "no imports found — the scan is looking at the wrong file"
    allowed = set(sys.stdlib_module_names) | _RENDERER_EXTRA_ALLOWED
    for module in modules:
        top = module.split(".")[0]
        assert top not in _RENDERER_FORBIDDEN_IMPORTS, (
            f"lwc_view.py reached into the backend/network: {module}")
        assert top in allowed, (
            f"lwc_view.py imports outside the renderer boundary: {module}")
