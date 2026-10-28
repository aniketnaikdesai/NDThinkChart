"""ui/lwc_view.py — the LWC core-chart driver (P6-T05 / Phase 3, D47.5 + T10).

Renders through the offline LWC host behind the batched ``LwBridge`` column
transport (``{v:1, ops:[]}``). The value mapping is shared with the default
engine — every plotted value below comes from ``services/chart_model.py``
and the ``gap_is_non_trading`` authority in
``services/time_collapse_service.py`` — so parity is by construction, not
by parallel logic:

* **v5 panes** — the price pane carries the per-mode series, the volume
  pane the histogram (the JS side keeps them on separate scales).
* **volume ceiling** (Q-9 / AC-D21.2.1, the D21.2 port) — the volume
  transport keeps shipping the raw ``Bar.volume`` values
  (``chart_model.volume_display_columns`` applies no ceiling); the pane's Y
  range is priced engine-side from the *visible* logical range by
  ``chart_assets/lwc/chart.js``'s ``autoscaleInfoProvider``: ``1.10 x`` the
  visible max, the ``100`` floor when no visible bar is non-zero, Y minimum
  ``0`` — ``chart_model.visible_volume_ceiling`` ported verbatim (the
  ESC-028 small-positive band included), recomputed on load/pan/zoom with no
  per-gesture round-trip to Python.
* **real UTC time axis** (Q-20) — the ``ts`` column carries each bar's own
  UTC epoch seconds, **not** a logical index: the axis renders real dates.
  LWC places bars by data index, so a collapsed non-trading gap still
  renders adjacent (the time values jumping is what the label shows). The
  series is strictly ascending and unique. A hole — both bars on the same
  trading session with missing periods between them — crosses as ``k``
  whitespace placeholders (``None`` value slots, rendered as ``{time}``
  only) so it keeps its ``k`` empty slots (AC-D21.4.4). A gap that is
  non-trading time (overnight, weekend, holiday) or that crosses a session
  boundary contributes no placeholders at all (AC-D21.4.1): the two bars
  stay adjacent, so a two-day load is not padded back into a multi-day
  block of blanks. The logical index stays **internal** — drawings, overlays
  and the ``fractional_index_from_display`` pair keep using it, never the
  series time. ``update_live_bar`` sends the same domain, so the live and
  history paths agree.
* **``gap_is_non_trading`` authority** — the collapse map (and therefore
  every logical step) is built on it, exactly as on the default engine.
* **custom tz formatters** — ``local = t - offset`` (``format_tz_label``;
  the JS side mirrors it as ``tzLabel``).
* **per-mode series** — ``candles`` / ``hollow`` / ``heikin`` / ``line`` /
  ``area``. The candle payload always carries OHLC (Heikin-Ashi rows are
  precomputed here for ``heikin``); the mode travels on the ``set_bars``
  op as an optional ``mode`` key the P6-04 validators accept and ignore,
  so the wire contract is unchanged and replay identity holds.
* **live ``series.update``** — ``update_live_bar`` emits single-element
  ``update_bar`` ops (last-tick-wins coalesced by the bridge); history
  is never resent for a tick.
* **study overlays** (P6-06 / Phase 4) — ``set_studies`` /
  ``set_study_overlay`` publish the shared model's study arrays
  (``chart_model.compute_study_values`` over the one ``StudyCache``) as
  nullable value columns on a dedicated study envelope
  (``{"v": 1, "ops": [{"op": "set_study", …}]}``). The bar transport
  pins its series set, so study ops never ride it; the values that cross
  are the model's own arrays — the engine formats, it never computes.
* **interaction** (P6-07 / Phase 5) — the in-HTML control surface
  (``CONTROL_IDS``, mirroring ``ui/chart_controls.py``'s signals) has its
  Python shim in ``LwcChartView.handle_control``: every magnifier press
  goes through the **frozen** ``ui/chart_mouse_router.py`` router, so
  alarm placement refuses it (TR-9) exactly as on the default engine.
  ``ROUTER_TRANSITIONS`` is the transcription of the frozen TR-1…TR-17
  table that ``chart_assets/lwc/interaction.js`` mirrors row for row
  (``tests/test_lwc_router_mirror.py`` drives both engines). Interaction
  ops travel on their own envelope (``interactionOpsEmitted``) — the bar
  transport pins its series set, as for studies. Crosshair and its axis
  labels are **library-native** (Q63 / A108 owner-confirmed accept-drift):
  no custom crosshair primitive exists here or in ``chart_assets/``; the
  zone / horizontal-line / alarm dialogs stay the same Qt dialogs.
* **alarm lines/overlays** (P6-08 / Phase 6) — ``set_alarm_lines`` publishes
  the unchanged alarm records as raw state columns (id, price, direction,
  state bits, note) on their own alarm envelope
  (``{"v": 1, "ops": [{"op": "set_alarms", …}]}``, plus the D21.10 preview
  line ops). The colour precedence, glyph/label composition, pen width and
  z-order mirror ``ui/alarm_overlay.py`` value-for-value, so identical alarm
  state renders identically on both engines. JS composes the label text from
  prices and state — no formatted strings cross. Alarm placement stays in
  the frozen router (``set_alarm_mode``), and the Qt alarm dialogs (create /
  edit / rearm / mute / delete) are untouched.
* **drawing primitives** (P6-09 / Phase 7, D47.5 + DG93) — ``set_drawings``
  publishes the unchanged drawing records as validated primitives on their
  own envelope (``{"v": 1, "ops": [{"op": "set_drawings", …}]}``). Every
  anchor timestamp is mapped to a **fractional logical index** — the same
  display-x axis the candles use, expressed in the axis' own unit — so a
  drawing lands on the identical bar (and between bars at the identical
  relative position) on both engines. ``fractional_index_from_display`` /
  ``display_from_fractional_index`` are the single mapping pair, and
  ``display_from_fractional_index(fractional_index_from_display(x))``
  equals the reference overlay's ``_ts_to_x(ts)`` on the DG93 edge fixtures
  (DST folds, session-boundary bars, display-x collisions). Geometry
  (Fibonacci levels, measure delta, handles) is computed here from
  ``services.drawing_service``; JS receives fractional indices and prices
  only and composes the D11 inner-right labels itself. Zone /
  horizontal-line settings stay the same Qt dialogs (no HTML dialog).
* **overlays** (P6-10 / Phase 8, D47.5) — ``set_overlay`` publishes the
  session bands, the RTH-gap staircase, the VIX sigma lines and the ICT
  concepts on its own envelope (``overlayOpsEmitted``). Every value comes from
  the **unchanged** services the default engine calls (``session_bands``,
  ``calculate_rth_gaps``, ``calculate_vix_standard_deviation``,
  ``calculate_ict_concepts``) and every position from the same display-x
  authority, so identical inputs render identical visuals on both engines.
  The reference constants — the session orange/blue at 10 % alpha and z -10,
  the gap green/red brushes at 0.55/0.32 with their dotted filled border, the
  VIX right-edge sigma labels and the ICT per-concept alphas/z/widths — are
  asserted against those modules by the parity suite, not restated here. JS
  receives fractional indices and prices; it composes every glyph and label
  itself.
* **multi-window hosting** (P6-11 / Phase 9, Q62/A107 + DG90) — the
  per-symbol pop-out window re-hosts on whichever engine
  ``ui.chart_view.create_chart_view`` resolves (the default engine stays the
  default through cutover) and attaches the view to the symbol's
  ``TickerSession`` exactly as the
  default engine's ``ChartPanel`` does (``update_chart`` / ``set_studies`` /
  ``drawing_overlay.set_data`` / ``set_alarms``), so D24's single-writer
  fan-out is unchanged and the D24 cap stays 10 on **both** engines
  (Q62/A107). Each view accounts its own memory (``memory_bytes``: the
  private series copy, the study arrays, the primitives and the replay log)
  and releases it on close (``release_resources``), so no window's arrays
  outlive it. Each window's offline host is its own (``ensure_host``),
  never a shared one.

Density-cap retirement (T10 / Q60 answered-by-default YES / A106): the
density-cap wording of ``AC-D6.4`` / ``AC-D7.1`` / ``AC-D9.1`` is retired
for the library ``barSpacing`` control. The no-overlap guarantee is
restated in ``barSpacing`` terms (DG94) by ``bar_spacing_geometry``:
bodies never overlap (``gap >= 0`` always; ``gap > 0`` whenever the
spacing allows). The default engine keeps satisfying the old ACs until
cutover.

Renderer-only boundary: this module imports nothing beyond Qt, the
standard library, the shared chart model, the collapse authority and the
LWC bridge. It creates no persistence, no network surface, no symbol
list or layout surface, and no transmit path of any kind. Engine
selection (``NDT_CHART_ENGINE``) stays with ``ui/chart_view.py`` — the
factory wiring for this driver lands at cutover; until then the seam
stub keeps session wiring unbroken and this driver is composed directly.
"""

from __future__ import annotations

import bisect
import logging
from datetime import datetime, timezone
from typing import Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from data.bar_aggregator import TIMEFRAME_SECONDS
from services import chart_model
from services.drawing_service import (
    DEFAULT_DRAWING_COLOR,
    DRAWING_KINDS,
    fib_levels,
    normalize_payload,
)
from services.gap_vix_service import (
    calculate_rth_gaps,
    calculate_vix_standard_deviation,
    infer_ticker_context,
)
from services.ict_service import calculate_ict_concepts
from services.market_calendar import session_windows
from services.session_service import session_bands
from services.time_collapse_service import gap_is_non_trading, is_daily_or_coarser
from ui import lwc_bridge as LB
from ui.chart_mouse_router import ChartMouseRouter, RouterMode
from ui.drawing_tools import DRAWING_TOOLS, TOOL_CURSOR

_LOG = logging.getLogger(__name__)

#: The five render modes, mirroring the default engine's ``ChartMode``.
MODES = ("candles", "hollow", "heikin", "line", "area")

#: Mode used before any explicit selection.
DEFAULT_MODE = "candles"

#: Legibility floor carried into the ``barSpacing`` restatement (DG94),
#: in ViewBox logical pixels — the same unit the shipped floor used.
FLOOR_PX = 4.0

#: Full-body share of one inter-bar pitch in the non-dense regime
#: (65 % body / 35 % gap — the D6 intent, restated for ``barSpacing``).
BODY_FRACTION = 0.65


def logical_indices(bars: Sequence, timeframe: str | None,
                    ext_hours: bool) -> list:
    """Logical-index positions for ``bars`` in plotted order.

    Index 0 starts the series; consecutive bars with no hole advance by
    1; a within-session hole of ``k`` missing bars advances by ``1 + k``
    (rendering ``k`` slots of whitespace). Collapsed non-trading gaps
    advance by exactly 1 — ``gap_is_non_trading`` (via the shared
    collapse map) is the authority, as on the default engine.

    Call with the plotted rows (RTH filtering already applied); the
    input list is only read. A degenerate step (two bars sharing one
    display-x) is clamped to advance by 1 so no bar is ever lost to a
    same-time upsert. Returns plain ``int`` positions.
    """
    rows = list(bars or [])
    if not rows:
        return []
    period = TIMEFRAME_SECONDS.get(timeframe or "")
    cmap = chart_model.collapse_for_bars(rows, timeframe, ext_hours)
    if cmap is None or not period:
        return list(range(len(rows)))
    return logical_indices_from_display(chart_model.display_xs(rows, cmap),
                                        period)


def logical_indices_from_display(display_xs: Sequence, period: int) -> list:
    """Logical indices from display-x coordinates (one shared step rule)."""
    out: list = []
    prev_dx = None
    prev_idx = -1
    for dx in display_xs:
        if prev_dx is None:
            idx = 0
        else:
            step = int(round((dx - prev_dx) / period))
            idx = prev_idx + max(1, step)
        out.append(idx)
        prev_dx = dx
        prev_idx = idx
    return out


def hole_spans(indices: Sequence) -> list:
    """Whitespace runs in a logical-index series.

    Returns ``[(after_position, missing_count)]`` — one entry per step
    larger than 1, where ``missing_count = step - 1`` is the number of
    whitespace slots between ``after_position`` and the next bar.
    """
    spans: list = []
    idx = list(indices)
    for prev, cur in zip(idx, idx[1:]):
        if cur - prev > 1:
            spans.append((prev, cur - prev - 1))
    return spans


def gap_is_within_session(a, b, ext_hours: bool) -> bool:
    """True iff the whole span ``(a, b)`` lies inside **one** trading session.

    ``session_windows`` is the non-trading authority here — the very window
    list ``gap_is_non_trading`` (and therefore ``chart_model.collapse_for_bars``)
    is built from, so this adds no second definition of trading time. A span
    no window covers is overnight / weekend / holiday time; a span covered
    only across a boundary (its window starts after ``a`` or ends before
    ``b``) crosses a session. Neither is a within-session hole, so neither
    keeps whitespace slots (AC-D21.4.1 / AC-D21.4.4).
    """
    try:
        a, b = int(a), int(b)
    except (TypeError, ValueError):
        return False
    if b <= a:
        return False
    return any(window["start_ts"] <= a and window["end_ts"] >= b
               for window in session_windows(a, b, ext_hours))


def series_times(bars: Sequence, indices: Sequence,
                 period=None, ext_hours: bool = True) -> tuple[list, list]:
    """Real UTC series times for the plotted rows, plus whitespace flags.

    Returns ``(times, whitespace)`` — two parallel lists in plotted order.
    Every bar contributes its own ``int(bar.ts)``: the page's time axis is
    real UTC epoch seconds (Q-20), so the axis labels real dates. A
    within-session hole of ``k`` missing periods contributes ``k``
    placeholder times **before** the next bar, each flagged ``True`` in
    ``whitespace`` — the page renders those as ``{time}``-only points, so the
    hole keeps its ``k`` empty slots (AC-D21.4.4).

    The hole test is **trading time**, not an index jump:
    ``gap_is_within_session`` (built on ``session_windows``, the same
    authority as ``gap_is_non_trading``) decides. A gap that is
    non-trading time (overnight, weekend, holiday) or that crosses a session
    boundary contributes nothing, so those bars stay adjacent
    (AC-D21.4.1) — without this, a two-day load was padded across the whole
    weekend (824 placeholder slots for 80 bars).

    The result is strictly ascending and unique, which the library requires:
    a duplicate bar timestamp (two bars sharing one display-x) is nudged one
    second past its predecessor instead of being dropped. With no ``period``
    (no timeframe) no placeholder times are derivable, so the bare bar
    timestamps cross. ``indices`` is kept for the caller's parallel-array
    contract; the hole decision no longer derives from it.
    """
    rows = list(bars or [])
    positions = list(indices or [])
    times: list = []
    whitespace: list = []
    prev_ts = None
    try:
        step = int(period) if period else 0
    except (TypeError, ValueError):
        step = 0
    for bar, _position in zip(rows, positions):
        try:
            ts = int(bar.ts)
        except (AttributeError, TypeError, ValueError):
            continue
        if prev_ts is not None and step > 0 and gap_is_within_session(
                prev_ts, ts, ext_hours):
            hole = int(prev_ts) + step
            while hole < ts:
                times.append(hole)
                whitespace.append(True)
                hole += step
        if prev_ts is not None and ts <= prev_ts:
            ts = prev_ts + 1
        times.append(ts)
        whitespace.append(False)
        prev_ts = ts
    return times, whitespace


