"""D77 / D82 / D83 (P27-01) — planner identity, the empty span, one window rule.

Three promises, asserted separately so a regression in one cannot hide behind
another:

* **D77** — ``plan_requests`` emits one plan per request identity
  ``(endDateTime, duration, bar_size)``; two spans that share an anchor are the
  same request and are charged once, while the *detector* keeps its overlapping
  spans and their reasons (the floor span's earlier start survives).
* **D83** — a span with no positive length (``end_ts <= start_ts``) yields no
  plan at all.
* **D82** — ``_bar_level_missing_spans`` assigns a bar to exactly one session
  window with half-open ``[start, end)`` membership (the *now* cap stays
  inclusive) and uses one 1.5-bar-period threshold for the leading, internal
  and trailing edges. ``present_days`` is deliberately **not** that rule: its
  day-level predicate stays inclusive at the close so an end-stamped (``16:00``
  ET) daily bar is present.

The suite is pure: no Qt, no DB, no clock — every timestamp is injected, and the
expected chunk arithmetic is written here (the pre-change rule) rather than
imported from the module under test.
"""

from __future__ import annotations

import inspect
import re
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

import services.backfill_service as planner
from services.backfill_service import (
    MissingSpan,
    find_missing_spans,
    plan_requests,
    present_days,
)
from services.market_calendar import is_trading_day, session_windows

EASTERN = ZoneInfo("America/New_York")

# The planner's configured duration/bar size for the two timeframes this suite
# exercises, hardcoded so the expectations do not derive from the module under
# test (the repo's config: 5 mins -> 30 D, 1 hour -> 60 D).
_DURATION = {"5 mins": "30 D", "1 hour": "60 D"}
_BAR_SIZE = {"5 mins": "5 mins", "1 hour": "1 hour"}
_CHUNK_SECONDS = {"5 mins": 30 * 86400, "1 hour": 60 * 86400}
_PERIOD = {"5 mins": 300, "1 hour": 3600}


# ---------------------------------------------------------------------------
# helpers — ET timestamps, chunk arithmetic, coverage
# ---------------------------------------------------------------------------
def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _fmt(ts: int) -> str:
    """The IBKR anchor format the planner emits (UTC, hyphenated)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d-%H:%M:%S")


def _parse_end(end_date_time: str) -> int:
    return int(
        datetime.strptime(end_date_time, "%Y%m%d-%H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def _identities(plans) -> list[tuple[str, str, str]]:
    return [(p.endDateTime, p.duration, p.bar_size) for p in plans]


def _pre_change_anchors(spans, chunk_seconds: int) -> list[int]:
    """The pre-change planner's anchor list, computed here (independent).

    Spans sorted by ``end_ts`` descending, each chunked independently as
    ``max(1, ceil(span_seconds / chunk_seconds))`` anchored at ``end_ts`` and
    stepping back one chunk. No cross-span comparison at all — the identity
    multiset this produces is what D77 de-duplicates.
    """
    anchors: list[int] = []
    for span in sorted(spans, key=lambda s: s.end_ts, reverse=True):
        span_seconds = span.end_ts - span.start_ts
        if span_seconds < 0:
            continue
        count = max(1, -(-span_seconds // chunk_seconds))
        anchor = span.end_ts
        for _ in range(count):
            anchors.append(anchor)
            anchor -= chunk_seconds
    return anchors


def _coverage(plans, chunk_seconds: int) -> list[tuple[int, int]]:
    """Each plan's requested interval ``[anchor - duration, anchor]``."""
    return [(_parse_end(p.endDateTime) - chunk_seconds, _parse_end(p.endDateTime))
            for p in plans]


def _merge(intervals):
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _union_covers(intervals, span: MissingSpan) -> bool:
    return any(
        start <= span.start_ts and span.end_ts <= end
        for start, end in _merge(intervals)
    )


def _rth_bars(y: int, m: int, d: int, last_h: int = 15,
              last_min: int = 55) -> list[int]:
    """5-min RTH bar timestamps from 09:30 ET through ``last_h:last_min``."""
    out: list[int] = []
    h, minute = 9, 30
    while (h, minute) <= (last_h, last_min):
        out.append(_et_ts(y, m, d, h, minute))
        minute += 5
        if minute >= 60:
            h += 1
            minute = 0
    return out


