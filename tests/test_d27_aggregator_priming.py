"""D27.9 — aggregator priming.

On chart load the fresh BarAggregator SHALL be primed with recent history
before the live feed attaches, so the forming candle's OHLCV is not
fabricated from the first live tick.

AC-D27.9 (revised 2026-10-16 by D43/ESC-036): fresh load mid-period -> the
forming candle's open/volume reflect the primed history, not just the first
live tick. The priming bar size follows the elapsed forming-period span: the
fine timeframes (1 min / 5 mins / 15 mins / 1 hour) prime with 5-second bars
and a duration in [60 S, 3600 S]; the coarse timeframes ('4 hours' / '1 day')
prime with 1-minute bars and a duration in [60 S, 1 D].
"""

from __future__ import annotations

import itertools

from ibkr.client import IBApiClient


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


class _FakeHistBar:
    """Minimal ibapi historical-bar stand-in (formatDate=2 -> epoch string)."""

    def __init__(self, ts, o, h, l, c, v):
        self.date = str(ts)
        self.open = o
        self.high = h
        self.low = l
        self.close = c
        self.volume = v


def test_d27_9_prime_before_live_feed(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    counter = iter(range(9100, 9300))
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = iter(range(9300, 9400))
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    # Mid-period load: 5-min timeframe, now 200s into the current period.
    now = 1_760_000_000
    win._now_ts = lambda: now
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()
    qapp.processEvents()

    # A priming request was issued; the live feed is NOT attached yet.
    assert win._prime_req_id is not None
    assert win._rt_req_id is None
    prime_calls = [c for c in calls if c.get("bar_size") == "5 secs"]
    assert len(prime_calls) == 1, f"expected one 5-sec priming request: {calls}"

    # Two 5-sec priming bars inside the current period arrive, then end.
    ps = win._aggregator.period_start(now)
    assert now - ps == 200
    t1, t2 = ps + 5, ps + 10
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(t1, 100.0, 100.5, 99.5, 100.2, 50.0)
    )
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(t2, 100.2, 101.0, 100.0, 100.8, 70.0)
    )
    win._on_historical_data_end(win._prime_req_id)
    qapp.processEvents()

    # The live feed attaches only after priming completes...
    assert win._rt_req_id is not None
    # ...and the forming candle reflects primed history, not thin air.
    forming = win._aggregator.current_bar()
    assert forming is not None
    assert forming.ts == ps
    assert forming.open == 100.0
    assert forming.high == 101.0
    assert forming.low == 99.5
    assert forming.close == 100.8
    assert forming.volume == 120.0
    win.close()


def test_d27_9_prime_failure_fails_open(monkeypatch, qapp):
    """A failed priming request must not strand the chart: the live feed
    still attaches (with an unprimed aggregator) rather than never."""
    win = _make_window(monkeypatch, qapp)
    counter = iter(range(9100, 9300))
    monkeypatch.setattr(
        win.md_manager, "req_historical_data", lambda **k: next(counter)
    )
    rt_ids = iter(range(9300, 9400))
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    win._now_ts = lambda: 1_760_000_000
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()
    qapp.processEvents()

    assert win._prime_req_id is not None
    assert win._rt_req_id is None

    # Priming errors out -> live feed attaches anyway.
    win._on_error(win._prime_req_id, 162, "pacing violation")
    qapp.processEvents()
    assert win._prime_req_id is None
    assert win._rt_req_id is not None
    win.close()


def test_d27_9_no_prime_at_period_boundary(monkeypatch, qapp):
    """Loading exactly at a period boundary needs no priming: the live feed
    attaches immediately."""
    win = _make_window(monkeypatch, qapp)
    counter = iter(range(9100, 9300))
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = iter(range(9300, 9400))
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    # now sits exactly on a 5-min boundary -> nothing to prime.
    win._now_ts = lambda: 1_759_999_800
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()
    qapp.processEvents()

    assert win._prime_req_id is None
    assert not any(c.get("bar_size") == "5 secs" for c in calls)
    assert win._rt_req_id is not None
    win.close()


def _prime_duration_seconds(call) -> int:
    """Parse the seconds out of an IBKR duration string like ``'60 S'``."""
    return int(call["duration"].split()[0])


