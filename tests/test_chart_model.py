"""tests/test_chart_model.py — P6-03 delegation probe (P6-T03-T11/T13).

Proves every plotted chart value comes from ``services/chart_model.py`` and
that ``ChartPanel`` merely delegates (zero behaviour change):

* plotted-index filtering + ``floor_bar_budget`` asserted against the model
  directly, plus spies proving the panel's value paths call into the model
  (identical inputs -> identical plotted outputs on both paths);
* study full/incremental equivalence through the model's cache;
* Heikin-Ashi equivalence with the item layer's transform;
* the renderer-only residue scan (no ibkr/schema/service-signature/
  watchlist/dock/order-code change; Qt-free model; pyqtgraph present+default).

D42/S14 convention: delegation fixtures drive upper-case symbols.
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


@pytest.fixture(scope="module")
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def panel(qapp):
    from ui.chart_panel import ChartPanel
    p = ChartPanel()
    p.set_symbol("SPY")
    p.set_timeframe("5 mins")
    yield p
    p.close()


class _Spy:
    def __init__(self, fn):
        self.fn = fn
        self.calls: list = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.fn(*args, **kwargs)


# ── T11: plotted-index filtering + floor_bar_budget ──────────────────────────

def test_plotted_index_filtering_against_model(panel):
    bars = _mixed_bars()
    rth_idx = [3, 4, 5, 6]
    # Model directly: RTH-only with Ext Hours OFF, everything with ON.
    assert chart_model.plotted_index_rows(bars, "5 mins", False) == rth_idx
    assert chart_model.plotted_index_rows(bars, "5 mins", True) == list(range(len(bars)))
    assert chart_model.plotted_index_rows([], "5 mins", False) == []
    # Single-bar predicate agrees with the row filter.
    assert all(chart_model.is_bar_plotted(bars[i], "5 mins", False)
               for i in rth_idx)
    assert not any(chart_model.is_bar_plotted(bars[i], "5 mins", False)
                   for i in (0, 1, 2, 7, 8, 9))
    # Panel path: identical inputs -> identical plotted outputs.
    panel._ext_hours = False
    panel.update_chart(bars)
    assert panel._plotted_indices == rth_idx
    assert panel._plotted_indices == chart_model.plotted_index_rows(
        panel._bars, panel._current_timeframe, False)
    assert [b.ts for b in panel._plotted_bars] == [bars[i].ts for i in rth_idx]


def test_floor_bar_budget_delegated(panel, monkeypatch):
    # The model re-exports the one budget implementation (identity, not a copy).
    assert chart_model.floor_bar_budget is backfill_budget
    for tf, ext in (("1 min", True), ("1 min", False), ("5 mins", True),
                    ("1 hour", False), ("1 day", True)):
        assert chart_model.floor_bar_budget(tf, ext) == backfill_budget(tf, ext)
    # The panel's live-bar trim calls into the model for the budget.
    calls: list = []

    def capped_budget(timeframe: str, ext_hours: bool) -> int:
        calls.append((timeframe, ext_hours))
        return 5

    monkeypatch.setattr(chart_model, "floor_bar_budget", capped_budget)
    bars = _rth_bars(8)
    panel._ext_hours = True
    panel.update_chart(bars)
    new = _bar(bars[-1].ts + 300, 99)
    panel.update_last_bar(new, False)
    assert calls == [("5 mins", True)], \
        "update_last_bar must take its budget from chart_model.floor_bar_budget"
    # The trim used the model's number (9 bars -> budget 5).
    assert len(panel._bars) == 5


def test_panel_value_paths_call_into_model(panel, monkeypatch):
    spies = {}
    for name in ("plotted_index_rows", "collapse_for_bars", "plot_arrays",
                 "candle_display_rows", "volume_display_columns",
                 "visible_max_volume", "visible_volume_ceiling",
                 "compute_study_values", "median_spacing",
                 "base_candle_half_width", "trailing_bars"):
        spy = _Spy(getattr(chart_model, name))
        spies[name] = spy
        monkeypatch.setattr(chart_model, name, spy)
    panel.set_studies([{"type": "sma", "params": {"period": 5},
                        "enabled": True}])
    bars = _rth_bars(30)
    panel._ext_hours = True
    panel.update_chart(bars)
    # Full-load path delegates everything.
    for name in ("plotted_index_rows", "collapse_for_bars", "plot_arrays",
                 "candle_display_rows", "volume_display_columns",
                 "visible_max_volume", "visible_volume_ceiling",
                 "compute_study_values", "median_spacing",
                 "base_candle_half_width"):
        assert spies[name].calls, f"update_chart never called model.{name}"
    # Identical inputs -> identical plotted outputs on both paths.
    assert panel._plotted_indices == backfill_free_plotted(bars)
    assert panel._plot_xs == [panel._to_display(b.ts) for b in panel._plotted_bars]
    assert panel._plot_vols == [float(b.volume) for b in panel._plotted_bars]
    history = panel._plotted_bars[:-1]
    assert list(panel.candlestick._raw_data) == chart_model.candle_display_rows(
        history, panel._collapse_map)
    # New-candle path delegates the incremental study computation.
    before = len(spies["compute_study_values"].calls)
    panel.update_last_bar(_bar(bars[-1].ts + 300, 100), True)
    assert len(spies["compute_study_values"].calls) == before + 1


def backfill_free_plotted(bars):
    """Expected plotted indices computed straight from the model."""
    return chart_model.plotted_index_rows(bars, "5 mins", True)


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


def test_heikin_ashi_matches_item_layer():
    rows = [(float(i), 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i)
            for i in range(10)]
    from ui.candlestick_item import _compute_heikin
    assert chart_model.heikin_ashi(rows) == _compute_heikin(rows)
    # Spot-check the recurrence: first open seeds from (o+c)/2.
    t, ha_o, ha_h, ha_l, ha_c = chart_model.heikin_ashi(rows)[0]
    assert ha_c == pytest.approx((100.0 + 101.0 + 99.0 + 100.5) / 4)
    assert ha_o == pytest.approx((100.0 + 100.5) / 2)


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


# ── T13: residue scan over this task's footprint ────────────────────────────

_THIS_TASK_FILES = ("services/chart_model.py", "ui/chart_panel.py",
                    "tests/test_chart_model.py", "docs/lwc_parity_matrix.md")

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


def test_model_is_qt_free_and_panel_keeps_pyqtgraph():
    model_imports = _imports_of(Path("services/chart_model.py"))
    for mod in model_imports:
        top = mod.split(".")[0]
        assert top not in ("PyQt6", "PyQt5", "pyqtgraph", "Qt"), mod
    panel_imports = _imports_of(Path("ui/chart_panel.py"))
    assert any(m.split(".")[0] == "pyqtgraph" for m in panel_imports), \
        "pyqtgraph must stay present and default through Phase 10"
    assert any("chart_model" in m for m in panel_imports), \
        "ChartPanel must import the shared model"


def test_no_out_of_scope_residue():
    for rel in ("services/chart_model.py", "ui/chart_panel.py"):
        src = Path(rel).read_text()
        assert "from ibkr" not in src and "import ibkr" not in src, rel
        for tok in _FORBIDDEN_TOKENS:
            assert tok not in src, f"{rel}: forbidden token {tok!r}"
        for tok in _DOCK_WATCHLIST_TOKENS:
            assert tok not in src, f"{rel}: out-of-scope token {tok!r}"
