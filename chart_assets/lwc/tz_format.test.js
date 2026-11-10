// tz_format.test.js — P22-T3 (D62 labels + D64 shared leg) page-formatter suite.
// Runs with the repo's node install, no npm deps, no network, no DOM.
// Covers the zone-aware ET formatter core (AC2), the live tz apply path
// (AC1: per-tick re-labels + flip-back restore), the shared crosshair /
// tooltip time path (AC3: same formatter by construction) and the
// toggle-only control matrix (AC4: equity + futures matrices, single
// formatter-mutation site, two-mode domain).
const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const DIR = __dirname;
const read = (name) => readFileSync(path.join(DIR, name), "utf8");

// Page harness: boot the real chart.js browser glue in-process against a
// stubbed document and a fake LightweightCharts 5.x tree. The fake captures
// the live formatter closures the apply re-applies (AC3 evidence) and
// records range re-assertions (the forced tick re-render), mirroring the
// chart.test.js page idiom.
const fakeState = { range: null, count: 0, tickFmt: null, timeFmt: null, ranges: [] };
function fakeTimeScale() {
  return {
    getVisibleLogicalRange() {
      const r = fakeState.range;
      return r ? { from: r.from, to: r.to } : null;
    },
    setVisibleLogicalRange(r) {
      fakeState.ranges.push({ from: Number(r.from), to: Number(r.to) });
      fakeState.range = { from: Number(r.from), to: Number(r.to) };
    },
    getVisibleRange() { return null; },
    fitContent() {
      if (fakeState.count > 0) {
        fakeState.range = { from: 0, to: fakeState.count - 1 };
      }
    },
    applyOptions(o) {
      if (o && typeof o.tickMarkFormatter === "function") {
        fakeState.tickFmt = o.tickMarkFormatter;
      }
    },
    options() { return { barSpacing: 8 }; },
  };
}
function fakeSeries() {
  return {
    _rows: [],
    setData(rows) {
      this._rows = rows;
      fakeState.count = rows.length;
      fakeState.range = { from: 0, to: rows.length - 1 };
    },
    update(row) {
      const last = this._rows.length ? this._rows[this._rows.length - 1].time : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        fakeState.count = this._rows.length;
      } else if (row && last !== null && row.time === last) {
        this._rows[this._rows.length - 1] = row;
      }
    },
    applyOptions() {},
  };
}
function fakeChart() {
  const scale = fakeTimeScale();
  return {
    timeScale() { return scale; },
    addSeries() { return fakeSeries(); },
    addCandlestickSeries() { return fakeSeries(); },
    addLineSeries() { return fakeSeries(); },
    addAreaSeries() { return fakeSeries(); },
    addHistogramSeries() { return fakeSeries(); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    applyOptions(o) {
      if (o && o.localization && typeof o.localization.timeFormatter === "function") {
        fakeState.timeFmt = o.localization.timeFormatter;
      }
    },
  };
}
const fakeEl = {
  clientWidth: 960,
  clientHeight: 850,
  _listeners: {},
  addEventListener(type, fn) { this._listeners[type] = fn; },
  getBoundingClientRect() {
    return { width: 960, height: 850, top: 0, left: 0 };
  },
};
globalThis.LightweightCharts = {
  createChart() { return fakeChart(); },
  CandlestickSeries: {},
  LineSeries: {},
  AreaSeries: {},
  HistogramSeries: {},
};
globalThis.document = {
  readyState: "complete",
  title: "",
  getElementById() { return fakeEl; },
  addEventListener() {},
};
globalThis.window = {};
for (const name of ["LwInteraction", "LwAlarms", "LwPrimitives",
  "LwOverlays", "LwStudies", "LwGestures"]) {
  globalThis.window[name] = { bind() {} };
}
const LwEnvelope = require("./envelope.js");
globalThis.window.LwEnvelope = LwEnvelope;
const LwChart = require("./chart.js");
const page = globalThis.window;

const utc = (y, mo, d, h, mi) => Math.floor(Date.UTC(y, mo - 1, d, h, mi) / 1000);

// Bars straddling the 2026-11-01 fall-back (EDT -> EST at 06:00 UTC):
// 04:30 UTC is 00:30 EDT, 06:30 UTC is 01:30 EST, 08:00 UTC is 03:00 EST.
// A fixed 5h scalar mislabels the EDT side by a full hour (wrong date).
const DST_TIMES = [utc(2026, 11, 1, 4, 30), utc(2026, 11, 1, 6, 30), utc(2026, 11, 1, 8, 0)];
const DST_ET = ["11/01 00:30", "11/01 01:30", "11/01 03:00"];
// Bars straddling the 2026-03-08 spring-forward (EST -> EDT at 07:00 UTC):
// 06:30 UTC is 01:30 EST, 07:30 UTC is 03:30 EDT (02:xx never existed).
// A fixed 4h scalar invents the nonexistent 02:30 on the EST side.
const SPRING_TIMES = [utc(2026, 3, 8, 6, 30), utc(2026, 3, 8, 7, 30)];
const SPRING_ET = ["03/08 01:30", "03/08 03:30"];

function seedBars(times) {
  const n = times.length;
  const same = (v) => times.map(() => v);
  const res = page.lwApplyOps({
    v: 1,
    ops: [{
      op: "set_bars", series: "candles",
      cols: { ts: times.slice(), open: same(100), high: same(101), low: same(99), close: same(100.5) },
    }],
  });
  assert.equal(res.error, null, "seed envelope applies");
}

function applyMode(mode) {
  return page.lwApplyChannel("interaction", {
    v: 1, channel: "interaction", ops: [{ op: "set_timezone", mode }],
  });
}

describe("P22-T3-AC2: DST date-correctness (formatter core)", () => {
  it("fall-back bars label date-correctly in ET mode (fixed 5h would mislabel)", () => {
    assert.deepEqual(DST_TIMES.map((t) => LwChart.etLabel(t)), DST_ET);
    // The discriminator: a fixed EST scalar is wrong on the EDT side.
    assert.equal(LwChart.tzLabel(DST_TIMES[0], 18000), "10/31 23:30");
    assert.notEqual(LwChart.tzLabel(DST_TIMES[0], 18000), LwChart.etLabel(DST_TIMES[0]));
    // ... and a fixed EDT scalar is wrong on the EST side.
    assert.equal(LwChart.tzLabel(DST_TIMES[2], 14400), "11/01 04:00");
    assert.notEqual(LwChart.tzLabel(DST_TIMES[2], 14400), LwChart.etLabel(DST_TIMES[2]));
  });

  it("spring-forward bars label date-correctly in ET mode (fixed 4h invents 02:30)", () => {
    assert.deepEqual(SPRING_TIMES.map((t) => LwChart.etLabel(t)), SPRING_ET);
    assert.equal(LwChart.tzLabel(SPRING_TIMES[0], 14400), "03/08 02:30");
    assert.notEqual(LwChart.tzLabel(SPRING_TIMES[0], 14400), LwChart.etLabel(SPRING_TIMES[0]));
  });

  it("UTC mode is plain UTC math through the scalar", () => {
    for (const t of [...DST_TIMES, ...SPRING_TIMES]) {
      assert.equal(LwChart.formatTickWith(t, "UTC", 0), LwChart.tzLabel(t, 0));
    }
    assert.equal(LwChart.formatTickWith(DST_TIMES[0], "UTC", 0), "11/01 04:30");
  });

  it("formatTickWith routes by mode and nothing else", () => {
    for (const t of DST_TIMES) {
      assert.equal(LwChart.formatTickWith(t, "Eastern Time"), LwChart.etLabel(t));
      assert.equal(LwChart.formatTickWith(t, "UTC", 0), LwChart.tzLabel(t, 0));
    }
  });
});

describe("P22-T3-AC1: live tz apply re-labels every tick (page path)", () => {
  beforeEach(() => { applyMode("UTC"); seedBars(DST_TIMES); fakeState.ranges.length = 0; });

  it("UTC flip labels every bar in UTC math; ET flip shifts each by its date-correct delta", () => {
    assert.equal(page.lwTzMode(), "UTC");
    assert.deepEqual(DST_TIMES.map((t) => page.lwFormatTick(t)),
      DST_TIMES.map((t) => LwChart.tzLabel(t, 0)));
    const res = applyMode("Eastern Time");
    assert.equal(res.error, null);
    assert.equal(page.lwTzMode(), "Eastern Time");
    assert.deepEqual(DST_TIMES.map((t) => page.lwFormatTick(t)), DST_ET);
    // The axis probe reports the active zone, not a recomputed guess.
    assert.equal(page.lwAxisProbe().tzMode, "Eastern Time");
    assert.equal(page.lwAxisProbe().firstLabel, page.lwFormatTick(DST_TIMES[0]));
  });

  it("flipping back restores the original labels exactly", () => {
    const before = DST_TIMES.map((t) => page.lwFormatTick(t));
    applyMode("Eastern Time");
    assert.notDeepEqual(DST_TIMES.map((t) => page.lwFormatTick(t)), before);
    applyMode("UTC");
    assert.deepEqual(DST_TIMES.map((t) => page.lwFormatTick(t)), before);
    assert.equal(page.lwTzMode(), "UTC");
  });

  it("labels keep the fixed MM/DD HH:MM width in both modes (no clipping/overlap regression)", () => {
    for (const mode of ["UTC", "Eastern Time"]) {
      applyMode(mode);
      for (const t of DST_TIMES) {
        const label = page.lwFormatTick(t);
        assert.equal(label.length, 11, `${mode} label keeps fixed width: ${label}`);
        assert.match(label, /^\d\d\/\d\d \d\d:\d\d$/);
      }
    }
  });

  it("the apply forces a tick re-render without moving the viewport", () => {
    const rangeBefore = page.lwVisibleRange().range;
    fakeState.ranges.length = 0;
    applyMode("Eastern Time");
    assert.ok(fakeState.ranges.length >= 1, "logical range re-asserted (re-render forced)");
    assert.deepEqual(page.lwVisibleRange().range, rangeBefore, "viewport bit-identical");
  });

  it("unknown modes are refused with no state touched", () => {
    const res = applyMode("Mars Time");
    assert.ok(res.error, "unknown mode reports an error");
    assert.equal(page.lwTzMode(), "UTC", "mode untouched");
  });
});

describe("P22-T3-AC3: crosshair/tooltip time follows the axis (shared path)", () => {
  beforeEach(() => { applyMode("UTC"); seedBars(DST_TIMES); });

  it("timeFormatter and tickMarkFormatter are the same shared path", () => {
    applyMode("Eastern Time");
    assert.equal(typeof fakeState.tickFmt, "function", "tick formatter re-applied");
    assert.equal(typeof fakeState.timeFmt, "function", "time formatter re-applied");
    for (const t of DST_TIMES) {
      assert.equal(fakeState.timeFmt(t), fakeState.tickFmt(t),
        `cursor time equals axis label at t=${t}`);
      assert.equal(fakeState.timeFmt(t), page.lwFormatTick(t));
    }
  });

  it("cursor times shift by exactly the axis delta on flip", () => {
    const axisBefore = DST_TIMES.map((t) => page.lwFormatTick(t));
    applyMode("Eastern Time");
    const cursorAfter = DST_TIMES.map((t) => fakeState.timeFmt(t));
    const axisAfter = DST_TIMES.map((t) => page.lwFormatTick(t));
    assert.deepEqual(cursorAfter, axisAfter, "cursor follows the axis tick for tick");
    for (let i = 0; i < DST_TIMES.length; i++) {
      assert.notEqual(axisAfter[i], axisBefore[i], "flip moves the label");
    }
    assert.deepEqual(cursorAfter, DST_ET);
  });
});

describe("P22-T3-AC4: futures plus toggle-only control", () => {
  beforeEach(() => { applyMode("UTC"); });

  it("equity and futures bars label identically in both modes (as-is-ET, one path)", () => {
    // Futures render through the same formatter — no symbol-dependent path.
    const equity = [utc(2026, 11, 2, 13, 30), utc(2026, 11, 2, 18, 0), utc(2026, 11, 2, 20, 0)];
    const futures = equity.slice();
    for (const mode of ["UTC", "Eastern Time"]) {
      applyMode(mode);
      assert.deepEqual(futures.map((t) => page.lwFormatTick(t)),
        equity.map((t) => page.lwFormatTick(t)), `${mode}: futures match equity`);
    }
    applyMode("Eastern Time");
    // Independently pinned strings (EST Monday: UTC-5).
    assert.deepEqual(equity.map((t) => page.lwFormatTick(t)),
      ["11/02 08:30", "11/02 13:00", "11/02 15:00"]);
    applyMode("UTC");
    assert.deepEqual(equity.map((t) => page.lwFormatTick(t)),
      ["11/02 13:30", "11/02 18:00", "11/02 20:00"]);
  });

  it("the ONLY formatter-mutation sites are init plus the tz apply", () => {
    const src = read("chart.js");
    const tickSites = src.split("tickMarkFormatter:").length - 1;
    const timeSites = src.split("timeFormatter:").length - 1;
    assert.equal(tickSites, 2, `tickMarkFormatter applied at init + applyTz only (got ${tickSites})`);
    assert.equal(timeSites, 2, `timeFormatter applied at init + applyTz only (got ${timeSites})`);
    const applyBody = src.slice(src.indexOf("function applyTz(mode)"), src.indexOf("window.lwApplyOps"));
    assert.ok(applyBody.includes("tickMarkFormatter:"), "applyTz re-applies the tick formatter");
    assert.ok(applyBody.includes("timeFormatter:"), "applyTz re-applies the time formatter");
  });

  it("the mode domain is exactly UTC plus Eastern Time", () => {
    assert.equal(page.lwApplyTz("UTC"), true);
    assert.equal(page.lwApplyTz("Eastern Time"), true);
    for (const bad of ["ET", "EST", "EDT", "America/New_York", "", null, undefined, 0]) {
      assert.equal(page.lwApplyTz(bad), false, `refused: ${String(bad)}`);
    }
    page.lwApplyTz("UTC");
  });
});
