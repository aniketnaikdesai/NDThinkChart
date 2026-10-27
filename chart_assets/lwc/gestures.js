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
  /* A press that moves more than this is a drag, not a placement click. */
  var DRAG_PX = 3;
  /* Leaving the canvas briefly (e.g. onto the price axis) is not a cancel. */
  var LEAVE_GRACE_MS = 250;

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

  /* ── chart glue (a container is required; node never needs one) ─────── */

  var chartRef = null;
  var containerRef = null;
  var seriesGetter = null;
  var alarmsRef = null;
  var bridgeRef = null;
  var timers = null;
  var router = initialRouterState();
  var previewPrice = null;
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

  /* Transition-driven chrome sync: crosshair + suppressed pan/zoom only in
   * ALARM_PLACING, restored everywhere else. The mode op repeats on every
   * interaction envelope, so this must not re-apply on a no-op call. */
  function syncChrome() {
    var alarm = isAlarmPlacing(router);
    if (alarm === suppressed) {
      if (!alarm && previewPrice !== null) clearPreviewNow();
      return;
    }
    suppressed = alarm;
    if (containerRef && containerRef.style) {
      containerRef.style.cursor = alarm ? "crosshair" : "";
    }
    if (chartRef && typeof chartRef.applyOptions === "function") {
      chartRef.applyOptions({ handleScroll: !alarm, handleScale: !alarm });
    }
    if (!alarm) clearPreviewNow();
  }

  /* Apply one interaction-channel op. Idempotent: the same mode applied
   * twice changes nothing and issues no second `applyOptions`. */
  function applyRouterOp(op) {
    var wasAlarm = isAlarmPlacing(router);
    router = nextRouterState(router, op);
    if (wasAlarm && !isAlarmPlacing(router)) clearPreview();
    syncChrome();
    return state();
  }

  function state() {
    return {
      mode: router.mode,
      tool: router.tool,
      previewPrice: previewPrice,
      alarmMode: isAlarmPlacing(router),
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
    return isAlarmPlacing(router);
  }

  function onPointerMove(ev) {
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
    press = null;
    suppressed = false;
    return state();
  }

  return {
    GESTURE_VERSION: GESTURE_VERSION,
    ALARM_MODE: ALARM_MODE,
    DRAG_PX: DRAG_PX,
    LEAVE_GRACE_MS: LEAVE_GRACE_MS,
    initialRouterState: initialRouterState,
    nextRouterState: nextRouterState,
    isAlarmPlacing: isAlarmPlacing,
    dragExceeded: dragExceeded,
    priceAt: priceAt,
    applyRouterOp: applyRouterOp,
    bind: bind,
    state: state,
    clearPreview: clearPreview,
    reset: reset,
  };
});
