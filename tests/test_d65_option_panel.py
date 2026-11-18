"""D65 / P23-T2 — OptionSpreadsPanel shell, Target gate, toggle, elide, collapse.

Standalone offscreen integration suite for ``ui/option_spreads_panel``.  It does
not build a ``MainWindow`` for the shell groups and does not wire the panel's
signals to an engine — the panel's ``toggle_clicked`` / ``target_committed``
receivers land in P23-09.

Covered:
* P23-T2-AC1 — header button, CCS/PCS sub-header order, exact header tuple,
  four-row tables, empty-state visibility.
* P23-T2-AC2 — Target default, toggle placement, ``spread_state`` + red/green
  colour, ``toggle_clicked(bool)``.
* P23-T2-AC3 — the S-P23-23 Target gate (accepted edges, every rejection).
* P23-T2-AC4 — 360 px preferred width, ``Ignored`` size policy, name-cell
  tooltip + ellipsis elision.
* P23-T2-AC5 — the D21.13/D44 collapse round trip.

P23-T3 appends the **dock** half (AC-D65.9): the right dock's new identity, the
launch width through the unchanged clamp (wide and narrow fixtures), the retired
names' absence from ``ui/`` and the deletions' completion.
"""

import ast
import re
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QPalette
from PyQt6.QtWidgets import QDockWidget, QHeaderView, QSizePolicy

from ui.dock_layout import (
    CHART_MIN_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    right_dock_max_width,
)
from ui.option_spreads_panel import (
    COLOUR_OFF,
    COLOUR_ON,
    DEFAULT_TARGET,
    HEADERS,
    PREFERRED_WIDTH,
    TARGET_RANGE_MESSAGE,
    OptionSpreadsPanel,
)
from ui.visual_conventions import DiagonalStrikeButton

REPO_ROOT = Path(__file__).resolve().parents[1]


def _panel(qapp, show=True):
    panel = OptionSpreadsPanel()
    if show:
        panel.resize(PREFERRED_WIDTH, 700)
        panel.show()
        qapp.processEvents()
    return panel


def _headers(table):
    return tuple(
        table.horizontalHeaderItem(column).text()
        for column in range(table.columnCount())
    )


def _button_colour(panel):
    """The toggle button's rendered text colour, lower-cased (``#rrggbb``)."""
    return (
        panel.toggle_button.palette()
        .color(QPalette.ColorRole.ButtonText)
        .name()
        .lower()
    )


def _elide_right(text, metrics, width):
    """The test-local elide check standing in for the deleted panel helper."""
    return metrics.elidedText(
        str(text), Qt.TextElideMode.ElideRight, max(int(width), 1)
    )


# ── P23-T2-AC1 ───────────────────────────────────────────────────────────────

def test_P23_T2_AC1_shell_header_tables_and_empty_state(qapp):
    panel = _panel(qapp)
    try:
        # Header: the dock's title-bar control.
        assert isinstance(panel.header_button, DiagonalStrikeButton)
        assert panel.header_button.text() == "Option Spreads"
        assert panel.header_button.isCheckable()
        assert panel.header_button.isChecked()

        # Sub-header order: CCS, its table, PCS, its table.
        layout = panel.body.layout()
        widgets = [
            layout.itemAt(index).widget()
            for index in range(layout.count())
            if layout.itemAt(index).widget() is not None
        ]
        order = [
            widgets.index(panel.ccs_header),
            widgets.index(panel.ccs_table),
            widgets.index(panel.pcs_header),
            widgets.index(panel.pcs_table),
        ]
        assert order == sorted(order) and len(set(order)) == 4

        # Exact column tuple, in order, on both tables.
        for table in (panel.ccs_table, panel.pcs_table):
            assert table.columnCount() == 5
            assert _headers(table) == HEADERS
            assert HEADERS == (
                "Financial instrument", "ASK", "BID", "Delta", "Gamma",
            )
            assert table.rowCount() == 4

        # Empty state: visible while no rows are applied…
        assert panel.empty_label.isVisible()
        # …hidden once a snapshot supplies rows, and both tables keep 4 rows.
        panel.apply_snapshot(["row"] * 4, ["row"] * 4)
        qapp.processEvents()
        assert not panel.empty_label.isVisible()
        assert panel.ccs_table.rowCount() == 4
        assert panel.pcs_table.rowCount() == 4
        assert panel.ccs_table.item(0, 0).text() == "row"
        assert panel.pcs_table.item(3, 0).text() == "row"
    finally:
        panel.close()


