import contextlib
import time
import threading
from collections import deque
from config import settings


class PacingExceeded(Exception):
    """Raised instead of sleeping when a pacing budget is exhausted.

    Carries the seconds the caller should wait before retrying; callers
    defer via QTimer.singleShot and show a persistent "pacing-limited"
    status (D28.1). Pacing must NEVER time.sleep on the GUI thread.
    """

    def __init__(self, wait_seconds: float):
        self.wait_seconds = max(0.0, float(wait_seconds))
        super().__init__(
            f"pacing budget exhausted; retry in {self.wait_seconds:.1f}s"
        )


class PacingManager:
    # Q-17: a caller that sleeps exactly the reported interval wait must land
    # PAST the gate, not on it. The value is sampled before the caller starts
    # its timer, and a coarse Qt timer may fire a few percent early, so an
    # exact wait can be rejected forever (PacingExceeded(0.0004) -> "in 0s").
    # Pad the binding interval wait by this margin (never above one interval).
    _INTERVAL_SAFETY_MARGIN_S = 0.05

    def __init__(self):
        self._lock = threading.Lock()
        self._last_req_time = 0.0
        self._min_interval = 1.0 / settings.MAX_REQ_PER_SEC
        # P26/D71: unspent units of an open generic batch reservation. Only
        # non-zero inside ``generic_batch``; cleared in its ``finally`` and
        # by ``reset_for_tests`` so it can never admit a later send.
        self._batch_remaining = 0
        self._rt_window = 600.0
        self._rt_times: deque = deque()
        # D28.3: rolling 600s window for reqHistoricalData. Same shape as
        # the realtime-bar budget (IBKR error 162 = pacing violation).
        self._hist_window = 600.0
        self._hist_times: deque = deque()
        # Q-2: minimum spacing between historical requests. IBKR cancels
        # same-contract requests issued microseconds apart (error 162), so
        # the issuer defers instead of bursting a whole wave synchronously.
        self._last_hist_time = 0.0

    def request_wait_seconds(self) -> float:
        """Seconds until the next generic request may issue; 0.0 = now.

        Covers the minimum-interval gate (``1 / MAX_REQ_PER_SEC``) shared by
        the live market-data paths (reqMktData, reqContractDetails,
        reqMatchingSymbols). Pure and non-blocking: never sleeps. The lock
        is held only around the timestamp bookkeeping.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_req_time
            return max(0.0, self._min_interval - elapsed)

    def record_request_slot(self) -> None:
        """Stamp the minimum-interval clock after a request was issued.

        Call only after the request was actually sent, mirroring
        ``record_historical_slot`` / ``record_realtime_slot``. Lock held
        only for bookkeeping.
        """
        with self._lock:
            self._last_req_time = time.time()

    def generic_wait_for_batch(self, count: int) -> float:
        """Seconds until ``count`` back-to-back generic sends may issue.

        Pure and non-blocking. ``count <= 0`` is an empty reservation: it
        reserves no unit and never touches the interval clock, so 0.0 is
        reported. A batch of exactly one reserves one unit **by design**:
        an open batch of ``n`` admits ``n`` calls to :meth:`throttle`
        (AC-D71.5), so its single send is admitted without reading the
        ordinary gate — a caller that wants the gate to decide must not
        open a reservation. For ``count > 1`` the batch is modelled as
        occupying ``count - 1`` further intervals after the last real send.
        The lock is held only around the timestamp read.
        """
        if count <= 1:
            return 0.0
        with self._lock:
            now = time.time()
            interval = 1.0 / settings.MAX_REQ_PER_SEC
            return max(0.0, (count - 1) * interval - (now - self._last_req_time))

    @contextlib.contextmanager
    def generic_batch(self, count: int):
        """Reserve ``count`` generic sends as one pacing transaction.

        P26/D71: a replay pass issues many ``reqMktData`` calls back to back,
        which the minimum-interval gate would refuse from the second send
        onward. The batch converts that burst into pacing-timeline
        bookkeeping: it re-checks :meth:`generic_wait_for_batch` before the
        body runs (raising ``PacingExceeded`` from ``__enter__`` so the body
        never executes), admits the next ``count`` calls to :meth:`throttle`
        without consulting the gate, and on exit clears the reservation and
        stamps the interval clock once for the whole burst.

        An empty reservation (``count <= 0``) is not spendable and does not
        touch the interval clock: the body still runs — so a caller can pass
        a derived count unguarded, as ``replay_all`` does — but no unit is
        reserved, the gate decides every send, and the exit stamp is
        skipped. A batch of exactly one admits its single send by design
        (an open batch of ``n`` admits ``n`` calls, AC-D71.5) and likewise
        stamps the clock once on exit.

        Fail-closed: a send beyond the reservation falls through to the
        unchanged gate — admitted only when the interval has genuinely
        elapsed since the last real stamp, and raising otherwise — so a
        reservation can never be spent twice or leak past this ``with``.
        """
        units = int(count)
        if units <= 0:
            yield
            return
        wait = self.generic_wait_for_batch(units)
        if wait > 0:
            raise PacingExceeded(wait)
        with self._lock:
            self._batch_remaining = units
        try:
            yield
        finally:
            with self._lock:
                self._batch_remaining = 0
            self.record_request_slot()

    def throttle(self, *, stamp: bool = True) -> bool:
        """Non-blocking minimum-interval gate (D28.1 / Q-41 / D81).

        Never sleeps: when the minimum interval has not elapsed since the
        last request, raises ``PacingExceeded`` carrying the seconds the
        caller must wait before retrying. Callers defer via
        ``QTimer.singleShot`` / existing timer paths (never ``time.sleep``
        on the GUI thread). The lock is held only around timestamp
        bookkeeping and is never held across the wait.

        Returns whether a :meth:`generic_batch` reservation unit was spent.

        D81: ``stamp=False`` reads the gate without stamping it, for callers
        that stamp only after their own send actually crossed the wire —
        ``MarketDataManager``'s request paths call it in front of the send and
        then ``record_request_slot()`` on success. A refused gate therefore
        charges nothing at all, whichever mode is used; the default
        (``stamp=True``) keeps the original stamp-on-success behaviour for
        every existing caller.

        P26/D71: while a :meth:`generic_batch` reservation is open, a call
        consumes one reserved unit, returns ``True`` and does not touch the
        clock; the reservation's ``finally`` stamps the interval once for the
        whole burst.
        """
        with self._lock:
            if self._batch_remaining > 0:
                self._batch_remaining -= 1
                return True
        wait = self.request_wait_seconds()
        if wait > 0:
            raise PacingExceeded(wait)
        if stamp:
            self.record_request_slot()
        return False

    def _expire_rt_slots(self, now: float) -> None:
        """Drop slots older than the rolling window. Caller must hold the lock."""
        while self._rt_times and now - self._rt_times[0] >= self._rt_window:
            self._rt_times.popleft()

    def realtime_available_slots(self) -> int:
        """Free realtime-bar slots right now (no sleep, no mutation)."""
        with self._lock:
            self._expire_rt_slots(time.time())
            return settings.MAX_REALTIME_BARS_PER_10_MIN - len(self._rt_times)

    def realtime_wait_for_slots(self, n: int) -> float:
        """Seconds until ``n`` realtime-bar slots free up; 0.0 = subscribe now.

        Never sleeps. The lock is held only around deque bookkeeping (D28.1).
        """
        if n <= 0:
            return 0.0
        with self._lock:
            now = time.time()
            self._expire_rt_slots(now)
            budget = settings.MAX_REALTIME_BARS_PER_10_MIN
            free = budget - len(self._rt_times)
            if free >= n:
                return 0.0
            # Need (n - free) more slots: the (n-free)-th oldest entry's
            # expiry is when enough slots have freed.
            needed = n - free
            idx = min(needed - 1, len(self._rt_times) - 1)
            expiry = self._rt_times[idx] + self._rt_window
            return max(0.0, expiry - now)

    def realtime_wait_seconds(self) -> float:
        """Seconds until one realtime-bar slot frees; 0.0 = subscribe now."""
        return self.realtime_wait_for_slots(1)

    def record_realtime_slot(self) -> None:
        """Record a realtime-bar subscription against the budget (call after
        the request is actually issued). Lock held only for bookkeeping."""
        with self._lock:
            now = time.time()
            self._expire_rt_slots(now)
            self._rt_times.append(now)
            self._last_req_time = now

    def _expire_hist_slots(self, now: float) -> None:
        """Drop historical slots older than the rolling window.

        Caller must hold the lock."""
        while self._hist_times and now - self._hist_times[0] >= self._hist_window:
            self._hist_times.popleft()

    def historical_wait_seconds(self) -> float:
        """Seconds until the next historical request may issue; 0.0 = now.

        Both gates are reported together: the rolling 600s budget and the
        minimum interval between requests (Q-2). Pure and non-blocking:
        never sleeps. Callers that must issue many requests (the backfill
        wave) defer the rest via QTimer.singleShot (D28.3), so the interval
        naturally spaces a wave out instead of bursting it.
        """
        with self._lock:
            now = time.time()
            self._expire_hist_slots(now)
            budget = settings.MAX_HISTORICAL_PER_600S
            free = budget - len(self._hist_times)
            if free > 0:
                budget_wait = 0.0
            else:
                budget_wait = max(
                    0.0, self._hist_times[0] + self._hist_window - now
                )
            interval_wait = max(
                0.0,
                settings.HISTORICAL_MIN_INTERVAL_S
                - (now - self._last_hist_time),
            )
            reported = budget_wait
            if interval_wait > 0.0:
                # Q-17: when the interval is the binding gate, report the wait
                # AUTHORITATIVELY rather than exactly — with a small margin so
                # a caller that sleeps the returned duration is guaranteed past
                # the gate even if its timer fires a few ms early. Capped at
                # one interval so a freshly recorded request never reports
                # more than its own interval.
                reported = max(
                    reported,
                    min(
                        interval_wait + self._INTERVAL_SAFETY_MARGIN_S,
                        settings.HISTORICAL_MIN_INTERVAL_S,
                    ),
                )
            return reported

    def record_historical_slot(self) -> None:
        """Record a reqHistoricalData request against the budget. Call only
        after the request was actually issued (D28.3). Also stamps the
        minimum-interval clock (Q-2)."""
        with self._lock:
            now = time.time()
            self._expire_hist_slots(now)
            self._hist_times.append(now)
            self._last_hist_time = now

    def reset_for_tests(self) -> None:
        """Clear pacing state. Test-only: keeps the suite hermetic.

        P26/D71: also drops any open batch reservation, so a leftover
        counter can never admit a later send.
        """
        with self._lock:
            self._rt_times.clear()
            self._hist_times.clear()
            self._last_hist_time = 0.0
            self._last_req_time = 0.0
            self._batch_remaining = 0


# Global singleton
pacing_manager = PacingManager()
