/* chart.js — LWC core-chart glue (P6-04 host + P6-05 Phase 3 core chart).
 * Offline: only the vendored relative scripts from chart.html are available
 * here. Applies batched {v:1,ops:[]} envelopes idempotently; JS receives
 * timestamps and prices only (renderer boundary — no formatted strings
 * inbound, no trading logic).
 *
 * P6-05 (D47.5 + T10):
 * - v5 panes: the price pane carries the per-mode series, the volume pane
 *   the histogram on its own scale (scaleMargins keep the panes apart).
 * - real UTC time axis (Q-20): the `ts` column carries each bar's own UTC
 *   epoch seconds, not a logical index — the axis labels real dates. The
 *   library places bars by data index, so a collapsed non-trading gap still
 *   renders adjacent. A within-session hole crosses as whitespace
 *   placeholders (a row whose OHLC/value slots are null — `seriesRows` turns
 *   it into `{time}` only), so the hole keeps its empty slots (AC-D21.4.4).
 *   `lwSnapshot()` keeps the real bars only: a placeholder is not a bar.
 * - custom tz formatters: `local = t - offset` (`tzLabel`, wired as the
 *   localisation timeFormatter and the time-scale tickMarkFormatter).
 * - per-mode series: `candles` / `hollow` / `heikin` / `line` / `area`.
 *   The mode travels on the candles `set_bars` op as an optional `mode`
 *   key (accepted-and-ignored by the P6-04 validators, so the wire
 *   contract and replay identity are unchanged); the hollow style is a
 *   border-only candlestick, line/area read the close leg of the same
 *   candle rows, and volume colours derive from the candle snapshot.
 * - live `series.update`: `update_bar` ops call `.update()` on the live
 *   series (history is never resent for a tick); `set_*` ops replace via
 *   `.setData()`. Replaying the full op log twice stays a no-op.
 * - `barSpacing` replaces the density caps (T10 / Q60 YES / A106): the
 *   no-overlap guarantee is restated in `barSpacing` terms (DG94) by
 *   `barGeometry` — gap >= 0 always, gap > 0 whenever the spacing allows.
 * - volume pane ceiling (Q-9 / AC-D21.2.1, the D21.2 port): the histogram's
 *   own price scale is priced from the *visible* range —
 *   `maxValue = 1.10 x max(volume of the visible bars)`, the
 *   `VOLUME_NICE_FLOOR` (100) when no bar is visible or every visible bar
 *   is zero, `minValue` always 0 (D21.1). It rides an
 *   `autoscaleInfoProvider` over
 *   `chart.timeScale().getVisibleLogicalRange()`, so load/pan/zoom re-price
 *   engine-side with no per-gesture round-trip to Python.
 *
 * Node note: the pure core below (MODES, tzLabel, barGeometry,
 * describeOp, volumeBarColor, volumeScaleRange) has no DOM dependency and is exported for
 * `node --test` when loaded as a module; the browser boot at the bottom
 * runs only where `document` exists.
 */

/* ── pure core (no DOM, no chart library) ─────────────────────────── */

var LwChartModes = ["candles", "hollow", "heikin", "line", "area"];

var LW_UP_COLOR = "#34d399";
var LW_DOWN_COLOR = "#f87171";

function lwIsMode(value) {
  return LwChartModes.indexOf(value) !== -1;
}

/* Custom tz formatter: `local = t - offset` (seconds), rendered as
 * MM/DD HH:MM in UTC math — the mirror of the Python driver's
 * `format_tz_label`. */
function tzLabel(t, offsetSeconds) {
  var local = Number(t) - Number(offsetSeconds || 0);
  var d = new Date(local * 1000);
  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }
  return (
    pad(d.getUTCMonth() + 1) +
    "/" +
    pad(d.getUTCDate()) +
    " " +
    pad(d.getUTCHours()) +
    ":" +
    pad(d.getUTCMinutes())
  );
}

/* DG94 restatement: with library spacing S (px per bar) the body is
 * min(S, max(0.65*S, floor)) so the gap S - body is >= 0 always and
 * > 0 whenever S exceeds the floor. Mirrors the Python driver's
 * `bar_spacing_geometry`. */
function barGeometry(barSpacingPx, floorPx) {
  var floor = floorPx === undefined ? 4.0 : floorPx;
  if (!(barSpacingPx > 0)) throw new Error("barSpacingPx must be positive");
  var body = Math.min(barSpacingPx, Math.max(0.65 * barSpacingPx, floor));
  return { body: body, gap: barSpacingPx - body };
}

