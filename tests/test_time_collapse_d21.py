"""Unit tests for the pure time-collapse service (D21.4 / task D21-14).

Covers the task's D21-14-T01..T04:

* **T01** (``AC-D21.4.1``) — the coverage-adjusted predicate against the real
  ``services.market_calendar.session_windows``: the eight boundary cases.
* **T02** (``AC-D21.4.2``) — ``1 day`` is a no-op identity map.
* **T03** (``AC-D21.4.1``) — strictly increasing display-x, exact round-trip,
  within-session spacing preserved (only between-session gaps removed).
* **T04** (``AC-D21.4.4``) — a genuine trading-session hole stays visible and the
  service never mutates or drops input bar timestamps.

No Qt/QApplication is required; the service is pure.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from datetime import datetime
from typing import List

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.models import Bar
from services.market_calendar import session_windows
from services.time_collapse_service import (
    TimeCollapseMap,
    build_collapse_map,
    gap_is_non_trading,
)

EASTERN = ZoneInfo("America/New_York")
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BAR_PERIOD = 300  # 5 mins


def _et_ts(y: int, m: int, d: int, h: int = 0, mi: int = 0) -> int:
    return int(datetime(y, m, d, h, mi, tzinfo=EASTERN).timestamp())


def _rth_bars(symbol: str, y: int, m: int, d: int) -> List[Bar]:
    """One full RTH session of 5-min bars (09:30..15:55 inclusive)."""
    bars: List[Bar] = []
    t = _et_ts(y, m, d, 9, 30)
    close = _et_ts(y, m, d, 15, 55)
    while t <= close:
        bars.append(
            Bar(symbol=symbol, timeframe="5 mins", ts=t, open=1.0, high=1.0,
                low=1.0, close=1.0, volume=1.0)
        )
        t += _BAR_PERIOD
    return bars


# ===========================================================================
# D21-14-T01 — the eight boundary cases (coverage-adjusted predicate)
# ===========================================================================
# Clean trading week Mon 2026-09-21 .. Fri 2026-09-25 (no holidays); Thanksgiving
# Thu 2026-11-26 is a genuine mid-week holiday.
_T01_CASES = [
    # (label, a, b, ext_hours, expected_collapse)
    (
        "rth_overnight_fri_1555_to_mon_0930",
        _et_ts(2026, 9, 24, 15, 55),  # Thu last RTH bar (covers to 16:00)
        _et_ts(2026, 9, 25, 9, 30),   # Fri RTH open
        False,
        True,
    ),
    (
        "ext_overnight_fri_1955_to_mon_0400",
        _et_ts(2026, 9, 24, 19, 55),  # Thu last ext bar (covers to 20:00)
        _et_ts(2026, 9, 25, 4, 0),    # Fri ext open
        True,
        True,
    ),
    (
        "weekend_fri_1555_to_mon_0930",
        _et_ts(2026, 9, 25, 15, 55),  # Fri last RTH bar
        _et_ts(2026, 9, 28, 9, 30),   # Mon RTH open
        False,
        True,
    ),
    (
        "holiday_wed_1555_to_fri_0930_thanksgiving",
        _et_ts(2026, 11, 25, 15, 55),  # Wed before Thanksgiving
        _et_ts(2026, 11, 27, 9, 30),   # Fri after (Thu 11-26 holiday)
        False,
        True,
    ),
    (
        "within_session_hole_1100_to_1300",
        _et_ts(2026, 9, 21, 11, 0),
        _et_ts(2026, 9, 21, 13, 0),
        False,
        False,
    ),
    (
        "missing_full_session_mon_close_to_wed_open",
        _et_ts(2026, 9, 21, 15, 55),  # Mon last RTH bar
        _et_ts(2026, 9, 23, 9, 30),   # Wed open (Tue 09-22 absent)
        False,
        False,
    ),
    (
        "partial_halfday_afternoon_hole_1300_to_next_open",
        _et_ts(2026, 9, 21, 13, 0),   # early-close-style last bar
        _et_ts(2026, 9, 22, 9, 30),   # next session open
        False,
        False,
    ),
    (
        "adjacent_bars_1100_to_1105",
        _et_ts(2026, 9, 21, 11, 0),
        _et_ts(2026, 9, 21, 11, 5),
        False,
        True,  # predicate True; removes zero duration (no-op for the map)
    ),
]


@pytest.mark.parametrize(
    "label,a,b,ext_hours,expected",
    _T01_CASES,
    ids=[c[0] for c in _T01_CASES],
)
def test_d21_14_t01_boundary_predicate(label, a, b, ext_hours, expected) -> None:
    got = gap_is_non_trading(a, b, ext_hours, _BAR_PERIOD)
    assert got is expected, f"{label}: gap_is_non_trading -> {got}, expected {expected}"


@pytest.mark.parametrize(
    "label,a,b,ext_hours,expected",
    _T01_CASES,
    ids=[c[0] for c in _T01_CASES],
)
def test_d21_14_t01_predicate_matches_real_session_windows(
    label, a, b, ext_hours, expected
) -> None:
    # The predicate is defined against the real calendar helper — assert the tie.
    windows = session_windows(a + _BAR_PERIOD, b, ext_hours)
    assert (not windows) is expected, f"{label}: session_windows={windows}"


def test_d21_14_t01_adjacent_bar_collapse_is_noop_in_map() -> None:
    # Adjacent bars collapse per the predicate, but the map must not shift them.
    a = _et_ts(2026, 9, 21, 11, 0)
    b = _et_ts(2026, 9, 21, 11, 5)
    assert gap_is_non_trading(a, b, False, _BAR_PERIOD) is True
    bars = [
        Bar("X", "5 mins", a, 1.0, 1.0, 1.0, 1.0, 1.0),
        Bar("X", "5 mins", b, 1.0, 1.0, 1.0, 1.0, 1.0),
    ]
    cmap = build_collapse_map(bars, "5 mins", False)
    assert cmap.is_identity is True
    assert cmap.x_values == [a, b]


def test_d21_14_t01_no_forward_gap_is_not_collapsed() -> None:
    # Defensive: a non-forward pair is never collapsed.
    a = _et_ts(2026, 9, 21, 11, 0)
    assert gap_is_non_trading(a, a, False, _BAR_PERIOD) is False
    assert gap_is_non_trading(a, a - 300, False, _BAR_PERIOD) is False


# ===========================================================================
# D21-14-T02 — 1 day is the identity map
# ===========================================================================
def test_d21_14_t02_one_day_is_identity() -> None:
    daily_ts = [
        _et_ts(2026, 9, 21),  # Mon
        _et_ts(2026, 9, 22),  # Tue
        _et_ts(2026, 9, 23),  # Wed
        _et_ts(2026, 9, 24),  # Thu
        _et_ts(2026, 9, 25),  # Fri
        _et_ts(2026, 9, 28),  # Mon (weekend between)
    ]
    bars = [Bar("SPY", "1 day", t, 1.0, 1.0, 1.0, 1.0, 1.0) for t in daily_ts]
    cmap = build_collapse_map(bars, "1 day", False)

    assert isinstance(cmap, TimeCollapseMap)
    assert cmap.is_identity is True
    for t in daily_ts:
        assert cmap.to_display(t) == t
        assert cmap.to_ts(t) == t
    assert cmap.x_values == daily_ts


def test_d21_14_t02_one_day_identity_even_with_ext_hours() -> None:
    bars = _rth_bars("SPY", 2026, 9, 25) + _rth_bars("SPY", 2026, 9, 28)
    cmap = build_collapse_map(bars, "1 day", True)
    assert cmap.is_identity is True
    for b in bars:
        assert cmap.to_display(b.ts) == b.ts


def test_d21_14_t02_empty_bars_identity() -> None:
    cmap = build_collapse_map([], "1 day", False)
    assert cmap.is_identity is True
    assert cmap.x_values == []


# ===========================================================================
# D21-14-T03 — monotonic display-x, round-trip, within-session spacing
# ===========================================================================
def _multi_session_bars() -> List[Bar]:
    bars: List[Bar] = []
    bars += _rth_bars("SPY", 2026, 9, 24)  # Thu
    bars += _rth_bars("SPY", 2026, 9, 25)  # Fri
    bars += _rth_bars("SPY", 2026, 9, 28)  # Mon (weekend between)
    return bars


def test_d21_14_t03_x_values_strictly_increasing() -> None:
    bars = _multi_session_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    xv = cmap.x_values
    assert len(xv) == len(bars)
    assert all(xv[i] < xv[i + 1] for i in range(len(xv) - 1))


def test_d21_14_t03_round_trip_for_bar_timestamps() -> None:
    bars = _multi_session_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    assert cmap.is_identity is False  # sessions were collapsed
    for b in bars:
        assert cmap.to_ts(cmap.to_display(b.ts)) == b.ts
    for x in cmap.x_values:
        assert cmap.to_display(cmap.to_ts(x)) == x


def test_d21_14_t03_within_session_spacing_preserved() -> None:
    bars = _multi_session_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    # Adjacent 5-min bars inside one session keep their 300s spacing.
    by_ts = {b.ts: cmap.to_display(b.ts) for b in bars}
    thu = _rth_bars("SPY", 2026, 9, 24)
    for prev, nxt in zip(thu, thu[1:]):
        assert by_ts[nxt.ts] - by_ts[prev.ts] == _BAR_PERIOD


def test_d21_14_t03_between_session_gap_is_contiguous() -> None:
    bars = _multi_session_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    by_ts = {b.ts: cmap.to_display(b.ts) for b in bars}
    # Fri last bar -> Mon first bar: collapsed to one bar-period (no empty space).
    fri_last = _et_ts(2026, 9, 25, 15, 55)
    mon_first = _et_ts(2026, 9, 28, 9, 30)
    assert by_ts[mon_first] - by_ts[fri_last] == _BAR_PERIOD
    # Thu last -> Fri first likewise.
    thu_last = _et_ts(2026, 9, 24, 15, 55)
    fri_first = _et_ts(2026, 9, 25, 9, 30)
    assert by_ts[fri_first] - by_ts[thu_last] == _BAR_PERIOD


def test_d21_14_t03_within_session_hole_width_preserved() -> None:
    # A hole inside a session must keep its full width (only between-session
    # gaps are removed). Bars: 09:30, 09:35, 11:00, 13:00 within one session.
    ts = [
        _et_ts(2026, 9, 21, 9, 30),
        _et_ts(2026, 9, 21, 9, 35),
        _et_ts(2026, 9, 21, 11, 0),
        _et_ts(2026, 9, 21, 13, 0),
    ]
    bars = [Bar("SPY", "5 mins", t, 1.0, 1.0, 1.0, 1.0, 1.0) for t in ts]
    cmap = build_collapse_map(bars, "5 mins", False)
    by_ts = {b.ts: cmap.to_display(b.ts) for b in bars}
    assert by_ts[ts[2]] - by_ts[ts[1]] == ts[2] - ts[1]  # 09:35 -> 11:00 kept
    assert by_ts[ts[3]] - by_ts[ts[2]] == ts[3] - ts[2]  # 11:00 -> 13:00 kept


# ===========================================================================
# D21-14-T04 — trading-session holes stay visible; Bar.ts untouched
# ===========================================================================
def _hole_and_collapse_bars() -> List[Bar]:
    bars: List[Bar] = []
    bars += _rth_bars("SPY", 2026, 9, 21)  # Mon
    # Tue 2026-09-22 deliberately absent -> genuine trading-session hole
    bars += _rth_bars("SPY", 2026, 9, 23)  # Wed
    bars += _rth_bars("SPY", 2026, 9, 24)  # Thu
    bars += _rth_bars("SPY", 2026, 9, 25)  # Fri
    bars += _rth_bars("SPY", 2026, 9, 28)  # Mon (weekend between)
    return bars


def test_d21_14_t04_missing_trading_session_is_kept() -> None:
    bars = _hole_and_collapse_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    by_ts = {b.ts: cmap.to_display(b.ts) for b in bars}
    mon_last = _et_ts(2026, 9, 21, 15, 55)
    wed_first = _et_ts(2026, 9, 23, 9, 30)
    # The absent Tuesday keeps its full span visible (not collapsed).
    assert by_ts[wed_first] - by_ts[mon_last] == wed_first - mon_last


def test_d21_14_t04_weekend_still_collapses_alongside_kept_hole() -> None:
    bars = _hole_and_collapse_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    by_ts = {b.ts: cmap.to_display(b.ts) for b in bars}
    fri_last = _et_ts(2026, 9, 25, 15, 55)
    mon_first = _et_ts(2026, 9, 28, 9, 30)
    assert by_ts[mon_first] - by_ts[fri_last] == _BAR_PERIOD


def test_d21_14_t04_never_mutates_or_drops_bars() -> None:
    bars = _hole_and_collapse_bars()
    original_ts = [b.ts for b in bars]
    original_ids = [id(b) for b in bars]
    snapshot = [(b.symbol, b.timeframe, b.ts, b.open, b.high, b.low, b.close, b.volume) for b in bars]

    cmap = build_collapse_map(bars, "5 mins", False)

    # Same objects, same order, same values, same length — nothing dropped/edited.
    assert [b.ts for b in bars] == original_ts
    assert [id(b) for b in bars] == original_ids
    assert [
        (b.symbol, b.timeframe, b.ts, b.open, b.high, b.low, b.close, b.volume)
        for b in bars
    ] == snapshot
    assert len(cmap.x_values) == len(bars)


def test_d21_14_t04_display_only_does_not_fabricate_bars() -> None:
    # x_values has exactly one entry per input bar — no fabricated inter-session
    # bars are inserted, even though display-x is compressed.
    bars = _hole_and_collapse_bars()
    cmap = build_collapse_map(bars, "5 mins", False)
    assert len(cmap.x_values) == len(bars)
    # Every bar's display-x is unique and maps back to its own ts.
    assert len(set(cmap.x_values)) == len(bars)
    for b, x in zip(bars, cmap.x_values):
        assert cmap.to_ts(x) == b.ts


# ===========================================================================
# Purity — the service is Qt-free (no QApplication needed)
# ===========================================================================
def test_d21_14_service_source_imports_no_qt() -> None:
    source = os.path.join(_REPO_ROOT, "services", "time_collapse_service.py")
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


_QT_MODULE_CHECK = """
import sys
import services.time_collapse_service as s
bad = [n for n in sys.modules if n.split('.')[0] in {'PyQt6','PyQt5','PySide2','PySide6','pyqtgraph'}]
assert not bad, 'Qt modules imported: %r' % (bad,)
from data.models import Bar
a = 1790010000
b = a + 300
bars = [Bar('X','5 mins',a,1,1,1,1,1), Bar('X','5 mins',b,1,1,1,1,1)]
cmap = s.build_collapse_map(bars, '5 mins', False)
assert cmap.is_identity is True
print('QT_FREE_OK')
"""


def test_d21_14_service_imports_qt_free_in_isolated_interpreter() -> None:
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


# ===========================================================================
# D21-15 — ChartPanel display-x x-model integration (AC-D21.4.1/.3, D21.2)
# ===========================================================================
# These are integration tests: they boot a real offscreen ChartPanel and assert
# the *rendered* candle/volume x-positions are display-x (non-trading time
# collapsed), that the D1 bands render at collapsed positions, and that the
# D21.2 visible-max volume scan uses display-x after collapse.


def _make_panel(qapp):
    from ui.chart_panel import ChartPanel

    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    return panel


def _candle_xs(panel) -> List[float]:
    # D28.4: candles render across the static layer (closed bars) and the
    # live layer (forming bar) — combine both for the full rendered set.
    return ([float(c[0]) for c in panel.candlestick._raw_data]
            + [float(c[0]) for c in panel.live_candle._raw_data])


def _vol_xs(panel) -> List[float]:
    return ([float(v) for v in panel.volume_bars.opts["x"]]
            + [float(v) for v in panel.live_volume.opts["x"]])


def _ext_bars(symbol: str, y: int, m: int, d: int) -> List[Bar]:
    """One full extended-hours session of 5-min bars (04:00..19:55 inclusive)."""
    bars: List[Bar] = []
    t = _et_ts(y, m, d, 4, 0)
    close = _et_ts(y, m, d, 19, 55)
    while t <= close:
        bars.append(
            Bar(symbol=symbol, timeframe="5 mins", ts=t, open=1.0, high=1.0,
                low=1.0, close=1.0, volume=1.0)
        )
        t += _BAR_PERIOD
    return bars


def _display_of(bars, xs):
    return {b.ts: x for b, x in zip(bars, xs)}


# ── D21-15-T01 / AC-D21.4.1 ───────────────────────────────────────────────────
def test_d21_15_t01_rendered_sessions_contiguous_after_collapse(qapp) -> None:
    panel = _make_panel(qapp)
    try:
        # Full extended-hours sessions Thu / Fri / Mon (weekend between Fri/Mon).
        bars = (
            _ext_bars("SPY", 2026, 9, 24)
            + _ext_bars("SPY", 2026, 9, 25)
            + _ext_bars("SPY", 2026, 9, 28)
        )
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        cmap = panel._collapse_map
        assert cmap is not None and cmap.is_identity is False

        xs = _candle_xs(panel)
        assert len(xs) == len(bars)
        # Candles (and volume bars) are rendered at display-x, not raw ts.
        assert xs == [float(x) for x in cmap.x_values]
        assert _vol_xs(panel) == xs

        x_of = _display_of(bars, xs)
        # Fri last bar -> Mon first bar: collapsed to one bar period (contiguous).
        fri_last = _et_ts(2026, 9, 25, 19, 55)
        mon_first = _et_ts(2026, 9, 28, 4, 0)
        assert x_of[mon_first] - x_of[fri_last] == _BAR_PERIOD
        # Thu last -> Fri first likewise.
        thu_last = _et_ts(2026, 9, 24, 19, 55)
        fri_first = _et_ts(2026, 9, 25, 4, 0)
        assert x_of[fri_first] - x_of[thu_last] == _BAR_PERIOD

        # Normal within-session spacing is preserved.
        thu = _ext_bars("SPY", 2026, 9, 24)
        for prev, nxt in zip(thu, thu[1:]):
            assert x_of[nxt.ts] - x_of[prev.ts] == _BAR_PERIOD
    finally:
        panel.hide()
        panel.close()


# ── D21-15-T02 / AC-D21.4.2 ───────────────────────────────────────────────────
def test_d21_15_t02_one_day_renders_unchanged(qapp) -> None:
    panel = _make_panel(qapp)
    try:
        daily = [
            Bar("SPY", "1 day", _et_ts(2026, 9, d), 1.0, 1.0, 1.0, 1.0, 1.0)
            for d in (21, 22, 23, 24, 25, 28)
        ]
        panel.set_timeframe("1 day")
        panel.set_extended_hours(True)
        panel.update_chart(daily)
        qapp.processEvents()

        assert panel._collapse_map.is_identity is True
        xs = _candle_xs(panel)
        # Identity no-op: one bar per trading day at its real timestamp.
        assert xs == [float(b.ts) for b in daily]
        assert _vol_xs(panel) == xs
        assert len(xs) == len(daily)
    finally:
        panel.hide()
        panel.close()


# ── D21-15-T03 / AC-D21.4.4 ───────────────────────────────────────────────────
def test_d21_15_t03_trading_session_hole_stays_visible(qapp) -> None:
    panel = _make_panel(qapp)
    try:
        # Tue 2026-09-22 deliberately absent -> genuine trading-session hole.
        bars = (
            _ext_bars("SPY", 2026, 9, 21)
            + _ext_bars("SPY", 2026, 9, 23)
            + _ext_bars("SPY", 2026, 9, 24)
            + _ext_bars("SPY", 2026, 9, 25)
            + _ext_bars("SPY", 2026, 9, 28)
        )
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        xs = _candle_xs(panel)
        x_of = _display_of(bars, xs)

        # The absent Tuesday keeps its full span visible (not collapsed away).
        mon_last = _et_ts(2026, 9, 21, 19, 55)
        wed_first = _et_ts(2026, 9, 23, 4, 0)
        assert x_of[wed_first] - x_of[mon_last] == wed_first - mon_last

        # The weekend gap still collapses alongside the kept hole.
        fri_last = _et_ts(2026, 9, 25, 19, 55)
        mon_first = _et_ts(2026, 9, 28, 4, 0)
        assert x_of[mon_first] - x_of[fri_last] == _BAR_PERIOD
    finally:
        panel.hide()
        panel.close()


# ── D21-15-T04 / AC-D21.4.3 ───────────────────────────────────────────────────
def test_d21_15_t04_rth_only_and_d1_bands_at_collapsed_positions(qapp) -> None:
    from services.session_service import session_bands

    panel = _make_panel(qapp)
    try:
        # Two sessions, each with a pre-market, RTH and post-market bar.
        def _b(y, m, d, h):
            return Bar("SPY", "5 mins", _et_ts(y, m, d, h), 1.0, 1.0, 1.0, 1.0, 1.0)

        bars = (
            [_b(2026, 9, 24, 5)] + _rth_bars("SPY", 2026, 9, 24) + [_b(2026, 9, 24, 18)]
            + [_b(2026, 9, 25, 5)] + _rth_bars("SPY", 2026, 9, 25) + [_b(2026, 9, 25, 18)]
        )
        rth_ts = {b.ts for b in _rth_bars("SPY", 2026, 9, 24)} | {
            b.ts for b in _rth_bars("SPY", 2026, 9, 25)
        }

        panel.set_timeframe("5 mins")

        # Ext Hours OFF (RTH): only RTH bars are plotted; non-RTH time collapses.
        panel.set_extended_hours(False)
        panel.update_chart(bars)
        qapp.processEvents()
        assert panel._collapse_map.ext_hours is False
        assert {b.ts for b in panel._plotted_bars} == rth_ts
        xs = _candle_xs(panel)
        assert len(xs) == len(rth_ts)
        assert set(round(x) for x in xs) == {
            float(panel._to_display(t)) for t in rth_ts
        }
        # No pre/post band is rendered with RTH selected.
        assert panel._session_overlay.item_count() == 0

        # Ext Hours ON: all bars plotted and the D1 pre/post bands render at the
        # collapsed display-x positions of the sessions shown.
        panel.set_extended_hours(True)
        qapp.processEvents()
        assert {b.ts for b in panel._plotted_bars} == {b.ts for b in bars}

        expected = session_bands(bars, "5 mins")
        assert expected
        regions = sorted(
            (float(a), float(b)) for a, b in
            (it.getRegion() for it in panel._session_overlay._items)
        )
        mapped = sorted(
            (
                float(panel._to_display(band["start_ts"])),
                float(panel._to_display(band["end_ts"])),
            )
            for band in expected
        )
        assert len(regions) == len(mapped)
        for got, exp in zip(regions, mapped):
            assert got[0] == pytest.approx(exp[0], abs=1e-6)
            assert got[1] == pytest.approx(exp[1], abs=1e-6)
    finally:
        panel.hide()
        panel.close()


# ── D21-15-T05 / D21.2 reconciliation ─────────────────────────────────────────
def test_d21_15_t05_volume_ceiling_uses_display_x_after_collapse(qapp) -> None:
    panel = _make_panel(qapp)
    try:
        thu = _ext_bars("SPY", 2026, 9, 24)
        fri = _ext_bars("SPY", 2026, 9, 25)
        for b in thu:
            b.volume = 1000.0
        for b in fri:
            b.volume = 1000.0
        fri[10].volume = 50000.0  # spike, visible only when Friday is in view
        bars = thu + fri

        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        cmap = panel._collapse_map
        assert cmap.is_identity is False
        pvb = panel.price_plot.getViewBox()

        # Visible display-x range = Thursday only -> ceiling 1.10 x 1000.
        thu0 = cmap.to_display(thu[0].ts)
        thu1 = cmap.to_display(thu[-1].ts)
        pvb.setRange(xRange=(thu0 - 30, thu1 + 30), padding=0)
        qapp.processEvents()
        y_range = panel.volume_plot.getViewBox().viewRange()[1]
        assert y_range[0] == pytest.approx(0.0, abs=1e-9)
        assert y_range[1] == pytest.approx(1.10 * 1000.0, rel=1e-6)

        # Visible display-x range = Friday only (spike in view) -> 1.10 x 50000.
        fri0 = cmap.to_display(fri[0].ts)
        fri1 = cmap.to_display(fri[-1].ts)
        pvb.setRange(xRange=(fri0 - 30, fri1 + 30), padding=0)
        qapp.processEvents()
        y_range = panel.volume_plot.getViewBox().viewRange()[1]
        assert y_range[1] == pytest.approx(1.10 * 50000.0, rel=1e-6)
    finally:
        panel.hide()
        panel.close()


# ===========================================================================
# D21-16 — collapse consumers: session bands, time-anchored drawings, alarm
#          label x, date axis / crosshair inverse-map (AC-D21.4.1, AC-D21.4.3)
# ===========================================================================
# These integration tests boot a real offscreen ChartPanel and assert that the
# remaining consumers of the x-model map through the *same* TimeCollapseMap as
# the candles/volume: SessionOverlay bands at display-x, time-anchored drawings
# rendered at display-x (and inverse-mapped on drag), and the alarm label at the
# display-x of the last bar.

from PyQt6.QtCore import QPointF, Qt  # noqa: E402  (test-only harness)


class _OverlayEvent:
    """Minimal stand-in exposing the fields the drawing overlay reads."""

    def __init__(self, scene_pos, finish=False, button=Qt.MouseButton.LeftButton):
        self._scene = scene_pos
        self._finish = finish
        self._button = button

    def scenePos(self):
        return self._scene

    def button(self):
        return self._button

    def isFinish(self):
        return self._finish

    def accept(self):
        pass


def _draw_event(overlay, x, y, finish=False):
    """A view-space (display-x, price) gesture event for ``overlay``."""
    return _OverlayEvent(overlay._view.mapViewToScene(QPointF(x, y)), finish=finish)


# ── D21-16-T01 / AC-D21.4.3 — SessionOverlay bands at collapsed positions ────
def test_d21_16_t01_session_bands_render_at_collapsed_positions(qapp) -> None:
    from services.session_service import session_bands

    panel = _make_panel(qapp)
    try:
        def _b(y, m, d, h, mi=0):
            return Bar("SPY", "5 mins", _et_ts(y, m, d, h, mi), 1.0, 1.0, 1.0, 1.0, 1.0)

        # Two sessions (Thu/Fri), each spanning the full extended session from
        # the 04:00 open to the 19:55 bar (covers to 20:00), so the overnight
        # gap between them is genuinely non-trading and collapses.
        bars = (
            [_b(2026, 9, 24, 4)] + _rth_bars("SPY", 2026, 9, 24) + [_b(2026, 9, 24, 19, 55)]
            + [_b(2026, 9, 25, 4)] + _rth_bars("SPY", 2026, 9, 25) + [_b(2026, 9, 25, 19, 55)]
        )
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        cmap = panel._collapse_map
        assert cmap is not None and cmap.is_identity is False

        expected = session_bands(bars, "5 mins")
        assert expected
        regions = sorted(
            (float(a), float(b)) for a, b in
            (it.getRegion() for it in panel._session_overlay._items)
        )
        mapped = sorted(
            (
                float(panel._to_display(band["start_ts"])),
                float(panel._to_display(band["end_ts"])),
            )
            for band in expected
        )
        # Every D1 pre/post band lands at the collapsed display-x of its session
        # (not at the raw timestamps).
        assert len(regions) == len(mapped)
        for got, exp in zip(regions, mapped):
            assert got[0] == pytest.approx(exp[0], abs=1e-6)
            assert got[1] == pytest.approx(exp[1], abs=1e-6)
        raw_bands = sorted(
            (float(band["start_ts"]), float(band["end_ts"])) for band in expected
        )
        assert mapped != raw_bands  # collapse really moved the bands

        # Each band stays inside the displayed bar span; none bridges the two
        # sessions across the collapsed overnight gap.
        lo = min(panel._to_display(b.ts) for b in bars)
        hi = max(panel._to_display(b.ts) for b in bars)
        thu_last = _b(2026, 9, 24, 19, 55).ts
        fri_first = _b(2026, 9, 25, 4).ts
        gap_lo, gap_hi = panel._to_display(thu_last), panel._to_display(fri_first)
        assert gap_hi - gap_lo == _BAR_PERIOD
        for a, b in regions:
            assert lo <= a <= b <= hi
            assert not (a <= gap_lo and b >= gap_hi)
        # The Friday pre band starts at the collapsed Friday session open.
        assert any(a == pytest.approx(gap_hi, abs=1e-6) for a, _b in regions)
    finally:
        panel.hide()
        panel.close()


# ── D21-16-T02 / AC-D21.4.1 — time-anchored drawing render + drag round-trip ─
def test_d21_16_t02_time_anchored_drawing_round_trips_after_collapse(qapp) -> None:
    from data.models import Drawing

    panel = _make_panel(qapp)
    try:
        thu = _ext_bars("SPY", 2026, 9, 24)
        fri = _ext_bars("SPY", 2026, 9, 25)
        mon = _ext_bars("SPY", 2026, 9, 28)
        bars = thu + fri + mon
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        ov = panel.drawing_overlay
        cmap = panel._collapse_map
        assert cmap is not None and cmap.is_identity is False

        # A drawing anchored to a Thursday bar and a Friday bar — across the
        # collapsed overnight/weekend gaps.
        p1_ts = thu[10].ts
        p2_ts = fri[10].ts
        drawing = Drawing(
            id=1, symbol="SPY", kind="trendline",
            payload={"p1": {"x": p1_ts, "y": 100.0},
                     "p2": {"x": p2_ts, "y": 110.0}},
        )
        ov.set_data("SPY", [drawing], [])
        qapp.processEvents()

        # Rendered on its original bars: item x == display-x of each anchor.
        item = ov._items[1][0]
        xs = [float(x) for x in item.getData()[0]]
        assert xs == [float(cmap.to_display(p1_ts)), float(cmap.to_display(p2_ts))]
        assert xs[1] != float(p2_ts)  # the sessions really collapsed
        # Round-trip through the overlay's own render/inverse mapping.
        for ts in (p1_ts, p2_ts):
            assert ov._x_to_ts(ov._ts_to_x(ts)) == ts

        # Drag the body by exactly one bar period of display-x inside Thursday:
        # the payload timestamps shift by one bar period (scene -> view mapping).
        updated = []
        ov.updated.connect(lambda did, payload, color: updated.append((did, payload, color)))
        press_x = ov._ts_to_x(p1_ts)
        ov.view_mouse_press(_draw_event(ov, press_x, 100.0))
        assert ov._drag is not None and ov._drag["body"] is True
        ov.view_mouse_drag(_draw_event(ov, press_x + _BAR_PERIOD, 100.0, finish=True))
        assert updated
        payload = updated[-1][1]
        assert payload["p1"]["x"] == p1_ts + _BAR_PERIOD
        assert payload["p2"]["x"] == p2_ts + _BAR_PERIOD
        # The moved anchors still round-trip through the same map.
        assert ov._x_to_ts(ov._ts_to_x(payload["p1"]["x"])) == payload["p1"]["x"]
    finally:
        panel.hide()
        panel.close()


# ── D21-16-T03 / AC-D21.4.1 — alarm label x + axis/crosshair inverse-map ─────
def test_d21_16_t03_alarm_label_and_axis_inverse_map(qapp) -> None:
    import pyqtgraph as pg

    from data.models import Alarm

    panel = _make_panel(qapp)
    try:
        bars = (
            _ext_bars("SPY", 2026, 9, 24)
            + _ext_bars("SPY", 2026, 9, 25)
            + _ext_bars("SPY", 2026, 9, 28)
        )
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_chart(bars)
        qapp.processEvents()

        cmap = panel._collapse_map
        assert cmap is not None and cmap.is_identity is False
        last_ts = bars[-1].ts
        last_dx = panel._to_display(last_ts)
        assert last_dx != last_ts  # collapse really moved the last bar

        # The alarm label x is the display-x of the last bar, not its raw ts.
        alarm = Alarm(id=1, symbol="SPY", price=100.0, direction="cross_either")
        panel.alarm_overlay.set_data([alarm])
        qapp.processEvents()
        assert panel.alarm_overlay._label_x() == pytest.approx(float(last_dx), abs=1e-6)
        _line, label = panel.alarm_overlay._items[1]
        assert float(label.pos().x()) == pytest.approx(float(last_dx), abs=1e-6)

        # The date axis inverse-maps a display-x tick back to the real ts before
        # formatting, so the label shows the wall-clock time of the bar.
        axis = panel._price_date_axis
        assert axis._collapse_map is panel._collapse_map
        spacing = 3600.0
        got = axis.tickStrings([last_dx], 1.0, spacing)
        expected = pg.DateAxisItem.tickStrings(axis, [last_ts], 1.0, spacing)
        assert got == expected

        # Crosshair time tag: display-x -> ts -> formatted label.
        assert panel._to_ts(last_dx) == last_ts
        assert panel._format_axis_time(panel._to_ts(last_dx)) == panel._format_axis_time(last_ts)
    finally:
        panel.hide()
        panel.close()


# ── D21-16-T04 / AC-D21.4.1 — D16/D1 lockstep modules consistent with D21.4 ──
def test_d21_16_t04_lockstep_modules_are_consistent_with_display_x() -> None:
    """The D16/D1 lockstep modules encode the D21.4 display-x contract.

    Zero failures in the three modules is verified by running them directly (see
    the D21-16 task log); this guard pins the *content* requirement — no
    remaining assertion compares the rendered candle/volume x to a raw
    ``Bar.ts``, and the history-backfill module checks rendered x through the
    panel's collapse map. The D16 no-silent-hole rules are otherwise unchanged.
    """
    import pathlib

    tests_dir = pathlib.Path(__file__).resolve().parent
    modules = (
        "test_session_service.py",
        "test_session_overlay.py",
        "test_history_backfill.py",
    )
    for name in modules:
        src = (tests_dir / name).read_text(encoding="utf-8")
        for line in src.splitlines():
            # A rendered-x assertion (candle_ts / vol_x) must never compare to a
            # raw Bar.ts; it must go through the panel's display-x map.
            if "candle_ts" in line or "vol_x" in line:
                assert "b.ts for b in" not in line, (
                    f"{name} still asserts rendered x == raw Bar.ts: {line.strip()!r}"
                )
    hb = (tests_dir / "test_history_backfill.py").read_text(encoding="utf-8")
    # The lockstep update checks rendered x through the display-x map.
    assert "_to_display" in hb
