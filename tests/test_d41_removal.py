"""D41 Phase-3 removal guards (AC-D41.1 / .2 / .3 / .5).

Three independent kinds of guard, because "the feature is gone" can fail in
three different ways:

1. **module / identifier absence** — the nine deleted modules and five deleted
   suites have no spec/source, and the removed classes, members and
   integration-surface tokens appear nowhere in the source outside a small
   documented allow-list;
2. **UI absence** — a real offscreen ``MainWindow`` exposes no footprint /
   depth / auction control, attribute or signal, while the retained controls
   still exist and render;
3. **request absence** — driving the app (connect + chart load + the remaining
   controls + a symbol switch) issues no ``reqMktDepth`` /
   ``cancelMktDepth`` / ``reqHistoricalTicks`` / ``reqTickByTickData`` and no
   generic-ticks request carrying the removed ``"225"`` auction need, while the
   D38 S0 line and the watchlist/RT lines still issue.

The token scan is **AST-based** on purpose: it sees identifiers and *string
constants*, so a stale live lookup is caught, while explanatory prose in a
comment or docstring is not. That is what lets the re-pointed suites document
what they replaced without tripping their own guard.
"""

import ast
import importlib.util
from pathlib import Path

import pytest

from ibkr.client import IBApiClient

_REPO = Path(__file__).resolve().parent.parent
_SOURCE_DIRS = ("ui", "services", "data", "ibkr", "config")

#: The nine modules D41 deleted.
_DELETED_MODULES = (
    "ui.footprint_item",
    "services.footprint_service",
    "data.footprint_cache",
    "ibkr.tick_history",
    "ui.depth_heatmap_item",
    "services.depth_heatmap",
    "ui.active_trader_panel",
    "ibkr.market_depth",
    "ibkr.order_book",
)

#: The five suites D41 deleted.
_DELETED_SUITES = (
    "tests/test_d36_footprint.py",
    "tests/test_d37_microstructure.py",
    "tests/test_market_depth.py",
    "tests/test_order_entry_side.py",
    "tests/test_order_entry_mkt.py",
)

#: Removed classes / factories / members / integration-surface tokens. Any of
#: these appearing as an identifier (or a string constant) in the source tree
#: means a removal is incomplete.
_REMOVED_NAMES = frozenset({
    # classes + factories + module-level helpers
    "FootprintItem", "FootprintService", "FootprintCache", "TickHistoryManager",
    "DepthHeatmapItem", "DepthHeatmapService", "MarketDepthManager",
    "OrderBookLevel", "ActiveTraderPanel", "on_depth_callback",
    "resolve_footprint_contract", "is_cacheable",
    # ChartPanel render layers + control cluster
    "footprint_static", "footprint_live", "footprint_toggled",
    "footprint_viewport_changed", "depth_toggled", "depth_heatmap_item",
    "_fp_enabled_ui", "_fp_viewport_timer", "_fp_queue_viewport_sync",
    "_fp_emit_viewport", "refresh_footprint", "_position_fp_controls",
    "_position_d37_controls", "_on_depth_toggled", "_on_imb_clicked",
    "_on_auction_clicked", "_on_depth_refresh", "bind_d37_session",
    "unbind_d37_session", "_on_auction_tick", "update_auction_chip",
    "_in_auction_window", "set_depth_state", "depth_enabled", "_d37_session",
    "_imbalance_n", "_depth_state_text", "_auction_state", "_depth_toggle",
    "_imb_label", "_auction_chip",
    # TickerSession
    "ensure_depth_subscribed", "release_depth", "_cancel_depth",
    "_reissue_depth", "_rebind_depth_req_id", "on_depth_update",
    "on_depth_error", "depth_imbalance", "depth_req_id", "_depth_state",
    "_depth_roll_timer", "footprint_enable", "footprint_resync",
    "footprint_disable", "footprint_snapshot", "on_fp_error",
    "on_fp_reconnect", "on_fp_disconnect", "on_fp_ticks_bid_ask",
    "on_fp_ticks_last", "sync_footprint_viewport", "auction_state",
    # NOTE: the session's auction S0 ingress methods ``on_tick_price`` /
    # ``on_tick_size`` are deliberately NOT listed -- the retained
    # WatchlistPanel and MainWindow both define methods of those names, so a
    # token match would be a false positive. Their removal is proven by the
    # TickerSession attribute probes in P1-T10's suite instead.
    # MainWindow + bridge + client + subscription surface
    "update_mkt_depth", "historical_ticks_bid_ask", "historical_ticks_last",
    "historicalTicksBidAsk", "historicalTicksLast", "reqMktDepth",
    "cancelMktDepth", "reqHistoricalTicks", "reqTickByTickData",
    "updateMktDepth", "updateMktDepthL2", "DEPTH_HEATMAP",
    "set_depth_manager", "_on_mkt_depth", "_subscribe_dom", "_on_dom_toggled",
    "_on_order_place_requested", "_place_order", "dom_btn",
    "right_dock_container", "_right_dock_layout", "_depth_req_id",
})