function volumeBarColor(open, close) {
  return close >= open ? LW_UP_COLOR : LW_DOWN_COLOR;
}

/* ── volume ceiling (Q-9 / AC-D21.2.1, the D21.2 port) ─────────────
 * The default engine's reference is `chart_model.visible_volume_ceiling`:
 *   visible_max > 0  -> 1.10 x visible_max
 *   otherwise        -> VOLUME_NICE_FLOOR (100)
 * with Y minimum always 0 (D21.1). The small positive band
 * `0 < visible_max <= 90.9` keeps the literal 1.10 x max — a second
 * unconditional `< 100` clamp would wrongly inflate 10 -> 100 instead of
 * 11 (ESC-028); never reintroduce it. */
var VOLUME_CEILING_FACTOR = 1.1;
var VOLUME_NICE_FLOOR = 100;

/* Max volume of the bars whose slot intersects `[from, to]` in the time
 * scale's own unit (real UTC seconds — see the header). A bar centred on an
 * endpoint is visible. Non-finite / negative volumes read as 0: a hole is
 * not a volume spike. Returns 0 when nothing is visible. */
function visibleVolumeMax(rows, from, to) {
  // A missing range (before the chart has ever been laid out) is not the
  // range [0, 0] — it is "nothing visible", which is the floor.
  if (from === null || from === undefined || to === null || to === undefined) {
    return 0;
  }
  var lo = Number(from);
  var hi = Number(to);
  if (!isFinite(lo) || !isFinite(hi)) return 0;
  if (hi < lo) {
    var swap = lo;
    lo = hi;
    hi = swap;
  }
  var rowsIn = rows || [];
  var max = 0;
  for (var i = 0; i < rowsIn.length; i++) {
    var row = rowsIn[i];
    if (!row || row.time === undefined || row.time === null) continue;
    var t = Number(row.time);
    if (!isFinite(t)) continue;
    if (t + 0.5 <= lo || t - 0.5 >= hi) continue;
    var value = Number(row.value);
    if (isFinite(value) && value > max) max = value;
  }
  return max;
}

function volumeCeiling(visibleMax) {
  var m = Number(visibleMax);
  if (isFinite(m) && m > 0) return m * VOLUME_CEILING_FACTOR;
  return VOLUME_NICE_FLOOR;
}

/* The price range the volume pane renders for one logical range: the
 * ceiling from the visible bars, the Y minimum pinned at 0. */
function volumeScaleRange(rows, from, to) {
  return {
    minValue: 0,
    maxValue: volumeCeiling(visibleVolumeMax(rows, from, to)),
  };
}

/* Classify one envelope op for the glue: replace (set_*), upsert
 * (update_bar) or clear — plus the target series family and any mode
 * switch the op carries. Unknown shapes are reported, never thrown. */
function describeOp(op) {
  if (!op || typeof op !== "object") return { action: "ignore" };
  if (op.op === "clear") return { action: "clear", series: op.series || "" };
  if (op.op === "set_bars" || op.op === "set_volume") {
    return {
      action: "replace",
      series: op.series || "",
      mode: lwIsMode(op.mode) ? op.mode : null,
    };
  }
  if (op.op === "update_bar") {
    return { action: "upsert", series: op.series || "" };
  }
  return { action: "ignore" };
}