def format_tz_label(t, tz_offset) -> str:
    """Format a series time as a chart-local label.

    ``local = t - offset`` with a positive offset for zones behind UTC
    (18000 for EST, 14400 for EDT) — the same formula the default
    engine's axis uses. ``t`` is the bar's real UTC epoch time (Q-20), so
    the label names the bar's actual date.
    """
    dt = datetime.fromtimestamp(t - tz_offset, tz=timezone.utc)
    return dt.strftime("%m/%d %H:%M")


def bar_spacing_geometry(bar_spacing_px: float,
                         floor_px: float = FLOOR_PX) -> tuple:
    """Restate the no-overlap guarantee in ``barSpacing`` terms (DG94).

    With library inter-bar spacing ``S`` (px per bar) the rendered body
    is ``min(S, max(0.65 * S, floor))`` and the inter-bar gap is
    ``S - body``. Returns ``(body_px, gap_px)`` with:

    * ``gap >= 0`` always (bodies never overlap — the ESC-041 lesson,
      kept across the engine change);
    * ``gap > 0`` whenever the spacing allows it (``S > floor``);
      at or below the floor the body yields to the pitch (gap 0).
    """
    if bar_spacing_px <= 0:
        raise ValueError("bar_spacing_px must be positive")
    body = min(bar_spacing_px, max(BODY_FRACTION * bar_spacing_px, floor_px))
    return (body, bar_spacing_px - body)


# ── Study overlays (P6-06 / Phase 4) ──────────────────────────────────────────
# The numeric study set the shared model computes incrementally; the
# remaining study types (rth_gaps / vix_sd / ict) are overlay studies that
# render through their own overlay surfaces (P6-10) and are skipped here.

#: Numeric study kinds carried as value series on the LWC engine.
STUDY_KINDS = ("sma", "ema", "ema2", "vwap", "bollinger", "rsi", "macd")

#: Kinds that overlay the price pane (same scale as the candles).
PRICE_STUDIES = frozenset({"sma", "ema", "ema2", "vwap", "bollinger"})

#: Kinds that belong on their own oscillator pane.
OSCILLATOR_STUDIES = frozenset({"rsi", "macd"})

STUDY_PANE_PRICE = "price"
STUDY_PANE_OSCILLATOR = "oscillator"

#: One entry per rendered line, keyed by kind. The suffixes are exactly the
#: shared model's series suffixes (``study_key`` + suffix), so an overlay id
#: such as ``"bollinger:0_mid"`` names one model array without translation.
STUDY_LINES = {
    "sma": ("",),
    "ema": ("",),
    "ema2": ("",),
    "vwap": ("",),
    "bollinger": ("", "_mid", "_lower"),
    "rsi": ("",),
    "macd": ("", "_signal", "_hist"),
}

#: Line colours mirroring the default engine's study renderer.
STUDY_COLORS = {"rsi": "#818cf8", "macd": "#60a5fa"}
MACD_SIGNAL_COLOR = "#f59e0b"
STUDY_HIST_COLORS = {"up": "#34d399", "down": "#f87171"}
DEFAULT_STUDY_COLOR = "#ffffff"


def study_base_kind(overlay_id: str) -> str:
    """Base study kind of an overlay id.

    ``"sma:0"`` -> ``"sma"``; ``"bollinger:0_mid"`` -> ``"bollinger"``;
    ``"macd:1_hist"`` -> ``"macd"``. Longest match wins so ``ema2`` never
    degrades to ``ema``. Unknown heads are returned unchanged.
    """
    head = str(overlay_id or "").split(":", 1)[0]
    best = ""
    for kind in STUDY_KINDS:
        if (head == kind or head.startswith(kind + "_")) and len(kind) > len(best):
            best = kind
    return best or head


def study_pane(overlay_id: str) -> str:
    """Pane an overlay belongs on (``price`` or ``oscillator``)."""
    base = study_base_kind(overlay_id)
    return (STUDY_PANE_OSCILLATOR if base in OSCILLATOR_STUDIES
            else STUDY_PANE_PRICE)


def study_overlay_style(overlay_id: str, params: dict | None = None) -> dict:
    """Wire style for one overlay — a mirror of the default renderer's pens.

    JSON-safe primitives only (the engine receives no formatted strings and
    no objects). Colours match the default engine: a study's own ``color``
    param when set, the RSI indigo, the MACD blue/orange pair, the green/red
    histogram, and a dotted middle band on Bollinger.
    """
    base = study_base_kind(overlay_id)
    params = params or {}
    if base == "rsi":
        return {"type": "line", "color": STUDY_COLORS["rsi"],
                "width": 1.0, "lineStyle": "solid"}
    if base == "macd":
        if overlay_id.endswith("_hist"):
            return {"type": "histogram", "colorUp": STUDY_HIST_COLORS["up"],
                    "colorDown": STUDY_HIST_COLORS["down"]}
        color = (MACD_SIGNAL_COLOR if overlay_id.endswith("_signal")
                 else STUDY_COLORS["macd"])
        return {"type": "line", "color": color, "width": 1.0,
                "lineStyle": "solid"}
    return {
        "type": "line",
        "color": params.get("color") or DEFAULT_STUDY_COLOR,
        "width": 1.5 if base == "vwap" else 1.0,
        "lineStyle": "dotted" if overlay_id.endswith("_mid") else "solid",
    }


def study_op(overlay_id: str, ts: Sequence, values: Sequence,
             params: dict | None = None) -> dict:
    """One ``set_study`` op: the study channel's wire shape.

    ``cols.ts`` carries the series' real UTC times — the same column the
    candles op carries (Q-20), so the study lands on its bars. ``cols.value``
    carries one nullable price per bar — ``None`` is a period the study is
    not yet valid, which the engine renders as whitespace. Mirrored by
    ``chart_assets/lwc/studies.js``.
    """
    return {
        "op": "set_study",
        "series": "studies",
        "kind": overlay_id,
        "pane": study_pane(overlay_id),
        "style": study_overlay_style(overlay_id, params),
        "cols": {"ts": list(ts), "value": list(values)},
    }


def clear_study_op() -> dict:
    """Clear every study series on the engine (no cols — like ``clear``)."""
    return {"op": "clear_study", "series": "studies"}


# ── Phase 5 interaction: controls + router mirror (P6-07 / D47.7) ────────────
#
# The in-HTML control surface mirrors ``ui/chart_controls.py`` (zoom_out /
# zoom_in / magnify_toggled / reset). The buttons live in the page; the
# gesture precedence stays in exactly one place — the frozen
# ``ui.chart_mouse_router`` router — and the shim below only routes the
# control into it. ``chart_assets/lwc/interaction.js`` carries the JS mirror
# of both halves: the control list (same ids, labels, tooltips) and
# ``ROUTER_TRANSITIONS`` (the frozen TR-1…TR-17 table), which the mirror
# resolves with the same precedence and never reinterprets.

#: The ``RouterMode`` members, in the router's declaration order.
ROUTER_MODES = ("IDLE", "DRAWING", "ZOOMING", "ALARM_PLACING")

#: Router intent triggers — the router's own transition helpers.
ROUTER_TRIGGERS = (
    "draw_tool",
    "draw_cursor",
    "enter_zoom",
    "enter_alarm_placing",
    "exit_to_idle",
    "symbol_change",
)

#: Gesture triggers — the guard-clause dispatch rows.
ROUTER_GESTURES = ("press", "drag", "click")

#: Transcription of the frozen TR-1…TR-17 table (``chart_mouse_router.py``).
#: ``from`` is the mode the gesture starts in, ``to`` the mode it ends in;
#: ``refused`` marks the one row the router declines without touching any
#: overlay (TR-9, alarm placement refuses the magnifier). TR-13…TR-16 are
#: dispatch rows — the mode is unchanged and the interesting result is which
#: overlay receives the gesture. ``chart_assets/lwc/interaction.js`` holds
#: the mirror of this list, row for row; the mirror suites prove both.
ROUTER_TRANSITIONS = (
    {"id": "TR-1", "from": "IDLE", "trigger": "draw_tool", "to": "DRAWING"},
    {"id": "TR-2", "from": "IDLE", "trigger": "enter_zoom", "to": "ZOOMING"},
    {"id": "TR-3", "from": "IDLE", "trigger": "enter_alarm_placing",
     "to": "ALARM_PLACING"},
    {"id": "TR-4", "from": "DRAWING", "trigger": "enter_zoom", "to": "ZOOMING"},
    {"id": "TR-5", "from": "ZOOMING", "trigger": "draw_tool", "to": "DRAWING"},
    {"id": "TR-6", "from": "ZOOMING", "trigger": "enter_alarm_placing",
     "to": "ALARM_PLACING"},
    {"id": "TR-7", "from": "DRAWING", "trigger": "enter_alarm_placing",
     "to": "ALARM_PLACING"},
    {"id": "TR-8", "from": "ALARM_PLACING", "trigger": "draw_tool",
     "to": "DRAWING"},
    {"id": "TR-9", "from": "ALARM_PLACING", "trigger": "enter_zoom",
     "to": "ALARM_PLACING", "refused": True},
    {"id": "TR-10", "from": "DRAWING", "trigger": "draw_cursor", "to": "IDLE"},
    {"id": "TR-11", "from": "ZOOMING", "trigger": "exit_to_idle", "to": "IDLE"},
    {"id": "TR-12", "from": "ALARM_PLACING", "trigger": "exit_to_idle",
     "to": "IDLE"},
    {"id": "TR-13", "from": "IDLE", "trigger": "press", "to": "IDLE"},
    {"id": "TR-14", "from": "IDLE", "trigger": "drag", "to": "IDLE"},
    {"id": "TR-15", "from": "IDLE", "trigger": "click", "to": "IDLE"},
    {"id": "TR-16", "from": "DRAWING", "trigger": "click", "to": "DRAWING"},
    {"id": "TR-17", "from": "DRAWING", "trigger": "symbol_change", "to": "IDLE"},
)

#: The in-HTML control ids, in the mirror of ``ChartControls``' button order.
CONTROL_IDS = ("zoom-out", "zoom-in", "magnifier", "reset")

#: Magnifier / zoom multipliers — the same numbers the page's keyboard
#: handler uses (``chart.js::zoom``), mirrored by ``interaction.js``.
ZOOM_FACTORS = {"in": 0.8, "out": 1.25}

#: Library-native crosshair (Q63 / A108 accept-drift): the library's own
#: crosshair with both axis labels visible. No custom primitive — the
#: D2/Q33 lane stops at the engine boundary.
CROSSHAIR_MODE_NAME = "normal"
CROSSHAIR_MODE_ID = 0


def reset_router_for_symbol_change(router) -> "RouterMode":
    """TR-17: a symbol change mid-gesture resets the router to ``IDLE``.

    The draft is discarded (tool back to ``TOOL_CURSOR``) and the magnifier
    is deactivated, so a stale drag from the previous symbol can never land
    on the new series. Public router API only — the frozen module is not
    modified by this wave.
    """
    router.exit_to_idle()
    router.enter_drawing(TOOL_CURSOR)
    return router.active_mode


# ── Phase 6 alarms: lines/overlays (P6-08 / D47.5) ──────────────────────────
#
# The renderer-only mirror of ``ui/alarm_overlay.py``: the same colour
# precedence, glyph table, label composition, pen width, z-order and the
# D21.10 preview line of ``ui/chart_panel.py``. Only the *state* crosses —
# the engine composes the label text, exactly as it composes study labels.
# The colours below are the reference constants; the parity suite asserts
# they equal ``ui/alarm_overlay``'s own constants rather than trusting this
# comment.

#: Alarm channel id (its own envelope; the bar transport stays pinned).
ALARM_CHANNEL = "alarms"

#: Colour per alarm state — the reference ``AlarmOverlay._color_for`` order:
#: triggered -> inactive (off) -> muted -> armed.
ALARM_TRIGGERED_COLOR = "#f87171"
ALARM_ARMED_COLOR = "#fbbf24"
ALARM_MUTED_COLOR = "#94a3b8"
ALARM_INACTIVE_COLOR = "#64748b"

#: D21.10 preview line: yellow, dashed, 1.4 px, below the alarm lines.
ALARM_PREVIEW_COLOR = "#ffff00"

#: Pen width and z-order of the reference alarm items / preview line.
ALARM_LINE_WIDTH = 1.4
ALARM_LINE_Z = 6
ALARM_LABEL_Z = 7
ALARM_PREVIEW_Z = 5

#: Direction glyphs — the reference ``DIRECTION_GLYPH`` table.
ALARM_DIRECTION_GLYPH = {
    "cross_above": "\u25b2",
    "cross_below": "\u25bc",
    "cross_either": "\u25c6",
}

#: The alarm envelope's column set (one column array per attribute).
ALARM_COLS = ("id", "price", "direction", "active", "triggered", "sound",
              "note")

#: The state columns (booleans) — the rest are numbers / display strings.
ALARM_BOOL_COLS = ("active", "triggered", "sound")


def alarm_visible(alarm) -> bool:
    """Whether an alarm draws a chart line on either engine.

    Mirrors ``AlarmOverlay``: only ``kind == "price"`` alarms have a price
    level (D39), and an alarm without an id has no line yet.
    """
    return (getattr(alarm, "kind", "price") == "price"
            and getattr(alarm, "id", None) is not None)


def alarm_color(alarm) -> str:
    """Colour for one alarm — the reference ``AlarmOverlay._color_for``."""
    if getattr(alarm, "triggered", False):
        return ALARM_TRIGGERED_COLOR
    if not getattr(alarm, "active", True):
        return ALARM_INACTIVE_COLOR
    if not getattr(alarm, "sound", True):
        return ALARM_MUTED_COLOR
    return ALARM_ARMED_COLOR


def alarm_label(alarm) -> str:
    """Label text for one alarm — the reference ``AlarmOverlay._label_text``.

    Composed here only as the parity reference and for the wave record; the
    wire carries the raw state and ``chart_assets/lwc/alarms.js`` composes
    the same string engine-side (no formatted string crosses).
    """
    glyph = ALARM_DIRECTION_GLYPH.get(getattr(alarm, "direction", ""), "")
    text = f"{glyph} {alarm.price:.4f}"
    if getattr(alarm, "triggered", False):
        text += " (hit)"
    elif not getattr(alarm, "active", True):
        text += " (off)"
    elif not getattr(alarm, "sound", True):
        text += " (muted)"
    note = getattr(alarm, "note", "")
    if note:
        text += f" \u00b7 {note}"
    return text


def alarm_columns(alarms: Sequence) -> dict:
    """The ``set_alarms`` column arrays for the visible alarms, in order."""
    rows = [alarm for alarm in (alarms or []) if alarm_visible(alarm)]
    return {
        "id": [int(alarm.id) for alarm in rows],
        "price": [float(alarm.price) for alarm in rows],
        "direction": [str(getattr(alarm, "direction", "")) for alarm in rows],
        "active": [bool(getattr(alarm, "active", True)) for alarm in rows],
        "triggered": [bool(getattr(alarm, "triggered", False))
                      for alarm in rows],
        "sound": [bool(getattr(alarm, "sound", True)) for alarm in rows],
        "note": [str(getattr(alarm, "note", "") or "") for alarm in rows],
    }


def alarm_op(alarms: Sequence) -> dict:
    """Replace-all ``set_alarms`` op (replay idempotent, like ``set_bars``)."""
    return {"op": "set_alarms", "series": ALARM_CHANNEL,
            "cols": alarm_columns(alarms)}


def clear_alarms_op() -> dict:
    """Remove every alarm line on the engine."""
    return {"op": "clear_alarms", "series": ALARM_CHANNEL}


