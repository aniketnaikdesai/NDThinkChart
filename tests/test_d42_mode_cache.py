"""D42 / S16 — mode-aware cache and migration suite (AC-D16.9).

The ``bars`` cache gained ``ext_hours INTEGER NOT NULL DEFAULT 1`` and its key
became ``(symbol, timeframe, ext_hours, ts)`` so a mode switch can never read
the other mode's bars as coverage. This suite pins the two normative halves of
that change:

* ``P2-T21-T11`` — the legacy -> mode-aware migration preserves every legacy
  row and tags it ``ext_hours = 1`` (ETH, the app default), idempotently across
  re-opens; and per-mode reads return only their own mode's bars.
* ``P2-T21-T21`` — no cross-contamination in either direction: writing ETH bars
  and reading RTH returns empty, and writing RTH bars and reading ETH returns
  empty.

The tests drive the real ``data/db.py`` migration path and the real
``data/bar_cache.py`` reads/writes, on a throwaway on-disk DB, so they exercise
the shipped key semantics rather than a mock.
"""

import sqlite3

import pytest

from config import paths
from data.bar_cache import BarCache
from data.db import DB
from data.models import Bar


#: Legacy (pre-D42) rows: (symbol, timeframe, ts, open, high, low, close, volume).
LEGACY_ROWS = [
    ("SPY", "5 mins", 1_700_000_000, 100.0, 101.0, 99.0, 100.5, 1000.0),
    ("SPY", "5 mins", 1_700_000_300, 100.5, 102.0, 100.0, 101.5, 1200.0),
    ("QQQ", "1 min", 1_700_000_600, 50.0, 50.5, 49.5, 50.2, 500.0),
]


def _seed_legacy_bars(path):
    """Create a pre-D42 ``bars`` table (no ``ext_hours``) with seeded rows."""
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE bars ("
        "symbol TEXT NOT NULL, "
        "timeframe TEXT NOT NULL, "
        "ts INTEGER NOT NULL, "
        "open REAL, high REAL, low REAL, close REAL, volume REAL, "
        "PRIMARY KEY (symbol, timeframe, ts))"
    )
    conn.executemany(
        "INSERT INTO bars (symbol, timeframe, ts, open, high, low, close, volume) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        LEGACY_ROWS,
    )
    conn.commit()
    conn.close()


def _all_rows(conn):
    """Every ``bars`` row, including its ``ext_hours`` tag, in a stable order."""
    return conn.execute(
        "SELECT symbol, timeframe, ext_hours, ts, open, high, low, close, volume "
        "FROM bars ORDER BY symbol, timeframe, ts"
    ).fetchall()


def _bar_key(bar):
    return (bar.symbol, bar.timeframe, bar.ts, bar.open, bar.high, bar.low,
            bar.close, bar.volume)


@pytest.fixture
def legacy_db(tmp_path, monkeypatch):
    """Open a seeded pre-D42 DB through the real ``DB()`` migration path."""
    db_path = tmp_path / "legacy_cache.db"
    _seed_legacy_bars(db_path)
    monkeypatch.setattr(paths, "get_db_path", lambda: db_path)
    return DB()


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """A fresh (already mode-aware) DB wired into ``BarCache``."""
    db_path = tmp_path / "fresh_cache.db"
    monkeypatch.setattr(paths, "get_db_path", lambda: db_path)
    fresh = DB()
    monkeypatch.setattr("data.bar_cache.db", fresh)
    return fresh


def test_p2_t21_t11_migration_preserves_and_tags_every_row(legacy_db, monkeypatch):
    """AC1 (S16 / AC-D16.9): migration preserves all rows, tagged ext_hours = 1."""
    columns = {row[1] for row in legacy_db.conn.execute("PRAGMA table_info(bars)")}
    assert "ext_hours" in columns, "migrated bars table must carry ext_hours"

    rows = _all_rows(legacy_db.conn)

    # every legacy row preserved (count) and tagged ext_hours = 1 (ETH default)
    assert len(rows) == len(LEGACY_ROWS)
    assert all(row[2] == 1 for row in rows)

    # and preserved *verbatim* — no value drift through the rebuild
    expected = sorted(LEGACY_ROWS, key=lambda r: (r[0], r[1], r[2]))
    got = [(r[0], r[1], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows]
    assert got == expected

    # idempotent: a second open neither duplicates nor drops rows
    monkeypatch.setattr(paths, "get_db_path", lambda: legacy_db.db_path)
    reopened = DB()
    assert _all_rows(reopened.conn) == rows


def test_p2_t21_t11_per_mode_reads_return_only_their_own_mode(
    legacy_db, monkeypatch
):
    """AC1: per-mode reads return only their own mode's bars."""
    monkeypatch.setattr("data.bar_cache.db", legacy_db)

    eth = BarCache.get_bars("SPY", "5 mins", ext_hours=True)
    assert [b.ts for b in eth] == [1_700_000_000, 1_700_000_300]
    assert [b.close for b in eth] == [100.5, 101.5]

    # the legacy rows were tagged ETH, so the RTH key is empty
    assert BarCache.get_bars("SPY", "5 mins", ext_hours=False) == []


def test_p2_t21_t21_no_cross_contamination(fresh_db):
    """AC2: ETH write -> RTH read empty; RTH write -> ETH read empty."""
    eth_bar = Bar("SPY", "5 mins", 1_700_000_000, 100.0, 101.0, 99.0, 100.5, 1000.0)
    BarCache.save_bars([eth_bar], ext_hours=True)

    # ETH read sees its own bar; the RTH read is untouched by the ETH write
    assert [_bar_key(b) for b in BarCache.get_bars("SPY", "5 mins", ext_hours=True)] \
        == [_bar_key(eth_bar)]
    assert BarCache.get_bars("SPY", "5 mins", ext_hours=False) == []

    # now write an RTH bar at a different timestamp
    rth_bar = Bar("SPY", "5 mins", 1_700_000_300, 101.0, 102.0, 100.0, 101.5, 1100.0)
    BarCache.save_bars([rth_bar], ext_hours=False)

    # RTH read sees only the RTH bar; the ETH read is not contaminated by it
    assert [_bar_key(b) for b in BarCache.get_bars("SPY", "5 mins", ext_hours=False)] \
        == [_bar_key(rth_bar)]
    assert [_bar_key(b) for b in BarCache.get_bars("SPY", "5 mins", ext_hours=True)] \
        == [_bar_key(eth_bar)]


def test_p2_t21_t21_default_mode_is_eth(fresh_db):
    """AC2 (guard): the app-default read/write mode is ETH, and stays isolated."""
    default_bar = Bar("SPY", "5 mins", 1_700_000_000, 100.0, 101.0, 99.0, 100.5, 1000.0)
    # no explicit ext_hours -> app default (True / ETH)
    BarCache.save_bars([default_bar])
    assert [_bar_key(b) for b in BarCache.get_bars("SPY", "5 mins")] \
        == [_bar_key(default_bar)]
    assert BarCache.get_bars("SPY", "5 mins", ext_hours=False) == []
