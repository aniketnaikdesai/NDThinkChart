import sqlite3
from config import paths


class DB:
    def __init__(self):
        # Use paths.get_db_path() for production (user-space) and dev (local)
        self.db_path = paths.get_db_path()
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self._init_schema()

    def _init_schema(self):
        schema = """
        CREATE TABLE IF NOT EXISTS bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts INTEGER NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume REAL,
            PRIMARY KEY (symbol, timeframe, ts)
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            sort_order INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            direction TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            triggered INTEGER NOT NULL DEFAULT 0,
            triggered_at INTEGER,
            sound INTEGER NOT NULL DEFAULT 1,
            note TEXT
        );
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price_low REAL NOT NULL,
            price_high REAL NOT NULL,
            kind TEXT NOT NULL,
            label TEXT,
            color TEXT,
            visible INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS drawing_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            seq_number INTEGER NOT NULL,
            color TEXT,
            visible INTEGER NOT NULL DEFAULT 1,
            locked INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            color TEXT,
            label TEXT,
            group_id INTEGER REFERENCES drawing_groups(id)
        );
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            params TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            account TEXT NOT NULL,
            con_id INTEGER,
            contract_type TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_cost REAL,
            local_symbol TEXT,
            multiplier REAL DEFAULT 1,
            expiry TEXT,
            strike REAL,
            right TEXT,
            stop_loss REAL,
            take_profit REAL,
            trade_group_id INTEGER REFERENCES trade_groups(id),
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trade_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            underlying TEXT NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            collapsed INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS position_group_map (
            ibkr_position_id TEXT NOT NULL,
            trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
            PRIMARY KEY (ibkr_position_id, trade_group_id)
        );
        """
        self.conn.executescript(schema)
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self):
        alarm_columns = self._table_columns("alarms")
        if "created_at" not in alarm_columns:
            self.conn.execute("ALTER TABLE alarms ADD COLUMN created_at INTEGER")
        # D27.5: _upsert_position's ON CONFLICT(symbol, con_id) requires a
        # matching unique constraint — without it every position persist
        # raised OperationalError.
        self.conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "idx_positions_symbol_con_id ON positions(symbol, con_id)"
        )

    def _table_columns(self, table_name: str) -> set[str]:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    # ── Watchlist ──────────────────────────────────────────────────────────────

    def get_watchlist(self) -> list[tuple[str, str]]:
        """Return [(symbol, category)] ordered by sort_order."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT symbol, category FROM watchlist ORDER BY sort_order ASC")
        return [(row[0], row[1]) for row in cursor.fetchall()]

    def add_watchlist_symbol(self, symbol: str, category: str = "EQUITIES") -> None:
        """Append a symbol to the watchlist (case-insensitive, idempotent).

        If ``symbol`` is already present under any letter case the existing row
        is left untouched (its category and sort_order are preserved). Otherwise
        a new row is appended with ``sort_order = max(existing) + 1`` (0 when the
        table is empty).
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO watchlist (symbol, category, sort_order) "
            "SELECT ?, ?, (SELECT COALESCE(MAX(sort_order), -1) + 1 FROM watchlist) "
            "WHERE NOT EXISTS ("
            "SELECT 1 FROM watchlist WHERE symbol = ? COLLATE NOCASE"
            ")",
            (symbol, category, symbol),
        )
        self.conn.commit()

    def remove_watchlist_symbol(self, symbol: str) -> None:
        """Remove a symbol (case-insensitive) and renumber survivors 0..n-1.

        The remaining rows are renumbered contiguously preserving their relative
        order. Removing a symbol that is not present is a no-op.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM watchlist WHERE symbol = ? COLLATE NOCASE", (symbol,)
        )
        if cursor.rowcount == 0:
            self.conn.commit()
            return
        cursor.execute("SELECT rowid FROM watchlist ORDER BY sort_order ASC")
        rowids = [row[0] for row in cursor.fetchall()]
        for new_order, rowid in enumerate(rowids):
            cursor.execute(
                "UPDATE watchlist SET sort_order = ? WHERE rowid = ?",
                (new_order, rowid),
            )
        self.conn.commit()

    def set_watchlist(self, symbols: list[str], category: str = "EQUITIES", sort_order: list[str] | None = None) -> None:
        """Replace the whole watchlist.

        Args:
            symbols: list of symbol strings.
            category: category label for all symbols (default: 'EQUITIES').
            sort_order: optional list of sort-order strings (same length as symbols).
                If not provided, numeric indices are used.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM watchlist")
        if sort_order is None:
            sort_order = [str(i) for i in range(len(symbols))]
        elif len(sort_order) != len(symbols):
            raise ValueError("sort_order must have same length as symbols")
        cursor.executemany(
            "INSERT OR REPLACE INTO watchlist (symbol, category, sort_order) VALUES (?, ?, ?)",
            [(sym, category, sort_order[i]) for i, sym in enumerate(symbols)],
        )
        self.conn.commit()


# Main thread singleton
db = DB()