# ── P23-T2-AC2 ───────────────────────────────────────────────────────────────

def test_P23_T2_AC2_target_default_toggle_placement_state_and_colour(qapp):
    panel = _panel(qapp)
    try:
        # Target field shows 1.00 and reads back as a float.
        assert panel.target_edit.text() == "1.00"
        assert panel._last_valid_target == pytest.approx(DEFAULT_TARGET)

        # The toggle's left edge is to the right of the Target field's right
        # edge (same controls-row parent, so geometry is comparable).
        assert (
            panel.toggle_button.geometry().left()
            > panel.target_edit.geometry().right()
        )
        assert panel.toggle_button.isCheckable()

        # Default: ON / green.
        assert panel.toggle_button.isChecked() is True
        assert panel.toggle_button.property("spread_state") == "on"
        assert panel.toggle_button.text() == "ON"
        assert _button_colour(panel) == COLOUR_ON
        # Both colour constants live in the state-keyed stylesheet.
        sheet = panel.toggle_button.styleSheet()
        assert '[spread_state="off"]' in sheet and COLOUR_OFF in sheet
        assert '[spread_state="on"]' in sheet and COLOUR_ON in sheet

        # A user click flips state, colour and emits toggle_clicked(False).
        seen = []
        panel.toggle_clicked.connect(seen.append)
        panel.toggle_button.click()
        qapp.processEvents()
        assert seen == [False]
        assert panel.toggle_button.isChecked() is False
        assert panel.toggle_button.property("spread_state") == "off"
        assert panel.toggle_button.text() == "OFF"
        assert _button_colour(panel) == COLOUR_OFF

        # Programmatic flip: property/colour follow, no extra toggle_clicked.
        panel.set_toggle_state(True)
        qapp.processEvents()
        assert panel.toggle_button.isChecked() is True
        assert panel.toggle_button.property("spread_state") == "on"
        assert _button_colour(panel) == COLOUR_ON
        assert seen == [False]
    finally:
        panel.close()


# ── P23-T2-AC3 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "typed,accepted",
    [
        ("0.05", True),
        ("19.95", True),
        ("", False),
        ("abc", False),
        ("0", False),
        ("-1", False),
        ("nan", False),
        ("inf", False),
        ("20.00", False),
    ],
)
def test_P23_T2_AC3_target_gate(qapp, typed, accepted):
    panel = OptionSpreadsPanel()
    try:
        seen = []
        panel.target_committed.connect(seen.append)

        panel.target_edit.setText(typed)
        panel.target_edit.editingFinished.emit()
        qapp.processEvents()

        if accepted:
            assert len(seen) == 1, seen
            assert seen[0] == pytest.approx(float(typed))
            assert panel._last_valid_target == pytest.approx(float(typed))
            # The typed value is kept (normalised to 2 dp).
            assert panel.target_edit.text() == f"{float(typed):.2f}"
        else:
            # No downstream ladder move on a rejected edit.
            assert seen == []
            # The field is restored to the last valid value…
            assert panel.target_edit.text() == "1.00"
            assert panel._last_valid_target == pytest.approx(DEFAULT_TARGET)
            # …and the status label holds ONE message naming the range.
            status = panel.status_label.text()
            assert status == TARGET_RANGE_MESSAGE
            assert len([line for line in status.splitlines() if line.strip()]) == 1
            assert "0.05" in status and "19.95" in status
    finally:
        panel.close()


# ── P23-T2-AC4 ───────────────────────────────────────────────────────────────

