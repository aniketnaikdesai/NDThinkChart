"""D45/P5 removal book — the batch's acceptance instrument (AC-D45.1–.8,
AC-D46.1/.8/.9/.10/.11/.12).

Three independent nets, because "the order path is gone" can fail three ways:

1. **static absence** — the six deleted modules and seven deleted suites do not
   resolve, and no forbidden token survives in ``ui/ services/ data/ ibkr/
   config/``: identifiers *and* string constants, via AST (the
   ``tests/test_d41_removal.py`` precedent), plus a raw-text ``ui/``-only grep
   twin over the same list. The two instruments are deliberately not the same
   net: comments are invisible to the AST scan, so the twin is the prose half,
   and the twin is ``ui/``-only. Two tokens (``orders``/``Orders``) are
   exact-matched — a whole identifier or whole string constant in the AST scan,
   a delimited word in the twin — because both are ordinary English words that
   legitimate explanatory prose may contain; every other token is
   substring-matched. There is **no** file-scoped exemption any more: P23
   (D65) dropped the stop/target columns, so ``stop_loss``/``take_profit``
   are forbidden everywhere with no migration left to name them; and the
   AC-D65.18 file-set grep (over the ten files the D65 removals touched) is
   the third static net;
2. **no transmit/cancel** — ``placeOrder`` / ``cancelOrder`` /
   ``reqGlobalCancel`` are neither defined in the repo nor called anywhere in
   the scanned tree, so a future caller fails here rather than in a review;
3. **behavioural absence** — a real offscreen ``MainWindow`` with
   ``IBApiClient.connect`` mocked and the three transmit/cancel methods
   replaced by call recorders is driven through every remaining affordance
   (chart load, timeframe/mode/ext-hours switches, watchlist add/remove and the
   column popup, alarms, studies, drawings, pop-outs, the Option Spreads
   panel's collapse/restore, an ``_on_error`` emission that shows the generic
   ``Error [<code>]: <text>`` line and ``closeEvent``) and records **zero**
   calls of each — while every step records the Option Spreads panel's shape
   and collapse state. The panel renderer that replaced the removed positions
   view is asserted in ``tests/test_d65_option_panel.py`` (and, once live, in
   the P23-05 stream suite).

``tests/`` is covered by neither static instrument, so D45's and P5's
``hasattr(...) is False`` measurables are asserted **directly** (the absence
tests below).

Memory: every non-pytest probe must export ``DB_PATH`` to a temp file
(ESC-043); ``tests/conftest.py`` does that for the whole suite, and the
walkthrough below builds a real window.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import re
import sqlite3
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest
from PyQt6.QtCore import QPoint

from ibkr.client import IBApiClient

_REPO = Path(__file__).resolve().parent.parent
_SOURCE_DIRS = ("ui", "services", "data", "ibkr", "config")

#: The six modules removed by D45 + P5 (``ibkr.orders`` landed in P5 wave 3).
_DELETED_MODULES = (
    "ui.news_digest_dock",
    "ibkr.news",
    "ui.trade_context_menu",
    "ui.stop_loss_target_dialog",
    "ibkr.validation",
    "ibkr.orders",
)

#: The seven suites removed by D45 + P5 (the last two died with their subjects
#: in P5 waves 3 and 7).
_DELETED_SUITES = (
    "tests/test_d28_6_close_contracts.py",
    "tests/test_d41_retained_order_path.py",
    "tests/test_order_validation.py",
    "tests/test_sltp_honesty.py",
    "tests/test_kill_switch.py",
    "tests/test_order_builders.py",
    "tests/test_stop_loss_target.py",
)

#: The plan's full "forbidden after D45 and P5" list (docs/plan.md § D45 and
#: § P5 residue verification steps). The static half of this module and the
#: per-wave residue grep share it, so they cannot drift.
_FORBIDDEN = (
    "292",
    "NewsManager",
    "news_manager",
    "news_digest",
    "NewsDigest",
    "news_digest_dock",
    "_on_news_digest_visibility",
    "menuBar",
    "view_menu",
    "Ctrl+Shift+N",
    "_on_s0_tick_news",
    "on_s0_tick_news",
    "news_push_listener",
    "set_s0_headless",
    "_s0_headless",
    "TradeContextMenu",
    "trade_context_menu",
    "position_close_requested",
    "group_close_requested",
    "flatten_all_requested",
    "_on_portfolio_close_position",
    "_on_portfolio_close_group",
    "_on_portfolio_flatten_all",
    "_close_position_by_id",
    "validate_order",
    "placeOrder",
    "_ref_price_for",
    "kill_btn",
    "KillSwitchButton",
    "_kill_switch",
    "_on_kill_switch_clicked",
    "reqGlobalCancel",
    "cancelOrder",
    "StopLossTargetDialog",
    "stop_loss_target_dialog",
    "position_sltp_changed",
    "group_sltp_changed",
    "_on_portfolio_sltp_changed",
    "_on_portfolio_group_sltp_changed",
    "_on_set_sltp",
    "_on_sltp_confirmed",
    "_sltp_dialog",
    "update_position_sltp",
    "update_group_sltp",
    "_show_context_menu",
    "_on_close_position",
    "_on_close_group",
    "_on_ungroup",
    "_on_flatten_all",
    "_selected_row",
    "_selected_position",
    "_on_selection_changed",
    "set_sltp_action",
    # ---- added by P5 (D46): the order path and the stop/target storage ----
    "ibkr.orders",
    "order_registry",
    "orders",
    "Orders",
    "UserOrder",
    "market_order",
    "limit_order",
    "stop_order",
    "bracket_order",
    "_on_open_order",
    "_on_order_status",
    "_on_exec_details",
    "_update_order_status",
    "_on_order_error",
    "order_status",
    "open_order",
    "exec_details",
    "OrderRateLimiter",
    "order_limiter",
    "MAX_ORDER_NOTIONAL",
    "render_fill_blip",
    "BLIP_DURATION",
    "play_fill",
    "_fill_effect",
    "order_fill",
    "stop_loss",
    "take_profit",
    # ---- added by P23 (D65): the position/trade-group substrate ----
    "ActivePortfolioPanel",
    "portfolio_panel",
    "Account Summary",
    "account_summary",
    "account_summary_end",
    "position_update",
    "position_end",
    "build_position_from_ib",
    "_parse_contract_type",
    "detect_and_group",
    "OptionLeg",
    "strategy_detection",
    "Position",
    "TradeGroup",
    "_upsert_position",
    "_symbol_last_prices",
    "_record_symbol_price",
    "set_price_sink",
    "_price_sink",
    "reqAccountSummary",
    "reqPositions",
    "_account_id",
)

#: The three tables D65 dropped. Deliberately **not** forbidden tokens: the
#: one-time ``DROP TABLE IF EXISTS`` in ``data/db.py`` and the table-absence
#: assertions in ``tests/test_db_schema.py`` and block (g) below must *spell*
#: the names they drop and prove gone, so tokenising them would redden the
#: instrument on the very migration it describes. Their absence is measured by
#: the schema cases, never by a token grep.
_RETIRED_TABLES = ("position_group_map", "positions", "trade_groups")

#: The AC-D65.18 file set: every file a D65 removal touched (or deleted).
_D65_FILE_SET = (
    "ui/main_window.py",
    "ui/watchlist_panel.py",
    "ui/ticker_session.py",
    "ui/active_portfolio_panel.py",
    "ibkr/account.py",
    "ibkr/bridge.py",
    "ibkr/client.py",
    "data/db.py",
    "data/models.py",
    "services/strategy_detection.py",
)

#: The survivor allow-list (plan § "Survivors — MUST NOT be reported as
#: residue"). These are AC-D45.2/A90's and P5's deliberate end state, not
#: leftovers: the ibapi news boundary names, the error-severity gate and the
#: shared pacing substrate. The D38 dividend-marker path was removed with the
#: markers themselves (owner instruction, 2026-10-27), so its tokens are no
#: longer survivors — they are gone from the tree. P5 deleted the inert
#: inbound observers, the ``ibkr/orders`` module, ``order_limiter``,
#: ``MAX_ORDER_NOTIONAL`` and ``IdManager.reserve``; ``reserve`` is **not** a
#: forbidden token (the English word "preserve(s/d)" appears across files the
#: phase keeps) and is asserted by ``hasattr(IdManager, "reserve") is False`` in
#: the end-state test. None of the survivors shares a name with a forbidden
#: token today; the list is here so a future rename that would otherwise
#: collide is a documented decision instead of a silent false positive.
_SURVIVORS = frozenset({
    # ibapi news boundary (S35) — unconnected, never requested
    "tick_news", "news_providers", "historical_news", "historical_news_end",
    "news_article",
    # error visibility (S46) — the gate the surviving _on_error path uses
    "classify_error",
    # shared pacing substrate (S46) — realtime/historical pacing keeps serving
    "pacing_manager", "PacingExceeded",
})

#: Tokens too short (or too generic) for a substring match: ``"292"`` appears
#: inside arbitrary numbers, so it is matched exactly (or as a delimited
#: generic-tick component, e.g. ``"456,292"``). ``orders``/``Orders`` are
#: handled by ``_EXACT_ONLY`` instead — both are ordinary English words, so only
#: a whole identifier / whole string constant (AST) or a delimited word (twin)
#: counts. Every remaining token is a repo-specific identifier, so a substring
#: match is the stronger test; there is no file-scoped exemption left after
#: P23 deleted the D46 stop/target migration that needed one.
_MIN_SUBSTRING = 6
#: Consulted **before** the substring branch in both instruments.
_EXACT_ONLY = frozenset({"orders", "Orders"})
_SPLIT = re.compile(r"[^0-9A-Za-z_]+")

_TRANSMIT_METHODS = ("placeOrder", "cancelOrder", "reqGlobalCancel")


# ---------------------------------------------------------------------------
# static half — module/suite absence + the AST token scan
# ---------------------------------------------------------------------------

def _scan_file(path: Path) -> tuple[set[str], set[str]]:
    """Return (identifiers, string constants) the module mentions.

    Mirrors ``tests/test_d41_removal.py::_identifiers`` but keeps identifiers
    and string constants apart so the numeric generic-tick code can be matched
    exactly instead of as a substring. Comments are invisible to ``ast`` by
    construction; docstrings are string constants and are therefore scanned.
    """
    tree = ast.parse(path.read_text())
    idents: set[str] = set()
    strings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            idents.add(node.id)
        elif isinstance(node, ast.Attribute):
            idents.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            idents.add(node.name)
        elif isinstance(node, ast.arg):
            idents.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            idents.add(node.arg)
        elif isinstance(node, ast.alias):
            idents.add(node.name)
            idents.add((node.asname or node.name).split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return idents, strings


def _source_files():
    for d in _SOURCE_DIRS:
        root = _REPO / d
        if root.is_dir():
            yield from sorted(root.rglob("*.py"))


def _matches(name: str) -> str | None:
    """The forbidden token ``name`` carries, or ``None``.

    ``_EXACT_ONLY`` is tested first: ``token in parts`` is the wrong AST
    implementation (it splits a docstring into words, so "Orders were
    throttled…" would match), and the branch must compare the whole unit
    (``name == token``). Only the raw-text ``ui`` twin uses a delimited word.
    """
    if name in _SURVIVORS:
        return None
    parts = _SPLIT.split(name)
    for token in _FORBIDDEN:
        if token in _SURVIVORS:  # documented survivor wins over the net
            continue
        if token in _EXACT_ONLY:
            if name == token:
                return token
        elif len(token) >= _MIN_SUBSTRING:
            if token in name:
                return token
        elif name == token or token in parts:
            return token
    return None


def _token_offences(path: Path) -> list[tuple[str, str]]:
    idents, strings = _scan_file(path)
    offences: list[tuple[str, str]] = []
    for name in sorted(idents | strings):
        token = _matches(name)
        if token is not None:
            offences.append((name, token))
    return offences


def test_deleted_modules_and_suites_are_gone():
    """P4-T06-T11 (a) / AC1 + P5-T08-T31 / AC3: the six modules and seven
    suites are gone."""
    offences: list[str] = []
    for mod in _DELETED_MODULES:
        try:
            spec = importlib.util.find_spec(mod)
        except (ImportError, ModuleNotFoundError):
            spec = None
        if spec is not None:
            offences.append(f"{mod} still resolvable")
    for rel in _DELETED_SUITES:
        if (_REPO / rel).exists():
            offences.append(f"{rel} still present")
    assert not offences, (
        "D45 deletions are incomplete:\n  " + "\n  ".join(offences))


def test_no_removed_token_survives_in_source():
    """P4-T06-T21 (b) / AC2 + P5-T08-T61 / AC6: the AST scan over the five
    source dirs.

    Every token is forbidden in every file; P23 deleted the ``DROP COLUMN``
    migration that used to exempt ``stop_loss``/``take_profit`` inside
    ``data/db.py``, so no exemption call site remains. The ``ui/`` twin below
    is the prose half of the same list.
    """
    offences: list[str] = []
    for path in _source_files():
        rel = path.relative_to(_REPO).as_posix()
        for name, token in _token_offences(path):
            offences.append(f"{rel}: {name!r} matches forbidden token {token!r}")
    assert not offences, (
        "removed D45 tokens still present in source:\n  "
        + "\n  ".join(offences))


def _text_offences(path: Path, rel: str) -> list[str]:
    """Raw-text token hits in one file (the prose net: comments included)."""
    hits: list[str] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        parts = _SPLIT.split(line)
        for token in _FORBIDDEN:
            if token in _SURVIVORS:
                continue
            if token in _EXACT_ONLY:
                if token in parts:
                    hits.append(f"{rel}:{line_no}: {token!r}")
            elif len(token) >= _MIN_SUBSTRING:
                if token in line:
                    hits.append(f"{rel}:{line_no}: {token!r}")
            elif token in parts:
                hits.append(f"{rel}:{line_no}: {token!r}")
    return hits


def test_no_removed_token_survives_in_ui_text():
    """P4-T06-T31 (b) twin / AC2: the ``ui/``-only grep, over raw text.

    The prose net for human workers: unlike the AST scan this reads comments
    too. Same token list as the test above, so the two cannot drift apart.
    """
    hits: list[str] = []
    ui_root = _REPO / "ui"
    for path in sorted(ui_root.rglob("*.py")):
        rel = path.relative_to(_REPO).as_posix()
        hits.extend(_text_offences(path, rel))
    assert not hits, (
        "removed D45 tokens still present in ui/ (grep twin):\n  "
        + "\n  ".join(hits))


def test_d65_file_set_has_no_displaced_tokens():
    """P23-T12-AC6 / AC-D65.18: the file-set residue grep.

    The ten files a D65 removal touched (or deleted) carry no live occurrence
    of any displaced token. A deleted file is the strongest absence, so it is
    skipped; a surviving file is grepped as raw text, comments included.
    """
    hits: list[str] = []
    for rel in _D65_FILE_SET:
        path = _REPO / rel
        if not path.exists():
            continue
        hits.extend(_text_offences(path, rel))
    assert not hits, (
        "displaced D65 tokens still live in the AC-D65.18 file set:\n  "
        + "\n  ".join(hits))


def test_no_transmit_or_cancel_call_site():
    """P4-T06-T41 (c) / AC3: no definition and no call site, anywhere."""
    offences: list[str] = []
    for path in _source_files():
        rel = path.relative_to(_REPO).as_posix()
        idents, _strings = _scan_file(path)
        for name in _TRANSMIT_METHODS:
            if name in idents:
                offences.append(f"{rel}: {name}")
    assert not offences, (
        "order transmit/cancel still referenced in source "
        "(AC-D45.4 — the app must define and call none of them):\n  "
        + "\n  ".join(offences))
    for name in _TRANSMIT_METHODS:
        assert name not in IBApiClient.__dict__, (
            f"ibkr/client.py defines {name}; the boundary must stay "
            "inherited-only (Frozen Interfaces (D45))")


# ---------------------------------------------------------------------------
# behavioural half — zero transmit/cancel around every remaining affordance
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


class _RecordingExcepthook:
    """Temporary ``sys.excepthook`` that records unhandled slot exceptions.

    pyqtgraph installs a non-abort excepthook, so a slot exception (an
    ``AttributeError`` from a removed member, say) is printed and swallowed —
    observable state plus this recorder are the only reliable guard.
    """

    def __init__(self):
        self.records: list = []
        self._prev = None

    def __call__(self, exc_type, exc_value, tb):
        self.records.append((exc_type, exc_value, tb))

    def __enter__(self):
        self._prev = sys.excepthook
        sys.excepthook = self
        return self

    def __exit__(self, *exc):
        sys.excepthook = self._prev
        return False


def _install_transmit_recorders(monkeypatch):
    """Replace the three inherited EClient methods with call recorders."""
    calls: dict[str, list] = {name: [] for name in _TRANSMIT_METHODS}

    def _make(name):
        def _record(self, *a, **k):
            calls[name].append((a, k))
        return _record

    for name in _TRANSMIT_METHODS:
        monkeypatch.setattr(IBApiClient, name, _make(name), raising=False)
    return calls


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    fake = _RecordingClient()
    win.rt_manager.client = fake
    win.md_manager.client = fake
    # Historical requests never reach the fake: stub at the manager. The id
    # source is UNBOUNDED (memory 2026-10-16, D42) — a load path that issues
    # more than the initial range must not exhaust it.
    req_ids = itertools.count(9001)
    win.md_manager.req_historical_data = lambda **k: next(req_ids)
    win.show()
    qapp.processEvents()
    return win, fake


def _table_shape(table) -> dict:
    """One spread table's column count, header tuple and row count."""
    header = table.horizontalHeaderItem
    return {
        "columns": table.columnCount(),
        "headers": [
            header(i).text() if header(i) is not None else None
            for i in range(table.columnCount())
        ],
        "rows": table.rowCount(),
    }


def _snapshot(win) -> dict:
    """Record the Option Spreads panel's shape and collapse state."""
    panel = win.option_spreads_panel
    return {
        "ccs": _table_shape(panel.ccs_table),
        "pcs": _table_shape(panel.pcs_table),
        "collapsed": panel.is_collapsed(),
    }


def _other_timeframe(current: str) -> str:
    from ibkr.market_data import TIMEFRAME_CONFIG

    return next((k for k in TIMEFRAME_CONFIG if k != current), current)


@pytest.fixture
def walkthrough(monkeypatch, qapp):
    """Drive the real window through every remaining affordance, record.

    The window is built with ``IBApiClient.connect`` mocked and the three
    transmit/cancel methods replaced by call recorders, then driven through
    every affordance the batch leaves standing, ending with ``closeEvent``.
    Nothing is asserted here — the tests read the record, so a failure names
    the step and the offence.
    """
    calls = _install_transmit_recorders(monkeypatch)
    win, fake = _make_window(monkeypatch, qapp)
    record: dict = {"steps": []}
    recorder = _RecordingExcepthook()

    def snap(label: str) -> None:
        qapp.processEvents()
        record["steps"].append((label, _snapshot(win)))

    try:
        from ibkr.contracts import get_contract_for_symbol
        from ui.alarm_dialog import AlarmDialog
        from ui.drawing_groups_dialog import DrawingGroupsDialog
        from ui.studies_dialog import StudiesDialog

        # A modal dialog would block the walkthrough; the dialog itself is
        # still constructed and wired — only its event loop is stubbed.
        monkeypatch.setattr(AlarmDialog, "exec", lambda self, *a, **k: 0)
        monkeypatch.setattr(StudiesDialog, "exec", lambda self, *a, **k: 0)
        monkeypatch.setattr(DrawingGroupsDialog, "exec", lambda self, *a, **k: 0)

        with recorder:
            win._on_connected()
            snap("connect")

            win.symbol_input.setText("aapl")   # load_chart upper-cases
            win.load_chart()
            win._on_historical_data_end(win._prime_req_id)
            snap("chart load")

            win.tf_combo.setCurrentText(_other_timeframe(win.tf_combo.currentText()))
            win.load_chart()
            win._on_historical_data_end(win._prime_req_id)
            snap("timeframe switch")

            win.mode_combo.setCurrentText("Line")
            win.mode_combo.setCurrentText("Candles")
            snap("mode switch")

            win.ext_hours_btn.setChecked(not win.ext_hours_btn.isChecked())
            win.ext_hours_btn.setChecked(not win.ext_hours_btn.isChecked())
            snap("ext-hours switch")

            win.watchlist_panel.add_symbol("MSFT", get_contract_for_symbol("MSFT"))
            snap("watchlist add")
            win.watchlist_panel.remove_symbol("MSFT")
            snap("watchlist remove")

            menu = win.watchlist_panel._on_header_context_menu(
                QPoint(0, 0), show=False)
            assert menu is not None, "the watchlist column popup did not build"
            menu.deleteLater()
            snap("watchlist column popup")

            win._open_alarm_dialog()
            snap("alarms")

            win._open_studies_dialog()
            snap("studies")

            win.draw_combo.setCurrentText("Trendline")
            win.draw_combo.setCurrentText("Cursor")
            win.draw_sets_btn.click()
            snap("drawings")

            win._open_popout()
            snap("pop-out")
            for popout in list(win._popouts):
                popout.close()
            snap("pop-out close")

            win.option_spreads_panel.header_button.click()
            snap("panel collapse")
            win.option_spreads_panel.header_button.click()
            snap("panel restore")

            win._on_error(1, 201, "Order rejected (walkthrough)")
            snap("order error")

            win.close()
            snap("closeEvent")
    finally:
        if not getattr(win, "_closing", False):
            win.close()

    yield {"win": win, "calls": calls, "record": record,
           "recorder": recorder, "fake": fake}


def test_zero_transmit_walkthrough(walkthrough):
    """P4-T06-T51 (d) / AC4: zero transmit/cancel; every step constructible."""
    calls = walkthrough["calls"]
    for name in _TRANSMIT_METHODS:
        assert calls[name] == [], (
            f"{name} was called {len(calls[name])} time(s) during the "
            f"walkthrough: {calls[name]!r}")

    record = walkthrough["record"]
    assert record["steps"], "the walkthrough recorded no steps"
    headers = ["Financial instrument", "ASK", "BID", "Delta", "Gamma"]
    for label, snap in record["steps"]:
        for side in ("ccs", "pcs"):
            shape = snap[side]
            assert shape["columns"] == 5, (
                f"the window was not constructible at step {label!r}: "
                f"the {side.upper()} table has {shape['columns']} columns")
            assert shape["rows"] == 4, (
                f"the {side.upper()} table has {shape['rows']} rows at step "
                f"{label!r}, expected 4")
            assert shape["headers"] == headers, (
                f"unexpected {side.upper()} headers at step {label!r}: "
                f"{shape['headers']!r}")

    collapsed = {label: snap["collapsed"] for label, snap in record["steps"]}
    assert collapsed["panel collapse"] is True, (
        "the header button did not collapse the Option Spreads panel")
    assert collapsed["panel restore"] is False, (
        "the header button did not restore the Option Spreads panel")

    bad = [r for r in walkthrough["recorder"].records
           if r[0] in (AttributeError, TypeError)]
    assert not bad, (
        "unhandled AttributeError/TypeError during the walkthrough "
        f"(a removed member is still reachable): {bad!r}")


# ---------------------------------------------------------------------------
# D41's half-removal — the session tick relays, asserted where the static
# instruments cannot see them (tests/ is outside their scope either way, but
# the failure mode here is behavioural: a disconnected-or-dead slot is only
# visible when a tick is emitted)
# ---------------------------------------------------------------------------

#: D41 deleted ``TickerSession.on_tick_price``/``on_tick_size``; MainWindow's
#: two relays and their ``bridge.tick_price``/``tick_size`` connects outlived
#: them, so every market-data tick raised ``AttributeError`` and pyqtgraph's
#: non-abort excepthook printed it. The watchlist's own handlers
#: (``WatchlistPanel.on_tick_price``/``on_tick_size``) are a different object's
#: and stay wired.
_D41_REMOVED_SESSION_TICK_SLOTS = (
    "_on_session_tick_price",
    "_on_session_tick_size",
)


def test_no_dead_session_tick_relay(monkeypatch, qapp):
    """D41: the two relays are gone and a tick no longer raises.

    The static nets cannot see this: the slots are defined in ``ui/`` (so the
    token scan finds nothing wrong) and their bodies only fail at *call* time.
    ``hasattr`` is the right measure for the removal — no base class supplies
    them — and a real offscreen window is the measure for the wiring: the
    unknown reqId keeps the watchlist's own handler on its early-return path,
    so any recorded exception is the dead relay's.
    """
    from ui.main_window import MainWindow

    for name in _D41_REMOVED_SESSION_TICK_SLOTS:
        assert not hasattr(MainWindow, name), (
            f"MainWindow still has {name!r}; its TickerSession counterpart was "
            "deleted (D41)")

    win, _fake = _make_window(monkeypatch, qapp)
    recorder = _RecordingExcepthook()
    try:
        with recorder:
            win.ib_client.bridge.tick_price.emit(9999, 1, 123.45)
            win.ib_client.bridge.tick_size.emit(9999, 8, 100)
            qapp.processEvents()
    finally:
        win.close()

    assert not recorder.records, (
        "a market-data tick raised on a constructed window after D41 removed "
        f"the session tick handlers: {recorder.records!r}")


# ---------------------------------------------------------------------------
# P5 / D46 end state asserted directly — the same scope rule as above, now for
# every member the phase removed (AC-D46.1/.8/.9/.10/.11/.12)
# ---------------------------------------------------------------------------

#: P5 wave 1's five window members. Safe as ``hasattr``: no base class supplies
#: them, so their absence is real (unlike the ``ibapi`` overrides below).
_P5_REMOVED_WINDOW_MEMBERS = (
    "_on_open_order",
    "_on_order_status",
    "_on_exec_details",
    "_update_order_status",
    "_on_order_error",
)

#: P5 wave 2's three bridge signals — deleted together with their only emitters.
_P5_REMOVED_BRIDGE_SIGNALS = ("order_status", "open_order", "exec_details")

#: **Never** ``hasattr``: the inherited ``EWrapper`` no-ops keep it ``True``
#: before *and* after the override is deleted (AP-D46-14), so only
#: ``name not in IBApiClient.__dict__`` measures the removal.
_P5_REMOVED_OVERRIDES = ("orderStatus", "openOrder", "execDetails")

#: The pre-P23 ``positions``/``trade_groups``/``position_group_map`` DDL (HEAD
#: before D65): both stop/target column pairs, the ``trade_group_id`` FK and the
#: unique index D65 no longer creates. The D65 migration must drop all three
#: tables and leave the index behind with them.
_PRE_P5_DDL = """
CREATE TABLE trade_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    underlying TEXT NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    account TEXT NOT NULL,
    con_id INTEGER,
    contract_type TEXT NOT NULL,
    qty REAL NOT NULL,
    avg_cost REAL,
    local_symbol TEXT,
    multiplier REAL DEFAULT 1,
    expiry TEXT,
    strike REAL,
    right TEXT,
    stop_loss REAL,
    take_profit REAL,
    trade_group_id INTEGER REFERENCES trade_groups(id),
    updated_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX idx_positions_symbol_con_id
    ON positions(symbol, con_id);
CREATE TABLE position_group_map (
    ibkr_position_id TEXT NOT NULL,
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
"""


def _write_pre_p5_db(path: Path) -> None:
    """Create a pre-P23 DB: one row in every retired table."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_PRE_P5_DDL)
        conn.execute(
            "INSERT INTO trade_groups (id, name, strategy_type, underlying,"
            " stop_loss, take_profit, collapsed, created_at)"
            " VALUES (7, 'PCS', 'PCS', 'AAPL', 1.5, 2.5, 0, 1760000000)"
        )
        conn.execute(
            "INSERT INTO positions (id, symbol, account, con_id,"
            " contract_type, qty, avg_cost, local_symbol, multiplier, expiry,"
            " strike, right, stop_loss, take_profit, trade_group_id,"
            " updated_at)"
            " VALUES (1, 'AAPL', 'DU123', 1, 'stock', 10.0, 40.0, 'AAPL',"
            " 1.0, NULL, NULL, NULL, 1.5, 2.5, 7, 1760000000)"
        )
        conn.execute(
            "INSERT INTO position_group_map (ibkr_position_id, trade_group_id)"
            " VALUES ('DU123:1', 7)"
        )
        conn.commit()
    finally:
        conn.close()


def _schema_tables(conn) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }


def _schema_indexes(conn) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()
    }


def test_p5_end_state_all_removed_members_absent(monkeypatch):
    """P5-T08-T41 / AC-D46.1, .8, .9, .10, .11, .12 — the direct end state.

    ``tests/`` is covered by neither static instrument, so every P5 removal is
    measured here by the correct measure for its half: ``hasattr`` for the five
    window members and three bridge signals, ``IBApiClient.__dict__`` for the
    three ``ibapi`` overrides, ``find_spec``/``Path.exists()`` for the module and
    the two suites, ``hasattr`` for ``UserOrder`` and the displaced model
    classes, ``hasattr`` for ``IdManager.reserve`` with
    ``get_id``/``set_next_valid_id`` still present,
    and absence of the four order utilities.

    The schema half is P23's (block (g) below, AC-D65.18): the pre-P23 fixture
    is opened through ``DB_PATH`` routed via ``config.paths._DB_FILENAME``, and
    all three retired tables plus their unique index are proven gone on the
    first open, on a second open, and in a fresh DB.
    """
    import data.models as models

    from config import paths, settings
    from data.db import DB
    from ibkr import pacing
    from ibkr.bridge import IBBridge
    from ibkr.id_manager import IdManager
    from services import sound_service
    from ui.main_window import MainWindow

    # (a) window consumers (wave 1) and bridge signals (wave 2)
    for name in _P5_REMOVED_WINDOW_MEMBERS:
        assert not hasattr(MainWindow, name), (
            f"MainWindow still has {name!r} (P5 wave 1)")
    for name in _P5_REMOVED_BRIDGE_SIGNALS:
        assert not hasattr(IBBridge, name), (
            f"IBBridge still defines the {name!r} signal (P5 wave 2)")

    # (b) the three ibapi overrides — __dict__, never hasattr
    for name in _P5_REMOVED_OVERRIDES:
        assert name not in IBApiClient.__dict__, (
            f"IBApiClient still overrides {name!r} (P5 wave 2)")

    # (c) the module and the two suites (waves 3 and 7)
    try:
        spec = importlib.util.find_spec("ibkr.orders")
    except (ImportError, ModuleNotFoundError):
        spec = None
    assert spec is None, "ibkr.orders is still importable"
    assert not (_REPO / "ibkr" / "orders.py").exists(), (
        "ibkr/orders.py is still present")
    for rel in ("tests/test_order_builders.py",
                "tests/test_stop_loss_target.py"):
        assert not (_REPO / rel).exists(), f"{rel} is still present"

    # (d) UserOrder and the displaced model classes are gone (waves 3 and 7)
    assert not hasattr(models, "UserOrder"), "data.models.UserOrder is back"
    assert not hasattr(models, "Position"), "data.models.Position is back"
    assert not hasattr(models, "TradeGroup"), "data.models.TradeGroup is back"

    # (e) IdManager: reserve gone, the allocator intact (wave 6)
    assert not hasattr(IdManager, "reserve"), "IdManager.reserve is back"
    assert hasattr(IdManager, "get_id"), "IdManager.get_id was removed"
    assert hasattr(IdManager, "set_next_valid_id"), (
        "IdManager.set_next_valid_id was removed")

    # (f) the four order utilities (waves 4 and 5)
    for name in ("OrderRateLimiter", "order_limiter"):
        assert not hasattr(pacing, name), f"ibkr.pacing still exports {name!r}"
    assert not hasattr(settings, "MAX_ORDER_NOTIONAL"), (
        "config.settings still defines MAX_ORDER_NOTIONAL")
    for name in ("render_fill_blip", "BLIP_DURATION"):
        assert not hasattr(sound_service, name), (
            f"services.sound_service still defines {name!r}")
    assert not hasattr(sound_service.SoundService, "play_fill"), (
        "SoundService.play_fill is back")

    # (g) the schema end state — the three D65-retired tables are gone for good
    with tempfile.TemporaryDirectory() as tmp:
        # Keep the pre-drop backup out of the owner's application-support dir.
        monkeypatch.setattr(paths, "_USER_APP_SUPPORT_DIR", Path(tmp) / "userdata")

        legacy = Path(tmp) / "pre_p5.sqlite3"
        _write_pre_p5_db(legacy)
        monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy))

        upgraded = DB()
        try:
            tables = _schema_tables(upgraded.conn)
            for name in _RETIRED_TABLES:
                assert name not in tables, (
                    f"the migration left the retired table {name!r} behind")
            assert "idx_positions_symbol_con_id" not in _schema_indexes(
                upgraded.conn), "the unique index outlived its positions table"
        finally:
            upgraded.conn.close()

        # a second open is a no-op — still absent, no error
        again = DB()
        try:
            tables = _schema_tables(again.conn)
            for name in _RETIRED_TABLES:
                assert name not in tables, (
                    f"a second open resurrected the retired table {name!r}")
        finally:
            again.conn.close()

        # a fresh DB is created without any of them at all
        monkeypatch.setattr(paths, "_DB_FILENAME", str(Path(tmp) / "fresh.sqlite3"))
        fresh = DB()
        try:
            tables = _schema_tables(fresh.conn)
            for name in _RETIRED_TABLES:
                assert name not in tables, (
                    f"a fresh DB still creates the retired table {name!r}")
            assert "idx_positions_symbol_con_id" not in _schema_indexes(
                fresh.conn)
        finally:
            fresh.conn.close()


# ---------------------------------------------------------------------------
# P23 (D65) — the re-baselined token lists
# ---------------------------------------------------------------------------

#: Symbols and modules this phase killed. Every one is dead by the end of the
#: D65 wave; the list is what stops a later wave resurrecting them.
_D65_DEAD_TOKENS = (
    "ActivePortfolioPanel",
    "portfolio_panel",
    "Account Summary",
    "account_summary",
    "account_summary_end",
    "position_update",
    "position_end",
    "build_position_from_ib",
    "_parse_contract_type",
    "detect_and_group",
    "OptionLeg",
    "strategy_detection",
    "Position",
    "TradeGroup",
    "_upsert_position",
    "_symbol_last_prices",
    "_record_symbol_price",
    "set_price_sink",
    "_price_sink",
    "reqAccountSummary",
    "reqPositions",
    "_account_id",
)


def test_d65_dead_tokens_are_forbidden_and_tables_are_not():
    """P23-T12-AC5: the re-baselined instrument measures this phase.

    Every D65-dead symbol/module token is in ``_FORBIDDEN`` (and therefore
    scanned), while the three table names the migration and the absence
    assertions must spell stay out of both token lists.
    """
    for token in _D65_DEAD_TOKENS:
        assert token in _FORBIDDEN, (
            f"{token!r} is not a forbidden token; the D65 residue net is stale")
        assert token not in _SURVIVORS, (
            f"{token!r} is listed as a survivor, so the net would skip it")
        # Overlapping tokens (``account_summary`` inside
        # ``account_summary_end``) match the first entry in _FORBIDDEN; what
        # matters is that each one is measured, not which name is reported.
        assert _matches(token) is not None, (
            f"{token!r} is in _FORBIDDEN but _matches() does not see it")

    for table in _RETIRED_TABLES:
        assert table not in _FORBIDDEN, (
            f"{table!r} must not be a token: the migration and the absence "
            "assertions have to spell it")
        assert table not in _SURVIVORS

    # The carve-out lost its only subject with the D46 columns.
    assert "DROP COLUMN" not in (_REPO / "data" / "db.py").read_text()
