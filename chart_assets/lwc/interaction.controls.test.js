// interaction.controls.test.js — D101 page-DOM contract suite (P30-01).
//
// Boots the REAL interaction.js against a stub document the file builds
// itself (no npm, no network, no jsdom): four control buttons mount in
// mirror order, a second mount into the same container appends nothing, the
// three-branch latch rule never advertises a refused state, and the exported
// `syncControlState(op)` drives the magnifier from the durable router mode.
//
// The shipped chart.test.js harness is deliberately NOT touched (AR-P30-7):
// this file owns its own per-container stub.

const { test } = require("node:test");
const assert = require("node:assert/strict");

// ── stub document (defined BEFORE interaction.js is required) ───────────────

let ELEMENTS = {};
let DOM = null;

function makeElement(tag) {
  const attrs = {};
  const listeners = {};
  return {
    tagName: String(tag || "div").toUpperCase(),
    id: "",
    className: "",
    textContent: "",
    title: "",
    type: "",
    setAttribute(name, value) {
      attrs[name] = String(value);
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(attrs, name)
        ? attrs[name]
        : null;
    },
    addEventListener(type, fn) {
      (listeners[type] = listeners[type] || []).push(fn);
    },
    click() {
      (listeners.click || []).forEach((fn) => fn({ type: "click" }));
    },
    hasListener(type) {
      return Array.isArray(listeners[type]) && listeners[type].length > 0;
    },
  };
}

function resetDom() {
  ELEMENTS = {};
  const container = {
    children: [],
    appendChild(child) {
      this.children.push(child);
      ELEMENTS[child.id] = child;
    },
  };
  DOM = {
    createElement(tag) {
      return makeElement(tag);
    },
    getElementById(id) {
      return ELEMENTS[id] || null;
    },
  };
  globalThis.document = DOM;
  return container;
}

const container = resetDom();
const interaction = require("./interaction.js");

// ── recorders ───────────────────────────────────────────────────────────────

function recordingBridge() {
  const calls = { zoomRefused: [], controlPressed: [] };
  return {
    calls,
    zoomRefused(payload) {
      calls.zoomRefused.push(JSON.parse(payload));
    },
    controlPressed(payload) {
      calls.controlPressed.push(JSON.parse(payload));
    },
  };
}

function recordingOnControl(answer) {
  const calls = [];
  const fn = (id, value) => {
    calls.push([id, value]);
    return typeof answer === "function" ? answer(id, value) : answer;
  };
  fn.calls = calls;
  return fn;
}

const MAGNIFIER = "control-magnifier";

// ── (a)/(b) mount + idempotence (AC-D101.1) ─────────────────────────────────

test("(a) mounts the four mirror controls in order, once", () => {
  const box = resetDom();
  const bridge = recordingBridge();
  const made = interaction.mountControls(box, recordingOnControl(null), bridge);

  assert.equal(made.length, 4);
  assert.deepEqual(
    made.map((btn) => btn.id),
    ["control-zoom-out", "control-zoom-in", "control-magnifier", "control-reset"],
  );
  assert.deepEqual(
    box.children.map((btn) => btn.id),
    made.map((btn) => btn.id),
  );
  assert.deepEqual(
    box.children.map((btn) => btn.id),
    interaction.CONTROL_BUTTONS.map((spec) => "control-" + spec.id),
  );
  for (const btn of box.children) {
    assert.equal(btn.hasListener("click"), true, `${btn.id} is clickable`);
  }
  assert.equal(box.children[2].getAttribute("aria-pressed"), "false");
  assert.equal(box.children[0].getAttribute("aria-pressed"), null);
  assert.equal(box.children[1].getAttribute("aria-pressed"), null);
  assert.equal(box.children[3].getAttribute("aria-pressed"), null);
});

test("(b) a second mount is idempotent per container", () => {
  const box = resetDom();
  const first = interaction.mountControls(box, recordingOnControl(null));
  const second = interaction.mountControls(box, recordingOnControl(null));

  assert.equal(second, first, "the same buttons come back");
  assert.equal(box.children.length, 4, "nothing was appended twice");
});

// ── (c)/(d)/(e)/(f) the three-branch latch rule (AC-D101.2) ────────────────

