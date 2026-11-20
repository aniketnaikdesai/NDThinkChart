"""P29-T4 / D99 (DG134): one delivery path per page-ready transition.

A page-ready transition is a full-log replay and nothing else. Every accepted
op is already in ``_op_log`` (``send_ops`` logs before it queues or stages),
so the staging buffers (``_queued`` / ``_outbox`` / ``_live_buf``) are
**discarded, not drained**, and ``set_ready`` only sets a flag — it cannot
emit. Each accepted op crosses exactly once per transition, the log is never
cleared, and an op that arrives *during* a transition is logged and delivered
by the armed flush like any other (never lost, never replayed beside it).

Reconstruction uses ``apply_ops_to_bars`` — the same fold the page applies —
so a duplicated or lost op fails the reconstruction, not just a count.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from ui.lwc_bridge import (
    LwBridge,
    apply_ops_to_bars,
    candle_update_op,
    candles_set_op,
    volume_set_op,
)

BASE = 1_700_000_000
STEP = 60

ALARM_OP = {
    "op": "set_alarms",
    "series": "alarms",
    "cols": {"id": [7], "price": [123.45]},
}


# ── fixtures ───────────────────────────────────────────────────────────────


def _bar(ts, o=100.0, h=101.0, lo=99.0, c=100.5, volume=10.0):
    return SimpleNamespace(ts=ts, open=o, high=h, low=lo, close=c,
                           volume=volume)


def _bars(n=4, ts0=BASE, step=STEP):
    return [
        _bar(
            ts0 + i * step,
            o=100.0 + i,
            h=101.0 + i,
            lo=99.0 + i,
            c=100.5 + i,
            volume=1000.0 + i,
        )
        for i in range(n)
    ]


def _rows(bars):
    return [(b.ts, b.open, b.high, b.low, b.close) for b in bars]


def _identities(op):
    """The ``(op, series, ts)`` identities one op contributes to a crossing.

    A multi-row replace contributes one identity per (op, series, ts), which
    is what "each queued op exactly once" means for a column-array op.
    """
    kind = op.get("op")
    series = op.get("series")
    cols = op.get("cols") or {}
    if "ts" in cols:
        return [(kind, series, ts) for ts in cols["ts"]]
    return [(kind, series, None)]


class _Recorder:
    """Capture every crossing a bridge makes (the page-side view)."""

    def __init__(self, bridge):
        self.ops: list = []
        self.channels: list = []
        self.replays: list = []
        self.bridge = bridge
        bridge.opsEmitted.connect(self.ops.append)
        bridge.channelOpsJson.connect(self.channels.append)
        bridge.replayFinished.connect(self.replays.append)


# ── AC-D99.1 · the transition delivers each queued op exactly once ─────────


def test_p29_t4_01_transition_delivers_each_queued_op_once():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bars = _bars(4)
    updates = [
        _bar(bars[1].ts, o=1.0, h=2.0, lo=0.5, c=1.5, volume=11.0),
        _bar(bars[2].ts, o=2.0, h=3.0, lo=1.5, c=2.5, volume=12.0),
        _bar(BASE + 4 * STEP, o=5.0, h=6.0, lo=4.5, c=5.5, volume=13.0),
    ]
    ops = (
        [candles_set_op(bars), volume_set_op(bars)]
        + [candle_update_op(b) for b in updates]
    )

    bridge.send_ops(ops)
    assert rec.ops == [] and rec.channels == [], "nothing crosses before ready"
    assert bridge.counters()["queued"] == 5

    env = bridge.handle_page_ready()
    assert env is not None
    assert rec.ops == [env], "exactly one bar envelope in the transition"
    assert rec.channels == [], "no channel op was queued"

    delivered = []
    for op in rec.ops[0]["ops"]:
        delivered.extend(_identities(op))
    for op in ops:
        for identity in _identities(op):
            assert delivered.count(identity) == 1, (
                f"{identity!r} did not cross exactly once"
            )
    assert len(delivered) == len(set(delivered)), "a duplicate crossed"

    by_ts = {b.ts: row for b, row in zip(bars, _rows(bars))}
    for b in updates:
        by_ts[b.ts] = (b.ts, b.open, b.high, b.low, b.close)
    expected = [by_ts[ts] for ts in sorted(by_ts)]
    assert apply_ops_to_bars(rec.ops[0]["ops"]) == expected


# ── AC-P29-04-SETREADY · set_ready is a flag setter, not a delivery path ───


def test_p29_t4_02_set_ready_emits_nothing_then_transition_delivers_once():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bars = _bars(2)
    bridge.send_ops([candles_set_op(bars), volume_set_op(bars)])
    assert bridge.counters()["queued"] == 2
    assert bridge.flush() is None, "pre-ready ops are not staged"

    bridge.set_ready(True)
    assert bridge.is_ready
    assert rec.ops == [] and rec.channels == [], "set_ready must not emit"
    assert rec.replays == [], "set_ready must not replay"
    assert bridge.counters()["emitted"] == 0
    assert bridge.counters()["emissions"] == 0
    assert bridge.counters()["replays"] == 0
    assert bridge.flush() is None, "set_ready must not drain into staging"

    env = bridge.handle_page_ready()
    assert env is not None
    assert [op["op"] for op in env["ops"]] == ["set_bars", "set_volume"]
    assert len(rec.ops) == 1, "the transition delivers, once"
    assert bridge.counters()["replays"] == 1


def test_p29_t4_03_empty_log_returns_none_and_counts_one_replay():
    bridge = LwBridge()
    rec = _Recorder(bridge)

    env = bridge.handle_page_ready()
    assert env is None
    assert rec.ops == []
    assert rec.channels == []
    assert bridge.counters()["replays"] == 1
    assert bridge.counters()["emissions"] == 0
    assert rec.replays == [], "no replayFinished without a payload"


def test_p29_t4_03_nonempty_log_is_one_envelope_with_the_whole_log_once():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bridge.send_ops([candles_set_op(_bars(3))])

    env = bridge.handle_page_ready()
    assert env is not None
    assert len(rec.ops) == 1 and rec.ops[0] == env
    assert len(env["ops"]) == len(bridge.replay_log())
    assert rec.replays == [len(bridge.replay_log())]
    assert bridge.counters()["replays"] == 1
    assert bridge.counters()["emissions"] == 1


# ── AC-D99.2 · recovery replays the never-cleared log once per transition ──


def test_p29_t4_04_each_recovery_replays_the_full_log_once():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bars = _bars(3)
    live = _bar(bars[-1].ts, o=10.0, h=11.0, lo=9.5, c=10.5, volume=77.0)

    bridge.set_ready(True)
    bridge.send_ops([candles_set_op(bars), candle_update_op(live)])
    log_len = len(bridge.replay_log())

    by_ts = {b.ts: row for b, row in zip(bars, _rows(bars))}
    by_ts[live.ts] = (live.ts, live.open, live.high, live.low, live.close)
    expected = [by_ts[ts] for ts in sorted(by_ts)]

    for round_no in range(2):
        before = len(rec.ops)
        bridge.handle_render_terminated()
        assert not bridge.is_ready

        env = bridge.handle_page_ready()
        assert env is not None
        emitted = rec.ops[before:]
        assert len(emitted) == 1, f"round {round_no}: one envelope per transition"
        assert len(emitted[0]["ops"]) == log_len

        identities = []
        for op in emitted[0]["ops"]:
            identities.extend(_identities(op))
        assert len(identities) == len(set(identities)), (
            f"round {round_no}: an envelope contains an op twice"
        )
        assert apply_ops_to_bars(emitted[0]["ops"]) == expected
        assert len(bridge.replay_log()) == log_len, "the log is never cleared"


# ── AC-P29-04-CHANNEL · a staged live op and the channel path ──────────────


def test_p29_t4_05_staged_live_op_crosses_once_via_the_log():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bridge.set_ready(True)
    live = _bar(BASE + 10 * STEP)
    bridge.send_ops([candle_update_op(live)])
    assert rec.ops == [], "staged in _live_buf, not emitted yet"
    assert bridge.counters()["emitted"] == 0

    bridge.handle_render_terminated()
    env = bridge.handle_page_ready()
    assert env is not None
    assert len(rec.ops) == 1, "one envelope — no flush beside the replay"
    assert [op["op"] for op in rec.ops[0]["ops"]] == ["update_bar"]
    assert apply_ops_to_bars(rec.ops[0]["ops"]) == _rows([live])
    assert bridge._outbox == [] and bridge._live_buf == {}


def test_p29_t4_05_channel_op_sent_while_not_ready_replays_once():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bridge.send_channel("alarms", [ALARM_OP])
    assert rec.channels == [], "nothing crosses before the page is ready"
    assert bridge._channel_queue == [("alarms", [ALARM_OP])]

    bar_env = bridge.handle_page_ready()
    assert bar_env is None, "the bar log is empty"
    assert len(rec.channels) == 1
    channel_env = json.loads(rec.channels[0])
    assert channel_env["v"] == 1
    assert channel_env["channel"] == "alarms"
    assert channel_env["ops"] == [ALARM_OP]
    assert bridge._channel_queue == [], "the queue is dropped, not drained"
    assert bridge.counters()["channel_replays"] == 1


def test_p29_t4_06_mixed_transition_one_bar_and_one_channel_envelope():
    bridge = LwBridge()
    rec = _Recorder(bridge)
    bars = _bars(2)
    late = _bar(BASE + 5 * STEP)
    bar_ops = [candles_set_op(bars), candle_update_op(late)]

    for op in bar_ops:
        bridge.send_ops([op])
    bridge.send_channel("alarms", [ALARM_OP])
    assert bridge.counters()["queued"] == len(bar_ops)

    env = bridge.handle_page_ready()
    assert env is not None
    assert len(rec.ops) == 1, "one bar envelope"
    assert len(rec.channels) == 1, "one channel envelope"

    assert [op["op"] for op in env["ops"]] == ["set_bars", "update_bar"]
    identities = []
    for op in env["ops"]:
        identities.extend(_identities(op))
    assert len(identities) == len(set(identities))

    channel_env = json.loads(rec.channels[0])
    assert channel_env["channel"] == "alarms"
    assert channel_env["ops"] == [ALARM_OP]
    assert bridge.counters()["queued"] == len(bar_ops), (
        "queued still counts what was queued"
    )


# ── the invariant: an op arriving DURING the transition ────────────────────


def test_p29_t4_op_during_transition_is_logged_and_flushed_once():
    """Neither lost nor doubled: logged now, delivered by the armed flush."""
    bridge = LwBridge()
    late = _bar(BASE + 20 * STEP)
    delivered = []

    def _during_transition(env):
        delivered.append(env)
        if len(delivered) == 1:
            # Re-entrant arrival: the page-readiness slot is still running.
            bridge.send_ops([candle_update_op(late)])

    bridge.opsEmitted.connect(_during_transition)
    bars = _bars(2)
    bridge.send_ops([candles_set_op(bars)])

    env = bridge.handle_page_ready()
    assert [op["op"] for op in env["ops"]] == ["set_bars"], (
        "the replay envelope was built before the late op arrived"
    )
    assert bridge.replay_log()[-1]["op"] == "update_bar", "the late op is logged"

    flushed = bridge.flush()
    assert flushed is not None, "the armed flush delivers the late op"
    assert [op["op"] for op in flushed["ops"]] == ["update_bar"]
    assert bridge.flush() is None, "and only once"
    assert len(delivered) == 2

    assert apply_ops_to_bars(delivered[0]["ops"] + delivered[1]["ops"]) == (
        _rows(bars) + _rows([late])
    )
