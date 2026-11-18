"""P23-T26 — the AC-D65.19 acceptance record and its index entry.

The record is the phase's only owner-run gate: every suite uses fakes, so a real
TWS session is the sole evidence that quotes and greeks arrive and that OFF
releases lines. These cases assert the *checklist*, never a run: all six items
must still read PENDING, because the build records no result.

AC-D65.19 was amended on 2026-11-18 (A211): the acceptance is the owner's live
TWS on ``127.0.0.1:7496``, read-only by construction and observation-only. The
file name is retained for existing references; its content describes the live
run.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RECORD = REPO / "docs/archive/probe_records/d65_paper_tws_acceptance.md"
INDEX = REPO / "docs/archive/probe_records/INDEX.md"

ITEM_HEADING = re.compile(r"^### \((\d)\) ", re.M)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """Collapse markdown wrapping so a sentence can be asserted as written."""
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# AC1 — the environment: live TWS, read-only by construction, observation-only
# ---------------------------------------------------------------------------


def test_record_states_the_live_tws_read_only_environment():
    text = _text(RECORD)
    for phrase in (
        "127.0.0.1:7496",
        "read-only",
        "observation-only",
        "cancelMktData",
        "zero order code",
    ):
        assert phrase in text, f"the record does not state {phrase!r}"

    for banned in (
        "paper port",
        "never the live port",
        "Paper account",
        "IB Gateway paper",
    ):
        assert banned not in text, f"the record still carries {banned!r}"

    assert (
        "Nothing in the checklist asks the owner to place, modify or cancel an order"
        in _flat(text)
    ), "the record must forbid every order-shaped request to the owner"
    assert "The only cancel in the run is a market-data line" in _flat(text), (
        "the record must say the run's only cancel is a market-data line"
    )


# ---------------------------------------------------------------------------
# AC2 — six checks, in order, PENDING; the fixed numbers; the evidence slots
# ---------------------------------------------------------------------------


def test_record_carries_the_six_checks_in_order_and_all_pending():
    text = _text(RECORD)
    headings = list(ITEM_HEADING.finditer(text))
    assert [int(m.group(1)) for m in headings] == [1, 2, 3, 4, 5, 6], (
        "the record must carry the six AC-D65.19 items in order"
    )

    table_start = text.index("## TWS market-data line count")
    starts = [m.start() for m in headings]
    ends = starts[1:] + [table_start]
    for number, start, end in zip((1, 2, 3, 4, 5, 6), starts, ends):
        section = text[start:end]
        assert "**Result:** PENDING" in section, f"item ({number}) is not PENDING"
        assert re.search(r"\*\*Evidence:\*\* _\(empty", section), (
            f"item ({number}) must leave its evidence field empty"
        )

    assert text.count("**Result:** PENDING") == 6, "a sixth result line is missing"
    for outcome in ("**ACCEPTED**", "**REJECTED**", "**WAIVED**"):
        assert f"- [ ] {outcome}" in text, f"the {outcome} box must be unchecked"


def test_record_states_the_fixed_numbers_and_evidence_slots():
    text = _text(RECORD)
    for phrase in (
        "h = max(0.05, one_tick)",
        "ASK = long.ask - short.bid",
        "BID = long.bid - short.ask",
        "long - short",
        "7425/7445",
        "7340/7320",
        "at most 17",
        "returns to the pre-ON baseline",
    ):
        assert phrase in text, f"the record does not state {phrase!r}"

    for row in ("Before ON (baseline)", "While ON", "After OFF"):
        assert row in text, f"the line-count table lost its {row!r} row"
    assert "## Screenshots and notes" in text, "the screenshots/notes slot is gone"


def test_header_names_the_build_commit_and_the_d48_d52_precedent():
    text = _text(RECORD)
    match = re.search(r"Build commit: `([0-9a-f]{7,40})` \(`([0-9a-f]{40})`\)", text)
    assert match, "the header must name the build commit the checklist describes"
    assert match.group(2).startswith(match.group(1)), (
        "the short commit must be the long commit's prefix"
    )

    for phrase in (
        "D48",
        "D52",
        "d48_probe_record.md",
        "d52_probe_record.md",
        "127.0.0.1:7496",
    ):
        assert phrase in text, f"the header/precedent does not cite {phrase!r}"


# ---------------------------------------------------------------------------
# AC3 — the probe-records index lists the record like its neighbours
# ---------------------------------------------------------------------------


def test_index_lists_the_record_in_the_three_column_table():
    text = _text(INDEX)
    assert "| Record | Evidence for | Phase / decision |" in text

    rows = [
        line
        for line in text.splitlines()
        if line.startswith("|") and "d65_paper_tws_acceptance.md" in line
    ]
    assert len(rows) == 1, f"expected exactly one D65 index row, found {rows}"
    row = rows[0]

    for phrase in (
        "d65_paper_tws_acceptance.md",
        "AC-D65.19",
        "P23-T26",
        "live",
        "PENDING",
        "no result recorded",
    ):
        assert phrase in row, f"the D65 index row does not name {phrase!r}"

    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    assert len(cells) == 3, f"the D65 row is not three columns: {cells}"

    d48 = next(
        line
        for line in text.splitlines()
        if line.startswith("| `d48_probe_record.md`")
    )
    assert len(d48.strip().strip("|").split("|")) == 3, (
        "the neighbouring d48 row is not the same three-column shape"
    )
    assert text.index(row) > text.index(d48), "the D65 row belongs after its neighbours"
