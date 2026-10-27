// gestures.test.js — node --test contract suite for the Q-32 alarm gesture
// layer. No DOM, no chart library: the mapping core is exercised directly and
// the glue runs against a fake chart/container/series, exactly the shapes
// chart.js hands it.
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const LwGestures = require("./gestures.js");

const DIR = __dirname;
const read = (name) => readFileSync(path.join(DIR, name), "utf8");

/* A container shaped like the page's #chart: one style object, listener
 * capture, and a real client rect. */
function fakeContainer(top = 50) {
  const handlers = {};
  return {
    style: {},
    handlers,
    addEventListener(name, fn) {
      handlers[name] = fn;
    },
    removeEventListener(name, fn) {
      if (handlers[name] === fn) delete handlers[name];
    },
    getBoundingClientRect() {
      return { top, left: 0, width: 800, height: 600 };
    },
  };
}

function fakeChart() {
  const calls = [];
  return {
    calls,
    applyOptions(options) {
      if (options && ("handleScroll" in options || "handleScale" in options)) {
        calls.push({
          handleScroll: options.handleScroll,
          handleScale: options.handleScale,
        });
      }
    },
  };
}

/* price = 100 + (pane-local y) / 10 — monotonic and easy to assert. */
function fakeSeries() {
  return {
    coordinateToPrice(y) {
      return 100 + Number(y) / 10;
    },
  };
}

function fakeAlarms() {
  const seen = { previews: [], cleared: 0, created: [] };
  return {
    seen,
    showPreview(price) {
      seen.previews.push(price);
      return true;
    },
    clearPreview() {
      seen.cleared += 1;
      return true;
    },
    reportAlarmCreated(price, bridge) {
      seen.created.push({ price, bridge });
      return true;
    },
  };
}

function bindAll(extra = {}) {
  LwGestures.reset();
  const chart = fakeChart();
  const container = fakeContainer();
  const alarms = fakeAlarms();
  const timers = {
    pending: [],
    set(fn, ms) {
      this.pending.push({ fn, ms });
      return this.pending.length;
    },
    clear() {},
  };
  LwGestures.bind(chart, container, fakeSeries, {
    alarms,
    timers,
    bridge: { id: "fake-bridge" },
    ...extra,
  });
  return { chart, container, alarms, timers, handlers: container.handlers };
}

