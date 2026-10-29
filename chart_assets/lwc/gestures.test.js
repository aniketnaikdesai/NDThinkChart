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
    // Q-33: a drawing anchor needs the page's own time axis. `logicalAt`
    // subtracts the container's left edge and asks this scale.
    timeScale() {
      return {
        coordinateToLogical(x) {
          return Number(x) / 10;
        },
      };
    },
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

// ---------------------------------------------------------------------------
// Q-33 — the drawing half. Same fake glue as above, plus a primitives stub so
// the draft/commit path is observable without the renderer.
// ---------------------------------------------------------------------------

function fakePrimitives() {
  const seen = { drafts: [], committed: [], cleared: 0 };
  let draft = null;
  return {
    seen,
    setDraft(item) {
      draft = item ? JSON.parse(JSON.stringify(item)) : null;
      seen.drafts.push(draft);
      return true;
    },
    clearDraft() {
      draft = null;
      seen.cleared += 1;
      return true;
    },
    snapshot() {
      return { draft };
    },
    commitDrawing(item) {
      seen.committed.push(JSON.parse(JSON.stringify(item)));
      return true;
    },
  };
}

function drawingGlue(primitives) {
  const glue = bindAll({ primitives });
  return glue;
}

function armTool(glue, tool) {
  LwGestures.applyRouterOp({ op: "router_mode", mode: "DRAWING", tool });
}

describe("gestures.js — drawing tool arming", () => {
  it("suppresses pan/zoom and sets the crosshair while a tool is armed", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    armTool(glue, "trendline");
    assert.equal(glue.container.style.cursor, "crosshair");
    const state = LwGestures.state();
    assert.equal(state.mode, "DRAWING");
    assert.equal(state.tool, "trendline");
    assert.equal(state.panZoomSuppressed, true);
  });

  it("restores pan/zoom and the cursor on the cursor tool", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    armTool(glue, "trendline");
    LwGestures.applyRouterOp({ op: "router_mode", mode: "IDLE", tool: "cursor" });
    assert.equal(glue.container.style.cursor, "");
    assert.equal(LwGestures.state().panZoomSuppressed, false);
  });
});

describe("gestures.js — drawing geometry", () => {
  it("builds a trendline item from two anchors", () => {
    const item = LwGestures.drawingItem(
      "trendline", { frac: 1.5, price: 100 }, { frac: 9.5, price: 110 });
    assert.equal(item.kind, "trendline");
    assert.deepEqual(item.points, [[1.5, 100], [9.5, 110]]);
    assert.equal(item.id, null);
    assert.equal(item.selected, false);
  });

  it("normalises a zone's span and prices", () => {
    const item = LwGestures.drawingItem(
      "zone", { frac: 9.0, price: 120 }, { frac: 2.0, price: 100 });
    assert.deepEqual(item.span, [2.0, 9.0]);
    assert.equal(item.y1, 100);
    assert.equal(item.y2, 120);
  });

  it("marks a horizontal line from the press price alone", () => {
    const item = LwGestures.drawingItem(
      "horizontal", { frac: 3.0, price: 101.25 }, null);
    assert.equal(item.price, 101.25);
    assert.equal(item.points, undefined);
  });

  it("gives fibonacci retracement levels and a measure its delta", () => {
    const fib = LwGestures.drawingItem(
      "fibonacci", { frac: 0, price: 100 }, { frac: 10, price: 120 });
    assert.equal(fib.type, "retr");
    assert.ok(Array.isArray(fib.levels) && fib.levels.length >= 3);
    const measure = LwGestures.drawingItem(
      "measure", { frac: 0, price: 100 }, { frac: 10, price: 110 });
    assert.equal(measure.delta.dy, 10);
    assert.equal(measure.delta.pct, 10);
  });

  it("refuses a half-built item (null anchor)", () => {
    assert.equal(LwGestures.drawingItem("trendline", { frac: 0, price: 100 }, null), null);
    assert.equal(LwGestures.drawingItem("trendline", null, { frac: 1, price: 1 }), null);
    assert.equal(LwGestures.drawingItem("nonsense", { frac: 0, price: 1 }, { frac: 1, price: 2 }), null);
  });
});