def _last_trading_days(end_day: date, count: int) -> list[date]:
    """The ``count`` trading days ending at ``end_day`` (ascending)."""
    out: list[date] = []
    day = end_day
    while len(out) < count:
        if is_trading_day(day):
            out.append(day)
        day -= timedelta(days=1)
    return list(reversed(out))


def _window(day: date, ext_hours: bool):
    """``day``'s mode window as ``(start_ts, end_ts)``, or ``None``."""
    nxt = day + timedelta(days=1)
    windows = session_windows(
        _et_ts(day.year, day.month, day.day),
        _et_ts(nxt.year, nxt.month, nxt.day),
        ext_hours,
    )
    if not windows:
        return None
    return windows[0]["start_ts"], windows[0]["end_ts"]


def _half_open_present(ts_values, days, ext_hours: bool) -> set[date]:
    """A test-local half-open ``[start, end)`` variant of ``present_days``.

    Written here on purpose (not imported): it exists to show *why* the
    day-level predicate cannot adopt the bar-level window rule — on an
    end-stamped daily series it reports every cached day absent.
    """
    by_day: dict[date, list[int]] = {}
    for ts in ts_values:
        by_day.setdefault(_et_date(ts), []).append(ts)
    present: set[date] = set()
    for day in days:
        window = _window(day, ext_hours)
        if window is None:
            continue
        ws, we = window
        if any(ws <= t < we for t in by_day.get(day, ())):
            present.add(day)
    return present


# ---------------------------------------------------------------------------
# P27-T1-01 (AC-D77.1, AC-D77.3) — one plan per request identity
# ---------------------------------------------------------------------------
def test_p27_t1_01_one_plan_per_identity() -> None:
    """Journey 71's out-of-mode cache, plus a hand-built coinciding pair."""
    now_ts = _et_ts(2026, 10, 16, 12, 0)
    days = _last_trading_days(_et_date(now_ts), 40)

    # Journey 71: the cache holds *ETH* bars (05:00 / 19:00 ET — outside RTH,
    # inside ETH) while the load runs under RTH, so every cached day is
    # out-of-mode and the day-presence span starts at the first cached day. The
    # depth floor (min_sessions=30) adds its own span, sharing the same end_ts.
    cached: list[int] = []
    for day in days:
        cached.append(_et_ts(day.year, day.month, day.day, 5, 0))
        cached.append(_et_ts(day.year, day.month, day.day, 19, 0))
    assert not present_days(cached, ext_hours=False), (
        "fixture must be entirely out of mode under RTH"
    )

    spans = find_missing_spans(
        cached, now_ts, "5 mins", ext_hours=False, min_sessions=30
    )
    assert len(spans) >= 2, f"fixture must produce coinciding spans: {spans}"
    assert len({s.end_ts for s in spans}) == 1, "the spans must share their end"

    plans = plan_requests(spans, "5 mins")
    ids = _identities(plans)
    assert len(ids) == len(set(ids)), f"duplicate request identities: {ids}"

    chunk = _CHUNK_SECONDS["5 mins"]
    pre = _pre_change_anchors(spans, chunk)
    duplicate_count = len(pre) - len(set(pre))
    assert duplicate_count > 0, f"fixture must duplicate an identity: {pre}"
    assert len(plans) == len(pre) - duplicate_count
    assert set(ids) == {
        (_fmt(anchor), _DURATION["5 mins"], _BAR_SIZE["5 mins"])
        for anchor in set(pre)
    }
    # The shared newest anchor is charged once, not once per span.
    shared = max(pre)
    assert sum(1 for p in plans if _parse_end(p.endDateTime) == shared) == 1

    # Hand-built: two spans with the same end and one chunk each -> the
    # pre-change planner spent two identical requests, the new one spends one.
    end = _et_ts(2026, 7, 1)
    pair = [
        MissingSpan(_et_ts(2026, 6, 1), end),
        MissingSpan(_et_ts(2026, 6, 8), end),
    ]
    pair_pre = _pre_change_anchors(pair, chunk)
    assert pair_pre == [end, end], "fixture: two identical single-chunk plans"
    pair_plans = plan_requests(pair, "5 mins")
    assert len(pair_plans) == 1
    assert _identities(pair_plans) == [(_fmt(end), "30 D", "5 mins")]
    assert len(pair_plans) == len(pair_pre) - (len(pair_pre) - len(set(pair_pre)))


