"""P8-T05 batch gate: probe record, history-intact, and full-suite green.

Covers AC-D48.6 (record side) and AC-D48.7. Reads the P8-T02 probe artifact
and the requirements text; never re-probes (no live TWS contact).

T31 (full offscreen suite green) is verified by running the suite itself, not
by a case in this file — a gate case that shells out to the whole suite would
recurse and double the runtime.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
PROBE_RECORD = REPO_ROOT / "docs" / "d48_probe_record.md"
PRIME_TABLE_OWNER = REPO_ROOT / "ui" / "ticker_session.py"

MARKER_SENTENCE = "This is an existing repository."


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# P8-T05-T11 — probe record names both combos with clean completion.
class TestProbeRecord:
    def test_probe_record_exists(self):
        assert PROBE_RECORD.is_file(), "docs/d48_probe_record.md missing"

    def test_probe_record_names_both_combos(self):
        text = _read(PROBE_RECORD)
        assert "(2 Y, 1 week)" in text, "weekly combo not documented"
        assert "(10 Y, 1 month)" in text, "monthly combo not documented"

    def test_probe_record_clean_completion_no_321(self):
        text = _read(PROBE_RECORD)
        assert "`2 Y` | `1 week` | yes" in text, "weekly row not completed"
        assert "`10 Y` | `1 month` | yes" in text, "monthly row not completed"
        assert "no 321-class rejection" in text, "no-rejection statement missing"
        assert "probe gate **passes**" in text, "pass conclusion missing"


# P8-T05-T21 — requirements history intact; only the recorded extension touched.
class TestHistoryIntact:
    def test_marker_sentence_present(self):
        assert MARKER_SENTENCE in _read(REQUIREMENTS)

    def test_d41_through_d47_sections_present(self):
        text = _read(REQUIREMENTS)
        missing = [f"### D{n}" for n in range(41, 48) if f"### D{n}" not in text]
        assert not missing, f"missing sections: {missing}"

    def test_current_tech_stack_present(self):
        assert "Current Tech Stack" in _read(REQUIREMENTS)

    def test_ac_d16_1_enumeration_reads_nine_timeframes(self):
        text = _read(REQUIREMENTS)
        assert "nine timeframes" in text, "AC-D16.1 still does not read nine"
        anchor = text.index("parameterized over all nine timeframes")
        window = text[anchor:anchor + 500]
        assert "`1 week`" in window and "`1 month`" in window, (
            "new timeframes missing from the AC-D16.1 enumeration"
        )
        # Any surviving old enumeration wording ("all six timeframes" from the
        # pre-D48 text, "all eight timeframes" from the pre-D52 text) must only
        # appear inside a recorded extension note that quotes the old wording
        # to describe the change ("now reads eight" for D48, "now reads nine"
        # for D52) — never as a live enumeration.
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "all six timeframes" in line or "all eight timeframes" in line:
                assert ("now reads eight" in line
                        or "now reads nine" in line), (
                    f"stale timeframe wording at line {lineno}: "
                    f"{line.strip()[:160]}"
                )

    # Back-compat alias: the dispatch test command still addresses the pre-D52
    # node id; both names execute the nine-timeframe assertion above.
    test_ac_d16_1_enumeration_reads_eight_timeframes = (
        test_ac_d16_1_enumeration_reads_nine_timeframes
    )

    def test_ac_d27_9_table_carries_two_added_rows(self):
        text = _read(PRIME_TABLE_OWNER)
        anchor = text.index("Per-span priming table")
        window = text[anchor:anchor + 2000]
        assert "'1 week'" in window, "weekly priming-table row missing"
        assert "'1 month'" in window, "monthly priming-table row missing"