describe("gestures.js — draft, commit, and the 3 px threshold", () => {
  it("shows the draft while dragging and commits it on release", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    armTool(glue, "trendline");

    glue.handlers.pointerdown({ clientX: 100, clientY: 450, button: 0 });
    glue.handlers.pointermove({ clientX: 300, clientY: 400 });
    assert.ok(primitives.seen.drafts.some((d) => d && d.kind === "trendline"),
      "no live draft while dragging");

    glue.handlers.pointerup({ clientX: 300, clientY: 400 });
    assert.equal(primitives.seen.committed.length, 1);
    assert.equal(primitives.seen.committed[0].kind, "trendline");
    assert.equal(LwGestures.state().draft, null, "the draft survived the commit");
    assert.equal(LwGestures.state().tool, "trendline",
      "the tool must stay armed after a commit");
  });

  it("discards a drag shorter than the threshold", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    armTool(glue, "zone");

    glue.handlers.pointerdown({ clientX: 200, clientY: 300, button: 0 });
    glue.handlers.pointerup({ clientX: 202, clientY: 301 });
    assert.equal(primitives.seen.committed.length, 0);
  });

  it("commits a horizontal line on a click with no movement", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    armTool(glue, "horizontal");

    glue.handlers.pointerdown({ clientX: 200, clientY: 300, button: 0 });
    glue.handlers.pointerup({ clientX: 200, clientY: 300 });
    assert.equal(primitives.seen.committed.length, 1);
    assert.equal(primitives.seen.committed[0].kind, "horizontal");
  });

  it("does nothing outside the drawing modes", () => {
    const primitives = fakePrimitives();
    const glue = drawingGlue(primitives);
    LwGestures.applyRouterOp({ op: "router_mode", mode: "IDLE", tool: "cursor" });

    glue.handlers.pointerdown({ clientX: 100, clientY: 200, button: 0 });
    glue.handlers.pointermove({ clientX: 400, clientY: 300 });
    glue.handlers.pointerup({ clientX: 400, clientY: 300 });
    assert.equal(primitives.seen.committed.length, 0);
  });
});

// ---------------------------------------------------------------------------
// P9-T4 (S-P9-1 / finding 3.1) — the active draw group travels into the
// commit payload: setActiveGroup is the single writer, drawingItem stamps
// the group ID plus color, and an ungrouped tool keeps the default color
// with a null group.
// ---------------------------------------------------------------------------

describe("gestures.js — active draw group (P9-T4)", () => {
  const anchors = () => [
    { frac: 1.5, price: 100 },
    { frac: 9.5, price: 110 },
  ];

  it("stamps the active group ID and color into new items", () => {
    LwGestures.reset();
    LwGestures.setActiveGroup(7, "#ff0000");
    const [first, second] = anchors();
    const item = LwGestures.drawingItem("trendline", first, second);
    assert.equal(item.group_id, 7);
    assert.equal(item.color, "#ff0000");
  });

  it("keeps the default color and a null group when ungrouped", () => {
    LwGestures.reset();
    LwGestures.setActiveGroup(7, "#ff0000");
    LwGestures.setActiveGroup(null, null);
    const [first, second] = anchors();
    const item = LwGestures.drawingItem("trendline", first, second);
    assert.equal(item.group_id, null);
    // The shipped default (mirrors DEFAULT_DRAWING_COLOR in gestures.js).
    assert.equal(item.color, "#38bdf8");
  });

  it("starts ungrouped after a reset", () => {
    LwGestures.reset();
    const [first, second] = anchors();
    const item = LwGestures.drawingItem("trendline", first, second);
    assert.equal(item.group_id, null);
    assert.equal(item.color, "#38bdf8");
  });

  it("applies a set_active_group router op into new items", () => {
    LwGestures.reset();
    LwGestures.applyRouterOp({
      op: "set_active_group", group_id: 12, color: "#00ff00",
    });
    const [first, second] = anchors();
    const item = LwGestures.drawingItem("trendline", first, second);
    assert.equal(item.group_id, 12);
    assert.equal(item.color, "#00ff00");
  });

  it("rejects a junk group ID instead of stamping it", () => {
    LwGestures.reset();
    LwGestures.setActiveGroup("not-a-group", "#ff0000");
    const [first, second] = anchors();
    const item = LwGestures.drawingItem("trendline", first, second);
    assert.equal(item.group_id, null);
    assert.equal(item.color, "#38bdf8");
  });
});