# ---------------------------------------------------------------------------
# P27-T1-02 (AC-D77.2, AC-D77.1) — coverage survives de-duplication
# ---------------------------------------------------------------------------
def test_p27_t1_02_overlap_keeps_floor_coverage() -> None:
    """The floor span starts earlier than the presence span; its part still fetches."""
    floor_start = _et_ts(2026, 6, 1)
    presence_start = _et_ts(2026, 6, 11)
    end = _et_ts(2026, 7, 11)  # 40 days from the floor start, 30 from presence
    spans = [
        MissingSpan(floor_start, end),
        MissingSpan(presence_start, end),
    ]
    chunk = _CHUNK_SECONDS["5 mins"]

    plans = plan_requests(spans, "5 mins")
    anchors = [_parse_end(p.endDateTime) for p in plans]

    # Every independently derived pre-change anchor is planned exactly once.
    expected = set(_pre_change_anchors(spans, chunk))
    pre = _pre_change_anchors(spans, chunk)
    assert len(pre) == 3, f"fixture: 2 chunks for the floor span, 1 for presence {pre}"
    assert sorted(anchors, reverse=True) == sorted(expected, reverse=True)
    assert len(anchors) == len(set(anchors))

    # The floor span's earlier part is still fetched (the newest-first chunks
    # reach back past the floor start, not just past the presence start).
    intervals = _coverage(plans, chunk)
    assert min(start for start, _ in intervals) <= floor_start
    assert _union_covers(intervals, MissingSpan(floor_start, end))

    # Coverage is unchanged by the change and contains every input span.
    assert set(_identities(plans)) == {(_fmt(a), "30 D", "5 mins") for a in expected}
    for span in spans:
        assert _union_covers(intervals, span), f"span not covered: {span}"


# ---------------------------------------------------------------------------
# P27-T1-03 (AC-D77.1) — the identity key is all three fields
# ---------------------------------------------------------------------------
def test_p27_t1_03_identity_key_is_three_fields() -> None:
    """Same anchor, different duration/bar size -> two requests, not one."""
    end = _et_ts(2026, 7, 1)
    spans = [MissingSpan(end - 3600, end)]

    five = plan_requests(spans, "5 mins")
    hour = plan_requests(spans, "1 hour")
    assert len(five) == 1 and len(hour) == 1

    assert five[0].endDateTime == hour[0].endDateTime == _fmt(end)
    assert five[0].duration == "30 D" and hour[0].duration == "60 D"
    assert five[0].bar_size == "5 mins" and hour[0].bar_size == "1 hour"

    combined = _identities(five) + _identities(hour)
    assert len(combined) == 2
    assert len(set(combined)) == 2, "an anchor/duration difference must survive"
    assert _PERIOD["1 hour"] != _PERIOD["5 mins"]


# ---------------------------------------------------------------------------
# P27-T1-04 (AC-D83.1) — a span with no positive length plans nothing
# ---------------------------------------------------------------------------
def test_p27_t1_04_zero_length_span_emits_nothing() -> None:
    t = _et_ts(2026, 6, 1, 12, 0)
    u = t + 3600

    assert plan_requests([MissingSpan(t, t)], "5 mins") == []
    assert plan_requests([MissingSpan(t, t), MissingSpan(u, u)], "5 mins") == []
    # Reversed (negative) length is no more requestable than an empty span.
    assert plan_requests([MissingSpan(u, t)], "5 mins") == []

    # Control: a positive span still plans its request.
    control = plan_requests([MissingSpan(t, u)], "5 mins")
    assert len(control) == 1
    assert _parse_end(control[0].endDateTime) == u


