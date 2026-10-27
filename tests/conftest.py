"""Shared fixtures. Deterministic candle datasets for pure-logic services."""

import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Per-process test DB (S12; ESC-024/ESC-025). The old harness used ONE fixed
# path under ``tempfile.gettempdir()`` and ``os.remove()``'d it at import, so
# every concurrent pytest process opened, deleted and committed against the same
# file -- surfacing as ``sqlite3.OperationalError: attempt to write a readonly
# database`` (SQLITE_READONLY_DBMOVED) in the autouse teardown while the test
# bodies passed. Each process now gets its own temp directory (``mkdtemp`` is
# unique even for same-named callers) whose name carries its PID, and nothing is
# ever removed: a process must not delete a path it did not create.
_TEST_DB_DIR = tempfile.mkdtemp(prefix=f"ndtc_test_db_{os.getpid()}_")
_TEST_DB_PATH = os.path.join(_TEST_DB_DIR, "test.sqlite3")
os.environ["DB_PATH"] = _TEST_DB_PATH

import pytest

from data.models import Bar


BASE_TS = 1_700_000_000
DAY = 86_400


def _bar(i: int, value: float, ts: int | None = None, volume: float = 1000.0) -> Bar:
    return Bar(
        symbol="TEST",
        timeframe="5 mins",
        ts=ts if ts is not None else BASE_TS + i * 60,
        open=value,
        high=value + 0.5,
        low=value - 0.5,
        close=value,
        volume=volume,
    )


@pytest.fixture
def sample_bars() -> list[Bar]:
    """200 one-minute bars with monotonically rising closes (no gaps)."""
    return [_bar(i, 100 + i * 0.1) for i in range(200)]


@pytest.fixture
def impulse_bars() -> list[Bar]:
    """Deterministic alternating impulse dataset rich enough for ICT concepts.

    Builds swings: sharp displacement moves, small retracements, and a couple
    of fair-value-gap-sized gaps between closes.
    """
    bars = []
    base = 100.0
    ts = BASE_TS
    for i in range(300):
        phase = (i // 20) % 4
        if phase == 0:
            o = base
            c = base + 6.0
        elif phase == 1:
            o = base + 6.0
            c = base + 1.0
        elif phase == 2:
            o = base + 1.0
            c = base - 3.0
        else:
            o = base - 3.0
            c = base + 2.0
        h, l = max(o, c) + 0.5, min(o, c) - 0.5
        bars.append(Bar("TEST", "5 mins", ts, o, h, l, c, 1000.0))
        base = c
        ts += 60
    return bars


@pytest.fixture
def gap_bars() -> list[Bar]:
    """Two sessions with an up gap, plus a bar that fills it back in.

    Day 1 closes at 103.5, day 2 opens at 110.0 (up gap). A following bar
    trades down to 99.0, which fills the gap.
    """
    day1 = [_bar(0, 100.0 + i * 0.5, ts=BASE_TS + i * 300) for i in range(8)]
    day2_open = BASE_TS + DAY
    day2 = [
        Bar("TEST", "5 mins", day2_open, 110.0, 110.5, 109.5, 110.0, 1000.0),
        Bar("TEST", "5 mins", day2_open + 300, 110.0, 111.0, 99.0, 108.0, 1000.0),
        Bar("TEST", "5 mins", day2_open + 600, 108.0, 108.5, 107.5, 108.0, 1000.0),
    ]
    return day1 + day2


@pytest.fixture(scope="session")
def qapp():
    """Single offscreen QApplication for the whole test session."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _isolate_test_db():
    """Hermetic DB: no test sees another test's rows (D28.6).

    The suite shares one SQLite file per process; a test that writes
    bars/alarms/drawings/positions without cleanup would otherwise leak
    rows into later tests (order-dependent flakes). Wipe after each test.
    """
    yield
    from data.db import db

    cur = db.conn.cursor()
    for table in (
        "position_group_map",  # FK child first
        "bars", "watchlist", "alarms", "zones", "drawing_groups",
        "drawings", "studies", "popouts", "positions", "trade_groups",
        "volume_baseline",  # D39
    ):
        cur.execute(f"DELETE FROM {table}")
    db.conn.commit()


@pytest.fixture(autouse=True)
def _reset_pacing_state():
    """Hermetic pacing: every test starts with a full realtime budget.
    Without this, the global singleton would accumulate slots across the
    suite and later tests would trip PacingExceeded."""
    from ibkr import pacing as pacing_mod
    pacing_mod.pacing_manager.reset_for_tests()
    yield
    pacing_mod.pacing_manager.reset_for_tests()