// ---------------------------------------------------------------------------
// P10-T2 (D50.1) — page drag initiation: body whole-move plus per-kind
// anchor drags, locked never-start, commit/cancel.
//
// Harness geometry (same fakes as above): frac = clientX / 10,
// price = 100 + (clientY - 50) / 10. The fake primitives stand in for the
// engine (snapshot / handlePoints / dragItem / reportDrawingUpdate) and the
// fake drag surface stands in for the `drag_drawing` validation surface:
// every per-move delta must be addressed to its
// (id, kind, point_index, d_frac, d_price, body) signature.
// ---------------------------------------------------------------------------

/* Engine double: holds wire items (never mutated mid-drag — the preview
 * rides the draft only), answers the selection/handles/drag/commit calls
 * the initiation path uses, and records every commit. */
function fakeDragPrimitives(items) {
  const stored = JSON.parse(JSON.stringify(items));
  const seen = { drafts: [], cleared: 0, updates: [] };
  const surface = {
    calls: [],
    dragDrawing(id, kind, point_index, d_frac, d_price, body) {
      surface.calls.push([id, kind, point_index, d_frac, d_price, body]);
      return true;
    },
  };
  function moveItem(start, point_index, d_frac, d_price, body) {
    const moved = JSON.parse(JSON.stringify(start));
    const shift = (pair) => [pair[0] + d_frac, pair[1] + d_price];
    if (moved.kind === "horizontal") {
      moved.price = moved.price + d_price;
      moved.handles = [[null, moved.price]];
      return moved;
    }
    if (moved.kind === "zone") {
      if (body) {
        moved.span = [moved.span[0] + d_frac, moved.span[1] + d_frac];
        moved.y1 = moved.y1 + d_price;
        moved.y2 = moved.y2 + d_price;
      } else if (point_index === 0) {
        moved.span = [moved.span[0] + d_frac, moved.span[1]];
        moved.y1 = moved.y1 + d_price;
      } else {
        moved.span = [moved.span[0], moved.span[1] + d_frac];
        moved.y2 = moved.y2 + d_price;
      }
      moved.handles = [
        [moved.span[0], moved.y1],
        [moved.span[1], moved.y2],
      ];
      return moved;
    }
    // trendline / fibonacci / measure: two-point anchors.
    if (body) {
      moved.points = moved.points.map(shift);
    } else {
      moved.points = moved.points.map((p, i) =>
        i === point_index ? shift(p) : p.slice());
    }
    moved.handles = moved.points.map((p) => p.slice());
    if (moved.kind === "measure") {
      const dy = moved.points[1][1] - moved.points[0][1];
      moved.delta = {
        dy,
        pct: moved.points[0][1] ? (dy / moved.points[0][1]) * 100 : 0,
      };
    }
    return moved;
  }
  return {
    seen,
    surface,
    stored,
    setDraft(item) {
      seen.drafts.push(item ? JSON.parse(JSON.stringify(item)) : null);
      return true;
    },
    clearDraft() {
      seen.cleared += 1;
      return true;
    },
    snapshot() {
      return { items: stored, selectedId: null };
    },
    handlePoints(kind, item) {
      return Array.isArray(item.handles) ?
        item.handles.map((h) => h.slice()) : [];
    },
    dragItem(start, point_index, d_frac, d_price, body) {
      return moveItem(start, point_index, d_frac, d_price, body);
    },
    reportDrawingUpdate(moved, bridge) {
      seen.updates.push({
        item: JSON.parse(JSON.stringify(moved)),
        bridge,
      });
      return true;
    },
  };
}

