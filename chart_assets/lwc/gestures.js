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
  /* P10 (D50.1): drag-editing grab radii. A handle press starts the kind's
   * anchor drag; a body press nearby starts a whole-move. Radii are in
   * screen px and converted to anchor units through the local axis scales,
   * so they behave the same at any zoom. */
  var DRAG_HANDLE_PX = 6;
  var DRAG_BODY_PX = 12;
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
  /* ESC-091: pending abandon of an orphaned in-flight drag (pointerleave
   * past the grace window). Separate from the alarm-preview `leaveTimer`
   * so neither path disturbs the other. */
  var leaveDragTimer = null;
  /* P10 (D50.1): the in-flight drag-edit session, or null. Shape:
   * { id, kind, point_index, body, start, anchor, d_frac, d_price, moved,
   *   current }. `point_index` is the addressed anchor (-1 for a whole-move,
   *   which the drag surface ignores in favour of `body`). `start` is the
   *   untouched wire item the deltas apply to; the engine's own items are
   *   never mutated mid-drag — the preview rides the draft only. */
  var drag = null;
  /* P10 (D50.1): optional per-move validation surface, injected through
   * `bind` options (`{ drag: { dragDrawing(id, kind, point_index, d_frac,
   * d_price, body) } }`). It stands in for the `drag_drawing` validation
   * surface: every per-move delta is addressed to that signature. Absent in
   * the page (no per-move slot exists on the bridge yet), where the drag is
   * previewed locally and only the pointer-up commit crosses to Python. */
  var dragSurfaceRef = null;

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
    /* Any route change abandons an in-flight drag-edit: the press context
     * it measured against is gone, and it must never commit afterwards. */
    if (drag) cancelDrag();
    if (leaveDragTimer !== null) {
      cancel(leaveDragTimer);
      leaveDragTimer = null;
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
    /* A fresh press supersedes any pending orphan abandon: the pointer is
     * back inside, so a stale timer must not kill the new session. */
    if (leaveDragTimer !== null) {
      cancel(leaveDragTimer);
      leaveDragTimer = null;
    }
    press = {
      x: Number(ev && ev.clientX),
      y: Number(ev && ev.clientY),
    };
    if (isDrawing(router)) {
      press.anchor = anchorAt(press.x, press.y);
      return true;
    }
    if (isAlarmPlacing(router)) return true;
    /* Select mode: a press on the selected drawing starts a drag-edit
     * session (body whole-move or the handle's anchor drag). Anything
     * else — including a locked drawing — is left to selection. */
    var hit = hitTest(press.x, press.y);
    if (!hit) {
      /* ESC-091: a non-hit press clears a stale session (its pointer-up
       * happened off-canvas and never arrived), so the next travel
       * cannot commit orphaned geometry. */
      if (drag) cancelDrag();
      press = null;
      return false;
    }
    press.anchor = anchorAt(press.x, press.y);
    startDrag(hit, press.anchor);
    return true;
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
    /* An in-flight drag-edit: accumulate the delta from the press anchor,
     * route it to the validation surface, and refresh the preview.
     * ESC-091: moves that arrive with the primary button released are
     * not drag travel (the pointer-up happened off-canvas) — ignore
     * them. Synthetic node events omit `buttons`, so only an explicit
     * release refuses. */
    if (drag && !isAlarmPlacing(router)) {
      if (!dragButtonHeld(ev)) return false;
      /* The pointer is back inside with the button held: the excursion
       * was within grace, so the pending orphan abandon is dropped. */
      if (leaveDragTimer !== null) {
        cancel(leaveDragTimer);
        leaveDragTimer = null;
      }
      var now = anchorAt(ev && ev.clientX, ev && ev.clientY);
      if (!validAnchor(now) || !validAnchor(drag.anchor)) return false;
      var dFrac = now.frac - drag.anchor.frac;
      var dPrice = now.price - drag.anchor.price;
      if (!isFiniteNumber(dFrac) || !isFiniteNumber(dPrice)) return false;
      drag.d_frac = dFrac;
      drag.d_price = dPrice;
      drag.moved = true;
      routeDragDelta(drag);
      previewDrag(drag);
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
    /* The pointer is inside (it released here): no orphan abandon can
     * still be pending for the session this resolves. */
    if (leaveDragTimer !== null) {
      cancel(leaveDragTimer);
      leaveDragTimer = null;
    }
    if (isDrawing(router)) {
      return commitDrawingGesture(down, ev);
    }
    /* An in-flight drag-edit: travel past the threshold commits the
     * dragged geometry; a click with no travel is selection's, not a drag,
     * so it emits nothing. */
    if (drag) {
      var session = drag;
      drag = null;
      var up = { x: Number(ev && ev.clientX), y: Number(ev && ev.clientY) };
      if (!session.moved || !dragExceeded(down, up)) {
        clearDragPreview();
        return false;
      }
      return commitDrag(session);
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

  /* ── drag-editing (P10 / D50.1) ──────────────────────────────────────
   *
   * The page initiation path `gestures.js` lacked (A129): while the router
   * is outside the drawing/alarm modes, a press on the selected drawing's
   * body starts a whole-move (all five kinds) and a press on a handle
   * starts that handle's anchor drag (trendline/fibonacci/measure
   * endpoints, zone corners, the horizontal price level). A locked drawing
   * never starts a drag here — presentation-level refusal only; the Python
   * `drag_drawing` surface remains the authoritative gate (S-P10-4).
   *
   * Per-move deltas are addressed exactly to the `drag_drawing` signature
   * `(id, kind, point_index, d_frac, d_price, body)` and routed to the
   * injected drag surface when one is bound; the live preview is the
   * page-side `dragItem` geometry shown through the draft. Pointer-up past
   * the drag threshold commits through `reportDrawingUpdate` (the existing
   * `drawingUpdated` → `updated(id, payload, color)` close-out); a click
   * with no travel and an explicit cancel emit nothing and clear the draft,
   * restoring the engine state. */

  function cloneWire(item) {
    return JSON.parse(JSON.stringify(item));
  }

  /* The selected wire item, or null. The handles it carries are the
   * selection-gated wire handles (S-P10-1); a drawing without them is not
   * draggable from the page. */
  function selectedDrawing() {
    var prim = primitivesModule();
    if (!prim || typeof prim.snapshot !== "function") return null;
    var snap = null;
    try {
      snap = prim.snapshot();
    } catch (err) {
      return null;
    }
    if (!snap || !isArray(snap.items)) return null;
    var i;
    for (i = 0; i < snap.items.length; i++) {
      if (snap.items[i] && snap.items[i].selected === true) {
        return snap.items[i];
      }
    }
    if (snap.selectedId !== null && snap.selectedId !== undefined) {
      for (i = 0; i < snap.items.length; i++) {
        if (snap.items[i] && snap.items[i].id === snap.selectedId) {
          return snap.items[i];
        }
      }
    }
    return null;
  }

  /* The kind's anchors from the authoritative page source when present. */
  function handlePointsFor(item) {
    var prim = primitivesModule();
    if (prim && typeof prim.handlePoints === "function") {
      try {
        var pts = prim.handlePoints(item.kind, item);
        if (isArray(pts)) return pts;
      } catch (err) {
        /* fall through to the wire handles */
      }
    }
    return isArray(item.handles) ? item.handles : [];
  }

  /* Local axis scales around a client point: anchor units per screen px,
   * sampled from the same forward maps the gestures use. */
  function scaleAround(clientX, clientY) {
    var f0 = logicalAt(clientX);
    var f1 = logicalAt(clientX + 1);
    var p0 = priceAt(clientY);
    var p1 = priceAt(clientY + 1);
    return {
      fracPerPx: (isFiniteNumber(f0) && isFiniteNumber(f1)) ?
        Math.abs(f1 - f0) : NaN,
      pricePerPx: (isFiniteNumber(p0) && isFiniteNumber(p1)) ?
        Math.abs(p1 - p0) : NaN,
    };
  }

  /* One axis delta in screen px. An exact zero is always zero, so an exact
   * press still grabs when the local scale is degenerate. */
  function axisPx(delta, perPx) {
    if (delta === 0) return 0;
    if (!isFiniteNumber(perPx) || perPx <= 0) return Infinity;
    return Math.abs(delta) / perPx;
  }

  function segDistPx(ax, ay, bx, by, px, py) {
    var dx = bx - ax;
    var dy = by - ay;
    var len2 = dx * dx + dy * dy;
    var t = len2 > 0 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
    if (t < 0) t = 0;
    else if (t > 1) t = 1;
    var cx = ax + t * dx;
    var cy = ay + t * dy;
    return Math.sqrt((px - cx) * (px - cx) + (py - cy) * (py - cy));
  }

  /* Is the anchor on the item's body (whole-move target)? Handles are
   * tested first by the caller, so this never competes with them. */
  function bodyHit(item, anchor, scales) {
    var kind = item.kind;
    var i;
    if (kind === "trendline" || kind === "measure" ||
        kind === "fibonacci") {
      var points = isArray(item.points) ? item.points : [];
      if (points.length !== 2) return false;
      var coords = [];
      for (i = 0; i < 2; i++) {
        coords.push([Number(points[i][0]), Number(points[i][1])]);
        if (!isFiniteNumber(coords[i][0]) || !isFiniteNumber(coords[i][1])) {
          return false;
        }
      }
      var fpp = scales.fracPerPx;
      var ppp = scales.pricePerPx;
      if (!isFiniteNumber(fpp) || fpp <= 0 ||
          !isFiniteNumber(ppp) || ppp <= 0) {
        return false;
      }
      var dist = segDistPx(
        0, 0,
        (coords[1][0] - coords[0][0]) / fpp,
        (coords[1][1] - coords[0][1]) / ppp,
        (anchor.frac - coords[0][0]) / fpp,
        (anchor.price - coords[0][1]) / ppp);
      return dist <= DRAG_BODY_PX;
    }
    if (kind === "horizontal") {
      if (!isFiniteNumber(Number(item.price))) return false;
      return axisPx(anchor.price - Number(item.price),
                    scales.pricePerPx) <= DRAG_BODY_PX;
    }
    if (kind === "zone") {
      if (!isArray(item.span)) return false;
      var f0 = Math.min(Number(item.span[0]), Number(item.span[1]));
      var f1 = Math.max(Number(item.span[0]), Number(item.span[1]));
      var y0 = Math.min(Number(item.y1), Number(item.y2));
      var y1 = Math.max(Number(item.y1), Number(item.y2));
      if (!isFiniteNumber(f0) || !isFiniteNumber(f1) ||
          !isFiniteNumber(y0) || !isFiniteNumber(y1)) {
        return false;
      }
      return anchor.frac >= f0 && anchor.frac <= f1 &&
        anchor.price >= y0 && anchor.price <= y1;
    }
    return false;
  }

  /* The drag the press starts: { item, point_index, body } or null.
   * Handles win over the body; a locked drawing never starts (the
   * presentation-level half of the lock refusal). */
  function hitTest(clientX, clientY) {
    var item = selectedDrawing();
    if (!item || DRAWING_TOOLS.indexOf(item.kind) === -1) return null;
    if (item.locked === true) return null;
    var anchor = anchorAt(clientX, clientY);
    if (!validAnchor(anchor)) return null;
    var scales = scaleAround(clientX, clientY);
    var handles = handlePointsFor(item);
    for (var h = 0; h < handles.length; h++) {
      var hp = handles[h];
      if (!isArray(hp) || hp.length !== 2) continue;
      if (!isFiniteNumber(Number(hp[1]))) continue;
      var dPrice = axisPx(anchor.price - Number(hp[1]), scales.pricePerPx);
      if (!(dPrice <= DRAG_HANDLE_PX)) continue;
      /* A horizontal handle carries a null x: the price level alone
       * addresses it. */
      if (hp[0] === null || hp[0] === undefined) {
        return { item: item, point_index: h, body: false };
      }
      if (!isFiniteNumber(Number(hp[0]))) continue;
      var dFrac = axisPx(anchor.frac - Number(hp[0]), scales.fracPerPx);
      if (dFrac <= DRAG_HANDLE_PX) {
        return { item: item, point_index: h, body: false };
      }
    }
    if (bodyHit(item, anchor, scales)) {
      return { item: item, point_index: -1, body: true };
    }
    return null;
  }

  /* ESC-091: is the primary button held for this move? A real pointermove
   * always carries `buttons` (bit 1 = primary); an explicit release means
   * the drag already ended off-canvas. Synthetic node events omit both
   * fields, so only an explicit release refuses — the T21/T23 suites
   * drive moves without `buttons` and must keep working. */
  function dragButtonHeld(ev) {
    if (!ev || typeof ev !== "object") return true;
    if (typeof ev.buttons === "number") return (ev.buttons & 1) === 1;
    if (typeof ev.pressure === "number") return ev.pressure > 0;
    return true;
  }

  /* One per-move delta, addressed to the `drag_drawing` signature. */
  function routeDragDelta(session) {
    var surface = dragSurfaceRef;
    if (!surface || typeof surface.dragDrawing !== "function") return false;
    try {
      surface.dragDrawing(session.id, session.kind, session.point_index,
                          session.d_frac, session.d_price, session.body);
      return true;
    } catch (err) {
      return false;
    }
  }

  function clearDragPreview() {
    var prim = primitivesModule();
    if (prim && typeof prim.clearDraft === "function") {
      try {
        prim.clearDraft();
      } catch (err) {
        /* the preview is best-effort; the session state is authoritative */
      }
    }
    return true;
  }

  /* Refresh the live preview from the session totals (never incremental,
   * so the geometry cannot drift across moves). */
  function previewDrag(session) {
    var prim = primitivesModule();
    if (!prim || typeof prim.dragItem !== "function") return false;
    var moved = null;
    try {
      moved = prim.dragItem(session.start, session.point_index,
                            session.d_frac, session.d_price, session.body);
    } catch (err) {
      return false;
    }
    if (!moved) return false;
    session.current = moved;
    if (typeof prim.setDraft === "function") {
      try {
        prim.setDraft(moved);
      } catch (err) {
        /* the preview is best-effort; the session state is authoritative */
      }
    }
    return true;
  }

  function startDrag(hit, anchor) {
    drag = {
      id: hit.item.id,
      kind: hit.item.kind,
      point_index: hit.point_index,
      body: hit.body,
      start: cloneWire(hit.item),
      anchor: { frac: anchor.frac, price: anchor.price },
      d_frac: 0,
      d_price: 0,
      moved: false,
      current: null,
    };
    return drag;
  }

  /* Pointer-up past the drag threshold: the commit. The dragged geometry
   * is recomputed from the session totals and reported through the
   * existing `drawingUpdated` → `updated(id, payload, color)` close-out. */
  function commitDrag(session) {
    var prim = primitivesModule();
    clearDragPreview();
    if (!prim || typeof prim.dragItem !== "function" ||
        typeof prim.reportDrawingUpdate !== "function") {
      return false;
    }
    var moved = null;
    try {
      moved = prim.dragItem(session.start, session.point_index,
                            session.d_frac, session.d_price, session.body);
    } catch (err) {
      return false;
    }
    if (!moved || moved.id === null || moved.id === undefined) return false;
    var reported = false;
    try {
      reported = prim.reportDrawingUpdate(moved, bridgeRef) === true;
    } catch (err) {
      reported = false;
    }
    return reported;
  }

  /* Cancel the in-flight drag: nothing is emitted and the draft preview
   * is cleared, so the engine state (never mutated mid-drag) stands. */
  function cancelDrag() {
    if (!drag) return false;
    drag = null;
    clearDragPreview();
    return true;
  }

  /* The in-flight drag session (a clone), or null. */
  function dragState() {
    return drag ? cloneWire(drag) : null;
  }

  /* Crossing onto the price/time axis briefly must not eat the preview; a
   * real exit does. The mode is never changed here — only the preview. */
  function onPointerLeave() {
    var handled = false;
    /* ESC-091: an in-flight drag that leaves the canvas is abandoned
     * past the grace window (cancelDrag-equivalent: nothing emitted,
     * draft cleared), so a pointer-up outside can never commit stale
     * geometry on a later unrelated pan. */
    if (drag) {
      if (leaveDragTimer !== null) cancel(leaveDragTimer);
      leaveDragTimer = schedule(function () {
        leaveDragTimer = null;
        if (drag) cancelDrag();
      }, LEAVE_GRACE_MS);
      handled = true;
    }
    if (!isAlarmPlacing(router)) return handled;
    if (leaveTimer !== null) cancel(leaveTimer);
    leaveTimer = schedule(function () {
      leaveTimer = null;
      if (!isAlarmPlacing(router)) return;
      clearPreviewNow();
    }, LEAVE_GRACE_MS);
    return true;
  }

  /* ESC-091: the gesture is dead (the pointer will not return) — abandon
   * the in-flight drag immediately, emitting nothing. */
  function onPointerCancel() {
    if (leaveDragTimer !== null) {
      cancel(leaveDragTimer);
      leaveDragTimer = null;
    }
    if (drag) {
      cancelDrag();
      press = null;
      return true;
    }
    if (isDrawing(router)) {
      if (draftItem !== null) clearDraftNow();
      press = null;
      return true;
    }
    press = null;
    return false;
  }

  function detachPointer() {
    if (boundContainer &&
        typeof boundContainer.removeEventListener === "function") {
      boundContainer.removeEventListener("pointerdown", onPointerDown);
      boundContainer.removeEventListener("pointermove", onPointerMove);
      boundContainer.removeEventListener("pointerup", onPointerUp);
      boundContainer.removeEventListener("pointercancel", onPointerCancel);
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
    containerRef.addEventListener("pointercancel", onPointerCancel);
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
    if (options.drag) dragSurfaceRef = options.drag;
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
    if (leaveDragTimer !== null) {
      cancel(leaveDragTimer);
      leaveDragTimer = null;
    }
    router = initialRouterState();
    previewPrice = null;
    draftItem = null;
    press = null;
    drag = null;
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
    /* P10 (D50.1): drag-editing probes — the node suite drives
     * initiation through the pointer handlers and observes/cancels
     * through these. */
    dragState: dragState,
    cancelDrag: cancelDrag,
  };
});
