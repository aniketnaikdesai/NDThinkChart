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
   legitimate explanatory prose may contain; the other 78 are substring-matched;
   the only exemption is file-scoped (``_ALLOWED_IN_FILE``): ``stop_loss`` and
   ``take_profit`` inside ``data/db.py``, whose ``DROP COLUMN`` migration must
   name the two columns it removes — nowhere else, and never as code (the
   ``DROP COLUMN`` subject-tuple shape is asserted by
   ``test_allowed_in_file_is_narrow_and_named_not_used``, not merely stated);
2. **no transmit/cancel** — ``placeOrder`` / ``cancelOrder`` /
   ``reqGlobalCancel`` are neither defined in the repo nor called anywhere in
   the scanned tree, so a future caller fails here rather than in a review;
3. **behavioural absence** — a real offscreen ``MainWindow`` with
   ``IBApiClient.connect`` mocked and the three transmit/cancel methods
   replaced by call recorders is driven through every remaining affordance
   (chart load, timeframe/mode/ext-hours switches, watchlist add/remove and the
   column popup, alarms, studies, drawings, pop-outs, Portfolio selection and
   refresh, an external position update and an external TWS-side close, an
   ``_on_error`` emission that shows the generic ``Error [<code>]: <text>``
   line and ``closeEvent``) and records **zero** calls
   of each — while the Portfolio table still renders the position and reflects
   the TWS-side close. ``AC-D45.5``'s render/live path is intact.

``tests/`` is covered by neither static instrument, so D45's and P5's
``hasattr(...) is False`` measurables are asserted **directly** (the two
absence tests at the end).

Memory: every non-pytest probe must export ``DB_PATH`` to a temp file
(ESC-043); ``tests/conftest.py`` does that for the whole suite, and the
walkthrough below builds a real window.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import itertools
import re
import sqlite3
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest
from PyQt6.QtCore import QPoint, Qt

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
#: match is the stronger test; ``stop_loss``/``take_profit`` **must** stay
#: substrings so a column inside a SQL ``CREATE TABLE`` string constant is seen.
_MIN_SUBSTRING = 6
#: Consulted **before** the substring branch in both instruments.
_EXACT_ONLY = frozenset({"orders", "Orders"})

#: File-scoped exemption (AC7): ``stop_loss``/``take_profit`` stay forbidden
#: everywhere, but ``data/db.py``'s ``DROP COLUMN`` migration must *name* the two
#: columns it removes — that subject tuple is the one legitimate occurrence in
#: the tree. The exemption is applied at the scan call site (``_allowed_in``),
#: never inside ``_matches``, so ``_matches`` keeps reporting both tokens. It is
#: **named-not-used**, and that half is *enforced*, not promised:
#: ``test_allowed_in_file_is_narrow_and_named_not_used`` parses ``data/db.py``
#: and requires each token to be an element of the ``DROP COLUMN`` loop's subject
#: tuple — no identifier/attribute/argument/keyword use, and no other string
#: constant (CREATE/SELECT/PRAGMA) may name either token. A fresh occurrence
#: anywhere else reddens.
_ALLOWED_IN_FILE = {
    "stop_loss": {"data/db.py"},
    "take_profit": {"data/db.py"},
}
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


