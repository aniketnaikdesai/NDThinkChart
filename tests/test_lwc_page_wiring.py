"""Q-31: the five non-bar channels reach the page.

Root cause this suite pins: ``chart.html`` loaded only lightweight-charts,
envelope.js, qwebchannel and chart.js, so the channel modules never ran, and
``ui/lwc_view.py`` published study/interaction/alarm/drawing/overlay/marker
envelopes with no consumer. The tests below prove the page loads the modules,
each publish site feeds its channel to the bridge, and the bridge's
queue/replay/validation behaviour is real (not a static claim).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from ui import lwc_bridge as LB

REPO = Path(__file__).resolve().parent.parent
HTML = REPO / "chart_assets" / "lwc" / "chart.html"
CHART_JS = REPO / "chart_assets" / "lwc" / "chart.js"
VIEW = REPO / "ui" / "lwc_view.py"

#: The five UMD modules the page must load before chart.js, and the bridge
#: channel each publish site feeds.
MODULE_SCRIPTS = (
    "interaction.js",
    "alarms.js",
    "primitives.js",
    "overlays.js",
    "studies.js",
)

PUBLISH_CHANNELS = {
    "_publish_study_ops": "studies",
    "_publish_interaction_op": "interaction",
    "_publish_alarm_ops": "alarms",
    "_publish_drawing_ops": "drawings",
    "_publish_overlay_ops": "overlays",
    "_publish_marker_ops": "markers",
}


# ── page bootstrap (static: the page has no DOM in pytest) ─────────────────


def test_page_loads_the_five_modules_before_chart_js():
    text = HTML.read_text(encoding="utf-8")
    chart_js_at = text.index("./chart.js")
    for name in MODULE_SCRIPTS:
        assert f"./{name}" in text, f"chart.html does not load {name}"
        assert text.index(f"./{name}") < chart_js_at, (
            f"{name} must load before chart.js — chart.js binds it at startup"
        )


def test_page_stays_offline():
    text = HTML.read_text(encoding="utf-8")
    assert "http://" not in text and "https://" not in text


def test_chart_js_apply_channel_has_all_six_cases():
    text = CHART_JS.read_text(encoding="utf-8")
    start = text.index("function applyChannel(")
    end = text.index("/* v5 series API bridge", start)
    body = text[start:end]
    for channel in LB.CHANNELS:
        assert f'"{channel}"' in body, (
            f"applyChannel has no dispatch case for {channel!r}"
        )


def test_chart_js_binds_modules_before_page_ready():
    text = CHART_JS.read_text(encoding="utf-8")
    body = text[text.index("function bindChannel("):]
    assert "bindModules()" in body
    assert body.index("bindModules()") < body.index("bridge.pageReady()"), (
        "modules must be bound before the channel replay lands"
    )
    assert "channelOpsJson" in body


def test_every_publish_site_forwards_to_its_channel():
    text = VIEW.read_text(encoding="utf-8")
    blocks = re.split(r"\n    def ", text)
    for method, channel in PUBLISH_CHANNELS.items():
        block = next((b for b in blocks if b.startswith(f"{method}(")), None)
        assert block is not None, f"{method} is missing"
        assert f'send_channel("{channel}"' in block, (
            f"{method} does not forward its ops to the {channel!r} channel"
        )


# ── bridge behaviour ───────────────────────────────────────────────────────


def _alarm_op():
    return {
        "op": "set_alarms",
        "series": "alarms",
        "cols": {"id": [7], "price": [123.45]},
    }


def _bars():
    return [
        SimpleNamespace(ts=60, open=1.0, high=2.0, low=0.5, close=1.5,
                        volume=10),
        SimpleNamespace(ts=120, open=1.5, high=2.5, low=1.0, close=2.0,
                        volume=20),
    ]


def test_send_channel_before_ready_queues_then_replays():
    bridge = LB.LwBridge()
    seen: list[str] = []
    bridge.channelOpsJson.connect(seen.append)
    op = _alarm_op()

    bridge.send_channel("alarms", [op])
    assert seen == [], "nothing crosses before the page is ready"
    assert bridge.counters()["channel_received"] == 1
    assert bridge.replay_log() == [], "channels never touch the bar op log"

    bridge.handle_page_ready()
    assert seen, "the channel replay must cross on channelOpsJson"
    env = json.loads(seen[-1])
    assert env["v"] == 1
    assert env["channel"] == "alarms"
    assert env["ops"] == [op]
    assert bridge.counters()["channel_replays"] == 1


def test_send_channel_emits_immediately_when_ready():
    bridge = LB.LwBridge()
    bridge.set_ready(True)
    seen: list[str] = []
    bridge.channelOpsJson.connect(seen.append)
    bridge.send_channel("drawings", [{"op": "clear_drawings",
                                      "series": "drawings"}])
    assert len(seen) == 1
    assert json.loads(seen[0])["channel"] == "drawings"


def test_unknown_channel_raises():
    bridge = LB.LwBridge()
    with pytest.raises(ValueError):
        bridge.send_channel("bogus", [{"op": "x"}])


def test_non_dict_op_raises():
    bridge = LB.LwBridge()
    with pytest.raises(ValueError):
        bridge.send_channel("alarms", ["not-an-op"])


def test_nan_raises_before_emitting():
    bridge = LB.LwBridge()
    bridge.set_ready(True)
    seen: list[str] = []
    bridge.channelOpsJson.connect(seen.append)
    with pytest.raises(ValueError):
        bridge.send_channel("alarms", [{"op": "set_alarm_preview",
                                        "series": "alarms",
                                        "price": float("nan")}])
    assert seen == [], "a NaN must fail at the boundary, never cross"
    assert bridge.counters()["channel_received"] == 0


def test_bar_replay_contract_is_unchanged():
    bridge = LB.LwBridge()
    bridge.send_ops([LB.candles_set_op(_bars())])
    env = bridge.handle_page_ready()
    assert env is not None
    assert env["v"] == 1
    assert "channel" not in env
    assert len(LB.apply_ops_to_bars(env["ops"])) == 2


def test_view_publish_forwards_to_bridge(qapp):
    from ui.lwc_view import LwcChartView

    view = LwcChartView()
    view.bridge.set_ready(True)
    seen: list[str] = []
    view.bridge.channelOpsJson.connect(seen.append)
    view._publish_alarm_ops([_alarm_op()])
    channels = [json.loads(payload)["channel"] for payload in seen]
    assert "alarms" in channels
