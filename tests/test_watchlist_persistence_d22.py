"""D22-01: watchlist add/remove persistence helpers (data/db.py).

Pre-fix these tests are red (``DB.add_watchlist_symbol`` /
``remove_watchlist_symbol`` do not exist); post-fix they are green. Each test
runs against a throwaway SQLite file so the real user DB is never touched.
"""

import pytest

import config.paths as paths


def _fresh_db(tmp_path, monkeypatch):
    """Build a DB() pointed at a per-test temp file (never the real user DB)."""
    db_file = tmp_path / "watchlist_persistence_d22.sqlite3"
    # get_db_path() reads the module-global _DB_FILENAME at call time; an
    # absolute path replaces the user-app-support base when joined.
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    from data.db import DB

    fresh = DB()
    fresh.conn.execute("DELETE FROM watchlist")
    fresh.conn.commit()
    return fresh


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    yield db
    db.conn.close()


def _sort_order(db, symbol):
    row = db.conn.execute(
        "SELECT sort_order FROM watchlist WHERE symbol = ? COLLATE NOCASE",
        (symbol,),
    ).fetchone()
    return None if row is None else row[0]


def test_D22_01_T01_add_appends_with_next_sort_order(fresh_db):
    """AC-D22.1.1: sequential adds append with contiguous sort_order."""
    db = fresh_db
    db.add_watchlist_symbol("AAPL")
    assert db.get_watchlist() == [("AAPL", "EQUITIES")]
    assert _sort_order(db, "AAPL") == 0

    db.add_watchlist_symbol("TSLA")
    assert _sort_order(db, "TSLA") == 1
    assert db.get_watchlist() == [("AAPL", "EQUITIES"), ("TSLA", "EQUITIES")]


def test_D22_01_T02_case_variant_add_is_idempotent(fresh_db):
    """AC-D22.1.2: a case-variant add preserves the existing row."""
    db = fresh_db
    db.conn.execute(
        "INSERT INTO watchlist (symbol, category, sort_order) "
        "VALUES ('AAPL', 'FUTURES', 7)"
    )
    db.conn.commit()

    db.add_watchlist_symbol("aapl")

    rows = db.conn.execute(
        "SELECT symbol, category, sort_order FROM watchlist"
    ).fetchall()
    assert len(rows) == 1, f"expected no duplicate row, got {rows}"
    assert rows[0] == ("AAPL", "FUTURES", 7)


def test_D22_01_T03_remove_case_insensitive_renumbers(fresh_db):
    """AC-D22.1.3: remove is case-insensitive and renumbers 0..n-1."""
    db = fresh_db
    db.set_watchlist(["AAPL", "TSLA", "SPY"])

    db.remove_watchlist_symbol("tsla")

    rows = db.conn.execute(
        "SELECT symbol, sort_order FROM watchlist ORDER BY sort_order ASC"
    ).fetchall()
    assert rows == [("AAPL", 0), ("SPY", 1)]
    assert db.get_watchlist() == [("AAPL", "EQUITIES"), ("SPY", "EQUITIES")]

    # Removing an absent symbol is a no-op leaving the table unchanged.
    before = db.conn.execute(
        "SELECT symbol, sort_order FROM watchlist ORDER BY sort_order ASC"
    ).fetchall()
    db.remove_watchlist_symbol("MSFT")
    after = db.conn.execute(
        "SELECT symbol, sort_order FROM watchlist ORDER BY sort_order ASC"
    ).fetchall()
    assert after == before


def test_D22_01_T04_existing_api_unchanged(fresh_db):
    """AC-D22.1.4: get_watchlist ordering / set_watchlist replace-all unchanged."""
    db = fresh_db
    db.set_watchlist(["AAPL", "TSLA"])
    assert db.get_watchlist() == [("AAPL", "EQUITIES"), ("TSLA", "EQUITIES")]

    # Replace-all drops the previous contents.
    db.set_watchlist(["SPY"], category="FUTURES")
    assert db.get_watchlist() == [("SPY", "FUTURES")]

    # The new helper coexists with set_watchlist without disturbing it.
    db.add_watchlist_symbol("QQQ")
    assert db.get_watchlist() == [("SPY", "FUTURES"), ("QQQ", "EQUITIES")]

    # An explicit sort_order list is still honoured verbatim.
    db.set_watchlist(["A", "B"], sort_order=["5", "1"])
    assert db.get_watchlist() == [("B", "EQUITIES"), ("A", "EQUITIES")]
