"""Offscreen unit tests for the pure ET trading-day/holiday calendar (T37 / D16).

Covers the task's T37-T01..T37-T06 tests: by-rule holidays (incl. Good Friday and
a future year), ordinary weekday/weekend classification, observed-day shifts for
weekend-falling fixed-date holidays, ``trading_days`` exactness, ``session_windows``
boundaries/clipping, and Qt-free import.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime, timedelta

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from services.market_calendar import (
    is_trading_day,
    session_windows,
    trading_days,
)

EASTERN = ZoneInfo("America/New_York")
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _et_ts(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=EASTERN).timestamp())


# ---------------------------------------------------------------------------
# T37-T01 — every by-rule holiday returns False, across >=2 years incl. future
# ---------------------------------------------------------------------------
# Every US equity market holiday, for 2023 and a future year (2027), with the
# observed/actual market-closure date. These are derived expectations, not a
# source of truth in the implementation (the module computes them by rule).
_BY_RULE_HOLIDAY_CLOSURES = [
    # --- 2023 ---
    (date(2023, 1, 2), "New Year's Day (observed; Jan 1 Sun)"),
    (date(2023, 1, 16), "MLK Jr. Day (3rd Mon Jan)"),
    (date(2023, 2, 20), "Presidents' Day (3rd Mon Feb)"),
    (date(2023, 4, 7), "Good Friday"),
    (date(2023, 5, 29), "Memorial Day (last Mon May)"),
    (date(2023, 6, 19), "Juneteenth"),
    (date(2023, 7, 4), "Independence Day"),
    (date(2023, 9, 4), "Labor Day (1st Mon Sep)"),
    (date(2023, 11, 23), "Thanksgiving (4th Thu Nov)"),
    (date(2023, 12, 25), "Christmas Day"),
    # --- 2027 (future) ---
    (date(2027, 1, 1), "New Year's Day"),
    (date(2027, 1, 18), "MLK Jr. Day (3rd Mon Jan)"),
    (date(2027, 2, 15), "Presidents' Day (3rd Mon Feb)"),
    (date(2027, 3, 26), "Good Friday"),
    (date(2027, 5, 31), "Memorial Day (last Mon May)"),
    (date(2027, 6, 18), "Juneteenth (observed; Jun 19 Sat)"),
    (date(2027, 7, 5), "Independence Day (observed; Jul 4 Sun)"),
    (date(2027, 9, 6), "Labor Day (1st Mon Sep)"),
    (date(2027, 11, 25), "Thanksgiving (4th Thu Nov)"),
    (date(2027, 12, 24), "Christmas Day (observed; Dec 25 Sat)"),
]


@pytest.mark.parametrize(
    "holiday,label",
    _BY_RULE_HOLIDAY_CLOSURES,
    ids=[label for _, label in _BY_RULE_HOLIDAY_CLOSURES],
)
def test_t37_t01_by_rule_holidays_are_non_trading(holiday: date, label: str) -> None:
    assert is_trading_day(holiday) is False, f"{label} {holiday} should be non-trading"


def test_t37_t01_good_friday_derived_for_future_year() -> None:
    # 2027 Easter Sunday is 2027-03-28, so Good Friday is 2027-03-26 — computed,
    # not listed. (A fixed year list would have to be edited for this.)
    easter_2027 = date(2027, 3, 28)
    good_friday_2027 = easter_2027 - timedelta(days=2)
    assert good_friday_2027 == date(2027, 3, 26)
    assert is_trading_day(good_friday_2027) is False


# ---------------------------------------------------------------------------
# T37-T02 — ordinary weekday True; Saturday/Sunday False
# ---------------------------------------------------------------------------
def test_t37_t02_ordinary_weekday_and_weekend() -> None:
    assert date(2026, 9, 21).weekday() == 0  # Monday sanity
    assert is_trading_day(date(2026, 9, 21)) is True
    assert is_trading_day(date(2026, 9, 19)) is False  # Saturday
    assert is_trading_day(date(2026, 9, 20)) is False  # Sunday


def test_t37_t02_accepts_datetime() -> None:
    assert is_trading_day(datetime(2026, 9, 21, 14, 30)) is True
    assert is_trading_day(datetime(2026, 9, 20, 14, 30)) is False


# ---------------------------------------------------------------------------
# T37-T03 — observed-day shifts for weekend-falling fixed-date holidays
# ---------------------------------------------------------------------------
def test_t37_t03_observed_shifts_are_non_trading() -> None:
    # Independence Day 2026-07-04 is a Saturday -> observed Fri 2026-07-03.
    assert date(2026, 7, 4).weekday() == 5
    assert is_trading_day(date(2026, 7, 3)) is False
    # Christmas 2022-12-25 is a Sunday -> observed Mon 2022-12-26.
    assert date(2022, 12, 25).weekday() == 6
    assert is_trading_day(date(2022, 12, 26)) is False
    # Juneteenth 2027-06-19 is a Saturday -> observed Fri 2027-06-18.
    assert date(2027, 6, 19).weekday() == 5
    assert is_trading_day(date(2027, 6, 18)) is False
    # New Year's Day 2023-01-01 is a Sunday -> observed Mon 2023-01-02.
    assert date(2023, 1, 1).weekday() == 6
    assert is_trading_day(date(2023, 1, 2)) is False
    # The weekend legal dates themselves are non-trading as well.
    for legal in (
        date(2026, 7, 4),
        date(2022, 12, 25),
        date(2027, 6, 19),
        date(2023, 1, 1),
    ):
        assert is_trading_day(legal) is False


def test_t37_t03_new_years_year_end_exception_keeps_dec31_open() -> None:
    # NYSE Rule 7.2 year-end accounting-period exception (ESC-023 / AC-D16.7):
    # when Jan 1 is a Saturday the market does NOT close on the preceding Friday
    # (Dec 31 of the prior year), and no substitute closure is created, so that
    # Dec 31 stays a trading day. Every other observed shift is unchanged.
    for jan1, dec31 in (
        (date(2022, 1, 1), date(2021, 12, 31)),
        (date(2028, 1, 1), date(2027, 12, 31)),
        (date(2033, 1, 1), date(2032, 12, 31)),
        (date(2039, 1, 1), date(2038, 12, 31)),
    ):
        assert jan1.weekday() == 5, f"{jan1} must be a Saturday"
        assert dec31.weekday() == 4, f"{dec31} must be the preceding Friday"
        assert is_trading_day(dec31) is True, f"{dec31} must stay open"
    # The Saturday legal New Year's date is non-trading only because it is a
    # weekend; the following Monday trades.
    assert is_trading_day(date(2022, 1, 1)) is False
    assert is_trading_day(date(2022, 1, 3)) is True


def test_t37_t03_neighbour_weekday_still_trades() -> None:
    # The shift must not bleed into the surrounding trading days.
    assert is_trading_day(date(2026, 7, 2)) is True   # Thu before observed Jul 3
    assert is_trading_day(date(2022, 12, 27)) is True  # Tue after observed Dec 26
    assert is_trading_day(date(2022, 1, 3)) is True    # Mon after a Saturday Jan 1


# ---------------------------------------------------------------------------
# T37-T04 — trading_days returns the exact ascending trading-day set
# ---------------------------------------------------------------------------
def test_t37_t04_trading_days_excludes_weekend_and_holiday() -> None:
    # Mon 2026-06-29 .. Tue 2026-07-07 (ET) contains the Independence Day
    # weekend: Jul 4 Sat, Jul 5 Sun, and the observed closure Fri Jul 3.
    start = _et_ts(2026, 6, 29, 0, 0)
    end = _et_ts(2026, 7, 7, 23, 59)
    days = trading_days(start, end)
    expected = [
        date(2026, 6, 29),
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
        date(2026, 7, 6),
        date(2026, 7, 7),
    ]
    assert days == expected
    assert days == sorted(days)
    for non_trading in (date(2026, 7, 3), date(2026, 7, 4), date(2026, 7, 5)):
        assert non_trading not in days


def test_t37_t04_trading_days_inclusive_endpoints_and_empty_reversed() -> None:
    # A single trading day is included when the range is that exact ET day.
    one_day = _et_ts(2026, 9, 21, 0, 0)
    assert trading_days(one_day, _et_ts(2026, 9, 21, 23, 59)) == [date(2026, 9, 21)]
    # Reversed range yields nothing.
    assert trading_days(_et_ts(2026, 9, 22), _et_ts(2026, 9, 21)) == []


# ---------------------------------------------------------------------------
# T37-T05 — session_windows: one per trading day, correct ET bounds, clipped
# ---------------------------------------------------------------------------
def test_t37_t05_rth_windows_clipped_no_non_trading_day() -> None:
    # Thu 2026-07-02 12:00 ET .. Mon 2026-07-06 12:00 ET. Jul 3 is the observed
    # holiday and Jul 4/5 are the weekend, so only Jul 2 and Jul 6 trade.
    start = _et_ts(2026, 7, 2, 12, 0)
    end = _et_ts(2026, 7, 6, 12, 0)
    windows = session_windows(start, end, ext_hours=False)

    assert windows == [
        {"start_ts": start, "end_ts": _et_ts(2026, 7, 2, 16, 0)},
        {"start_ts": _et_ts(2026, 7, 6, 9, 30), "end_ts": end},
    ]
    # One window per trading day, none for the holiday/weekend days.
    assert len(windows) == len(trading_days(start, end)) == 2
    for w in windows:
        assert w["start_ts"] >= start and w["end_ts"] <= end


def test_t37_t05_extended_hours_bounds_and_clipping() -> None:
    start = _et_ts(2026, 7, 2, 12, 0)
    end = _et_ts(2026, 7, 6, 12, 0)
    windows = session_windows(start, end, ext_hours=True)

    assert windows == [
        {"start_ts": start, "end_ts": _et_ts(2026, 7, 2, 20, 0)},
        {"start_ts": _et_ts(2026, 7, 6, 4, 0), "end_ts": end},
    ]
    assert len(windows) == 2
    for w in windows:
        assert w["start_ts"] >= start and w["end_ts"] <= end


@pytest.mark.parametrize("ext_hours", [False, True])
def test_t37_t05_full_day_exact_et_boundaries(ext_hours: bool) -> None:
    # A full ET day that is a trading day yields exactly one window with the
    # canonical ET boundaries (no clipping).
    start = _et_ts(2026, 7, 2, 0, 0)
    end = _et_ts(2026, 7, 2, 23, 59)
    windows = session_windows(start, end, ext_hours=ext_hours)
    if ext_hours:
        expected = [{"start_ts": _et_ts(2026, 7, 2, 4, 0), "end_ts": _et_ts(2026, 7, 2, 20, 0)}]
    else:
        expected = [{"start_ts": _et_ts(2026, 7, 2, 9, 30), "end_ts": _et_ts(2026, 7, 2, 16, 0)}]
    assert windows == expected


def test_t37_t05_non_trading_range_has_no_windows() -> None:
    # Fri 2026-07-03 (observed holiday) .. Sun 2026-07-05: all non-trading.
    start = _et_ts(2026, 7, 3, 0, 0)
    end = _et_ts(2026, 7, 5, 23, 59)
    assert session_windows(start, end, ext_hours=False) == []
    assert session_windows(start, end, ext_hours=True) == []


# ---------------------------------------------------------------------------
# T37-T06 — Qt-free import (no PyQt6/pyqtgraph, no QApplication)
# ---------------------------------------------------------------------------
_QT_MODULE_CHECK = """
import sys
import services.market_calendar as m

bad = [
    name for name in sys.modules
    if name.split(".")[0] in {"PyQt6", "PyQt5", "PySide2", "PySide6", "pyqtgraph"}
]
assert not bad, "Qt modules imported: %r" % (bad,)
assert "QApplication" not in dir(sys.modules.get("PyQt6"))
# Prove the calendar is functional without a QApplication.
from datetime import date
assert m.is_trading_day(date(2026, 9, 21)) is True
assert m.is_trading_day(date(2026, 9, 19)) is False
print("QT_FREE_OK")
"""


def test_t37_t06_import_is_qt_free_in_isolated_interpreter() -> None:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", _QT_MODULE_CHECK],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    assert "QT_FREE_OK" in result.stdout


def test_t37_t06_source_imports_no_qt() -> None:
    import ast

    source = os.path.join(_REPO_ROOT, "services", "market_calendar.py")
    with open(source, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=source)

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden = {"PyQt6", "PyQt5", "PySide6", "PySide2", "pyqtgraph"}
    assert imported_roots.isdisjoint(forbidden), imported_roots & forbidden
