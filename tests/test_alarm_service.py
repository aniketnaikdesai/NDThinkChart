"""Tests for services/alarm_service.py — crossing logic."""

import math

import pytest

from data.models import Alarm
from services.alarm_service import evaluate_alarms, evaluate_volume_burst
from services.volume_baseline import DEFAULT_Z_THRESHOLD


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


def make_burst_alarm(z_threshold, active=True, triggered=False) -> Alarm:
    return Alarm(id=None, symbol="TEST", price=0.0, direction="cross_above",
                 active=active, triggered=triggered, kind="volume_burst",
                 params={"z_threshold": z_threshold})


class TestVolumeBurstThreshold:
    """Q-42: the z_threshold parser restores the documented default for
    zero/negative/NaN/inf instead of silently never firing."""

    # med=100, mad=10 -> z = 0.6745 * (x - 100) / 10.
    baseline = (100.0, 10.0, 30, "tod")

    def test_valid_threshold_fires(self):
        alarm = make_burst_alarm(2.0)
        # z ~ 2.02 -> at/above 2.0 fires, below the 4.0 default.
        assert evaluate_volume_burst(130.0, self.baseline, [alarm]) == [alarm]

    def test_default_threshold_does_not_fire_at_z2(self):
        alarm = Alarm(id=None, symbol="TEST", price=0.0,
                      direction="cross_above", kind="volume_burst", params={})
        assert evaluate_volume_burst(130.0, self.baseline, [alarm]) == []

    @pytest.mark.parametrize("bad", [0, 0.0, -1.0, -4,
                                     float("nan"), float("inf"),
                                     float("-inf"), "high", None])
    def test_invalid_threshold_restores_default(self, bad):
        # z ~ 2.02: would fire for a small/NaN threshold, must not fire
        # once the invalid value is replaced by the 4.0 default.
        alarm = make_burst_alarm(bad)
        assert evaluate_volume_burst(130.0, self.baseline, [alarm]) == []
        # And a genuine burst (z >> 4) still fires with the restored default.
        alarm2 = make_burst_alarm(bad)
        assert evaluate_volume_burst(200.0, self.baseline, [alarm2]) == [alarm2]
        assert math.isfinite(alarm2.trigger_z)

    def test_nan_threshold_fires_real_burst(self):
        alarm = make_burst_alarm(float("nan"))
        assert evaluate_volume_burst(200.0, self.baseline, [alarm]) == [alarm]

    def test_inf_threshold_fires_real_burst(self):
        alarm = make_burst_alarm(float("inf"))
        assert evaluate_volume_burst(200.0, self.baseline, [alarm]) == [alarm]

    def test_none_baseline_fires_nothing(self):
        alarm = make_burst_alarm(0.5)
        assert evaluate_volume_burst(500.0, None, [alarm]) == []

    def test_inactive_or_triggered_burst_ignored(self):
        assert evaluate_volume_burst(
            500.0, self.baseline, [make_burst_alarm(0.5, active=False)]) == []
        assert evaluate_volume_burst(
            500.0, self.baseline,
            [make_burst_alarm(0.5, triggered=True)]) == []