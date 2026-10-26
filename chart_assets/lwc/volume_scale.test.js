// volume_scale.test.js — node --test gate for the volume pane ceiling
// (Q-9 / AC-D21.2.1, the D21.2 port to the LWC engine).
//
// The reference is the pyqtgraph path: `ChartPanel._recompute_visible_volume_range`
// -> `chart_model.visible_volume_ceiling`:
//   * ceiling = 1.10 x max(volume of the bars in the CURRENTLY VISIBLE range)
//   * VOLUME_NICE_FLOOR (100) when no bar is visible or every visible bar is zero
//   * Y minimum always 0 (D21.1)
//   * the small positive band 0 < max <= 90.9 keeps the literal 1.10 x max
//     (ESC-028: a second unconditional `< 100` clamp is a regression)
//
// A static "max of everything" ceiling cannot pass: case group 2 narrows the
// visible range and requires the ceiling to move with it.
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const DIR = __dirname;
const LwChart = require("./chart.js");

// `ts` column order == logical index; the fixture's own max is at time 5.
const ROWS = [
  { time: 0, value: 120 },
  { time: 1, value: 90 },
  { time: 2, value: 640 },
  { time: 3, value: 250 },
  { time: 4, value: 80 },
  { time: 5, value: 1000 },
  { time: 6, value: 30 },
  { time: 7, value: 0 },
  { time: 8, value: 450 },
  { time: 9, value: 600 },
];
const ALL_MAX = 1000; // max(ROWS.value) — what a static ceiling would use

const close = (actual, expected, label) => {
  const eps = 1e-9 * Math.max(1, Math.abs(expected));
  assert.ok(
    Math.abs(actual - expected) <= eps,
    `${label}: expected ${expected}, got ${actual}`,
  );
};

describe("volume ceiling = 1.10 x max of the VISIBLE bars (AC-D21.2.1)", () => {
  it("full range prices 1.10 x the fixture max", () => {
    const r = LwChart.volumeScaleRange(ROWS, 0, 9);
    close(r.maxValue, ALL_MAX * 1.1, "full-range ceiling");
    assert.equal(r.minValue, 0, "Y minimum is 0 (D21.1)");
  });

  it("each visible window prices its own max", () => {
    const cases = [
      [0, 3, 640],
      [3, 5, 1000],
      [8, 9, 600],
      [1, 1, 90],
      [5, 5, 1000],
    ];
    for (const [from, to, expectedMax] of cases) {
      const r = LwChart.volumeScaleRange(ROWS, from, to);
      close(r.maxValue, expectedMax * 1.1, `ceiling for [${from}, ${to}]`);
      assert.equal(r.minValue, 0, `minValue for [${from}, ${to}]`);
    }
  });

  it("the ceiling follows the visible bars, not the whole series", () => {
    // The series max (1000) sits at time 5; a window that excludes it must
    // NOT keep the 1100 ceiling a static max-of-everything would produce.
    const window = LwChart.volumeScaleRange(ROWS, 0, 3);
    assert.notEqual(window.maxValue, ALL_MAX * 1.1, "static ceiling would pass this");
    close(window.maxValue, 704, "704 — 1.10 x 640");
  });
});

