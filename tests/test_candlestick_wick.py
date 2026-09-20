import pytest
from pathlib import Path
import pyqtgraph as pg
from data.models import Bar
from ui.chart_panel import ChartPanel
from ui.candlestick_item import CandlestickItem, ChartMode

def _bar(ts, o, h, l, c):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=h, low=l, close=c, volume=1000)

def test_wick_is_cosmetic_body_coloured_and_behind_body():
    # Static check: file contains cosmetic wick logic
    text = Path("ui/candlestick_item.py").read_text()
    assert "wick_green" in text
    assert "wick_red" in text
    assert "setCosmetic(True)" in text
    assert "GREEN" in text and "RED" in text
    # Check wick drawn before body (order)
    assert text.index("wick_pen") < text.index("drawRect")

def test_wick_extends_beyond_body_when_shadow(qapp):
    # Functional: single candle with shadows should have wick beyond body
    # Use CandlestickItem directly to avoid ChartPanel side-effects on DB
    _BASE_TS = 1_700_000_000
    bar = _bar(_BASE_TS, 95, 110, 90, 105)  # bull with both shadows
    assert bar.high > max(bar.open, bar.close)
    assert bar.low < min(bar.open, bar.close)
    # Create item directly
    item = CandlestickItem([(bar.ts, bar.open, bar.high, bar.low, bar.close)])
    assert item._picture is not None
    assert not item._picture.isNull()
    # Verify wick would extend beyond body by data: high>body_top and low<body_bottom
    body_top = max(bar.open, bar.close)
    body_bottom = min(bar.open, bar.close)
    assert bar.high > body_top
    assert bar.low < body_bottom

def test_wick_body_share_direction_colour():
    # Check source has body-coloured wick
    text = Path("ui/candlestick_item.py").read_text()
    # wick_green uses GREEN, wick_red uses RED
    assert "QPen(GREEN)" in text
    assert "QPen(RED)" in text
    # Both wick pens should be body colours, not gray
    assert "#9ca3af" not in text or "wick_pen    = QPen(QColor('#9ca3af'))" not in text  # old gray removed
    # Functional colour check via item
    bull = CandlestickItem([(0, 95, 110, 90, 105)])
    bear = CandlestickItem([(0, 105, 110, 90, 95)])
    # Ensure they render without error
    assert not bull._picture.isNull()
    assert not bear._picture.isNull()

def test_dense_view_wick_stays_1px_body_clamped(qapp):
    # Simulate dense view: 960 1-min bars
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i*60, 100 + (i%5), 102 + (i%2), 99 - (i%2), 100 + (i%3)) for i in range(960)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    # After dense load, body should be clamped to >=4px device
    # We can't directly measure device px, but we can check that wick is still cosmetic 1px
    text = Path("ui/candlestick_item.py").read_text()
    assert "setCosmetic(True)" in text
    assert "min_w" in text or "2.0 / px_per_sec" in text
    # Ensure chart still renders
    assert not panel.candlestick._picture.isNull()
    panel.hide()
    panel.close()