def test_P23_T2_AC4_width_policy_tooltip_and_elision(qapp):
    assert OptionSpreadsPanel.PREFERRED_WIDTH == 360
    assert PREFERRED_WIDTH == 360

    panel = _panel(qapp)
    try:
        assert panel.sizeHint().width() == 360
        assert (
            panel.sizePolicy().horizontalPolicy()
            == QSizePolicy.Policy.Ignored
        )

        name = "SPX Nov17 7425/7445"
        panel.apply_snapshot(
            [["SPX Nov17 7425/7445", "1.00", "1.10", "0.500", "0.0123"],
             ["SPX Nov17 7445/7465", "0.90", "1.00", "0.400", "0.0100"],
             ["", "", "", "", ""],
             ["", "", "", "", ""]],
            ["row"] * 4,
        )
        item = panel.ccs_table.item(0, 0)
        assert item.text() == name
        # Every name cell carries the full name as its tooltip.
        assert item.toolTip() == name

        # Right-elide with a trailing ellipsis when the column is narrower than
        # the text (never a hard-truncated cell).
        assert panel.ccs_table.textElideMode() == Qt.TextElideMode.ElideRight
        # Narrow the name column for real (Stretch would re-fill the panel).
        header = panel.ccs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        panel.ccs_table.setColumnWidth(0, 40)
        qapp.processEvents()
        narrow_width = panel.ccs_table.columnWidth(0)
        assert narrow_width <= 44
        elided = _elide_right(name, panel.ccs_table.fontMetrics(), narrow_width)
        assert elided != name
        assert elided.endswith("\u2026")
        assert len(elided) < len(name)
        # Wide enough: the full name is returned unchanged.
        assert _elide_right(name, panel.ccs_table.fontMetrics(), 2000) == name
    finally:
        panel.close()


# ── P23-T2-AC5 ───────────────────────────────────────────────────────────────

def test_P23_T2_AC5_collapse_round_trip(qapp):
    panel = _panel(qapp)
    try:
        panel.apply_snapshot(["row"] * 4, ["row"] * 4)
        qapp.processEvents()

        assert panel.is_collapsed() is False
        assert panel.body.isVisible()
        assert panel.header_button.isChecked()

        # Collapse: body hidden, header unchecked (and struck by VIS-D21.1).
        panel.header_button.click()
        qapp.processEvents()
        assert panel.is_collapsed() is True
        assert not panel.body.isVisible()
        assert not panel.header_button.isChecked()
        assert panel.header_button.is_struck()

        # Expand: body restored, header checked again, every row still there.
        panel.header_button.click()
        qapp.processEvents()
        assert panel.is_collapsed() is False
        assert panel.body.isVisible()
        assert panel.header_button.isChecked()
        assert panel.ccs_table.rowCount() == 4
        assert panel.pcs_table.rowCount() == 4
        assert panel.ccs_table.item(0, 0).text() == "row"
        assert panel.pcs_table.item(0, 0).text() == "row"

        # ``header_button.setChecked`` is the programmatic form of the same
        # contract (the header's ``toggled`` slot owns the body flip).
        panel.header_button.setChecked(False)
        qapp.processEvents()
        assert panel.is_collapsed() is True
        assert not panel.body.isVisible()
        panel.header_button.setChecked(True)
        qapp.processEvents()
        assert panel.is_collapsed() is False
        assert panel.body.isVisible()

        # Clicking the header itself drives the same contract.
        panel.header_button.click()
        qapp.processEvents()
        assert panel.is_collapsed() is True
        assert not panel.body.isVisible()
        panel.header_button.click()
        qapp.processEvents()
        assert panel.is_collapsed() is False
        assert panel.body.isVisible()
    finally:
        panel.close()


# ── P23-T3 — dock swap, rename, launch width (AC-D65.9 / S-P23-16) ───────────
#
# The dock half of D65: the right region hosts this panel, its identity is
# "Option Spreads", and the panel's PREFERRED_WIDTH is the remembered launch
# request — clamped once through the unchanged ``plan_dock_widths`` model.

