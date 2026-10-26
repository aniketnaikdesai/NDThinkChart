"""services/chart_model.py — Qt-free shared chart value model (P6-03 / Phase 1b).

The single value source for every plotted chart value: plotted-index
filtering (RTH display filter), the floor-aware bar budget, whitespace
derivation (display-x collapse), study computation + cache, Heikin-Ashi,
and volume formatting/ceilings. ``ui/chart_panel.py`` delegates to this
module with zero behaviour change — every function below is a verbatim move
of the computation the panel previously inlined (provenance noted per
symbol), so the pre-D47 chart suites stay green unmodified.

No PyQt6 / pyqtgraph / Qt import may ever appear in this module; importing
it needs no ``QApplication``. Anything needing a view (ViewBox ranges,
pixels-per-second) stays in the panel, which passes plain data in.
"""

from __future__ import annotations

import hashlib
from bisect import bisect_left, bisect_right
from typing import Sequence

from data.bar_aggregator import TIMEFRAME_SECONDS
from services.backfill_service import floor_bar_budget  # noqa: F401 — re-exported: the single budget source
from services.indicator_service import (
    bollinger_update,
    ema_update,
    macd_update,
    rsi_update,
    sma_update,
    vwap_update,
)
from services.market_calendar import session_windows
from services.time_collapse_service import TimeCollapseMap, build_collapse_map


# ── Plotted-index filtering (from ChartPanel._compute_plotted_indices /
#    ChartPanel._new_bar_is_plotted) ───────────────────────────────────────────

def plotted_index_rows(bars: Sequence, timeframe: str | None, ext_hours: bool) -> list:
    """Return indices into ``bars`` for the bars to plot.

    With Ext Hours ON every bar is plotted. With Ext Hours OFF (RTH) only
    RTH bars are plotted (``AC-D21.4.3``) — a *display* filter; the input
    list (and every ``Bar.ts``) is untouched. Indices (not objects) are
    returned so an in-place intra-bar update of the forming bar is reflected
    in the plotted set.
    """
    if ext_hours or not bars:
        return list(range(len(bars)))
    if timeframe is None or timeframe not in TIMEFRAME_SECONDS:
        return list(range(len(bars)))
    period = TIMEFRAME_SECONDS[timeframe]
    return [
        i for i, b in enumerate(bars)
        if session_windows(int(b.ts), int(b.ts) + period, False)
    ]


def is_bar_plotted(bar, timeframe: str | None, ext_hours: bool) -> bool:
    """The single-bar predicate behind :func:`plotted_index_rows`."""
    if ext_hours:
        return True
    if timeframe is None or timeframe not in TIMEFRAME_SECONDS:
        return True
    period = TIMEFRAME_SECONDS[timeframe]
    return bool(session_windows(int(bar.ts), int(bar.ts) + period, False))


# ── Whitespace derivation (from ChartPanel._rebuild_collapse_map) ────────────

def collapse_for_bars(bars: Sequence, timeframe: str | None,
                      ext_hours: bool) -> TimeCollapseMap | None:
    """Build the display-x collapse map for ``bars`` (None when inapplicable).

    The map is timeframe-dependent; an unknown timeframe (or ``None``) yields
    ``None`` (identity display), exactly as the panel's rebuild did.
    """
    if timeframe is None or timeframe not in TIMEFRAME_SECONDS:
        return None
    return build_collapse_map(bars, timeframe, ext_hours)


def _to_display(collapse_map: TimeCollapseMap | None, ts) -> float:
    """Map an original timestamp to display-x (identity when no map)."""
    if collapse_map is None:
        return ts
    return collapse_map.to_display(ts)


def display_xs(bars: Sequence, collapse_map: TimeCollapseMap | None) -> list:
    """Display-x coordinates for ``bars`` in order (bisection source)."""
    return [_to_display(collapse_map, b.ts) for b in bars]


