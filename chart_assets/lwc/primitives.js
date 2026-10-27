/* primitives.js — LWC drawing primitives (P6-09 / Phase 7, D47.5 + DG93).
 *
 * The drawing channel: `ui/lwc_view.py` publishes one envelope per render —
 * `{v: 1, ops: [{op: "set_drawings", series: "drawings", items: [...]}]}` —
 * and this module renders those primitives on the chart. The reference is the
 * shipped `ui/drawing_overlay.py`: the same geometry, colours, pen widths,
 * z-order, handles and D11 inner-right labels. The zone / horizontal-line
 * settings dialogs stay the Qt dialogs — no HTML dialog exists here.
 *
 * The unit of the time axis is the **fractional logical index**:
 * - a bar's own timestamp maps to that bar's integer logical index, so the
 *   primitive lands exactly on the candle;
 * - a timestamp between two bars maps linearly between their indices, which
 *   is the same relative position the reference engine's linear display-x
 *   axis renders;
 * - a display-x collision (DG93: two bars sharing one x) resolves to one
 *   index and the inverse returns the shared x for either — no anchor is
 *   lost and no two bars are merged.
 * `fracToDisplay` / `displayToFrac` are the JS mirror of the Python pair
 * (`fractional_index_from_display` / `display_from_fractional_index`); the
 * parity suite drives both over the DG93 edge fixtures.
 *
 * Geometry is Python-owned: Fibonacci levels, the measure delta and the
 * handle anchors arrive precomputed from `services/drawing_service.py` and
 * this side only replays them. Labels are composed here from numbers — the
 * wire never carries a formatted string — exactly as the alarm and study
 * labels are composed engine-side.
 *
 * Node note: the pure core below has no DOM/chart dependency and is
 * exported for `node --test`; the canvas glue never boots without a chart
 * handle.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwPrimitives = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ENVELOPE_VERSION = 1;
  var DRAWING_CHANNEL = "drawings";

  var DRAWING_KINDS = ["trendline", "horizontal", "zone", "fibonacci", "measure"];
  var DEFAULT_DRAWING_COLOR = "#38bdf8";

  /* Reference pen widths per kind (ui/drawing_overlay.py `_build_items`). */
  var LINE_WIDTHS = {
    trendline: 1.4,
    horizontal: 1.2,
    zone: 1.0,
    fibonacci: 1.0,
    measure: 1.4,
  };

  /* The reference `_build_items` final loop overrides every item's z to 10;
   * the per-kind -4 (zone) / -3 (fib) values never survive it. */
  var DRAWING_Z = 10;

  /* QColor.setAlpha(36) on the zone brush. */
  var ZONE_ALPHA = 36;

  /* D11 inner-right labels: view_rect.right() - 4, measured-bbox stacking
   * with a 15 px floor (`_update_inner_labels`). */
  var LABEL_INSET_PX = 4;
  var LABEL_MIN_HEIGHT_PX = 15;
  var LABEL_ANCHOR = "inner-right";

  /* Selection pen (`_style_selected`) and handles (`_refresh_handles`). */
  var SELECTED_COLOR = "#ffffff";
  var SELECTED_WIDTH = 2.0;
  var HANDLE_SIZE = 10;
  var HANDLE_PEN = "#ffffff";
  var HANDLE_BRUSH = "#0ea5e9";
  var HANDLE_PEN_WIDTH = 1.5;

  /* The service's own Fibonacci ratios — the drag mirror needs them. */
  var FIB_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
  var FIB_EXTENSION_LEVELS = [0.0, 0.618, 1.0, 1.272, 1.618, 2.0, 2.618];

  var MEASURE_PREFIX = "\u0394 "; /* Δ */
  var SOLID = 0;

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isFiniteNumber(x) {
    return typeof x === "number" && isFinite(x);
  }

  function isFiniteOrNull(x) {
    return x === null || x === undefined || isFiniteNumber(x);
  }

  function isBool(x) {
    return x === true || x === false;
  }

  function num(x) {
    var n = Number(x);
    return isFinite(n) ? n : 0;
  }

  function interp(x, x1, y1, x2, y2) {
    if (x2 === x1) return Number(y2);
    return Number(y1 + ((x - x1) * (y2 - y1)) / (x2 - x1));
  }

  /* First/last non-degenerate (x, index) pair — mirrors the Python
   * `_edge_pair`. A collision at the series edge must not lose the identity
   * of an out-of-window anchor. */
  function edgePair(xs, indices, atStart) {
    var n = xs.length;
    var j;
    if (atStart) {
      var base = xs[0];
      for (j = 1; j < n; j++) {
        if (xs[j] !== base) {
          return [Number(base), Number(indices[0]),
                  Number(xs[j]), Number(indices[j])];
        }
      }
      return null;
    }
    var last = xs[n - 1];
    for (j = n - 2; j >= 0; j--) {
      if (xs[j] !== last) {
        return [Number(xs[j]), Number(indices[j]),
                Number(last), Number(indices[n - 1])];
      }
    }
    return null;
  }

  /* ── fractional-index axis (mirror of the Python mapping pair) ───────── */

  function fracToDisplay(frac, xs, indices) {
    xs = isArray(xs) ? xs : [];
    indices = isArray(indices) ? indices : [];
    var n = indices.length;
    if (n === 0) return 0;
    if (n === 1) return Number(xs[0]);
    var f = Number(frac);
    var pair;
    if (f <= indices[0]) {
      pair = edgePair(xs, indices, true);
      if (!pair) return Number(xs[0]);
      return interp(f, pair[1], pair[0], pair[3], pair[2]);
    }
    if (f >= indices[n - 1]) {
      pair = edgePair(xs, indices, false);
      if (!pair) return Number(xs[n - 1]);
      return interp(f, pair[1], pair[0], pair[3], pair[2]);
    }
    var i = 0;
    for (var k = 0; k < n - 1; k++) {
      if (indices[k] <= f && f <= indices[k + 1]) {
        i = k;
        break;
      }
    }
    i = Math.max(0, Math.min(i, n - 2));
    return interp(f, indices[i], xs[i], indices[i + 1], xs[i + 1]);
  }

  function displayToFrac(x, xs, indices) {
    xs = isArray(xs) ? xs : [];
    indices = isArray(indices) ? indices : [];
    var n = xs.length;
    if (n === 0) return 0;
    if (n === 1) return Number(indices[0]);
    var xf = Number(x);
    var pair;
    /* A collision resolves to the last index sharing that display-x. */
    if (xf === xs[0]) {
      var run = 0;
      while (run + 1 < n && xs[run + 1] === xs[0]) run++;
      return Number(indices[run]);
    }
    if (xf === xs[n - 1]) return Number(indices[n - 1]);
    if (xf <= xs[0]) {
      pair = edgePair(xs, indices, true);
      if (!pair) return Number(indices[0]);
      return interp(xf, pair[0], pair[1], pair[2], pair[3]);
    }
    if (xf >= xs[n - 1]) {
      pair = edgePair(xs, indices, false);
      if (!pair) return Number(indices[n - 1]);
      return interp(xf, pair[0], pair[1], pair[2], pair[3]);
    }
    var i = 0;
    /* Last index of a display-x run wins (the collision rule). */
    for (var k = 0; k < n - 1; k++) {
      if (xs[k] <= xf && xf <= xs[k + 1]) i = k;
    }
    i = Math.max(0, Math.min(i, n - 2));
    return interp(xf, xs[i], indices[i], xs[i + 1], indices[i + 1]);
  }

  /* ── pure geometry mirrors (service-owned values, replayed here) ─────── */

  function fibLevels(y1, y2, fibType) {
    var ratios = fibType === "ext" ? FIB_EXTENSION_LEVELS : FIB_LEVELS;
    var out = [];
    for (var i = 0; i < ratios.length; i++) {
      out.push([ratios[i], y1 + ratios[i] * (y2 - y1)]);
    }
    return out;
  }

  function priceText(price) {
    return num(price).toFixed(2);
  }

  /* Python's "+.2f" for a non-negative value; a plain "-.2f" otherwise. */
  function signedText(value) {
    var v = Number(value);
    if (!isFinite(v)) v = 0;
    if (v === 0) v = 0; /* normalise -0 */
    var text = v.toFixed(2);
    return v >= 0 ? "+" + text : text;
  }

  /* f"{ratio * 100:.1f}%  {price:.2f}" — the reference fib label. */
  function fibLabel(ratio, price) {
    return (num(ratio) * 100).toFixed(1) + "%  " + priceText(price);
  }

  /* f"\u0394 {dy:+.2f}  ({pct:+.2f}%)" — the reference measure label. */
  function measureLabel(delta) {
    var d = delta || {};
    return MEASURE_PREFIX + signedText(d.dy) + "  (" + signedText(d.pct) + "%)";
  }

  function handlePoints(kind, item) {
    if (kind === "trendline" || kind === "measure" || kind === "fibonacci") {
      var points = isArray(item.points) ? item.points : [];
      var out = [];
      for (var i = 0; i < points.length; i++) {
        out.push([Number(points[i][0]), Number(points[i][1])]);
      }
      return out;
    }
    if (kind === "horizontal") {
      return [[null, Number(item.price)]];
    }
    if (kind === "zone") {
      var span = isArray(item.span) ? item.span : [null, null];
      return [[span[0], Number(item.y1)], [span[1], Number(item.y2)]];
    }
    return [];
  }

  /* ── label primitives ────────────────────────────────────────────────── */

  /* One label per reference TextItem: inner-right price labels for every
   * kind except measure, whose Δ label is centred over the segment. */
  function labelsFor(item) {
    var kind = item && item.kind;
    var color = (item && item.color) || DEFAULT_DRAWING_COLOR;
    var labels = [];
    if (kind === "trendline" || kind === "measure") {
      var points = (item && item.points) || [];
      if (kind === "measure") {
        if (points.length === 2) {
          labels.push({
            id: item.id,
            kind: kind,
            anchor: "center",
            text: measureLabel(item.delta),
            frac: (Number(points[0][0]) + Number(points[1][0])) / 2,
            price: (Number(points[0][1]) + Number(points[1][1])) / 2,
            color: color,
          });
        }
        return labels;
      }
      for (var i = 0; i < points.length; i++) {
        labels.push({
          id: item.id,
          kind: kind,
          anchor: LABEL_ANCHOR,
          text: priceText(points[i][1]),
          price: Number(points[i][1]),
          color: color,
        });
      }
      return labels;
    }
    if (kind === "horizontal") {
      labels.push({
        id: item.id, kind: kind, anchor: LABEL_ANCHOR,
        text: priceText(item.price), price: Number(item.price), color: color,
      });
      return labels;
    }
    if (kind === "zone") {
      labels.push({
        id: item.id, kind: kind, anchor: LABEL_ANCHOR,
        text: priceText(item.y1), price: Number(item.y1), color: color,
      });
      labels.push({
        id: item.id, kind: kind, anchor: LABEL_ANCHOR,
        text: priceText(item.y2), price: Number(item.y2), color: color,
      });
      return labels;
    }
    if (kind === "fibonacci") {
      var levels = (item && item.levels) || [];
      for (var j = 0; j < levels.length; j++) {
        labels.push({
          id: item.id, kind: kind, anchor: LABEL_ANCHOR,
          text: fibLabel(levels[j][0], levels[j][1]),
          ratio: Number(levels[j][0]),
          price: Number(levels[j][1]),
          color: color,
        });
      }
      return labels;
    }
    return labels;
  }

  /* D11 stacking: sort by pixel y, clamp inside the pane, push each label
   * at least the measured bbox height (never below 15 px) below its
   * predecessor — `_update_inner_labels`, in pure form. */
  function stackInnerLabels(entries, opts) {
    opts = opts || {};
    var top = typeof opts.top === "number" ? opts.top : 0;
    var bottom = typeof opts.bottom === "number" ? opts.bottom : 0;
    var fallback = typeof opts.labelHeight === "number"
      ? opts.labelHeight : LABEL_MIN_HEIGHT_PX;
    var rows = [];
    for (var i = 0; i < entries.length; i++) {
      var entry = entries[i];
      var y = Number(entry.y);
      var height = isFiniteNumber(entry.height) && entry.height > 0
        ? entry.height : 0;
      rows.push({ entry: entry, y: y, height: height, order: i });
    }
    rows.sort(function (a, b) {
      if (a.y !== b.y) return a.y - b.y;
      return a.order - b.order;
    });
    var lastY = null;
    var lastHeight = 0;
    var out = [];
    for (var j = 0; j < rows.length; j++) {
      var row = rows[j];
      var half = row.height / 2;
      var topLimit = top + half;
      var bottomLimit = bottom - half;
      if (topLimit > bottomLimit) {
        var mid = (top + bottom) / 2;
        topLimit = mid;
        bottomLimit = mid;
      }
      var py = Math.max(topLimit, Math.min(bottomLimit, row.y));
      var offset = Math.max(LABEL_MIN_HEIGHT_PX, row.height || 0,
                            lastHeight || 0);
      if (lastY !== null && py - lastY < offset) {
        py = Math.min(lastY + offset, bottomLimit);
      }
      lastY = py;
      lastHeight = row.height || fallback;
      out.push({
        entry: row.entry, y: py,
        height: row.height || fallback,
      });
    }
    return out;
  }

  /* ── group + selection primitives ────────────────────────────────────── */

  function groupMap(groups) {
    var map = {};
    if (!isArray(groups)) return map;
    for (var i = 0; i < groups.length; i++) {
      var group = groups[i];
      if (!group || group.id === null || group.id === undefined) continue;
      map[String(group.id)] = group;
    }
    return map;
  }

  function isVisible(item, groups) {
    var map = groupMap(groups);
    var group = map[String(item && item.group_id)];
    if (!group) return true;
    return group.visible !== false;
  }

  function visibleItems(items, groups) {
    var out = [];
    for (var i = 0; i < (items || []).length; i++) {
      if (isVisible(items[i], groups)) out.push(items[i]);
    }
    return out;
  }

  function effectiveStyle(item, selectedId) {
    var selected = selectedId !== null && selectedId !== undefined &&
      item.id === selectedId;
    if (selected && item.kind !== "zone") {
      return { selected: true, color: SELECTED_COLOR, width: SELECTED_WIDTH };
    }
    return {
      selected: selected,
      color: item.color || DEFAULT_DRAWING_COLOR,
      width: typeof item.width === "number" ? item.width
        : (LINE_WIDTHS[item.kind] || 1.0),
    };
  }

  /* ── the render plan (all geometry in frac-index / price) ────────────── */

  function renderPlan(items, groups, selectedId) {
    var plan = {
      lines: [], hlines: [], rects: [], labels: [], handles: [],
      selectedId: selectedId === undefined ? null : selectedId,
    };
    var rows = visibleItems(items, groups);
    for (var i = 0; i < rows.length; i++) {
      var item = rows[i];
      var style = effectiveStyle(item, plan.selectedId);
      var z = typeof item.z === "number" ? item.z : DRAWING_Z;
      var j;
      if (item.kind === "trendline" || item.kind === "measure") {
        var points = item.points || [];
        if (points.length !== 2) continue;
        plan.lines.push({
          id: item.id, kind: item.kind,
          x1: Number(points[0][0]), y1: Number(points[0][1]),
          x2: Number(points[1][0]), y2: Number(points[1][1]),
          color: style.color, width: style.width, z: z,
          selected: style.selected,
        });
      } else if (item.kind === "horizontal") {
        plan.hlines.push({
          id: item.id, kind: item.kind, level: null,
          price: Number(item.price), color: style.color,
          width: style.width, z: z,
        });
      } else if (item.kind === "fibonacci") {
        var levels = item.levels || [];
        for (j = 0; j < levels.length; j++) {
          plan.hlines.push({
            id: item.id, kind: item.kind, level: Number(levels[j][0]),
            price: Number(levels[j][1]), color: style.color,
            width: style.width, z: z,
          });
        }
      } else if (item.kind === "zone") {
        plan.rects.push({
          id: item.id, kind: item.kind,
          /* LinearRegionItem spans the whole pane; x1/x2 are handle-only. */
          x1: null, x2: null,
          y1: Number(item.y1), y2: Number(item.y2),
          color: item.color || DEFAULT_DRAWING_COLOR,
          fillAlpha: typeof item.fillAlpha === "number"
            ? item.fillAlpha : ZONE_ALPHA,
          width: style.width, z: z,
        });
      }
      var labels = labelsFor(item);
      for (j = 0; j < labels.length; j++) plan.labels.push(labels[j]);
      if (style.selected && !item.locked) {
        var anchors = handlePoints(item.kind, item);
        for (j = 0; j < anchors.length; j++) {
          plan.handles.push({
            id: item.id, frac: anchors[j][0], price: anchors[j][1],
            size: HANDLE_SIZE, pen: HANDLE_PEN, brush: HANDLE_BRUSH,
            penWidth: HANDLE_PEN_WIDTH,
          });
        }
      }
    }
    return plan;
  }

  /* ── drag-edit mirror (Python `drag_drawing_item` is authoritative) ──── */

  function clampZone(item) {
    var y1 = Number(item.y1);
    var y2 = Number(item.y2);
    item.y1 = Math.min(y1, y2);
    item.y2 = Math.max(y1, y2);
    return item;
  }

  function dragItem(item, pointIndex, dFrac, dPrice, body) {
    var out = {};
    for (var key in item) {
      if (Object.prototype.hasOwnProperty.call(item, key)) out[key] = item[key];
    }
    var dPriceN = Number(dPrice);
    var dFracN = Number(dFrac);
    if (out.kind === "trendline" || out.kind === "measure" ||
        out.kind === "fibonacci") {
      var points = [];
      for (var i = 0; i < (out.points || []).length; i++) {
        points.push([Number(out.points[i][0]), Number(out.points[i][1])]);
      }
      if (points.length !== 2) return out;
      if (body) {
        for (var j = 0; j < points.length; j++) {
          points[j][0] += dFracN;
          points[j][1] += dPriceN;
        }
      } else {
        var at = pointIndex === 0 ? 0 : 1;
        points[at][0] += dFracN;
        points[at][1] += dPriceN;
      }
      out.points = points;
      if (out.kind === "fibonacci") {
        out.levels = fibLevels(points[0][1], points[1][1], out.type || "retr");
      } else if (out.kind === "measure") {
        var dy = points[1][1] - points[0][1];
        out.delta = {
          dy: dy,
          pct: points[0][1] ? (dy / points[0][1]) * 100.0 : 0.0,
        };
      }
    } else if (out.kind === "horizontal") {
      out.price = Number(out.price) + dPriceN;
    } else if (out.kind === "zone") {
      if (body) {
        out.y1 = Number(out.y1) + dPriceN;
        out.y2 = Number(out.y2) + dPriceN;
      } else if (pointIndex === 0) {
        out.y1 = Number(out.y1) + dPriceN;
      } else {
        out.y2 = Number(out.y2) + dPriceN;
      }
      clampZone(out);
    }
    out.handles = handlePoints(out.kind, out);
    return out;
  }

  /* ── wire validation (JS receives validated payloads only) ───────────── */

  function validatePoint(point, allowNullX) {
    if (!isArray(point) || point.length !== 2) {
      return "point must be [frac_index, price]";
    }
    if (!(allowNullX && point[0] === null) && !isFiniteNumber(point[0])) {
      return "point frac_index must be a finite number";
    }
    if (!isFiniteNumber(point[1])) return "point price must be a finite number";
    return null;
  }

  function validatePoints(points, count) {
    if (!isArray(points)) return "points must be an array";
    if (count !== null && points.length !== count) {
      return "points must carry exactly " + count + " anchors";
    }
    for (var i = 0; i < points.length; i++) {
      var err = validatePoint(points[i], false);
      if (err) return "points[" + i + "]: " + err;
    }
    return null;
  }

  function validateItem(item) {
    if (item === null || typeof item !== "object" || isArray(item)) {
      return "item must be an object";
    }
    if (DRAWING_KINDS.indexOf(item.kind) === -1) {
      return "unknown drawing kind: " + item.kind;
    }
    if (typeof item.color !== "string" || item.color.length === 0) {
      return "item.color must be a non-empty string";
    }
    if (item.id !== null && item.id !== undefined && !isFiniteNumber(item.id)) {
      return "item.id must be a number or null";
    }
    if (!isFiniteNumber(item.z)) return "item.z must be a finite number";
    if (!isFiniteNumber(item.width)) return "item.width must be a finite number";
    if (typeof item.locked !== "boolean") return "item.locked must be a boolean";
    if (typeof item.selected !== "boolean") {
      return "item.selected must be a boolean";
    }
    if (!isArray(item.handles)) return "item.handles must be an array";
    for (var h = 0; h < item.handles.length; h++) {
      var herr = validatePoint(item.handles[h], true);
      if (herr) return "handles[" + h + "]: " + herr;
    }
    var err;
    if (item.kind === "trendline" || item.kind === "measure" ||
        item.kind === "fibonacci") {
      err = validatePoints(item.points, 2);
      if (err) return err;
    }
    if (item.kind === "measure") {
      if (!item.delta || typeof item.delta !== "object" ||
          !isFiniteNumber(item.delta.dy) || !isFiniteNumber(item.delta.pct)) {
        return "measure requires a numeric delta {dy, pct}";
      }
    }
    if (item.kind === "horizontal") {
      if (!isFiniteNumber(item.price)) return "horizontal requires price";
    }
    if (item.kind === "zone") {
      if (!isFiniteNumber(item.y1) || !isFiniteNumber(item.y2)) {
        return "zone requires numeric y1/y2";
      }
      if (item.y1 > item.y2) return "zone bounds must be normalised (y1 <= y2)";
      if (!isArray(item.span) || item.span.length !== 2 ||
          !isFiniteNumber(item.span[0]) || !isFiniteNumber(item.span[1])) {
        return "zone span must be two fractional indices";
      }
      if (item.span[0] > item.span[1]) return "zone span must be normalised";
      if (!isFiniteNumber(item.fillAlpha)) {
        return "zone requires a numeric fillAlpha";
      }
    }
    if (item.kind === "fibonacci") {
      if (item.type !== "retr" && item.type !== "ext") {
        return "fib type must be 'retr' or 'ext'";
      }
      if (!isArray(item.levels) || item.levels.length === 0) {
        return "fibonacci requires levels";
      }
      for (var i = 0; i < item.levels.length; i++) {
        var level = item.levels[i];
        if (!isArray(level) || level.length !== 2 ||
            !isFiniteNumber(level[0]) || !isFiniteNumber(level[1])) {
          return "levels entries must be [ratio, price]";
        }
      }
    }
    return null;
  }

  function validateOp(op) {
    if (op === null || typeof op !== "object" || isArray(op)) {
      return "op must be an object";
    }
    if (op.series !== DRAWING_CHANNEL) {
      return 'op.series must be "drawings"';
    }
    if (op.op === "clear_drawings") {
      if (Object.keys(op).sort().join(",") !== "op,series") {
        return "clear_drawings must not carry payload";
      }
      return null;
    }
    if (op.op === "set_drawings") {
      if (Object.keys(op).sort().join(",") !== "items,op,series") {
        return "set_drawings must carry exactly items";
      }
      if (!isArray(op.items)) return "op.items must be an array";
      for (var i = 0; i < op.items.length; i++) {
        var err = validateItem(op.items[i]);
        if (err) return "items[" + i + "]: " + err;
      }
      return null;
    }
    if (op.op === "set_drawing_primitive") {
      if (DRAWING_KINDS.indexOf(op.kind) === -1) {
        return "unknown drawing kind: " + op.kind;
      }
      var count = op.kind === "horizontal" ? 1 : 2;
      return validatePoints(op.points, count);
    }
    if (op.op === "select_drawing") {
      if (op.id !== null && !isFiniteNumber(op.id)) {
        return "select_drawing id must be a number or null";
      }
      return null;
    }
    if (op.op === "drag_drawing") {
      if (!isFiniteNumber(op.id)) return "drag_drawing requires id";
      if (DRAWING_KINDS.indexOf(op.kind) === -1) {
        return "unknown drawing kind: " + op.kind;
      }
      if (typeof op.body !== "boolean") {
        return "drag_drawing requires the body flag";
      }
      if (!isFiniteNumber(op.point_index)) {
        return "drag_drawing requires point_index";
      }
      if (op.points !== null && op.points !== undefined) {
        var perr = validatePoints(op.points, 2);
        if (perr) return perr;
      }
      if (!isArray(op.handles)) return "drag_drawing requires handles";
      return null;
    }
    return "unknown op: " + op.op;
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

  /* ── chart glue (a chart/series handle is required; node never needs) ── */

  var chartRef = null;
  var seriesRef = null;
  var items = [];
  var groups = [];
  var primitives = [];
  var selectedId = null;
  var planSnapshot = renderPlan([], [], null);
  var primitiveHandle = null;

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

  function itemsWithSelection() {
    var rows = [];
    for (var i = 0; i < items.length; i++) {
      var item = {};
      for (var key in items[i]) {
        if (Object.prototype.hasOwnProperty.call(items[i], key)) {
          item[key] = items[i][key];
        }
      }
      item.selected = selectedId !== null && item.id === selectedId;
      rows.push(item);
    }
    return rows;
  }

  function planForCurrent() {
    var rows = itemsWithSelection();
    var extra = [];
    for (var i = 0; i < primitives.length; i++) {
      extra.push(primitives[i]);
    }
    return renderPlan(rows.concat(extra), groups, selectedId);
  }

  function refresh() {
    planSnapshot = planForCurrent();
    if (primitiveHandle && typeof primitiveHandle.requestUpdate === "function") {
      primitiveHandle.requestUpdate();
    }
  }

  function replaceGeometry(target, op) {
    if (op.points !== null && op.points !== undefined) {
      target.points = clone(op.points);
    }
    if (op.price !== null && op.price !== undefined) target.price = op.price;
    if (op.y1 !== null && op.y1 !== undefined) target.y1 = op.y1;
    if (op.y2 !== null && op.y2 !== undefined) target.y2 = op.y2;
    if (op.delta !== null && op.delta !== undefined) {
      target.delta = clone(op.delta);
    }
    if (op.levels !== null && op.levels !== undefined) {
      target.levels = clone(op.levels);
    }
    if (op.handles !== null && op.handles !== undefined) {
      target.handles = clone(op.handles);
    }
    return target;
  }

  function applyOp(op) {
    if (op.op === "clear_drawings") {
      items = [];
      primitives = [];
      selectedId = null;
      return true;
    }
    if (op.op === "set_drawings") {
      items = clone(op.items);
      if (selectedId !== null) {
        var found = false;
        for (var i = 0; i < items.length; i++) {
          if (items[i].id === selectedId) found = true;
        }
        if (!found) selectedId = null;
      }
      return true;
    }
    if (op.op === "set_drawing_primitive") {
      primitives.push({
        id: null,
        kind: op.kind,
        color: DEFAULT_DRAWING_COLOR,
        group_id: null,
        locked: false,
        selected: false,
        z: DRAWING_Z,
        width: LINE_WIDTHS[op.kind] || 1.0,
        points: clone(op.points),
        handles: [],
      });
      return true;
    }
    if (op.op === "select_drawing") {
      selectedId = op.id === null || op.id === undefined ? null : op.id;
      return true;
    }
    if (op.op === "drag_drawing") {
      for (var j = 0; j < items.length; j++) {
        if (items[j].id === op.id) {
          replaceGeometry(items[j], op);
          return true;
        }
      }
      return false;
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

  /* ── canvas primitive (LWC v5 series primitive) ─────────────────────── */

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

  function drawPlan(context, scope, plan) {
    var chart = chartRef;
    var series = seriesRef;
    if (!chart || !series) return 0;
    var timeScale = chart.timeScale ? chart.timeScale() : null;
    var priceToCoordinate = series.priceToCoordinate;
    if (!timeScale || typeof priceToCoordinate !== "function") return 0;
    var drawCount = 0;
    var width = scope && scope.mediaSize ? scope.mediaSize.width : 0;
    var height = scope && scope.mediaSize ? scope.mediaSize.height : 0;
    var hpr = scope && scope.horizontalPixelRatio ? scope.horizontalPixelRatio : 1;
    var vpr = scope && scope.verticalPixelRatio ? scope.verticalPixelRatio : 1;
    var cssWidth = width / hpr;
    var cssHeight = height / vpr;
    var right = cssWidth - LABEL_INSET_PX;

    context.save();
    context.beginPath();
    context.rect(0, 0, width, height);
    context.clip();
    var i;
    for (i = 0; i < plan.rects.length; i++) {
      var rect = plan.rects[i];
      var yTop = priceToCoordinate(rect.y2);
      var yBottom = priceToCoordinate(rect.y1);
      if (yTop === null || yBottom === null) continue;
      context.globalAlpha = (rect.fillAlpha === undefined ? ZONE_ALPHA
        : rect.fillAlpha) / 255;
      context.fillStyle = rect.color;
      context.fillRect(0, yTop * vpr, width, (yBottom - yTop) * vpr);
      context.globalAlpha = 1;
      context.strokeStyle = rect.color;
      context.lineWidth = Math.max(1, rect.width * vpr);
      context.beginPath();
      context.moveTo(0, yTop * vpr);
      context.lineTo(width, yTop * vpr);
      context.moveTo(0, yBottom * vpr);
      context.lineTo(width, yBottom * vpr);
      context.stroke();
      drawCount++;
    }
    for (i = 0; i < plan.hlines.length; i++) {
      var line = plan.hlines[i];
      var y = priceToCoordinate(line.price);
      if (y === null) continue;
      context.strokeStyle = line.color;
      context.lineWidth = Math.max(1, line.width * vpr);
      context.beginPath();
      context.moveTo(0, y * vpr);
      context.lineTo(width, y * vpr);
      context.stroke();
      drawCount++;
    }
    for (i = 0; i < plan.lines.length; i++) {
      var seg = plan.lines[i];
      var x1 = coordinateForFrac(seg.x1, timeScale);
      var x2 = coordinateForFrac(seg.x2, timeScale);
      var y1 = priceToCoordinate(seg.y1);
      var y2 = priceToCoordinate(seg.y2);
      if (x1 === null || x2 === null || y1 === null || y2 === null) continue;
      context.strokeStyle = seg.color;
      context.lineWidth = Math.max(1, seg.width * vpr);
      context.beginPath();
      context.moveTo(x1 * hpr, y1 * vpr);
      context.lineTo(x2 * hpr, y2 * vpr);
      context.stroke();
      drawCount++;
    }

    /* Labels: two groups — inner-right labels stack by pixel y; the measure
     * Δ label is centred on its segment and never participates. */
    var inner = [];
    var centred = [];
    for (i = 0; i < plan.labels.length; i++) {
      var label = plan.labels[i];
      var py = priceToCoordinate(label.price);
      if (py === null) continue;
      if (label.anchor === LABEL_ANCHOR) {
        inner.push({ label: label, y: py, height: LABEL_MIN_HEIGHT_PX });
      } else {
        centred.push({ label: label, y: py });
      }
    }
    var stacked = stackInnerLabels(inner, {
      top: 0, bottom: cssHeight, labelHeight: LABEL_MIN_HEIGHT_PX,
    });
    context.font = "11px sans-serif";
    context.textBaseline = "middle";
    for (i = 0; i < stacked.length; i++) {
      var placed = stacked[i];
      context.fillStyle = placed.entry.label.color;
      context.textAlign = "right";
      context.fillText(placed.entry.label.text, right * hpr,
                       placed.y * vpr);
      drawCount++;
    }
    for (i = 0; i < centred.length; i++) {
      var mid = centred[i];
      var mx = coordinateForFrac(mid.label.frac, timeScale);
      if (mx === null) continue;
      context.fillStyle = mid.label.color;
      context.textAlign = "center";
      context.fillText(mid.label.text, mx * hpr, mid.y * vpr);
      drawCount++;
    }

    /* Handles: the selected, unlocked drawing's anchors. */
    for (i = 0; i < plan.handles.length; i++) {
      var handle = plan.handles[i];
      var hx = handle.frac === null
        ? LABEL_INSET_PX
        : coordinateForFrac(handle.frac, timeScale);
      var hy = priceToCoordinate(handle.price);
      if (hx === null || hy === null) continue;
      context.beginPath();
      context.arc(hx * hpr, hy * vpr, (handle.size / 2) * vpr, 0,
                  Math.PI * 2);
      context.fillStyle = handle.brush;
      context.fill();
      context.strokeStyle = handle.pen;
      context.lineWidth = Math.max(1, handle.penWidth * vpr);
      context.stroke();
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
      /* LWC 5.x `ISeriesPrimitivePaneView.renderer` is a **method**
       * (``renderer(): IPrimitivePaneRenderer | null``). Returning the object
       * itself made the library call it as a function — "this.Yh.renderer is
       * not a function" — so no primitive ever drew. */
      paneViews: function () {
        return [{
          renderer: function () { return renderer; },
        }];
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

  /* The host page forwards the view's drawing envelopes here. */
  function applyDrawOps(env) {
    return applyOps(chartRef, seriesRef, env);
  }

  function setGroups(value) {
    groups = isArray(value) ? clone(value) : [];
    refresh();
  }

  /* What the engine currently shows — the parity evidence. */
  function snapshot() {
    return {
      items: clone(items),
      primitives: clone(primitives),
      selectedId: selectedId,
      plan: clone(planSnapshot),
    };
  }

  function clear() {
    items = [];
    primitives = [];
    selectedId = null;
    refresh();
  }

  /* ── page → Python reports (Q-20) ─────────────────────────────────────
   *
   * The drawing tools were dead because nothing in the page could reach a
   * Python slot. Every message below is one JSON string handed to the
   * `LwBridge` slot of the same name (the mirror of `opsJson`), and the view
   * re-emits it on the pre-D47 `DrawingController` surface. Geometry crosses
   * as the page's own fractional indices; Python maps it back to timestamps.
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

  function geometryPayload(item) {
    var out = { kind: (item && item.kind) ? item.kind : "" };
    if (!item) return out;
    if (isArray(item.points)) out.points = clone(item.points);
    if (isArray(item.span)) out.span = clone(item.span);
    if (item.price !== undefined && item.price !== null) {
      out.price = Number(item.price);
    }
    if (item.y1 !== undefined && item.y1 !== null) out.y1 = Number(item.y1);
    if (item.y2 !== undefined && item.y2 !== null) out.y2 = Number(item.y2);
    if (item.type) out.type = item.type;
    if (item.color) out.color = item.color;
    if (item.group_id !== undefined) out.group_id = item.group_id;
    return out;
  }

  /* A drawing gesture finished: report the new primitive. */
  function commitDrawing(item, bridge) {
    if (!item || !item.kind) return false;
    return notifyPage("drawingCommitted", geometryPayload(item), bridge);
  }

  /* An existing drawing was edited (drag / colour / settings). */
  function reportDrawingUpdate(item, bridge) {
    if (!item || !item.kind) return false;
    var payload = geometryPayload(item);
    payload.id = (item.id === undefined ? null : item.id);
    return notifyPage("drawingUpdated", payload, bridge);
  }

  function reportDrawingDelete(id, bridge) {
    return notifyPage("drawingDeleted", { id: id }, bridge);
  }

  /* Selection is a page-side gesture: mirror it locally, then report it. */
  function selectDrawing(id, bridge) {
    selectedId = (id === null || id === undefined) ? null : id;
    refresh();
    return notifyPage("selectionChanged", { id: selectedId }, bridge);
  }

  return {
    ENVELOPE_VERSION: ENVELOPE_VERSION,
    DRAWING_CHANNEL: DRAWING_CHANNEL,
    DRAWING_KINDS: DRAWING_KINDS,
    DEFAULT_DRAWING_COLOR: DEFAULT_DRAWING_COLOR,
    LINE_WIDTHS: LINE_WIDTHS,
    DRAWING_Z: DRAWING_Z,
    ZONE_ALPHA: ZONE_ALPHA,
    LABEL_INSET_PX: LABEL_INSET_PX,
    LABEL_MIN_HEIGHT_PX: LABEL_MIN_HEIGHT_PX,
    LABEL_ANCHOR: LABEL_ANCHOR,
    SELECTED_COLOR: SELECTED_COLOR,
    SELECTED_WIDTH: SELECTED_WIDTH,
    HANDLE_SIZE: HANDLE_SIZE,
    HANDLE_PEN: HANDLE_PEN,
    HANDLE_BRUSH: HANDLE_BRUSH,
    HANDLE_PEN_WIDTH: HANDLE_PEN_WIDTH,
    FIB_LEVELS: FIB_LEVELS,
    FIB_EXTENSION_LEVELS: FIB_EXTENSION_LEVELS,
    SOLID: SOLID,
    interp: interp,
    fracToDisplay: fracToDisplay,
    displayToFrac: displayToFrac,
    fibLevels: fibLevels,
    priceText: priceText,
    signedText: signedText,
    fibLabel: fibLabel,
    measureLabel: measureLabel,
    handlePoints: handlePoints,
    labelsFor: labelsFor,
    stackInnerLabels: stackInnerLabels,
    groupMap: groupMap,
    isVisible: isVisible,
    visibleItems: visibleItems,
    effectiveStyle: effectiveStyle,
    renderPlan: renderPlan,
    dragItem: dragItem,
    validatePoint: validatePoint,
    validateItem: validateItem,
    validateOp: validateOp,
    validateEnvelope: validateEnvelope,
    bind: bind,
    applyOps: applyOps,
    applyDrawOps: applyDrawOps,
    setGroups: setGroups,
    snapshot: snapshot,
    clear: clear,
    pageBridge: pageBridge,
    notifyPage: notifyPage,
    commitDrawing: commitDrawing,
    reportDrawingUpdate: reportDrawingUpdate,
    reportDrawingDelete: reportDrawingDelete,
    selectDrawing: selectDrawing,
  };
});