def test_d27_9_prime_span_bounded(monkeypatch, qapp):
    """P2-T35-T21 / AC2 — corrected, not weakened.

    The superseded assertion enshrined the invalid ``'5 secs'``/``'7200 S'``
    shape for a '1 day' load (IBKR error 321). D43/ESC-036 supersedes it: a
    coarse load past the first hour primes with ``'1 min'`` bars and a
    duration inside IBKR's accepted ``[60 S, 1 D]`` window. The fine-timeframe
    ``'5 secs'`` / ``[60 S, 3600 S]`` shape is asserted by
    ``test_d27_9_prime_duration_in_accepted_range``.
    """
    assert "trailing 5-sec history" not in (__doc__ or ""), (
        "module docstring still states the superseded 'trailing 5-sec history'"
    )
    win = _make_window(monkeypatch, qapp)
    counter = itertools.count(9100)
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = itertools.count(9300)
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    # '1 day' load, several hours into the period: the span exceeds the
    # '5 secs' 3600 S ceiling, so the coarse branch must be taken.
    now = 1_759_989_600
    win._now_ts = lambda: now
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("1 day")
    win.load_chart()
    qapp.processEvents()

    prime_calls = [c for c in calls if c.get("bar_size") == "1 min"]
    assert len(prime_calls) == 1, f"expected one 1-min priming request: {calls}"
    assert not any(c.get("bar_size") == "5 secs" for c in calls), (
        f"'1 day' load issued a superseded 5-sec request: {calls}"
    )
    span = now - win._aggregator.period_start(now)
    assert span > 3600, "test setup: span must exceed the 5-sec 3600 S ceiling"
    duration_s = _prime_duration_seconds(prime_calls[0])
    assert duration_s == max(60, min(span, 86400)), (
        f"coarse clamp not applied: {prime_calls[0]['duration']!r} vs span {span}"
    )
    assert 60 <= duration_s <= 86400, (
        f"duration {prime_calls[0]['duration']!r} outside [60 S, 1 D]"
    )
    win.close()


def test_d27_9_coarse_prime_uses_one_min_bars(monkeypatch, qapp):
    """P2-T35-T11 / AC1 — the coarse timeframes ('4 hours'/'1 day') prime
    with ``'1 min'`` bars (never ``'5 secs'``) and a duration inside IBKR's
    accepted ``[60 S, 1 D]`` window.
    """
    now = 1_759_989_600  # 02:00 ET: both coarse spans exceed 3600 s
    for timeframe in ("4 hours", "1 day"):
        win = _make_window(monkeypatch, qapp)
        counter = itertools.count(9100)
        calls = []

        def fake_req_hist(**k):
            calls.append(k)
            return next(counter)

        monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
        rt_ids = itertools.count(9300)
        monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

        win._now_ts = lambda: now
        win.symbol_input.setText("TEST")
        win.tf_combo.setCurrentText(timeframe)
        win.load_chart()
        qapp.processEvents()

        span = now - win._aggregator.period_start(now)
        assert span > 3600, (
            f"{timeframe}: test setup, span {span} must exceed the 3600 S ceiling"
        )
        prime_calls = [c for c in calls if c.get("bar_size") == "1 min"]
        assert len(prime_calls) == 1, (
            f"{timeframe}: expected one '1 min' priming request: {calls}"
        )
        assert not any(c.get("bar_size") == "5 secs" for c in calls), (
            f"{timeframe}: coarse load issued a '5 secs' request: {calls}"
        )
        duration_s = _prime_duration_seconds(prime_calls[0])
        assert 60 <= duration_s <= 86400, (
            f"{timeframe}: duration {prime_calls[0]['duration']!r} outside [60 S, 1 D]"
        )
        assert duration_s == max(60, min(span, 86400)), (
            f"{timeframe}: {prime_calls[0]['duration']!r} != clamped span {span} S"
        )
        win.close()


def test_d27_9_coarse_prime_no_fabricated_previous_period_candle(
    monkeypatch, qapp
):
    """P2-T35-T31 / AC3 — a '1 min' prime can return a bar whose ts precedes
    the current period's start (the [60 S, 1 D] floor at a coarse boundary);
    replaying it must not open (and emit) a fabricated previous-period candle.
    """
    win = _make_window(monkeypatch, qapp)
    counter = itertools.count(9100)
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = itertools.count(9300)
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    # Mid-period '4 hours' load (span 7200 s): the coarse branch issues the
    # '1 min' prime.
    now = 1_759_989_600
    win._now_ts = lambda: now
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("4 hours")
    win.load_chart()
    qapp.processEvents()

    prime_calls = [c for c in calls if c.get("bar_size") == "1 min"]
    assert len(prime_calls) == 1, f"expected one 1-min priming request: {calls}"
    assert win._prime_req_id is not None
    assert win._rt_req_id is None

    agg = win._aggregator
    ps = agg.period_start(now)
    assert now - ps > 3600
    session = win._primary_session
    emitted = []
    session.bar_updated.connect(
        lambda bar, is_new: emitted.append((bar, is_new))
    )

    # A pre-period 1-min bar (the clamp's floor padding) arrives first, then
    # the in-period primed history.
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps - 60, 90.0, 91.0, 89.0, 90.5, 10.0)
    )
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps + 60, 100.0, 100.5, 99.5, 100.2, 50.0)
    )
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps + 120, 100.2, 101.0, 100.0, 100.8, 70.0)
    )
    win._on_historical_data_end(win._prime_req_id)
    qapp.processEvents()

    # No completed candle for the earlier period was fabricated.
    fabricated = [(bar.ts, is_new) for bar, is_new in emitted if is_new and bar.ts < ps]
    assert not fabricated, f"fabricated previous-period candle(s): {fabricated}"

    # The forming candle is the CURRENT period's and reflects the in-period
    # primed history only (the pre-period bar's 90.x prices are absent).
    forming = agg.current_bar()
    assert forming is not None
    assert forming.ts == ps
    assert forming.open == 100.0
    assert forming.high == 101.0
    assert forming.low == 99.5
    assert forming.close == 100.8
    assert forming.volume == 120.0
    # The live feed attaches only after priming completes (unchanged).
    assert win._rt_req_id is not None
    win.close()


