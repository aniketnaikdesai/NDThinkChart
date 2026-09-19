import time
import threading
from collections import deque
from config import settings

class PacingManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_req_time = 0.0
        self._min_interval = 1.0 / settings.MAX_REQ_PER_SEC
        self._rt_window = 600.0
        self._rt_times: deque = deque()

    def throttle(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_req_time
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                time.sleep(sleep_time)
            self._last_req_time = time.time()

    def throttle_realtime(self):
        """Enforce MAX_REALTIME_BARS_PER_10_MIN with a rolling 10-minute window."""
        with self._lock:
            now = time.time()
            while self._rt_times and now - self._rt_times[0] >= self._rt_window:
                self._rt_times.popleft()
            if len(self._rt_times) >= settings.MAX_REALTIME_BARS_PER_10_MIN:
                wait = self._rt_times[0] + self._rt_window - now
                time.sleep(wait)
                now = time.time()
                while self._rt_times and now - self._rt_times[0] >= self._rt_window:
                    self._rt_times.popleft()
            self._rt_times.append(now)
            self._last_req_time = now

# Global singleton
pacing_manager = PacingManager()