"""P12-T6 batch gate: probe record, history-intact, and full-suite green.

Covers AC-D52.7 (record side) and AC-D52.8. Reads the P12-T3 probe artifact
and the requirements text; never re-probes (no live TWS contact).

T63 (full offscreen suite green) is verified by running the suite itself, not
by a case in this file — a gate case that shells out to the whole suite would
recurse and double the runtime. The skip/xfail scan below is static text
matching, so it is safe to keep in-file.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
PROBE_RECORD = REPO_ROOT / "docs" / "d52_probe_record.md"
PRIME_TABLE_OWNER = REPO_ROOT / "ui" / "ticker_session.py"

MARKER_SENTENCE = "This is an existing repository."


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# P12-T6-T61 — probe record names the combo with clean completion.
class TestProbeRecord:
    def test_probe_record_exists(self):
        assert PROBE_RECORD.is_file(), "docs/d52_probe_record.md missing"

    def test_probe_record_names_combo(self):
        text = _read(PROBE_RECORD)
        assert "(30 D, 30 mins)" in text, "combo not documented"

    def test_probe_record_clean_completion_no_321(self):
        text = _read(PROBE_RECORD)
        assert "`30 D` | `30 mins` | yes" in text, "combo row not completed"
        assert "no 321-class rejection" in text, "no-rejection statement missing"
        assert "probe gate **passes**" in text, "pass conclusion missing"


# P12-T6-T62 — requirements history intact; only the recorded extension touched.
class TestHistoryIntact:
    def test_marker_sentence_present(self):
        assert MARKER_SENTENCE in _read(REQUIREMENTS)

    def test_d41_through_d51_sections_present(self):
        text = _read(REQUIREMENTS)
        missing = [f"### D{n}" for n in range(41, 52) if f"### D{n}" not in text]
        assert not missing, f"missing sections: {missing}"

    def test_current_tech_stack_present(self):
        assert "Current Tech Stack" in _read(REQUIREMENTS)

    def test_ac_d16_1_enumeration_reads_nine_timeframes(self):
        text = _read(REQUIREMENTS)
        assert "nine timeframes" in text, "AC-D16.1 still does not read nine"
        anchor = text.index("parameterized over all nine timeframes")
        window = text[anchor:anchor + 500]
        assert "`30 mins`" in window, (
            "new timeframe missing from the AC-D16.1 enumeration"
        )
        assert "`1 week`" in window and "`1 month`" in window, (
            "D48 timeframes missing from the AC-D16.1 enumeration"
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

    def test_ac_d16_8_given_reads_six_intraday(self):
        text = _read(REQUIREMENTS)
        anchor = text.index("Given an intraday timeframe")
        window = text[anchor:anchor + 500]
        assert "`30 mins`" in window, (
            "AC-D16.8 Given does not list the six intraday timeframes"
        )

    def test_ac_d27_9_table_carries_added_row(self):
        text = _read(PRIME_TABLE_OWNER)
        anchor = text.index("Per-span priming table")
        window = text[anchor:anchor + 2000]
        assert "'30 mins'" in window, "30-mins priming-table row missing"


# P12-T6-T63 — no skips/xfails in P12 tests (suite-green verified by the run).
class TestNoSkips:
    def test_no_skip_or_xfail_markers_in_p12_tests(self):
        # Marker fragments are built indirectly so this file's own source
        # does not literally contain them (it is itself a test_p12_* file).
        skip_mark = "pytest.mark." + "skip"
        xfail_mark = "pytest.mark." + "xfail"
        unittest_skip = "@unittest." + "skip"
        offenders = []
        for path in sorted(REPO_ROOT.glob("tests/test_p12_*.py")):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if (skip_mark in line or xfail_mark in line
                        or unittest_skip in line):
                    # Ignore this file's own indirect marker definitions above.
                    if path.name == "test_p12_gate.py" and (
                            "skip_mark" in line or "xfail_mark" in line
                            or "unittest_skip" in line):
                        continue
                    offenders.append(f"{path.name}:{lineno}")
        assert not offenders, f"skip/xfail markers found: {offenders}"
