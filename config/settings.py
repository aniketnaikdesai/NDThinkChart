import os

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
# Default to Live TWS (7496)
IBKR_PORT = int(os.getenv("IBKR_PORT", 7496))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", 1))

# D26.5: the only port this app may trade on. TWS uses 7496 for live and
# 7497 for paper; a paper-port typo must never silently trade paper while
# the UI claims to be live.
LIVE_PORT = 7496


def check_live_port() -> None:
    """Fail fast unless configured for the live TWS port.

    Raises SystemExit with a human-readable message; main.py surfaces it
    as a fatal dialog before any connection is attempted.
    """
    if IBKR_PORT != LIVE_PORT:
        raise SystemExit(
            f"Refusing to start: IBKR_PORT={IBKR_PORT} is not the live TWS "
            f"port ({LIVE_PORT}). NDThinkChart trades live only — fix IBKR_PORT."
        )

DB_PATH = os.getenv("DB_PATH", "charting_app.sqlite3")

# Pacing & Rate Limits (per IBKR API guidelines)
MAX_REQ_PER_SEC = 50
MAX_REALTIME_BARS_PER_10_MIN = 60
# D28.3: rolling 600s window budget for reqHistoricalData. IBKR's documented
# limit is ~60 historical requests per 10 minutes; exceeding it yields
# error 162 (pacing violation). Non-blocking: the issuer raises
# PacingExceeded when the budget is exhausted.
MAX_HISTORICAL_PER_600S = 60

# D24.5: maximum pop-out chart windows (owner-set 2026-10-12).
MAX_POPOUTS = 10

# D28.2/D28.4: per-session in-memory bar cap (front-loaded from D28.4).
SESSION_BAR_CAP = 5000

# D42/S20 (AC-D16.8): the owner-required intraday depth floor — each intraday
# timeframe in each mode loads >= this many trading sessions before the current
# session. This is the floor's single tunable: both the backfill planner's floor
# span and floor_bar_budget() derive from it. ibkr/market_data.py::TIMEFRAME_CONFIG
# durations are deliberately NOT changed — those are the per-request IBKR caps,
# and the depth comes from chaining requests (S17).
MIN_INTRADAY_SESSIONS = 30
