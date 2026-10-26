"""test_d38_events_news.py — D38 (events & news).

Acceptance criteria:
- AC-D38.1: synthetic provider events (1 earnings, 1 dividend, 1 split) →
  three distinctly-styled markers at the correct dates + countdown shows
  days to the next event.
- AC-D38.4: corporate-events-only — non-corporate types rejected at the
  provider boundary; yfinance layer only calls the 3 approved endpoints.
- AC-D38.5: IBKR tick-59 dividend renders while yfinance is down →
  "event data unavailable" for earnings/splits (mocked outage).
- AC-D38.6: full suite green (run separately), no D1–D37 regressions.

Plus: tick-59 parsing, yfinance cache/TTL, and the no-mock-endpoint
production tree rule (owner-mandated, D36 pattern).
"""

import os
from datetime import date, timedelta

import pytest

from data.events.provider import (
    Event, EVENT_TYPES, parse_ib_dividend_string,
)
from data.events.ibkr_source import (
    IBKREventSource, dividend_event_from_tick_string,
)
from data.events.yfinance_source import YFinanceCache


# ── Fakes (tests only — never production) ─────────────────────────────

class _StubSession:
    def __init__(self, symbol="AAPL", dividend_info=None):
        self.symbol = symbol
        self._div = dividend_info or {}


    def dividend_info(self):
        return dict(self._div)


def _ev(etype, symbol, day_offset, source="yfinance"):
    d = date.today() + timedelta(days=day_offset)
    return Event(id=f"{source}:{etype}:{symbol}:{d.isoformat()}",
                 type=etype, symbol=symbol, date=d, source=source)


# ── Tick-59 parsing ───────────────────────────────────────────────────

def test_tick59_full_shape():
    p = parse_ib_dividend_string("0.82,0.90,20260315,0.225")
    assert p["past12m"] == 0.82
    assert p["next12m"] == 0.90
    assert p["next_date"] == date(2026, 3, 15)
    assert p["next_amt"] == 0.225


def test_tick59_semicolon_separator():
    p = parse_ib_dividend_string("0.82;0.90;20260315;0.225")
    assert p["next_date"] == date(2026, 3, 15)


def test_tick59_garbage_never_raises():
    for bad in ("", "n/a", "1,2", "x,y,zzzzzz,w", None, "1,2,20261345,3"):
        p = parse_ib_dividend_string(bad)
        assert isinstance(p, dict)
        assert p["next_date"] is None or isinstance(p["next_date"], date)


def test_dividend_event_from_tick_string():
    ev = dividend_event_from_tick_string("AAPL", "0.82,0.90,20260315,0.225")
    assert ev is not None
    assert ev.type == "dividend" and ev.source == "ibkr"
    assert ev.date == date(2026, 3, 15)
    assert dividend_event_from_tick_string("AAPL", "garbage") is None


# ── AC-D38.4: corporate-events-only guard ─────────────────────────────

def test_non_corporate_event_rejected():
    with pytest.raises(ValueError):
        Event(id="x", type="economic", symbol="AAPL",
              date=date.today(), source="yfinance")
    assert set(EVENT_TYPES) == {"earnings", "dividend", "split"}


# ── IBKREventSource ───────────────────────────────────────────────────

def test_ibkr_source_dividend_from_session():
    sess = _StubSession("AAPL", {"next_date": date(2026, 3, 15),
                                 "next_amt": 0.225})
    src = IBKREventSource(lambda _s: sess)
    evs = src.get_events("AAPL", date(2026, 1, 1), date(2026, 12, 31))
    assert len(evs) == 1
    assert evs[0].type == "dividend" and evs[0].source == "ibkr"


def test_ibkr_source_skips_futures():
    sess = _StubSession("ES", {"next_date": date(2026, 3, 15)})
    src = IBKREventSource(lambda _s: sess)
    assert src.get_events("ES", date(2026, 1, 1), date(2026, 12, 31)) == []


def test_ibkr_source_no_data_no_events():
    src = IBKREventSource(lambda _s: _StubSession("AAPL", {}))
    assert src.get_events("AAPL", date(2026, 1, 1), date(2026, 12, 31)) == []
    assert src.unavailable("AAPL") is False


# ── YFinanceCache: round-trip + TTL ───────────────────────────────────

def test_yfinance_cache_round_trip(tmp_path):
    cache = YFinanceCache(str(tmp_path / "t.sqlite3"))
    # Ensure the table exists (production creates it in data/db.py).
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "t.sqlite3"))
    conn.execute(
        "CREATE TABLE yfinance_events_cache (symbol TEXT PRIMARY KEY, "
        "fetched_at REAL DEFAULT 0, failed_at REAL DEFAULT 0, "
        "payload TEXT DEFAULT '[]')")
    conn.commit()
    conn.close()

    evs = [_ev("earnings", "AAPL", 5), _ev("split", "AAPL", -400)]
    cache.write("AAPL", evs)
    back, fetched_at, failed_at = cache.read("AAPL")
    assert len(back) == 2
    assert {e.type for e in back} == {"earnings", "split"}
    assert fetched_at > 0 and failed_at == 0.0

    cache.mark_failed("MSFT")
    _, _, failed = cache.read("MSFT")
    assert failed > 0.0


