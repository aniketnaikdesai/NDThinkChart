"""D96 / D100 — a persisted write is one transaction over one declaration.

Covers AC-D96.1–AC-D96.3, AC-D100.1, AC-D100.2 and AC-P29-01-BOOL for
``StudyStore.save`` and ``DrawingStore.update_group``.

Instruments: the shared temp DB from ``tests/conftest.py``,
``db.conn.in_transaction`` (a failure must leave no transaction pending) and
``db.conn.set_trace_callback`` (a rejected field must execute no SQL at all).
Every fixture seeds through a store method, so the fixture's rows are
committed before each call under test.
"""

import json
import sqlite3

import pytest

from data.db import db
from data.drawing_store import DrawingStore
from data.study_store import StudyStore

#: One dedicated symbol for the studies cases and the group cases.
SYMBOL = "ATOMIC1"
#: The "unrelated write" lands on the same connection and the same table,
#: under a different symbol, so a resurrected DELETE is visible.
OTHER_SYMBOL = "ATOMIC_OTHER"

STUDIES_A = [
    {"type": "sma", "enabled": True, "params": {"period": 20}},
    {"type": "rsi", "enabled": False, "params": {"period": 14}},
]
STUDIES_B = [
    {"type": "ema", "enabled": True, "params": {"period": 9}},
]


def _wipe() -> None:
    cur = db.conn.cursor()
    cur.execute("DELETE FROM drawings WHERE symbol=?", (SYMBOL,))
    cur.execute("DELETE FROM drawing_groups WHERE symbol=?", (SYMBOL,))
    cur.execute(
        "DELETE FROM studies WHERE symbol IN (?, ?)", (SYMBOL, OTHER_SYMBOL)
    )
    db.conn.commit()


@pytest.fixture(autouse=True)
def isolated_rows():
    """The dedicated rows only; committed before and after every case."""
    _wipe()
    assert db.conn.in_transaction is False
    yield
    _wipe()


def _expected(studies: list[dict]) -> list[dict]:
    """What ``StudyStore.load`` returns for a just-saved set."""
    return [
        {
            "type": study["type"],
            "enabled": bool(study.get("enabled")),
            "params": dict(study.get("params", {})),
        }
        for study in studies
    ]


def _snapshot() -> str:
    """Byte-identical comparison form for the symbol's stored studies."""
    return json.dumps(StudyStore.load(SYMBOL), sort_keys=True)


def _row_count() -> int:
    cur = db.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM studies WHERE symbol=?", (SYMBOL,))
    return int(cur.fetchone()[0])


def _unrelated_write() -> None:
    """A committed write on the shared connection, for the other symbol."""
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO studies (symbol, type, enabled, params) VALUES (?, ?, ?, ?)",
        (OTHER_SYMBOL, "sma", 1, json.dumps({"period": 20})),
    )
    db.conn.commit()
    assert db.conn.in_transaction is False


def _group_row(gid: int):
    cur = db.conn.cursor()
    cur.execute(
        "SELECT name, color, visible, locked FROM drawing_groups WHERE id=?",
        (gid,),
    )
    return cur.fetchone()


class TestSaveAtomicity:
    def test_p29_t1_01_serialization_failure_leaves_rows_and_no_transaction(self):
        StudyStore.save(SYMBOL, STUDIES_A)
        assert db.conn.in_transaction is False
        before = _snapshot()
        assert json.loads(before) == _expected(STUDIES_A)

        with pytest.raises(TypeError):
            StudyStore.save(
                SYMBOL,
                [{"type": "sma", "enabled": True, "params": {"bad": object()}}],
            )

        assert db.conn.in_transaction is False
        assert _snapshot() == before

        _unrelated_write()
        assert _snapshot() == before
        assert _row_count() == len(STUDIES_A)

    def test_p29_t1_02_db_error_between_delete_and_insert_rolls_back(self):
        StudyStore.save(SYMBOL, STUDIES_A)
        assert db.conn.in_transaction is False
        before = _snapshot()

        # studies.type is NOT NULL: this row fails inside the executemany,
        # after the DELETE has run.
        with pytest.raises(sqlite3.IntegrityError):
            StudyStore.save(SYMBOL, [{"type": None, "enabled": True, "params": {}}])

        assert db.conn.in_transaction is False
        assert _snapshot() == before

        _unrelated_write()
        assert _snapshot() == before
        assert _row_count() == len(STUDIES_A)

    def test_p29_t1_03_first_write_on_connection_seed_survives_and_retry_lands(self):
        # The only prior writes on the connection were committed fixture seeds.
        StudyStore.save(SYMBOL, STUDIES_A)
        before = _snapshot()
        assert db.conn.in_transaction is False

        with pytest.raises(TypeError):
            StudyStore.save(
                SYMBOL,
                [{"type": "sma", "enabled": True, "params": {"bad": object()}}],
            )

        assert db.conn.in_transaction is False
        assert _snapshot() == before

        StudyStore.save(SYMBOL, STUDIES_B)
        assert db.conn.in_transaction is False
        assert _row_count() == len(STUDIES_B)
        assert StudyStore.load(SYMBOL) == _expected(STUDIES_B)

    @pytest.mark.parametrize(
        "first, second",
        [
            (STUDIES_A, None),
            (STUDIES_A, STUDIES_B),
        ],
    )
    def test_p29_t1_04_valid_save_replaces_exactly(self, first, second):
        StudyStore.save(SYMBOL, first)
        assert _row_count() == len(first)
        assert StudyStore.load(SYMBOL) == _expected(first)
        assert db.conn.in_transaction is False

        if second is not None:
            StudyStore.save(SYMBOL, second)
            assert _row_count() == len(second)
            assert StudyStore.load(SYMBOL) == _expected(second)
            assert db.conn.in_transaction is False

    def test_p29_t1_05_empty_save_removes_and_commits(self):
        StudyStore.save(SYMBOL, STUDIES_A)
        assert _row_count() == len(STUDIES_A)

        StudyStore.save(SYMBOL, [])

        assert StudyStore.load(SYMBOL) == []
        assert _row_count() == 0
        assert db.conn.in_transaction is False


