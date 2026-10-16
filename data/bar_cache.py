from data.db import db
from data.models import Bar
from typing import List, Optional

#: D28.4: SQLite retention — the newest N bars per (symbol, timeframe) are
#: kept; older rows are pruned after each backfill wave so the on-disk
#: cache stays bounded alongside the in-memory SESSION_BAR_CAP.
RETENTION_BARS = 5000


class BarCache:
    @staticmethod
    def save_bars(bars: List[Bar], ext_hours: bool = True):
        """Insert or replace bars in the SQLite cache for one mode.

        ``ext_hours`` (default ``True``, the app default) is part of the cache
        key: rows written for one mode are never visible to the other
        (AC-D16.9).
        """
        if not bars:
            return
        mode = 1 if ext_hours else 0
        cursor = db.conn.cursor()
        cursor.executemany(
            """INSERT OR REPLACE INTO bars
               (symbol, timeframe, ext_hours, ts, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(b.symbol, b.timeframe, mode, b.ts, b.open, b.high, b.low, b.close, b.volume)
             for b in bars]
        )
        db.conn.commit()

    @staticmethod
    def get_bars(symbol: str, timeframe: str, ext_hours: bool = True) -> List[Bar]:
        """Load all cached bars for a symbol/timeframe in one mode, sorted ascending.

        ``ext_hours`` (default ``True``, the app default) scopes the read to the
        requested mode, so an RTH read cannot return ETH rows and vice versa
        (AC-D16.9).
        """
        mode = 1 if ext_hours else 0
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT ts, open, high, low, close, volume FROM bars "
            "WHERE symbol=? AND timeframe=? AND ext_hours=? ORDER BY ts ASC",
            (symbol, timeframe, mode)
        )
        return [Bar(symbol, timeframe, r[0], r[1], r[2], r[3], r[4], r[5])
                for r in cursor.fetchall()]

    @staticmethod
    def prune(symbol: str, timeframe: str, ext_hours: bool = True,
              keep: int = RETENTION_BARS) -> int:
        """D28.4: delete cached bars beyond the newest ``keep`` rows for
        one (symbol, timeframe) in one mode. Returns the number of rows deleted.

        ``ext_hours`` (default ``True``, the app default) scopes retention to
        the mode, so pruning one mode never deletes the other's rows
        (AC-D16.9).
        """
        mode = 1 if ext_hours else 0
        cursor = db.conn.cursor()
        cursor.execute(
            """DELETE FROM bars WHERE symbol=? AND timeframe=? AND ext_hours=?
               AND ts NOT IN (
                   SELECT ts FROM bars WHERE symbol=? AND timeframe=? AND ext_hours=?
                   ORDER BY ts DESC LIMIT ?
               )""",
            (symbol, timeframe, mode, symbol, timeframe, mode, keep),
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
