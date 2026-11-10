"""P18-T3: joint chevron x framing verification (D57 cross-state; AC1).

Composes the P18-T1 chevron (``lwChevronVisible`` / go-to-realtime click)
with the P18-T2 fresh frame (the ``set_visible_range`` directive applied
post-``set_series`` through the existing range-op wire shape): a fresh
frame while following hides the chevron, a fresh frame while
remembered-away shows it, a chevron click after a fresh frame preserves
the remembered gap with follow re-engaged (P21-T4), and Fit/reset after
framing frames all bars plus the gap and leaves the chevron state
consistent via the existing ``fitAndFollow`` path.

Each case shells out to ``node`` with the same self-contained harness
``test_d57_chevron.py`` uses: the REAL page glue (``chart.js`` +
``envelope.js``) against the stubbed document (with button creation, so the
page takes its ensure-or-create chevron path) and the fake
LightweightCharts 5.x tree, driven through the real ``lwApplyOps`` and
queried through the real ``lwChevronVisible`` / ``lwGoToRealtime`` /
``lwFit`` / ``lwIsFollowing`` surface, including the real ``bindKeyboard``
pan path (AR-P11-1). Verifies joint behaviour only — edits no production
files.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The harness prelude: stub document (with button creation) + fake 5.x tree,
# then boot the real page. Mirrors test_d57_chevron.py (same library
# behaviours: setData frames the fresh series, update leaves the visible
# range untouched, fitContent frames all loaded bars, scrollToRealTime shows
# the realtime edge preserving the span) plus the S-P18-1 chevron button.
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
    addSeries(ctor) {
      return _fakeSeries(ctor !== globalThis.LightweightCharts.HistogramSeries);
    },
    addCandlestickSeries() { return _fakeSeries(true); },
    addLineSeries() { return _fakeSeries(true); },
    addAreaSeries() { return _fakeSeries(true); },
    addHistogramSeries() { return _fakeSeries(false); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    applyOptions() {},
  };
}
function _makeButton() {
  return {
    tagName: "BUTTON",
    textContent: "",
    hidden: false,
    disabled: false,
    style: {},
    _attrs: {},
    _listeners: {},
    setAttribute(k, v) { this._attrs[String(k)] = String(v); },
    getAttribute(k) { return (k in this._attrs) ? this._attrs[k] : null; },
    addEventListener(t, f) { this._listeners[t] = f; },
  };
}
const _fakeEl = {
  clientWidth: 960,
  clientHeight: 850,
  style: {},
  _listeners: {},
  _children: [],
  addEventListener(type, fn) { this._listeners[type] = fn; },
  appendChild(child) { this._children.push(child); return child; },
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
  getElementById(id) {
    if (id === "chart") return _fakeEl;
    return null; // no static #goToLatest here: the page creates the button
  },
  createElement(tag) {
    if (String(tag).toLowerCase() !== "button") return null;
    return _makeButton();
  },
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
function applyFrame(from, to, following) {
  // The S-P18-3 wire shape the Python side emits post-set_series through
  // the existing range-op path (AR-P18-5: ordered after the rows).
  const res = page.lwApplyOps({
    v: 1,
    ops: [{ op: "set_visible_range",
             range: { from, to }, following }],
  });
  assert.equal(res.error, null, "frame envelope applies");
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
function chevronButton() {
  const btns = _fakeEl._children.filter(function (e) {
    return e && e.tagName === "BUTTON";
  });
  assert.equal(btns.length, 1, "exactly one chevron button in the chart DOM");
  return btns[0];
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


def test_p18_t3_t31_fresh_frame_while_following_hides_chevron():
    """P18-T3-T31 (AC1): a fresh frame under follow hides the chevron.

    A tracking S-P18-3 frame (live edge inside the range, following encoded)
    applied over a seeded series derives following, so the away-only
    chevron hides — framing and chevron compose with no interaction defect.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwChevronVisible, "function", "chevron probe exists");
const N = 60;
seedCandles(N);
assert.equal(page.lwIsFollowing(), true, "seeded edge follows");
// A fresh tracking frame as the Python side emits it (live edge inside
// the range with the newest-window right padding, following encoded).
applyFrame(N - 15, N - 1 + 2, true);
const probe = page.lwVisibleRange();
assert.equal(probe.newestSlot, N - 1, "series unchanged under the frame");
assert.ok(probe.range.from <= probe.newestSlot &&
          probe.newestSlot <= probe.range.to, "frame tracks the live edge");
assert.equal(page.lwIsFollowing(), true, "frame derives following");
assert.equal(page.lwChevronVisible(), false, "chevron hidden: fresh frame + follow");
assert.equal(chevronButton().hidden, true, "button hidden: fresh frame + follow");
console.log(JSON.stringify({
  test: "T31-follow", newestSlot: probe.newestSlot,
  range: probe.range, following: page.lwIsFollowing(),
  chevron: page.lwChevronVisible(),
}));
""")
    assert payload["test"] == "T31-follow"
    assert payload["newestSlot"] == 60 - 1
    assert payload["following"] is True
    assert payload["chevron"] is False


def test_p18_t3_t31_fresh_frame_while_remembered_away_shows_chevron():
    """P18-T3-T31 (AC1): a fresh frame under remembered-away shows it.

    A minimally back-shifted S-P18-3 frame (newest slot outside the range,
    away encoded per AP-P18-3) derives away, so the away-only chevron shows
    — the remembered-away encoding stays honest under the derivation model.
    """
    payload = _run_node(r"""
