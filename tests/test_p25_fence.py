"""P25 / P25-T5 — the phase fence (``AC-D70.3`` and the four D67–D70 seams).

One assertion per named artefact the phase relies on. Every value is read from
the live document or module; no value is copied into a fixture beyond the
record's own permanent identifiers. The fence pins:

* the requirements record's existing-repository marker, the ``D41``–``D66``
  record (presence per id in a heading — the record is mixed: ``### D41``–
  ``### D53`` are defect entries while ``D54``–``D66`` sit in their
  ``## Phase P<n>`` headers and ``#### Journey`` titles, so ``AC-D70.3``'s
  ``### D41``–``### D66`` is shorthand for that record), P25's own
  ``#### D67``–``#### D70`` entries, ``Journey 65``–``Journey 67``, the
  ``AC-D1.1``–``AC-D66.8`` and ``AC-D67.1``–``AC-D70.3`` acceptance ids,
  ``A1``–``A224`` and ``R1``–``R164``, and the ``Current Tech Stack`` section;
* the three **module-level** bridge constants (``ui.lwc_bridge``, not
  ``LwBridge`` attributes), and the page's one marker colour constant, which
  must differ from the up/down candle colours.

The delta-scope record (``git diff --name-only <base>`` against the phase
allowlist) is a build artefact, not a test: a git diff pinned inside pytest
would redden every later phase (P24's precedent, S-P24-5). It is recorded in
the wave result beside the allowlist, with gates **G1**/**G2** named as
owner-run and never claimed as satisfied.

No literal count of files, lines or ops appears here: a later phase must not
redden this fence.
"""

import re
from pathlib import Path

from ui import lwc_bridge as LB

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
CHART_JS = REPO_ROOT / "chart_assets" / "lwc" / "chart.js"

#: ``AC-D70.3``'s marker sentence, verbatim.
EXISTING_REPO_MARKER = "This is an existing repository."

#: The section ``AC-D70.3`` requires the record to keep.
TECH_STACK_HEADING = "**Current Tech Stack:**"

#: ``AC-D70.3``'s shorthand span, ``### D41``–``### D66``, as presence per id.
RECORD_DEFECT_IDS = tuple(range(41, 67))

#: P25's own four defect entries (``####`` headings, not ``###``).
P25_DEFECT_HEADINGS = ("#### D67", "#### D68", "#### D69", "#### D70")

#: P25's three journeys.
P25_JOURNEY_HEADINGS = ("#### Journey 65", "#### Journey 66", "#### Journey 67")

#: The ten acceptance ids P25 states, verbatim.
P25_AC_IDS = (
    "AC-D67.1", "AC-D67.2", "AC-D67.3",
    "AC-D68.1", "AC-D68.2",
    "AC-D69.1", "AC-D69.2",
    "AC-D70.1", "AC-D70.2", "AC-D70.3",
)

#: Defect numbers in ``1..66`` the record gives no acceptance criteria of its
#: own: ``D29``–``D35`` were never opened (the numbering jumps ``D28``→``D36``)
#: and ``D42``/``D43`` are REQUIREMENTS resolutions with no criteria.
AC_LESS_DEFECTS = frozenset({29, 30, 31, 32, 33, 34, 35, 42, 43})

#: ``AC-D1.1``–``AC-D66.8``: the span's endpoints, plus one criterion per
#: defect that has one. Both are asserted below.
AC_SPAN_ENDPOINTS = ("AC-D1.1", "AC-D66.8")

#: ``A1``–``A219`` plus ``A220``–``A224``.
ASSUMPTION_IDS = tuple(range(1, 225))

#: ``R1``–``R159`` plus ``R160``–``R164``.
REQUIREMENT_RULE_IDS = tuple(range(1, 165))

#: The three module-level bridge constants the phase must not drift.
BRIDGE_CONSTANTS = (
    ("ENVELOPE_VERSION", 1),
    ("COALESCE_MS", 33),
    ("LIVE_OPS", frozenset({"update_bar"})),
)

#: The page's marker colour constant and the two candle colours it must differ
#: from (``chart.js`` declares all three as ``var NAME = "#rrggbb"``).
MARKER_COLOUR_CONSTANT = "PARTIAL_MARKER_COLOR"
CANDLE_COLOUR_CONSTANTS = ("LW_UP_COLOR", "LW_DOWN_COLOR")

_COLOUR_DECLARATION = r'var\s+{name}\s*=\s*"([^"]+)"'


def _requirements_text():
    return REQUIREMENTS.read_text(encoding="utf-8")


def _headings(text):
    return [line for line in text.splitlines() if line.startswith("#")]


def _id_pattern(prefix, number):
    """``prefix+number`` as a whole identifier (never ``A1`` inside ``A148``)."""
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(prefix)}{number}(?![0-9])")


def _page_colour(name):
    match = re.search(_COLOUR_DECLARATION.format(name=name), CHART_JS.read_text(encoding="utf-8"))
    assert match, f"chart.js declares no colour constant {name!r}"
    return match.group(1)


# ── AC-D70.3 — the requirements record is intact ────────────────────────────

def test_requirements_marker_sentence_is_present():
    assert EXISTING_REPO_MARKER in _requirements_text()


def test_every_record_defect_id_is_present_in_a_heading():
    headings = _headings(_requirements_text())
    for defect in RECORD_DEFECT_IDS:
        pattern = _id_pattern("D", defect)
        assert any(pattern.search(heading) for heading in headings), (
            f"D{defect}: no heading carries it"
        )


def test_p25_defect_entries_are_present():
    headings = _headings(_requirements_text())
    for marker in P25_DEFECT_HEADINGS:
        assert any(heading.startswith(marker) for heading in headings), marker


def test_p25_journeys_are_present():
    headings = _headings(_requirements_text())
    for marker in P25_JOURNEY_HEADINGS:
        assert any(heading.startswith(marker) for heading in headings), marker


def test_acceptance_criteria_record_is_present():
    text = _requirements_text()
    for criterion in AC_SPAN_ENDPOINTS + P25_AC_IDS:
        assert criterion in text, criterion
    for defect in range(1, 67):
        if defect in AC_LESS_DEFECTS:
            continue
        assert re.search(rf"AC-D{defect}\.\d+", text), (
            f"D{defect}: no acceptance criterion in the record"
        )


def test_assumption_record_is_present():
    text = _requirements_text()
    for number in ASSUMPTION_IDS:
        assert _id_pattern("A", number).search(text), f"A{number} is absent"


def test_requirement_rule_record_is_present():
    text = _requirements_text()
    for number in REQUIREMENT_RULE_IDS:
        assert _id_pattern("R", number).search(text), f"R{number} is absent"


def test_current_tech_stack_section_is_present():
    assert any(
        line.startswith(TECH_STACK_HEADING)
        for line in _requirements_text().splitlines()
    )


# ── AC-D70.3 — the live constants the phase relies on ───────────────────────

def test_bridge_constants_are_read_off_the_module():
    for name, expected in BRIDGE_CONSTANTS:
        assert getattr(LB, name) == expected, name


def test_chart_defines_the_partial_marker_colour():
    marker = _page_colour(MARKER_COLOUR_CONSTANT)
    assert marker, "the marker colour constant is empty"
    candle_colours = {_page_colour(name).lower() for name in CANDLE_COLOUR_CONSTANTS}
    assert marker.lower() not in candle_colours, (
        f"{MARKER_COLOUR_CONSTANT}={marker!r} must differ from the candle colours"
    )
