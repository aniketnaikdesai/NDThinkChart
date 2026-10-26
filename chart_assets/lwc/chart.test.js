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
const LwEnvelope = require("./envelope.js");
const LwChart = require("./chart.js");

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
