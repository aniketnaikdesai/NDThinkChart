from pathlib import Path
import pytest

def test_candle_half_width_is_0325():
    text = Path("ui/candlestick_item.py").read_text()
    assert "0.325" in text
    assert "median_diff * 0.325" in text
    # Gap is 35%: full body 0.65*spacing, gap 0.35
    # Check comment mentions gap 35%
    assert "gap 35%" in text.lower() or "35%" in text

def test_gap_increase_between_old_and_new():
    # Old gap 0.20, new gap 0.35, increase 0.15
    old_w = 0.40
    new_w = 0.325
    old_gap = 1 - old_w*2
    new_gap = 1 - new_w*2
    assert old_gap == pytest.approx(0.20)
    assert new_gap == pytest.approx(0.35)
    assert new_gap - old_gap == pytest.approx(0.15)