def alarm_preview_op(price: float) -> dict:
    """The D21.10 preview line at ``price`` (yellow, dashed, below alarms)."""
    return {"op": "set_alarm_preview", "series": ALARM_CHANNEL,
            "price": float(price)}


def clear_alarm_preview_op() -> dict:
    """Remove the D21.10 preview line (AC-D21.10.4)."""
    return {"op": "clear_alarm_preview", "series": ALARM_CHANNEL}


# ── Phase 7 drawings: ts-to-fractional-index primitives (P6-09 / DG93) ──────
#
# The renderer-only mirror of ``ui/drawing_overlay.py``. Every drawing keeps
# its persisted ts/price payload; this module maps each anchor timestamp to a
# **fractional logical index** — the LWC time axis' own unit — and publishes
# validated geometry. The default engine's x-model is display-x (the collapse map's
# output); the fractional index is that same axis expressed in the candles'
# time unit, so ``display_from_fractional_index`` round-trips to the
# reference overlay's ``_ts_to_x`` exactly (the parity suite asserts it on
# the DG93 edge fixtures: DST folds, session-boundary bars and display-x
# collisions). JS never interprets a timestamp: it receives fractional
# indices and prices only, and composes its labels from those numbers.
#
# The payload contract is the service's own: every payload is normalised by
# ``services.drawing_service.normalize_payload`` before it crosses, so JS
# receives validated keys only. Fibonacci levels and the measure delta are
# computed here with ``services.drawing_service.fib_levels`` — the same
# pure geometry the reference overlay calls.

#: The drawing channel (its own envelope; the bar transport stays pinned).
DRAWING_CHANNEL = "drawings"

#: The z-value every reference drawing item ends up with. ``_build_items``
#: sets the per-kind z (-4 zone, -3 fib) first and then overrides every item
#: to 10 in its final loop; parity follows the shipped behaviour.
DRAWING_Z = 10

#: Zone fill alpha (``QColor.setAlpha(36)`` in the reference renderer).
DRAWING_ZONE_ALPHA = 36

#: Pen widths per kind — the reference ``pg.mkPen`` widths.
DRAWING_LINE_WIDTHS = {
    "trendline": 1.4,
    "horizontal": 1.2,
    "zone": 1.0,
    "fibonacci": 1.0,
    "measure": 1.4,
}

#: D11 inner-right labels: ``view_rect.right() - 4``, never stacked closer
#: than the measured bbox (a 15 px floor), matching ``_update_inner_labels``.
DRAWING_LABEL_INSET_PX = 4.0
DRAWING_LABEL_MIN_HEIGHT_PX = 15.0

#: Selection / handle primitives (the reference ``_refresh_handles`` values).
DRAWING_HANDLE_SIZE = 10
DRAWING_HANDLE_PEN = "#ffffff"
DRAWING_HANDLE_BRUSH = "#0ea5e9"
DRAWING_HANDLE_PEN_WIDTH = 1.5
DRAWING_SELECTED_COLOR = "#ffffff"
DRAWING_SELECTED_WIDTH = 2.0


def _interp(x, x1, y1, x2, y2) -> float:
    """Linear interpolation, degenerate-safe (``x2 == x1`` collapses)."""
    if x2 == x1:
        return float(y2)
    return float(y1 + (x - x1) * (y2 - y1) / (x2 - x1))


def _edge_pair(xs: Sequence, indices: Sequence, at_start: bool):
    """First (or last) non-degenerate ``(x, index)`` pair for extrapolation.

    A display-x collision at the edge of the series makes the adjacent pair
    degenerate; extrapolating off it would lose the anchor's identity. Use
    the nearest pair with a real slope instead, so an out-of-window anchor
    still round-trips to its own display-x.
    """
    n = len(xs)
    if at_start:
        base = xs[0]
        for j in range(1, n):
            if xs[j] != base:
                return float(base), float(indices[0]), float(xs[j]), float(indices[j])
    else:
        base = xs[-1]
        for j in range(n - 2, -1, -1):
            if xs[j] != base:
                return float(xs[j]), float(indices[j]), float(base), float(indices[-1])
    return None


def drawing_axis(plotted: Sequence, timeframe: str | None,
                 ext_hours: bool) -> tuple[list, list, object]:
    """``(display_xs, logical_indices, collapse_map)`` for the plotted rows.

    The same two arrays ``set_series`` builds for the candles, from the one
    collapse authority and the one step rule (``logical_indices_from_display``).
    The collapse map is returned with them because a drawing timestamp maps
    through ``to_display`` exactly as the reference overlay's ``_ts_to_x``
    does — including an out-of-window anchor, which the map clamps to the
    loaded range rather than extrapolating.
    """
    rows = list(plotted or [])
    cmap = chart_model.collapse_for_bars(rows, timeframe, ext_hours)
    xs = chart_model.display_xs(rows, cmap)
    period = TIMEFRAME_SECONDS.get(timeframe or "")
    if cmap is None or not period:
        return xs, list(range(len(rows))), cmap
    return xs, logical_indices_from_display(xs, period), cmap


def fractional_index_from_display(x, xs: Sequence, indices: Sequence) -> float:
    """Map a display-x coordinate onto the fractional logical index axis.

    The candles' logical indices are integers at the bar display-x values.
    Between two bars the index interpolates linearly, which is the same
    relative position the reference engine's linear x-axis renders. Before
    the first / after the last bar the edge slope extrapolates. A display-x
    collision (two bars sharing one x — DG93) resolves to the later bar's
    index; the inverse then returns that same x for either.
    """
    xs = list(xs)
    idx = list(indices)
    n = len(xs)
    if n == 0:
        return 0.0
    if n == 1:
        return float(idx[0])
    xf = float(x)
    # A display-x collision resolves to the *last* index sharing that x,
    # consistently at the series edges and in the interior (the interior
    # path's bisect already lands on the run's last member).
    if xf == xs[0]:
        j = 0
        while j + 1 < n and xs[j + 1] == xs[0]:
            j += 1
        return float(idx[j])
    if xf == xs[-1]:
        return float(idx[-1])
    if xf <= xs[0]:
        pair = _edge_pair(xs, idx, True)
        if pair is None:
            return float(idx[0])
        return _interp(xf, *pair)
    if xf >= xs[-1]:
        pair = _edge_pair(xs, idx, False)
        if pair is None:
            return float(idx[-1])
        return _interp(xf, *pair)
    i = bisect.bisect_right(xs, xf) - 1
    i = max(0, min(i, n - 2))
    return _interp(xf, xs[i], idx[i], xs[i + 1], idx[i + 1])


def display_from_fractional_index(frac, xs: Sequence,
                                  indices: Sequence) -> float:
    """Inverse of :func:`fractional_index_from_display`.

    A bar's own index returns that bar's display-x exactly — including a
    timestamp collision, where either colliding index returns the shared x.
    This is the identity the parity suite asserts against the reference
    overlay's ``_ts_to_x``.
    """
    xs = list(xs)
    idx = list(indices)
    n = len(idx)
    if n == 0:
        return 0.0
    if n == 1:
        return float(xs[0])
    f = float(frac)
    if f <= idx[0]:
        pair = _edge_pair(xs, idx, True)
        if pair is None:
            return float(xs[0])
        x1, i1, x2, i2 = pair
        return _interp(f, i1, x1, i2, x2)
    if f >= idx[-1]:
        pair = _edge_pair(xs, idx, False)
        if pair is None:
            return float(xs[-1])
        x1, i1, x2, i2 = pair
        return _interp(f, i1, x1, i2, x2)
    i = bisect.bisect_right(idx, f) - 1
    i = max(0, min(i, n - 2))
    return _interp(f, idx[i], xs[i], idx[i + 1], xs[i + 1])


def ts_for_fractional_index(frac, plotted: Sequence, indices: Sequence,
                            period=None):
    """Inverse of the drawing axis for a page-originated anchor (Q-20).

    The page reports drawing anchors as fractional indices (its time axis'
    own unit). The drawing records, the store and the session fan-out are
    timestamp-keyed, so a page anchor is mapped back here: a bar's own index
    returns that bar's ``ts``, and an index between two bars adds whole
    ``period`` steps to the bar it starts from — the same relative position
    ``fractional_index_from_display`` produced. Out-of-range fractions clamp
    to the loaded range (the page cannot see outside it). ``None`` when the
    axis is empty.
    """
    rows = list(plotted or [])
    idx = list(indices or [])
    if not rows or not idx:
        return None
    try:
        f = float(frac)
    except (TypeError, ValueError):
        return None
    f = max(float(idx[0]), min(float(idx[-1]), f))
    i = bisect.bisect_right(idx, f) - 1
    i = max(0, min(i, len(idx) - 1))
    try:
        base = int(rows[i].ts)
    except (AttributeError, TypeError, ValueError, IndexError):
        return None
    if not period:
        return base
    steps = int(round(f - float(idx[i])))
    return base + steps * int(period)


def _drawing_frac(xs: Sequence, indices: Sequence, ts, cmap=None) -> float:
    """A timestamp's fractional index: ``ts -> display-x -> fractional``."""
    if not xs:
        return 0.0
    # ``_ts_to_x`` on the reference engine: the collapse map's ``to_display``
    # (identity without a map). An out-of-window anchor clamps with the map.
    x = float(cmap.to_display(ts)) if cmap is not None else float(ts)
    return fractional_index_from_display(x, xs, indices)


def fractional_index_for_ts(ts, plotted: Sequence, timeframe: str | None,
                            ext_hours: bool) -> float:
    """Public one-shot mapping: a drawing timestamp's fractional index.

    The pair ``fractional_index_for_ts`` + ``display_from_fractional_index``
    is the whole contract the engine receives: a timestamp becomes one
    fractional logical index and the inverse recovers the reference
    overlay's display-x exactly.
    """
    xs, indices, cmap = drawing_axis(plotted, timeframe, ext_hours)
    return _drawing_frac(xs, indices, ts, cmap)


def drawing_handle_points(kind: str, item: dict) -> list:
    """Handle anchors in ``[frac_index, price]`` / ``[None, price]`` form.

    Mirrors ``DrawingOverlay._handle_points``: a zone's two corner handles are
    its normalised ``(x1, y1)`` / ``(x2, y2)`` pair; a horizontal line has one
    price handle at the pane's left edge (``None`` x); the two-point kinds use
    their endpoints.
    """
    if kind in ("trendline", "measure", "fibonacci"):
        return [[float(p[0]), float(p[1])] for p in item.get("points", [])]
    if kind == "horizontal":
        return [[None, float(item["price"])]]
    if kind == "zone":
        return [[item["span"][0], float(item["y1"])],
                [item["span"][1], float(item["y2"])]]
    return []


def drawing_item(drawing, xs: Sequence, indices: Sequence,
                 group=None, selected: bool = False, cmap=None) -> dict:
    """One validated wire item for a ``Drawing`` (geometry in frac/price).

    Raises ``ValueError`` for an unknown kind or a malformed payload, exactly
    as ``DrawingOverlay._build_items`` swallows those rows. The wire carries
    numbers only: colours, fractional indices, prices, fib ratios and the
    measure delta; the engine composes every label string.
    """
    kind = drawing.kind
    if kind not in DRAWING_KINDS:
        raise ValueError(f"Unknown drawing kind: {kind!r}")
    payload = normalize_payload(kind, getattr(drawing, "payload", {}) or {})
    color = str(getattr(drawing, "color", None) or DEFAULT_DRAWING_COLOR)
    item = {
        "id": (int(drawing.id) if getattr(drawing, "id", None) is not None
               else None),
        "kind": kind,
        "color": color,
        "group_id": (int(drawing.group_id)
                     if getattr(drawing, "group_id", None) is not None
                     else None),
        "locked": bool(group is not None and getattr(group, "locked", False)),
        "selected": bool(selected),
        "z": DRAWING_Z,
        "width": DRAWING_LINE_WIDTHS[kind],
    }
    if kind in ("trendline", "measure"):
        p1, p2 = payload["p1"], payload["p2"]
        item["points"] = [[_drawing_frac(xs, indices, p1["x"], cmap), p1["y"]],
                          [_drawing_frac(xs, indices, p2["x"], cmap), p2["y"]]]
        if kind == "measure":
            dy = p2["y"] - p1["y"]
            item["delta"] = {"dy": float(dy),
                             "pct": float(dy / p1["y"] * 100.0) if p1["y"] else 0.0}
    elif kind == "horizontal":
        item["price"] = float(payload["y"])
    elif kind == "zone":
        item["span"] = [_drawing_frac(xs, indices, payload["x1"], cmap),
                        _drawing_frac(xs, indices, payload["x2"], cmap)]
        item["y1"] = float(payload["y1"])
        item["y2"] = float(payload["y2"])
        item["fillAlpha"] = DRAWING_ZONE_ALPHA
    elif kind == "fibonacci":
        p1, p2 = payload["p1"], payload["p2"]
        item["type"] = payload["type"]
        item["points"] = [[_drawing_frac(xs, indices, p1["x"], cmap), p1["y"]],
                          [_drawing_frac(xs, indices, p2["x"], cmap), p2["y"]]]
        item["levels"] = [[float(ratio), float(price)] for ratio, price in
                          fib_levels(p1["y"], p2["y"], payload["type"])]
    item["handles"] = drawing_handle_points(kind, item)
    return item


def drawing_op(drawings: Sequence, groups: Sequence, xs: Sequence,
               indices: Sequence, selected_id=None, cmap=None) -> dict:
    """Replace-all ``set_drawings`` op for the visible, valid drawings.

    Group visibility mirrors ``DrawingOverlay._is_visible_group`` (a drawing
    outside any group is visible; a group with ``visible=False`` hides its
    members). A drawing in a locked group renders ``locked`` so the engine
    never starts a drag. Replace-all keeps replay idempotent, like alarms.
    """
    gmap = {getattr(g, "id", None): g for g in (groups or [])
            if getattr(g, "id", None) is not None}
    items: list = []
    for drawing in (drawings or []):
        kind = getattr(drawing, "kind", None)
        if kind not in DRAWING_KINDS:
            continue
        group = gmap.get(getattr(drawing, "group_id", None))
        if group is not None and not getattr(group, "visible", True):
            continue
        try:
            items.append(drawing_item(
                drawing, xs, indices, group=group,
                selected=(selected_id is not None
                          and getattr(drawing, "id", None) == selected_id),
                cmap=cmap))
        except ValueError:
            continue
    return {"op": "set_drawings", "series": DRAWING_CHANNEL, "items": items}


def clear_drawings_op() -> dict:
    """Remove every drawing primitive on the engine."""
    return {"op": "clear_drawings", "series": DRAWING_CHANNEL}


def drawing_primitive_op(kind: str, frac_index_pts: Sequence) -> dict:
    """The ``set_drawing_primitive`` op — validated fractional-index points.

    ``frac_index_pts`` is a list of ``[frac_index, price]`` pairs. The kind
    selects the primitive geometry (a horizontal line reads the first point's
    price; a zone reads two y values; the rest are two-point primitives).
    Every value must be a finite number, so the engine receives validated
    payloads only.
    """
    if kind not in DRAWING_KINDS:
        raise ValueError(f"Unknown drawing kind: {kind!r}")
    points = []
    for point in (frac_index_pts or []):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"point must be [frac_index, price]: {point!r}")
        frac, price = point
        if isinstance(frac, bool) or not isinstance(frac, (int, float)):
            raise ValueError(f"frac_index must be a number: {frac!r}")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError(f"price must be a number: {price!r}")
        points.append([float(frac), float(price)])
    if not points:
        raise ValueError("frac_index_pts must carry at least one point")
    if kind == "horizontal":
        points = points[:1]
    elif len(points) != 2:
        raise ValueError(f"{kind} requires exactly two points")
    return {"op": "set_drawing_primitive", "series": DRAWING_CHANNEL,
            "kind": kind, "points": points}


