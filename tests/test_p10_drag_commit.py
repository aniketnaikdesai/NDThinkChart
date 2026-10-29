"""P10-T3: Python commit close-out — lock refusal, geometry-only updated,
persist-reload-fan-out (D50.1 / D50.3 / D50.5).

Mapping to the wave acceptance tests:
- ``test_t31_locked_drag_refused`` -> P10-T3-T31 (locked drag refused)
- ``test_t32_commit_closeout`` -> P10-T3-T32 (geometry-only commit + close-out)
- ``test_t33_cancel_and_zero_view`` -> P10-T3-T33 (cancel identity, zero-view)
- ``test_t32_unknown_item_empty_color_dropped`` -> ESC-092 (unknown-item
  empty-color guard: dropped commit, stored color untouched)

Repro-first: T31 errors pre-fix (no ``LwcDrawingSurface.drag_drawing`` gate —
no gate at all) and T32 fails pre-fix (empty commit color clobbers the stored
color). T33 pins behaviour that already holds.
"""

import os
from datetime import datetime, timezone
from types import SimpleNamespace

from data.drawing_store import DrawingStore
from data.models import Bar, Drawing

BASE_SYMBOL = f"P10T3_{os.getpid()}"
SEED_COLORS = {
    "trendline": "#e11d48",
    "horizontal": "#0ea5e9",
    "zone": "#22c55e",
    "fibonacci": "#a855f7",
    "measure": "#f59e0b",
}


def _bars(symbol):
    base = int(datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc).timestamp())
    return [
        Bar(symbol=symbol, timeframe="5 mins", ts=base + i * 300,
            open=100.0 + i, high=101.0 + i, low=99.0 + i,
            close=100.5 + i, volume=1000.0)
        for i in range(10)
    ]


def _seed_group(symbol, locked=False, name="set"):
    from data.drawing_store import DrawingStore as DS

    gid = DS.create_group(symbol, name, DS.next_group_seq(symbol),
                          color="#38bdf8")
    if locked:
        DS.update_group(gid, locked=True)
    return gid


def _seed_drawing(symbol, kind, payload, group_id, color=None):
    return DrawingStore.create_drawing(Drawing(
        symbol=symbol, kind=kind, payload=payload,
        color=color if color is not None else SEED_COLORS[kind],
        group_id=group_id))


def _store_row(symbol, drawing_id):
    return next(
        d for d in DrawingStore.drawings_for_symbol(symbol)
        if d.id == drawing_id)


def _seed_payload(kind, ts):
    if kind in ("trendline", "fibonacci", "measure"):
        payload = {"p1": {"x": ts[0], "y": 101.0},
                   "p2": {"x": ts[3], "y": 102.0}}
        if kind == "fibonacci":
            payload["type"] = "retr"
        return payload
    if kind == "horizontal":
        return {"y": 103.0}
    if kind == "zone":
        return {"x1": ts[0], "x2": ts[3], "y1": 91.0, "y2": 94.0}
    raise AssertionError(kind)


def _view_with_axis(bars):
    from ui.lwc_view import LwcChartView

    view = LwcChartView()
    view.set_timeframe("5 mins")
    view.set_series("candles", bars)
    return view


def _session(symbol):
    from ui.ticker_session import TickerSession

    host = SimpleNamespace(_teardown_session=lambda s: None)
    return TickerSession(symbol, host)


def _closeout(session):
    from ui.main_window import MainWindow

    stub = SimpleNamespace(_session_for_facade=lambda: session)
    return lambda i, p, c: MainWindow._on_drawing_updated(stub, i, p, c)


def _wire_item(view, drawing_id):
    return next(
        it for it in view.drawing_items if it.get("id") == drawing_id)


def _cleanup(symbol):
    for drawing in DrawingStore.drawings_for_symbol(symbol):
        DrawingStore.delete_drawing(drawing.id)
    for group in DrawingStore.groups_for_symbol(symbol):
        DrawingStore.delete_group(group.id)


