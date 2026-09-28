"""Schema regression tests for data/db.py (ESC-001 / DOC-3).

Guards that a fresh DB() creates the full table set and that ``_init_schema``
is defined exactly once in data/db.py.
"""

import ast
from pathlib import Path

import config.paths as paths

# ESC-001: the complete set of tables a fresh database must contain.
EXPECTED_TABLES = {
    "bars",
    "watchlist",
    "alarms",
    "zones",
    "drawing_groups",
    "drawings",
    "studies",
    "positions",
    "trade_groups",
    "position_group_map",
}

# data/db.py lives one directory above this test file.
_DB_SOURCE = Path(__file__).resolve().parent.parent / "data" / "db.py"


def test_fresh_db_creates_full_table_set(tmp_path, monkeypatch):
    """T26-T01: a fresh DB() against a temp path creates all ten tables."""
    db_file = tmp_path / "fresh_schema_test.sqlite3"
    # Route the DB at a throwaway path so nothing touches the shared test DB.
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))

    from data.db import DB

    fresh = DB()
    try:
        rows = fresh.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        tables = {row[0] for row in rows}
    finally:
        fresh.conn.close()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"missing tables: {sorted(missing)}"
    assert EXPECTED_TABLES <= tables


def test_init_schema_defined_once():
    """T26-T02: data/db.py defines _init_schema exactly once."""
    source = _DB_SOURCE.read_text()
    tree = ast.parse(source)
    count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_init_schema"
    )
    assert count == 1, f"expected 1 _init_schema definition, found {count}"
