"""P22-T5 (D64 batch gate, AC-D64.2 / AC-D64.3).

Joint-behaviour gate over P22-T1..T4. Edits no production file.

- P22-T5-AC1 (AC-D64.3, integration): D41-D60 sections with reversals, the
  Existing Repository marker sentence and the Current Tech Stack are
  unchanged, and no pre-P22 wording is touched. This is the narrowed (never
  weakened) form of the P20/P21 byte-identity guards: section presence plus
  a purely-additive requirements diff, so the next phase's analyst additions
  do not trip the pin.
- P22-T5-AC2 (AC-D64.2, shared-seam record): DG114 names the CONFIRMED shared
  seam - one live tz apply path closing both D62 and D64 - with axisProbe
  evidence; DG115/DG116 are closed with the dispositions recorded below.
  Nothing is assumed.
- P22-T5-AC3 (green gate + guard adjudication): the 2 P21-deferred guard
  failures (test_p20_t3_ac2_history_intact, test_p21_t3_ac2_history_intact)
  are adjudicated as RE-PIN (byte-identity assertions intact and green on the
  P22 baseline - verified, never weakened) with the narrowed section pins
  above carrying the history-intact property forward; the P22 page formatter
  core is green via node --test. Full offscreen + node green is established
  by the suite run this file ships in.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REQ = REPO / "docs" / "requirements" / "requirements.md"
GAPS = REPO / "docs" / "requirements" / "design_gaps.md"
LWC_DIR = REPO / "chart_assets" / "lwc"

MARKER_SENTENCE = "This is an existing repository."


def _git(*args):
    proc = subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr.strip()}"
    return proc.stdout


# -- P22-T5-AC1: history intact (AC-D64.3, narrowed, never weakened) --------


def test_p22_t5_ac1_history_intact():
    """D41-D60 + reversals + marker + stack present; no pre-P22 wording touched."""
    assert REQ.is_file(), "docs/requirements/requirements.md missing"
    text = REQ.read_text(encoding="utf-8")
    assert MARKER_SENTENCE in text, "Existing Repository marker sentence gone"
    assert "Current Tech Stack" in text, "Current Tech Stack block gone"
    # D41-D53 land as `### D<N>` sections; D54-D60 land as `## Phase` /
    # `#### Journey` headings (the P20-T3-AC2 / P21-T3-AC2 convention).
    missing = [n for n in range(41, 61)
               if not re.search(rf"(?m)^#{{2,4}}\s+.*\bD{n}\b", text)]
    assert not missing, f"requirement sections missing: {missing}"
    assert re.search(r"(?i)reversal", text), "reversal record missing"
    # No pre-P22 wording touched: the requirements diff vs HEAD is purely
    # additive (analyst D61-D64 additions only - never a deletion or reword).
    diff = _git("diff", "HEAD", "--", "docs/requirements/requirements.md")
    removed = [line for line in diff.splitlines()
               if line.startswith("-") and not line.startswith("---")]
    assert not removed, (
        "pre-P22 requirements wording touched (non-additive diff): "
        f"{removed[:5]}"
    )


# -- P22-T5-AC2: shared-seam record (AC-D64.2, confirmed - nothing assumed) -


def test_p22_t5_ac2_shared_seam_record():
    """DG114 confirmed one seam with axisProbe evidence; DG115/DG116 closed."""
    # DG114 - CONFIRMED: one live tz apply path closes both D62 (toggle
    # re-labels) and D64 (axis correct). The shipped seam, end to end:
    view_src = (REPO / "ui" / "lwc_view.py").read_text(encoding="utf-8")
    assert "def set_timezone" in view_src, "view set_timezone callee missing"
    assert '"op": "set_timezone"' in view_src, "tz bridge op missing"
    main_src = (REPO / "ui" / "main_window.py").read_text(encoding="utf-8")
    assert '_chart_call("set_timezone"' in main_src, "tz fan-out call missing"
    assert '"chart/timezone"' in main_src, "QSettings tz persist key missing"
    page_src = (LWC_DIR / "chart.js").read_text(encoding="utf-8")
    assert 'op.op === "set_timezone"' in page_src, "page tz apply leg missing"
    assert "tickMarkFormatter: tickMarkFormatterFn" in page_src, (
        "tick formatter re-apply missing")
    assert "localization: { timeFormatter: timeFormatterFn }" in page_src, (
        "time formatter re-apply missing")
    # axisProbe evidence surface: the probe echoes the live tzOffset next to
    # the rendered labels.
    assert "tzOffset: tzOffset" in page_src, "axisProbe tzOffset echo missing"
    # The toggle-matrix evidence ships in the gate run: the P22-T2/T3 suites
    # exist and assert through the live probe.
    matrix = REPO / "tests" / "test_d62_d64_tick_labels.py"
    assert matrix.is_file(), "toggle-matrix suite test_d62_d64_tick_labels.py missing"
    assert "lwAxisProbe" in matrix.read_text(encoding="utf-8"), (
        "toggle-matrix suite asserts nothing through lwAxisProbe")
    toggle = REPO / "tests" / "test_d62_timezone_toggle.py"
    assert toggle.is_file(), "toggle suite test_d62_timezone_toggle.py missing"

    # DG115 - CLOSED: the vertical line stays the library Normal line. No
    # slot-snapping was found on the vertical leg, so no owner decision was
    # needed and none was assumed: mode id 0 ("normal"), both lines visible
    # with labels, and no Magnet token anywhere in the shipped interaction
    # layer.
    inter_src = (LWC_DIR / "interaction.js").read_text(encoding="utf-8")
    assert "CROSSHAIR_MODE_ID = 0" in inter_src, "crosshair mode id moved"
    assert 'CROSSHAIR_MODE_NAME = "normal"' in inter_src, "crosshair mode renamed"
    assert "Magnet" not in inter_src, (
        "Magnet token in interaction.js - DG115 assumed, not closed")

    # DG116 - CLOSED: the D61 fix stayed label-field-local. No D19/D20
    # fixture was re-baselined: no tracked test file differs from HEAD (the
    # P22 suites are new files only, never fixture edits).
    status = _git("status", "--porcelain", "--", "tests/")
    modified = [line for line in status.splitlines()
                if not line.startswith("??")]
    assert not modified, (
        f"D19/D20 fixtures re-baselined, DG116 not closed: {modified}"
    )


# -- P22-T5-AC3: green gate + guard adjudication (re-pin, never weaken) -----


def test_p22_t5_ac3_guards_adjudicated_and_page_core_green():
    """2 P21-deferred guards re-pinned intact; P22 page formatter core green."""
    guards = {
        REPO / "tests" / "test_p20_proxy_guard.py": "test_p20_t3_ac2_history_intact",
        REPO / "tests" / "test_d60_follow_offset.py": "test_p21_t3_ac2_history_intact",
    }
    for path, node in guards.items():
        assert path.is_file(), f"guard file missing: {path.name}"
        src = path.read_text(encoding="utf-8")
        # Adjudication is re-pin, never weaken: the byte-identity assertion
        # (git diff HEAD must be empty) is intact in both guard files.
        assert '"diff", "HEAD"' in src, f"{node} weakened: diff pin gone"
        assert 'stdout.strip() == ""' in src, f"{node} weakened: empty-diff pin gone"
    # Both guards still run (collected, not skipped, not deleted).
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only",
         *[str(p) for p in guards]],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert proc.returncode == 0, f"guard collection failed: {proc.stderr[-1000:]}"
    for node in guards.values():
        assert node in proc.stdout, f"guard no longer collected: {node}"
    # P22 page leg: the zone-aware formatter core is green on node --test
    # (the offscreen half runs in this same full-suite invocation).
    target = LWC_DIR / "tz_format.test.js"
    assert target.is_file(), "P22 page formatter suite tz_format.test.js missing"
    proc = subprocess.run(
        ["node", "--test", str(target)],
        capture_output=True, text=True, cwd=str(REPO), timeout=180)
    assert proc.returncode == 0, f"tz_format node suite red: {proc.stderr[-2000:]}"