def test_t31_locked_drag_refused(qapp):
    """P10-T3-T31: locked drag refused (body + anchor) — geometry unchanged,
    store untouched, no validated drag op published."""
    from ui.lwc_view import LwcChartView

    symbol = BASE_SYMBOL + "_T31"
    try:
        gid = _seed_group(symbol, locked=True)
        bars = _bars(symbol)
        ts = [b.ts for b in bars]
        did = _seed_drawing(symbol, "trendline", _seed_payload("trendline", ts),
                            gid)
        view = LwcChartView()
        view.drawing_overlay.set_data(
            symbol, DrawingStore.drawings_for_symbol(symbol),
            DrawingStore.groups_for_symbol(symbol))
        pre_items = [dict(it) for it in view.drawing_items]
        assert len(pre_items) == 1
        pre_payload = dict(_store_row(symbol, did).payload)
        pre_color = _store_row(symbol, did).color
        pre_ops = [dict(op) for op in view.drawing_ops]
        surface = view.drawing_overlay

        for kwargs in ({"point_index": 0, "d_frac": 1.5, "d_price": 2.0,
                        "body": True},
                       {"point_index": 1, "d_frac": -0.5, "d_price": 1.0,
                        "body": False}):
            returned = surface.drag_drawing(did, "trendline", **kwargs)
            assert returned == pre_items[0]
            assert [dict(it) for it in view.drawing_items] == pre_items
            assert dict(_store_row(symbol, did).payload) == pre_payload
            assert _store_row(symbol, did).color == pre_color
            assert [dict(op) for op in view.drawing_ops] == pre_ops
            assert not [op for op in view.drawing_ops
                        if op.get("op") == "drag_drawing"]
    finally:
        _cleanup(symbol)


def test_t32_commit_closeout(qapp):
    """P10-T3-T32: per-kind commit with empty color — payload updated, stored
    color preserved, reload restores geometry on every view, one fan-out."""
    from services.drawing_service import fib_levels
    from ui.lwc_view import LwcChartView  # noqa: F401 (view class used)

    symbol = BASE_SYMBOL + "_T32"
    try:
        gid = _seed_group(symbol, locked=False)
        bars = _bars(symbol)
        ts = [b.ts for b in bars]
        kinds = ["trendline", "horizontal", "zone", "fibonacci", "measure"]
        ids = {k: _seed_drawing(symbol, k, _seed_payload(k, ts), gid)
               for k in kinds}

        view1 = _view_with_axis(bars)
        view2 = _view_with_axis(bars)
        session = _session(symbol)
        session.reload_drawings()
        session.attach_view(view1, "5 mins")
        session.attach_view(view2, "5 mins")
        session.sync_drawings_to_views()
        views = [view1, view2]

        closeout = _closeout(session)
        view1.drawing_controller.updated.connect(
            lambda i, p, c: closeout(i, p, c))

        sync_calls = []
        for view in views:
            surface = view.drawing_overlay
            orig = surface.set_data

            def _wrap(sym, drawings, groups, _orig=orig):
                sync_calls.append(sym)
                return _orig(sym, drawings, groups)

            surface.set_data = _wrap

        commits = {
            "trendline": ({"points": [[2.0, 100.0], [5.0, 110.0]]},
                          {"p1": {"x": ts[2], "y": 100.0},
                           "p2": {"x": ts[5], "y": 110.0}},
                          {"points": [[2.0, 100.0], [5.0, 110.0]]}),
            "horizontal": ({"price": 105.0},
                           {"y": 105.0},
                           {"price": 105.0}),
            "zone": ({"span": [1.0, 4.0], "y1": 90.0, "y2": 95.0},
                     {"x1": ts[1], "x2": ts[4], "y1": 90.0, "y2": 95.0},
                     {"span": [1.0, 4.0]}),
            "fibonacci": ({"points": [[2.0, 100.0], [5.0, 110.0]],
                           "type": "retr"},
                          {"p1": {"x": ts[2], "y": 100.0},
                           "p2": {"x": ts[5], "y": 110.0}, "type": "retr"},
                          {"points": [[2.0, 100.0], [5.0, 110.0]]}),
            "measure": ({"points": [[2.0, 100.0], [5.0, 110.0]]},
                        {"p1": {"x": ts[2], "y": 100.0},
                         "p2": {"x": ts[5], "y": 110.0}},
                        {"points": [[2.0, 100.0], [5.0, 110.0]]}),
        }
        for kind in kinds:
            page, expected_store, expected_wire = commits[kind]
            payload = dict(page, id=ids[kind], kind=kind, color="")
            del sync_calls[:]
            view1._on_page_drawing_updated(payload)

            row = _store_row(symbol, ids[kind])
            assert dict(row.payload) == expected_store
            assert row.color == SEED_COLORS[kind]
            assert sync_calls == [symbol, symbol]
            for view in views:
                item = _wire_item(view, ids[kind])
                for key, value in expected_wire.items():
                    assert item[key] == value, (kind, key)
            fib_item = _wire_item(view1, ids["fibonacci"]) \
                if kind == "fibonacci" else None
            if fib_item is not None:
                assert fib_item["levels"] == [
                    [float(r), float(p)]
                    for r, p in fib_levels(100.0, 110.0, "retr")]
            measure_item = _wire_item(view1, ids["measure"]) \
                if kind == "measure" else None
            if measure_item is not None:
                assert measure_item["delta"] == {"dy": 10.0, "pct": 10.0}
    finally:
        _cleanup(symbol)