const N = 60;
seedCandles(N);
// A fresh remembered-away frame as the Python side emits it (minimal
// back-shift: the newest slot falls just outside the range).
applyFrame(N - 16, N - 2, false);
const probe = page.lwVisibleRange();
assert.equal(probe.newestSlot, N - 1, "series unchanged under the frame");
assert.ok(!(probe.range.from <= probe.newestSlot &&
            probe.newestSlot <= probe.range.to),
          "back-shifted frame derives away");
assert.equal(page.lwIsFollowing(), false, "away derives honestly");
assert.equal(page.lwChevronVisible(), true, "chevron shown: fresh frame + away");
assert.equal(chevronButton().hidden, false, "button shown: fresh frame + away");
console.log(JSON.stringify({
  test: "T31-away", newestSlot: probe.newestSlot,
  range: probe.range, following: page.lwIsFollowing(),
  chevron: page.lwChevronVisible(),
}));
""")
    assert payload["test"] == "T31-away"
    assert payload["newestSlot"] == 60 - 1
    assert payload["following"] is False
    assert payload["chevron"] is True


def test_p18_t3_t31_chevron_click_after_fresh_frame_lands_live_edge():
    """P18-T3-T31 (AC1) as re-pinned by P21-T4 (S-P21-2 preserve semantics).

    From a fresh remembered-away frame with new bars on board, invoking the
    chevron's own click wiring preserves the remembered gap (established by
    a gap-carrying tracking frame before the away frame): the post-click
    range keeps the pre-click span and lands the newest bar at gap G,
    re-engages follow, consumes the badge and hides the chevron — through
    the preserve ``goToRealtime`` path, not the retired edge-pin scroll.
    """
    payload = _run_node(r"""
const N = 60;
seedCandles(N);
// Establish the remembered gap (G) through a frame-carrying envelope
// before going away: a tracking frame with right padding.
const G = 2;
applyFrame(N - 15, N - 1 + G, true);
assert.equal(page.lwIsFollowing(), true, "framed tracking follows");
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
// A fresh remembered-away frame over the grown series (minimal
// back-shift, away encoded) — the joint state under test. The remembered
// gap survives the away frame (only following ranges refresh it).
const newest = page.lwVisibleRange().newestSlot;
applyFrame(newest - 17, newest - 1, false);
assert.equal(page.lwIsFollowing(), false, "framed away");
assert.equal(page.lwChevronVisible(), true, "chevron shown on the fresh away frame");
const before = page.lwVisibleRange().range;
const span = before.to - before.from;
// Click the chevron itself — the wired goToRealtime path, not the probe.
chevronButton()._listeners["click"]();
const after = page.lwVisibleRange();
assert.equal(after.newestSlot, newest, "series unchanged by the click");
assert.equal(after.range.to - after.newestSlot, G,
  "post-click gap equals the remembered gap");
assert.equal(after.range.to - after.range.from, span,
  "post-click span preserved");
assert.equal(page.lwIsFollowing(), true, "click re-engaged follow");
assert.equal(page.lwAffordanceVisible(), false, "badge consumed");
assert.equal(page.lwChevronVisible(), false, "chevron hidden by derivation");
console.log(JSON.stringify({
  test: "T31-click",
  newestSlot: after.newestSlot, range: after.range,
  following: page.lwIsFollowing(), chevron: page.lwChevronVisible(),
}));
""")
    assert payload["test"] == "T31-click"
    assert payload["newestSlot"] == 60 + 3 - 1
    assert payload["range"] == {"from": 60 + 3 - 1 + 2 - 16, "to": 60 + 3 - 1 + 2}
    assert payload["following"] is True
    assert payload["chevron"] is False


def test_p18_t3_t31_fit_after_framing_keeps_chevron_consistent():
    """P18-T3-T31 (AC1) as re-pinned by P21-T4 (S-P21-2 preserve semantics).

    From a fresh remembered-away frame, Fit/reset frames all loaded bars
    and extends ``to`` by the remembered gap (established by a
    gap-carrying tracking frame before the away frame), so the post-Fit
    range is ``{0, newest+G}`` with follow re-engaged and the chevron
    hidden by derivation — no stuck-visible or stuck-hidden state.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwFit, "function", "Fit entry exists");
const N = 60;
seedCandles(N);
// Establish the remembered gap (G) through a frame-carrying envelope,
// then take the fresh remembered-away frame (minimal back-shift, away
// encoded). The gap survives the away frame.
const G = 2;
applyFrame(N - 15, N - 1 + G, true);
assert.equal(page.lwIsFollowing(), true, "framed tracking follows");
applyFrame(N - 16, N - 2, false);
assert.equal(page.lwIsFollowing(), false, "framed away");
assert.equal(page.lwChevronVisible(), true, "chevron shown on the fresh away frame");
// Fit/reset after the frame: all bars framed, gap preserved,
// follow re-engaged, chevron consistent via the existing fitAndFollow path.
assert.equal(page.lwFit(), true, "Fit lands after framing");
const probe = page.lwVisibleRange();
assert.equal(probe.newestSlot, N - 1, "series unchanged by Fit");
assert.equal(probe.range.from, 0, "fit frames from slot 0");
assert.equal(probe.range.to, probe.newestSlot + G, "fit preserves the remembered gap");
assert.equal(page.lwIsFollowing(), true, "follow re-engaged");
assert.equal(page.lwChevronVisible(), false, "chevron hidden after Fit");
assert.equal(chevronButton().hidden, true, "button hidden after Fit");
console.log(JSON.stringify({
  test: "T31-fit", newestSlot: probe.newestSlot,
  range: probe.range, following: page.lwIsFollowing(),
  chevron: page.lwChevronVisible(),
}));
""")
    assert payload["test"] == "T31-fit"
    assert payload["range"] == {"from": 0, "to": 60 - 1 + 2}
    assert payload["following"] is True
    assert payload["chevron"] is False