test("(c) refusal off→refused restores the pre-click value, one report", () => {
  const box = resetDom();
  const bridge = recordingBridge();
  interaction.mountControls(
    box,
    recordingOnControl({ refused: true, mode: "ALARM_PLACING" }),
    bridge,
  );
  const btn = ELEMENTS[MAGNIFIER];
  assert.equal(btn.getAttribute("aria-pressed"), "false");

  btn.click();

  assert.equal(btn.getAttribute("aria-pressed"), "false",
    "a refused request never latches true");
  assert.equal(bridge.calls.zoomRefused.length, 1);
  assert.deepEqual(bridge.calls.zoomRefused[0], {
    trigger: "magnify_toggle",
    mode: "ALARM_PLACING",
  });
});

test("(d) refusal on→refused never adopts the refused request, one report", () => {
  const box = resetDom();
  const bridge = recordingBridge();
  const onControl = recordingOnControl({ refused: true, mode: "ALARM_PLACING" });
  interaction.mountControls(box, onControl, bridge);
  const btn = ELEMENTS[MAGNIFIER];
  btn.setAttribute("aria-pressed", "true"); // AP-P30-3: the constructed state

  btn.click();

  assert.deepEqual(onControl.calls, [["magnifier", false]]);
  assert.notEqual(btn.getAttribute("aria-pressed"), "false",
    "the attribute never equals the refused request");
  assert.equal(btn.getAttribute("aria-pressed"), "true");
  assert.equal(bridge.calls.zoomRefused.length, 1);
});

test("(e) a synchronous mode drives the attribute, never a refusal report", () => {
  const box = resetDom();
  const bridge = recordingBridge();
  const answers = [
    { refused: false, mode: "ZOOMING" },
    { refused: false, mode: "IDLE" },
  ];
  const onControl = recordingOnControl(() => answers.shift());
  interaction.mountControls(box, onControl, bridge);
  const btn = ELEMENTS[MAGNIFIER];

  btn.click();
  assert.equal(btn.getAttribute("aria-pressed"), "true");
  btn.click();
  assert.equal(btn.getAttribute("aria-pressed"), "false");
  assert.equal(bridge.calls.zoomRefused.length, 0);
  assert.deepEqual(onControl.calls, [["magnifier", true], ["magnifier", false]]);
});

test("(f) no synchronous answer leaves the attribute for the mode op", () => {
  const box = resetDom();
  const bridge = recordingBridge();
  const onControl = recordingOnControl(undefined);
  interaction.mountControls(box, onControl, bridge);
  const btn = ELEMENTS[MAGNIFIER];

  btn.click();

  assert.deepEqual(onControl.calls, [["magnifier", true]]);
  assert.equal(btn.getAttribute("aria-pressed"), "false",
    "the attribute still describes the state the app is in");
  assert.equal(bridge.calls.zoomRefused.length, 0);
});

// ── (g) syncControlState (S-P30-2) ───────────────────────────────────────────

test("(g) syncControlState follows the durable mode and ignores a zoom op", () => {
  const box = resetDom();
  interaction.mountControls(box, recordingOnControl(null));
  const btn = ELEMENTS[MAGNIFIER];

  assert.equal(
    interaction.syncControlState({ op: "router_mode", mode: "ZOOMING" }), true);
  assert.equal(btn.getAttribute("aria-pressed"), "true");

  assert.equal(
    interaction.syncControlState({ op: "reset_view", mode: "IDLE" }), true);
  assert.equal(btn.getAttribute("aria-pressed"), "false");

  const before = btn.getAttribute("aria-pressed");
  assert.equal(interaction.syncControlState({ op: "zoom", step: 1 }), false);
  assert.equal(btn.getAttribute("aria-pressed"), before,
    "a zoom op carries no mode and changes nothing");

  assert.equal(
    interaction.syncControlState({ op: "set_timezone", mode: "12h" }), false);
  assert.equal(btn.getAttribute("aria-pressed"), before);
});

test("(g) syncControlState returns false when nothing is mounted", () => {
  resetDom();
  assert.equal(
    interaction.syncControlState({ op: "router_mode", mode: "ZOOMING" }),
    false,
  );
});

// ── (h) container guard ─────────────────────────────────────────────────────

test("(h) an inert container mounts nothing and does not throw", () => {
  resetDom();
  assert.deepEqual(interaction.mountControls({}, recordingOnControl(null)), []);
});
