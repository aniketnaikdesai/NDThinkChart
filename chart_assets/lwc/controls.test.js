// controls.test.js — D101 page-glue suite (P30-01).
//
// Boots the REAL chart.js + interaction.js against this file's own minimal
// stub document (no npm, no network, no jsdom) and drives the restored
// control cluster end to end: init mounts it once, a zoom click moves the
// page's own viewport exactly once and reports once, Reset re-frames a
// panned series, and the interaction channel's durable mode op drives the
// magnifier's latch.
//
// The shipped chart.test.js harness is deliberately NOT touched (AR-P30-7):
// this file builds a per-id element map instead of that suite's one shared
// fake element.

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const HTML = readFileSync(path.join(__dirname, "chart.html"), "utf8");
const PAGE_WIDTH = 400;
const PAGE_HEIGHT = 300;
const PRICE_SCALE_ALLOWANCE_PX = 70; // chart.js:410

// ── stub environment ────────────────────────────────────────────────────────

function fakeButton() {
  const attrs = {};
  const listeners = {};
  return {
    tagName: "BUTTON",
    id: "",
    textContent: "",
    hidden: false,
    style: {},
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
    fire(type, ev) {
      (listeners[type] || []).forEach((fn) => fn(ev || {}));
    },
  };
}

function recordingBridge() {
  const calls = { controlPressed: [], zoomRefused: [], keyPressed: [] };
  return {
    calls,
    controlPressed(payload) {
      calls.controlPressed.push(JSON.parse(payload));
    },
    zoomRefused(payload) {
      calls.zoomRefused.push(JSON.parse(payload));
    },
    keyPressed(payload) {
      calls.keyPressed.push(JSON.parse(payload));
    },
  };
}

// One page load: a fresh document, fake library tree and the real glue.
function boot() {
  const scale = { range: null, count: 0 };
  const calls = { range: [], fitContent: 0 };
  const els = {};

  function series() {
    return {
      _rows: [],
      setData(rows) {
        this._rows = rows;
        scale.count = rows.length;
        scale.range = rows.length
          ? { from: 0, to: rows.length - 1 }
          : null;
      },
      update(row) {
        const last = this._rows.length
          ? this._rows[this._rows.length - 1].time
          : null;
        if (row && (last === null || row.time > last)) {
          this._rows.push(row);
          scale.count = this._rows.length;
        } else if (row && last !== null && row.time === last) {
          this._rows[this._rows.length - 1] = row;
        }
      },
      applyOptions() {},
    };
  }

  const timeScale = {
    getVisibleLogicalRange() {
      return scale.range
        ? { from: scale.range.from, to: scale.range.to }
        : null;
    },
    setVisibleLogicalRange(range) {
      scale.range = { from: Number(range.from), to: Number(range.to) };
      calls.range.push({ from: scale.range.from, to: scale.range.to });
    },
    getVisibleRange() {
      return null;
    },
    fitContent() {
      calls.fitContent += 1;
      if (scale.count > 0) {
        scale.range = { from: 0, to: scale.count - 1 };
      }
    },
    applyOptions() {},
    options() {
      return {};
    },
  };

  const fakeChart = {
    timeScale() {
      return timeScale;
    },
    addSeries() {
      return series();
    },
    addCandlestickSeries() {
      return series();
    },
    addLineSeries() {
      return series();
    },
    addAreaSeries() {
      return series();
    },
    addHistogramSeries() {
      return series();
    },
    priceScale() {
      return { applyOptions() {} };
    },
    resize() {},
    fitContent() {
      calls.fitContent += 1;
      if (scale.count > 0) {
        scale.range = { from: 0, to: scale.count - 1 };
      }
    },
    applyOptions() {},
    options() {
      return {};
    },
  };

  const chartEl = {
    tagName: "DIV",
    clientWidth: PAGE_WIDTH,
    clientHeight: PAGE_HEIGHT,
    listeners: {},
    addEventListener(type, fn) {
      (this.listeners[type] = this.listeners[type] || []).push(fn);
    },
    fire(type, ev) {
      (this.listeners[type] || []).forEach((fn) => fn(ev || {}));
    },
    appendChild() {},
    getBoundingClientRect() {
      return { width: PAGE_WIDTH, height: PAGE_HEIGHT, top: 0, left: 0 };
    },
  };
  const chevron = fakeButton();
  chevron.id = "goToLatest";
  const controls = {
    children: [],
    appendChild(child) {
      this.children.push(child);
      els[child.id] = child;
    },
  };
  els.chart = chartEl;
  els.goToLatest = chevron;
  els.controls = controls;

  const documentStub = {
    readyState: "complete",
    title: "",
    documentElement: {
      clientWidth: PAGE_WIDTH,
      clientHeight: PAGE_HEIGHT,
    },
    createElement(tag) {
      return fakeButton(tag);
    },
    getElementById(id) {
      return els[id] || null;
    },
    addEventListener() {},
  };

  const windowStub = {};
  globalThis.document = documentStub;
  globalThis.window = windowStub;
  globalThis.LightweightCharts = {
    createChart() {
      return fakeChart;
    },
    createSeriesMarkers() {
      return { setMarkers() {} };
    },
    CandlestickSeries: {},
    LineSeries: {},
    AreaSeries: {},
    HistogramSeries: {},
  };
  windowStub.LwEnvelope = require("./envelope.js");
  windowStub.LwInteraction = require("./interaction.js");
  const bridge = recordingBridge();
  windowStub.lwBridge = bridge;

  // A real reload: drop the glue from the require cache so its module state
  // (chart, series, follow flags) starts fresh against the new document.
  delete require.cache[require.resolve("./chart.js")];
  require("./chart.js"); // boots and publishes the window.lw* probe surface
  const page = windowStub;

  return { page, els, calls, scale, bridge, windowStub, documentStub };
}

