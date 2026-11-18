"""D66 / P24-T3 — the restated-contract fence.

One assertion per artefact P24 restates (``AC-D66.1``, ``AC-D66.3``-``AC-D66.8``).
Every value is read from the live modules or the recorded documents; no literal
is copied into a fixture.  The fence pins:

* the panel's Target gate, its two toggle colours and the ladder's geometry;
* the eight rendered instrument names, short-leg-first ``MmmDD``;
* four rows a side with the PCS anchor on row 2 and the CCS anchor on row 3,
  exactly the five named columns, and no rendered row number (Q117);
* the toggle's Target-row placement and its on/off/on state sequence, and the
  Target's two accepted edges and two rejections (``AC-D66.3``/``AC-D66.4``);
* the five recorded ``[revises P23, 2026-11-18`` notes and the retired
  "one table on both sides" phrases (``AC-D66.7``).

The delta-scope record (``AC-D66.8``) is a build artefact, not a test: a git
diff pinned inside pytest would redden every later phase (S-P24-5).
"""

import re
from datetime import date
from pathlib import Path

import pytest
from PyQt6.QtGui import QPalette

from services.option_ladder import (
    SPREAD_WIDTH,
    STRIKE_STEP,
    format_instrument,
    ladder_pairs,
)
from ui.option_spreads_panel import (
    COLOUR_OFF,
    COLOUR_ON,
    DEFAULT_TARGET,
    HEADERS,
    MIN_ROWS,
    TARGET_MAX,
    TARGET_MIN,
    TARGET_RANGE_MESSAGE,
    OptionSpreadsPanel,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
LADDER_MODULE = REPO_ROOT / "services" / "option_ladder.py"

EXPIRY = date(2026, 11, 17)
CCS_ANCHOR = 7425.0
PCS_ANCHOR = 7325.0

#: ``AC-D66.1``'s regex, verbatim: ``MmmDD`` expiry, short leg first.
NAME_RE = r"^SPX (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:[1-9]|[12]\d|3[01]) \d+(?:\.\d+)?/\d+(?:\.\d+)?$"

#: ``AC-D66.7``'s recorded-revision marker prefix.
REVISION_MARKER = "[revises P23, 2026-11-18"

#: The sentences DG127 retired from the ladder module.
RETIRED_PHRASES = (
    "both sides",
    "identically on both sides",
    "same offset table on both sides",
)

#: The five ``AC-D66.7`` sites, each named by the identifier line it sits on.
REVISION_SITES = (
    ("the P23 glossary's anchor entry", "**Spread 3 (the anchor):**"),
    ("AC-D65.2", "- **AC-D65.2 ("),
    ("A187", "- **A187 —"),
    ("A212", "- **A212 —"),
    ("R142", "| R142 —"),
)


def _panel(qapp):
    panel = OptionSpreadsPanel()
    panel.resize(360, 700)
    panel.show()
    qapp.processEvents()
    return panel


def _row(short, long):
    """One snapshot row: the rendered name plus four dummy display cells."""
    return [
        format_instrument("SPX", EXPIRY, short, long),
        "1.00", "1.10", "0.500", "0.0123",
    ]


def _headers(table):
    return tuple(
        table.horizontalHeaderItem(column).text()
        for column in range(table.columnCount())
    )


def _button_colour(panel):
    """The toggle's rendered text colour, lower-cased (``#rrggbb``)."""
    return (
        panel.toggle_button.palette()
        .color(QPalette.ColorRole.ButtonText)
        .name()
        .lower()
    )


# ── AC-D66.8 / AC-D66.2 — the live constants ────────────────────────────────

def test_constants_are_pinned_from_the_live_modules():
    assert DEFAULT_TARGET == 1.00
    assert TARGET_MIN == 0.05
    assert TARGET_MAX == 19.95
    assert COLOUR_OFF == "#ef4444"
    assert COLOUR_ON == "#22c55e"
    assert COLOUR_OFF != COLOUR_ON
    assert MIN_ROWS == 4
    assert SPREAD_WIDTH == 20
    assert STRIKE_STEP == 5
    assert SPREAD_WIDTH == 4 * STRIKE_STEP


# ── AC-D66.1 — the rendered name format ─────────────────────────────────────

def test_eight_rendered_names_match_the_ac_d66_1_regex():
    pairs = list(ladder_pairs(CCS_ANCHOR)) + list(ladder_pairs(PCS_ANCHOR, "PCS"))
    assert len(pairs) == 8

    names = [
        format_instrument("SPX", EXPIRY, short, long) for short, long in pairs
    ]
    for name in names:
        assert re.fullmatch(NAME_RE, name), name

    # Short leg first, on both sides.
    for (short, long), name in zip(pairs, names):
        assert name.endswith(f"{int(short)}/{int(long)}"), name

    # The corrected PCS anchor pair, and the untouched CCS anchor pair.
    assert "SPX Nov17 7325/7305" in names
    assert "SPX Nov17 7425/7445" in names

    # The convention is a regex, not prose: both malformed shapes are rejected.
    assert re.fullmatch(NAME_RE, "SPX 2026-11-17 7330/7310") is None
    assert re.fullmatch(NAME_RE, "SPX Nov07 7330/7310") is None


# ── AC-D66.5 / AC-D66.6 / Q117 — the rendered tables ────────────────────────

def test_tables_show_four_rows_with_the_anchors_on_rows_two_and_three(qapp):
    panel = _panel(qapp)
    try:
        ccs_rows = [_row(short, long) for short, long in ladder_pairs(CCS_ANCHOR)]
        pcs_rows = [
            _row(short, long) for short, long in ladder_pairs(PCS_ANCHOR, "PCS")
        ]
        panel.apply_snapshot(ccs_rows, pcs_rows)
        qapp.processEvents()

        for table in (panel.ccs_table, panel.pcs_table):
            assert table.rowCount() == MIN_ROWS == 4
            assert table.columnCount() == len(HEADERS) == 5
            assert _headers(table) == HEADERS
            assert HEADERS == (
                "Financial instrument", "ASK", "BID", "Delta", "Gamma",
            )
            # No row-number column anywhere (Q117).
            assert not table.verticalHeader().isVisible()
            for index in range(table.rowCount()):
                text = table.item(index, 0).text()
                assert not re.match(r"^\s*\d", text), text
                assert not re.match(r"^\d+\s", text), text

        # The offset-0 anchor pair: PCS row 2, CCS row 3.
        assert "7325/7305" in panel.pcs_table.item(1, 0).text()
        assert "7425/7445" in panel.ccs_table.item(2, 0).text()
        # And only the anchor row carries that exact pair.
        pcs_names = [panel.pcs_table.item(i, 0).text() for i in range(4)]
        ccs_names = [panel.ccs_table.item(i, 0).text() for i in range(4)]
        assert sum("7325/7305" in name for name in pcs_names) == 1
        assert sum("7425/7445" in name for name in ccs_names) == 1
    finally:
        panel.close()


# ── AC-D66.3 / AC-D66.4 — the toggle and the Target ─────────────────────────

def test_toggle_and_target_contract(qapp):
    panel = _panel(qapp)
    try:
        # The toggle sits in the Target row, right of the field, at the
        # panel's content edge.
        assert panel.toggle_button.parent() is panel.controls_row
        assert (
            panel.toggle_button.geometry().left()
            > panel.target_edit.geometry().right()
        )
        content_edge = panel.controls_row.contentsRect().right()
        assert abs(panel.toggle_button.geometry().right() - content_edge) <= 1, (
            panel.toggle_button.geometry().right(), content_edge
        )

        # Default ON, then OFF, then ON again.
        assert panel.toggle_button.property("spread_state") == "on"
        assert panel.toggle_button.text() == "ON"
        assert _button_colour(panel) == COLOUR_ON

        panel.set_toggle_state(False)
        assert panel.toggle_button.property("spread_state") == "off"
        assert panel.toggle_button.text() == "OFF"
        assert _button_colour(panel) == COLOUR_OFF

        panel.set_toggle_state(True)
        assert panel.toggle_button.property("spread_state") == "on"
        assert panel.toggle_button.text() == "ON"
        assert _button_colour(panel) == COLOUR_ON

        # The Target gate: the two accepted edges, then two rejections.
        seen = []
        panel.target_committed.connect(seen.append)
        for typed in ("0.05", "19.95"):
            panel.target_edit.setText(typed)
            panel.target_edit.editingFinished.emit()
            qapp.processEvents()
            assert seen[-1] == pytest.approx(float(typed))
            assert panel.target_edit.text() == f"{float(typed):.2f}"

        for typed in ("0.04", "19.96"):
            panel.target_edit.setText(typed)
            panel.target_edit.editingFinished.emit()
            qapp.processEvents()
            assert seen == pytest.approx([0.05, 19.95]), seen
            assert panel.target_edit.text() == "19.95"
            status = panel.status_label.text()
            assert status == TARGET_RANGE_MESSAGE
            assert len([line for line in status.splitlines() if line.strip()]) == 1
    finally:
        panel.close()


# ── AC-D66.7 — the recorded history and the retired phrases ─────────────────

def test_five_revision_notes_sit_at_their_named_sites():
    text = REQUIREMENTS.read_text(encoding="utf-8")
    for site, identifier in REVISION_SITES:
        lines = [line for line in text.splitlines() if identifier in line]
        assert lines, f"{site}: identifier {identifier!r} not found"
        assert any(REVISION_MARKER in line for line in lines), (
            f"{site}: no {REVISION_MARKER!r} note on its identifier line"
        )


def test_retired_phrases_are_absent_from_the_ladder_module():
    source = LADDER_MODULE.read_text(encoding="utf-8")
    for phrase in RETIRED_PHRASES:
        assert phrase not in source, phrase
