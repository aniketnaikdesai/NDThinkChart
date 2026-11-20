"""P25-T8 — ``usage.md`` documents the amber partial marker (ESC-128, DG129).

The user-facing record gets two edits, and only two:

* one bullet under ``### Weekly & Monthly Timeframes (Phase D48)`` saying what
  the amber dot on a forming ``1 week`` / ``1 month`` candle means, where it
  sits, and when it clears;
* the ``### Event Markers (removed — Q-34, commit 1a30d41)`` note keeps its
  D38 removal record and distinguishes the dot as a data-completeness cue
  rather than an event marker.

The assertions read the live document (no fixture copies) and are scoped to
each section, so a claim added elsewhere in ``usage.md`` cannot satisfy them.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USAGE = REPO_ROOT / "usage.md"

WEEKLY_HEADING = "### Weekly & Monthly Timeframes"
EVENT_HEADING = "### Event Markers"


def _usage_text():
    return USAGE.read_text(encoding="utf-8")


def _section(text, heading_prefix):
    """The section starting at ``heading_prefix`` up to the next ``### ``."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith(heading_prefix)),
        None,
    )
    assert start is not None, f"usage.md has no {heading_prefix!r} heading"
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("### "):
            end = i
            break
    return "\n".join(lines[start:end]).lower()


# ── AC1 — the forming-candle bullet ─────────────────────────────────────────

def test_weekly_monthly_section_documents_the_partial_marker():
    section = _section(_usage_text(), WEEKLY_HEADING)
    assert "1 week" in section
    assert "1 month" in section
    assert "forming" in section
    assert "amber" in section
    # Why the dot is shown: the loaded history does not cover the period.
    assert any(
        phrase in section
        for phrase in ("cannot cover", "not covered", "partial")
    ), "the section must say the period's data is not complete"
    # What the values mean: the aggregate of the bars actually available.
    assert any(
        phrase in section
        for phrase in ("aggregate", "bars actually")
    ), "the section must say the values aggregate the available bars"
    # When it goes away.
    assert any(
        phrase in section
        for phrase in ("disappear", "clears", "complete")
    ), "the section must say the dot clears once the data is complete"


# ── AC2 — the Event Markers note keeps its record, adds the distinction ─────

def test_event_markers_note_keeps_the_record_and_adds_the_distinction():
    section = _section(_usage_text(), EVENT_HEADING)
    assert "d38" in section
    assert "removed" in section
    for marker_kind in ("earnings", "dividend", "split"):
        assert marker_kind in section, marker_kind
    assert "amber" in section
    assert any(
        phrase in section
        for phrase in ("not an event marker", "data-completeness", "data completeness")
    ), "the note must distinguish the amber dot from an event marker"
