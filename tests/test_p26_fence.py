"""P26-T4 — the phase fence for D71–D76 (``AC-D76.3``).

One assertion per named artefact the phase relies on. Every value is read off
the live modules or the live requirements record — nothing is copied from
prose, and no literal file/line count or phase commit hash is pinned, so a
later phase can extend the record without reddening this fence.

The fence pins:

* the requirements record's own markers: the existing-repository sentence, the
  ``D41``–``D70`` record (presence per id in *a* heading — the record is mixed,
  exactly as P25's fence notes), P26's own ``#### D71``–``#### D76`` entries,
  ``Journey 68``–``Journey 70``, the ``AC-D1.1``–``AC-D70.3`` range plus
  ``AC-D71.1``–``AC-D76.3``, ``A1``–``A224`` plus ``A225``–``A229``,
  ``R1``–``R164`` plus ``R165``–``R169``, and the Current Tech Stack section;
* the six pinning values P26 must not move: ``per_load_historical_cap()``, the
  two watchdog window fractions, the zero-wait watchdog bound, the four
  subscription tags, the ``include_types`` set ``_replay_subscriptions``
  passes, and ``TIMEFRAME_CONFIG``'s key set.

The delta-scope record (``git diff --name-only 629be4a`` against the phase
allowlist) is a **build artefact**, not a test: a git diff pinned inside pytest
would redden every later phase (S-P24-5 / the P24 fence precedent). It is
recorded in ``docs/build/results/P26-T4.json`` beside gates G3/G4, which are
owner-run and never claimed by this suite.
"""

import re
from pathlib import Path
from types import SimpleNamespace