def plot_arrays(bars: Sequence,
                collapse_map: TimeCollapseMap | None) -> tuple[list, list]:
    """Cached display-x / volume arrays aligned with the plotted bars.

    The bisection targets for the crosshair and the volume ceiling (no O(n)
    scans on per-frame paths). From ``ChartPanel._sync_plot_arrays``.
    """
    to_display = collapse_map.to_display if collapse_map is not None else None
    if to_display is None:
        return ([b.ts for b in bars], [float(b.volume) for b in bars])
    return ([to_display(b.ts) for b in bars],
            [float(b.volume) for b in bars])


# ── Candle / volume display rows (from ChartPanel._refresh_candles) ─────────

BULL_COLOR = '#34d399'
BEAR_COLOR = '#f87171'


def candle_display_rows(bars: Sequence,
                        collapse_map: TimeCollapseMap | None) -> list:
    """``(display_x, open, high, low, close)`` rows for ``bars`` in order."""
    return [(_to_display(collapse_map, b.ts), b.open, b.high, b.low, b.close)
            for b in bars]


def volume_display_columns(bars: Sequence, collapse_map: TimeCollapseMap | None
                           ) -> tuple[list, list, list]:
    """``(xs, heights, colors)`` volume columns for ``bars`` in order."""
    xs, heights, colors = [], [], []
    for b in bars:
        xs.append(_to_display(collapse_map, b.ts))
        heights.append(float(b.volume))
        colors.append(BULL_COLOR if b.close >= b.open else BEAR_COLOR)
    return xs, heights, colors


# ── Candle geometry (from ChartPanel._compute_candle_half_width) ─────────────

def median_spacing(display_xs: Sequence) -> float | None:
    """Median of adjacent display-x spacings (None for < 2 points)."""
    if len(display_xs) < 2:
        return None
    diffs = sorted(display_xs[i] - display_xs[i - 1]
                   for i in range(1, len(display_xs)))
    return diffs[len(diffs) // 2]


def base_candle_half_width(median_diff: float | None) -> float:
    """Base half-width: 32.5 % of the median spacing (35 % gap, the D6
    formula); the ``0.25`` single-bar fallback (matches ``CandlestickItem``).
    The D42/S13 density cap itself still applies at generation time through
    the shared ``capped_body_half_width`` helper at the host / item layer.
    """
    if median_diff is None:
        return 0.25
    return median_diff * 0.325


# ── Volume formatting + ceilings (from chart_panel module level +
#    ChartPanel._recompute_visible_volume_range) ──────────────────────────────

# D8 / RG-002: the single pinned volume nice-number family.
VOLUME_NICE_MANTISSAS = (1.0, 1.5, 2.0, 2.5, 5.0, 7.5)
VOLUME_NICE_FLOOR = 100.0


def volume_nice_family(max_exponent: int = 12) -> tuple:
    """Pinned volume family ``1 / 1.5 / 2 / 2.5 / 5 / 7.5 x 10^k`` (RG-002).

    Generated from ``1 x 10^2`` — the required ``100`` floor (AC-D8.4) —
    upward, so the sequence scales with ``k`` and has no fixed ceiling.
    """
    values: list = []
    for k in range(2, max_exponent + 1):
        base = 10.0 ** k
        for mantissa in VOLUME_NICE_MANTISSAS:
            values.append(mantissa * base)
    return tuple(values)


def nice_volume_max(max_vol: float) -> float:
    """Smallest pinned-family value ``>= max_vol * 1.1`` (floor ``100``).

    Retained for the all-zero ``100`` floor (AC-D8.4) and as the pinned-family
    fixture the volume test modules exercise directly; the *live* volume pane
    ceiling is ``1.10 x max(visible volume)`` via
    :func:`visible_volume_ceiling`.
    """
    if max_vol <= 0:
        return VOLUME_NICE_FLOOR
    target = float(max_vol) * 1.1
    if target <= VOLUME_NICE_FLOOR:
        return VOLUME_NICE_FLOOR
    k = 2
    while True:
        base = 10.0 ** k
        for mantissa in VOLUME_NICE_MANTISSAS:
            value = mantissa * base
            if value >= target:
                return value
        k += 1


def format_volume_tick(value: float) -> str:
    """Format a volume-axis tick as ``500.0K`` / ``1.0M`` (AC-D8.3)."""
    v = float(value)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}K"
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


