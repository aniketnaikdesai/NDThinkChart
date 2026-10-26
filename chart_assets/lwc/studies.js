/* studies.js — LWC study overlays (P6-06 / Phase 4, D47.5).
 *
 * The study channel: `ui/lwc_view.py` publishes one envelope per render —
 * `{v: 1, ops: [{op: "set_study", series: "studies", kind, pane, style,
 * cols: {ts: [...], value: [...]}}, ...]}` — and this module puts those
 * columns onto line/histogram series. Values arrive precomputed from the
 * shared model (`services/chart_model.py` + `indicator_service`) — this
 * side formats and renders, it never computes an indicator. JS receives
 * timestamps and prices only (renderer boundary: no strings in, no trading
 * logic).
 *
 * The bar transport (`ui/lwc_bridge.py` -> `chart_assets/lwc/envelope.js`)
 * pins its series set to candles/volume, so study ops travel on this
 * channel instead of riding the bar envelope; `chart.html` includes this
 * script at cutover and the host page forwards the view's
 * `studyOpsEmitted` envelopes to `LwStudies.applyStudyOps(env)`.
 *
 * Column semantics, mirrored exactly by the Python driver:
 * - `cols.ts` — logical-index times, the same unit as the candles op.
 * - `cols.value` — one nullable price per bar; `null` means the study is
 *   not yet valid for that bar and crosses as whitespace (a `{time}`
 *   row), never as a fabricated 0.
 * - `kind` — the shared model's overlay id: `study_key` + line suffix,
 *   e.g. `"sma:0"`, `"bollinger:0_mid"`, `"macd:1_signal"`.
 * - `pane` — `price` (overlays the candles) or `oscillator` (its own pane).
 *
 * Node note: the pure core below has no DOM/chart dependency and is
 * exported for `node --test`; the glue never boots without a chart handle.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwStudies = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var STUDY_KINDS = ["sma", "ema", "ema2", "vwap", "bollinger", "rsi", "macd"];
  var PRICE_STUDIES = ["sma", "ema", "ema2", "vwap", "bollinger"];
  var OSCILLATOR_STUDIES = ["rsi", "macd"];

  var PANE_PRICE = "price";
  var PANE_OSCILLATOR = "oscillator";

  /* Series suffixes per kind — the shared model's own suffixes. */
  var STUDY_LINES = {
    sma: [""],
    ema: [""],
    ema2: [""],
    vwap: [""],
    bollinger: ["", "_mid", "_lower"],
    rsi: [""],
    macd: ["", "_signal", "_hist"],
  };

  var DEFAULT_COLOR = "#ffffff";
  var HIST_UP_COLOR = "#34d399";
  var HIST_DOWN_COLOR = "#f87171";

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isFiniteNumber(x) {
    return typeof x === "number" && isFinite(x);
  }

  /* Base study kind of an overlay id: "bollinger:0_mid" -> "bollinger".
   * Longest match wins, so "ema2" never degrades to "ema". Unknown heads
   * are returned unchanged. */
  function baseKind(overlayId) {
    var head = String(overlayId === undefined || overlayId === null ? "" : overlayId)
      .split(":")[0];
    var best = "";
    for (var i = 0; i < STUDY_KINDS.length; i++) {
      var kind = STUDY_KINDS[i];
      var hit = head === kind || head.indexOf(kind + "_") === 0;
      if (hit && kind.length > best.length) best = kind;
    }
    return best || head;
  }

  function paneFor(overlayId) {
    return OSCILLATOR_STUDIES.indexOf(baseKind(overlayId)) !== -1
      ? PANE_OSCILLATOR
      : PANE_PRICE;
  }

  /* Column op -> [{time, value|null}]. The null is preserved: it is the
   * "not yet valid" marker the renderer turns into whitespace. */
  function studyRows(op) {
    var cols = (op && op.cols) || {};
    var ts = isArray(cols.ts) ? cols.ts : [];
    var values = isArray(cols.value) ? cols.value : [];
    var rows = new Array(ts.length);
    for (var i = 0; i < ts.length; i++) {
      var v = values[i];
      rows[i] = {
        time: ts[i],
        value: v === null || v === undefined ? null : Number(v),
      };
    }
    return rows;
  }

  /* Column op -> LWC rows: `{time}` (whitespace) where the study is not
   * valid yet, `{time, value}` otherwise. */
  function lineRows(op) {
    return studyRows(op).map(function (row) {
      return row.value === null ? { time: row.time } : { time: row.time, value: row.value };
    });
  }

  function describeStudyOp(op) {
    if (!op || typeof op !== "object" || isArray(op)) return { action: "ignore" };
    if (op.op === "clear_study") return { action: "clear", kind: "*", pane: "*" };
    if (op.op !== "set_study") return { action: "ignore" };
    if (STUDY_KINDS.indexOf(baseKind(op.kind)) === -1) return { action: "ignore" };
    return { action: "replace", kind: op.kind, pane: paneFor(op.kind) };
  }

  function validateOp(op) {
    if (op === null || typeof op !== "object" || isArray(op)) {
      return "op must be an object";
    }
    if (op.series !== "studies") return "op.series must be \"studies\"";
    if (op.op === "clear_study") {
      if ("cols" in op) return "clear_study must not carry cols";
      return null;
    }
    if (op.op !== "set_study") return "unknown op: " + op.op;
    if (typeof op.kind !== "string" || op.kind.length === 0) {
      return "op.kind must be a non-empty string";
    }
    if (STUDY_KINDS.indexOf(baseKind(op.kind)) === -1) {
      return "unknown study kind: " + op.kind;
    }
    if (op.pane !== undefined && op.pane !== paneFor(op.kind)) {
      return "op.pane disagrees with op.kind";
    }
    var cols = op.cols;
    if (cols === null || typeof cols !== "object" || isArray(cols)) {
      return "op.cols must be an object of arrays";
    }
    if (Object.keys(cols).sort().join(",") !== "ts,value") {
      return "cols must be exactly ts,value";
    }
    if (!isArray(cols.ts) || !isArray(cols.value)) {
      return "cols.ts and cols.value must be arrays";
    }
    if (cols.ts.length !== cols.value.length) {
      return "column arrays must share one length";
    }
    for (var i = 0; i < cols.ts.length; i++) {
      if (!isFiniteNumber(cols.ts[i])) return "cols.ts must be finite numbers";
      var v = cols.value[i];
      if (v !== null && !isFiniteNumber(v)) {
        return "cols.value entries must be finite numbers or null";
      }
    }
    return null;
  }

  function validateEnvelope(env) {
    if (env === null || typeof env !== "object" || isArray(env)) {
      return { ok: false, error: "envelope must be an object" };
    }
    var keys = Object.keys(env).sort();
    if (keys.length !== 2 || keys[0] !== "ops" || keys[1] !== "v") {
      return { ok: false, error: "envelope must be exactly {v, ops}" };
    }
    if (env.v !== 1) return { ok: false, error: "unsupported envelope version: " + env.v };
    if (!isArray(env.ops)) return { ok: false, error: "ops must be an array" };
    for (var i = 0; i < env.ops.length; i++) {
      var err = validateOp(env.ops[i]);
      if (err) return { ok: false, error: "ops[" + i + "]: " + err };
    }
    return { ok: true, error: null };
  }

  /* ── chart glue (a chart handle is required; node never reaches this) ── */

  var chartRef = null;
  var seriesByKind = {};
  var snapshotByKind = {};

  function lwcLib() {
    return typeof LightweightCharts === "undefined" ? null : LightweightCharts;
  }

  function lineStyleFor(style) {
    var lib = lwcLib();
    if (!style || style.lineStyle !== "dotted" || !lib || !lib.LineStyle) {
      return lib && lib.LineStyle ? lib.LineStyle.Solid : 0;
    }
    return lib.LineStyle.Dotted;
  }

  function optionsFor(style) {
    style = style || {};
    if (style.type === "histogram") {
      return { priceLineVisible: false, lastValueVisible: false };
    }
    return {
      color: style.color || DEFAULT_COLOR,
      lineWidth: typeof style.width === "number" ? style.width : 1,
      lineStyle: lineStyleFor(style),
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    };
  }

  function seriesFor(chart, kind, style) {
    if (seriesByKind[kind]) return seriesByKind[kind];
    var lib = lwcLib();
    var paneIndex = paneFor(kind) === PANE_OSCILLATOR ? 1 : 0;
    var histogram = !!(style && style.type === "histogram");
    var handle = null;
    if (lib && typeof chart.addSeries === "function") {
      var ctor = histogram ? lib.HistogramSeries : lib.LineSeries;
      handle = chart.addSeries(ctor, optionsFor(style), paneIndex);
    } else if (histogram && typeof chart.addHistogramSeries === "function") {
      handle = chart.addHistogramSeries(optionsFor(style));
    } else if (typeof chart.addLineSeries === "function") {
      handle = chart.addLineSeries(optionsFor(style));
    }
    if (handle) seriesByKind[kind] = handle;
    return handle;
  }

  function clearAll() {
    for (var kind in seriesByKind) {
      if (!Object.prototype.hasOwnProperty.call(seriesByKind, kind)) continue;
      var handle = seriesByKind[kind];
      if (handle && typeof handle.setData === "function") handle.setData([]);
    }
    seriesByKind = {};
    snapshotByKind = {};
  }

  function histColored(rows, style) {
    var up = (style && style.colorUp) || HIST_UP_COLOR;
    var down = (style && style.colorDown) || HIST_DOWN_COLOR;
    return rows.map(function (row) {
      if (row.value === undefined) return row;
      return { time: row.time, value: row.value, color: row.value >= 0 ? up : down };
    });
  }

  /* Apply one study envelope to `chart`; returns {applied, error}. */
  function applyOps(chart, env) {
    var check = validateEnvelope(env);
    if (!check.ok) return { applied: 0, error: check.error };
    if (!chart) return { applied: 0, error: "no chart handle" };
    var applied = 0;
    for (var i = 0; i < env.ops.length; i++) {
      var op = env.ops[i];
      var kind = describeStudyOp(op);
      if (kind.action === "ignore") continue;
      if (kind.action === "clear") {
        clearAll();
        applied++;
        continue;
      }
      var handle = seriesFor(chart, op.kind, op.style);
      if (!handle || typeof handle.setData !== "function") continue;
      var rows = lineRows(op);
      if (op.style && op.style.type === "histogram") rows = histColored(rows, op.style);
      handle.setData(rows);
      snapshotByKind[op.kind] = studyRows(op);
      applied++;
    }
    return { applied: applied, error: null };
  }

  function bind(chart) {
    chartRef = chart || null;
    return chartRef !== null;
  }

  /* The host page forwards the view's study envelopes here. */
  function applyStudyOps(env) {
    return applyOps(chartRef, env);
  }

  function snapshot() {
    var out = {};
    for (var kind in snapshotByKind) {
      if (!Object.prototype.hasOwnProperty.call(snapshotByKind, kind)) continue;
      out[kind] = snapshotByKind[kind].slice();
    }
    return out;
  }

  function clear() {
    clearAll();
  }

  return {
    STUDY_KINDS: STUDY_KINDS,
    PRICE_STUDIES: PRICE_STUDIES,
    OSCILLATOR_STUDIES: OSCILLATOR_STUDIES,
    STUDY_LINES: STUDY_LINES,
    PANE_PRICE: PANE_PRICE,
    PANE_OSCILLATOR: PANE_OSCILLATOR,
    baseKind: baseKind,
    paneFor: paneFor,
    studyRows: studyRows,
    lineRows: lineRows,
    describeStudyOp: describeStudyOp,
    validateOp: validateOp,
    validateEnvelope: validateEnvelope,
    applyOps: applyOps,
    bind: bind,
    applyStudyOps: applyStudyOps,
    snapshot: snapshot,
    clear: clear,
  };
});