# ---------------------------------------------------------------------------
# P27-T1-05 (AC-D82.1) — a close-stamped bar is counted in no window
# ---------------------------------------------------------------------------
def test_p27_t1_05_close_instant_in_no_window() -> None:
    """A complete RTH session + a 16:00 bar + the next session's first bar."""
    day1, day2 = date(2026, 10, 14), date(2026, 10, 15)
    assert is_trading_day(day1) and is_trading_day(day2)

    bars = _rth_bars(day1.year, day1.month, day1.day)  # 09:30..15:55
    boundary = _et_ts(day1.year, day1.month, day1.day, 16, 0)
    next_first = _et_ts(day2.year, day2.month, day2.day, 9, 30)
    cached = bars + [boundary, next_first]

    spans = find_missing_spans(cached, next_first, "5 mins", ext_hours=False)
    assert spans == [], f"spurious spans for a complete session: {spans}"
    assert not any(s.start_ts == boundary or s.end_ts == boundary for s in spans)

    # Membership observable: the closing window's accounting ends at the 15:55
    # bar, so a day whose *only* bar is the 16:00 one contributes nothing (the
    # pre-change ``ws <= t <= we`` membership spent a whole-session span here).
    lone = find_missing_spans([boundary, next_first], next_first, "5 mins",
                              ext_hours=False)
    assert lone == [], f"the 16:00 bar must not be counted in the closing window: {lone}"

    # Partition claim, stated locally: every cached instant lies in exactly one
    # of the two RTH windows, and the boundary instant in none.
    windows = [_window(day1, False), _window(day2, False)]
    for ts in cached:
        counted = sum(1 for ws, we in windows if ws <= ts < we)
        if ts == boundary:
            assert counted == 0
        else:
            assert counted == 1, f"{ts} counted in {counted} windows"


# ---------------------------------------------------------------------------
# P27-T1-06 (AC-D82.2) — one 1.5-period threshold on every edge
# ---------------------------------------------------------------------------
def test_p27_t1_06_one_gap_threshold() -> None:
    day = date(2026, 10, 16)
    assert is_trading_day(day)
    bars = _rth_bars(day.year, day.month, day.day, 11, 0)  # 09:30..11:00
    last = bars[-1]
    period = _PERIOD["5 mins"]

    # hole (in seconds above the last bar), reported?
    cases = [(1.0 * period, False), (1.7 * period, True), (2.0 * period, True)]
    for hole, reported in cases:
        now_ts = last + int(hole)
        spans = find_missing_spans(bars, now_ts, "5 mins", ext_hours=False)
        trailing = [s for s in spans if s.start_ts == last and s.end_ts == now_ts]
        if reported:
            assert trailing, f"{hole / period:.1f}-period hole not reported: {spans}"
            assert spans == [MissingSpan(last, now_ts)], f"unexpected spans: {spans}"
        else:
            assert not trailing, f"{hole / period:.1f}-period hole wrongly reported"
            assert spans == [], f"unexpected spans: {spans}"

    # The docstring states the same number the fixtures bracket.
    texts = [
        planner.__doc__ or "",
        find_missing_spans.__doc__ or "",
        planner._bar_level_missing_spans.__doc__ or "",
        plan_requests.__doc__ or "",
    ]
    stated = {
        float(match)
        for text in texts
        for match in re.findall(r"(\d+(?:\.\d+)?)\s*bar periods", text)
    }
    assert stated == {1.5}, f"docstrings state {stated!r}, code uses 1.5"
    threshold = next(iter(stated))
    assert 1.0 <= threshold < 1.7, "threshold must bracket the 1.0/1.7 fixtures"