def _allowed_in(rel: str, token: str) -> bool:
    """True only when ``token`` is scoped to exactly this repo-relative file.

    Scope, not identity: the token stays forbidden in ``_matches`` and in every
    other file; only the one file whose migration has to spell the column may
    carry it. ``tests/test_d41_removal.py``'s ``_ALLOWED_IN_FILE`` idiom.
    """
    return rel in _ALLOWED_IN_FILE.get(token, ())


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
    source dirs, with the one file-scoped exemption.

    ``stop_loss``/``take_profit`` are exempt **only** inside ``data/db.py``
    (``_ALLOWED_IN_FILE``), because that file's ``DROP COLUMN`` migration must
    name the columns it removes; every other file forbids all 80 tokens. The
    ``ui/`` twin below needs no such exemption — it scans ``ui/`` only.
    """
    offences: list[str] = []
    for path in _source_files():
        rel = path.relative_to(_REPO).as_posix()
        for name, token in _token_offences(path):
            if _allowed_in(rel, token):
                continue
            offences.append(f"{rel}: {name!r} matches forbidden token {token!r}")
    assert not offences, (
        "removed D45 tokens still present in source:\n  "
        + "\n  ".join(offences))


def test_no_removed_token_survives_in_ui_text():
    """P4-T06-T31 (b) twin / AC2: the ``ui/``-only grep, over raw text.

    The prose net for human workers: unlike the AST scan this reads comments
    too. Same token list as the test above, so the two cannot drift apart.
    """
    hits: list[str] = []
    ui_root = _REPO / "ui"
    for path in sorted(ui_root.rglob("*.py")):
        rel = path.relative_to(_REPO).as_posix()
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
    assert not hits, (
        "removed D45 tokens still present in ui/ (grep twin):\n  "
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


def _stub_account_calls(win, monkeypatch):
    """Keep ``_on_connected`` off the (mocked) socket."""
    monkeypatch.setattr(win.ib_client, "reqPositions", lambda: None)
    monkeypatch.setattr(
        win.ib_client, "reqAccountSummary",
        lambda req_id, group, tags: None,
    )


def _snapshot(win) -> dict:
    table = win.portfolio_panel.positions_table
    header = table.horizontalHeaderItem
    return {
        "columns": table.columnCount(),
        "headers": [
            header(i).text() if header(i) is not None else None
            for i in range(table.columnCount())
        ],
        "rows": table.rowCount(),
        "first": table.item(0, 0).text() if table.item(0, 0) is not None else None,
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
    record: dict = {"steps": [], "positions": {}}
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

        contract = get_contract_for_symbol("AAPL")

        with recorder:
            _stub_account_calls(win, monkeypatch)
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

            win.ib_client.bridge.position_update.emit(
                "DU123", contract, 10.0, 40.0)
            record["positions"]["live update"] = _snapshot(win)
            snap("external position update")

            win.portfolio_panel.positions_table.selectRow(0)
            win.portfolio_panel.refresh()
            win.portfolio_panel.toggle_collapsed()
            win.portfolio_panel.toggle_collapsed()
            snap("portfolio selection + refresh")

            # External TWS-side close: a flat position update must clear the row.
            win.ib_client.bridge.position_update.emit(
                "DU123", contract, 0.0, 40.0)
            record["positions"]["tws-side close"] = _snapshot(win)
            snap("external TWS-side close")

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
    """P4-T06-T51 (d) / AC4: zero transmit/cancel, Portfolio render intact."""
    calls = walkthrough["calls"]
    for name in _TRANSMIT_METHODS:
        assert calls[name] == [], (
            f"{name} was called {len(calls[name])} time(s) during the "
            f"walkthrough: {calls[name]!r}")

    record = walkthrough["record"]
    assert record["steps"], "the walkthrough recorded no steps"
    for label, snap in record["steps"]:
        assert snap["columns"] == 8, (
            f"the window was not constructible at step {label!r}: "
            f"portfolio table has {snap['columns']} columns")

    live = record["positions"]["live update"]
    assert live["rows"] == 1, (
        f"the Portfolio table did not render the live position "
        f"(rows={live['rows']})")
    assert live["first"] == "AAPL", (
        f"the Portfolio table rendered {live['first']!r}, expected 'AAPL'")

    closed = record["positions"]["tws-side close"]
    assert closed["rows"] == 0, (
        "the Portfolio table did not reflect the TWS-side close "
        f"(rows={closed['rows']})")

    bad = [r for r in walkthrough["recorder"].records
           if r[0] in (AttributeError, TypeError)]
    assert not bad, (
        "unhandled AttributeError/TypeError during the walkthrough "
        f"(a removed member is still reachable): {bad!r}")


def test_positions_table_is_eight_columns(walkthrough):
    """P4-T06-T61 (e) / AC5: the S33 view model, with no Stop/Target."""
    table = walkthrough["win"].portfolio_panel.positions_table
    assert table.columnCount() == 8, (
        f"the positions table has {table.columnCount()} columns, expected 8")
    headers = [
        table.horizontalHeaderItem(i).text()
        for i in range(table.columnCount())
    ]
    assert headers == [
        "Symbol", "Qty", "Avg Price", "Type", "Multiplier", "P/L",
        "Strategy", "Group",
    ], f"unexpected positions headers: {headers!r}"
    assert "Stop" not in headers and "Target" not in headers, (
        f"the removed Stop/Target columns are still rendered: {headers!r}")
    assert table.horizontalHeaderItem(6).text() == "Strategy"
    assert table.horizontalHeaderItem(7).text() == "Group"


# ---------------------------------------------------------------------------
# AC-D45.3 asserted directly — tests/ is covered by neither static instrument
# ---------------------------------------------------------------------------

_REMOVED_PANEL_MEMBERS = (
    "_show_context_menu",
    "_on_close_position",
    "_on_close_group",
    "_on_ungroup",
    "_on_flatten_all",
    "_selected_row",
    "_selected_position",
    "_on_selection_changed",
    "set_sltp_action",
    "position_close_requested",
    "group_close_requested",
    "flatten_all_requested",
    "position_sltp_changed",
    "group_sltp_changed",
)


def test_removed_panel_members_absent(qapp):
    """P4-T06-T81 (g) / AC7: the nine members, five signals and the policy."""
    from ui.active_portfolio_panel import ActivePortfolioPanel

    panel = ActivePortfolioPanel()
    try:
        for name in _REMOVED_PANEL_MEMBERS:
            assert not hasattr(panel, name), (
                f"ActivePortfolioPanel still has {name!r}")
        policy = panel.positions_table.contextMenuPolicy()
        assert policy != Qt.ContextMenuPolicy.CustomContextMenu, (
            "the positions table still requests a custom context menu")
    finally:
        panel.deleteLater()


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

#: The pre-P5 ``positions``/``trade_groups`` DDL (HEAD before the batch): both
#: stop/target column pairs plus the ``trade_group_id`` FK. The migration must
#: drop exactly the four columns and keep rows, the unique index and the FK.
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
"""