function seedBars(page, n) {
  const ts = [];
  const open = [];
  const high = [];
  const low = [];
  const close = [];
  for (let i = 0; i < n; i++) {
    ts.push(1700000000 + i * 300);
    open.push(100 + i * 0.1);
    high.push(100 + i * 0.1 + 0.25);
    low.push(100 + i * 0.1 - 0.25);
    close.push(100 + i * 0.1 + 0.05);
  }
  const result = page.lwApplyOps({
    v: 1,
    ops: [{ op: "set_bars", series: "candles", cols: { ts, open, high, low, close } }],
  });
  assert.equal(result.error, null, "seed envelope applies");
}

const ids = (els) => els.controls.children.map((btn) => btn.id);

// ── (a) mount + no chart area lost (AC-D101.1, R186) ────────────────────────

test("(a) init mounts the four mirror controls once in order", () => {
  const { els } = boot();
  assert.deepEqual(ids(els), [
    "control-zoom-out",
    "control-zoom-in",
    "control-magnifier",
    "control-reset",
  ]);
  assert.equal(els["control-magnifier"].getAttribute("aria-pressed"), "false");
});

test("(a) #chart keeps the full viewport; the strip sits in the gutter", () => {
  const { els, documentStub } = boot();
  assert.equal(els.chart.clientWidth, documentStub.documentElement.clientWidth);
  assert.equal(els.chart.clientWidth, PAGE_WIDTH);
  assert.equal(els.chart.clientHeight, PAGE_HEIGHT);

  const chartRule = /#chart\s*\{([^}]*)\}/.exec(HTML);
  assert.ok(chartRule, "#chart rule exists");
  assert.match(chartRule[1], /width:\s*100%/);
  assert.match(chartRule[1], /height:\s*100%/);

  const controlsRule = /#controls\s*\{([^}]*)\}/.exec(HTML);
  assert.ok(controlsRule, "#controls rule exists");
  const right = /right:\s*(\d+)px/.exec(controlsRule[1]);
  assert.ok(right, "#controls is anchored to the right gutter");
  assert.ok(Number(right[1]) >= PRICE_SCALE_ALLOWANCE_PX,
    "the strip stays inside the reserved price-scale gutter");
});

// ── (b) a zoom click: one viewport change, one report (S-P30-1) ─────────────