# ---------------------------------------------------------------------------
# P27-T1-07 (AC-P27-01-7) — presence stays inclusive at the close
# ---------------------------------------------------------------------------
def test_p27_t1_07_presence_inclusive_at_close() -> None:
    end_day = date(2026, 10, 16)
    assert is_trading_day(end_day)
    days = _last_trading_days(end_day, 10)
    assert len(days) == 10

    # The tree's daily fixture convention: a "1 day" bar is stamped 16:00 ET.
    daily = [_et_ts(d.year, d.month, d.day, 16, 0) for d in days]
    last_close = daily[-1]

    assert present_days(daily, ext_hours=False) == set(days)
    assert present_days(daily, ext_hours=True) == set(days)
    assert find_missing_spans(daily, last_close, "1 day") == []
    assert find_missing_spans(daily, last_close, "1 day", ext_hours=True) == []

    # The regression the inclusive predicate forbids: a half-open *presence*
    # test sees none of the ten cached days and re-requests the whole history.
    # (Under ETH the same bars sit well inside 4:00-20:00, so only the RTH
    # window — whose end is exactly the daily stamp — is the coincidence.)
    assert _half_open_present(daily, days, ext_hours=False) == set()
    assert _half_open_present(daily, days, ext_hours=True) == set(days)

    # An intraday out-of-mode day (pre/post only, under RTH) is still absent.
    prepost_day = days[3]
    prepost = [
        _et_ts(prepost_day.year, prepost_day.month, prepost_day.day, 5, 0),
        _et_ts(prepost_day.year, prepost_day.month, prepost_day.day, 19, 0),
    ]
    assert prepost_day not in present_days(prepost, ext_hours=False)
    assert prepost_day in present_days(prepost, ext_hours=True)

    # Where the two predicates can differ: an intraday bar at the window end is
    # present (inclusive at the close), while the local half-open variant says
    # absent — the divergence the mode-aware cache cannot hold (AR-P27-2).
    close_only = [_et_ts(days[-1].year, days[-1].month, days[-1].day, 16, 0)]
    assert days[-1] in present_days(close_only, ext_hours=False)
    assert _half_open_present(close_only, [days[-1]], ext_hours=False) == set()

    # present_days' signature and its futures branch stay as they were.
    params = list(inspect.signature(present_days).parameters.values())
    assert [p.name for p in params] == ["cached_ts", "ext_hours", "is_futures"]
    assert params[1].default is False and params[2].default is False
    saturday = _et_ts(2026, 10, 17, 12, 0)  # a Saturday
    sunday = _et_ts(2026, 10, 18, 12, 0)    # a Sunday
    futures = present_days([saturday, sunday], is_futures=True)
    assert _et_date(saturday) not in futures
    assert _et_date(sunday) in futures


# ---------------------------------------------------------------------------
# P27-T1-08 (AC-D77.3, AC-D77.1) — Journey 71's edges, end to end
# ---------------------------------------------------------------------------
def test_p27_t1_08_journey_edges() -> None:
    end_day = date(2026, 10, 16)
    assert is_trading_day(end_day)
    now_ts = _et_ts(end_day.year, end_day.month, end_day.day, 16, 0)
    chunk = _CHUNK_SECONDS["5 mins"]

    # (1) Partial floor: the cache covers only the most recent five sessions,
    # so the depth floor's span starts earlier — and must still be fetched.
    week = _last_trading_days(end_day, 5)
    cached = []
    for day in week:
        cached.extend(_rth_bars(day.year, day.month, day.day))
    spans = find_missing_spans(cached, now_ts, "5 mins", min_sessions=30)
    assert len(spans) == 1, f"expected only the floor span: {spans}"
    floor_span = spans[0]
    assert floor_span.start_ts < _et_ts(week[0].year, week[0].month, week[0].day)

    plans = plan_requests(spans, "5 mins")
    ids = _identities(plans)
    assert ids and len(ids) == len(set(ids))
    intervals = _coverage(plans, chunk)
    assert min(start for start, _ in intervals) <= floor_span.start_ts
    assert _union_covers(intervals, floor_span)

    # (2) Empty cache with the floor enabled: one span, one plan — no span pair
    # to collide, and no duplicate identity either way.
    empty_now = _et_ts(end_day.year, end_day.month, end_day.day, 12, 0)
    empty_spans = find_missing_spans([], empty_now, "5 mins", min_sessions=10)
    assert len(empty_spans) == 1
    empty_plans = plan_requests(empty_spans, "5 mins")
    assert len(empty_plans) == 1
    assert len(_identities(empty_plans)) == len(set(_identities(empty_plans)))

    # (3) A cache holding exactly one in-mode bar: in-window, no bar-level hole.
    # 1.0 and exactly 1.5 periods above the last bar are both inside the
    # threshold, so neither spends a request.
    single = [_et_ts(end_day.year, end_day.month, end_day.day, 9, 30)]
    for periods in (1.0, 1.5):
        now = single[0] + int(periods * _PERIOD["5 mins"])
        assert find_missing_spans(single, now, "5 mins") == []
