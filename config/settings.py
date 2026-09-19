import os

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
# Default to Live TWS (7496)
IBKR_PORT = int(os.getenv("IBKR_PORT", 7496))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", 1))

DB_PATH = os.getenv("DB_PATH", "charting_app.sqlite3")

# Pacing & Rate Limits (per IBKR API guidelines)
MAX_REQ_PER_SEC = 50
MAX_REALTIME_BARS_PER_10_MIN = 60
