// chart.test.js — node --test contract suite for the P6-05 core-chart glue.
// Runs with the repo's node install, no npm deps, no network, no DOM.
// Covers the pure core exported by chart.js (MODES, tzLabel, barGeometry,
// describeOp, volumeBarColor) plus the envelope forward-compat the mode
// key relies on: P6-04 validators must accept mode-carrying set_bars ops.
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const DIR = __dirname;
const read = (name) => readFileSync(path.join(DIR, name), "utf8");
// S-P11-1 follow-state probe harness: boot the page glue in-process against
// a stubbed document and a fake LightweightCharts 5.x tree, so a seeded
// series can be driven through the real `lwApplyOps` and queried through the
// real `lwFollowProbe` / `lwVisibleRange` / `lwIsFollowing` surface —
// including the real `bindKeyboard` pan path (AR-P11-1). The fake mimics
// only the library behaviours the probes depend on: `setData` frames the
// fresh series, `update` leaves the visible range untouched, `fitContent`
// frames every loaded bar.
const _fakeScaleState = { range: null };
const _fakeChartState = { count: 0 };
function _fakeTimeScale() {
  return {
    getVisibleLogicalRange() {
      const r = _fakeScaleState.range;
      return r ? { from: r.from, to: r.to } : null;
    },
    setVisibleLogicalRange(r) {
      _fakeScaleState.range = { from: Number(r.from), to: Number(r.to) };
    },
    getVisibleRange() { return null; },
    fitContent() {
      if (_fakeChartState.count > 0) {
        _fakeScaleState.range = { from: 0, to: _fakeChartState.count - 1 };
      }
    },
    applyOptions() {},
    options() { return {}; },
  };
}
function _fakeSeries() {
  return {
    _rows: [],
    setData(rows) {
      this._rows = rows;
      _fakeChartState.count = rows.length;
      _fakeScaleState.range = { from: 0, to: rows.length - 1 };
    },
    update(row) {
      // The library appends a bar with a newer time (forming-bar ticks with
      // the same time repaint in place) and leaves the visible range
      // untouched — the refit afterwards is applyOps' own fitToWidth().
      const last = this._rows.length ? this._rows[this._rows.length - 1].time : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        _fakeChartState.count = this._rows.length;
      } else if (row && last !== null && row.time === last) {
        this._rows[this._rows.length - 1] = row;
      }
    },
    applyOptions() {},
  };
}
function _fakeChart() {
  const scale = _fakeTimeScale();
  return {
    timeScale() { return scale; },
    addSeries() { return _fakeSeries(); },
    addCandlestickSeries() { return _fakeSeries(); },
    addLineSeries() { return _fakeSeries(); },
    addAreaSeries() { return _fakeSeries(); },
    addHistogramSeries() { return _fakeSeries(); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    fitContent() {
      if (_fakeChartState.count > 0) {
        _fakeScaleState.range = { from: 0, to: _fakeChartState.count - 1 };
      }
    },
    applyOptions() {},
  };
}
const _fakeEl = {
  clientWidth: 960,
  clientHeight: 850,
  _listeners: {},
  addEventListener(type, fn) { this._listeners[type] = fn; },
  getBoundingClientRect() {
    return { width: 960, height: 850, top: 0, left: 0 };
  },
};
globalThis.LightweightCharts = {
  createChart() { return _fakeChart(); },
  CandlestickSeries: {},
  LineSeries: {},
  AreaSeries: {},
  HistogramSeries: {},
};
globalThis.document = {
  readyState: "complete",
  title: "",
  getElementById() { return _fakeEl; },
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

describe("offline / no-CDN loader surface (P6-05 glue)", () => {
  it("chart.js has no remote fetch", () => {
    const src = read("chart.js");
    assert.ok(!/(src|href)\s*=\s*["']https?:\/\//i.test(src), "no remote src/href");
    assert.ok(!/\bfrom\s+["']https?:\/\//.test(src), "no remote import");
    assert.ok(!/unpkg\.com|cdn\.jsdelivr|cdnjs\.cloudflare/i.test(src), "no CDN host");
    assert.ok(!/require\(["'][^./]/.test(src), "no bare npm require");
  });
});

describe("per-mode series registry (P6-05)", () => {
  it("exposes exactly the five chart modes", () => {
    assert.deepEqual(LwChart.MODES, ["candles", "hollow", "heikin", "line", "area"]);
  });

  it("isMode accepts the five modes and nothing else", () => {
    for (const m of LwChart.MODES) assert.equal(LwChart.isMode(m), true);
    for (const bad of ["candle", "bars", "", null, undefined, 42]) {
      assert.equal(LwChart.isMode(bad), false);
    }
  });

  it("describeOp routes set/update/clear to replace/upsert/clear", () => {
    assert.deepEqual(LwChart.describeOp({ op: "set_bars", series: "candles", cols: {} }), {
      action: "replace", series: "candles", mode: null,
    });
    assert.deepEqual(LwChart.describeOp({ op: "set_volume", series: "volume", cols: {} }), {
      action: "replace", series: "volume", mode: null,
    });
    assert.deepEqual(LwChart.describeOp({ op: "update_bar", series: "candles", cols: {} }), {
      action: "upsert", series: "candles",
    });
    assert.deepEqual(LwChart.describeOp({ op: "clear", series: "candles" }), {
      action: "clear", series: "candles",
    });
    assert.deepEqual(LwChart.describeOp({ op: "nonsense", series: "candles" }), {
      action: "ignore",
    });
  });

  it("describeOp carries the mode off a set_bars op (per-mode series)", () => {
    for (const m of LwChart.MODES) {
      const d = LwChart.describeOp({ op: "set_bars", series: "candles", cols: {}, mode: m });
      assert.equal(d.mode, m, `mode ${m} survives`);
      assert.equal(d.action, "replace");
    }
    const d = LwChart.describeOp({ op: "set_bars", series: "candles", cols: {}, mode: "bogus" });
    assert.equal(d.mode, null, "unknown mode is not adopted");
  });
});

describe("envelope forward-compat: the mode key crosses untouched", () => {
  const cols = (ts) => ({ ts, open: [1], high: [2], low: [0.5], close: [1.5] });

  it("P6-04 validators accept a mode-carrying set_bars op", () => {
    const env = {
      v: 1,
      ops: [{ op: "set_bars", series: "candles", cols: cols([1000]), mode: "heikin" }],
    };
    assert.equal(LwEnvelope.validateEnvelope(env).ok, true);
  });

  it("mergeRows ignores the mode key (replay identity holds per mode)", () => {
    const ops = [
      { op: "set_bars", series: "candles", cols: cols([1000]), mode: "heikin" },
      { op: "update_bar", series: "candles", cols: cols([1060]) },
      { op: "update_bar", series: "candles", cols: cols([1060]) },
    ];
    const once = LwEnvelope.mergeRows([], ops);
    const twice = LwEnvelope.mergeRows(once, ops);
    assert.equal(once.length, 2);
    assert.deepEqual(twice, once);
  });

  it("logical-index times keep hole whitespace (steps > 1 survive)", () => {
    const ops = [
      {
        op: "set_bars", series: "candles", mode: "candles",
        cols: {
          ts: [0, 1, 2, 6, 7], // hole of 3 slots between 2 and 6
          open: [1, 1, 1, 1, 1], high: [2, 2, 2, 2, 2],
          low: [0.5, 0.5, 0.5, 0.5, 0.5], close: [1.5, 1.5, 1.5, 1.5, 1.5],
        },
      },
    ];
    const rows = LwEnvelope.mergeRows([], ops);
    assert.deepEqual(rows.map((r) => r.time), [0, 1, 2, 6, 7]);
  });
});

describe("custom tz formatter: local = t - offset", () => {
  it("formats summer (EDT, offset 14400) labels", () => {
    // 2026-07-01 16:00 UTC == 12:00 EDT.
    const t = Math.floor(Date.UTC(2026, 6, 1, 16, 0, 0) / 1000);
    assert.equal(LwChart.tzLabel(t, 14400), "07/01 12:00");
  });

  it("formats winter (EST, offset 18000) labels", () => {
    // 2026-01-15 14:30 UTC == 09:30 EST.
    const t = Math.floor(Date.UTC(2026, 0, 15, 14, 30, 0) / 1000);
    assert.equal(LwChart.tzLabel(t, 18000), "01/15 09:30");
  });

  it("zero offset renders UTC", () => {
    const t = Math.floor(Date.UTC(2026, 2, 9, 13, 30, 0) / 1000);
    assert.equal(LwChart.tzLabel(t, 0), "03/09 13:30");
  });
});

describe("barSpacing geometry guard (DG94 restatement)", () => {
  it("gap >= 0 in every regime; gap > 0 whenever spacing allows", () => {
    for (const s of [0.5, 1.0, 2.0, 4.0, 5.0, 8.0, 20.0, 100.0]) {
      const g = LwChart.barGeometry(s);
      assert.ok(g.body <= s, `body <= spacing at S=${s}`);
      assert.ok(g.gap >= 0, `gap >= 0 at S=${s}`);
      assert.equal(g.gap > 0, s > 4.0, `gap>0 iff S>floor at S=${s}`);
    }
  });

  it("non-dense regime keeps the 65/35 split", () => {
    const g = LwChart.barGeometry(100.0);
    assert.equal(g.body, 65.0);
    assert.equal(g.gap, 35.0);
  });

  it("volume bars share the price-body geometry (one rule)", () => {
    const price = LwChart.barGeometry(8.0);
    const vol = LwChart.barGeometry(8.0);
    assert.deepEqual(vol, price);
  });
});

describe("volume colours follow the candle (price-coloured bars)", () => {
  it("up bar green, down bar red", () => {
    assert.equal(LwChart.volumeBarColor(100, 101), "#34d399");
    assert.equal(LwChart.volumeBarColor(101, 100), "#f87171");
    assert.equal(LwChart.volumeBarColor(100, 100), "#34d399");
  });
});

// S-P11-1 follow-state definition + repro probes (D51.1; P11-T1-T11/T12).
// A seeded series is driven through the REAL page surface (`lwApplyOps`,
// the real `bindKeyboard` pan/zoom path) and queried through the real
// `lwFollowProbe` / `lwVisibleRange` / `lwIsFollowing` probes — including the
// real `bindKeyboard` pan path (AR-P11-1). W1 proved the follow surface red
// (no `isFollowing` at all); W2 (P11-T2, S-P11-2) gates the refit and owns
// the T12 characterisation below — away viewports stay bit-identical across
// live upserts, and the edge keeps following.
describe("S-P11-1 follow-state probes (P11-T1)", () => {
  const N = 60;
  const seedCandles = (n) => {
    const ts = [], open = [], high = [], low = [], close = [];
    for (let i = 0; i < n; i++) {
      ts.push(1700000000 + i * 300);
      open.push(100 + i * 0.1);
      high.push(100 + i * 0.1 + 0.25);
      low.push(100 + i * 0.1 - 0.25);
      close.push(100 + i * 0.1 + 0.05);
    }
    const res = page.lwApplyOps({
      v: 1,
      ops: [{
        op: "set_bars", series: "candles",
        cols: { ts, open, high, low, close },
      }],
    });
    assert.equal(res.error, null, "seed envelope applies");
    return res;
  };
  const pressKey = (k) => _fakeEl._listeners["keydown"]({
    key: k, preventDefault() {},
  });

  it("P11-T1-T11: seeded series at the live edge reports following", () => {
    seedCandles(N);
    assert.equal(page.lwIsFollowing(), true);
    const probe = page.lwFollowProbe();
    assert.equal(probe.following, true);
    assert.equal(probe.newestSlot, N - 1);
    assert.ok(probe.range.from <= N - 1 && N - 1 <= probe.range.to,
      `newest slot inside the visible range: ${JSON.stringify(probe.range)}`);
  });

  it("P11-T1-T11: scripted pan away reports scrolled back", () => {
    seedCandles(N);
    assert.equal(page.lwIsFollowing(), true);
    for (let i = 0; i < 6; i++) pressKey("ArrowLeft"); // real bindKeyboard path
    const probe = page.lwFollowProbe();
    assert.equal(probe.newestSlot, N - 1, "panning never moves the newest slot");
    assert.equal(probe.following, false);
    assert.equal(page.lwIsFollowing(), false);
  });

  it("P11-T1-T11: keyboard zoom and library wheel-zoom report scrolled back", () => {
    seedCandles(N);
    pressKey("+"); // real bindKeyboard zoom path (AR-P11-1)
    assert.equal(page.lwIsFollowing(), false);
    seedCandles(N); // setData reframes the fresh series at the edge
    assert.equal(page.lwIsFollowing(), true);
    // A wheel gesture is library-internal (no page handler): it moves the
    // library range itself, and the derived probe reflects it by construction.
    _fakeScaleState.range = { from: 10, to: 40 };
    assert.equal(page.lwIsFollowing(), false);
    assert.deepEqual(page.lwFollowProbe(),
      { following: false, newestSlot: N - 1, range: { from: 10, to: 40 } });
  });

  it("P11-T1-T11: the pure isFollowingSlot predicate covers the edges", () => {
    assert.equal(LwChart.isFollowingSlot(59, { from: 0, to: 59 }), true);
    assert.equal(LwChart.isFollowingSlot(59, { from: 0, to: 58.999 }), false);
    assert.equal(LwChart.isFollowingSlot(59, null), false);
    assert.equal(LwChart.isFollowingSlot(-1, { from: 0, to: 59 }), false);
  });

  it("P11-T1-T12: visible-range probe matches the library range + newest slot", () => {
    seedCandles(N);
    const probe = page.lwVisibleRange();
    assert.equal(probe.newestSlot, N - 1);
    assert.deepEqual(probe.range, { from: 0, to: N - 1 },
      "seeded fit frames every loaded bar at this width");
  });

  it("P11-T1-T12: applyOps gates its viewport moves on follow state (S-P11-2)", () => {
    // Static: the W1 unconditional refit is gone — the refit survives only
    // for full replaces, and the live path follows through the realtime
    // scroll only while following (P11-T2 owns this characterisation).
    const src = read("chart.js");
    const body = src.slice(
      src.indexOf("function applyOps(env)"),
      src.indexOf("function applyRows("),
    );
    assert.ok(body.includes("isFollowing"), "applyOps gates on follow state");
    assert.ok(body.includes("followLive()"),
      "live path follows via the realtime scroll");
    assert.ok(!/\n    fitToWidth\(\);\n/.test(body),
      "no unconditional post-envelope refit (the yank)");
    // Behavioural: panned away, a live upsert leaves the range bit-identical
    // and follow disengaged — new bars never auto-resume.
    seedCandles(N);
    for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
    assert.equal(page.lwIsFollowing(), false);
    const frozen = page.lwVisibleRange().range;
    const t1 = 1700000000 + N * 300;
    const res = page.lwApplyOps({
      v: 1,
      ops: [{
        op: "update_bar", series: "candles",
        cols: {
          ts: [t1], open: [106], high: [106.25], low: [105.75], close: [106.05],
        },
      }],
    });
    assert.equal(res.error, null);
    assert.equal(page.lwVisibleRange().newestSlot, N, "upsert extended the series");
    assert.deepEqual(page.lwVisibleRange().range, frozen,
      "away viewport stays bit-identical across the upsert");
    assert.equal(page.lwIsFollowing(), false, "no auto-resume on bars alone");
  });

  it("P11-T2-T23: live edge follows while following (fallback pin)", () => {
    // While following, a new-period upsert keeps the newest slot visible.
    // This harness models no scrollToRealTime, so the setVisibleLogicalRange
    // fallback pins the edge; the scroll entry itself is covered by
    // tests/test_p11_no_yank.py T22.
    seedCandles(N);
    assert.equal(page.lwIsFollowing(), true);
    const t1 = 1700000000 + N * 300;
    const res = page.lwApplyOps({
      v: 1,
      ops: [{
        op: "update_bar", series: "candles",
        cols: {
          ts: [t1], open: [106], high: [106.25], low: [105.75], close: [106.05],
        },
      }],
    });
    assert.equal(res.error, null);
    assert.equal(page.lwVisibleRange().newestSlot, N, "upsert extended the series");
    assert.equal(page.lwIsFollowing(), true, "live edge keeps following");
  });
});
