"""Tests for services/alarm_service.py — crossing logic."""

import inspect
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

    def test_arrival_on_the_level_is_a_touch_not_a_cross(self):
        """AC-D97.1 / A242: arrival exactly on the level is a touch, not a
        crossing — the touch arms, and the next strictly-beyond sample fires."""
        arriving = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(9.5, 10.0, [arriving]) == []
        fresh = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(10.0, 10.01, [fresh]) == [fresh]

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


class TestCrossingRuleP29:
    """D97 / S-P29-2: one crossing rule — the previous side is inclusive
    (a touch arms), the current side is exclusive (sitting on the level
    never fires). AC-D97.1–D97.3, Journey 79, A242."""

    @pytest.mark.parametrize(
        "direction,beyond,further",
        [("cross_above", 10.5, 11.0),
         ("cross_below", 9.5, 9.0),
         ("cross_either", 10.5, 11.0)],
    )
    def test_touch_at_level_fires_once_on_next_beyond_sample(
            self, direction, beyond, further):
        """P29-T2-01 / AC-D97.1: a tick at the level is a touch, the first
        strictly-beyond sample fires exactly once, a later one is latched."""
        alarm = make_alarm(10.0, direction)
        assert evaluate_alarms(9.0, 10.0, [alarm]) == []
        assert evaluate_alarms(10.0, beyond, [alarm]) == [alarm]
        alarm.triggered = True
        assert evaluate_alarms(beyond, further, [alarm]) == []

    @pytest.mark.parametrize(
        "direction", ["cross_above", "cross_below", "cross_either"])
    def test_staying_at_the_level_never_fires(self, direction):
        """P29-T2-02 / AC-D97.1: the current-side boundary is exclusive."""
        alarm = make_alarm(10.0, direction)
        assert evaluate_alarms(None, 10.0, [alarm]) == []
        for _ in range(3):
            assert evaluate_alarms(10.0, 10.0, [alarm]) == []
        assert alarm.triggered is False

    @pytest.mark.parametrize(
        "direction", ["cross_above", "cross_below", "cross_either"])
    def test_seed_at_level_never_fires_and_stays_untriggered(self, direction):
        """P29-T2-03 / AC-D97.2: no previous price means no evaluation, and
        a seed tick followed by a sample at the same level fires nothing."""
        alarm = make_alarm(10.0, direction)
        assert evaluate_alarms(None, 10.0, [alarm]) == []
        assert evaluate_alarms(10.0, 10.0, [alarm]) == []
        assert alarm.triggered is False

    def test_touch_then_opposite_move_does_not_fire(self):
        """P29-T2-04 / AC-D97.3: a touch arms, but only a move in the
        alarm's own direction crosses the level."""
        above = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(9.5, 10.0, [above]) == []
        assert evaluate_alarms(10.0, 9.4, [above]) == []

        below = make_alarm(10.0, "cross_below")
        assert evaluate_alarms(10.5, 10.0, [below]) == []
        assert evaluate_alarms(10.0, 10.6, [below]) == []

    def test_opposite_alarms_at_one_level_only_matching_fires(self):
        """Journey 79 / AC-D97.1: two alarms at one level — the move's
        direction selects exactly one."""
        above = make_alarm(10.0, "cross_above")
        below = make_alarm(10.0, "cross_below")
        assert evaluate_alarms(10.0, 10.5, [above, below]) == [above]
        assert evaluate_alarms(10.0, 9.5, [above, below]) == [below]

    def test_touched_from_either_side_then_crossed(self):
        """Journey 79: whichever side the touch arrives from, the first move
        strictly through the level fires."""
        first = make_alarm(10.0, "cross_either")
        assert evaluate_alarms(10.5, 10.0, [first]) == []
        assert evaluate_alarms(10.0, 9.5, [first]) == [first]

        second = make_alarm(10.0, "cross_either")
        assert evaluate_alarms(9.5, 10.0, [second]) == []
        assert evaluate_alarms(10.0, 10.5, [second]) == [second]

    def test_frozen_surface_guards_gap_and_no_touch_field(self):
        """P29-T2-05 / AC-P29-02-INVARIANTS + Journey 79: the signature, the
        guard and the skips are unchanged; a one-tick gap fires; a return to
        the level after firing does not; no touch/armed field exists."""
        expected = ("(prev_price: float | None, curr_price: float, "
                    "alarms: list[data.models.Alarm]) "
                    "-> list[data.models.Alarm]")
        assert str(inspect.signature(evaluate_alarms)) == expected
        assert not any("touch" in name or "armed" in name
                       for name in Alarm.__dataclass_fields__)

        # Guards: no previous price / non-positive current price.
        alarm = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(None, 10.0, [alarm]) == []
        assert evaluate_alarms(9.0, 0.0, [alarm]) == []
        assert evaluate_alarms(9.0, -1.0, [alarm]) == []

        # Skips: inactive and already-triggered alarms.
        assert evaluate_alarms(
            9.0, 11.0, [make_alarm(10.0, "cross_above", active=False)]) == []
        assert evaluate_alarms(
            9.0, 11.0, [make_alarm(10.0, "cross_above", triggered=True)]) == []

        # Journey 79: a one-tick gap over the level fires once...
        gap = make_alarm(10.0, "cross_above")
        assert evaluate_alarms(9.0, 11.0, [gap]) == [gap]

        # ...and a return to the level after firing does not re-fire.
        gap.triggered = True
        assert evaluate_alarms(11.0, 10.0, [gap]) == []
        assert evaluate_alarms(10.0, 10.0, [gap]) == []


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