"""D28.4 (4b-5) — BarCache retention policy per (symbol, timeframe).

The SQLite bar cache must stay bounded: after each backfill wave the
cache keeps the newest RETENTION_BARS per (symbol, timeframe) and drops
older rows. Other symbols/timeframes are untouched.
"""
from data.bar_cache import BarCache, RETENTION_BARS
from data.models import Bar

BASE = 1_760_000_000


def _bars(symbol, tf, n, base=BASE):
    return [Bar(symbol, tf, base + i * 300,
                100.0, 101.0, 99.0, 100.5, 1000.0) for i in range(n)]


def _count(symbol, tf):
    return len(BarCache.get_bars(symbol, tf))


def test_prune_keeps_newest_retention_bars():
    BarCache.save_bars(_bars("RET1", "5 mins", RETENTION_BARS + 1000))
    assert _count("RET1", "5 mins") == RETENTION_BARS + 1000
    deleted = BarCache.prune("RET1", "5 mins")
    assert deleted == 1000
    kept = BarCache.get_bars("RET1", "5 mins")
    assert len(kept) == RETENTION_BARS
    assert kept[0].ts == BASE + 1000 * 300, "the oldest 1000 must be dropped"
    assert kept[-1].ts == BASE + (RETENTION_BARS + 999) * 300


def test_prune_noop_when_under_retention():
    BarCache.save_bars(_bars("RET2", "5 mins", 100))
    assert BarCache.prune("RET2", "5 mins") == 0
    assert _count("RET2", "5 mins") == 100


def test_prune_scoped_per_symbol_timeframe():
    BarCache.save_bars(_bars("RET3", "5 mins", RETENTION_BARS + 500))
    BarCache.save_bars(_bars("RET3", "1 day", RETENTION_BARS + 500))
    BarCache.save_bars(_bars("OTHER", "5 mins", RETENTION_BARS + 500))
    BarCache.prune("RET3", "5 mins")
    assert _count("RET3", "5 mins") == RETENTION_BARS
    assert _count("RET3", "1 day") == RETENTION_BARS + 500
    assert _count("OTHER", "5 mins") == RETENTION_BARS + 500


def test_prune_custom_keep():
    BarCache.save_bars(_bars("RET4", "5 mins", 1000))
    assert BarCache.prune("RET4", "5 mins", keep=100) == 900
    assert _count("RET4", "5 mins") == 100