from config import settings
from ibkr import market_data as market_data_module
from ibkr.pacing import pacing_manager
from ibkr.subscription_manager import (
    MARKET_DATA,
    OPTION_LEGS,
    RT_BARS,
    S0_TICKS,
)
from ui.main_window import MainWindow
from ui.ticker_session import (
    _WATCHDOG_BASE_WINDOW_FRACTION,
    _WATCHDOG_MARGIN_WINDOW_FRACTION,
    TickerSession,
    per_load_historical_cap,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"

#: The Existing Repository marker sentence (R25's standing rule).
MARKER_SENTENCE = "This is an existing repository."

#: ``### D41``–``### D70`` are the pre-P26 ledger the P26 phase must not drop.
PRE_P26_DEFECTS = range(41, 71)
#: P26's own defect entries, as ``#### D71``–``#### D76`` sub-headings.
P26_DEFECTS = range(71, 77)
#: Journeys 68–70 are P26's three journeys.
P26_JOURNEYS = (68, 69, 70)

#: Defects that carry no numbered acceptance criteria. ``D29``–``D35`` are
#: *intentionally unassigned* (the record says so: the batch numbering jumps
#: ``D28`` → ``D36``); ``D42``/``D43`` are requirement-resolution defects whose
#: record is the resolution text plus A/R rows, with no ``AC-D<n>.<m>`` ledger.
DEFECTS_WITHOUT_CRITERIA = frozenset(range(29, 36)) | {42, 43}

#: P26's own criteria: the AC-D71.1–AC-D76.3 range, per defect. A later phase
#: may add criteria (presence only, never absence) but may not delete one.
P26_CRITERIA = {
    71: (1, 2, 3),
    72: (1, 2, 3),
    73: (1, 2),
    74: (1, 2),
    75: (1, 2),
    76: (1, 2, 3),
}

#: The pre-P26 ranges A1–A224 / R1–R164 plus P26's A225–A229 / R165–R169.
ASSUMPTIONS = range(1, 230)
RISKS = range(1, 170)


def _text() -> str:
    return REQUIREMENTS.read_text(encoding="utf-8")


def _headings(text: str) -> list[str]:
    """Every markdown heading line, at any level (1–4 ``#``)."""
    return [
        line for line in text.splitlines() if re.match(r"^#{1,4} \S", line)
    ]


# ── AC-D76.3 — the requirements record's markers ────────────────────────────

def test_existing_repository_marker_and_current_tech_stack_are_present():
    text = _text()
    assert MARKER_SENTENCE in text
    assert "Current Tech Stack" in text
    # The stack section itself, not merely a mention of its name.
    assert re.search(r"(?m)^\*\*Current Tech Stack:\*\*", text)


def test_d41_to_d70_are_present_per_id_in_a_heading():
    headings = _headings(_text())
    missing = [
        defect
        for defect in PRE_P26_DEFECTS
        if not any(
            re.search(rf"\bD{defect}\b", heading) for heading in headings
        )
    ]
    assert not missing, f"D41–D70 ids missing from every heading: {missing}"


def test_p26_defect_entries_and_journeys_are_present():
    headings = _headings(_text())
    # P26's own entries are the ``#### D71``–``#### D76`` sub-headings.
    for defect in P26_DEFECTS:
        assert any(
            re.match(rf"^#### D{defect}\b", heading) for heading in headings
        ), f"#### D{defect} entry missing"
    for journey in P26_JOURNEYS:
        assert any(
            re.match(rf"^#{{2,4}} Journey {journey}\b", heading)
            for heading in headings
        ), f"Journey {journey} heading missing"


def test_acceptance_criteria_ranges_are_present():
    text = _text()
    # The range's endpoint definitions are what "AC-D1.1–AC-D70.3" names.
    assert re.search(r"\*\*AC-D1\.1\b", text)
    assert re.search(r"\*\*AC-D70\.3\b", text)

    # Presence per defect id across the whole ledger, minus the defects the
    # record itself states carry no numbered criteria.
    missing = [
        defect
        for defect in range(1, 77)
        if defect not in DEFECTS_WITHOUT_CRITERIA
        and not re.search(rf"\*\*AC-D{defect}\.\d", text)
    ]
    assert not missing, f"AC-D<defect>.<n> families missing: {missing}"

    # P26's own AC-D71.1–AC-D76.3, criterion by criterion.
    for defect, suffixes in P26_CRITERIA.items():
        for suffix in suffixes:
            assert re.search(rf"\*\*AC-D{defect}\.{suffix}\b", text), (
                f"AC-D{defect}.{suffix} missing"
            )


def test_assumption_and_risk_ranges_are_present():
    text = _text()
    # Assumptions appear in two shapes: the early table (``| A<n> |``) and the
    # later bold bullets (``- **A<n> —``); both are recorded entries.
    missing_a = [
        n
        for n in ASSUMPTIONS
        if not re.search(
            rf"(?m)^(?:\| A{n}(?=[ |—])|- \*\*A{n} —)", text
        )
    ]
    assert not missing_a, f"A ids missing: {missing_a}"
    missing_r = [
        n for n in RISKS if not re.search(rf"(?m)^\| R{n}(?=[ |—])", text)
    ]
    assert not missing_r, f"R ids missing: {missing_r}"


# ── AC-D76.3 — the six pinning values, read off the live modules ────────────

def test_per_load_cap_is_read_off_the_tunable():
    assert per_load_historical_cap() == max(
        1, int(settings.MAX_HISTORICAL_PER_600S) // 4
    )


def test_watchdog_window_fractions_are_one_fifth_and_one_twentieth():
    assert _WATCHDOG_BASE_WINDOW_FRACTION == 1 / 5
    assert _WATCHDOG_MARGIN_WINDOW_FRACTION == 1 / 20


def test_zero_wait_watchdog_bound_is_a_fifth_of_the_historical_window(qapp):
    session = TickerSession("SPX", SimpleNamespace())
    try:
        window_s = float(pacing_manager._hist_window)
        assert session._history_wave_watchdog_bound_ms(0.0) == int(
            window_s * 1000 / 5
        )
    finally:
        session.deleteLater()


def test_subscription_tags_keep_their_recorded_values():
    # The four tags as the frozen interface records them; a rename or a
    # re-tag would break the registry's replay filter and the retire resolvers.
    assert (RT_BARS, MARKET_DATA, S0_TICKS, OPTION_LEGS) == (
        "rt_bars",
        "market_data",
        "s0_ticks",
        "option_legs",
    )
    assert len({RT_BARS, MARKET_DATA, S0_TICKS, OPTION_LEGS}) == 4


class _ReplayRecorder:
    """A ``SubscriptionManager`` stand-in that records the requested types."""

    def __init__(self) -> None:
        self.include_types = None

    def replay_all(self, include_types=None):
        self.include_types = include_types
        return []


class _StatusBar:
    def showMessage(self, *_args, **_kwargs) -> None:  # noqa: N802 (Qt shape)
        return None


def test_replay_subscriptions_passes_exactly_three_tags(qapp):
    sub_manager = _ReplayRecorder()
    window = SimpleNamespace(
        sub_manager=sub_manager,
        status_bar=_StatusBar(),
    )
    # The live method, not a copy of its source: a stub self is enough because
    # the call needs only the registry, the status bar and the epoch counter.
    MainWindow._replay_subscriptions(window)
    assert sub_manager.include_types == {RT_BARS, S0_TICKS, OPTION_LEGS}
    assert MARKET_DATA not in sub_manager.include_types


def test_timeframe_config_keys_are_unchanged():
    # P26 owns no request shape or timeframe (P27 owns them): the key set the
    # chart, the planner and the priming paths read is exactly the P25 set.
    assert set(market_data_module.TIMEFRAME_CONFIG) == {
        "1 min",
        "5 mins",
        "15 mins",
        "30 mins",
        "1 hour",
        "4 hours",
        "1 day",
        "1 week",
        "1 month",
    }