def _make_window(monkeypatch, qapp, width=1600, height=900):
    """Build a shown ``MainWindow`` that never touches TWS.

    Two ``processEvents`` passes: the first runs the deferred dock setup (which
    issues the launch ``resizeDocks``), the second lets the dock area apply it.
    """
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()
    qapp.processEvents()
    return win


# ── P23-T3-AC1 — the dock's new identity ─────────────────────────────────────

def test_P23_T3_AC1_dock_identity(monkeypatch, qapp):
    from ui.main_window import MainWindow  # noqa: F401  (clean import)

    win = _make_window(monkeypatch, qapp)
    try:
        dock = win.right_dock
        assert isinstance(dock, QDockWidget)

        # Title AND objectName are the new identity; the title bar is the
        # panel's own header button.
        assert dock.windowTitle() == "Option Spreads"
        assert dock.objectName() == "Option Spreads"
        assert dock.titleBarWidget() is win.option_spreads_panel.header_button

        # The dock hosts the panel, and its widget is the window's attribute.
        assert isinstance(win.option_spreads_panel, OptionSpreadsPanel)
        assert dock.widget() is win.option_spreads_panel

        # D18 Phase 4's floor is unchanged by the swap.
        assert dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH

        # The objectName lookup the helper suites use resolves THIS dock.
        assert win.findChild(QDockWidget, "Option Spreads") is dock

        # No dock carries the retired identity, by either key.
        for other in win.findChildren(QDockWidget):
            assert other.windowTitle() != "Portfolio"
            assert other.objectName() != "Portfolio"
    finally:
        win.close()


# ── P23-T3-AC2 — the rename, and the handlers that survive it ────────────────

_UI_DIR = REPO_ROOT / "ui"
_RETIRED_UI_NAMES = ("portfolio_panel", "positions_table", "ActivePortfolioPanel")
_RETIRED_PANEL_METHODS = (
    "set_account_summary", "set_account_id", "set_account_unavailable",
    "set_positions", "add_position",
)


