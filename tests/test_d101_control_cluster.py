"""tests/test_d101_control_cluster.py — P30-01 / D101 control-cluster evidence.

Three of the four offscreen layers the phase declares for the restored
zoom / magnifier / Reset cluster:

* **The join (AC-D101.3)** — a node process defines ``globalThis.document``
  *before* it requires ``chart_assets/lwc/interaction.js`` (``mountControls``
  returns ``[]`` without a document, so a bare run would compare two empty
  tuples), mounts the four buttons into a stub container and reports the ids
  it built. The module-local :func:`missing_ids` helper then joins the mounted
  ids to ``ui.lwc_view.CONTROL_IDS`` and ``ui.chart_controls.CONTROL_SPECS``,
  with a negative case (one mounted button dropped) and a non-vacuous guard
  (an empty mount is missing every id).
* **The Python bridge path (AC-D101.5)** — ``LwChartView`` is constructed with
  no host (the ``tests/test_lwc_router_mirror.py`` pattern) and each id is
  driven through the *production* slot ``LwBridge.controlPressed``; the shim's
  op must reach the interaction log and the router must move. A TR-9 refusal
  reports exactly once, and hostile payloads are ignored, never raised.
* **The production reference (AC-D101.3/AC-D101.5)** — an AST read of
  ``ui/lwc_view.py`` proves it imports ``ui.chart_controls`` and that
  ``_on_page_control_pressed`` is a caller of ``handle_control``, so neither
  half can drift back to being referenced only by tests.

The painted page is **not** evidence here: nothing in this file starts a
web-engine view or captures its pixels. That check is owner-run (G7) and is
claimed by no case in this file.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ui import lwc_view as LV
from ui.chart_controls import CONTROL_SPECS, ChartControls

ROOT = Path(__file__).resolve().parents[1]
INTERACTION_JS = ROOT / "chart_assets" / "lwc" / "interaction.js"
LWC_VIEW_PY = ROOT / "ui" / "lwc_view.py"

_NODE = shutil.which("node")

#: The node driver: it builds a minimal stub document (the same shape
#: ``chart_assets/lwc/interaction.controls.test.js`` builds) **before**
#: requiring the module, mounts the buttons into a stub container and reports
#: what the page made. ``stub: false`` requires the module *without* a
#: document, which is the run that must mount nothing.
_NODE_SCRIPT = r"""
const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8"));

function makeElement(tag) {
  var attrs = Object.create(null);
  var listeners = Object.create(null);
  return {
    tagName: tag,
    id: "",
    className: "",
    textContent: "",
    title: "",
    type: "",
    children: [],
    setAttribute: function (name, value) { attrs[name] = String(value); },
    getAttribute: function (name) {
      return Object.prototype.hasOwnProperty.call(attrs, name)
        ? attrs[name]
        : null;
    },
    appendChild: function (child) { this.children.push(child); return child; },
    addEventListener: function (type, fn) {
      (listeners[type] = listeners[type] || []).push(fn);
    },
    click: function () {
      (listeners.click || []).forEach(function (fn) { fn(); });
    },
  };
}

var byId = Object.create(null);

if (req.stub !== false) {
  globalThis.document = {
    createElement: function (tag) { return makeElement(tag); },
    getElementById: function (id) {
      return Object.prototype.hasOwnProperty.call(byId, id) ? byId[id] : null;
    },
  };
}

const mod = require(req.module);

const container = {
  children: [],
  appendChild: function (child) {
    this.children.push(child);
    if (child && child.id) byId[child.id] = child;
    return child;
  },
};

const calls = [];
const mounted = mod.mountControls(container, function (id, value) {
  calls.push([id, value]);
  return undefined; /* the production shape: a QWebChannel call returns nothing */
});

/* One magnifier press: the attribute must stay at its pre-click value. */
const magnifier = mounted[2];
if (magnifier && typeof magnifier.click === "function") magnifier.click();

const domIds = mounted.map(function (button) { return button.id; });

