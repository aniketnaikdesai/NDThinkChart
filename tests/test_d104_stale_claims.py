"""D104 (P30) — the engine claims match the code, and the release matches its words.

Two classes of ``pyqtgraph`` mention are allowed to survive in production
modules: a **negative assertion** ("imports no pyqtgraph") and **marked
history** (the removal record, the "names survive the removal" note). Every
other hit is a stale present-tense claim and must disappear. The allow-list is
keyed by ``(relative path, distinctive fragment)`` — never by line number — so
ordinary edits do not break it while a new claim does.

The release half is the reverse of the wording half: ``release_resources``'s
docstring is the contract, so the body is asserted bucket by bucket after a
call. ``memory_bytes`` is deliberately not extended (AR-P30-6): it still
accounts the bar log only.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("ui", "services", "data", "ibkr")

# 8 negative assertions: each says "no Qt here", never that an engine exists.
NEGATIVE_ASSERTIONS = (
    ("ui/dock_layout.py",
     "imports no PyQt6 / pyqtgraph / any Qt"),
    ("ui/lwc_view.py",
     "never drags the pyqtgraph seam in at import time"),
    ("services/time_collapse_service.py",
     "No PyQt6/pyqtgraph/Qt import appears anywhere in this module"),
    ("services/market_calendar.py",
     "No PyQt6/pyqtgraph/Qt import appears anywhere in this module"),
    ("services/backfill_service.py",
     "No PyQt6/pyqtgraph/Qt import appears anywhere in this module"),
    ("services/option_ladder.py",
     "No PyQt6/pyqtgraph/Qt import appears anywhere in this module"),
    ("services/option_spread_engine.py",
     "No PyQt6/pyqtgraph/Qt import appears anywhere in this module"),
    ("services/chart_model.py",
     "No PyQt6 / pyqtgraph / Qt import may ever appear in this module"),
)

# 4 marked-history lines: they describe the removal, not a live engine.
MARKED_HISTORY = (
    ("ui/chart_view.py",
     "P6-13 / Phase 11 removed the pyqtgraph engine"),
    ("ui/chart_view.py",
     "returning to pyqtgraph is a ``git revert`` of the removal"),
    ("ui/drawing_tools.py",
     "The names survive the pyqtgraph removal"),
    ("services/chart_model.py",
     "Moved here from ``ui/candlestick_item`` when the pyqtgraph engine was"),
)

ALLOW_LIST = NEGATIVE_ASSERTIONS + MARKED_HISTORY


def _source_lines():
    """Yield ``(relative path, line number, line)`` for every production module."""
    for dirname in SCAN_DIRS:
        for path in sorted((REPO / dirname).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                yield rel, lineno, line


def test_engine_claims_are_allow_listed_negative_or_history():
    """(a) AC-D104.1: every surviving claim is a negative or marked history."""
    lines = list(_source_lines())
    hits = [(rel, lineno, line) for rel, lineno, line in lines
            if "pyqtgraph" in line.lower()]

    matched = {row: 0 for row in ALLOW_LIST}
    unmatched: list[str] = []
    ambiguous: list[str] = []
    for rel, lineno, line in hits:
        rows = [row for row in ALLOW_LIST
                if row[0] == rel and row[1].lower() in line.lower()]
        if len(rows) == 1:
            matched[rows[0]] += 1
        elif not rows:
            unmatched.append(f"{rel}:{lineno}: {line.strip()}")
        else:
            ambiguous.append(f"{rel}:{lineno}: {line.strip()} -> {rows}")

    assert not unmatched, (
        "unlisted pyqtgraph claim(s):\n" + "\n".join(unmatched))
    assert not ambiguous, (
        "hit matches more than one allow-list row:\n" + "\n".join(ambiguous))
    assert all(count == 1 for count in matched.values()), (
        "every allow-listed line must survive exactly once; got "
        + repr(matched))
    # Twelve remaining hits = 8 negative assertions + 4 marked-history lines.
    assert len(hits) == 12, (
        f"expected twelve allow-listed hits, found {len(hits)}: "
        + repr([f"{rel}:{lineno}" for rel, lineno, _ in hits]))

    # The seven stale mentions (main_window 3, popout_window 4) are gone.
    for name in ("ui/main_window.py", "ui/popout_window.py"):
        offenders = [
            f"{name}:{lineno}: {line.strip()}"
            for rel, lineno, line in lines
            if rel == name and "pyqtgraph" in line.lower()
        ]
        assert not offenders, "stale engine claim survives:\n" + "\n".join(offenders)

    # The rewritten sentence and the two outright present-tense claims are gone.
    forbidden = (
        "keeps its identical local copy until p6-13",
        "stays present and default",
        "keeps pyqtgraph",
    )
    survivors = [
        f"{rel}:{lineno}: {line.strip()}"
        for rel, lineno, line in lines
        for fragment in forbidden
        if fragment in line.lower()
    ]
    assert not survivors, "retired claim survives:\n" + "\n".join(survivors)


def test_chart_view_removal_record_is_unchanged():
    """(c) AC-D104.1: the removal record is history, never sanitised away."""
    text = (REPO / "ui/chart_view.py").read_text(encoding="utf-8")
    assert "P6-13 / Phase 11 removed the pyqtgraph engine" in text
    assert "gate_P6_T13.md" in text

    # ``create_chart_view`` is still the LWC-only factory: no engine switch.
    factory = text.split("def create_chart_view", 1)[1]
    assert "from ui.lwc_view import LwcChartView" in factory
    assert "return LwcChartView(tz_offset=tz_offset, editable=editable)" in factory
    assert "NDT_CHART_ENGINE" not in factory


def test_release_resources_clears_every_documented_bucket(qapp):
    """(b) AC-D104.2: every item the docstring names is empty after the call."""
    from ui.lwc_view import LwcChartView

    view = LwcChartView()
    try:
        # Make every documented view bucket non-empty, so the release is
        # measurable rather than vacuously true.
        view._bars = [object()]
        view._plotted = [object()]
        view._logical = [1]
        view._study_overlays = {"sma": [1.0, 2.0]}
        view._study_log = [{"op": "studies"}]
        view._study_envelopes = [{"op": "studies"}]
        view._interaction_log = [{"op": "interaction"}]
        view._interaction_envelopes = [{"op": "interaction"}]
        view._alarm_log = [{"op": "alarms"}]
        view._alarm_envelopes = [{"op": "alarms"}]
        view._drawing_items = [object()]
        view._drawing_log = [{"op": "drawings"}]
        view._drawing_envelopes = [{"op": "drawings"}]
        view._overlay_log = [{"op": "overlays"}]
        view._overlay_envelopes = [{"op": "overlays"}]

        bridge = view._bridge
        for channel in ("studies", "interaction", "alarms", "drawings", "overlays"):
            bridge.send_channel(channel, [{"op": "test", "channel": channel},
                                          {"op": "test", "channel": channel}])

        # Preconditions: the channel logs really hold ops, so the release has
        # something to clear (this is the assertion that is red pre-fix).
        assert all(bucket for bucket in bridge._channel_logs.values())
        assert bridge._channel_queue
        assert view.memory_bytes()["total_bytes"] > 0

        view.release_resources()

        assert view._bars == []
        assert view._plotted == []
        assert view._logical == []
        assert view._study_overlays == {}
        assert view._study_log == []
        assert view._study_envelopes == []
        assert view._interaction_log == []
        assert view._interaction_envelopes == []
        assert view._alarm_log == []
        assert view._alarm_envelopes == []
        assert view._drawing_items == []
        assert view._drawing_log == []
        assert view._drawing_envelopes == []
        assert view._overlay_log == []
        assert view._overlay_envelopes == []
        assert not bridge._op_log
        assert not bridge._queued
        assert not bridge._outbox
        assert not bridge._live_buf
        assert all(not bucket for bucket in bridge._channel_logs.values())
        assert bridge._channel_queue == []
        assert view.memory_bytes()["total_bytes"] == 0

        # Idempotent: a second call changes nothing.
        view.release_resources()
        assert view._bars == []
        assert view._plotted == []
        assert view._logical == []
        assert view._study_overlays == {}
        assert view._drawing_items == []
        assert all(not bucket for bucket in bridge._channel_logs.values())
        assert bridge._channel_queue == []
        assert view.memory_bytes()["total_bytes"] == 0
    finally:
        view.deleteLater()
