"""P2-T23 — D42 Phase 3 reconciliation / non-regression guard.

Guards the D16 rules that the D42 mode-aware presence change must leave intact:

* **AC-D16.7 (ESC-023)** — the NYSE Rule 7.2 year-end exception: a *Saturday*
  New Year's Day is **not** pulled back onto the preceding Friday, so the Dec 31
  year-ends that precede a Saturday Jan 1 stay open trading sessions.
* **AC-D16.1 / AC-D16.3 / AC-D16.4** — the no-fill / no-silent-hole rule (a
  genuine closure is never reported as missing and no bar is fabricated), the
  genuine-closure rule, and the AC-D16.4 shortfall report — all unchanged by
  mode-aware presence (``present_days``): a present-but-mode-empty day (bars only
  outside the current mode's window) is reported as missing by the planner and
  surfaced by the shortfall report; a genuine closure stays empty.
* **AC-D16.x / ESC-065** — the reconciliation node runs a **stable non-timing
  subset** of the offscreen suite in a hermetic subprocess and asserts it is
  green (no assertion weakened, none deleted). The subset is every module under
  ``tests/`` except six, excluded for structural reasons — not because their
  assertions are wrong:

  * **wall-clock gates** — ``test_d24_smoke_gate.py`` (baseline x multiplier),
    ``test_d28_4_gate.py`` (50 ms/tick), ``test_d28_tick_burst_baseline.py``
    (``per_tick_ms < 50.0``);
  * **Qt teardown / ``processEvents``** — ``test_session_overlay.py`` (the
    documented offscreen SIGSEGV at its ``panel`` fixture),
    ``test_d28_5_teardown.py`` (closes windows mid-reader-thread and pumps
    ``processEvents``), and ``test_watchlist_addflow_d22.py`` (a SIGSEGV at
    ``test_D22_07_T03_seed_guard``'s ``watchlist_panel`` lambda slot, caught by
    this task's own three-run check).

  Whole-suite-green evidence has one named owner and does **not** come from
  this node: ``verify_tests.py`` -> ``docs/code_review/test_verification.json``
  (the external full-suite run) and the ``P5-T10`` phase gate. This node is the
  cheap, deterministic in-suite signal.

The suite runs offscreen; ``tests/conftest.py`` pins ``DB_PATH`` so pytest runs
are hermetic (ESC-043).
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from services.backfill_service import MissingSpan, find_missing_spans, present_days
from services.market_calendar import is_trading_day, trading_days

_EASTERN = ZoneInfo("America/New_York")


def _ts(day: date, hour: int = 0, minute: int = 0) -> int:
    """Unix seconds for an ET wall-clock instant on ``day``."""
    return int(
        datetime(day.year, day.month, day.day, hour, minute, tzinfo=_EASTERN).timestamp()
    )


class _Bar:
    """Minimal stand-in for a cached bar (the report only reads ``.ts``)."""

    __slots__ = ("ts",)

    def __init__(self, ts: int) -> None:
        self.ts = ts


class _FakeSession:
    """Minimal stand-in for ``TickerSession`` (the report reads two fields)."""

    def __init__(self, spans, ext_hours: bool) -> None:
        self._backfill_missing_spans = list(spans)
        self._wave_extended_hours = ext_hours


# ---------------------------------------------------------------------------
# AC-D16.7 (ESC-023) — the NYSE Rule 7.2 New-Year year-end exception is intact
# ---------------------------------------------------------------------------
def test_ac_d16_7_new_year_exception_year_ends_are_trading_days() -> None:
    """AC1 (P2-T23-T11): the four New-Year year-ends stay open sessions."""
    year_ends = (
        date(2021, 12, 31),
        date(2027, 12, 31),
        date(2032, 12, 31),
        date(2038, 12, 31),
    )
    for year_end in year_ends:
        # Each is a Friday whose following Jan 1 falls on a Saturday; the Rule
        # 7.2 exception means no closure is created for that Saturday New Year,
        # so Dec 31 remains a trading day.
        assert year_end.weekday() == 4, f"{year_end} is not a Friday"
        assert date(year_end.year + 1, 1, 1).weekday() == 5, (
            f"{year_end.year + 1}-01-01 is not a Saturday"
        )
        assert is_trading_day(year_end) is True, (
            f"AC-D16.7 regressed: {year_end} is no longer a trading day"
        )


# ---------------------------------------------------------------------------
# AC-D16.1 / AC-D16.3 / AC-D16.4 — no-fill, genuine closure, shortfall report
# ---------------------------------------------------------------------------
def test_ac_d16_1_3_4_genuine_closure_empty_and_mode_empty_shortfall() -> None:
    """AC2 (P2-T23-T21): closures stay empty; mode-empty days are reported."""
    # --- Part A: a genuine closure (2024-07-04, Independence Day, a Thursday)
    # stays empty — no span is created for it, and the adjacent real hole is
    # reported exactly, with no bar fabricated (spans only, never bars).
    closure = date(2024, 7, 4)
    assert is_trading_day(closure) is False, "2024-07-04 must be a genuine closure"

    present_day = date(2024, 7, 3)   # Wed, seeded inside the RTH window
    missing_day = date(2024, 7, 5)   # Fri, left empty
    now = _ts(date(2024, 7, 5), 16, 0)

    spans = find_missing_spans(
        [_ts(present_day, 10, 0)],
        now,
        "5 mins",
        trailing_days=0,
        ext_hours=False,
        min_sessions=0,
    )
    assert all(isinstance(span, MissingSpan) for span in spans)
    covered = {day for span in spans for day in trading_days(span.start_ts, span.end_ts)}

    assert missing_day in covered, "the real hole must still be reported"
    assert closure not in covered, "the genuine closure must stay empty (no fill)"
    assert all(is_trading_day(day) for day in covered)

    # --- Part B: a present-but-mode-empty day. 2024-07-02 carries a pre-market
    # bar (08:00 ET) only — outside the RTH window, inside the ETH window.
    mode_empty_day = date(2024, 7, 2)
    premarket = _ts(mode_empty_day, 8, 0)

    assert mode_empty_day not in present_days([premarket], ext_hours=False), (
        "a pre-market-only day must not be present under RTH"
    )
    assert mode_empty_day in present_days([premarket], ext_hours=True), (
        "a pre-market-only day must be present under ETH"
    )

    now2 = _ts(mode_empty_day, 16, 0)
    rth_spans = find_missing_spans(
        [premarket], now2, "5 mins", trailing_days=0, ext_hours=False, min_sessions=0
    )
    rth_covered = {
        day for span in rth_spans for day in trading_days(span.start_ts, span.end_ts)
    }
    assert mode_empty_day in rth_covered, (
        "AC-D16.9: a present-but-mode-empty day must be reported missing under RTH"
    )

    eth_spans = find_missing_spans(
        [premarket], now2, "5 mins", trailing_days=0, ext_hours=True, min_sessions=0
    )
    eth_covered = {
        day for span in eth_spans for day in trading_days(span.start_ts, span.end_ts)
    }
    assert mode_empty_day not in eth_covered, (
        "the day is present under ETH, so it must not be reported missing there"
    )

    # --- Part C: the AC-D16.4 shortfall report agrees with the planner. The
    # report reads the SAME exported mode-aware predicate, so the planner and the
    # report cannot disagree. ``_missing_backfill_trading_days`` uses no instance
    # state, so it is exercised directly without a QApplication/MainWindow.
    from ui.main_window import MainWindow  # lazy: keeps the pure guards Qt-free

    session = _FakeSession(
        spans=[MissingSpan(start_ts=_ts(mode_empty_day), end_ts=now2)],
        ext_hours=False,
    )
    shortfall = MainWindow._missing_backfill_trading_days(None, session, [_Bar(premarket)])

    assert shortfall == [mode_empty_day], (
        "AC-D16.4: the shortfall report must surface the present-but-mode-empty day"
    )
    assert all(isinstance(day, date) for day in shortfall)


# ---------------------------------------------------------------------------
# AC-D16.x / ESC-065 — a stable non-timing subset of the offscreen suite is green
# ---------------------------------------------------------------------------

#: Modules the child run never collects, with the reason each is structural
#: rather than an assertion defect. Kept a minority of ``tests/`` on purpose.
_INNER_EXCLUDED: tuple[str, ...] = (
    "test_d24_smoke_gate.py",           # wall-clock: baseline x multiplier
    "test_d28_4_gate.py",               # wall-clock: 50 ms/tick
    "test_d28_tick_burst_baseline.py",  # wall-clock: per_tick_ms < 50.0
    "test_session_overlay.py",          # Qt teardown: documented SIGSEGV at `panel`
    "test_d28_5_teardown.py",           # Qt teardown: processEvents mid-reader-thread
    # Qt teardown: observed SIGSEGV at test_D22_07_T03_seed_guard (watchlist_panel
    # lambda slot) in this task's three-run AC2 check, ESC-065.
    "test_watchlist_addflow_d22.py",
)

#: A hung child must fail the node instead of hanging the outer suite.
_INNER_TIMEOUT_S = 600.0

#: pytest's ``-q`` summary line ("123 passed, 2 skipped in 4.56s"), from which
#: the child's collected-outcome count is read for the node's record line.
_INNER_OUTCOME_RE = re.compile(
    r"(\d+) (?:passed|failed|errors?|skipped|xfailed|xpassed)"
)


def _inner_pytest_args(repo: pathlib.Path) -> list[str]:
    """argv of the child run: a stable, non-timing subset of ``<repo>/tests``.

    Pins ``pytest.ini``/``--rootdir`` so the child does not depend on its cwd's
    config, and carries both recursion guards (``--ignore`` *and*
    ``--deselect`` for this module / this node).
    """
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(repo / "pytest.ini"),
        "--rootdir",
        str(repo),
        # pytest.ini's own ``addopts = -q`` would make this ``-qq``, which
        # suppresses the summary line the node records; keep exactly one ``-q``.
        "-o",
        "addopts=",
        "-q",
        "-p",
        "no:cacheprovider",
        str(repo / "tests"),
    ]
    for module in _INNER_EXCLUDED:
        args.append(f"--ignore={repo / 'tests' / module}")
    # Recursion guard — belt and braces: the child never runs this module (and
    # so never this node), whether or not the ignore alone is honoured.
    this_module = repo / "tests" / "test_d42_nonregression.py"
    args.append(f"--ignore={this_module}")
    args.append(f"--deselect={this_module}::test_full_offscreen_suite_is_green")
    return args


def _run_inner_suite(
    cwd: pathlib.Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run the child suite from ``cwd`` with ``env`` — the single seam tests patch.

    ``env["DB_PATH"]`` lives under the caller's ``tmp_path``; the ``--basetemp``
    is derived beside it so every invocation gets a unique, isolated one.
    """
    basetemp = pathlib.Path(env["DB_PATH"]).parent / "inner-basetemp"
    return subprocess.run(
        _inner_pytest_args(cwd) + [f"--basetemp={basetemp}"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=_INNER_TIMEOUT_S,
    )


def _inner_collected_count(stdout: str) -> int:
    """Collected-outcome count from pytest's ``-q`` summary line (0 if absent)."""
    lines = [line for line in stdout.strip().splitlines() if line.strip()]
    if not lines:
        return 0
    return sum(int(count) for count in _INNER_OUTCOME_RE.findall(lines[-1]))


def test_full_offscreen_suite_is_green(tmp_path) -> None:
    """AC3 (P2-T23-T31) / ESC-065: the stable non-timing subset is green.

    The child is a **subset**, never a full-suite run: every module under
    ``tests/`` except the six in :data:`_INNER_EXCLUDED` — the three wall-clock
    gates (``test_d24_smoke_gate.py``, ``test_d28_4_gate.py``,
    ``test_d28_tick_burst_baseline.py``) and the three Qt-teardown-sensitive
    ones (``test_session_overlay.py``, ``test_d28_5_teardown.py``, which pumps
    ``processEvents`` mid-teardown, and ``test_watchlist_addflow_d22.py``, whose
    ``seed_guard`` node segfaulted in this task's three-run check).
    Whole-suite-green evidence belongs to ``verify_tests.py`` ->
    ``docs/code_review/test_verification.json`` and to the ``P5-T10`` phase
    gate, not to this node.

    The child runs from the repo (three modules read repo-relative paths) with a
    fresh ``DB_PATH``, a unique ``--basetemp``, ``-p no:cacheprovider`` and
    ``PYTHONDONTWRITEBYTECODE=1`` (ESC-043). The node is excluded from the inner
    run so the check cannot recurse; the outer run still exercises this file
    (including the AC-D16.7 and AC-D16.1/3/4 guards above).
    """
    repo = pathlib.Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["DB_PATH"] = str(tmp_path / "d42_reconciliation_suite.db")
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    started = time.perf_counter()
    result = _run_inner_suite(repo, env)
    elapsed = time.perf_counter() - started

    collected = _inner_collected_count(result.stdout)
    print(
        f"inner suite: {collected} collected outcomes in {elapsed:.2f}s "
        f"(rc={result.returncode})"
    )

    assert result.returncode == 0, (
        f"the stable non-timing subset is not green (rc={result.returncode}):\n"
        + result.stdout[-12000:]
        + "\n--- stderr (head: the crash site) ---\n"
        + result.stderr[:4000]
        + "\n--- stderr (tail) ---\n"
        + result.stderr[-4000:]
    )
    assert collected > 0, (
        "the child collected no tests — the subset selection is broken:\n"
        + result.stdout[-8000:]
    )


# ---------------------------------------------------------------------------
# ESC-065 — the discrimination half (durable; the real-tree check is manual)
# ---------------------------------------------------------------------------
def test_inner_selection_is_a_stable_non_timing_subset(tmp_path, monkeypatch) -> None:
    """P5-T11-T11: the argv shape, the guards, and the node's cwd/env seam."""
    repo = pathlib.Path(__file__).resolve().parents[1]
    args = _inner_pytest_args(repo)

    assert str(repo / "tests") in args
    assert args[args.index("-c") + 1] == str(repo / "pytest.ini")
    assert args[args.index("--rootdir") + 1] == str(repo)
    assert args[args.index("-p") + 1] == "no:cacheprovider"

    assert set(_INNER_EXCLUDED) == {
        "test_d24_smoke_gate.py",
        "test_d28_4_gate.py",
        "test_d28_tick_burst_baseline.py",
        "test_session_overlay.py",
        "test_d28_5_teardown.py",
        # Added after this task's three-run check caught a real SIGSEGV at
        # test_D22_07_T03_seed_guard; see the comment at _INNER_EXCLUDED.
        "test_watchlist_addflow_d22.py",
    }
    ignores = [arg for arg in args if arg.startswith("--ignore=")]
    assert len(ignores) == len(_INNER_EXCLUDED) + 1
    for module in _INNER_EXCLUDED:
        assert f"--ignore={repo / 'tests' / module}" in ignores

    this_module = repo / "tests" / "test_d42_nonregression.py"
    assert f"--ignore={this_module}" in ignores
    assert (
        f"--deselect={this_module}::test_full_offscreen_suite_is_green" in args
    )

    seen: dict[str, object] = {}

    def _fake_run_inner_suite(cwd, env):
        seen["cwd"] = cwd
        seen["env"] = env
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout="7 passed in 0.01s", stderr=""
        )

    monkeypatch.setattr(sys.modules[__name__], "_run_inner_suite", _fake_run_inner_suite)
    test_full_offscreen_suite_is_green(tmp_path)

    assert pathlib.Path(seen["cwd"]) == repo
    child_env = seen["env"]
    assert child_env["QT_QPA_PLATFORM"] == "offscreen"
    assert child_env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert pathlib.Path(child_env["DB_PATH"]).parent == tmp_path


def test_red_inner_child_is_caught(tmp_path, monkeypatch) -> None:
    """P5-T11-T31 (durable half): a red child makes the node fail, naming it."""
    tail = "FAILED tests/test_x.py::test_y - assert False"

    def _fake_run_inner_suite(cwd, env):
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout=tail, stderr=""
        )

    monkeypatch.setattr(sys.modules[__name__], "_run_inner_suite", _fake_run_inner_suite)
    with pytest.raises(AssertionError) as excinfo:
        test_full_offscreen_suite_is_green(tmp_path)
    assert tail in str(excinfo.value)