process.stdout.write(JSON.stringify({
  controls: mod.CONTROL_BUTTONS,
  mounted: domIds.map(function (id) { return id.replace(/^control-/, ""); }),
  domIds: domIds,
  pressed: mounted.map(function (button) {
    return button.getAttribute("aria-pressed");
  }),
  calls: calls,
  count: mounted.length,
  containerChildren: container.children.length,
  mountExport: typeof mod.mountControls,
  syncExport: typeof mod.syncControlState,
}));
"""


# ── harness ──────────────────────────────────────────────────────────────────


def _run_node(payload: dict) -> dict:
    """Run the page module under node and return its JSON answer."""
    if _NODE is None:  # pragma: no cover — the wave's test command needs node too
        pytest.fail("node is required for the D101 control-cluster suite")
    proc = subprocess.run(
        [_NODE, "-e", _NODE_SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        pytest.fail(f"node control-cluster driver failed:\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)


def missing_ids(mounted, expected) -> list:
    """The ids in ``expected`` that ``mounted`` does not carry (order kept).

    The one join both the positive and the negative case drive, so a future
    control surface that stops being mounted turns this helper red instead of
    passing vacuously.
    """
    present = list(mounted)
    return [control_id for control_id in expected if control_id not in present]


@pytest.fixture(scope="module")
def _qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture(scope="module")
def page_mount() -> dict:
    """One node process: the page's controls mounted against the stub document."""
    return _run_node({"module": str(INTERACTION_JS), "stub": True})


# ── AC-D101.3: the four-way join ─────────────────────────────────────────────


def test_p30_t01_every_control_id_is_mounted_and_declared(page_mount):
    """Mirror ids == mounted ids == CONTROL_IDS == CONTROL_SPECS, in order."""
    expected = [spec.id for spec in CONTROL_SPECS]
    assert expected == ["zoom-out", "zoom-in", "magnifier", "reset"]
    assert list(LV.CONTROL_IDS) == expected
    assert page_mount["mounted"] == expected
    assert missing_ids(page_mount["mounted"], expected) == []
    # The DOM ids are the mirror ids under the page's own prefix, so the join
    # is against buttons that really exist rather than a derived list.
    assert page_mount["domIds"] == [f"control-{cid}" for cid in expected]
    assert page_mount["count"] == len(expected)
    assert page_mount["containerChildren"] == len(expected)
    assert page_mount["mountExport"] == "function"
    assert page_mount["syncExport"] == "function"


def test_p30_t01_the_three_declarations_agree_row_for_row(page_mount):
    """Intent, toggle flag and ChartControls' signal agree across the three."""
    specs = list(CONTROL_SPECS)
    buttons = page_mount["controls"]
    assert [button["id"] for button in buttons] == [spec.id for spec in specs]
    assert [button["intent"] for button in buttons] == [spec.intent for spec in specs]
    assert [bool(button.get("toggle", False)) for button in buttons] == [
        spec.toggle for spec in specs]
    assert [spec.toggle for spec in specs] == [False, False, True, False]
    for spec in specs:
        assert hasattr(ChartControls, spec.signal), (
            f"ChartControls no longer carries the {spec.signal!r} signal")
    # The widget's own signal surface is exactly the declaration's signal column.
    assert {spec.signal for spec in specs} == {
        "zoom_in", "zoom_out", "magnify_toggled", "reset"}


def test_p30_t01_the_join_is_red_when_a_mounted_id_is_missing(page_mount):
    """The negative case: drop the last mounted id and the same helper reports it."""
    expected = [spec.id for spec in CONTROL_SPECS]
    assert missing_ids(page_mount["mounted"][:-1], expected) == [expected[-1]]
    # A press on the missing control is the DOM-side symptom: the magnifier is
    # what carries the toggle, so removing it is the case AC-D101.2 depends on.
    assert missing_ids(page_mount["mounted"][:-1], expected) == ["reset"]


def test_p30_t01_the_join_cannot_pass_vacuously(page_mount):
    """An empty mount is missing every id — the helper is not a no-op."""
    expected = [spec.id for spec in CONTROL_SPECS]
    assert expected, "CONTROL_SPECS is empty — nothing to join"
    assert missing_ids([], expected) == expected
    assert missing_ids(page_mount["mounted"], expected) == []


def test_p30_t01_a_document_less_run_mounts_nothing():
    """Why the stub is defined first: without a document the page makes no buttons."""
    bare = _run_node({"module": str(INTERACTION_JS), "stub": False})
    assert bare["mounted"] == []
    assert bare["domIds"] == []
    assert bare["containerChildren"] == 0