def test_P23_T3_AC2_retired_names_absent_from_ui():
    offenders = []
    for path in sorted(_UI_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        identifiers = {node.id for node in ast.walk(tree)
                       if isinstance(node, ast.Name)}
        identifiers |= {node.attr for node in ast.walk(tree)
                        if isinstance(node, ast.Attribute)}
        for token in _RETIRED_UI_NAMES:
            # Raw text catches docstrings/comments/imports too; the AST set
            # catches a spelling this file's own source cannot hide.
            if token in text or token in identifiers:
                offenders.append(f"{path.name}:{token}")
    assert not offenders, f"retired names under ui/: {offenders}"

    main_source = (_UI_DIR / "main_window.py").read_text(encoding="utf-8")
    for method in _RETIRED_PANEL_METHODS:
        assert method not in main_source, method


# ── P23-T3-AC3 — the launch width is derived, never persisted ────────────────

def test_P23_T3_AC3_launch_width_derived(monkeypatch, qapp):
    def _expected(win):
        return max(
            RIGHT_DOCK_MIN_WIDTH,
            min(OptionSpreadsPanel.PREFERRED_WIDTH,
                right_dock_max_width(win._chart_area_width())),
        )

    win = _make_window(monkeypatch, qapp)
    try:
        ca = win._chart_area_width()
        assert win._right_dock_width == _expected(win)
        # The 40% cap on this fixture's chart area cannot bind: the preferred
        # width is what lands, not the 200px floor.
        assert right_dock_max_width(ca) >= OptionSpreadsPanel.PREFERRED_WIDTH
        assert win._right_dock_width == OptionSpreadsPanel.PREFERRED_WIDTH
        assert win.right_dock.width() == OptionSpreadsPanel.PREFERRED_WIDTH

        # Derived, never persisted: no right-region QSettings key exists (the
        # macOS-scoped keys QSettings also exposes are not ours to name).
        keys = list(win._settings.allKeys())
        forbidden = ("right_dock", "right_region", "portfolio", "option_spread")
        offenders = [
            key for key in keys
            if any(token in key.lower() for token in forbidden)
        ]
        assert not offenders, offenders
    finally:
        win.close()

    # A freshly rebuilt window reaches the same launch width (a restart returns
    # the derived default, never the last dragged width).
    win2 = _make_window(monkeypatch, qapp)
    try:
        assert win2._right_dock_width == _expected(win2)
        assert win2._right_dock_width == OptionSpreadsPanel.PREFERRED_WIDTH

        # A below-minimum drag still floors at RIGHT_DOCK_MIN_WIDTH.
        win2._apply_dock_widths(None, 0)
        qapp.processEvents()
        assert win2._right_dock_width == RIGHT_DOCK_MIN_WIDTH
        assert win2.right_dock.width() == RIGHT_DOCK_MIN_WIDTH

        # The D44 collapsed strip is unchanged: collapse pins the region to the
        # computed button-strip width, expand restores the 200px floor.
        collapsed_w = win2._right_dock_collapsed_min_width
        win2.option_spreads_panel.header_button.click()
        qapp.processEvents()
        assert win2.right_dock.minimumWidth() == collapsed_w
        assert win2.right_dock.width() <= collapsed_w + 2
        win2.option_spreads_panel.header_button.click()
        qapp.processEvents()
        assert win2.right_dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win2.close()


# ── P23-T3-AC4 — wide: no elision; narrow: the cap wins, elision is real ─────

def test_P23_T3_AC4_wide_and_narrow_fixtures(monkeypatch, qapp):
    name = "SPX Nov17 7425/7445"
    pcs_name = "SPX Nov17 7340/7320"
    row = [name, "1.00", "1.10", "0.500", "0.0123"]
    pcs_row = [pcs_name, "0.90", "1.00", "0.400", "0.0100"]

    # ── Wide fixture (1600x900): the preferred width lands, nothing elides ──
    wide = _make_window(monkeypatch, qapp, 1600, 900)
    try:
        panel = wide.option_spreads_panel
        panel.apply_snapshot([row] * 4, [pcs_row] * 4)
        qapp.processEvents()

        assert wide.right_dock.width() >= 340, wide.right_dock.width()
        for table in (panel.ccs_table, panel.pcs_table):
            metrics = table.fontMetrics()
            name_column = table.columnWidth(0)
            for index in range(table.rowCount()):
                item = table.item(index, 0)
                text_width = metrics.horizontalAdvance(item.text())
                assert text_width <= name_column, (
                    item.text(), text_width, name_column
                )
        wide_name_column = panel.ccs_table.columnWidth(0)
    finally:
        wide.close()

    # ── Narrow fixture (900x700): the 40% cap wins outright ─────────────────
    # The pure cap fact the AC cites: a 680px chart area yields 272px, exactly
    # 88px below the preferred width. (680 is 900 - 220, the region left of the
    # watchlist; the real window's own chart area is smaller still, because the
    # right dock consumes its own width — so the settled dock is the 200px
    # floor. The cap binds either way; the elision path is what this case
    # proves, on real margin.)
    assert right_dock_max_width(680) == 272
    assert OptionSpreadsPanel.PREFERRED_WIDTH - 272 == 88

    narrow = _make_window(monkeypatch, qapp, 900, 700)
    try:
        panel = narrow.option_spreads_panel
        panel.apply_snapshot([row] * 4, [pcs_row] * 4)
        qapp.processEvents()

        # The cross-clamp settles the left dock at its floor and the region at
        # RIGHT_DOCK_MIN_WIDTH; the chart keeps its own minimum.
        assert narrow.watchlist_dock.width() == 150
        assert narrow.right_dock.width() == RIGHT_DOCK_MIN_WIDTH
        assert narrow._right_dock_width == RIGHT_DOCK_MIN_WIDTH
        assert narrow._chart_area_width() >= CHART_MIN_WIDTH
        # The preferred width is never reached here.
        assert narrow.right_dock.width() < OptionSpreadsPanel.PREFERRED_WIDTH

        table = panel.ccs_table
        narrow_name_column = table.columnWidth(0)
        assert narrow_name_column <= (2 * wide_name_column) // 3, (
            narrow_name_column, wide_name_column
        )
        # The name no longer fits: the elide + tooltip path is taken, with real
        # margin, and the tooltip still carries the full name.
        metrics = table.fontMetrics()
        assert metrics.horizontalAdvance(name) > narrow_name_column
        elided = _elide_right(name, metrics, narrow_name_column)
        assert elided != name
        assert elided.endswith("\u2026")
        assert table.item(0, 0).toolTip() == name
        assert table.item(0, 0).text() == name
    finally:
        narrow.close()


