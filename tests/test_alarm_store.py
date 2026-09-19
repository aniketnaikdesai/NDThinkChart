"""Tests for data/alarm_store.py CRUD and updates."""

import pytest

from data.alarm_store import AlarmStore
from data.db import db
from data.models import Alarm


@pytest.fixture(autouse=True)
def clean_alarms():
    db.conn.execute("DELETE FROM alarms WHERE symbol='TEST'")
    db.conn.commit()
    yield
    db.conn.execute("DELETE FROM alarms WHERE symbol='TEST'")
    db.conn.commit()


def add(price=100.0, direction="cross_either", sound=True, note=""):
    alarm = Alarm(id=None, symbol="TEST", price=price, direction=direction,
                  sound=sound, note=note)
    alarm.id = AlarmStore.add(alarm)
    return alarm


class TestCrud:
    def test_add_and_load_roundtrip(self):
        add(price=101.5, direction="cross_above", note="breakout")
        loaded = AlarmStore.load("TEST")
        assert len(loaded) == 1
        assert loaded[0].price == 101.5
        assert loaded[0].direction == "cross_above"
        assert loaded[0].note == "breakout"
        assert loaded[0].active is True

    def test_load_orders_by_price_desc(self):
        add(price=90.0)
        add(price=110.0)
        add(price=100.0)
        assert [a.price for a in AlarmStore.load("TEST")] == [110.0, 100.0, 90.0]

    def test_mark_triggered(self):
        alarm = add()
        AlarmStore.mark_triggered(alarm.id)
        loaded = AlarmStore.load("TEST")[0]
        assert loaded.triggered is True
        assert loaded.triggered_at is not None

    def test_rearm_clears_trigger(self):
        alarm = add()
        AlarmStore.mark_triggered(alarm.id)
        AlarmStore.rearm(alarm.id)
        loaded = AlarmStore.load("TEST")[0]
        assert loaded.triggered is False
        assert loaded.triggered_at is None
        assert loaded.active is True

    def test_delete(self):
        alarm = add()
        AlarmStore.delete(alarm.id)
        assert AlarmStore.load("TEST") == []


class TestUpdate:
    def test_set_price(self):
        alarm = add(price=100.0)
        AlarmStore.set_price(alarm.id, 104.25)
        assert AlarmStore.load("TEST")[0].price == 104.25

    def test_set_sound(self):
        alarm = add(sound=True)
        AlarmStore.set_sound(alarm.id, False)
        assert AlarmStore.load("TEST")[0].sound is False

    def test_update_ignores_unknown_fields(self):
        alarm = add(price=100.0)
        AlarmStore.update(alarm.id, price=99.0, bogus="x")
        loaded = AlarmStore.load("TEST")[0]
        assert loaded.price == 99.0

    def test_update_no_fields_is_noop(self):
        alarm = add(price=100.0)
        AlarmStore.update(alarm.id)
        assert AlarmStore.load("TEST")[0].price == 100.0