def drag_drawing_item(kind: str, item: dict, point_index: int,
                      d_frac: float, d_price: float,
                      body: bool = False) -> dict:
    """Apply one drag delta to a wire item — the reference ``_apply_drag``.

    Endpoint drags move the addressed point (``point_index`` 0/1); a body
    drag translates the whole primitive. Both-point kinds translate both
    anchors by ``(d_frac, d_price)``; a horizontal line follows the pointer's
    price; a zone moves its bounds and re-normalises, exactly as
    ``normalize_payload`` does after the reference drag. Returns a new item
    (the input is not mutated) with Fibonacci levels / the measure delta
    recomputed from the new geometry.
    """
    if kind not in DRAWING_KINDS:
        raise ValueError(f"Unknown drawing kind: {kind!r}")
    item = dict(item)
    d_price = float(d_price)
    if kind in ("trendline", "measure", "fibonacci"):
        points = [list(point) for point in (item.get("points") or [])]
        if len(points) != 2:
            raise ValueError("item is missing its two points")
        if body:
            for point in points:
                point[0] += float(d_frac)
                point[1] += d_price
        else:
            index = 0 if point_index == 0 else 1
            points[index][0] += float(d_frac)
            points[index][1] += d_price
        item["points"] = points
        if kind == "fibonacci":
            item["levels"] = [[float(ratio), float(price)] for ratio, price in
                              fib_levels(points[0][1], points[1][1],
                                         item.get("type", "retr"))]
        elif kind == "measure":
            dy = points[1][1] - points[0][1]
            item["delta"] = {
                "dy": float(dy),
                "pct": float(dy / points[0][1] * 100.0)
                if points[0][1] else 0.0,
            }
    elif kind == "horizontal":
        item["price"] = float(item["price"]) + d_price
    elif kind == "zone":
        y1 = float(item["y1"])
        y2 = float(item["y2"])
        if body:
            y1 += d_price
            y2 += d_price
        elif point_index == 0:
            y1 += d_price
        else:
            y2 += d_price
        item["y1"], item["y2"] = min(y1, y2), max(y1, y2)
    item["handles"] = drawing_handle_points(kind, item)
    return item


# ── Phase 8 overlays (P6-10 / D47.5) ───────────────────────────────────────
#
# The renderer-only mirror of the four overlay surfaces. Every value below
# comes from the **unchanged** services the default engine itself calls —
# ``session_bands``, ``calculate_rth_gaps``,
# ``calculate_vix_standard_deviation``, ``calculate_ict_concepts`` — mapped
# through the one display-x axis (``drawing_axis``) into the candles'
# fractional logical index. No service signature, no store, no ``ibkr`` module
# and no order surface is touched: the same inputs render the same visuals on
# both engines, and JS receives fractional indices and prices only — it
# composes glyphs and labels itself.
#
# The reference constants below are the shipped renderers' own values
# (``ui/overlays/{session,gap,vix,ict}_overlay.py``); the parity suite asserts
# equality against those modules rather than trusting this comment.

#: The overlay channel (its own envelope; the bar transport stays pinned).
OVERLAY_CHANNEL = "overlays"

#: The overlay names this driver publishes.
OVERLAY_NAMES = ("session", "rth_gaps", "vix_sd", "ict")

#: ``SessionOverlay``: orange pre-market, blue post-market, 10 % alpha, z -10.
SESSION_COLORS = {"pre": "#f59e0b", "post": "#60a5fa"}
SESSION_POST_COLOR = SESSION_COLORS["post"]
SESSION_ALPHA = 0.10
SESSION_Z = -10

#: ``RthGapOverlay``: green up / red down, a darker brush per direction, the
#: 0.55/0.32 alpha pair (open / fully filled), 0.8 px border, z -5.
GAP_UP_COLOR = "#089981"
GAP_UP_BRUSH = "#064e3b"
GAP_DOWN_COLOR = "#f23645"
GAP_DOWN_BRUSH = "#7f1d1d"
GAP_OPEN_ALPHA = 0.55
GAP_FILLED_ALPHA = 0.32
GAP_BORDER_WIDTH = 0.8
GAP_Z = -5

#: ``VixOverlay``: the reference pen width default, the right-edge label
#: anchor, and the item z (``add_hline`` adds without a z override).
VIX_LABEL_ANCHOR = "right"
VIX_Z = 0.0

#: ``ICTStudyOverlay`` geometry: per-concept alpha / z / width. The values are
#: the shipped ``add_band`` / ``add_segment`` / ``add`` arguments.
ICT_TRAILING_BARS = 500
ICT_STRUCTURE_WIDTH = 1.2
ICT_STRUCTURE_STYLE = "dashed"
ICT_STRUCTURE_Z = 3
ICT_ORDER_BLOCK_ALPHA = 0.18
ICT_ORDER_BLOCK_Z = -3
ICT_FVG_ALPHA = 0.14
ICT_FVG_MITIGATED_ALPHA = 0.06
ICT_FVG_Z = -4
ICT_POOL_ALPHA = 0.07
ICT_POOL_Z = -6
ICT_POOL_SEGMENT_WIDTH = 1.0
ICT_POOL_SEGMENT_Z = -2
ICT_VOLUME_IMBALANCE_COLOR = "#e879f9"
ICT_VOLUME_IMBALANCE_ALPHA = 0.35
ICT_VOLUME_IMBALANCE_Z = -4
ICT_OPENING_GAP_ALPHA = 0.10
ICT_OPENING_GAP_Z = -5
ICT_OPENING_GAP_MID_WIDTH = 1.0
ICT_OPENING_GAP_MID_Z = -2
ICT_DISPLACEMENT_COLORS = {"up": "#34d399", "down": "#f87171"}
ICT_DISPLACEMENT_SIZE = 10
ICT_DISPLACEMENT_Z = 4
ICT_KILLZONE_Z = -8

def overlay_op(name: str, regions: Sequence) -> dict:
    """One ``set_overlay`` op: a named overlay's regions, replace-all."""
    return {"op": "set_overlay", "series": OVERLAY_CHANNEL, "name": name,
            "regions": [dict(region) for region in (regions or [])]}


def clear_overlay_op(name: str) -> dict:
    """Remove one overlay's primitives from the engine."""
    return {"op": "clear_overlay", "series": OVERLAY_CHANNEL, "name": name}


def session_regions(bars: Sequence, plotted: Sequence, timeframe: str | None,
                    ext_hours: bool) -> list:
    """Session pre/post bands as engine regions (fractional indices).

    Mirrors ``ChartPanel._render_sessions``: nothing without extended hours,
    nothing for daily-and-coarser timeframes (S-P8-4), nothing for an empty
    load; the bands themselves
    come from the unchanged ``session_bands`` and are mapped through the same
    display-x axis the candles use (``AC-D21.4.3``), so a band lands on the
    session actually shown and never covers a collapsed gap. A band whose
    mapped end does not exceed its start draws nothing (the reference
    ``SessionOverlay`` skips it).
    """
    if not ext_hours or not bars or is_daily_or_coarser(timeframe):
        return []
    xs, indices, cmap = drawing_axis(plotted, timeframe, ext_hours)
    regions: list = []
    for band in session_bands(bars, timeframe or ""):
        kind = band.get("kind")
        start = _drawing_frac(xs, indices, band["start_ts"], cmap)
        end = _drawing_frac(xs, indices, band["end_ts"], cmap)
        if end <= start:
            continue
        regions.append({
            "shape": "region", "kind": kind, "from": start, "to": end,
            "color": SESSION_COLORS.get(kind, SESSION_POST_COLOR),
            "alpha": SESSION_ALPHA, "z": SESSION_Z,
        })
    return regions


def gap_regions(gaps: Sequence, bars: Sequence, plotted: Sequence,
                timeframe: str | None, ext_hours: bool) -> list:
    """RTH gap staircase steps as engine bands.

    Mirrors ``RthGapOverlay.render``: one band per gap *step*, its x range
    from the step's bar-index window mapped to display-x and then to the
    fractional index axis, its brush the reference dark green/red at the
    0.55 (open) / 0.32 (fully filled) alpha, its border dotted once the gap is
    filled. A step whose top is not above its bottom draws nothing, and the
    range clamps to the last bar exactly as ``_index_to_x`` does.
    """
    rows = list(bars or [])
    if not rows:
        return []
    xs, indices, cmap = drawing_axis(plotted, timeframe, ext_hours)
    last = len(rows) - 1

    def _bar_frac(index) -> float | None:
        try:
            i = int(index)
        except (TypeError, ValueError):
            return None
        i = min(max(i, 0), last)
        return _drawing_frac(xs, indices, rows[i].ts, cmap)

    regions: list = []
    for gap in gaps or []:
        is_up = bool(gap.get("isUp"))
        filled = bool(gap.get("isFullyFilled"))
        for step in gap.get("steps") or []:
            bottom = step.get("bottom", gap.get("currentBottom",
                                                gap.get("initialBottom")))
            top = step.get("top", gap.get("currentTop", gap.get("initialTop")))
            x1 = _bar_frac(step.get("startBarIndex",
                                    gap.get("startBarIndex", 0)))
            x2 = _bar_frac(min(step.get("endBarIndex", last), last))
            if x1 is None or x2 is None or top is None or bottom is None:
                continue
            if float(top) <= float(bottom) or x2 <= x1:
                continue
            regions.append({
                "shape": "band", "kind": "gap", "id": str(gap.get("id", "")),
                "isUp": is_up, "filled": filled,
                "from": x1, "to": x2,
                "bottom": float(bottom), "top": float(top),
                "color": GAP_UP_COLOR if is_up else GAP_DOWN_COLOR,
                "brush": GAP_UP_BRUSH if is_up else GAP_DOWN_BRUSH,
                "alpha": GAP_FILLED_ALPHA if filled else GAP_OPEN_ALPHA,
                "borderWidth": GAP_BORDER_WIDTH,
                "borderStyle": "dotted" if filled else "solid",
                "z": GAP_Z,
            })
    return regions


def vix_label(sigma, price) -> str:
    """Label text for one sigma level — the reference ``VixOverlay`` format.

    ``0σ 4321.50`` for the anchor, ``+1σ 4340.12`` / ``-2σ 4260.00`` for a
    sigma pair. Composed engine-side from these two numbers; this function is
    the parity reference the wave records.
    """
    if sigma == 0:
        return f"0\u03c3 {float(price):.2f}"
    return f"{sigma:+.2g}\u03c3 {float(price):.2f}"


def vix_levels(result, plotted: Sequence, timeframe: str | None,
               ext_hours: bool) -> list:
    """VIX sigma lines with right-edge labels (the reference ``add_hline``).

    One horizontal line per level from the unchanged
    ``calculate_vix_standard_deviation`` result: its price, colour, line style
    and width cross unchanged; the label sits at the last bar's display-x
    (``_index_to_x(bar_count - 1)``), right-anchored.
    """
    levels = (result or {}).get("levels") if isinstance(result, dict) else None
    levels = list(levels or [])
    if not levels:
        return []
    _xs, indices, _cmap = drawing_axis(plotted, timeframe, ext_hours)
    label_from = float(indices[-1]) if indices else 0.0
    rows: list = []
    for level in levels:
        sigma = level.get("sigma", 0)
        rows.append({
            "shape": "hline", "kind": "vix",
            "sigma": sigma,
            "price": float(level["price"]),
            "color": str(level.get("color", "#94a3b8")),
            "lineStyle": str(level.get("lineStyle", "solid")),
            "width": float(level.get("lineWidth", 1)),
            "z": VIX_Z,
            "labelAnchor": VIX_LABEL_ANCHOR,
            "labelFrom": label_from,
        })
    return rows


def ict_regions(result, window: Sequence, plotted: Sequence,
                timeframe: str | None, ext_hours: bool) -> list:
    """ICT concepts as engine regions, in the reference draw order.

    Mirrors ``ICTStudyOverlay.render`` one concept at a time — market
    structures (dashed 1.2 px segments at z 3), order blocks (alpha 0.18, z
    -3, breaker colour), fair value gaps (alpha 0.14 / 0.06 mitigated, dotted
    once broken, z -4), liquidity pools (alpha 0.07, z -6, plus their level
    segment at z -2), volume imbalances (±1 bar window in *index* space, alpha
    0.35, z -4), opening gaps (alpha 0.10, z -5, dotted midpoint at z -2),
    displacements (scatter points, z 4) and killzones (vertical regions, z
    -8). ``window`` is the trailing bar list the concepts were computed over,
    so its indices map through the same display-x authority as the candles.
    """
    rows = list(window or [])
    if not rows:
        return []
    xs, indices, cmap = drawing_axis(plotted, timeframe, ext_hours)
    last_index = len(rows) - 1

    def _x(index) -> float | None:
        try:
            i = int(index)
        except (TypeError, ValueError):
            return None
        i = min(max(i, 0), last_index)
        return _drawing_frac(xs, indices, rows[i].ts, cmap)

    out: list = []
    last = _x(last_index)
    for structure in (result or {}).get("marketStructures", []) or []:
        x1, x2 = _x(structure["startIndex"]), _x(structure["endIndex"])
        if x1 is None or x2 is None:
            continue
        out.append({
            "shape": "segment", "kind": "structure", "from": x1, "to": x2,
            "price": float(structure["price"]),
            "color": str(structure["color"]),
            "lineStyle": ICT_STRUCTURE_STYLE, "width": ICT_STRUCTURE_WIDTH,
            "label": str(structure.get("type", "")), "z": ICT_STRUCTURE_Z,
        })
    for block in (result or {}).get("orderBlocks", []) or []:
        x1 = _x(block["barIndex"])
        if x1 is None or last is None:
            continue
        color = (block.get("breakColor") if block.get("isBreaker")
                 else block["color"])
        out.append({
            "shape": "band", "kind": "order_block", "from": x1, "to": last,
            "bottom": float(block["bottom"]), "top": float(block["top"]),
            "color": str(color), "alpha": ICT_ORDER_BLOCK_ALPHA,
            "z": ICT_ORDER_BLOCK_Z,
        })
    for fvg in (result or {}).get("fairValueGaps", []) or []:
        x1, x2 = _x(fvg["startIndex"]), _x(fvg["endIndex"])
        if x1 is None or x2 is None:
            continue
        out.append({
            "shape": "band", "kind": "fvg", "from": x1, "to": x2,
            "bottom": float(fvg["bottom"]), "top": float(fvg["top"]),
            "color": str(fvg["color"]),
            "alpha": (ICT_FVG_MITIGATED_ALPHA if fvg.get("isMitigated")
                      else ICT_FVG_ALPHA),
            "borderStyle": "dotted" if fvg.get("isBroken") else "solid",
            "z": ICT_FVG_Z,
        })
    for pool in (result or {}).get("liquidityPools", []) or []:
        x1 = _x(pool["startIndex"])
        if x1 is None or last is None:
            continue
        color = str(pool["color"])
        out.append({
            "shape": "band", "kind": "pool", "from": x1, "to": last,
            "bottom": float(pool["bottom"]), "top": float(pool["top"]),
            "color": color, "alpha": ICT_POOL_ALPHA, "z": ICT_POOL_Z,
        })
        out.append({
            "shape": "segment", "kind": "pool_level", "from": x1, "to": last,
            "price": float(pool["levelPrice"]), "color": color,
            "lineStyle": "dotted" if pool.get("isSwept") else "dashed",
            "width": ICT_POOL_SEGMENT_WIDTH,
            "label": str(pool.get("type", "")), "z": ICT_POOL_SEGMENT_Z,
        })
    for imbalance in (result or {}).get("volumeImbalances", []) or []:
        try:
            raw = int(imbalance["barIndex"])
        except (TypeError, ValueError, KeyError):
            raw = 0
        x1, x2 = _x(max(raw - 1, 0)), _x(raw + 1)
        if x1 is None or x2 is None:
            continue
        if x1 > x2:
            x1, x2 = x2, x1
        out.append({
            "shape": "band", "kind": "volume_imbalance", "from": x1, "to": x2,
            "bottom": float(imbalance["bottom"]),
            "top": float(imbalance["top"]),
            "color": str(imbalance.get("color") or ICT_VOLUME_IMBALANCE_COLOR),
            "alpha": ICT_VOLUME_IMBALANCE_ALPHA,
            "z": ICT_VOLUME_IMBALANCE_Z,
        })
    for gap in (result or {}).get("openingGaps", []) or []:
        x1 = _x(gap["startIndex"])
        if x1 is None or last is None:
            continue
        color = str(gap["color"])
        out.append({
            "shape": "band", "kind": "opening_gap", "from": x1, "to": last,
            "bottom": float(gap["bottom"]), "top": float(gap["top"]),
            "color": color, "alpha": ICT_OPENING_GAP_ALPHA,
            "z": ICT_OPENING_GAP_Z,
        })
        out.append({
            "shape": "segment", "kind": "opening_gap_mid", "from": x1,
            "to": last, "price": float(gap["midpoint"]), "color": color,
            "lineStyle": "dotted", "width": ICT_OPENING_GAP_MID_WIDTH,
            "z": ICT_OPENING_GAP_MID_Z,
        })
    for item in (result or {}).get("displacements", []) or []:
        x = _x(item["barIndex"])
        if x is None:
            continue
        up = item.get("direction") in ("up", "bullish")
        out.append({
            "shape": "point", "kind": "displacement", "from": x, "to": x,
            "price": float(item["price"]),
            "color": str(item.get("color") or
                         ICT_DISPLACEMENT_COLORS["up" if up else "down"]),
            "direction": "up" if up else "down",
            "size": ICT_DISPLACEMENT_SIZE, "z": ICT_DISPLACEMENT_Z,
        })
    for zone in (result or {}).get("killzones", []) or []:
        x1, x2 = _x(zone["startIndex"]), _x(zone["endIndex"])
        if x1 is None or x2 is None:
            continue
        out.append({
            "shape": "region", "kind": "killzone", "from": x1, "to": x2,
            "color": str(zone["color"]), "z": ICT_KILLZONE_Z,
        })
    return out


