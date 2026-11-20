import os

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
# Default to Live TWS (7496)
# D94 / S-P28-6: settings parsing cannot raise. A malformed value is kept as
# text in _<NAME>_PARSE_ERROR and refused by check_live_port() — which runs in
# main() AFTER QApplication exists, so the user gets the fatal dialog instead
# of a bare ValueError before any UI can speak. IBKR_PORT is `int | None` only
# between this import and the guard; MainWindow never sees anything but an int.
_RAW_PORT = os.getenv("IBKR_PORT", "7496")
try:
    IBKR_PORT: int | None = int(_RAW_PORT)
    _PORT_PARSE_ERROR: str | None = None
except ValueError:
    IBKR_PORT = None
    _PORT_PARSE_ERROR = _RAW_PORT

_RAW_CLIENT_ID = os.getenv("IBKR_CLIENT_ID", "1")
try:
    IBKR_CLIENT_ID: int | None = int(_RAW_CLIENT_ID)
    _CLIENT_ID_PARSE_ERROR: str | None = None
except ValueError:
    IBKR_CLIENT_ID = None
    _CLIENT_ID_PARSE_ERROR = _RAW_CLIENT_ID

# D26.5: the only port this app may connect on. NDThinkChart is a read-only
# market-data client that places no orders; this guard is a configuration
# check — it verifies the configured port only, not the TWS account behind it.
LIVE_PORT = 7496


def check_live_port() -> None:
    """Fail fast unless configured for the live TWS port.

    Raises SystemExit with a human-readable message; main.py surfaces it
    as a fatal dialog before any connection is attempted.

    D94 / S-P28-6: this is also where a malformed setting is refused — the
    import keeps the raw text so the offending value can be named. The order
    is port-parse, client-id-parse, then the D26.5 live-port comparison.
    """
    if _PORT_PARSE_ERROR is not None:
        raise SystemExit(
            f"Refusing to start: IBKR_PORT={_PORT_PARSE_ERROR} is not a "
            f"valid integer port (the live TWS port is {LIVE_PORT}). "
            "NDThinkChart is a read-only market-data client that places no "
            "orders — fix IBKR_PORT."
        )
    if _CLIENT_ID_PARSE_ERROR is not None:
        raise SystemExit(
            f"Refusing to start: IBKR_CLIENT_ID={_CLIENT_ID_PARSE_ERROR} is "
            "not a valid integer client id. NDThinkChart is a read-only "
            "market-data client that places no orders — fix IBKR_CLIENT_ID."
        )
    if IBKR_PORT != LIVE_PORT:
        raise SystemExit(
            f"Refusing to start: IBKR_PORT={IBKR_PORT} is not the configured "
            f"TWS port ({LIVE_PORT}). NDThinkChart is a read-only market-data "
            "client — it places no orders. "
            f"Set IBKR_PORT={LIVE_PORT} to continue. This check verifies the "
            "configured port only, not the TWS account behind it."
        )

DB_PATH = os.getenv("DB_PATH", "charting_app.sqlite3")

# Pacing & Rate Limits (per IBKR API guidelines)
MAX_REQ_PER_SEC = 50
MAX_REALTIME_BARS_PER_10_MIN = 60
# D28.3/Q-30: rolling 600s window budget for reqHistoricalData. Exceeding it
# yields error 162 (pacing violation). Owner-set to 100 requests per window:
# with the 0.5 s minimum interval below the interval gate's theoretical
# ceiling is 1200 requests per 600 s, so THIS budget binds first.
# Non-blocking: the issuer raises PacingExceeded when the budget is exhausted.
MAX_HISTORICAL_PER_600S = 100

# D28.3/Q-2/Q-30: IBKR cancels same-contract historical requests issued in
# quick succession (error 162 "API historical data query cancelled"), so keep
# at least this many seconds between reqHistoricalData calls. Owner-set to
# 0.5 s (faster backfills, ~2 requests/second). Enforced non-blocking:
# historical_wait_seconds() reports the remainder and callers defer via
# PacingExceeded -> continuation timer.
HISTORICAL_MIN_INTERVAL_S = 0.5

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
