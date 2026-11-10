// follow_offset.test.js — P21-T1 follow-offset preservation (D60.1/D60.2/D60.5).
// node --test suite for the S-P21-1 envelope slot-delta shift, the S-P21-2
// explicit-action preserve, and the S-P21-4 per-view remembered gap.
//
// Each case boots a FRESH page instance (require-cache-busted, own fake
// LightweightCharts tree) so per-instance state never leaks between cases —
// and the two-view case boots two live instances side by side to prove
// independence. The fake mimics only the library behaviours the page
// depends on: `setData` reframes the fresh series (AR-P11-3 may reset the
// range), `update` leaves the visible range untouched, `fitContent` frames
// every loaded bar. The harness models no `scrollToRealTime` — the edge-pin
// under test was the page's own call, and its removal is what these cases
// pin (red-first: post-arrival gap zeroed for every G > 0 cell).
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const Ew = require("./envelope.js");

function bootPage() {
  const scaleState = { range: null };
  const chartState = { count: 0 };
  const listeners = {};
  const fakeTimeScale = () => ({
    getVisibleLogicalRange() {
      const r = scaleState.range;
      return r ? { from: r.from, to: r.to } : null;
    },
    setVisibleLogicalRange(r) {
      scaleState.range = { from: Number(r.from), to: Number(r.to) };
    },
    getVisibleRange() { return null; },
    fitContent() {
      if (chartState.count > 0) {
        scaleState.range = { from: 0, to: chartState.count - 1 };
      }
    },
    applyOptions() {},
    options() { return {}; },
  });
  const fakeSeries = () => ({
    _rows: [],
    setData(rows) {
      this._rows = rows;
      chartState.count = rows.length;
      scaleState.range = { from: 0, to: rows.length - 1 };
    },
    update(row) {
      const last = this._rows.length
        ? this._rows[this._rows.length - 1].time
        : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        chartState.count = this._rows.length;
      } else if (row && last !== null && row.time === last) {
        this._rows[this._rows.length - 1] = row;
      }
    },
    applyOptions() {},
  });
  const scale = fakeTimeScale();
  const fakeChart = () => ({
    timeScale() { return scale; },
    addSeries() { return fakeSeries(); },
    addCandlestickSeries() { return fakeSeries(); },
    addLineSeries() { return fakeSeries(); },
    addAreaSeries() { return fakeSeries(); },
    addHistogramSeries() { return fakeSeries(); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    applyOptions() {},
  });
  const fakeEl = {
    clientWidth: 960,
    clientHeight: 850,
    _listeners: listeners,
    addEventListener(type, fn) { listeners[type] = fn; },
    appendChild() {},
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
    createElement() {
      return { tagName: "BUTTON", style: {}, hidden: true,
        setAttribute() {}, addEventListener() {} };
    },
    addEventListener() {},
  };
  globalThis.window = {
    setTimeout() { return 0; },
    clearTimeout() {},
  };
  for (const name of ["LwInteraction", "LwAlarms", "LwPrimitives",
    "LwOverlays", "LwStudies", "LwGestures"]) {
    globalThis.window[name] = { bind() {} };
  }
  globalThis.window.LwEnvelope = Ew;
  delete require.cache[require.resolve("./chart.js")];
  require("./chart.js");
  const page = globalThis.window;
  const T0 = 1700000000;
  const STEP = 300;
  const candleCols = (n, start = 0) => {
    const ts = [], open = [], high = [], low = [], close = [];
    for (let i = 0; i < n; i++) {
      ts.push(T0 + (start + i) * STEP);
      open.push(100 + (start + i) * 0.1);
      high.push(100 + (start + i) * 0.1 + 0.25);
      low.push(100 + (start + i) * 0.1 - 0.25);
      close.push(100 + (start + i) * 0.1 + 0.05);
    }
    return { ts, open, high, low, close };
  };
  const updateOp = (t) => ({
    op: "update_bar",
    series: "candles",
    cols: {
      ts: [t], open: [106], high: [106.25], low: [105.75], close: [106.05],
    },
  });
  return {
    page,
    T0,
    STEP,
    seed(n) {
      const res = page.lwApplyOps({
        v: 1,
        ops: [{
          op: "set_bars", series: "candles", cols: candleCols(n),
        }],
      });
      assert.equal(res.error, null, "seed envelope applies");
    },
    // Library-internal gesture stand-in (wheel/pinch/drag): moves the
    // library range itself, exactly as chart.test.js does for the wheel.
    setRange(from, to) {
      scaleState.range = { from, to };
    },
    pressKey(k) {
      listeners["keydown"]({ key: k, preventDefault() {} });
    },
    gap() {
      const probe = page.lwVisibleRange();
      return probe.range.to - probe.newestSlot;
    },
    updateOp,
    candleCols,
    newSlotTs: (k) => T0 + (60 + k) * STEP,
  };
}

