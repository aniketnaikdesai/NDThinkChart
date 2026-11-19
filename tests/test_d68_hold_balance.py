"""D68 — a pop-out releases at most the one RT hold it acquired (P25-T3).

The defect: ``PopoutChartWindow.detach`` released the session's RT hold
unconditionally, so a pop-out whose first ``ensure_rt_subscribed()`` raised
``PacingExceeded`` (no hold acquired) released the *main chart's* hold on
close — the subscription died while a visible chart still showed live bars.

The session's hold API is frozen as a plain integer refcount whose
``release_rt`` takes no owner (``tests/test_p13_hold_fix.py`` pins the
``["self"]`` parameter lists and the absence of ``acquire_rt`` /
``release_rt_for`` / ``_rt_owners``), so the acquisition record lives on the
pop-out (``_hold_acquired``) and a closed latch (``_closed``) keeps a deferred
retry from acquiring after close.

Every case runs the real ``MainWindow``/host and a real ``TickerSession``; the
realtime manager is replaced by a recorder so subscribe/unsubscribe per reqId
(and therefore the live subscription set) is observable.
"""

from __future__ import annotations

import itertools

import pytest

from ibkr.pacing import PacingExceeded

SYMBOL = "HOLD68"
OTHER = "HOLD69"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


class _FakeRtManager:
    """Records subscribe/unsubscribe per reqId; ``live`` is the open set."""

    def __init__(self, first_id: int = 6001):
        self._ids = itertools.count(first_id)
        self.subscribed: list[int] = []
        self.unsubscribed: list[int] = []

    def subscribe(self, symbol, contract=None, *args, **kwargs) -> int:
        req_id = next(self._ids)
        self.subscribed.append(req_id)
        return req_id

    def unsubscribe(self, req_id: int) -> None:
        self.unsubscribed.append(req_id)

    @property
    def live(self) -> set[int]:
        return set(self.subscribed) - set(self.unsubscribed)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    fake = _FakeRtManager()
    win.rt_manager.subscribe = fake.subscribe
    win.rt_manager.unsubscribe = fake.unsubscribe
    # D42's depth floor can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(6101)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    win._now_ts = lambda: NOW_TS
    return win, fake


def _load_main(win, qapp):
    """Load the main chart: it holds exactly one RT hold on the session."""
    win.load_chart(SYMBOL, TF)
    qapp.processEvents()
    session = win._sessions[SYMBOL]
    assert session._rt_holders == 1, "main chart must own the baseline hold"
    return session


def _defer_subscribe(session, raise_on) -> dict:
    """Make ``ensure_rt_subscribed`` raise PacingExceeded on chosen calls.

    Installed on the instance (the class contract is untouched) and after the
    main chart has already acquired its hold, so ``calls["count"]`` counts
    only pop-out acquisitions.
    """
    real = session.ensure_rt_subscribed
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] in raise_on:
            # Long enough that the singleShot retry cannot fire in-test.
            raise PacingExceeded(30.0)
        return real()

    session.ensure_rt_subscribed = flaky
    return calls


def _count_releases(session) -> list:
    """Record every ``release_rt`` call (with the holder count it saw)."""
    releases: list[int] = []
    real = session.release_rt

    def counting():
        releases.append(session._rt_holders)
        return real()

    session.release_rt = counting
    return releases


def test_deferred_popout_close_releases_nothing(monkeypatch, qapp):
    """AC-D68.1: a deferred pop-out closed before its retry releases nothing."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        session = _load_main(win, qapp)
        main_req = session.rt_req_id
        before = session._rt_holders
        live_before = set(fake.live)

        calls = _defer_subscribe(session, raise_on={1})
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        assert popout._hold_acquired is False
        assert calls["count"] == 1
        assert session._rt_holders == before
        assert set(fake.live) == live_before

        # Close before the deferred retry fires.
        popout.close()
        assert popout._hold_acquired is False
        assert popout._closed is True
        qapp.processEvents()

        assert session._rt_holders == before
        assert fake.unsubscribed == [], "no release may be recorded"
        assert main_req not in fake.unsubscribed
        assert set(fake.live) == live_before
    finally:
        win.close()


def test_acquired_popout_releases_exactly_once(monkeypatch, qapp):
    """AC-D68.2: an acquired pop-out releases once; a second detach no-ops."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        session = _load_main(win, qapp)
        before = session._rt_holders
        releases = _count_releases(session)

        win._open_popout()
        qapp.processEvents()
        popout = win._popouts[0]
        assert popout._hold_acquired is True
        assert session._rt_holders == before + 1

        popout.close()
        assert popout._hold_acquired is False
        assert len(releases) == 1
        assert session._rt_holders == before
        qapp.processEvents()
        # The main chart's hold still keeps the subscription live.
        assert fake.unsubscribed == []

        # AC-D68.2 (second half): a second detach releases nothing further.
        popout.detach()
        qapp.processEvents()
        assert len(releases) == 1
        assert session._rt_holders == before
        assert fake.unsubscribed == []
    finally:
        win.close()


