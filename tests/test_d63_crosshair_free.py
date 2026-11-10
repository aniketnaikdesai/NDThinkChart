"""P22-T4 (D63 free cursor-price tracking pin, AC-D63.1).

Repro-first diagnosis (verified on this tree, not assumed): ``chart.js``
``init()`` built the chart with no ``crosshair`` key, so the vendored
default (Magnet, mode 1 — see
``chart_assets/lwc/lightweight-charts.standalone.production.js``) governed
the live chart while ``LwInteraction.applyCrosshair`` (Normal, mode 0) was
never called from any page path — the horizontal line snapped to bar OHLC
instead of tracking the cursor price.

T4-AC1 (integration, node harness with the REAL page glue): offscreen
between-close hover cases asserting the line price equals the cursor price
at rest and across live forming-bar ticks (red-first on the pre-fix tree:
creation carried no crosshair key, so the probe read the Magnet default),
plus the out-of-range clamp edge.
T4-AC2 (unit): source + runtime assertions that no Magnet mode id is
applied and no snap subscriber is registered on any crosshair-touching
path; Normal pinned at creation and on every crosshair-touching
applyOptions.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LWC_DIR = REPO / "chart_assets" / "lwc"
VENDORED = "lightweight-charts.standalone.production.js"

node = shutil.which("node")
needs_node = pytest.mark.skipif(node is None, reason="node is required")


def _strip_js_comments(src: str) -> str:
    """Remove block + line comments (prose may name the removed default)."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _non_vendored_js() -> list[Path]:
    return sorted(
        p for p in LWC_DIR.glob("*.js") if p.name != VENDORED
    )