/* One selected wire item per kind. Endpoints sit on the fake grid so a
 * press lands exactly: frac = clientX / 10, price = 100 + (clientY-50)/10. */
function dragWireItems(locked) {
  const base = (extra) => Object.assign({
    id: null,
    color: "#38bdf8",
    group_id: null,
    locked: !!locked,
    selected: true,
    z: 10,
  }, extra);
  return [
    base({ id: 11, kind: "trendline", points: [[20, 110], [40, 120]], handles: [[20, 110], [40, 120]] }),
    base({ id: 12, kind: "fibonacci", points: [[20, 110], [40, 120]], handles: [[20, 110], [40, 120]], type: "retr" }),
    base({ id: 13, kind: "measure", points: [[20, 110], [40, 120]], handles: [[20, 110], [40, 120]], delta: { dy: 10, pct: 10 } }),
    base({ id: 14, kind: "zone", span: [20, 40], y1: 105, y2: 125, handles: [[20, 105], [40, 125]] }),
    base({ id: 15, kind: "horizontal", price: 115, handles: [[null, 115]] }),
  ];
}

/* Body presses: the two-point midpoint (frac 30, price 115), the zone
 * interior, and — for horizontal — 10 px off the level (outside the 6 px
 * handle grab but inside the 12 px body grab). */
function bodyPressFor(kind) {
  if (kind === "horizontal") return { clientX: 100, clientY: 210 };
  return { clientX: 300, clientY: 200 };
}

/* Handle presses: endpoint 0 (frac 20, price 110), zone corner 0
 * (frac 20, price 105), the horizontal price level. */
function handlePressFor(kind) {
  if (kind === "zone") return { clientX: 200, clientY: 100 };
  if (kind === "horizontal") return { clientX: 100, clientY: 200 };
  return { clientX: 200, clientY: 150 };
}

describe("gestures.js — drag initiation (P10-T2-T21)", () => {
  it("starts a whole-move on a body press for all five kinds", () => {
    for (const wire of dragWireItems(false)) {
      const prim = fakeDragPrimitives([wire]);
      const glue = bindAll({ primitives: prim, drag: prim.surface });
      const press = bodyPressFor(wire.kind);
      assert.equal(glue.handlers.pointerdown(press), true,
        `${wire.kind}: a body press starts a drag`);
      const session = LwGestures.dragState();
      assert.ok(session, `${wire.kind}: a drag session is in flight`);
      assert.equal(session.body, true, `${wire.kind}: body whole-move`);
      assert.equal(session.point_index, -1, `${wire.kind}: no anchor addressed`);
      assert.equal(session.id, wire.id);
      assert.equal(session.kind, wire.kind);
      // One per-move tick is addressed to the drag_drawing validation
      // surface: (id, kind, point_index, d_frac, d_price, body).
      assert.equal(
        glue.handlers.pointermove(
          { clientX: press.clientX + 10, clientY: press.clientY + 10 }), true);
      const last = prim.surface.calls[prim.surface.calls.length - 1];
      assert.deepEqual(last, [wire.id, wire.kind, -1, 1, 1, true],
        `${wire.kind}: the whole-move delta is addressed to the body`);
      assert.equal(LwGestures.cancelDrag(), true, "cleanup");
    }
  });

  it("starts the kind's anchor drag on a handle press", () => {
    for (const wire of dragWireItems(false)) {
      const prim = fakeDragPrimitives([wire]);
      const glue = bindAll({ primitives: prim, drag: prim.surface });
      const press = handlePressFor(wire.kind);
      assert.equal(glue.handlers.pointerdown(press), true,
        `${wire.kind}: a handle press starts a drag`);
      const session = LwGestures.dragState();
      assert.ok(session, `${wire.kind}: a drag session is in flight`);
      assert.equal(session.body, false, `${wire.kind}: anchor drag, not a move`);
      assert.equal(session.point_index, 0, `${wire.kind}: the handle anchor`);
      assert.equal(
        glue.handlers.pointermove(
          { clientX: press.clientX + 10, clientY: press.clientY + 10 }), true);
      const last = prim.surface.calls[prim.surface.calls.length - 1];
      assert.deepEqual(last, [wire.id, wire.kind, 0, 1, 1, false],
        `${wire.kind}: the anchor delta is addressed to the handle`);
      assert.equal(LwGestures.cancelDrag(), true, "cleanup");
    }
  });

  it("addresses the zone's second corner to its own anchor", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "zone");
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    // Corner 1: frac 40, price 125.
    assert.equal(
      glue.handlers.pointerdown({ clientX: 400, clientY: 300 }), true);
    const session = LwGestures.dragState();
    assert.equal(session.body, false);
    assert.equal(session.point_index, 1);
    assert.equal(LwGestures.cancelDrag(), true, "cleanup");
  });
});