@pytest.mark.parametrize("first_closed", ["deferred", "acquired"])
def test_two_popouts_close_in_either_order(monkeypatch, qapp, first_closed):
    """AC-D68.3: two pop-outs, one deferred; either close order balances."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        session = _load_main(win, qapp)
        before = session._rt_holders
        live_before = set(fake.live)
        releases = _count_releases(session)

        # Pop-out #1 acquires; pop-out #2's subscribe is pacing-deferred.
        calls = _defer_subscribe(session, raise_on={2})
        win._open_popout()
        qapp.processEvents()
        win._open_popout()
        qapp.processEvents()

        acquired, deferred = win._popouts
        assert calls["count"] == 2
        assert acquired._hold_acquired is True
        assert deferred._hold_acquired is False
        assert session._rt_holders == before + 1

        first, last = (
            (deferred, acquired) if first_closed == "deferred"
            else (acquired, deferred)
        )
        first.close()
        qapp.processEvents()

        # Closing one leaves the main chart's hold intact — and whichever
        # window just closed releases only a hold it actually acquired.
        assert session._rt_holders >= before
        assert fake.unsubscribed == []
        assert len(releases) == (0 if first_closed == "deferred" else 1)

        last.close()
        qapp.processEvents()

        assert session._rt_holders == before
        assert len(releases) == 1, "only the acquired pop-out released"
        assert fake.unsubscribed == []
        assert set(fake.live) == live_before
    finally:
        win.close()


def test_retry_after_close_acquires_nothing(monkeypatch, qapp):
    """AC-D68.4: the closed latch makes a late retry a no-op."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        session = _load_main(win, qapp)
        before = session._rt_holders
        calls = _defer_subscribe(session, raise_on={1})
        releases = _count_releases(session)

        win._open_popout()
        qapp.processEvents()
        popout = win._popouts[0]
        popout.close()
        qapp.processEvents()

        assert popout._closed is True
        subscribed_after_close = list(fake.subscribed)
        unsubscribed_after_close = list(fake.unsubscribed)
        assert calls["count"] == 1

        # The retry QTimer would have queued this call; fire it by hand.
        popout._retry_rt_subscribe()
        qapp.processEvents()

        assert calls["count"] == 1, "the retry must not call subscribe"
        assert fake.subscribed == subscribed_after_close
        assert fake.unsubscribed == unsubscribed_after_close
        assert releases == []
        assert session._rt_holders == before
    finally:
        win.close()


def test_main_closed_first_popout_keeps_feed_alive(monkeypatch, qapp):
    """AC-D68.5: the pop-out's hold survives the main chart's close."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        session = _load_main(win, qapp)
        popout_req = session.rt_req_id

        win._open_popout()
        qapp.processEvents()
        popout = win._popouts[0]
        assert popout._hold_acquired is True
        assert session._rt_holders == 2

        # Close the main chart by loading another symbol: the primary's hold
        # and view leave HOLD68's session, the pop-out's hold remains.
        win.load_chart(OTHER, TF)
        qapp.processEvents()

        assert session._rt_holders == 1
        assert popout_req not in fake.unsubscribed
        assert popout_req in fake.live

        releases = _count_releases(session)
        popout.close()
        qapp.processEvents()

        assert len(releases) == 1
        assert fake.unsubscribed == [popout_req]
        assert popout_req not in fake.live
    finally:
        win.close()