def test_p30_t01_a_toggle_press_is_not_latched_ahead_of_the_answer(page_mount):
    """The production shape (no return) leaves the magnifier at its pre-click state."""
    assert page_mount["calls"] == [["magnifier", True]]
    assert page_mount["pressed"] == [None, None, "false", None]


# ── AC-D101.1 / AC-D101.5: the production bridge path ────────────────────────


def test_p30_t01_every_control_press_crosses_to_the_shim(_qapp):
    """Each id, through LwBridge.controlPressed, logs its op and moves the router."""
    view = LV.LwcChartView()
    emitted: list = []
    view.interactionOpsEmitted.connect(emitted.append)
    refusals: list = []
    view.zoom_refused.connect(lambda: refusals.append(True))

    cases = [
        ("zoom-out", None, {"op": "zoom", "step": -1}, "IDLE"),
        ("zoom-in", None, {"op": "zoom", "step": 1}, "IDLE"),
        ("magnifier", True, {"op": "router_mode", "mode": "ZOOMING",
                             "intent": "enter_zoom", "refused": False},
         "ZOOMING"),
        ("reset", None, {"op": "reset_view", "mode": "IDLE"}, "IDLE"),
    ]
    for index, (control, value, expected_op, mode) in enumerate(cases):
        view._bridge.controlPressed(
            json.dumps({"control": control, "value": value}))
        # The production slot decoded the payload and the shim ran: one op per
        # press, appended by _publish_interaction_op (the replay log).
        assert view._interaction_log[-1] == expected_op, control
        assert len(view._interaction_log) == index + 1, control
        assert len(emitted) == index + 1, control
        assert view._router.active_mode.name == mode, control

    assert refusals == []
    # The op is also what the page receives: the interaction channel replays it.
    assert [env["v"] for env in view.interaction_envelopes] == [1, 1, 1, 1]


def test_p30_t01_a_refused_toggle_is_reported_exactly_once(_qapp):
    """TR-9: alarm placement refuses the magnifier; one report, refused op."""
    view = LV.LwcChartView()
    refusals: list = []
    view.zoom_refused.connect(lambda: refusals.append(True))
    view._router.enter_alarm_placing()
    assert view._router.active_mode.name == "ALARM_PLACING"
    before = len(view._interaction_log)

    view._bridge.controlPressed(
        json.dumps({"control": "magnifier", "value": True}))

    assert view._interaction_log[-1] == {
        "op": "router_mode",
        "mode": "ALARM_PLACING",
        "intent": "enter_zoom",
        "refused": True,
    }
    assert len(view._interaction_log) == before + 1
    assert view._router.active_mode.name == "ALARM_PLACING"
    assert refusals == [True], "the refusal must be reported exactly once"


def test_p30_t01_hostile_payloads_never_raise_or_act(_qapp):
    """A stale page must not raise across the bridge, log an op or refuse."""
    view = LV.LwcChartView()
    refusals: list = []
    view.zoom_refused.connect(lambda: refusals.append(True))

    view._bridge.controlPressed(
        json.dumps({"control": "no-such-control", "value": True}))
    view._bridge.controlPressed("not json")
    view._bridge.controlPressed(json.dumps(["not", "a", "dict"]))

    assert view._interaction_log == []
    assert refusals == []
    assert view._router.active_mode.name == "IDLE"


# ── AC-D101.3 / AC-D101.5: the production reference (AST, not text) ─────────


def test_p30_t01_the_shim_has_a_production_caller():
    """ui/lwc_view.py imports ui.chart_controls and _on_page_control_pressed calls it."""
    tree = ast.parse(LWC_VIEW_PY.read_text(encoding="utf-8"))

    control_imports = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "ui.chart_controls"
    ]
    assert control_imports, "ui/lwc_view.py no longer imports ui.chart_controls"
    imported = {alias.name for node in control_imports for alias in node.names}
    assert "CONTROL_SPECS" in imported, (
        "the ids must derive from the one declaration, not a second literal")

    handlers = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_on_page_control_pressed"
    ]
    assert len(handlers) == 1, "the page slot handler is missing or duplicated"
    calls = [
        node for node in ast.walk(handlers[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "handle_control"
    ]
    assert calls, "_on_page_control_pressed no longer calls handle_control"
    assert isinstance(calls[0].func.value, ast.Name)
    assert calls[0].func.value.id == "self"