# ── P23-T3-AC5 — the D18 region suite is re-pointed, not patched around ─────

def test_P23_T3_AC5_d18_region_suite_repointed():
    text = (REPO_ROOT / "tests" / "test_dock_d18_region.py").read_text(
        encoding="utf-8"
    )
    # The retired module import would be a collection error for the whole file.
    assert "active_portfolio_panel" not in text
    # The two hasattr probes and the _receiver_count helper went with their
    # only call site.
    assert "account_summary_changed" not in text
    assert "positions_changed" not in text
    assert "_receiver_count" not in text
    assert "portfolio_panel" not in text
    assert "positions_table" not in text
    # ...and the group asserts on the new panel / identity.
    assert "OptionSpreadsPanel" in text
    assert 'findChild(QDockWidget, "Option Spreads")' in text
    assert "header_button" in text
    assert "is_collapsed" in text


# ── P23-T3-AC6 — the deletions, the allowlist and a clean window import ─────

def test_P23_T3_AC6_deletions_and_allowlist():
    assert not (_UI_DIR / "active_portfolio_panel.py").exists()
    for suite in (
        "test_d41_portfolio_dock.py",
        "test_d27_account_subs.py",
        "test_d27_account_scoping.py",
        "test_d27_account_partial_window.py",
        "test_d27_flat_rows.py",
        "test_d27_position_id.py",
        "test_d27_position_prices.py",
    ):
        assert not (REPO_ROOT / "tests" / suite).exists(), suite

    gate = (REPO_ROOT / "tests" / "test_p13_gate.py").read_text(encoding="utf-8")
    assert '"option_spreads_panel.py"' in gate
    assert "active_portfolio_panel" not in gate

    # ``ui.main_window`` imported cleanly with the module deleted — this suite's
    # own collection is the proof; assert the symbol to make it explicit.
    import ui.main_window as main_window

    assert hasattr(main_window, "MainWindow")


# ── P23-T19 — the seven test-only accessors are gone (ESC-121) ───────────────
#
# Under AC-D65.12(i) no member without a production reader survives: the
# assertions these helpers carried moved to the production surfaces the app
# itself uses (the Target field, the toggle button, the header button,
# ``PREFERRED_WIDTH``/``sizeHint`` and the table's own elide mode).

_DELETED_PANEL_ACCESSORS = (
    "target_value",
    "toggle_colour",
    "toggle_state",
    "toggle_collapsed",
    "set_collapsed",
    "preferred_width",
    "elided_name",
)

_P23_T19_SUITES = (
    REPO_ROOT / "tests" / "test_d65_option_panel.py",
    REPO_ROOT / "tests" / "test_d65_option_stream.py",
    REPO_ROOT / "tests" / "test_d45_removal.py",
)


def test_P23_T19_AC1_seven_test_only_accessors_are_deleted():
    import ui.option_spreads_panel as module

    # Not one of the seven is a panel member any more.
    for name in _DELETED_PANEL_ACCESSORS:
        assert name not in vars(OptionSpreadsPanel), name

    # The module docstring no longer names them…
    doc = module.__doc__ or ""
    for name in _DELETED_PANEL_ACCESSORS:
        assert re.search(rf"\b{name}\b", doc) is None, name

    # …and no replacement helper re-introduces one. A word boundary keeps the
    # surviving ``set_toggle_state`` / ``set_target_value`` from matching.
    source = (_UI_DIR / "option_spreads_panel.py").read_text(encoding="utf-8")
    for name in _DELETED_PANEL_ACCESSORS:
        assert re.search(rf"\b{name}\b", source) is None, name

    # The production surface the app uses is intact.
    for name in (
        "set_target_value",
        "set_toggle_state",
        "is_collapsed",
        "sizeHint",
        "PREFERRED_WIDTH",
    ):
        assert name in vars(OptionSpreadsPanel), name


