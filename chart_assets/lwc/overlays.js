/* overlays.js — LWC session/gap/VIX/ICT overlays + D38 event markers
 * (P6-10 / Phase 8, D47.5).
 *
 * Two renderer channels, both fed by `ui/lwc_view.py`:
 *
 * - `overlays` — `{v: 1, ops: [{op: "set_overlay", series: "overlays",
 *   name: "session"|"rth_gaps"|"vix_sd"|"ict", regions: [...]},
 *   {op: "clear_overlay", series: "overlays", name}]}`. Every region is one
 *   shape the default engine draws: a `region` (vertical band, full pane
 *   height), a `band` (price rectangle over a fractional x range), an
 *   `hline` (full-width price line with a right-edge label), a `segment`
 *   (price line over a fractional x range, optionally labelled) or a `point`
 *   (a displacement marker).
 * - `markers` — `{v: 1, ops: [{op: "set_markers", series: "markers",
 *   items: [...], countdown: {...}|null, unavailable: bool}]}` for the D38
 *   corporate-event markers and their countdown label.
 *
 * The references are the shipped renderers — `ui/overlays/session_overlay.py`,
 * `ui/overlays/gap_overlay.py`, `ui/overlays/vix_overlay.py`,
 * `ui/overlays/ict_overlay.py` and `ui/event_marker_overlay.py`. Their
 * colours, alphas, pen widths, z-order, anchors and label formats are the
 * constants below; the parity suite asserts them against those modules rather
 * than trusting this comment.
 *
 * Renderer boundary: the wire carries **fractional logical indices** (the
 * candles' own axis unit, so a region lands on the identical bar as on the
 * default engine), prices and raw event fields. No timestamp, no service
 * call, no formatted string: this side composes the VIX sigma labels, the
 * D38 glyphs/labels/tooltips and the countdown text from numbers.
 *
 * The bar transport (`ui/lwc_bridge.py` -> `chart_assets/lwc/envelope.js`)
 * pins its series set to candles/volume, so these ops travel on their own
 * envelopes; `chart.html` includes this script at cutover and the host page
 * forwards `overlayOpsEmitted` / `markerOpsEmitted` here.
 *
 * Node note: the pure core below has no DOM/chart dependency and is exported
 * for the parity harness; the canvas glue never boots without a chart handle.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwOverlays = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ENVELOPE_VERSION = 1;
  var OVERLAY_CHANNEL = "overlays";
  var MARKER_CHANNEL = "markers";
  var OVERLAY_NAMES = ["session", "rth_gaps", "vix_sd", "ict"];
  var REGION_SHAPES = ["band", "hline", "segment", "point", "region"];
  var LINE_STYLES = ["solid", "dashed", "dotted"];

  /* SessionOverlay: orange pre-market, blue post-market, 10 % alpha, z -10. */
  var SESSION_COLORS = { pre: "#f59e0b", post: "#60a5fa" };
  var SESSION_ALPHA = 0.10;
  var SESSION_Z = -10;

  /* RthGapOverlay: green up / red down with the darker brush per direction,
   * the 0.55 (open) / 0.32 (fully filled) alpha pair, 0.8 px border, z -5. */
  var GAP_STYLE = {
    up: { color: "#089981", brush: "#064e3b" },
    down: { color: "#f23645", brush: "#7f1d1d" },
    openAlpha: 0.55,
    filledAlpha: 0.32,
    borderWidth: 0.8,
    z: -5,
  };

  /* VixOverlay: right-edge labels, the reference pen default, no z override. */
  var VIX_STYLE = {
    labelAnchor: "right",
    defaultWidth: 1,
    defaultColor: "#94a3b8",
    z: 0,
  };

  /* ICTStudyOverlay: per-concept alpha / z / width and the default colours. */
  var ICT_STYLE = {
    structure: { width: 1.2, lineStyle: "dashed", z: 3 },
    orderBlock: { alpha: 0.18, z: -3 },
    fvg: { alpha: 0.14, mitigatedAlpha: 0.06, z: -4 },
    pool: { alpha: 0.07, z: -6 },
    poolLevel: { width: 1.0, z: -2 },
    volumeImbalance: { alpha: 0.35, color: "#e879f9", z: -4 },
    openingGap: { alpha: 0.10, z: -5 },
    openingGapMid: { width: 1.0, z: -2 },
    displacement: { size: 10, z: 4, up: "#34d399", down: "#f87171" },
    killzone: { z: -8 },
  };

  /* D38 event markers — value-for-value with ui/event_marker_overlay.py's
   * EVENT_STYLE table (glyph, colour, label per type). */
  var EVENT_STYLE = {
    earnings: { glyph: "\u25C6 E", color: "#fbbf24", label: "Earnings" },
    dividend: { glyph: "\u25CF D", color: "#4ade80", label: "Dividend" },
    split: { glyph: "\u25B2 S", color: "#60a5fa", label: "Split" },
  };

  /* Marker TextItem: z 10, anchor (0.5, 1.0). */
  var MARKER_Z = 10;
  var MARKER_ANCHOR = [0.5, 1.0];

  /* Countdown label: anchor (0, 0), z 10, the reference fallback colour. */
  var COUNTDOWN_ANCHOR = [0.0, 0.0];
  var COUNTDOWN_Z = 10;
  var COUNTDOWN_COLOR = "#e5e7eb";
  var COUNTDOWN_UNAVAILABLE_COLOR = "#f87171";
  var COUNTDOWN_UNAVAILABLE_TEXT = "Event data unavailable";

  var DEFAULT_BORDER_WIDTH = 0.8;
  var LABEL_INSET_PX = 4;

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isFiniteNumber(x) {
    return typeof x === "number" && isFinite(x);
  }

  function clone(value) {
    if (value === null || value === undefined) return value;
    if (isArray(value)) {
      var arr = [];
      for (var i = 0; i < value.length; i++) arr.push(clone(value[i]));
      return arr;
    }
    if (typeof value === "object") {
      var out = {};
      for (var key in value) {
        if (Object.prototype.hasOwnProperty.call(value, key)) {
          out[key] = clone(value[key]);
        }
      }
      return out;
    }
    return value;
  }

  /* ── label composition (the reference formats, engine-side) ──────────── */

  /* Python's f"{sigma:+.2g}": a signed, compact sigma multiplier. */
  function sigmaText(sigma) {
    var v = Number(sigma);
    if (!isFinite(v)) v = 0;
    if (v === 0) return "0";
    return (v > 0 ? "+" : "-") + String(Math.abs(v));
  }

  /* VixOverlay's label: "0σ 4321.50" / "+1σ 4340.12" / "-2σ 4260.00". */
  function vixLabel(sigma, price) {
    var text = Number(sigma) === 0
      ? "0\u03C3"
      : sigmaText(sigma) + "\u03C3";
    return text + " " + Number(price).toFixed(2);
  }

  /* EventMarkerOverlay._tooltip_for, composed from the raw event fields. */
  function tooltipFor(item, style) {
    style = style || {};
    var details = (item && item.details) || {};
    var label = style.label || String((item && item.type) || "");
    var lines = [label + " \u2014 " + String((item && item.date) || ""),
                 "Source: " + String((item && item.source) || "")];
    if (item && item.type === "dividend" &&
        details.amount !== null && details.amount !== undefined) {
      lines.push("Amount: " + details.amount);
    }
    if (item && item.type === "earnings") {
      if (details.estimate !== null && details.estimate !== undefined) {
        lines.push("EPS est: " + details.estimate);
      }
      if (details.reported !== null && details.reported !== undefined) {
        lines.push("Reported: " + details.reported);
      }
    }
    if (item && item.type === "split" &&
        details.ratio !== null && details.ratio !== undefined) {
      lines.push("Ratio: " + details.ratio);
    }
    return lines.join("\n");
  }

  /* The countdown text: "Earnings in 3d", "Split today" or the explicit
   * unavailable state — the reference `_update_countdown` wording. */
  function countdownText(countdown) {
    if (!countdown) return "";
    if (countdown.kind === "unavailable") return COUNTDOWN_UNAVAILABLE_TEXT;
    var style = EVENT_STYLE[countdown.type] || {};
    var label = style.label || String(countdown.type || "");
    var days = Number(countdown.days);
    if (!isFinite(days)) days = 0;
    var when = days === 0 ? "today" : "in " + days + "d";
    return label + " " + when;
  }

  function countdownColor(countdown) {
    if (!countdown) return COUNTDOWN_COLOR;
    if (countdown.kind === "unavailable") return COUNTDOWN_UNAVAILABLE_COLOR;
    var style = EVENT_STYLE[countdown.type] || {};
    return style.color || COUNTDOWN_COLOR;
  }

  /* One wire marker item -> the visual the engine draws. */
  function markerSpec(item) {
    var style = item ? EVENT_STYLE[item.type] : null;
    if (!style) return null;
    var x = item.x === null || item.x === undefined ? null : Number(item.x);
    var visible = item.visible === true && isFiniteNumber(x);
    return {
      id: item.id,
      type: item.type,
      x: visible ? x : null,
      visible: visible,
      glyph: style.glyph,
      color: style.color,
      label: style.label,
      date: item.date,
      source: item.source,
      tooltip: tooltipFor(item, style),
      z: MARKER_Z,
      anchor: MARKER_ANCHOR.slice(),
    };
  }

  /* The label one overlay line carries (VIX only; other kinds are silent). */
  function labelFor(region) {
    if (!region) return "";
    if (region.shape === "hline" && region.kind === "vix") {
      return vixLabel(region.sigma, region.price);
    }
    return typeof region.label === "string" ? region.label : "";
  }

  /* ── wire validation (this side receives validated payloads only) ────── */

  function validateRegion(region) {
    if (region === null || typeof region !== "object" || isArray(region)) {
      return "region must be an object";
    }
    if (REGION_SHAPES.indexOf(region.shape) === -1) {
      return "unknown region shape: " + region.shape;
    }
    if (typeof region.kind !== "string" || region.kind.length === 0) {
      return "region.kind must be a non-empty string";
    }
    if (region.shape !== "hline") {
      if (!isFiniteNumber(region.from)) {
        return "region.from must be a finite number";
      }
      if (!isFiniteNumber(region.to)) {
        return "region.to must be a finite number";
      }
      if (region.to < region.from) {
        return "region.to must not precede region.from";
      }
    }
    if (!isFiniteNumber(region.z)) return "region.z must be a finite number";
    if (typeof region.color !== "string" || region.color.length === 0) {
      return "region.color must be a non-empty string";
    }
    if (region.shape === "band") {
      if (!isFiniteNumber(region.top) || !isFiniteNumber(region.bottom)) {
        return "band requires numeric top/bottom";
      }
      if (region.top < region.bottom) {
        return "band must be normalised (bottom <= top)";
      }
      if (!isFiniteNumber(region.alpha)) return "band requires a numeric alpha";
      if (region.alpha < 0 || region.alpha > 1) {
        return "band alpha must be within 0..1";
      }
    }
    if (region.shape === "hline" || region.shape === "segment") {
      if (!isFiniteNumber(region.price)) {
        return region.shape + " requires a numeric price";
      }
      if (!isFiniteNumber(region.width)) {
        return region.shape + " requires a numeric width";
      }
      if (LINE_STYLES.indexOf(region.lineStyle) === -1) {
        return "unknown lineStyle: " + region.lineStyle;
      }
    }
    if (region.shape === "hline") {
      if (!isFiniteNumber(region.labelFrom)) {
        return "hline requires a numeric labelFrom";
      }
      if (typeof region.labelAnchor !== "string") {
        return "hline requires a labelAnchor";
      }
    }
    if (region.shape === "point") {
      if (!isFiniteNumber(region.price)) return "point requires a numeric price";
      if (!isFiniteNumber(region.size)) return "point requires a numeric size";
    }
    if (region.shape === "region" &&
        region.alpha !== undefined && !isFiniteNumber(region.alpha)) {
      return "region alpha must be a number when present";
    }
    return null;
  }

  function validateMarker(item) {
    if (item === null || typeof item !== "object" || isArray(item)) {
      return "marker must be an object";
    }
    if (typeof item.id !== "string") return "marker.id must be a string";
    if (EVENT_STYLE[item.type] === undefined) {
      return "unknown event type: " + item.type;
    }
    if (item.visible !== true && item.visible !== false) {
      return "marker.visible must be a boolean";
    }
    if (item.x !== null && item.x !== undefined && !isFiniteNumber(item.x)) {
      return "marker.x must be a finite number or null";
    }
    if (item.visible === true && !isFiniteNumber(item.x)) {
      return "a visible marker needs a finite x";
    }
    if (typeof item.date !== "string") return "marker.date must be a string";
    if (typeof item.source !== "string") return "marker.source must be a string";
    if (item.details === null || typeof item.details !== "object" ||
        isArray(item.details)) {
      return "marker.details must be an object";
    }
    return null;
  }

  function validateCountdown(countdown) {
    if (countdown === null || countdown === undefined) return null;
    if (typeof countdown !== "object" || isArray(countdown)) {
      return "countdown must be an object or null";
    }
    if (countdown.kind === "unavailable") {
      return Object.keys(countdown).sort().join(",") === "kind"
        ? null : "the unavailable countdown must carry exactly kind";
    }
    if (countdown.kind !== "upcoming") {
      return "unknown countdown kind: " + countdown.kind;
    }
    if (EVENT_STYLE[countdown.type] === undefined) {
      return "unknown countdown type: " + countdown.type;
    }
    if (!isFiniteNumber(countdown.days)) {
      return "countdown.days must be a finite number";
    }
    return null;
  }

  function validateOp(op) {
    if (op === null || typeof op !== "object" || isArray(op)) {
      return "op must be an object";
    }
    var keys = Object.keys(op).sort().join(",");
    if (op.op === "clear_overlay") {
      if (op.series !== OVERLAY_CHANNEL) {
        return 'op.series must be "overlays"';
      }
      if (keys !== "name,op,series") {
        return "clear_overlay must carry exactly name";
      }
      if (OVERLAY_NAMES.indexOf(op.name) === -1) {
        return "unknown overlay: " + op.name;
      }
      return null;
    }
    if (op.op === "set_overlay") {
      if (op.series !== OVERLAY_CHANNEL) {
        return 'op.series must be "overlays"';
      }
      if (keys !== "name,op,regions,series") {
        return "set_overlay must carry exactly name,regions";
      }
      if (OVERLAY_NAMES.indexOf(op.name) === -1) {
        return "unknown overlay: " + op.name;
      }
      if (!isArray(op.regions)) return "op.regions must be an array";
      for (var i = 0; i < op.regions.length; i++) {
        var err = validateRegion(op.regions[i]);
        if (err) return "regions[" + i + "]: " + err;
      }
      return null;
    }
    if (op.op === "clear_markers") {
      if (op.series !== MARKER_CHANNEL) {
        return 'op.series must be "markers"';
      }
      if (keys !== "op,series") {
        return "clear_markers must not carry payload";
      }
      return null;
    }
    if (op.op !== "set_markers") return "unknown op: " + op.op;
    if (op.series !== MARKER_CHANNEL) {
      return 'op.series must be "markers"';
    }
    if (keys !== "countdown,items,op,series,unavailable") {
      return "set_markers must carry exactly items,countdown,unavailable";
    }
    if (!isArray(op.items)) return "op.items must be an array";
    for (var j = 0; j < op.items.length; j++) {
      var merr = validateMarker(op.items[j]);
      if (merr) return "items[" + j + "]: " + merr;
    }
    if (typeof op.unavailable !== "boolean") {
      return "op.unavailable must be a boolean";
    }
    return validateCountdown(op.countdown);
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

  /* ── state + render plan ─────────────────────────────────────────────── */

  var chartRef = null;
  var seriesRef = null;
  var overlays = {};
  var markerItems = [];
  var countdown = null;
  var unavailable = false;
  var primitiveHandle = null;
  var planSnapshot = null;

  function renderPlan() {
    var plan = {
      regions: [], bands: [], hlines: [], segments: [], points: [],
      markers: [], countdown: null, countdownText: "",
      countdownColor: COUNTDOWN_COLOR, countdownAnchor: COUNTDOWN_ANCHOR.slice(),
      unavailable: unavailable,
    };
    for (var n = 0; n < OVERLAY_NAMES.length; n++) {
      var name = OVERLAY_NAMES[n];
      var rows = overlays[name] || [];
      for (var i = 0; i < rows.length; i++) {
        var region = rows[i];
        var row = clone(region);
        row.overlay = name;
        row.text = labelFor(region);
        row.alpha = typeof region.alpha === "number" ? region.alpha : null;
        row.borderWidth = typeof region.borderWidth === "number"
          ? region.borderWidth : DEFAULT_BORDER_WIDTH;
        row.borderStyle = region.borderStyle || "solid";
        if (region.shape === "band") plan.bands.push(row);
        else if (region.shape === "hline") plan.hlines.push(row);
        else if (region.shape === "segment") plan.segments.push(row);
        else if (region.shape === "point") plan.points.push(row);
        else if (region.shape === "region") plan.regions.push(row);
      }
    }
    for (var j = 0; j < markerItems.length; j++) {
      var spec = markerSpec(markerItems[j]);
      if (spec && spec.visible) plan.markers.push(spec);
    }
    plan.countdown = clone(countdown);
    plan.countdownText = countdownText(countdown);
    plan.countdownColor = countdownColor(countdown);
    return plan;
  }

  function refresh() {
    planSnapshot = renderPlan();
    if (primitiveHandle && typeof primitiveHandle.requestUpdate === "function") {
      primitiveHandle.requestUpdate();
    }
  }

  function applyOp(op) {
    if (op.op === "clear_overlay") {
      delete overlays[op.name];
      return true;
    }
    if (op.op === "set_overlay") {
      overlays[op.name] = clone(op.regions);
      return true;
    }
    if (op.op === "clear_markers") {
      markerItems = [];
      countdown = null;
      unavailable = false;
      return true;
    }
    if (op.op === "set_markers") {
      markerItems = clone(op.items);
      countdown = clone(op.countdown);
      unavailable = !!op.unavailable;
      return true;
    }
    return false;
  }

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
    refresh();
    return { applied: applied, error: null };
  }

  /* What the engine currently shows — the parity evidence. */
  function snapshot() {
    return {
      overlays: clone(overlays),
      markers: { items: clone(markerItems), countdown: clone(countdown),
                 unavailable: unavailable },
      plan: clone(planSnapshot),
    };
  }

  function clear() {
    overlays = {};
    markerItems = [];
    countdown = null;
    unavailable = false;
    refresh();
  }

  /* ── canvas glue (the LWC primitive; node never reaches this) ────────── */

  function lwcLib() {
    return typeof LightweightCharts === "undefined" ? null : LightweightCharts;
  }

  function dashFor(style) {
    if (style === "dotted") return [1, 3];
    if (style === "dashed") return [4, 3];
    return [];
  }

  function coordinateForFrac(frac, timeScale) {
    var lo = Math.floor(frac);
    var hi = Math.ceil(frac);
    var a = timeScale.timeToCoordinate(lo);
    var b = timeScale.timeToCoordinate(hi);
    if (a === null || a === undefined) a = b;
    if (b === null || b === undefined) b = a;
    if (a === null || a === undefined) return null;
    if (hi === lo) return a;
    return a + (frac - lo) * (b - a);
  }

  function applyAlpha(context, value) {
    context.globalAlpha = typeof value === "number" ? value : 1;
  }

  function strokeStyle(context, style) {
    if (typeof context.setLineDash !== "function") return;
    context.setLineDash(dashFor(style));
  }

  function drawPlan(context, scope, plan) {
    var chart = chartRef;
    var series = seriesRef;
    if (!chart || !series) return 0;
    var timeScale = chart.timeScale ? chart.timeScale() : null;
    var priceToCoordinate = series.priceToCoordinate;
    if (!timeScale || typeof priceToCoordinate !== "function") return 0;
    var width = scope && scope.mediaSize ? scope.mediaSize.width : 0;
    var height = scope && scope.mediaSize ? scope.mediaSize.height : 0;
    var hpr = scope && scope.horizontalPixelRatio ? scope.horizontalPixelRatio : 1;
    var vpr = scope && scope.verticalPixelRatio ? scope.verticalPixelRatio : 1;
    var drawCount = 0;
    var i;

    context.save();
    context.beginPath();
    context.rect(0, 0, width, height);
    context.clip();

    /* Vertical regions (session bands, killzones) span the whole pane. */
    for (i = 0; i < plan.regions.length; i++) {
      var region = plan.regions[i];
      var rx1 = coordinateForFrac(region.from, timeScale);
      var rx2 = coordinateForFrac(region.to, timeScale);
      if (rx1 === null || rx2 === null) continue;
      applyAlpha(context, region.alpha);
      context.fillStyle = region.color;
      context.fillRect(rx1 * hpr, 0, (rx2 - rx1) * hpr, height);
      context.globalAlpha = 1;
      drawCount++;
    }

    /* Price bands (gap steps, ICT concepts). The gap staircase fills with its
     * darker brush; every other concept fills with its own colour. */
    for (i = 0; i < plan.bands.length; i++) {
      var band = plan.bands[i];
      var bx1 = coordinateForFrac(band.from, timeScale);
      var bx2 = coordinateForFrac(band.to, timeScale);
      var yTop = priceToCoordinate(band.top);
      var yBottom = priceToCoordinate(band.bottom);
      if (bx1 === null || bx2 === null || yTop === null || yBottom === null) {
        continue;
      }
      applyAlpha(context, band.alpha);
      context.fillStyle = band.brush || band.color;
      context.fillRect(bx1 * hpr, yTop * vpr, (bx2 - bx1) * hpr,
                       (yBottom - yTop) * vpr);
      context.globalAlpha = 1;
      context.strokeStyle = band.color;
      context.lineWidth = Math.max(1, band.borderWidth * vpr);
      strokeStyle(context, band.borderStyle);
      context.strokeRect(bx1 * hpr, yTop * vpr, (bx2 - bx1) * hpr,
                         (yBottom - yTop) * vpr);
      strokeStyle(context, "solid");
      drawCount++;
    }

    /* Full-width price lines (VIX levels) with their right-edge labels. */
    context.font = "11px sans-serif";
    context.textBaseline = "middle";
    for (i = 0; i < plan.hlines.length; i++) {
      var hline = plan.hlines[i];
      var hy = priceToCoordinate(hline.price);
      if (hy === null) continue;
      context.strokeStyle = hline.color;
      context.lineWidth = Math.max(1, hline.width * vpr);
      strokeStyle(context, hline.lineStyle);
      context.beginPath();
      context.moveTo(0, hy * vpr);
      context.lineTo(width, hy * vpr);
      context.stroke();
      strokeStyle(context, "solid");
      if (hline.text) {
        var labelX = coordinateForFrac(hline.labelFrom, timeScale);
        var x = labelX === null ? width - LABEL_INSET_PX * hpr
          : labelX * hpr + LABEL_INSET_PX * hpr;
        context.fillStyle = hline.color;
        context.textAlign = "left";
        context.fillText(hline.text, x, hy * vpr);
      }
      drawCount++;
    }

    /* Bounded price segments (market structures, pool levels, gap midpoints). */
    for (i = 0; i < plan.segments.length; i++) {
      var segment = plan.segments[i];
      var sx1 = coordinateForFrac(segment.from, timeScale);
      var sx2 = coordinateForFrac(segment.to, timeScale);
      var sy = priceToCoordinate(segment.price);
      if (sx1 === null || sx2 === null || sy === null) continue;
      context.strokeStyle = segment.color;
      context.lineWidth = Math.max(1, segment.width * vpr);
      strokeStyle(context, segment.lineStyle);
      context.beginPath();
      context.moveTo(sx1 * hpr, sy * vpr);
      context.lineTo(sx2 * hpr, sy * vpr);
      context.stroke();
      strokeStyle(context, "solid");
      if (segment.text) {
        context.fillStyle = segment.color;
        context.textAlign = "center";
        context.fillText(segment.text, sx2 * hpr, sy * vpr - 6 * vpr);
      }
      drawCount++;
    }

    /* Displacement points: up triangle for a bullish open, down for bearish. */
    for (i = 0; i < plan.points.length; i++) {
      var point = plan.points[i];
      var px = coordinateForFrac(point.from, timeScale);
      var py = priceToCoordinate(point.price);
      if (px === null || py === null) continue;
      var half = (point.size / 2) * vpr;
      context.fillStyle = point.color;
      context.beginPath();
      if (point.direction === "up") {
        context.moveTo(px * hpr, py * vpr - half);
        context.lineTo(px * hpr - half, py * vpr + half);
        context.lineTo(px * hpr + half, py * vpr + half);
      } else {
        context.moveTo(px * hpr, py * vpr + half);
        context.lineTo(px * hpr - half, py * vpr - half);
        context.lineTo(px * hpr + half, py * vpr - half);
      }
      context.closePath();
      context.fill();
      drawCount++;
    }

    /* Event markers: the glyph at the event's display-x, above the pane top. */
    for (i = 0; i < plan.markers.length; i++) {
      var marker = plan.markers[i];
      var mx = coordinateForFrac(marker.x, timeScale);
      if (mx === null) continue;
      context.fillStyle = marker.color;
      context.textAlign = "center";
      context.fillText(marker.glyph, mx * hpr, 12 * vpr);
      drawCount++;
    }

    /* Countdown: the reference label at the pane's left edge. */
    if (plan.countdownText) {
      context.fillStyle = plan.countdownColor;
      context.textAlign = "left";
      context.fillText(plan.countdownText, 4 * hpr, 12 * vpr);
      drawCount++;
    }

    context.restore();
    return drawCount;
  }

  var renderer = {
    draw: function (target) {
      if (!target) return;
      if (typeof target.useBitmapCoordinateSpace === "function") {
        target.useBitmapCoordinateSpace(function (scope) {
          drawPlan(scope.context, scope, planSnapshot);
        });
        return;
      }
      var ctx = target.ctx || target.context;
      if (ctx) {
        drawPlan(ctx, {
          mediaSize: {
            width: target.mediaSize ? target.mediaSize.width : 0,
            height: target.mediaSize ? target.mediaSize.height : 0,
          },
          horizontalPixelRatio: 1,
          verticalPixelRatio: 1,
        }, planSnapshot);
      }
    },
  };

  function makePrimitive() {
    return {
      paneViews: function () {
        return [{ renderer: renderer }];
      },
      updateAllViews: function () {},
      attached: function () {},
      detached: function () {},
    };
  }

  function attach() {
    if (primitiveHandle || !seriesRef ||
        typeof seriesRef.attachPrimitive !== "function") {
      return;
    }
    primitiveHandle = makePrimitive();
    seriesRef.attachPrimitive(primitiveHandle);
  }

  function bind(chart, series) {
    chartRef = chart || null;
    seriesRef = series || null;
    attach();
    refresh();
    return chartRef !== null || seriesRef !== null;
  }

  /* The host page forwards the view's two envelopes here. */
  function applyOverlayOps(env) {
    return applyOps(chartRef, seriesRef, env);
  }

  function applyMarkerOps(env) {
    return applyOps(chartRef, seriesRef, env);
  }

  refresh();

  return {
    ENVELOPE_VERSION: ENVELOPE_VERSION,
    OVERLAY_CHANNEL: OVERLAY_CHANNEL,
    MARKER_CHANNEL: MARKER_CHANNEL,
    OVERLAY_NAMES: OVERLAY_NAMES,
    REGION_SHAPES: REGION_SHAPES,
    LINE_STYLES: LINE_STYLES,
    SESSION_COLORS: SESSION_COLORS,
    SESSION_ALPHA: SESSION_ALPHA,
    SESSION_Z: SESSION_Z,
    GAP_STYLE: GAP_STYLE,
    VIX_STYLE: VIX_STYLE,
    ICT_STYLE: ICT_STYLE,
    EVENT_STYLE: EVENT_STYLE,
    MARKER_Z: MARKER_Z,
    MARKER_ANCHOR: MARKER_ANCHOR,
    COUNTDOWN_ANCHOR: COUNTDOWN_ANCHOR,
    COUNTDOWN_Z: COUNTDOWN_Z,
    COUNTDOWN_COLOR: COUNTDOWN_COLOR,
    COUNTDOWN_UNAVAILABLE_COLOR: COUNTDOWN_UNAVAILABLE_COLOR,
    COUNTDOWN_UNAVAILABLE_TEXT: COUNTDOWN_UNAVAILABLE_TEXT,
    sigmaText: sigmaText,
    vixLabel: vixLabel,
    tooltipFor: tooltipFor,
    countdownText: countdownText,
    countdownColor: countdownColor,
    markerSpec: markerSpec,
    labelFor: labelFor,
    validateRegion: validateRegion,
    validateMarker: validateMarker,
    validateCountdown: validateCountdown,
    validateOp: validateOp,
    validateEnvelope: validateEnvelope,
    renderPlan: renderPlan,
    bind: bind,
    applyOps: applyOps,
    applyOverlayOps: applyOverlayOps,
    applyMarkerOps: applyMarkerOps,
    snapshot: snapshot,
    clear: clear,
    lwcLib: lwcLib,
  };
});
