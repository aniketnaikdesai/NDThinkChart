"""D24.9 — pop-out persistence via the popouts table."""

from __future__ import annotations

from data.popout_store import PopoutStore


def _clear() -> None:
    PopoutStore.clear()


def test_popout_save_load_delete():
    """AC-D24.9: save → load → delete round-trips through SQLite."""
    _clear()
    try:
        pid = PopoutStore.save(
            "POPX", "5 mins", "Candles", True, {"x": 10, "y": 20, "w": 640, "h": 420}
        )
        assert pid is not None

        saved = PopoutStore.load_all()
        assert len(saved) == 1
        rec = saved[0]
        assert rec["symbol"] == "POPX"
        assert rec["timeframe"] == "5 mins"
        assert rec["mode"] == "Candles"
        assert rec["ext_hours"] is True
        assert rec["geometry"] == {"x": 10, "y": 20, "w": 640, "h": 420}

        # Re-saving the same snapshot updates (no duplicate rows).
        PopoutStore.save(
            "POPX", "5 mins", "Candles", True, {"x": 30, "y": 40, "w": 800, "h": 600}
        )
        assert len(PopoutStore.load_all()) == 1
        assert PopoutStore.load_all()[0]["geometry"]["x"] == 30

        PopoutStore.delete(pid)
        assert PopoutStore.load_all() == []
    finally:
        _clear()


def test_popout_window_persists_on_open_close(monkeypatch, qapp):
    """AC-D24.9: opening a pop-out saves; closing deletes the record."""
    _clear()
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([7001, 7002])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter([7101])
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    try:
        win._now_ts = lambda: 1_759_999_800
        win.load_chart("POPY", "5 mins")
        assert PopoutStore.load_all() == []

        win._open_popout()
        qapp.processEvents()
        saved = PopoutStore.load_all()
        assert len(saved) == 1
        assert saved[0]["symbol"] == "POPY"

        win._popouts[0].close()
        qapp.processEvents()
        assert PopoutStore.load_all() == []
    finally:
        _clear()
        win.close()
