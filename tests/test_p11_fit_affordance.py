"""P11-T3: Fit/reset + go-to-realtime affordance (D51.3; S-P11-4) — pytest half.

The behavioural probes live here (not in ``chart_assets/lwc/chart.test.js``,
which this task does not touch): each test shells out to ``node`` with a
self-contained harness that boots the REAL page glue (``chart.js`` +
``envelope.js``) against the same stubbed document / fake LightweightCharts
5.x tree ``test_p11_no_yank.py`` uses — a seeded series driven through the
real ``lwApplyOps`` and queried through the real ``lwFit`` /
``lwAffordanceVisible`` / ``lwGoToRealtime`` / ``lwIsFollowing`` surface,
including the real ``bindKeyboard`` pan path (AR-P11-1).

Red pre-fix (no Fit entry, no affordance surface: ``lwFit`` /
``lwAffordanceVisible`` are undefined), green post-fix (Fit frames all loaded
bars plus the remembered gap and re-engages follow from any starting state;
the badge is visible exactly when away AND new-bars-since-away, and invoking
it resumes follow in place and re-engages follow). P21-T4: the invoke and
Fit halves assert the S-P21-2 preserve semantics — no case pins the retired
``scrollToRealTime`` edge-pin or its call count.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The harness prelude: stub document + fake 5.x tree, then boot the real page.
# Mirrors test_p11_no_yank.py (same library behaviours: setData frames the
# fresh series, update leaves the visible range untouched, fitContent frames
# all loaded bars) plus the call-counted scrollToRealTime fake the page
# resumed through pre-P21 (P21-T4: invoke/Fit preserve the remembered gap;
# the counter pins no path). Adds the S-P11-4 entries under test: lwFit + lwAffordanceVisible.
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


def test_p11_t3_t31_fit_frames_all_and_reengages():
    """P11-T3-T31 (AC1) as re-pinned by P21-T4 (S-P21-2 preserve semantics).

    Latent case, re-seeded through a frame-carrying envelope: a tracking
    frame with right padding establishes a non-zero remembered gap (G),
    so Fit/reset must frame ``{0, newest+G}`` — the frame-all promise and
    the gap hold together — with follow re-engaged in both the following
    and the scrolled-back cases.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwFit, "function", "Fit entry exists");
const N = 60;
seedCandles(N);
// The faithful seed: a frame-carrying envelope with non-zero remembered
// gap (G), still following.
const G = 2;
{
  const res = page.lwApplyOps({
    v: 1,
    ops: [{ op: "set_visible_range",
            range: { from: N - 15, to: N - 1 + G }, following: true }],
  });
  assert.equal(res.error, null, "gap-carrying frame applies");
}
// Case 1: Fit from the following state frames all bars plus the gap,
// follow engaged.
assert.equal(page.lwIsFollowing(), true, "framed tracking follows");
assert.equal(page.lwFit(), true, "Fit lands");
let probe = page.lwVisibleRange();
assert.equal(probe.range.from, 0, "fit frames from slot 0 (following case)");
assert.equal(probe.range.to, probe.newestSlot + G,
  "fit preserves the remembered gap (following)");
assert.equal(page.lwIsFollowing(), true, "follow engaged (following case)");
// Case 2: pan away, grow the series, Fit frames everything plus the gap.
for (let i = 0; i < 6; i++) pressKey("ArrowLeft"); // real pan path
assert.equal(page.lwIsFollowing(), false, "panned away");
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
assert.equal(page.lwIsFollowing(), false, "still away after new bars");
assert.equal(page.lwFit(), true, "Fit lands while away");
probe = page.lwVisibleRange();
assert.equal(probe.newestSlot, N + 3 - 1, "series grew under the away view");
assert.equal(probe.range.from, 0, "fit frames from slot 0 (away case)");
assert.equal(probe.range.to, probe.newestSlot + G,
  "fit preserves the remembered gap (away case)");
assert.equal(page.lwIsFollowing(), true, "follow re-engaged (away case)");
console.log(JSON.stringify({
  test: "T31", newestSlot: probe.newestSlot,
  range: probe.range, following: page.lwIsFollowing(),
}));
""")
    assert payload["test"] == "T31"
    assert payload["newestSlot"] == 60 + 3 - 1
    assert payload["range"] == {"from": 0, "to": 60 + 3 - 1 + 2}, \
        "Fit must frame all loaded bars plus the remembered gap"
    assert payload["following"] is True


def test_p11_t3_t32_affordance_visibility_and_invoke():
    """P11-T3-T32 (AC2) as re-pinned by P21-T4 (S-P21-2 preserve semantics).

    The badge (``lwAffordanceVisible``) keeps away-AND-new-bars internally
    (still armed/disarmed on the same transitions, still probe-observable),
    while the *visible* control (``lwChevronVisible``) is away-only — so the
    two away-alone cells (no new bars; forming-bar ticks only) now assert the
    chevron SHOWN where the badge stays hidden. Invoking preserves the
    remembered gap (established by a frame-carrying envelope): the
    post-invoke range keeps the pre-invoke span and lands the newest bar at
    gap G with follow re-engaged — no retired scrollToRealTime edge-pin —
    and a manual pan-back-to-edge still hides both.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwAffordanceVisible, "function", "badge probe exists");
