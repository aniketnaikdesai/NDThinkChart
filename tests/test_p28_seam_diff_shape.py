"""P28-T12 — the audited seam set's diff shape (``AC-P28-02-S5``).

``AC-P28-02-S1``/``S2``/``S3`` said "each changed suite differs only by its seam
assignment — no assertion changed" as prose. This suite is that sentence as a
test, over the whole 21-file seam set: the eighteen suites P28-T3/T4/T5/T7
seamed plus the three P28-T12 seams. For every member, ``git diff ef04c5a --
<file>`` must add exactly one line and it must be the harness seam
(``win._transport_ready = lambda: True``, optionally with a trailing comment,
or the ``_transport_ready=lambda: True`` stub keyword on a ``SimpleNamespace``
double) and remove nothing — otherwise a future "seam edit" could smuggle an
assertion change past the seam ACs.

One exemption is *declared*, not inferred: ``tests/test_p7_w4_streaming.py``,
whose removed lines are P28-T2's retired ``replay_all`` case (headed by
``def test_p7_t07_t11_manager_replay_rebounds_every_subscription``). Its added
line must still be exactly one seam, and its removals must be one contiguous
block of the base file starting at that ``def`` — so the exemption cannot hide
a removal anywhere else in the file.

The case is **phase-bounded**, following the P24 fence precedent (S-P24-5):
a git diff pinned inside pytest reddens every later phase, so once a commit
outside the ``P28`` family exists in ``ef04c5a..HEAD`` the 21 members skip with
a named reason. A later phase's edits to these suites are its own.

Self-checks keep the detector honest, so "it passes" cannot mean "it cannot
fail": a synthetic ``- assert a`` / ``+ assert b`` patch is flagged as a
removal-plus-addition, a docstring-only addition is flagged (it is an added
line, not a seam), and the in-phase predicate is exercised both ways with a
later-phase subject.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The phase base (the P27 close-out). No phase commit hash and no file/line
#: count is pinned: the comparison is always base -> current tree.
PHASE_BASE = "ef04c5a"

#: The one seam shape the phase shipped: the window instance attribute (with or
#: without a trailing comment) and the stub keyword form. Matched against the
#: stripped diff line, so a stub's deeper indentation is not a second shape.
SEAM_RE = re.compile(r"^(win\.)?_transport_ready\s*=\s*lambda:\s*True\b")

#: The 21 audited members of ``AC-P28-02-S5``: the eighteen already seamed by
#: P28-T3/T4/T5/T7 plus the three P28-T12 seams.
AUDITED_SEAMS: tuple[str, ...] = (
    "tests/test_p7_w4_deferral.py",
    "tests/test_p7_w4_streaming.py",
    "tests/test_d24_alarm_full_chain.py",
    "tests/test_d24_popouts.py",
    "tests/test_d24_smoke_gate.py",
    "tests/test_d27_aggregator_priming.py",
    "tests/test_d27_phantom_alarms.py",
    "tests/test_d27_reconnect.py",
    "tests/test_d27_stream_health.py",
    "tests/test_d28_2_sessions.py",
    "tests/test_d28_4_gate.py",
    "tests/test_d28_pacing.py",
    "tests/test_d28_tick_burst_baseline.py",
    "tests/test_d68_hold_balance.py",
    "tests/test_p13_hold_fix.py",
    "tests/test_p13_restore.py",
    "tests/test_phase3_fixpass.py",
    "tests/test_p13_attach.py",
    "tests/test_p13_hold_probe.py",
    "tests/test_d41_removal.py",
    "tests/test_p7_w2_prime.py",
)

#: The single declared exemption: P28-T2 deleted this case (D88, ``replay_all``),
#: so the file's 20 removed lines are that block and nothing else. The value is
#: the retired case's name; its ``def`` line must head the removals.
DECLARED_REMOVALS: dict[str, str] = {
    "tests/test_p7_w4_streaming.py": (
        "test_p7_t07_t11_manager_replay_rebounds_every_subscription"
    ),
}

#: The P28 commit family. A commit subject outside it closes the phase diff.
PHASE_SUBJECT_PREFIX = "P28"

#: The named skip reason: the P28 diff is closed and a later phase owns the file.
PHASE_CLOSED_REASON = (
    "phase-bounded skip: ef04c5a..HEAD contains a commit outside the P28 family, "
    "so the P28 phase diff is closed and a later phase's edits to the audited "
    "seam suites are that phase's own (S-P24-5 precedent)"
)


def _git(*args: str) -> str:
    """Run one git command at the repo root, failing loudly if it cannot run."""
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def _phase_subjects() -> list[str]:
    """Commit subjects in ``PHASE_BASE..HEAD`` (the phase diff's subjects)."""
    out = _git("log", "--format=%s", f"{PHASE_BASE}..HEAD").splitlines()
    return [line for line in out if line.strip()]


def _in_phase(subjects: list[str]) -> bool:
    """False when any commit subject in ``ef04c5a..HEAD`` is not a P28 commit."""
    return all(subject.startswith(PHASE_SUBJECT_PREFIX) for subject in subjects)


def _phase_diff(relpath: str) -> tuple[list[str], list[str]]:
    """(added, removed) content lines of ``relpath`` against ``PHASE_BASE``.

    The ``+++``/``---`` headers are excluded by only reading hunk bodies, so a
    content line that happens to begin with ``++``/``--`` is not mistaken for a
    marker.
    """
    added: list[str] = []
    removed: list[str] = []
    in_hunk = False
    for raw in _git("diff", "-U0", PHASE_BASE, "--", relpath).splitlines():
        if raw.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:  # --- a/... , +++ b/... , diff --git, index, ...
            continue
        if raw.startswith("\\"):  # "\ No newline at end of file"
            continue
        if raw.startswith("+"):
            added.append(raw[1:])
        elif raw.startswith("-"):
            removed.append(raw[1:])
    return added, removed


def _base_lines(relpath: str) -> list[str]:
    """The file's full text at ``PHASE_BASE``, one entry per line."""
    return _git("show", f"{PHASE_BASE}:{relpath}").splitlines()


def _violations(added: list[str], removed: list[str]) -> list[str]:
    """The shape rule, independent of git: one added seam line, nothing removed.

    Kept pure so the detector itself is testable: the self-checks below feed it
    synthetic patches rather than mutating a real suite.
    """
    problems: list[str] = []
    if len(added) != 1:
        problems.append(f"expected exactly 1 added line, found {len(added)}: {added!r}")
    for line in added:
        if not SEAM_RE.match(line.strip()):
            problems.append(f"added line is not the seam assignment: {line!r}")
    if removed:
        problems.append(f"expected no removed lines, found {len(removed)}: {removed!r}")
    return problems


@pytest.fixture(scope="module")
def in_phase() -> bool:
    """Skip the whole parametrized set once the P28 commit family is closed."""
    subjects = _phase_subjects()
    if not _in_phase(subjects):
        later = [s for s in subjects if not s.startswith(PHASE_SUBJECT_PREFIX)]
        pytest.skip(f"{PHASE_CLOSED_REASON} (first: {later[0]!r})")
    return True


@pytest.mark.parametrize(
    "relpath", AUDITED_SEAMS, ids=[Path(path).stem for path in AUDITED_SEAMS]
)
def test_p28_audited_seam_diff_shape(relpath: str, in_phase: bool) -> None:
    """Each audited suite differs from ``ef04c5a`` by its one seam line only."""
    added, removed = _phase_diff(relpath)
    declared = DECLARED_REMOVALS.get(relpath)

    if declared is None:
        problems = _violations(added, removed)
        assert problems == [], f"{relpath}: " + "; ".join(problems)
        return

    # The one exempt file: still exactly one added seam line, and every removed
    # line is the declared retired case, contiguously, headed by its def line.
    seam_problems = _violations(added, [])
    assert seam_problems == [], f"{relpath}: " + "; ".join(seam_problems)
    assert removed, f"{relpath}: the declared retired case is absent from the patch"

    header = f"def {declared}("
    assert removed[0].strip().startswith(header), (
        f"{relpath}: removals are not headed by {header}…: {removed[0]!r}"
    )
    base = _base_lines(relpath)
    assert removed[0] in base, f"{relpath}: {removed[0]!r} is not in the base file"
    start = base.index(removed[0])
    assert base[start : start + len(removed)] == removed, (
        f"{relpath}: the {len(removed)} removed lines are not one contiguous "
        f"block of the base file starting at {removed[0]!r}"
    )


def test_p28_seam_detector_flags_a_synthetic_assertion_edit() -> None:
    """A ``- assert a`` / ``+ assert b`` patch is a removal plus a non-seam add."""
    problems = _violations(["assert b"], ["assert a"])
    assert problems, "the detector must flag a removal-plus-addition (assert a -> assert b)"
    assert any("removed lines" in item for item in problems), problems
    assert any("not the seam assignment" in item for item in problems), problems


def test_p28_seam_detector_flags_a_docstring_or_noop_addition() -> None:
    """A docstring-only addition is an added line, not a seam; so is a no-op."""
    docstring = ['    """A harmless note."""']
    assert _violations(docstring, []), "a docstring-only addition must be flagged"
    assert _violations(["    # just a comment"], []), "a comment-only addition must be flagged"
    assert _violations([], []), "an unchanged member has no seam and must be flagged"
    # ... while the two shipped seam shapes are accepted.
    assert _violations(["    win._transport_ready = lambda: True"], []) == []
    assert _violations(
        ["    win._transport_ready = lambda: True  # P28 harness seam"], []
    ) == []
    assert _violations(["            _transport_ready=lambda: True,"], []) == []


def test_p28_seam_in_phase_predicate_excludes_a_later_phase_subject() -> None:
    """The phase bound is a real predicate, not an unconditional skip."""
    assert _in_phase(
        [
            "P28 build: readiness gate + deferred attach (D84-D95)",
            "P28: plan approved after two revision rounds",
        ]
    )
    assert not _in_phase(
        [
            "P28 build: readiness gate + deferred attach (D84-D95)",
            "P29 build: startup polish (D96-D99)",
        ]
    )
    assert not _in_phase(["Q-81 quick fix"])
