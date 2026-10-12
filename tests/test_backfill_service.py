"""Offscreen unit tests for the pure missing-span / chunk-request planner (T38 / D16).

Covers the task's T38-T01..T38-T08 tests: per-timeframe bar periods; internal-hole
and tail-gap detection at trading-day granularity (parameterized over all six
timeframes and two seeded series scenarios); no-redundant-request and empty-cache
guards; newest-first chunking with UTC-hyphenated anchors; short-span single-plan
behaviour; and Qt-free import in an isolated interpreter.

The planner is pure, so no QApplication, live TWS or database is required.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import (
    MissingSpan,
    RequestPlan,
    bar_period_seconds,
    find_missing_spans,
    plan_requests,
)
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIMEFRAMES = ["1 min", "5 mins", "15 mins", "1 hour", "4 hours", "1 day"]

# Hardcoded expectations, deliberately independent of the implementation's own
# duration parser (the repo's TIMEFRAME_CONFIG durations are 1D / 5D / 5D / 10D /
# 30D / 1Y).
_EXPECTED_PERIODS = {
    "1 min": 60,
    "5 mins": 300,
    "15 mins": 900,
    "1 hour": 3600,
    "4 hours": 14400,
    "1 day": 86400,
}
_DURATION_SECONDS = {
    "1 min": 1 * 86400,
    "5 mins": 5 * 86400,
    "15 mins": 5 * 86400,
    "1 hour": 10 * 86400,
    "4 hours": 30 * 86400,
    "1 day": 365 * 86400,
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _et_ts(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=EASTERN).timestamp())


def _day_start(year: int, month: int, day: int) -> int:
    return _et_ts(year, month, day, 0, 0)


def _seed(days) -> list[int]:
    """One *complete* RTH day of 1-min bars for each ``(y, m, d)`` in ``days``.

    D27.7: ``find_missing_spans`` now also runs bar-period-granularity gap
    detection on trailing trading days, so a "present" day must be seeded as
    a genuinely complete intraday series — a single noon bar is (correctly)
    reported as a day with intraday holes. A full 1-min series is gap-free
    for every timeframe in the suite, so these day-presence tests keep their
    exact assertions.
    """
    out: list[int] = []
    for (y, m, d) in days:
        h, minute = 9, 30
        while (h, minute) <= (15, 59):
            out.append(_et_ts(y, m, d, h, minute))
            minute += 1
            if minute >= 60:
                h += 1
                minute = 0
    return out


def _covered_days(span: MissingSpan) -> list[date]:
    """ET calendar days that the span overlaps (end boundary exclusive)."""
    days: list[date] = []
    current = datetime.fromtimestamp(span.start_ts, tz=EASTERN).date()
    while _day_start(current.year, current.month, current.day) < span.end_ts:
        days.append(current)
        current += timedelta(days=1)
    return days


def _covered_trading_days(span: MissingSpan) -> list[date]:
    return [d for d in _covered_days(span) if is_trading_day(d)]


def _parse_end(end_date_time: str) -> int:
    return int(
        datetime.strptime(end_date_time, "%Y%m%d-%H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


# ---------------------------------------------------------------------------
# T38-T01 — bar_period_seconds over the six timeframes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe", TIMEFRAMES)
def test_t38_t01_bar_period_seconds(timeframe: str) -> None:
    assert bar_period_seconds(timeframe) == _EXPECTED_PERIODS[timeframe]
    assert bar_period_seconds(timeframe) == TIMEFRAME_SECONDS[timeframe]


# ---------------------------------------------------------------------------
# T38-T02 — internal hole detection, merged, weekends/holidays excluded
# ---------------------------------------------------------------------------
# Scenario A: an internal hole that spans a weekend. Present Thu 09-17 and the
# following Tue 09-22; missing Fri 09-18 and Mon 09-21 -> one merged span.
_SCENARIO_WEEKEND_HOLE = {
    "present": [(2026, 9, 14), (2026, 9, 15), (2026, 9, 16), (2026, 9, 17), (2026, 9, 22)],
    "missing": [(2026, 9, 18), (2026, 9, 21)],
    "now": (2026, 9, 22, 12, 0),
    "expected": [MissingSpan(_day_start(2026, 9, 18), _day_start(2026, 9, 22))],
}

# Scenario B: the reported repro — present 09-14..09-18 and 09-28..10-02, missing
# the five trading weekdays 09-21..09-25 -> one merged span.
_SCENARIO_REPORTED_REPRO = {
    "present": [
        (2026, 9, 14), (2026, 9, 15), (2026, 9, 16), (2026, 9, 17), (2026, 9, 18),
        (2026, 9, 28), (2026, 9, 29), (2026, 9, 30), (2026, 10, 1), (2026, 10, 2),
    ],
    "missing": [
        (2026, 9, 21), (2026, 9, 22), (2026, 9, 23), (2026, 9, 24), (2026, 9, 25),
    ],
    "now": (2026, 10, 2, 20, 0),
    "expected": [MissingSpan(_day_start(2026, 9, 21), _day_start(2026, 9, 26))],
}

_SCENARIOS = {
    "weekend_hole": _SCENARIO_WEEKEND_HOLE,
    "reported_repro": _SCENARIO_REPORTED_REPRO,
}


@pytest.mark.parametrize("timeframe", TIMEFRAMES)
@pytest.mark.parametrize("scenario", list(_SCENARIOS))
def test_t38_t02_internal_hole_detected_merged(timeframe: str, scenario: str) -> None:
    cfg = _SCENARIOS[scenario]
    spans = find_missing_spans(_seed(cfg["present"]), _et_ts(*cfg["now"]), timeframe)

    assert spans == cfg["expected"], f"{scenario} spans: {spans}"
    assert len(spans) == 1  # adjacent missing trading days merged into one span

    # Exactly the missing trading weekdays are covered; weekends/holidays are not.
    covered = _covered_trading_days(spans[0])
    assert covered == [date(*d) for d in cfg["missing"]]
    for covered_day in covered:
        assert is_trading_day(covered_day) is True
    # The weekend between Fri 09-18 and Mon 09-21 is inside the merged span but is
    # never reported as its own missing day (genuine closure).
    assert date(2026, 9, 19) not in covered and date(2026, 9, 20) not in covered


# ---------------------------------------------------------------------------
# T38-T03 — tail gap after the newest cached bar
# ---------------------------------------------------------------------------
def test_t38_t03_tail_gap_span() -> None:
    cached = _seed([(2026, 9, 14), (2026, 9, 15), (2026, 9, 16)])  # ends Wed
    now = _et_ts(2026, 9, 22, 12, 0)  # following Tue

    spans = find_missing_spans(cached, now, "5 mins")

    assert spans == [MissingSpan(_day_start(2026, 9, 17), now)]
    assert _covered_trading_days(spans[0]) == [
        date(2026, 9, 17),  # Thu
        date(2026, 9, 18),  # Fri
        date(2026, 9, 21),  # Mon
        date(2026, 9, 22),  # Tue (now)
    ]
    # The span is one continuous fetch window Thu..now (it trivially straddles the
    # weekend), but the weekend days are never reported as missing trading days.
    weekend = {date(2026, 9, 19), date(2026, 9, 20)}
    assert weekend.isdisjoint(set(_covered_trading_days(spans[0])))


# ---------------------------------------------------------------------------
# T38-T04 — no redundant request when cache is current / only a weekend gap
# ---------------------------------------------------------------------------
def test_t38_t04_cache_current_at_now_returns_empty() -> None:
    cached = _seed(
        [(2026, 9, 21), (2026, 9, 22), (2026, 9, 23), (2026, 9, 24), (2026, 9, 25)]
    )
    now = _et_ts(2026, 9, 25, 18, 0)
    assert find_missing_spans(cached, now, "5 mins") == []


def test_t38_t04_weekend_only_gap_returns_empty() -> None:
    cached = _seed(
        [(2026, 9, 14), (2026, 9, 15), (2026, 9, 16), (2026, 9, 17), (2026, 9, 18)]
    )
    now = _et_ts(2026, 9, 20, 12, 0)  # Sunday after the cached Friday
    assert find_missing_spans(cached, now, "5 mins") == []


# ---------------------------------------------------------------------------
# T38-T05 — empty cache returns []
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe", TIMEFRAMES)
def test_t38_t05_empty_cache_returns_empty(timeframe: str) -> None:
    assert find_missing_spans([], _et_ts(2026, 9, 22, 12, 0), timeframe) == []


# ---------------------------------------------------------------------------
# T38-T06 — chunking: newest-first, full coverage, anchors step by one duration
# ---------------------------------------------------------------------------
# (span_seconds, expected_chunk_count) chosen so the span exceeds one configured
# duration and chunk count is the configured-duration ceiling.
_CHUNK_CASES = {
    "1 min": (3 * 86400 + 43200, 4),   # 3.5 D / 1 D  -> 4
    "5 mins": (12 * 86400, 3),         # 12 D / 5 D   -> 3
    "15 mins": (10 * 86400, 2),        # 10 D / 5 D   -> 2
    "1 hour": (25 * 86400, 3),         # 25 D / 10 D  -> 3
    "4 hours": (75 * 86400, 3),        # 75 D / 30 D  -> 3
    "1 day": (500 * 86400, 2),         # 500 D / 365 D -> 2
}
_BASE = 1_700_000_000


@pytest.mark.parametrize("timeframe", TIMEFRAMES)
def test_t38_t06_chunking_newest_first_full_coverage(timeframe: str) -> None:
    span_seconds, expected_count = _CHUNK_CASES[timeframe]
    start = _BASE
    end = _BASE + span_seconds
    cfg = TIMEFRAME_CONFIG[timeframe]
    duration_seconds = _DURATION_SECONDS[timeframe]

    plans = plan_requests([MissingSpan(start, end)], timeframe)

    # Chunk count equals the configured-duration ceiling of the span.
    assert len(plans) == expected_count
    assert len(plans) == -(-span_seconds // duration_seconds)

    # Each plan carries the timeframe bar_size/duration and its origin span.
    for plan in plans:
        assert isinstance(plan, RequestPlan)
        assert plan.duration == cfg["duration"]
        assert plan.bar_size == cfg["bar_size"]
        assert plan.span_start_ts == start and plan.span_end_ts == end

    anchors = [_parse_end(p.endDateTime) for p in plans]

    # Newest first, first anchor at the span end, successive anchors step back by
    # exactly one configured duration.
    expected_anchors = [end - i * duration_seconds for i in range(expected_count)]
    assert anchors == expected_anchors
    assert anchors == sorted(anchors, reverse=True)

    # Combined coverage reaches the whole span (tightly: the oldest anchor is
    # still past the span start, yet the full chunk below it covers it).
    assert end - expected_count * duration_seconds <= start
    if expected_count > 1:
        assert end - (expected_count - 1) * duration_seconds > start

    # UTC hyphenated yyyyMMdd-HH:mm:ss format, matching the repo anchor helper.
    for plan, anchor in zip(plans, expected_anchors):
        assert re.fullmatch(r"\d{8}-\d{2}:\d{2}:\d{2}", plan.endDateTime)
        assert plan.endDateTime == datetime.fromtimestamp(
            anchor, tz=timezone.utc
        ).strftime("%Y%m%d-%H:%M:%S")


# ---------------------------------------------------------------------------
# T38-T07 — short span: exactly one plan anchored at the span end
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe", TIMEFRAMES)
def test_t38_t07_short_span_single_plan_anchor_at_end(timeframe: str) -> None:
    start = _BASE
    end = _BASE + 3600  # one hour, shorter than every configured duration
    assert 3600 < _DURATION_SECONDS[timeframe]

    plans = plan_requests([MissingSpan(start, end)], timeframe)

    assert len(plans) == 1
    assert plans[0].span_start_ts == start and plans[0].span_end_ts == end
    assert _parse_end(plans[0].endDateTime) == end


# ---------------------------------------------------------------------------
# T38-T08 — Qt-free import (no PyQt6/pyqtgraph, no live IBKR connection)
# ---------------------------------------------------------------------------
_QT_MODULE_CHECK = """
import sys
import services.backfill_service as m

bad = [
    name for name in sys.modules
    if name.split(".")[0] in {"PyQt6", "PyQt5", "PySide2", "PySide6", "pyqtgraph"}
]
assert not bad, "Qt modules imported: %r" % (bad,)
assert "QApplication" not in dir(sys.modules.get("PyQt6"))
# The planner is functional without a QApplication and without any connection.
assert m.bar_period_seconds("1 min") == 60
assert m.find_missing_spans([], 0, "5 mins") == []
plans = m.plan_requests([m.MissingSpan(1_700_000_000, 1_700_000_000 + 3600)], "5 mins")
assert len(plans) == 1 and plans[0].bar_size == "5 mins"
print("QT_FREE_OK")
"""


def test_t38_t08_import_is_qt_free_in_isolated_interpreter() -> None:
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


def test_t38_t08_source_imports_no_qt() -> None:
    source = os.path.join(_REPO_ROOT, "services", "backfill_service.py")
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
