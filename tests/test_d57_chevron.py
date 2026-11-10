"""P18-T1: visible go-to-latest chevron (D57.1; S-P18-1) — pytest half.

The behavioural probes live here (not in ``chart_assets/lwc/chart.test.js``,
which owns the T12 unit cases): each test shells out to ``node`` with a
self-contained harness that boots the REAL page glue (``chart.js`` +
``envelope.js``) against the same stubbed document / fake LightweightCharts
5.x tree ``test_p11_fit_affordance.py`` uses — a seeded series driven through
the real ``lwApplyOps`` and queried through the real ``lwChevronVisible`` /
``lwGoToRealtime`` / ``lwIsFollowing`` surface, including the real
``bindKeyboard`` pan path (AR-P11-1). The stub document additionally offers
``createElement("button")`` so the page exercises its ensure-or-create
chevron path with production attributes; the static ``chart.html`` button
markup and CSS are asserted directly off the file.

Red pre-fix (no chevron surface: ``lwChevronVisible`` undefined), green
post-fix (away-only visibility incl. the away-without-new-bars cell that is
red against the old away-AND-new-bars badge rule, click-through-goToRealtime,
glyph-only bottom-right DOM with no polling).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The harness prelude: stub document (with button creation) + fake 5.x tree,
# then boot the real page. Mirrors test_p11_fit_affordance.py (same library
# behaviours: setData frames the fresh series, update leaves the visible
# range untouched, fitContent frames all loaded bars, scrollToRealTime shows
# the realtime edge preserving the span) plus the S-P18-1 entry under test:
# lwChevronVisible. getElementById("goToLatest") answers null so the page
# takes its createElement path (identical attributes to the static HTML).
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


def test_p18_t1_t11_chevron_away_only_matrix():
    """P18-T1-T11 (AC1): chevron visible iff away, new bars or not.

    The viewport-state x new-bars matrix through ``lwChevronVisible``: away
    + new bars and away + no new bars assert visible; following + new bars
    and following + no new bars assert hidden. The away-alone cell is the
    red-first proof: the old badge rule (``lwAffordanceVisible``) keeps it
    hidden while the chevron shows.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwChevronVisible, "function", "chevron probe exists");
const N = 60;
seedCandles(N);
// Following + no new bars: hidden.
assert.equal(page.lwIsFollowing(), true, "seeded edge follows");
assert.equal(page.lwChevronVisible(), false, "hidden: following, no new bars");
// Away + no new bars: SHOWN — red against the old badge rule.
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
assert.equal(page.lwAffordanceVisible(), false, "badge hidden (old away-AND-new-bars rule)");
assert.equal(page.lwChevronVisible(), true, "shown: away, no new bars");
// Away + new bars: shown.
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
assert.equal(page.lwIsFollowing(), false, "bars alone never resume");
assert.equal(page.lwChevronVisible(), true, "shown: away + new bars");
// Following + new bars: hidden (resume, then grow under the edge).
page.lwGoToRealtime();
assert.equal(page.lwIsFollowing(), true, "resume re-engages follow");
lastT += 300;
liveTick(lastT, 106.1, 106.35, 105.85, 106.15, 1300);
assert.equal(page.lwIsFollowing(), true, "live edge keeps following");
assert.equal(page.lwChevronVisible(), false, "hidden: following + new bars");
console.log(JSON.stringify({
  test: "T11", following: page.lwIsFollowing(),
  chevron: page.lwChevronVisible(), newestSlot: page.lwVisibleRange().newestSlot,
}));
""")
    assert payload["test"] == "T11"
    assert payload["following"] is True
    assert payload["chevron"] is False
    assert payload["newestSlot"] == 60 + 3 + 1 - 1


def test_p18_t1_t13_chevron_click_goes_realtime():
    """P18-T1-T13 (AC2) as re-pinned by P21-T4 (S-P21-2 preserve semantics).

    While away, clicking the chevron runs the goToRealtime preserve path:
    the post-click range keeps the pre-click span and lands the newest bar
    at the remembered gap (established here by a frame-carrying envelope),
    follow re-derives true, the badge is consumed and the chevron hides —
    with no call through the retired scrollToRealTime edge-pin.
    """
    payload = _run_node(r"""
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
assert.equal(page.lwIsFollowing(), true, "framed tracking follows");
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
let lastT = BASE + (N - 1) * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  liveTick(lastT, 106.0, 106.25, 105.75, 106.05, 1200);
}
assert.equal(page.lwChevronVisible(), true, "chevron shown while away");
const before = page.lwVisibleRange().range;
const span = before.to - before.from;
// Click the chevron itself — the wired goToRealtime path, not the probe.
chevronButton()._listeners["click"]();
const after = page.lwVisibleRange();
assert.equal(after.newestSlot, N + 3 - 1, "series grew under the away view");
assert.equal(after.range.to - after.newestSlot, G,
  "post-click gap equals the remembered gap");
assert.equal(after.range.to - after.range.from, span,
  "post-click span preserved");