def series_ops(mode: str, bars: Sequence, timeframe: str | None,
               ext_hours: bool) -> list:
    """Build the ``set_bars`` / ``set_volume`` ops for one full series.

    ``rows`` are the loaded bars (any mode); RTH filtering, the
    collapse map and the Heikin-Ashi transform (``heikin`` mode) are
    applied here so the payload carries real UTC times (Q-20) and the JS
    side renders values without trading logic. The candles op carries
    the optional ``mode`` key the P6-04 validators accept; volume
    colours are derived JS-side from the candle snapshot.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode!r}")
    rows = list(bars or [])
    plotted = [rows[i] for i in
               chart_model.plotted_index_rows(rows, timeframe, ext_hours)]
    cmap = chart_model.collapse_for_bars(plotted, timeframe, ext_hours)
    period = TIMEFRAME_SECONDS.get(timeframe or "")
    if cmap is None or not period:
        indices = list(range(len(plotted)))
    else:
        indices = logical_indices_from_display(
            chart_model.display_xs(plotted, cmap), period)
    return build_series_ops(mode, plotted, cmap, indices, period)


def build_series_ops(mode: str, plotted: Sequence, cmap, indices: Sequence,
                     period=None) -> list:
    """Column ops for already-filtered rows, their collapse map and indices.

    Shared by the public :func:`series_ops` wrapper and the live driver
    (which derives the same three arrays once per full replace), so the
    full-history ``ts`` column and the live ``update_bar`` ``ts`` are in
    one domain: the bar's real UTC epoch seconds (Q-20).

    The ``indices`` stay the logical axis internal to this engine —
    ``series_times`` accepts them for its parallel-array contract, but a
    within-session hole's whitespace placeholders are decided by the
    non-trading authority (``gap_is_within_session``), never by an index
    jump. Those placeholders cross as ``None`` value slots (the page renders
    ``{time}`` only), so a hole keeps its empty slots (AC-D21.4.4) while a
    non-trading or between-session gap stays adjacent (AC-D21.4.1).
    """
    times, whitespace = series_times(
        plotted, indices, period, getattr(cmap, "ext_hours", True))
    candle_rows = [(idx, o, h, lo, c) for idx, (_t, o, h, lo, c) in
                   zip(indices, chart_model.candle_display_rows(plotted, cmap))]
    if mode == "heikin" and candle_rows:
        candle_rows = chart_model.heikin_ashi(candle_rows)
    _vol_x, vol_h, _colors = chart_model.volume_display_columns(plotted, cmap)
    ts_col: list = []
    open_col: list = []
    high_col: list = []
    low_col: list = []
    close_col: list = []
    volume_col: list = []
    row = 0
    for t, hole in zip(times, whitespace):
        ts_col.append(t)
        if hole:
            open_col.append(None)
            high_col.append(None)
            low_col.append(None)
            close_col.append(None)
            volume_col.append(None)
            continue
        if row < len(candle_rows):
            _idx, o, h, lo, c = candle_rows[row]
        else:  # pragma: no cover — times/rows are built in lock step
            o = h = lo = c = None
        open_col.append(o)
        high_col.append(h)
        low_col.append(lo)
        close_col.append(c)
        volume_col.append(float(vol_h[row]) if row < len(vol_h) else None)
        row += 1
    candles_op = {
        "op": "set_bars",
        "series": "candles",
        "cols": {
            "ts": ts_col,
            "open": open_col,
            "high": high_col,
            "low": low_col,
            "close": close_col,
        },
        "mode": mode,
    }
    # Q-9 / AC-D21.2.1: the raw volumes cross unchanged — the D21.2 ceiling
    # (1.10 x the visible max, the 100 floor, Y minimum 0) is a render-time
    # decision `chart_assets/lwc/chart.js` makes from this snapshot and the
    # visible logical range, so there is no ceiling on the wire and no
    # per-gesture round-trip back here.
    volume_op = {
        "op": "set_volume",
        "series": "volume",
        "cols": {"ts": list(ts_col), "value": volume_col},
    }
    return [candles_op, volume_op]


class PageDrawing:
    """A drawing committed in the page — ``Drawing``-shaped, renderer-local.

    ``MainWindow._on_drawing_created`` hands the emitted object straight to
    the drawing store, so it carries the attributes that path reads
    (``symbol`` / ``kind`` / ``payload`` / ``color`` / ``label`` /
    ``group_id`` / ``id``). It is a small transport record defined here rather than imported
    from ``data.models``: this module must stay free of the data layer
    (renderer boundary), and a page commit is not a stored row.
    """

    def __init__(self, symbol: str = "", kind: str = "", payload=None,
                 color=None, group_id=None, id=None, label: str = ""):
        self.symbol = symbol
        self.kind = kind
        self.payload = dict(payload or {})
        self.color = color
        self.group_id = group_id
        self.id = id
        # The store's create path reads ``drawing.label``; a page commit has no
        # label editor (the page is renderer-only), so the attribute exists and
        # stays empty until the Qt settings path sets one. Named without the
        # store's module symbol on purpose: the renderer boundary forbids it.
        self.label = label


def _optional_int(value):
    """``int(value)`` or ``None`` — booleans and junk never become ids."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value):
    """``float(value)`` or ``None`` — booleans and junk never become prices."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def page_geometry_payload(payload, plotted: Sequence, indices: Sequence,
                          period=None) -> dict:
    """Map one page drawing payload back onto bar timestamps (Q-20).

    ``payload`` is the page's own shape: ``points`` (``[[frac, price], …]``)
    for trendline / measure / fibonacci, ``price`` for a horizontal line,
    ``span`` + ``y1``/``y2`` for a zone. Every fractional index maps through
    :func:`ts_for_fractional_index`, so the result is the ts-keyed payload a
    ``Drawing`` record carries. ``{}`` when the shape is unusable — the
    caller drops the message rather than emitting a half-record.
    """
    data = payload if isinstance(payload, dict) else {}
    kind = str(data.get("kind") or "")
    if kind not in DRAWING_KINDS:
        return {}

    def _ts(value):
        return ts_for_fractional_index(value, plotted, indices, period)

    if kind in ("trendline", "measure", "fibonacci"):
        points = data.get("points") or []
        if not isinstance(points, (list, tuple)) or len(points) != 2:
            return {}
        first_x, second_x = _ts(points[0][0]), _ts(points[1][0])
        first_y = _optional_float(points[0][1])
        second_y = _optional_float(points[1][1])
        if None in (first_x, second_x, first_y, second_y):
            return {}
        built = {"p1": {"x": first_x, "y": first_y},
                 "p2": {"x": second_x, "y": second_y}}
        if kind == "fibonacci":
            built["type"] = "ext" if data.get("type") == "ext" else "retr"
        return built
    if kind == "horizontal":
        price = _optional_float(data.get("price"))
        return {} if price is None else {"y": price}
    if kind == "zone":
        span = data.get("span") or []
        if not isinstance(span, (list, tuple)) or len(span) != 2:
            return {}
        start, end = _ts(span[0]), _ts(span[1])
        y1, y2 = _optional_float(data.get("y1")), _optional_float(data.get("y2"))
        if None in (start, end, y1, y2):
            return {}
        return {"x1": min(start, end), "x2": max(start, end),
                "y1": min(y1, y2), "y2": max(y1, y2)}
    return {}


class LwcDrawingSurface:
    """``DrawingOverlay``-shaped read-only surface for the session fan-out.

    ``TickerSession`` fans drawings out to every attached view through
    ``view.drawing_overlay.set_data(symbol, drawings, groups)`` (the D24
    contract the pop-out relies on). This view renders primitives instead of
    the default engine's overlay, so it exposes the same single entry point
    and maps it onto :meth:`LwcChartView.set_drawings`. Read-only by
    construction:
    there is no tool mode to query and no drag/edit surface — a pop-out is
    never an editor (D24.6), and the main chart remains the sole writer.
    """

    def __init__(self, view: "LwcChartView"):
        self._view = view

    def set_data(self, symbol, drawings, groups=None) -> None:
        """Session fan-out entry point (drawings + groups → primitives)."""
        self._view.set_drawings(drawings, groups)

    @property
    def drawings(self) -> list:
        """The drawing records currently rendered (read-only copy)."""
        return self._view.drawings

    def tool_active(self) -> bool:
        """No tool can be active on the LWC engine's read-only surface."""
        return False


