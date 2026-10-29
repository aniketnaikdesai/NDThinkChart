"""P13-T7 (D49.6 create half): main-chart timezone offset threaded into pop-out creation.

T71 (integration): a non-zero main-chart offset is carried into a pop-out
created offscreen — red pre-fix (hardcoded ``tz_offset=0.0``).
T72 (unit): the ``create_chart_view`` seam signature is unchanged and the
creation call site passes ``self._tz_offset`` with no new timezone source.
"""

import inspect

import pytest


@pytest.fixture()
def window(monkeypatch, tmp_path):
    """Offscreen MainWindow with no live TWS connection."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p13_tz_create.db"))
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    from PyQt6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])
    from ui.main_window import MainWindow

    w = MainWindow()
    yield w
    for popout in list(getattr(w, "_popouts", [])):
        try:
            popout.close()
        except Exception:
            pass
    w.close()


def test_p13_t71_popout_inherits_main_chart_offset(window):
    """New pop-out view carries the main chart's non-zero tz offset."""
    window._current_symbol = "AAPL"
    window._current_tf = "5 mins"
    window._tz_offset = 14400.0
    window._open_popout()
    assert window._popouts, "expected _open_popout to create a pop-out"
    popout = window._popouts[-1]
    assert popout.chart.tz_offset == pytest.approx(window._tz_offset)
    assert popout.chart.tz_offset == pytest.approx(14400.0)


def test_p13_t72_seam_signature_and_offset_source():
    """Seam unchanged; creation site threads self._tz_offset; no new source."""
    from ui import main_window as mw_mod
    from ui import popout_window as po_mod
    from ui.chart_view import create_chart_view

    # The seam contract is unchanged.
    sig = inspect.signature(create_chart_view)
    assert list(sig.parameters) == ["tz_offset", "editable"]
    assert sig.parameters["tz_offset"].default == 0.0
    assert sig.parameters["editable"].default is True

    # The constructor accepts the threaded offset.
    init_sig = inspect.signature(po_mod.PopoutChartWindow.__init__)
    assert "tz_offset" in init_sig.parameters

    # _open_popout passes the main chart's current offset, never a literal.
    open_src = inspect.getsource(mw_mod.MainWindow._open_popout)
    assert "self._tz_offset" in open_src
    assert "tz_offset=0.0" not in open_src

    # The hardcoded 0.0 at the pop-out creation call site is gone.
    po_src = inspect.getsource(po_mod)
    assert "popout_view(tz_offset=0.0)" not in po_src

    # No new timezone source introduced on the creation path.
    for src in (open_src, inspect.getsource(po_mod.PopoutChartWindow.__init__)):
        assert "ZoneInfo" not in src
        assert "utcoffset" not in src
        assert "datetime.now" not in src