describe("narrowing the visible range CHANGES the ceiling", () => {
  it("zoom in from the full range to a quiet window lowers the ceiling", () => {
    const wide = LwChart.volumeScaleRange(ROWS, 0, 9);
    const narrow = LwChart.volumeScaleRange(ROWS, 0, 2); // max(120, 90, 640) = 640
    const quieter = LwChart.volumeScaleRange(ROWS, 6, 7); // max(30, 0) = 30
    close(wide.maxValue, 1100, "wide ceiling");
    close(narrow.maxValue, 704, "narrow ceiling");
    close(quieter.maxValue, 33, "quietest ceiling");
    assert.ok(narrow.maxValue < wide.maxValue, "narrowing lowers it");
    assert.ok(quieter.maxValue < narrow.maxValue, "narrowing lowers it again");
    assert.notEqual(quieter.maxValue, wide.maxValue, "no static max");
  });

  it("panning a fixed-width window moves the ceiling both ways", () => {
    // Same width (3 slots), three positions — a static ceiling is flat.
    const left = LwChart.volumeScaleRange(ROWS, 0, 2).maxValue; // 640 -> 704
    const mid = LwChart.volumeScaleRange(ROWS, 4, 6).maxValue; // 1000 -> 1100
    const right = LwChart.volumeScaleRange(ROWS, 7, 9).maxValue; // 600 -> 660
    close(left, 704, "left window");
    close(mid, 1100, "mid window");
    close(right, 660, "right window");
    assert.ok(mid > left && mid > right, "the same width can price differently");
    assert.equal(new Set([left, mid, right]).size, 3, "three distinct ceilings");
  });

  it("recomputes per call — no cached range between two autoscales", () => {
    const first = LwChart.volumeScaleRange(ROWS, 0, 9).maxValue;
    const second = LwChart.volumeScaleRange(ROWS, 6, 7).maxValue;
    const third = LwChart.volumeScaleRange(ROWS, 0, 9).maxValue;
    close(first, 1100, "first autoscale");
    close(second, 33, "second autoscale");
    close(third, 1100, "third autoscale");
  });
});

describe("floor 100 when the visible subset is empty or all zero", () => {
  it("no bar in the visible range falls back to VOLUME_NICE_FLOOR", () => {
    for (const [from, to] of [[20, 30], [-40, -1], [10, 40]]) {
      const r = LwChart.volumeScaleRange(ROWS, from, to);
      assert.equal(r.maxValue, 100, `floor for [${from}, ${to}]`);
      assert.equal(r.minValue, 0, `minValue for [${from}, ${to}]`);
    }
  });

  it("every visible bar zero falls back to the floor", () => {
    const zeros = [
      { time: 0, value: 0 },
      { time: 1, value: 0 },
      { time: 2, value: 0 },
    ];
    assert.deepEqual(LwChart.volumeScaleRange(zeros, 0, 2), { minValue: 0, maxValue: 100 });
    // In the mixed fixture, the zero bar alone is still the floor.
    assert.deepEqual(LwChart.volumeScaleRange(ROWS, 7, 7), { minValue: 0, maxValue: 100 });
  });

  it("an empty series is the floor, never NaN/0", () => {
    assert.deepEqual(LwChart.volumeScaleRange([], 0, 10), { minValue: 0, maxValue: 100 });
    assert.deepEqual(LwChart.volumeScaleRange(null, 0, 10), { minValue: 0, maxValue: 100 });
    assert.equal(LwChart.volumeCeiling(0), 100);
    assert.equal(LwChart.VOLUME_NICE_FLOOR, 100);
  });

  it("a missing/non-finite visible range is the floor", () => {
    assert.deepEqual(LwChart.volumeScaleRange(ROWS, null, null), { minValue: 0, maxValue: 100 });
    assert.deepEqual(LwChart.volumeScaleRange(ROWS, undefined, undefined), { minValue: 0, maxValue: 100 });
    assert.deepEqual(LwChart.volumeScaleRange(ROWS, NaN, 3), { minValue: 0, maxValue: 100 });
  });
});

describe("ESC-028: the small positive band keeps 1.10 x max, not 100", () => {
  it("50 -> 55 and 10 -> 11 (a second floor clamp is a regression)", () => {
    close(LwChart.volumeCeiling(50), 55, "50 -> 55");
    close(LwChart.volumeCeiling(10), 11, "10 -> 11");
    close(LwChart.volumeCeiling(90.9), 99.99, "just under the floor");
    close(LwChart.volumeCeiling(91), 100.1, "just over the floor");
    assert.equal(LwChart.volumeCeiling(0), 100, "only zero falls back");
    assert.equal(LwChart.VOLUME_CEILING_FACTOR, 1.1);
  });

  it("a quiet-but-nonzero window is not inflated to 100", () => {
    const quiet = LwChart.volumeScaleRange(ROWS, 6, 6); // 30
    close(quiet.maxValue, 33, "30 -> 33, not 100");
  });
});

