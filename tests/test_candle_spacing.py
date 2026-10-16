import pytest

from ui.candlestick_item import capped_body_half_width

# The shipped legibility floor, in ViewBox logical pixels (the unit
# ``px_per_sec`` yields — see ``capped_body_half_width``'s docstring).
FLOOR_PX = 4.0


def _body_width(median_diff, px_per_sec, floor_px=FLOOR_PX):
    """Full candle-body width (2 * half-width) from the shared D42 helper.

    ``base_half_width = 0.325 * median_diff`` is the D6 formula: a full body of
    65 % of the inter-bar pitch and a 35 % gap in the non-dense regime.
    """
    half = capped_body_half_width(
        median_diff, 0.325 * median_diff, px_per_sec, floor_px
    )
    return 2.0 * half


def test_candle_half_width_is_0325():
    # Non-dense regime (pitch > F): the shared helper's base half-width is
    # 0.325 * spacing, i.e. a full body 65 % of the spacing and a 35 % gap.
    median_diff = 100.0
    px_per_sec = 1.0
    pitch = median_diff * px_per_sec
    assert pitch > FLOOR_PX

    half = capped_body_half_width(median_diff, 0.325 * median_diff, px_per_sec)
    assert half == pytest.approx(0.325 * median_diff)

    body = 2.0 * half
    assert body == pytest.approx(0.65 * pitch)
    assert body == pytest.approx(max(0.65 * pitch, FLOOR_PX))


def test_regime_pitch_greater_than_floor():
    # pitch > F  ->  body = max(0.65 * pitch, F)
    median_diff = 100.0
    px_per_sec = 1.0
    pitch = median_diff * px_per_sec
    assert pitch > FLOOR_PX

    body = _body_width(median_diff, px_per_sec)
    assert body == pytest.approx(max(0.65 * pitch, FLOOR_PX))
    assert body <= pitch


def test_regime_pitch_equals_floor():
    # pitch == F  ->  body = F
    median_diff = 4.0
    px_per_sec = 1.0
    pitch = median_diff * px_per_sec
    assert pitch == pytest.approx(FLOOR_PX)

    body = _body_width(median_diff, px_per_sec)
    assert body == pytest.approx(FLOOR_PX)
    assert body == pytest.approx(pitch)


def test_regime_pitch_less_than_floor():
    # pitch < F  ->  body = pitch (the floor yields; the gap is never negative)
    median_diff = 1.0
    px_per_sec = 1.0
    pitch = median_diff * px_per_sec
    assert pitch < FLOOR_PX

    body = _body_width(median_diff, px_per_sec)
    assert body == pytest.approx(pitch)
    assert body <= pitch


def test_non_dense_gap_is_35_percent_of_spacing():
    # The original 0.325 / 35 % intent survives: in the non-dense regime the
    # inter-bar gap is 35 % of the spacing (full body 65 %).
    median_diff = 100.0
    px_per_sec = 1.0
    pitch = median_diff * px_per_sec

    body = _body_width(median_diff, px_per_sec)
    gap = pitch - body
    assert gap == pytest.approx(0.35 * pitch)


def test_gap_increase_between_old_and_new():
    # Old gap 0.20, new gap 0.35, increase 0.15
    old_w = 0.40
    new_w = 0.325
    old_gap = 1 - old_w * 2
    new_gap = 1 - new_w * 2
    assert old_gap == pytest.approx(0.20)
    assert new_gap == pytest.approx(0.35)
    assert new_gap - old_gap == pytest.approx(0.15)