describe("gestures.js — offline / no remote assets", () => {
  it("loads no remote script and no bare npm require", () => {
    const src = read("gestures.js");
    assert.ok(!/(src|href)\s*=\s*["']https?:\/\//i.test(src));
    assert.ok(!/unpkg\.com|cdn\.jsdelivr|cdnjs\.cloudflare/i.test(src));
    assert.ok(!/require\(["'][^./]/.test(src), "no bare npm require");
  });
});

describe("interaction op -> router mode/tool (mirror of chart.js)", () => {
  it("starts IDLE with the cursor tool", () => {
    assert.deepEqual(LwGestures.initialRouterState(), {
      mode: "IDLE",
      tool: "none",
    });
  });

  it("takes an explicit mode and tool", () => {
    let state = LwGestures.initialRouterState();
    state = LwGestures.nextRouterState(state, {
      op: "set_router_mode",
      mode: "ALARM_PLACING",
      tool: "alarm",
    });
    assert.deepEqual(state, { mode: "ALARM_PLACING", tool: "alarm" });
  });

  it("takes a bare mode op (the alarm arm path) without touching the tool", () => {
    let state = { mode: "IDLE", tool: "cursor" };
    state = LwGestures.nextRouterState(state, { mode: "ALARM_PLACING" });
    assert.deepEqual(state, { mode: "ALARM_PLACING", tool: "cursor" });
  });

  it("mirrors reset_view -> IDLE/cursor", () => {
    let state = { mode: "DRAWING", tool: "trendline" };
    state = LwGestures.nextRouterState(state, { op: "reset_view" });
    assert.deepEqual(state, { mode: "IDLE", tool: "cursor" });
  });

  it("mirrors the intent fallbacks (enter_zoom / exit_to_idle / symbol_change)", () => {
    const base = { mode: "IDLE", tool: "none" };
    assert.equal(
      LwGestures.nextRouterState(base, { intent: "enter_zoom" }).tool,
      "zoom",
    );
    assert.equal(
      LwGestures.nextRouterState(base, { intent: "exit_to_idle" }).tool,
      "cursor",
    );
    assert.equal(
      LwGestures.nextRouterState(base, { intent: "symbol_change" }).tool,
      "cursor",
    );
  });

  it("ignores junk without throwing", () => {
    const base = { mode: "IDLE", tool: "none" };
    for (const junk of [null, undefined, 42, "x", []]) {
      assert.deepEqual(LwGestures.nextRouterState(base, junk), base);
    }
  });

  it("an explicit tool wins over the intent fallback", () => {
    const state = LwGestures.nextRouterState(
      { mode: "IDLE", tool: "none" },
      { intent: "enter_zoom", tool: "alarm" },
    );
    assert.equal(state.tool, "alarm");
  });
});

describe("drag threshold (3 px)", () => {
  it("a still click is not a drag", () => {
    assert.equal(LwGestures.dragExceeded({ x: 10, y: 10 }, { x: 12, y: 11 }), false);
  });

  it("movement beyond 3 px is a drag", () => {
    assert.equal(LwGestures.dragExceeded({ x: 10, y: 10 }, { x: 14, y: 10 }), true);
    assert.equal(LwGestures.dragExceeded({ x: 10, y: 10 }, { x: 10, y: 15 }), true);
  });

  it("a missing press is never a drag", () => {
    assert.equal(LwGestures.dragExceeded(null, { x: 0, y: 0 }), false);
    assert.equal(LwGestures.dragExceeded({ x: 0, y: 0 }, null), false);
  });
});

describe("applyRouterOp — chrome only in ALARM_PLACING", () => {
  it("suppresses pan/zoom and sets a crosshair while placing", () => {
    const { chart, container } = bindAll();
    const state = LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    assert.equal(state.mode, "ALARM_PLACING");
    assert.equal(state.alarmMode, true);
    assert.equal(container.style.cursor, "crosshair");
    assert.deepEqual(chart.calls, [
      { handleScroll: false, handleScale: false },
    ]);
  });

  it("is idempotent: a repeated mode op does not re-apply options", () => {
    const { chart } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    assert.equal(chart.calls.length, 1);
    assert.equal(LwGestures.state().mode, "ALARM_PLACING");
  });

  it("restores the cursor and both library handles on the way out", () => {
    const { chart, container } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    const state = LwGestures.applyRouterOp({ op: "reset_view" });
    assert.equal(state.mode, "IDLE");
    assert.equal(container.style.cursor, "");
    assert.deepEqual(chart.calls, [
      { handleScroll: false, handleScale: false },
      { handleScroll: true, handleScale: true },
    ]);
    assert.equal(LwGestures.state().panZoomSuppressed, false);
  });

  it("leaving by any mode op clears the preview", () => {
    const { handlers, alarms } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.equal(LwGestures.state().previewPrice, 110);
    LwGestures.applyRouterOp({ mode: "DRAWING" });
    assert.equal(LwGestures.state().previewPrice, null);
    assert.ok(alarms.seen.cleared >= 1);
  });
});

describe("pointer gestures", () => {
  it("maps client Y to a price through the live series", () => {
    const { handlers } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    assert.equal(handlers.pointermove({ clientX: 400, clientY: 150 }), true);
    // container top 50 -> pane-local 100 -> 100 + 100/10
    assert.equal(LwGestures.state().previewPrice, 110);
  });

  it("pointermove draws the preview through LwAlarms.showPreview", () => {
    const { handlers, alarms } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.deepEqual(alarms.seen.previews, [110]);
    assert.equal(alarms.seen.cleared, 0);
  });

  it("a click reports the clicked price once and clears the preview", () => {
    const { handlers, alarms } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointerdown({ clientX: 400, clientY: 150 });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.equal(handlers.pointerup({ clientX: 400, clientY: 150 }), true);
    assert.deepEqual(alarms.seen.created.map((c) => c.price), [110]);
    assert.equal(LwGestures.state().previewPrice, null);
    assert.ok(alarms.seen.cleared >= 1);
  });

  it("a drag beyond 3 px creates nothing", () => {
    const { handlers, alarms } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointerdown({ clientX: 400, clientY: 150 });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.equal(handlers.pointerup({ clientX: 400, clientY: 200 }), false);
    assert.deepEqual(alarms.seen.created, []);
    assert.equal(LwGestures.state().previewPrice, null);
  });

  it("never creates outside ALARM_PLACING", () => {
    const { handlers, alarms } = bindAll();
    handlers.pointerdown({ clientX: 400, clientY: 150 });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.equal(handlers.pointerup({ clientX: 400, clientY: 150 }), false);
    assert.deepEqual(alarms.seen.previews, []);
    assert.deepEqual(alarms.seen.created, []);
  });

  it("also creates nothing after the mode is disarmed", () => {
    const { handlers, alarms } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointerdown({ clientX: 400, clientY: 150 });
    handlers.pointerup({ clientX: 400, clientY: 150 });
    LwGestures.applyRouterOp({ op: "reset_view" });
    handlers.pointerdown({ clientX: 400, clientY: 150 });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    handlers.pointerup({ clientX: 400, clientY: 150 });
    assert.equal(alarms.seen.created.length, 1, "only the armed click created");
  });

  it("pointerleave clears the preview only after the 250 ms grace", () => {
    const { handlers, alarms, timers } = bindAll();
    LwGestures.applyRouterOp({ mode: "ALARM_PLACING" });
    handlers.pointermove({ clientX: 400, clientY: 150 });
    assert.equal(handlers.pointerleave(), true);
    assert.equal(timers.pending.length, 1);
    assert.equal(timers.pending[0].ms, LwGestures.LEAVE_GRACE_MS);
    assert.equal(LwGestures.state().previewPrice, 110, "grace period keeps it");
    timers.pending[0].fn();
    assert.equal(LwGestures.state().previewPrice, null);
    assert.ok(alarms.seen.cleared >= 1);
  });
});

describe("alarms.js preview wrappers (Q-32)", () => {
  const LwAlarms = require("./alarms.js");

  it("exposes showPreview / clearPreview", () => {
    assert.equal(typeof LwAlarms.showPreview, "function");
    assert.equal(typeof LwAlarms.clearPreview, "function");
  });

  it("builds the same two ops the Python preview publishes", () => {
    assert.deepEqual(LwAlarms.previewOp(123.45), {
      op: "set_alarm_preview",
      series: "alarms",
      price: 123.45,
    });
    assert.deepEqual(LwAlarms.clearPreviewOp(), {
      op: "clear_alarm_preview",
      series: "alarms",
    });
    assert.equal(LwAlarms.validateOp(LwAlarms.previewOp(123.45)), null);
    assert.equal(LwAlarms.validateOp(LwAlarms.clearPreviewOp()), null);
  });

  it("rejects a non-finite price instead of drawing a NaN line", () => {
    assert.equal(LwAlarms.showPreview(NaN), false);
    assert.equal(LwAlarms.showPreview("110"), false);
  });

  it("draws and clears the preview through its own applyOp", () => {
    const lines = [];
    const series = {
      createPriceLine(options) {
        const handle = { options };
        lines.push(handle);
        return handle;
      },
      removePriceLine(handle) {
        lines.splice(lines.indexOf(handle), 1);
      },
    };
    LwAlarms.bind(null, series);
    assert.equal(LwAlarms.showPreview(101.5), true);
    assert.equal(lines.length, 1);
    assert.equal(lines[0].options.price, 101.5);
    assert.equal(lines[0].options.color, LwAlarms.PREVIEW_COLOR);
    assert.equal(LwAlarms.snapshot().preview.price, 101.5);
    assert.equal(LwAlarms.clearPreview(), true);
    assert.equal(lines.length, 0);
    assert.equal(LwAlarms.snapshot().preview, null);
    LwAlarms.clear();
  });
});
