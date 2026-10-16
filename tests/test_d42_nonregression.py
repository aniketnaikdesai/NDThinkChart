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
* **AC-D16.x** — the reconciliation node runs the rest of the offscreen suite in
  a hermetic subprocess and asserts it is green (no assertion weakened, none
  deleted).

The suite runs offscreen; ``tests/conftest.py`` pins ``DB_PATH`` so pytest runs
are hermetic (ESC-043).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

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
# AC-D16.x — the whole offscreen suite is green (reconciliation node)
# ---------------------------------------------------------------------------
def test_full_offscreen_suite_is_green(tmp_path) -> None:
    """AC3 (P2-T23-T31): the rest of the offscreen suite is green.

    Runs pytest over the whole suite in a hermetic subprocess (fresh ``DB_PATH``;
    ESC-043) and asserts a clean exit. This module is excluded from the inner run
    so the check cannot recurse; the outer run of the suite still exercises this
    file (including the AC-D16.7 and AC-D16.1/3/4 guards above).
    """
    import os
    import pathlib
    import subprocess
    import sys

    repo = pathlib.Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["DB_PATH"] = str(tmp_path / "d42_reconciliation_suite.db")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--ignore={repo / 'tests' / 'test_d42_nonregression.py'}",
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "the offscreen suite is not green:\n"
        + result.stdout[-8000:]
        + "\n--- stderr ---\n"
        + result.stderr[-4000:]
    )
