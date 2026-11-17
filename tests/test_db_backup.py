"""Pre-drop backup and abort-on-failure for the D65 table drop (P23-T12).

AC-D65.18 (and the schema half of AC-D65.12/.13): ``backup_before_drop`` copies
the database, verifies the **copy** read-only (integrity check + the three
retired tables and their row counts) and raises on any failure, and
``DB._migrate_schema`` sits that call before a child-first
``position_group_map`` -> ``positions`` -> ``trade_groups`` drop so an
unverified database is never dropped.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

import data.db_backup as db_backup
from data.db_backup import BackupVerificationError, backup_before_drop

_REPO = Path(__file__).resolve().parent.parent

_NOW = datetime(2026, 11, 17, 14, 5, 9)

_RETIRED_TABLES = ("positions", "trade_groups", "position_group_map")

#: A pre-P23 database: the three retired tables, the unique index the D65
#: schema no longer creates, and rows in every table.
_PRE_D65_DDL = """
CREATE TABLE trade_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    underlying TEXT NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE positions (
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
CREATE UNIQUE INDEX idx_positions_symbol_con_id
    ON positions(symbol, con_id);
CREATE TABLE position_group_map (
    ibkr_position_id TEXT NOT NULL,
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
"""

_EXPECTED_COUNTS = {"positions": 2, "trade_groups": 1, "position_group_map": 1}


def _write_pre_d65_db(path: Path) -> Path:
    """Create a pre-D65 DB holding rows in all three retired tables."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_PRE_D65_DDL)
        conn.execute(
            "INSERT INTO trade_groups (id, name, strategy_type, underlying,"
            " stop_loss, take_profit, collapsed, created_at)"
            " VALUES (7, 'PCS', 'PCS', 'AAPL', 1.5, 2.5, 0, 1760000000)"
        )
        conn.executemany(
            "INSERT INTO positions (id, symbol, account, con_id, contract_type,"
            " qty, avg_cost, local_symbol, multiplier, expiry, strike, right,"
            " stop_loss, take_profit, trade_group_id, updated_at)"
            " VALUES (?, ?, 'DU123', ?, 'stock', 10.0, 40.0, ?, 1.0, NULL,"
            " NULL, NULL, 1.5, 2.5, 7, 1760000000)",
            [
                (1, "AAPL", 1, "AAPL"),
                (2, "MSFT", 2, "MSFT"),
            ],
        )
        conn.execute(
            "INSERT INTO position_group_map (ibkr_position_id, trade_group_id)"
            " VALUES ('DU123:1', 7)"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def _index_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }


def _route_db(monkeypatch, db_file: Path, user_dir: Path) -> None:
    """Point ``DB()`` at ``db_file`` and its backups at ``user_dir``."""
    from config import paths

    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    monkeypatch.setattr(paths, "_USER_APP_SUPPORT_DIR", user_dir)


# ---------------------------------------------------------------------------
# AC1 — the copy exists at the expected name and is verified read-only
# ---------------------------------------------------------------------------

def test_backup_before_drop_copies_and_verifies(tmp_path):
    """P23-T12-AC1: exact filename, read-only open, integrity, row counts."""
    source = _write_pre_d65_db(tmp_path / "pre_d65.sqlite3")
    backup_dir = tmp_path / "backups"

    result = backup_before_drop(source, now=_NOW, backup_dir=backup_dir)

    # The declared contract is ``-> Path``; the counts ride along with it.
    assert isinstance(result, Path)
    assert result == backup_dir / "charting_app_pre-D65_20261117-140509.sqlite3"
    assert result.parent == backup_dir
    assert result.exists(), "the verified copy must exist"
    assert result.stat().st_size == source.stat().st_size

    # The counts come from the copy, not from the source.
    assert result.row_counts == _EXPECTED_COUNTS

    # The copy opens read-only, passes integrity_check and holds every row.
    copy_conn = sqlite3.connect(f"{result.as_uri()}?mode=ro", uri=True)
    try:
        assert copy_conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        for table, expected in _EXPECTED_COUNTS.items():
            assert copy_conn.execute(
                f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == expected
        assert copy_conn.execute(
            "SELECT symbol, con_id FROM positions ORDER BY id").fetchall() == [
                ("AAPL", 1), ("MSFT", 2)]
        with pytest.raises(sqlite3.OperationalError):
            copy_conn.execute("DELETE FROM positions")
    finally:
        copy_conn.close()


def test_backup_defaults_to_user_backups_directory(tmp_path, monkeypatch):
    """P23-T12-AC1: no ``backup_dir`` -> ``get_user_data_path("backups")``."""
    source = _write_pre_d65_db(tmp_path / "pre_d65_default.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, source, user_dir)

    result = backup_before_drop(source, now=_NOW)

    assert result == (
        user_dir / "backups" / "charting_app_pre-D65_20261117-140509.sqlite3"
    )
    assert result.exists()


def test_backup_never_opens_the_application_db(tmp_path, monkeypatch):
    """P23-T12-AC1: the ESC-043 opt-in gate is untouched.

    With ``DB_PATH`` unset the app's ``DB()`` refuses to open the production
    database; the backup must not care, because it opens only the copy it made
    of the file it was handed.
    """
    from config import paths

    source = _write_pre_d65_db(tmp_path / "pre_d65_gate.sqlite3")
    monkeypatch.setattr(paths, "_DB_FILENAME", paths._DEFAULT_DB_FILENAME)
    monkeypatch.setattr(paths, "_app_db_opt_in", False)
    assert paths.uses_production_db() and not paths.is_production_db_opted_in()

    result = backup_before_drop(
        source, now=_NOW, backup_dir=tmp_path / "backups")

    assert result.exists()
    assert result.row_counts == _EXPECTED_COUNTS


# ---------------------------------------------------------------------------
# AC1/AC2 — every verification failure raises
# ---------------------------------------------------------------------------

def test_corrupt_copy_source_raises(tmp_path):
    """P23-T12-AC1/AC2: a copy that is not SQLite is rejected, not trusted."""
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"this is not a sqlite database" * 64)

    with pytest.raises(BackupVerificationError):
        backup_before_drop(corrupt, now=_NOW, backup_dir=tmp_path / "backups")


def test_missing_source_raises(tmp_path):
    """P23-T12-AC2: an unreadable source raises instead of dropping."""
    with pytest.raises(BackupVerificationError):
        backup_before_drop(
            tmp_path / "does_not_exist.sqlite3",
            now=_NOW,
            backup_dir=tmp_path / "backups",
        )


def test_source_missing_a_required_table_raises(tmp_path):
    """P23-T12-AC2: a copy without one of the three tables is unverified."""
    partial = tmp_path / "partial.sqlite3"
    conn = sqlite3.connect(str(partial))
    try:
        conn.execute(
            "CREATE TABLE trade_groups (id INTEGER PRIMARY KEY,"
            " name TEXT NOT NULL)"
        )
        conn.execute("CREATE TABLE positions (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(BackupVerificationError, match="position_group_map"):
        backup_before_drop(partial, now=_NOW, backup_dir=tmp_path / "backups")


# ---------------------------------------------------------------------------
# AC2 — the migration aborts when the backup fails
# ---------------------------------------------------------------------------

def test_migrate_schema_aborts_drop_when_backup_fails(tmp_path, monkeypatch):
    """P23-T12-AC2: backup raises -> no DROP runs, all tables and rows remain."""
    legacy = _write_pre_d65_db(tmp_path / "abort.sqlite3")
    _route_db(monkeypatch, legacy, tmp_path / "userdata")

    def _boom(*args, **kwargs):
        raise BackupVerificationError("injected: verification failed")

    monkeypatch.setattr(db_backup, "backup_before_drop", _boom)

    from data.db import DB

    with pytest.raises(BackupVerificationError):
        DB()

    # Inspect the file directly: nothing was dropped.
    conn = sqlite3.connect(str(legacy))
    try:
        assert set(_RETIRED_TABLES) <= _table_names(conn)
        assert "idx_positions_symbol_con_id" in _index_names(conn)
        assert conn.execute("SELECT COUNT(*) FROM positions").fetchone() == (2,)
        assert conn.execute(
            "SELECT COUNT(*) FROM trade_groups").fetchone() == (1,)
        assert conn.execute(
            "SELECT COUNT(*) FROM position_group_map").fetchone() == (1,)
    finally:
        conn.close()


def test_migrate_schema_skips_backup_on_fresh_db(tmp_path, monkeypatch):
    """P23-T12-AC2: a fresh DB has no retired tables, so no backup is taken."""
    fresh = tmp_path / "fresh.sqlite3"
    _route_db(monkeypatch, fresh, tmp_path / "userdata")

    def _unexpected(*args, **kwargs):
        raise AssertionError("a fresh database must not trigger a backup")

    monkeypatch.setattr(db_backup, "backup_before_drop", _unexpected)

    from data.db import DB

    db = DB()
    try:
        assert not set(_RETIRED_TABLES) & _table_names(db.conn)
        assert "idx_positions_symbol_con_id" not in _index_names(db.conn)
    finally:
        db.conn.close()


def test_migrate_schema_drops_child_first_and_only_once(tmp_path, monkeypatch):
    """P23-T12-AC2: sequential drop of all three tables must be interrupted
    while FK children still exist.
    """
    legacy = _write_pre_d65_db(tmp_path / "order.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, legacy, user_dir)

    statements: list[str] = []
    real_connect = sqlite3.connect

    def _tracing_connect(database, *args, **kwargs):
        conn = real_connect(database, *args, **kwargs)
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(sqlite3, "connect", _tracing_connect)

    from data.db import DB

    first = DB()
    try:
        drops = [
            sql.strip()
            for sql in statements
            if sql.strip().startswith("DROP TABLE")
        ]
        retired_drops = [sql for sql in drops if any(
            table in sql for table in _RETIRED_TABLES)]
        assert retired_drops == [
            "DROP TABLE IF EXISTS position_group_map",
            "DROP TABLE IF EXISTS positions",
            "DROP TABLE IF EXISTS trade_groups",
        ], f"drop order is not child-first: {retired_drops!r}"

        assert not set(_RETIRED_TABLES) & _table_names(first.conn)
        assert "idx_positions_symbol_con_id" not in _index_names(first.conn)
    finally:
        first.conn.close()

    backups = sorted((user_dir / "backups").glob("charting_app_pre-D65_*.sqlite3"))
    assert len(backups) == 1, f"expected one pre-drop backup, got {backups!r}"

    # A second open is a no-op: no DROP statement, no second backup.
    statements.clear()
    second = DB()
    try:
        assert not set(_RETIRED_TABLES) & _table_names(second.conn)
    finally:
        second.conn.close()
    assert not [sql for sql in statements if "IF EXISTS position_group_map" in sql]
    assert not [sql for sql in statements if "IF EXISTS trade_groups" in sql]
    assert len(sorted(
        (user_dir / "backups").glob("charting_app_pre-D65_*.sqlite3"))) == 1
