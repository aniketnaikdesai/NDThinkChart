"""P9-T4 (S-P9-1 / finding 3.1): active draw group plus color into the commit.

_red pre-fix_: the page stamps ``null``/default into every drawing item, the
commit path stores a foreign group ID verbatim, and no setter reaches the
page on reload/symbol change. _green post-fix_: ``setActiveGroup`` (the
single writer) stamps the active ID plus color at commit time;
``_on_page_drawing_committed`` forwards both unchanged; ``_on_drawing_created``
coerces a foreign-symbol group to ``None``; ``_apply_active_draw_group``
re-pushes the setter on every group reload and symbol change.
"""
import pytest

from data.drawing_store import DrawingStore
from data.models import Bar
from ibkr.client import IBApiClient
from services.drawing_service import DEFAULT_DRAWING_COLOR
from ui.main_window import MainWindow

SYM = "P9T4A"
OTHER = "P9T4B"
GROUP_COLOR = "#12ab34"
TF = "5 mins"
TS0 = 1_700_000_000
STEP = 300


@pytest.fixture()
def window(qapp, tmp_path, monkeypatch):
    """Offscreen MainWindow: no live TWS, DB scoped to a temp file."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p9t4.db"))
    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    w = MainWindow()
    w._current_symbol = SYM
    yield w
    w.close()


def _bars(symbol: str, n: int = 12) -> list:
    rows = []
    for i in range(n):
        price = 100.0 + i * 0.1
        rows.append(Bar(symbol, TF, TS0 + i * STEP, price,
                        price + 0.25, price - 0.25, price + 0.05, 1000.0))
    return rows


def _load_chart_bars(window) -> list:
    """Put deterministic bars on the window's LWC view (page-commit axis)."""
    bars = _bars(SYM)
    window.chart_panel.set_symbol(SYM)
    window.chart_panel.set_timeframe(TF)
    window.chart_panel.update_chart(bars)
    return bars


def _commit(window, payload: dict):
    """Drive one page commit through the view into ``_on_drawing_created``."""
    seen = []
    window.chart_panel.drawing_controller.created.connect(seen.append)
    try:
        window.chart_panel._on_page_drawing_committed(payload)
    finally:
        try:
            window.chart_panel.drawing_controller.created.disconnect(
                seen.append)
        except (RuntimeError, TypeError):
            pass
    return seen


def _stored(symbol: str):
    return DrawingStore.drawings_for_symbol(symbol)


def test_t42_group_and_color_persist_end_to_end(window):
    """T42: a page commit carrying group+color stores both on the row."""
    gid = DrawingStore.create_group(SYM, "set-a", 1, color=GROUP_COLOR)
    bars = _load_chart_bars(window)
    seen = _commit(window, {
        "kind": "trendline",
        "points": [[2.0, 101.0], [7.0, 102.0]],
        "color": GROUP_COLOR,
        "group_id": gid,
    })
    assert seen, "the page commit must reach drawing_controller.created"
    assert seen[0].group_id == gid
    assert seen[0].color == GROUP_COLOR
    rows = _stored(SYM)
    assert rows, "the commit must persist a drawing row"
    row = rows[-1]
    assert row.group_id == gid
    assert row.color == GROUP_COLOR
    assert row.payload["p1"]["x"] == bars[2].ts
    assert row.payload["p2"]["x"] == bars[7].ts


def test_t43_foreign_group_coerces_to_none(window):
    """T43: a commit whose group belongs to another symbol stores None."""
    foreign = DrawingStore.create_group(OTHER, "foreign", 1,
                                        color=GROUP_COLOR)
    _load_chart_bars(window)
    seen = _commit(window, {
        "kind": "trendline",
        "points": [[2.0, 101.0], [7.0, 102.0]],
        "color": GROUP_COLOR,
        "group_id": foreign,
    })
    assert seen, "the page commit must reach drawing_controller.created"
    rows = _stored(SYM)
    assert rows, "the commit must persist a drawing row"
    assert rows[-1].group_id is None
    assert DrawingStore.drawings_for_symbol(OTHER) == []


def test_t44_setter_repushed_on_reload_and_symbol_change(window, monkeypatch):
    """T44: reload + symbol change re-push setActiveGroup with ID and color."""
    gid = DrawingStore.create_group(SYM, "set-a", 1, color=GROUP_COLOR)
    window._active_draw_group_id = gid

    calls = []

    class _Rec:
        def set_active_group(self, group_id, color):
            calls.append((group_id, color))

    monkeypatch.setattr(window, "_drawing_actions", lambda: _Rec())

    window._refresh_drawing_groups(SYM)
    assert calls, "the tool state must be re-pushed on group reload"
    assert calls[-1] == (gid, GROUP_COLOR)

    window.load_chart(OTHER)
    assert window._active_draw_group_id is None
    assert len(calls) > 1, "the symbol change must re-push the setter"
    assert calls[-1] == (None, DEFAULT_DRAWING_COLOR)