class TestUpdateGroupUnknownFields:
    @pytest.mark.parametrize(
        "fields",
        [
            {"visible": False, "bogus": 1},
            {"bogus": 1},
        ],
    )
    def test_p29_t1_06_unknown_field_raises_before_any_sql(self, fields):
        gid = DrawingStore.create_group(SYMBOL, "G", 1, "#38bdf8")
        assert db.conn.in_transaction is False
        before = _group_row(gid)

        records: list[str] = []
        db.conn.set_trace_callback(records.append)
        try:
            records.clear()
            with pytest.raises(ValueError) as excinfo:
                DrawingStore.update_group(gid, **fields)
            assert "bogus" in str(excinfo.value)
            # No cursor was created, so no statement reached SQLite.
            assert records == []
            assert db.conn.in_transaction is False
            assert _group_row(gid) == before
        finally:
            db.conn.set_trace_callback(None)

        _unrelated_write()
        assert _group_row(gid) == before
        assert db.conn.in_transaction is False

        # The same call after an unrelated commit behaves identically.
        records_after: list[str] = []
        db.conn.set_trace_callback(records_after.append)
        try:
            with pytest.raises(ValueError) as excinfo:
                DrawingStore.update_group(gid, **fields)
            assert "bogus" in str(excinfo.value)
            assert records_after == []
            assert db.conn.in_transaction is False
        finally:
            db.conn.set_trace_callback(None)
        assert _group_row(gid) == before


class TestUpdateGroupOneDeclaration:
    @pytest.mark.parametrize(
        "fields, changed",
        [
            ({"visible": False}, {"visible": 0}),
            ({"visible": False, "locked": True}, {"visible": 0, "locked": 1}),
            ({"color": "#123456"}, {"color": "#123456"}),
            ({"name": "renamed"}, {"name": "renamed"}),
            ({}, {}),
        ],
    )
    def test_p29_t1_07_exactly_the_named_columns_change(self, fields, changed):
        gid = DrawingStore.create_group(SYMBOL, "G", 1, "#38bdf8")
        assert db.conn.in_transaction is False
        before = _group_row(gid)

        records: list[str] = []
        db.conn.set_trace_callback(records.append)
        try:
            records.clear()
            DrawingStore.update_group(gid, **fields)
        finally:
            db.conn.set_trace_callback(None)

        after = _group_row(gid)
        expected = list(before)
        for key, value in changed.items():
            expected[("name", "color", "visible", "locked").index(key)] = value
        assert tuple(expected) == after
        assert db.conn.in_transaction is False

        updates = [s for s in records if s.startswith("UPDATE drawing_groups")]
        if not fields:
            # Today's no-op: nothing to write, so nothing is written.
            assert updates == []
            return

        assert len(updates) == 1
        stmt = updates[0]
        # set_trace_callback reports the statement post-expansion: every
        # placeholder was bound, and a binding-count mismatch raises
        # ProgrammingError before SQLite executes anything (so no UPDATE
        # would appear). No residual "?" therefore means one value per
        # placeholder.
        assert "?" not in stmt
        assignments = stmt.split(" SET ", 1)[1].split(" WHERE ", 1)[0]
        columns = [part.split("=", 1)[0].strip() for part in assignments.split(",")]
        assert columns == list(fields)


class TestUpdateGroupBoolRule:
    def test_p29_t1_08_bool_coerces_for_flags_and_is_rejected_for_text(self):
        gid = DrawingStore.create_group(SYMBOL, "G", 1, "#38bdf8")

        DrawingStore.update_group(gid, visible=True)
        row = _group_row(gid)
        assert row[2] == 1
        assert DrawingStore.groups_for_symbol(SYMBOL)[0].visible is True

        for key in ("name", "color"):
            before = _group_row(gid)
            records: list[str] = []
            db.conn.set_trace_callback(records.append)
            try:
                records.clear()
                with pytest.raises(ValueError) as excinfo:
                    DrawingStore.update_group(gid, **{key: True})
                assert key in str(excinfo.value)
                assert "bool" in str(excinfo.value)
                assert records == []
                assert db.conn.in_transaction is False
            finally:
                db.conn.set_trace_callback(None)
            assert _group_row(gid) == before