# The AC1 harness: stub document + fake LightweightCharts 5.x tree that
# mirrors the vendored default (no ``crosshair`` key at creation -> the
# Magnet default governs), then boots the REAL page glue (envelope.js +
# interaction.js + chart.js) and drives it through the real ``lwApplyOps``
# / ``lwCrosshairProbe`` / ``freeLinePrice`` surface.
_AC1_HARNESS = r"""
const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const DIR = %DIR%;

// ── fake 5.x tree (mirrors the vendored default) ──
// The vendored bundle's default crosshair carries mode 1 (Magnet). The fake
// reproduces exactly that: creation options WITHOUT a crosshair key leave
// the live crosshair at mode 1; a crosshair key (the S-P22-4 pin) governs.
let _liveCrosshair = null;      // the chart's live crosshair state
let _creationCrosshair = "unset";
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
function _fakeChart(createOpts) {
  _creationCrosshair = createOpts && createOpts.crosshair
    ? JSON.parse(JSON.stringify(createOpts.crosshair))
    : null; // absent key -> vendored Magnet default governs
  _liveCrosshair = _creationCrosshair
    ? JSON.parse(JSON.stringify(_creationCrosshair))
    : { mode: 1 };
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
    applyOptions(opts) {
      if (opts && opts.crosshair) {
        _liveCrosshair = JSON.parse(JSON.stringify(opts.crosshair));
      }
    },
    options() { return { crosshair: _liveCrosshair }; },
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
  createChart(el, opts) { return _fakeChart(opts || {}); },
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
for (const name of ["LwAlarms", "LwPrimitives",
  "LwOverlays", "LwStudies", "LwGestures"]) {
  globalThis.window[name] = { bind() {} };
}
const read = (name) => readFileSync(DIR + "/" + name, "utf8");
globalThis.window.LwEnvelope = require(DIR + "/envelope.js");
globalThis.window.LwInteraction = require(DIR + "/interaction.js");
const LwChart = require(DIR + "/chart.js");
const page = globalThis.window;

// ── seed: 8 one-minute bars, distinct closes, no two closes equal ──
const N = 8;
const closes = [];
for (let i = 0; i < N; i++) closes.push(100 + i * 0.5);
const ts = [], open = [], high = [], low = [], close = [];
for (let i = 0; i < N; i++) {
  ts.push(1700000000 + i * 60);
  open.push(closes[i] - 0.1);
  high.push(closes[i] + 0.2);
  low.push(closes[i] - 0.2);
  close.push(closes[i]);
}
const LO0 = Math.min(...low);
const HI0 = Math.max(...high);
let lo = LO0;
let hi = HI0;
function trackRange() {
  lo = Math.min(...closes) - 0.2;
  hi = Math.max(...closes) + 0.2;
}
const res = page.lwApplyOps({
  v: 1,
  ops: [
    { op: "set_bars", series: "candles",
      cols: { ts, open, high, low, close } },
    { op: "set_volume", series: "volume",
      cols: { ts, value: ts.map(() => 1000) } },
    { op: "set_visible_range", range: { from: 0, to: N - 1 },
      following: true },
  ],
});
assert.equal(res.error, null, "seed envelope applies");

// Between-close cursor prices: strictly inside (LO, HI), equal to NO
// visible bar close (the AC-D63.1 precondition, guarded explicitly).
function betweenClosePrices(extraCloses) {
  const all = closes.concat(extraCloses || []);
  const out = [];
  for (let i = 0; i < all.length - 1; i++) {
    out.push((all[i] + all[i + 1]) / 2);   // exact midpoint
    out.push(all[i] + (all[i + 1] - all[i]) * 0.1); // off-midpoint
  }
  for (const p of out) {
    assert.ok(!all.some((c) => c === p), `P=${p} must equal no close`);
  }
  return out;
}
function checkIdentity(label, prices) {
  for (const p of prices) {
    assert.equal(
      LwChart.freeLinePrice(p, lo, hi), p,
      `${label}: line price must equal cursor price P=${p}`);
  }
}

// 1. Pinned at creation: the creation options carried Normal (mode 0).
//    Pre-fix this is null -> the Magnet default governed (red-first).
assert.ok(_creationCrosshair, "creation must carry a crosshair key");
assert.equal(_creationCrosshair.mode, 0, "creation pins Normal (mode 0)");

// 2. Live probe: the governing mode is Normal, both lines visible.
let probe = page.lwCrosshairProbe();
assert.equal(probe.mode, 0, "live crosshair mode is Normal");
assert.equal(probe.vertVisible, true);
assert.equal(probe.horzVisible, true);

// 3. At rest: line price equals cursor price at every between-close P.
checkIdentity("at rest", betweenClosePrices());

// 4. Across live forming-bar ticks: same-ts repaint then a new-ts bar.
//    The pin (and the identity) holds continuously, never a bar close.
let tickRes = page.lwApplyOps({
  v: 1,
  ops: [{ op: "update_bar", series: "candles",
    cols: { ts: [ts[N - 1]], open: [open[N - 1]], high: [104.4],
            low: [low[N - 1]], close: [104.2] } }],
});
assert.equal(tickRes.error, null, "forming-bar tick applies");
closes[N - 1] = 104.2;
trackRange();
probe = page.lwCrosshairProbe();
assert.equal(probe.mode, 0, "pin holds across the forming-bar tick");
checkIdentity("forming-bar tick", betweenClosePrices());

const tNew = ts[N - 1] + 60;
tickRes = page.lwApplyOps({
  v: 1,
  ops: [{ op: "update_bar", series: "candles",
    cols: { ts: [tNew], open: [104.2], high: [105.2],
            low: [104.0], close: [105.0] } }],
});
assert.equal(tickRes.error, null, "new-period tick applies");
closes.push(105.0);
trackRange();
probe = page.lwCrosshairProbe();
assert.equal(probe.mode, 0, "pin holds across the new-period tick");
checkIdentity("new-period tick", betweenClosePrices());

// 5. Out-of-range clamp edge (existing library behaviour): beyond the
//    visible scale pins to the edge, never to a bar close.
assert.equal(LwChart.freeLinePrice(hi + 10, lo, hi), hi, "above clamps to HI");
assert.equal(LwChart.freeLinePrice(lo - 10, lo, hi), lo, "below clamps to LO");

console.log(JSON.stringify({ ok: true, closes: closes.length }));
"""


@needs_node
def test_p22_t4_ac1_line_equals_cursor(tmp_path):
    """Line price == cursor price at rest + across live ticks + clamp."""
    harness = tmp_path / "p22_t4_ac1_harness.js"
    harness.write_text(
        _AC1_HARNESS.replace("%DIR%", '"%s"' % LWC_DIR), encoding="utf-8"
    )
    proc = subprocess.run(
        [node, str(harness)], capture_output=True, text=True,
        cwd=str(REPO), timeout=120,
    )
    assert proc.returncode == 0, (
        f"AC1 harness failed:\nSTDOUT:\n{proc.stdout[-2000:]}\n"
        f"STDERR:\n{proc.stderr[-2000:]}"
    )


