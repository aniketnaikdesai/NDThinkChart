"""P11-T4: per-symbol viewport memory (D51.4; S-P11-5).

Python-side in-memory ``symbol -> {range, following}`` store on the LWC
view, fed by throttled page range reports (gesture-end + post-update only,
AP-P11-3); saved on switch-away via the existing ``set_symbol`` lifecycle
and restored on switch-back via a ``set_visible_range`` range op. No
persistence, no schema change — a fresh view starts empty.

Both tests run offscreen (no renderer): the throttled page reports arrive
through the view's ``report_viewport`` sink (and the bridge's
``viewportReport`` JSON slot, which feeds the same sink), and the restore
range op is asserted on the view's interaction log + the bridge's
interaction-channel log.
"""

from __future__ import annotations

import json
from pathlib import Path

from data.models import Bar
from ui import lwc_view as LV

REPO = Path(__file__).resolve().parent.parent

TIMEFRAME = "5 mins"
PERIOD = 300
BASE_TS = 1_700_000_000


def _bars(symbol: str, n: int = 40):
    return [
        Bar(symbol, TIMEFRAME, BASE_TS + i * PERIOD,
            100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 1000.0)
        for i in range(n)
    ]


def _view(qapp):
    view = LV.LwcChartView(tz_offset=14400)
    view.set_symbol("aaa")
    view.set_timeframe(TIMEFRAME)
    view.set_series("candles", _bars("AAA"))
    return view


def test_p11_t4_t41_switch_away_and_back_restores_viewport(qapp):
    """P11-T4-T41 (AC1): switch-back restores the remembered viewport.

    Symbol A scrolled back (two reports — the freshest gesture-end /
    post-update report wins, AR-P11-2); switch to B; switch back to A
    (mixed case). A's remembered range + follow state is restored exactly
    via one ``set_visible_range`` range op, and B's own report is saved
    under its key.
    """
    view = _view(qapp)
    marked = len(view.interaction_ops)
    # Scrolled back on A: an older report then the freshest one.
    assert view.report_viewport({"from": 10.0, "to": 40.0}, following=True)
    assert view.report_viewport({"from": 2.0, "to": 20.0}, following=False)
    # Switch away to B: A's freshest report is saved (upper-cased key).
    view.set_symbol("BBB")
    assert view.viewport_memory["AAA"] == {
        "range": {"from": 2.0, "to": 20.0}, "following": False}
    view.set_series("candles", _bars("BBB"))
    # B's report arrives through the real page -> Python path (the bridge's
    # JSON slot, the mirror of opsJson) into the same sink.
    view.bridge.viewportReport(json.dumps(
        {"range": {"from": 0.0, "to": 30.0}, "following": True}))
    # Switch back to A (mixed case): one range op restores A exactly, and
    # B's report is saved under its own key.
    view.set_symbol("aAa")
    assert view.viewport_memory["BBB"] == {
        "range": {"from": 0.0, "to": 30.0}, "following": True}
    restores = [op for op in view.interaction_ops[marked:]
                if op.get("op") == "set_visible_range"]
    assert len(restores) == 1
    assert restores[0]["range"] == {"from": 2.0, "to": 20.0}
    assert restores[0]["following"] is False
    # The restore rides the existing interaction channel (no new channel
    # type, no bar-transport change).
    channel_ops = view.bridge._channel_logs["interaction"]
    assert restores[0] in channel_ops


def test_p11_t4_t42_upper_case_keying_no_persistence(qapp):
    """P11-T4-T42 (AC2): upper-cased keys, empty fresh store, no schema.

    A lowercase ``set_symbol`` lands on the upper-cased key; a fresh view
    holds no entries (in-memory session state only); junk reports are
    ignored; and the bars/drawings/alarms schemas plus migrations are
    untouched (no ``viewport`` persistence anywhere).
    """
    view = LV.LwcChartView(tz_offset=14400)
    assert view.viewport_memory == {}
    view.set_symbol("aaa")
    assert view.report_viewport({"from": 1.0, "to": 9.0},
                                following=True) is True
    assert view.report_viewport("junk") is False
    assert view.report_viewport({"from": float("nan"), "to": 1.0}) is False
    assert view.report_viewport({"from": 1.0}) is False
    view.set_symbol("BBB")
    assert set(view.viewport_memory) == {"AAA"}
    assert view.viewport_memory["AAA"] == {
        "range": {"from": 1.0, "to": 9.0}, "following": True}
    # Same-symbol call is not a switch: nothing saved, nothing restored.
    marked = len(view.interaction_ops)
    view.set_symbol("BBB")
    assert set(view.viewport_memory) == {"AAA"}
    assert [op for op in view.interaction_ops[marked:]
            if op.get("op") == "set_visible_range"] == []
    # No persistence: a fresh view starts empty, and no schema or migration
    # carries a viewport store.
    assert LV.LwcChartView(tz_offset=14400).viewport_memory == {}
    for path in ("data/db.py", "data/models.py"):
        assert "viewport" not in (REPO / path).read_text(
            encoding="utf-8").lower(), path