// P21-T1-AC1 (AC-D60.1): G x N shift matrix on the main view.
describe("P21-T1-AC1: following viewport shifts by exactly the arrival width", () => {
  const SPAN = 40;
  for (const G of [0, 1, 3]) {
    for (const N of [1, 3]) {
      it(`G=${G} N=${N}: range shifts by +${N}, post-arrival gap stays ${G}`, () => {
        const ctx = bootPage();
        const { page } = ctx;
        ctx.seed(60);
        assert.equal(page.lwIsFollowing(), true);
        // Park a following range with right-edge gap G (span preserved).
        const to = 59 + G;
        ctx.setRange(to - SPAN, to);
        assert.equal(page.lwIsFollowing(), true, "setup range follows");
        assert.equal(page.lwRememberedGap(), G, "setup gap remembered");
        const before = page.lwVisibleRange().range;
        // Inject N new slots through one envelope (N=3 is a batch).
        const ops = [];
        for (let k = 0; k < N; k++) ops.push(ctx.updateOp(ctx.newSlotTs(k)));
        const res = page.lwApplyOps({ v: 1, ops });
        assert.equal(res.error, null);
        const after = page.lwVisibleRange();
        assert.equal(after.newestSlot, 59 + N, "envelope added N slots");
        assert.deepEqual(after.range,
          { from: before.from + N, to: before.to + N },
          "visible range shifts by exactly N (span preserved)");
        assert.equal(ctx.gap(), G, "post-arrival gap equals G");
        assert.equal(page.lwIsFollowing(), true, "still following");
        assert.equal(page.lwRememberedGap(), G, "remembered gap intact");
      });
    }
  }
});