def _write_pre_p5_db(path: Path) -> None:
    """Create a pre-P5 DB: the legacy columns, one trade group, one position."""
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
        conn.commit()
    finally:
        conn.close()


def test_p5_end_state_all_removed_members_absent(monkeypatch):
    """P5-T08-T41 / AC-D46.1, .8, .9, .10, .11, .12 — the direct end state.

    ``tests/`` is covered by neither static instrument, so every P5 removal is
    measured here by the correct measure for its half: ``hasattr`` for the five
    window members and three bridge signals, ``IBApiClient.__dict__`` for the
    three ``ibapi`` overrides, ``find_spec``/``Path.exists()`` for the module and
    the two suites, ``__dataclass_fields__``/``inspect.signature`` for
    ``UserOrder`` and the four stop/target fields, ``hasattr`` for
    ``IdManager.reserve`` with ``get_id``/``set_next_valid_id`` still present,
    and absence of the four order utilities. The schema half runs on a pre-P5
    fixture (``DB_PATH`` routed through ``config.paths._DB_FILENAME``, the
    ``tests/test_db_schema.py`` pattern) and asserts rows, the unique index and
    the FK survive, a second open is a no-op, and a fresh DB has no such column.
    """
    import data.models as models

    from config import paths, settings
    from data.db import DB
    from ibkr import pacing
    from ibkr.account import Position as AccountPosition
    from ibkr.account import build_position_from_ib
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

    # (d) UserOrder and the four stop/target fields (waves 3 and 7)
    assert not hasattr(models, "UserOrder"), "data.models.UserOrder is back"
    for cls in (models.Position, models.TradeGroup, AccountPosition):
        fields = getattr(cls, "__dataclass_fields__", {})
        assert fields, f"{cls!r} is not a dataclass"
        for field_name in ("stop_loss", "take_profit"):
            assert field_name not in fields, (
                f"{cls.__name__} still carries the {field_name!r} field")
    params = inspect.signature(build_position_from_ib).parameters
    for field_name in ("stop_loss", "take_profit"):
        assert field_name not in params, (
            f"build_position_from_ib still takes {field_name!r}")

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

    # (g) the schema end state — pre-P5 fixture, second open, fresh DB
    with tempfile.TemporaryDirectory() as tmp:
        legacy = Path(tmp) / "pre_p5.sqlite3"
        _write_pre_p5_db(legacy)
        monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy))

        upgraded = DB()
        try:
            for table in ("positions", "trade_groups"):
                columns = upgraded._table_columns(table)
                for field_name in ("stop_loss", "take_profit"):
                    assert field_name not in columns, (
                        f"{table} still has the {field_name!r} column")
            rows = upgraded.conn.execute(
                "SELECT symbol, con_id, trade_group_id FROM positions"
            ).fetchall()
            assert rows == [("AAPL", 1, 7)], (
                f"the migration lost or changed a row: {rows!r}")
            index_list = upgraded.conn.execute(
                "PRAGMA index_list(positions)").fetchall()
            unique_indexes = {row[1] for row in index_list if row[2]}
            assert "idx_positions_symbol_con_id" in unique_indexes, (
                f"the unique index was lost: {index_list!r}")
            fks = upgraded.conn.execute(
                "PRAGMA foreign_key_list(positions)").fetchall()
            assert any(
                row[2] == "trade_groups" and row[3] == "trade_group_id"
                and row[4] == "id" for row in fks
            ), f"the trade_group_id FK was lost: {fks!r}"
            first_columns = upgraded._table_columns("positions")
        finally:
            upgraded.conn.close()

        # a second open is a no-op — same columns, same row, same index
        again = DB()
        try:
            assert again._table_columns("positions") == first_columns
            for table in ("positions", "trade_groups"):
                columns = again._table_columns(table)
                for field_name in ("stop_loss", "take_profit"):
                    assert field_name not in columns, (
                        f"a second open re-added {table}.{field_name}")
            assert again.conn.execute(
                "SELECT COUNT(*) FROM positions").fetchone() == (1,)
        finally:
            again.conn.close()

        # a fresh DB is created without the columns at all
        monkeypatch.setattr(paths, "_DB_FILENAME", str(Path(tmp) / "fresh.sqlite3"))
        fresh = DB()
        try:
            for table in ("positions", "trade_groups"):
                columns = fresh._table_columns(table)
                for field_name in ("stop_loss", "take_profit"):
                    assert field_name not in columns, (
                        f"a fresh DB still creates {table}.{field_name}")
            assert "trade_group_id" in fresh._table_columns("positions"), (
                "the frozen trade_group_id column is missing from a fresh DB")
        finally:
            fresh.conn.close()


