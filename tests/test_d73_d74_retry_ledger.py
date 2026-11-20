"""P26-T3 — D73 + D74: one chunk-surrender rule, one generation-scoped ledger.

Offscreen, clock-controlled waves driven directly on a live ``TickerSession``
with a stub transport (the D56 harness shape). Both retry paths — error 162
and trailing silence — are asserted through the SAME post-condition helper, so
the two fixtures cannot drift.

No test here weakens, skips or rewrites an existing test.
"""

from __future__ import annotations

import logging

from collections import namedtuple

from data.bar_cache import BarCache

Plan = namedtuple("Plan", ["endDateTime", "bar_size", "duration"])

TF = "5 mins"
BASE_TS = 1_700_000_000
_STEP = 300

# Two hundred waves in one session is the D74.1 fixture: a ledger that grows
# with the wave count fails it long before two hundred.
_MANY_WAVES = 200


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))  # 10-digit epoch string -> parse_ibkr_date
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _ReqStub:
    """``req_historical_data`` / ``cancel_historical_data`` double.

    ``req`` behaves like the transport (fresh reqId, recorded call); a test
    then feeds a chosen bar set for that reqId through :func:`_feed`, which
    drives the real ``on_historical_bar`` ingress.
    """

    def __init__(self, first_id: int = 7000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None):
        req_id = self._next
        self._next += 1
        self.calls.append({
            "reqId": req_id,
            "contract": contract,
            "timeframe": timeframe,
            "endDateTime": endDateTime,
            "whatToShow": whatToShow,
            "useRTH": useRTH,
            "extended_hours": extended_hours,
            "bar_size": bar_size,
            "duration": duration,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _make_session(monkeypatch, qapp, symbol: str):
    """A live ``TickerSession`` on a shown ``MainWindow`` with stub transport."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()

    stub = _ReqStub()
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel

    session = win.get_or_create_session(symbol)
    # Clock control: replace the monotonic seam BEFORE the wave issues.
    clock = {"t": 5000.0}
    session._silence_now = lambda: clock["t"]
    return win, session, stub, clock


def _plan(end: str) -> Plan:
    return Plan(endDateTime=end, bar_size="5 mins", duration="5 D")


def _issue(session, stub, plans) -> list[int]:
    session.queue_wave_plans(list(plans), None, TF, False)
    return [c["reqId"] for c in stub.calls]


def _feed(session, req_id: int, timestamps) -> None:
    """Deliver one chosen bar set for ``req_id`` through the real ingress."""
    for ts in timestamps:
        session.on_historical_bar(req_id, _FakeIbBar(ts))


def _spy_surrender(monkeypatch, session) -> list[int]:
    """Record each ``_surrender_chunk_bars`` call (one helper, two callers)."""
    calls: list[int] = []
    original = session._surrender_chunk_bars

    def spy(req_id: int) -> None:
        calls.append(req_id)
        original(req_id)

    monkeypatch.setattr(session, "_surrender_chunk_bars", spy)
    return calls


def _key(bar) -> tuple:
    return (bar.symbol, bar.timeframe, bar.ts)


def _assert_no_duplicate_chunk_state(
    session, timeframe: str, expected_rows: int
) -> None:
    """THE shared post-condition of a surrendered-then-retried chunk.

    Every timestamp in the in-memory wave record appears exactly once
    (``_pending_bars`` holds at most one bar per ``(symbol, timeframe, ts)``),
    the mode-aware cache holds no duplicated row, and its row count equals
    the number of distinct timestamps the wave actually kept. Called by the
    162 path's case and the silence path's case alike — one helper, one
    expectation, no second wording.
    """
    pending = [_key(b) for b in session._pending_bars]
    assert len(pending) == len(set(pending)), pending
    rows = BarCache.get_bars(
        session.symbol, timeframe, ext_hours=session._wave_extended_hours
    )
    row_keys = [_key(b) for b in rows]
    assert len(row_keys) == len(set(row_keys)), row_keys
    assert len(rows) == expected_rows, row_keys


# ---------------------------------------------------------------------------
# AC-D73.1 — a 162 chunk surrenders its partial bars before the retry
# ---------------------------------------------------------------------------
def test_ac_d73_1_retry_after_162_keeps_one_bar_per_timestamp(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T73A")
    try:
        surrendered = _spy_surrender(monkeypatch, session)
        plan = _plan("20260105-20:00:00")
        (first,) = _issue(session, stub, [plan])

        first_bars = [BASE_TS + _STEP * i for i in range(5)]
        _feed(session, first, first_bars)
        assert len(session._pending_bars) == 5

        session.on_historical_error(first, 162, "pacing violation")

        # The failed attempt left no trace: buffer popped, rows gone by id().
        assert surrendered == [first]
        assert session._pending_bars == []
        assert first not in session._req_bars
        assert plan in session._retried_plans

        # The retry redelivers the same five plus five more.
        session._on_wave_continue_timeout()
        assert len(stub.calls) == 2
        second = stub.calls[1]["reqId"]
        assert second != first
        retry_bars = [BASE_TS + _STEP * i for i in range(10)]
        _feed(session, second, retry_bars)
        session.on_historical_data_end(second)

        # Ten distinct timestamps: ten rows, no duplicates anywhere.
        _assert_no_duplicate_chunk_state(session, TF, 10)
    finally:
        win.close()


def test_ac_d73_1_retry_refused_twice_finalises_short_no_duplicates(
    monkeypatch, qapp
):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T73B")
    try:
        surrendered = _spy_surrender(monkeypatch, session)
        plan = _plan("20260105-20:00:00")
        (first,) = _issue(session, stub, [plan])

        first_bars = [BASE_TS + _STEP * i for i in range(5)]
        _feed(session, first, first_bars)
        session.on_historical_error(first, 162, "pacing violation")

        session._on_wave_continue_timeout()
        second = stub.calls[1]["reqId"]
        _feed(session, second, first_bars)
        # The plan is already in the shared allowance: no third issue, the
        # wave finalises short with the partial bars surrendered.
        session.on_historical_error(second, 162, "pacing violation")

        assert surrendered == [first, second]
        assert len(stub.calls) == 2
        assert session._backfill_failed_req_ids == {second}
        assert session._pending_bars == []
        # Nothing was ever completed, so nothing was persisted — the short
        # wave keeps zero rows and zero duplicated timestamps.
        _assert_no_duplicate_chunk_state(session, TF, 0)
    finally:
        win.close()


def test_ac_d73_1_162_with_zero_partial_bars_is_a_noop(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T73C")
    try:
        plan = _plan("20260105-20:00:00")
        (first,) = _issue(session, stub, [plan])

        # No bars at all before the 162: the surrender is a no-op.
        session.on_historical_error(first, 162, "pacing violation")
        assert session._pending_bars == []
        assert first not in session._req_bars

        session._on_wave_continue_timeout()
        second = stub.calls[1]["reqId"]
        bars = [BASE_TS + _STEP * i for i in range(5)]
        _feed(session, second, bars)
        session.on_historical_data_end(second)

        _assert_no_duplicate_chunk_state(session, TF, 5)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC-D73.2 — the silence path satisfies the identical post-condition
# ---------------------------------------------------------------------------
def test_ac_d73_2_silence_retry_keeps_one_bar_per_timestamp(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T73D")
    try:
        surrendered = _spy_surrender(monkeypatch, session)
        plan = _plan("20260105-20:00:00")
        (first,) = _issue(session, stub, [plan])

        first_bars = [BASE_TS + _STEP * i for i in range(5)]
        _feed(session, first, first_bars)
        assert len(session._pending_bars) == 5

        # Trailing silence past the shape bound: cancel + re-issue once.
        clock["t"] += 31.0
        session._sweep_silent_chunks()

        # Same helper, same effect as the 162 path.
        assert surrendered == [first]
        assert session._pending_bars == []
        assert first not in session._req_bars

        second = stub.calls[1]["reqId"]
        retry_bars = [BASE_TS + _STEP * i for i in range(10)]
        _feed(session, second, retry_bars)
        session.on_historical_data_end(second)

        # The very same helper and expectation the 162 case uses.
        _assert_no_duplicate_chunk_state(session, TF, 10)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC-D74.1 — the cancel-tag ledger is bounded by a generation window
# ---------------------------------------------------------------------------
def test_ac_d74_1_cancel_tags_bounded_and_current_wave_ack_is_debug(
    monkeypatch, qapp, caplog
):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T74A")
    shown: list[str] = []
    win.status_bar.showMessage = lambda msg, ms=0: shown.append(msg)
    try:
        sizes: list[int] = []
        cancelled: list[int] = []
        for wave in range(_MANY_WAVES):
            _issue(session, stub, [_plan(f"202601{(wave % 28) + 1:02d}-20:00:00")])
            # The next load cancels the wave exactly as the load path does:
            # cancel (tags the current generation) → advance the generation
            # → drop the abandoned queue.
            session._cancel_history_requests()
            cancelled.append(stub.calls[-1]["reqId"])
            session._wave_plan_queue.clear()
            session._history_generation += 1
            sizes.append(len(session._cancelled_history_req_ids))

        # One more wave: the prune runs lazily at the wave's start, so this
        # is where the window contracts to the previous generation before the
        # current wave's own cancel adds its tag.
        _issue(session, stub, [_plan("20260101-20:00:00")])
        assert len(session._cancelled_history_req_ids) == 1
        session._cancel_history_requests()
        cancelled.append(stub.calls[-1]["reqId"])
        sizes.append(len(session._cancelled_history_req_ids))

        # One id is cancelled per generation: the window is the current and
        # previous generation, never the whole session's history.
        assert max(sizes) <= 2, sizes
        assert max(sizes) == 2
        assert len(sizes) == _MANY_WAVES + 1
        assert len(session._cancelled_history_req_ids) == 2
        # The id set and its generation ledger are pruned together.
        assert (
            set(session._cancelled_history_gen)
            == session._cancelled_history_req_ids
        )
        assert min(session._cancelled_history_gen.values()) >= (
            session._history_generation - 1
        )

        # A late ack for an id cancelled in the current wave: debug only.
        caught = cancelled[-1]
        assert session.is_superseded(caught)
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="ui.main_window")
        shown.clear()
        win._on_error(caught, 162, "Request cancelled")

        assert not any("Error [" in msg for msg in shown), shown
        assert any(
            record.levelno == logging.DEBUG and "superseded" in record.getMessage()
            for record in caplog.records
        ), caplog.records
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC-D74.2 — the failure set belongs to one wave, not the session
# ---------------------------------------------------------------------------
def test_ac_d74_2_wave_b_with_no_failures_reports_zero(monkeypatch, qapp):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T74B")
    shown: list[str] = []
    win.status_bar.showMessage = lambda msg, ms=0: shown.append(msg)
    try:
        # Wave A: two chunks, both fail.
        session.queue_wave_plans(
            [_plan("20260105-20:00:00"), _plan("20260104-20:00:00")],
            None, TF, False,
        )
        a1, a2 = [c["reqId"] for c in stub.calls]
        session.on_historical_error(a1, 500, "boom")
        mark = len(shown)
        session.on_historical_error(a2, 500, "boom")

        wave_a = shown[mark:]
        assert any("2 historical request(s) failed" in m for m in wave_a), wave_a
        assert session._backfill_failed_req_ids == {a1, a2}

        # Wave B: a fresh wave, its own chunk completes.
        mark = len(shown)
        session.queue_wave_plans([_plan("20260103-20:00:00")], None, TF, False)
        assert session._backfill_failed_req_ids == set()
        b1 = stub.calls[-1]["reqId"]
        _feed(session, b1, [BASE_TS + _STEP * i for i in range(3)])
        session.on_historical_data_end(b1)

        wave_b = shown[mark:]
        assert session._backfill_failed_req_ids == set()
        assert not any("historical request(s) failed" in m for m in wave_b), wave_b
    finally:
        win.close()


def test_ac_d74_2_prefetch_after_failed_load_reports_only_its_own(
    monkeypatch, qapp
):
    win, session, stub, clock = _make_session(monkeypatch, qapp, "T74C")
    shown: list[str] = []
    win.status_bar.showMessage = lambda msg, ms=0: shown.append(msg)
    try:
        # A failed load: two failed chunks.
        session.queue_wave_plans(
            [_plan("20260105-20:00:00"), _plan("20260104-20:00:00")],
            None, TF, False,
        )
        a1, a2 = [c["reqId"] for c in stub.calls]
        session.on_historical_error(a1, 500, "boom")
        session.on_historical_error(a2, 500, "boom")
        assert session._backfill_failed_req_ids == {a1, a2}

        # A prefetch wave starts immediately after that failed load: it is
        # issued through the same queue_wave_plans call
        # maybe_issue_prefetch_wave makes, so its ledger is its own.
        mark = len(shown)
        session.queue_wave_plans([_plan("20260103-20:00:00")], None, TF, False)
        p1 = stub.calls[-1]["reqId"]
        session.on_historical_error(p1, 500, "boom")

        wave_p = shown[mark:]
        assert session._backfill_failed_req_ids == {p1}
        assert any(
            "1 historical request(s) failed" in m for m in wave_p
        ), wave_p
        assert not any(
            "2 historical request(s) failed" in m for m in wave_p
        ), wave_p
    finally:
        win.close()