def test_P23_T19_AC2_every_fact_still_asserted_on_the_production_surface(qapp):
    panel = _panel(qapp)
    try:
        # The accepted Target: the field's text and the last accepted value.
        assert panel.target_edit.text() == "1.00"
        assert panel._last_valid_target == pytest.approx(DEFAULT_TARGET)
        panel.set_target_value(2.00)
        assert panel.target_edit.text() == "2.00"
        assert panel._last_valid_target == pytest.approx(2.00)

        # The toggle: isChecked(), the spread_state property, the palette.
        assert panel.toggle_button.isChecked() is True
        assert panel.toggle_button.property("spread_state") == "on"
        assert _button_colour(panel) == COLOUR_ON
        panel.toggle_button.click()
        assert panel.toggle_button.isChecked() is False
        assert panel.toggle_button.property("spread_state") == "off"
        assert _button_colour(panel) == COLOUR_OFF
        panel.set_toggle_state(True)
        assert panel.toggle_button.isChecked() is True
        assert panel.toggle_button.property("spread_state") == "on"
        assert _button_colour(panel) == COLOUR_ON

        # Collapse: header_button click / setChecked + is_collapsed().
        assert panel.is_collapsed() is False
        panel.header_button.click()
        assert panel.is_collapsed() is True
        assert not panel.body.isVisible()
        panel.header_button.click()
        assert panel.is_collapsed() is False
        assert panel.body.isVisible()
        panel.header_button.setChecked(False)
        assert panel.is_collapsed() is True
        assert not panel.body.isVisible()
        panel.header_button.setChecked(True)
        assert panel.is_collapsed() is False
        assert panel.body.isVisible()

        # The 360 px width: the class constant and the size hint.
        assert OptionSpreadsPanel.PREFERRED_WIDTH == 360
        assert OptionSpreadsPanel.PREFERRED_WIDTH == PREFERRED_WIDTH
        assert panel.sizeHint().width() == 360

        # Right-elision: the table's own mode, its tooltip, and a test-local
        # QFontMetrics check in place of the deleted helper.
        name = "SPX Nov17 7425/7445"
        panel.apply_snapshot(
            [[name, "1.00", "1.10", "0.500", "0.0123"]], []
        )
        table = panel.ccs_table
        assert table.textElideMode() == Qt.TextElideMode.ElideRight
        assert panel.pcs_table.textElideMode() == Qt.TextElideMode.ElideRight
        assert table.item(0, 0).text() == name
        assert table.item(0, 0).toolTip() == name
        narrow = QFontMetrics(table.font()).horizontalAdvance("SPX Nov17 74")
        elided = _elide_right(name, table.fontMetrics(), narrow)
        assert elided != name
        assert elided.endswith("\u2026")
        assert len(elided) < len(name)
        assert _elide_right(name, table.fontMetrics(), 2000) == name
    finally:
        panel.close()


def test_P23_T19_AC2_d45_walkthrough_drives_the_header_button():
    text = (REPO_ROOT / "tests" / "test_d45_removal.py").read_text(
        encoding="utf-8"
    )
    assert "option_spreads_panel.header_button.click()" in text
    assert "toggle_collapsed" not in text
    assert "set_collapsed" not in text


def test_P23_T19_AC3_suites_reference_no_deleted_member():
    """The exit-0 half is the task's own ``pytest`` command; this is the
    no-reference half, measured on attribute/name use (a string that merely
    names a retired member in the guard list is not a reference)."""
    offenders: list[str] = []
    for path in _P23_T19_SUITES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                used.add(node.attr)
            elif isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                used.add(node.name)
        for name in _DELETED_PANEL_ACCESSORS:
            if name in used:
                offenders.append(f"{path.name}:{name}")
    assert not offenders, offenders