describe("gestures.js — locked drawings never start a drag (P10-T2-T22)", () => {
  it("refuses body and handle presses on a locked drawing of every kind", () => {
    for (const wire of dragWireItems(true)) {
      for (const press of [bodyPressFor(wire.kind), handlePressFor(wire.kind)]) {
        const prim = fakeDragPrimitives([wire]);
        const glue = bindAll({ primitives: prim, drag: prim.surface });
        assert.equal(glue.handlers.pointerdown(press), false,
          `${wire.kind}: a locked press starts nothing`);
        assert.equal(LwGestures.dragState(), null,
          `${wire.kind}: no drag session starts`);
        assert.deepEqual(prim.surface.calls, [],
          `${wire.kind}: nothing routed to validation`);
        assert.deepEqual(prim.seen.updates, [],
          `${wire.kind}: nothing emitted`);
      }
    }
  });
});

describe("gestures.js — drag commit and cancel (P10-T2-T23)", () => {
  it("commits the dragged geometry on pointer-up past the threshold", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.equal(glue.handlers.pointermove({ clientX: 310, clientY: 210 }), true);
    assert.equal(glue.handlers.pointerup({ clientX: 310, clientY: 210 }), true);
    assert.equal(prim.seen.updates.length, 1, "one commit emitted");
    const committed = prim.seen.updates[0].item;
    assert.equal(committed.id, wire.id);
    assert.deepEqual(committed.points, [[21, 111], [41, 121]],
      "the commit carries the dragged geometry");
    assert.deepEqual(
      prim.surface.calls[prim.surface.calls.length - 1],
      [wire.id, "trendline", -1, 1, 1, true]);
    assert.deepEqual(prim.stored, [before],
      "the engine state was never mutated mid-drag");
    assert.equal(LwGestures.dragState(), null, "no session lingers");
  });

  it("emits nothing on cancel and keeps the pre-drag state", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.equal(glue.handlers.pointermove({ clientX: 310, clientY: 210 }), true);
    assert.ok(prim.seen.drafts.length >= 1, "a preview rode the draft");
    assert.equal(LwGestures.cancelDrag(), true);
    assert.equal(LwGestures.dragState(), null);
    assert.deepEqual(prim.seen.updates, [], "cancel emits no commit");
    assert.deepEqual(prim.stored, [before],
      "the item matches its pre-drag state");
    assert.ok(prim.seen.cleared >= 1, "the draft preview was cleared");
  });
});

// ---------------------------------------------------------------------------
// ESC-091 — an orphaned in-flight drag never commits: a drag whose
// pointer-up happens off-canvas must not commit stale geometry on a later
// unrelated pan. Guard: orphan a drag (press, move, pointerup-less leave,
// then an unrelated pan) and assert no drawingUpdated is emitted and the
// draft is cleared. The T21/T23 suites above are untouched.
// ---------------------------------------------------------------------------

