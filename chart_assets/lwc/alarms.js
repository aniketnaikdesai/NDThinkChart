/* alarms.js — LWC alarm lines/overlays (P6-08 / Phase 6, D47.5).
 *
 * The alarm channel: `ui/lwc_view.py` publishes one envelope per render —
 * `{v: 1, ops: [{op: "set_alarms", series: "alarms", cols: {...}}]}` — and
 * this module turns those columns into price lines on the candle series.
 * The default engine's reference is `ui/alarm_overlay.py`: the same colour
 * order, the same glyph/label composition, the same z-order, and the same
 * yellow dashed preview line as `ui/chart_panel.py` (D21.10).
 *
 * Column semantics, mirrored exactly by the Python driver:
 * - `cols.id` / `cols.price` — alarm id and price level.
 * - `cols.direction` — `cross_above` / `cross_below` / `cross_either` (the
 *   glyph table below); an unknown direction renders no glyph, as on the
 *   default engine.
 * - `cols.active` / `cols.triggered` / `cols.sound` — the raw alarm state
 *   bits. The colour is derived here, in the same precedence as
 *   `AlarmOverlay._color_for`: triggered -> inactive -> muted -> armed.
 * - `cols.note` — the user's own note text (display data, never a formatted
 *   value from Python).
 *
 * JS receives prices and state only: the label string is composed on this
 * side (`labelText`), exactly as the study labels are composed from values.
 *
 * The bar transport (`ui/lwc_bridge.py` -> `chart_assets/lwc/envelope.js`)
 * pins its series set to candles/volume, so alarm ops travel on this channel
 * instead of riding the bar envelope; `chart.html` includes this script at
 * cutover and the host page forwards the view's `alarmOpsEmitted` envelopes
 * to `LwAlarms.applyAlarmOps(env)`.
 *
 * Library note: LWC price lines accept an integer `lineWidth` (1..4) while
 * the default engine's pen is 1.4 px. The reference width crosses in the op
 * spec unchanged (`spec.width`), and `lineWidthFor()` picks the nearest
 * supported integer for the library call — the one documented visual
 * concession, forced by the library's option type.
 *
 * Node note: the pure core below has no DOM/chart dependency and is
 * exported for `node --test`; the glue never boots without a series handle.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwAlarms = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ENVELOPE_VERSION = 1;
  var ALARM_CHANNEL = "alarms";

  /* Reference colours — value-for-value with ui/alarm_overlay.py. */
  var TRIGGERED_COLOR = "#f87171";
  var ARMED_COLOR = "#fbbf24";
  var MUTED_COLOR = "#94a3b8";
  var INACTIVE_COLOR = "#64748b";

  /* D21.10 preview line — value-for-value with ui/chart_panel.py. */
  var PREVIEW_COLOR = "#ffff00";

  var ALARM_COLORS = {
    triggered: TRIGGERED_COLOR,
    armed: ARMED_COLOR,
    muted: MUTED_COLOR,
    inactive: INACTIVE_COLOR,
  };

  var DIRECTION_GLYPH = {
    cross_above: "\u25B2",
    cross_below: "\u25BC",
    cross_either: "\u25C6",
  };

  /* Pen width / z-order of the default engine's alarm items. */
  var LINE_WIDTH_PX = 1.4;
  var ALARM_LINE_Z = 6;
  var ALARM_LABEL_Z = 7;
  var PREVIEW_LINE_Z = 5;

  /* The label rides the library-native right-edge axis label. */
  var LABEL_ANCHOR = "right";
  var LABEL_MARKER = " \u00b7 ";
  var TRIGGERED_SUFFIX = " (hit)";
  var INACTIVE_SUFFIX = " (off)";
  var MUTED_SUFFIX = " (muted)";

  var ALARM_COLS = ["id", "price", "direction", "active", "triggered", "sound", "note"];
  var BOOL_COLS = ["active", "triggered", "sound"];

  var SOLID = 0;
  var DASHED = 2;

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isFiniteNumber(x) {
    return typeof x === "number" && isFinite(x);
  }

  function isBool(x) {
    return x === true || x === false;
  }

  function glyphFor(direction) {
    return DIRECTION_GLYPH[direction] || "";
  }

  /* f"{price:.4f}" — the default engine's label format. */
  function priceText(price) {
    return Number(price).toFixed(4);
  }

  /* AlarmOverlay._color_for, in the same precedence order. */
  function colorFor(alarm) {
    if (alarm && alarm.triggered) return TRIGGERED_COLOR;
    if (!alarm || !alarm.active) return INACTIVE_COLOR;
    if (!alarm.sound) return MUTED_COLOR;
    return ARMED_COLOR;
  }

  /* AlarmOverlay._label_text: glyph, 4dp price, one state suffix, the note. */
  function labelText(alarm) {
    var text = glyphFor(alarm && alarm.direction) + " " + priceText(alarm ? alarm.price : 0);
    if (alarm && alarm.triggered) {
      text += TRIGGERED_SUFFIX;
    } else if (alarm && !alarm.active) {
      text += INACTIVE_SUFFIX;
    } else if (alarm && !alarm.sound) {
      text += MUTED_SUFFIX;
    }
    if (alarm && alarm.note) text += LABEL_MARKER + alarm.note;
    return text;
  }

  /* One alarm -> the full visual description the engine renders. */
  function lineSpec(alarm) {
    return {
      id: alarm ? alarm.id : null,
      price: Number(alarm ? alarm.price : 0),
      color: colorFor(alarm),
      title: labelText(alarm),
      width: LINE_WIDTH_PX,
      lineStyle: "solid",
      z: ALARM_LINE_Z,
      labelZ: ALARM_LABEL_Z,
      axisLabelVisible: true,
      labelAnchor: LABEL_ANCHOR,
    };
  }

  /* The D21.10 preview line: yellow, dashed, below the alarm lines. */
  function previewSpec(price) {
    return {
      price: Number(price),
      color: PREVIEW_COLOR,
      title: "",
      width: LINE_WIDTH_PX,
      lineStyle: "dashed",
      z: PREVIEW_LINE_Z,
      axisLabelVisible: false,
    };
  }

  /* A `set_alarms` op -> one row object per alarm (raw state, no strings). */
  function alarmRows(op) {
    var cols = (op && op.cols) || {};
    var ts = isArray(cols.id) ? cols.id : [];
    var rows = new Array(ts.length);
    for (var i = 0; i < ts.length; i++) {
      rows[i] = {
        id: cols.id[i],
        price: Number(cols.price[i]),
        direction: cols.direction[i],
        active: cols.active[i],
        triggered: cols.triggered[i],
        sound: cols.sound[i],
        note: cols.note[i],
      };
    }
    return rows;
  }

  function validateOp(op) {
    if (op === null || typeof op !== "object" || isArray(op)) {
      return "op must be an object";
    }
    if (op.series !== ALARM_CHANNEL) {
      return "op.series must be \"alarms\"";
    }
    if (op.op === "clear_alarms" || op.op === "clear_alarm_preview") {
      var keys = Object.keys(op).sort().join(",");
      if (keys !== "op,series") return op.op + " must not carry payload";
      return null;
    }
    if (op.op === "set_alarm_preview") {
      var pkeys = Object.keys(op).sort().join(",");
      if (pkeys !== "op,price,series") {
        return "set_alarm_preview must carry exactly price";
      }
      if (!isFiniteNumber(op.price)) return "op.price must be a finite number";
      return null;
    }
    if (op.op !== "set_alarms") return "unknown op: " + op.op;
    if (Object.keys(op).sort().join(",") !== "cols,op,series") {
      return "set_alarms must carry exactly cols";
    }
    var cols = op.cols;
    if (cols === null || typeof cols !== "object" || isArray(cols)) {
      return "op.cols must be an object of arrays";
    }
    if (Object.keys(cols).sort().join(",") !== ALARM_COLS.slice().sort().join(",")) {
      return "cols must be exactly " + ALARM_COLS.join(",");
    }
    var n = null;
    for (var i = 0; i < ALARM_COLS.length; i++) {
      var name = ALARM_COLS[i];
      if (!isArray(cols[name])) return "cols." + name + " must be an array";
      if (n === null) n = cols[name].length;
      else if (cols[name].length !== n) return "column arrays must share one length";
    }
    for (var j = 0; j < n; j++) {
      if (!isFiniteNumber(cols.id[j])) return "cols.id must be finite numbers";
      if (!isFiniteNumber(cols.price[j])) return "cols.price must be finite numbers";
      if (typeof cols.direction[j] !== "string") {
        return "cols.direction entries must be strings";
      }
      for (var b = 0; b < BOOL_COLS.length; b++) {
        if (!isBool(cols[BOOL_COLS[b]][j])) {
          return "cols." + BOOL_COLS[b] + " entries must be booleans";
        }
      }
      if (typeof cols.note[j] !== "string") return "cols.note entries must be strings";
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
    if (env.v !== ENVELOPE_VERSION) {
      return { ok: false, error: "unsupported envelope version: " + env.v };
    }
    if (!isArray(env.ops)) return { ok: false, error: "ops must be an array" };
    for (var i = 0; i < env.ops.length; i++) {
      var err = validateOp(env.ops[i]);
      if (err) return { ok: false, error: "ops[" + i + "]: " + err };
    }
    return { ok: true, error: null };
  }

  /* ── chart glue (a series handle is required; node never needs one) ── */

  var chartRef = null;
  var seriesRef = null;
  var lineHandles = [];
  var previewHandle = null;
  var snapshotLines = [];
  var snapshotPreview = null;

  function lwcLib() {
    return typeof LightweightCharts === "undefined" ? null : LightweightCharts;
  }

  function lineStyleId(name) {
    var lib = lwcLib();
    var styles = lib && lib.LineStyle;
    if (name === "dashed") {
      return styles && typeof styles.Dashed === "number" ? styles.Dashed : DASHED;
    }
    return styles && typeof styles.Solid === "number" ? styles.Solid : SOLID;
  }

  /* LWC price lines take an integer width 1..4; the nearest supported one. */
  function lineWidthFor(width) {
    var w = Number(width);
    if (!isFinite(w)) w = 1;
    return Math.max(1, Math.min(4, Math.round(w)));
  }

  function priceLineOptions(spec) {
    return {
      price: spec.price,
      color: spec.color,
      lineWidth: lineWidthFor(spec.width),
      lineStyle: lineStyleId(spec.lineStyle),
      axisLabelVisible: !!spec.axisLabelVisible,
      title: spec.title || "",
    };
  }

  function removeLineHandles() {
    if (!seriesRef || typeof seriesRef.removePriceLine !== "function") {
      lineHandles = [];
      return;
    }
    for (var i = 0; i < lineHandles.length; i++) {
      seriesRef.removePriceLine(lineHandles[i]);
    }
    lineHandles = [];
  }

  function addLine(spec) {
    var handle = null;
    if (seriesRef && typeof seriesRef.createPriceLine === "function") {
      handle = seriesRef.createPriceLine(priceLineOptions(spec));
    }
    if (handle !== null && handle !== undefined) lineHandles.push(handle);
    return spec;
  }

  function removePreview() {
    if (previewHandle !== null && seriesRef &&
        typeof seriesRef.removePriceLine === "function") {
      seriesRef.removePriceLine(previewHandle);
    }
    previewHandle = null;
    snapshotPreview = null;
  }

  function applyOp(op) {
    if (op.op === "clear_alarms") {
      removeLineHandles();
      snapshotLines = [];
      return true;
    }
    if (op.op === "clear_alarm_preview") {
      removePreview();
      return true;
    }
    if (op.op === "set_alarm_preview") {
      removePreview();
      var spec = previewSpec(op.price);
      if (seriesRef && typeof seriesRef.createPriceLine === "function") {
        previewHandle = seriesRef.createPriceLine(priceLineOptions(spec));
      }
      snapshotPreview = spec;
      return true;
    }
    /* set_alarms replaces the whole set — idempotent under replay. */
    removeLineHandles();
    var rows = alarmRows(op);
    snapshotLines = [];
    for (var i = 0; i < rows.length; i++) {
      var line = lineSpec(rows[i]);
      addLine(line);
      snapshotLines.push(line);
    }
    return true;
  }

  /* Apply one alarm envelope to `chart`/`series`; returns {applied, error}. */
  function applyOps(chart, series, env) {
    var check = validateEnvelope(env);
    if (!check.ok) return { applied: 0, error: check.error };
    var chartHandle = chart || chartRef;
    var seriesHandle = series || seriesRef;
    if (!chartHandle && !seriesHandle) {
      return { applied: 0, error: "no chart handle" };
    }
    chartRef = chartHandle || chartRef;
    seriesRef = seriesHandle || seriesRef;
    var applied = 0;
    for (var i = 0; i < env.ops.length; i++) {
      if (applyOp(env.ops[i])) applied++;
    }
    return { applied: applied, error: null };
  }

  function bind(chart, series) {
    chartRef = chart || null;
    seriesRef = series || null;
    return chartRef !== null || seriesRef !== null;
  }

  /* The host page forwards the view's alarm envelopes here. */
  function applyAlarmOps(env) {
    return applyOps(chartRef, seriesRef, env);
  }

  function cloneSpec(spec) {
    if (spec === null || spec === undefined) return null;
    var out = {};
    for (var key in spec) {
      if (Object.prototype.hasOwnProperty.call(spec, key)) out[key] = spec[key];
    }
    return out;
  }

  /* What the engine currently shows — the parity evidence. */
  function snapshot() {
    var lines = [];
    for (var i = 0; i < snapshotLines.length; i++) {
      lines.push(cloneSpec(snapshotLines[i]));
    }
    return { lines: lines, preview: cloneSpec(snapshotPreview) };
  }

  function clear() {
    removeLineHandles();
    removePreview();
    snapshotLines = [];
    snapshotPreview = null;
  }

  /* ── page → Python reports (Q-20) ─────────────────────────────────────
   *
   * An alarm gesture (place / drag / delete) was unreachable from the page:
   * no slot existed. Each message is one JSON string handed to the
   * `LwBridge` slot of the same name; the view re-emits it on the pre-D47
   * `AlarmController` (create_requested / moved / delete_requested).
   */
  function pageBridge(bridge) {
    if (bridge) return bridge;
    if (typeof window !== "undefined" && window.lwBridge) {
      return window.lwBridge;
    }
    return null;
  }

  function notifyPage(message, payload, bridge) {
    var target = pageBridge(bridge);
    if (!target || typeof target[message] !== "function") return false;
    target[message](JSON.stringify(payload || {}));
    return true;
  }

  function reportAlarmCreated(price, bridge) {
    var value = Number(price);
    if (!isFinite(value)) return false;
    return notifyPage("alarmCreated", { price: value }, bridge);
  }

  function reportAlarmMoved(id, price, bridge) {
    var value = Number(price);
    if (!isFinite(value)) return false;
    return notifyPage("alarmMoved", { id: id, price: value }, bridge);
  }

  function reportAlarmDelete(id, bridge) {
    return notifyPage("alarmDeleted", { id: id }, bridge);
  }

  return {
    ENVELOPE_VERSION: ENVELOPE_VERSION,
    ALARM_CHANNEL: ALARM_CHANNEL,
    ALARM_COLS: ALARM_COLS,
    ALARM_COLORS: ALARM_COLORS,
    TRIGGERED_COLOR: TRIGGERED_COLOR,
    ARMED_COLOR: ARMED_COLOR,
    MUTED_COLOR: MUTED_COLOR,
    INACTIVE_COLOR: INACTIVE_COLOR,
    PREVIEW_COLOR: PREVIEW_COLOR,
    DIRECTION_GLYPH: DIRECTION_GLYPH,
    LINE_WIDTH_PX: LINE_WIDTH_PX,
    ALARM_LINE_Z: ALARM_LINE_Z,
    ALARM_LABEL_Z: ALARM_LABEL_Z,
    PREVIEW_LINE_Z: PREVIEW_LINE_Z,
    LABEL_ANCHOR: LABEL_ANCHOR,
    glyphFor: glyphFor,
    priceText: priceText,
    colorFor: colorFor,
    labelText: labelText,
    lineSpec: lineSpec,
    previewSpec: previewSpec,
    alarmRows: alarmRows,
    validateOp: validateOp,
    validateEnvelope: validateEnvelope,
    lineWidthFor: lineWidthFor,
    priceLineOptions: priceLineOptions,
    bind: bind,
    applyOps: applyOps,
    applyAlarmOps: applyAlarmOps,
    snapshot: snapshot,
    clear: clear,
    pageBridge: pageBridge,
    notifyPage: notifyPage,
    reportAlarmCreated: reportAlarmCreated,
    reportAlarmMoved: reportAlarmMoved,
    reportAlarmDelete: reportAlarmDelete,
  };
});
