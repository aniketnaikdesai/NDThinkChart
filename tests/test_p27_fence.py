"""P27-T5 — the phase fence for D77–D83 (``AC-D83.2``).

One assertion per named artefact the phase relies on. Every value is read off
the live modules or the live requirements record — nothing is copied from
prose, and no literal file/line count or phase commit hash is pinned, so a
later phase can extend the record without reddening this fence.

The fence pins:

* the requirements record's own markers: the existing-repository sentence, the
  ``D41``–``D76`` record (presence per id in *a* heading — the record is mixed,
  exactly as P26's fence notes), P27's own ``#### D77``–``#### D83`` entries,
  ``Journey 71``–``Journey 73``, the ``AC-D1.1``–``AC-D76.3`` range plus
  ``AC-D77.1``–``AC-D83.2``, ``A1``–``A229`` plus ``A230``–``A234``,
  ``R1``–``R169`` plus ``R170``–``R174``, and the Current Tech Stack section;
* the values P27 must not move, read off source: the five pacing settings, the
  per-load historical cap derived from the 600 s budget, the two watchdog
  window fractions, the prime's flat backstop and its derived deadline
  (``2_000``→``15_000``, ``40_000``→``41_000``, ``600_000``→``601_000``),
  ``TIMEFRAME_CONFIG``'s nine keys with their durations, and the planner's
  Qt/DB/clock-free import block.

The delta-scope record (``git diff --name-only 623809e`` against the phase
allowlist) is a **build artefact**, not a test: a git diff pinned inside pytest
would redden every later phase (S-P24-5 / the P24 fence precedent). It is
recorded in ``docs/build/results/P27-T5.json``. The in-scope delta is the six
production files (``services/backfill_service.py``, ``ui/ticker_session.py``,
``ibkr/pacing.py``, ``ibkr/market_data.py``, ``ibkr/id_manager.py``,
``data/bar_cache.py``), the four new suites (this file,
``tests/test_d77_d82_d83_planner_identity.py``,
``tests/test_d78_prime_retry_reachable.py``,
``tests/test_d79_d80_d81_budget_honesty.py``), the two re-baselined cases
(``tests/test_p7_w1_coalesce.py``, ``tests/test_d56_taxonomy_pacing.py``), the
two class-based pacing doubles (``tests/test_d65_option_chain.py``,
``tests/test_ibkr_contract_details_d22.py``), the **eight** ``throttle``
lambdas P27-T3's keyword-only ``stamp`` invalidated and P27-T6 swept
(``tests/test_d27_aggregator_priming.py``, ``tests/test_d27_reconnect.py``,
``tests/test_d27_stream_health.py``, ``tests/test_d41_removal.py``,
``tests/test_d45_removal.py``, ``tests/test_d48_mode_parity.py``,
``tests/test_d65_option_stream.py``, ``tests/test_d67_forming_candle.py``), the
guard that keeps them honest (``tests/test_p27_throttle_double_signature.py``),
and ``docs/``. P27's requirements declare no live gate, so this suite claims
none.
"""

import ast
import re
from pathlib import Path

from config import settings
from ibkr import market_data as market_data_module
from ui.ticker_session import (
    _PRIME_BACKSTOP_MS,
    _WATCHDOG_BASE_WINDOW_FRACTION,
    _WATCHDOG_MARGIN_WINDOW_FRACTION,
    _prime_backstop_ms,
    per_load_historical_cap,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
PLANNER = REPO_ROOT / "services" / "backfill_service.py"

#: The Existing Repository marker sentence (R25's standing rule).
MARKER_SENTENCE = "This is an existing repository."

#: ``D41``–``D76`` are the pre-P27 ledger the P27 phase must not drop.
PRE_P27_DEFECTS = range(41, 77)
#: P27's own defect entries, as ``#### D77``–``#### D83`` sub-headings.
P27_DEFECTS = range(77, 84)
#: Journeys 71–73 are P27's three journeys.
P27_JOURNEYS = (71, 72, 73)

#: Defects that carry no numbered acceptance criteria. ``D29``–``D35`` are
#: *intentionally unassigned* (the record says so: the batch numbering jumps
#: ``D28`` → ``D36``); ``D42``/``D43`` are requirement-resolution defects whose
#: record is the resolution text plus A/R rows, with no ``AC-D<n>.<m>`` ledger.
DEFECTS_WITHOUT_CRITERIA = frozenset(range(29, 36)) | {42, 43}

#: P27's own criteria: the ``AC-D77.1``–``AC-D83.2`` range, per defect. A
#: later phase may add criteria (presence only, never absence) but may not
#: delete one.
P27_CRITERIA = {
    77: (1, 2, 3),
    78: (1, 2, 3),
    79: (1,),
    80: (1,),
    81: (1, 2),
    82: (1, 2),
    83: (1, 2),
}

#: The pre-P27 ranges A1–A229 / R1–R169 plus P27's A230–A234 / R170–R174.
ASSUMPTIONS = range(1, 235)
P27_ASSUMPTIONS = range(230, 235)
RISKS = range(1, 175)
P27_RISKS = range(170, 175)


def _text() -> str:
    return REQUIREMENTS.read_text(encoding="utf-8")


def _headings(text: str) -> list[str]:
    """Every markdown heading line, at any level (1–6 ``#``)."""
    return [
        line for line in text.splitlines() if re.match(r"^#{1,6} \S", line)
    ]


# ── AC-D83.2 — the requirements record's markers ────────────────────────────

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
        for defect in PRE_P27_DEFECTS
        if not any(
            re.search(rf"\bD{defect}\b", heading) for heading in headings
        )
    ]
    assert not missing, f"D41–D76 ids missing from every heading: {missing}"

    # P27's own entries are the ``#### D77``–``#### D83`` sub-headings.
    for defect in P27_DEFECTS:
        assert any(
            re.match(rf"^#### D{defect}\b", heading) for heading in headings
        ), f"#### D{defect} entry missing"