describe("gestures.js — orphaned drag never commits (ESC-091)", () => {
  it("ignores moves that arrive with the button released", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.ok(LwGestures.dragState(), "a drag session is in flight");
    // The button is up (its pointer-up happened off-canvas and never
    // reached us): the move is not drag travel.
    assert.equal(
      glue.handlers.pointermove({ clientX: 310, clientY: 210, buttons: 0 }), false);
    assert.deepEqual(prim.surface.calls, [], "nothing routed to validation");
    const session = LwGestures.dragState();
    assert.ok(session, "the session is still open (leave/cancel abandons it)");
    assert.equal(session.moved, false);
    assert.deepEqual([session.d_frac, session.d_price], [0, 0]);
    // The later pointer-up is a click, not a commit.
    assert.equal(glue.handlers.pointerup({ clientX: 310, clientY: 210 }), false);
    assert.deepEqual(prim.seen.updates, [], "no commit emitted");
    assert.deepEqual(prim.stored, [before]);
    assert.equal(LwGestures.dragState(), null);
  });

  it("abandons the drag past the leave grace and never commits a later pan", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.equal(
      glue.handlers.pointermove({ clientX: 310, clientY: 210, buttons: 1 }), true);
    assert.equal(LwGestures.dragState().moved, true);
    // The pointer leaves with the button still down; no pointer-up follows.
    assert.equal(glue.handlers.pointerleave(), true);
    assert.ok(LwGestures.dragState(), "grace period keeps the session");
    const pending = glue.timers.pending;
    assert.ok(pending.length >= 1);
    assert.equal(pending[pending.length - 1].ms, LwGestures.LEAVE_GRACE_MS);
    pending[pending.length - 1].fn();
    assert.equal(LwGestures.dragState(), null, "the orphaned drag is abandoned");
    assert.deepEqual(prim.seen.updates, [], "abandon emits nothing");
    assert.ok(prim.seen.cleared >= 1, "the draft preview was cleared");
    // An unrelated pan afterwards commits nothing stale.
    assert.equal(glue.handlers.pointerdown({ clientX: 700, clientY: 500 }), false);
    assert.equal(
      glue.handlers.pointermove({ clientX: 720, clientY: 520, buttons: 1 }), false);
    assert.equal(glue.handlers.pointerup({ clientX: 720, clientY: 520 }), false);
    assert.deepEqual(prim.seen.updates, [], "no stale commit");
    assert.equal(LwGestures.dragState(), null);
    assert.deepEqual(prim.stored, [before]);
  });

  it("pointercancel abandons the drag and emits nothing", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.equal(
      glue.handlers.pointermove({ clientX: 310, clientY: 210, buttons: 1 }), true);
    assert.equal(glue.handlers.pointercancel(), true);
    assert.equal(LwGestures.dragState(), null);
    assert.deepEqual(prim.seen.updates, [], "cancel emits no commit");
    assert.ok(prim.seen.cleared >= 1, "the draft preview was cleared");
    assert.equal(glue.handlers.pointerup({ clientX: 310, clientY: 210 }), false);
    assert.deepEqual(prim.seen.updates, [], "no late commit");
    assert.deepEqual(prim.stored, [before]);
  });

  it("a non-hit press clears a stale session instead of committing it later", () => {
    const wire = dragWireItems(false).find((w) => w.kind === "trendline");
    const before = JSON.parse(JSON.stringify(wire));
    const prim = fakeDragPrimitives([wire]);
    const glue = bindAll({ primitives: prim, drag: prim.surface });
    assert.equal(glue.handlers.pointerdown({ clientX: 300, clientY: 200 }), true);
    assert.equal(
      glue.handlers.pointermove({ clientX: 310, clientY: 210, buttons: 1 }), true);
    assert.ok(LwGestures.dragState().moved);
    // The pointer-up outside the container never arrives; the next press
    // misses the drawing entirely.
    assert.equal(glue.handlers.pointerdown({ clientX: 700, clientY: 500 }), false);
    assert.equal(LwGestures.dragState(), null, "the stale session is cleared");
    assert.ok(prim.seen.cleared >= 1, "the draft preview was cleared");
    assert.equal(glue.handlers.pointerup({ clientX: 700, clientY: 500 }), false);
    assert.deepEqual(prim.seen.updates, [], "no stale commit");
    assert.deepEqual(prim.stored, [before]);
  });
});
