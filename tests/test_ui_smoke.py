"""Smoke test: all UI modules import cleanly in offscreen mode.

No Qt event loop or TWS connection is required — this only guards against
import regressions (broken names, missing symbols, etc.).
"""

def test_import_all_ui_modules():
    import ui.candlestick_item
    import ui.chart_panel
    import ui.watchlist_panel
    import ui.studies_dialog
    import ui.alarm_dialog
    import ui.drawing_overlay
    import ui.drawing_groups_dialog
    import ui.alarm_overlay
    import ui.chart_mouse_router
    import ui.toast
    import ui.main_window
    assert ui.candlestick_item.ChartMode.CANDLES.value == "candles"
    assert ui.main_window.DEFAULT_WATCHLIST


def test_import_all_ibkr_modules():
    import ibkr.bridge
    import ibkr.client
    import ibkr.contracts
    import ibkr.error_codes
    import ibkr.id_manager
    import ibkr.market_data
    import ibkr.pacing
    import ibkr.realtime_bars
    import ibkr.utils
    assert ibkr.market_data.TIMEFRAME_CONFIG


def test_import_all_data_modules():
    import data.models
    import data.alarm_store
    import data.bar_aggregator
    import data.bar_cache
    import data.db
    import data.study_store
    import data.drawing_store
    import services.drawing_service
    import services.sound_service
    assert hasattr(data.models, "Position")
    assert hasattr(data.models, "Drawing")


def test_chart_modes_enum():
    from ui.candlestick_item import ChartMode
    modes = [m.value for m in ChartMode]
    assert modes == ["candles", "hollow", "heikin", "line", "area"]