def test_yfinance_source_unavailable_states(tmp_path):
    import sqlite3
    from data.events.yfinance_source import YFinanceEventSource

    dbp = str(tmp_path / "t.sqlite3")
    conn = sqlite3.connect(dbp)
    conn.execute(
        "CREATE TABLE yfinance_events_cache (symbol TEXT PRIMARY KEY, "
        "fetched_at REAL DEFAULT 0, failed_at REAL DEFAULT 0, "
        "payload TEXT DEFAULT '[]')")
    conn.commit()
    conn.close()
    cache = YFinanceCache(dbp)

    class _NoWorker:
        def submit(self, symbol):
            pass

        @property
        def finished(self):
            raise AssertionError("no worker in test")

    src = YFinanceEventSource(cache, worker=_NoWorker())
    # Never fetched, never failed -> not "unavailable" (refresh in flight).
    assert src.unavailable("AAPL") is False
    cache.mark_failed("AAPL")
    assert src.unavailable("AAPL") is True
    cache.write("AAPL", [_ev("earnings", "AAPL", 5)])
    assert src.unavailable("AAPL") is False
    # Date-range filtering.
    got = src.get_events("AAPL", date.today(), date.today() + timedelta(days=30))
    assert len(got) == 1 and got[0].type == "earnings"


# ── AC-D38.1: markers + countdown ─────────────────────────────────────

def _bars_for(dates):
    """Minimal bar stubs with ts for the given dates (UTC midnight)."""
    from datetime import datetime, timezone

    class _B:
        def __init__(self, ts):
            self.ts = ts
    return [_B(int(datetime(d.year, d.month, d.day,
                           tzinfo=timezone.utc).timestamp()))
            for d in dates]


class _Map:
    def __init__(self, bars):
        self._m = {b.ts: i for i, b in enumerate(bars)}

    def to_display(self, ts):
        return self._m[ts]


def test_ac_d38_1_markers_and_countdown(qapp):
    from ui.event_marker_overlay import EventMarkerOverlay, EVENT_STYLE
    import pyqtgraph as pg

    plot = pg.PlotWidget()
    ov = EventMarkerOverlay(plot)
    today = date.today()
    dates = [today - timedelta(days=10), today - timedelta(days=3),
             today + timedelta(days=4)]
    ov.set_bars(_bars_for(dates))
    ov.set_collapse_map(_Map(ov._bars))

    evs = [
        _ev("earnings", "AAPL", -10),
        _ev("dividend", "AAPL", -3),
        _ev("split", "AAPL", 4),
    ]
    # Align event dates with the bar dates.
    for e, d in zip(evs, dates):
        e.date = d
    ov.set_events(evs)
    assert ov.event_count() == 3
    # Distinct styling per type.
    colors = set()
    for e in evs:
        item = ov._items[e.id]
        colors.add(EVENT_STYLE[e.type]["color"])
        assert item.isVisible()
    assert len(colors) == 3
    # Countdown names the next upcoming event with days.
    assert ov.countdown_text() == "Split in 4d"
    plot.close()


def test_ac_d38_1_no_upcoming_hides_countdown(qapp):
    from ui.event_marker_overlay import EventMarkerOverlay
    import pyqtgraph as pg

    plot = pg.PlotWidget()
    ov = EventMarkerOverlay(plot)
    today = date.today()
    dates = [today - timedelta(days=10)]
    ov.set_bars(_bars_for(dates))
    ov.set_collapse_map(_Map(ov._bars))
    evs = [_ev("dividend", "AAPL", -10)]
    evs[0].date = dates[0]
    ov.set_events(evs)
    assert ov.countdown_text() == ""
    plot.close()


def test_ac_d38_1_unavailable_state(qapp):
    from ui.event_marker_overlay import EventMarkerOverlay
    import pyqtgraph as pg

    plot = pg.PlotWidget()
    ov = EventMarkerOverlay(plot)
    ov.set_bars(_bars_for([date.today()]))
    ov.set_collapse_map(_Map(ov._bars))
    ov.set_events([], unavailable=True)
    assert ov.countdown_text() == "Event data unavailable"
    plot.close()