#: Documented allow-list. Each entry is KEEP-list substrate that shares a name
#: with removed machinery.
_ALLOWED_ANYWHERE = frozenset({
    "footprint_cache_key",  # KEEP (D39): the burst-alarm tape key, retained verbatim
    "queue_depth",          # NewsManager's own queue-depth attribute
})
#: Allowed only inside the named file.
_ALLOWED_IN_FILE = {
    "has_subscription": {"ibkr/subscription_manager.py"},
}

#: In tests, the ibapi request-method names are the RECORDING surface the
#: absence guards must call, so they are legitimately present there. The
#: app-internal removals are still forbidden.
_IBAPI_SURFACE = frozenset({
    "reqMktDepth", "cancelMktDepth", "reqHistoricalTicks", "reqTickByTickData",
    "updateMktDepth", "updateMktDepthL2", "historicalTicksBidAsk",
    "historicalTicksLast",
})


def _identifiers(path: Path) -> set[str]:
    """Every identifier the module mentions, plus its string constants.

    Comments are invisible to ``ast`` by construction; docstrings appear as
    string constants and are therefore included, which is intended for the
    source scan (a stale *lookup* is usually written as a literal).
    """
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            names.add((node.asname or node.name).split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add(node.value)
    return names


def _source_files():
    for d in _SOURCE_DIRS:
        root = _REPO / d
        if root.is_dir():
            yield from sorted(root.rglob("*.py"))


def test_deleted_modules_and_suites_have_no_spec_or_source():
    """P1-T60-T11 (a) / AC-D41.3: the nine modules and five suites are gone."""
    for mod in _DELETED_MODULES:
        assert importlib.util.find_spec(mod) is None, f"{mod} still resolvable"
    for rel in _DELETED_SUITES:
        assert not (_REPO / rel).exists(), f"{rel} still present"


def test_no_removed_token_survives_in_source():
    """P1-T60-T11 (b) / AC-D41.3: the token scan over the source tree.

    Allow-list: ``footprint_cache_key`` (KEEP, D39), ``queue_depth``
    (NewsManager's) and ``has_subscription`` scoped to
    ``ibkr/subscription_manager.py``.
    """
    offences: list[str] = []
    for path in _source_files():
        rel = path.relative_to(_REPO).as_posix()
        names = _identifiers(path)
        for name in sorted(names):
            if name in _ALLOWED_ANYWHERE:
                continue
            scoped = _ALLOWED_IN_FILE.get(name)
            if scoped is not None and rel in scoped:
                continue
            if name in _REMOVED_NAMES:
                offences.append(f"{rel}: {name!r}")
            # string constants may be longer than the bare token
            else:
                for token in _REMOVED_NAMES:
                    if token in name and name != token:
                        offences.append(f"{rel}: {name!r} contains {token!r}")
                        break
    assert not offences, (
        "removed D41 tokens still present in source:\n  " + "\n  ".join(offences))


def test_no_removed_app_identifier_in_tests():
    """P1-T60-T11 (c) / AC-D41.3: the re-pointed suites use no removed API.

    The ibapi request-method names are excluded: they are the recording surface
    the request-absence guard below must call. Prose in comments/docstrings is
    out of scope by construction (identifiers only). This file itself is
    skipped: it *is* the token list.
    """
    offences: list[str] = []
    for path in sorted((_REPO / "tests").glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        rel = path.relative_to(_REPO).as_posix()
        names = _identifiers(path)
        for name in sorted(names):
            if name in _IBAPI_SURFACE or name in _ALLOWED_ANYWHERE:
                continue
            if name in _REMOVED_NAMES:
                offences.append(f"{rel}: {name!r}")
    assert not offences, (
        "removed D41 identifiers still used in tests:\n  "
        + "\n  ".join(offences))


# ---------------------------------------------------------------------------
# UI absence + retained controls
# ---------------------------------------------------------------------------

class _RecordingClient:
    """Records subscription calls; hands out nothing."""

    def __init__(self):
        self.rt_bars: list[int] = []
        self.mkt_data: list[int] = []

    def reqRealTimeBars(self, reqId, *a, **k):
        self.rt_bars.append(reqId)

    def cancelRealTimeBars(self, reqId):
        pass

    def reqMktData(self, reqId, *a, **k):
        self.mkt_data.append(reqId)

    def cancelMktData(self, reqId):
        pass

    def reqHistoricalData(self, *a, **k):
        pass

    def cancelHistoricalData(self, reqId):
        pass


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    fake = _RecordingClient()
    win.rt_manager.client = fake
    win.md_manager.client = fake
    # Historical requests never reach the fake: stub at the manager.
    _req_ids = iter(range(9001, 9999))
    win.md_manager.req_historical_data = lambda **k: next(_req_ids)
    win.show()
    qapp.processEvents()
    return win, fake


_REMOVED_CHART_ATTRS = (
    "footprint_static", "footprint_live", "depth_heatmap_item",
    "_fp_enabled_ui", "_fp_viewport_timer", "_d37_session", "_imbalance_n",
    "_depth_state_text", "_auction_state", "_depth_toggle", "_imb_label",
    "_auction_chip", "_depth_enabled_ui",
)
_REMOVED_CHART_METHODS = (
    "refresh_footprint", "_position_fp_controls", "_position_d37_controls",
    "_on_depth_toggled", "_on_imb_clicked", "_on_auction_clicked",
    "_on_depth_refresh", "bind_d37_session", "unbind_d37_session",
    "_on_auction_tick", "update_auction_chip", "_in_auction_window",
    "set_depth_state", "_fp_queue_viewport_sync", "_fp_emit_viewport",
)
_REMOVED_CHART_SIGNALS = (
    "footprint_toggled", "footprint_viewport_changed", "depth_toggled",
)
_REMOVED_WINDOW_ATTRS = (
    "active_trader", "dom_btn", "depth_manager", "_depth_req_id",
    "tick_history_manager", "footprint_cache", "right_dock_container",
    "_right_dock_layout",
)


def test_removed_controls_absent_and_retained_present(monkeypatch, qapp):
    """P1-T60-T21 / AC-D41.1: no removed control, attribute or signal; the
    retained controls still exist."""
    from PyQt6.QtWidgets import QPushButton

    win, _fake = _make_window(monkeypatch, qapp)
    try:
        cp = win.chart_panel
        for name in _REMOVED_CHART_ATTRS + _REMOVED_CHART_METHODS:
            assert not hasattr(cp, name), f"ChartPanel still has {name}"
        for name in _REMOVED_CHART_SIGNALS:
            assert not hasattr(cp, name), f"ChartPanel still has signal {name}"
        for name in _REMOVED_WINDOW_ATTRS:
            assert not hasattr(win, name), f"MainWindow still has {name}"

        texts = {b.text() for b in win.findChildren(QPushButton)}
        for label in ("Footprint", "Classic", "Tick count", "Depth", "DOM"):
            assert label not in texts, f"removed control {label!r} still rendered"
        assert not [t for t in texts if t.startswith(("IMB", "AUC"))], (
            f"removed IMB/AUC chips still rendered: {sorted(texts)}")

        # ...and the retained chart surfaces are still there.
        for name in ("set_alarms", "set_drawings", "set_studies"):
            assert callable(getattr(cp, name, None)), f"chart view lost {name}"
        assert win.portfolio_panel is not None
        assert win.right_dock.objectName() == "Portfolio"
    finally:
        win.close()


# ---------------------------------------------------------------------------
# request absence
# ---------------------------------------------------------------------------

_FORBIDDEN = ("reqMktDepth", "cancelMktDepth", "reqHistoricalTicks",
              "reqTickByTickData", "updateMktDepth", "updateMktDepthL2")


def test_removed_requests_are_never_issued(monkeypatch, qapp):
    """P1-T60-T31 / AC-D41.2: driving the app issues none of the removed
    requests and no ``"225"`` generic-ticks need, while the D38 S0 line and the
    watchlist/RT lines still issue."""
    issued: dict[str, list] = {"forbidden": [], "mkt_data": [], "rt": []}

    def _record_forbidden(name):
        def _f(self, *a, **k):
            issued["forbidden"].append((name, a, k))
        return _f

    for name in _FORBIDDEN:
        monkeypatch.setattr(IBApiClient, name, _record_forbidden(name),
                            raising=False)

    def _record_mkt_data(self, reqId, *a, **k):
        issued["mkt_data"].append((a, k))

    def _record_rt(self, reqId, *a, **k):
        issued["rt"].append(reqId)

    monkeypatch.setattr(IBApiClient, "reqMktData", _record_mkt_data)
    monkeypatch.setattr(IBApiClient, "reqRealTimeBars", _record_rt)

    win, fake = _make_window(monkeypatch, qapp)
    try:
        win._on_connected()
        win.symbol_input.setText("TEST")
        win.tf_combo.setCurrentText("5 mins")
        win.load_chart()
        # D27.9: the live RT feed attaches after priming completes.
        win._on_historical_data_end(win._prime_req_id)
        # Drive the remaining controls, including a symbol switch.
        win.ext_hours_btn.setChecked(True)
        win.symbol_input.setText("TEST2")
        win.load_chart()
        win._on_historical_data_end(win._prime_req_id)
        qapp.processEvents()

        assert issued["forbidden"] == [], (
            f"removed requests were issued: {issued['forbidden']}")

        # No generic-ticks string may carry the removed "225" auction need.
        # (Only STRING arguments are inspected, so a reqId of 225 cannot
        # false-positive.)
        strings = [x for a, k in issued["mkt_data"]
                   for x in list(a) + list(k.values()) if isinstance(x, str)]
        assert not [s for s in strings if "225" in s], (
            f'the removed "225" auction need is still requested: {strings}')

        # ...while the RT bar line still issues. (It is issued on the
        # recording fake the RT manager was handed, hence both sources.) The
        # session opens no market-data line any more: S0's last consumer was
        # the D38 dividend markers, removed with them.
        assert issued["rt"] or fake.rt_bars, "the RT bar line stopped issuing"
        assert not issued["mkt_data"] and not fake.mkt_data, (
            "a chart-only session opened a market-data line with no consumer")
    finally:
        win.close()


# ---------------------------------------------------------------------------
# the app still works
# ---------------------------------------------------------------------------

def test_app_launches_and_renders_candles_and_volume(monkeypatch, qapp,
                                                     sample_bars):
    """P1-T60-T41 / AC-D41.5: the app launches and the chart still renders."""
    from services import chart_model

    win, _fake = _make_window(monkeypatch, qapp)
    try:
        cp = win.chart_panel
        cp.set_symbol("TEST")
        cp.update_chart(sample_bars)
        qapp.processEvents()
        assert cp.plotted_bars, "candles did not render"
        _xs, heights, _colors = chart_model.volume_display_columns(
            cp.plotted_bars, None)
        assert heights, "volume did not render"
        assert any(v > 0 for v in heights), "volume rendered as all-zero"
    finally:
        win.close()
