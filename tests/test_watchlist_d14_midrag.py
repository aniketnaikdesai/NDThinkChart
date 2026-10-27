"""T30 / ESC-010 — D14 mid-drag symbol change (TR-17 / AC-D14.4).

A symbol change that lands while a gesture is in flight (the D14 watchlist
double-click path → ``MainWindow.load_chart`` → the chart view) must not
leave the mouse router holding a gesture the new symbol never started. The
historical failure mode (``docs/debug/debug_log.md``) was a pyqtgraph
``GraphicsScene.dragItem`` reference to a drawing item removed mid-gesture.
That scene went with the pyqtgraph engine; TR-17 is the engine-neutral half
that survives: the view discards the gesture and the router returns to
``RouterMode.IDLE``.
"""

from ui.chart_mouse_router import RouterMode


# ── T30-T02 / TR-17 — router mode reset on a symbol change ───────────────────

def test_T30_T02_symbol_change_resets_router_mode(qapp, sample_bars):
    """T30-T02 / TR-17: ALARM_PLACING (mid-gesture) -> symbol change -> IDLE."""
    from ui.lwc_view import LwcChartView

    view = LwcChartView()
    try:
        view.resize(900, 600)
        view.set_symbol("TEST")
        view.update_bars(sample_bars)
        qapp.processEvents()

        # Arm a gesture: the router leaves IDLE for ALARM_PLACING.
        assert view.set_alarm_mode(True) == "ALARM_PLACING"
        assert view.router.active_mode == RouterMode.ALARM_PLACING

        # Symbol change (the overlay reset half of the D14 path, unit-level).
        view.set_symbol("AAPL")
        qapp.processEvents()

        assert view.router.active_mode == RouterMode.IDLE
        assert view.interaction_ops[-1]["intent"] == "symbol_change"
        assert view.interaction_ops[-1]["mode"] == "IDLE"
    finally:
        view.close()


# ── T30-T03 / AC-D14.1-3 preserved — existing D14 no-op paths unchanged ──────

def test_T30_T03_existing_d14_noop_paths_unchanged(qapp):
    """T30-T03 / AC-D14.1-3: re-run the existing D14 decision + emit tests."""
    # Imported lazily so the manifest's new file does not alter the originals.
    from tests.test_watchlist import (
        test_should_load_on_double_click,
        test_panel_double_click_emits_symbol,
    )

    test_should_load_on_double_click()
    test_panel_double_click_emits_symbol(qapp)