test("(b) zoom-in narrows the range once by 0.8 and reports once", () => {
  const { page, els, calls, bridge } = boot();
  seedBars(page, 60);
  const before = page.lwVisibleRange().range;
  assert.ok(before);
  calls.range.length = 0;
  bridge.calls.controlPressed.length = 0;

  els["control-zoom-in"].click();

  const mid = (before.from + before.to) / 2;
  const half = ((before.to - before.from) / 2) * 0.8;
  assert.equal(calls.range.length, 1, "exactly one range change in the turn");
  assert.ok(Math.abs(calls.range[0].from - (mid - half)) < 1e-9);
  assert.ok(Math.abs(calls.range[0].to - (mid + half)) < 1e-9);
  assert.deepEqual(bridge.calls.controlPressed, [
    { control: "zoom-in", value: null },
  ]);
});

// ── (c) Reset re-frames a panned series (S-P30-1) ───────────────────────────

test("(c) reset re-frames the series and following returns", () => {
  const { page, els, calls, bridge } = boot();
  seedBars(page, 60);
  for (let i = 0; i < 6; i++) {
    els.chart.fire("keydown", { key: "ArrowLeft", preventDefault() {} });
  }
  assert.equal(page.lwIsFollowing(), false, "the pan moved the viewport away");
  const fitsBefore = calls.fitContent;

  els["control-reset"].click();

  assert.ok(calls.fitContent > fitsBefore, "Reset re-frames through fitToWidth");
  assert.equal(page.lwIsFollowing(), true);
  assert.deepEqual(bridge.calls.controlPressed.slice(-1), [
    { control: "reset", value: null },
  ]);
});

// ── (d)/(e) the durable mode drives the latch ────────────────────────────────

test("(d) interaction mode ops drive aria-pressed; a zoom op changes nothing", () => {
  const { page, els } = boot();
  const btn = els["control-magnifier"];

  let result = page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "router_mode", mode: "ZOOMING" }],
  });
  assert.equal(result.error, null);
  assert.equal(btn.getAttribute("aria-pressed"), "true");

  result = page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "reset_view", mode: "IDLE" }],
  });
  assert.equal(result.error, null);
  assert.equal(btn.getAttribute("aria-pressed"), "false");

  result = page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "zoom", step: 1 }],
  });
  assert.equal(result.error, null);
  assert.equal(btn.getAttribute("aria-pressed"), "false", "a zoom op is not state");
});

test("(e) a refused mode op never leaves the magnifier pressed", () => {
  const { page, els } = boot();
  const btn = els["control-magnifier"];

  page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "router_mode", mode: "ZOOMING" }],
  });
  assert.equal(btn.getAttribute("aria-pressed"), "true");

  page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "router_mode", mode: "ALARM_PLACING", refused: true }],
  });
  assert.equal(btn.getAttribute("aria-pressed"), "false",
    "the refused state is never advertised");

  // AR-P30-2: replaying the mode op is idempotent.
  page.lwApplyChannel("interaction", {
    v: 1,
    ops: [{ op: "router_mode", mode: "ALARM_PLACING", refused: true }],
  });
  assert.equal(btn.getAttribute("aria-pressed"), "false");
});

// ── (f) a second load mounts once; a second call appends nothing ────────────

test("(f) a fresh document mounts four; a second mount adds none", () => {
  const first = boot();
  assert.equal(first.els.controls.children.length, 4);

  const second = boot();
  assert.equal(second.els.controls.children.length, 4);

  const again = second.windowStub.LwInteraction.mountControls(
    second.els.controls,
    () => null,
  );
  assert.equal(again.length, 4);
  assert.equal(second.els.controls.children.length, 4);
});

// ── (g) FI-P30-1: a no-range press is a viewport no-op, never a refusal ────

test("(g) zoom-in with no visible range does nothing and reports once", () => {
  const { page, els, calls, bridge, scale } = boot();
  assert.equal(scale.range, null);
  calls.range.length = 0;
  bridge.calls.controlPressed.length = 0;
  bridge.calls.zoomRefused.length = 0;

  els["control-zoom-in"].click();

  assert.equal(scale.range, null, "no viewport change");
  assert.equal(calls.range.length, 0, "zoom() was not called");
  assert.equal(bridge.calls.zoomRefused.length, 0, "no fabricated refusal");
  assert.deepEqual(bridge.calls.controlPressed, [
    { control: "zoom-in", value: null },
  ]);
});
