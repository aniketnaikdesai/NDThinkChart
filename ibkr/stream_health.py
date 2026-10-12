"""
stream_health.py

D27.4: per-stream health state for a live IBKR realtime subscription.

States: SUBSCRIBED -> AWAITING_FIRST_BAR -> LIVE, or FAILED with the TWS
error code. A failed subscription retries with backoff (the attempt count
lives here so the window can compute the delay).

Ownership seam (D27.4 / Phase 3b): owned by ``MainWindow`` in Phase 2 for the
chart's RT stream; migrates into ``TickerSession`` (one per session) in
Phase 3b — it carries no window references, so the move is a field move.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class StreamState:
    SUBSCRIBED = "subscribed"
    AWAITING_FIRST_BAR = "awaiting_first_bar"
    LIVE = "live"
    FAILED = "failed"


@dataclass
class StreamHealth:
    """Health of one live realtime subscription."""

    state: str = StreamState.SUBSCRIBED
    fail_code: int | None = None
    fail_message: str = ""
    retry_attempt: int = 0

    def mark_subscribed(self, reset_backoff: bool = True) -> None:
        """A (re)subscription was issued; awaiting the first bar.

        ``reset_backoff`` is True for fresh user-initiated subscriptions
        (load_chart). Backoff retries pass False so consecutive failures keep
        progressing 5s -> 10s -> 20s -> 60s instead of restarting at 5s
        (D27.4: each 5s retry burns a pacing slot).
        """
        self.state = StreamState.AWAITING_FIRST_BAR
        self.fail_code = None
        self.fail_message = ""
        if reset_backoff:
            self.retry_attempt = 0

    def mark_first_bar(self) -> None:
        """The first bar arrived: the stream is live."""
        self.state = StreamState.LIVE
        self.fail_code = None
        self.fail_message = ""
        self.retry_attempt = 0

    def mark_failed(self, code: int, message: str = "") -> None:
        """The subscription failed; records the TWS error code."""
        self.state = StreamState.FAILED
        self.fail_code = code
        self.fail_message = message

    @property
    def is_live(self) -> bool:
        return self.state == StreamState.LIVE

    def describe(self) -> str:
        """Short human-readable state for status lines (D27.4)."""
        if self.state == StreamState.LIVE:
            return "live"
        if self.state == StreamState.FAILED:
            code = f" [{self.fail_code}]" if self.fail_code is not None else ""
            return f"failed{code}"
        return "awaiting first bar"

    def next_retry_delay_s(self, base_s: float = 5.0,
                           max_s: float = 60.0) -> float:
        """Exponential backoff for the next retry; counts the attempt."""
        self.retry_attempt += 1
        return min(base_s * (2 ** (self.retry_attempt - 1)), max_s)
