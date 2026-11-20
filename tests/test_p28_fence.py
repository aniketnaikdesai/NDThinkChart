"""P28-T11 — the phase fence for D84–D95 (``AC-D95.3``, ``AC-P28-08-1``).

One assertion per named artefact the phase relies on. Every value is read off
the live modules or the live requirements record — nothing is copied from
prose, and no literal file/line count or phase commit hash is pinned, so a
later phase can extend the record without reddening this fence.

The fence pins:

* the requirements record's own markers: the existing-repository sentence, the
  ``D41``–``D83`` record (presence per id in *a* heading — the record is mixed,
  as P26's/P27's fences note), P28's own ``#### D84``–``#### D95`` entries,
  ``Journey 74``–``Journey 77``, the ``AC-D1.1``–``AC-D83.2`` range plus
  ``AC-D84.1``–``AC-D95.3``, ``A1``–``A234`` plus ``A235``–``A240``,
  ``R1``–``R174`` plus ``R175``–``R180``, and the Current Tech Stack section;
* the values P28 must not move, read off source: ``LIVE_PORT``/``MAX_POPOUTS``,
  ``MAX_RETRY_ATTEMPTS`` and the terminal ``StreamState.EXHAUSTED`` distinct
  from ``FAILED``, the shipped ``5/10/20/40/60/60 s`` progression read off
  ``next_retry_delay_s``, the absence of ``RealtimeBarsManager.replay_all``,
  ``TickerSession._rt_attach_pending``'s ``False`` default and the one
  ``_clear_prime_state()`` its three in-file sites (and ``_on_disconnected``)
  call, the frozen ``backup_before_drop``/``check_live_port`` signatures, the
  lock-before-window-import ordering in ``main.py``, and the six D92 strings
  asserted where each is produced.

The delta-scope record (``git diff --name-only ef04c5a`` against the phase
allowlist) is a **build artefact**, not a test: a git diff pinned inside pytest
would redden every later phase (S-P24-5 / the P24 fence precedent). It is
recorded in ``docs/build/results/P28-T11.json``. ``ef04c5a`` (the P27
close-out) is this build's baseline — the plan's ``0ff7964`` predates P27's
rework, whose delta touches ``tests/test_p27_throttle_double_signature.py``
(outside P28 scope). The in-scope delta is the five ``ibkr`` modules,
``ui/ticker_session.py``, ``ui/main_window.py``, ``data/db.py``,
``config/settings.py``, ``config/instance_lock.py``, ``main.py``, the three
guide files, the audited suites (whose task-graph footprints also carry
``tests/test_p13_attach.py`` — P28-T7 — and ``tests/test_db_backup.py`` —
P28-T8, the D65 fatality case D86 necessarily re-baselines), the two named
re-baselines, the eight new suites, and ``docs/``. Anything outside that is a
scope breach to escalate, never to justify.

G5 is **owner-run and never claimed here**: no case in this suite (or any P28
unit suite) asserts a process exit or a dock icon; ``AC-D85.1``'s live gate is
the owner's to observe.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from config import settings
from ibkr import stream_health
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.stream_health import StreamHealth, StreamState

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"

#: The Existing Repository marker sentence (R25's standing rule).
MARKER_SENTENCE = "This is an existing repository."

#: ``D41``–``D83`` are the standing ledger the P28 phase must not drop.
PRE_P28_DEFECTS = range(41, 84)
#: P28's own defect entries, as ``#### D84``–``#### D95`` sub-headings.
P28_DEFECTS = range(84, 96)
#: Journeys 74–77 are P28's four journeys.
P28_JOURNEYS = (74, 75, 76, 77)

#: Defects that carry no numbered acceptance criteria. ``D29``–``D35`` are
#: *intentionally unassigned* (the record says so: the batch numbering jumps
#: ``D28`` → ``D36``); ``D42``/``D43`` are requirement-resolution defects whose
#: record is the resolution text plus A/R rows, with no ``AC-D<n>.<m>`` ledger.
DEFECTS_WITHOUT_CRITERIA = frozenset(range(29, 36)) | {42, 43}

#: P28's own criteria: the ``AC-D84.1``–``AC-D95.3`` ledger, per defect.
P28_CRITERIA = {
    84: (1, 2, 3),
    85: (1, 2),
    86: (1, 2, 3),
    87: (1,),
    88: (1,),
    89: (1, 2),
    90: (1, 2, 3),
    91: (1,),
    92: (1,),
    93: (1, 2),
    94: (1,),
    95: (1, 2, 3),
}

#: The standing A1–A234 / R1–R174 ranges plus P28's A235–A240 / R175–R180.
ASSUMPTIONS = range(1, 235)
P28_ASSUMPTIONS = range(235, 241)
RISKS = range(1, 175)
P28_RISKS = range(175, 181)

#: The six D92 strings, each asserted where its one owner produces it.
D92_TITLE = "NDThinkChart \u2014 read-only market data"
D92_GUARD_STRINGS = (
    "read-only market-data client",
    "places no orders",
    "configured port",
)
D92_GUIDE_STRINGS = ("refuses any other port", "configuration check")
D92_GUIDES = ("usage.md", "USAGE.md", "USAGE.txt")

#: A prime-clear caller must call the helper, never restate its six statements.
PRIME_CLEAR_CALLERS = ("teardown", "prepare_load", "_fail_open_prime")


def _text() -> str:
    return REQUIREMENTS.read_text(encoding="utf-8")


def _headings(text: str) -> list[str]:
    """Every markdown heading line, at any level (1–6 ``#``)."""
    return [
        line for line in text.splitlines() if re.match(r"^#{1,6} \S", line)
    ]


# ── AC-D95.3 / P28-T11-01 — the requirements record's markers ───────────────

def test_existing_repository_marker_and_current_tech_stack_are_present():
    text = _text()
    assert MARKER_SENTENCE in text
    assert "Current Tech Stack" in text
    # The stack section itself, not merely a mention of its name.
    assert re.search(r"(?m)^\*\*Current Tech Stack:\*\*", text)


def test_d41_to_d83_are_present_per_id_in_a_heading():
    headings = _headings(_text())
    missing = [
        defect
        for defect in PRE_P28_DEFECTS
        if not any(
            re.search(rf"\bD{defect}\b", heading) for heading in headings
        )
    ]
    assert not missing, f"D41–D83 ids missing from every heading: {missing}"

    # P28's own entries are the ``#### D84``–``#### D95`` sub-headings.
    for defect in P28_DEFECTS:
        assert any(
            re.match(rf"^#### D{defect}\b", heading) for heading in headings
        ), f"#### D{defect} entry missing"


def test_p28_journeys_are_present():
    headings = _headings(_text())
    for journey in P28_JOURNEYS:
        assert any(
            re.match(rf"^#{{2,4}} Journey {journey}\b", heading)
            for heading in headings
        ), f"Journey {journey} heading missing"


def test_acceptance_criteria_ranges_are_present():
    text = _text()
    # The standing range's endpoint definitions are what
    # "AC-D1.1–AC-D83.2" names.
    assert re.search(r"\*\*AC-D1\.1\b", text)
    assert re.search(r"\*\*AC-D83\.2\b", text)

    # Presence per defect id across the whole ledger, minus the defects the
    # record itself states carry no numbered criteria.
    missing = [
        defect
        for defect in range(1, 84)
        if defect not in DEFECTS_WITHOUT_CRITERIA
        and not re.search(rf"\*\*AC-D{defect}\.\d", text)
    ]
    assert not missing, f"AC-D<defect>.<n> families missing: {missing}"

    # P28's own AC-D84.1–AC-D95.3, criterion by criterion. The range's
    # endpoint is asserted explicitly so a truncated ledger cannot pass.
    assert re.search(r"\*\*AC-D95\.3\b", text)
    for defect, suffixes in P28_CRITERIA.items():
        for suffix in suffixes:
            assert re.search(rf"\*\*AC-D{defect}\.{suffix}\b", text), (
                f"AC-D{defect}.{suffix} missing"
            )


def test_assumption_and_risk_ranges_are_present():
    text = _text()
    # Assumptions appear in two shapes: the early table (``| A<n> |``) and the
    # later bold bullets (``- **A<n> —``); both are recorded entries.
    def missing_assumptions(numbers) -> list[int]:
        return [
            n
            for n in numbers
            if not re.search(
                rf"(?m)^(?:\| A{n}(?=[ |—])|- \*\*A{n} —)", text
            )
        ]

    def missing_risks(numbers) -> list[int]:
        return [
            n
            for n in numbers
            if not re.search(rf"(?m)^\| R{n}(?=[ |—])", text)
        ]

    assert not missing_assumptions(ASSUMPTIONS), (
        f"A1–A234 ids missing: {missing_assumptions(ASSUMPTIONS)}"
    )
    assert not missing_assumptions(P28_ASSUMPTIONS), (
        f"A235–A240 ids missing: {missing_assumptions(P28_ASSUMPTIONS)}"
    )
    assert not missing_risks(RISKS), (
        f"R1–R174 ids missing: {missing_risks(RISKS)}"
    )
    assert not missing_risks(P28_RISKS), (
        f"R175–R180 ids missing: {missing_risks(P28_RISKS)}"
    )


# ── AC-P28-08-1 / P28-T11-02 — the values, read off the modules ─────────────

def test_the_pinned_settings_constants_are_unchanged():
    assert settings.LIVE_PORT == 7496
    assert settings.MAX_POPOUTS == 10


def test_the_retry_budget_and_terminal_state_are_pinned():
    assert stream_health.MAX_RETRY_ATTEMPTS == 6
    assert hasattr(StreamState, "EXHAUSTED")
    assert StreamState.EXHAUSTED != StreamState.FAILED
    # Terminal by construction: distinct from every other state, set only by
    # mark_exhausted(), and the recorded failure is kept.
    assert StreamState.EXHAUSTED not in {
        StreamState.SUBSCRIBED,
        StreamState.AWAITING_FIRST_BAR,
        StreamState.LIVE,
        StreamState.FAILED,
    }
    health = StreamHealth()
    health.mark_failed(162, "pacing")
    health.mark_exhausted()
    assert health.state == StreamState.EXHAUSTED
    assert health.describe() == "stopped"


def test_the_shipped_backoff_progression_is_unchanged():
    health = StreamHealth()
    delays = [health.next_retry_delay_s() for _ in range(6)]
    assert delays == [5.0, 10.0, 20.0, 40.0, 60.0, 60.0]
    # The arithmetic is unchanged: the delay caps, the count does not.
    assert health.retry_attempt == 6
    assert health.retry_budget_spent is True


def test_the_dead_realtime_replay_is_gone():
    assert not hasattr(RealtimeBarsManager, "replay_all")


def test_the_session_owns_one_prime_clear_and_one_attach_obligation():
    from ui.ticker_session import TickerSession

    init_source = inspect.getsource(TickerSession.__init__)
    assert "_rt_attach_pending" in init_source
    assert re.search(
        r"self\._rt_attach_pending[^\n=]*=\s*False", init_source
    ), "_rt_attach_pending must default False"

    assert hasattr(TickerSession, "_clear_prime_state")
    for name in PRIME_CLEAR_CALLERS:
        source = inspect.getsource(getattr(TickerSession, name))
        assert "_clear_prime_state()" in source, (
            f"{name} does not call the one prime clear"
        )
        # The six statements live in exactly one place.
        assert "self._prime_timer.stop()" not in source, (
            f"{name} restates the prime block instead of calling the helper"
        )

    from ui.main_window import MainWindow

    disconnect_source = inspect.getsource(MainWindow._on_disconnected)
    assert "_clear_prime_state()" in disconnect_source, (
        "a drop must clear every session's prime through the one helper"
    )


def test_the_frozen_signatures_are_unchanged():
    from data import db_backup

    backup_sig = inspect.signature(db_backup.backup_before_drop)
    assert list(backup_sig.parameters) == ["db_path", "now", "backup_dir"]
    assert backup_sig.parameters["now"].default is None
    assert backup_sig.parameters["backup_dir"].default is None
    assert backup_sig.return_annotation is not inspect.Signature.empty

    guard_sig = inspect.signature(settings.check_live_port)
    assert list(guard_sig.parameters) == []
    assert guard_sig.return_annotation is None


def test_main_acquires_the_lock_before_the_window_import():
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
    port_guard_at = source.index("settings.check_live_port()")
    lock_at = source.index("instance_lock.acquire(")
    window_import_at = source.index("from ui.main_window import MainWindow")

    assert port_guard_at < lock_at, "the port guard must run before the lock"
    assert lock_at < window_import_at, (
        "the lock must be acquired before the window (and the DB) is imported"
    )
    # ... and the import lives inside main(), after QApplication exists.
    assert source.index("def main()") < window_import_at


def test_the_six_d92_strings_are_produced_at_their_owners():
    # Title → MainWindow (the owner that produces it).
    from ui.main_window import MainWindow

    title_source = inspect.getsource(MainWindow.__init__)
    assert f'setWindowTitle("{D92_TITLE}")' in title_source

    # Guard message + port comments → config/settings.py.
    guard_source = inspect.getsource(settings.check_live_port)
    for text in D92_GUARD_STRINGS:
        assert text in guard_source, f"{text!r} missing from the guard"

    # Guides → usage.md / USAGE.md / USAGE.txt (one wording, three files).
    for name in D92_GUIDES:
        guide = (REPO_ROOT / name).read_text(encoding="utf-8")
        for text in D92_GUIDE_STRINGS:
            assert text in guide, f"{text!r} missing from {name}"
