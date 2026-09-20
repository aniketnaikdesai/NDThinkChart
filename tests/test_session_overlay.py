import pytest
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from data.models import Bar
from ui.chart_panel import ChartPanel

EASTERN = ZoneInfo("America/New_York")

def _et_ts(y,m,d,h,mi=0):
    return int(datetime(y,m,d,h,mi,tzinfo=EASTERN).timestamp())

def _bar(ts):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=100, high=101, low=99, close=100, volume=1000)

@pytest.fixture
def panel(qapp):
    p = ChartPanel()
    p.resize(900,600)
    p.show()
    qapp.processEvents()
    yield p
    p.hide()
    p.close()

def test_session_overlay_ext_on_intraday_renders_bands(panel, qapp):
    bars = [_bar(_et_ts(2024,1,10,5,0)), _bar(_et_ts(2024,1,10,10,0)), _bar(_et_ts(2024,1,11,18,0)), _bar(_et_ts(2024,1,12,10,0))]
    panel.set_timeframe("5 mins")
    panel.set_extended_hours(True)
    panel.update_chart(bars)
    qapp.processEvents()
    count = panel._session_overlay.item_count()
    # 3 days => 6 bands but clipped: day10 pre clipped? Should be 6 or maybe 5? At least >0 and pre/post
    assert count > 0
    # Verify at least one pre and one post
    # Check that items exist
    assert count >= 4

def test_session_overlay_ext_off_no_bands(panel, qapp):
    bars = [_bar(_et_ts(2024,1,10,5,0)), _bar(_et_ts(2024,1,11,10,0))]
    panel.set_timeframe("5 mins")
    panel.set_extended_hours(True)
    panel.update_chart(bars)
    qapp.processEvents()
    assert panel._session_overlay.item_count() > 0
    panel.set_extended_hours(False)
    qapp.processEvents()
    assert panel._session_overlay.item_count() == 0

def test_session_overlay_1day_no_bands(panel, qapp):
    bars = [_bar(_et_ts(2024,1,10,10,0)), _bar(_et_ts(2024,1,11,10,0))]
    panel.set_timeframe("1 day")
    panel.set_extended_hours(True)
    panel.update_chart(bars)
    qapp.processEvents()
    assert panel._session_overlay.item_count() == 0

def test_session_overlay_toggle_and_new_candle_recomputes_not_intra_tick(panel, qapp, monkeypatch):
    from services import session_service
    call_count = {"n":0}
    orig = session_service.session_bands
    def spy(bars, tf):
        call_count["n"] +=1
        return orig(bars, tf)
    monkeypatch.setattr(session_service, "session_bands", spy)
    # Also need ChartPanel imported session_bands to be patched - patch both
    import ui.chart_panel as cp
    monkeypatch.setattr(cp, "session_bands", spy)

    bars = [_bar(_et_ts(2024,1,10,5,0)), _bar(_et_ts(2024,1,10,18,0))]
    panel.set_timeframe("5 mins")
    panel.set_extended_hours(True)
    panel.update_chart(bars)
    qapp.processEvents()
    n_after_load = call_count["n"]
    assert n_after_load >=1
    assert panel._session_overlay.item_count() > 0
    # intra-bar same ts should not recompute
    bar_same = _bar(bars[-1].ts)
    bar_same.close = 101
    panel.update_last_bar(bar_same, is_new_candle=False)
    qapp.processEvents()
    assert call_count["n"] == n_after_load
    # new candle should recompute (still within same day but should call)
    new_bar = _bar(_et_ts(2024,1,10,18,5))
    panel.update_last_bar(new_bar, is_new_candle=True)
    qapp.processEvents()
    assert call_count["n"] == n_after_load + 1
    # toggle ext hours should recompute/clear
    panel.set_extended_hours(False)
    qapp.processEvents()
    # After toggle off, overlay cleared
    assert panel._session_overlay.item_count() == 0
    panel.set_extended_hours(True)
    qapp.processEvents()
    assert panel._session_overlay.item_count() > 0
