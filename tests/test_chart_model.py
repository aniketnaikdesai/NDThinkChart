"""tests/test_chart_model.py — the shared chart model's own values (P6-03).

Proves the plotted chart values come from ``services/chart_model.py``:

* plotted-index filtering + ``floor_bar_budget`` asserted against the model
  directly;
* study full/incremental equivalence through the model's cache;
* the Heikin-Ashi recurrence;
* the residue scan (Qt-free model; the LWC view renders from the shared model).

Q-27 retires the deleted ChartPanel probes: the panel value path and its
delegation spies, the pyqtgraph item-layer oracle comparison and the
pyqtgraph-present residue assertion went with that engine. What is left is
the model-direct contract itself.
"""

import ast
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from services import chart_model
from services.backfill_service import floor_bar_budget as backfill_budget
from data.models import Bar

_ET = ZoneInfo("America/New_York")
# Friday 2026-10-23 — a plain trading day (no holiday edge).
_DAY = datetime(2026, 10, 23, tzinfo=_ET)


def _ts(hour: int, minute: int) -> int:
    return int(_DAY.replace(hour=hour, minute=minute).timestamp())


def _bar(ts: int, i: int) -> Bar:
    base = 500.0 + i * 0.5
    o, c = (base, base + 0.2) if i % 2 == 0 else (base + 0.2, base)
    return Bar("SPY", "5 mins", ts, o, base + 0.5, base - 0.5, c,
               1000.0 + i * 10.0)


def _rth_bars(n: int = 20):
    """Clearly-inside-RTH 5-min bars starting 10:00 ET (no boundary edge)."""
    start = _ts(10, 0)
    return [_bar(start + i * 300, i) for i in range(n)]


def _mixed_bars():
    """Pre-market + RTH + post-market bars for the display filter."""
    specs = [(4, 5), (8, 0), (9, 0)]  # outside RTH
    specs += [(10, 0), (10, 5), (12, 0), (15, 30)]  # inside RTH
    specs += [(16, 5), (18, 0), (20, 30)]  # outside RTH
    return [_bar(_ts(h, m), i) for i, (h, m) in enumerate(specs)]


# ── T11: plotted-index filtering + floor_bar_budget ──────────────────────────

def test_plotted_index_filtering_against_model():
    bars = _mixed_bars()
    rth_idx = [3, 4, 5, 6]
    # RTH-only with Ext Hours OFF, everything with ON.
    assert chart_model.plotted_index_rows(bars, "5 mins", False) == rth_idx
    assert chart_model.plotted_index_rows(bars, "5 mins", True) == list(range(len(bars)))
    assert chart_model.plotted_index_rows([], "5 mins", False) == []
    # Single-bar predicate agrees with the row filter.
    assert all(chart_model.is_bar_plotted(bars[i], "5 mins", False)
               for i in rth_idx)
    assert not any(chart_model.is_bar_plotted(bars[i], "5 mins", False)
                   for i in (0, 1, 2, 7, 8, 9))


def test_floor_bar_budget_is_the_model_budget():
    # The model re-exports the one budget implementation (identity, not a copy).
    assert chart_model.floor_bar_budget is backfill_budget
    for tf, ext in (("1 min", True), ("1 min", False), ("5 mins", True),
                    ("1 hour", False), ("1 day", True)):
        assert chart_model.floor_bar_budget(tf, ext) == backfill_budget(tf, ext)


