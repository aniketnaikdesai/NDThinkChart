/* LwEnvelope — pure op-envelope contract for the LWC bridge (P6-04, D47.4).
 *
 * Shared by chart.js (browser) and envelope.test.js (node). No DOM, no
 * network, no dependencies. Plain <script>-safe and CommonJS-safe (UMD).
 *
 * Envelope: { v: 1, ops: [...] } — exactly these two keys.
 * Every data op carries column arrays (never scalars, never row objects):
 *   { op: "set_bars",   series: "candles", cols: { ts:[...], open:[...],
 *       high:[...], low:[...], close:[...] } }
 *   { op: "update_bar", series: "candles", cols: { ts:[t], open:[o],
 *       high:[h], low:[l], close:[c] } }            (single-element columns)
 *   { op: "set_volume", series: "volume",  cols: { ts:[...], value:[...] } }
 *   { op: "update_bar", series: "volume",  cols: { ts:[t], value:[v] } }
 *   { op: "clear",      series: "<name>" }          (no cols)
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwEnvelope = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ENVELOPE_VERSION = 1;

  var CANDLE_COLS = ["ts", "open", "high", "low", "close"];
  var VOLUME_COLS = ["ts", "value"];

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isInteger(x) {
    return typeof x === "number" && isFinite(x) && Math.floor(x) === x;
  }

  function validateEnvelope(env) {
    if (env === null || typeof env !== "object" || isArray(env)) {
      return { ok: false, error: "envelope must be an object" };
    }
    var keys = Object.keys(env).sort();
    if (keys.length !== 2 || keys[0] !== "ops" || keys[1] !== "v") {
      return { ok: false, error: "envelope must be exactly {v, ops}" };
    }
    if (env.v !== ENVELOPE_VERSION) {
      return { ok: false, error: "unsupported envelope version: " + env.v };
    }
    if (!isArray(env.ops)) {
      return { ok: false, error: "ops must be an array" };
    }
    for (var i = 0; i < env.ops.length; i++) {
      var err = validateOp(env.ops[i]);
      if (err) return { ok: false, error: "ops[" + i + "]: " + err };
    }
    return { ok: true, error: null };
  }

  function validateOp(op) {
    if (op === null || typeof op !== "object" || isArray(op)) {
      return "op must be an object";
    }
    if (typeof op.op !== "string") return "op.op must be a string";
    /* S-P18-3 (D57.2): the fresh-frame directive rides the bar envelope
     * after the rows in the existing range-op wire shape — it is not a
     * series op, so it carries no ``series``/``cols``. Accepted here so
     * the envelope carrying rows + frame still validates; chart.js
     * ``applyOps`` lifts it out before the series application. */
    if (op.op === "set_visible_range") {
      if (op.range === null || typeof op.range !== "object" ||
          isArray(op.range)) {
        return "range must be an object";
      }
      if (typeof op.range.from !== "number" ||
          typeof op.range.to !== "number" ||
          !isFinite(op.range.from) || !isFinite(op.range.to)) {
        return "range.from/to must be finite numbers";
      }
      return null;
    }
    /* S-P25-2 (D67.2): the partial-marker directive rides the bar envelope
     * beside the fresh frame — it annotates one candle, so it is not a
     * series op and carries no ``series``/``cols``. Accepted here so the
     * envelope carrying rows + marker validates; chart.js ``applyOps``
     * lifts it out before the series application. */
    if (op.op === "set_partial") {
      if (!isInteger(op.ts)) return "ts must be an integer";
      if (typeof op.partial !== "boolean") return "partial must be a boolean";
      if ("series" in op) return "set_partial must not carry series";
      if ("cols" in op) return "set_partial must not carry cols";
      return null;
    }
    if (typeof op.series !== "string" || op.series.length === 0) {
      return "op.series must be a non-empty string";
    }
    if (op.op === "clear") {
      if ("cols" in op) return "clear must not carry cols";
      return null;
    }
    var want = null;
    if (op.series === "candles") want = CANDLE_COLS;
    else if (op.series === "volume") want = VOLUME_COLS;
    else return "unknown series: " + op.series;
    if (op.op !== "set_bars" && op.op !== "set_volume" && op.op !== "update_bar") {
      return "unknown op: " + op.op;
    }
    if (op.op === "update_bar" && op.series === "candles" && want !== CANDLE_COLS) {
      return "unreachable";
    }
    var cols = op.cols;
    if (cols === null || typeof cols !== "object" || isArray(cols)) {
      return "op.cols must be an object of arrays";
    }
    var names = Object.keys(cols).sort();
    var sorted = want.slice().sort();
    if (names.length !== sorted.length) return "cols must be exactly " + want.join(",");
    for (var i = 0; i < sorted.length; i++) {
      if (names[i] !== sorted[i]) return "cols must be exactly " + want.join(",");
      if (!isArray(cols[names[i]])) return "cols." + names[i] + " must be an array";
    }
    var n = cols[want[0]].length;
    for (var j = 1; j < want.length; j++) {
      if (cols[want[j]].length !== n) return "column arrays must share one length";
    }
    if (op.op === "update_bar" && n !== 1) {
      return "update_bar must carry single-element columns";
    }
    return null;
  }

  /* Expand one data op into row objects { time, open, high, low, close } or
   * { time, value }. Times are integer unix timestamps (JS receives
   * timestamps and prices only — no formatted strings). */
  function rowsOf(op) {
    if (op.op === "clear") return [];
    var cols = op.cols;
    var n = cols.ts.length;
    var rows = new Array(n);
    for (var i = 0; i < n; i++) {
      var row = { time: cols.ts[i] };
      if (op.series === "candles") {
        row.open = cols.open[i];
        row.high = cols.high[i];
        row.low = cols.low[i];
        row.close = cols.close[i];
      } else {
        row.value = cols.value[i];
      }
      rows[i] = row;
    }
    return rows;
  }

  /* S-P25-6 (D70): the one whitespace predicate — a whitespace row is not a
   * bar. Candles: ``open`` or ``close`` is null; volume: ``value`` is null.
   * Stated once, here, and shared by ``mergeRows`` (the fold) and
   * ``chart.js`` (the display/snapshot helpers), mirroring Python's
   * ``ui/lwc_bridge.py::_candle_row_is_whitespace``. On a replace a
   * whitespace row is skipped; on an upsert it removes that time. */
  function isWhitespaceRow(series, row) {
    if (!row) return true;
    if (series === "volume") {
      return row.value === null || row.value === undefined;
    }
    return (row.open === null || row.open === undefined ||
            row.close === null || row.close === undefined);
  }

  /* Idempotent replay: fold an op list onto a base row array keyed by time.
   * set_bars/set_volume replace the series; update_bar upserts one row;
   * clear empties it. A whitespace row is not a bar in either branch (skip
   * on a replace, delete its time on an upsert), so the fold agrees with
   * the Python reconstruction and with ``lwSnapshot()``. Replaying the same
   * log twice yields the same array — the replay-identity property the
   * Python side asserts in T13. */
  function mergeRows(base, ops) {
    var byTime = {};
    var k;
    for (k = 0; k < base.length; k++) byTime[base[k].time] = base[k];
    for (var o = 0; o < ops.length; o++) {
      var op = ops[o];
      if (op.op === "clear") {
        byTime = {};
      } else if (op.op === "set_bars" || op.op === "set_volume") {
        var rows = rowsOf(op);
        byTime = {};
        for (k = 0; k < rows.length; k++) {
          if (isWhitespaceRow(op.series, rows[k])) continue;
          byTime[rows[k].time] = rows[k];
        }
      } else if (op.op === "update_bar") {
        var one = rowsOf(op)[0];
        if (isWhitespaceRow(op.series, one)) {
          delete byTime[one.time];
        } else {
          byTime[one.time] = one;
        }
      }
    }
    var times = Object.keys(byTime).map(Number).sort(function (a, b) { return a - b; });
    return times.map(function (t) { return byTime[t]; });
  }

  return {
    ENVELOPE_VERSION: ENVELOPE_VERSION,
    validateEnvelope: validateEnvelope,
    validateOp: validateOp,
    rowsOf: rowsOf,
    mergeRows: mergeRows,
    /* S-P25-6: the fold's whitespace predicate is exported so chart.js uses
     * this one definition instead of carrying a second copy (D70). */
    isWhitespaceRow: isWhitespaceRow,
  };
});
