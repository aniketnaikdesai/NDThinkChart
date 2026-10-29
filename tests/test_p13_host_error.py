"""P13-T3 — in-pop-out chart-host failure error state (D49.3, ESC-070 model).

T31: a chart host that raises on startup produces a visible in-pop-out error
state (message area plus status text) instead of a blank chart, while the
diagnostic log entry for the failure is retained.
T32: the rendered error text reuses chart_engine_failure_message verbatim and
the error widget is distinct from the no-data (blank-chart) state.
"""

from __future__ import annotations

import itertools
import logging

SYMBOL = "P13H"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter(range(7001, 7200))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    # D42's depth floor (S17) can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(7301)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _make_broken_popout(monkeypatch, win, caplog, qapp):
    """Open a pop-out whose chart host raises on startup; return it attached."""
    from ui.popout_window import PopoutChartWindow

    popout = PopoutChartWindow(SYMBOL, TF, "Candles", False, win)

    def _boom():
        raise RuntimeError("boom-host")

    monkeypatch.setattr(popout.chart, "ensure_host", _boom)
    with caplog.at_level(logging.DEBUG, logger="ui.popout_window"):
        popout.attach()
    # The real open path shows the window after attach; visibility of the
    # error state is only meaningful once shown.
    popout.show()
    qapp.processEvents()
    return popout


def test_host_failure_shows_error_state_and_keeps_diagnostic_log(
    monkeypatch, qapp, caplog
):
    """T31: broken host → visible error state, diagnostic log retained."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        qapp.processEvents()

        popout = _make_broken_popout(monkeypatch, win, caplog, qapp)
        try:
            # The failure is flagged on the ESC-070 model, not silent.
            assert popout.chart_engine_failed is True
            # Message area: visible with text (not a blank chart).
            assert popout._engine_error_label.isVisible()
            assert popout._engine_error_label.text().strip() != ""
            # Status text: visible with text.
            assert popout._status_label.isVisible()
            assert popout._status_label.text().strip() != ""
            # The diagnostic log entry for the failure is retained.
            assert any(
                "engine host unavailable" in (record.getMessage() or "")
                for record in caplog.records
            ), [record.getMessage() for record in caplog.records]
        finally:
            popout.close()
            qapp.processEvents()
    finally:
        win.close()


def test_error_text_verbatim_and_distinct_from_no_data(monkeypatch, qapp, caplog):
    """T32: error text reuses the ESC-070 wording; widget differs from no-data."""
    from ui.main_window import chart_engine_failure_message

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        qapp.processEvents()

        popout = _make_broken_popout(monkeypatch, win, caplog, qapp)
        try:
            engine_name = getattr(popout.chart, "ENGINE_NAME", "unknown")
            expected = chart_engine_failure_message(engine_name)
            # Verbatim reuse — never reworded.
            assert popout._engine_error_label.text() == expected
            assert popout._status_label.text() == expected
            # Unambiguous versus no-data: the error widget is a dedicated
            # object, not the chart (whose blank/empty rendering is the
            # no-data state), and the text is non-empty.
            assert popout._engine_error_label is not popout.chart
            assert popout._status_label is not popout.chart
            assert expected.strip() != ""
        finally:
            popout.close()
            qapp.processEvents()
    finally:
        win.close()
