"""P10-T4: lock completion + recolor interplay (D50.3/D50.4).

Mapping to the wave acceptance tests:
- ``test_t41_locked_delete_refused_color_allowed`` -> P10-T4-T41: delete on
  a locked drawing refused (store row + geometry intact) via the page
  deleted path and the Del-button path; color/style edits — including a
  group recolour repainting a locked member — still apply.
- ``test_t42_recolor_interplay_pins`` -> P10-T4-T42: drag-edit commits are
  geometry-only (stored color untouched); mid-drag group recolour updates
  the store at once while the ghost keeps the start color and the stored
  (recoloured) color wins at commit; leave-group keeps its color in both
  directions.

Repro-first: T41's delete legs are red pre-fix (``_on_drawing_deleted``
removes the row; the Del-button path raises ``AttributeError`` — the LWC
surface has no ``delete_selected``). The color legs are
allowed-behavior guards (green pre- and post-fix). T42 pins the P10-T3
normalisation and the reused recolor machinery.
"""

import itertools
import os
from datetime import datetime, timezone

from data.drawing_store import DrawingStore
from data.models import Bar, Drawing

BASE_SYMBOL = f"P10T4_{os.getpid()}"
TF = "5 mins"
START_COLOR = "#e11d48"
RECOLORED = "#0ea5e9"
MID_DRAG_COLOR = "#22c55e"


def _bars(symbol):
    base = int(datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc).timestamp())
    return [
        Bar(symbol=symbol, timeframe=TF, ts=base + i * 300,
            open=100.0 + i, high=101.0 + i, low=99.0 + i,
            close=100.5 + i, volume=1000.0)
        for i in range(10)
    ]


def _make_window(monkeypatch, qapp, symbol):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([6001, 6002, 6003, 6004, 6005])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = itertools.count(6101)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    win._now_ts = lambda: 1_760_000_000
    win.load_chart(symbol, TF)
    win._sessions[symbol].set_bars(TF, _bars(symbol))
    return win


def _seed_locked(symbol, color=START_COLOR):
    gid = DrawingStore.create_group(
        symbol, "set", DrawingStore.next_group_seq(symbol), color="#38bdf8")
    DrawingStore.update_group(gid, locked=True)
    did = DrawingStore.create_drawing(Drawing(
        symbol=symbol, kind="trendline",
        payload={"p1": {"x": _bars(symbol)[0].ts, "y": 101.0},
                 "p2": {"x": _bars(symbol)[3].ts, "y": 102.0}},
        color=color, group_id=gid))
    return gid, did


def _row(symbol, drawing_id):
    return next(
        d for d in DrawingStore.drawings_for_symbol(symbol)
        if d.id == drawing_id)


def _sync(win, symbol):
    session = win._sessions[symbol]
    session.reload_drawings()
    session.sync_drawings_to_views()


def test_t41_locked_delete_refused_color_allowed(monkeypatch, qapp):
    """P10-T4-T41: locked deletes refused on both paths; color still applies."""
    symbol = BASE_SYMBOL + "_T41"
    win = _make_window(monkeypatch, qapp, symbol)
    try:
        gid, did = _seed_locked(symbol)
        _sync(win, symbol)
        qapp.processEvents()
        pre_payload = dict(_row(symbol, did).payload)
        pre_items = [dict(it) for it in win.chart_panel.drawing_items]
        assert len(pre_items) == 1

        # Page deleted path (real signal wiring) — refused.
        win.chart_panel._on_page_drawing_deleted({"id": did})
        qapp.processEvents()
        assert dict(_row(symbol, did).payload) == pre_payload
        assert [dict(it) for it in win.chart_panel.drawing_items] == pre_items

        # Del-button path (real selection wiring + literal button click).
        win.chart_panel._on_page_selection_changed({"id": did})
        qapp.processEvents()
        assert win.draw_delete_btn.isEnabled()
        win.draw_delete_btn.click()
        qapp.processEvents()
        assert dict(_row(symbol, did).payload) == pre_payload
        assert [dict(it) for it in win.chart_panel.drawing_items] == pre_items

        # Color/style change on the locked drawing applies.
        new_payload = dict(pre_payload, extra="style")
        win._on_drawing_updated(did, new_payload, RECOLORED)
        qapp.processEvents()
        assert _row(symbol, did).color == RECOLORED
        assert dict(_row(symbol, did).payload) == new_payload

        # Group recolour repaints the locked member's stored color.
        DrawingStore.update_group(gid, color=MID_DRAG_COLOR)
        DrawingStore.repaint_group_members(gid, MID_DRAG_COLOR)
        win._on_drawing_groups_changed()
        qapp.processEvents()
        assert _row(symbol, did).color == MID_DRAG_COLOR
        item = next(it for it in win.chart_panel.drawing_items
                    if it.get("id") == did)
        assert item["color"] == MID_DRAG_COLOR

        # Control: unlocking makes the Del-button path live (not vacuous).
        DrawingStore.update_group(gid, locked=False)
        win.chart_panel._on_page_selection_changed({"id": did})
        qapp.processEvents()
        win.draw_delete_btn.click()
        qapp.processEvents()
        assert [d for d in DrawingStore.drawings_for_symbol(symbol)
                if d.id == did] == []
        assert [it for it in win.chart_panel.drawing_items
                if it.get("id") == did] == []
    finally:
        win.close()


