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
    def __init__(self):
        self._lock = threading.Lock()
        self._last_req_time = 0.0
        self._min_interval = 1.0 / settings.MAX_REQ_PER_SEC
        self._rt_window = 600.0
        self._rt_times: deque = deque()
        # D28.3: rolling 600s window for reqHistoricalData. Same shape as
        # the realtime-bar budget (IBKR error 162 = pacing violation).
        self._hist_window = 600.0
        self._hist_times: deque = deque()

    def throttle(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_req_time
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                time.sleep(sleep_time)
            self._last_req_time = time.time()

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
        """Seconds until one historical-data slot frees; 0.0 = request now.

        Pure and non-blocking: never sleeps. Callers that must issue many
        requests (the backfill wave) cap their chunk count and defer the
        rest via QTimer.singleShot (D28.3).
        """
        with self._lock:
            now = time.time()
            self._expire_hist_slots(now)
            budget = settings.MAX_HISTORICAL_PER_600S
            free = budget - len(self._hist_times)
            if free > 0:
                return 0.0
            expiry = self._hist_times[0] + self._hist_window
            return max(0.0, expiry - now)

    def record_historical_slot(self) -> None:
        """Record a reqHistoricalData request against the budget. Call only
        after the request was actually issued (D28.3)."""
        with self._lock:
            now = time.time()
            self._expire_hist_slots(now)
            self._hist_times.append(now)

    def reset_for_tests(self) -> None:
        """Clear pacing state. Test-only: keeps the suite hermetic."""
        with self._lock:
            self._rt_times.clear()
            self._hist_times.clear()
            self._last_req_time = 0.0


class OrderRateLimiter:
    """Token bucket for the order path (D28.1).

    Orders were throttled by the realtime-bar budget (which could sleep the
    GUI thread for up to 10 minutes). They now get their own limiter that
    never blocks: ``try_acquire`` returns False when empty and the caller
    defers via QTimer.singleShot.
    """

    def __init__(self, rate_per_sec: float = 5.0, capacity: int = 5):
        self._rate = rate_per_sec
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            self._tokens = min(
                self._capacity, self._tokens + (now - self._last) * self._rate
            )
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    def retry_delay_s(self) -> float:
        """Seconds until (at least) one token refills."""
        with self._lock:
            if self._tokens >= 1.0:
                return 0.0
            return max(0.0, (1.0 - self._tokens) / self._rate)

    def reset_for_tests(self) -> None:
        """Refill the bucket. Test-only: keeps the suite hermetic."""
        with self._lock:
            self._tokens = float(self._capacity)
            self._last = time.monotonic()


# Global singletons
pacing_manager = PacingManager()
order_limiter = OrderRateLimiter()
