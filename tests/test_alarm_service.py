"""Tests for services/alarm_service.py — crossing logic."""

import pytest

from data.models import Alarm
from services.alarm_service import evaluate_alarms


def make_alarm(price: float, direction: str, active=True, triggered=False) -> Alarm:
    return Alarm(id=None, symbol="TEST", price=price, direction=direction,
                 active=active, triggered=triggered)


class TestCrossAbove:
    def test_triggers_on_up_cross(self):
        alarms = [make_alarm(11.0, "cross_above")]
        triggered = evaluate_alarms(10.0, 12.0, alarms)
        assert triggered == alarms

    def test_no_trigger_when_stays_below(self):
        alarms = [make_alarm(11.0, "cross_above")]
        assert evaluate_alarms(10.0, 10.5, alarms) == []

    def test_no_trigger_when_crossing_down(self):
        alarm = make_alarm(11.0, "cross_above")
        assert evaluate_alarms(12.0, 11.0, [alarm]) == []


class TestCrossBelow:
    def test_triggers_on_down_cross(self):
        alarms = [make_alarm(10.0, "cross_below")]
        triggered = evaluate_alarms(12.0, 9.0, alarms)
        assert triggered == alarms

    def test_no_trigger_when_stays_above(self):
        alarms = [make_alarm(10.0, "cross_below")]
        assert evaluate_alarms(12.0, 11.0, alarms) == []

    def test_no_trigger_when_crossing_up(self):
        alarm = make_alarm(10.0, "cross_below")
        assert evaluate_alarms(9.0, 10.0, [alarm]) == []


class TestCrossEither:
    def test_triggers_either_direction(self):
        above = make_alarm(11.0, "cross_either")
        below = make_alarm(9.0, "cross_either")
        assert evaluate_alarms(10.0, 12.0, [above, below]) == [above]
        assert evaluate_alarms(10.0, 8.0, [above, below]) == [below]


class TestBoundaryAndState:
    def test_equal_prev_price_is_not_a_cross(self):
        alarms = [make_alarm(10.0, "cross_above")]
        assert evaluate_alarms(10.0, 10.0, alarms) == []

    def test_exactly_on_alert_price_above_counts(self):
        alarm = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(9.5, 10.0, [alarm]) == [alarm]

    def test_inactive_alarm_ignored(self):
        alarms = [make_alarm(10.0, "cross_below", active=False)]
        assert evaluate_alarms(14.0, 9.0, alarms) == []

    def test_already_triggered_ignored(self):
        alarms = [make_alarm(10.0, "cross_either", triggered=True)]
        assert evaluate_alarms(14.0, 9.0, alarms) == []

    def test_none_prev_price_returns_empty(self):
        assert evaluate_alarms(None, 10.0, [make_alarm(9.0, "cross_either")]) == []

    def test_nonpositive_current_price_returns_empty(self):
        assert evaluate_alarms(5.0, 0.0, [make_alarm(4.0, "cross_either")]) == []