def visible_max_volume(xs: Sequence, vols: Sequence,
                       x0: float, x1: float) -> float:
    """Max volume of the bars whose display-x lies in ``[x0, x1]`` (bisected).

    From the D28.4 slice of ``_recompute_visible_volume_range`` — no O(n)
    scan on the per-frame pan/zoom path. ``0.0`` when nothing is visible.
    """
    lo = bisect_left(xs, x0)
    hi = bisect_right(xs, x1, lo=lo)
    return max(vols[lo:hi], default=0.0)


def visible_volume_ceiling(visible_max: float) -> float:
    """Volume Y ceiling for a visible max (D21.2 / AC-D21.2.1).

    ``1.10 x visible_max`` for any positive max — including the small band
    ``0 < visible_max <= 90.9`` (a second unconditional floor clamp would
    wrongly inflate those to 100; see ESC-028) — else ``VOLUME_NICE_FLOOR``.
    """
    if visible_max > 0.0:
        return visible_max * 1.1
    return VOLUME_NICE_FLOOR


# ── Heikin-Ashi (value transform; the item layer keeps rendering it) ─────────

def heikin_ashi(rows: Sequence) -> list:
    """Transform ``(t, o, h, l, c)`` rows to Heikin-Ashi ``(t, ha_o, ha_h,
    ha_l, ha_c)``. The single value source going forward (LWC phases use
    this); the pyqtgraph item keeps its identical local copy until P6-13.
    """
    result = []
    prev_ha_o, prev_ha_c = None, None
    for (t, o, h, l, c) in rows:
        ha_c = (o + h + l + c) / 4
        ha_o = ((prev_ha_o + prev_ha_c) / 2) if prev_ha_o is not None else (o + c) / 2
        ha_h = max(h, ha_o, ha_c)
        ha_l = min(l, ha_o, ha_c)
        result.append((t, ha_o, ha_h, ha_l, ha_c))
        prev_ha_o, prev_ha_c = ha_o, ha_c
    return result


# ── Studies + cache (from ChartPanel._StudyCache / _study_* — D28.4) ─────────
# Numeric studies are computed through the incremental ``*_update``
# functions (services/indicator_service.py), which exactly match the
# batch ``calculate_*`` tails. The full path feeds every bar once (building
# fresh states); the new-candle path shifts the cached arrays and
# computes only the new bar.

# Study types with incremental numeric computation (overlay studies —
# rth_gaps/vix_sd/ict — render directly and are never cached).
INCREMENTAL_STUDIES = frozenset(
    {"sma", "ema", "ema2", "vwap", "bollinger", "rsi", "macd"})


class StudyCache:
    """Cache for computed study values keyed by (symbol, timeframe, studies_hash).

    Stores computed arrays so that on intra-bar ticks or new candles,
    only the latest values need recomputation for the new bar.
    """

    def __init__(self):
        self._cache: dict = {}

    def _studies_hash(self, studies: list) -> str:
        """Compute a hash of the enabled study configurations."""
        enabled = [(s["type"], s.get("params", {}))
                   for s in studies if s.get("enabled")]
        return hashlib.md5(str(enabled).encode()).hexdigest()[:16]

    def _key(self, symbol: str, timeframe: str, studies_hash: str) -> str:
        return f"{symbol}:{timeframe}:{studies_hash}"

    def get(self, symbol: str, timeframe: str, studies: list) -> dict | None:
        """Return cached study arrays if valid for current studies."""
        h = self._studies_hash(studies)
        k = self._key(symbol, timeframe, h)
        return self._cache.get(k)

    def set(self, symbol: str, timeframe: str, studies: list, data: dict):
        h = self._studies_hash(studies)
        k = self._key(symbol, timeframe, h)
        self._cache[k] = data

    def invalidate(self, symbol: str | None = None, timeframe: str | None = None):
        """Invalidate cache entries. If symbol/timeframe is None, clear all."""
        if symbol is None and timeframe is None:
            self._cache.clear()
        else:
            prefix = f"{symbol or '*'}:{timeframe or '*'}"
            to_del = [k for k in self._cache if k.startswith(prefix)]
            for k in to_del:
                self._cache.pop(k, None)