def test_d27_9_prime_duration_in_accepted_range(monkeypatch, qapp):
    """P2-T30-T11 / AC1 — every fine-timeframe ``'5 secs'`` priming request
    asks for a duration inside IBKR's accepted ``[60 S, 3600 S]`` window,
    including the first-minute case that exercises the 60 S floor.
    """
    # (timeframe, now) — the first-minute case has span < 60 s (the floor).
    cases = [
        ("1 min", 1_760_000_010),    # span 30 s   -> floor 60 S
        ("5 mins", 1_760_000_000),   # span 200 s
        ("15 mins", 1_760_000_000),  # span 500 s
        ("1 hour", 1_760_000_000),   # span 3200 s
    ]
    for timeframe, now in cases:
        win = _make_window(monkeypatch, qapp)
        counter = itertools.count(9100)
        calls = []

        def fake_req_hist(**k):
            calls.append(k)
            return next(counter)

        monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
        rt_ids = itertools.count(9300)
        monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

        win._now_ts = lambda: now
        win.symbol_input.setText("TEST")
        win.tf_combo.setCurrentText(timeframe)
        win.load_chart()
        qapp.processEvents()

        prime_calls = [c for c in calls if c.get("bar_size") == "5 secs"]
        assert prime_calls, f"{timeframe}: no 5-sec priming request issued"
        span = now - win._aggregator.period_start(now)
        expected = max(60, min(span, 3600))
        for call in prime_calls:
            duration_s = _prime_duration_seconds(call)
            assert 60 <= duration_s <= 3600, (
                f"{timeframe}: duration {call['duration']!r} outside [60 S, 3600 S]"
            )
            assert duration_s == expected, (
                f"{timeframe}: {call['duration']!r} != clamped span {expected} S"
            )
        win.close()


def test_d27_9_no_fabricated_previous_period_candle(monkeypatch, qapp):
    """P2-T30-T21 / AC2 — the clamped request can return 5-sec bars whose ts
    precedes the current period's start; replaying them must not open (and
    emit) a fabricated partial previous-period candle.
    """
    win = _make_window(monkeypatch, qapp)
    counter = itertools.count(9100)
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = itertools.count(9300)
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    now = 1_760_000_000
    win._now_ts = lambda: now
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("5 mins")
    win.load_chart()
    qapp.processEvents()

    assert win._prime_req_id is not None
    assert win._rt_req_id is None

    agg = win._aggregator
    ps = agg.period_start(now)
    session = win._primary_session
    emitted = []
    session.bar_updated.connect(
        lambda bar, is_new: emitted.append((bar, is_new))
    )

    # A pre-period bar (the clamp's padding) arrives first, then the in-period
    # primed history.
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps - 5, 90.0, 91.0, 89.0, 90.5, 10.0)
    )
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps + 5, 100.0, 100.5, 99.5, 100.2, 50.0)
    )
    win._on_historical_bar(
        win._prime_req_id, _FakeHistBar(ps + 10, 100.2, 101.0, 100.0, 100.8, 70.0)
    )
    win._on_historical_data_end(win._prime_req_id)
    qapp.processEvents()

    # No completed candle for the earlier period was fabricated.
    fabricated = [(bar.ts, is_new) for bar, is_new in emitted if is_new and bar.ts < ps]
    assert not fabricated, f"fabricated previous-period candle(s): {fabricated}"

    # The forming candle is the CURRENT period's and reflects the in-period
    # primed history only (the pre-period bar's 90.x prices are absent).
    forming = agg.current_bar()
    assert forming is not None
    assert forming.ts == ps
    assert forming.open == 100.0
    assert forming.high == 101.0
    assert forming.low == 99.5
    assert forming.close == 100.8
    assert forming.volume == 120.0
    # The live feed attaches only after priming completes (unchanged).
    assert win._rt_req_id is not None
    win.close()