def test_p22_t4_ac2_no_magnet_no_snap_subscriber():
    """No Magnet mode id, no snap subscriber anywhere (absence half)."""
    for rel in ("chart.js", "interaction.js"):
        src = _strip_js_comments((LWC_DIR / rel).read_text(encoding="utf-8"))
        assert "magnet" not in src.lower(), f"{rel}: Magnet id present"
        assert re.search(r"mode\s*:\s*1\b", src) is None, (
            f"{rel}: Magnet mode id (mode: 1) applied"
        )
        assert "CrosshairMode.Magnet" not in src, f"{rel}: Magnet enum"
    for path in _non_vendored_js():
        src = path.read_text(encoding="utf-8")
        assert "subscribeCrosshairMove" not in src, (
            f"{path.name}: snap subscriber present"
        )
    for path in sorted((REPO / "ui").glob("*.py")):
        src = path.read_text(encoding="utf-8")
        assert "subscribeCrosshairMove" not in src, (
            f"ui/{path.name}: snap subscriber present"
        )
        assert "CrosshairMode" not in src, f"ui/{path.name}: crosshair mode"


def test_p22_t4_ac2_normal_pinned_at_creation_and_apply():
    """Normal pinned at creation + on every crosshair-touching applyOptions."""
    interaction = (LWC_DIR / "interaction.js").read_text(encoding="utf-8")
    assert "CROSSHAIR_MODE_ID = 0" in interaction
    assert "mode: CROSSHAIR_MODE_ID" in interaction

    chart = (LWC_DIR / "chart.js").read_text(encoding="utf-8")
    # Creation: the chartOptions carry the Normal pin.
    assert re.search(
        r"crosshair:\s*crosshairPageOptions\(\)", chart
    ), "creation must pin Normal crosshair options"
    # Every chart-level applyOptions that re-touches chart chrome carries
    # the pin: init wires applyCrosshair to the live chart, applyTz
    # re-asserts it alongside the formatter re-apply.
    assert chart.count("pinCrosshair()") >= 2, (
        "pinCrosshair defined + wired to the live chart at init"
    )
    assert chart.count("crosshairPageOptions()") >= 4, (
        "Normal options supplied at creation, the pin, and the tz re-apply"
    )
    assert "li.applyCrosshair(chart)" in chart, (
        "the existing Normal-mode applyCrosshair must reach the live chart"
    )
    apply_tz = chart[
        chart.index("function applyTz(mode)"):chart.index("function isFollowing()")
    ]
    assert "crosshair" in apply_tz, "applyTz must re-assert the Normal pin"


@needs_node
def test_p22_t4_ac2_apply_crosshair_runtime():
    """The shipped applyCrosshair applies Normal (mode 0) to a chart."""
    script = (
        "const assert = require('node:assert/strict');"
        "const Li = require(%r);"
        "assert.equal(Li.CROSSHAIR_MODE_ID, 0);"
        "assert.equal(Li.crosshairOptions().mode, 0);"
        "let got = null;"
        "const fake = { applyOptions(o) { got = o; } };"
        "const ret = Li.applyCrosshair(fake);"
        "assert.ok(got && got.crosshair, 'applyOptions crossed');"
        "assert.equal(got.crosshair.mode, 0, 'Normal reaches the chart');"
        "assert.equal(ret.crosshair.mode, 0);"
        "assert.equal(Li.applyCrosshair(null), null);"
        "console.log('AC2 runtime pin ok');"
    ) % (str(LWC_DIR / "interaction.js"),)
    proc = subprocess.run(
        [node, "-e", script], capture_output=True, text=True,
        cwd=str(REPO), timeout=120,
    )
    assert proc.returncode == 0, (
        f"AC2 runtime failed:\nSTDOUT:\n{proc.stdout[-2000:]}\n"
        f"STDERR:\n{proc.stderr[-2000:]}"
    )