def study_key(stype: str, idx: int) -> str:
    """Per-study-instance cache key (two SMAs with different periods must
    not collide)."""
    return f"{stype}:{idx}"


def study_update_one(stype: str, params: dict, state: dict, bar) -> dict:
    """Advance one study's incremental state with one bar.

    Returns {suffix: value}; the empty suffix is the study's primary
    series (e.g. "bollinger:0" -> upper, "bollinger:0_mid" -> middle).
    """
    if stype == "sma":
        return {"": sma_update(state, bar.close, params.get("period", 20))}
    if stype in ("ema", "ema2"):
        return {"": ema_update(state, bar.close, params.get("period", 9))}
    if stype == "vwap":
        return {"": vwap_update(state, bar.high, bar.low, bar.close,
                                bar.volume, bar.ts)}
    if stype == "bollinger":
        upper, mid, lower = bollinger_update(
            state, bar.close,
            params.get("period", 20), params.get("std_dev", 2.0))
        return {"": upper, "_mid": mid, "_lower": lower}
    if stype == "rsi":
        return {"": rsi_update(state, bar.close, params.get("period", 14))}
    if stype == "macd":
        m, s = macd_update(
            state, bar.close,
            params.get("fast", 12), params.get("slow", 26),
            params.get("signal", 9))
        return {"": m, "_signal": s}
    return {}


def study_values_full(bars: Sequence, studies: list) -> tuple:
    """Compute every numeric study over all bars, building fresh states."""
    all_vals: dict = {}
    states: dict = {}
    for idx, study in enumerate(studies):
        if not study.get("enabled"):
            continue
        stype = study["type"]
        if stype not in INCREMENTAL_STUDIES:
            continue  # overlay study — rendered, not cached
        params = study.get("params", {})
        key = study_key(stype, idx)
        state: dict = {}
        series: dict = {}
        for bar in bars:
            for suffix, value in study_update_one(
                    stype, params, state, bar).items():
                series.setdefault(suffix, []).append(value)
        for suffix, vals in series.items():
            all_vals[f"{key}{suffix}"] = vals
        states[key] = state
    return all_vals, states


def study_values_incremental(cached: dict, studies: list, new_bar) -> tuple:
    """Shift cached arrays and compute only the new bar (D28.4)."""
    all_vals = {k: list(v) for k, v in cached["values"].items()}
    states = cached["states"]
    for idx, study in enumerate(studies):
        if not study.get("enabled"):
            continue
        stype = study["type"]
        key = study_key(stype, idx)
        state = states.get(key)
        if state is None:
            continue  # overlay study — rendered, not cached
        for suffix, value in study_update_one(
                stype, study.get("params", {}), state, new_bar).items():
            all_vals[f"{key}{suffix}"].append(value)
    return all_vals, states


def compute_study_values(bars: Sequence, studies: list, cache: StudyCache,
                         symbol: str, timeframe: str) -> tuple:
    """Full or incremental study computation (D28.4).

    The incremental path applies when the cache holds this exact study
    set for the series ending at the previous bar (n_bars == len-1 and
    the second-to-last timestamp matches) — i.e. exactly one new candle
    arrived. Anything else (fresh load, timeframe/study change, history
    rewrite) takes the full path.
    """
    n = len(bars)
    cached = cache.get(symbol, timeframe or "", studies)
    if (cached is not None and n >= 2
            and cached.get("n_bars") == n - 1
            and cached.get("last_ts") == bars[-2].ts):
        return study_values_incremental(cached, studies, bars[-1])
    return study_values_full(bars, studies)


def trailing_bars(bars: Sequence, n: int) -> list:
    """Last ``n`` bars (the trailing window overlay studies render over).

    D28.4: ICT concepts are computed over a trailing window, not the full
    series — the overlay renders window-relative bar indices, so the window
    itself is passed as the bar list (indices stay consistent by
    construction).
    """
    return list(bars[-n:])