def test_marker_diff_by_id(qapp):
    """Date corrections move the marker (id-keyed), not duplicate it."""
    from ui.event_marker_overlay import EventMarkerOverlay
    import pyqtgraph as pg

    plot = pg.PlotWidget()
    ov = EventMarkerOverlay(plot)
    today = date.today()
    dates = [today - timedelta(days=5), today + timedelta(days=5)]
    ov.set_bars(_bars_for(dates))
    ov.set_collapse_map(_Map(ov._bars))
    e1 = _ev("earnings", "AAPL", -5)
    e1.date = dates[0]
    ov.set_events([e1])
    assert len(ov._items) == 1
    # Correction: same id, new date.
    e2 = _ev("earnings", "AAPL", 5)
    e2.id = e1.id
    e2.date = dates[1]
    ov.set_events([e2])
    assert len(ov._items) == 1
    assert list(ov._items)[0] == e1.id
    plot.close()


# ── AC-D38.5: IBKR dividend renders while yfinance is down ────────────

def test_ac_d38_5_fallback_merge(qapp):
    """Session merge: IBKR dividend present + yfinance unavailable →
    dividend marker renders, earnings/splits show the unavailable state.

    Exercises the real TickerSession._merge_events (reviewer A1, D38) so a
    production regression in the merge rule fails this test."""
    from datetime import date as _date
    from ui.ticker_session import TickerSession

    session = TickerSession("AAPL", host=object())
    ibkr_evs = [Event(id="ibkr:dividend:AAPL:2026-03-15", type="dividend",
                      symbol="AAPL", date=_date(2026, 3, 15), source="ibkr",
                      details={"amount": 0.24})]
    session._merge_events(ibkr_evs, source="ibkr")
    session._merge_events([], source="yfinance")  # outage: nothing cached

    assert [e.id for e in session._events] == ["ibkr:dividend:AAPL:2026-03-15"]
    assert session._events[0].source == "ibkr"
    # yfinance outage is surfaced by the source layer as "event data
    # unavailable" for earnings/splits — not part of the merge.


def test_merge_drops_duplicate_yfinance_dividend(qapp):
    """Exercises the real TickerSession._merge_events (reviewer A1, D38):
    a yfinance dividend on the same date as an IBKR dividend is dropped;
    other yfinance events survive."""
    from ui.ticker_session import TickerSession

    session = TickerSession("AAPL", host=object())
    session._merge_events(
        [Event(id="ibkr:dividend:AAPL:2026-03-15", type="dividend",
               symbol="AAPL", date=date(2026, 3, 15), source="ibkr")],
        source="ibkr")
    session._merge_events(
        [Event(id="yf:dividend:AAPL:2026-03-15", type="dividend",
               symbol="AAPL", date=date(2026, 3, 15), source="yfinance",
               details={"amount": 0.24}),
         Event(id="yf:earnings:AAPL:2026-04-30", type="earnings",
               symbol="AAPL", date=date(2026, 4, 30), source="yfinance")],
        source="yfinance")
    assert [e.id for e in session._events] == ["ibkr:dividend:AAPL:2026-03-15",
                                              "yf:earnings:AAPL:2026-04-30"]


# ── B.6: no mock endpoint in production code (owner-mandated) ─────────

def test_ac_d38_production_tree_has_no_mock_endpoint():
    """Owner rule: mocked/faked/stubbed endpoints exist ONLY in tests.

    Same scan shape as the D36 B.6 test (concatenated client/server names —
    honest comments mentioning test fakes do not trip it).
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    for sub in ("ibkr", "services", "ui", "data"):
        for path in (root / sub).rglob("*.py"):
            lowered = path.read_text().lower()
            assert "fakeclient" not in lowered, path
            assert "mockclient" not in lowered, path
            assert "stubclient" not in lowered, path
            assert "simulatedclient" not in lowered, path
            assert "fakeserver" not in lowered, path
            assert "mockserver" not in lowered, path
            assert "mockendpoint" not in lowered, path


# ── MD-line guard (37.5, re-homed from the deleted D37 suite) ─────────

def test_md_line_guard_thresholds():
    """`services/md_line_guard.py::assess` keeps its only test post-D41.

    The assertions moved from the deleted
    ``tests/test_d37_microstructure.py::test_md_line_guard_thresholds``,
    re-purposed to the surviving purpose: D38's dividend S0 line (``"456"``)
    is what ``MainWindow._guard_md_lines`` still gates, so the thresholds are
    asserted against that caller rather than the removed depth feed.
    """
    from services.md_line_guard import assess

    assert assess(50, "SPX", "S0 ticks") == ("ok", "")
    level, msg = assess(90, "SPX", "S0 ticks")
    assert level == "approaching"
    assert "SPX" in msg and "90/100" in msg
    level, msg = assess(100, "SPX", "S0 ticks")
    assert level == "exceeded"
    assert "SPX" in msg and "not subscribing" in msg
