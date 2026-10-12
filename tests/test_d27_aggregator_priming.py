"""D27.9 — aggregator priming.

On chart load the fresh BarAggregator SHALL be primed with trailing 5-sec
history before the live feed attaches, so the forming candle's OHLCV is not
fabricated from the first live tick.

AC-D27.9: fresh load mid-period -> forming candle's open/volume reflect the
primed 5-sec history, not just the first live tick.
"""

from __future__ import annotations

from ibkr.client import IBApiClient


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)
    monkeypatch.setattr(
        pacing_mod.pacing_manager, "throttle_realtime", lambda: None
    )
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


def test_d27_9_prime_span_bounded(monkeypatch, qapp):
    """The trailing priming fetch is bounded: a daily load must not pull a
    full day of 5-sec bars (pacing)."""
    win = _make_window(monkeypatch, qapp)
    counter = iter(range(9100, 9300))
    calls = []

    def fake_req_hist(**k):
        calls.append(k)
        return next(counter)

    monkeypatch.setattr(win.md_manager, "req_historical_data", fake_req_hist)
    rt_ids = iter(range(9300, 9400))
    monkeypatch.setattr(win.rt_manager, "subscribe", lambda s, c: next(rt_ids))

    now = 1_760_000_000
    win._now_ts = lambda: now
    win.symbol_input.setText("TEST")
    win.tf_combo.setCurrentText("1 day")
    win.load_chart()
    qapp.processEvents()

    prime_calls = [c for c in calls if c.get("bar_size") == "5 secs"]
    assert len(prime_calls) == 1
    span = now - win._aggregator.period_start(now)
    assert span > 7_200, "test setup: period must exceed the cap"
    assert prime_calls[0]["duration"] == "7200 S"
    win.close()