// P21-T1-AC2 (AC-D60.2): explicit actions preserve the remembered gap.
describe("P21-T1-AC2: explicit actions resume with the remembered gap", () => {
  it("goToRealtime from away keeps span and lands newest at the gap offset", () => {
    const ctx = bootPage();
    const { page } = ctx;
    ctx.seed(60);
    ctx.setRange(19, 61); // span 42, gap 2 over newest 59
    assert.equal(page.lwIsFollowing(), true);
    for (let i = 0; i < 6; i++) ctx.pressKey("ArrowLeft"); // real pan path
    assert.equal(page.lwIsFollowing(), false, "setup is away");
    assert.equal(page.lwRememberedGap(), 2, "away holds the last gap");
    assert.equal(page.lwGoToRealtime(), true);
    assert.equal(page.lwIsFollowing(), true, "follow re-engaged");
    assert.deepEqual(page.lwVisibleRange().range, { from: 19, to: 61 },
      "span preserved, newest lands at the remembered-gap offset");
    assert.equal(ctx.gap(), 2, "post-action gap equals the remembered gap");
  });

  it("fitAndFollow frames all loaded bars then extends to by the gap", () => {
    for (const away of [false, true]) {
      const ctx = bootPage();
      const { page } = ctx;
      ctx.seed(60);
      ctx.setRange(15, 61); // span 46, gap 2
      assert.equal(page.lwIsFollowing(), true);
      if (away) {
        for (let i = 0; i < 6; i++) ctx.pressKey("ArrowLeft");
        assert.equal(page.lwIsFollowing(), false, "setup is away");
      }
      assert.equal(page.lwFit(), true);
      assert.equal(page.lwIsFollowing(), true, "follow re-engaged");
      assert.deepEqual(page.lwVisibleRange().range, { from: 0, to: 61 },
        "fit frames every loaded bar, then extends to by the gap");
      assert.equal(ctx.gap(), 2, "post-action gap equals the remembered gap");
    }
  });

  it("double-click/Fit shares the fitAndFollow preserve entry (no edge-pin)", () => {
    // No dblclick listener exists in chart.js: the right-edge
    // double-click/Fit gesture routes through the same lwFit entry, so the
    // preserve above IS the double-click path. Pin the single-entry shape.
    const fs = require("node:fs");
    const path = require("node:path");
    const src = fs.readFileSync(path.join(__dirname, "chart.js"), "utf8");
    assert.ok(!/dblclick/i.test(src), "no separate double-click edge-pin");
    assert.ok(src.includes("function fitAndFollow()"), "single Fit entry");
  });

  it("only a manual scroll/pinch to the edge zeroes the gap", () => {
    const ctx = bootPage();
    const { page } = ctx;
    ctx.seed(60);
    ctx.setRange(19, 61); // gap 2
    assert.equal(page.lwIsFollowing(), true);
    assert.equal(page.lwRememberedGap(), 2);
    // Explicit actions never zero: both preserve 2.
    page.lwGoToRealtime();
    assert.equal(page.lwRememberedGap(), 2, "goToRealtime never zeroes");
    page.lwFit();
    assert.equal(page.lwRememberedGap(), 2, "fitAndFollow never zeroes");
    // The manual path moves the range itself: newest parked at the edge.
    ctx.setRange(20, 59);
    assert.equal(page.lwIsFollowing(), true);
    assert.equal(ctx.gap(), 0, "manual scroll to the edge zeroes the gap");
    assert.equal(page.lwRememberedGap(), 0, "the zero is remembered");
    // Resuming afterwards preserves the (now zero) gap in place.
    page.lwGoToRealtime();
    assert.equal(ctx.gap(), 0, "resume keeps the manual zero");
    assert.deepEqual(page.lwVisibleRange().range, { from: 20, to: 59 });
  });

  it("a never-followed view resumes at the fresh-frame default gap", () => {
    const ctx = bootPage();
    const { page } = ctx;
    ctx.seed(60);
    // Park the fresh-frame landing (newest at the default offset): the
    // first observed following range sets the remembered gap.
    ctx.setRange(17, 61);
    assert.equal(page.lwIsFollowing(), true);
    assert.equal(page.lwRememberedGap(), 2, "default gap observed");
    for (let i = 0; i < 6; i++) ctx.pressKey("ArrowLeft");
    page.lwGoToRealtime();
    assert.equal(ctx.gap(), 2, "resume lands at the default offset");
  });
});