def test_study_full_incremental_equivalence():
    bars = _rth_bars(40)
    studies = [{"type": "sma", "params": {"period": 5}, "enabled": True},
               {"type": "rsi", "params": {"period": 14}, "enabled": True},
               {"type": "bollinger", "params": {"period": 10, "std_dev": 2.0},
                "enabled": True},
               {"type": "macd", "params": {}, "enabled": True}]
    cache = chart_model.StudyCache()
    full_vals, _ = chart_model.compute_study_values(bars, studies, cache,
                                                    "SPY", "5 mins")
    cache.set("SPY", "5 mins", studies,
              {"n_bars": len(bars), "last_ts": bars[-1].ts,
               "values": {k: list(v) for k, v in full_vals.items()},
               "states": chart_model.study_values_full(bars, studies)[1]})
    extra = _bar(bars[-1].ts + 300, 999)
    inc_vals, _ = chart_model.compute_study_values(bars + [extra], studies,
                                                   cache, "SPY", "5 mins")
    ref_vals, _ = chart_model.study_values_full(bars + [extra], studies)
    assert inc_vals.keys() == ref_vals.keys()
    for key in ref_vals:
        assert inc_vals[key] == pytest.approx(ref_vals[key]), key


def test_heikin_ashi_recurrence():
    rows = [(float(i), 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i)
            for i in range(10)]
    # Spot-check the recurrence: first open seeds from (o+c)/2.
    t, ha_o, ha_h, ha_l, ha_c = chart_model.heikin_ashi(rows)[0]
    assert ha_c == pytest.approx((100.0 + 101.0 + 99.0 + 100.5) / 4)
    assert ha_o == pytest.approx((100.0 + 100.5) / 2)
    assert ha_h == pytest.approx(101.0)
    assert ha_l == pytest.approx(99.0)


def test_volume_values_owned_by_model():
    assert chart_model.format_volume_tick(500_000) == "500.0K"
    assert chart_model.format_volume_tick(1_500_000) == "1.5M"
    assert chart_model.nice_volume_max(0) == 100.0
    assert chart_model.visible_volume_ceiling(50.0) == pytest.approx(55.0)
    assert chart_model.visible_volume_ceiling(0.0) == 100.0
    assert chart_model.visible_max_volume([1.0, 2.0, 3.0], [10.0, 50.0, 5.0],
                                           1.5, 2.5) == 50.0
    assert chart_model.visible_max_volume([1.0], [7.0], 5.0, 9.0) == 0.0
    assert chart_model.base_candle_half_width(10.0) == pytest.approx(3.25)
    assert chart_model.base_candle_half_width(None) == 0.25
    assert chart_model.median_spacing([1.0, 3.0, 5.0, 9.0]) == 2.0
    assert chart_model.median_spacing([1.0]) is None


# ── T13: residue scan over this batch's footprint ────────────────────────────

_THIS_TASK_FILES = ("services/chart_model.py", "ui/lwc_view.py")

_FORBIDDEN_TOKENS = (
    "placeOrder", "cancelOrder", "reqGlobalCancel", "UserOrder",
    "OrderRateLimiter", "order_limiter", "MAX_ORDER_NOTIONAL",
    "CREATE TABLE", "ALTER TABLE", "DROP COLUMN",
    "openOrder", "orderStatus", "execDetails",
)

_DOCK_WATCHLIST_TOKENS = ("WatchlistPanel", "dock_layout", "watchlist_panel")


def _imports_of(path: Path) -> list:
    tree = ast.parse(path.read_text())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
            mods.extend(f"{node.module}.{a.name}" if node.module else a.name
                        for a in node.names)
    return mods


def test_model_is_qt_free_and_view_renders_from_it():
    model_imports = _imports_of(Path("services/chart_model.py"))
    for mod in model_imports:
        top = mod.split(".")[0]
        assert top not in ("PyQt6", "PyQt5", "pyqtgraph", "Qt"), mod
    view_imports = _imports_of(Path("ui/lwc_view.py"))
    assert any("chart_model" in m for m in view_imports), \
        "LwcChartView must import the shared model"


def test_no_out_of_scope_residue():
    for rel in _THIS_TASK_FILES:
        src = Path(rel).read_text()
        assert "from ibkr" not in src and "import ibkr" not in src, rel
        for tok in _FORBIDDEN_TOKENS:
            assert tok not in src, f"{rel}: forbidden token {tok!r}"
        for tok in _DOCK_WATCHLIST_TOKENS:
            assert tok not in src, f"{rel}: out-of-scope token {tok!r}"