assert.equal(page.lwIsFollowing(), true, "click re-engaged follow");
assert.equal(page.lwAffordanceVisible(), false, "badge consumed");
assert.equal(page.lwChevronVisible(), false, "chevron hidden by derivation");
console.log(JSON.stringify({
  test: "T13",
  newestSlot: after.newestSlot, range: after.range,
  following: page.lwIsFollowing(),
}));
""")
    assert payload["test"] == "T13"
    assert payload["newestSlot"] == 60 + 3 - 1
    assert payload["range"] == {"from": 60 + 3 - 1 + 2 - 16, "to": 60 + 3 - 1 + 2}
    assert payload["following"] is True


def test_p18_t1_t14_chevron_dom_and_coupling():
    """P18-T1-T14 (AC3): glyph-only button, placed, coupled, unpolled.

    The live button carries no text label (glyph only), has an aria-label,
    is a focusable <button>, sits absolute bottom-right of the chart
    container, hides while following and shows while away — and no
    timer/poll drives it (``chart.js`` ships no ``setInterval``; visibility
    flips only on viewport-change notifications, asserted via the static
    markup/CSS plus the live coupling below).
    """
    payload = _run_node(r"""
const N = 60;
seedCandles(N);
// Shape: one glyph-only button with an aria-label, focusable, placed.
const btn = chevronButton();
assert.equal(btn.tagName, "BUTTON", "chevron is a button");
assert.ok(typeof btn.textContent === "string" && btn.textContent.trim().length >= 1,
  "chevron carries a glyph");
assert.ok(!/[A-Za-z]{2,}/.test(btn.textContent), "glyph-only: no text label");
const aria = btn.getAttribute("aria-label");
assert.ok(typeof aria === "string" && aria.length > 0, "chevron labelled for AT");
assert.ok(!btn.disabled, "chevron enabled");
assert.ok(btn.getAttribute("tabindex") !== "-1", "chevron keyboard-focusable");
assert.equal(btn.style.position, "absolute", "chevron overlaid, not in flow");
assert.ok(btn.style.right && btn.style.bottom, "chevron pinned bottom-right");
assert.equal(typeof btn._listeners["click"], "function", "click wired");
// Coupling: hidden while following, shown while away.
assert.equal(page.lwIsFollowing(), true, "seeded edge follows");
assert.equal(page.lwChevronVisible(), false, "hidden while following");
assert.equal(btn.hidden, true, "button hidden while following");
for (let i = 0; i < 6; i++) pressKey("ArrowLeft");
assert.equal(page.lwIsFollowing(), false, "panned away");
assert.equal(page.lwChevronVisible(), true, "shown while away");
assert.equal(btn.hidden, false, "button shown while away");
console.log(JSON.stringify({
  test: "T14", glyph: btn.textContent, aria: aria,
  position: btn.style.position, right: btn.style.right,
  bottom: btn.style.bottom, hiddenWhileFollowing: true,
}));
""")
    assert payload["test"] == "T14"
    assert payload["position"] == "absolute"

    # Static half: the real chart.html carries the same button (markup +
    # CSS), and chart.js drives visibility without any polling timer.
    html = (REPO / "chart_assets" / "lwc" / "chart.html").read_text()
    assert 'id="goToLatest"' in html, "chevron button home"
    assert "aria-label" in html, "chevron labelled in markup"
    assert "hidden" in html, "chevron hidden by default in markup"
    assert "#goToLatest" in html, "chevron CSS present"
    assert "absolute" in html, "chevron overlaid in CSS"
    assert "bottom" in html and "right" in html, "chevron pinned bottom-right in CSS"
    src = (REPO / "chart_assets" / "lwc" / "chart.js").read_text()
    assert "setInterval" not in src, "no polling timer drives the chevron"
    assert "lwChevronVisible" in src, "chevron probe surface present"


def test_p18_t1_t14_empty_chart_chevron_hidden():
    """P18-T1-T14 (AC1/AC3; ESC-105): an empty chart never shows the chevron.

    With no bars the newest slot (-1) fails the follow range check, which
    reads as away — the page-side guard in ``updateChevron`` must still
    answer hidden (probe and button), matching the hidden-by-default
    markup on first paint. No seeding: this is the bare boot state.
    """
    payload = _run_node(r"""
assert.equal(typeof page.lwChevronVisible, "function", "chevron probe exists");
// No seedCandles: the series is empty.
assert.equal(page.lwVisibleRange().newestSlot, -1, "no bars on the empty chart");
assert.equal(page.lwIsFollowing(), false, "empty chart is never following");
assert.equal(page.lwChevronVisible(), false, "hidden: no bars");
const btn = chevronButton();
assert.equal(btn.hidden, true, "button hidden: no bars");
console.log(JSON.stringify({
  test: "T14-empty", chevron: page.lwChevronVisible(), hidden: btn.hidden,
}));
""")
    assert payload["test"] == "T14-empty"
    assert payload["chevron"] is False
    assert payload["hidden"] is True
