"""P11-T2: no-yank live path (D51.2; S-P11-2) — pytest half.

The behavioural probes live here (not in ``chart_assets/lwc/chart.test.js``):
each test shells out to ``node`` with a self-contained harness that boots the
REAL page glue (``chart.js`` + ``envelope.js``) against the same stubbed
document / fake LightweightCharts 5.x tree ``chart.test.js`` uses — a seeded
series driven through the real ``lwApplyOps`` and queried through the real
``lwVisibleRange`` / ``lwFollowProbe`` / ``lwIsFollowing`` surface, including
the real ``bindKeyboard`` pan path (AR-P11-1). The harness fake additionally
models ``scrollToRealTime`` (the realtime scroll path S-P11-2 resumes through)
as a call-counted edge-pin, so T22 proves the resume went through that path.

Red pre-fix (the unconditional post-``applyOps`` refit moves the viewport on
every upsert), green post-fix (upserts leave a scrolled-back viewport
bit-identical; follow re-engages only via the realtime scroll, never on new
bars alone).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The harness prelude: stub document + fake 5.x tree, then boot the real page.
# Mirrors chart.test.js (same library behaviours: setData frames the fresh
# series, update leaves the visible range untouched, fitContent frames all
# loaded bars) plus a call-counted scrollToRealTime the page resumes through.
_PRELUDE = r"""
const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const DIR = %DIR%;
const _fakeScaleState = { range: null };
const _fakeChartState = { count: 0 };
let _scrollCalls = 0;
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
    scrollToRealTime() {
      // Library semantic: show the realtime edge, preserving the span.
      _scrollCalls++;
      const r = _fakeScaleState.range;
      const span = r ? (r.to - r.from) : 10;
      _fakeScaleState.range = {
        from: _fakeChartState.count - 1 - span,
        to: _fakeChartState.count - 1,
      };
    },
    applyOptions() {},
    options() { return {}; },
  };
}
function _fakeSeries(trackCount) {
  return {
    _rows: [],
    setData(rows) {
      this._rows = rows;
      // Only the price (candle) series drives the bar count and the fresh
      // framing: the volume histogram mirrors candle times and never moves
      // the scale on its own (the page fits explicitly after a replace).
      if (trackCount) {
        _fakeChartState.count = rows.length;
        _fakeScaleState.range = { from: 0, to: rows.length - 1 };
      }
    },
    update(row) {
      const last = this._rows.length ? this._rows[this._rows.length - 1].time : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        if (trackCount) _fakeChartState.count = this._rows.length;
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
    // v5 bridge: every series (price AND volume) is created through
    // chart.addSeries(Ctor, options) — the legacy add*Series methods below
    // are never reached. Tag by constructor: only the price series drives
    // the bar count / fresh framing (see _fakeSeries).
    addSeries(ctor) {
      return _fakeSeries(ctor !== globalThis.LightweightCharts.HistogramSeries);
    },
    addCandlestickSeries() { return _fakeSeries(true); },
    addLineSeries() { return _fakeSeries(true); },
    addAreaSeries() { return _fakeSeries(true); },
    addHistogramSeries() { return _fakeSeries(false); },
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
globalThis.window.setTimeout = (...a) => setTimeout(...a);
globalThis.window.clearTimeout = (...a) => clearTimeout(...a);
for (const name of ["LwInteraction", "LwAlarms", "LwPrimitives",
  "LwOverlays", "LwStudies", "LwGestures"]) {
  globalThis.window[name] = { bind() {} };
}
globalThis.window.LwEnvelope = require(DIR + "/envelope.js");
require(DIR + "/chart.js");
const page = globalThis.window;
const BASE = 1700000000;
function seedCandles(n) {
  const ts = [], open = [], high = [], low = [], close = [];
  for (let i = 0; i < n; i++) {
    ts.push(BASE + i * 300);
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
}
function liveTick(t, o, h, l, c, v) {
  // The production live envelope: one candles upsert + one volume upsert.
  const res = page.lwApplyOps({
    v: 1,
    ops: [
      { op: "update_bar", series: "candles",
        cols: { ts: [t], open: [o], high: [h], low: [l], close: [c] } },
      { op: "update_bar", series: "volume",
        cols: { ts: [t], value: [v] } },
    ],
  });
  assert.equal(res.error, null, "live tick applies");
}
function pressKey(k) {
  _fakeEl._listeners["keydown"]({ key: k, preventDefault() {} });
}
"""


def _run_node(flow: str) -> dict:
    """Run the harness prelude + one test flow; return the JSON it prints."""
    program = _PRELUDE.replace("%DIR%", json.dumps(
        str(REPO / "chart_assets" / "lwc"))) + flow
    node = shutil.which("node") or "node"
    proc = subprocess.run(
        [node, "-e", program],
        capture_output=True, text=True, timeout=120,
        cwd=str(REPO),
    )
    assert proc.returncode == 0, (
        "node harness failed (exit %d):\nSTDOUT:\n%s\nSTDERR:\n%s"
        % (proc.returncode, proc.stdout, proc.stderr)
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, "node harness printed nothing"
    return json.loads(lines[-1])


def test_p11_t2_t21_no_yank_while_away():
    """P11-T2-T21 (AC-D51.1 stay-put): scrolled-back viewport bit-identical.

    Seed 60 bars at the edge (following), pan away with the real keyboard
    path, freeze the visible range, then inject 8 live upserts alternating
    forming-bar ticks (same timestamp) and new periods. Every injection must
    leave the visible logical range bit-identical and follow disengaged —
    pre-fix the unconditional refit snaps the range back to the edge.
    """
    payload = _run_node(r"""
const N = 60;
seedCandles(N);
assert.equal(page.lwIsFollowing(), true, "seeded edge follows");
for (let i = 0; i < 6; i++) pressKey("ArrowLeft"); // real pan path
assert.equal(page.lwIsFollowing(), false, "panned away");
const frozen = page.lwVisibleRange().range;
let lastT = BASE + (N - 1) * 300;
let newest = N - 1;
for (let k = 0; k < 8; k++) {
  if (k % 2 === 0) {
    liveTick(lastT, 106.0, 106.25, 105.75, 106.05 + k * 0.01, 1200); // forming tick
  } else {
    lastT += 300;
    liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200); // new period
    newest++;
  }
  const probe = page.lwVisibleRange();
  assert.deepEqual(probe.range, frozen, `range moved on injection ${k}`);
  assert.equal(page.lwIsFollowing(), false, `auto-resumed on injection ${k}`);
}
const end = page.lwVisibleRange();
assert.equal(end.newestSlot, newest, "series grew under the frozen viewport");
console.log(JSON.stringify({
  test: "T21", injections: 8, newestSlot: end.newestSlot,
  range: end.range, frozen, following: page.lwIsFollowing(),
}));
""")
    assert payload["test"] == "T21"
    assert payload["injections"] == 8
    assert payload["newestSlot"] == 60 + 4 - 1  # 4 new periods on a 60-bar seed
    assert payload["range"] == payload["frozen"], "viewport moved under live bars"
    assert payload["following"] is False


def test_p11_t2_t22_no_auto_resume_pan_back_resume():
    """P11-T2-T22 (AC-D51.2 resume rule): bars never auto-resume.

    While away, new bars arrive and follow stays disengaged; then
    pan-back-to-edge re-engages follow — once via the explicit realtime
    scroll entry (asserted through the scrollToRealTime call count) and once
    via the user's own ArrowRight pans (derivation needs no call).
    """
    payload = _run_node(r"""
const N = 60;
seedCandles(N);
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
const frozen = page.lwVisibleRange().range;
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
assert.deepEqual(page.lwVisibleRange().range, frozen, "bars moved the away view");
assert.equal(page.lwIsFollowing(), false, "bars alone re-engaged follow");
assert.equal(typeof page.lwGoToRealtime, "function", "resume entry exists");
page.lwGoToRealtime(); // scripted pan-back-to-edge through the realtime scroll
assert.ok(_scrollCalls >= 1, "resume went through the realtime scroll path");
assert.equal(page.lwIsFollowing(), true, "resume re-engaged follow");
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "away again");
let pans = 0;
while (!page.lwIsFollowing() && pans < 40) { pressKey("ArrowRight"); pans++; }
assert.equal(page.lwIsFollowing(), true, "user pan-back-to-edge resumes follow");
console.log(JSON.stringify({
  test: "T22", scrollCalls: _scrollCalls, userPans: pans,
  newestSlot: page.lwVisibleRange().newestSlot,
  range: page.lwVisibleRange().range, following: page.lwIsFollowing(),
}));
""")
    assert payload["test"] == "T22"
    assert payload["scrollCalls"] >= 1, "resume must use the realtime scroll path"
    assert payload["following"] is True
    assert payload["newestSlot"] == 60 + 3 - 1  # 3 new periods on a 60-bar seed
    rng = payload["range"]
    assert rng["from"] <= payload["newestSlot"] <= rng["to"]