def test_t42_recolor_interplay_pins(monkeypatch, qapp):
    """P10-T4-T42: geometry-only commits, mid-drag recolour, leave-group."""
    symbol = BASE_SYMBOL + "_T42"
    win = _make_window(monkeypatch, qapp, symbol)
    try:
        bars = _bars(symbol)
        ts = [b.ts for b in bars]
        gid = DrawingStore.create_group(
            symbol, "set", DrawingStore.next_group_seq(symbol),
            color="#38bdf8")
        gid_b = DrawingStore.create_group(
            symbol, "set-b", DrawingStore.next_group_seq(symbol),
            color="#38bdf8")
        mk_payload = lambda: {  # noqa: E731
            "p1": {"x": ts[0], "y": 101.0},
            "p2": {"x": ts[3], "y": 102.0}}
        did_a = DrawingStore.create_drawing(Drawing(
            symbol=symbol, kind="trendline", payload=mk_payload(),
            color=START_COLOR, group_id=gid))
        did_b = DrawingStore.create_drawing(Drawing(
            symbol=symbol, kind="trendline", payload=mk_payload(),
            color=START_COLOR, group_id=gid_b))
        _sync(win, symbol)
        qapp.processEvents()
        session = win._sessions[symbol]
        surface = win.chart_panel.drawing_overlay

        # Geometry-only commit on a recoloured drawing: payload lands,
        # stored color untouched.
        DrawingStore.update_group(gid, color=RECOLORED)
        DrawingStore.repaint_group_members(gid, RECOLORED)
        _sync(win, symbol)
        qapp.processEvents()
        assert _row(symbol, did_a).color == RECOLORED
        drag_page = {"id": did_a, "kind": "trendline", "color": "",
                     "points": [[2.0, 100.0], [5.0, 110.0]]}
        win.chart_panel._on_page_drawing_updated(dict(drag_page))
        qapp.processEvents()
        assert dict(_row(symbol, did_a).payload) == {
            "p1": {"x": ts[2], "y": 100.0},
            "p2": {"x": ts[5], "y": 110.0}}
        assert _row(symbol, did_a).color == RECOLORED

        # Mid-drag recolour: store updates at once, ghost keeps start color.
        ghost = surface.drag_drawing(did_b, "trendline", 0, 1.5, 2.0,
                                     body=True)
        assert ghost["color"] == START_COLOR
        assert dict(_row(symbol, did_b).payload) == mk_payload()
        assert _row(symbol, did_b).color == START_COLOR
        DrawingStore.update_group(gid_b, color=MID_DRAG_COLOR)
        DrawingStore.repaint_group_members(gid_b, MID_DRAG_COLOR)
        assert _row(symbol, did_b).color == MID_DRAG_COLOR
        live = [dict(it) for it in win.chart_panel.drawing_items]
        ghost_item = next(it for it in live if it.get("id") == did_b)
        assert ghost_item["color"] == START_COLOR

        # Fan-out (the dialog-changed path), then the commit: the stored
        # (recoloured) color wins, geometry lands.
        session.reload_drawings()
        session.sync_drawings_to_views()
        qapp.processEvents()
        win.chart_panel._on_page_drawing_updated(
            {"id": did_b, "kind": "trendline", "color": "",
             "points": [[2.0, 100.0], [5.0, 110.0]]})
        qapp.processEvents()
        assert dict(_row(symbol, did_b).payload) == {
            "p1": {"x": ts[2], "y": 100.0},
            "p2": {"x": ts[5], "y": 110.0}}
        assert _row(symbol, did_b).color == MID_DRAG_COLOR

        # Leave-group keeps its color in both directions.
        DrawingStore.assign_groups([did_b], None)
        assert _row(symbol, did_b).color == MID_DRAG_COLOR
        assert _row(symbol, did_b).group_id is None
        DrawingStore.assign_groups([did_b], gid_b)
        assert _row(symbol, did_b).color == MID_DRAG_COLOR
        assert _row(symbol, did_b).group_id == gid_b
    finally:
        win.close()
