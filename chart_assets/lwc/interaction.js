/* interaction.js — Phase 5 interaction surface for the LWC engine (P6-07, D47.7).
 *
 * Two mirrored halves. Both transcribe Python; neither reinterprets it:
 *
 * 1. Router mirror. ROUTER_TRANSITIONS is a row-for-row transcription of the
 *    frozen Python table owned by `ui/chart_mouse_router.py` (one `RouterMode`
 *    state, intent helpers, guard-clause dispatch). `resolveTransition()`
 *    keeps the same precedence (DRAWING > ZOOMING > ALARM_PLACING > IDLE),
 *    the same refusal on ALARM_PLACING + magnifier (TR-9) and the same
 *    mid-gesture symbol-change reset (TR-17). `routeGesture()` mirrors the
 *    press/drag/click guard clauses (alarm first in IDLE, drawing-only click
 *    while DRAWING). `tests/test_lwc_router_mirror.py` drives every row on
 *    both engines and fails on any divergence.
 *
 * 2. In-HTML controls. CONTROL_BUTTONS mirrors `ui/chart_controls.py`'s
 *    signal surface — zoom_out / zoom_in / magnify_toggled / reset — with the
 *    same labels and tooltips. The Python shim
 *    (`ui/lwc_view.py::LwcChartView.handle_control`) owns the router intent;
 *    this side renders the buttons, reports the intent and applies the
 *    resulting op. The buttons live in the page, the precedence stays in one
 *    frozen place.
 *
 * Crosshair drift (Q63 / A108, owner-confirmed accept-drift). The crosshair
 * and its price/time labels are the library-native crosshair + axis labels:
 * `crosshairOptions()` sets `vertLine.labelVisible` / `horzLine.labelVisible`
 * on the chart's own crosshair, and `applyCrosshair()` applies it through
 * `chart.applyOptions`. No custom crosshair-label primitive exists here or
 * anywhere else in `chart_assets/` — the D2/Q33 lane stops at the engine
 * boundary. Both zoom/magnifier and crosshair are the library's; the Qt
 * dialogs (zone / horizontal line / alarm) are untouched and stay Qt.
 *
 * Renderer boundary: timestamps and prices only. No network, no trading
 * logic, no DOM access outside the browser-guarded glue at the bottom.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.LwInteraction = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var INTERACTION_VERSION = 1;

  /* ── router mirror (frozen Python table: TR-1 … TR-17) ─────────────── */

  var ROUTER_MODES = ["IDLE", "DRAWING", "ZOOMING", "ALARM_PLACING"];

  /* Intent triggers: the router's own transition helpers. */
  var ROUTER_TRIGGERS = [
    "draw_tool",
    "draw_cursor",
    "enter_zoom",
    "enter_alarm_placing",
    "exit_to_idle",
    "symbol_change",
  ];

  /* Gesture triggers: the guard-clause dispatch rows. */
  var ROUTER_GESTURES = ["press", "drag", "click"];

  /* One row per frozen Python transition. `from` is the mode the hidden
   * gesture starts in, `to` the mode it ends in; `refused` marks a row the
   * router declines without touching any overlay (TR-9). TR-13…TR-16 are
   * dispatch rows: the mode is unchanged and the interesting result is which
   * overlay received the gesture (`routeGesture`). */
  var ROUTER_TRANSITIONS = [
    { id: "TR-1", from: "IDLE", trigger: "draw_tool", to: "DRAWING" },
    { id: "TR-2", from: "IDLE", trigger: "enter_zoom", to: "ZOOMING" },
    { id: "TR-3", from: "IDLE", trigger: "enter_alarm_placing", to: "ALARM_PLACING" },
    { id: "TR-4", from: "DRAWING", trigger: "enter_zoom", to: "ZOOMING" },
    { id: "TR-5", from: "ZOOMING", trigger: "draw_tool", to: "DRAWING" },
    { id: "TR-6", from: "ZOOMING", trigger: "enter_alarm_placing", to: "ALARM_PLACING" },
    { id: "TR-7", from: "DRAWING", trigger: "enter_alarm_placing", to: "ALARM_PLACING" },
    { id: "TR-8", from: "ALARM_PLACING", trigger: "draw_tool", to: "DRAWING" },
    { id: "TR-9", from: "ALARM_PLACING", trigger: "enter_zoom", to: "ALARM_PLACING", refused: true },
    { id: "TR-10", from: "DRAWING", trigger: "draw_cursor", to: "IDLE" },
    { id: "TR-11", from: "ZOOMING", trigger: "exit_to_idle", to: "IDLE" },
    { id: "TR-12", from: "ALARM_PLACING", trigger: "exit_to_idle", to: "IDLE" },
    { id: "TR-13", from: "IDLE", trigger: "press", to: "IDLE" },
    { id: "TR-14", from: "IDLE", trigger: "drag", to: "IDLE" },
    { id: "TR-15", from: "IDLE", trigger: "click", to: "IDLE" },
    { id: "TR-16", from: "DRAWING", trigger: "click", to: "DRAWING" },
    { id: "TR-17", from: "DRAWING", trigger: "symbol_change", to: "IDLE" },
  ];

  function initialState() {
    return { mode: "IDLE", tool: "none", zoomActive: false, alarmMode: false };
  }

  function copyState(state) {
    if (!state || ROUTER_MODES.indexOf(state.mode) === -1) {
      throw new Error("unknown router mode: " + (state && state.mode));
    }
    return {
      mode: state.mode,
      tool: state.tool || "none",
      zoomActive: !!state.zoomActive,
      alarmMode: !!state.alarmMode,
    };
  }

  /* One router intent — the JS face of `ChartMouseRouter`'s helpers.
   * Returns `{ state, refused, trigger }`; `refused` is TR-9's refusal. */
  function resolveTransition(state, trigger) {
    var s = copyState(state);
    var refused = false;

    if (trigger === "draw_tool") {
      /* enter_drawing(real tool): cancel zoom or alarm placement first. */
      if (s.mode === "ZOOMING") s.zoomActive = false;
      else if (s.mode === "ALARM_PLACING") s.alarmMode = false;
      s.tool = "tool";
      s.mode = "DRAWING";
    } else if (trigger === "draw_cursor") {
      /* enter_drawing(cursor): disarm the tool, never disturb zoom/alarm. */
      s.tool = "cursor";
      if (s.mode === "DRAWING") s.mode = "IDLE";
    } else if (trigger === "enter_zoom") {
      /* TR-9: alarm placement has first refusal on the magnifier. */
      if (s.mode === "ALARM_PLACING") {
        refused = true;
      } else {
        if (s.mode === "DRAWING") s.tool = "cursor";
        s.zoomActive = true;
        s.mode = "ZOOMING";
      }
    } else if (trigger === "enter_alarm_placing") {
      if (s.mode === "ZOOMING") s.zoomActive = false;
      else if (s.mode === "DRAWING") s.tool = "cursor";
      s.alarmMode = true;
      s.mode = "ALARM_PLACING";
    } else if (trigger === "exit_to_idle") {
      s.zoomActive = false;
      s.mode = "IDLE";
    } else if (trigger === "symbol_change") {
      /* TR-17: a symbol change mid-gesture resets, discarding the draft. */
      s.zoomActive = false;
      s.tool = "cursor";
      s.mode = "IDLE";
    } else if (ROUTER_GESTURES.indexOf(trigger) !== -1) {
      /* Dispatch row: a gesture never changes the mode. */
    } else {
      throw new Error("unknown router trigger: " + trigger);
    }

    return { state: s, refused: refused, trigger: trigger };
  }

  /* Guard-clause dispatch (the Python `view_mouse_*` order). `hits` says
   * whether each wired overlay would handle the gesture (default: yes).
   * Returns the overlay that ends up handling it, or "none". */
  function routeGesture(state, gesture, hits) {
    var h = hits || {};
    if (ROUTER_GESTURES.indexOf(gesture) === -1) {
      throw new Error("unknown gesture: " + gesture);
    }
    function handled(name) {
      return { handledBy: h[name] === false ? "none" : name };
    }
    if (state.mode === "ZOOMING") return handled("zoom");
    if (state.mode === "DRAWING") return handled("drawing");
    if (state.mode === "ALARM_PLACING") return handled("alarm");
    /* IDLE: alarm gets first refusal on a press/drag unless a drawing tool
     * is armed (never true in IDLE by derivation); a click always prefers
     * the alarm. Both fall through to drawing on a miss. */
    var toolActive = state.tool === "tool";
    if (gesture === "press" || gesture === "drag") {
      if (!toolActive && h.alarm !== false) return { handledBy: "alarm" };
    } else if (h.alarm !== false) {
      return { handledBy: "alarm" };
    }
    return { handledBy: h.drawing === false ? "none" : "drawing" };
  }

  /* ── in-HTML controls (mirror of ui/chart_controls.py) ─────────────── */

  var CONTROL_BUTTONS = [
    { id: "zoom-out", label: "−", title: "Zoom out", intent: "zoom_out" },
    { id: "zoom-in", label: "+", title: "Zoom in", intent: "zoom_in" },
    {
      id: "magnifier",
      label: "⌕",
      title: "Magnifier (drag to zoom)",
      intent: "magnify_toggle",
      toggle: true,
    },
    { id: "reset", label: "Reset", title: "Reset view", intent: "reset" },
  ];

  function controlFor(id) {
    for (var i = 0; i < CONTROL_BUTTONS.length; i++) {
      if (CONTROL_BUTTONS[i].id === id) return CONTROL_BUTTONS[i];
    }
    return null;
  }

  /* Zoom multipliers — the same numbers `chart.js`'s keyboard handler and the
   * Python shim carry (magnifier/+ zoom in, − zooms out). */
  var ZOOM_FACTORS = { in: 0.8, out: 1.25 };

  /* Zoom about the visible-range midpoint (mirror of chart.js `zoom`). */
  function zoomBy(chart, step) {
    if (!chart || !chart.timeScale || typeof chart.timeScale !== "function") {
      return false;
    }
    var scale = chart.timeScale();
    var range = scale.getVisibleLogicalRange();
    if (!range) return false;
    var factor = step > 0 ? ZOOM_FACTORS.in : ZOOM_FACTORS.out;
    var mid = (range.from + range.to) / 2;
    var half = ((range.to - range.from) / 2) * factor;
    scale.setVisibleLogicalRange({ from: mid - half, to: mid + half });
    return true;
  }

  /* ── library-native crosshair (Q63 / A108 accept-drift) ─────────────── */

  /* LightweightCharts.CrosshairMode.Normal — the library's own crosshair;
   * both axis labels are the library's. Nothing below draws a label. */
  var CROSSHAIR_MODE_ID = 0;
  var CROSSHAIR_MODE_NAME = "normal";

  var CROSSHAIR_OPTIONS = {
    mode: CROSSHAIR_MODE_ID,
    vertLine: {
      color: "rgba(148,163,184,0.55)",
      width: 1,
      style: 0,
      visible: true,
      labelVisible: true,
      labelBackgroundColor: "#1f2937",
    },
    horzLine: {
      color: "rgba(148,163,184,0.55)",
      width: 1,
      style: 0,
      visible: true,
      labelVisible: true,
      labelBackgroundColor: "#1f2937",
    },
  };

  function lineOptions(line) {
    return {
      color: line.color,
      width: line.width,
      style: line.style,
      visible: line.visible,
      labelVisible: line.labelVisible,
      labelBackgroundColor: line.labelBackgroundColor,
    };
  }

  function crosshairOptions() {
    return {
      mode: CROSSHAIR_OPTIONS.mode,
      vertLine: lineOptions(CROSSHAIR_OPTIONS.vertLine),
      horzLine: lineOptions(CROSSHAIR_OPTIONS.horzLine),
    };
  }

  /* Apply the library crosshair to a chart; returns what crossed. */
  function applyCrosshair(chart) {
    if (!chart || typeof chart.applyOptions !== "function") return null;
    var options = { crosshair: crosshairOptions() };
    chart.applyOptions(options);
    return options;
  }

  /* ── DG92 focus round-trip (lwc-focus-forward-v1) ───────────────────── */

  var FOCUS_MODEL = "lwc-focus-forward-v1";

  /* Esc blurs the page and hands focus back to the Qt chain through the
   * bridge's `focusReleased` slot (chart.js's bindKeyboard calls the same). */
  function releaseFocus(el, bridge) {
    var target = pageBridge(bridge);
    if (el && typeof el.blur === "function") el.blur();
    if (target && typeof target.focusReleased === "function") {
      target.focusReleased();
      return true;
    }
    return false;
  }

  /* ── page → Python report (Q-20) ─────────────────────────────────────
   *
   * TR-9's refusal is a real user-facing event: the magnifier is pressed
   * while alarm placement is armed and nothing happens. The page reports it
   * on the bridge's `zoomRefused` slot so the Qt status hint runs; the view
   * re-emits it on `zoom_refused`, the same signal the default engine has.
   */
  function pageBridge(bridge) {
    var target = bridge;
    if (!target && typeof window !== "undefined") target = window.lwBridge;
    return target || null;
  }

  function reportZoomRefused(trigger, bridge, mode) {
    var target = pageBridge(bridge);
    if (!target || typeof target.zoomRefused !== "function") return false;
    target.zoomRefused(JSON.stringify({
      trigger: String(trigger || ""),
      mode: (mode === undefined ? null : mode),
    }));
    return true;
  }

  /* ── browser glue (called from the page; nothing runs at load) ──────── */

  function mountControls(container, onControl, bridge) {
    if (!container || typeof document === "undefined") return [];
    var made = [];
    for (var i = 0; i < CONTROL_BUTTONS.length; i++) {
      (function (spec) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.id = "control-" + spec.id;
        btn.className = "lw-control";
        btn.textContent = spec.label;
        btn.title = spec.title;
        if (spec.toggle) btn.setAttribute("aria-pressed", "false");
        btn.addEventListener("click", function () {
          var value = null;
          if (spec.toggle) {
            var next = btn.getAttribute("aria-pressed") !== "true";
            btn.setAttribute("aria-pressed", next ? "true" : "false");
            value = next;
          }
          var result = (typeof onControl === "function")
            ? onControl(spec.id, value)
            : null;
          /* Q-20: the router refused this control (TR-9) — report it. */
          if (result && result.refused) {
            reportZoomRefused(spec.intent, bridge, result.mode);
          }
        });
        container.appendChild(btn);
        made.push(btn);
      })(CONTROL_BUTTONS[i]);
    }
    return made;
  }

  return {
    INTERACTION_VERSION: INTERACTION_VERSION,
    ROUTER_MODES: ROUTER_MODES,
    ROUTER_TRIGGERS: ROUTER_TRIGGERS,
    ROUTER_GESTURES: ROUTER_GESTURES,
    ROUTER_TRANSITIONS: ROUTER_TRANSITIONS,
    CONTROL_BUTTONS: CONTROL_BUTTONS,
    ZOOM_FACTORS: ZOOM_FACTORS,
    CROSSHAIR_MODE_ID: CROSSHAIR_MODE_ID,
    CROSSHAIR_MODE_NAME: CROSSHAIR_MODE_NAME,
    CROSSHAIR_OPTIONS: CROSSHAIR_OPTIONS,
    FOCUS_MODEL: FOCUS_MODEL,
    initialState: initialState,
    resolveTransition: resolveTransition,
    routeGesture: routeGesture,
    controlFor: controlFor,
    zoomBy: zoomBy,
    crosshairOptions: crosshairOptions,
    applyCrosshair: applyCrosshair,
    releaseFocus: releaseFocus,
    pageBridge: pageBridge,
    reportZoomRefused: reportZoomRefused,
    mountControls: mountControls,
  };
});