# ---------------------------------------------------------------------------
# AC7's condition on the one exemption — the columns are *named*, never *used*
# ---------------------------------------------------------------------------

#: The tokens ``_ALLOWED_IN_FILE`` covers, in dict order. Derived, so the shape
#: test below and the scan call site cannot drift apart.
_EXEMPT_TOKENS = tuple(_ALLOWED_IN_FILE)


def _drop_column_subject_nodes(tree: ast.AST) -> set[int]:
    """``id()`` of every constant in a ``DROP COLUMN`` loop's subject tuple.

    ``data/db.py`` spells its migration subject inline::

        for _table in ("positions", "trade_groups"):
            ...
            for _column in ("stop_loss", "take_profit"):
                ...
                self.conn.execute(f"ALTER TABLE {_table} DROP COLUMN {_column}")

    A constant qualifies only when it is an element of the tuple a ``for``
    iterates **and** that loop's body holds a string constant containing
    ``DROP COLUMN`` — i.e. the loop really is the column-dropping migration, not
    any other loop that happens to iterate these strings.
    """
    allowed: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        body_strings = [
            child.value
            for stmt in node.body
            for child in ast.walk(stmt)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
        if not any("DROP COLUMN" in value for value in body_strings):
            continue
        for element in getattr(node.iter, "elts", ()):
            if isinstance(element, ast.Constant):
                allowed.add(id(element))
    return allowed


def test_allowed_in_file_is_narrow_and_named_not_used():
    """P5-T08-T71 (a)-(c) / AC7 — shape, scope, and *named-not-used*, persisted.

    AC7 makes the exemption conditional: ``data/db.py`` must **name** the two
    columns its migration drops and must never **use** them. A (file, token)
    scope cannot see that difference on its own — it exempts every occurrence of
    the token in the file — so the condition is asserted here instead of being
    described in prose (ESC-064): without this test a re-introduced
    ``row.stop_loss`` read or a ``SELECT stop_loss …`` constant inside
    ``data/db.py`` would be exempted exactly like the drop loop's subject.

    (a) the dict is exactly two tokens × one file, and both tokens are still in
    ``_FORBIDDEN`` and still reported by ``_matches``; (b) ``_allowed_in`` is
    True for those two pairings and no other; (c) an AST read of ``data/db.py``
    requires every string constant naming either token to be an element of the
    ``DROP COLUMN`` loop's subject tuple, and no ``Name``/``Attribute``/
    ``arg``/``keyword`` (nor a ``def``/``class``/import alias) to carry one.
    """
    # (a) shape — exactly the two drop subjects, in the one file
    assert _ALLOWED_IN_FILE == {
        "stop_loss": {"data/db.py"},
        "take_profit": {"data/db.py"},
    }, (
        f"_ALLOWED_IN_FILE is not exactly the two drop subjects: "
        f"{_ALLOWED_IN_FILE!r}")
    assert len(_EXEMPT_TOKENS) == 2, (
        f"the exemption widened to {_EXEMPT_TOKENS!r}")
    for token in _EXEMPT_TOKENS:
        assert token in _FORBIDDEN, (
            f"{token!r} left _FORBIDDEN; AC7 keeps it a forbidden token")
        assert _matches(token) == token, (
            f"_matches({token!r}) is {_matches(token)!r}; the exemption must "
            "live at the call site, never inside _matches")

    # (b) scope — True only for ("data/db.py", one of the two tokens)
    for token in _FORBIDDEN:
        for rel in ("data/db.py", "ibkr/account.py", "data/models.py",
                    "ui/main_window.py", "services/sound_service.py"):
            expected = rel == "data/db.py" and token in _EXEMPT_TOKENS
            assert _allowed_in(rel, token) is expected, (
                f"_allowed_in({rel!r}, {token!r}) is {not expected}, "
                f"expected {expected}")

    # (c) named-not-used — data/db.py names the columns, never uses them
    tree = ast.parse((_REPO / "data" / "db.py").read_text())
    subject_nodes = _drop_column_subject_nodes(tree)
    assert subject_nodes, (
        "no `for` loop in data/db.py iterates a tuple while its body contains "
        "a 'DROP COLUMN' string — the migration this exemption exists for is "
        "gone, so the exemption must go too")

    named_in_other_strings: list[str] = []
    named_in_subjects: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        named = [token for token in _EXEMPT_TOKENS if token in node.value]
        if not named:
            continue
        if id(node) in subject_nodes:
            named_in_subjects.update(named)
        else:
            named_in_other_strings.append(
                f"data/db.py:{node.lineno}: string {node.value!r} names {named!r}")
    assert not named_in_other_strings, (
        "data/db.py names a dropped column outside the DROP COLUMN subject "
        "tuple (another SQL string, a docstring, or code):\n  "
        + "\n  ".join(named_in_other_strings))
    for token in _EXEMPT_TOKENS:
        assert token in named_in_subjects, (
            f"data/db.py no longer names {token!r} in its drop-subject tuple; "
            "the file-scoped exemption has nothing left to permit")

    identifier_hits: list[str] = []
    for node in ast.walk(tree):
        name = None
        kind = type(node).__name__
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.arg):
            name = node.arg
        elif isinstance(node, ast.keyword):
            name = node.arg
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.alias):
            name = (node.asname or node.name).split(".")[-1]
        if name in _EXEMPT_TOKENS:
            identifier_hits.append(
                f"data/db.py:{node.lineno}: {kind} names {name!r}")
    assert not identifier_hits, (
        "data/db.py uses a dropped column token as code, not as the migration's "
        "subject:\n  " + "\n  ".join(identifier_hits))