class LwcChartView(QWidget):
    """The LWC engine view: the Phase 3 core-chart driver.

    Owns the ``ChartView`` state (``update_bars`` / ``update_last_bar``
    / ``set_symbol`` / ``set_timeframe``) plus the P6-05 contract
    (``set_series(mode, rows)`` / ``update_live_bar(bar)``), and emits
    through an owned ``LwBridge`` the host page drains. Alarm lines/overlays
    are published on the alarm channel (P6-08) and drawings on the drawing
    channel (P6-09); the pre-D47 ``drawing_controller`` / ``alarm_controller``
    signal surface is present too (Q-20) and is what the page's messages
    re-emit onto, so MainWindow wires either engine identically.
    """

    ENGINE_NAME = "lwc"

    #: One study envelope per publish — ``{"v": 1, "ops": [...]}``. Kept
    #: separate from ``LwBridge``: the bar transport pins its series set
    #: (candles/volume), so study ops travel on their own channel.
    studyOpsEmitted = pyqtSignal(dict)

    #: One interaction envelope per control/router event — same reasoning as
    #: the study channel: the bar transport's series set is pinned, so
    #: router/control ops never ride it.
    interactionOpsEmitted = pyqtSignal(dict)

    #: One alarm envelope per publish (set / preview) — the alarm channel.
    alarmOpsEmitted = pyqtSignal(dict)

    #: One drawing envelope per publish (drawings / selection / drag).
    drawingOpsEmitted = pyqtSignal(dict)

    #: One overlay envelope per publish (session / gap / VIX / ICT regions).
    overlayOpsEmitted = pyqtSignal(dict)

    #: DG92 focus round-trip: the page's Esc blur handed focus back to Qt.
    focusRoundTrip = pyqtSignal()

    #: AC-D3.9: the page's router refused a zoom (TR-9). Named exactly as
    #: ``ChartPanel.zoom_refused`` so MainWindow's status hint wires to either
    #: engine unchanged.
    zoom_refused = pyqtSignal()

    #: Q-20: a keyboard gesture the page handled (``"ArrowLeft"``, ``"+"``,
    #: ``"Escape"``, …). No pre-D47 counterpart exists, so this is the view's
    #: own surface rather than a controller re-emit.
    key_pressed = pyqtSignal(str)

    def __init__(self, tz_offset: float = 0.0, editable: bool = True,
                 parent=None):
        super().__init__(parent)
        self._tz_offset = tz_offset
        self._editable = editable
        self._bars: list = []
        self._symbol: str = ""
        self._timeframe = None
        self._ext_hours = True
        self._mode = DEFAULT_MODE
        self._bridge = LB.LwBridge(self)
        # D47/Q-20: the engine-neutral controller surface MainWindow already
        # wires. Imported here (not at module import) so the renderer module
        # never drags the pyqtgraph seam in at import time.
        from ui.chart_view import AlarmController, DrawingController

        self.drawing_controller = DrawingController(parent=self)
        self.alarm_controller = AlarmController(parent=self)
        # Q-20 page → Python messages: the bridge slots raise these; the
        # handlers below re-emit onto the controller signals
        # (``drawing_controller.created`` …) and the view's own
        # ``zoom_refused`` / ``key_pressed``. Connected here rather than in
        # ``ensure_host`` so the message path needs no page.
        self._bridge.pageFocusReleased.connect(self.handle_focus_released)
        self._bridge.pageDrawingCommitted.connect(
            self._on_page_drawing_committed)
        self._bridge.pageDrawingUpdated.connect(self._on_page_drawing_updated)
        self._bridge.pageDrawingDeleted.connect(self._on_page_drawing_deleted)
        self._bridge.pageSelectionChanged.connect(
            self._on_page_selection_changed)
        self._bridge.pageAlarmCreated.connect(self._on_page_alarm_created)
        self._bridge.pageAlarmMoved.connect(self._on_page_alarm_moved)
        self._bridge.pageAlarmDeleted.connect(self._on_page_alarm_deleted)
        self._bridge.pageZoomRefused.connect(self._on_page_zoom_refused)
        self._bridge.pageKeyPressed.connect(self._on_page_key_pressed)
        self._plotted: list = []
        self._logical: list = []
        self._cmap = None
        # Q-54: rate-limiting for the logical-map extend-failure log in
        # update_live_bar — the first failure per series warns, repeats
        # drop to debug until the map is healthy again.
        self._extend_fallback_warned = False
        self._host = None
        # Q-19/S3a: the host was parented to this view but never added to a
        # layout, so it kept Qt's default widget size (measured 100x30 inside
        # a 950x850 view). One zero-margin layout owned by the view covers the
        # main chart and every pop-out (each LWC view builds its own).
        self._host_layout = QVBoxLayout(self)
        self._host_layout.setContentsMargins(0, 0, 0, 0)
        self._host_layout.setSpacing(0)
        # P6-11: the session fan-out reaches drawings through the same
        # ``drawing_overlay.set_data`` entry point the default engine has.
        self._drawing_surface = LwcDrawingSurface(self)
        # P6-06: studies come from the shared model through the one cache.
        self._studies: list = []
        self._study_cache = chart_model.StudyCache()
        self._study_overlays: dict = {}
        self._study_log: list = []
        self._study_envelopes: list = []
        self._study_sig: tuple | None = None
        # P6-07: the frozen router owns gesture precedence; the controls shim
        # routes into it. Drawings are not wired until P6-09 owns their
        # surface; alarm placement is armed through the same router (P6-08).
        self._router = ChartMouseRouter()
        self._interaction_log: list = []
        self._interaction_envelopes: list = []
        self._focus_released = 0
        # P6-08: alarms render from the unchanged alarm records. The Qt
        # dialogs (create/edit/rearm/mute/delete) stay exactly where they are.
        self._alarms: list = []
        self._alarm_log: list = []
        self._alarm_envelopes: list = []
        self._alarm_preview_price: float | None = None
        # P6-09: drawings render as ts-to-fractional-index primitives from
        # the validated payloads; the Qt drawing dialogs stay where they are.
        self._drawings: list = []
        self._drawing_groups: list = []
        self._selected_drawing_id = None
        self._drawing_items: list = []
        self._drawing_log: list = []
        self._drawing_envelopes: list = []
        # P6-10: overlays render from the unchanged services.
        self._overlays: dict = {}
        self._overlay_log: list = []
        self._overlay_envelopes: list = []

    @property
    def tz_offset(self) -> float:
        return self._tz_offset

    @property
    def editable(self) -> bool:
        return self._editable

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def bridge(self) -> LB.LwBridge:
        """The owned transport (tests and the host drain it)."""
        return self._bridge

    @property
    def plotted_bars(self) -> list:
        """The rows actually sent (RTH filtering already applied)."""
        return list(self._plotted)

    @property
    def logical_index(self) -> list:
        """Logical-index positions parallel to ``plotted_bars``.

        Internal only (Q-20): drawings/overlays map through it; the series
        ``ts`` column carries real UTC times.
        """
        return list(self._logical)

    @property
    def series_times(self) -> list:
        """Real UTC epoch seconds parallel to ``plotted_bars`` (Q-20)."""
        return [int(bar.ts) for bar in self._plotted]

    @property
    def studies(self) -> list:
        """The study configuration currently driving the overlays."""
        return [dict(study) for study in self._studies]

    @property
    def study_cache(self) -> chart_model.StudyCache:
        """The one ``StudyCache`` backing this view's study values."""
        return self._study_cache

    @property
    def study_overlays(self) -> dict:
        """Overlay id -> the value array last published to the engine."""
        return {kind: list(values)
                for kind, values in self._study_overlays.items()}

    @property
    def study_ops(self) -> list:
        """Every study op published so far, in order (the replay log)."""
        return [dict(op) for op in self._study_log]

    @property
    def study_envelopes(self) -> list:
        """Every study envelope emitted, in order."""
        return [{"v": env["v"], "ops": [dict(op) for op in env["ops"]]}
                for env in self._study_envelopes]

    @property
    def router(self) -> ChartMouseRouter:
        """The frozen router this view's interaction shims route through."""
        return self._router

    @property
    def interaction_ops(self) -> list:
        """Every interaction op emitted so far, in order (the replay log)."""
        return [dict(op) for op in self._interaction_log]

    @property
    def interaction_envelopes(self) -> list:
        """Every interaction envelope emitted, in order."""
        return [{"v": env["v"], "ops": [dict(op) for op in env["ops"]]}
                for env in self._interaction_envelopes]

    @property
    def focus_releases(self) -> int:
        """DG92 focus round-trips recorded (page Esc blur → Qt focus)."""
        return self._focus_released

    @property
    def alarms(self) -> list:
        """The alarm records currently rendered (visible price alarms)."""
        return list(self._alarms)

    @property
    def alarm_ops(self) -> list:
        """Every alarm op published so far, in order (the replay log)."""
        return [dict(op) for op in self._alarm_log]

    @property
    def alarm_envelopes(self) -> list:
        """Every alarm envelope emitted, in order."""
        return [{"v": env["v"], "ops": [dict(op) for op in env["ops"]]}
                for env in self._alarm_envelopes]

    @property
    def alarm_preview_price(self) -> float | None:
        """The D21.10 preview line's price, or ``None`` when hidden."""
        return self._alarm_preview_price

    @property
    def drawings(self) -> list:
        """The drawing records currently rendered (visible, valid)."""
        return list(self._drawings)

    @property
    def drawing_items(self) -> list:
        """The wire items last published (fractional indices + prices)."""
        return [dict(item) for item in self._drawing_items]

    @property
    def drawing_ops(self) -> list:
        """Every drawing op published so far, in order (the replay log)."""
        return [dict(op) for op in self._drawing_log]

    @property
    def drawing_envelopes(self) -> list:
        """Every drawing envelope emitted, in order."""
        return [{"v": env["v"], "ops": [dict(op) for op in env["ops"]]}
                for env in self._drawing_envelopes]

    @property
    def selected_drawing(self):
        """The id of the drawing last selected (or ``None``)."""
        return self._selected_drawing_id

    @property
    def overlays(self) -> dict:
        """Overlay name -> the regions last published to the engine."""
        return {name: [dict(region) for region in regions]
                for name, regions in self._overlays.items()}

    @property
    def overlay_ops(self) -> list:
        """Every overlay op published so far, in order (the replay log)."""
        return [dict(op) for op in self._overlay_log]

    @property
    def overlay_envelopes(self) -> list:
        """Every overlay envelope emitted, in order."""
        return [{"v": env["v"], "ops": [dict(op) for op in env["ops"]]}
                for env in self._overlay_envelopes]

    # ── ChartView protocol ──────────────────────────────────────────

    def update_bars(self, bars: list) -> None:
        """Full history replace in the current mode."""
        self.set_series(self._mode, bars or [])

    def update_last_bar(self, bar, is_new_candle: bool) -> None:
        """Intra-bar live update (replace the forming bar or append)."""
        if not self._bars:
            if is_new_candle:
                self.update_bars([bar])
            return
        self.update_live_bar(bar)

    def set_symbol(self, symbol: str) -> None:
        self._symbol = symbol
        # TR-17: a symbol change mid-gesture resets the interaction state.
        self.reset_interaction()
        # A different symbol is a different study series: never serve the
        # previous symbol's cached arrays.
        self._study_cache.invalidate()
        self._study_sig = None
        if self._bars:
            self._render_studies()
            self._render_overlays()

    def set_timeframe(self, timeframe: str) -> None:
        self._timeframe = timeframe
        if self._bars:
            self.set_series(self._mode, self._bars)

    # ── P6-05 contract ──────────────────────────────────────────────

    def set_extended_hours(self, enabled: bool) -> None:
        """Re-derive the plotted set + logical axis for the new mode."""
        self._ext_hours = bool(enabled)
        if self._bars:
            self.set_series(self._mode, self._bars)

    def set_mode(self, mode: str) -> None:
        """Select one of the five render modes (resends when loaded)."""
        if mode not in MODES:
            raise ValueError(f"unknown mode: {mode!r}")
        if mode == self._mode:
            return
        self._mode = mode
        if self._bars:
            self.set_series(mode, self._bars)

    def set_series(self, mode: str, rows: list) -> None:
        """Full replace: filter, map to real UTC time, emit set ops.

        The series ``ts`` column is the bar's real UTC epoch seconds (Q-20);
        the logical index is derived here for the internal drawing/overlay
        axis only and never leaves as a series time.
        """
        if mode not in MODES:
            raise ValueError(f"unknown mode: {mode!r}")
        self._mode = mode
        self._bars = list(rows or [])
        # Q-54: a wholesale replacement rebuilds the map — re-arm the
        # extend-failure warning for the new series.
        self._extend_fallback_warned = False
        self._plotted = [self._bars[i] for i in chart_model.plotted_index_rows(
            self._bars, self._timeframe, self._ext_hours)]
        self._cmap = chart_model.collapse_for_bars(
            self._plotted, self._timeframe, self._ext_hours)
        period = TIMEFRAME_SECONDS.get(self._timeframe or "")
        if self._cmap is None or not period:
            self._logical = list(range(len(self._plotted)))
        else:
            self._logical = logical_indices_from_display(
                chart_model.display_xs(self._plotted, self._cmap), period)
        self._bridge.send_ops(build_series_ops(
            mode, self._plotted, self._cmap, self._logical, period))
        # A wholesale bar replacement invalidates the study cache (the
        # incremental path assumes the same series), exactly as the default
        # engine's chart panel does on a load.
        self._study_cache.invalidate()
        self._study_sig = None
        self._render_studies()
        # Drawings are time-anchored: a new axis re-maps every anchor to the
        # candles' fractional logical index, exactly as the reference overlay
        # re-renders at the new display-x (AC-D21.4.1).
        if self._drawings:
            self._render_drawings()
        # Overlays are time-anchored too: a new axis re-maps every region
        # through the same fractional logical index.
        self._render_overlays()

    def update_live_bar(self, bar) -> None:
        """Advance the forming bar via single-element ``update_bar`` ops.

        A same-timestamp tick replaces the forming bar; a newer
        timestamp appends a new period; an out-of-order tick is ignored
        (history is never rewritten by a stale tick). Only the tick's
        ops cross — history is never resent. The ``ts`` is the bar's real
        UTC time, the same domain as ``set_series`` (Q-20); a new period that
        opens a within-session hole republishes the series so the hole keeps
        its whitespace slots (AC-D21.4.4).
        """
        if not self._bars:
            self.set_series(self._mode, [bar])
            return
        last = self._bars[-1]
        if bar.ts < last.ts:
            return
        new_period = bar.ts != last.ts
        if new_period:
            self._bars.append(bar)
        else:
            self._bars[-1] = bar
        if not chart_model.is_bar_plotted(
                bar, self._timeframe, self._ext_hours):
            # Visible set unchanged (filtered out) — still rebuild the
            # plotted/logical arrays so a later tick sees the true tail.
            self._plotted = [self._bars[i] for i in
                             chart_model.plotted_index_rows(
                                 self._bars, self._timeframe,
                                 self._ext_hours)]
            if self._plotted:
                self._cmap = chart_model.collapse_for_bars(
                    self._plotted, self._timeframe, self._ext_hours)
                self._logical = logical_indices(
                    self._plotted, self._timeframe, self._ext_hours)
            return
        if new_period:
            previous_index = self._logical[-1] if self._logical else None
            self._plotted.append(bar)
            extended = False
            if self._cmap is not None:
                try:
                    extended = bool(self._cmap.extend(bar.ts))
                except Exception as exc:
                    # Q-54: keep the rebuild fallback, but make it visible:
                    # first failure per series warns (timeframe + exception
                    # type), repeats drop to debug so a per-bar failure
                    # storm logs once.
                    extended = False
                    if not self._extend_fallback_warned:
                        _LOG.warning(
                            "lwc logical-map extend failed "
                            "(timeframe=%s, exc=%s) — rebuilding map",
                            self._timeframe,
                            type(exc).__name__,
                        )
                        self._extend_fallback_warned = True
                    else:
                        _LOG.debug(
                            "lwc logical-map extend failed "
                            "(timeframe=%s, exc=%s) — rebuilding map",
                            self._timeframe,
                            type(exc).__name__,
                        )
                if extended:
                    self._extend_fallback_warned = False
            if not extended:
                self._cmap = chart_model.collapse_for_bars(
                    self._plotted, self._timeframe, self._ext_hours)
            self._logical = logical_indices(
                self._plotted, self._timeframe, self._ext_hours)
            opened_hole = (previous_index is not None
                           and self._logical
                           and self._logical[-1] - previous_index > 1)
            if opened_hole:
                # A within-session hole opened live: republish the series so
                # the missing periods keep their whitespace slots. The tick's
                # single update_bar cannot carry placeholders.
                self._bridge.send_ops(build_series_ops(
                    self._mode, self._plotted, self._cmap, self._logical,
                    TIMEFRAME_SECONDS.get(self._timeframe or "")))
                self._render_studies()
                self._render_overlays()
                return
        else:
            self._plotted[-1] = bar
        tick = self._tick_candle_cols(bar)
        self._bridge.send_ops([
            {"op": "update_bar", "series": "candles", "cols": tick},
            {"op": "update_bar", "series": "volume",
             "cols": {"ts": [int(bar.ts)], "value": [float(bar.volume)]}},
        ])
        # Studies follow the tick — a new candle is served by the cache's
        # incremental path, an intra-bar tick takes the full path (the
        # forming bar's study value has no cache state to replay from).
        self._render_studies()
        if new_period:
            # A new period changes the axis' span: the session bands' clip,
            # the gap staircase's extension and the VIX label anchor all move.
            self._render_overlays()

    # ── P6-06 study overlays (shared model + one cache) ─────────────

    def set_studies(self, studies: list) -> None:
        """Store the study configuration and publish it through the model.

        Every numeric value comes from ``chart_model.compute_study_values``
        over this view's one ``StudyCache`` — the same source the default
        engine renders — so parity is by construction. A configuration that
        did not change re-renders as a no-op (no compute, no traffic).
        """
        requested = [dict(study) for study in (studies or [])]
        if requested != self._studies:
            self._studies = requested
            self._study_cache.invalidate()
            self._study_sig = None
        if self._bars:
            self._render_studies()
        elif self._study_overlays:
            self._publish_study_ops([clear_study_op()], {})
        # rth_gaps / vix_sd / ict are overlay studies: their configuration
        # drives the overlay channel, so a study change re-renders it.
        self._render_overlays()

    def study_overlay_signature(self) -> tuple | None:
        """Fingerprint of the rendered study state (bars + configuration).

        Two identical renders produce the same fingerprint, which is what
        lets a repeated render skip recomputation entirely.
        """
        return self._study_signature()

    def set_study_overlay(self, kind: str, series: list) -> None:
        """Publish one study overlay's value series to the LWC engine.

        ``kind`` is the overlay id — the shared model's ``study_key`` plus
        its line suffix, e.g. ``"sma:0"``, ``"bollinger:0_mid"``,
        ``"macd:0_hist"``. ``series`` holds one nullable value per plotted
        bar; ``None`` marks a period where the study is not yet valid and
        crosses as whitespace. The values are published exactly as given —
        no engine-side arithmetic.
        """
        base = study_base_kind(kind)
        if base not in STUDY_KINDS:
            raise ValueError(f"unknown study kind: {kind!r}")
        values = list(series or [])
        if self._plotted and len(values) != len(self._plotted):
            raise ValueError(
                "series must be parallel to the plotted bars "
                f"({len(values)} != {len(self._plotted)})")
        ts = self.series_times if self._plotted else list(range(len(values)))
        overlay = dict(self._study_overlays)
        overlay[kind] = values
        self._study_sig = None
        self._publish_study_ops([study_op(kind, ts, values)], overlay)

    def _render_studies(self) -> None:
        """Compute (or reuse) every study overlay and publish the ops.

        Fully served by ``StudyCache`` when only the forming bar or a single
        new candle changed; a repeated render of an identical state does no
        work at all. Overlay studies (rth_gaps / vix_sd / ict) are skipped —
        they render through their own surfaces at P6-10.
        """
        if not self._studies or not self._plotted:
            if self._study_overlays:
                self._study_sig = None
                self._publish_study_ops([clear_study_op()], {})
            return
        sig = self._study_signature()
        if sig == self._study_sig:
            return  # identical state: no recompute, no traffic
        all_vals, states = chart_model.compute_study_values(
            self._plotted, self._studies, self._study_cache,
            self._symbol, self._timeframe or "")
        ops: list = []
        overlays: dict = {}
        for idx, study in enumerate(self._studies):
            if not study.get("enabled"):
                continue
            stype = study["type"]
            if stype not in STUDY_LINES:
                continue  # overlay study — not a numeric series
            params = study.get("params", {})
            key = chart_model.study_key(stype, idx)
            for suffix in STUDY_LINES[stype]:
                values = self._study_series(stype, key, suffix, all_vals)
                if values is None:
                    continue
                overlay_id = f"{key}{suffix}"
                overlays[overlay_id] = list(values)
                ops.append(study_op(overlay_id, self.series_times, values,
                                    params))
        self._study_sig = sig
        if all_vals:
            self._study_cache.set(
                self._symbol, self._timeframe or "", self._studies,
                {"n_bars": len(self._plotted),
                 "last_ts": self._plotted[-1].ts,
                 "values": {k: list(v) for k, v in all_vals.items()},
                 "states": states},
            )
        if not ops:
            if self._study_overlays:
                self._publish_study_ops([clear_study_op()], {})
            return
        self._publish_study_ops(ops, overlays)

    @staticmethod
    def _study_series(stype: str, key: str, suffix: str,
                      all_vals: dict) -> list | None:
        """One overlay's value array, or ``None`` when the model has none.

        MACD's histogram is the model's MACD minus its signal (the default
        engine draws exactly that difference) and is whitespace until both
        legs are valid.
        """
        if stype == "macd" and suffix == "_hist":
            macd = all_vals.get(key) or []
            signal = all_vals.get(f"{key}_signal") or []
            if not macd or not signal:
                return None
            return [None if (m is None or s is None) else m - s
                    for m, s in zip(macd, signal)]
        return all_vals.get(f"{key}{suffix}")

    def _study_signature(self) -> tuple:
        """Bars + configuration fingerprint for the render guard."""
        return (
            len(self._plotted),
            self._plotted[-1].ts if self._plotted else None,
            tuple(sorted((str(study.get("type")),
                          repr(study.get("params", {})))
                         for study in self._studies if study.get("enabled"))),
        )

    def _publish_study_ops(self, ops: list, overlays: dict) -> None:
        """Log and emit one study envelope (``{"v": 1, "ops": [...]}``)."""
        self._study_overlays = {kind: list(values)
                                for kind, values in overlays.items()}
        env = {"v": LB.ENVELOPE_VERSION,
               "ops": [dict(op) for op in ops]}
        self._study_log.extend(env["ops"])
        self._study_envelopes.append(env)
        self.studyOpsEmitted.emit(env)
        # Q-31: the page's consumer for this channel.
        self._bridge.send_channel("studies", env["ops"])

    # ── P6-07 interaction: in-HTML controls + router shims ─────────────

    def handle_control(self, control_id: str, value=None) -> dict:
        """One in-HTML control event → router intent → interaction op.

        ``control_id`` is one of ``CONTROL_IDS`` — the page's buttons mirror
        ``ui/chart_controls.py``'s signals. The magnifier and reset go through
        the frozen router (so alarm placement refuses the magnifier, TR-9);
        zoom in/out are pure view intents the page applies to its own time
        scale. Returns ``{"control", "op", "mode", "refused"}``.
        """
        if control_id not in CONTROL_IDS:
            raise ValueError(f"unknown control: {control_id!r}")
        if control_id in ("zoom-in", "zoom-out"):
            step = 1 if control_id == "zoom-in" else -1
            op = {"op": "zoom", "step": step}
            refused = False
        elif control_id == "magnifier":
            # ``value`` is the toggle's checked state (ChartControls emits
            # ``magnify_toggled(bool)``); ``None`` toggles from the router.
            before = self._router.active_mode
            mode = self._router.active_mode
            enabled = (mode != RouterMode.ZOOMING) if value is None else bool(value)
            if enabled:
                # TR-2 / TR-4 / TR-9 — the router decides, not this shim.
                refused = not self._router.enter_zoom()
                intent = "enter_zoom"
            else:
                self._router.exit_to_idle()
                refused = False
                intent = "exit_to_idle"
            op = {"op": "router_mode", "mode": self._router.active_mode.name,
                  "intent": intent, "refused": refused}
            # TR-4 (and the refused TR-9 from DRAWING): entering zoom from
            # DRAWING is the router clearing the drawing tool as a side
            # effect. Mirror the overlay's signal so the combo resets.
            if (enabled and not refused and before == RouterMode.DRAWING):
                self.drawing_controller.mode_changed.emit(TOOL_CURSOR)
        else:  # "reset"
            self._router.exit_to_idle()
            op = {"op": "reset_view", "mode": self._router.active_mode.name}
            refused = False
        self._publish_interaction_op(op)
        return {"control": control_id, "op": dict(op),
                "mode": self._router.active_mode.name, "refused": refused}

    def set_drawing_tool(self, tool: str) -> str:
        """Arm (or clear) a drawing tool through the frozen router.

        The main window's toolbar calls this for every combo change. An
        unknown/``None`` name falls back to ``TOOL_CURSOR`` — the reference
        overlay's ``set_tool`` contract — and a real tool enters ``DRAWING``
        (TR-1/TR-5/TR-8). D24: a pop-out (non-editable) view is read-only and
        the call is inert.

        ``mode_changed`` mirrors the overlay's own signal, so ``MainWindow``
        keeps its combo in step (ESC-017). The tool stays armed after a
        commit; only an explicit cursor switch / router clear disarms it.
        """
        if not self._editable:
            return self._router.active_mode.name
        name = tool if tool in DRAWING_TOOLS else TOOL_CURSOR
        self._router.enter_drawing(name)
        real_tool = name != TOOL_CURSOR
        self._publish_interaction_op({
            "op": "router_mode",
            "mode": self._router.active_mode.name,
            "intent": "draw_tool" if real_tool else "draw_cursor",
            "refused": False,
            "tool": name,
        })
        self.drawing_controller.mode_changed.emit(name)
        return self._router.active_mode.name

    def reset_interaction(self) -> str:
        """TR-17: reset the router (discard any draft) on a symbol change.

        Emits one ``router_mode`` op when a gesture was in progress, so the
        page drops its magnifier/draft state with the Python router. A
        symbol change out of ``DRAWING`` also cleared the drawing tool as a
        side effect, so the overlay's ``mode_changed(cursor)`` fires and the
        toolbar combo resets (ESC-017).
        """
        before = self._router.active_mode
        mode = reset_router_for_symbol_change(self._router)
        if before != RouterMode.IDLE:
            self._publish_interaction_op(
                {"op": "router_mode", "mode": mode.name,
                 "intent": "symbol_change", "refused": False})
        if before == RouterMode.DRAWING:
            self.drawing_controller.mode_changed.emit(TOOL_CURSOR)
        return mode.name

    def handle_focus_released(self) -> None:
        """DG92 focus round-trip: the page's Esc blur hands focus back to Qt.

        The page glue (``lwc-focus-forward-v1``) calls the bridge's
        ``focusReleased`` slot; the host forwards it here so the view can
        restore the Qt focus chain. The recorded count is the round-trip
        evidence P6-07 reports.
        """
        self._focus_released += 1
        self.focusRoundTrip.emit()

    # ── page → Python messages (Q-20) ───────────────────────────────────
    #
    # Every bridge slot funnels into one handler here, and each handler
    # re-emits the signal MainWindow already wires (the pre-D47
    # ``DrawingController`` / ``AlarmController`` surface, ``zoom_refused``)
    # or the view's own ``key_pressed``. Payloads are the page's own units —
    # fractional indices for geometry — so drawing anchors map back onto bar
    # timestamps before they reach the store-facing signal.

    def _page_axis(self) -> tuple:
        """``(plotted, indices, period)`` for a page-originated anchor."""
        return (self._plotted, self._logical,
                TIMEFRAME_SECONDS.get(self._timeframe or ""))

    def _on_page_drawing_committed(self, payload: dict) -> None:
        """A drawing gesture finished in the page → ``created``.

        The record carries no id (``created`` means "not stored yet"); its
        payload is ts-keyed again because the store and the session fan-out
        are. An unusable geometry is dropped rather than emitted half-built.
        """
        data = payload if isinstance(payload, dict) else {}
        plotted, indices, period = self._page_axis()
        geometry = page_geometry_payload(data, plotted, indices, period)
        if not geometry:
            return
        # The page does not know the chart's symbol (it is renderer-only
        # state), so the record takes it from the view — falling back to the
        # symbol carried by the loaded bars when no explicit ``set_symbol``
        # has run (the ``update_chart``-only path).
        symbol = self._symbol
        if not symbol and self._plotted:
            symbol = str(getattr(self._plotted[-1], "symbol", "") or "")
        self.drawing_controller.created.emit(PageDrawing(
            symbol=symbol,
            kind=str(data.get("kind") or ""),
            payload=geometry,
            color=(str(data["color"]) if data.get("color") else None),
            group_id=_optional_int(data.get("group_id")),
        ))

    def _on_page_drawing_updated(self, payload: dict) -> None:
        """An edited drawing in the page → ``updated(id, payload, color)``."""
        data = payload if isinstance(payload, dict) else {}
        drawing_id = _optional_int(data.get("id"))
        geometry = page_geometry_payload(
            data, *self._page_axis())
        if drawing_id is None or not geometry:
            return
        self.drawing_controller.updated.emit(
            int(drawing_id), geometry, str(data.get("color") or ""))

    def _on_page_drawing_deleted(self, payload: dict) -> None:
        """A drawing deleted in the page → ``deleted(id)``."""
        data = payload if isinstance(payload, dict) else {}
        drawing_id = _optional_int(data.get("id"))
        if drawing_id is None:
            return
        if self._selected_drawing_id == drawing_id:
            self._selected_drawing_id = None
        self.drawing_controller.deleted.emit(int(drawing_id))

    def _on_page_selection_changed(self, payload: dict) -> None:
        """The page's selection → ``selection_changed(id)`` (``-1`` clears).

        The page already applied its own highlight, so this only mirrors the
        state: republishing a ``select_drawing`` op here would echo the
        message straight back.
        """
        data = payload if isinstance(payload, dict) else {}
        drawing_id = _optional_int(data.get("id"))
        value = -1 if drawing_id is None or drawing_id < 0 else int(drawing_id)
        self._selected_drawing_id = None if value < 0 else value
        self.drawing_controller.selection_changed.emit(value)

    def _on_page_alarm_created(self, payload: dict) -> None:
        """An alarm placed on the page's price axis → ``create_requested``."""
        data = payload if isinstance(payload, dict) else {}
        price = _optional_float(data.get("price"))
        if price is None:
            return
        self.alarm_controller.create_requested.emit(float(price))

    def _on_page_alarm_moved(self, payload: dict) -> None:
        """An alarm line dragged in the page → ``moved(id, price)``."""
        data = payload if isinstance(payload, dict) else {}
        alarm_id = _optional_int(data.get("id"))
        price = _optional_float(data.get("price"))
        if alarm_id is None or price is None:
            return
        self.alarm_controller.moved.emit(int(alarm_id), float(price))

    def _on_page_alarm_deleted(self, payload: dict) -> None:
        """An alarm line deleted in the page → ``delete_requested(id)``."""
        data = payload if isinstance(payload, dict) else {}
        alarm_id = _optional_int(data.get("id"))
        if alarm_id is None:
            return
        self.alarm_controller.delete_requested.emit(int(alarm_id))

    def _on_page_zoom_refused(self, payload: dict) -> None:
        """The page's router refused a zoom (TR-9) → ``zoom_refused``."""
        self.zoom_refused.emit()

    def _on_page_key_pressed(self, payload: dict) -> None:
        """A keyboard gesture the page handled → ``key_pressed(key)``."""
        data = payload if isinstance(payload, dict) else {}
        self.key_pressed.emit(str(data.get("key") or ""))

    def _publish_interaction_op(self, op: dict) -> None:
        """Log and emit one interaction envelope (``{"v": 1, "ops": [...]}``)."""
        env = {"v": LB.ENVELOPE_VERSION, "ops": [dict(op)]}
        self._interaction_log.extend(env["ops"])
        self._interaction_envelopes.append(env)
        self.interactionOpsEmitted.emit(env)
        self._bridge.send_channel("interaction", env["ops"])

    # ── P6-08 alarm lines/overlays ─────────────────────────────────────

    def set_alarm_lines(self, alarms: list) -> None:
        """Render the unchanged alarm records as lines on the LWC engine.

        The contracted Phase-6 surface: identical alarm state produces the
        same colours, label text, price levels and z-order as the default
        engine's ``AlarmOverlay``. The ``kind == "price"`` / id filtering
        mirrors that overlay (D39), and the whole set crosses as one
        replace-all op, so a replay never duplicates or orphans a line. An
        empty set clears the engine.
        """
        rows = [alarm for alarm in (alarms or []) if alarm_visible(alarm)]
        self._alarms = rows
        self._publish_alarm_ops(
            [alarm_op(rows)] if rows else [clear_alarms_op()])

    def set_alarms(self, alarms) -> None:
        """``ChartPanel.set_alarms`` under the view's own name (parity)."""
        self.set_alarm_lines(alarms)

    def set_alarm_mode(self, enabled: bool) -> str:
        """Arm/disarm alarm placement through the frozen router.

        TR-3/TR-6 arm it (exiting a zoom, discarding a drawing draft), TR-13
        disarms it. D24: a pop-out (non-editable) view is read-only and the
        call is inert, exactly as ``ChartPanel.set_alarm_mode`` is. Returns
        the resulting mode name.
        """
        if not self._editable:
            return self._router.active_mode.name
        before = self._router.active_mode
        if enabled:
            self._router.enter_alarm_placing()
            intent = "enter_alarm_placing"
        else:
            if self._router.active_mode == RouterMode.ALARM_PLACING:
                self._router.exit_to_idle()
            intent = "exit_to_idle"
        self._publish_interaction_op({
            "op": "router_mode", "mode": self._router.active_mode.name,
            "intent": intent, "refused": False,
        })
        # TR-7: arming alarm placement from DRAWING discards the drawing
        # tool. Mirror the overlay's signal so the toolbar combo resets
        # (ESC-017) — otherwise the stale label can never re-arm the tool.
        if enabled and before == RouterMode.DRAWING:
            self.drawing_controller.mode_changed.emit(TOOL_CURSOR)
        return self._router.active_mode.name

    def show_alarm_preview(self, price: float) -> None:
        """Show the D21.10 preview line at ``price`` (idempotent, as on Qt)."""
        self._alarm_preview_price = float(price)
        self._publish_alarm_ops([alarm_preview_op(price)])

    def update_alarm_preview(self, price: float) -> None:
        """Move the preview line (no-op while it is hidden — AC-D21.10.3)."""
        if self._alarm_preview_price is None:
            return
        self._alarm_preview_price = float(price)
        self._publish_alarm_ops([alarm_preview_op(price)])

    def hide_alarm_preview(self) -> None:
        """Remove the preview line (idempotent — AC-D21.10.4)."""
        if self._alarm_preview_price is None:
            return
        self._alarm_preview_price = None
        self._publish_alarm_ops([clear_alarm_preview_op()])

    def _publish_alarm_ops(self, ops: list) -> None:
        """Log and emit one alarm envelope (``{"v": 1, "ops": [...]}``)."""
        env = {"v": LB.ENVELOPE_VERSION, "ops": [dict(op) for op in ops]}
        self._alarm_log.extend(env["ops"])
        self._alarm_envelopes.append(env)
        self.alarmOpsEmitted.emit(env)
        self._bridge.send_channel("alarms", env["ops"])

    # ── P6-09 drawing primitives (ts -> fractional index) ─────────────

    def drawing_axis(self) -> tuple[list, list, object]:
        """``(display_xs, logical_indices, collapse_map)`` for the plotted rows."""
        return drawing_axis(self._plotted, self._timeframe, self._ext_hours)

    def set_drawings(self, drawings: list, groups: list | None = None) -> None:
        """Render the unchanged drawing records as LWC primitives.

        The contracted Phase-7 surface. Every payload is normalised by the
        pure drawing service first, then every anchor timestamp is mapped to
        the fractional logical index of the *same* display-x axis the
        reference overlay draws on. Group visibility and lock state mirror
        ``DrawingOverlay``; the whole set crosses as one replace-all op, so a
        replay never duplicates or orphans a primitive. An empty set clears
        the engine.
        """
        self._drawings = list(drawings or [])
        self._drawing_groups = list(groups or [])
        self._render_drawings()

    def set_drawing_groups(self, groups: list) -> None:
        """Update group visibility/lock state (re-publishes the same rows)."""
        self._drawing_groups = list(groups or [])
        self._render_drawings()

    def set_drawing_primitive(self, kind: str, frac_index_pts: list) -> None:
        """Publish one validated primitive from fractional-index points.

        The Phase-7 seam: JS receives fractional indices and prices only,
        never a timestamp. Raises ``ValueError`` on an unknown kind or a
        non-numeric point — validation happens here, at the engine boundary.
        """
        self._publish_drawing_ops(
            [drawing_primitive_op(kind, frac_index_pts)])

    def select_drawing(self, drawing_id) -> None:
        """Select one drawing (white 2.0 px pen + handles) or clear with None."""
        self._selected_drawing_id = (None if drawing_id is None
                                     else int(drawing_id))
        self._render_drawings()
        self._publish_drawing_ops([{
            "op": "select_drawing", "series": DRAWING_CHANNEL,
            "id": self._selected_drawing_id,
        }])

    def drag_drawing(self, drawing_id, kind: str, point_index: int,
                     d_frac: float, d_price: float,
                     body: bool = False) -> dict:
        """Apply a drag delta to one drawing and publish the validated result.

        The geometry is computed here (``drag_drawing_item``), so the engine
        only ever replaces a primitive with already-validated numbers. Returns
        the new wire item (also reflected in the stored record's payload for
        the engine's own state, never persisted — persistence stays with the
        drawing store, which the LWC engine never touches).
        """
        item = next((item for item in self._drawing_items
                     if item.get("id") == drawing_id), None)
        if item is None:
            raise ValueError(f"unknown drawing: {drawing_id!r}")
        moved = drag_drawing_item(kind, item, point_index, d_frac, d_price,
                                  body=body)
        self._drawing_items = [dict(moved) if existing.get("id") == drawing_id
                               else existing
                               for existing in self._drawing_items]
        self._publish_drawing_ops([{
            "op": "drag_drawing", "series": DRAWING_CHANNEL,
            "id": moved["id"], "kind": kind, "points": moved.get("points"),
            "price": moved.get("price"), "y1": moved.get("y1"),
            "y2": moved.get("y2"), "delta": moved.get("delta"),
            "levels": moved.get("levels"), "handles": moved["handles"],
            "body": bool(body), "point_index": int(point_index),
        }])
        return moved

    def _render_drawings(self) -> None:
        """Publish the replace-all drawing op from the current axis."""
        if not self._drawings:
            self._drawing_items = []
            if self._drawing_log:
                self._publish_drawing_ops([clear_drawings_op()])
            return
        xs, indices, cmap = self.drawing_axis()
        op = drawing_op(self._drawings, self._drawing_groups, xs, indices,
                        selected_id=self._selected_drawing_id, cmap=cmap)
        self._drawing_items = [dict(item) for item in op["items"]]
        self._publish_drawing_ops([op])

    def _publish_drawing_ops(self, ops: list) -> None:
        """Log and emit one drawing envelope (``{"v": 1, "ops": [...]}``)."""
        env = {"v": LB.ENVELOPE_VERSION, "ops": [dict(op) for op in ops]}
        self._drawing_log.extend(env["ops"])
        self._drawing_envelopes.append(env)
        self.drawingOpsEmitted.emit(env)
        self._bridge.send_channel("drawings", env["ops"])

    # ── P6-10 overlays ─────────────────────────────────────────────────

    def set_overlay(self, name: str, regions: list) -> None:
        """Publish one overlay's regions to the LWC engine.

        ``name`` is one of ``OVERLAY_NAMES``: ``session`` (pre/post bands from
        ``services.session_service.session_bands``), ``rth_gaps`` (staircase
        steps from ``calculate_rth_gaps``), ``vix_sd`` (sigma lines from
        ``calculate_vix_standard_deviation``) or ``ict`` (concepts from
        ``calculate_ict_concepts``). The regions are the shapes
        ``_render_overlays`` builds; passing an empty list clears that
        overlay. Replace-all, so a replay never duplicates or orphans a
        primitive.
        """
        if name not in OVERLAY_NAMES:
            raise ValueError(f"unknown overlay: {name!r}")
        rows = [dict(region) for region in (regions or [])]
        if rows == self._overlays.get(name):
            return
        self._overlays[name] = rows
        self._publish_overlay_ops(
            [overlay_op(name, rows)] if rows else [clear_overlay_op(name)])

    def overlay_regions(self, name: str) -> list:
        """The regions last published for ``name`` (an empty list when none)."""
        return [dict(region) for region in self._overlays.get(name, [])]

    def _render_overlays(self) -> None:
        """Recompute every overlay from the unchanged services on this axis.

        Composition mirrors ``ChartPanel``: ``session_bands`` over the loaded
        bars (extended hours only, never on ``1 day``); the three overlay
        studies — ``rth_gaps`` / ``vix_sd`` / ``ict`` — only when the study
        configuration carries them and is enabled, each through the same
        service call and the same ticker context the panel builds. Identical
        regions are not republished (no traffic, like the study channel).
        """
        wanted: dict = {name: [] for name in OVERLAY_NAMES}
        if self._bars and self._plotted:
            wanted["session"] = session_regions(
                self._bars, self._plotted, self._timeframe, self._ext_hours)
            for study in self._studies:
                if not study.get("enabled"):
                    continue
                stype = study.get("type")
                params = study.get("params", {}) or {}
                if stype == "rth_gaps":
                    ticker = infer_ticker_context(self._symbol, self._bars)
                    wanted["rth_gaps"] = gap_regions(
                        calculate_rth_gaps(self._bars, ticker, params),
                        self._bars, self._plotted, self._timeframe,
                        self._ext_hours)
                elif stype == "vix_sd":
                    ticker = infer_ticker_context(self._symbol, self._bars)
                    wanted["vix_sd"] = vix_levels(
                        calculate_vix_standard_deviation(
                            ticker, self._bars, params),
                        self._plotted, self._timeframe, self._ext_hours)
                elif stype == "ict":
                    ticker = infer_ticker_context(self._symbol, self._bars)
                    window = chart_model.trailing_bars(
                        self._bars, ICT_TRAILING_BARS)
                    wanted["ict"] = ict_regions(
                        calculate_ict_concepts(window, ticker, params), window,
                        self._plotted, self._timeframe, self._ext_hours)
        ops: list = []
        for name in OVERLAY_NAMES:
            rows = wanted[name]
            published = self._overlays.get(name)
            if rows == published:
                continue
            self._overlays[name] = rows
            if not rows and published is None:
                # Nothing was ever drawn for this overlay and there is nothing
                # to draw now: record the empty state, but send no traffic.
                continue
            ops.append(overlay_op(name, rows) if rows
                       else clear_overlay_op(name))
        if ops:
            self._publish_overlay_ops(ops)

    def _publish_overlay_ops(self, ops: list) -> None:
        """Log and emit one overlay envelope (``{"v": 1, "ops": [...]}``)."""
        env = {"v": LB.ENVELOPE_VERSION, "ops": [dict(op) for op in ops]}
        self._overlay_log.extend(env["ops"])
        self._overlay_envelopes.append(env)
        self.overlayOpsEmitted.emit(env)
        self._bridge.send_channel("overlays", env["ops"])

    # ── host (cutover owns the wiring) ──────────────────────────────

    def ensure_host(self):
        """Create the offline host for the owned bridge (lazy).

        Raises where no engine exists (offscreen CI); the production
        wiring of view + host lands at cutover.
        """
        if self._host is None:
            from ui import lwc_host as LH
            if not LH.HAS_WEBENGINE:
                raise RuntimeError(
                    "QtWebEngine is not available — no host here "
                    "(offscreen CI; engine boxes only)."
                )
            self._host = LH.create_host(self._bridge, self, load=False)
            # Q-19/S3a: give the host the view's rectangle. Without this the
            # page's #chart stayed at the host's default 100x30. Adding the
            # widget here (once, because ensure_host is lazy) also keeps every
            # pop-out correct — each pop-out view owns its own layout.
            self._host_layout.addWidget(self._host)
            self._host_layout.activate()
            # Q-23: size the host BEFORE the page boots, so the chart is
            # created at the view's real rectangle instead of at a zero/
            # default size (the fit then ran at zero width and collapsed the
            # series onto one column). A view that has not been laid out yet
            # keeps the page's own resize/fit retry as the safety net.
            width = max(0, int(self.width()))
            height = max(0, int(self.height()))
            if width > 0 and height > 0:
                self._host.resize(width, height)
            self._host.load_chart()
            # Q-19/S3e + Q-20: the page → Python path is already connected in
            # ``__init__`` (the bridge slots need no page); the host's own Esc
            # key handler is the second source of the same round-trip.
            self._host.focusReleased.connect(self.handle_focus_released)
        return self._host

    # ── P6-11 pop-outs: session surfaces + per-pop-out memory (DG90) ──

    @property
    def drawing_overlay(self):
        """The session's drawing fan-out surface (read-only primitives).

        Exposes exactly the one method ``TickerSession`` calls on an attached
        view — ``set_data(symbol, drawings, groups)`` — so a pop-out hosted on
        this engine attaches to the same D24 fan-out as the default engine's
        panel.
        """
        return self._drawing_surface

    def update_chart(self, bars: list) -> None:
        """``ChartPanel.update_chart`` under the view's own name (parity).

        ``TickerSession._sync_view`` and the pop-out's ``bars_refreshed`` slot
        call this name; the engine-neutral ``ChartView`` spelling is
        ``update_bars``. Both replace the whole series, so a pop-out renders
        the same bars it would on the default engine.
        """
        self.update_bars(bars)

    #: DG90: bytes budgeted per stored bar in this view's private copy.
    BAR_BYTES = 128
    #: DG90: bytes budgeted per transport op / logical index / wire item.
    OP_BYTES = 96

    def memory_bytes(self) -> dict:
        """DG90 account of this view's own memory, bucket by bucket.

        A pop-out owns a private copy of the series (``_bars`` /
        ``_plotted``), its logical index column, its study value arrays, its
        drawing wire items and — the one structure that grows with traffic —
        the bridge replay log (the transport replays it after a renderer
        restart). Reporting the buckets separately keeps a leak attributable
        instead of collapsing into one opaque number; the pop-out ledger
        aggregates ``total_bytes`` per window.
        """
        buckets = {
            "bars": len(self._bars) * self.BAR_BYTES,
            "plotted": len(self._plotted) * self.BAR_BYTES,
            "logical": len(self._logical) * self.OP_BYTES,
            "study_values": (sum(len(values) for values in
                                 self._study_overlays.values()) * 8),
            "drawing_items": len(self._drawing_items) * self.OP_BYTES,
            "op_log": 0,
        }
        counters: dict = {}
        try:
            buckets["op_log"] = len(self._bridge.replay_log()) * self.OP_BYTES
            counters = dict(self._bridge.counters())
        except Exception:
            # A closed (C++-deleted) view still reports its Python buckets.
            counters = {}
        return {
            "engine": self.ENGINE_NAME,
            "read_only": not self._editable,
            "bars": len(self._bars),
            "buckets": buckets,
            "total_bytes": sum(buckets.values()),
            "bridge": counters,
        }

    def release_resources(self) -> None:
        """Drop every per-view array on close (DG90: no pop-out leak).

        Called by the pop-out window after it detaches from the session: the
        private series copy, the study arrays and the per-channel replay logs
        go, and the offline host (if one was created) is scheduled for
        deletion. Idempotent — a second call is a no-op.
        """
        self._bars = []
        self._plotted = []
        self._logical = []
        self._cmap = None
        self._study_overlays = {}
        self._study_cache.invalidate()
        self._study_sig = None
        self._study_log = []
        self._study_envelopes = []
        self._interaction_log = []
        self._interaction_envelopes = []
        self._alarm_log = []
        self._alarm_envelopes = []
        self._drawing_items = []
        self._drawing_log = []
        self._drawing_envelopes = []
        self._overlay_log = []
        self._overlay_envelopes = []
        bridge = getattr(self, "_bridge", None)
        for name in ("_op_log", "_queued", "_outbox", "_live_buf"):
            bucket = getattr(bridge, name, None)
            if bucket is not None:
                try:
                    bucket.clear()
                except Exception:
                    pass
        host = self._host
        if host is not None:
            self._host = None
            try:
                host.deleteLater()
            except Exception:
                pass

    # ── private ─────────────────────────────────────────────────────

    def _tick_candle_cols(self, bar) -> dict:
        """Single-element candle columns for one live tick.

        ``ts`` is the bar's real UTC time (Q-20) — the same unit ``set_series``
        sends. Heikin-Ashi ticks are recomputed over the current plotted tail
        (O(n), obviously correct; the bridge coalesce window bounds how often
        ticks cross). Every other mode sends the tick's own OHLC.
        """
        ts = int(bar.ts)
        if self._mode == "heikin" and self._plotted:
            cmap = self._cmap
            base = chart_model.candle_display_rows(self._plotted[:-1], cmap)
            last_dx = cmap.to_display(bar.ts) if cmap is not None else bar.ts
            base.append((last_dx, bar.open, bar.high, bar.low, bar.close))
            ha = chart_model.heikin_ashi(base)[-1]
            _t, o, h, lo, c = ha
            return {"ts": [ts], "open": [o], "high": [h],
                    "low": [lo], "close": [c]}
        return {"ts": [ts], "open": [bar.open], "high": [bar.high],
                "low": [bar.low], "close": [bar.close]}
