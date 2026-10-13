from data.db import db
from data.models import Bar
from typing import List, Optional

#: D28.4: SQLite retention — the newest N bars per (symbol, timeframe) are
#: kept; older rows are pruned after each backfill wave so the on-disk
#: cache stays bounded alongside the in-memory SESSION_BAR_CAP.
RETENTION_BARS = 5000


class BarCache:
    @staticmethod
    def save_bars(bars: List[Bar]):
        """Insert or replace bars in the SQLite cache."""
        if not bars:
            return
        cursor = db.conn.cursor()
        cursor.executemany(
            """INSERT OR REPLACE INTO bars (symbol, timeframe, ts, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(b.symbol, b.timeframe, b.ts, b.open, b.high, b.low, b.close, b.volume)
             for b in bars]
        )
        db.conn.commit()

    @staticmethod
    def get_bars(symbol: str, timeframe: str) -> List[Bar]:
        """Load all cached bars for a symbol/timeframe, sorted ascending."""
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT ts, open, high, low, close, volume FROM bars "
            "WHERE symbol=? AND timeframe=? ORDER BY ts ASC",
            (symbol, timeframe)
        )
        return [Bar(symbol, timeframe, r[0], r[1], r[2], r[3], r[4], r[5])
                for r in cursor.fetchall()]

    @staticmethod
    def prune(symbol: str, timeframe: str, keep: int = RETENTION_BARS) -> int:
        """D28.4: delete cached bars beyond the newest ``keep`` rows for
        one (symbol, timeframe). Returns the number of rows deleted."""
        cursor = db.conn.cursor()
        cursor.execute(
            """DELETE FROM bars WHERE symbol=? AND timeframe=?
               AND ts NOT IN (
                   SELECT ts FROM bars WHERE symbol=? AND timeframe=?
                   ORDER BY ts DESC LIMIT ?
               )""",
            (symbol, timeframe, symbol, timeframe, keep),
        )
        db.conn.commit()
        return cursor.rowcount

    @staticmethod
    def get_last_timestamp(symbol: str, timeframe: str) -> Optional[int]:
        """Return the unix timestamp of the most recent cached bar, or None."""
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT MAX(ts) FROM bars WHERE symbol=? AND timeframe=?",
            (symbol, timeframe)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