assert.equal(typeof page.lwChevronVisible, "function", "chevron probe exists");
assert.equal(typeof page.lwGoToRealtime, "function", "resume entry exists");
const N = 60;
seedCandles(N);
// Establish the remembered gap through a frame-carrying envelope: a
// tracking frame with right padding (gap G), still following.
const G = 2;
{
  const res = page.lwApplyOps({
    v: 1,
    ops: [{ op: "set_visible_range",
            range: { from: N - 15, to: N - 1 + G }, following: true }],
  });
  assert.equal(res.error, null, "gap-carrying frame applies");
}
// Following: badge and chevron both hidden (nothing to announce).
assert.equal(page.lwIsFollowing(), true, "framed tracking follows");
assert.equal(page.lwAffordanceVisible(), false, "hidden while following");
assert.equal(page.lwChevronVisible(), false, "chevron hidden while following");
// Away with no new bars: the badge stays hidden internally, but the
// visible chevron shows (S-P18-1 supersession of the badge rule).
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
assert.equal(page.lwAffordanceVisible(), false, "badge hidden: away, no new bars");
assert.equal(page.lwChevronVisible(), true, "chevron shown: away, no new bars");
// Away + new bars: both show.
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
assert.equal(page.lwIsFollowing(), false, "bars alone never resume");
assert.equal(page.lwAffordanceVisible(), true, "shown: away + new bars");
assert.equal(page.lwChevronVisible(), true, "chevron shown: away + new bars");
// Invoke: the preserve resume keeps the span and lands the newest bar at
// the remembered gap, re-engages follow and consumes the badge;
// the chevron hides by derivation.
{
  const before = page.lwVisibleRange().range;
  const span = before.to - before.from;
  page.lwGoToRealtime();
  const after = page.lwVisibleRange();
  assert.equal(after.range.to - after.newestSlot, G,
    "post-invoke gap equals the remembered gap");
  assert.equal(after.range.to - after.range.from, span,
    "post-invoke span preserved");
}
assert.equal(page.lwIsFollowing(), true, "invoke re-engaged follow");
assert.equal(page.lwAffordanceVisible(), false, "hidden after invoke resumes");
assert.equal(page.lwChevronVisible(), false, "chevron hidden after invoke resumes");
// Away again + forming-bar ticks only (no new bars): the badge stays
// hidden internally, but the away-only chevron shows.
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "away again");
for (let k = 0; k < 3; k++) {
  liveTick(lastT, 106.0 + k * 0.01, 106.25, 105.75, 106.05, 1200);
}
assert.equal(page.lwAffordanceVisible(), false, "badge hidden: ticks are not bars");
assert.equal(page.lwChevronVisible(), true, "chevron shown: away, ticks are not bars");
// Two new periods while away: badge shows again; a user pan-back-to-edge
// (derivation, no invoke call) hides both.
lastT += 300;
liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
lastT += 300;
liveTick(lastT, 106.1, 106.35, 105.85, 106.15, 1300);
assert.equal(page.lwAffordanceVisible(), true, "shown again on new bars");
assert.equal(page.lwChevronVisible(), true, "chevron shown again on new bars");
let pans = 0;
while (!page.lwIsFollowing() && pans < 40) { pressKey("ArrowRight"); pans++; }
assert.equal(page.lwIsFollowing(), true, "user pan-back-to-edge resumes");
assert.equal(page.lwAffordanceVisible(), false, "hidden after manual pan-back");
assert.equal(page.lwChevronVisible(), false, "chevron hidden after manual pan-back");
console.log(JSON.stringify({
  test: "T32", userPans: pans,
  newestSlot: page.lwVisibleRange().newestSlot,
  range: page.lwVisibleRange().range, following: page.lwIsFollowing(),
  badge: page.lwAffordanceVisible(), chevron: page.lwChevronVisible(),
}));
""")
    assert payload["test"] == "T32"
    assert payload["newestSlot"] == 60 + 3 + 2 - 1
    assert payload["following"] is True
    assert payload["badge"] is False
    assert payload["chevron"] is False
    rng = payload["range"]
    assert rng["from"] <= payload["newestSlot"] <= rng["to"]