def test_t32_unknown_item_empty_color_dropped(qapp):
    """ESC-092: a commit for an id absent from _drawing_items with an empty
    color is dropped — nothing emitted, stored payload and color untouched."""
    symbol = BASE_SYMBOL + "_T32UNK"
    try:
        gid = _seed_group(symbol, locked=False)
        bars = _bars(symbol)
        ts = [b.ts for b in bars]
        did = _seed_drawing(symbol, "trendline", _seed_payload("trendline", ts),
                            gid)
        view = _view_with_axis(bars)
        # Renderer-owned source of truth (Q-59): the view only knows stored
        # colors delivered via set_drawings. Sync the record but keep it
        # unrendered through a hidden group, so the commit meets the
        # unrendered + known-color drop path without touching the store.
        DrawingStore.update_group(gid, visible=False)
        view.drawing_overlay.set_data(
            symbol, DrawingStore.drawings_for_symbol(symbol),
            DrawingStore.groups_for_symbol(symbol))
        assert all(it.get("id") != did for it in view.drawing_items)
        pre_payload = dict(_store_row(symbol, did).payload)
        pre_color = _store_row(symbol, did).color
        emitted = []
        view.drawing_controller.updated.connect(
            lambda i, p, c: emitted.append((i, p, c)))
        view._on_page_drawing_updated(
            {"id": did, "kind": "trendline", "color": "",
             "points": [[2.0, 100.0], [5.0, 110.0]]})
        assert emitted == []
        assert dict(_store_row(symbol, did).payload) == pre_payload
        assert _store_row(symbol, did).color == pre_color
    finally:
        _cleanup(symbol)


def test_t32_unknown_id_without_store_row_emits(qapp):
    """Q-20 compat: a commit for an id with no rendered item AND no stored
    row still reaches ``updated`` (nothing to protect, pre-P10 transport
    behavior) — the real-page edit leg of ``test_page_messages_reach_python_signals``."""
    symbol = BASE_SYMBOL + "_T32NOROW"
    try:
        bars = _bars(symbol)
        view = _view_with_axis(bars)
        emitted = []
        view.drawing_controller.updated.connect(
            lambda i, p, c: emitted.append((i, p, c)))
        view._on_page_drawing_updated(
            {"id": 424242, "kind": "horizontal", "color": "",
             "price": 102.0})
        assert len(emitted) == 1
        drawing_id, payload, color = emitted[0]
        assert drawing_id == 424242
        assert payload == {"y": 102.0}
        assert color == ""
    finally:
        _cleanup(symbol)


def test_t33_cancel_and_zero_view(qapp):
    """P10-T3-T33: cancelled drag restores geometry with no store write;
    zero-view commit still persists."""
    from ui.lwc_view import LwcChartView

    symbol = BASE_SYMBOL + "_T33"
    try:
        gid = _seed_group(symbol, locked=False)
        bars = _bars(symbol)
        ts = [b.ts for b in bars]
        did = _seed_drawing(symbol, "trendline", _seed_payload("trendline", ts),
                            gid)
        view = _view_with_axis(bars)
        view.drawing_overlay.set_data(
            symbol, DrawingStore.drawings_for_symbol(symbol),
            DrawingStore.groups_for_symbol(symbol))
        pre_items = [dict(it) for it in view.drawing_items]
        pre_payload = dict(_store_row(symbol, did).payload)

        view.drawing_overlay.drag_drawing(did, "trendline", 0, 2.0, 3.0)
        assert [dict(it) for it in view.drawing_items] != pre_items
        view._render_drawings()
        assert [dict(it) for it in view.drawing_items] == pre_items
        assert dict(_store_row(symbol, did).payload) == pre_payload

        from ui.main_window import MainWindow

        stub = SimpleNamespace(_session_for_facade=lambda: None)
        new_payload = {"p1": {"x": ts[1], "y": 111.0},
                       "p2": {"x": ts[6], "y": 112.0}}
        MainWindow._on_drawing_updated(stub, did, new_payload, "#123456")
        row = _store_row(symbol, did)
        assert dict(row.payload) == new_payload
        assert row.color == "#123456"
    finally:
        _cleanup(symbol)
