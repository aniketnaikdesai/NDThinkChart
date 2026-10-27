"""tests/test_lwc_drawing_tool.py — Q-33: the drawing toolbar drives the LWC view.

MainWindow's toolbar calls ``_chart_call("set_drawing_tool", tool)`` on every
combo change. Before Q-33 the LWC driver had no such method, so the call was
swallowed and no tool was ever armed. These cases pin the contract the toolbar
(and the combo reset, ESC-017) depend on, without a page:

* a real tool enters ``DRAWING`` and publishes it on the interaction channel;
* an unknown name falls back to the cursor, exactly as the deleted overlay's
  ``set_tool`` did;
* ``mode_changed`` fires for an explicit switch **and** whenever the router
  clears the tool as a side effect (magnifier, alarm mode, symbol change) —
  the signal MainWindow uses to reset the stale combo;
* ``PageDrawing`` carries ``label``, so the store's create path does not raise
  the moment a real page commit arrives.
"""

from __future__ import annotations

import pytest

from data.db import db
from data.drawing_store import DrawingStore
from ui import lwc_view as LV

SYMBOL = "TESTLWC33"


@pytest.fixture(autouse=True)
def clean():
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM drawings WHERE symbol=?", (SYMBOL,))
    db.conn.commit()
    yield
    cursor.execute("DELETE FROM drawings WHERE symbol=?", (SYMBOL,))
    db.conn.commit()


def _view(tz_offset: int = 0, editable: bool = True) -> LV.LwcChartView:
    view = LV.LwcChartView(tz_offset=tz_offset, editable=editable)
    view.bridge.set_ready(True)
    return view


def test_a_real_tool_enters_drawing_and_is_published(qapp):
    view = _view()
    assert view.set_drawing_tool("trendline") == "DRAWING"

    op = view.interaction_ops[-1]
    assert op["op"] == "router_mode"
    assert op["mode"] == "DRAWING"
    assert op["tool"] == "trendline"
    assert op["intent"] == "draw_tool"
    assert op["refused"] is False


@pytest.mark.parametrize("tool", ["", None, "nonsense"])
def test_an_unknown_tool_falls_back_to_the_cursor(qapp, tool):
    view = _view()
    view.set_drawing_tool("trendline")

    assert view.set_drawing_tool(tool) == "IDLE"
    op = view.interaction_ops[-1]
    assert op["tool"] == "cursor"
    assert op["intent"] == "draw_cursor"
    assert op["mode"] == "IDLE"


def test_the_combo_reset_signal_fires_for_an_explicit_switch(qapp):
    view = _view()
    seen = []
    view.drawing_controller.mode_changed.connect(seen.append)

    view.set_drawing_tool("zone")
    view.set_drawing_tool("cursor")

    assert seen == ["zone", "cursor"]


def test_the_magnifier_clears_the_tool_and_reports_it(qapp):
    """TR-4: entering zoom from DRAWING drops the tool; the combo must follow."""
    view = _view()
    view.set_drawing_tool("fibonacci")
    seen = []
    view.drawing_controller.mode_changed.connect(seen.append)

    result = view.handle_control("magnifier", True)

    assert result["mode"] == "ZOOMING"
    assert seen == ["cursor"], "the toolbar combo would stay stale"


def test_alarm_mode_clears_the_tool_and_reports_it(qapp):
    """TR-7: alarm placement takes the tool away."""
    view = _view()
    view.set_drawing_tool("measure")
    seen = []
    view.drawing_controller.mode_changed.connect(seen.append)

    view.set_alarm_mode(True)

    assert view.router.active_mode.name == "ALARM_PLACING"
    assert seen == ["cursor"]


def test_a_symbol_change_reports_the_cleared_tool(qapp):
    """TR-17: a mid-gesture symbol change resets, discarding the draft."""
    view = _view()
    view.set_drawing_tool("trendline")
    seen = []
    view.drawing_controller.mode_changed.connect(seen.append)

    view.set_symbol("MSFT")

    assert view.router.active_mode.name == "IDLE"
    assert seen == ["cursor"]


def test_a_pop_out_view_is_inert(qapp):
    """D24: a non-editable view never arms a tool."""
    view = _view(editable=False)
    before = list(view.interaction_ops)

    assert view.set_drawing_tool("trendline") == "IDLE"
    assert view.interaction_ops == before


def test_page_drawing_carries_the_label_the_store_reads(qapp):
    """A page commit reaches ``create_*``; the attribute must exist and survive."""
    drawing = LV.PageDrawing(
        symbol=SYMBOL, kind="horizontal", payload={"y": 101.5},
        color="#38bdf8", group_id=None,
    )
    assert drawing.label == ""

    drawing_id = DrawingStore.create_drawing(drawing)
    stored = DrawingStore.drawings_for_symbol(SYMBOL)
    assert [d.kind for d in stored] == ["horizontal"]
    assert stored[0].payload == {"y": 101.5}
    assert drawing_id == stored[0].id