// P21-T1-AC3 (AC-D60.5): two views, independent gaps, nothing over the bridge.
describe("P21-T1-AC3: per-view gaps stay independent and off the bridge", () => {
  it("each view shifts by the arrival width and keeps its own gap", () => {
    const a = bootPage();
    const b = bootPage();
    a.seed(60);
    b.seed(60);
    a.setRange(19, 60); // gap 1 over newest 59
    b.setRange(17, 62); // gap 3 over newest 59
    assert.equal(a.page.lwIsFollowing(), true);
    assert.equal(b.page.lwIsFollowing(), true);
    assert.equal(a.page.lwRememberedGap(), 1);
    assert.equal(b.page.lwRememberedGap(), 3);
    // The same arrival lands in both views.
    for (const ctx of [a, b]) {
      const res = ctx.page.lwApplyOps({
        v: 1,
        ops: [ctx.updateOp(ctx.newSlotTs(0)), ctx.updateOp(ctx.newSlotTs(1))],
      });
      assert.equal(res.error, null);
    }
    assert.equal(a.page.lwVisibleRange().newestSlot, 61);
    assert.equal(b.page.lwVisibleRange().newestSlot, 61);
    assert.deepEqual(a.page.lwVisibleRange().range, { from: 21, to: 62 });
    assert.deepEqual(b.page.lwVisibleRange().range, { from: 19, to: 64 });
    assert.equal(a.gap(), 1, "view A keeps its gap");
    assert.equal(b.gap(), 3, "view B keeps its gap");
    assert.equal(a.page.lwRememberedGap(), 1);
    assert.equal(b.page.lwRememberedGap(), 3);
    assert.notEqual(a.page.lwRememberedGap(), b.page.lwRememberedGap(),
      "the gaps never equalize across views");
  });

  it("no gap value crosses the Python bridge", () => {
    const ctx = bootPage();
    const { page } = ctx;
    const sent = [];
    const bridge = { keyPressed(payload) { sent.push(payload); } };
    page.lwReportKey("ArrowLeft", bridge);
    assert.equal(sent.length, 1);
    assert.ok(!/gap/i.test(sent[0]), "bridge payload carries no gap field");
    assert.deepEqual(JSON.parse(sent[0]), { key: "ArrowLeft" });
  });
});

// P21-T1-AC4 (AC-D60.7 envelope half): forming ticks vs hole-republish.
describe("P21-T1-AC4: forming ticks hold still, republish shifts exactly once", () => {
  it("forming-bar-only envelopes move nothing across repeated ticks", () => {
    const ctx = bootPage();
    const { page } = ctx;
    ctx.seed(60);
    ctx.setRange(19, 61); // gap 2
    assert.equal(page.lwIsFollowing(), true);
    const frozen = page.lwVisibleRange().range;
    const formingTs = 1700000000 + 59 * 300; // newest bar's own timestamp
    for (let k = 0; k < 5; k++) {
      const res = page.lwApplyOps({ v: 1, ops: [ctx.updateOp(formingTs)] });
      assert.equal(res.error, null);
      assert.equal(page.lwVisibleRange().newestSlot, 59, "no new slot");
      assert.deepEqual(page.lwVisibleRange().range, frozen,
        `tick ${k}: no per-tick jitter`);
    }
    assert.equal(page.lwIsFollowing(), true);
    assert.equal(ctx.gap(), 2);
  });

  it("a hole-republish envelope appending N slots shifts exactly N, once", () => {
    const ctx = bootPage();
    const { page } = ctx;
    ctx.seed(60);
    ctx.setRange(19, 61); // gap 2
    assert.equal(page.lwIsFollowing(), true);
    // Opened-hole republish: same-symbol replace appending 2 slots plus a
    // forming tick on the new newest bar, all in ONE envelope.
    const republish = () => ({
      v: 1,
      ops: [
        {
          op: "set_bars", series: "candles", same_symbol: true,
          cols: ctx.candleCols(62),
        },
        ctx.updateOp(1700000000 + 61 * 300),
      ],
    });
    assert.equal(page.lwApplyOps(republish()).error, null);
    assert.equal(page.lwVisibleRange().newestSlot, 61, "N=2 slots appended");
    assert.deepEqual(page.lwVisibleRange().range, { from: 21, to: 63 },
      "exactly-N shift, gap preserved");
    assert.equal(ctx.gap(), 2);
    // Replaying the identical envelope is a no-op (AR-P21-1: never twice).
    assert.equal(page.lwApplyOps(republish()).error, null);
    assert.deepEqual(page.lwVisibleRange().range, { from: 21, to: 63 },
      "second landing shifts nothing");
    assert.equal(page.lwIsFollowing(), true);
  });
});
