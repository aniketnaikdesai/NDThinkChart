/* gestures.js — the LWC page's gesture layer (Q-32: ALARM_PLACING end-to-end).
 *
 * Q-31 carried the five channels to the page, but the mode was arm-only: the
 * interaction channel published `mode`/`tool`, `chart.js` mirrored them into
 * `routerState`, and nothing turned a click during ALARM_PLACING into an
 * alarm. This module is that half:
 *
 * - `applyRouterOp(op)` mirrors the router mode/tool exactly as `chart.js`'s
 *   `routerState` does (same precedence, same `reset_view` handling, same
 *   intent fallbacks), then syncs the page chrome: in ALARM_PLACING the
 *   container cursor is a crosshair and the library's own pan/zoom is
 *   suppressed (`handleScroll` / `handleScale`); every other mode restores
 *   both. The sync is transition-driven, so a repeated mode op is a no-op.
 * - pointer gestures on the container: `pointermove` maps the client Y to a
 *   price through the live series (`coordinateToPrice`) and draws the D21.10
 *   yellow preview via `LwAlarms.showPreview`; `pointerup` without a drag
 *   (> 3 px) reports the click as `alarmCreated`, so the existing bridge slot
 *   -> `pageAlarmCreated` -> `_on_page_alarm_created` ->
 *   `alarm_controller.create_requested` path runs. The preview is cleared
 *   after the report and on every route out of ALARM_PLACING.
 *
 * The price-line code is NOT duplicated here: `alarms.js` owns the preview
 * op (`showPreview` / `clearPreview` apply `set_alarm_preview` /
 * `clear_alarm_preview` through its own `applyOp`, the same path Python's
 * `show_alarm_preview` uses).
 *
 * Q-33 adds the drawing half alongside it: in DRAWING with a real tool the
 * same suppression/cursor machinery applies, pointer gestures build the
 * kind's item in page units (fractional index + price), the draft renders
 * live through `LwPrimitives.setDraft`, and pointerup commits it through
 * `LwPrimitives.commitDrawing`. A half-built item (null fraction/price) is
 * discarded, and the tool stays armed after a commit.
 *
 * Node note: the mapping core has no DOM/chart dependency and is exported for
 * `node --test`; the glue never boots without a bound container, and a
 * container without `addEventListener` (the node fake) simply does not get
 * pointer listeners.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwGestures = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var GESTURE_VERSION = 1;
  var ALARM_MODE = "ALARM_PLACING";
  var DRAWING_MODE = "DRAWING";
  /* The tools that draw. "cursor"/"zoom"/"none" never arm a drawing. */
  var DRAWING_TOOLS = ["trendline", "horizontal", "zone", "fibonacci", "measure"];
  /* A press that moves more than this is a drag, not a placement click. */
  var DRAG_PX = 3;
  /* Leaving the canvas briefly (e.g. onto the price axis) is not a cancel. */
  var LEAVE_GRACE_MS = 250;

  /* Draft geometry constants — the same values primitives.js renders.
   * Geometry itself is the service's (ui/lwc_view.py sends it for stored
   * rows); a live draft is composed here from pixels and replayed through
   * `LwPrimitives.setDraft`. */
  var DEFAULT_DRAWING_COLOR = "#38bdf8";
  var DRAWING_Z = 10;
  var ZONE_ALPHA = 36;
  var DRAWING_LINE_WIDTHS = {
    trendline: 1.4,
    horizontal: 1.2,
    zone: 1.0,
    fibonacci: 1.0,
    measure: 1.4,
  };
  var FIB_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];

  function isArray(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
  }

  function isFiniteNumber(x) {
    return typeof x === "number" && isFinite(x);
  }

  function initialRouterState() {
    return { mode: "IDLE", tool: "none" };
  }

  /* One interaction-channel op -> the router mode/tool it sets.
   *
   * Row-for-row the precedence `chart.js` uses for `routerState`: a
   * `reset_view` resets to IDLE/cursor, an explicit `mode`/`tool` always
   * wins, and the intent fallbacks cover the ops that carry no `tool`. */
  function nextRouterState(state, op) {
    var next = { mode: state.mode, tool: state.tool };
    if (!op || typeof op !== "object" || isArray(op)) return next;
    if (op.op === "reset_view") {
      next.mode = "IDLE";
      next.tool = "cursor";
    }
    if (typeof op.mode === "string") next.mode = op.mode;
    if (typeof op.tool === "string") {
      next.tool = op.tool;
    } else if (op.intent === "enter_zoom") {
      next.tool = "zoom";
    } else if (op.intent === "exit_to_idle" || op.intent === "symbol_change") {
      next.tool = "cursor";
    }
    return next;
  }

  function isAlarmPlacing(state) {
    return !!state && state.mode === ALARM_MODE;
  }

  function isDrawing(state) {
    return !!state && state.mode === DRAWING_MODE &&
      DRAWING_TOOLS.indexOf(state.tool) !== -1;
  }

  function interactionActive(state) {
    return isAlarmPlacing(state) || isDrawing(state);
  }

  /* Did the pointer travel far enough between down and up to be a drag? */
  function dragExceeded(down, up, limit) {
    if (!down || !up) return false;
    var dx = Number(up.x) - Number(down.x);
    var dy = Number(up.y) - Number(down.y);
    if (!isFinite(dx) || !isFinite(dy)) return false;
    var px = limit === undefined ? DRAG_PX : Number(limit);
    if (!isFinite(px)) px = DRAG_PX;
    return Math.sqrt(dx * dx + dy * dy) > px;
  }

  /* ── drawing draft geometry (page units: fractional index + price) ──── */

  function fibLevels(y1, y2) {
    var out = [];
    for (var i = 0; i < FIB_LEVELS.length; i++) {
      out.push([FIB_LEVELS[i], y1 + FIB_LEVELS[i] * (y2 - y1)]);
    }
    return out;
  }

  /* Active-group tool state (P9 / S-P9-1): the toolbar's selected draw
   * group plus its color. `setActiveGroup` is the single writer — the
   * Python toolbar re-pushes it on every group reload and symbol change —
   * and `drawingItem` stamps both into the commit item. Ungrouped (a null
   * / non-numeric id) keeps the default color and a null group. */
  var activeGroupId = null;
  var activeGroupColor = DEFAULT_DRAWING_COLOR;

  function setActiveGroup(id, color) {
    var num = (id === null || id === undefined ||
               typeof id === "boolean") ? null : Number(id);
    if (num === null || !isFinite(num)) {
      activeGroupId = null;
      activeGroupColor = DEFAULT_DRAWING_COLOR;
    } else {
      activeGroupId = num;
      activeGroupColor = (typeof color === "string" && color) ?
        color : DEFAULT_DRAWING_COLOR;
    }
    return { id: activeGroupId, color: activeGroupColor };
  }

  function validAnchor(anchor) {
    return !!anchor && isFiniteNumber(anchor.frac) &&
      isFiniteNumber(anchor.price);
  }

  /* One kind's item from its anchors. `null` while any needed anchor is
   * missing/non-finite — a half-built drawing is never rendered or sent.
   * Horizontal uses the press price only and needs no second anchor. */
  function drawingItem(kind, first, second) {
    if (DRAWING_TOOLS.indexOf(kind) === -1) return null;
    if (!validAnchor(first)) return null;
    var item = {
      id: null,
      kind: kind,
      color: activeGroupColor,
      group_id: activeGroupId,
      locked: false,
      selected: false,
      z: DRAWING_Z,
      width: DRAWING_LINE_WIDTHS[kind] || 1.0,
      handles: [],
    };
    if (kind === "horizontal") {
      item.price = first.price;
      item.handles = [[null, first.price]];
      return item;
    }
    if (!validAnchor(second)) return null;
    if (kind === "zone") {
      item.span = [Math.min(first.frac, second.frac),
                   Math.max(first.frac, second.frac)];
      item.y1 = Math.min(first.price, second.price);
      item.y2 = Math.max(first.price, second.price);
      item.fillAlpha = ZONE_ALPHA;
      item.handles = [[item.span[0], item.y1], [item.span[1], item.y2]];
      return item;
    }
    var points = [[first.frac, first.price], [second.frac, second.price]];
    item.points = points;
    if (kind === "measure") {
      var dy = second.price - first.price;
      item.delta = {
        dy: dy,
        pct: first.price ? (dy / first.price) * 100.0 : 0.0,
      };
    } else if (kind === "fibonacci") {
      item.type = "retr";
      item.levels = fibLevels(first.price, second.price);
    }
    item.handles = [[points[0][0], points[0][1]],
                    [points[1][0], points[1][1]]];
    return item;
  }

  /* ── chart glue (a container is required; node never needs one) ─────── */

  var chartRef = null;
  var containerRef = null;
  var seriesGetter = null;
  var alarmsRef = null;
  var primitivesRef = null;
  var bridgeRef = null;
  var timers = null;
  var router = initialRouterState();
  var previewPrice = null;
  var draftItem = null;
  var suppressed = false;
  var pointerBound = false;
  var boundContainer = null;
  var press = null;
  var leaveTimer = null;

  function resolveGlobal(name) {
    if (typeof self !== "undefined" && self && self[name]) return self[name];
    if (typeof window !== "undefined" && window && window[name]) return window[name];
    return null;
  }

  function alarmsModule() {
    return alarmsRef || resolveGlobal("LwAlarms");
  }

  function primitivesModule() {
    return primitivesRef || resolveGlobal("LwPrimitives");
  }

  function schedule(fn, ms) {
    if (timers && typeof timers.set === "function") return timers.set(fn, ms);
    if (typeof setTimeout === "function") return setTimeout(fn, ms);
    return null;
  }

  function cancel(handle) {
    if (handle === null || handle === undefined) return;
    if (timers && typeof timers.clear === "function") {
      timers.clear(handle);
      return;
    }
    if (typeof clearTimeout === "function") clearTimeout(handle);
  }

  function liveSeries() {
    return typeof seriesGetter === "function" ? seriesGetter() : null;
  }

  /* client Y -> the live series' price. The coordinate the library wants is
   * pane-local, so the container's own top is the offset. A null price (no
   * series data under that pixel) never becomes 0. */
  function priceAt(clientY) {
    var target = liveSeries();
    if (!target || typeof target.coordinateToPrice !== "function") return null;
    var top = 0;
    if (containerRef && typeof containerRef.getBoundingClientRect === "function") {
      var rect = containerRef.getBoundingClientRect();
      if (rect && isFinite(Number(rect.top))) top = Number(rect.top);
    }
    var price = target.coordinateToPrice(Number(clientY) - top);
    if (price === null || price === undefined) return null;
    var value = Number(price);
    return isFinite(value) ? value : null;
  }

  /* Draw the yellow preview through the alarm channel's own op path. */
  function showPreview(price) {
    var alarms = alarmsModule();
    if (!alarms || typeof alarms.showPreview !== "function") return false;
    return alarms.showPreview(price) === true;
  }

  /* client X -> the page's fractional logical index. The axis unit is the
   * candle axis (the same one Python maps back to bar timestamps). */
  function logicalAt(clientX) {
    var chart = chartRef;
    if (!chart || typeof chart.timeScale !== "function") return null;
    var scale = chart.timeScale();
    if (!scale || typeof scale.coordinateToLogical !== "function") return null;
    var left = 0;
    if (containerRef &&
        typeof containerRef.getBoundingClientRect === "function") {
      var rect = containerRef.getBoundingClientRect();
      if (rect && isFinite(Number(rect.left))) left = Number(rect.left);
    }
    var frac = scale.coordinateToLogical(Number(clientX) - left);
    if (frac === null || frac === undefined) return null;
    var value = Number(frac);
    return isFinite(value) ? value : null;
  }

  function anchorAt(clientX, clientY) {
    return { frac: logicalAt(clientX), price: priceAt(clientY) };
  }

  /* The draft is rendered by primitives.js through its normal plan; gestures
   * only owns the geometry. A module that is absent (node, a page without the
   * drawing channel) simply gets no live draft. */
  function showDraft(item) {
    var prim = primitivesModule();
    if (!prim || typeof prim.setDraft !== "function") return false;
    return prim.setDraft(item) !== false;
  }

  function clearDraftNow() {
    draftItem = null;
    var prim = primitivesModule();
    if (prim && typeof prim.clearDraft === "function") prim.clearDraft();
    return true;
  }

  function clearPreviewNow() {
    previewPrice = null;
    var alarms = alarmsModule();
    if (alarms && typeof alarms.clearPreview === "function") alarms.clearPreview();
    return true;
  }

  /* Public clear: also drops a pending pointerleave debounce. */
  function clearPreview() {
    if (leaveTimer !== null) {
      cancel(leaveTimer);
      leaveTimer = null;
    }
    return clearPreviewNow();
  }

  /* Transition-driven chrome sync: crosshair + suppressed pan/zoom while the
   * router owns the gesture (ALARM_PLACING or DRAWING with a real tool),
   * restored everywhere else. The mode op repeats on every interaction
   * envelope, so this must not re-apply on a no-op call. */
  function syncChrome() {
    var active = interactionActive(router);
    if (active === suppressed) {
      if (!active) {
        if (previewPrice !== null) clearPreviewNow();
        if (draftItem !== null) clearDraftNow();
      }
      return;
    }
    suppressed = active;
    if (containerRef && containerRef.style) {
      containerRef.style.cursor = active ? "crosshair" : "";
    }
    if (chartRef && typeof chartRef.applyOptions === "function") {
      chartRef.applyOptions({ handleScroll: !active, handleScale: !active });
    }
    if (!active) {
      clearPreviewNow();
      clearDraftNow();
    }
  }

  /* Apply one interaction-channel op. Idempotent: the same mode applied
   * twice changes nothing and issues no second `applyOptions`. */
  function applyRouterOp(op) {
    /* P9 / S-P9-1: the toolbar's active-group push. It carries no mode or
     * tool, so the router is untouched — only the stamped group/color the
     * next commit carries. Every interaction op reaches this function (the
     * chart dispatcher forwards the whole channel), so no other page change
     * is needed for the push to land. */
    if (op && op.op === "set_active_group") {
      setActiveGroup(op.group_id, op.color);
      return state();
    }
    var wasAlarm = isAlarmPlacing(router);
    var wasDrawing = isDrawing(router);
    var previousTool = router.tool;
    router = nextRouterState(router, op);
    if (wasAlarm && !isAlarmPlacing(router)) clearPreview();
    /* Leave DRAWING, or switch tools inside it: the half-drawn item is
     * discarded (the reference overlay's "cursor switch drops the draft"). */
    if (wasDrawing && (!isDrawing(router) || previousTool !== router.tool)) {
      clearDraftNow();
    }
    syncChrome();
    return state();
  }

  function state() {
    return {
      mode: router.mode,
      tool: router.tool,
      previewPrice: previewPrice,
      draft: draftItem ? JSON.parse(JSON.stringify(draftItem)) : null,
      alarmMode: isAlarmPlacing(router),
      drawingMode: isDrawing(router),
      panZoomSuppressed: suppressed,
      pointerBound: pointerBound,
    };
  }

  /* ── pointer gestures ──────────────────────────────────────────────── */

  function onPointerDown(ev) {
    press = {
      x: Number(ev && ev.clientX),
      y: Number(ev && ev.clientY),
    };
    if (isDrawing(router)) {
      press.anchor = anchorAt(press.x, press.y);
      return true;
    }
    return isAlarmPlacing(router);
  }

  function onPointerMove(ev) {
    if (isDrawing(router)) {
      if (!press) return false;
      var first = press.anchor;
      var current = anchorAt(ev && ev.clientX, ev && ev.clientY);
      if (!validAnchor(first) || !validAnchor(current)) {
        clearDraftNow();
        return false;
      }
      var item = drawingItem(router.tool, first, current);
      if (!item) {
        clearDraftNow();
        return false;
      }
      draftItem = item;
      showDraft(item);
      return true;
    }
    if (!isAlarmPlacing(router)) return false;
    var price = priceAt(ev && ev.clientY);
    if (price === null) return false;
    previewPrice = price;
    showPreview(price);
    return true;
  }

  function onPointerUp(ev) {
    var down = press;
    press = null;
    if (isDrawing(router)) {
      return commitDrawingGesture(down, ev);
    }
    if (!isAlarmPlacing(router)) return false;
    var up = { x: Number(ev && ev.clientX), y: Number(ev && ev.clientY) };
    /* A drag in alarm mode is a cancel, not a placement. */
    if (dragExceeded(down, up)) {
      clearPreview();
      return false;
    }
    var price = priceAt(ev && ev.clientY);
    if (price === null) price = previewPrice;
    if (price === null) {
      clearPreview();
      return false;
    }
    var alarms = alarmsModule();
    var reported = false;
    if (alarms && typeof alarms.reportAlarmCreated === "function") {
      reported = alarms.reportAlarmCreated(price, bridgeRef) === true;
    }
    clearPreview();
    return reported;
  }

  /* The drawing half of pointerup: build the armed kind's item and commit it
   * through primitives.js. Horizontal commits from the press price with no
   * travel; every other kind needs a real drag (> 3 px) so a stray click is
   * not a degenerate two-point drawing. The tool stays armed — only the
   * draft is cleared — so several drawings can be made in a row. */
  function commitDrawingGesture(down, ev) {
    if (!down || !validAnchor(down.anchor)) {
      clearDraftNow();
      return false;
    }
    var kind = router.tool;
    var item;
    if (kind === "horizontal") {
      item = drawingItem("horizontal", down.anchor, null);
    } else {
      var up = { x: Number(ev && ev.clientX), y: Number(ev && ev.clientY) };
      if (!dragExceeded(down, up)) {
        clearDraftNow();
        return false;
      }
      var current = anchorAt(up.x, up.y);
      if (!validAnchor(current)) {
        clearDraftNow();
        return false;
      }
      item = drawingItem(kind, down.anchor, current);
    }
    if (!item) {
      clearDraftNow();
      return false;
    }
    var prim = primitivesModule();
    var reported = false;
    if (prim && typeof prim.commitDrawing === "function") {
      reported = prim.commitDrawing(item, bridgeRef) === true;
    }
    clearDraftNow();
    return reported;
  }

  /* Crossing onto the price/time axis briefly must not eat the preview; a
   * real exit does. The mode is never changed here — only the preview. */
  function onPointerLeave() {
    if (!isAlarmPlacing(router)) return false;
    if (leaveTimer !== null) cancel(leaveTimer);
    leaveTimer = schedule(function () {
      leaveTimer = null;
      if (!isAlarmPlacing(router)) return;
      clearPreviewNow();
    }, LEAVE_GRACE_MS);
    return true;
  }

  function detachPointer() {
    if (boundContainer &&
        typeof boundContainer.removeEventListener === "function") {
      boundContainer.removeEventListener("pointerdown", onPointerDown);
      boundContainer.removeEventListener("pointermove", onPointerMove);
      boundContainer.removeEventListener("pointerup", onPointerUp);
      boundContainer.removeEventListener("pointerleave", onPointerLeave);
    }
    boundContainer = null;
    pointerBound = false;
  }

  function attachPointer() {
    if (!containerRef || typeof containerRef.addEventListener !== "function") {
      return false;
    }
    if (pointerBound && boundContainer === containerRef) return false;
    if (pointerBound) detachPointer();
    containerRef.addEventListener("pointerdown", onPointerDown);
    containerRef.addEventListener("pointermove", onPointerMove);
    containerRef.addEventListener("pointerup", onPointerUp);
    containerRef.addEventListener("pointerleave", onPointerLeave);
    boundContainer = containerRef;
    pointerBound = true;
    return true;
  }

  /* bind(chart, container, seriesGetter[, options]) — options may carry the
   * alarm module / bridge / timer pair for a node test; the page passes
   * three arguments and resolves the globals. */
  function bind(chart, container, getter, options) {
    chartRef = chart || null;
    containerRef = container || null;
    seriesGetter = typeof getter === "function" ? getter : null;
    options = options || {};
    if (options.alarms) alarmsRef = options.alarms;
    if (options.primitives) primitivesRef = options.primitives;
    if (options.bridge) bridgeRef = options.bridge;
    if (options.timers) timers = options.timers;
    attachPointer();
    syncChrome();
    return chartRef !== null || containerRef !== null;
  }

  /* Test/probe reset — back to the page's boot state. */
  function reset() {
    if (leaveTimer !== null) {
      cancel(leaveTimer);
      leaveTimer = null;
    }
    router = initialRouterState();
    previewPrice = null;
    draftItem = null;
    press = null;
    suppressed = false;
    activeGroupId = null;
    activeGroupColor = DEFAULT_DRAWING_COLOR;
    return state();
  }

  return {
    GESTURE_VERSION: GESTURE_VERSION,
    ALARM_MODE: ALARM_MODE,
    DRAWING_MODE: DRAWING_MODE,
    DRAWING_TOOLS: DRAWING_TOOLS,
    DRAG_PX: DRAG_PX,
    LEAVE_GRACE_MS: LEAVE_GRACE_MS,
    initialRouterState: initialRouterState,
    nextRouterState: nextRouterState,
    isAlarmPlacing: isAlarmPlacing,
    isDrawing: isDrawing,
    dragExceeded: dragExceeded,
    priceAt: priceAt,
    logicalAt: logicalAt,
    drawingItem: drawingItem,
    setActiveGroup: setActiveGroup,
    fibLevels: fibLevels,
    applyRouterOp: applyRouterOp,
    bind: bind,
    state: state,
    clearPreview: clearPreview,
    clearDraft: clearDraftNow,
    reset: reset,
  };
});