/* ── browser glue (browser only; node loads just the pure core) ─── */
if (typeof window !== "undefined" && typeof document !== "undefined") (function () {
  "use strict";

  var chart = null;
  var chartEl = null; // the #chart container (for the width-aware fit)
  var needsFit = false; // data arrived before the container had a width
  var priceSeries = {}; // mode -> series handle (candles/hollow share one)
  var candleSeries = null; // active candlestick handle (candles + hollow)
  var lineSeries = null;
  var areaSeries = null;
  var volumeSeries = null;
  var activeMode = "candles";
  var tzOffset = 0; // seconds behind UTC (18000 EST, 14400 EDT)
  var snapshot = { candles: [], volume: [] }; // last applied rows per series
  /* Q-20 probe state: the labels the axis formatter actually produced. */
  var lastTickLabels = [];

  var HOLLOW_STYLE = {
    upColor: "rgba(52,211,153,0.05)",
    downColor: "rgba(248,113,113,0.05)",
    borderVisible: true,
    borderUpColor: LW_UP_COLOR,
    borderDownColor: LW_DOWN_COLOR,
    wickUpColor: LW_UP_COLOR,
    wickDownColor: LW_DOWN_COLOR,
  };
  var SOLID_STYLE = {
    upColor: LW_UP_COLOR,
    downColor: LW_DOWN_COLOR,
    borderVisible: false,
    wickUpColor: LW_UP_COLOR,
    wickDownColor: LW_DOWN_COLOR,
  };

  function seriesFor(name) {
    if (name === "candles") return visiblePriceSeries();
    return volumeSeries;
  }

  function visiblePriceSeries() {
    if (activeMode === "line") return lineSeries;
    if (activeMode === "area") return areaSeries;
    return candleSeries;
  }

  function snapshotFor(name) {
    return name === "candles" ? snapshot.candles : snapshot.volume;
  }

  function setSnapshot(name, rows) {
    if (name === "candles") snapshot.candles = rows;
    else snapshot.volume = rows;
  }

  function withColor(rows) {
    var byTime = {};
    for (var i = 0; i < snapshot.candles.length; i++) {
      byTime[snapshot.candles[i].time] = snapshot.candles[i];
    }
    return rows.map(function (r) {
      /* Q-20: a placeholder row stays a placeholder — never a zero bar. */
      if (isWhitespaceRow("volume", r)) return { time: r.time };
      var candle = byTime[r.time];
      var color = candle
        ? volumeBarColor(candle.open, candle.close)
        : LW_UP_COLOR;
      return { time: r.time, value: r.value, color: color };
    });
  }

  /* Q-20 whitespace: a row whose value slots are null is a placeholder, not
   * a bar. `seriesRows` turns it into `{time}` only (the library's own
   * whitespace point), so a within-session hole keeps its empty slots
   * (AC-D21.4.4); `barRows` drops it from the snapshot, which is the real
   * series the page reports and the volume pane prices. */
  function isWhitespaceRow(name, row) {
    if (!row) return true;
    if (name === "volume") {
      return row.value === null || row.value === undefined;
    }
    return (row.open === null || row.open === undefined ||
            row.close === null || row.close === undefined);
  }

  function seriesRows(name, rows) {
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      out.push(isWhitespaceRow(name, row) ? { time: row.time } : row);
    }
    return out;
  }

  function barRows(name, rows) {
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      if (!isWhitespaceRow(name, rows[i])) out.push(rows[i]);
    }
    return out;
  }

  /* Q-9 / AC-D21.2.1: the range the volume pane should render right now.
   * Read fresh on every autoscale, from the visible logical range and the
   * raw volume snapshot — never a cached "max of everything". */
  function currentVolumeRange() {
    var range = chart ? chart.timeScale().getVisibleLogicalRange() : null;
    if (!range) return { minValue: 0, maxValue: VOLUME_NICE_FLOOR };
    return volumeScaleRange(snapshot.volume, range.from, range.to);
  }

  function applyMode(mode) {    if (!lwIsMode(mode)) return activeMode;
    activeMode = mode;
    var showCandles = mode === "candles" || mode === "hollow" || mode === "heikin";
    if (candleSeries) {
      candleSeries.applyOptions({ visible: showCandles });
      candleSeries.applyOptions(mode === "hollow" ? HOLLOW_STYLE : SOLID_STYLE);
    }
    if (lineSeries) lineSeries.applyOptions({ visible: mode === "line" });
    if (areaSeries) areaSeries.applyOptions({ visible: mode === "area" });
    // Line/area read the close leg of the shared candle snapshot.
    if ((mode === "line" || mode === "area") && snapshot.candles.length) {
      var rows = snapshot.candles.map(function (r) {
        /* A missing close (never present in the snapshot) is a hole. */
        return (r.close === null || r.close === undefined)
          ? { time: r.time }
          : { time: r.time, value: r.close };
      });
      var target = mode === "line" ? lineSeries : areaSeries;
      if (target) target.setData(rows);
    }
    return activeMode;
  }

  /* v5 series API bridge (Q-14). The vendored tree is lightweight-charts
   * 5.2.1, where `chart.addCandlestickSeries` / `addLineSeries` /
   * `addAreaSeries` / `addHistogramSeries` no longer exist: a series is created
   * with `chart.addSeries(LightweightCharts.<Ctor>, options)` (the pattern
   * studies.js already uses). Without this, init() throws on the first series
   * and the canvas never leaves the background colour — a blank chart even
   * when the host itself is constructed. The v4 method names stay as a
   * fallback so an older vendored tree still boots. */
  function addSeries(ctorName, options, legacyMethod) {
    var lib = typeof LightweightCharts !== "undefined" ? LightweightCharts : null;
    if (lib && typeof chart.addSeries === "function" && lib[ctorName]) {
      return chart.addSeries(lib[ctorName], options);
    }
    if (legacyMethod && typeof chart[legacyMethod] === "function") {
      return chart[legacyMethod](options);
    }
    return null;
  }

  function addHistogramSeries(options) {
    return addSeries("HistogramSeries", options, "addHistogramSeries");
  }

  function init() {
    if (typeof LightweightCharts === "undefined") {
      document.title = "LWC runtime missing (vendored asset not served)";
      return;
    }
    var el = document.getElementById("chart");
    chartEl = el;
    chart = LightweightCharts.createChart(el, {
      layout: { background: { color: "#0d0f14" }, textColor: "#e5e7eb" },
      grid: {
        vertLines: { color: "rgba(148,163,184,0.08)" },
        horzLines: { color: "rgba(148,163,184,0.08)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { timeVisible: true, secondsVisible: false, barSpacing: 8 },
      localization: {
        timeFormatter: function (t) {
          return tzLabel(t, tzOffset);
        },
      },
    });
    chart.timeScale().applyOptions({
      tickMarkFormatter: function (t) {
        var label = tzLabel(t, tzOffset);
        recordTick(t, label);
        return label;
      },
    });
    // Price pane (per-mode series) + volume pane (own scale).
    candleSeries = addSeries("CandlestickSeries", {}, "addCandlestickSeries");
    lineSeries = addSeries(
      "LineSeries",
      { color: "#60a5fa", lineWidth: 2 },
      "addLineSeries",
    );
    areaSeries = addSeries(
      "AreaSeries",
      {
        lineColor: "#60a5fa",
        topColor: "rgba(96,165,250,0.4)",
        bottomColor: "rgba(96,165,250,0.0)",
      },
      "addAreaSeries",
    );
    if (lineSeries) lineSeries.applyOptions({ visible: false });
    if (areaSeries) areaSeries.applyOptions({ visible: false });
    priceSeries = {
      candles: candleSeries,
      hollow: candleSeries,
      heikin: candleSeries,
      line: lineSeries,
      area: areaSeries,
    };
    volumeSeries = addHistogramSeries({ priceScaleId: "vol" });
    // Q-9 / AC-D21.2.1: the volume pane's ceiling follows the *visible*
    // range, re-priced by the library on every autoscale (load, pan, zoom)
    // from the snapshot the driver already sent — no per-gesture round-trip
    // to Python. The price pane's autoscale is untouched.
    if (volumeSeries) {
      volumeSeries.applyOptions({
        autoscaleInfoProvider: function () {
          return { priceRange: currentVolumeRange() };
        },
      });
    }
    chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
    /* The Qt host sizes the page after the first envelope can already have
     * arrived; re-fit once the container finally has a width. */
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(function () {
        if (needsFit) fitToWidth();
      }).observe(el);
    }
    bindKeyboard(el);
    bindChannel();
  }

  /* DG92 focus/keyboard model (lwc-focus-forward-v1): arrows pan the
   * visible range, +/- zoom, Esc blurs back to the Qt focus chain. */
  function bindKeyboard(el) {
    el.addEventListener("keydown", function (ev) {
      if (!chart) return;
      var range = chart.timeScale().getVisibleLogicalRange();
      if (ev.key === "Escape") {
        el.blur();
        if (window.lwBridge && window.lwBridge.focusReleased) {
          window.lwBridge.focusReleased();
        }
        reportKey(ev.key); // Q-20: the key crossed to Python too
      } else if (ev.key === "ArrowLeft" && range) {
        chart.timeScale().setVisibleLogicalRange({ from: range.from - 5, to: range.to - 5 });
        reportKey(ev.key);
        ev.preventDefault();
      } else if (ev.key === "ArrowRight" && range) {
        chart.timeScale().setVisibleLogicalRange({ from: range.from + 5, to: range.to + 5 });
        reportKey(ev.key);
        ev.preventDefault();
      } else if ((ev.key === "+" || ev.key === "=") && range) {
        zoom(range, 0.8);
        reportKey(ev.key);
        ev.preventDefault();
      } else if (ev.key === "-" && range) {
        zoom(range, 1.25);
        reportKey(ev.key);
        ev.preventDefault();
      }
    });
  }

  function zoom(range, factor) {
    var mid = (range.from + range.to) / 2;
    var half = ((range.to - range.from) / 2) * factor;
    chart.timeScale().setVisibleLogicalRange({ from: mid - half, to: mid + half });
  }

  /* ── Q-20 probes: what the axis really shows, and the page → Python keys ──
   *
   * `axisProbe` answers with the time scale's own visible *time* values — real
   * UTC epoch seconds now, so a logical-index axis would report 0..N-1 here
   * (the 1970 label the owner saw). `ticks` are the labels the formatter
   * actually produced during layout (empty when the page has never painted);
   * every entry is a rendered tick, never a recomputed guess. */
  function recordTick(t, label) {
    lastTickLabels.push({ time: Number(t), label: label });
    if (lastTickLabels.length > 24) lastTickLabels.shift();
  }

  function axisProbe() {
    if (!chart) return null;
    var scale = chart.timeScale();
    var range = (typeof scale.getVisibleRange === "function")
      ? scale.getVisibleRange()
      : null;
    var logical = (typeof scale.getVisibleLogicalRange === "function")
      ? scale.getVisibleLogicalRange()
      : null;
    var rows = snapshot.candles;
    var first = rows.length ? Number(rows[0].time) : null;
    var last = rows.length ? Number(rows[rows.length - 1].time) : null;
    return {
      from: range ? Number(range.from) : null,
      to: range ? Number(range.to) : null,
      logical: logical
        ? { from: Number(logical.from), to: Number(logical.to) }
        : null,
      firstTime: first,
      lastTime: last,
      firstLabel: first === null ? null : tzLabel(first, tzOffset),
      ticks: lastTickLabels.slice(0),
      tzOffset: tzOffset,
    };
  }

  /* Q-20: a keyboard gesture the page handled crosses to Python (the bridge's
   * `keyPressed` slot takes one JSON string, the mirror of `opsJson`). */
  function reportKey(key, bridge) {
    var target = bridge;
    if (!target && typeof window !== "undefined") target = window.lwBridge;
    if (!target || typeof target.keyPressed !== "function") return false;
    target.keyPressed(JSON.stringify({ key: String(key) }));
    return true;
  }

  function bindChannel() {
    if (typeof QWebChannel === "undefined") return; // offscreen/probe: ops via lwApplyOps
    // eslint-disable-next-line no-undef
    new QWebChannel(qt.webChannelTransport, function (channel) {
      var bridge = channel.objects.lwBridge;
      window.lwBridge = bridge;
      if (!bridge) return;
      // Q-19/S3b+S3c: subscribe to the transport. `opsEmitted(dict)` reaches
      // a JS slot as a Python repr string (`{'v': 1, ...}`), which is not
      // JSON, so the page listens on `opsJson(str)` — the same envelope,
      // serialized Python-side. Nothing else calls applyOps in the app.
      if (bridge.opsJson && typeof bridge.opsJson.connect === "function") {
        bridge.opsJson.connect(function (payload) {
          var env;
          try {
            env = JSON.parse(payload);
          } catch (err) {
            console.error("lwBridge: envelope is not JSON", err);
            return;
          }
          try {
            var result = applyOps(env);
            if (result && result.error) {
              console.warn("lwBridge: envelope rejected:", result.error);
            }
          } catch (err) {
            console.error("lwBridge: applyOps threw", err);
          }
        });
      }
      // Q-19/S3d: readiness is the page's word. The listener above exists
      // only now, so the drain/replay cannot race the QWebChannel setup the
      // way loadFinished did.
      if (typeof bridge.pageReady === "function") bridge.pageReady();
    });
  }

  /* Fit the whole series once the container has a real width. `fitContent()`
   * at width 0 is a no-op: the library later falls back to its default
   * `barSpacing` and shows only the tail, so the first envelope must be
   * remembered and fitted after layout (the Qt host can deliver data before
   * the page viewport has been laid out). */
  function fitToWidth() {
    if (!chart) return;
    if (chartEl && chartEl.clientWidth > 0) {
      chart.timeScale().fitContent();
      needsFit = false;
    } else {
      needsFit = true;
    }
  }

  /* Apply one envelope idempotently; returns { applied, error }.
   * set_bars/set_volume replace the series snapshot; update_bar upserts
   * one row through `series.update` (the live path — history untouched);
   * clear empties. Replaying the full op log twice is a no-op the second
   * time (replay identity, AC-D47.4). A candles set_bars may carry the
   * optional `mode` key selecting the visible per-mode series. */
  function applyOps(env) {
    var check = window.LwEnvelope.validateEnvelope(env);
    if (!check.ok) return { applied: 0, error: check.error };
    var applied = 0;
    for (var i = 0; i < env.ops.length; i++) {
      var op = env.ops[i];
      var kind = describeOp(op);
      if (kind.action === "ignore") continue;
      if (kind.action === "clear") {
        applyRows(op.series, []);
        applied++;
        continue;
      }
      if (kind.mode) applyMode(kind.mode);
      var rows = window.LwEnvelope.rowsOf(op);
      if (kind.action === "upsert") {
        upsertRow(op.series, rows[0]);
      } else {
        applyRows(op.series, rows);
      }
      applied++;
    }
    fitToWidth();
    return { applied: applied, error: null };
  }

  function applyRows(series, rows) {
    var display = (series === "volume")
      ? withColor(rows)
      : seriesRows("candles", rows);
    /* The snapshot is the real series: placeholders are rendering-only and
     * must not inflate the bar count the page reports (Q-20). */
    setSnapshot(series, barRows(series, rows));
    var target = seriesFor(series);
    if (target) target.setData(display);
    if (series === "candles" && (activeMode === "line" || activeMode === "area")) {
      applyMode(activeMode); // refresh the derived close-leg series
    }
  }

  function upsertRow(series, row) {
    if (series === "candles") {
      var next = window.LwEnvelope.mergeRows(snapshot.candles, [
        {
          op: "update_bar",
          series: "candles",
          cols: {
            ts: [row.time],
            open: [row.open],
            high: [row.high],
            low: [row.low],
            close: [row.close],
          },
        },
      ]);
      setSnapshot("candles", next);
      var target = seriesFor("candles");
      if (target) target.update(row);
      if (activeMode === "line" || activeMode === "area") {
        var derived = seriesFor("candles");
        if (derived && derived !== target) {
          derived.update({ time: row.time, value: row.close });
        } else if (target) {
          // Single shared snapshot: the visible derived series follows.
          applyMode(activeMode);
        }
      }
    } else {
      var vnext = window.LwEnvelope.mergeRows(
        snapshot.volume.map(function (r) {
          return { time: r.time, value: r.value };
        }),
        [
          {
            op: "update_bar",
            series: "volume",
            cols: { ts: [row.time], value: [row.value] },
          },
        ]
      );
      setSnapshot("volume", vnext);
      if (volumeSeries) {
        var candle = null;
        for (var i = 0; i < snapshot.candles.length; i++) {
          if (snapshot.candles[i].time === row.time) {
            candle = snapshot.candles[i];
            break;
          }
        }
        volumeSeries.update({
          time: row.time,
          value: row.value,
          color: candle ? volumeBarColor(candle.open, candle.close) : LW_UP_COLOR,
        });
      }
    }
  }

  window.lwApplyOps = applyOps;
  window.lwDescribeOp = describeOp;
  window.lwApplyMode = applyMode;
  window.lwTzLabel = tzLabel;
  window.lwBarGeometry = barGeometry;
  // Probe surface for the volume ceiling (Q-9): the range the pane prices
  // for the current visible logical range, computed exactly as the
  // autoscale provider computes it.
  window.lwVolumeRange = currentVolumeRange;
  window.lwConfigure = function (cfg) {
    cfg = cfg || {};
    if (typeof cfg.tzOffset === "number") tzOffset = cfg.tzOffset;
    if (typeof cfg.barSpacing === "number" && chart) {
      chart.timeScale().applyOptions({ barSpacing: cfg.barSpacing });
    }
    return { tzOffset: tzOffset };
  };
  window.lwSnapshot = function () {
    return { candles: snapshot.candles.slice(), volume: snapshot.volume.slice() };
  };
  /* Q-20: the page's own answer for the time axis (real dates, rendered tick
   * labels) — the acceptance evidence the count-only test never had. */
  window.lwAxisProbe = axisProbe;
  window.lwReportKey = reportKey;
  window.lwActiveMode = function () {
    return activeMode;
  };

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})();

/* Node export for `node --test` (browser boot above is document-guarded). */
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    MODES: LwChartModes,
    isMode: lwIsMode,
    tzLabel: tzLabel,
    barGeometry: barGeometry,
    describeOp: describeOp,
    volumeBarColor: volumeBarColor,
    visibleVolumeMax: visibleVolumeMax,
    volumeCeiling: volumeCeiling,
    volumeScaleRange: volumeScaleRange,
    VOLUME_CEILING_FACTOR: VOLUME_CEILING_FACTOR,
    VOLUME_NICE_FLOOR: VOLUME_NICE_FLOOR,
  };
}