def test_p27_journeys_are_present():
    headings = _headings(_text())
    for journey in P27_JOURNEYS:
        assert any(
            re.match(rf"^#{{2,4}} Journey {journey}\b", heading)
            for heading in headings
        ), f"Journey {journey} heading missing"


def test_acceptance_criteria_ranges_are_present():
    text = _text()
    # The range's endpoint definitions are what "AC-D1.1–AC-D76.3" names.
    assert re.search(r"\*\*AC-D1\.1\b", text)
    assert re.search(r"\*\*AC-D76\.3\b", text)

    # Presence per defect id across the whole ledger, minus the defects the
    # record itself states carry no numbered criteria.
    missing = [
        defect
        for defect in range(1, 77)
        if defect not in DEFECTS_WITHOUT_CRITERIA
        and not re.search(rf"\*\*AC-D{defect}\.\d", text)
    ]
    assert not missing, f"AC-D<defect>.<n> families missing: {missing}"

    # P27's own AC-D77.1–AC-D83.2, criterion by criterion.
    for defect, suffixes in P27_CRITERIA.items():
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


# ── AC-P27-05-2 — the pacing settings, read off the live module ─────────────

def test_the_five_pacing_settings_are_unchanged():
    assert settings.MAX_REQ_PER_SEC == 50
    assert settings.HISTORICAL_MIN_INTERVAL_S == 0.5
    assert settings.MAX_HISTORICAL_PER_600S == 100
    assert settings.MIN_INTRADAY_SESSIONS == 30
    assert settings.SESSION_BAR_CAP == 5000


def test_per_load_cap_is_read_off_the_tunable():
    assert per_load_historical_cap() == max(
        1, int(settings.MAX_HISTORICAL_PER_600S) // 4
    )


def test_watchdog_window_fractions_are_one_fifth_and_one_twentieth():
    assert _WATCHDOG_BASE_WINDOW_FRACTION == 1 / 5
    assert _WATCHDOG_MARGIN_WINDOW_FRACTION == 1 / 20


# ── AC-P27-05-2 — the prime's backstop arithmetic ───────────────────────────

def test_prime_backstop_is_the_flat_bound_at_short_waits():
    assert _PRIME_BACKSTOP_MS == 15_000
    # A wait at or below 14 s keeps the flat 15 s bound.
    assert _prime_backstop_ms(2_000) == 15_000


def test_prime_backstop_tracks_the_retry_deadline_at_long_waits():
    # 40 s and the historic-wait ceiling (S-P27-3): the retry's own deadline
    # plus one grace tick, so the retry always fires before the backstop.
    assert _prime_backstop_ms(40_000) == 41_000
    assert _prime_backstop_ms(600_000) == 601_000


# ── AC-P27-05-2 — the request shape and the planner's purity ────────────────

#: ``TIMEFRAME_CONFIG``'s nine rows, as the frozen interface records them.
EXPECTED_TIMEFRAMES = {
    "1 min": ("30 D", "1 min"),
    "5 mins": ("30 D", "5 mins"),
    "15 mins": ("30 D", "15 mins"),
    "30 mins": ("30 D", "30 mins"),
    "1 hour": ("60 D", "1 hour"),
    "4 hours": ("60 D", "4 hours"),
    "1 day": ("1 Y", "1 day"),
    "1 week": ("2 Y", "1 week"),
    "1 month": ("10 Y", "1 month"),
}

#: Modules the pure planner may not import: no Qt, no DB, no clock.
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "pyqtgraph",
        "sqlite3",
        "time",
    }
)
FORBIDDEN_IMPORT_MODULES = frozenset({"data.bar_cache", "data.db"})

#: Clock reads: ``now_ts`` is always injected, never read inside the planner.
CLOCK_READ_PATTERNS = (
    r"\bdatetime\.now\(",
    r"\bdatetime\.utcnow\(",
    r"\bdate\.today\(",
    r"\btime\.time\(",
    r"\btime\.monotonic\(",
    r"\btime\.perf_counter\(",
)


def test_timeframe_config_keys_and_durations_are_unchanged():
    actual = {
        key: (row["duration"], row["bar_size"])
        for key, row in market_data_module.TIMEFRAME_CONFIG.items()
    }
    assert actual == EXPECTED_TIMEFRAMES
    assert len(actual) == 9


def test_planner_import_block_is_qt_db_and_clock_free():
    tree = ast.parse(PLANNER.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    offenders = sorted(
        name
        for name in imported
        if name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS
        or name in FORBIDDEN_IMPORT_MODULES
    )
    assert not offenders, f"planner imports a forbidden module: {offenders}"

    source = PLANNER.read_text(encoding="utf-8")
    clock_reads = [
        pattern for pattern in CLOCK_READ_PATTERNS if re.search(pattern, source)
    ]
    assert not clock_reads, f"planner reads the clock: {clock_reads}"