describe("visible-bar selection rules", () => {
  it("includes every bar whose slot the range touches", () => {
    // Bar `time` owns (time-0.5, time+0.5). [2.5, 4.5] overlaps bars 3 and 4
    // (250, 80) and touches bars 2/5 only at their edges.
    const r = LwChart.volumeScaleRange(ROWS, 2.5, 4.5);
    close(r.maxValue, 250 * 1.1, "fractional range ceiling");
    assert.equal(LwChart.visibleVolumeMax(ROWS, 2.5, 4.5), 250);
  });

  it("a reversed range is normalised, not dropped", () => {
    assert.equal(LwChart.visibleVolumeMax(ROWS, 3, 0), LwChart.visibleVolumeMax(ROWS, 0, 3));
    close(LwChart.volumeScaleRange(ROWS, 3, 0).maxValue, 704, "reversed-range ceiling");
  });

  it("holes are whitespace, not volume: the indices between bars are empty", () => {
    const gapped = [
      { time: 0, value: 500 },
      { time: 1, value: 400 },
      { time: 5, value: 300 }, // 3 slots of whitespace at 2,3,4
    ];
    assert.equal(LwChart.visibleVolumeMax(gapped, 2, 4), 0, "whitespace has no volume");
    assert.deepEqual(LwChart.volumeScaleRange(gapped, 2, 4), { minValue: 0, maxValue: 100 });
    assert.equal(LwChart.visibleVolumeMax(gapped, 0, 1), 500);
  });

  it("non-finite / negative values never raise the ceiling", () => {
    const dirty = [
      { time: 0, value: -500 },
      { time: 1, value: null },
      { time: 2 },
      { time: 3, value: 200 },
      { time: 4, value: "x" },
      { time: "later", value: 999 }, // non-numeric time: not on the axis
    ];
    assert.equal(LwChart.visibleVolumeMax(dirty, 0, 9), 200);
    close(LwChart.volumeScaleRange(dirty, 0, 9).maxValue, 220, "only real volume counts");
  });
});

describe("the provider is wired to the volume series (not the price pane)", () => {
  const src = readFileSync(path.join(DIR, "chart.js"), "utf8");

  it("exactly one autoscaleInfoProvider — the volume series'", () => {
    // Count in code only: the header/comments name the option too.
    const code = src
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/\/\/[^\n]*/g, "");
    assert.equal(
      (code.match(/autoscaleInfoProvider/g) || []).length,
      1,
      "the price pane's autoscale must stay untouched",
    );
    const hist = code.indexOf("addHistogramSeries");
    const provider = code.indexOf("autoscaleInfoProvider");
    assert.ok(hist > 0 && provider > hist, "provider attaches after the histogram series");
    const block = src.slice(hist, src.indexOf('chart.priceScale("vol")'));
    assert.match(block, /autoscaleInfoProvider/, "inside the volume series' setup");
    assert.match(block, /volumeScaleRange\(snapshot\.volume,/, "reads the volume snapshot");
  });

  it("reads the live visible logical range, so pan/zoom re-price engine-side", () => {
    assert.match(src, /getVisibleLogicalRange\(\)/);
    assert.match(src, /function currentVolumeRange\(\)/);
    assert.match(src, /return volumeScaleRange\(snapshot\.volume, range\.from, range\.to\)/);
    // No wire/round-trip surface: the ceiling is never published to Python.
    assert.ok(!/lwBridge\.[a-zA-Z]*[Vv]olume/.test(src), "no per-gesture bridge call");
  });
});
